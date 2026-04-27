import json
import pytest

from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMGemini
from app.domain.excecoes import LLMError


class _GeminiMockavel(AdaptadorLLMGemini):
    """Subclasse de teste — substitui a chamada de rede por uma resposta canned."""
    def __init__(self, resposta_bruta: str = "", excecao: Exception | None = None):
        # bypass do __init__ pai (que exige api_key) — só pra teste
        self._resposta = resposta_bruta
        self._excecao = excecao

    def _chamar_modelo(self, prompt: str) -> str:
        if self._excecao is not None:
            raise self._excecao
        return self._resposta


def test_gemini_parsing_json_valido():
    bruto = json.dumps({
        "responsabilidades": {"Calc": "Faz contas."},
        "relacoes": [{"origem": "Calc", "destino": "Logger", "tipo": "usa"}],
    })
    g = _GeminiMockavel(resposta_bruta=bruto)
    resp, rels = g.inferir_relacoes_e_responsabilidades("código", ["Calc", "Logger"])
    assert resp == {"Calc": "Faz contas."}
    assert len(rels) == 1
    r = rels[0]
    assert r.origem == "Calc" and r.destino == "Logger"
    assert r.tipo == "usa" and r.fonte == "llm"


def test_gemini_filtra_classe_alucinada():
    bruto = json.dumps({
        "responsabilidades": {"Calc": "ok", "Fantasma": "inventada"},
        "relacoes": [
            {"origem": "Calc", "destino": "Fantasma", "tipo": "usa"},
            {"origem": "Calc", "destino": "Logger", "tipo": "usa"},
        ],
    })
    g = _GeminiMockavel(resposta_bruta=bruto)
    resp, rels = g.inferir_relacoes_e_responsabilidades("c", ["Calc", "Logger"])
    assert "Fantasma" not in resp
    assert resp["Calc"] == "ok"
    assert len(rels) == 1
    assert rels[0].destino == "Logger"


def test_gemini_filtra_tipo_invalido():
    bruto = json.dumps({
        "responsabilidades": {},
        "relacoes": [
            {"origem": "A", "destino": "B", "tipo": "magico"},
            {"origem": "A", "destino": "B", "tipo": "depende_de"},
        ],
    })
    g = _GeminiMockavel(resposta_bruta=bruto)
    _, rels = g.inferir_relacoes_e_responsabilidades("c", ["A", "B"])
    assert len(rels) == 1
    assert rels[0].tipo == "depende_de"


def test_gemini_json_malformado_levanta_llm_error():
    g = _GeminiMockavel(resposta_bruta="isso { não é } json")
    with pytest.raises(LLMError):
        g.inferir_relacoes_e_responsabilidades("c", ["X"])


def test_gemini_resposta_sem_chaves_obrigatorias_levanta_llm_error():
    g = _GeminiMockavel(resposta_bruta=json.dumps({"foo": "bar"}))
    with pytest.raises(LLMError):
        g.inferir_relacoes_e_responsabilidades("c", ["X"])


def test_gemini_excecao_de_rede_levanta_llm_error():
    g = _GeminiMockavel(excecao=TimeoutError("rede caiu"))
    with pytest.raises(LLMError):
        g.inferir_relacoes_e_responsabilidades("c", ["X"])
