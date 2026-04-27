from app.domain.entidades.relacao import Relacao


def test_relacao_de_heranca_via_ast():
    r = Relacao(origem="Filha", destino="Pai", tipo="heranca", fonte="ast")
    assert r.origem == "Filha"
    assert r.destino == "Pai"
    assert r.tipo == "heranca"
    assert r.fonte == "ast"


def test_relacao_de_uso_via_llm():
    r = Relacao(origem="Service", destino="Repository", tipo="usa", fonte="llm")
    assert r.tipo == "usa"
    assert r.fonte == "llm"
