import os
import requests

WA_SERVER = os.environ.get("WA_SERVER_URL", "http://localhost:3000")


def _armar_mensaje(nombre, alimento):
    return (
        f"Hola {nombre}! 🐾\n\n"
        f"Mañana se termina el alimento *{alimento}* de tu mascota.\n\n"
        f"¿Querés que te enviemos más?\n"
        f"Respondé *SI* o *NO*"
    )


def enviar_recordatorio(nombre, telefono, alimento, cliente_id):
    mensaje = _armar_mensaje(nombre, alimento)
    try:
        r = requests.post(
            f"{WA_SERVER}/send",
            json={"telefono": telefono, "mensaje": mensaje},
            timeout=10
        )
        data = r.json()
        if data.get("ok"):
            print(f"[WA] Enviado a {nombre} ({telefono})")
            return "enviado"
        else:
            print(f"[WA] Error al enviar a {nombre}: {data.get('error')}")
            return f"error: {data.get('error')}"
    except requests.exceptions.ConnectionError:
        print(f"[WA] No se pudo conectar al servidor WhatsApp. ¿Está corriendo?")
        return "error: servidor no disponible"
    except Exception as e:
        print(f"[WA] Error inesperado: {e}")
        return f"error: {e}"


def get_estado_conexion():
    """Devuelve el estado del servidor WhatsApp para mostrarlo en el dashboard."""
    try:
        r = requests.get(f"{WA_SERVER}/status", timeout=3)
        return r.json()
    except Exception:
        return {"connected": False, "has_qr": False, "server_down": True}
