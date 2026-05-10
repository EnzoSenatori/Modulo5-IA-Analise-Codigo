# Testes do ComparacaoDiagramaServiceImpl (US IA-10).

import pytest

from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMFake
from app.application.services.comparacao_diagrama_service_impl import (
    ComparacaoDiagramaServiceImpl,
)
from app.application.services.estrutura_service_impl import EstruturaServiceImpl
from app.domain.entidades.componente import Componente
from app.domain.entidades.estrutura_arquitetural import EstruturaArquitetural
from app.domain.entidades.relacao import Relacao
from app.domain.excecoes import ParserError


@pytest.fixture
def service():
    estrutura = EstruturaServiceImpl(
        parser_codigo=AdaptadorParserPython(),
        provedor_llm=AdaptadorLLMFake(),
    )
    return ComparacaoDiagramaServiceImpl(estrutura_service=estrutura)


# ------------------ diff_de_estruturas ------------------

def _estrutura(componentes, relacoes=()):
    return EstruturaArquitetural(
        componentes=list(componentes),
        relacoes=list(relacoes),
        linguagem="python",
    )


def test_diff_iguais_nao_tem_mudancas(service):
    a = _estrutura([Componente(nome="X", tipo="classe", metodos=["foo"])])
    diff = service.diff_de_estruturas(a, a)
    assert diff.tem_mudancas() is False


def test_diff_componente_adicionado(service):
    antes = _estrutura([Componente(nome="A", tipo="classe")])
    depois = _estrutura([Componente(nome="A", tipo="classe"), Componente(nome="B", tipo="classe")])
    diff = service.diff_de_estruturas(antes, depois)
    assert {c.nome for c in diff.componentes_adicionados} == {"B"}
    assert diff.componentes_removidos == []


def test_diff_componente_removido(service):
    antes = _estrutura([Componente(nome="A", tipo="classe"), Componente(nome="B", tipo="classe")])
    depois = _estrutura([Componente(nome="A", tipo="classe")])
    diff = service.diff_de_estruturas(antes, depois)
    assert {c.nome for c in diff.componentes_removidos} == {"B"}


def test_diff_metodo_adicionado_e_removido(service):
    antes = _estrutura([Componente(nome="X", tipo="classe", metodos=["foo", "bar"])])
    depois = _estrutura([Componente(nome="X", tipo="classe", metodos=["foo", "baz"])])
    diff = service.diff_de_estruturas(antes, depois)
    assert len(diff.componentes_alterados) == 1
    alt = diff.componentes_alterados[0]
    assert alt.metodos_adicionados == ["baz"]
    assert alt.metodos_removidos == ["bar"]


def test_diff_responsabilidade_alterada(service):
    antes = _estrutura([Componente(nome="X", tipo="classe", responsabilidade="versao 1")])
    depois = _estrutura([Componente(nome="X", tipo="classe", responsabilidade="versao 2")])
    diff = service.diff_de_estruturas(antes, depois)
    assert len(diff.componentes_alterados) == 1
    alt = diff.componentes_alterados[0]
    assert alt.responsabilidade_alterada is True
    assert alt.responsabilidade_antes == "versao 1"
    assert alt.responsabilidade_depois == "versao 2"


def test_diff_relacao_adicionada(service):
    antes = _estrutura(
        [Componente(nome="A", tipo="classe"), Componente(nome="B", tipo="classe")],
        relacoes=[],
    )
    depois = _estrutura(
        [Componente(nome="A", tipo="classe"), Componente(nome="B", tipo="classe")],
        relacoes=[Relacao(origem="A", destino="B", tipo="usa", fonte="llm")],
    )
    diff = service.diff_de_estruturas(antes, depois)
    assert len(diff.relacoes_adicionadas) == 1
    assert diff.relacoes_adicionadas[0].origem == "A"


def test_diff_relacao_orfa_eh_descartada(service):
    """Se uma relacao referencia componente que nao existe, ignoramos
    (mesma logica do to_mermaid em IA-01)."""
    antes = _estrutura(
        [Componente(nome="A", tipo="classe")],
        relacoes=[Relacao(origem="A", destino="X_inexistente", tipo="usa", fonte="llm")],
    )
    depois = _estrutura([Componente(nome="A", tipo="classe")])
    diff = service.diff_de_estruturas(antes, depois)
    # A relacao orfa nao conta como removida porque foi descartada antes.
    assert diff.relacoes_removidas == []
    assert diff.tem_mudancas() is False


def test_diff_ignora_fonte_de_relacao(service):
    """Mudanca de fonte (ast/llm) na mesma (origem,destino,tipo) nao deve gerar diff."""
    antes = _estrutura(
        [Componente(nome="A", tipo="classe"), Componente(nome="B", tipo="classe")],
        relacoes=[Relacao(origem="A", destino="B", tipo="usa", fonte="ast")],
    )
    depois = _estrutura(
        [Componente(nome="A", tipo="classe"), Componente(nome="B", tipo="classe")],
        relacoes=[Relacao(origem="A", destino="B", tipo="usa", fonte="llm")],
    )
    diff = service.diff_de_estruturas(antes, depois)
    assert diff.relacoes_adicionadas == []
    assert diff.relacoes_removidas == []


def test_linguagens_diferentes_geram_warning(service):
    antes = EstruturaArquitetural(componentes=[], relacoes=[], linguagem="python")
    depois = EstruturaArquitetural(componentes=[], relacoes=[], linguagem="javascript")
    diff = service.diff_de_estruturas(antes, depois)
    assert any("Linguagens diferentes" in w for w in diff.warnings)


# ------------------ diff_de_codigos (e2e leve) ------------------

def test_diff_de_codigos_pipeline_ponta_a_ponta(service):
    antes = "class A:\n    def foo(self): pass\n"
    depois = "class A:\n    def foo(self): pass\n    def bar(self): pass\nclass B:\n    pass\n"
    diff = service.diff_de_codigos(antes, depois)
    assert {c.nome for c in diff.componentes_adicionados} == {"B"}
    assert any(c.nome == "A" and "bar" in c.metodos_adicionados for c in diff.componentes_alterados)


def test_diff_de_codigos_propaga_erro_de_parser(service):
    with pytest.raises(ParserError):
        service.diff_de_codigos("class A:", "class B:\n    pass")
