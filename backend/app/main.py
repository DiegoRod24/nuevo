from __future__ import annotations

import re
from typing import Any, Dict, Optional

from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel

from app.config import settings
from app.services.batch import inspect_excel
from app.services.factiliza import FactilizaClient
from app.services.massive import output_path as massive_output_path
from app.services.massive import status as massive_status
from app.services.massive import submit as submit_massive
from app.services.pj import prepare as pj_prepare, status as pj_status
from app.services.sunat_cpe import SunatCPEClient
from app.services.sunat_web import SunatWebClient

app = FastAPI(title="ROD API", version="0.3.0", description="Backend privado de ROD Assistant")
app.add_middleware(
    CORSMiddleware,
    allow_origins=list(settings.cors_origins) or ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

factiliza = FactilizaClient()
sunat_cpe = SunatCPEClient()


class DNIRequest(BaseModel):
    dni: str
    nombre_declarado: str = ""


class RUCRequest(BaseModel):
    ruc: str
    razon_social_declarada: str = ""


class RepresentativesRequest(BaseModel):
    ruc: str
    razon_social: str = ""


class CPERequest(BaseModel):
    tipo: str
    ruc: str
    serie: str
    numero: str
    fecha: str
    monto: Optional[float] = None


class PJRequest(BaseModel):
    dni: str = ""
    batch_count: int = 0


@app.get("/")
def root() -> Dict[str, Any]:
    return {"ok": True, "service": "ROD API", "version": "0.3.0"}


@app.get("/api/health")
def health() -> Dict[str, Any]:
    return {"ok": True, "environment": settings.app_env, "demo_fallback": settings.demo_fallback, "version": "0.3.0"}


@app.get("/api/health/services")
def services_health() -> Dict[str, Any]:
    f_ok, f_msg = factiliza.config_ok()
    c_ok, c_msg = sunat_cpe.config_ok()
    pj = pj_status()
    sw_ok, sw_msg = SunatWebClient.config_status()
    return {
        "ok": True,
        "services": {
            "factiliza": {"configured": f_ok, "mode": "API", "detail": f_msg},
            "sunat_cpe": {"configured": c_ok, "mode": "API", "detail": c_msg},
            "sunat_web": {"configured": sw_ok, "mode": "HEADLESS_WEB", "detail": sw_msg},
            "pj": {"configured": pj["configured"], "mode": "ASSISTED", "detail": pj["message"]},
            "batch_4b": {"configured": True, "mode": "REAL_MASSIVE", "detail": "Excel masivo: DNI + RUC + observados + cola PJ"},
            "batch_4d": {"configured": True, "mode": "REAL_MASSIVE", "detail": "Excel masivo: proveedor + CPE + observados + cola PJ"},
        },
    }


@app.post("/api/dni")
def dni(req: DNIRequest) -> Dict[str, Any]:
    return factiliza.consultar(req.dni, req.nombre_declarado)


@app.post("/api/ruc")
def ruc(req: RUCRequest) -> Dict[str, Any]:
    clean = re.sub(r"\D", "", req.ruc)
    if len(clean) != 11:
        raise HTTPException(status_code=400, detail="El RUC debe tener 11 dígitos")
    client = SunatWebClient()
    try:
        return client.consultar(clean, req.razon_social_declarada)
    finally:
        client.close()


@app.post("/api/ruc/representatives")
def representatives(req: RepresentativesRequest) -> Dict[str, Any]:
    clean = re.sub(r"\D", "", req.ruc)
    if len(clean) != 11:
        raise HTTPException(status_code=400, detail="El RUC debe tener 11 dígitos")
    client = SunatWebClient()
    try:
        return client.representantes(clean, req.razon_social)
    finally:
        client.close()


@app.post("/api/cpe")
def cpe(req: CPERequest) -> Dict[str, Any]:
    return sunat_cpe.validar(req.model_dump())


@app.post("/api/pj/prepare")
def prepare_pj(req: PJRequest) -> Dict[str, Any]:
    return pj_prepare(req.dni, req.batch_count)


@app.post("/api/files/detect")
async def detect_file(file: UploadFile = File(...)) -> Dict[str, Any]:
    content = await file.read()
    return inspect_excel(content, file.filename or "archivo.xlsx", "AUTO")


@app.post("/api/batch/4b")
async def batch_4b(file: UploadFile = File(...)) -> Dict[str, Any]:
    content = await file.read()
    return inspect_excel(content, file.filename or "anexo4b.xlsx", "4B")


@app.post("/api/batch/4d")
async def batch_4d(file: UploadFile = File(...)) -> Dict[str, Any]:
    content = await file.read()
    return inspect_excel(content, file.filename or "anexo4d.xlsx", "4D")


@app.post("/api/jobs/massive")
async def massive_job(
    file: UploadFile = File(...),
    mode: str = Query("AUTO"),
    dni: bool = Query(True),
    ruc: bool = Query(True),
    cpe: bool = Query(True),
    representatives: bool = Query(False),
    pj_queue: bool = Query(True),
) -> Dict[str, Any]:
    content = await file.read()
    if not content:
        raise HTTPException(status_code=400, detail="El archivo está vacío")
    return submit_massive(
        content=content,
        filename=file.filename or "consulta_masiva.xlsx",
        mode=mode,
        use_dni=dni,
        use_ruc=ruc,
        use_cpe=cpe,
        use_reps=representatives,
        pj_queue=pj_queue,
    )


@app.get("/api/jobs/{job_id}")
def get_massive_job(job_id: str) -> Dict[str, Any]:
    job = massive_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    return job


@app.get("/api/jobs/{job_id}/download")
def download_massive_job(job_id: str):
    job = massive_status(job_id)
    if not job:
        raise HTTPException(status_code=404, detail="Trabajo no encontrado")
    if job.get("status") != "DONE":
        raise HTTPException(status_code=409, detail="El trabajo todavía no terminó")
    path = massive_output_path(job_id)
    if not path:
        raise HTTPException(status_code=404, detail="El archivo de salida ya no está disponible")
    return FileResponse(path, media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet", filename=job.get("download_name") or path.name)
