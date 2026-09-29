/**
 * app.js — Chat Interactivo con Memoria y Persistencia en LocalStorage
 * Manejo del historial de mensajes, guardado/restauración local en navegador,
 * interacción continua con el LLM Groq y exportación de tablas en formato Rich Text / TSV.
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
  
  const chatFeed = document.getElementById('chatFeed');
  const storyInput = document.getElementById('storyInput');
  const generateBtn = document.getElementById('generateBtn');
  const newChatBtn = document.getElementById('newChatBtn');
  const spinner = document.getElementById('spinner');
  const toast = document.getElementById('toast');

  // Estado de la sesión
  let apiKeys = [];
  let chatHistory = []; // Array de { role: 'user' | 'assistant', content: string, timestamp: string }

  const STORAGE_KEY_CHAT = 'hu_auditor_chat_history';
  const STORAGE_KEY_KEYS = 'hu_auditor_api_keys';

  // 1. Inicialización: Cargar configuración y chat persistente
  init();

  async function init() {
    loadLocalKeys();
    loadLocalChat();

    try {
      const res = await fetch('/api/config');
      const data = await res.json();
      
      // Modelos
      modelSelect.innerHTML = data.models.map(m => 
        `<option value="${m}" ${m === data.defaultModel ? 'selected' : ''}>${m}</option>`
      ).join('');

      // API Keys precargadas desde .env si no hay en localStorage
      if (apiKeys.length === 0 && data.defaultKeys && data.defaultKeys.length > 0) {
        apiKeys = [...data.defaultKeys];
        saveLocalKeys();
      }
      renderKeys();

    } catch (err) {
      showToast('⚠️ No se pudo conectar con el servidor backend.', 'warn');
      globalStatus.innerHTML = '<span style="color: var(--danger)">❌ Error de conexión</span>';
    }
  }

  // --- PERSISTENCIA LOCALSTORAGE ---
  function loadLocalKeys() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_KEYS);
      if (stored) apiKeys = JSON.parse(stored);
    } catch (e) { console.error('Error al cargar keys:', e); }
  }

  function saveLocalKeys() {
    try {
      localStorage.setItem(STORAGE_KEY_KEYS, JSON.stringify(apiKeys));
    } catch (e) { console.error('Error al guardar keys:', e); }
  }

  function loadLocalChat() {
    try {
      const stored = localStorage.getItem(STORAGE_KEY_CHAT);
      if (stored) {
        chatHistory = JSON.parse(stored);
      }
    } catch (e) { console.error('Error al cargar historial:', e); }
    renderChatFeed();
  }

  function saveLocalChat() {
    try {
      localStorage.setItem(STORAGE_KEY_CHAT, JSON.stringify(chatHistory));
    } catch (e) { console.error('Error al guardar chat:', e); }
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

  // 3. Manejo de API Keys
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
    newKeyInput.type = newKeyInput.type === 'password' ? 'text' : 'password';
    toggleEyeBtn.textContent = newKeyInput.type === 'password' ? '👁️' : '🙈';
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
    saveLocalKeys();
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
    saveLocalKeys();
    renderKeys();
    showToast('🗑️ API Key eliminada.', 'ok');
  });

  // 4. Renderizado del Feed de Chat
  function renderChatFeed() {
    chatFeed.innerHTML = '';

    if (chatHistory.length === 0) {
      chatFeed.innerHTML = `
        <div class="empty-chat">
          <div class="empty-chat-icon">💬</div>
          <h3>¡Bienvenido al Chat de Auditoría de Historias de Usuario!</h3>
          <p>Escribe una historia de usuario o contexto de proyecto para comenzar. La conversación se guardará automáticamente.</p>
        </div>
      `;
      return;
    }

    chatHistory.forEach((msg, idx) => {
      const msgDiv = document.createElement('div');
      msgDiv.className = `chat-message ${msg.role}`;
      
      const roleName = msg.role === 'user' ? 'TÚ' : '🤖 AUDITOR GROQ';
      const timeStr = msg.timestamp || new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

      let contentHtml = '';
      if (msg.role === 'user') {
        contentHtml = `<div class="message-bubble">${escapeHtml(msg.content)}</div>`;
      } else {
        const parsedMd = marked.parse(msg.content);
        const hasTable = parsedMd.includes('<table');
        contentHtml = `
          <div class="message-bubble markdown-body">
            ${parsedMd}
            ${hasTable ? `
              <div class="message-actions">
                <button class="btn btn-copy copy-msg-table-btn" data-msg-idx="${idx}">
                  📋 Copiar Tabla (Docs / Word)
                </button>
              </div>
            ` : ''}
          </div>
        `;
      }

      msgDiv.innerHTML = `
        <div class="message-header">
          <span>${roleName}</span> · <span>${timeStr}</span>
        </div>
        ${contentHtml}
      `;

      chatFeed.appendChild(msgDiv);
    });

    // Delegación de eventos para copiar tablas de respuestas específicas
    document.querySelectorAll('.copy-msg-table-btn').forEach(btn => {
      btn.onclick = (e) => {
        const msgBubble = e.target.closest('.message-bubble');
        const tableEl = msgBubble.querySelector('table');
        if (tableEl) {
          copyTableAsRichText(tableEl);
        } else {
          showToast('⚠️ No se encontró tabla en este mensaje.', 'warn');
        }
      };
    });

    scrollToBottom();
  }

  function scrollToBottom() {
    chatFeed.scrollTop = chatFeed.scrollHeight;
  }

  function escapeHtml(str) {
    return str.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;").replace(/'/g, "&#039;");
  }

  // 5. Envío de Mensaje al Chat
  async function sendMessage() {
    const text = storyInput.value.trim();
    const apiKey = keySelect.value;
    const model = modelSelect.value;

    if (!text) {
      showToast('⚠️ Escribe un mensaje antes de enviar.', 'warn');
      storyInput.focus();
      return;
    }

    if (!apiKey) {
      showToast('⚠️ Selecciona o agrega una API key de Groq.', 'warn');
      return;
    }

    // Agregar mensaje del usuario
    const userMsg = {
      role: 'user',
      content: text,
      timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
    };
    chatHistory.push(userMsg);
    saveLocalChat();
    renderChatFeed();

    storyInput.value = '';
    storyInput.style.height = 'auto';

    // UI Loading state
    generateBtn.disabled = true;
    spinner.style.display = 'inline-block';
    globalStatus.textContent = '🔄 Consultando a Groq...';

    // Preparar array de mensajes para backend (role + content)
    const formattedMessages = chatHistory.map(m => ({ role: m.role, content: m.content }));

    try {
      const response = await fetch('/api/audit', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          messages: formattedMessages,
          apiKey,
          model
        })
      });

      const data = await response.json();

      if (!response.ok) {
        throw new Error(data.detail || 'Error al procesar el mensaje');
      }

      // Guardar respuesta del asistente
      const assistantMsg = {
        role: 'assistant',
        content: data.resultMarkdown,
        timestamp: new Date().toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
      };

      chatHistory.push(assistantMsg);
      saveLocalChat();
      renderChatFeed();

      globalStatus.innerHTML = `<span style="color: var(--success)">✅ Respondido · ${model}</span>`;

    } catch (err) {
      showToast(`❌ ${err.message}`, 'warn');
      globalStatus.innerHTML = `<span style="color: var(--danger)">❌ ${err.message}</span>`;
    } finally {
      generateBtn.disabled = false;
      spinner.style.display = 'none';
    }
  }

  generateBtn.addEventListener('click', sendMessage);

  // Manejo de Enter para enviar mensaje
  storyInput.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  // Reiniciar / Nuevo Chat
  newChatBtn.addEventListener('click', () => {
    if (chatHistory.length === 0) return;
    if (confirm('¿Deseas iniciar una nueva conversación y borrar el historial actual?')) {
      chatHistory = [];
      saveLocalChat();
      renderChatFeed();
      globalStatus.textContent = 'Estado: Listo';
      showToast('🧹 Nueva conversación iniciada.', 'ok');
    }
  });

  // 6. Copiar tabla como Rich Text (Word / Google Docs compatible)
  function tableToTSV(table) {
    const rows = Array.from(table.querySelectorAll('tr'));
    return rows.map(row => {
      const cells = Array.from(row.querySelectorAll('th, td'));
      return cells.map(c => c.innerText.trim().replace(/\n/g, ' ')).join('\t');
    }).join('\n');
  }

  async function copyTableAsRichText(table) {
    const rows = Array.from(table.querySelectorAll('tr'));

    const htmlRows = rows.map(row => {
        const cells = Array.from(row.querySelectorAll('th, td'));
        const htmlCells = cells.map(cell => {
            const isHeader = cell.tagName.toLowerCase() === 'th';
            return `
                <${isHeader ? 'th' : 'td'}
                    style="
                        border: 1px solid #999;
                        padding: 8px;
                        text-align: left;
                        vertical-align: top;
                        background: ${isHeader ? '#eeeeee' : '#ffffff'};
                        color: #000000;
                    "
                >
                    ${cell.innerHTML}
                </${isHeader ? 'th' : 'td'}>
            `;
        }).join('');

        return `<tr>${htmlCells}</tr>`;
    }).join('');

    const html = `
        <table style="
            border-collapse: collapse;
            width: 100%;
            font-family: Arial, sans-serif;
            color: #000000;
            background: #ffffff;
        ">
            ${htmlRows}
        </table>
    `;

    const text = tableToTSV(table);

    try {
        const item = new ClipboardItem({
            'text/html': new Blob([html], { type: 'text/html' }),
            'text/plain': new Blob([text], { type: 'text/plain' })
        });

        await navigator.clipboard.write([item]);
        showToast('📋 Tabla copiada correctamente.', 'ok');

    } catch (error) {
        console.error('Error copiando tabla:', error);
        fallbackCopyText(text);
    }
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