from app.adapters.driven.analise.adaptador_parser_python import AdaptadorParserPython
from app.application.services.openapi_service_impl import OpenApiServiceImpl

class CompositionRoot:
    """
    A Raiz de Composição é responsável por instanciar as classes
    e 'injetar' as dependências necessárias.
    """

    def __init__(self):
        # 1. Instanciamos os adaptadores (Driven Adapters)
        self.parser_python = AdaptadorParserPython()

        # 2. Instanciamos os serviços injetando seus respectivos adaptadores
        self.openapi_service = OpenApiServiceImpl(
            parser_codigo=self.parser_python
        )

    def get_openapi_service(self):
        return self.openapi_service