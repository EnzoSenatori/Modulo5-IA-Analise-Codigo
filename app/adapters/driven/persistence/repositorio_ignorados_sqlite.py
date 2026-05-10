# Repositorio SQLite para componentes ignorados na analise de cobertura (US IA-07).

import sqlite3
import threading
from datetime import datetime
from typing import List, Optional, Set

from app.application.ports.driven.repositorio_ignorados import RepositorioIgnorados
from app.domain.entidades.mapa_cobertura import ComponenteIgnorado


_SCHEMA = """
CREATE TABLE IF NOT EXISTS componentes_ignorados (
    nome TEXT PRIMARY KEY,
    motivo TEXT NOT NULL,
    marcado_por TEXT NOT NULL,
    marcado_em TEXT NOT NULL
);
"""


class RepositorioIgnoradosSQLite(RepositorioIgnorados):

    def __init__(self, caminho_db: str):
        self._caminho = caminho_db
        self._conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conexao.executescript(_SCHEMA)
            self._conexao.commit()

    def salvar(self, ignorado: ComponenteIgnorado) -> None:
        sql = """
            INSERT INTO componentes_ignorados (nome, motivo, marcado_por, marcado_em)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(nome) DO UPDATE SET
                motivo = excluded.motivo,
                marcado_por = excluded.marcado_por,
                marcado_em = excluded.marcado_em
        """
        with self._lock:
            self._conexao.execute(sql, (
                ignorado.nome, ignorado.motivo, ignorado.marcado_por,
                ignorado.marcado_em.isoformat(),
            ))
            self._conexao.commit()

    def obter(self, nome: str) -> Optional[ComponenteIgnorado]:
        with self._lock:
            linha = self._conexao.execute(
                "SELECT * FROM componentes_ignorados WHERE nome = ?", (nome,),
            ).fetchone()
        return self._linha_para_entidade(linha) if linha else None

    def listar(self) -> List[ComponenteIgnorado]:
        with self._lock:
            linhas = self._conexao.execute(
                "SELECT * FROM componentes_ignorados ORDER BY marcado_em DESC",
            ).fetchall()
        return [self._linha_para_entidade(l) for l in linhas]

    def remover(self, nome: str) -> bool:
        with self._lock:
            cur = self._conexao.execute(
                "DELETE FROM componentes_ignorados WHERE nome = ?", (nome,),
            )
            self._conexao.commit()
            return cur.rowcount > 0

    def nomes_ignorados(self) -> Set[str]:
        with self._lock:
            linhas = self._conexao.execute(
                "SELECT nome FROM componentes_ignorados",
            ).fetchall()
        return {l["nome"] for l in linhas}

    def fechar(self) -> None:
        with self._lock:
            self._conexao.close()

    @staticmethod
    def _linha_para_entidade(linha: sqlite3.Row) -> ComponenteIgnorado:
        return ComponenteIgnorado(
            nome=linha["nome"],
            motivo=linha["motivo"],
            marcado_por=linha["marcado_por"],
            marcado_em=datetime.fromisoformat(linha["marcado_em"]),
        )
