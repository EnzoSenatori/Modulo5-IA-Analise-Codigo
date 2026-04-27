from typing import Dict, Any
from app.application.ports.driving.openapi_service import OpenApiService
from app.application.ports.driven.parser_codigo import ParserCodigo
from app.domain.excecoes import ParserError

class OpenApiServiceImpl(OpenApiService):
    """
    Implementação do serviço de OpenAPI.
    Esta classe orquestra o uso das portas para realizar a tarefa de negócio.
    """

    def __init__(self, parser_codigo: ParserCodigo):
        # Recebemos o parser via Injeção de Dependência.
        # O serviço não sabe se o parser usa IA ou AST, apenas que ele segue o contrato.
        self._parser_codigo = parser_codigo

    def gerar_especificacao_do_codigo(self, codigo_fonte: str) -> Dict[str, Any]:
        """
        Coordena o processo de extração e conversão.
        """
        if not codigo_fonte or len(codigo_fonte.strip()) == 0:
            raise ParserError("O código fonte fornecido está vazio.")

        # 1. Solicita a extração para o parser (Porta de Saída)
        entidade_api = self._parser_codigo.extrair_especificacao(codigo_fonte)

        # 2. Utiliza o método da própria entidade de domínio para gerar o dicionário OAS
        return entidade_api.to_openapi_dict()