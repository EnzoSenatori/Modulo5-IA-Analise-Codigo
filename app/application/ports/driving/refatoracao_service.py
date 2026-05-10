# Porta driving: RefatoracaoService (US IA-05)

from abc import ABC, abstractmethod

from app.domain.entidades.sugestao_refatoracao import RelatorioRefatoracao


class RefatoracaoService(ABC):

    @abstractmethod
    def sugerir(self, codigo: str) -> RelatorioRefatoracao:
        """
        Aplica detectores deterministicos (AST puro) sobre o codigo e devolve
        sugestoes ranqueadas por linha. Mesmo input -> mesmo output (determinismo).
        Levanta CodigoVazioError se codigo vazio, ParserError em sintaxe invalida.
        """
        pass
