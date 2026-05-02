"""Driven port do repositório git.

Contrato mínimo necessário à IA-08; outras USs (IA-01..IA-11) podem
estender com métodos adicionais sem quebrar este contrato.
"""
from __future__ import annotations

from typing import Protocol


class RepositorioGit(Protocol):
    """Contrato para acesso a um repositório git."""

    def hash_commit(self, repo: str, ref: str = "HEAD") -> str:
        """Resolve a ref para o hash completo do commit."""

    def obter_readme(self, repo: str, ref: str = "HEAD") -> str:
        """Devolve o conteúdo do README do repositório no commit indicado."""

    def obter_codigo(self, repo: str, ref: str = "HEAD") -> str:
        """Devolve uma representação textual do código-fonte do repositório."""
