from app.application.services.saude_service_impl import SaudeServiceImpl
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMFake


class _ProvedorLLMReal:
    """Stub que simula um adapter real (não-Fake) para testes."""
    pass


class _CacheStub:
    pass


class _BancoStub:
    pass


def test_saude_com_apenas_fake_llm_resulta_degraded():
    service = SaudeServiceImpl(provedor_llm=AdaptadorLLMFake())
    s = service.verificar_saude()

    assert s.status == "degraded"
    assert s.checks["provedor_llm"].status == "degraded"
    assert s.checks["provedor_llm"].detalhe["tipo"] == "AdaptadorLLMFake"
    assert s.checks["cache"].status == "not_configured"
    assert s.checks["banco"].status == "not_configured"


def test_saude_com_provedor_real_e_sem_cache_banco_resulta_healthy():
    real = _ProvedorLLMReal()
    service = SaudeServiceImpl(provedor_llm=real)
    s = service.verificar_saude()

    assert s.status == "healthy"
    assert s.checks["provedor_llm"].status == "healthy"
    assert s.checks["provedor_llm"].detalhe["tipo"] == "_ProvedorLLMReal"
    assert s.checks["cache"].status == "not_configured"
    assert s.checks["banco"].status == "not_configured"


def test_saude_sem_provedor_llm_resulta_unhealthy():
    service = SaudeServiceImpl(provedor_llm=None)
    s = service.verificar_saude()

    assert s.status == "unhealthy"
    assert s.checks["provedor_llm"].status == "unhealthy"


def test_saude_com_todos_subsistemas_resulta_healthy():
    service = SaudeServiceImpl(
        provedor_llm=_ProvedorLLMReal(),
        cache_adapter=_CacheStub(),
        banco_adapter=_BancoStub(),
    )
    s = service.verificar_saude()

    assert s.status == "healthy"
    assert s.checks["cache"].status == "healthy"
    assert s.checks["banco"].status == "healthy"


def test_saude_responde_em_menos_de_200ms():
    service = SaudeServiceImpl(provedor_llm=AdaptadorLLMFake())
    s = service.verificar_saude()
    assert s.tempo_ms < 200, f"tempo_ms={s.tempo_ms} excedeu 200ms"
