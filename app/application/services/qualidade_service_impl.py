from typing import Dict, Any
from app.application.ports.driving.qualidade_service import QualidadeService
from app.application.ports.driven.analisador_estatico import AnalisadorEstatico

class QualidadeServiceImpl(QualidadeService):
    """
    Implementação do serviço de qualidade.
    Coordena a análise de acoplamento e gera o relatório final.
    """

    def __init__(self, analisador_estatico: AnalisadorEstatico):
        # Recebemos o adaptador injetado via CompositionRoot
        self._analisador = analisador_estatico

    def obter_diagnostico_completo(self, codigo_fonte: str) -> Dict[str, Any]:
        """
        Executa a análise e formata o resultado para o contrato da US IA-04.
        """
        diagnostico = self._analisador.analisar_complexidade_e_acoplamento(codigo_fonte)

        # Formatação para o retorno da API (JSON)
        return {
            "score_geral": diagnostico.score_geral,
            "analise_acoplamento": [
                {
                    "componente": m.componente,
                    "depende_de": m.depende_de,
                    "grau": m.acoplamento_saida
                } for m in diagnostico.analise_acoplamento
            ],
            "ciclos_detectados": diagnostico.ciclos_dependencia,
            "sugestoes_refatoracao": diagnostico.sugestoes
        }