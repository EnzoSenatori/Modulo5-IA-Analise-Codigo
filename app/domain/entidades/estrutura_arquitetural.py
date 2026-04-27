from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any

from app.domain.entidades.componente import Componente
from app.domain.entidades.relacao import Relacao

_SETA_POR_TIPO = {
    "heranca": None,           # tratado à parte (Pai <|-- Filha)
    "usa": "..>",
    "depende_de": "..>",
}


@dataclass
class EstruturaArquitetural:
    """Resultado da análise: componentes, relações e avisos de degradação."""
    componentes: List[Componente]
    relacoes: List[Relacao]
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "componentes": [asdict(c) for c in self.componentes],
            "relacoes": [asdict(r) for r in self.relacoes],
            "warnings": list(self.warnings),
        }

    def to_mermaid(self) -> str:
        nomes_validos = {c.nome for c in self.componentes}
        linhas: List[str] = ["classDiagram"]

        for c in self.componentes:
            if c.metodos or c.atributos:
                linhas.append(f"    class {c.nome} {{")
                for atributo in c.atributos:
                    linhas.append(f"        +{atributo}")
                for metodo in c.metodos:
                    linhas.append(f"        +{metodo}()")
                linhas.append("    }")
            else:
                linhas.append(f"    class {c.nome}")

        for r in self.relacoes:
            if r.origem not in nomes_validos or r.destino not in nomes_validos:
                continue
            if r.tipo == "heranca":
                linhas.append(f"    {r.destino} <|-- {r.origem}")
            else:
                seta = _SETA_POR_TIPO.get(r.tipo)
                if seta is None:
                    continue
                rotulo = "usa" if r.tipo == "usa" else "depende"
                linhas.append(f"    {r.origem} {seta} {r.destino} : {rotulo}")

        return "\n".join(linhas) + "\n"
