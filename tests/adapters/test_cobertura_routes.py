# Testes da rota REST /cobertura (US IA-07).

import pytest
from fastapi.testclient import TestClient

import main as main_module
from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.persistence.repositorio_ignorados_sqlite import (
    RepositorioIgnoradosSQLite,
)
from app.adapters.driving.http.cobertura_routes import get_cobertura_service
from app.application.services.cobertura_service_impl import CoberturaServiceImpl


@pytest.fixture
def cliente(tmp_path):
    repo = RepositorioIgnoradosSQLite(str(tmp_path / "ignorados.db"))
    service = CoberturaServiceImpl(parser=AdaptadorParserPython(), repositorio_ignorados=repo)
    main_module.app.dependency_overrides[get_cobertura_service] = lambda: service
    yield TestClient(main_module.app)
    main_module.app.dependency_overrides.clear()
    repo.fechar()


def test_post_analisar_devolve_mapa(cliente):
    payload = {
        "codigo_producao": "class UserService:\n    def login(self): pass\nclass Helper:\n    def x(self): pass\n",
        "codigo_testes": "class TestUserService:\n    def test_login(self): pass\n",
    }
    r = cliente.post("/cobertura/analisar", json=payload)
    assert r.status_code == 200
    body = r.json()
    assert body["resumo"]["cobertos"] == 1
    assert body["resumo"]["sem_cobertura"] == 1
    # Helper aparece em sem_cobertura
    sem = body["sem_cobertura"]
    assert sem[0]["componente"]["nome"] == "Helper"
    assert "criticidade_score" in sem[0]


def test_post_analisar_com_codigo_vazio_400(cliente):
    r = cliente.post("/cobertura/analisar", json={"codigo_producao": "", "codigo_testes": ""})
    assert r.status_code == 400


def test_post_analisar_codigo_prod_invalido_400(cliente):
    r = cliente.post("/cobertura/analisar", json={"codigo_producao": "class A:", "codigo_testes": ""})
    assert r.status_code == 400


def test_marcar_ignorar_201(cliente):
    r = cliente.post("/cobertura/ignorar", json={
        "nome": "Legacy", "motivo": "codigo legado", "marcado_por": "alice",
    })
    assert r.status_code == 201
    assert r.json()["nome"] == "Legacy"


def test_marcar_ignorar_motivo_vazio_400(cliente):
    r = cliente.post("/cobertura/ignorar", json={
        "nome": "Legacy", "motivo": "", "marcado_por": "alice",
    })
    assert r.status_code == 400


def test_listar_ignorados(cliente):
    cliente.post("/cobertura/ignorar", json={"nome": "A", "motivo": "x", "marcado_por": "alice"})
    cliente.post("/cobertura/ignorar", json={"nome": "B", "motivo": "y", "marcado_por": "bob"})
    r = cliente.get("/cobertura/ignorados")
    assert r.status_code == 200
    nomes = {i["nome"] for i in r.json()["ignorados"]}
    assert nomes == {"A", "B"}


def test_desmarcar_ignorar_204_e_404(cliente):
    cliente.post("/cobertura/ignorar", json={"nome": "X", "motivo": "x", "marcado_por": "alice"})
    r = cliente.delete("/cobertura/ignorar/X")
    assert r.status_code == 204
    r = cliente.delete("/cobertura/ignorar/X")
    assert r.status_code == 404


def test_ignorar_filtra_componente_da_analise(cliente):
    cliente.post("/cobertura/ignorar", json={
        "nome": "Legacy", "motivo": "x", "marcado_por": "alice",
    })
    payload = {
        "codigo_producao": "class A:\n    pass\nclass Legacy:\n    pass\n",
        "codigo_testes": "class TestA:\n    def test_x(self): pass\n",
    }
    r = cliente.post("/cobertura/analisar", json=payload)
    body = r.json()
    assert body["resumo"]["ignorados"] == 1
    assert body["percentual_cobertura"] == 100.0


def test_resposta_inclui_warnings_quando_codigo_teste_vazio(cliente):
    payload = {"codigo_producao": "class A:\n    pass\n", "codigo_testes": ""}
    r = cliente.post("/cobertura/analisar", json=payload)
    body = r.json()
    assert any("vazio" in w.lower() for w in body["warnings"])
