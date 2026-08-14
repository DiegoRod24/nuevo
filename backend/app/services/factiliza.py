from __future__ import annotations

import random
import re
import time
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict

import requests

from app.config import env, env_float, env_int


def _clean(value: Any) -> str:
    return re.sub(r"\s+", " ", str(value or "").replace("\xa0", " ")).strip()


def _norm(value: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(value).upper())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def _similarity(a: str, b: str) -> float:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    sa, sb = " ".join(sorted(na.split())), " ".join(sorted(nb.split()))
    return max(SequenceMatcher(None, na, nb).ratio(), SequenceMatcher(None, sa, sb).ratio())


class FactilizaClient:
    def __init__(self) -> None:
        self.token = env("FACTILIZA_TOKEN")
        self.endpoint = env("FACTILIZA_ENDPOINT_DNI", "https://api.factiliza.com/v1/dni/info/{dni}")
        self.timeout = max(5, env_int("FACTILIZA_TIMEOUT", 25))
        self.retries = max(1, env_int("FACTILIZA_REINTENTOS", 3))
        self.session = requests.Session()

    def config_ok(self) -> tuple[bool, str]:
        if not self.token:
            return False, "Falta FACTILIZA_TOKEN"
        return True, "OK"

    def consultar(self, dni: str, nombre_declarado: str = "") -> Dict[str, Any]:
        dni = re.sub(r"\D", "", dni or "")
        if len(dni) != 8:
            return {"ok": False, "status": "DOCUMENTO_INVALIDO", "message": "El DNI debe tener 8 dígitos."}
        ok, msg = self.config_ok()
        if not ok:
            return {"ok": False, "status": "CONFIG_REQUIRED", "message": msg}

        url = self.endpoint.format(dni=dni)
        headers = {
            "Authorization": f"Bearer {self.token}",
            "X-API-Key": self.token,
            "Accept": "application/json",
        }
        last_error = ""
        for attempt in range(1, self.retries + 1):
            try:
                resp = self.session.get(url, headers=headers, timeout=self.timeout)
                if resp.status_code != 200:
                    last_error = f"HTTP_{resp.status_code}: {_clean(resp.text)[:180]}"
                    if resp.status_code in {400, 401, 403, 404}:
                        break
                else:
                    raw = resp.json()
                    payload = raw.get("data", raw) if isinstance(raw, dict) else {}
                    if not isinstance(payload, dict):
                        payload = {}
                    ap_pat = _clean(payload.get("apellido_paterno") or payload.get("apellidoPaterno") or payload.get("ape_paterno")).upper()
                    ap_mat = _clean(payload.get("apellido_materno") or payload.get("apellidoMaterno") or payload.get("ape_materno")).upper()
                    nombres = _clean(payload.get("nombres") or payload.get("prenombres") or payload.get("nombre")).upper()
                    nombre = " ".join(x for x in [ap_pat, ap_mat, nombres] if x).strip()
                    if not nombre:
                        return {"ok": False, "status": "RESPUESTA_SIN_NOMBRE", "message": "Factiliza respondió sin nombre utilizable."}
                    sim = _similarity(nombre_declarado, nombre) if nombre_declarado else None
                    threshold = env_float("MATCH_MIN_SIMILITUD_DNI", 0.82)
                    match = None if sim is None else sim >= threshold
                    return {
                        "ok": True,
                        "status": "OK",
                        "source": "FACTILIZA",
                        "dni": dni,
                        "nombre": nombre,
                        "apellido_paterno": ap_pat,
                        "apellido_materno": ap_mat,
                        "nombres": nombres,
                        "nombre_declarado": _clean(nombre_declarado).upper(),
                        "similarity": round(sim, 3) if sim is not None else None,
                        "match": match,
                        "human_status": "COINCIDE" if match is True else ("NO COINCIDE" if match is False else "DNI ENCONTRADO"),
                    }
            except requests.Timeout:
                last_error = "TIMEOUT"
            except Exception as exc:
                last_error = f"ERROR: {type(exc).__name__}: {exc}"
            if attempt < self.retries:
                time.sleep(0.5 * (1.6 ** (attempt - 1)) + random.uniform(0.0, 0.25))
        return {"ok": False, "status": "ERROR_CONSULTA", "message": last_error or "No se pudo consultar Factiliza."}
