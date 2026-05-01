from abc import ABC, abstractmethod
from typing import Dict, Any

class QualidadeService(ABC):
    """
    Interface (Porta de Entrada) para o serviço de qualidade.
    Define o que o mundo externo pode pedir para este módulo.
    """

    @abstractmethod
    def obter_diagnostico_completo(self, codigo_fonte: str) -> Dict[str, Any]:
        """
        Deve retornar um dicionário com score, acoplamento e sugestões.
        """
        pass