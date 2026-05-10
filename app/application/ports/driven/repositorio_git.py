# Porta driven: RepositorioGit (US IA-11)
# Le arquivos e lista mudancas de PRs no GitHub.

from abc import ABC, abstractmethod
from typing import List, Optional


class RepositorioGit(ABC):

    @abstractmethod
    def listar_arquivos_python_no_pr(
        self, repositorio: str, pr_numero: int,
    ) -> List[str]:
        """Lista arquivos .py mudados no PR (relativos a raiz do repo)."""
        pass

    @abstractmethod
    def obter_arquivo(
        self, repositorio: str, sha: str, caminho: str,
    ) -> Optional[str]:
        """
        Busca o conteudo do arquivo no commit especifico.
        Retorna None se o arquivo nao existir naquele ref (arquivo novo no head, ou removido).
        """
        pass
