# Testes da rota POST /impacto/analisar (US IA-06).

import pytest
from fastapi.testclient import TestClient

import main
from app.adapters.driving.http.impacto_routes import get_impacto_service
from app.application.services.impacto_service_impl import ImpactoServiceImpl


@pytest.fixture
def client():
    main.app.dependency_overrides[get_impacto_service] = lambda: ImpactoServiceImpl()
    yield TestClient(main.app)
    main.app.dependency_overrides.clear()


def test_post_alvo_invalido_retorna_400(client):
    resp = client.post(
        "/impacto/analisar",
        json={"alvo": {"nome_simbolo": "", "modulo": "x"}, "testes": {}},
    )
    assert resp.status_code == 400


def test_post_sem_testes_retorna_relatorio_vazio(client):
    resp = client.post(
        "/impacto/analisar",
        json={"alvo": {"nome_simbolo": "UserService", "modulo": "app.x"}, "testes": {}},
    )
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_afetados"] == 0
    assert body["por_confianca"] == {"alta": 0, "media": 0, "baixa": 0}


def test_post_classifica_corretamente(client):
    payload = {
        "alvo": {"nome_simbolo": "UserService", "modulo": "app.services.user_service"},
        "testes": {
            "tests/test_a.py": "from app.services.user_service import UserService\n\ndef test_a():\n    UserService()\n",
            "tests/test_b.py": "def test_b():\n    assert True\n",
        },
    }
    resp = client.post("/impacto/analisar", json=payload)
    assert resp.status_code == 200
    body = resp.json()
    assert body["total_afetados"] == 1
    assert body["afetados"][0]["arquivo"] == "tests/test_a.py"
    assert body["afetados"][0]["confianca"] == "alta"
    assert "tests/test_b.py" in body["sem_impacto"]
