"""Driving port do serviço de documentação (IA-08)."""
from __future__ import annotations

from typing import Protocol

from app.domain.entidades.relatorio_drift import RelatorioDrift


class DocumentacaoService(Protocol):
    """Contrato para o caso de uso de drift de documentação."""

    def detectar_drift(self, repo: str, ref: str = "HEAD") -> RelatorioDrift:
        """Detecta divergências entre o README e o código no commit indicado."""
