# Porta driven: RepositorioWebhooks (US IA-11)
# Persiste eventos recebidos para auditoria e retry.

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.evento_ci import EventoCI


class RepositorioWebhooks(ABC):

    @abstractmethod
    def salvar(self, evento: EventoCI) -> None:
        """Insere ou atualiza por id (upsert — usado tambem para anotar resultado)."""
        pass

    @abstractmethod
    def obter(self, evento_id: str) -> Optional[EventoCI]:
        pass

    @abstractmethod
    def listar(
        self,
        repositorio: Optional[str] = None,
        processado: Optional[bool] = None,
        limite: int = 50,
    ) -> List[EventoCI]:
        pass
