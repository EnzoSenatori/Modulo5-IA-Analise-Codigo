# Testes do CoberturaServiceImpl (US IA-07).

import pytest

from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.persistence.repositorio_ignorados_sqlite import (
    RepositorioIgnoradosSQLite,
)
from app.application.services.cobertura_service_impl import CoberturaServiceImpl
from app.domain.excecoes import CoberturaInvalidaError, IgnorarInvalidoError


@pytest.fixture
def cenario(tmp_path):
    repo = RepositorioIgnoradosSQLite(str(tmp_path / "ignorados.db"))
    service = CoberturaServiceImpl(parser=AdaptadorParserPython(), repositorio_ignorados=repo)
    yield service, repo
    repo.fechar()


# ------------------ Detection ------------------

def test_classe_com_test_classe_eh_coberta(cenario):
    service, _ = cenario
    prod = "class UserService:\n    def login(self, u): pass\n"
    testes = "class TestUserService:\n    def test_login(self): pass\n"
    mapa = service.analisar(prod, testes)
    assert {c.nome for c in mapa.cobertos} == {"UserService"}
    assert mapa.sem_cobertura == []


def test_classe_com_sufixo_test_eh_coberta(cenario):
    service, _ = cenario
    prod = "class Calculator:\n    def add(self, a, b): pass\n"
    testes = "class CalculatorTest:\n    def test_add(self): pass\n"
    mapa = service.analisar(prod, testes)
    assert {c.nome for c in mapa.cobertos} == {"Calculator"}


def test_classe_com_sufixo_tests_eh_coberta(cenario):
    service, _ = cenario
    prod = "class Logger:\n    def log(self): pass\n"
    testes = "class LoggerTests:\n    def test_log(self): pass\n"
    mapa = service.analisar(prod, testes)
    assert {c.nome for c in mapa.cobertos} == {"Logger"}


def test_funcao_test_com_nome_em_snake_eh_match(cenario):
    service, _ = cenario
    prod = "class UserService:\n    pass\n"
    testes = "def test_user_service_login(): pass\n"
    mapa = service.analisar(prod, testes)
    assert {c.nome for c in mapa.cobertos} == {"UserService"}


def test_classe_sem_teste_aparece_em_sem_cobertura(cenario):
    service, _ = cenario
    prod = "class Foo:\n    def bar(self): pass\n"
    testes = ""
    mapa = service.analisar(prod, testes)
    assert mapa.cobertos == []
    assert {c.componente.nome for c in mapa.sem_cobertura} == {"Foo"}


def test_codigo_de_teste_vazio_gera_warning(cenario):
    service, _ = cenario
    prod = "class A:\n    pass\n"
    mapa = service.analisar(prod, "")
    assert any("vazio" in w.lower() for w in mapa.warnings)


# ------------------ Criticidade ------------------

def test_sufixo_critico_aumenta_score(cenario):
    service, _ = cenario
    prod = """
class Helper:
    def foo(self): pass

class UserService:
    def foo(self): pass
"""
    mapa = service.analisar(prod, "")
    sem = {c.componente.nome: c for c in mapa.sem_cobertura}
    assert sem["UserService"].criticidade_score > sem["Helper"].criticidade_score
    assert any("critico" in m for m in sem["UserService"].motivos_criticidade)


def test_classe_com_mais_metodos_eh_mais_critica(cenario):
    service, _ = cenario
    prod = """
class Pequena:
    def a(self): pass

class Grande:
    def a(self): pass
    def b(self): pass
    def c(self): pass
    def d(self): pass
"""
    mapa = service.analisar(prod, "")
    sem = {c.componente.nome: c for c in mapa.sem_cobertura}
    assert sem["Grande"].criticidade_score > sem["Pequena"].criticidade_score


def test_dependentes_aumentam_criticidade(cenario):
    service, _ = cenario
    prod = """
class Base:
    def x(self): pass

class FilhoUm(Base):
    pass

class FilhoDois(Base):
    pass

class Solta:
    def x(self): pass
"""
    mapa = service.analisar(prod, "")
    sem = {c.componente.nome: c for c in mapa.sem_cobertura}
    # Base tem 2 dependentes (FilhoUm, FilhoDois) — Solta nao tem
    assert sem["Base"].criticidade_score > sem["Solta"].criticidade_score
    assert any("dependem" in m for m in sem["Base"].motivos_criticidade)


def test_lista_sem_cobertura_ordenada_por_criticidade(cenario):
    service, _ = cenario
    prod = """
class HelperPequeno:
    def a(self): pass

class UserService:
    def login(self): pass
    def logout(self): pass
"""
    mapa = service.analisar(prod, "")
    nomes_em_ordem = [c.componente.nome for c in mapa.sem_cobertura]
    # UserService deve vir antes (sufixo critico + mais metodos)
    assert nomes_em_ordem == ["UserService", "HelperPequeno"]


# ------------------ Ignorados ------------------

def test_marcar_ignorar_remove_da_analise(cenario):
    service, _ = cenario
    prod = "class Legacy:\n    def a(self): pass\n"
    service.marcar_ignorar("Legacy", motivo="codigo legado a remover", marcado_por="alice")
    mapa = service.analisar(prod, "")
    assert mapa.sem_cobertura == []
    assert {c.nome for c in mapa.ignorados} == {"Legacy"}


def test_marcar_ignorar_persiste(cenario):
    service, repo = cenario
    service.marcar_ignorar("X", motivo="trivial", marcado_por="alice")
    persistido = repo.obter("X")
    assert persistido is not None
    assert persistido.motivo == "trivial"


def test_desmarcar_ignorar(cenario):
    service, _ = cenario
    service.marcar_ignorar("X", motivo="trivial", marcado_por="alice")
    assert service.desmarcar_ignorar("X") is True
    assert service.desmarcar_ignorar("X") is False


def test_marcar_ignorar_motivo_vazio_falha(cenario):
    service, _ = cenario
    with pytest.raises(IgnorarInvalidoError):
        service.marcar_ignorar("X", motivo="", marcado_por="alice")


def test_marcar_ignorar_marcado_por_vazio_falha(cenario):
    service, _ = cenario
    with pytest.raises(IgnorarInvalidoError):
        service.marcar_ignorar("X", motivo="x", marcado_por="")


def test_listar_ignorados(cenario):
    service, _ = cenario
    service.marcar_ignorar("A", "x", "alice")
    service.marcar_ignorar("B", "y", "bob")
    nomes = {i.nome for i in service.listar_ignorados()}
    assert nomes == {"A", "B"}


# ------------------ Resumo / Percentual ------------------

def test_percentual_de_cobertura(cenario):
    service, _ = cenario
    prod = "class A:\n    pass\nclass B:\n    pass\n"
    testes = "class TestA:\n    def test_x(self): pass\n"
    mapa = service.analisar(prod, testes)
    # 1 coberto, 1 sem cobertura -> 50%
    assert mapa.percentual_cobertura == 50.0


def test_percentual_ignora_ignorados(cenario):
    service, _ = cenario
    service.marcar_ignorar("Legacy", "x", "alice")
    prod = "class A:\n    pass\nclass Legacy:\n    pass\n"
    testes = "class TestA:\n    def test_x(self): pass\n"
    mapa = service.analisar(prod, testes)
    # A coberto, Legacy ignorado -> 100% dos considerados
    assert mapa.percentual_cobertura == 100.0


# ------------------ Validacao ------------------

def test_codigo_producao_vazio_falha(cenario):
    service, _ = cenario
    with pytest.raises(CoberturaInvalidaError):
        service.analisar("", "")


def test_codigo_producao_invalido_400(cenario):
    service, _ = cenario
    with pytest.raises(CoberturaInvalidaError):
        service.analisar("class A:", "")  # syntax error


def test_codigo_teste_invalido_gera_warning_mas_nao_falha(cenario):
    service, _ = cenario
    prod = "class A:\n    pass\n"
    mapa = service.analisar(prod, "class TestA:")  # syntax error em testes
    assert any("nao parseou" in w for w in mapa.warnings)
    # A aparece em sem_cobertura porque os alvos nao puderam ser extraidos
    assert any(c.componente.nome == "A" for c in mapa.sem_cobertura)
