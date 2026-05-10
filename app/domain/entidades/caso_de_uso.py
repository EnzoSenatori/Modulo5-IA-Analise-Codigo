# Entidades de dominio para diagramas de caso de uso (US IA-03).
# 100% deterministicas — geradas por regex sobre texto de requisitos.

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Tuple


@dataclass(frozen=True)
class Ator:
    nome: str

    def to_dict(self) -> Dict[str, Any]:
        return {"nome": self.nome}


@dataclass(frozen=True)
class CasoDeUso:
    descricao: str           # acao que o ator quer realizar
    atores: Tuple[str, ...]  # podem ser varios atores realizando o mesmo
    beneficio: str = ""      # opcional: clausula "para X"
    linha_origem: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "descricao": self.descricao,
            "atores": list(self.atores),
            "beneficio": self.beneficio,
            "linha_origem": self.linha_origem,
        }


@dataclass(frozen=True)
class Ambiguidade:
    linha: int
    trecho: str
    motivo: str   # ex: "uso de palavra vaga 'etc'"
    palavra: str  # palavra/padrao gatilho

    def to_dict(self) -> Dict[str, Any]:
        return {
            "linha": self.linha,
            "trecho": self.trecho,
            "motivo": self.motivo,
            "palavra": self.palavra,
        }


@dataclass
class DiagramaCasoDeUso:
    atores: List[Ator] = field(default_factory=list)
    casos_uso: List[CasoDeUso] = field(default_factory=list)
    ambiguidades: List[Ambiguidade] = field(default_factory=list)
    avisos: List[str] = field(default_factory=list)
    mermaid: str = ""

    @property
    def total_casos(self) -> int:
        return len(self.casos_uso)

    @property
    def total_atores(self) -> int:
        return len(self.atores)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total_atores": self.total_atores,
            "total_casos": self.total_casos,
            "total_ambiguidades": len(self.ambiguidades),
            "atores": [a.to_dict() for a in self.atores],
            "casos_uso": [c.to_dict() for c in self.casos_uso],
            "ambiguidades": [a.to_dict() for a in self.ambiguidades],
            "avisos": list(self.avisos),
            "mermaid": self.mermaid,
        }
