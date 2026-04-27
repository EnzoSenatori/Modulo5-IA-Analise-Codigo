from abc import ABC, abstractmethod
from typing import Dict, Any

class OpenApiService(ABC):
    """
    Porta de entrada (Driving Port).
    Define as ações que o usuário (via Portal) pode solicitar sobre OpenAPI.
    """

    @abstractmethod
    def gerar_especificacao_do_codigo(self, codigo_fonte: str) -> Dict[str, Any]:
        """
        Orquestra o processo: chama o parser, converte para entidade e
        retorna o dicionário pronto para o formato JSON/OAS 3.0.
        """
        pass