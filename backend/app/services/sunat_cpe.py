from __future__ import annotations

import re
import time
from typing import Any, Dict

import requests

from app.config import env, env_bool, env_float, env_int

ESTADO_CP_MAP = {"0": "NO EXISTE", "1": "ACEPTADO", "2": "ANULADO", "3": "AUTORIZADO", "4": "NO AUTORIZADO"}
ONPE_TIPO_MAP = {"1": "01", "2": "03", "3": "R1", "01": "01", "03": "03", "R1": "R1", "RHE": "R1", "RH": "R1"}


def _clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "").replace("\xa0", " ")).strip()


def _deep_find(obj: Any, keys: set[str]) -> Any:
    if isinstance(obj, dict):
        for k, v in obj.items():
            if str(k).lower() in keys:
                return v
        for v in obj.values():
            found = _deep_find(v, keys)
            if found not in (None, ""):
                return found
    elif isinstance(obj, list):
        for item in obj:
            found = _deep_find(item, keys)
            if found not in (None, ""):
                return found
    return ""


class SunatCPEClient:
    def __init__(self) -> None:
        self.session = requests.Session()
        self.token = ""
        self.token_until = 0.0

    def config_ok(self) -> tuple[bool, str]:
        ruc = env("SUNAT_API_RUC_CONSULTANTE")
        if not re.fullmatch(r"\d{11}", ruc):
            return False, "SUNAT_API_RUC_CONSULTANTE debe ser RUC de 11 dígitos"
        if not env("SUNAT_API_CLIENT_ID"):
            return False, "Falta SUNAT_API_CLIENT_ID"
        if not env("SUNAT_API_CLIENT_SECRET"):
            return False, "Falta SUNAT_API_CLIENT_SECRET"
        return True, "OK"

    def _get_token(self, force: bool = False) -> tuple[bool, str]:
        if force:
            self.token = ""
            self.token_until = 0
        if self.token and time.time() < self.token_until - 60:
            return True, "TOKEN_CACHE_OK"
        ok, msg = self.config_ok()
        if not ok:
            return False, msg
        cid, secret = env("SUNAT_API_CLIENT_ID"), env("SUNAT_API_CLIENT_SECRET")
        url = env("SUNAT_TOKEN_URL", "https://api-seguridad.sunat.gob.pe/v1/clientesextranet/{client_id}/oauth2/token/").format(client_id=cid)
        data = {
            "grant_type": "client_credentials",
            "scope": env("SUNAT_API_SCOPE", "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes"),
            "client_id": cid,
            "client_secret": secret,
        }
        retries = max(1, env_int("SUNAT_TOKEN_REINTENTOS", 3))
        timeout = max(5, env_int("SUNAT_TOKEN_TIMEOUT", 40))
        waits = [float(x) for x in env("SUNAT_TOKEN_ESPERAS_REINTENTO", "2,5,10").split(",") if x.strip()]
        last = "TOKEN_SIN_RESPUESTA"
        for i in range(retries):
            try:
                resp = self.session.post(url, data=data, timeout=timeout)
                js = resp.json() if resp.content else {}
                if resp.status_code == 200 and isinstance(js, dict) and js.get("access_token"):
                    self.token = _clean(js["access_token"])
                    self.token_until = time.time() + int(js.get("expires_in", 3600) or 3600)
                    return True, "TOKEN_OK"
                last = f"TOKEN_HTTP_{resp.status_code}: {_clean(js)[:200]}"
                if resp.status_code in {400, 401, 403, 404}:
                    break
            except Exception as exc:
                last = f"TOKEN_ERROR: {type(exc).__name__}: {exc}"
            if i < retries - 1:
                time.sleep(waits[min(i, len(waits)-1)] if waits else 2)
        return False, last

    @staticmethod
    def _physical_series(cod_comp: str, serie: str) -> bool:
        digits = re.sub(r"\D", "", serie or "")
        return bool(digits) and digits == (serie or "").strip() and cod_comp in {"01", "03"}

    def validar(self, data: Dict[str, Any]) -> Dict[str, Any]:
        cod_comp = ONPE_TIPO_MAP.get(_clean(data.get("tipo") or data.get("codComp")).upper(), _clean(data.get("tipo") or data.get("codComp")).upper())
        ruc_emisor = re.sub(r"\D", "", _clean(data.get("ruc") or data.get("numRuc")))
        serie = _clean(data.get("serie") or data.get("numeroSerie")).upper()
        numero_raw = _clean(data.get("numero"))
        fecha = _clean(data.get("fecha") or data.get("fechaEmision"))
        monto_raw = data.get("monto")
        if cod_comp not in {"01", "03", "R1"}:
            return {"ok": False, "status": "TIPO_INVALIDO", "message": "Tipo de comprobante no soportado."}
        if len(ruc_emisor) not in {8, 11}:
            return {"ok": False, "status": "RUC_INVALIDO", "message": "Documento del emisor inválido."}
        if not serie or not numero_raw or not fecha:
            return {"ok": False, "status": "DATOS_INCOMPLETOS", "message": "Serie, número y fecha son obligatorios."}
        ok, token_msg = self._get_token()
        if not ok:
            return {"ok": False, "status": "CONFIG_REQUIRED", "message": token_msg}

        payload: Dict[str, Any] = {
            "numRuc": ruc_emisor,
            "codComp": cod_comp,
            "numeroSerie": serie,
            "numero": int(numero_raw) if numero_raw.isdigit() else numero_raw,
            "fechaEmision": fecha,
        }
        physical = self._physical_series(cod_comp, serie)
        if not physical and monto_raw not in (None, ""):
            payload["monto"] = float(monto_raw)
        elif cod_comp == "R1" and monto_raw not in (None, ""):
            payload["monto"] = float(monto_raw)

        url = env("SUNAT_CPE_URL", "https://api.sunat.gob.pe/v1/contribuyente/contribuyentes/{ruc_consultante}/validarcomprobante").format(ruc_consultante=env("SUNAT_API_RUC_CONSULTANTE"))
        retries = max(1, env_int("SUNAT_CPE_REINTENTOS", 4))
        timeout = max(5, env_int("SUNAT_CPE_TIMEOUT", 45))
        waits = [float(x) for x in env("SUNAT_CPE_ESPERAS_REINTENTO", "2,5,10,20").split(",") if x.strip()]
        last = "SIN_RESPUESTA"
        for attempt in range(1, retries + 1):
            try:
                resp = self.session.post(url, headers={"Authorization": f"Bearer {self.token}", "Content-Type": "application/json"}, json=payload, timeout=timeout)
                try:
                    js = resp.json()
                except Exception:
                    js = {"raw": (resp.text or "")[:1000]}
                if resp.status_code == 401 and attempt < retries:
                    self._get_token(force=True)
                    last = "TOKEN_RENOVADO"
                    continue
                data_obj = js.get("data") if isinstance(js, dict) and isinstance(js.get("data"), dict) else {}
                estado = _clean(data_obj.get("estadoCp") if data_obj else "") or _clean(_deep_find(js, {"estadocp", "estadocomprobante"}))
                estado_ruc = _clean(data_obj.get("estadoRuc") if data_obj else "") or _clean(_deep_find(js, {"estadoruc"}))
                condicion = _clean(data_obj.get("condDomiRuc") if data_obj else "") or _clean(_deep_find(js, {"conddomiruc", "condiciondomicilio"}))
                obs = data_obj.get("Observaciones", data_obj.get("observaciones", "")) if data_obj else _deep_find(js, {"observaciones"})
                if estado:
                    text = ESTADO_CP_MAP.get(estado, f"CODIGO_{estado}")
                    human = "COMPROBANTE ACEPTADO" if estado in {"1", "3"} else ("COMPROBANTE ANULADO" if estado == "2" else "REVISAR COMPROBANTE")
                    return {
                        "ok": True,
                        "status": text,
                        "human_status": human,
                        "estado_cp": estado,
                        "estado_cp_texto": text,
                        "estado_ruc": estado_ruc,
                        "condicion_ruc": condicion,
                        "observaciones": obs,
                        "tipo": cod_comp,
                        "serie": serie,
                        "numero": numero_raw,
                        "attempts": attempt,
                    }
                last = f"HTTP_{resp.status_code}_SIN_ESTADO"
                if resp.status_code in {400, 403, 404, 422}:
                    break
            except requests.Timeout:
                last = "TIMEOUT"
            except Exception as exc:
                last = f"ERROR: {type(exc).__name__}: {exc}"
            if attempt < retries:
                time.sleep(waits[min(attempt-1, len(waits)-1)] if waits else 2)
        return {"ok": False, "status": "PENDIENTE_TECNICO", "message": last}
