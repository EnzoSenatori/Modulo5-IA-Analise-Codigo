from app.config import settings
from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMGemini, AdaptadorLLMFake
from app.application.services.openapi_service_impl import OpenApiServiceImpl
from app.application.services.estrutura_service_impl import EstruturaServiceImpl
from app.application.services.saude_service_impl import SaudeServiceImpl
from app.adapters.driven.analise.adaptador_analisador_python import AdaptadorAnalisadorPython
from app.application.services.qualidade_service_impl import QualidadeServiceImpl
from app.application.services.comparacao_diagrama_service_impl import (
    ComparacaoDiagramaServiceImpl,
)
from app.application.services.cobertura_service_impl import CoberturaServiceImpl
from app.application.services.integracao_ci_service_impl import (
    IntegracaoCIServiceImpl,
)
from app.adapters.driven.git.adaptador_github import (
    AdaptadorGitHubFake,
    AdaptadorGitHubHTTP,
)
from app.adapters.driven.git.notificador_pr_github import (
    NotificadorPRFake,
    NotificadorPRGitHubHTTP,
)
from app.adapters.driven.persistence.repositorio_ignorados_sqlite import (
    RepositorioIgnoradosSQLite,
)
from app.adapters.driven.persistence.repositorio_webhooks_sqlite import (
    RepositorioWebhooksSQLite,
)


class CompositionRoot:
    """Instancia adapters e injeta dependências nos services."""

    def __init__(self):
        # Driven adapters
        self.parser_python = AdaptadorParserPython()
        self.analisador_estatico = AdaptadorAnalisadorPython()

        if settings.GEMINI_API_KEY:
            self.provedor_llm = AdaptadorLLMGemini(
                api_key=settings.GEMINI_API_KEY,
                modelo=settings.LLM_MODELO,
                timeout=settings.LLM_TIMEOUT_S,
            )
        else:
            # Sem chave configurada → modo dev/demo com fake.
            self.provedor_llm = AdaptadorLLMFake()

        # Cache e Banco ainda não têm adapters reais — entram como None
        # para o SaudeServiceImpl reportá-los como "not_configured".
        self.cache_adapter = None
        self.banco_adapter = None

        # Services
        self.openapi_service = OpenApiServiceImpl(
            parser_codigo=self.parser_python,
        )
        self.qualidade_service = QualidadeServiceImpl(
            analisador_estatico=self.analisador_estatico
        )
        self.estrutura_service = EstruturaServiceImpl(
            parser_codigo=self.parser_python,
            provedor_llm=self.provedor_llm,
        )
        self.saude_service = SaudeServiceImpl(
            provedor_llm=self.provedor_llm,
            cache_adapter=self.cache_adapter,
            banco_adapter=self.banco_adapter,
        )
        self.comparacao_service = ComparacaoDiagramaServiceImpl(
            estrutura_service=self.estrutura_service,
        )

        # --- Cobertura (IA-07) ---
        self.repositorio_ignorados = RepositorioIgnoradosSQLite(settings.COBERTURA_SQLITE_PATH)
        self.cobertura_service = CoberturaServiceImpl(
            parser=self.parser_python,
            repositorio_ignorados=self.repositorio_ignorados,
        )

        # --- Integracao CI (IA-11) ---
        self.repositorio_webhooks = RepositorioWebhooksSQLite(settings.WEBHOOKS_SQLITE_PATH)

        if (settings.ADAPTADOR_GITHUB or "github").lower() == "fake":
            self.repositorio_git = AdaptadorGitHubFake()
        else:
            self.repositorio_git = AdaptadorGitHubHTTP(
                base_url=settings.GITHUB_API_BASE,
                token=settings.GITHUB_TOKEN or None,
                timeout_segundos=settings.GITHUB_TIMEOUT_S,
            )

        if (settings.ADAPTADOR_NOTIFICADOR_PR or "github").lower() == "fake":
            self.notificador_pr = NotificadorPRFake()
        else:
            self.notificador_pr = NotificadorPRGitHubHTTP(
                base_url=settings.GITHUB_API_BASE,
                token=settings.GITHUB_TOKEN or None,
                timeout_segundos=settings.GITHUB_TIMEOUT_S,
            )

        self.integracao_ci_service = IntegracaoCIServiceImpl(
            repositorio_webhooks=self.repositorio_webhooks,
            repositorio_git=self.repositorio_git,
            notificador=self.notificador_pr,
            comparacao=self.comparacao_service,
        )

    def get_openapi_service(self):
        return self.openapi_service

    def get_estrutura_service(self):
        return self.estrutura_service

    def get_saude_service(self):
        return self.saude_service

    def get_qualidade_service(self):
        return self.qualidade_service

    def get_comparacao_service(self):
        return self.comparacao_service

    def get_cobertura_service(self):
        return self.cobertura_service

    def get_integracao_ci_service(self):
        return self.integracao_ci_service
