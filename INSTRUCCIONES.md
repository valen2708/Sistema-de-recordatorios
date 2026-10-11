# Sistema de Recordatorios - PetShop

## Cómo funciona

1. Cargás clientes con su alimento, kg comprados y fecha de compra
2. El sistema calcula cuándo se termina el alimento
3. Todos los días a las 9am revisa y manda recordatorios automáticos por WhatsApp
4. Los mensajes salen desde el número del local
5. El cliente responde SI o NO — si dice SI, se reinicia el ciclo automáticamente

---

## Configurar Green API (WhatsApp gratuito)

Green API permite mandar mensajes desde el número del local sin costo.

1. Entrá a **https://green-api.com** y creá una cuenta gratis
2. Creá una nueva instancia
3. En el panel de la instancia, hacé clic en **"Escanear QR"**
4. Abrí WhatsApp en el celular del local → Dispositivos vinculados → Vincular dispositivo → escanear
5. Copiá el **ID de instancia** y el **API Token**

---

## Deploy en Render

1. Subí el repo a GitHub (ya está)
2. Entrá a **https://render.com** y creá una cuenta
3. New → Blueprint → conectá tu repo → Render lee el `render.yaml` automáticamente
4. Una vez creado el servicio, andá a **Environment** y completá:
   - `GREENAPI_INSTANCE` → el ID de instancia de Green API
   - `GREENAPI_TOKEN` → el token de Green API
5. Redeploy y listo

La URL del sistema va a ser algo como: `https://petshop-recordatorios.onrender.com`

---

## Formato del Excel para cargar clientes

| nombre | telefono | alimento | kg_comprados | fecha_compra |
|--------|----------|----------|--------------|--------------|
| Juan López | 5491155555555 | Royal Canin 15kg | 15 | 17/05/2026 |

- **telefono**: sin espacios ni +, con código de país (Argentina = 549 + número)
- **fecha_compra**: formato DD/MM/YYYY o YYYY-MM-DD

---

## Contraseña de acceso

La contraseña por defecto es `0804`. Para cambiarla, editá la línea en `app.py`:
```python
PASSWORD = "0804"
```
