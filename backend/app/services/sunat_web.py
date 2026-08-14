from __future__ import annotations

import os
import re
import shutil
import time
import unicodedata
from difflib import SequenceMatcher
from typing import Any, Dict, List, Tuple

from app.config import env, env_bool, env_float, env_int


def _clean(v: Any) -> str:
    return re.sub(r"\s+", " ", str(v or "").replace("\xa0", " ")).strip()


def _norm(v: Any) -> str:
    text = unicodedata.normalize("NFKD", _clean(v).upper())
    text = "".join(ch for ch in text if not unicodedata.combining(ch))
    text = re.sub(r"\b(S\.?A\.?C\.?|S\.?A\.?|E\.?I\.?R\.?L\.?|SRL|SAC|SA)\b", " ", text)
    return re.sub(r"[^A-Z0-9]+", " ", text).strip()


def _similarity(a: Any, b: Any) -> float:
    na, nb = _norm(a), _norm(b)
    if not na or not nb:
        return 0.0
    if na == nb:
        return 1.0
    ta, tb = " ".join(sorted(na.split())), " ".join(sorted(nb.split()))
    return max(SequenceMatcher(None, na, nb).ratio(), SequenceMatcher(None, ta, tb).ratio())


class SunatWebClient:
    """Adaptador headless basado en el flujo real usado por los bots 4B/4D."""

    def __init__(self) -> None:
        self.driver = None
        self.wait = None

    def _imports(self):
        from selenium import webdriver
        from selenium.webdriver.chrome.options import Options
        from selenium.webdriver.chrome.service import Service
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.support import expected_conditions as EC
        from selenium.webdriver.support.ui import Select, WebDriverWait
        from selenium.common.exceptions import TimeoutException
        return webdriver, Options, Service, ActionChains, By, Keys, EC, Select, WebDriverWait, TimeoutException

    @staticmethod
    def config_status() -> tuple[bool, str]:
        try:
            import selenium  # noqa: F401
        except Exception:
            return False, "Falta Selenium en el backend"
        chrome = env("CHROME_BINARY") or env("CHROME_BIN") or shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome") or shutil.which("google-chrome-stable")
        driver = env("CHROMEDRIVER_PATH") or shutil.which("chromedriver")
        if not chrome:
            return False, "Falta Chrome/Chromium en el backend"
        if not driver:
            return False, "Falta ChromeDriver en el backend"
        return True, "Chrome/Chromium + Selenium listos en modo headless"

    def start(self) -> None:
        if self.driver:
            return
        webdriver, Options, Service, *_rest = self._imports()
        opts = Options()
        if env_bool("SUNAT_WEB_HEADLESS", True):
            opts.add_argument("--headless=new")
        opts.add_argument("--window-size=1280,900")
        opts.add_argument("--disable-gpu")
        opts.add_argument("--no-sandbox")
        opts.add_argument("--disable-dev-shm-usage")
        opts.add_argument("--log-level=3")
        opts.add_argument("--disable-blink-features=AutomationControlled")
        opts.add_argument("--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124 Safari/537.36")
        chrome_binary = env("CHROME_BINARY") or env("CHROME_BIN") or shutil.which("chromium") or shutil.which("chromium-browser") or shutil.which("google-chrome") or shutil.which("google-chrome-stable")
        driver_path = env("CHROMEDRIVER_PATH") or shutil.which("chromedriver")
        if chrome_binary:
            opts.binary_location = chrome_binary
        service = Service(executable_path=driver_path) if driver_path else Service()
        self.driver = webdriver.Chrome(service=service, options=opts)
        WebDriverWait = self._imports()[8]
        self.wait = WebDriverWait(self.driver, env_int("SUNAT_WEB_TIMEOUT", 22))

    def close(self) -> None:
        if self.driver:
            try:
                self.driver.quit()
            except Exception:
                pass
        self.driver = None
        self.wait = None

    def _text_page(self, text: str) -> bool:
        try:
            return bool(self.driver.execute_script("return !!document.body && document.body.innerText.includes(arguments[0]);", text))
        except Exception:
            return False

    def _prepare(self, identifier: str) -> str:
        _, _, _, _, By, _, EC, Select, _, _ = self._imports()
        if re.fullmatch(r"\d{11}", identifier):
            button = self.wait.until(EC.element_to_be_clickable((By.ID, "btnPorRuc")))
            self.driver.execute_script("arguments[0].click();", button)
            field = self.wait.until(EC.visibility_of_element_located((By.ID, "txtRuc")))
            typ = "RUC"
        elif re.fullmatch(r"\d{8}", identifier):
            button = self.wait.until(EC.element_to_be_clickable((By.ID, "btnPorDocumento")))
            self.driver.execute_script("arguments[0].click();", button)
            combo = self.wait.until(EC.presence_of_element_located((By.ID, "cmbTipoDoc")))
            Select(combo).select_by_value("1")
            field = self.wait.until(EC.visibility_of_element_located((By.ID, "txtNumeroDocumento")))
            typ = "DNI"
        else:
            raise ValueError("El identificador debe ser DNI de 8 dígitos o RUC de 11 dígitos.")
        field.clear()
        field.send_keys(identifier)
        return typ

    def _open_detail(self) -> None:
        _, _, _, ActionChains, By, Keys, EC, _, WebDriverWait, _ = self._imports()
        WebDriverWait(self.driver, 25).until(lambda d: self._text_page("Relación de contribuyentes") or self._text_page("Número de RUC:"))
        if self._text_page("Número de RUC:"):
            return
        xp = "//span[contains(concat(' ',normalize-space(@class),' '),' glyphicon-chevron-right ') and ancestor::a[1]]"
        arrow = WebDriverWait(self.driver, 15).until(EC.element_to_be_clickable((By.XPATH, xp)))
        link = arrow.find_element(By.XPATH, "ancestor::a[1]")
        def ready(seconds=7):
            try:
                WebDriverWait(self.driver, seconds).until(lambda d: self._text_page("Número de RUC:"))
                return True
            except Exception:
                return False
        try:
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", arrow)
            ActionChains(self.driver).move_to_element(arrow).pause(0.2).click().perform()
        except Exception:
            pass
        if ready():
            return
        try:
            link.send_keys(Keys.ENTER)
        except Exception:
            pass
        if not ready(10):
            raise RuntimeError("SUNAT no abrió la ficha del contribuyente.")

    def _label(self, label: str) -> str:
        _, _, _, _, By, *_ = self._imports()
        xps = [
            f'//h4[contains(normalize-space(.),"{label}")]/../following-sibling::div[1]',
            f'//div[h4[contains(normalize-space(.),"{label}")]]/following-sibling::div[1]',
            f'//h4[contains(. ,"{label}")]/ancestor::div[contains(@class,"row")][1]/div[last()]',
        ]
        for xp in xps:
            try:
                el = self.driver.find_element(By.XPATH, xp)
                text = _clean(el.get_attribute("textContent") or el.text)
                if text:
                    return text
            except Exception:
                continue
        return ""

    @staticmethod
    def _reason_from_numero_ruc(text: str) -> str:
        text = _clean(text)
        m = re.search(r"\b\d{11}\b\s*[-–—:]\s*(.+)$", text)
        return _clean(m.group(1)) if m else ""

    def consultar(self, identifier: str, nombre_declarado: str = "") -> Dict[str, Any]:
        self.start()
        _, _, _, _, By, _, EC, _, _, _ = self._imports()
        self.driver.get(env("SUNAT_WEB_URL", "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"))
        typ = self._prepare(identifier)
        self.wait.until(EC.element_to_be_clickable((By.ID, "btnAceptar"))).click()
        self._open_detail()
        numero_ruc = self._label("Número de RUC")
        ruc_match = re.search(r"\b\d{11}\b", numero_ruc)
        ruc = ruc_match.group(0) if ruc_match else (identifier if typ == "RUC" else "")
        razon = self._label("Nombre o Razón Social") or self._label("Razón Social") or self._reason_from_numero_ruc(numero_ruc)
        sim = _similarity(nombre_declarado, razon) if nombre_declarado else None
        match_ok = None if sim is None else sim >= env_float("MATCH_MIN_SIMILITUD_RUC_OK", 0.92)
        match_review = False if sim is None else (not match_ok and sim >= env_float("MATCH_MIN_SIMILITUD_RUC_REVISAR", 0.84))
        return {
            "ok": bool(ruc or razon),
            "status": "OK" if (ruc or razon) else "NO_ENCONTRADO",
            "source": "SUNAT_WEB",
            "tipo_consulta": typ,
            "ruc": ruc,
            "numero_ruc": numero_ruc,
            "razon_social": razon,
            "tipo_contribuyente": self._label("Tipo Contribuyente"),
            "nombre_comercial": self._label("Nombre Comercial"),
            "fecha_inscripcion": self._label("Fecha de Inscripción"),
            "fecha_inicio_actividades": self._label("Fecha de Inicio de Actividades"),
            "estado": self._label("Estado del Contribuyente"),
            "condicion": self._label("Condición del Contribuyente"),
            "domicilio_fiscal": self._label("Domicilio Fiscal"),
            "comprobantes_electronicos": self._label("Comprobantes Electrónicos"),
            "razon_social_declarada": _clean(nombre_declarado).upper(),
            "similarity": round(sim, 3) if sim is not None else None,
            "match": match_ok,
            "match_review": match_review,
            "human_match_status": (
                "COINCIDE" if match_ok is True else
                "REVISAR SIMILITUD" if match_review else
                "NO COINCIDE" if match_ok is False else
                "SIN COMPARACIÓN"
            ),
        }

    def representantes(self, ruc: str, razon: str = "") -> Dict[str, Any]:
        self.start()
        _, _, _, _, By, _, EC, _, WebDriverWait, TimeoutException = self._imports()
        self.driver.get(env("SUNAT_WEB_URL", "https://e-consultaruc.sunat.gob.pe/cl-ti-itmrconsruc/jcrS00Alias"))
        self._prepare(ruc)
        self.wait.until(EC.element_to_be_clickable((By.ID, "btnAceptar"))).click()
        self._open_detail()
        xp_button = "//button[contains(@class,'btnInfRepLeg') and contains(.,'Representante')]"
        try:
            btn = WebDriverWait(self.driver, 10).until(EC.element_to_be_clickable((By.XPATH, xp_button)))
            self.driver.execute_script("arguments[0].scrollIntoView({block:'center'});", btn)
            self.driver.execute_script("arguments[0].click();", btn)
        except TimeoutException:
            if "REPRESENTANTES LEGALES" not in (self.driver.page_source or "").upper():
                return {"ok": True, "status": "SIN_BOTON_REPRESENTANTES", "representantes": []}
        try:
            WebDriverWait(self.driver, env_int("SUNAT_REPRESENTANTES_TIMEOUT_SEG", 25)).until(
                lambda d: "REPRESENTANTES LEGALES" in (d.page_source or "").upper() or len(d.find_elements(By.XPATH, "//table//tr[td]")) > 0
            )
        except Exception:
            pass
        time.sleep(env_float("SUNAT_REPRESENTANTES_ESPERA_TABLA_SEG", 2.0))
        rows = self.driver.find_elements(By.XPATH, "//table//tr[td]")
        reps: List[Dict[str, Any]] = []
        for tr in rows:
            cells = tr.find_elements(By.TAG_NAME, "td")
            vals = [_clean(td.get_attribute("textContent")) for td in cells]
            if len(vals) < 5 or not vals[1] or not vals[2]:
                continue
            joined = " ".join(vals).upper()
            if "INGRESAR EMAIL" in joined:
                continue
            reps.append({"ruc": ruc, "razon_social": razon, "doc_tipo": vals[0], "doc_num": vals[1], "nombre": vals[2], "cargo": vals[3], "fecha_desde": vals[4]})
        return {"ok": True, "status": "OK" if reps else "SIN_REPRESENTANTES_LEIDOS", "count": len(reps), "representantes": reps}
