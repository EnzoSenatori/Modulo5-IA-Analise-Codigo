from abc import ABC, abstractmethod
from app.domain.entidades.especificacao_api import EspecificacaoApi

class ParserCodigo(ABC):
    """
    Porta de saída (Driven Port).
    Define como o sistema deve solicitar a extração de dados de um código-fonte.
    """

    @abstractmethod
    def extrair_especificacao(self, codigo_fonte: str) -> EspecificacaoApi:
        """
        Recebe uma string contendo o código-fonte (ex: um arquivo .py)
        e retorna uma entidade EspecificacaoApi preenchida.
        """
        pass