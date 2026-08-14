# ROD API

Backend privado de **ROD Assistant**. La PWA pública vive en Cloudflare Pages; las claves y automatizaciones reales viven aquí.

## Arranque local

```bash
cd backend
python -m venv .venv
# Windows: .venv\\Scripts\\activate
# Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
copy .env.example .env  # Windows
# cp .env.example .env  # Linux/macOS
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

Abre `http://localhost:8000/docs`.

## Seguridad

- **Nunca** subas `.env` al repositorio.
- En producción, configura las variables desde el panel del hosting (Render/Railway/VM/Windows Bridge).
- Cloudflare Pages solo debe conocer la URL pública de ROD API, nunca los tokens.

## Servicios

- `/api/dni`: Factiliza, sin navegador visible.
- `/api/ruc`: SUNAT Web con Selenium headless.
- `/api/ruc/representatives`: representantes legales SUNAT headless.
- `/api/cpe`: SUNAT OAuth + consulta integrada de comprobantes.
- `/api/pj/prepare`: PJ asistido; prepara sesión y mantiene credenciales solo en backend.
- `/api/files/detect`: detecta estructura de Excel.
- `/api/batch/4b` y `/api/batch/4d`: prevalidación web; punto de integración para los motores integrales legacy.
