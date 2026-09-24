"""
config.py
---------
Configuración centralizada de la aplicación.
Contiene modelos disponibles, parámetros de inferencia y el system prompt.
"""

from dotenv import load_dotenv
import os

load_dotenv()

# ---------------------------------------------------------------------------
# API Keys por defecto (cargadas desde el entorno al iniciar la app).
# Agrega tantas variables de entorno como keys quieras precargar:
#   GROQ_API_KEY_1, GROQ_API_KEY_2, …
# Si sólo hay GROQ_API_KEY, también se toma en cuenta.
# ---------------------------------------------------------------------------
def load_default_api_keys() -> list[str]:
    """Carga las API keys por defecto desde variables de entorno."""
    keys: list[str] = []

    # Clave principal (nombre clásico)
    main_key = os.getenv("GROQ_API_KEY", "").strip()
    if main_key:
        keys.append(main_key)

    # Claves adicionales numeradas: GROQ_API_KEY_1, GROQ_API_KEY_2, ...
    i = 1
    while True:
        extra = os.getenv(f"GROQ_API_KEY_{i}", "").strip()
        if not extra:
            break
        if extra not in keys:
            keys.append(extra)
        i += 1

    return keys


# ---------------------------------------------------------------------------
# Modelos disponibles en Groq
# ---------------------------------------------------------------------------
GROQ_MODELS: list[str] = [
    "openai/gpt-oss-120b",
    "llama-3.3-70b-versatile",
    "llama-3.1-8b-instant",
    "llama3-70b-8192",
    "llama3-8b-8192",
    "mixtral-8x7b-32768",
    "gemma2-9b-it",
    "meta-llama/llama-4-maverick-17b-128e-instruct",
    "meta-llama/llama-4-scout-17b-16e-instruct",
    "deepseek-r1-distill-llama-70b",
    "qwen-qwq-32b",
]

DEFAULT_MODEL: str = "openai/gpt-oss-120b"

# ---------------------------------------------------------------------------
# Parámetros de inferencia
# ---------------------------------------------------------------------------
INFERENCE_PARAMS: dict = {
    "temperature": 1,
    "max_completion_tokens": 8192,
    "top_p": 1,
    "reasoning_effort": "medium",
    "stream": True,
    "stop": None,
}

# ---------------------------------------------------------------------------
# System prompt
# ---------------------------------------------------------------------------
SYSTEM_PROMPT: str = """
Eres un auditor experto en Historias de Usuario y en el marco INVEST.

Debes crear la Historia de Usuario de modo que cumpla con los siguientes criterios:

- Cumplir con INVEST: Independiente, Negociable, Valiosa, Estimable,
  Pequeña y Verificable.
- El rol, la acción y el beneficio están claramente definidos.
- La historia es suficientemente específica y no demasiado amplia.
- Es coherente con el propósito y alcance del proyecto.
- No existe ambigüedad, redundancia o información innecesaria.
- El actor indicado puede realizar la acción descrita.

Responde de forma breve y directa con:

1. Las historias de usuario generadas completamente.
2. Evaluación INVEST: indica cómo cumple con los principios.
3. Criterios de aceptación sugeridos, cuando sean útiles.

No inventes funcionalidades que no estén relacionadas con el contexto proporcionado
por el usuario.
No conviertas la historia en una especificación técnica.
Haz que las historias de usuario abarquen los distintos tipos de usuario que
pueden interactuar con el sistema.

Formato:
Debes unificar todo en una tabla que contenga tres columnas:
- Historia de usuario generada por el agente.
- Justificación de cumplimiento de los criterios INVEST para la historia en cuestión.
- Criterios de aceptación formulados para esa historia.
"""
