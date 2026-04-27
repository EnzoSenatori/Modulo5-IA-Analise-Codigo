from abc import ABC, abstractmethod

from app.domain.entidades.estrutura_arquitetural import EstruturaArquitetural


class EstruturaService(ABC):
    """Porta de entrada (driving). Casos de uso de geração de diagrama."""

    @abstractmethod
    def gerar_diagrama(self, codigo: str) -> EstruturaArquitetural:
        """Recebe código-fonte Python e retorna a estrutura arquitetural."""
        pass
