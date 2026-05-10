# Rota HTTP do servico de comparacao de diagramas (US IA-10).

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.ports.driving.comparacao_diagrama_service import (
    ComparacaoDiagramaService,
)
from app.config.composition_root import CompositionRoot
from app.domain.excecoes import ParserError


router = APIRouter(prefix="/comparacao", tags=["Comparacao"])


class CodigosParaCompararRequest(BaseModel):
    codigo_antes: str
    codigo_depois: str


def get_comparacao_service() -> ComparacaoDiagramaService:
    return CompositionRoot().get_comparacao_service()


@router.post("/diagrama")
async def comparar_diagramas(
    request: CodigosParaCompararRequest,
    service: ComparacaoDiagramaService = Depends(get_comparacao_service),
):
    """
    Compara duas versoes de codigo Python (ex: base e head de um PR) e devolve:
      - JSON estrutural com componentes adicionados/removidos/alterados e relacoes
      - Mermaid colorido (componentes verdes/vermelhos/amarelos)
    Atende a US IA-10.
    """
    try:
        diff = service.diff_de_codigos(request.codigo_antes, request.codigo_depois)
    except ParserError as e:
        raise HTTPException(status_code=400, detail=str(e))

    payload = diff.to_dict()
    payload["mermaid"] = diff.to_mermaid()
    return payload
