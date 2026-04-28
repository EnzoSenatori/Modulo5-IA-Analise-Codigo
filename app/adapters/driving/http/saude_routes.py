from fastapi import APIRouter, Depends

from app.application.ports.driving.saude_service import SaudeService
from app.config.composition_root import CompositionRoot

router = APIRouter(prefix="/saude", tags=["Saúde"])


def get_saude_service() -> SaudeService:
    return CompositionRoot().get_saude_service()


@router.get("/ia")
async def verificar_saude_ia(
    deep: bool = False,
    service: SaudeService = Depends(get_saude_service),
):
    """
    Health-check do subsistema de IA: verifica provedor LLM, cache e banco.

    - **deep=False** (default): inspeção dos adapters injetados, sem I/O.
      Resposta garantida em < 200ms.
    - **deep=true**: ping ativo no LLM com timeout estrito de 100ms. Pode
      detectar Gemini fora do ar / chave inválida. Latência adicional.

    Atende à US IA-12.
    """
    status = service.verificar_saude(deep=deep)
    return status.to_dict()
