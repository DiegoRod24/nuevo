# 🤖 ROD Assistant — Centro Inteligente de Consultas y Validación

**Web/PWA:** https://nuevo-cv5.pages.dev/  
**Repositorio:** https://github.com/DiegoRod24/nuevo

ROD unifica consultas y procesos operativos en una experiencia conversacional: el usuario puede hablar, escribir o tocar una opción, mientras la parte técnica queda detrás.

## Servicios de ROD

### Consultas rápidas
- DNI
- DNI + nombres
- RUC
- RUC + razón social
- domicilio y datos SUNAT
- representantes legales bajo demanda
- factura, boleta y recibo por honorarios
- Poder Judicial individual o por lote (asistido)

### Procesos integrales
- Anexo 4B
- Anexo 4D
- detección automática de tipo de Excel
- prevalidación
- comparación declarado vs consultado
- procesamiento múltiple
- reproceso de observados
- flujo personalizado
- historial y resultados

## Arquitectura

```text
Celular / Laptop
      │
      ▼
ROD Assistant · Cloudflare Pages
      │ HTTPS
      ▼
ROD API · FastAPI / Docker
  ├─ Factiliza · DNI
  ├─ SUNAT API · comprobantes
  ├─ SUNAT Web headless · RUC / representantes
  ├─ Excel · 4B / 4D
  └─ PJ Bridge · asistido
```

La web nunca contiene `FACTILIZA_TOKEN`, secretos SUNAT ni credenciales PJ.

## Estado actual

- ✅ PWA/UX de ROD
- ✅ voz, texto y botones
- ✅ DNI/Factiliza: adaptador backend real
- ✅ SUNAT CPE: OAuth + consulta + reintentos
- ✅ SUNAT Web: RUC/razón social/domicilio/representantes en headless
- ✅ diagnóstico de motores desde `/api/health/services`
- ✅ detección/prevalidación de Excel
- 🟡 4B/4D: prevalidación web lista; el motor integral legacy se conecta en el backend privado
- 🟡 PJ: preparación lista; la sesión manual/captcha requiere ROD Bridge

## Seguridad

No subas un `.env` real a este repositorio público. Usa `backend/.env.example` como plantilla y carga los valores reales como secrets/variables de entorno del backend. `.gitignore` bloquea `.env`.

Consulta [CONFIGURACION_ENV.md](./CONFIGURACION_ENV.md).

## Cloudflare Pages

La PWA funciona desde la raíz y también desde `frontend/` para mantener compatibilidad con la configuración actual.

Configuración recomendada:

```text
Production branch: main
Framework preset: None
Root directory: /
Build command: exit 0
Build output directory: .
```

## Backend local

```bash
cd backend
python -m venv .venv
# Windows: .venv\Scripts\activate
pip install -r requirements.txt
copy .env.example .env
uvicorn app.main:app --reload --port 8000
```

Luego coloca en `config.js`:

```js
API_BASE: "http://localhost:8000"
```

## Endpoints

```text
GET  /api/health
GET  /api/health/services
POST /api/dni
POST /api/ruc
POST /api/ruc/representatives
POST /api/cpe
POST /api/pj/prepare
POST /api/files/detect
POST /api/batch/4b
POST /api/batch/4d
```
