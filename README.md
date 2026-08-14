# ROD Assistant — Centro Inteligente de Consultas y Validación

ROD es una PWA interactiva diseñada como interfaz unificada para consultas y validaciones operativas.

## Módulos incluidos en la demo

- DNI individual
- DNI + nombres
- RUC individual
- RUC + razón social
- Representantes legales
- Validación de comprobantes (factura, boleta y RH)
- Poder Judicial individual y masivo con login/captcha manual
- Anexo 4B
- Anexo 4D
- Detección automática de tipo de archivo
- Prevalidación de archivos
- Procesamiento de varios archivos
- Comparador declarado vs consultado
- Reprocesamiento de observados
- Flujo personalizado
- Historial y resultados locales
- Voz, micrófono continuo y animaciones de ROD
- PWA instalable en celular y laptop

## Estado

La versión pública funciona en modo DEMO para probar la experiencia sin exponer credenciales ni secretos. Los motores reales de SUNAT, Factiliza y Poder Judicial deben conectarse mediante backend privado.

## Cloudflare Pages

Esta publicación deja los mismos archivos en raíz, `frontend`, `public`, `dist`, `frontend/public` y `frontend/dist` para evitar errores por configuración previa del directorio de salida.

Recomendado:

- Production branch: `main`
- Framework preset: `None`
- Root directory: `/`
- Build command: vacío o `exit 0`
- Build output directory: `.`
