import os
import requests

# Green API - credenciales desde variables de entorno
GREENAPI_INSTANCE = os.environ.get("GREENAPI_INSTANCE", "")
GREENAPI_TOKEN = os.environ.get("GREENAPI_TOKEN", "")
GREENAPI_URL = "https://api.green-api.com"


def _armar_mensaje(nombre, alimento):
    return (
        f"Hola {nombre}! 🐾\n\n"
        f"Mañana se termina el alimento *{alimento}* de tu mascota.\n\n"
        f"¿Querés que te enviemos más?\n"
        f"Respondé *SI* o *NO*"
    )


def enviar_mensaje_personalizado(telefono, mensaje):
    if not GREENAPI_INSTANCE or not GREENAPI_TOKEN:
        print(f"[SIMULADO] Mensaje personalizado a {telefono}")
        return "simulado"
    numero = telefono.strip().replace("+", "").replace(" ", "") + "@c.us"
    url = f"{GREENAPI_URL}/waInstance{GREENAPI_INSTANCE}/sendMessage/{GREENAPI_TOKEN}"
    try:
        r = requests.post(url, json={"chatId": numero, "message": mensaje}, timeout=10)
        data = r.json()
        return data.get("idMessage", f"error: {data}")
    except Exception as e:
        return f"error: {e}"


def enviar_recordatorio(nombre, telefono, alimento, cliente_id):
    if not GREENAPI_INSTANCE or not GREENAPI_TOKEN:
        print(f"[SIMULADO] Recordatorio para {nombre} ({telefono}) - {alimento}")
        return "simulado"

    mensaje = _armar_mensaje(nombre, alimento)

    # Formato Green API: código de país + número + @c.us (sin +)
    numero = telefono.strip().replace("+", "").replace(" ", "") + "@c.us"

    url = f"{GREENAPI_URL}/waInstance{GREENAPI_INSTANCE}/sendMessage/{GREENAPI_TOKEN}"

    try:
        r = requests.post(url, json={
            "chatId": numero,
            "message": mensaje
        }, timeout=10)

        data = r.json()
        if data.get("idMessage"):
            print(f"[WA] Enviado a {nombre} ({telefono}) - ID: {data['idMessage']}")
            return data["idMessage"]
        else:
            print(f"[WA] Error al enviar a {nombre}: {data}")
            return f"error: {data}"

    except Exception as e:
        print(f"[WA] Error inesperado: {e}")
        return f"error: {e}"


def get_estado_conexion():
    """Verifica si la instancia de Green API está conectada."""
    if not GREENAPI_INSTANCE or not GREENAPI_TOKEN:
        return {"connected": False, "no_config": True}

    try:
        url = f"{GREENAPI_URL}/waInstance{GREENAPI_INSTANCE}/getStateInstance/{GREENAPI_TOKEN}"
        r = requests.get(url, timeout=5)
        data = r.json()
        estado = data.get("stateInstance", "")
        return {
            "connected": estado == "authorized",
            "estado": estado,
            "no_config": False
        }
    except Exception:
        return {"connected": False, "no_config": False, "error": True}
