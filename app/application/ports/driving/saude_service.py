from abc import ABC, abstractmethod

from app.domain.entidades.status_saude import StatusSaude


class SaudeService(ABC):
    """Porta de entrada (driving). Verificação de saúde do sistema de IA."""

    @abstractmethod
    def verificar_saude(self, deep: bool = False) -> StatusSaude:
        """
        Retorna o status consolidado dos subsistemas (LLM, cache, banco).

        Quando `deep=False` (default) faz só inspeção dos adapters injetados
        — resposta garantida em <200ms, sem I/O externo.

        Quando `deep=True`, além da inspeção, faz um `ping` ativo no provedor
        LLM com timeout estrito. Pode estourar 200ms se o LLM estiver lento;
        o cliente assume essa janela em troca de validação real.
        """
        pass
