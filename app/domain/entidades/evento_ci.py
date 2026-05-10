# Entidade de dominio: EventoCI (US IA-11)
# Representa um webhook do GitHub que vamos processar para comentar em PR.

from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Any, Dict, Optional
import uuid


class TipoEventoGitHub(Enum):
    PULL_REQUEST_OPENED = "pull_request.opened"
    PULL_REQUEST_SYNCHRONIZE = "pull_request.synchronize"
    PULL_REQUEST_REOPENED = "pull_request.reopened"
    PULL_REQUEST_FECHADO = "pull_request.closed"
    PING = "ping"
    OUTRO = "outro"

    @classmethod
    def from_header_e_action(cls, evento_header: str, action: str) -> "TipoEventoGitHub":
        chave = f"{evento_header}.{action}" if action else evento_header
        for membro in cls:
            if membro.value == chave:
                return membro
        return cls.OUTRO


# Eventos que disparam analise — todos os outros sao registrados mas ignorados.
ALVOS_PROCESSAMENTO = frozenset({
    TipoEventoGitHub.PULL_REQUEST_OPENED,
    TipoEventoGitHub.PULL_REQUEST_SYNCHRONIZE,
    TipoEventoGitHub.PULL_REQUEST_REOPENED,
})


@dataclass(frozen=True)
class EventoCI:
    tipo: TipoEventoGitHub
    repositorio: str
    pr_numero: Optional[int]
    pr_head_sha: Optional[str]
    pr_base_sha: Optional[str]
    payload_bruto: Dict[str, Any] = field(default_factory=dict)
    recebido_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    # Resultado do processamento (preenchido depois pelo service)
    processado_em: Optional[datetime] = None
    sucesso: Optional[bool] = None
    resultado: Optional[str] = None  # mensagem postada ou erro

    @property
    def deve_processar(self) -> bool:
        return self.tipo in ALVOS_PROCESSAMENTO

    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "tipo": self.tipo.value,
            "repositorio": self.repositorio,
            "pr_numero": self.pr_numero,
            "pr_head_sha": self.pr_head_sha,
            "pr_base_sha": self.pr_base_sha,
            "recebido_em": self.recebido_em.isoformat(),
            "processado_em": self.processado_em.isoformat() if self.processado_em else None,
            "sucesso": self.sucesso,
            "resultado": self.resultado,
        }


def construir_evento_de_payload(
    evento_header: str,
    payload: Dict[str, Any],
) -> EventoCI:
    tipo = TipoEventoGitHub.from_header_e_action(evento_header, payload.get("action", ""))
    pr = payload.get("pull_request") or {}
    repositorio = ((payload.get("repository") or {}).get("full_name")) or ""
    return EventoCI(
        tipo=tipo,
        repositorio=repositorio,
        pr_numero=(pr.get("number") if pr else None) or payload.get("number"),
        pr_head_sha=((pr.get("head") or {}).get("sha")) if pr else None,
        pr_base_sha=((pr.get("base") or {}).get("sha")) if pr else None,
        payload_bruto=payload,
    )
