"""Implementação do serviço de documentação (IA-08)."""
from __future__ import annotations

import re
from typing import Any, Dict, Tuple

from app.application.ports.driven.cache_analises import CacheAnalises
from app.application.ports.driven.provedor_llm import ProvedorLLM
from app.application.ports.driven.repositorio_git import RepositorioGit
from app.application.ports.driving.documentacao_service import DocumentacaoService
from app.domain.entidades.relatorio_drift import DivergenciaDoc, RelatorioDrift


TIPO_ANALISE = "drift"
LIMITE_DOC_LONGO = 4000  # caracteres antes de acionar resumo via LLM

# Heurísticas para preservar decisões arquiteturais ao resumir o README:
# capturamos seções cujo cabeçalho indica arquitetura/ADR/decisão e as
# anexamos integralmente ao relatório.
_PADROES_DECISAO_ARQ = (
    re.compile(
        r"^#+\s*(arquitetura|architecture|adr|architectural decision).*$",
        re.IGNORECASE | re.MULTILINE,
    ),
    re.compile(
        r"^#+\s*(decis(?:ã|a)o|decision|trade-?off).*$",
        re.IGNORECASE | re.MULTILINE,
    ),
)


class DocumentacaoServiceImpl(DocumentacaoService):
    """Caso de uso: comparar README vs código e produzir RelatorioDrift."""

    def __init__(
        self,
        repositorio_git: RepositorioGit,
        provedor_llm: ProvedorLLM,
        cache: CacheAnalises,
    ) -> None:
        self._git = repositorio_git
        self._llm = provedor_llm
        self._cache = cache

    def detectar_drift(self, repo: str, ref: str = "HEAD") -> RelatorioDrift:
        hash_commit = self._git.hash_commit(repo, ref)

        try:
            readme = self._git.obter_readme(repo, ref)
            codigo = self._git.obter_codigo(repo, ref)

            decisoes = _extrair_decisoes_arquiteturais(readme)
            resumo = self._resumir_se_longo(readme)
            divergencias = self._detectar_divergencias(resumo, codigo)

            relatorio = RelatorioDrift(
                hash_commit=hash_commit,
                divergencias=divergencias,
                decisoes_arquiteturais=decisoes,
                resumo_documentacao=resumo,
                origem="analise",
            )
            self._cache.salvar(
                hash_commit, TIPO_ANALISE, _serializar(relatorio)
            )
            return relatorio
        except Exception:
            cacheado = self._cache.obter(hash_commit, TIPO_ANALISE)
            if cacheado is None:
                raise
            return _desserializar(cacheado.payload, aviso=cacheado.aviso)

    def _resumir_se_longo(self, doc: str) -> str:
        if len(doc) <= LIMITE_DOC_LONGO:
            return doc
        return self._llm.resumir(doc, max_caracteres=LIMITE_DOC_LONGO)

    def _detectar_divergencias(
        self, resumo: str, codigo: str
    ) -> Tuple[DivergenciaDoc, ...]:
        bruto = self._llm.detectar_drift(resumo, codigo)
        return tuple(
            DivergenciaDoc(
                tipo=item.get("tipo", "indeterminado"),
                descricao=item.get("descricao", ""),
                referencia_readme=item.get("referencia_readme"),
                referencia_codigo=item.get("referencia_codigo"),
            )
            for item in bruto.get("divergencias", [])
        )


def _extrair_decisoes_arquiteturais(readme: str) -> Tuple[str, ...]:
    encontrados = []
    for padrao in _PADROES_DECISAO_ARQ:
        for match in padrao.finditer(readme):
            inicio = match.start()
            proxima = readme.find("\n# ", match.end())
            secao = readme[inicio: proxima if proxima != -1 else len(readme)]
            encontrados.append(secao.strip())
    return tuple(encontrados)


def _serializar(rel: RelatorioDrift) -> Dict[str, Any]:
    return {
        "hash_commit": rel.hash_commit,
        "divergencias": [
            {
                "tipo": d.tipo,
                "descricao": d.descricao,
                "referencia_readme": d.referencia_readme,
                "referencia_codigo": d.referencia_codigo,
            }
            for d in rel.divergencias
        ],
        "decisoes_arquiteturais": list(rel.decisoes_arquiteturais),
        "resumo_documentacao": rel.resumo_documentacao,
    }


def _desserializar(payload: Dict[str, Any], *, aviso: str) -> RelatorioDrift:
    return RelatorioDrift(
        hash_commit=payload["hash_commit"],
        divergencias=tuple(
            DivergenciaDoc(
                tipo=d.get("tipo", ""),
                descricao=d.get("descricao", ""),
                referencia_readme=d.get("referencia_readme"),
                referencia_codigo=d.get("referencia_codigo"),
            )
            for d in payload.get("divergencias", [])
        ),
        decisoes_arquiteturais=tuple(payload.get("decisoes_arquiteturais", [])),
        resumo_documentacao=payload.get("resumo_documentacao", ""),
        origem="cache",
        aviso=aviso,
    )
