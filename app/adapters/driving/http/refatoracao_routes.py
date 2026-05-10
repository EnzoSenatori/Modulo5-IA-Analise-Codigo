# Rotas REST para sugestoes de refatoracao (US IA-05).

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.ports.driving.refatoracao_service import RefatoracaoService
from app.config.composition_root import CompositionRoot
from app.domain.excecoes import CodigoVazioError, ParserError


router = APIRouter(prefix="/refatoracao", tags=["Refatoracao"])


def get_refatoracao_service() -> RefatoracaoService:
    return CompositionRoot().get_refatoracao_service()


class SugerirRequest(BaseModel):
    codigo: str


@router.post("/sugerir")
def sugerir(
    payload: SugerirRequest,
    service: RefatoracaoService = Depends(get_refatoracao_service),
):
    """
    Aplica detectores deterministicos sobre o codigo Python e devolve sugestoes
    com snippet antes/depois e estimativa de esforco. Mesmo input -> mesmo output.
    """
    try:
        relatorio = service.sugerir(payload.codigo)
    except CodigoVazioError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except ParserError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return relatorio.to_dict()
