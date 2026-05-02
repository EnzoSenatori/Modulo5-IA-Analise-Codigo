"""Driven port do provedor de LLM.

Contrato mínimo exposto para a IA-08; outras USs (IA-01..IA-11) podem
estender com métodos adicionais sem quebrar este contrato.
"""
from __future__ import annotations

from typing import Any, Dict, Protocol


class ProvedorLLM(Protocol):
    """Contrato para o provedor de LLM."""

    def resumir(self, texto: str, max_caracteres: int = 4000) -> str:
        """Resume um texto longo respeitando um limite aproximado de caracteres."""

    def detectar_drift(self, resumo_doc: str, codigo: str) -> Dict[str, Any]:
        """Compara documentação resumida com o código e devolve divergências.

        Formato esperado de retorno:
            {
                "divergencias": [
                    {
                        "tipo": str,
                        "descricao": str,
                        "referencia_readme": Optional[str],
                        "referencia_codigo": Optional[str],
                    },
                    ...
                ]
            }
        """
