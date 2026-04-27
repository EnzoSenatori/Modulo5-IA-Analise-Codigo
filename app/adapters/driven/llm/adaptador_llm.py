import json
from typing import Dict, List, Optional, Tuple

from app.application.ports.driven.provedor_llm import ProvedorLLM
from app.domain.entidades.relacao import Relacao
from app.domain.excecoes import LLMError

_TIPOS_VALIDOS = {"usa", "depende_de"}


class AdaptadorLLMGemini(ProvedorLLM):
    """Adaptador que usa Google Gemini para inferir relações e responsabilidades."""

    def __init__(self, api_key: str, modelo: str = "gemini-2.0-flash", timeout: int = 20):
        if not api_key:
            raise ValueError("api_key é obrigatória para AdaptadorLLMGemini")
        self._api_key = api_key
        self._modelo_nome = modelo
        self._timeout = timeout
        self._modelo = self._inicializar_modelo()

    def _inicializar_modelo(self):
        from google import genai
        return genai.Client(api_key=self._api_key)

    def inferir_relacoes_e_responsabilidades(
        self,
        codigo: str,
        nomes_componentes: List[str],
    ) -> Tuple[Dict[str, str], List[Relacao]]:
        prompt = self._montar_prompt(codigo, nomes_componentes)
        try:
            bruto = self._chamar_modelo(prompt)
        except Exception as e:
            raise LLMError(f"Falha ao chamar Gemini: {e}")

        try:
            payload = json.loads(bruto)
        except json.JSONDecodeError as e:
            raise LLMError(f"JSON inválido na resposta do LLM: {e}")

        if not isinstance(payload, dict):
            raise LLMError("Resposta do LLM não é um objeto JSON.")
        if "responsabilidades" not in payload or "relacoes" not in payload:
            raise LLMError("Resposta do LLM não contém as chaves esperadas.")

        nomes_set = set(nomes_componentes)
        responsabilidades = {
            nome: texto
            for nome, texto in (payload.get("responsabilidades") or {}).items()
            if nome in nomes_set and isinstance(texto, str)
        }

        relacoes_filtradas: List[Relacao] = []
        for item in payload.get("relacoes") or []:
            if not isinstance(item, dict):
                continue
            origem = item.get("origem")
            destino = item.get("destino")
            tipo = item.get("tipo")
            if (
                origem in nomes_set
                and destino in nomes_set
                and tipo in _TIPOS_VALIDOS
            ):
                relacoes_filtradas.append(Relacao(
                    origem=origem,
                    destino=destino,
                    tipo=tipo,
                    fonte="llm",
                ))

        return responsabilidades, relacoes_filtradas

    def _chamar_modelo(self, prompt: str) -> str:
        from google.genai import types
        resposta = self._modelo.models.generate_content(
            model=self._modelo_nome,
            contents=prompt,
            config=types.GenerateContentConfig(
                response_mime_type="application/json",
            ),
        )
        return resposta.text or ""

    def _montar_prompt(self, codigo: str, nomes: List[str]) -> str:
        lista = "\n".join(f"- {n}" for n in nomes) if nomes else "(nenhuma)"
        return f"""Você é um analista de arquitetura de software. Recebe o código-fonte Python
abaixo e a lista de classes já extraídas por análise estática. Sua tarefa:

1. Para cada classe da lista, escrever uma "responsabilidade" em uma frase curta
   (máx. 15 palavras), em português.
2. Identificar relações entre as classes da lista. Use APENAS nomes que apareçam
   na lista — não invente classes. Tipos válidos:
   - "usa": a classe origem instancia ou chama métodos da destino.
   - "depende_de": a classe origem recebe a destino como parâmetro/atributo
     (injeção de dependência).
   NÃO inclua heranças (já foram extraídas por AST).

Responda EXCLUSIVAMENTE em JSON válido, sem texto extra, no formato:
{{
  "responsabilidades": {{"NomeDaClasse": "frase curta", ...}},
  "relacoes": [{{"origem": "X", "destino": "Y", "tipo": "usa"}}, ...]
}}

CÓDIGO:
```python
{codigo}
```

CLASSES (extraídas por AST):
{lista}
"""


class AdaptadorLLMFake(ProvedorLLM):
    """Implementação determinística para testes — não faz I/O."""

    def __init__(
        self,
        responsabilidades: Optional[Dict[str, str]] = None,
        relacoes: Optional[List[Relacao]] = None,
        erro: Optional[Exception] = None,
    ):
        self._responsabilidades = responsabilidades or {}
        self._relacoes = relacoes or []
        self._erro = erro

    def inferir_relacoes_e_responsabilidades(
        self,
        codigo: str,
        nomes_componentes: List[str],
    ) -> Tuple[Dict[str, str], List[Relacao]]:
        if self._erro is not None:
            raise self._erro
        return dict(self._responsabilidades), list(self._relacoes)
