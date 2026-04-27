import time
from typing import Optional

from app.application.ports.driving.saude_service import SaudeService
from app.application.ports.driven.provedor_llm import ProvedorLLM
from app.domain.entidades.status_saude import StatusSaude, CheckSaude


class SaudeServiceImpl(SaudeService):
    """
    Verifica saúde de subsistemas sem fazer I/O externo (garante <200ms).

    Os checks são feitos por inspeção do tipo dos adapters injetados, sem
    chamar a API do Gemini de fato. Cache e Banco aparecem como
    `not_configured` enquanto não houver adapters reais para eles.
    """

    def __init__(
        self,
        provedor_llm: Optional[ProvedorLLM] = None,
        cache_adapter=None,
        banco_adapter=None,
    ):
        self._provedor_llm = provedor_llm
        self._cache = cache_adapter
        self._banco = banco_adapter

    def verificar_saude(self) -> StatusSaude:
        inicio = time.perf_counter()

        check_llm = self._check_provedor_llm()
        check_cache = self._check_cache()
        check_banco = self._check_banco()

        checks = {
            "provedor_llm": check_llm,
            "cache": check_cache,
            "banco": check_banco,
        }

        status_geral = self._consolidar_status(checks)
        tempo_ms = int((time.perf_counter() - inicio) * 1000)

        return StatusSaude(
            status=status_geral,
            checks=checks,
            tempo_ms=tempo_ms,
        )

    def _check_provedor_llm(self) -> CheckSaude:
        if self._provedor_llm is None:
            return CheckSaude(status="unhealthy", detalhe={"motivo": "não injetado"})

        tipo = type(self._provedor_llm).__name__
        # Fake é dev-mode: funciona, mas não é o LLM real → degraded.
        if tipo == "AdaptadorLLMFake":
            return CheckSaude(
                status="degraded",
                detalhe={"tipo": tipo, "motivo": "modo dev sem chave Gemini"},
            )
        return CheckSaude(status="healthy", detalhe={"tipo": tipo})

    def _check_cache(self) -> CheckSaude:
        if self._cache is None:
            return CheckSaude(status="not_configured")
        return CheckSaude(
            status="healthy",
            detalhe={"tipo": type(self._cache).__name__},
        )

    def _check_banco(self) -> CheckSaude:
        if self._banco is None:
            return CheckSaude(status="not_configured")
        return CheckSaude(
            status="healthy",
            detalhe={"tipo": type(self._banco).__name__},
        )

    def _consolidar_status(self, checks):
        """healthy se nenhum unhealthy/degraded; degraded se algum degraded; unhealthy se algum unhealthy."""
        statuses = {c.status for c in checks.values()}
        if "unhealthy" in statuses:
            return "unhealthy"
        if "degraded" in statuses:
            return "degraded"
        return "healthy"
