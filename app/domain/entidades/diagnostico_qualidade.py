from dataclasses import dataclass, field
from typing import List, Dict, Any

@dataclass
class MetricaAcoplamento:
    componente: str
    depende_de: List[str]
    acoplamento_saida: int

@dataclass
class DiagnosticoQualidade:
    score_geral: float
    ciclos_dependencia: List[List[str]]
    analise_acoplamento: List[MetricaAcoplamento]
    sugestoes: List[Dict[str, str]]