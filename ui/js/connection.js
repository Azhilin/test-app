import { IS_SERVED, STORE_KEYS } from './config.js';
import { store } from './store.js';
import { saveConfig, testConnection } from './api.js';

const BADGE_CLASSES = ['badge-neutral', 'badge-success', 'badge-error', 'badge-testing'];
const BADGE_LABELS = {
  neutral: 'Not configured',
  success: 'Connected',
  error:   'Error',
  testing: 'Testing…',
};

// Shared module state
export const state = {
  hasServerToken: false,
  connectedOk:    false,
};

const flashTimers = {};
export function flashConfirm(id) {
  const el = document.getElementById(id);
  if (!el) return;
  el.classList.add('visible');
  clearTimeout(flashTimers[id]);
  flashTimers[id] = setTimeout(() => el.classList.remove('visible'), 2500);
}

export function setStatus(stateName, detail = '') {
  const badge = document.getElementById('conn-status-badge');
  const badgeDetail = document.getElementById('conn-status-detail');
  if (!badge) return;
  BADGE_CLASSES.forEach((c) => badge.classList.remove(c));
  badge.classList.add(
    stateName === 'success' ? 'badge-success'
    : stateName === 'error'   ? 'badge-error'
    : stateName === 'testing' ? 'badge-testing'
    : 'badge-neutral'
  );
  badge.textContent = BADGE_LABELS[stateName] ?? stateName;
  badgeDetail.textContent = detail;
  badgeDetail.style.color = stateName === 'error' ? 'var(--error)' : stateName === 'success' ? 'var(--success)' : 'var(--text-muted)';
}

function allConnFieldsFilled() {
  const jiraUrlInput   = document.getElementById('jira-url');
  const jiraEmailInput = document.getElementById('jira-email');
  const jiraTokenInput = document.getElementById('jira-token');
  return !!(
    jiraUrlInput.value.trim() &&
    jiraEmailInput.value.trim() &&
    (jiraTokenInput.value || state.hasServerToken)
  );
}

export function updateSaveBtn() {
  const btn = document.getElementById('btn-save-conn');
  if (btn) btn.disabled = !(state.connectedOk && allConnFieldsFilled());
}

export function updateBadgeFromSaved() {
  const url   = store.get(STORE_KEYS.JIRA_URL);
  const email = store.get(STORE_KEYS.JIRA_EMAIL);
  const token = store.get(STORE_KEYS.JIRA_API_TOKEN);
  const badge = document.getElementById('conn-status-badge');
  if (!url || !email || (!token && !state.hasServerToken)) {
    setStatus('neutral', 'Enter your Jira URL, email, and API token to get started.');
  } else {
    setStatus('neutral', 'Credentials saved. Click "Test Connection" to verify.');
    if (badge) badge.textContent = 'Configured';
  }
}

export function validateConnFields() {
  const jiraUrlInput   = document.getElementById('jira-url');
  const jiraEmailInput = document.getElementById('jira-email');
  const jiraTokenInput = document.getElementById('jira-token');
  let ok = true;

  const urlVal = jiraUrlInput.value.trim();
  const urlErr = document.getElementById('err-jira-url');
  if (!urlVal || !/^https?:\/\/.+/.test(urlVal)) {
    jiraUrlInput.classList.add('invalid');
    urlErr.classList.add('visible');
    ok = false;
  } else {
    jiraUrlInput.classList.remove('invalid');
    urlErr.classList.remove('visible');
  }

  const emailVal = jiraEmailInput.value.trim();
  const emailErr = document.getElementById('err-jira-email');
  if (!emailVal || !/^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(emailVal)) {
    jiraEmailInput.classList.add('invalid');
    emailErr.classList.add('visible');
    ok = false;
  } else {
    jiraEmailInput.classList.remove('invalid');
    emailErr.classList.remove('visible');
  }

  const tokenVal = jiraTokenInput.value;
  const tokenErr = document.getElementById('err-jira-token');
  if (!tokenVal && !state.hasServerToken) {
    jiraTokenInput.classList.add('invalid');
    tokenErr.classList.add('visible');
    ok = false;
  } else {
    jiraTokenInput.classList.remove('invalid');
    tokenErr.classList.remove('visible');
  }

  return ok;
}

export function initConnection() {
  const jiraUrlInput   = document.getElementById('jira-url');
  const jiraEmailInput = document.getElementById('jira-email');
  const jiraTokenInput = document.getElementById('jira-token');
  const btnSaveConn    = document.getElementById('btn-save-conn');
  const btnTestConn    = document.getElementById('btn-test-conn');
  const btnToggleToken = document.getElementById('btn-toggle-token');

  if (btnSaveConn) {
    btnSaveConn.addEventListener('click', () => {
      if (!validateConnFields()) return;
      const url   = jiraUrlInput.value.trim().replace(/\/+$/, '');
      const email = jiraEmailInput.value.trim();
      const token = jiraTokenInput.value;
      store.set(STORE_KEYS.JIRA_URL,       url);
      store.set(STORE_KEYS.JIRA_EMAIL,     email);
      store.set(STORE_KEYS.JIRA_API_TOKEN, token);
      updateBadgeFromSaved();
      flashConfirm('save-confirm-conn');
      if (IS_SERVED) {
        saveConfig({
          JIRA_URL:       url,
          JIRA_EMAIL:     email,
          JIRA_API_TOKEN: token || (state.hasServerToken ? '***' : ''),
        });
      }
    });
  }

  if (btnTestConn) {
    btnTestConn.addEventListener('click', async () => {
      const url   = jiraUrlInput.value.trim();
      const email = jiraEmailInput.value.trim();
      const token = jiraTokenInput.value;

      if (!url || !email || (!token && !state.hasServerToken)) {
        setStatus('error', 'Fill in URL, email, and token before testing.');
        return;
      }

      if (!IS_SERVED) {
        setStatus('error', 'Cannot test from file:// — run python server.py then open http://localhost:8080');
        return;
      }

      setStatus('testing', 'Testing connection…');

      try {
        const { status, data } = await testConnection({
          url,
          email,
          token: token || (state.hasServerToken ? '***' : ''),
        });

        if (data && data.ok) {
          state.connectedOk = true;
          setStatus('success', `Connected as ${data.displayName || data.emailAddress || email}`);
        } else if (data && data.httpStatus === 401) {
          state.connectedOk = false;
          setStatus('error', 'Authentication failed — check your email and API token.');
        } else if (data && data.httpStatus === 403) {
          state.connectedOk = false;
          setStatus('error', 'Access denied (HTTP 403). Verify your account permissions.');
        } else {
          state.connectedOk = false;
          setStatus('error', (data && data.error) || `HTTP error ${(data && data.httpStatus) ?? status}`);
        }
        updateSaveBtn();
      } catch (err) {
        state.connectedOk = false;
        updateSaveBtn();
        setStatus('error', `Request failed: ${err.message}`);
      }
    });
  }

  if (btnToggleToken) {
    const iconEye    = document.getElementById('icon-eye');
    const iconEyeOff = document.getElementById('icon-eye-off');
    btnToggleToken.addEventListener('click', () => {
      const isPassword = jiraTokenInput.type === 'password';
      jiraTokenInput.type = isPassword ? 'text' : 'password';
      iconEye.style.display    = isPassword ? 'none' : '';
      iconEyeOff.style.display = isPassword ? ''    : 'none';
      btnToggleToken.setAttribute('aria-label', isPassword ? 'Hide API token' : 'Show API token');
    });
  }

  [jiraUrlInput, jiraEmailInput, jiraTokenInput].forEach((input) => {
    input.addEventListener('blur', () => {
      if (input.classList.contains('invalid')) validateConnFields();
    });
    input.addEventListener('input', () => {
      state.connectedOk = false;
      updateSaveBtn();
      if (input.classList.contains('invalid')) validateConnFields();
    });
  });
}
