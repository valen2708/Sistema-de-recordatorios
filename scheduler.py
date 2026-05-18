import os
from datetime import datetime, timedelta
from database import get_conn
from whatsapp import enviar_recordatorio


def revisar_vencimientos():
    manana = (datetime.today() + timedelta(days=1)).strftime("%Y-%m-%d")
    conn = get_conn()

    clientes = conn.execute(
        "SELECT * FROM clientes WHERE fecha_vencimiento = ? AND activo = 1",
        (manana,)
    ).fetchall()

    for c in clientes:
        ya_enviado = conn.execute(
            "SELECT id FROM recordatorios WHERE cliente_id = ? AND fecha_envio = ?",
            (c["id"], datetime.today().strftime("%Y-%m-%d"))
        ).fetchone()

        if ya_enviado:
            continue

        sid = enviar_recordatorio(c["nombre"], c["telefono"], c["alimento"], c["id"])
        conn.execute(
            "INSERT INTO recordatorios (cliente_id, fecha_envio) VALUES (?, ?)",
            (c["id"], datetime.today().strftime("%Y-%m-%d"))
        )
        conn.commit()
        print(f"Recordatorio enviado a {c['nombre']} - {sid}")

    conn.close()


def iniciar_scheduler():
    from apscheduler.schedulers.background import BackgroundScheduler
    scheduler = BackgroundScheduler()
    scheduler.add_job(revisar_vencimientos, "cron", hour=9, minute=0)
    scheduler.start()
    return scheduler
