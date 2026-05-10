# Adaptador driven: GitHub HTTP (US IA-11).
# Le arquivos via Contents API e lista arquivos do PR via Pulls API.

import base64
import logging
from typing import List, Optional

import httpx

from app.application.ports.driven.repositorio_git import RepositorioGit
from app.domain.excecoes import GitHubAPIError


_logger = logging.getLogger("ia.github")


class AdaptadorGitHubHTTP(RepositorioGit):

    def __init__(
        self,
        base_url: str = "https://api.github.com",
        token: Optional[str] = None,
        timeout_segundos: float = 10.0,
    ):
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_segundos

    def listar_arquivos_python_no_pr(
        self, repositorio: str, pr_numero: int,
    ) -> List[str]:
        url = f"{self._base}/repos/{repositorio}/pulls/{pr_numero}/files"
        cabecalhos = self._cabecalhos()
        arquivos: List[str] = []
        pagina = 1
        with httpx.Client(timeout=self._timeout) as cliente:
            while True:
                try:
                    resposta = cliente.get(
                        url, headers=cabecalhos, params={"per_page": 100, "page": pagina},
                    )
                except httpx.HTTPError as e:
                    raise GitHubAPIError(f"erro ao listar arquivos do PR {pr_numero}: {e}") from e

                if resposta.status_code != 200:
                    raise GitHubAPIError(
                        f"GitHub retornou {resposta.status_code} ao listar arquivos do PR: "
                        f"{resposta.text[:200]}"
                    )
                lote = resposta.json() or []
                for item in lote:
                    nome = item.get("filename") or ""
                    if nome.endswith(".py"):
                        arquivos.append(nome)
                if len(lote) < 100:
                    break
                pagina += 1
        return arquivos

    def obter_arquivo(
        self, repositorio: str, sha: str, caminho: str,
    ) -> Optional[str]:
        url = f"{self._base}/repos/{repositorio}/contents/{caminho}"
        cabecalhos = self._cabecalhos()
        try:
            with httpx.Client(timeout=self._timeout) as cliente:
                resposta = cliente.get(url, headers=cabecalhos, params={"ref": sha})
        except httpx.HTTPError as e:
            raise GitHubAPIError(f"erro de rede ao obter {caminho}@{sha[:7]}: {e}") from e

        if resposta.status_code == 404:
            return None
        if resposta.status_code != 200:
            raise GitHubAPIError(
                f"GitHub retornou {resposta.status_code} ao obter {caminho}@{sha[:7]}: "
                f"{resposta.text[:200]}"
            )
        payload = resposta.json()
        encoding = payload.get("encoding")
        if encoding == "base64":
            return base64.b64decode(payload.get("content", "")).decode("utf-8", errors="replace")
        # Arquivos > 1MB nao vem inline; teriamos que usar git/blobs API.
        if payload.get("size", 0) > 1_000_000:
            return None
        return payload.get("content") or ""

    def _cabecalhos(self) -> dict:
        h = {"Accept": "application/vnd.github+json"}
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h


class AdaptadorGitHubFake(RepositorioGit):
    """Implementacao fake para testes — preenche por configuracao."""

    def __init__(self):
        self._arquivos_pr = {}  # (repo, pr) -> [arquivo, ...]
        self._conteudo = {}     # (repo, sha, caminho) -> str | None
        self._falha_listar: Optional[Exception] = None

    def configurar_arquivos_pr(self, repo: str, pr: int, arquivos: List[str]) -> None:
        self._arquivos_pr[(repo, pr)] = list(arquivos)

    def configurar_conteudo(self, repo: str, sha: str, caminho: str, conteudo: Optional[str]) -> None:
        self._conteudo[(repo, sha, caminho)] = conteudo

    def fazer_falhar_listagem(self, exc: Exception) -> None:
        self._falha_listar = exc

    def listar_arquivos_python_no_pr(self, repositorio: str, pr_numero: int) -> List[str]:
        if self._falha_listar:
            raise self._falha_listar
        return list(self._arquivos_pr.get((repositorio, pr_numero), []))

    def obter_arquivo(self, repositorio: str, sha: str, caminho: str) -> Optional[str]:
        return self._conteudo.get((repositorio, sha, caminho))
