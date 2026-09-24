"""
agent.py
--------
Punto de entrada de la aplicación.
Lanza el servidor web FastAPI mediante Uvicorn.
"""

import uvicorn

if __name__ == "__main__":
    print("Iniciando Auditor de Historias de Usuario en http://127.0.0.1:8000")
    uvicorn.run("server:app", host="127.0.0.1", port=8000, reload=True)