# ROD Shop

Versión pública de ROD Shop preparada para Cloudflare Pages.

La misma tienda está disponible en varias rutas de salida para evitar despliegues en blanco por una configuración distinta de Cloudflare:

- `/`
- `/public`
- `/dist`
- `/frontend`
- `/frontend/public`
- `/frontend/dist`

## Configuración recomendada de Cloudflare Pages

- Production branch: `main`
- Root directory: `frontend`
- Framework preset: `None`
- Build command: `exit 0`
- Build output directory: `.`

Si Cloudflare usa otra salida, `public` o `dist` también contienen la misma versión.
