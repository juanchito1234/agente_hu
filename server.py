"""
server.py
---------
Servidor FastAPI ligero para la aplicación de Auditoría de Historias de Usuario.
Provee endpoints REST para obtener configuración y ejecutar auditorías,
sirviendo la interfaz web (HTML/CSS/JS) estática directamente.
"""

import os
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel
from typing import List, Optional

from config import GROQ_MODELS, DEFAULT_MODEL, load_default_api_keys
from groq_client import create_client, InvalidApiKeyError
from auditor import audit_story
from table_formatter import markdown_to_tsv, has_table

app = FastAPI(title="Auditor de Historias de Usuario API")

# Modelo de petición para auditar
class AuditRequest(BaseModel):
    historia: str
    apiKey: str
    model: str

@app.get("/api/config")
def get_config():
    """Devuelve las API keys por defecto (env) y los modelos disponibles."""
    default_keys = load_default_api_keys()
    return {
        "models": GROQ_MODELS,
        "defaultModel": DEFAULT_MODEL,
        "defaultKeys": default_keys
    }

@app.post("/api/audit")
def handle_audit(req: AuditRequest):
    """Ejecuta la auditoría utilizando la key y modelo enviados."""
    if not req.historia or not req.historia.strip():
        raise HTTPException(status_code=400, detail="Por favor ingresa el contexto o la Historia de Usuario.")
    
    if not req.apiKey or not req.apiKey.strip():
        raise HTTPException(status_code=400, detail="Por favor selecciona o ingresa una API Key de Groq válida.")

    try:
        client = create_client(req.apiKey)
        result_md = audit_story(req.historia, req.model, client)
        tsv_data = markdown_to_tsv(result_md) if has_table(result_md) else ""
        return {
            "success": True,
            "resultMarkdown": result_md,
            "tsv": tsv_data
        }
    except InvalidApiKeyError as e:
        raise HTTPException(status_code=401, detail=f"API Key inválida: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al contactar Groq: {str(e)}")

# Servir archivos estáticos del directorio static/
static_dir = os.path.join(os.path.dirname(__file__), "static")
if os.path.exists(static_dir):
    app.mount("/static", StaticFiles(directory=static_dir), name="static")

@app.get("/", response_class=HTMLResponse)
def read_root():
    """Sirve la página index.html principal."""
    index_path = os.path.join(static_dir, "index.html")
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            return f.read()
    return "<h1>Frontend no encontrado</h1>"
