from abc import ABC, abstractmethod
from typing import Dict, List, Tuple

from app.domain.entidades.relacao import Relacao


class ProvedorLLM(ABC):
    """Porta de saída (driven). Inferência semântica via LLM."""

    @abstractmethod
    def inferir_relacoes_e_responsabilidades(
        self,
        codigo: str,
        nomes_componentes: List[str],
    ) -> Tuple[Dict[str, str], List[Relacao]]:
        """
        Retorna (responsabilidades_por_nome, relacoes_inferidas).

        Levanta LLMError se a chamada não puder ser concluída.
        Implementações DEVEM filtrar relações com classes fora de
        `nomes_componentes` (defesa contra alucinação) antes de retornar.
        """
        pass

    @abstractmethod
    def ping(self, timeout_ms: int = 100) -> Tuple[bool, str]:
        """
        Faz uma checagem rápida de disponibilidade do provedor.

        Retorna (sucesso, mensagem). Não levanta exceção — sempre retorna
        um par (False, motivo) quando algo falha. Usado pelo health check
        em modo `deep=True`.
        """
        pass
