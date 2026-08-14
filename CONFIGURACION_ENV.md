# Configurar ROD sin exponer claves

## Regla principal

`nuevo` es un repositorio público. **No subas un archivo `.env` real ni pegues tokens/contraseñas en `config.js`.**

El repositorio trae `backend/.env.example` como plantilla. Las claves reales se cargan en el servicio donde despliegues `ROD API` (por ejemplo, variables de entorno/secrets del proveedor) o en un `.env` local de una PC privada.

## 1. Factiliza

Variables mínimas:

```env
FACTILIZA_TOKEN=
FACTILIZA_ENDPOINT_DNI=https://api.factiliza.com/v1/dni/info/{dni}
```

ROD usa este servicio para DNI y para DNI + nombre.

## 2. SUNAT — comprobantes

Variables mínimas:

```env
SUNAT_API_RUC_CONSULTANTE=
SUNAT_API_CLIENT_ID=
SUNAT_API_CLIENT_SECRET=
SUNAT_API_SCOPE=https://api.sunat.gob.pe/v1/contribuyente/contribuyentes
SUNAT_TOKEN_URL=https://api-seguridad.sunat.gob.pe/v1/clientesextranet/{client_id}/oauth2/token/
SUNAT_CPE_URL=https://api.sunat.gob.pe/v1/contribuyente/contribuyentes/{ruc_consultante}/validarcomprobante
```

Los reintentos, renovación de token y tiempos están incluidos en `.env.example`.

## 3. SUNAT Web — RUC y representantes

En servidor se deja:

```env
SUNAT_WEB_HEADLESS=true
CHROME_BINARY=/usr/bin/chromium
CHROMEDRIVER_PATH=/usr/bin/chromedriver
```

El `Dockerfile` ya instala Chromium + ChromeDriver. ROD consulta sin abrir una ventana en el celular/laptop del usuario.

## 4. Poder Judicial

```env
PJ_USUARIO=
PJ_CLAVE=
PJ_URL=https://sap.pj.gob.pe/consulta-financiamiento-prohibido-web/autenticacion/login
PJ_BRIDGE_URL=
```

PJ es el único módulo asistido. Usuario/clave se pueden precargar. Si el portal pide captcha o confirmación manual, se resuelve en una sesión controlada por `ROD Bridge` y luego continúa la cola.

## 5. Conectar la web con ROD API

Después de desplegar el backend, edita **solo** la URL pública en `config.js` y `frontend/config.js`:

```js
window.ROD_CONFIG = {
  API_BASE: "https://TU-ROD-API.example.com",
  DEMO_FALLBACK: false,
  APP_NAME: "ROD Assistant",
  PUBLIC_URL: "https://nuevo-cv5.pages.dev"
};
```

`API_BASE` no es secreto. Los tokens permanecen exclusivamente en el backend.

## Comprobación

Abre:

```text
https://TU-ROD-API.example.com/api/health/services
```

La web de ROD también muestra el estado de Factiliza, SUNAT CPE, SUNAT Web y PJ en **Servicios**.
