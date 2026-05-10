# Testes do DiffArquitetural — entidade pura (US IA-10).

from app.domain.entidades.componente import Componente
from app.domain.entidades.diff_arquitetural import ComponenteAlterado, DiffArquitetural
from app.domain.entidades.relacao import Relacao


def test_diff_vazio_nao_tem_mudancas():
    d = DiffArquitetural()
    assert d.tem_mudancas() is False
    assert d.resumo() == {
        "componentes_adicionados": 0,
        "componentes_removidos": 0,
        "componentes_alterados": 0,
        "relacoes_adicionadas": 0,
        "relacoes_removidas": 0,
    }


def test_resumo_contem_contagens_corretas():
    d = DiffArquitetural(
        componentes_adicionados=[Componente(nome="A", tipo="classe")],
        componentes_removidos=[Componente(nome="B", tipo="classe"), Componente(nome="C", tipo="classe")],
        componentes_alterados=[ComponenteAlterado(nome="D", metodos_adicionados=["x"])],
        relacoes_adicionadas=[Relacao(origem="A", destino="X", tipo="usa", fonte="ast")],
        relacoes_removidas=[],
    )
    assert d.tem_mudancas() is True
    assert d.resumo() == {
        "componentes_adicionados": 1,
        "componentes_removidos": 2,
        "componentes_alterados": 1,
        "relacoes_adicionadas": 1,
        "relacoes_removidas": 0,
    }


def test_componente_alterado_tem_mudanca_so_quando_ha_diff_real():
    sem_diff = ComponenteAlterado(nome="X")
    assert sem_diff.tem_mudanca() is False

    com_metodo = ComponenteAlterado(nome="X", metodos_adicionados=["foo"])
    assert com_metodo.tem_mudanca() is True

    so_responsabilidade = ComponenteAlterado(
        nome="X",
        responsabilidade_alterada=True,
        responsabilidade_antes="velha",
        responsabilidade_depois="nova",
    )
    assert so_responsabilidade.tem_mudanca() is True


def test_to_dict_serializa_tudo():
    d = DiffArquitetural(
        componentes_adicionados=[Componente(nome="A", tipo="classe")],
    )
    j = d.to_dict()
    assert j["tem_mudancas"] is True
    assert j["componentes_adicionados"][0]["nome"] == "A"
    assert "warnings" in j
    assert "resumo" in j


def test_to_mermaid_inclui_classes_e_estilos():
    d = DiffArquitetural(
        componentes_adicionados=[Componente(nome="Novo", tipo="classe")],
        componentes_removidos=[Componente(nome="Velho", tipo="classe")],
        componentes_alterados=[ComponenteAlterado(nome="Mid", metodos_adicionados=["foo"])],
    )
    m = d.to_mermaid()
    assert "classDiagram" in m
    assert "Novo" in m and "Velho" in m and "Mid" in m
    assert "classDef adicionado" in m and "classDef removido" in m and "classDef alterado" in m
    assert ":::adicionado" in m
    assert ":::removido" in m
    assert ":::alterado" in m


def test_to_mermaid_relacoes_recebem_label_pos_neg():
    d = DiffArquitetural(
        relacoes_adicionadas=[Relacao(origem="A", destino="B", tipo="usa", fonte="ast")],
        relacoes_removidas=[Relacao(origem="C", destino="D", tipo="heranca", fonte="ast")],
    )
    m = d.to_mermaid()
    assert "A ..> B : + usa" in m
    assert "D <|-- C : -" in m
