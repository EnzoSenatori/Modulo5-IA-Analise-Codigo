# Detectores deterministicos para sugestoes de refatoracao (US IA-05).
# Cada detector recebe (ast_tree, linhas_codigo) e devolve List[SugestaoRefatoracao].
# Sem LLM, sem random, sem heuristica probabilistica — mesma entrada gera mesma saida.

import ast
from abc import ABC, abstractmethod
from typing import List, Set

from app.domain.entidades.sugestao_refatoracao import (
    CategoriaRefatoracao,
    EsforcoEstimado,
    SugestaoRefatoracao,
)


# --- Limites configuraveis (poderiam vir de settings; mantidos como constantes para simplicidade) ---
LIMITE_LINHAS_FUNCAO = 30
LIMITE_PARAMETROS = 5
LIMITE_BRANCHES_ELIF = 5
# Numeros mascarados como "magicos" — 0/1/-1 sao considerados triviais.
NUMEROS_PERMITIDOS = {0, 1, -1, 2, -2, 100}


class Detector(ABC):

    @abstractmethod
    def detectar(self, tree: ast.AST, linhas: List[str]) -> List[SugestaoRefatoracao]:
        pass

    @staticmethod
    def _trecho(linhas: List[str], inicio: int, fim: int, max_linhas: int = 12) -> str:
        if not linhas:
            return ""
        i = max(0, inicio - 1)
        f = min(len(linhas), fim)
        slice_ = linhas[i:f]
        if len(slice_) > max_linhas:
            slice_ = slice_[:max_linhas] + [f"# ... ({len(slice_) - max_linhas} linha(s) omitida(s))"]
        return "\n".join(slice_)


# ----------------------------------------------------------------------
# Funcao longa
# ----------------------------------------------------------------------

class DetectorFuncaoLonga(Detector):

    def detectar(self, tree, linhas):
        sugestoes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                inicio = node.lineno
                fim = getattr(node, "end_lineno", inicio) or inicio
                tamanho = fim - inicio + 1
                if tamanho > LIMITE_LINHAS_FUNCAO:
                    antes = self._trecho(linhas, inicio, fim, max_linhas=8)
                    depois = self._template_depois(node.name, len(node.args.args))
                    sugestoes.append(SugestaoRefatoracao(
                        titulo=f"Extrair partes de '{node.name}' (funcao com {tamanho} linhas)",
                        categoria=CategoriaRefatoracao.FUNCAO_LONGA,
                        esforco=EsforcoEstimado.MEDIO if tamanho > 60 else EsforcoEstimado.PEQUENO,
                        explicacao=(
                            f"A funcao '{node.name}' tem {tamanho} linhas (limite sugerido: "
                            f"{LIMITE_LINHAS_FUNCAO}). Extraia blocos coesos para funcoes "
                            f"privadas — facilita teste e leitura."
                        ),
                        snippet_antes=antes,
                        snippet_depois=depois,
                        linha_inicio=inicio, linha_fim=fim,
                        detalhes={"linhas": tamanho, "nome_funcao": node.name},
                    ))
        return sugestoes

    @staticmethod
    def _template_depois(nome: str, nargs: int) -> str:
        params = ", ".join(["..."] * max(1, nargs))
        return (
            f"def {nome}({params}):\n"
            f"    _validar_entrada(...)        # bloco extraido\n"
            f"    resultado = _processar(...)  # bloco extraido\n"
            f"    _persistir(resultado)        # bloco extraido\n"
            f"    return resultado"
        )


# ----------------------------------------------------------------------
# Muitos parametros
# ----------------------------------------------------------------------

class DetectorMuitosParametros(Detector):

    def detectar(self, tree, linhas):
        sugestoes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                qtd_params = self._contar_params_significativos(node)
                if qtd_params > LIMITE_PARAMETROS:
                    inicio = node.lineno
                    fim = getattr(node, "end_lineno", inicio) or inicio
                    nomes = [a.arg for a in node.args.args if a.arg != "self"]
                    sugestoes.append(SugestaoRefatoracao(
                        titulo=f"Agrupar parametros de '{node.name}' em dataclass",
                        categoria=CategoriaRefatoracao.MUITOS_PARAMETROS,
                        esforco=EsforcoEstimado.PEQUENO,
                        explicacao=(
                            f"A funcao '{node.name}' tem {qtd_params} parametros (limite "
                            f"sugerido: {LIMITE_PARAMETROS}). Agrupe os campos relacionados "
                            f"em uma dataclass para reduzir acoplamento e facilitar evolucao."
                        ),
                        snippet_antes=self._trecho(linhas, inicio, min(inicio + 2, fim)),
                        snippet_depois=self._template_depois(node.name, nomes),
                        linha_inicio=inicio, linha_fim=fim,
                        detalhes={"qtd_params": qtd_params, "nomes": nomes},
                    ))
        return sugestoes

    @staticmethod
    def _contar_params_significativos(node) -> int:
        total = len(node.args.args)
        # Desconta 'self'/'cls' como nao-parametro de negocio.
        if node.args.args and node.args.args[0].arg in ("self", "cls"):
            total -= 1
        return total

    @staticmethod
    def _template_depois(nome: str, nomes: List[str]) -> str:
        if not nomes:
            return ""
        campos = "\n    ".join(f"{n}: ..." for n in nomes)
        return (
            f"@dataclass\n"
            f"class {nome.title().replace('_', '')}Dados:\n    {campos}\n\n"
            f"def {nome}(dados: {nome.title().replace('_', '')}Dados):\n"
            f"    # use dados.{nomes[0]}, dados.{nomes[1] if len(nomes) > 1 else nomes[0]}, etc.\n"
            f"    ..."
        )


# ----------------------------------------------------------------------
# Default mutavel
# ----------------------------------------------------------------------

class DetectorDefaultMutavel(Detector):

    def detectar(self, tree, linhas):
        sugestoes = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                for default, arg in self._defaults_mutaveis(node):
                    inicio = node.lineno
                    fim = getattr(node, "end_lineno", inicio) or inicio
                    sugestoes.append(SugestaoRefatoracao(
                        titulo=f"Trocar default mutavel '{arg}' em '{node.name}'",
                        categoria=CategoriaRefatoracao.DEFAULT_MUTAVEL,
                        esforco=EsforcoEstimado.TRIVIAL,
                        explicacao=(
                            f"O parametro '{arg}' usa um valor mutavel como default — todas as "
                            f"chamadas compartilham a mesma instancia (bug classico de Python). "
                            f"Use None e construa dentro da funcao."
                        ),
                        snippet_antes=self._trecho(linhas, inicio, min(inicio + 1, fim)),
                        snippet_depois=self._template_depois(node.name, arg, type(default).__name__),
                        linha_inicio=inicio, linha_fim=inicio,
                        detalhes={"parametro": arg, "tipo_default": type(default).__name__},
                    ))
        return sugestoes

    @staticmethod
    def _defaults_mutaveis(node):
        # Defaults aplicam-se aos ULTIMOS N args; ignoramos self/cls.
        args = node.args.args
        defaults = node.args.defaults
        if not defaults:
            return
        offset = len(args) - len(defaults)
        for i, default in enumerate(defaults):
            arg = args[offset + i]
            if isinstance(default, (ast.List, ast.Dict, ast.Set)):
                yield default, arg.arg

    @staticmethod
    def _template_depois(nome_func: str, nome_arg: str, tipo: str) -> str:
        construtor = {"List": "[]", "Dict": "{}", "Set": "set()"}.get(tipo, "None")
        return (
            f"def {nome_func}(..., {nome_arg}=None):\n"
            f"    if {nome_arg} is None:\n"
            f"        {nome_arg} = {construtor}\n"
            f"    ..."
        )


# ----------------------------------------------------------------------
# Numeros magicos
# ----------------------------------------------------------------------

class DetectorNumeroMagico(Detector):

    def detectar(self, tree, linhas):
        sugestoes = []
        # Pre-pass: linhas onde ja temos NOME_UPPER = literal — extracao ja feita,
        # nao reclamar do mesmo numero ali.
        linhas_de_extracao: Set[int] = set()
        for node in ast.walk(tree):
            if isinstance(node, ast.Assign):
                for target in node.targets:
                    if (
                        isinstance(target, ast.Name) and target.id.isupper()
                        and isinstance(node.value, ast.Constant)
                    ):
                        linhas_de_extracao.add(node.lineno)

        # Coleta TODOS os usos primeiro pra agrupar — uma sugestao por linha
        # (evita 50 sugestoes pra mesmo numero).
        usos_por_linha: dict = {}
        for node in ast.walk(tree):
            if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
                if node.value in NUMEROS_PERMITIDOS:
                    continue
                if isinstance(node.value, bool):  # bool eh subclasse de int
                    continue
                if node.lineno in linhas_de_extracao:
                    continue
                linha = node.lineno
                usos_por_linha.setdefault(linha, set()).add(node.value)

        for linha, valores in sorted(usos_por_linha.items()):
            valores_str = ", ".join(str(v) for v in sorted(valores, key=str))
            sugestoes.append(SugestaoRefatoracao(
                titulo=f"Extrair constante(s) ao inves do(s) numero(s) {valores_str}",
                categoria=CategoriaRefatoracao.NUMERO_MAGICO,
                esforco=EsforcoEstimado.TRIVIAL,
                explicacao=(
                    f"Linha {linha} tem numero(s) magico(s): {valores_str}. "
                    f"Extraia para constante nomeada no topo do modulo — fica obvio o que "
                    f"o valor representa e fica facil ajustar."
                ),
                snippet_antes=self._trecho(linhas, linha, linha, max_linhas=1),
                snippet_depois=self._template_depois(valores),
                linha_inicio=linha, linha_fim=linha,
                detalhes={"valores": sorted(valores, key=str)},
            ))
        return sugestoes

    @staticmethod
    def _template_depois(valores) -> str:
        return "\n".join(
            f"NOME_DESCRITIVO_{i + 1} = {v}  # significado claro aqui"
            for i, v in enumerate(sorted(valores, key=str))
        )


# ----------------------------------------------------------------------
# Cadeia elif longa
# ----------------------------------------------------------------------

class DetectorCadeiaElifLonga(Detector):

    def detectar(self, tree, linhas):
        sugestoes = []
        ja_visitados: Set[int] = set()  # evita contar elifs aninhados como ifs separados
        for node in ast.walk(tree):
            if isinstance(node, ast.If) and id(node) not in ja_visitados:
                cadeia = self._tamanho_cadeia(node, ja_visitados)
                if cadeia > LIMITE_BRANCHES_ELIF:
                    inicio = node.lineno
                    fim = getattr(node, "end_lineno", inicio) or inicio
                    sugestoes.append(SugestaoRefatoracao(
                        titulo=f"Substituir cadeia de {cadeia} branches if/elif por dict ou polimorfismo",
                        categoria=CategoriaRefatoracao.CADEIA_ELIF_LONGA,
                        esforco=EsforcoEstimado.MEDIO,
                        explicacao=(
                            f"Cadeia com {cadeia} branches detectada (limite sugerido: "
                            f"{LIMITE_BRANCHES_ELIF}). Refatore para dict de handlers ou "
                            f"strategy pattern — abre extensao sem mexer no codigo existente."
                        ),
                        snippet_antes=self._trecho(linhas, inicio, fim, max_linhas=10),
                        snippet_depois=(
                            "_HANDLERS = {\n"
                            "    'caso_a': _tratar_caso_a,\n"
                            "    'caso_b': _tratar_caso_b,\n"
                            "    # ...\n"
                            "}\n"
                            "handler = _HANDLERS.get(chave, _tratar_default)\n"
                            "resultado = handler(args)"
                        ),
                        linha_inicio=inicio, linha_fim=fim,
                        detalhes={"qtd_branches": cadeia},
                    ))
        return sugestoes

    @staticmethod
    def _tamanho_cadeia(node: ast.If, visitados: Set[int]) -> int:
        cadeia = 1
        atual = node
        while atual.orelse and len(atual.orelse) == 1 and isinstance(atual.orelse[0], ast.If):
            atual = atual.orelse[0]
            visitados.add(id(atual))
            cadeia += 1
        return cadeia


# Lista canonica em ordem deterministica — aplicada nesta ordem pelo service.
DETECTORES_PADRAO: List[Detector] = [
    DetectorFuncaoLonga(),
    DetectorMuitosParametros(),
    DetectorDefaultMutavel(),
    DetectorNumeroMagico(),
    DetectorCadeiaElifLonga(),
]
