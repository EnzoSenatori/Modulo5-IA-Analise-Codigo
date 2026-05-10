# Entidades de dominio: MapaCobertura (US IA-07).
# Identifica componentes prod sem testes e os ranqueia por criticidade.

from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, List

from app.domain.entidades.componente import Componente


# Sufixos arquitetural-mente "criticos" — componentes com esses nomes geralmente
# carregam logica de negocio importante e sem teste sao mais arriscados.
SUFIXOS_CRITICOS = ("Service", "Manager", "Controller", "Repository", "Handler", "Gateway", "UseCase")


@dataclass
class ComponenteIgnorado:
    """Componente que o time decidiu ignorar na analise — geralmente codigo legado ou trivial."""
    nome: str
    motivo: str
    marcado_por: str
    marcado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def to_dict(self) -> Dict[str, Any]:
        return {
            "nome": self.nome,
            "motivo": self.motivo,
            "marcado_por": self.marcado_por,
            "marcado_em": self.marcado_em.isoformat(),
        }


@dataclass
class ComponenteSemCobertura:
    componente: Componente
    criticidade_score: float
    motivos_criticidade: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "componente": asdict(self.componente),
            "criticidade_score": round(self.criticidade_score, 2),
            "motivos_criticidade": list(self.motivos_criticidade),
        }


@dataclass
class MapaCobertura:
    sem_cobertura: List[ComponenteSemCobertura]
    cobertos: List[Componente]
    ignorados: List[Componente]
    warnings: List[str] = field(default_factory=list)
    gerado_em: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    @property
    def total_componentes_prod(self) -> int:
        return len(self.sem_cobertura) + len(self.cobertos) + len(self.ignorados)

    @property
    def percentual_cobertura(self) -> float:
        # Considera ignorados como "fora do calculo" — denominador exclui ignorados.
        considerados = len(self.sem_cobertura) + len(self.cobertos)
        if considerados == 0:
            return 100.0
        return round(len(self.cobertos) / considerados * 100, 2)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "gerado_em": self.gerado_em.isoformat(),
            "total_componentes_prod": self.total_componentes_prod,
            "percentual_cobertura": self.percentual_cobertura,
            "resumo": {
                "sem_cobertura": len(self.sem_cobertura),
                "cobertos": len(self.cobertos),
                "ignorados": len(self.ignorados),
            },
            # sem_cobertura ja vem ordenado por criticidade (mais critico primeiro)
            "sem_cobertura": [c.to_dict() for c in self.sem_cobertura],
            "cobertos": [asdict(c) for c in self.cobertos],
            "ignorados": [asdict(c) for c in self.ignorados],
            "warnings": list(self.warnings),
        }
