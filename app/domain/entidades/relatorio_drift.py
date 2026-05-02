"""Entidade RelatorioDrift (IA-08)."""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Optional, Tuple


@dataclass(frozen=True)
class DivergenciaDoc:
    """Uma divergência específica detectada entre README e código."""

    tipo: str  # ex.: "endpoint_ausente", "modulo_obsoleto", "parametro_divergente"
    descricao: str
    referencia_readme: Optional[str] = None
    referencia_codigo: Optional[str] = None


@dataclass(frozen=True)
class RelatorioDrift:
    """Relatório de drift entre documentação (README) e código (IA-08)."""

    hash_commit: str
    divergencias: Tuple[DivergenciaDoc, ...]
    decisoes_arquiteturais: Tuple[str, ...]
    resumo_documentacao: str
    origem: str = "analise"  # "analise" | "cache"
    aviso: Optional[str] = None
    gerado_em: datetime = field(
        default_factory=lambda: datetime.now(timezone.utc)
    )

    @property
    def possui_drift(self) -> bool:
        return len(self.divergencias) > 0
