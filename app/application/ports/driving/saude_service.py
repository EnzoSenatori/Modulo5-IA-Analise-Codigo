from abc import ABC, abstractmethod

from app.domain.entidades.status_saude import StatusSaude


class SaudeService(ABC):
    """Porta de entrada (driving). Verificação de saúde do sistema de IA."""

    @abstractmethod
    def verificar_saude(self) -> StatusSaude:
        """Retorna o status consolidado dos subsistemas (LLM, cache, banco)."""
        pass
