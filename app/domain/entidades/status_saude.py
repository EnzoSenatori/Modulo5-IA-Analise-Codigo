from dataclasses import dataclass, field, asdict
from typing import Dict, Any


@dataclass
class CheckSaude:
    """Resultado de uma verificação individual de subsistema."""
    status: str  # "healthy" | "degraded" | "unhealthy" | "not_configured"
    detalhe: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StatusSaude:
    """Resultado consolidado do health-check."""
    status: str  # "healthy" | "degraded" | "unhealthy"
    checks: Dict[str, CheckSaude] = field(default_factory=dict)
    tempo_ms: int = 0

    def to_dict(self) -> Dict[str, Any]:
        return {
            "status": self.status,
            "checks": {nome: asdict(c) for nome, c in self.checks.items()},
            "tempo_ms": self.tempo_ms,
        }
