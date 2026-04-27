from typing import List

from app.application.ports.driving.estrutura_service import EstruturaService
from app.application.ports.driven.parser_codigo import ParserCodigo
from app.application.ports.driven.provedor_llm import ProvedorLLM
from app.domain.entidades.estrutura_arquitetural import EstruturaArquitetural
from app.domain.entidades.relacao import Relacao
from app.domain.excecoes import LLMError, ParserError


class EstruturaServiceImpl(EstruturaService):
    """Orquestra AST + LLM para gerar diagrama de classes."""

    def __init__(self, parser_codigo: ParserCodigo, provedor_llm: ProvedorLLM):
        self._parser = parser_codigo
        self._llm = provedor_llm

    def gerar_diagrama(self, codigo: str) -> EstruturaArquitetural:
        if not codigo or not codigo.strip():
            raise ParserError("O código fonte fornecido está vazio.")

        componentes = self._parser.extrair_estrutura(codigo)
        herancas = self._parser.extrair_herancas(codigo)

        warnings: List[str] = []
        relacoes_llm: List[Relacao] = []

        if componentes:
            try:
                responsabilidades, relacoes_llm = (
                    self._llm.inferir_relacoes_e_responsabilidades(
                        codigo, [c.nome for c in componentes]
                    )
                )
                for c in componentes:
                    c.responsabilidade = responsabilidades.get(c.nome, "")
            except LLMError as e:
                warnings.append(
                    f"LLM indisponível — relações semânticas e responsabilidades omitidas. ({e})"
                )

        return EstruturaArquitetural(
            componentes=componentes,
            relacoes=herancas + relacoes_llm,
            warnings=warnings,
        )
