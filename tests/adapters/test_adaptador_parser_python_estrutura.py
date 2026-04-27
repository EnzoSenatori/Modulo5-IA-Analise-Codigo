import pytest

from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.domain.excecoes import ParserError


@pytest.fixture
def parser():
    return AdaptadorParserPython()


def test_extrair_estrutura_classe_simples(parser):
    codigo = """
class Calculadora:
    def __init__(self):
        self.historico = []

    def somar(self, a, b):
        return a + b
"""
    componentes = parser.extrair_estrutura(codigo)
    assert len(componentes) == 1
    c = componentes[0]
    assert c.nome == "Calculadora"
    assert c.tipo == "classe"
    assert "somar" in c.metodos
    assert "__init__" in c.metodos
    assert "historico" in c.atributos
    assert c.responsabilidade == ""


def test_extrair_estrutura_atributo_definido_em_metodo_qualquer(parser):
    codigo = """
class Foo:
    def setar(self):
        self.bar = 1
"""
    componentes = parser.extrair_estrutura(codigo)
    assert "bar" in componentes[0].atributos


def test_extrair_estrutura_sem_classes(parser):
    componentes = parser.extrair_estrutura("def funcao_solta():\n    return 42\n")
    assert componentes == []


def test_extrair_estrutura_codigo_invalido_levanta_parser_error(parser):
    with pytest.raises(ParserError):
        parser.extrair_estrutura("def quebrado(:\n    pass")


def test_extrair_herancas_simples(parser):
    codigo = """
class Pai:
    pass

class Filha(Pai):
    pass
"""
    relacoes = parser.extrair_herancas(codigo)
    assert len(relacoes) == 1
    r = relacoes[0]
    assert r.origem == "Filha"
    assert r.destino == "Pai"
    assert r.tipo == "heranca"
    assert r.fonte == "ast"


def test_extrair_herancas_multipla(parser):
    codigo = """
class A: pass
class B: pass
class C(A, B): pass
"""
    relacoes = parser.extrair_herancas(codigo)
    pares = {(r.origem, r.destino) for r in relacoes}
    assert ("C", "A") in pares
    assert ("C", "B") in pares


def test_extrair_herancas_sem_classes(parser):
    assert parser.extrair_herancas("x = 1\n") == []


def test_extrair_herancas_codigo_invalido_levanta_parser_error(parser):
    with pytest.raises(ParserError):
        parser.extrair_herancas("class :\n    pass")
