import ast
from typing import List

from app.application.ports.driven.parser_codigo import ParserCodigo
from app.domain.entidades.especificacao_api import EspecificacaoApi, RotaApi
from app.domain.entidades.componente import Componente
from app.domain.entidades.relacao import Relacao


class AdaptadorParserPython(ParserCodigo):
    """Adaptador que extrai dados de código Python via AST."""

    # ---------- IA-02 (não alterar) ----------

    def extrair_especificacao(self, codigo_fonte: str) -> EspecificacaoApi:
        try:
            tree = ast.parse(codigo_fonte)
        except SyntaxError as e:
            from app.domain.excecoes import ParserError
            raise ParserError(f"Erro de sintaxe no código fonte: {str(e)}")

        rotas_encontradas = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                rota = self._analisar_funcao(node)
                if rota:
                    rotas_encontradas.append(rota)

        return EspecificacaoApi(
            titulo="API Extraída Automaticamente",
            versao="1.0.0",
            descricao="Especificação gerada via Engenharia Reversa pelo Módulo 5.",
            rotas=rotas_encontradas,
        )

    def _analisar_funcao(self, node: ast.FunctionDef) -> RotaApi:
        for decorator in node.decorator_list:
            if isinstance(decorator, ast.Call):
                func_name = self._get_decorator_name(decorator.func)
                if func_name in ['route', 'get', 'post', 'put', 'delete']:
                    caminho = ""
                    if decorator.args and isinstance(decorator.args[0], ast.Constant):
                        caminho = decorator.args[0].value
                    metodo = func_name.upper() if func_name != 'route' else "GET"
                    if func_name == 'route':
                        for kw in decorator.keywords:
                            if kw.arg == 'methods' and isinstance(kw.value, ast.List):
                                if isinstance(kw.value.elts[0], ast.Constant):
                                    metodo = kw.value.elts[0].value.upper()
                    return RotaApi(
                        caminho=caminho,
                        metodo=metodo,
                        resumo=f"Endpoint: {node.name}",
                    )
        return None

    def _get_decorator_name(self, node):
        if isinstance(node, ast.Attribute):
            return node.attr
        elif isinstance(node, ast.Name):
            return node.id
        return ""

    # ---------- IA-01 ----------

    def extrair_estrutura(self, codigo_fonte: str) -> List[Componente]:
        tree = self._parse(codigo_fonte)
        componentes: List[Componente] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                componentes.append(self._classe_para_componente(node))
        return componentes

    def extrair_herancas(self, codigo_fonte: str) -> List[Relacao]:
        tree = self._parse(codigo_fonte)
        relacoes: List[Relacao] = []
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for base in node.bases:
                    nome_base = self._nome_da_base(base)
                    if nome_base:
                        relacoes.append(Relacao(
                            origem=node.name,
                            destino=nome_base,
                            tipo="heranca",
                            fonte="ast",
                        ))
        return relacoes

    # ---------- helpers IA-01 ----------

    def _parse(self, codigo: str) -> ast.AST:
        try:
            return ast.parse(codigo)
        except SyntaxError as e:
            from app.domain.excecoes import ParserError
            raise ParserError(f"Erro de sintaxe no código fonte: {str(e)}")

    def _classe_para_componente(self, node: ast.ClassDef) -> Componente:
        metodos: List[str] = []
        atributos: List[str] = []

        for filho in node.body:
            if isinstance(filho, (ast.FunctionDef, ast.AsyncFunctionDef)):
                metodos.append(filho.name)
                atributos.extend(self._atributos_self_em(filho))

        atributos_unicos: List[str] = []
        vistos = set()
        for a in atributos:
            if a not in vistos:
                vistos.add(a)
                atributos_unicos.append(a)

        return Componente(
            nome=node.name,
            tipo="classe",
            metodos=metodos,
            atributos=atributos_unicos,
        )

    def _atributos_self_em(self, func_node) -> List[str]:
        encontrados: List[str] = []
        for n in ast.walk(func_node):
            if isinstance(n, ast.Assign):
                for alvo in n.targets:
                    if (
                        isinstance(alvo, ast.Attribute)
                        and isinstance(alvo.value, ast.Name)
                        and alvo.value.id == "self"
                    ):
                        encontrados.append(alvo.attr)
        return encontrados

    def _nome_da_base(self, base) -> str:
        if isinstance(base, ast.Name):
            return base.id
        if isinstance(base, ast.Attribute):
            return base.attr
        return ""
