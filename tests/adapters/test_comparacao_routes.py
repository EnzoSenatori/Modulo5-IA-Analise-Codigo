# Testes da rota POST /comparacao/diagrama (US IA-10).

import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMFake
from app.adapters.driving.http.comparacao_routes import get_comparacao_service
from app.application.services.comparacao_diagrama_service_impl import (
    ComparacaoDiagramaServiceImpl,
)
from app.application.services.estrutura_service_impl import EstruturaServiceImpl


@pytest.fixture
def cliente():
    estrutura = EstruturaServiceImpl(
        parser_codigo=AdaptadorParserPython(),
        provedor_llm=AdaptadorLLMFake(),
    )
    service = ComparacaoDiagramaServiceImpl(estrutura_service=estrutura)
    main_module.app.dependency_overrides[get_comparacao_service] = lambda: service
    yield TestClient(main_module.app)
    main_module.app.dependency_overrides.clear()


def test_post_compara_dois_codigos_e_devolve_diff(cliente):
    antes = "class A:\n    def foo(self): pass\n"
    depois = "class A:\n    def foo(self): pass\n    def bar(self): pass\nclass B:\n    pass\n"
    r = cliente.post("/comparacao/diagrama", json={"codigo_antes": antes, "codigo_depois": depois})
    assert r.status_code == 200
    body = r.json()
    assert body["tem_mudancas"] is True
    assert body["resumo"]["componentes_adicionados"] == 1
    assert body["resumo"]["componentes_alterados"] == 1
    assert "mermaid" in body
    assert "classDef adicionado" in body["mermaid"]


def test_post_dois_codigos_iguais_sem_mudancas(cliente):
    codigo = "class X:\n    def foo(self): pass\n"
    r = cliente.post("/comparacao/diagrama", json={"codigo_antes": codigo, "codigo_depois": codigo})
    assert r.status_code == 200
    body = r.json()
    assert body["tem_mudancas"] is False
    assert body["resumo"]["componentes_adicionados"] == 0


def test_post_codigo_invalido_400(cliente):
    r = cliente.post("/comparacao/diagrama", json={"codigo_antes": "class A:", "codigo_depois": "class A:\n    pass"})
    assert r.status_code == 400


def test_post_body_incompleto_422(cliente):
    r = cliente.post("/comparacao/diagrama", json={"codigo_antes": "class A:\n    pass"})
    assert r.status_code == 422


def test_resposta_inclui_componentes_removidos(cliente):
    antes = "class A:\n    pass\nclass B:\n    pass\n"
    depois = "class A:\n    pass\n"
    r = cliente.post("/comparacao/diagrama", json={"codigo_antes": antes, "codigo_depois": depois})
    assert r.status_code == 200
    nomes = {c["nome"] for c in r.json()["componentes_removidos"]}
    assert nomes == {"B"}
