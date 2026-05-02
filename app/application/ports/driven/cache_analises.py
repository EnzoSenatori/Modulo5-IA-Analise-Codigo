"""Driven port do cache de análises (IA-13)."""
from __future__ import annotations

from typing import Any, Dict, Optional, Protocol

from app.domain.entidades.analise_cacheada import AnaliseCacheada, TTL_PADRAO_DIAS


class CacheAnalises(Protocol):
    """Contrato para um cache de análises indexado por commit + tipo."""

    def obter(
        self, hash_commit: str, tipo_analise: str
    ) -> Optional[AnaliseCacheada]:
        """Retorna a análise cacheada, ou None se não existir ou estiver expirada."""

    def salvar(
        self,
        hash_commit: str,
        tipo_analise: str,
        payload: Dict[str, Any],
        ttl_dias: int = TTL_PADRAO_DIAS,
    ) -> AnaliseCacheada:
        """Persiste uma análise no cache (upsert)."""

    def remover_expirados(self) -> int:
        """Remove entradas com TTL vencido. Retorna quantas foram apagadas."""
