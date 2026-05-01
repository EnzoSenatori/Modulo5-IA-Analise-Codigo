from abc import ABC, abstractmethod
from app.domain.entidades.diagnostico_qualidade import DiagnosticoQualidade

class AnalisadorEstatico(ABC):
    """
    Interface para ferramentas de análise de código.
    """

    @abstractmethod
    def analisar_complexidade_e_acoplamento(self, codigo_fonte: str) -> DiagnosticoQualidade:
        pass