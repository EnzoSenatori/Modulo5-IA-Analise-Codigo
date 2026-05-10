# Porta driving: IntegracaoCIService (US IA-11)

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.evento_ci import EventoCI


class IntegracaoCIService(ABC):

    @abstractmethod
    def registrar_evento(self, evento: EventoCI) -> None:
        """Persiste o evento; nao processa ainda (eh sincrono e rapido)."""
        pass

    @abstractmethod
    def processar_evento(self, evento_id: str) -> EventoCI:
        """
        Roda em background: busca arquivos, gera diff (IA-10) e posta comentario.
        Sempre devolve o evento atualizado (com sucesso=True/False e resultado preenchidos);
        nao levanta excecao para nao quebrar o background task.
        """
        pass

    @abstractmethod
    def listar_eventos(
        self,
        repositorio: Optional[str] = None,
        processado: Optional[bool] = None,
        limite: int = 50,
    ) -> List[EventoCI]:
        pass
