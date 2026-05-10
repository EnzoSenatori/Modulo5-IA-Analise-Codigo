# Rotas REST para analise de cobertura (US IA-07).

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.ports.driving.cobertura_service import CoberturaService
from app.config.composition_root import CompositionRoot
from app.domain.excecoes import CoberturaInvalidaError, IgnorarInvalidoError


router = APIRouter(prefix="/cobertura", tags=["Cobertura"])


def get_cobertura_service() -> CoberturaService:
    return CompositionRoot().get_cobertura_service()


class AnalisarRequest(BaseModel):
    codigo_producao: str
    codigo_testes: str = ""


class IgnorarRequest(BaseModel):
    nome: str
    motivo: str
    marcado_por: str


@router.post("/analisar")
def analisar(
    payload: AnalisarRequest,
    service: CoberturaService = Depends(get_cobertura_service),
):
    """
    Analisa cobertura cruzando codigo prod e codigo de teste.
    Devolve componentes sem teste ranqueados por criticidade.
    """
    try:
        mapa = service.analisar(
            codigo_producao=payload.codigo_producao,
            codigo_testes=payload.codigo_testes,
        )
    except CoberturaInvalidaError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return mapa.to_dict()


@router.post("/ignorar", status_code=201)
def marcar_ignorar(
    payload: IgnorarRequest,
    service: CoberturaService = Depends(get_cobertura_service),
):
    try:
        ignorado = service.marcar_ignorar(
            nome=payload.nome, motivo=payload.motivo, marcado_por=payload.marcado_por,
        )
    except IgnorarInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return ignorado.to_dict()


@router.delete("/ignorar/{nome}", status_code=204)
def desmarcar_ignorar(nome: str, service: CoberturaService = Depends(get_cobertura_service)):
    if not service.desmarcar_ignorar(nome):
        raise HTTPException(status_code=404, detail=f"'{nome}' nao estava na lista de ignorados.")
    return None


@router.get("/ignorados")
def listar_ignorados(service: CoberturaService = Depends(get_cobertura_service)):
    return {"ignorados": [i.to_dict() for i in service.listar_ignorados()]}
