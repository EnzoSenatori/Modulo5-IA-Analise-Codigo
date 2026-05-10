# Implementacao do CoberturaService (US IA-07).
# Heuristicas:
#   - Classe X tem teste se existe TestX, XTest, XTests no codigo de teste,
#     OU funcao test_*_x_* (substring de X em snake_case)
#   - Criticidade = #metodos*1 + #atributos*0.5 + (5 se sufixo critico) + (#dependentes*1.5)

import ast
import logging
import re
from typing import List, Set

from app.application.ports.driven.parser_codigo import ParserCodigo
from app.application.ports.driven.repositorio_ignorados import RepositorioIgnorados
from app.application.ports.driving.cobertura_service import CoberturaService
from app.domain.entidades.componente import Componente
from app.domain.entidades.mapa_cobertura import (
    SUFIXOS_CRITICOS,
    ComponenteIgnorado,
    ComponenteSemCobertura,
    MapaCobertura,
)
from app.domain.excecoes import (
    CoberturaInvalidaError,
    IgnorarInvalidoError,
    ParserError,
)


_logger = logging.getLogger("ia.cobertura")


class CoberturaServiceImpl(CoberturaService):

    def __init__(
        self,
        parser: ParserCodigo,
        repositorio_ignorados: RepositorioIgnorados,
    ):
        self._parser = parser
        self._ignorados = repositorio_ignorados

    # ------------------------------------------------------------------
    # Analise
    # ------------------------------------------------------------------

    def analisar(self, codigo_producao: str, codigo_testes: str) -> MapaCobertura:
        if not codigo_producao or not codigo_producao.strip():
            raise CoberturaInvalidaError("codigo_producao e obrigatorio.")

        warnings: List[str] = []

        try:
            componentes_prod = self._parser.extrair_estrutura(codigo_producao)
        except ParserError as e:
            raise CoberturaInvalidaError(f"codigo_producao invalido: {e}") from e

        # Codigo de teste eh opcional — se vazio, nada esta coberto.
        alvos_classes, funcoes_teste = self._extrair_alvos_de_teste(codigo_testes, warnings)

        # Pega heranças para calcular dependentes (proxy de criticidade).
        try:
            relacoes = self._parser.extrair_herancas(codigo_producao)
        except ParserError:
            relacoes = []
        dependentes_de = self._contar_dependentes(componentes_prod, relacoes)

        nomes_ignorados = self._ignorados.nomes_ignorados()

        sem_cobertura: List[ComponenteSemCobertura] = []
        cobertos: List[Componente] = []
        ignorados_encontrados: List[Componente] = []

        for c in componentes_prod:
            if c.nome in nomes_ignorados:
                ignorados_encontrados.append(c)
                continue
            if self._tem_teste(c.nome, alvos_classes, funcoes_teste):
                cobertos.append(c)
            else:
                score = self._calcular_criticidade(c, dependentes_de.get(c.nome, 0))
                motivos = self._motivos_criticidade(c, dependentes_de.get(c.nome, 0))
                sem_cobertura.append(ComponenteSemCobertura(
                    componente=c, criticidade_score=score, motivos_criticidade=motivos,
                ))

        sem_cobertura.sort(key=lambda x: x.criticidade_score, reverse=True)

        return MapaCobertura(
            sem_cobertura=sem_cobertura,
            cobertos=cobertos,
            ignorados=ignorados_encontrados,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Lista de ignorados (CRUD)
    # ------------------------------------------------------------------

    def marcar_ignorar(self, nome: str, motivo: str, marcado_por: str) -> ComponenteIgnorado:
        if not nome or not nome.strip():
            raise IgnorarInvalidoError("nome do componente e obrigatorio.")
        if not motivo or not motivo.strip():
            raise IgnorarInvalidoError("motivo e obrigatorio (rastreabilidade).")
        if not marcado_por or not marcado_por.strip():
            raise IgnorarInvalidoError("marcado_por e obrigatorio.")
        ignorado = ComponenteIgnorado(
            nome=nome.strip(), motivo=motivo.strip(), marcado_por=marcado_por.strip(),
        )
        self._ignorados.salvar(ignorado)
        return ignorado

    def desmarcar_ignorar(self, nome: str) -> bool:
        return self._ignorados.remover(nome)

    def listar_ignorados(self) -> List[ComponenteIgnorado]:
        return self._ignorados.listar()

    # ------------------------------------------------------------------
    # Heuristicas
    # ------------------------------------------------------------------

    @staticmethod
    def _extrair_alvos_de_teste(codigo_testes: str, warnings: List[str]) -> tuple:
        """Devolve (set de nomes-alvo de classe, set de nomes de funcao test_* lower)."""
        alvos: Set[str] = set()
        funcs: Set[str] = set()
        if not codigo_testes or not codigo_testes.strip():
            warnings.append("codigo_testes vazio — todos os componentes serao marcados como sem cobertura.")
            return alvos, funcs

        try:
            tree = ast.parse(codigo_testes)
        except SyntaxError as e:
            warnings.append(f"codigo_testes nao parseou ({e}); cobertura nao foi avaliada.")
            return alvos, funcs

        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                nome = node.name
                # Heuristica: TestX, XTest, XTests
                if nome.startswith("Test") and len(nome) > 4:
                    alvos.add(nome[4:])
                elif nome.endswith("Tests") and len(nome) > 5:
                    alvos.add(nome[:-5])
                elif nome.endswith("Test") and len(nome) > 4:
                    alvos.add(nome[:-4])
            elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.name.startswith("test_"):
                    funcs.add(node.name.lower())
        return alvos, funcs

    @staticmethod
    def _tem_teste(componente_nome: str, alvos_classes: Set[str], funcoes_teste: Set[str]) -> bool:
        if componente_nome in alvos_classes:
            return True
        # Funcao de teste cita a classe: test_user_service_login -> UserService
        nome_snake = _camel_para_snake(componente_nome)
        return any(nome_snake in func for func in funcoes_teste)

    @staticmethod
    def _calcular_criticidade(c: Componente, dependentes: int) -> float:
        score = len(c.metodos) * 1.0 + len(c.atributos) * 0.5
        if any(c.nome.endswith(s) for s in SUFIXOS_CRITICOS):
            score += 5.0
        score += dependentes * 1.5
        return score

    @staticmethod
    def _motivos_criticidade(c: Componente, dependentes: int) -> List[str]:
        motivos = []
        if c.metodos:
            motivos.append(f"{len(c.metodos)} metodo(s)")
        if c.atributos:
            motivos.append(f"{len(c.atributos)} atributo(s) de estado")
        sufixo = next((s for s in SUFIXOS_CRITICOS if c.nome.endswith(s)), None)
        if sufixo:
            motivos.append(f"papel arquitetural critico ({sufixo})")
        if dependentes > 0:
            motivos.append(f"{dependentes} componente(s) dependem dela")
        return motivos

    @staticmethod
    def _contar_dependentes(componentes, relacoes) -> dict:
        contagem: dict = {c.nome: 0 for c in componentes}
        for r in relacoes:
            if r.destino in contagem and r.origem != r.destino:
                contagem[r.destino] += 1
        return contagem


_REGEX_CAMEL = re.compile(r"(?<!^)(?=[A-Z])")


def _camel_para_snake(nome: str) -> str:
    return _REGEX_CAMEL.sub("_", nome).lower()
