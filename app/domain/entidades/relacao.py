from dataclasses import dataclass


@dataclass
class Relacao:
    """Representa uma aresta entre componentes no diagrama de arquitetura."""
    origem: str
    destino: str
    tipo: str  # "heranca" | "usa" | "depende_de"
    fonte: str  # "ast" | "llm"
