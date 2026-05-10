# Implementacao do ImpactoService (US IA-06).
# AST puro: para cada arquivo de teste, checa imports e usos do simbolo alvo.

import ast
from typing import Dict, List, Optional, Set, Tuple

from app.application.ports.driving.impacto_service import ImpactoService
from app.domain.entidades.matriz_impacto import (
    AlvoRefatoracao,
    NivelConfianca,
    RelatorioImpacto,
    TesteAfetado,
)
from app.domain.excecoes import ImpactoInvalidoError


class ImpactoServiceImpl(ImpactoService):

    def analisar(
        self,
        alvo: AlvoRefatoracao,
        testes: Dict[str, str],
    ) -> RelatorioImpacto:
        if not alvo.nome_simbolo or not alvo.nome_simbolo.strip():
            raise ImpactoInvalidoError("nome_simbolo do alvo e obrigatorio.")
        if testes is None:
            testes = {}

        afetados: List[TesteAfetado] = []
        sem_impacto: List[str] = []
        nao_parseaveis: List[str] = []

        nome_alvo = alvo.nome_simbolo.strip()
        modulo_alvo = (alvo.modulo or "").strip()

        for arquivo, codigo in testes.items():
            if not codigo or not codigo.strip():
                sem_impacto.append(arquivo)
                continue
            try:
                tree = ast.parse(codigo)
            except SyntaxError:
                nao_parseaveis.append(arquivo)
                continue

            resultado = self._avaliar_arquivo(tree, nome_alvo, modulo_alvo)
            if resultado is None:
                sem_impacto.append(arquivo)
            else:
                afetados.append(TesteAfetado(
                    arquivo=arquivo,
                    confianca=resultado[0],
                    motivos=resultado[1],
                    referencias_diretas=resultado[2],
                ))

        return RelatorioImpacto(
            alvo=alvo,
            afetados=afetados,
            sem_impacto=tuple(sem_impacto),
            nao_parseaveis=tuple(nao_parseaveis),
        )

    # ------------------------------------------------------------------
    # Avaliacao de um arquivo
    # ------------------------------------------------------------------

    @staticmethod
    def _avaliar_arquivo(
        tree: ast.AST,
        nome_alvo: str,
        modulo_alvo: str,
    ) -> Optional[Tuple[NivelConfianca, List[str], int]]:
        """
        Devolve (nivel, motivos, refs) se afetado; None se sem impacto.
        Sinais avaliados:
          - import direto do simbolo (from modulo_alvo import nome_alvo) -> ALTA potencial
          - import do modulo pai (from modulo_alvo import outra) -> BAIXA
          - import wildcard (from modulo_alvo import *) -> BAIXA
          - import do modulo (import modulo_alvo) -> MEDIA
          - usos do nome_alvo no corpo (ast.Name) -> aumenta refs e confianca
          - patches de mock referenciando o simbolo -> ALTA
        """
        importou_simbolo_direto = False
        importou_modulo_alvo = False
        importou_wildcard_do_alvo = False
        importou_outro_do_modulo = False

        # Walk imports
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                modulo = node.module or ""
                modulos_casam = (
                    modulo_alvo
                    and (modulo == modulo_alvo or modulo.endswith("." + modulo_alvo))
                )
                for alias in node.names:
                    if alias.name == "*":
                        if not modulo_alvo or modulos_casam:
                            importou_wildcard_do_alvo = True
                    elif alias.name == nome_alvo:
                        importou_simbolo_direto = True
                    elif modulos_casam:
                        importou_outro_do_modulo = True
            elif isinstance(node, ast.Import):
                for alias in node.names:
                    if modulo_alvo and (
                        alias.name == modulo_alvo or alias.name.endswith("." + modulo_alvo)
                    ):
                        importou_modulo_alvo = True
                    elif alias.name == nome_alvo:
                        # casos como 'import X' onde X eh o proprio nome
                        importou_simbolo_direto = True

        # Conta usos do nome no corpo
        refs_diretas = sum(
            1 for node in ast.walk(tree)
            if isinstance(node, ast.Name) and node.id == nome_alvo
        )

        # Detecta patches/mocks que referenciam o simbolo via string
        # Ex: @patch('modulo_alvo.NomeAlvo') ou patch('app.x.NomeAlvo')
        refs_em_strings = 0
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, str):
                if (
                    nome_alvo in node.value.split(".")
                    or node.value.endswith("." + nome_alvo)
                    or node.value == nome_alvo
                ):
                    refs_em_strings += 1

        motivos: List[str] = []
        if importou_simbolo_direto:
            motivos.append(f"importa diretamente '{nome_alvo}'")
        if importou_modulo_alvo:
            motivos.append(f"importa o modulo '{modulo_alvo}' inteiro")
        if importou_wildcard_do_alvo:
            motivos.append(f"importa wildcard de '{modulo_alvo}'")
        if importou_outro_do_modulo:
            motivos.append(f"importa outro simbolo de '{modulo_alvo}'")
        if refs_diretas > 0:
            motivos.append(f"usa '{nome_alvo}' {refs_diretas} vez(es) no corpo")
        if refs_em_strings > 0:
            motivos.append(f"referencia '{nome_alvo}' em string ({refs_em_strings} vez(es) — possivel mock/patch)")

        # Decide o nivel
        nivel: Optional[NivelConfianca] = None
        if importou_simbolo_direto and (refs_diretas > 0 or refs_em_strings > 0):
            nivel = NivelConfianca.ALTA
        elif importou_simbolo_direto:
            nivel = NivelConfianca.MEDIA
        elif importou_modulo_alvo and refs_diretas > 0:
            nivel = NivelConfianca.MEDIA
        elif importou_modulo_alvo:
            nivel = NivelConfianca.BAIXA
        elif importou_wildcard_do_alvo:
            nivel = NivelConfianca.BAIXA
        elif importou_outro_do_modulo and (refs_diretas > 0 or refs_em_strings > 0):
            # O simbolo alvo nao foi importado, mas aparece — provavel uso transitivo
            nivel = NivelConfianca.MEDIA
        elif importou_outro_do_modulo:
            nivel = NivelConfianca.BAIXA
        elif refs_em_strings > 0:
            # So aparece em string — patch de modulo nao importado eh sinal mais fraco
            nivel = NivelConfianca.BAIXA

        if nivel is None:
            return None
        return (nivel, motivos, refs_diretas)
