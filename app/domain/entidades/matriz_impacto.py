# Entidades de dominio para analise de impacto de refatoracao (US IA-06).

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Tuple


class NivelConfianca(Enum):
    ALTA = "alta"      # importacao direta + uso explicito do simbolo
    MEDIA = "media"    # importacao direta sem uso aparente, OU import transitivo
    BAIXA = "baixa"    # import wildcard, ou import do modulo pai


@dataclass(frozen=True)
class AlvoRefatoracao:
    """O simbolo que sera refatorado."""
    nome_simbolo: str
    modulo: str = ""

    def to_dict(self) -> Dict[str, Any]:
        return {"nome_simbolo": self.nome_simbolo, "modulo": self.modulo}


@dataclass
class TesteAfetado:
    arquivo: str
    confianca: NivelConfianca
    motivos: List[str] = field(default_factory=list)
    referencias_diretas: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "arquivo": self.arquivo,
            "confianca": self.confianca.value,
            "motivos": list(self.motivos),
            "referencias_diretas": self.referencias_diretas,
        }


@dataclass
class RelatorioImpacto:
    alvo: AlvoRefatoracao
    afetados: List[TesteAfetado] = field(default_factory=list)
    sem_impacto: Tuple[str, ...] = ()
    nao_parseaveis: Tuple[str, ...] = ()

    @property
    def total_afetados(self) -> int:
        return len(self.afetados)

    @property
    def por_confianca(self) -> Dict[str, int]:
        out = {n.value: 0 for n in NivelConfianca}
        for t in self.afetados:
            out[t.confianca.value] += 1
        return out

    def to_dict(self) -> Dict[str, Any]:
        ordem_conf = {NivelConfianca.ALTA: 0, NivelConfianca.MEDIA: 1, NivelConfianca.BAIXA: 2}
        afetados_ordenados = sorted(
            self.afetados,
            key=lambda t: (ordem_conf[t.confianca], t.arquivo),
        )
        return {
            "alvo": self.alvo.to_dict(),
            "total_afetados": self.total_afetados,
            "total_sem_impacto": len(self.sem_impacto),
            "por_confianca": self.por_confianca,
            "afetados": [t.to_dict() for t in afetados_ordenados],
            "sem_impacto": list(self.sem_impacto),
            "nao_parseaveis": list(self.nao_parseaveis),
        }
