import pytest

from app.application.services.estrutura_service_impl import EstruturaServiceImpl
from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMFake
from app.domain.entidades.relacao import Relacao
from app.domain.excecoes import LLMError, ParserError


@pytest.fixture
def parser():
    return AdaptadorParserPython()


def test_caminho_feliz_combina_ast_e_llm(parser):
    fake_llm = AdaptadorLLMFake(
        responsabilidades={"Calc": "Faz contas."},
        relacoes=[Relacao(origem="Calc", destino="Logger", tipo="usa", fonte="llm")],
    )
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=fake_llm)

    codigo = """
class Calc:
    def somar(self, a, b): return a + b

class Logger:
    def log(self, msg): pass

class CalcCient(Calc):
    pass
"""
    estrutura = service.gerar_diagrama(codigo)

    nomes = {c.nome for c in estrutura.componentes}
    assert nomes == {"Calc", "Logger", "CalcCient"}

    calc = next(c for c in estrutura.componentes if c.nome == "Calc")
    assert calc.responsabilidade == "Faz contas."

    tipos = {(r.origem, r.destino, r.tipo, r.fonte) for r in estrutura.relacoes}
    assert ("CalcCient", "Calc", "heranca", "ast") in tipos
    assert ("Calc", "Logger", "usa", "llm") in tipos
    assert estrutura.warnings == []


def test_degradacao_quando_llm_falha(parser):
    fake_llm = AdaptadorLLMFake(erro=LLMError("indisponível"))
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=fake_llm)

    estrutura = service.gerar_diagrama("class A:\n    pass\nclass B(A):\n    pass\n")

    nomes = {c.nome for c in estrutura.componentes}
    assert nomes == {"A", "B"}
    assert any(r.tipo == "heranca" for r in estrutura.relacoes)
    assert all(r.fonte == "ast" for r in estrutura.relacoes)
    assert all(c.responsabilidade == "" for c in estrutura.componentes)
    assert len(estrutura.warnings) == 1
    assert "LLM indisponível" in estrutura.warnings[0]


def test_codigo_vazio_levanta_parser_error(parser):
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=AdaptadorLLMFake())
    with pytest.raises(ParserError):
        service.gerar_diagrama("")
    with pytest.raises(ParserError):
        service.gerar_diagrama("   \n  \t")


def test_codigo_com_syntax_error_levanta_parser_error(parser):
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=AdaptadorLLMFake())
    with pytest.raises(ParserError):
        service.gerar_diagrama("def x(:\n  pass")


def test_codigo_sem_classes_retorna_estrutura_vazia(parser):
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=AdaptadorLLMFake())
    estrutura = service.gerar_diagrama("def f():\n    return 1\n")
    assert estrutura.componentes == []
    assert estrutura.relacoes == []
    assert estrutura.warnings == []
    assert estrutura.linguagem == "python"


def test_caminho_feliz_marca_linguagem_python(parser):
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=AdaptadorLLMFake())
    estrutura = service.gerar_diagrama("class A:\n    pass\n")
    assert estrutura.linguagem == "python"


def test_codigo_javascript_retorna_warning_e_estrutura_vazia(parser):
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=AdaptadorLLMFake())
    codigo_js = """
function somar(a, b) {
    return a + b;
}
const x = () => 42;
"""
    estrutura = service.gerar_diagrama(codigo_js)
    assert estrutura.linguagem == "javascript"
    assert estrutura.componentes == []
    assert estrutura.relacoes == []
    assert len(estrutura.warnings) == 1
    assert "javascript" in estrutura.warnings[0].lower()
    assert "não suportada" in estrutura.warnings[0]


def test_codigo_java_detectado_como_nao_suportado(parser):
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=AdaptadorLLMFake())
    codigo_java = """
public class Calculadora {
    public static void main(String[] args) {
        System.out.println("oi");
    }
}
"""
    estrutura = service.gerar_diagrama(codigo_java)
    assert estrutura.linguagem == "java"
    assert estrutura.componentes == []


def test_codigo_go_detectado_como_nao_suportado(parser):
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=AdaptadorLLMFake())
    codigo_go = """
package main

func somar(a int, b int) int {
    return a + b
}
"""
    estrutura = service.gerar_diagrama(codigo_go)
    assert estrutura.linguagem == "go"
    assert estrutura.componentes == []


def test_codigo_irreconhecivel_marcado_como_desconhecida(parser):
    service = EstruturaServiceImpl(parser_codigo=parser, provedor_llm=AdaptadorLLMFake())
    estrutura = service.gerar_diagrama("xpto qweasd 12345 !!!\n")
    assert estrutura.linguagem == "desconhecida"
    assert estrutura.componentes == []
    assert "não suportada" in estrutura.warnings[0]
