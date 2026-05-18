import os
import sqlite3
from datetime import datetime, timedelta

DATABASE_URL = os.environ.get("DATABASE_URL", "")


def _pg_url():
    url = DATABASE_URL
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql://", 1)
    return url


def _fix_sql(sql):
    if DATABASE_URL:
        return sql.replace("?", "%s")
    return sql


class Row(dict):
    def __getitem__(self, key):
        if isinstance(key, int):
            return list(self.values())[key]
        return super().__getitem__(key)


class Cursor:
    def __init__(self, cur, is_pg):
        self._cur = cur
        self._is_pg = is_pg

    def fetchall(self):
        rows = self._cur.fetchall()
        return [Row(r) for r in rows] if self._is_pg else rows

    def fetchone(self):
        row = self._cur.fetchone()
        if row is None:
            return None
        return Row(row) if self._is_pg else row


class Connection:
    def __init__(self):
        self._is_pg = bool(DATABASE_URL)
        if self._is_pg:
            import psycopg2
            import psycopg2.extras
            self._conn = psycopg2.connect(_pg_url(), cursor_factory=psycopg2.extras.RealDictCursor)
        else:
            self._conn = sqlite3.connect("petshop.db")
            self._conn.row_factory = sqlite3.Row

    def execute(self, sql, params=()):
        cur = self._conn.cursor()
        cur.execute(_fix_sql(sql), params)
        return Cursor(cur, self._is_pg)

    def executescript(self, sql):
        if self._is_pg:
            cur = self._conn.cursor()
            for stmt in sql.strip().split(";"):
                stmt = stmt.strip()
                if stmt:
                    cur.execute(stmt)
        else:
            self._conn.executescript(sql)

    def commit(self):
        self._conn.commit()

    def close(self):
        self._conn.close()


def get_conn():
    return Connection()


def init_db():
    conn = get_conn()
    if DATABASE_URL:
        pk = "SERIAL PRIMARY KEY"
    else:
        pk = "INTEGER PRIMARY KEY AUTOINCREMENT"

    conn.executescript(f"""
        CREATE TABLE IF NOT EXISTS clientes (
            id {pk},
            nombre TEXT NOT NULL,
            telefono TEXT NOT NULL,
            alimento TEXT NOT NULL,
            kg_comprados REAL NOT NULL,
            fecha_compra TEXT NOT NULL,
            gramos_por_dia REAL NOT NULL,
            fecha_vencimiento TEXT NOT NULL,
            activo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS recordatorios (
            id {pk},
            cliente_id INTEGER NOT NULL,
            fecha_envio TEXT NOT NULL,
            respuesta TEXT,
            fecha_respuesta TEXT
        )
    """)
    conn.commit()
    conn.close()


def calcular_fecha_vencimiento(fecha_compra_str, kg, gramos_por_dia):
    fecha = datetime.strptime(fecha_compra_str, "%Y-%m-%d")
    dias = (kg * 1000) / gramos_por_dia
    return (fecha + timedelta(days=int(dias))).strftime("%Y-%m-%d")
