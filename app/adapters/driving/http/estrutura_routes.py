from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from app.application.ports.driving.estrutura_service import EstruturaService
from app.config.composition_root import CompositionRoot
from app.domain.excecoes import ParserError

router = APIRouter(prefix="/estrutura", tags=["Estrutura"])


class CodigoFonteRequest(BaseModel):
    codigo: str


def get_estrutura_service() -> EstruturaService:
    return CompositionRoot().get_estrutura_service()


@router.post("/diagrama")
async def gerar_diagrama(
    request: CodigoFonteRequest,
    service: EstruturaService = Depends(get_estrutura_service),
):
    """
    Recebe código Python e retorna o diagrama de classes em JSON estruturado
    + Mermaid `classDiagram`. Atende à US IA-01.
    """
    try:
        estrutura = service.gerar_diagrama(request.codigo)
    except ParserError as e:
        raise HTTPException(status_code=400, detail=str(e))

    payload = estrutura.to_dict()
    payload["mermaid"] = estrutura.to_mermaid()
    return payload
