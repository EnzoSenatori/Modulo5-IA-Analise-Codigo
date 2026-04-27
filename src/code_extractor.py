import ast
import json


def extrair_dados(caminho_arquivo):
    # with open --> abre o arquivo que queremos
    with open(caminho_arquivo, "r", encoding="utf-8") as arquivo:
        codigo = arquivo.read()

    #ast.parse -≥ pega o código e o transforma de ‘string’ para uma estrutura de dado similar a uma árvore
    arvore = ast.parse(codigo)

    # Molde para o arquivo JSON que será gerado para passar adiante para outros repositórios
    dados = {
        "arquivo": caminho_arquivo,
        "classes": [],
        "funcoes": []
    }

    # Varre a árvore em busca de classes e funções
    for node in ast.iter_child_nodes(arvore):
        if isinstance(node, ast.ClassDef): #Se o nó for uma Classe, pegamos o nome e os métodos desta classe
            dados["classes"].append({
                "nome": node.name,
                "metodos": [n.name for n in node.body if isinstance(n, ast.FunctionDef)]
            })
        elif isinstance(node, ast.FunctionDef): #Se o nó não for uma classe, mas uma funcao solta, salvamos o nome da funcao
            dados["funcoes"].append(node.name)

    return dados


if __name__ == "__main__":

    resultado = extrair_dados(__file__)

    # Gera o arquivo JSON com as informacoes preenchidas
    with open("projeto_analisado.json", "w") as f:
        json.dump(resultado, f, indent=4)

    print("Sucesso! Arquivo 'projeto_analisado.json' gerado.")