from flask import Flask, render_template, request, redirect, url_for, flash
from database import init_db, get_conn, calcular_fecha_vencimiento
from scheduler import iniciar_scheduler
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = "petshop-secret-2024"


@app.route("/")
def dashboard():
    conn = get_conn()
    from datetime import timedelta
    hoy = datetime.today().strftime("%Y-%m-%d")
    proximos_7 = (datetime.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    por_vencer = conn.execute(
        "SELECT * FROM clientes WHERE fecha_vencimiento BETWEEN ? AND ? AND activo = 1 ORDER BY fecha_vencimiento",
        (hoy, proximos_7)
    ).fetchall()

    total_clientes = conn.execute("SELECT COUNT(*) FROM clientes WHERE activo = 1").fetchone()[0]
    total_recordatorios = conn.execute("SELECT COUNT(*) FROM recordatorios").fetchone()[0]
    respondieron_si = conn.execute("SELECT COUNT(*) FROM recordatorios WHERE respuesta = 'SI'").fetchone()[0]
    conn.close()

    return render_template("dashboard.html",
                           por_vencer=por_vencer,
                           total_clientes=total_clientes,
                           total_recordatorios=total_recordatorios,
                           respondieron_si=respondieron_si)


@app.route("/clientes")
def clientes():
    conn = get_conn()
    lista = conn.execute("SELECT * FROM clientes WHERE activo = 1 ORDER BY nombre").fetchall()
    conn.close()
    return render_template("clientes.html", clientes=lista)


@app.route("/clientes/nuevo", methods=["GET", "POST"])
def nuevo_cliente():
    if request.method == "POST":
        nombre = request.form["nombre"]
        telefono = request.form["telefono"]
        alimento = request.form["alimento"]
        kg = float(request.form["kg_comprados"])
        fecha = request.form["fecha_compra"]
        gramos = float(request.form["gramos_por_dia"])

        fecha_venc = calcular_fecha_vencimiento(fecha, kg, gramos)

        conn = get_conn()
        conn.execute(
            "INSERT INTO clientes (nombre, telefono, alimento, kg_comprados, fecha_compra, gramos_por_dia, fecha_vencimiento) VALUES (?,?,?,?,?,?,?)",
            (nombre, telefono, alimento, kg, fecha, gramos, fecha_venc)
        )
        conn.commit()
        conn.close()
        flash(f"Cliente {nombre} agregado. El alimento se termina el {fecha_venc}.", "success")
        return redirect(url_for("clientes"))

    return render_template("nuevo_cliente.html")


@app.route("/clientes/cargar-excel", methods=["GET", "POST"])
def cargar_excel():
    if request.method == "POST":
        archivo = request.files.get("archivo")
        gramos = float(request.form.get("gramos_por_dia", 300))

        if not archivo or not archivo.filename.endswith((".xlsx", ".xls")):
            flash("Seleccioná un archivo Excel válido (.xlsx o .xls)", "danger")
            return redirect(url_for("cargar_excel"))

        try:
            df = pd.read_excel(archivo)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            conn = get_conn()
            agregados = 0
            for _, row in df.iterrows():
                fecha_str = pd.to_datetime(row["fecha_compra"]).strftime("%Y-%m-%d")
                kg = float(row["kg_comprados"])
                fecha_venc = calcular_fecha_vencimiento(fecha_str, kg, gramos)

                conn.execute(
                    "INSERT INTO clientes (nombre, telefono, alimento, kg_comprados, fecha_compra, gramos_por_dia, fecha_vencimiento) VALUES (?,?,?,?,?,?,?)",
                    (str(row["nombre"]), str(row["telefono"]), str(row["alimento"]), kg, fecha_str, gramos, fecha_venc)
                )
                agregados += 1

            conn.commit()
            conn.close()
            flash(f"Se cargaron {agregados} clientes correctamente.", "success")
            return redirect(url_for("clientes"))

        except Exception as e:
            flash(f"Error al leer el archivo: {str(e)}", "danger")
            return redirect(url_for("cargar_excel"))

    return render_template("cargar_excel.html")


@app.route("/recordatorios")
def recordatorios():
    conn = get_conn()
    lista = conn.execute("""
        SELECT r.*, c.nombre, c.alimento, c.telefono
        FROM recordatorios r
        JOIN clientes c ON r.cliente_id = c.id
        ORDER BY r.fecha_envio DESC
    """).fetchall()
    conn.close()
    return render_template("recordatorios.html", recordatorios=lista)


@app.route("/webhook/respuesta", methods=["POST"])
def webhook_respuesta():
    """Twilio llama a este endpoint cuando el cliente responde el WhatsApp."""
    from_number = request.form.get("From", "").replace("whatsapp:+", "")
    body = request.form.get("Body", "").strip().upper()

    conn = get_conn()
    cliente = conn.execute(
        "SELECT * FROM clientes WHERE telefono LIKE ? AND activo = 1",
        (f"%{from_number}%",)
    ).fetchone()

    if cliente and body in ("SI", "SÍ", "NO"):
        recordatorio = conn.execute(
            "SELECT * FROM recordatorios WHERE cliente_id = ? AND respuesta IS NULL ORDER BY fecha_envio DESC LIMIT 1",
            (cliente["id"],)
        ).fetchone()

        if recordatorio:
            conn.execute(
                "UPDATE recordatorios SET respuesta = ?, fecha_respuesta = ? WHERE id = ?",
                (body, datetime.today().strftime("%Y-%m-%d"), recordatorio["id"])
            )

            if body in ("SI", "SÍ"):
                nueva_fecha = datetime.today().strftime("%Y-%m-%d")
                nueva_venc = calcular_fecha_vencimiento(nueva_fecha, cliente["kg_comprados"], cliente["gramos_por_dia"])
                conn.execute(
                    "UPDATE clientes SET fecha_compra = ?, fecha_vencimiento = ? WHERE id = ?",
                    (nueva_fecha, nueva_venc, cliente["id"])
                )

            conn.commit()

    conn.close()
    return '<?xml version="1.0" encoding="UTF-8"?><Response></Response>', 200, {"Content-Type": "text/xml"}


@app.route("/clientes/<int:cid>/eliminar", methods=["POST"])
def eliminar_cliente(cid):
    conn = get_conn()
    conn.execute("UPDATE clientes SET activo = 0 WHERE id = ?", (cid,))
    conn.commit()
    conn.close()
    flash("Cliente eliminado.", "warning")
    return redirect(url_for("clientes"))


if __name__ == "__main__":
    init_db()
    iniciar_scheduler()
    app.run(debug=True, port=5000)
