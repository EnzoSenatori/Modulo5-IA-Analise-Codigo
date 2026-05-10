# Rotas HTTP para extracao de diagramas de caso de uso (US IA-03).

import base64

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from app.application.ports.driving.caso_de_uso_service import CasoDeUsoService
from app.config.composition_root import CompositionRoot
from app.domain.excecoes import (
    FormatoNaoSuportadoError,
    PDFInvalidoError,
    RequisitosVaziosError,
)


router = APIRouter(prefix="/casos-uso", tags=["CasosDeUso"])


def get_caso_uso_service() -> CasoDeUsoService:
    return CompositionRoot().get_caso_uso_service()


class ExtrairTextoRequest(BaseModel):
    texto: str
    formato: str = "markdown"  # markdown | md | txt | plain


class ExtrairPDFRequest(BaseModel):
    conteudo_base64: str = Field(..., description="PDF codificado em base64")


@router.post("/extrair-de-texto")
def extrair_de_texto(
    payload: ExtrairTextoRequest,
    service: CasoDeUsoService = Depends(get_caso_uso_service),
):
    """
    Recebe texto markdown/plain com user stories ('Como X, eu quero Y') e
    devolve atores, casos de uso, ambiguidades e diagrama Mermaid.
    """
    try:
        diagrama = service.extrair_de_texto(payload.texto, formato=payload.formato)
    except RequisitosVaziosError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except FormatoNaoSuportadoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return diagrama.to_dict()


@router.post("/extrair-de-pdf")
def extrair_de_pdf(
    payload: ExtrairPDFRequest,
    service: CasoDeUsoService = Depends(get_caso_uso_service),
):
    """Decodifica PDF base64, extrai texto via pypdf e processa como user stories."""
    try:
        conteudo_bytes = base64.b64decode(payload.conteudo_base64, validate=True)
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"base64 invalido: {e}")
    try:
        diagrama = service.extrair_de_pdf(conteudo_bytes)
    except PDFInvalidoError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except RequisitosVaziosError as e:
        raise HTTPException(status_code=400, detail=str(e))
    return diagrama.to_dict()
