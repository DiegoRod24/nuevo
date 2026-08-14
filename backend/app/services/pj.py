from __future__ import annotations

from typing import Any, Dict

from app.config import env


def status() -> Dict[str, Any]:
    user = env("PJ_USUARIO")
    password = env("PJ_CLAVE")
    bridge = env("PJ_BRIDGE_URL")
    return {
        "configured": bool(user and password),
        "assisted": True,
        "bridge_configured": bool(bridge),
        "login_url": env("PJ_URL", "https://sap.pj.gob.pe/consulta-financiamiento-prohibido-web/autenticacion/login"),
        "message": "PJ es asistido: usuario/clave pueden precargarse; captcha o confirmación de acceso se resuelve manualmente cuando corresponda.",
    }


def prepare(dni: str = "", batch_count: int = 0) -> Dict[str, Any]:
    info = status()
    info.update({
        "ok": True,
        "status": "AUTH_REQUIRED",
        "dni": dni,
        "batch_count": batch_count,
        "next_action": "OPEN_PJ_SESSION",
    })
    return info
