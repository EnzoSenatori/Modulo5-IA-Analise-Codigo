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
