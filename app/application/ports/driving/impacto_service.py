# Porta driving: ImpactoService (US IA-06)

from abc import ABC, abstractmethod
from typing import Dict

from app.domain.entidades.matriz_impacto import AlvoRefatoracao, RelatorioImpacto


class ImpactoService(ABC):

    @abstractmethod
    def analisar(
        self,
        alvo: AlvoRefatoracao,
        testes: Dict[str, str],
    ) -> RelatorioImpacto:
        """
        Para cada teste em `testes` (dict arquivo->codigo), avalia se ele eh
        afetado pela refatoracao do `alvo` e atribui nivel de confianca.
        """
        pass
