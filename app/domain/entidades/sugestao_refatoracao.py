# Entidades de dominio: SugestaoRefatoracao (US IA-05)
# Sugestoes 100% deterministicas geradas por detectores AST puros (sem LLM).

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List


class CategoriaRefatoracao(Enum):
    FUNCAO_LONGA = "funcao_longa"
    MUITOS_PARAMETROS = "muitos_parametros"
    DEFAULT_MUTAVEL = "default_mutavel"
    NUMERO_MAGICO = "numero_magico"
    CADEIA_ELIF_LONGA = "cadeia_elif_longa"


class EsforcoEstimado(Enum):
    TRIVIAL = "trivial"     # < 30 min — fix mecanico
    PEQUENO = "pequeno"     # 30 min - 2h — extracao localizada
    MEDIO = "medio"         # 2h - 1 dia — restruturacao com testes
    GRANDE = "grande"       # > 1 dia — afeta varios arquivos


@dataclass
class SugestaoRefatoracao:
    titulo: str
    categoria: CategoriaRefatoracao
    esforco: EsforcoEstimado
    explicacao: str
    snippet_antes: str
    snippet_depois: str
    linha_inicio: int = 0
    linha_fim: int = 0
    detalhes: Dict[str, Any] = field(default_factory=dict)

    @property
    def chave_ordenacao(self) -> tuple:
        """Garante ordem deterministica entre sugestoes."""
        return (self.linha_inicio, self.categoria.value, self.titulo)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "titulo": self.titulo,
            "categoria": self.categoria.value,
            "esforco": self.esforco.value,
            "explicacao": self.explicacao,
            "snippet_antes": self.snippet_antes,
            "snippet_depois": self.snippet_depois,
            "linha_inicio": self.linha_inicio,
            "linha_fim": self.linha_fim,
            "detalhes": dict(self.detalhes),
        }


@dataclass
class RelatorioRefatoracao:
    sugestoes: List[SugestaoRefatoracao] = field(default_factory=list)

    @property
    def total(self) -> int:
        return len(self.sugestoes)

    def por_esforco(self) -> Dict[str, int]:
        contagem = {e.value: 0 for e in EsforcoEstimado}
        for s in self.sugestoes:
            contagem[s.esforco.value] += 1
        return contagem

    def por_categoria(self) -> Dict[str, int]:
        contagem: Dict[str, int] = {}
        for s in self.sugestoes:
            contagem[s.categoria.value] = contagem.get(s.categoria.value, 0) + 1
        return contagem

    def to_dict(self) -> Dict[str, Any]:
        return {
            "total": self.total,
            "resumo_por_esforco": self.por_esforco(),
            "resumo_por_categoria": self.por_categoria(),
            "sugestoes": [s.to_dict() for s in self.sugestoes],
        }
