# Porta driving: ComparacaoDiagramaService (US IA-10)

from abc import ABC, abstractmethod

from app.domain.entidades.diff_arquitetural import DiffArquitetural
from app.domain.entidades.estrutura_arquitetural import EstruturaArquitetural


class ComparacaoDiagramaService(ABC):

    @abstractmethod
    def diff_de_estruturas(
        self,
        antes: EstruturaArquitetural,
        depois: EstruturaArquitetural,
    ) -> DiffArquitetural:
        """Diff puro a partir de dois snapshots ja extraidos."""
        pass

    @abstractmethod
    def diff_de_codigos(
        self,
        codigo_antes: str,
        codigo_depois: str,
    ) -> DiffArquitetural:
        """
        Orquestra: roda IA-01 nos dois codigos e devolve o diff.
        Util para comparar dois commits via PR.
        """
        pass
