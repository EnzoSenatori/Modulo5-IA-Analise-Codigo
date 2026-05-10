# Testes da entidade EventoCI (US IA-11).

from app.domain.entidades.evento_ci import (
    ALVOS_PROCESSAMENTO,
    EventoCI,
    TipoEventoGitHub,
    construir_evento_de_payload,
)


def test_tipo_a_partir_de_header_e_action():
    assert (
        TipoEventoGitHub.from_header_e_action("pull_request", "opened")
        == TipoEventoGitHub.PULL_REQUEST_OPENED
    )
    assert (
        TipoEventoGitHub.from_header_e_action("pull_request", "synchronize")
        == TipoEventoGitHub.PULL_REQUEST_SYNCHRONIZE
    )
    assert TipoEventoGitHub.from_header_e_action("ping", "") == TipoEventoGitHub.PING
    assert (
        TipoEventoGitHub.from_header_e_action("issues", "opened") == TipoEventoGitHub.OUTRO
    )


def test_construir_evento_de_payload_pr_aberto():
    payload = {
        "action": "opened",
        "pull_request": {
            "number": 42,
            "head": {"sha": "abcdef1"},
            "base": {"sha": "1234567"},
        },
        "repository": {"full_name": "fnavai/Modulo5-Interface-e-Nuvem"},
    }
    evento = construir_evento_de_payload("pull_request", payload)
    assert evento.tipo == TipoEventoGitHub.PULL_REQUEST_OPENED
    assert evento.repositorio == "fnavai/Modulo5-Interface-e-Nuvem"
    assert evento.pr_numero == 42
    assert evento.pr_head_sha == "abcdef1"
    assert evento.pr_base_sha == "1234567"
    assert evento.deve_processar is True


def test_construir_evento_de_payload_pr_fechado_nao_processa():
    payload = {"action": "closed", "pull_request": {"number": 1, "head": {"sha": "x"}, "base": {"sha": "y"}},
               "repository": {"full_name": "o/r"}}
    evento = construir_evento_de_payload("pull_request", payload)
    assert evento.tipo == TipoEventoGitHub.PULL_REQUEST_FECHADO
    assert evento.deve_processar is False


def test_evento_outro_nao_processa():
    payload = {"action": "opened", "repository": {"full_name": "o/r"}}
    evento = construir_evento_de_payload("issues", payload)
    assert evento.tipo == TipoEventoGitHub.OUTRO
    assert evento.deve_processar is False


def test_alvos_processamento_inclui_eventos_certos():
    assert TipoEventoGitHub.PULL_REQUEST_OPENED in ALVOS_PROCESSAMENTO
    assert TipoEventoGitHub.PULL_REQUEST_SYNCHRONIZE in ALVOS_PROCESSAMENTO
    assert TipoEventoGitHub.PULL_REQUEST_REOPENED in ALVOS_PROCESSAMENTO
    assert TipoEventoGitHub.PULL_REQUEST_FECHADO not in ALVOS_PROCESSAMENTO
    assert TipoEventoGitHub.PING not in ALVOS_PROCESSAMENTO
