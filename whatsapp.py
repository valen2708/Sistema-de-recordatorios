from twilio.rest import Client
import os

ACCOUNT_SID = os.environ.get("TWILIO_ACCOUNT_SID", "")
AUTH_TOKEN = os.environ.get("TWILIO_AUTH_TOKEN", "")
TWILIO_WHATSAPP_FROM = os.environ.get("TWILIO_WHATSAPP_FROM", "whatsapp:+14155238886")


def enviar_recordatorio(nombre, telefono, alimento, cliente_id):
    if not ACCOUNT_SID or not AUTH_TOKEN:
        print(f"[SIMULADO] Recordatorio para {nombre} ({telefono}) - {alimento}")
        return "simulado"

    client = Client(ACCOUNT_SID, AUTH_TOKEN)
    numero_destino = f"whatsapp:+{telefono.strip().replace('+', '').replace(' ', '')}"

    mensaje = (
        f"Hola {nombre}! 🐾\n\n"
        f"Mañana se termina el alimento *{alimento}* de tu mascota.\n\n"
        f"¿Querés que te enviemos más?\n"
        f"Respondé *SI* o *NO*"
    )

    msg = client.messages.create(
        from_=TWILIO_WHATSAPP_FROM,
        to=numero_destino,
        body=mensaje
    )
    return msg.sid
