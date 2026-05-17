# Sistema de Recordatorios - PetShop

## Instalación (primera vez)

Abrí el `cmd` en la carpeta del proyecto y ejecutá:

```
pip install -r requirements.txt
```

## Configurar Twilio (para WhatsApp real)

1. Creá una cuenta gratuita en https://www.twilio.com
2. Activá el sandbox de WhatsApp en: Console > Messaging > Try it out > Send a WhatsApp message
3. Desde tu celular, mandá el código que te dan al número de Twilio por WhatsApp
4. Copiá tu Account SID y Auth Token del dashboard
5. Antes de correr el sistema, ejecutá en cmd:

```
set TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxx
set TWILIO_AUTH_TOKEN=xxxxxxxxxxxxxxxx
```

**Sin configurar Twilio**, el sistema igual funciona pero solo simula los envíos (los muestra en consola).

## Correr el sistema

```
python app.py
```

Luego abrí el navegador en: http://localhost:5000

## Formato del Excel para cargar clientes

| nombre | telefono | alimento | kg_comprados | fecha_compra |
|--------|----------|----------|--------------|--------------|
| Juan López | 5491155555555 | Royal Canin 15kg | 15 | 17/05/2026 |

- **telefono**: sin espacios ni +, con código de país (Argentina = 549 + número)
- **fecha_compra**: formato DD/MM/YYYY o YYYY-MM-DD

## Cómo funciona

1. Cargás clientes con su alimento, kg comprados y fecha de compra
2. El sistema calcula automáticamente cuándo se termina el alimento
3. Todos los días a las 9am revisa si algún cliente se queda sin alimento al día siguiente
4. Si es así, le manda un WhatsApp preguntando si quiere pedir más
5. Cuando el cliente responde SI, se registra la nueva compra y se reinicia el ciclo
