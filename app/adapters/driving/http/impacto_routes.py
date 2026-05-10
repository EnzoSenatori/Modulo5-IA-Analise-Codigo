# Rotas REST para analise de impacto de refatoracao (US IA-06).

from typing import Dict

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.ports.driving.impacto_service import ImpactoService
from app.config.composition_root import CompositionRoot
from app.domain.entidades.matriz_impacto import AlvoRefatoracao
from app.domain.excecoes import ImpactoInvalidoError


router = APIRouter(prefix="/impacto", tags=["Impacto"])


def get_impacto_service() -> ImpactoService:
    return CompositionRoot().get_impacto_service()


class AlvoRequest(BaseModel):
    nome_simbolo: str
    modulo: str = ""


class AnalisarImpactoRequest(BaseModel):
    alvo: AlvoRequest
    testes: Dict[str, str]   # arquivo -> codigo do teste


@router.post("/analisar")
def analisar(
    payload: AnalisarImpactoRequest,
    service: ImpactoService = Depends(get_impacto_service),
):
    """
    Analisa quais testes (dict arquivo->codigo) sao afetados se o simbolo do alvo
    for refatorado. Cada teste afetado vem com nivel de confianca + motivos.
    """
    alvo = AlvoRefatoracao(
        nome_simbolo=payload.alvo.nome_simbolo,
        modulo=payload.alvo.modulo,
    )
    try:
        relatorio = service.analisar(alvo=alvo, testes=payload.testes or {})
    except ImpactoInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return relatorio.to_dict()
