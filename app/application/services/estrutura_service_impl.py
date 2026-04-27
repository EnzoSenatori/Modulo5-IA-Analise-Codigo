import re
from typing import List

from app.application.ports.driving.estrutura_service import EstruturaService
from app.application.ports.driven.parser_codigo import ParserCodigo
from app.application.ports.driven.provedor_llm import ProvedorLLM
from app.domain.entidades.estrutura_arquitetural import EstruturaArquitetural
from app.domain.entidades.relacao import Relacao
from app.domain.excecoes import LLMError, ParserError


# Heurísticas leves para identificar a linguagem do código-fonte.
# Ordem importa: padrões mais específicos primeiro.
_LINGUAGENS = [
    ("javascript", [
        r"\bfunction\s+\w+\s*\(",
        r"=>\s*[{\(]",
        r"\b(const|let|var)\s+\w+\s*=",
    ]),
    ("typescript", [
        r":\s*(string|number|boolean|any)\b",
        r"\binterface\s+\w+\s*\{",
    ]),
    ("java", [
        r"\bpublic\s+(class|interface|static)\b",
        r"\bSystem\.out\.println\b",
    ]),
    ("go", [
        r"^package\s+\w+",
        r"\bfunc\s+\w+\s*\(",
    ]),
    ("python", [
        r"^\s*def\s+\w+\s*\(",
        r"^\s*class\s+\w+\s*[:\(]",
        r"^\s*import\s+\w+",
        r"^\s*from\s+\w+\s+import\b",
    ]),
]


class EstruturaServiceImpl(EstruturaService):
    """Orquestra AST + LLM para gerar diagrama de classes."""

    def __init__(self, parser_codigo: ParserCodigo, provedor_llm: ProvedorLLM):
        self._parser = parser_codigo
        self._llm = provedor_llm

    def gerar_diagrama(self, codigo: str) -> EstruturaArquitetural:
        if not codigo or not codigo.strip():
            raise ParserError("O código fonte fornecido está vazio.")

        linguagem = self._detectar_linguagem(codigo)

        if linguagem != "python":
            return EstruturaArquitetural(
                componentes=[],
                relacoes=[],
                warnings=[
                    f"Linguagem '{linguagem}' não suportada nesta versão. "
                    "Apenas Python é analisado."
                ],
                linguagem=linguagem,
            )

        componentes = self._parser.extrair_estrutura(codigo)
        herancas = self._parser.extrair_herancas(codigo)

        warnings: List[str] = []
        relacoes_llm: List[Relacao] = []

        if componentes:
            try:
                responsabilidades, relacoes_llm = (
                    self._llm.inferir_relacoes_e_responsabilidades(
                        codigo, [c.nome for c in componentes]
                    )
                )
                for c in componentes:
                    c.responsabilidade = responsabilidades.get(c.nome, "")
            except LLMError as e:
                warnings.append(
                    f"LLM indisponível — relações semânticas e responsabilidades omitidas. ({e})"
                )

        return EstruturaArquitetural(
            componentes=componentes,
            relacoes=herancas + relacoes_llm,
            warnings=warnings,
            linguagem="python",
        )

    def _detectar_linguagem(self, codigo: str) -> str:
        """Heurística: pontua cada linguagem por número de padrões que casam."""
        scores = {}
        for linguagem, padroes in _LINGUAGENS:
            casados = sum(
                1 for p in padroes if re.search(p, codigo, re.MULTILINE)
            )
            if casados > 0:
                scores[linguagem] = casados

        if not scores:
            return "desconhecida"

        return max(scores, key=lambda k: scores[k])
