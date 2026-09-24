"""
groq_client.py
--------------
Responsabilidad única: creación y validación del cliente Groq.
Aplica el principio de Responsabilidad Única (SRP) y permite
inyección de dependencia (DIP) al devolver el cliente listo para usar.
"""

from groq import Groq


class InvalidApiKeyError(ValueError):
    """Se lanza cuando la API key proporcionada está vacía o es inválida."""
    pass


def create_client(api_key: str) -> Groq:
    """
    Crea y devuelve un cliente Groq autenticado con la key indicada.

    Args:
        api_key: La clave de API de Groq. No puede estar vacía.

    Returns:
        Una instancia de Groq lista para hacer llamadas.

    Raises:
        InvalidApiKeyError: Si la api_key está vacía o es solo espacios.
    """
    key = api_key.strip() if api_key else ""
    if not key:
        raise InvalidApiKeyError(
            "La API key no puede estar vacía. "
            "Ingresa una clave válida de Groq."
        )
    return Groq(api_key=key)
