import time
from typing import Optional

from app.application.ports.driving.saude_service import SaudeService
from app.application.ports.driven.provedor_llm import ProvedorLLM
from app.domain.entidades.status_saude import StatusSaude, CheckSaude

# Timeout do ping em modo deep — escolhido pra balancear "validação real"
# com latência aceitável.
_PING_TIMEOUT_MS = 100


class SaudeServiceImpl(SaudeService):
    """
    Verifica saúde de subsistemas. Modo padrão (deep=False) é introspectivo
    e garante <200ms. Modo deep=True faz ping ativo no LLM com timeout
    estrito.

    Cache e Banco aparecem como `not_configured` enquanto não houver
    adapters reais para eles.
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

    def verificar_saude(self, deep: bool = False) -> StatusSaude:
        inicio = time.perf_counter()

        check_llm = self._check_provedor_llm(deep=deep)
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

    def _check_provedor_llm(self, deep: bool) -> CheckSaude:
        if self._provedor_llm is None:
            return CheckSaude(status="unhealthy", detalhe={"motivo": "não injetado"})

        tipo = type(self._provedor_llm).__name__
        detalhe = {"tipo": tipo}

        # Inspeção: Fake é dev-mode, conta como degraded.
        status_inspecao = "degraded" if tipo == "AdaptadorLLMFake" else "healthy"
        if status_inspecao == "degraded":
            detalhe["motivo"] = "modo dev sem chave Gemini"

        if not deep:
            return CheckSaude(status=status_inspecao, detalhe=detalhe)

        # Modo deep: faz ping ativo. Não joga exceção por design do port.
        ok, mensagem = self._provedor_llm.ping(timeout_ms=_PING_TIMEOUT_MS)
        detalhe["ping"] = mensagem

        if not ok:
            # Provedor inalcançável → unhealthy independente do tipo.
            return CheckSaude(status="unhealthy", detalhe=detalhe)

        # Ping ok, mas Fake continua sendo Fake → degraded preserva o sinal.
        return CheckSaude(status=status_inspecao, detalhe=detalhe)

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
