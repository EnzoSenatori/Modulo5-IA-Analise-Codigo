# Testes da rota REST /casos-uso (US IA-03).

import base64

import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.adapters.driving.http.caso_de_uso_routes import get_caso_uso_service
from app.application.services.caso_de_uso_service_impl import CasoDeUsoServiceImpl


@pytest.fixture
def cliente():
    service = CasoDeUsoServiceImpl()
    main_module.app.dependency_overrides[get_caso_uso_service] = lambda: service
    yield TestClient(main_module.app)
    main_module.app.dependency_overrides.clear()


def test_post_extrair_de_texto_devolve_diagrama(cliente):
    payload = {
        "texto": "Como Cliente, eu quero comprar.\nComo Atendente, eu quero atender.",
    }
    r = cliente.post("/casos-uso/extrair-de-texto", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["total_atores"] == 2
    assert body["total_casos"] == 2
    assert "flowchart" in body["mermaid"]


def test_post_extrair_inclui_ambiguidades(cliente):
    payload = {"texto": "O sistema deve ser rapido, etc."}
    r = cliente.post("/casos-uso/extrair-de-texto", json=payload)
    body = r.json()
    assert body["total_ambiguidades"] >= 1


def test_post_texto_vazio_400(cliente):
    r = cliente.post("/casos-uso/extrair-de-texto", json={"texto": ""})
    assert r.status_code == 400


def test_post_formato_invalido_400(cliente):
    r = cliente.post("/casos-uso/extrair-de-texto", json={
        "texto": "qualquer", "formato": "docx",
    })
    assert r.status_code == 400


def test_post_pdf_base64_invalido_400(cliente):
    r = cliente.post("/casos-uso/extrair-de-pdf", json={
        "conteudo_base64": "isso nao eh base64 valido!!!@#",
    })
    assert r.status_code == 400


def test_post_pdf_bytes_invalidos_400(cliente):
    payload_b64 = base64.b64encode(b"isso nao e PDF").decode("ascii")
    r = cliente.post("/casos-uso/extrair-de-pdf", json={"conteudo_base64": payload_b64})
    assert r.status_code == 400
