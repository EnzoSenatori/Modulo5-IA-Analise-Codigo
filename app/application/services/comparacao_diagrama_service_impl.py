# Implementacao do ComparacaoDiagramaService (US IA-10).

from typing import Iterable, List, Set, Tuple

from app.application.ports.driving.comparacao_diagrama_service import (
    ComparacaoDiagramaService,
)
from app.application.ports.driving.estrutura_service import EstruturaService
from app.domain.entidades.componente import Componente
from app.domain.entidades.diff_arquitetural import (
    ComponenteAlterado,
    DiffArquitetural,
)
from app.domain.entidades.estrutura_arquitetural import EstruturaArquitetural
from app.domain.entidades.relacao import Relacao


class ComparacaoDiagramaServiceImpl(ComparacaoDiagramaService):

    def __init__(self, estrutura_service: EstruturaService):
        self._estrutura = estrutura_service

    def diff_de_codigos(self, codigo_antes: str, codigo_depois: str) -> DiffArquitetural:
        antes = self._estrutura.gerar_diagrama(codigo_antes)
        depois = self._estrutura.gerar_diagrama(codigo_depois)
        diff = self.diff_de_estruturas(antes, depois)
        # Repassamos warnings do pipeline pra dentro do diff (LLM indisponivel etc).
        for w in (antes.warnings + depois.warnings):
            if w not in diff.warnings:
                diff.warnings.append(w)
        return diff

    def diff_de_estruturas(
        self,
        antes: EstruturaArquitetural,
        depois: EstruturaArquitetural,
    ) -> DiffArquitetural:
        warnings: List[str] = []
        if antes.linguagem != depois.linguagem:
            warnings.append(
                f"Linguagens diferentes nos dois lados: '{antes.linguagem}' vs '{depois.linguagem}'."
            )

        nomes_antes = {c.nome: c for c in antes.componentes}
        nomes_depois = {c.nome: c for c in depois.componentes}

        adicionados = [c for n, c in nomes_depois.items() if n not in nomes_antes]
        removidos = [c for n, c in nomes_antes.items() if n not in nomes_depois]

        alterados: List[ComponenteAlterado] = []
        for nome in nomes_antes.keys() & nomes_depois.keys():
            ca = self._comparar_componente(nomes_antes[nome], nomes_depois[nome])
            if ca.tem_mudanca():
                alterados.append(ca)

        relacoes_antes = self._normalizar_relacoes(antes.relacoes)
        relacoes_depois = self._normalizar_relacoes(depois.relacoes)
        # Filtra so relacoes onde origem e destino existem no respectivo lado
        # (evita ruido com relacoes "orfas" — mesmo criterio do to_mermaid original).
        relacoes_antes = self._descartar_orfas(antes.relacoes, set(nomes_antes.keys()))
        relacoes_depois = self._descartar_orfas(depois.relacoes, set(nomes_depois.keys()))

        chaves_antes = {self._chave(r) for r in relacoes_antes}
        chaves_depois = {self._chave(r) for r in relacoes_depois}

        adicionadas_rel = [r for r in relacoes_depois if self._chave(r) not in chaves_antes]
        removidas_rel = [r for r in relacoes_antes if self._chave(r) not in chaves_depois]

        return DiffArquitetural(
            componentes_adicionados=adicionados,
            componentes_removidos=removidos,
            componentes_alterados=alterados,
            relacoes_adicionadas=adicionadas_rel,
            relacoes_removidas=removidas_rel,
            warnings=warnings,
        )

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    @staticmethod
    def _comparar_componente(antes: Componente, depois: Componente) -> ComponenteAlterado:
        ma, md = set(antes.metodos), set(depois.metodos)
        aa, ad = set(antes.atributos), set(depois.atributos)
        return ComponenteAlterado(
            nome=antes.nome,
            metodos_adicionados=sorted(md - ma),
            metodos_removidos=sorted(ma - md),
            atributos_adicionados=sorted(ad - aa),
            atributos_removidos=sorted(aa - ad),
            responsabilidade_alterada=antes.responsabilidade != depois.responsabilidade,
            responsabilidade_antes=antes.responsabilidade,
            responsabilidade_depois=depois.responsabilidade,
        )

    @staticmethod
    def _normalizar_relacoes(rels: Iterable[Relacao]) -> List[Relacao]:
        # Sem dedupe agressivo aqui — o set de chaves abaixo ja faz isso.
        return list(rels)

    @staticmethod
    def _descartar_orfas(rels: Iterable[Relacao], nomes_validos: Set[str]) -> List[Relacao]:
        return [r for r in rels if r.origem in nomes_validos and r.destino in nomes_validos]

    @staticmethod
    def _chave(r: Relacao) -> Tuple[str, str, str]:
        # Identidade da relacao = (origem, destino, tipo). Ignoramos 'fonte' (ast/llm)
        # pra nao registrar como "alteracao" quando o LLM passa a inferir o que ja existia via heranca.
        return (r.origem, r.destino, r.tipo)
