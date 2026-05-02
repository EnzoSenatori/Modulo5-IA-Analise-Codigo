"""Adaptador Postgres para o cache de análises (IA-13)."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any, Dict, Optional

import psycopg2
from psycopg2.extras import Json, RealDictCursor

from app.application.ports.driven.cache_analises import CacheAnalises
from app.domain.entidades.analise_cacheada import AnaliseCacheada, TTL_PADRAO_DIAS


_DDL = """
CREATE TABLE IF NOT EXISTS cache_analises (
    hash_commit  TEXT        NOT NULL,
    tipo_analise TEXT        NOT NULL,
    payload      JSONB       NOT NULL,
    criado_em    TIMESTAMPTZ NOT NULL DEFAULT now(),
    ttl_dias     INTEGER     NOT NULL DEFAULT 30,
    PRIMARY KEY (hash_commit, tipo_analise)
);
"""


class CacheAnalisesPostgres(CacheAnalises):
    """Implementação Postgres do CacheAnalises."""

    def __init__(self, dsn: str) -> None:
        self._dsn = dsn
        self._garantir_schema()

    def _conectar(self):
        return psycopg2.connect(self._dsn)

    def _garantir_schema(self) -> None:
        with self._conectar() as conn, conn.cursor() as cur:
            cur.execute(_DDL)
            conn.commit()

    def obter(
        self, hash_commit: str, tipo_analise: str
    ) -> Optional[AnaliseCacheada]:
        sql = """
            SELECT hash_commit, tipo_analise, payload, criado_em, ttl_dias
              FROM cache_analises
             WHERE hash_commit = %s
               AND tipo_analise = %s
        """
        with self._conectar() as conn, conn.cursor(cursor_factory=RealDictCursor) as cur:
            cur.execute(sql, (hash_commit, tipo_analise))
            linha = cur.fetchone()

        if linha is None:
            return None

        analise = AnaliseCacheada(
            hash_commit=linha["hash_commit"],
            tipo_analise=linha["tipo_analise"],
            payload=linha["payload"],
            criado_em=linha["criado_em"],
            ttl_dias=linha["ttl_dias"],
        )
        if analise.expirado:
            return None
        return analise

    def salvar(
        self,
        hash_commit: str,
        tipo_analise: str,
        payload: Dict[str, Any],
        ttl_dias: int = TTL_PADRAO_DIAS,
    ) -> AnaliseCacheada:
        sql = """
            INSERT INTO cache_analises (hash_commit, tipo_analise, payload, criado_em, ttl_dias)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (hash_commit, tipo_analise)
            DO UPDATE SET payload   = EXCLUDED.payload,
                          criado_em = EXCLUDED.criado_em,
                          ttl_dias  = EXCLUDED.ttl_dias
            RETURNING criado_em
        """
        agora = datetime.now(timezone.utc)
        with self._conectar() as conn, conn.cursor() as cur:
            cur.execute(sql, (hash_commit, tipo_analise, Json(payload), agora, ttl_dias))
            criado_em = cur.fetchone()[0]
            conn.commit()

        return AnaliseCacheada(
            hash_commit=hash_commit,
            tipo_analise=tipo_analise,
            payload=payload,
            criado_em=criado_em,
            ttl_dias=ttl_dias,
        )

    def remover_expirados(self) -> int:
        sql = """
            DELETE FROM cache_analises
             WHERE criado_em + (ttl_dias || ' days')::interval < now()
        """
        with self._conectar() as conn, conn.cursor() as cur:
            cur.execute(sql)
            apagados = cur.rowcount
            conn.commit()
        return apagados
