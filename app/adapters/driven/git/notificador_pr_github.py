# Adaptador driven: posta comentarios em PRs do GitHub via Issues API (US IA-11).

import logging
from typing import List, Optional

import httpx

from app.application.ports.driven.notificador_pr import NotificadorPR


_logger = logging.getLogger("ia.notificador_pr")


class NotificadorPRGitHubHTTP(NotificadorPR):

    def __init__(
        self,
        base_url: str = "https://api.github.com",
        token: Optional[str] = None,
        timeout_segundos: float = 10.0,
    ):
        self._base = base_url.rstrip("/")
        self._token = token
        self._timeout = timeout_segundos

    def comentar_pr(self, repositorio: str, pr_numero: int, mensagem: str) -> Optional[int]:
        if not self._token:
            _logger.warning("GITHUB_TOKEN ausente — nao consigo postar comentario no PR.")
            return None
        url = f"{self._base}/repos/{repositorio}/issues/{pr_numero}/comments"
        headers = {
            "Accept": "application/vnd.github+json",
            "Authorization": f"Bearer {self._token}",
        }
        try:
            with httpx.Client(timeout=self._timeout) as cliente:
                resposta = cliente.post(url, headers=headers, json={"body": mensagem})
        except httpx.HTTPError as e:
            _logger.warning("Erro de rede ao postar no PR %s: %s", pr_numero, e)
            return None

        if resposta.status_code in (200, 201):
            return (resposta.json() or {}).get("id")
        _logger.warning(
            "GitHub retornou %s ao postar no PR %s: %s",
            resposta.status_code, pr_numero, resposta.text[:200],
        )
        return None


class NotificadorPRFake(NotificadorPR):
    """Para testes — registra cada chamada."""

    def __init__(self):
        self.chamadas: List[dict] = []
        self._proximo_id = 1
        self._falhar: bool = False

    def fazer_falhar(self) -> None:
        self._falhar = True

    def comentar_pr(self, repositorio: str, pr_numero: int, mensagem: str) -> Optional[int]:
        if self._falhar:
            return None
        registro = {
            "repositorio": repositorio,
            "pr_numero": pr_numero,
            "mensagem": mensagem,
            "id": self._proximo_id,
        }
        self.chamadas.append(registro)
        self._proximo_id += 1
        return registro["id"]
