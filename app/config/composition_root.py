from app.config import settings
from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.adapters.driven.llm.adaptador_llm import AdaptadorLLMGemini, AdaptadorLLMFake
from app.application.services.openapi_service_impl import OpenApiServiceImpl
from app.application.services.estrutura_service_impl import EstruturaServiceImpl
from app.application.services.saude_service_impl import SaudeServiceImpl
from app.adapters.driven.analise.adaptador_analisador_python import AdaptadorAnalisadorPython
from app.application.services.qualidade_service_impl import QualidadeServiceImpl

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

    def get_openapi_service(self):
        return self.openapi_service

    def get_estrutura_service(self):
        return self.estrutura_service

    def get_saude_service(self):
        return self.saude_service

    def get_qualidade_service(self):
        return self.qualidade_service
