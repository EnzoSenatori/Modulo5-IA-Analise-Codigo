# Implementacao do RefatoracaoService (US IA-05).
# Roda detectores deterministicos sobre o AST e devolve sugestoes ordenadas.

import ast
from typing import List

from app.application.ports.driving.refatoracao_service import RefatoracaoService
from app.application.services.detectores_refatoracao import (
    DETECTORES_PADRAO,
    Detector,
)
from app.domain.entidades.sugestao_refatoracao import (
    RelatorioRefatoracao,
    SugestaoRefatoracao,
)
from app.domain.excecoes import CodigoVazioError, ParserError


class RefatoracaoServiceImpl(RefatoracaoService):

    def __init__(self, detectores: List[Detector] = None):
        # Lista padrao garante mesma sequencia de detectores -> mesma saida.
        self._detectores = detectores if detectores is not None else DETECTORES_PADRAO

    def sugerir(self, codigo: str) -> RelatorioRefatoracao:
        if not codigo or not codigo.strip():
            raise CodigoVazioError("codigo fonte vazio.")

        try:
            tree = ast.parse(codigo)
        except SyntaxError as e:
            raise ParserError(f"erro de sintaxe no codigo fonte: {e}") from e

        linhas = codigo.splitlines()
        todas: List[SugestaoRefatoracao] = []
        for detector in self._detectores:
            todas.extend(detector.detectar(tree, linhas))

        # Ordem deterministica: linha asc, depois categoria, depois titulo.
        todas.sort(key=lambda s: s.chave_ordenacao)
        return RelatorioRefatoracao(sugestoes=todas)
