"""Entidade AnaliseCacheada (IA-13)."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, timezone
from typing import Any, Dict


TTL_PADRAO_DIAS = 30


@dataclass(frozen=True)
class AnaliseCacheada:
    """Análise persistida em cache, indexada por hash de commit + tipo de análise.

    Usada para manter disponibilidade quando o provedor de IA está fora do ar:
    o resultado anterior associado ao mesmo commit é devolvido junto a um
    aviso indicando que a resposta veio do cache.
    """

    hash_commit: str
    tipo_analise: str
    payload: Dict[str, Any]
    criado_em: datetime
    ttl_dias: int = TTL_PADRAO_DIAS

    @property
    def expira_em(self) -> datetime:
        return self.criado_em + timedelta(days=self.ttl_dias)

    @property
    def expirado(self) -> bool:
        return datetime.now(timezone.utc) >= self.expira_em

    @property
    def aviso(self) -> str:
        return (
            f"Resultado servido do cache (commit {self.hash_commit[:8]}, "
            f"gerado em {self.criado_em.isoformat()}, expira em "
            f"{self.expira_em.isoformat()}). A IA pode estar indisponível."
        )
