/**
 * AgentDesk Frontend
 * Talks to the FastAPI backend at http://localhost:8000
 */

const API = 'http://localhost:8000/api/v1';

// ── State ──────────────────────────────────────────────
let state = {
  apiKey: null,
  userId: null,
  displayName: null,
  conversations: [],
  activeConvId: null,
  streaming: false,
};

// ── Persistence ────────────────────────────────────────
function saveSession() {
  localStorage.setItem('agentdesk_session', JSON.stringify({
    apiKey: state.apiKey,
    userId: state.userId,
    displayName: state.displayName,
  }));
}

function loadSession() {
  try {
    const raw = localStorage.getItem('agentdesk_session');
    if (!raw) return false;
    const s = JSON.parse(raw);
    if (!s.apiKey) return false;
    state.apiKey = s.apiKey;
    state.userId = s.userId;
    state.displayName = s.displayName || 'User';
    return true;
  } catch { return false; }
}

// ── API helpers ────────────────────────────────────────
async function apiFetch(path, options = {}) {
  const headers = {
    'Content-Type': 'application/json',
    ...(state.apiKey ? { 'X-API-Key': state.apiKey } : {}),
    ...(options.headers || {}),
  };
  const res = await fetch(`${API}${path}`, { ...options, headers });
  if (!res.ok) {
    const err = await res.json().catch(() => ({ detail: res.statusText }));
    throw new Error(err.detail || 'Request failed');
  }
  if (res.status === 204) return null;
  return res.json();
}

// ── Toast ──────────────────────────────────────────────
let toastTimer = null;
function toast(msg, type = '') {
  const el = document.getElementById('toast');
  el.textContent = msg;
  el.className = `toast ${type}`;
  el.classList.remove('hidden');
  clearTimeout(toastTimer);
  toastTimer = setTimeout(() => el.classList.add('hidden'), 3500);
}

// ── Registration & Login ───────────────────────────────
async function registerUser() {
  const name = document.getElementById('display-name').value.trim();
  if (!name) { toast('Please enter your name.', 'error'); return; }

  const btn = document.getElementById('register-btn');
  setLoading(btn, true);

  try {
    const data = await apiFetch('/auth/register', {
      method: 'POST',
      body: JSON.stringify({ display_name: name }),
    });
    state.apiKey = data.api_key;
    state.userId = data.user_id;
    state.displayName = name;
    saveSession();

    document.getElementById('api-key-display').textContent = data.api_key;
    document.getElementById('register-section').classList.add('hidden');
    document.getElementById('key-section').classList.remove('hidden');
    toast('Account created! Save your API key.', 'success');
  } catch (e) {
    toast(e.message, 'error');
  } finally {
    setLoading(btn, false);
  }
}

function copyKey() {
  const key = document.getElementById('api-key-display').textContent;
  navigator.clipboard.writeText(key).then(() => toast('API key copied!', 'success'));
}

function enterApp() {
  document.getElementById('register-overlay').classList.add('hidden');
  document.getElementById('app').classList.remove('hidden');
  document.getElementById('sidebar-username').textContent = state.displayName || 'User';
  loadConversations();
}

async function loginWithKey() {
  const key = document.getElementById('existing-key').value.trim();
  if (!key) { toast('Please enter your API key.', 'error'); return; }
  state.apiKey = key;

  // Validate by calling a protected endpoint
  try {
    const data = await apiFetch('/conversations');
    // If we get here, the key is valid
    state.displayName = 'User';
    state.userId = null;
    saveSession();
    document.getElementById('register-overlay').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    document.getElementById('sidebar-username').textContent = 'User';
    loadConversations();
    toast('Signed in successfully.', 'success');
  } catch (e) {
    state.apiKey = null;
    toast('Invalid API key.', 'error');
  }
}

function logout() {
  localStorage.removeItem('agentdesk_session');
  location.reload();
}

// ── Loading helper ─────────────────────────────────────
function setLoading(btn, loading) {
  const text = btn.querySelector('.btn-text');
  const spinner = btn.querySelector('.btn-spinner');
  btn.disabled = loading;
  if (text) text.classList.toggle('hidden', loading);
  if (spinner) spinner.classList.toggle('hidden', !loading);
}

// ── Conversations ──────────────────────────────────────
async function loadConversations() {
  try {
    const data = await apiFetch('/conversations');
    state.conversations = data.items || [];
    renderConversationList();
  } catch (e) {
    console.error('Failed to load conversations', e);
  }
}

function renderConversationList() {
  const container = document.getElementById('conversations-list');
  if (!state.conversations.length) {
    container.innerHTML = '<div class="empty-state-small">No conversations yet</div>';
    return;
  }
  container.innerHTML = state.conversations.map(conv => `
    <div class="conv-item ${conv.id === state.activeConvId ? 'active' : ''}"
         id="conv-${conv.id}"
         onclick="selectConversation('${conv.id}', ${JSON.stringify(conv.title).replace(/"/g, '&quot;')})">
      <span class="conv-item-icon">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M21 15a2 2 0 01-2 2H7l-4 4V5a2 2 0 012-2h14a2 2 0 012 2z"/>
        </svg>
      </span>
      <span class="conv-item-title">${escHtml(conv.title)}</span>
      <button class="conv-item-delete" title="Delete" onclick="deleteConversation(event,'${conv.id}')">
        <svg width="13" height="13" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <polyline points="3 6 5 6 21 6"/><path d="M19 6v14a2 2 0 01-2 2H7a2 2 0 01-2-2V6m3 0V4a1 1 0 011-1h4a1 1 0 011 1v2"/>
        </svg>
      </button>
    </div>
  `).join('');
}

async function createConversation() {
  try {
    const conv = await apiFetch('/conversations', {
      method: 'POST',
      body: JSON.stringify({ title: 'New Conversation' }),
    });
    state.conversations.unshift(conv);
    renderConversationList();
    selectConversation(conv.id, conv.title);
  } catch (e) {
    toast(e.message, 'error');
  }
}

async function selectConversation(convId, title) {
  state.activeConvId = convId;
  renderConversationList();

  // Switch to message view
  document.getElementById('welcome-screen').classList.add('hidden');
  document.getElementById('chat-messages').classList.remove('hidden');
  document.getElementById('messages-container').innerHTML = '';
  hideToolPanel();

  const pill = document.getElementById('active-conversation-title');
  pill.textContent = title;
  pill.classList.add('visible');

  // Load messages
  try {
    const data = await apiFetch(`/conversations/${convId}/messages`);
    const msgs = data.items || [];
    msgs.forEach(m => renderMessage(m.role, m.content, m.tool_name, m.tool_output));
    scrollToBottom();
  } catch (e) {
    toast('Failed to load messages.', 'error');
  }
}

async function deleteConversation(evt, convId) {
  evt.stopPropagation();
  try {
    await apiFetch(`/conversations/${convId}`, { method: 'DELETE' });
    state.conversations = state.conversations.filter(c => c.id !== convId);
    if (state.activeConvId === convId) {
      state.activeConvId = null;
      document.getElementById('welcome-screen').classList.remove('hidden');
      document.getElementById('chat-messages').classList.add('hidden');
      document.getElementById('active-conversation-title').classList.remove('visible');
      hideToolPanel();
    }
    renderConversationList();
    toast('Conversation deleted.');
  } catch (e) {
    toast(e.message, 'error');
  }
}

// ── Messaging ──────────────────────────────────────────
async function sendMessage() {
  if (state.streaming) return;

  const input = document.getElementById('message-input');
  const content = input.value.trim();
  if (!content) return;

  if (!state.activeConvId) {
    // Auto-create conversation
    try {
      const title = content.length > 40 ? content.slice(0, 40) + '…' : content;
      const conv = await apiFetch('/conversations', {
        method: 'POST',
        body: JSON.stringify({ title }),
      });
      state.conversations.unshift(conv);
      state.activeConvId = conv.id;
      renderConversationList();

      document.getElementById('welcome-screen').classList.add('hidden');
      document.getElementById('chat-messages').classList.remove('hidden');
      const pill = document.getElementById('active-conversation-title');
      pill.textContent = conv.title;
      pill.classList.add('visible');
    } catch (e) {
      toast(e.message, 'error');
      return;
    }
  }

  input.value = '';
  autoResize(input);

  // Render user message immediately
  renderMessage('user', content);
  scrollToBottom();

  state.streaming = true;
  document.getElementById('send-btn').disabled = true;

  // Show typing indicator
  const typingId = addTypingIndicator();
  clearToolPanel();
  showToolPanel();

  try {
    const res = await fetch(`${API}/conversations/${state.activeConvId}/messages`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'X-API-Key': state.apiKey,
        'Accept': 'text/event-stream',
      },
      body: JSON.stringify({ content }),
    });

    if (!res.ok) {
      const err = await res.json().catch(() => ({ detail: res.statusText }));
      throw new Error(err.detail || 'Send failed');
    }

    // Remove typing indicator, add streaming message
    removeElement(typingId);
    const msgEl = addStreamingMessage();

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });

      // Parse SSE events
      const lines = buffer.split('\n');
      buffer = lines.pop(); // keep incomplete line

      let eventType = '';
      for (const line of lines) {
        if (line.startsWith('event: ')) {
          eventType = line.slice(7).trim();
        } else if (line.startsWith('data: ')) {
          const data = JSON.parse(line.slice(6));
          handleSSEEvent(eventType, data, msgEl);
        }
      }
    }

    // Finalize streaming message
    finalizeStreamingMessage(msgEl);
    hideToolPanel();
    scrollToBottom();

    // Refresh conversation title
    await loadConversations();

  } catch (e) {
    removeElement(typingId);
    hideToolPanel();
    renderMessage('assistant', `⚠️ Error: ${e.message}`);
    toast(e.message, 'error');
  } finally {
    state.streaming = false;
    document.getElementById('send-btn').disabled = false;
    scrollToBottom();
  }
}

function handleSSEEvent(event, data, msgEl) {
  switch (event) {
    case 'token':
      appendToStreamingMessage(msgEl, data.delta || '');
      scrollToBottom();
      break;
    case 'tool_call':
      addToolEvent('call', data.name, data.input);
      break;
    case 'tool_result':
      addToolEvent('result', data.name, data.output);
      break;
    case 'error':
      appendToStreamingMessage(msgEl, `⚠️ ${data.message || 'Unknown error'}`);
      break;
    case 'done':
      // stream complete
      break;
  }
}

// ── Message rendering ──────────────────────────────────
function renderMessage(role, content, toolName = null, toolOutput = null) {
  const container = document.getElementById('messages-container');

  if (role === 'tool') {
    const el = document.createElement('div');
    el.className = 'message tool-msg';
    el.innerHTML = `
      <div class="msg-avatar tool-av">
        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3-3a1 1 0 000-1.4l-1.6-1.6a1 1 0 00-1.4 0l-3 3zM14 10l-7 7H3v-4l7-7"/></svg>
      </div>
      <div class="msg-body">
        <div class="msg-role">${escHtml(toolName || 'tool')}</div>
        <div class="msg-content">${escHtml(JSON.stringify(toolOutput || content, null, 2))}</div>
      </div>`;
    container.appendChild(el);
    return;
  }

  const isUser = role === 'user';
  const el = document.createElement('div');
  el.className = `message ${isUser ? 'user' : 'assistant'}`;
  el.innerHTML = `
    <div class="msg-avatar ${isUser ? 'user-av' : 'ai-av'}">
      ${isUser
        ? `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><circle cx="12" cy="8" r="4"/><path d="M20 21a8 8 0 00-16 0"/></svg>`
        : `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>`
      }
    </div>
    <div class="msg-body">
      <div class="msg-role">${isUser ? 'You' : 'AgentDesk'}</div>
      <div class="msg-content">${escHtml(content)}</div>
    </div>`;
  container.appendChild(el);
}

let streamMsgCounter = 0;
function addStreamingMessage() {
  const container = document.getElementById('messages-container');
  const id = `stream-msg-${++streamMsgCounter}`;
  const el = document.createElement('div');
  el.className = 'message assistant';
  el.id = id;
  el.innerHTML = `
    <div class="msg-avatar ai-av">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
    </div>
    <div class="msg-body">
      <div class="msg-role">AgentDesk</div>
      <div class="msg-content streaming" id="${id}-content"></div>
    </div>`;
  container.appendChild(el);
  return id;
}

function appendToStreamingMessage(id, delta) {
  const el = document.getElementById(`${id}-content`);
  if (el) el.textContent += delta;
}

function finalizeStreamingMessage(id) {
  const el = document.getElementById(`${id}-content`);
  if (el) el.classList.remove('streaming');
}

// ── Typing indicator ───────────────────────────────────
let typingCounter = 0;
function addTypingIndicator() {
  const container = document.getElementById('messages-container');
  const id = `typing-${++typingCounter}`;
  const el = document.createElement('div');
  el.className = 'message assistant typing-indicator';
  el.id = id;
  el.innerHTML = `
    <div class="msg-avatar ai-av">
      <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><rect x="3" y="11" width="18" height="11" rx="2"/><path d="M7 11V7a5 5 0 0110 0v4"/></svg>
    </div>
    <div class="typing-dots"><span></span><span></span><span></span></div>`;
  container.appendChild(el);
  scrollToBottom();
  return id;
}

// ── Tool panel ─────────────────────────────────────────
function showToolPanel() {
  document.getElementById('tool-panel').classList.remove('hidden');
}
function hideToolPanel() {
  document.getElementById('tool-panel').classList.add('hidden');
}
function clearToolPanel() {
  document.getElementById('tool-panel-content').innerHTML = '';
}

function addToolEvent(type, name, data) {
  const panel = document.getElementById('tool-panel-content');
  const el = document.createElement('div');
  el.className = `tool-event ${type}`;
  const icon = type === 'call'
    ? `<svg class="tool-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><path d="M14.7 6.3a1 1 0 000 1.4l1.6 1.6a1 1 0 001.4 0l3-3a1 1 0 000-1.4l-1.6-1.6a1 1 0 00-1.4 0l-3 3zM14 10l-7 7H3v-4l7-7"/></svg>`
    : `<svg class="tool-icon" width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="20 6 9 17 4 12"/></svg>`;
  const label = type === 'call'
    ? `Calling <strong>${escHtml(name)}</strong>`
    : `<strong>${escHtml(name)}</strong> returned`;
  el.innerHTML = `${icon}<span>${label}</span>`;
  panel.appendChild(el);
}

// ── Utilities ──────────────────────────────────────────
function removeElement(id) {
  const el = document.getElementById(id);
  if (el) el.remove();
}

function scrollToBottom() {
  const msgs = document.getElementById('chat-messages');
  if (msgs) msgs.scrollTop = msgs.scrollHeight;
}

function autoResize(el) {
  el.style.height = 'auto';
  el.style.height = Math.min(el.scrollHeight, 200) + 'px';
}

function handleKeyDown(e) {
  if (e.key === 'Enter' && !e.shiftKey) {
    e.preventDefault();
    sendMessage();
  }
}

function escHtml(str) {
  if (str === null || str === undefined) return '';
  return String(str)
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');
}

function quickPrompt(text) {
  // Auto-create conversation and send
  document.getElementById('message-input').value = text;
  sendMessage();
}

// ── Init ───────────────────────────────────────────────
(function init() {
  if (loadSession()) {
    document.getElementById('register-overlay').classList.add('hidden');
    document.getElementById('app').classList.remove('hidden');
    document.getElementById('sidebar-username').textContent = state.displayName || 'User';
    loadConversations();
  }
})();
