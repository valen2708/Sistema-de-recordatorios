import sqlite3
from datetime import datetime

DB = "petshop.db"


def get_conn():
    conn = sqlite3.connect(DB)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
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
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            cliente_id INTEGER NOT NULL,
            fecha_envio TEXT NOT NULL,
            respuesta TEXT,
            fecha_respuesta TEXT,
            FOREIGN KEY (cliente_id) REFERENCES clientes(id)
        );
    """)
    conn.commit()
    conn.close()


def calcular_fecha_vencimiento(fecha_compra_str, kg, gramos_por_dia):
    from datetime import timedelta
    fecha = datetime.strptime(fecha_compra_str, "%Y-%m-%d")
    dias = (kg * 1000) / gramos_por_dia
    return (fecha + timedelta(days=int(dias))).strftime("%Y-%m-%d")
