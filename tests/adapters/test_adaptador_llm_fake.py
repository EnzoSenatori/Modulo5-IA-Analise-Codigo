import pytest

from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMFake
from app.domain.entidades.relacao import Relacao
from app.domain.excecoes import LLMError


def test_fake_retorna_resposta_pre_programada():
    fake = AdaptadorLLMFake(
        responsabilidades={"Calc": "Soma."},
        relacoes=[Relacao(origem="Calc", destino="Logger", tipo="usa", fonte="llm")],
    )
    resp, rels = fake.inferir_relacoes_e_responsabilidades("código", ["Calc", "Logger"])
    assert resp == {"Calc": "Soma."}
    assert rels[0].origem == "Calc"


def test_fake_pode_simular_falha():
    fake = AdaptadorLLMFake(erro=LLMError("simulado"))
    with pytest.raises(LLMError):
        fake.inferir_relacoes_e_responsabilidades("c", ["X"])


def test_fake_default_retorna_vazio():
    fake = AdaptadorLLMFake()
    resp, rels = fake.inferir_relacoes_e_responsabilidades("c", ["X"])
    assert resp == {}
    assert rels == []


def test_fake_ping_default_retorna_ok():
    fake = AdaptadorLLMFake()
    ok, msg = fake.ping()
    assert ok is True
    assert msg == "fake-ok"


def test_fake_ping_pode_simular_falha():
    fake = AdaptadorLLMFake(ping_falha="simulado: gemini fora")
    ok, msg = fake.ping(timeout_ms=100)
    assert ok is False
    assert "simulado" in msg
