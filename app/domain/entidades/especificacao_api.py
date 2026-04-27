from dataclasses import dataclass, field
from typing import List, Dict, Any


@dataclass
class RotaApi:
    caminho: str
    metodo: str  # GET, POST, DELETE, etc.
    resumo: str = ""
    parametros: List[Dict[str, Any]] = field(default_factory=list)
    respostas: Dict[str, Any] = field(default_factory=dict)


@dataclass
class EspecificacaoApi:
    titulo: str
    versao: str
    descricao: str
    rotas: List[RotaApi] = field(default_factory=list)

    def to_openapi_dict(self) -> Dict[str, Any]:
        """Converte a entidade para o dicionário padrão OpenAPI 3.0.0"""
        paths = {}
        for rota in self.rotas:
            if rota.caminho not in paths:
                paths[rota.caminho] = {}

            paths[rota.caminho][rota.metodo.lower()] = {
                "summary": rota.resumo,
                "parameters": rota.parametros,
                "responses": rota.respostas
            }

        return {
            "openapi": "3.0.0",
            "info": {
                "title": self.titulo,
                "version": self.versao,
                "description": self.descricao
            },
            "paths": paths
        }