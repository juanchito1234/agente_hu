"""
ui/components.py
----------------
Responsabilidad única: proveer funciones auxiliares y constantes
de UI reutilizables. Evita duplicar HTML/JS inline en app.py.
"""

# ---------------------------------------------------------------------------
# JavaScript global que se inyecta una vez en la página
# ---------------------------------------------------------------------------
GLOBAL_JS = """
function initApp() {
    // Inicialización si es requerida
}


// ---- Revelar / ocultar una API key ----
function toggleKeyVisibility(inputId, btnId) {
    const inp = document.getElementById(inputId);
    const btn = document.getElementById(btnId);
    if (!inp) return;
    if (inp.type === 'password') {
        inp.type = 'text';
        btn.textContent = '\\u{1F648}';
    } else {
        inp.type = 'password';
        btn.textContent = '\\u{1F441}\\uFE0F';
    }
}

// ---- Copiar tabla al portapapeles y mostrar toast ----
function copyTsv(textareaId) {
    const el = document.getElementById(textareaId);
    let text = el ? (el.value || el.innerText || '') : '';

    if (!text.trim()) {
        // Intenta obtener la tabla directamente de la zona de resultados si el textarea está vacío
        const resArea = document.querySelector('.result-area table');
        if (resArea) {
            text = resArea.innerText || resArea.textContent || '';
        }
    }

    if (!text.trim()) {
        showToast('⚠️ No hay tabla generada para copiar.', 'warn');
        return;
    }

    if (navigator.clipboard && window.isSecureContext) {
        navigator.clipboard.writeText(text).then(() => {
            showToast('✅ Tabla copiada — pega con Ctrl+V en Word o Docs', 'ok');
        }).catch(() => {
            fallbackCopy(text);
        });
    } else {
        fallbackCopy(text);
    }
}

function fallbackCopy(text) {
    const tempInput = document.createElement('textarea');
    tempInput.value = text;
    document.body.appendChild(tempInput);
    tempInput.select();
    try {
        document.execCommand('copy');
        showToast('✅ Tabla copiada — pega con Ctrl+V en Word o Docs', 'ok');
    } catch (err) {
        showToast('❌ Error al copiar. Copia manualmente.', 'warn');
    }
    document.body.removeChild(tempInput);
}

// ---- Toast helper ----
function showToast(msg, type) {
    let toast = document.getElementById('hu-toast');
    if (!toast) {
        toast = document.createElement('div');
        toast.id = 'hu-toast';
        toast.className = 'copy-toast';
        document.body.appendChild(toast);
    }
    toast.textContent = msg;
    toast.style.background = type === 'warn' ? '#f59e0b' : '#10b981';
    toast.style.color = '#ffffff';
    toast.style.display = 'block';
    clearTimeout(toast._timer);
    toast._timer = setTimeout(() => { toast.style.display = 'none'; }, 3500);
}
"""


# ---------------------------------------------------------------------------
# HTML del header de la aplicación
# ---------------------------------------------------------------------------
def header_html() -> str:
    return """
    <div class="hu-header">
      <div class="hu-badge">⚡ Groq · INVEST Framework</div>
      <h1>Auditor de Historias de Usuario</h1>
      <p>Genera, evalúa y exporta Historias de Usuario alineadas al marco INVEST.</p>
    </div>
    """


# ---------------------------------------------------------------------------
# Constantes de texto para la UI
# ---------------------------------------------------------------------------
PLACEHOLDER_HISTORIA = (
    "Describe el contexto del proyecto y las funcionalidades que necesitas.\n\n"
    "Ejemplo:\n"
    "Sistema de gestión de biblioteca universitaria. Los estudiantes deben poder "
    "buscar libros, reservarlos en línea y recibir notificaciones cuando estén "
    "disponibles. Los bibliotecarios necesitan gestionar el inventario y generar "
    "reportes de préstamos."
)

LABEL_GENERAR = "🚀 Generar Historias de Usuario"
LABEL_COPIAR  = "📋 Copiar tabla (Docs / Word)"
LABEL_LIMPIAR = "🗑️ Limpiar"
