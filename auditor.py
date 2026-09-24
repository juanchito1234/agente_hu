"""
auditor.py
----------
Responsabilidad única: lógica de auditoría de Historias de Usuario.
Se comunica con el LLM a través del cliente Groq inyectado,
manteniendo esta capa completamente desacoplada de la UI.
"""

from groq import Groq
from config import SYSTEM_PROMPT, INFERENCE_PARAMS


def audit_story(historia: str, model: str, client: Groq) -> str:
    """
    Envía la historia de usuario al LLM y retorna la respuesta completa.

    Cada llamada es independiente (sin historial): el contexto se compone
    únicamente del system prompt y el mensaje del usuario actual.

    Args:
        historia: Texto de la Historia de Usuario a auditar.
        model:    Identificador del modelo Groq a utilizar.
        client:   Cliente Groq autenticado (inyectado desde la UI).

    Returns:
        Respuesta completa del modelo como string (markdown).

    Raises:
        ValueError: Si la historia está vacía.
        Exception:  Cualquier error de la API Groq se propaga al llamador.
    """
    if not historia or not historia.strip():
        raise ValueError("La historia de usuario no puede estar vacía.")

    response = client.chat.completions.create(
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": historia.strip()},
        ],
        model=model,
        **INFERENCE_PARAMS,
    )

    full_response = ""
    for chunk in response:
        content = chunk.choices[0].delta.content
        if content:
            full_response += content

    return full_response
