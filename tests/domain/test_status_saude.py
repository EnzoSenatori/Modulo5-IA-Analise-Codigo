from app.domain.entidades.status_saude import StatusSaude, CheckSaude


def test_status_saude_vazio_serializa():
    s = StatusSaude(status="healthy")
    d = s.to_dict()
    assert d == {"status": "healthy", "checks": {}, "tempo_ms": 0}


def test_status_saude_com_checks_serializa():
    s = StatusSaude(
        status="degraded",
        checks={
            "provedor_llm": CheckSaude(
                status="degraded",
                detalhe={"tipo": "AdaptadorLLMFake"},
            ),
            "cache": CheckSaude(status="not_configured"),
        },
        tempo_ms=4,
    )
    d = s.to_dict()
    assert d["status"] == "degraded"
    assert d["tempo_ms"] == 4
    assert d["checks"]["provedor_llm"]["status"] == "degraded"
    assert d["checks"]["provedor_llm"]["detalhe"]["tipo"] == "AdaptadorLLMFake"
    assert d["checks"]["cache"]["status"] == "not_configured"
    assert d["checks"]["cache"]["detalhe"] == {}
