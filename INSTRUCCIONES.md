# Sistema de Recordatorios - PetShop

## Requisitos previos

- Python 3.8+
- Node.js 16+

---

## Instalación

### 1. Dependencias Python

```
pip install -r requirements.txt
```

### 2. Dependencias del servidor WhatsApp (Node)

```
cd whatsapp_server
npm install
```

---

## Correr el sistema

Necesitás abrir **dos terminales**:

### Terminal 1 — Servidor WhatsApp

```
cd whatsapp_server
node index.js
```

La primera vez, abrí el navegador en: **http://localhost:3000/qr**

Escaneá el QR con el celular del local:
- Abrí WhatsApp → Dispositivos vinculados → Vincular dispositivo
- Apuntá la cámara al QR

La sesión queda guardada. La próxima vez no hace falta escanear de nuevo.

### Terminal 2 — Sistema web (Flask)

```
python app.py
```

Abrí el navegador en: **http://localhost:5000**

---

## Cómo funciona

1. Cargás clientes con su alimento, kg comprados y fecha de compra
2. El sistema calcula automáticamente cuándo se termina el alimento
3. En el Dashboard ves los clientes que vencen en los próximos 7 días
4. Apretás el botón **Enviar** → sale el WhatsApp desde el número del local
5. El cliente responde SI o NO (se registra automáticamente si usás el webhook)

---

## Formato del Excel para cargar clientes

| nombre | telefono | alimento | kg_comprados | fecha_compra |
|--------|----------|----------|--------------|--------------|
| Juan López | 5491155555555 | Royal Canin 15kg | 15 | 17/05/2026 |

- **telefono**: sin espacios ni +, con código de país (Argentina = 549 + número)
- **fecha_compra**: formato DD/MM/YYYY o YYYY-MM-DD

---

## Variables de entorno opcionales

| Variable | Default | Descripción |
|----------|---------|-------------|
| `WA_SERVER_URL` | `http://localhost:3000` | URL del servidor WhatsApp Node |
| `WA_PORT` | `3000` | Puerto del servidor Node |
| `DATABASE_URL` | (vacío = SQLite local) | PostgreSQL para producción |
