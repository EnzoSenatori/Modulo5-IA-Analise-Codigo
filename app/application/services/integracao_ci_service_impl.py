# Implementacao do IntegracaoCIService (US IA-11).
# Usa ComparacaoDiagramaService (IA-10) para gerar o diff.
# Nao levanta excecoes em processar_evento — registra falha e segue.

import logging
from dataclasses import replace
from datetime import datetime, timezone
from typing import List, Optional, Tuple

from app.application.ports.driven.notificador_pr import NotificadorPR
from app.application.ports.driven.repositorio_git import RepositorioGit
from app.application.ports.driven.repositorio_webhooks import RepositorioWebhooks
from app.application.ports.driving.comparacao_diagrama_service import (
    ComparacaoDiagramaService,
)
from app.application.ports.driving.integracao_ci_service import IntegracaoCIService
from app.domain.entidades.diff_arquitetural import DiffArquitetural
from app.domain.entidades.evento_ci import EventoCI, TipoEventoGitHub


_logger = logging.getLogger("ia.ci")


class IntegracaoCIServiceImpl(IntegracaoCIService):

    def __init__(
        self,
        repositorio_webhooks: RepositorioWebhooks,
        repositorio_git: RepositorioGit,
        notificador: NotificadorPR,
        comparacao: ComparacaoDiagramaService,
    ):
        self._webhooks = repositorio_webhooks
        self._git = repositorio_git
        self._notificador = notificador
        self._comparacao = comparacao

    def registrar_evento(self, evento: EventoCI) -> None:
        self._webhooks.salvar(evento)

    def listar_eventos(
        self,
        repositorio: Optional[str] = None,
        processado: Optional[bool] = None,
        limite: int = 50,
    ) -> List[EventoCI]:
        return self._webhooks.listar(
            repositorio=repositorio, processado=processado, limite=limite,
        )

    def processar_evento(self, evento_id: str) -> EventoCI:
        evento = self._webhooks.obter(evento_id)
        if evento is None:
            _logger.warning("Evento %s nao encontrado para processar.", evento_id)
            return EventoCI(
                tipo=TipoEventoGitHub.OUTRO,
                repositorio="", pr_numero=None, pr_head_sha=None, pr_base_sha=None,
            )

        if not evento.deve_processar:
            return self._marcar(evento, sucesso=True, resultado=f"ignorado: {evento.tipo.value}")

        if not (evento.repositorio and evento.pr_numero and evento.pr_head_sha and evento.pr_base_sha):
            return self._marcar(evento, sucesso=False, resultado="payload sem dados de PR esperados")

        try:
            arquivos = self._git.listar_arquivos_python_no_pr(evento.repositorio, evento.pr_numero)
        except Exception as e:
            _logger.warning("Falha ao listar arquivos do PR %s: %s", evento.pr_numero, e)
            return self._marcar(evento, sucesso=False, resultado=f"erro ao listar arquivos: {e}")

        if not arquivos:
            mensagem = self._mensagem_sem_python()
            self._postar(evento, mensagem)
            return self._marcar(evento, sucesso=True, resultado=mensagem)

        diffs_por_arquivo: List[Tuple[str, DiffArquitetural]] = []
        warnings_globais: List[str] = []

        for arquivo in arquivos:
            antes = self._safe_obter(evento.repositorio, evento.pr_base_sha, arquivo)
            depois = self._safe_obter(evento.repositorio, evento.pr_head_sha, arquivo)

            try:
                diff = self._comparacao.diff_de_codigos(
                    self._codigo_ou_placeholder(antes),
                    self._codigo_ou_placeholder(depois),
                )
            except Exception as e:
                warnings_globais.append(f"`{arquivo}`: falha ao analisar — {e}")
                continue

            if diff.tem_mudancas() or antes is None or depois is None:
                diffs_por_arquivo.append((arquivo, diff))

        mensagem = self._formatar_markdown(evento, diffs_por_arquivo, warnings_globais)
        comentario_id = self._postar(evento, mensagem)
        sucesso = comentario_id is not None
        resultado = (
            f"comentario {comentario_id} postado" if sucesso else "falha ao postar comentario"
        )
        return self._marcar(evento, sucesso=sucesso, resultado=resultado)

    # ------------------------------------------------------------------
    # Helpers
    # ------------------------------------------------------------------

    def _safe_obter(self, repo: str, sha: str, caminho: str) -> Optional[str]:
        try:
            return self._git.obter_arquivo(repo, sha, caminho)
        except Exception as e:
            _logger.info("Arquivo %s@%s indisponivel: %s", caminho, sha[:7], e)
            return None

    @staticmethod
    def _codigo_ou_placeholder(codigo: Optional[str]) -> str:
        # ComparacaoDiagramaService usa o EstruturaService que rejeita string vazia,
        # entao colocamos um modulo neutro pra representar "nao havia nada antes/depois".
        if not codigo or not codigo.strip():
            return "# arquivo inexistente neste ref\n"
        return codigo

    def _postar(self, evento: EventoCI, mensagem: str) -> Optional[int]:
        try:
            return self._notificador.comentar_pr(evento.repositorio, evento.pr_numero, mensagem)
        except Exception as e:
            _logger.warning("Falha ao postar no PR %s: %s", evento.pr_numero, e)
            return None

    def _marcar(self, evento: EventoCI, sucesso: bool, resultado: str) -> EventoCI:
        atualizado = replace(
            evento,
            processado_em=datetime.now(timezone.utc),
            sucesso=sucesso,
            resultado=resultado,
        )
        self._webhooks.salvar(atualizado)
        return atualizado

    @staticmethod
    def _mensagem_sem_python() -> str:
        return (
            "## Analise Arquitetural Automatica (IA-11)\n\n"
            "Nenhum arquivo Python modificado neste PR — sem analise estrutural a fazer.\n\n"
            "*Mensagem informativa. Nao bloqueia CI.*"
        )

    @staticmethod
    def _formatar_markdown(
        evento: EventoCI,
        diffs: List[Tuple[str, DiffArquitetural]],
        warnings_globais: List[str],
    ) -> str:
        linhas: List[str] = []
        linhas.append("## Analise Arquitetural Automatica (IA-11)")
        linhas.append("")
        linhas.append(
            f"Comparando `{evento.pr_base_sha[:7]}` -> `{evento.pr_head_sha[:7]}` "
            f"em `{evento.repositorio}`."
        )
        linhas.append("")

        total_componentes_add = sum(len(d.componentes_adicionados) for _, d in diffs)
        total_componentes_rem = sum(len(d.componentes_removidos) for _, d in diffs)
        total_componentes_alt = sum(len(d.componentes_alterados) for _, d in diffs)
        total_relacoes_add = sum(len(d.relacoes_adicionadas) for _, d in diffs)
        total_relacoes_rem = sum(len(d.relacoes_removidas) for _, d in diffs)

        linhas.append("### Resumo")
        linhas.append(f"- Componentes adicionados: **{total_componentes_add}**")
        linhas.append(f"- Componentes removidos: **{total_componentes_rem}**")
        linhas.append(f"- Componentes alterados: **{total_componentes_alt}**")
        linhas.append(
            f"- Relacoes (+/-): **{total_relacoes_add}** / **{total_relacoes_rem}**"
        )
        linhas.append("")

        if not diffs:
            linhas.append("Nenhuma mudanca arquitetural detectada nos arquivos modificados.")
        else:
            linhas.append("### Por arquivo")
            for arquivo, d in diffs:
                resumo = d.resumo()
                linhas.append(
                    f"- `{arquivo}`: +{resumo['componentes_adicionados']} "
                    f"-{resumo['componentes_removidos']} "
                    f"~{resumo['componentes_alterados']} componentes"
                )

        if warnings_globais:
            linhas.append("")
            linhas.append("### Avisos")
            for w in warnings_globais:
                linhas.append(f"- {w}")

        linhas.append("")
        linhas.append("---")
        linhas.append("*Gerado automaticamente. Nao bloqueia CI.*")
        return "\n".join(linhas)
