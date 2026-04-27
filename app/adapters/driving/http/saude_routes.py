from fastapi import APIRouter, Depends

from app.application.ports.driving.saude_service import SaudeService
from app.config.composition_root import CompositionRoot

router = APIRouter(prefix="/saude", tags=["Saúde"])


def get_saude_service() -> SaudeService:
    return CompositionRoot().get_saude_service()


@router.get("/ia")
async def verificar_saude_ia(service: SaudeService = Depends(get_saude_service)):
    """
    Health-check do subsistema de IA: verifica provedor LLM, cache e banco.
    Resposta garantida em < 200ms (sem I/O externo). Atende à US IA-12.
    """
    status = service.verificar_saude()
    return status.to_dict()
