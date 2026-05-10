# Porta driven: NotificadorPR (US IA-11)
# Posta comentarios em PRs do GitHub.

from abc import ABC, abstractmethod
from typing import Optional


class NotificadorPR(ABC):

    @abstractmethod
    def comentar_pr(self, repositorio: str, pr_numero: int, mensagem: str) -> Optional[int]:
        """
        Posta um comentario no PR. Retorna o id do comentario do GitHub em sucesso,
        None se a postagem falhou (a falha eh logada mas nao quebra o pipeline:
        o objetivo eh nao bloquear o CI).
        """
        pass
