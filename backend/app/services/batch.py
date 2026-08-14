from __future__ import annotations

import io
import re
from typing import Any, Dict

import pandas as pd


def _norm_col(c: Any) -> str:
    return re.sub(r"[^A-Z0-9]+", " ", str(c or "").upper()).strip()


def inspect_excel(content: bytes, filename: str, expected: str = "AUTO") -> Dict[str, Any]:
    try:
        xls = pd.ExcelFile(io.BytesIO(content))
    except Exception as exc:
        return {"ok": False, "status": "ARCHIVO_INVALIDO", "message": f"No se pudo abrir el Excel: {exc}"}
    total_rows = 0
    dni = set()
    ruc = set()
    sheets = []
    detected = "DESCONOCIDO"
    hints_4b = 0
    hints_4d = 0
    for name in xls.sheet_names:
        try:
            df = pd.read_excel(xls, sheet_name=name, dtype=object)
        except Exception:
            continue
        rows = len(df)
        total_rows += rows
        cols = [_norm_col(c) for c in df.columns]
        joined = " | ".join(cols)
        if any(x in joined for x in ["APORTE EFECTIVO", "APORTE ESPECIE", "APORTANTE"]):
            hints_4b += 1
        if any(x in joined for x in ["COMPROBANTE", "SERIE", "FECHA EMISION", "PROVEEDOR"]):
            hints_4d += 1
        for col in df.columns:
            vals = df[col].dropna().astype(str).str.replace(r"\D", "", regex=True)
            for v in vals:
                if len(v) == 8:
                    dni.add(v)
                elif len(v) == 11:
                    ruc.add(v)
        sheets.append({"name": name, "rows": rows, "columns": [str(c) for c in df.columns]})
    if hints_4d > hints_4b and hints_4d:
        detected = "4D"
    elif hints_4b:
        detected = "4B"
    elif expected in {"4B", "4D"}:
        detected = expected
    return {
        "ok": True,
        "status": "PREVALIDADO",
        "filename": filename,
        "detected_type": detected,
        "rows": total_rows,
        "dni_unique": len(dni),
        "ruc_unique": len(ruc),
        "sheets": sheets,
        "message": "Archivo inspeccionado. La ejecución integral 4B/4D reutilizará los motores legacy en el backend privado.",
    }
