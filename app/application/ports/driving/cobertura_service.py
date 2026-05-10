# Porta driving: CoberturaService (US IA-07)

from abc import ABC, abstractmethod
from typing import List

from app.domain.entidades.mapa_cobertura import ComponenteIgnorado, MapaCobertura


class CoberturaService(ABC):

    @abstractmethod
    def analisar(self, codigo_producao: str, codigo_testes: str) -> MapaCobertura:
        """
        Compara componentes do codigo prod com tests, devolve mapa com lacunas
        ranqueadas por criticidade. Componentes na lista de ignorados sao filtrados.
        """
        pass

    @abstractmethod
    def marcar_ignorar(self, nome: str, motivo: str, marcado_por: str) -> ComponenteIgnorado:
        """Marca um componente como ignorado — nao aparece em sem_cobertura."""
        pass

    @abstractmethod
    def desmarcar_ignorar(self, nome: str) -> bool:
        pass

    @abstractmethod
    def listar_ignorados(self) -> List[ComponenteIgnorado]:
        pass
