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


def test_gemini_api_key_vazia_levanta_value_error():
    """Cobre o branch de validação no __init__ do AdaptadorLLMGemini."""
    with pytest.raises(ValueError, match="api_key"):
        AdaptadorLLMGemini(api_key="")


def test_gemini_init_com_api_key_constroi_client_sem_io():
    """O __init__ + _inicializar_modelo cria o cliente sem fazer chamada de rede."""
    g = AdaptadorLLMGemini(api_key="fake-key-just-for-init", modelo="gemini-2.0-flash", timeout=5)
    assert g._modelo is not None
    assert g._modelo_nome == "gemini-2.0-flash"
    assert g._timeout == 5


class _GeminiPingMockavel(AdaptadorLLMGemini):
    """Subclasse de teste que substitui só o _executar_ping."""
    def __init__(self, sleep_s: float = 0.0, raise_exc: Exception | None = None):
        # bypass __init__ pai
        self._modelo_nome = "gemini-2.0-flash"
        self._sleep_s = sleep_s
        self._raise = raise_exc

    def _executar_ping(self):
        import time as _t
        if self._raise is not None:
            raise self._raise
        if self._sleep_s > 0:
            _t.sleep(self._sleep_s)


def test_gemini_ping_caminho_feliz():
    g = _GeminiPingMockavel()
    ok, msg = g.ping(timeout_ms=200)
    assert ok is True
    assert "ok em" in msg


def test_gemini_ping_estoura_timeout():
    g = _GeminiPingMockavel(sleep_s=0.5)  # 500ms > 100ms timeout
    ok, msg = g.ping(timeout_ms=100)
    assert ok is False
    assert "timeout" in msg


def test_gemini_ping_captura_excecao_de_rede():
    g = _GeminiPingMockavel(raise_exc=ConnectionError("rede caiu"))
    ok, msg = g.ping()
    assert ok is False
    assert "erro" in msg
    assert "rede caiu" in msg


def test_gemini_montar_prompt_inclui_codigo_e_classes():
    """Cobre _montar_prompt diretamente — anteriormente só era testado por contra-prova."""
    g = _GeminiPingMockavel()
    prompt = g._montar_prompt("class X: pass", ["X", "Y"])
    assert "class X: pass" in prompt
    assert "- X" in prompt
    assert "- Y" in prompt
    assert "JSON válido" in prompt


def test_gemini_montar_prompt_lida_com_lista_vazia():
    g = _GeminiPingMockavel()
    prompt = g._montar_prompt("def x(): pass", [])
    assert "(nenhuma)" in prompt
