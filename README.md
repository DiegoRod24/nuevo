# ROD Assistant — Centro Inteligente de Consultas y Validación

ROD es una PWA interactiva para consultas y validaciones operativas por web.

## Qué ya funciona con backend real

- DNI individual por Factiliza.
- DNI + nombre con comparación.
- RUC individual por SUNAT Web headless.
- RUC + razón social.
- Representantes legales bajo demanda.
- Validación de comprobantes SUNAT: Factura, Boleta y RHE.
- Excel masivo 4B: detecta filas, consulta DNI/RUC únicos, separa correctos/observados/fallos técnicos y prepara cola PJ.
- Excel masivo 4D: lo anterior + comprobantes y representantes opcionales.
- Trabajo masivo en segundo plano con progreso y descarga XLSX.
- Excel final con hojas RESULTADO_GENERAL, DNI_FACTILIZA, RUC_SUNAT, COMPROBANTES_SUNAT, OBSERVADOS, PJ_PENDIENTES y CONTROL_INTERNO oculto.
- Poder Judicial preparado como etapa asistida.

## Importante: Cloudflare Pages NO ejecuta Python

`https://nuevo-cv5.pages.dev` solo aloja la interfaz. Para datos reales debes desplegar también el backend `ROD API` usando este mismo repositorio (Docker/Render u otro servidor compatible con Python + Chromium).

Después del despliegue coloca la URL pública del backend en `config.js`:

```js
window.ROD_CONFIG = {
  API_BASE: "https://TU-BACKEND",
  DEMO_FALLBACK: false,
  APP_NAME: "ROD Assistant",
  PUBLIC_URL: "https://nuevo-cv5.pages.dev"
};
```

## Variables privadas

No subas un `.env` real al repositorio. Configura los secretos en el servidor del backend:

- `FACTILIZA_TOKEN`
- `SUNAT_API_RUC_CONSULTANTE`
- `SUNAT_API_CLIENT_ID`
- `SUNAT_API_CLIENT_SECRET`
- `PJ_USUARIO`
- `PJ_CLAVE`

Usa `.env.example` solo como plantilla.

## Flujo masivo

1. Abrir ROD y elegir 4B o 4D.
2. Subir Excel.
3. ROD preanaliza hojas y documentos.
4. `Ejecutar flujo completo REAL`.
5. El backend crea un trabajo masivo y consulta los registros.
6. La web muestra progreso real.
7. Descargar el Excel final.
8. Los DNI aptos quedan en `PJ_PENDIENTES` para la etapa asistida.

### Caché

Dentro de cada trabajo ROD consulta cada DNI/RUC único una sola vez y reutiliza el resultado cuando se repite en el Excel.

### Observados vs fallos técnicos

ROD no mezcla una inconsistencia del registro con una caída de API/portal. El Excel final separa `OBSERVADO` de `PENDIENTE_TECNICO`.

## Cloudflare Pages

Recomendado:

- Production branch: `main`
- Framework preset: `None`
- Root directory: `/`
- Build command: vacío o `exit 0`
- Build output directory: `.`
