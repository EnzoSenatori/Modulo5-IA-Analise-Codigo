"""Rotas HTTP do serviço de documentação (IA-08)."""
from __future__ import annotations

from fastapi import APIRouter, Depends, HTTPException

from app.application.ports.driving.documentacao_service import DocumentacaoService


router = APIRouter(prefix="/documentacao", tags=["documentacao"])


def get_documentacao_service() -> DocumentacaoService:
    """Resolução do serviço; será sobrescrita pelo composition root."""
    raise NotImplementedError(
        "Configurar em app/config/composition_root.py"
    )


@router.get("/drift")
def get_drift(
    repo: str,
    ref: str = "HEAD",
    service: DocumentacaoService = Depends(get_documentacao_service),
):
    try:
        relatorio = service.detectar_drift(repo, ref)
    except Exception as exc:
        raise HTTPException(
            status_code=502,
            detail=f"Falha ao analisar drift: {exc}",
        ) from exc

    return {
        "hash_commit": relatorio.hash_commit,
        "possui_drift": relatorio.possui_drift,
        "divergencias": [
            {
                "tipo": d.tipo,
                "descricao": d.descricao,
                "referencia_readme": d.referencia_readme,
                "referencia_codigo": d.referencia_codigo,
            }
            for d in relatorio.divergencias
        ],
        "decisoes_arquiteturais": list(relatorio.decisoes_arquiteturais),
        "resumo_documentacao": relatorio.resumo_documentacao,
        "origem": relatorio.origem,
        "aviso": relatorio.aviso,
        "gerado_em": relatorio.gerado_em.isoformat(),
    }
