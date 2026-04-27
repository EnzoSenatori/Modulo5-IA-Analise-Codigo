from dataclasses import dataclass, field
from typing import List


@dataclass
class Componente:
    """Representa uma unidade de código (classe ou função) no diagrama de arquitetura."""
    nome: str
    tipo: str  # "classe" (futuro: "funcao")
    metodos: List[str] = field(default_factory=list)
    atributos: List[str] = field(default_factory=list)
    responsabilidade: str = ""
