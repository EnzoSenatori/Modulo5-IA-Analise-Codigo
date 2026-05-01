import ast
from typing import List
from app.application.ports.driven.analisador_estatico import AnalisadorEstatico
from app.domain.entidades.diagnostico_qualidade import DiagnosticoQualidade, MetricaAcoplamento


class AdaptadorAnalisadorPython(AnalisadorEstatico):
    """
    Adaptador que utiliza AST para mapear dependências e
    analisar a qualidade do código.
    """

    def analisar_complexidade_e_acoplamento(self, codigo_fonte: str) -> DiagnosticoQualidade:
        try:
            tree = ast.parse(codigo_fonte)
        except Exception:
            # Se o código estiver quebrado, retornamos um diagnóstico básico de erro
            return DiagnosticoQualidade(score_geral=0, ciclos_dependencia=[], analise_acoplamento=[], sugestoes=[])

        # 1. Extrair imports para calcular acoplamento
        dependencias = self._extrair_dependencias(tree)

        # Criamos a métrica de acoplamento para este componente
        metrica = MetricaAcoplamento(
            componente="ArquivoAnalisado",
            depende_de=dependencias,
            acoplamento_saida=len(dependencias)
        )

        # 2. Lógica simplificada de sugestões por severidade (Critério de Aceitação)
        sugestoes = []
        if len(dependencias) > 5:
            sugestoes.append({
                "severidade": "Alta",
                "acao": "Reduzir acoplamento: este arquivo depende de muitos módulos."
            })

        # 3. Cálculo de Score (0 a 100)
        score = max(0, 100 - (len(dependencias) * 10))

        return DiagnosticoQualidade(
            score_geral=score,
            ciclos_dependencia=[],  # A detecção de ciclos complexos virá na lógica de serviço
            analise_acoplamento=[metrica],
            sugestoes=sugestoes
        )

    def _extrair_dependencias(self, tree) -> List[str]:
        """Varre o AST em busca de imports"""
        deps = []
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                for alias in node.names:
                    deps.append(alias.name)
            elif isinstance(node, ast.ImportFrom):
                if node.module:
                    deps.append(node.module)
        return list(set(deps))  # Remove duplicados