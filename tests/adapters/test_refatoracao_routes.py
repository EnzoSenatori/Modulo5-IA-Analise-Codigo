# Testes da rota REST /refatoracao/sugerir (US IA-05).

import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.adapters.driving.http.refatoracao_routes import get_refatoracao_service
from app.application.services.refatoracao_service_impl import RefatoracaoServiceImpl


@pytest.fixture
def cliente():
    service = RefatoracaoServiceImpl()
    main_module.app.dependency_overrides[get_refatoracao_service] = lambda: service
    yield TestClient(main_module.app)
    main_module.app.dependency_overrides.clear()


def test_post_sugerir_devolve_relatorio(cliente):
    payload = {"codigo": "def f(x=[]):\n    return 999\n"}
    r = cliente.post("/refatoracao/sugerir", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["total"] >= 2  # default_mutavel + numero_magico
    assert "resumo_por_esforco" in body
    categorias = {s["categoria"] for s in body["sugestoes"]}
    assert "default_mutavel" in categorias
    assert "numero_magico" in categorias


def test_post_sugerir_codigo_vazio_400(cliente):
    r = cliente.post("/refatoracao/sugerir", json={"codigo": ""})
    assert r.status_code == 400


def test_post_sugerir_codigo_invalido_400(cliente):
    r = cliente.post("/refatoracao/sugerir", json={"codigo": "def f(:"})
    assert r.status_code == 400


def test_resposta_inclui_snippet_antes_e_depois(cliente):
    payload = {"codigo": "def f(x=[]):\n    return 1\n"}
    body = cliente.post("/refatoracao/sugerir", json=payload).json()
    primeira = body["sugestoes"][0]
    assert "snippet_antes" in primeira
    assert "snippet_depois" in primeira
    assert "esforco" in primeira
    assert "linha_inicio" in primeira


def test_request_repetido_devolve_mesma_resposta_byte_a_byte(cliente):
    payload = {"codigo": "def f(x=[]):\n    return 999\n"}
    r1 = cliente.post("/refatoracao/sugerir", json=payload).json()
    r2 = cliente.post("/refatoracao/sugerir", json=payload).json()
    assert r1 == r2


def test_codigo_limpo_devolve_total_zero(cliente):
    payload = {"codigo": "def soma(a, b):\n    return a + b\n"}
    body = cliente.post("/refatoracao/sugerir", json=payload).json()
    assert body["total"] == 0
