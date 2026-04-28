import time
import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.application.services.saude_service_impl import SaudeServiceImpl
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMFake
from app.adapters.driving.http.saude_routes import get_saude_service


@pytest.fixture
def client_com_fake_llm():
    """Sobrescreve a dependência do FastAPI para usar Fake LLM."""
    service = SaudeServiceImpl(provedor_llm=AdaptadorLLMFake())
    main_module.app.dependency_overrides[get_saude_service] = lambda: service
    yield TestClient(main_module.app)
    main_module.app.dependency_overrides.clear()


def test_get_saude_ia_retorna_estrutura_esperada(client_com_fake_llm):
    r = client_com_fake_llm.get("/saude/ia")
    assert r.status_code == 200
    body = r.json()

    assert "status" in body
    assert body["status"] in {"healthy", "degraded", "unhealthy"}
    assert "checks" in body
    assert "tempo_ms" in body

    checks = body["checks"]
    assert set(checks.keys()) == {"provedor_llm", "cache", "banco"}
    for nome, c in checks.items():
        assert "status" in c
        assert "detalhe" in c


def test_get_saude_ia_marca_fake_como_degraded(client_com_fake_llm):
    r = client_com_fake_llm.get("/saude/ia")
    body = r.json()
    assert body["status"] == "degraded"
    assert body["checks"]["provedor_llm"]["status"] == "degraded"
    assert body["checks"]["provedor_llm"]["detalhe"]["tipo"] == "AdaptadorLLMFake"


def test_get_saude_ia_cache_e_banco_not_configured(client_com_fake_llm):
    r = client_com_fake_llm.get("/saude/ia")
    body = r.json()
    assert body["checks"]["cache"]["status"] == "not_configured"
    assert body["checks"]["banco"]["status"] == "not_configured"


def test_get_saude_ia_responde_em_menos_de_200ms(client_com_fake_llm):
    inicio = time.perf_counter()
    r = client_com_fake_llm.get("/saude/ia")
    elapsed_ms = (time.perf_counter() - inicio) * 1000

    assert r.status_code == 200
    body = r.json()
    # Tempo medido pelo service (interno)
    assert body["tempo_ms"] < 200, f"tempo_ms reportado={body['tempo_ms']}"
    # Tempo medido pelo cliente (round-trip TestClient — sem rede real)
    assert elapsed_ms < 200, f"round-trip do client={elapsed_ms:.1f}ms"


def test_get_saude_ia_endpoint_registrado_em_main():
    paths = [r.path for r in main_module.app.routes]
    assert "/saude/ia" in paths


def test_get_saude_ia_deep_true_executa_ping(client_com_fake_llm):
    """Modo deep com Fake ok deve incluir o ping no detalhe e seguir degraded."""
    r = client_com_fake_llm.get("/saude/ia?deep=true")
    assert r.status_code == 200
    body = r.json()
    assert body["checks"]["provedor_llm"]["detalhe"].get("ping") == "fake-ok"
    assert body["status"] == "degraded"


def test_get_saude_ia_deep_marca_unhealthy_quando_ping_falha():
    """Override do service com Fake que falha no ping."""
    service = SaudeServiceImpl(
        provedor_llm=AdaptadorLLMFake(ping_falha="gemini timeout"),
    )
    main_module.app.dependency_overrides[get_saude_service] = lambda: service
    try:
        r = TestClient(main_module.app).get("/saude/ia?deep=true")
        assert r.status_code == 200
        body = r.json()
        assert body["status"] == "unhealthy"
        assert body["checks"]["provedor_llm"]["status"] == "unhealthy"
        assert "gemini timeout" in body["checks"]["provedor_llm"]["detalhe"]["ping"]
    finally:
        main_module.app.dependency_overrides.clear()
