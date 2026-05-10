# Porta driving: CasoDeUsoService (US IA-03)

from abc import ABC, abstractmethod

from app.domain.entidades.caso_de_uso import DiagramaCasoDeUso


class CasoDeUsoService(ABC):

    @abstractmethod
    def extrair_de_texto(self, texto: str, formato: str = "markdown") -> DiagramaCasoDeUso:
        """
        Extrai atores e casos de uso de texto markdown ou plain text.
        Suporta user stories no formato "Como X, eu quero Y para Z".
        Marca palavras vagas como ambiguidades.
        """
        pass

    @abstractmethod
    def extrair_de_pdf(self, conteudo_bytes: bytes) -> DiagramaCasoDeUso:
        """Extrai texto do PDF via pypdf e processa como markdown."""
        pass
