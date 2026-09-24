"""
table_formatter.py
------------------
Responsabilidad única: transformar la salida markdown del LLM en
formatos copiables para Google Docs y Microsoft Word.

Estrategia de copia:
  - TSV (Tab-Separated Values): al pegar en Google Docs/Word con Ctrl+V,
    ambas aplicaciones lo interpretan automáticamente como una tabla.
  - Se limpia el markdown de la tabla (pipes, guiones) antes de exportar.
"""

import re


def _parse_markdown_table(markdown_text: str) -> list[list[str]]:
    """
    Extrae las filas de una tabla markdown como listas de strings.

    Args:
        markdown_text: Texto completo que puede contener una tabla markdown.

    Returns:
        Lista de filas; cada fila es una lista de celdas (strings limpios).
        Devuelve lista vacía si no se detecta ninguna tabla.
    """
    lines = markdown_text.splitlines()
    rows: list[list[str]] = []

    for line in lines:
        stripped = line.strip()
        # Ignorar líneas separadoras (|---|---|)
        if re.fullmatch(r"[\|\s\-:]+", stripped):
            continue
        if stripped.startswith("|") and stripped.endswith("|"):
            cells = [cell.strip() for cell in stripped[1:-1].split("|")]
            rows.append(cells)

    return rows


def markdown_to_tsv(markdown_text: str) -> str:
    """
    Convierte la tabla markdown en texto TSV listo para pegar en
    Google Docs o Word como tabla.

    Args:
        markdown_text: Salida completa del LLM (puede incluir texto fuera
                       de la tabla; sólo se exporta la tabla).

    Returns:
        String TSV (columnas separadas por tabuladores, filas por saltos
        de línea). Si no hay tabla, devuelve el texto original.
    """
    rows = _parse_markdown_table(markdown_text)
    if not rows:
        return markdown_text  # Sin tabla detectada, devuelve tal cual

    tsv_lines = ["\t".join(row) for row in rows]
    return "\n".join(tsv_lines)


def has_table(markdown_text: str) -> bool:
    """Indica si el texto contiene al menos una tabla markdown."""
    return bool(_parse_markdown_table(markdown_text))
