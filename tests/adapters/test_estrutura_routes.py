import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.application.services.estrutura_service_impl import EstruturaServiceImpl
from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMFake
from app.domain.entidades.relacao import Relacao
from app.adapters.driving.http.estrutura_routes import get_estrutura_service


@pytest.fixture
def client_com_fake_llm():
    """Sobrescreve a dependência do FastAPI para usar LLM fake."""
    fake_llm = AdaptadorLLMFake(
        responsabilidades={"Calc": "Faz contas."},
        relacoes=[Relacao(origem="Calc", destino="Logger", tipo="usa", fonte="llm")],
    )
    service = EstruturaServiceImpl(
        parser_codigo=AdaptadorParserPython(),
        provedor_llm=fake_llm,
    )
    main_module.app.dependency_overrides[get_estrutura_service] = lambda: service
    yield TestClient(main_module.app)
    main_module.app.dependency_overrides.clear()


def test_post_diagrama_caminho_feliz(client_com_fake_llm):
    codigo = "class Calc:\n    def somar(self, a, b): return a + b\nclass Logger:\n    def log(self): pass\n"
    r = client_com_fake_llm.post("/estrutura/diagrama", json={"codigo": codigo})
    assert r.status_code == 200
    body = r.json()
    assert "componentes" in body
    assert "relacoes" in body
    assert "mermaid" in body
    assert "warnings" in body
    assert any(c["nome"] == "Calc" for c in body["componentes"])
    assert "classDiagram" in body["mermaid"]


def test_post_diagrama_body_sem_codigo(client_com_fake_llm):
    r = client_com_fake_llm.post("/estrutura/diagrama", json={})
    assert r.status_code == 422


def test_post_diagrama_codigo_invalido_400(client_com_fake_llm):
    r = client_com_fake_llm.post("/estrutura/diagrama", json={"codigo": "def x(:\n pass"})
    assert r.status_code == 400
    assert "detail" in r.json()


def test_post_diagrama_codigo_vazio_400(client_com_fake_llm):
    r = client_com_fake_llm.post("/estrutura/diagrama", json={"codigo": "   "})
    assert r.status_code == 400
