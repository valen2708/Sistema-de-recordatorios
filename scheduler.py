import os
from datetime import datetime, timedelta
from database import get_conn
from whatsapp import enviar_recordatorio


def revisar_vencimientos():
    from database import get_config
    dias_antes = int(get_config("dias_anticipacion", "1"))
    fecha_objetivo = (datetime.today() + timedelta(days=dias_antes)).strftime("%Y-%m-%d")
    conn = get_conn()

    ventas = conn.execute("""
        SELECT v.*, c.nombre, c.telefono
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE v.fecha_vencimiento = ? AND v.activo = 1 AND c.activo = 1
    """, (fecha_objetivo,)).fetchall()

    for v in ventas:
        ya_enviado = conn.execute(
            "SELECT id FROM recordatorios WHERE venta_id = ? AND fecha_envio = ?",
            (v["id"], datetime.today().strftime("%Y-%m-%d"))
        ).fetchone()

        if ya_enviado:
            continue

        sid = enviar_recordatorio(v["nombre"], v["telefono"], v["alimento"], v["id"])
        conn.execute(
            "INSERT INTO recordatorios (venta_id, cliente_id, fecha_envio) VALUES (?, ?, ?)",
            (v["id"], v["cliente_id"], datetime.today().strftime("%Y-%m-%d"))
        )
        conn.commit()
        print(f"Recordatorio enviado a {v['nombre']} - {sid}")

    conn.close()


def iniciar_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(revisar_vencimientos, "cron", hour=9, minute=0)
    scheduler.start()
    return scheduler
