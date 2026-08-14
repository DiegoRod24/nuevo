from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import List

from dotenv import load_dotenv

BASE_DIR = Path(__file__).resolve().parents[1]
load_dotenv(BASE_DIR / ".env", override=False)
load_dotenv(Path.cwd() / ".env", override=False)


def env(name: str, default: str = "") -> str:
    return str(os.getenv(name, default) or default).strip()


def env_bool(name: str, default: bool = False) -> bool:
    raw = env(name, "true" if default else "false").lower()
    return raw in {"1", "true", "yes", "si", "sí", "on"}


def env_int(name: str, default: int) -> int:
    try:
        return int(env(name, str(default)))
    except Exception:
        return default


def env_float(name: str, default: float) -> float:
    try:
        return float(env(name, str(default)))
    except Exception:
        return default


def env_csv(name: str, default: str = "") -> List[str]:
    return [x.strip() for x in env(name, default).split(",") if x.strip()]


@dataclass(frozen=True)
class Settings:
    app_env: str = env("APP_ENV", "development")
    demo_fallback: bool = env_bool("ROD_DEMO_FALLBACK", True)
    cors_origins: tuple[str, ...] = tuple(env_csv(
        "ROD_CORS_ORIGINS",
        "https://nuevo-cv5.pages.dev,http://localhost:5173,http://127.0.0.1:5173",
    ))
    output_dir: str = env("ROD_OUTPUT_DIR", "outputs")

    @property
    def factiliza_ready(self) -> bool:
        return bool(env("FACTILIZA_TOKEN"))

    @property
    def sunat_cpe_ready(self) -> bool:
        ruc = env("SUNAT_API_RUC_CONSULTANTE")
        return len(ruc) == 11 and ruc.isdigit() and bool(env("SUNAT_API_CLIENT_ID")) and bool(env("SUNAT_API_CLIENT_SECRET"))

    @property
    def sunat_web_ready(self) -> bool:
        return bool(env("SUNAT_WEB_URL", "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"))

    @property
    def pj_ready(self) -> bool:
        return bool(env("PJ_USUARIO")) and bool(env("PJ_CLAVE"))


settings = Settings()
