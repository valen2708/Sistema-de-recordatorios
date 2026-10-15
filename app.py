import os
from flask import Flask, render_template, request, redirect, url_for, flash, session, jsonify
from functools import wraps
from database import init_db, get_conn, calcular_fecha_vencimiento
from scheduler import iniciar_scheduler
from whatsapp import get_estado_conexion
import pandas as pd
from datetime import datetime

app = Flask(__name__)
app.secret_key = "petshop-secret-2024"

PASSWORD = "0804"


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get("logged_in"):
            return redirect(url_for("login"))
        return f(*args, **kwargs)
    return decorated


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        if request.form.get("password") == PASSWORD:
            session["logged_in"] = True
            return redirect(url_for("dashboard"))
        flash("Contraseña incorrecta.", "danger")
    return render_template("login.html")


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def dashboard():
    conn = get_conn()
    from datetime import timedelta
    hoy = datetime.today().strftime("%Y-%m-%d")
    proximos_7 = (datetime.today() + timedelta(days=7)).strftime("%Y-%m-%d")

    por_vencer_raw = conn.execute("""
        SELECT v.*, c.nombre, c.telefono
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE v.fecha_vencimiento BETWEEN ? AND ? AND v.activo = 1 AND c.activo = 1
        ORDER BY v.fecha_vencimiento
    """, (hoy, proximos_7)).fetchall()

    por_vencer = []
    for v in por_vencer_raw:
        dias = (datetime.strptime(v["fecha_vencimiento"], "%Y-%m-%d") - datetime.today()).days
        por_vencer.append({"v": v, "dias": dias})

    total_clientes = conn.execute("SELECT COUNT(*) FROM clientes WHERE activo = 1").fetchone()[0]
    total_recordatorios = conn.execute("SELECT COUNT(*) FROM recordatorios").fetchone()[0]
    respondieron_si = conn.execute("SELECT COUNT(*) FROM recordatorios WHERE respuesta = 'SI'").fetchone()[0]
    conn.close()

    wa_status = get_estado_conexion()

    return render_template("dashboard.html",
                           por_vencer=por_vencer,
                           total_clientes=total_clientes,
                           total_recordatorios=total_recordatorios,
                           respondieron_si=respondieron_si,
                           wa_status=wa_status)


# ── CLIENTES ──────────────────────────────────────────────────────────────────

@app.route("/clientes")
@login_required
def clientes():
    conn = get_conn()
    lista = conn.execute("SELECT * FROM clientes WHERE activo = 1 ORDER BY nombre").fetchall()
    conn.close()
    return render_template("clientes.html", clientes=lista)


@app.route("/clientes/nuevo", methods=["GET", "POST"])
@login_required
def nuevo_cliente():
    if request.method == "POST":
        nombre = request.form["nombre"].strip()
        telefono = request.form["telefono"].strip()
        conn = get_conn()
        conn.execute(
            "INSERT INTO clientes (nombre, telefono) VALUES (?,?)",
            (nombre, telefono)
        )
        conn.commit()
        conn.close()
        flash(f"Cliente {nombre} agregado.", "success")
        return redirect(url_for("clientes"))
    return render_template("nuevo_cliente.html")


@app.route("/clientes/<int:cid>")
@login_required
def historial_cliente(cid):
    conn = get_conn()
    cliente = conn.execute("SELECT * FROM clientes WHERE id = ? AND activo = 1", (cid,)).fetchone()
    if not cliente:
        conn.close()
        flash("Cliente no encontrado.", "danger")
        return redirect(url_for("clientes"))
    ventas_raw = conn.execute("""
        SELECT * FROM ventas WHERE cliente_id = ? AND activo = 1 ORDER BY fecha_compra DESC
    """, (cid,)).fetchall()
    conn.close()
    ventas = []
    for v in ventas_raw:
        dias = (datetime.strptime(v["fecha_vencimiento"], "%Y-%m-%d") - datetime.today()).days
        ventas.append({"v": v, "dias": dias})
    return render_template("historial_cliente.html", cliente=cliente, ventas=ventas)


@app.route("/clientes/<int:cid>/eliminar", methods=["POST"])
@login_required
def eliminar_cliente(cid):
    conn = get_conn()
    conn.execute("UPDATE clientes SET activo = 0 WHERE id = ?", (cid,))
    conn.execute("UPDATE ventas SET activo = 0 WHERE cliente_id = ?", (cid,))
    conn.commit()
    conn.close()
    flash("Cliente eliminado.", "warning")
    return redirect(url_for("clientes"))


@app.route("/api/buscar-clientes")
@login_required
def buscar_clientes():
    q = request.args.get("q", "").strip()
    conn = get_conn()
    resultados = conn.execute(
        "SELECT id, nombre, telefono FROM clientes WHERE activo = 1 AND (nombre LIKE ? OR telefono LIKE ?) LIMIT 10",
        (f"%{q}%", f"%{q}%")
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in resultados])


# ── VENTAS ────────────────────────────────────────────────────────────────────

@app.route("/ventas")
@login_required
def ventas():
    conn = get_conn()
    lista_raw = conn.execute("""
        SELECT v.*, c.nombre, c.telefono
        FROM ventas v
        JOIN clientes c ON v.cliente_id = c.id
        WHERE v.activo = 1 AND c.activo = 1
        ORDER BY v.fecha_compra DESC
    """).fetchall()
    conn.close()
    lista = []
    for v in lista_raw:
        dias = (datetime.strptime(v["fecha_vencimiento"], "%Y-%m-%d") - datetime.today()).days
        lista.append({"v": v, "dias": dias})
    return render_template("ventas.html", ventas=lista)


@app.route("/ventas/nueva", methods=["GET", "POST"])
@login_required
def nueva_venta():
    if request.method == "POST":
        cliente_id = request.form["cliente_id"]
        alimento = request.form["alimento"].strip()
        kg = float(request.form["kg_comprados"])
        fecha = request.form["fecha_compra"]
        gramos = float(request.form["gramos_por_dia"])

        fecha_venc = calcular_fecha_vencimiento(fecha, kg, gramos)

        conn = get_conn()
        # Verificar que el cliente existe
        cliente = conn.execute("SELECT * FROM clientes WHERE id = ? AND activo = 1", (cliente_id,)).fetchone()
        if not cliente:
            flash("Cliente no encontrado.", "danger")
            conn.close()
            return redirect(url_for("nueva_venta"))

        conn.execute(
            "INSERT INTO ventas (cliente_id, alimento, kg_comprados, fecha_compra, gramos_por_dia, fecha_vencimiento) VALUES (?,?,?,?,?,?)",
            (cliente_id, alimento, kg, fecha, gramos, fecha_venc)
        )
        conn.commit()
        conn.close()
        flash(f"Venta registrada para {cliente['nombre']}. El alimento se termina el {fecha_venc}.", "success")
        return redirect(url_for("ventas"))

    return render_template("nueva_venta.html")


@app.route("/ventas/cargar-excel", methods=["GET", "POST"])
@login_required
def cargar_excel():
    if request.method == "POST":
        archivo = request.files.get("archivo")
        gramos_default = float(request.form.get("gramos_por_dia", 300))

        if not archivo or not archivo.filename.endswith((".xlsx", ".xls")):
            flash("Seleccioná un archivo Excel válido (.xlsx o .xls)", "danger")
            return redirect(url_for("cargar_excel"))

        try:
            df = pd.read_excel(archivo)
            df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]

            conn = get_conn()
            agregados = 0
            for _, row in df.iterrows():
                nombre = str(row["nombre"]).strip()
                telefono = str(row["telefono"]).strip()
                alimento = str(row["alimento"]).strip()
                fecha_str = pd.to_datetime(row["fecha_compra"]).strftime("%Y-%m-%d")
                kg = float(row["kg_comprados"])
                gramos = float(row["gramos_por_dia"]) if "gramos_por_dia" in row and pd.notna(row.get("gramos_por_dia")) else gramos_default
                fecha_venc = calcular_fecha_vencimiento(fecha_str, kg, gramos)

                # Buscar o crear cliente por teléfono
                cliente = conn.execute(
                    "SELECT id FROM clientes WHERE telefono = ? AND activo = 1", (telefono,)
                ).fetchone()
                if cliente:
                    cliente_id = cliente["id"]
                else:
                    conn.execute("INSERT INTO clientes (nombre, telefono) VALUES (?,?)", (nombre, telefono))
                    conn.commit()
                    cliente_id = conn.execute(
                        "SELECT id FROM clientes WHERE telefono = ? ORDER BY id DESC LIMIT 1", (telefono,)
                    ).fetchone()["id"]

                conn.execute(
                    "INSERT INTO ventas (cliente_id, alimento, kg_comprados, fecha_compra, gramos_por_dia, fecha_vencimiento) VALUES (?,?,?,?,?,?)",
                    (cliente_id, alimento, kg, fecha_str, gramos, fecha_venc)
                )
                agregados += 1

            conn.commit()
            conn.close()
            flash(f"Se cargaron {agregados} ventas correctamente.", "success")
            return redirect(url_for("ventas"))

        except Exception as e:
            flash(f"Error al leer el archivo: {str(e)}", "danger")
            return redirect(url_for("cargar_excel"))

    return render_template("cargar_excel.html")


@app.route("/ventas/<int:vid>/eliminar", methods=["POST"])
@login_required
def eliminar_venta(vid):
    conn = get_conn()
    conn.execute("UPDATE ventas SET activo = 0 WHERE id = ?", (vid,))
    conn.commit()
    conn.close()
    flash("Venta eliminada.", "warning")
    return redirect(url_for("ventas"))


@app.route("/ventas/<int:vid>/enviar-recordatorio", methods=["POST"])
@login_required
def enviar_recordatorio_manual(vid):
    conn = get_conn()
    v = conn.execute("""
        SELECT v.*, c.nombre, c.telefono
        FROM ventas v JOIN clientes c ON v.cliente_id = c.id
        WHERE v.id = ?
    """, (vid,)).fetchone()
    if v:
        mensaje_custom = request.form.get("mensaje_custom", "").strip()
        if mensaje_custom:
            from whatsapp import enviar_mensaje_personalizado
            sid = enviar_mensaje_personalizado(v["telefono"], mensaje_custom)
        else:
            from whatsapp import enviar_recordatorio
            sid = enviar_recordatorio(v["nombre"], v["telefono"], v["alimento"], v["id"])
        conn.execute(
            "INSERT INTO recordatorios (venta_id, cliente_id, fecha_envio) VALUES (?, ?, ?)",
            (v["id"], v["cliente_id"], datetime.today().strftime("%Y-%m-%d"))
        )
        conn.commit()
        flash(f"Recordatorio enviado a {v['nombre']}. ID: {sid}", "success")
    conn.close()
    # Volver a donde vino (ventas o historial)
    ref = request.referrer or url_for("ventas")
    return redirect(ref)


# ── RECORDATORIOS ─────────────────────────────────────────────────────────────

@app.route("/recordatorios")
@login_required
def recordatorios():
    conn = get_conn()
    lista = conn.execute("""
        SELECT r.*, c.nombre, c.telefono, v.alimento
        FROM recordatorios r
        LEFT JOIN clientes c ON r.cliente_id = c.id
        LEFT JOIN ventas v ON r.venta_id = v.id
        ORDER BY r.fecha_envio DESC
    """).fetchall()
    conn.close()
    return render_template("recordatorios.html", recordatorios=lista)


# ── API ───────────────────────────────────────────────────────────────────────

@app.route("/api/check-reminders", methods=["POST"])
def check_reminders():
    secret = os.environ.get("SCHEDULER_SECRET", "")
    if not secret or request.form.get("secret") != secret:
        return "Unauthorized", 401
    from scheduler import revisar_vencimientos
    revisar_vencimientos()
    return "OK", 200


if __name__ == "__main__":
    init_db()
    if not os.environ.get("DATABASE_URL"):
        iniciar_scheduler()
    app.run(debug=True, port=5000)
