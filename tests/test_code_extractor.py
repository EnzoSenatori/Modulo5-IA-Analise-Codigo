import os
import json
from src.code_extractor import extrair_dados

def test_extrair_dados_identifica_classe_e_metodo():
    # 1. SETUP: Criamos um ficheiro temporário para testar
    test_file = "temp_test_code.py"
    content = """
    class MinhaClasse:
    def meu_metodo(self):
        pass

def funcao():
    pass
"""
    with open(test_file, "w") as f:
        f.write(content)

    # 2. EXECUÇÃO: Chamamos a nossa função
    resultado = extrair_dados(test_file)

    # 3. ASSERTS: Verificamos se o resultado é o que esperamos
    assert resultado["classes"][0]["nome"] == "MinhaClasse"
    assert "meu_metodo" in resultado["classes"][0]["metodos"]
    assert "funcao" in resultado["funcoes"]

    # CLEANUP: Removemos o ficheiro de teste
    os.remove(test_file)