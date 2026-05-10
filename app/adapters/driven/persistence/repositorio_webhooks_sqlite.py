# Repositorio SQLite para eventos de webhook (US IA-11).

import json
import sqlite3
import threading
from datetime import datetime
from typing import List, Optional

from app.application.ports.driven.repositorio_webhooks import RepositorioWebhooks
from app.domain.entidades.evento_ci import EventoCI, TipoEventoGitHub


_SCHEMA = """
CREATE TABLE IF NOT EXISTS webhooks (
    id TEXT PRIMARY KEY,
    tipo TEXT NOT NULL,
    repositorio TEXT NOT NULL,
    pr_numero INTEGER,
    pr_head_sha TEXT,
    pr_base_sha TEXT,
    payload_bruto TEXT NOT NULL,
    recebido_em TEXT NOT NULL,
    processado_em TEXT,
    sucesso INTEGER,
    resultado TEXT
);
CREATE INDEX IF NOT EXISTS idx_wh_repo ON webhooks(repositorio);
CREATE INDEX IF NOT EXISTS idx_wh_processado ON webhooks(processado_em);
"""


class RepositorioWebhooksSQLite(RepositorioWebhooks):

    def __init__(self, caminho_db: str):
        self._caminho = caminho_db
        self._conexao = sqlite3.connect(caminho_db, check_same_thread=False)
        self._conexao.row_factory = sqlite3.Row
        self._lock = threading.Lock()
        with self._lock:
            self._conexao.executescript(_SCHEMA)
            self._conexao.commit()

    def salvar(self, evento: EventoCI) -> None:
        sql = """
            INSERT INTO webhooks (id, tipo, repositorio, pr_numero, pr_head_sha, pr_base_sha,
                                  payload_bruto, recebido_em, processado_em, sucesso, resultado)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ON CONFLICT(id) DO UPDATE SET
                processado_em = excluded.processado_em,
                sucesso = excluded.sucesso,
                resultado = excluded.resultado
        """
        with self._lock:
            self._conexao.execute(sql, (
                evento.id,
                evento.tipo.value,
                evento.repositorio,
                evento.pr_numero,
                evento.pr_head_sha,
                evento.pr_base_sha,
                json.dumps(evento.payload_bruto, ensure_ascii=False),
                evento.recebido_em.isoformat(),
                evento.processado_em.isoformat() if evento.processado_em else None,
                None if evento.sucesso is None else (1 if evento.sucesso else 0),
                evento.resultado,
            ))
            self._conexao.commit()

    def obter(self, evento_id: str) -> Optional[EventoCI]:
        with self._lock:
            linha = self._conexao.execute(
                "SELECT * FROM webhooks WHERE id = ?", (evento_id,),
            ).fetchone()
        return self._linha_para_evento(linha) if linha else None

    def listar(
        self,
        repositorio: Optional[str] = None,
        processado: Optional[bool] = None,
        limite: int = 50,
    ) -> List[EventoCI]:
        clausulas: list = []
        valores: list = []
        if repositorio is not None:
            clausulas.append("repositorio = ?")
            valores.append(repositorio)
        if processado is True:
            clausulas.append("processado_em IS NOT NULL")
        elif processado is False:
            clausulas.append("processado_em IS NULL")

        sql = "SELECT * FROM webhooks"
        if clausulas:
            sql += " WHERE " + " AND ".join(clausulas)
        sql += " ORDER BY recebido_em DESC LIMIT ?"
        valores.append(limite)

        with self._lock:
            linhas = self._conexao.execute(sql, valores).fetchall()
        return [self._linha_para_evento(l) for l in linhas]

    def fechar(self) -> None:
        with self._lock:
            self._conexao.close()

    @staticmethod
    def _linha_para_evento(linha: sqlite3.Row) -> EventoCI:
        sucesso_int = linha["sucesso"]
        sucesso = None if sucesso_int is None else bool(sucesso_int)
        return EventoCI(
            id=linha["id"],
            tipo=TipoEventoGitHub(linha["tipo"]),
            repositorio=linha["repositorio"],
            pr_numero=linha["pr_numero"],
            pr_head_sha=linha["pr_head_sha"],
            pr_base_sha=linha["pr_base_sha"],
            payload_bruto=json.loads(linha["payload_bruto"]),
            recebido_em=datetime.fromisoformat(linha["recebido_em"]),
            processado_em=datetime.fromisoformat(linha["processado_em"]) if linha["processado_em"] else None,
            sucesso=sucesso,
            resultado=linha["resultado"],
        )
