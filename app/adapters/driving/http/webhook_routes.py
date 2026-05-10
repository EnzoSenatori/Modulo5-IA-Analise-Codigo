# Rota HTTP do webhook GitHub (US IA-11).
# Valida HMAC, registra evento, agenda processamento async, devolve 200 imediatamente.

import hashlib
import hmac
import json
import logging
from typing import Any, Dict, Optional

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Request

from app.application.ports.driving.integracao_ci_service import IntegracaoCIService
from app.config import settings
from app.config.composition_root import CompositionRoot
from app.domain.entidades.evento_ci import construir_evento_de_payload


_logger = logging.getLogger("ia.webhook")


router = APIRouter(prefix="/webhook", tags=["Webhook"])


def get_integracao_service() -> IntegracaoCIService:
    return CompositionRoot().get_integracao_ci_service()


def _validar_assinatura(corpo_bruto: bytes, assinatura_header: str, secret: str) -> bool:
    if not assinatura_header or not secret:
        return False
    if not assinatura_header.startswith("sha256="):
        return False
    esperada = "sha256=" + hmac.new(
        secret.encode("utf-8"), corpo_bruto, hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(esperada, assinatura_header)


@router.post("/github")
async def receber_webhook_github(
    request: Request,
    background: BackgroundTasks,
    servico: IntegracaoCIService = Depends(get_integracao_service),
):
    """
    Recebe webhook do GitHub. Sempre devolve 200 (ou 401 se HMAC nao bate)
    para nao bloquear o CI. O processamento real roda em background.
    """
    corpo = await request.body()
    secret = settings.GITHUB_WEBHOOK_SECRET
    assinatura = request.headers.get("X-Hub-Signature-256", "")
    if secret and not _validar_assinatura(corpo, assinatura, secret):
        _logger.warning("Webhook recebido com assinatura HMAC invalida.")
        raise HTTPException(status_code=401, detail="assinatura invalida")

    try:
        payload: Dict[str, Any] = json.loads(corpo or b"{}")
    except json.JSONDecodeError:
        raise HTTPException(status_code=400, detail="payload nao e JSON valido")

    evento_header = request.headers.get("X-GitHub-Event", "")
    evento = construir_evento_de_payload(evento_header, payload)
    servico.registrar_evento(evento)

    if not evento.deve_processar:
        return {"status": "ignored", "tipo": evento.tipo.value, "evento_id": evento.id}

    background.add_task(servico.processar_evento, evento.id)
    return {"status": "accepted", "evento_id": evento.id}


@router.get("/github/eventos")
def listar_eventos(
    repositorio: Optional[str] = None,
    processado: Optional[bool] = None,
    limite: int = 50,
    servico: IntegracaoCIService = Depends(get_integracao_service),
):
    eventos = servico.listar_eventos(repositorio=repositorio, processado=processado, limite=limite)
    return {"eventos": [e.to_dict() for e in eventos]}
