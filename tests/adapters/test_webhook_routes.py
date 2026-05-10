# Testes da rota POST /webhook/github (US IA-11).

import hashlib
import hmac
import importlib
import json

import pytest


@pytest.fixture
def cliente(monkeypatch, tmp_path):
    monkeypatch.setenv("GITHUB_WEBHOOK_SECRET", "supersecret")
    monkeypatch.setenv("ADAPTADOR_GITHUB", "fake")
    monkeypatch.setenv("ADAPTADOR_NOTIFICADOR_PR", "fake")
    monkeypatch.setenv("WEBHOOKS_SQLITE_PATH", str(tmp_path / "wh.db"))
    monkeypatch.setenv("GEMINI_API_KEY", "")  # forca AdaptadorLLMFake

    from app.config import composition_root, settings
    importlib.reload(settings)
    importlib.reload(composition_root)

    import main as main_module
    importlib.reload(main_module)

    from fastapi.testclient import TestClient
    return TestClient(main_module.app)


def _assinar(corpo_bytes: bytes, secret: str = "supersecret") -> str:
    return "sha256=" + hmac.new(secret.encode(), corpo_bytes, hashlib.sha256).hexdigest()


def _payload_pr(action="opened", pr=99, head="aaaaaaa", base="bbbbbbb"):
    return {
        "action": action,
        "pull_request": {
            "number": pr,
            "head": {"sha": head},
            "base": {"sha": base},
        },
        "repository": {"full_name": "o/r"},
    }


def test_webhook_assinatura_invalida_401(cliente):
    body = json.dumps(_payload_pr()).encode()
    r = cliente.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": "sha256=" + "0" * 64,
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 401


def test_webhook_pr_aberto_aceita_e_agenda_processamento(cliente):
    body = json.dumps(_payload_pr()).encode()
    r = cliente.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _assinar(body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200
    body_json = r.json()
    assert body_json["status"] == "accepted"
    assert "evento_id" in body_json


def test_webhook_pr_fechado_eh_ignorado(cliente):
    body = json.dumps(_payload_pr(action="closed")).encode()
    r = cliente.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _assinar(body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"


def test_webhook_ping_eh_ignorado(cliente):
    body = json.dumps({"zen": "Speak like a human."}).encode()
    r = cliente.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _assinar(body),
            "X-GitHub-Event": "ping",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 200
    assert r.json()["status"] == "ignored"
    assert r.json()["tipo"] == "ping"


def test_webhook_payload_nao_json_400(cliente):
    body = b"isso nao eh json"
    r = cliente.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _assinar(body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    assert r.status_code == 400


def test_listar_eventos_via_get(cliente):
    body = json.dumps(_payload_pr()).encode()
    cliente.post(
        "/webhook/github",
        content=body,
        headers={
            "X-Hub-Signature-256": _assinar(body),
            "X-GitHub-Event": "pull_request",
            "Content-Type": "application/json",
        },
    )
    r = cliente.get("/webhook/github/eventos", params={"repositorio": "o/r"})
    assert r.status_code == 200
    eventos = r.json()["eventos"]
    assert len(eventos) >= 1
    assert eventos[0]["repositorio"] == "o/r"
