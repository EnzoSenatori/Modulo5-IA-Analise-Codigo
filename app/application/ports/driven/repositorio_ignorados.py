# Porta driven: RepositorioIgnorados (US IA-07)
# Persiste lista de componentes que o time marcou para ignorar na analise.

from abc import ABC, abstractmethod
from typing import List, Optional

from app.domain.entidades.mapa_cobertura import ComponenteIgnorado


class RepositorioIgnorados(ABC):

    @abstractmethod
    def salvar(self, ignorado: ComponenteIgnorado) -> None:
        """Insere ou substitui (upsert por nome)."""
        pass

    @abstractmethod
    def obter(self, nome: str) -> Optional[ComponenteIgnorado]:
        pass

    @abstractmethod
    def listar(self) -> List[ComponenteIgnorado]:
        pass

    @abstractmethod
    def remover(self, nome: str) -> bool:
        pass

    @abstractmethod
    def nomes_ignorados(self) -> set:
        """Retorna so os nomes — usado pelo service pra filtrar rapido."""
        pass
