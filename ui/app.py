"""
ui/app.py
---------
Responsabilidad única: construir y lanzar la interfaz Gradio Blocks.
Orquesta los módulos de dominio (auditor, groq_client, table_formatter)
sin contener lógica de negocio propia.
"""

import os
import sys

# Aseguramos que el directorio raíz esté en el path para importaciones
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import gradio as gr

from config import GROQ_MODELS, DEFAULT_MODEL, load_default_api_keys
from groq_client import create_client, InvalidApiKeyError
from auditor import audit_story
from table_formatter import markdown_to_tsv, has_table
from ui.components import (
    GLOBAL_JS,
    header_html,
    PLACEHOLDER_HISTORIA,
    LABEL_GENERAR,
    LABEL_COPIAR,
    LABEL_LIMPIAR,
)

# ---------------------------------------------------------------------------
# Helpers internos
# ---------------------------------------------------------------------------

def _mask_key(key: str) -> str:
    """Devuelve una versión censurada de la API key para mostrar en el dropdown."""
    if len(key) <= 8:
        return "****"
    return f"{key[:4]}{'*' * (len(key) - 8)}{key[-4:]}"


def _build_key_choices(keys: list[str]) -> list[str]:
    """Genera las etiquetas del dropdown a partir de las keys almacenadas."""
    if not keys:
        return []
    return [f"Key {i+1}: {_mask_key(k)}" for i, k in enumerate(keys)]


# ---------------------------------------------------------------------------
# Manejadores de eventos
# ---------------------------------------------------------------------------

def handle_add_key(new_key: str, keys_state: list[str]):
    """Agrega una nueva API key a la lista si no está duplicada."""
    key = new_key.strip()
    if not key:
        status = "⚠️ Ingresa una API key antes de agregarla."
        choices = _build_key_choices(keys_state)
        return keys_state, gr.update(choices=choices, value=choices[0] if choices else None), "", status

    if key in keys_state:
        status = "⚠️ Esa API key ya está en la lista."
        choices = _build_key_choices(keys_state)
        return keys_state, gr.update(choices=choices, value=choices[0] if choices else None), "", status

    keys_state = keys_state + [key]
    choices = _build_key_choices(keys_state)
    status = f"✅ Key {len(keys_state)} agregada."
    return keys_state, gr.update(choices=choices, value=choices[-1]), "", status


def handle_remove_key(selected_label: str, keys_state: list[str]):
    """Elimina la API key actualmente seleccionada en el dropdown."""
    if not keys_state or not selected_label:
        return keys_state, gr.update(choices=[], value=None), "⚠️ Sin key seleccionada."

    try:
        idx = int(selected_label.split(":")[0].replace("Key", "").strip()) - 1
    except (ValueError, IndexError):
        choices = _build_key_choices(keys_state)
        return keys_state, gr.update(choices=choices, value=selected_label), "⚠️ No se identificó la key."

    if idx < 0 or idx >= len(keys_state):
        choices = _build_key_choices(keys_state)
        return keys_state, gr.update(choices=choices, value=None), "⚠️ Índice fuera de rango."

    keys_state = [k for i, k in enumerate(keys_state) if i != idx]
    choices = _build_key_choices(keys_state)
    return keys_state, gr.update(choices=choices, value=choices[0] if choices else None), "🗑️ Key eliminada."


def handle_audit(historia: str, selected_label: str, model: str, keys_state: list[str]):
    """
    Orquesta la auditoría:
    1. Obtiene la key seleccionada del estado.
    2. Crea el cliente Groq.
    3. Llama al auditor.
    4. Genera el TSV para copia.
    """
    if not historia or not historia.strip():
        return "⚠️ Escribe o pega una Historia de Usuario antes de generar.", "", "❌ Sin historia."

    if not keys_state:
        return "⚠️ Agrega al menos una API key de Groq.", "", "❌ Sin API key."

    try:
        idx = int(selected_label.split(":")[0].replace("Key", "").strip()) - 1
        active_key = keys_state[idx]
    except (ValueError, IndexError, AttributeError):
        active_key = keys_state[0]
        idx = 0

    try:
        client = create_client(active_key)
        result_md = audit_story(historia, model, client)
    except InvalidApiKeyError as e:
        return f"❌ API Key inválida: {e}", "", "❌ Error de autenticación."
    except Exception as e:
        return f"❌ Error al contactar Groq: {e}", "", "❌ Error de conexión."

    tsv = markdown_to_tsv(result_md) if has_table(result_md) else ""
    status = f"✅ **{model}** · Key {idx+1}"
    return result_md, tsv, status


def handle_copy_tsv(tsv_text: str):
    """Dispara copia al portapapeles via JS al presionar el botón de copiar."""
    if not tsv_text or not tsv_text.strip():
        return f"<script>showToast('⚠️ No hay tabla generada para copiar.', 'warn');</script>"
    
    # Sanitizar y escapar caracteres especiales para JS
    escaped = tsv_text.replace("\\", "\\\\").replace("`", "\\`").replace("$", "\\$").replace("\r", "")
    
    script = f"""<script>
    (function() {{
        const text = `{escaped}`;
        if (navigator.clipboard && window.isSecureContext) {{
            navigator.clipboard.writeText(text).then(() => {{
                showToast('✅ Tabla copiada — pega con Ctrl+V en Word o Docs', 'ok');
            }}).catch(() => {{
                fallbackCopy(text);
            }});
        }} else {{
            fallbackCopy(text);
        }}
    }})();
    </script>"""
    return script


def handle_toggle_key_visibility(current_type: str):
    """Alterna la visibilidad del campo de nueva API key."""
    if current_type == "password":
        return gr.update(type="text"), "🙈", "text"
    return gr.update(type="password"), "👁️", "password"


def handle_clear():
    """Limpia el área de entrada y los resultados."""
    return "", "", "", "—"


# ---------------------------------------------------------------------------
# Construcción de la UI
# ---------------------------------------------------------------------------

def build_app() -> tuple[gr.Blocks, str]:
    css_path = os.path.join(os.path.dirname(__file__), "styles.css")
    with open(css_path, "r", encoding="utf-8") as f:
        css = f.read()

    default_keys = load_default_api_keys()
    default_choices = _build_key_choices(default_keys)
    default_selected = default_choices[0] if default_choices else None

    with gr.Blocks(title="Auditor de HUs · Groq") as app:

        # ── Estado de sesión (sin persistencia entre sesiones) ──────────────
        keys_state = gr.State(value=default_keys)
        key_input_type = gr.State(value="password")

        # ── Layout: Native Sidebar + Main ───────────────────────────────────
        with gr.Sidebar(elem_id="hu-sidebar"):

            gr.HTML('<div class="sb-logo">⚡ HU Auditor</div>')

            # ── API Keys ─────────────────────────────────────────────
            gr.HTML('<p class="sb-section-label">API KEYS</p>')

            key_dropdown = gr.Dropdown(
                choices=default_choices,
                value=default_selected,
                label="Key activa",
                interactive=True,
                elem_id="key-dropdown",
            )

            key_status_lbl = gr.Markdown(
                value="✅ Cargada desde .env" if default_keys else "⚠️ Sin keys",
                elem_classes=["sb-status"],
            )

            with gr.Row(elem_classes=["sb-input-row"]):
                new_key_input = gr.Textbox(
                    placeholder="gsk_...",
                    type="password",
                    show_label=False,
                    scale=5,
                    elem_classes=["sb-input"],
                )
                eye_btn = gr.Button("👁️", scale=1, min_width=36, elem_classes=["sb-eye-btn"])

            with gr.Row(elem_classes=["sb-actions-row"]):
                add_key_btn = gr.Button("＋ Agregar", scale=3, elem_classes=["sb-btn-add"])
                remove_key_btn = gr.Button("✕", scale=1, min_width=36, elem_classes=["sb-btn-remove"])

            gr.HTML('<hr class="sb-divider"/>')

            # ── Modelo ───────────────────────────────────────────────
            gr.HTML('<p class="sb-section-label">MODELO</p>')

            model_dropdown = gr.Dropdown(
                choices=GROQ_MODELS,
                value=DEFAULT_MODEL,
                label="Modelo Groq",
                interactive=True,
                elem_id="model-dropdown",
            )

            gr.HTML('<hr class="sb-divider"/>')

            # ── Estado ───────────────────────────────────────────────
            status_lbl = gr.Markdown("—", elem_classes=["sb-global-status"])

        # ════════════════════════════════════════════════════════════════
        # MAIN CONTENT AREA
        # ════════════════════════════════════════════════════════════════
        with gr.Column(elem_id="hu-main"):

                gr.HTML(header_html())

                historia_input = gr.Textbox(
                    lines=8,
                    placeholder=PLACEHOLDER_HISTORIA,
                    label="Contexto y funcionalidades del sistema",
                    show_label=True,
                    elem_id="historia-input",
                )

                with gr.Row(elem_classes=["main-actions-row"]):
                    generate_btn = gr.Button(
                        LABEL_GENERAR,
                        variant="primary",
                        scale=4,
                        elem_classes=["btn-primary"],
                    )
                    clear_btn = gr.Button(
                        LABEL_LIMPIAR,
                        scale=1,
                        elem_classes=["btn-secondary"],
                    )

                result_output = gr.Markdown(
                    value="",
                    elem_id="result-output",
                    elem_classes=["result-area"],
                )

                # Campo invisible que almacena los datos TSV formateados
                tsv_output = gr.Textbox(
                    visible=False,
                    elem_id="tsv-output",
                )

                with gr.Row(elem_classes=["export-action-row"]):
                    copy_btn = gr.Button(
                        LABEL_COPIAR,
                        variant="secondary",
                        elem_classes=["btn-secondary", "btn-copy-table"],
                    )
                    copy_trigger = gr.HTML(value="", visible=False)

        # ── Eventos ─────────────────────────────────────────────────────────

        eye_btn.click(
            fn=handle_toggle_key_visibility,
            inputs=[key_input_type],
            outputs=[new_key_input, eye_btn, key_input_type],
        )

        add_key_btn.click(
            fn=handle_add_key,
            inputs=[new_key_input, keys_state],
            outputs=[keys_state, key_dropdown, new_key_input, key_status_lbl],
        )

        remove_key_btn.click(
            fn=handle_remove_key,
            inputs=[key_dropdown, keys_state],
            outputs=[keys_state, key_dropdown, key_status_lbl],
        )

        generate_btn.click(
            fn=handle_audit,
            inputs=[historia_input, key_dropdown, model_dropdown, keys_state],
            outputs=[result_output, tsv_output, status_lbl],
        )

        copy_btn.click(
            fn=handle_copy_tsv,
            inputs=[tsv_output],
            outputs=[copy_trigger],
        )

        clear_btn.click(
            fn=handle_clear,
            inputs=[],
            outputs=[historia_input, result_output, tsv_output, status_lbl],
        )

    return app, css


# ---------------------------------------------------------------------------
# Punto de entrada alternativo (para tests / ejecución directa)
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    _app, _css = build_app()
    _theme = gr.themes.Base(
        primary_hue="violet",
        neutral_hue="slate",
        font=gr.themes.GoogleFont("Inter"),
    )
    _app.launch(css=_css, js=GLOBAL_JS, theme=_theme)
