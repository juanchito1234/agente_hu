"""
auditor.py
----------
Responsabilidad única: lógica de auditoría de Historias de Usuario.
Se comunica con el LLM a través del cliente Groq inyectado,
manteniendo esta capa completamente desacoplada de la UI.
"""

from groq import Groq
from config import SYSTEM_PROMPT, INFERENCE_PARAMS


def audit_story(messages_or_story, model: str, client: Groq) -> str:
    """
    Envía la conversación (o la historia de usuario) al LLM y retorna la respuesta completa.

    Permite memoria en la conversación pasando una lista de mensajes [{'role': '...', 'content': '...'}]
    o un string directo.

    Args:
        messages_or_story: Lista de dicts de mensajes o texto de la Historia de Usuario.
        model:             Identificador del modelo Groq a utilizar.
        client:            Cliente Groq autenticado.

    Returns:
        Respuesta completa del modelo como string (markdown).
    """
    if isinstance(messages_or_story, list):
        # Asegurar que el system prompt esté presente como primer mensaje
        chat_messages = []
        if not messages_or_story or messages_or_story[0].get("role") != "system":
            chat_messages.append({"role": "system", "content": SYSTEM_PROMPT})
        chat_messages.extend(messages_or_story)
    elif isinstance(messages_or_story, str):
        if not messages_or_story.strip():
            raise ValueError("La historia de usuario no puede estar vacía.")
        chat_messages = [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user",   "content": messages_or_story.strip()},
        ]
    else:
        raise ValueError("Formato de mensajes no válido.")

    response = client.chat.completions.create(
        messages=chat_messages,
        model=model,
        **INFERENCE_PARAMS,
    )

    return response.choices[0].message.content
