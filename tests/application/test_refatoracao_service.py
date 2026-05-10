# Testes do RefatoracaoServiceImpl (US IA-05).
# Foco: determinismo + correcao de cada detector.

import pytest

from app.application.services.refatoracao_service_impl import RefatoracaoServiceImpl
from app.domain.entidades.sugestao_refatoracao import (
    CategoriaRefatoracao,
    EsforcoEstimado,
)
from app.domain.excecoes import CodigoVazioError, ParserError


@pytest.fixture
def service():
    return RefatoracaoServiceImpl()


# ------------------ Determinismo ------------------

def test_mesmo_input_gera_mesma_saida(service):
    codigo = """
def grande_funcao():
    x = 0
    x = 1
    x = 2
""" + "\n".join([f"    x = {i}" for i in range(40)])

    a = service.sugerir(codigo).to_dict()
    b = service.sugerir(codigo).to_dict()
    c = service.sugerir(codigo).to_dict()
    assert a == b == c  # determinismo total


def test_sugestoes_ordenadas_por_linha(service):
    codigo = """
class Foo:
    pass

def funcao_curta():
    return 99999  # numero magico

def funcao_longa():
""" + "\n".join([f"    x = {i}" for i in range(35)])

    relatorio = service.sugerir(codigo)
    linhas = [s.linha_inicio for s in relatorio.sugestoes]
    assert linhas == sorted(linhas)


# ------------------ Validacao ------------------

def test_codigo_vazio_levanta(service):
    with pytest.raises(CodigoVazioError):
        service.sugerir("")
    with pytest.raises(CodigoVazioError):
        service.sugerir("   \n\n")


def test_codigo_invalido_levanta_parser(service):
    with pytest.raises(ParserError):
        service.sugerir("def foo(:\n    pass")


# ------------------ Detector: funcao longa ------------------

def test_detecta_funcao_longa(service):
    corpo = "\n".join([f"    x = {i}" for i in range(40)])
    codigo = f"def grande():\n{corpo}\n"
    relatorio = service.sugerir(codigo)
    sugestoes_funcao = [s for s in relatorio.sugestoes if s.categoria == CategoriaRefatoracao.FUNCAO_LONGA]
    assert len(sugestoes_funcao) == 1
    s = sugestoes_funcao[0]
    assert "grande" in s.titulo
    assert "_validar_entrada" in s.snippet_depois  # template de extracao
    assert s.detalhes["nome_funcao"] == "grande"
    assert s.detalhes["linhas"] > 30


def test_funcao_curta_nao_gera_sugestao(service):
    codigo = "def pequena():\n    return 1\n"
    relatorio = service.sugerir(codigo)
    assert all(s.categoria != CategoriaRefatoracao.FUNCAO_LONGA for s in relatorio.sugestoes)


# ------------------ Detector: muitos parametros ------------------

def test_detecta_muitos_parametros(service):
    codigo = "def f(a, b, c, d, e, f_, g):\n    pass\n"
    relatorio = service.sugerir(codigo)
    s = next(s for s in relatorio.sugestoes if s.categoria == CategoriaRefatoracao.MUITOS_PARAMETROS)
    assert s.detalhes["qtd_params"] == 7
    assert s.esforco == EsforcoEstimado.PEQUENO
    assert "dataclass" in s.snippet_depois.lower()


def test_self_nao_conta_como_parametro(service):
    codigo = """
class X:
    def metodo(self, a, b, c, d, e):
        pass
"""
    relatorio = service.sugerir(codigo)
    # 5 params + self = 6 args, descontando self = 5 params (no limite, nao excede)
    assert all(s.categoria != CategoriaRefatoracao.MUITOS_PARAMETROS for s in relatorio.sugestoes)


# ------------------ Detector: default mutavel ------------------

def test_detecta_default_lista_mutavel(service):
    codigo = "def append_para(item, lst=[]):\n    lst.append(item)\n    return lst\n"
    relatorio = service.sugerir(codigo)
    s = next(s for s in relatorio.sugestoes if s.categoria == CategoriaRefatoracao.DEFAULT_MUTAVEL)
    assert s.esforco == EsforcoEstimado.TRIVIAL
    assert s.detalhes["parametro"] == "lst"
    assert "if lst is None" in s.snippet_depois


def test_detecta_default_dict_mutavel(service):
    codigo = "def f(x={}):\n    pass\n"
    relatorio = service.sugerir(codigo)
    sugestoes = [s for s in relatorio.sugestoes if s.categoria == CategoriaRefatoracao.DEFAULT_MUTAVEL]
    assert len(sugestoes) == 1
    assert sugestoes[0].detalhes["tipo_default"] == "Dict"


def test_default_imutavel_nao_alerta(service):
    codigo = "def f(x=5, y='hi', z=None):\n    pass\n"
    relatorio = service.sugerir(codigo)
    assert all(s.categoria != CategoriaRefatoracao.DEFAULT_MUTAVEL for s in relatorio.sugestoes)


# ------------------ Detector: numero magico ------------------

def test_detecta_numero_magico(service):
    codigo = "def f(idade):\n    if idade >= 18:\n        return idade * 365\n"
    relatorio = service.sugerir(codigo)
    sugestoes = [s for s in relatorio.sugestoes if s.categoria == CategoriaRefatoracao.NUMERO_MAGICO]
    # Linha 2 (>= 18) e linha 3 (* 365) — duas linhas com numeros magicos
    assert len(sugestoes) == 2
    valores_detectados = set()
    for s in sugestoes:
        valores_detectados.update(s.detalhes["valores"])
    assert 18 in valores_detectados
    assert 365 in valores_detectados


def test_numeros_triviais_nao_alertam(service):
    codigo = "def f():\n    return 0 + 1 - 1 + 2 - 2 + 100\n"
    relatorio = service.sugerir(codigo)
    assert all(s.categoria != CategoriaRefatoracao.NUMERO_MAGICO for s in relatorio.sugestoes)


def test_bool_nao_eh_tratado_como_magico(service):
    codigo = "def f():\n    return True if False else None\n"
    relatorio = service.sugerir(codigo)
    assert all(s.categoria != CategoriaRefatoracao.NUMERO_MAGICO for s in relatorio.sugestoes)


def test_multiplos_numeros_mesma_linha_geram_uma_sugestao(service):
    codigo = "def f():\n    return 17 + 23 + 31\n"
    relatorio = service.sugerir(codigo)
    sugestoes = [s for s in relatorio.sugestoes if s.categoria == CategoriaRefatoracao.NUMERO_MAGICO]
    assert len(sugestoes) == 1  # uma sugestao por linha
    assert set(sugestoes[0].detalhes["valores"]) == {17, 23, 31}


# ------------------ Detector: cadeia elif longa ------------------

def test_detecta_cadeia_elif_longa(service):
    codigo = """
def classificar(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    elif x == 3:
        return 'c'
    elif x == 4:
        return 'd'
    elif x == 5:
        return 'e'
    elif x == 6:
        return 'f'
    else:
        return 'z'
"""
    relatorio = service.sugerir(codigo)
    sugestoes = [s for s in relatorio.sugestoes if s.categoria == CategoriaRefatoracao.CADEIA_ELIF_LONGA]
    assert len(sugestoes) == 1
    assert sugestoes[0].detalhes["qtd_branches"] == 6
    assert "_HANDLERS" in sugestoes[0].snippet_depois


def test_if_curto_nao_alerta(service):
    codigo = """
def f(x):
    if x == 1:
        return 'a'
    elif x == 2:
        return 'b'
    else:
        return 'c'
"""
    relatorio = service.sugerir(codigo)
    assert all(s.categoria != CategoriaRefatoracao.CADEIA_ELIF_LONGA for s in relatorio.sugestoes)


# ------------------ Resumo ------------------

def test_relatorio_inclui_resumos(service):
    codigo = """
def f(x=[]):
    return 999
"""
    relatorio = service.sugerir(codigo)
    d = relatorio.to_dict()
    assert "resumo_por_esforco" in d
    assert "resumo_por_categoria" in d
    # default_mutavel tem esforco TRIVIAL
    assert d["resumo_por_esforco"]["trivial"] >= 1


def test_codigo_limpo_zero_sugestoes(service):
    codigo = """
\"\"\"Modulo limpo, sem sinais de refatoracao.\"\"\"
LIMITE_IDADE = 18

def eh_maior(idade: int) -> bool:
    return idade >= LIMITE_IDADE
"""
    relatorio = service.sugerir(codigo)
    assert relatorio.total == 0
