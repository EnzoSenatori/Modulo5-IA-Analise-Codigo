# Entidade de dominio: DiffArquitetural (US IA-10)
# Compara duas EstruturaArquitetural e expressa o que mudou em formato JSON
# + Mermaid colorido (componentes adicionados/removidos/alterados).

from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List

from app.domain.entidades.componente import Componente
from app.domain.entidades.relacao import Relacao


_SETA_POR_TIPO = {
    "heranca": None,         # tratado a parte (Pai <|-- Filha)
    "usa": "..>",
    "depende_de": "..>",
}


@dataclass
class ComponenteAlterado:
    """Diferenca de um componente que existe nas duas versoes mas mudou."""
    nome: str
    metodos_adicionados: List[str] = field(default_factory=list)
    metodos_removidos: List[str] = field(default_factory=list)
    atributos_adicionados: List[str] = field(default_factory=list)
    atributos_removidos: List[str] = field(default_factory=list)
    responsabilidade_alterada: bool = False
    responsabilidade_antes: str = ""
    responsabilidade_depois: str = ""

    def tem_mudanca(self) -> bool:
        return (
            bool(self.metodos_adicionados or self.metodos_removidos
                 or self.atributos_adicionados or self.atributos_removidos)
            or self.responsabilidade_alterada
        )


@dataclass
class DiffArquitetural:
    componentes_adicionados: List[Componente] = field(default_factory=list)
    componentes_removidos: List[Componente] = field(default_factory=list)
    componentes_alterados: List[ComponenteAlterado] = field(default_factory=list)
    relacoes_adicionadas: List[Relacao] = field(default_factory=list)
    relacoes_removidas: List[Relacao] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def tem_mudancas(self) -> bool:
        return bool(
            self.componentes_adicionados
            or self.componentes_removidos
            or self.componentes_alterados
            or self.relacoes_adicionadas
            or self.relacoes_removidas
        )

    def resumo(self) -> Dict[str, int]:
        return {
            "componentes_adicionados": len(self.componentes_adicionados),
            "componentes_removidos": len(self.componentes_removidos),
            "componentes_alterados": len(self.componentes_alterados),
            "relacoes_adicionadas": len(self.relacoes_adicionadas),
            "relacoes_removidas": len(self.relacoes_removidas),
        }

    def to_dict(self) -> Dict[str, Any]:
        return {
            "tem_mudancas": self.tem_mudancas(),
            "resumo": self.resumo(),
            "componentes_adicionados": [asdict(c) for c in self.componentes_adicionados],
            "componentes_removidos": [asdict(c) for c in self.componentes_removidos],
            "componentes_alterados": [asdict(c) for c in self.componentes_alterados],
            "relacoes_adicionadas": [asdict(r) for r in self.relacoes_adicionadas],
            "relacoes_removidas": [asdict(r) for r in self.relacoes_removidas],
            "warnings": list(self.warnings),
        }

    def to_mermaid(self) -> str:
        """
        Mermaid classDiagram com classes coloridas:
          - adicionado (verde) — tudo que sai no head e nao no base
          - removido (vermelho) — tudo que existia no base e sumiu
          - alterado (amarelo) — mesmo nome mas com diff interno
          - inalterado (cinza claro) — para dar contexto
        """
        linhas: List[str] = ["classDiagram"]

        adicionados = {c.nome: c for c in self.componentes_adicionados}
        removidos = {c.nome: c for c in self.componentes_removidos}
        alterados = {c.nome for c in self.componentes_alterados}

        # Renderiza adicionados e removidos (corpo completo).
        for nome, c in adicionados.items():
            linhas.extend(self._render_classe(c, sufixo="(+)"))
        for nome, c in removidos.items():
            linhas.extend(self._render_classe(c, sufixo="(-)"))

        # Para alterados, podemos so registrar o nome — o front mostra o diff via JSON.
        for nome in alterados:
            linhas.append(f"    class {nome}")

        # Relacoes
        for r in self.relacoes_adicionadas:
            self._render_relacao(linhas, r, label="+")
        for r in self.relacoes_removidas:
            self._render_relacao(linhas, r, label="-")

        # Estilos
        linhas.append("    classDef adicionado fill:#9f9,stroke:#0a0,color:#000")
        linhas.append("    classDef removido fill:#f99,stroke:#a00,color:#000")
        linhas.append("    classDef alterado fill:#ff9,stroke:#aa0,color:#000")

        for nome in adicionados:
            linhas.append(f"    class {nome}:::adicionado")
        for nome in removidos:
            linhas.append(f"    class {nome}:::removido")
        for nome in alterados:
            linhas.append(f"    class {nome}:::alterado")

        return "\n".join(linhas) + "\n"

    @staticmethod
    def _render_classe(c: Componente, sufixo: str) -> List[str]:
        out: List[str] = []
        if c.metodos or c.atributos:
            out.append(f"    class {c.nome} {{")
            for atributo in c.atributos:
                out.append(f"        +{atributo}")
            for metodo in c.metodos:
                out.append(f"        +{metodo}()")
            out.append(f"        {sufixo}")
            out.append("    }")
        else:
            out.append(f"    class {c.nome}[\"{c.nome} {sufixo}\"]")
        return out

    @staticmethod
    def _render_relacao(linhas: List[str], r: Relacao, label: str) -> None:
        if r.tipo == "heranca":
            linhas.append(f"    {r.destino} <|-- {r.origem} : {label}")
            return
        seta = _SETA_POR_TIPO.get(r.tipo)
        if seta is None:
            return
        rotulo = "usa" if r.tipo == "usa" else "depende"
        linhas.append(f"    {r.origem} {seta} {r.destino} : {label} {rotulo}")
