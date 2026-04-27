from app.domain.entidades.componente import Componente
from app.domain.entidades.relacao import Relacao
from app.domain.entidades.estrutura_arquitetural import EstruturaArquitetural


def test_to_dict_estrutura_vazia():
    e = EstruturaArquitetural(componentes=[], relacoes=[])
    assert e.to_dict() == {"componentes": [], "relacoes": [], "warnings": []}


def test_to_dict_serializa_componentes_e_relacoes():
    comp = Componente(
        nome="Calc",
        tipo="classe",
        metodos=["somar"],
        atributos=[],
        responsabilidade="Soma números.",
    )
    rel = Relacao(origem="CalcCient", destino="Calc", tipo="heranca", fonte="ast")
    e = EstruturaArquitetural(componentes=[comp], relacoes=[rel])
    d = e.to_dict()
    assert d["componentes"][0]["nome"] == "Calc"
    assert d["componentes"][0]["responsabilidade"] == "Soma números."
    assert d["relacoes"][0]["fonte"] == "ast"
    assert d["warnings"] == []


def test_to_dict_inclui_warnings():
    e = EstruturaArquitetural(
        componentes=[],
        relacoes=[],
        warnings=["LLM indisponível"],
    )
    assert e.to_dict()["warnings"] == ["LLM indisponível"]


def test_to_mermaid_vazio():
    e = EstruturaArquitetural(componentes=[], relacoes=[])
    saida = e.to_mermaid()
    assert saida.strip() == "classDiagram"


def test_to_mermaid_classe_com_metodos_e_atributos():
    comp = Componente(
        nome="Calc",
        tipo="classe",
        metodos=["somar", "subtrair"],
        atributos=["historico"],
    )
    e = EstruturaArquitetural(componentes=[comp], relacoes=[])
    saida = e.to_mermaid()
    assert "classDiagram" in saida
    assert "class Calc" in saida
    assert "+somar()" in saida
    assert "+subtrair()" in saida
    assert "+historico" in saida


def test_to_mermaid_emite_seta_de_heranca():
    a = Componente(nome="Pai", tipo="classe")
    b = Componente(nome="Filha", tipo="classe")
    rel = Relacao(origem="Filha", destino="Pai", tipo="heranca", fonte="ast")
    e = EstruturaArquitetural(componentes=[a, b], relacoes=[rel])
    saida = e.to_mermaid()
    assert "Pai <|-- Filha" in saida


def test_to_mermaid_emite_seta_de_uso():
    a = Componente(nome="Service", tipo="classe")
    b = Componente(nome="Repo", tipo="classe")
    rel = Relacao(origem="Service", destino="Repo", tipo="usa", fonte="llm")
    e = EstruturaArquitetural(componentes=[a, b], relacoes=[rel])
    saida = e.to_mermaid()
    assert "Service ..> Repo : usa" in saida


def test_to_mermaid_descarta_relacao_com_componente_inexistente():
    a = Componente(nome="Existente", tipo="classe")
    rel = Relacao(origem="Existente", destino="Fantasma", tipo="usa", fonte="llm")
    e = EstruturaArquitetural(componentes=[a], relacoes=[rel])
    saida = e.to_mermaid()
    assert "Fantasma" not in saida
