/**
 * app.js — Lógica de Interfaz y Cliente REST
 * Manejo de estado local de API keys, consumo del backend FastAPI,
 * colapsado de sidebar sin glitches y copiado directo de tabla en TSV/HTML.
 */

document.addEventListener('DOMContentLoaded', () => {
  // Elementos DOM
  const sidebar = document.getElementById('sidebar');
  const collapseSidebarBtn = document.getElementById('collapseSidebarBtn');
  const expandSidebarBtn = document.getElementById('expandSidebarBtn');
  
  const keySelect = document.getElementById('keySelect');
  const keyStatus = document.getElementById('keyStatus');
  const newKeyInput = document.getElementById('newKeyInput');
  const toggleEyeBtn = document.getElementById('toggleEyeBtn');
  const addKeyBtn = document.getElementById('addKeyBtn');
  const removeKeyBtn = document.getElementById('removeKeyBtn');
  
  const modelSelect = document.getElementById('modelSelect');
  const globalStatus = document.getElementById('globalStatus');
  
  const storyInput = document.getElementById('storyInput');
  const generateBtn = document.getElementById('generateBtn');
  const clearBtn = document.getElementById('clearBtn');
  const spinner = document.getElementById('spinner');
  
  const resultsSection = document.getElementById('resultsSection');
  const markdownContent = document.getElementById('markdownContent');
  const copyTableBtn = document.getElementById('copyTableBtn');
  const toast = document.getElementById('toast');

  // Estado de la sesión (en memoria local del navegador)
  let apiKeys = [];
  let currentRawTsv = "";

  // 1. Inicialización: Cargar configuración desde el servidor
  init();

  async function init() {
    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      
      // Modelos
      modelSelect.innerHTML = data.models.map(m => 
        `<option value="${m}" ${m === data.defaultModel ? 'selected' : ''}>${m}</option>`
      ).join('');

      // API Keys precargadas desde .env
      if (data.defaultKeys && data.defaultKeys.length > 0) {
        apiKeys = [...data.defaultKeys];
      }
      renderKeys();

    } catch (err) {
      showToast('⚠️ No se pudo conectar con el servidor backend.', 'warn');
      globalStatus.innerHTML = '<span style="color: var(--danger)">❌ Error de conexión</span>';
    }
  }

  // 2. Manejo de Sidebar Toggle
  collapseSidebarBtn.addEventListener('click', () => {
    sidebar.classList.add('collapsed');
    expandSidebarBtn.style.display = 'flex';
  });

  expandSidebarBtn.addEventListener('click', () => {
    sidebar.classList.remove('collapsed');
    expandSidebarBtn.style.display = 'none';
  });

  // 3. Manejo de API Keys (dropdown + agregar + eliminar + censurar)
  function maskKey(key) {
    if (!key || key.length <= 8) return '****';
    return `${key.slice(0, 4)}${'*'.repeat(key.length - 8)}${key.slice(-4)}`;
  }

  function renderKeys() {
    if (apiKeys.length === 0) {
      keySelect.innerHTML = '<option value="">(Sin keys registradas)</option>';
      keyStatus.textContent = '⚠️ Agrega al menos una API key';
      keyStatus.style.color = 'var(--warning)';
      return;
    }

    keySelect.innerHTML = apiKeys.map((k, idx) => 
      `<option value="${k}">Key ${idx + 1}: ${maskKey(k)}</option>`
    ).join('');
    
    keyStatus.textContent = `✅ ${apiKeys.length} key(s) disponible(s)`;
    keyStatus.style.color = 'var(--text-secondary)';
  }

  toggleEyeBtn.addEventListener('click', () => {
    if (newKeyInput.type === 'password') {
      newKeyInput.type = 'text';
      toggleEyeBtn.textContent = '🙈';
    } else {
      newKeyInput.type = 'password';
      toggleEyeBtn.textContent = '👁️';
    }
  });

  addKeyBtn.addEventListener('click', () => {
    const val = newKeyInput.value.trim();
    if (!val) {
      showToast('⚠️ Ingresa el texto de la API key antes de agregar.', 'warn');
      return;
    }
    if (apiKeys.includes(val)) {
      showToast('⚠️ Esa API key ya está en la lista.', 'warn');
      return;
    }
    apiKeys.push(val);
    newKeyInput.value = '';
    renderKeys();
    keySelect.value = val;
    showToast('✅ API Key agregada con éxito.', 'ok');
  });

  removeKeyBtn.addEventListener('click', () => {
    const selectedKey = keySelect.value;
    if (!selectedKey) {
      showToast('⚠️ No hay ninguna key seleccionada para eliminar.', 'warn');
      return;
    }
    apiKeys = apiKeys.filter(k => k !== selectedKey);
    renderKeys();
    showToast('🗑️ API Key eliminada.', 'ok');
  });

  // 4. Acción de Auditoría (Generación)
  generateBtn.addEventListener('click', async () => {
    const historia = storyInput.value.trim();
    const apiKey = keySelect.value;
    const model = modelSelect.value;

    if (!historia) {
      showToast('⚠️ Escribe o pega una Historia de Usuario primero.', 'warn');
      storyInput.focus();
      return;
    }

    if (!apiKey) {
      showToast('⚠️ Selecciona o agrega una API key de Groq.', 'warn');
      return;
    }

    // UI Loading state
    generateBtn.disabled = true;
    spinner.style.display = 'inline-block';
    globalStatus.textContent = '🔄 Consultando a Groq...';

    try {
      const response = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ historia, apiKey, model })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error en la auditoría');
      }

      // Render markdown response
      currentRawTsv = data.tsv;
      markdownContent.innerHTML = marked.parse(data.resultMarkdown);
      resultsSection.style.display = 'block';
      resultsSection.scrollIntoView({ behavior: 'smooth' });

      globalStatus.innerHTML = `<span style="color: var(--success)">✅ Listo · ${model}</span>`;
      showToast('🚀 Auditoría generada correctamente.', 'ok');

    } catch (err) {
      showToast(`❌ ${err.message}`, 'warn');
      globalStatus.innerHTML = `<span style="color: var(--danger)">❌ ${err.message}</span>`;
    } finally {
      generateBtn.disabled = false;
      spinner.style.display = 'none';
    }
  });

  // Limpiar
  clearBtn.addEventListener('click', () => {
    storyInput.value = '';
    resultsSection.style.display = 'none';
    markdownContent.innerHTML = '';
    currentRawTsv = '';
    globalStatus.textContent = 'Estado: Listo';
  });

  // 5. Copiar tabla directamente al portapapeles (Docs / Word compatible)
  copyTableBtn.addEventListener('click', () => {
    const tableEl = markdownContent.querySelector('table');
    
    if (!tableEl && !currentRawTsv) {
      showToast('⚠️ No hay ninguna tabla para copiar.', 'warn');
      return;
    }

    // Preferir copiar directamente el HTML de la tabla para mantener formato completo en Word/Docs,
    // acompañado del formato TSV plano como fallback en ClipboardItem.
    let tsvText = currentRawTsv;
    if (!tsvText && tableEl) {
      tsvText = tableToTSV(tableEl);
    }

    if (navigator.clipboard && window.ClipboardItem && tableEl) {
      try {
        const htmlBlob = new Blob([tableEl.outerHTML], { type: 'text/html' });
        const textBlob = new Blob([tsvText], { type: 'text/plain' });
        const item = new ClipboardItem({
          'text/html': htmlBlob,
          'text/plain': textBlob
        });

        navigator.clipboard.write([item]).then(() => {
          showToast('📋 ¡Tabla copiada! Pega directamente con Ctrl+V en Word o Docs.', 'ok');
        }).catch(() => {
          fallbackCopyText(tsvText);
        });
        return;
      } catch (e) {
        // Fallback standard
      }
    }

    fallbackCopyText(tsvText);
  });

  function tableToTSV(table) {
    const rows = Array.from(table.querySelectorAll('tr'));
    return rows.map(row => {
      const cells = Array.from(row.querySelectorAll('th, td'));
      return cells.map(c => c.innerText.trim().replace(/\n/g, ' ')).join('\t');
    }).join('\n');
  }

  function fallbackCopyText(text) {
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => {
      showToast('📋 Tabla copiada en formato TSV. Pega con Ctrl+V.', 'ok');
    }).catch(() => {
      const tempArea = document.createElement('textarea');
      tempArea.value = text;
      document.body.appendChild(tempArea);
      tempArea.select();
      document.execCommand('copy');
      document.body.removeChild(tempArea);
      showToast('📋 Tabla copiada (fallback). Pega con Ctrl+V.', 'ok');
    });
  }

  // Toast Helper
  function showToast(msg, type = 'ok') {
    toast.textContent = msg;
    toast.style.background = type === 'warn' ? 'var(--warning)' : 'var(--success)';
    toast.style.color = type === 'warn' ? '#000' : '#fff';
    toast.classList.add('show');
    
    setTimeout(() => {
      toast.classList.remove('show');
    }, 3500);
  }
});
