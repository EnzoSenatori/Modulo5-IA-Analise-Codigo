import ast
from typing import List
from app.application.ports.driven.parser_codigo import ParserCodigo
from app.domain.entidades.especificacao_api import EspecificacaoApi, RotaApi


class AdaptadorParserPython(ParserCodigo):
    """
    Adaptador que utiliza Análise Estática (AST) para extrair
    rotas de arquivos Python (Flask/FastAPI).
    """

    def extrair_especificacao(self, codigo_fonte: str) -> EspecificacaoApi:
        try:
            tree = ast.parse(codigo_fonte)
        except SyntaxError as e:
            from app.domain.excecoes import ParserError
            raise ParserError(f"Erro de sintaxe no código fonte: {str(e)}")

        rotas_encontradas = []

        # Percorre todas as definições de funções no arquivo
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                rota = self._analisar_funcao(node)
                if rota:
                    rotas_encontradas.append(rota)

        return EspecificacaoApi(
            titulo="API Extraída Automaticamente",
            versao="1.0.0",
            descricao="Especificação gerada via Engenharia Reversa pelo Módulo 5.",
            rotas=rotas_encontradas
        )

    def _analisar_funcao(self, node: ast.FunctionDef) -> RotaApi:
        """Analisa os decoradores da função em busca de rotas HTTP."""
        for decorator in node.decorator_list:
            # Caso simples: @app.route('/caminho', methods=['GET'])
            if isinstance(decorator, ast.Call):
                func_name = self._get_decorator_name(decorator.func)

                # Suporte para Flask (.route) e FastAPI (.get, .post, etc)
                if func_name in ['route', 'get', 'post', 'put', 'delete']:
                    caminho = ""
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        caminho = decorator.args[0].value

                    metodo = func_name.upper() if func_name != 'route' else "GET"

                    # Tenta extrair métodos do Flask se for .route(..., methods=['POST'])
                    if func_name == 'route':
                        for kw in decorator.keywords:
                            if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                                if isinstance(kw.value.elts[0], ast.Constant):
                                    metodo = kw.value.elts[0].value.upper()

                    return RotaApi(
                        caminho=caminho,
                        metodo=metodo,
                        resumo=f"Endpoint: {node.name}"
                    )
        return None

    def _get_decorator_name(self, node):
        """Auxiliar para extrair o nome do decorador (ex: route)"""
        if isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Name):
            return node.id
        return ""