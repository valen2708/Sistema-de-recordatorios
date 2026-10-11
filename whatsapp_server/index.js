const { Client, LocalAuth } = require('whatsapp-web.js');
const express = require('express');
const qrcode = require('qrcode');

const app = express();
app.use(express.json());

const PORT = process.env.WA_PORT || 3000;

let qrImageData = null;
let isReady = false;

const client = new Client({
    authStrategy: new LocalAuth({ dataPath: './wa_session' }),
    puppeteer: {
        headless: true,
        args: ['--no-sandbox', '--disable-setuid-sandbox']
    }
});

client.on('qr', async (qr) => {
    isReady = false;
    qrImageData = await qrcode.toDataURL(qr);
    console.log('[WA] QR generado — abrí http://localhost:' + PORT + '/qr para escanearlo');
});

client.on('ready', () => {
    isReady = true;
    qrImageData = null;
    console.log('[WA] Cliente listo y conectado');
});

client.on('disconnected', (reason) => {
    isReady = false;
    console.log('[WA] Desconectado:', reason);
    client.initialize();
});

client.initialize();

// ── Endpoints ────────────────────────────────────────────────

// Estado de conexión
app.get('/status', (req, res) => {
    res.json({ connected: isReady, has_qr: !!qrImageData });
});

// Página con el QR para escanear
app.get('/qr', (req, res) => {
    if (isReady) {
        return res.send('<h2 style="font-family:sans-serif;color:green">✅ WhatsApp ya está conectado</h2>');
    }
    if (!qrImageData) {
        return res.send('<h2 style="font-family:sans-serif">⏳ Generando QR... recargá en unos segundos</h2><script>setTimeout(()=>location.reload(),3000)</script>');
    }
    res.send(`
        <!DOCTYPE html>
        <html>
        <head>
            <meta charset="utf-8">
            <title>Conectar WhatsApp</title>
            <style>
                body { font-family: sans-serif; text-align: center; padding: 40px; background: #f0f2f5; }
                .card { background: white; border-radius: 12px; padding: 32px; display: inline-block; box-shadow: 0 2px 12px rgba(0,0,0,0.1); }
                img { width: 260px; height: 260px; }
                h2 { color: #128C7E; }
                p { color: #666; }
            </style>
            <script>
                // Recarga automática cada 3s hasta que esté conectado
                setInterval(async () => {
                    const r = await fetch('/status');
                    const d = await r.json();
                    if (d.connected) location.reload();
                }, 3000);
            </script>
        </head>
        <body>
            <div class="card">
                <h2>📱 Conectar WhatsApp del local</h2>
                <p>Abrí WhatsApp en el celular → Dispositivos vinculados → Vincular dispositivo</p>
                <img src="${qrImageData}" alt="QR Code">
                <p style="color:#999;font-size:13px">El QR se actualiza automáticamente</p>
            </div>
        </body>
        </html>
    `);
});

// Enviar mensaje
app.post('/send', async (req, res) => {
    const { telefono, mensaje } = req.body;

    if (!isReady) {
        return res.status(503).json({ ok: false, error: 'WhatsApp no está conectado' });
    }
    if (!telefono || !mensaje) {
        return res.status(400).json({ ok: false, error: 'Faltan campos: telefono, mensaje' });
    }

    try {
        // Formatear número: quitar +, espacios, asegurar que termine en @c.us
        const numero = telefono.replace(/\D/g, '') + '@c.us';
        await client.sendMessage(numero, mensaje);
        console.log(`[WA] Mensaje enviado a ${telefono}`);
        res.json({ ok: true });
    } catch (err) {
        console.error('[WA] Error al enviar:', err.message);
        res.status(500).json({ ok: false, error: err.message });
    }
});

app.listen(PORT, () => {
    console.log(`[WA] Servidor corriendo en http://localhost:${PORT}`);
});
