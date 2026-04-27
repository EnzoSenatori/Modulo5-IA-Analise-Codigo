from abc import ABC, abstractmethod
from typing import List

from app.domain.entidades.especificacao_api import EspecificacaoApi
from app.domain.entidades.componente import Componente
from app.domain.entidades.relacao import Relacao


class ParserCodigo(ABC):
    """Porta de saída (driven). Extração de informação de código-fonte."""

    @abstractmethod
    def extrair_especificacao(self, codigo_fonte: str) -> EspecificacaoApi:
        """Extrai uma EspecificacaoApi (rotas) — usada pela IA-02."""
        pass

    @abstractmethod
    def extrair_estrutura(self, codigo_fonte: str) -> List[Componente]:
        """Extrai a lista de componentes (classes) do código — usada pela IA-01."""
        pass

    @abstractmethod
    def extrair_herancas(self, codigo_fonte: str) -> List[Relacao]:
        """Extrai relações de herança AST — usada pela IA-01."""
        pass
