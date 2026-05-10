# Testes do ImpactoServiceImpl (US IA-06).

import pytest

from app.application.services.impacto_service_impl import ImpactoServiceImpl
from app.domain.entidades.matriz_impacto import AlvoRefatoracao, NivelConfianca
from app.domain.excecoes import ImpactoInvalidoError


@pytest.fixture
def service():
    return ImpactoServiceImpl()


def test_alvo_sem_simbolo_dispara_erro(service):
    with pytest.raises(ImpactoInvalidoError):
        service.analisar(alvo=AlvoRefatoracao(nome_simbolo=""), testes={})


def test_relatorio_vazio_quando_nao_ha_testes(service):
    rel = service.analisar(alvo=AlvoRefatoracao(nome_simbolo="UserService"), testes={})
    assert rel.total_afetados == 0
    assert rel.por_confianca == {"alta": 0, "media": 0, "baixa": 0}
    assert rel.sem_impacto == ()


def test_teste_que_nao_referencia_alvo_e_sem_impacto(service):
    codigo = """
def test_soma():
    assert 1 + 1 == 2
"""
    rel = service.analisar(
        alvo=AlvoRefatoracao(nome_simbolo="UserService", modulo="app.services.user_service"),
        testes={"tests/test_soma.py": codigo},
    )
    assert rel.total_afetados == 0
    assert "tests/test_soma.py" in rel.sem_impacto


def test_import_direto_e_uso_da_alta_confianca(service):
    codigo = """
from app.services.user_service import UserService

def test_user():
    s = UserService()
    assert s is not None
"""
    rel = service.analisar(
        alvo=AlvoRefatoracao(nome_simbolo="UserService", modulo="app.services.user_service"),
        testes={"tests/test_user.py": codigo},
    )
    assert rel.total_afetados == 1
    assert rel.afetados[0].confianca == NivelConfianca.ALTA
    assert rel.afetados[0].referencias_diretas >= 1


def test_import_direto_sem_uso_da_media_confianca(service):
    codigo = """
from app.services.user_service import UserService  # noqa

def test_outro():
    assert True
"""
    rel = service.analisar(
        alvo=AlvoRefatoracao(nome_simbolo="UserService", modulo="app.services.user_service"),
        testes={"tests/test_x.py": codigo},
    )
    assert rel.total_afetados == 1
    assert rel.afetados[0].confianca == NivelConfianca.MEDIA


def test_import_wildcard_da_baixa_confianca(service):
    codigo = """
from app.services.user_service import *

def test_x():
    assert True
"""
    rel = service.analisar(
        alvo=AlvoRefatoracao(nome_simbolo="UserService", modulo="app.services.user_service"),
        testes={"tests/test_w.py": codigo},
    )
    assert rel.total_afetados == 1
    assert rel.afetados[0].confianca == NivelConfianca.BAIXA


def test_import_outro_simbolo_do_modulo_baixa_quando_sem_uso(service):
    codigo = """
from app.services.user_service import OutroSimbolo

def test_y():
    OutroSimbolo()
"""
    rel = service.analisar(
        alvo=AlvoRefatoracao(nome_simbolo="UserService", modulo="app.services.user_service"),
        testes={"tests/test_y.py": codigo},
    )
    assert rel.total_afetados == 1
    assert rel.afetados[0].confianca == NivelConfianca.BAIXA


def test_patch_em_string_com_import_direto_aumenta_confianca(service):
    codigo = """
from app.services.user_service import UserService
from unittest.mock import patch

@patch('app.services.user_service.UserService')
def test_mock(mock_user):
    pass
"""
    rel = service.analisar(
        alvo=AlvoRefatoracao(nome_simbolo="UserService", modulo="app.services.user_service"),
        testes={"tests/test_mock.py": codigo},
    )
    assert rel.total_afetados == 1
    assert rel.afetados[0].confianca == NivelConfianca.ALTA


def test_codigo_invalido_vai_para_nao_parseaveis(service):
    codigo_quebrado = "def x(:\n    pass"
    rel = service.analisar(
        alvo=AlvoRefatoracao(nome_simbolo="UserService"),
        testes={"tests/test_q.py": codigo_quebrado},
    )
    assert rel.total_afetados == 0
    assert "tests/test_q.py" in rel.nao_parseaveis


def test_to_dict_ordena_por_confianca(service):
    codigo_alta = """
from app.services.user_service import UserService

def test_a():
    UserService()
"""
    codigo_baixa = """
from app.services.user_service import *

def test_b():
    pass
"""
    rel = service.analisar(
        alvo=AlvoRefatoracao(nome_simbolo="UserService", modulo="app.services.user_service"),
        testes={
            "tests/test_b.py": codigo_baixa,
            "tests/test_a.py": codigo_alta,
        },
    )
    d = rel.to_dict()
    assert d["total_afetados"] == 2
    assert d["afetados"][0]["confianca"] == "alta"
    assert d["afetados"][1]["confianca"] == "baixa"
