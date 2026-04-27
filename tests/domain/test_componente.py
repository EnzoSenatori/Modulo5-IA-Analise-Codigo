from app.domain.entidades.componente import Componente


def test_componente_aceita_valores_minimos():
    c = Componente(nome="Foo", tipo="classe", metodos=[], atributos=[])
    assert c.nome == "Foo"
    assert c.tipo == "classe"
    assert c.metodos == []
    assert c.atributos == []
    assert c.responsabilidade == ""


def test_componente_aceita_responsabilidade_opcional():
    c = Componente(
        nome="Calculadora",
        tipo="classe",
        metodos=["somar"],
        atributos=["historico"],
        responsabilidade="Realiza operações aritméticas.",
    )
    assert c.responsabilidade == "Realiza operações aritméticas."
