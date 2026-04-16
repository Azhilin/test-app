import { IS_SERVED } from './config.js';
import { getCertStatus, fetchCert } from './api.js';

const FETCH_CERT_BTN_IDLE   = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z"/></svg> Fetch Certificate`;
const REFRESH_CERT_BTN_IDLE = `<svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polyline points="23 4 23 10 17 10"/><path d="M20.49 15a9 9 0 1 1-2.12-9.36L23 10"/></svg> Refresh Certificate`;

function certDetailLine(data) {
  const parts = [data.path];
  if (data.subject)    parts.push(data.subject);
  if (data.expires_at) parts.push(`expires ${data.expires_at}`);
  return parts.join(' \u00b7 ');
}

function updateCertButtonLabel(btn, data) {
  if (!btn.disabled) {
    btn.innerHTML = (data.exists && data.valid) ? REFRESH_CERT_BTN_IDLE : FETCH_CERT_BTN_IDLE;
  }
}

export async function loadCertStatus() {
  const certBadge      = document.getElementById('cert-status-badge');
  const certStatusPath = document.getElementById('cert-status-path');
  const btnFetchCert   = document.getElementById('btn-fetch-cert');

  if (!IS_SERVED) {
    document.getElementById('cert-status-row').hidden       = true;
    document.getElementById('cert-server-controls').hidden  = true;
    document.getElementById('cert-file-mode-note').hidden   = false;
    return;
  }
  try {
    const data = await getCertStatus();
    ['badge-neutral', 'badge-success', 'badge-warning', 'badge-error'].forEach((c) => certBadge.classList.remove(c));
    if (!data.exists) {
      certBadge.classList.add('badge-neutral');
      certBadge.textContent      = 'No certificate';
      certStatusPath.textContent = '';
    } else if (data.error) {
      certBadge.classList.add('badge-error');
      certBadge.textContent      = 'Certificate unreadable';
      certStatusPath.textContent = data.path || '';
    } else if (!data.valid) {
      certBadge.classList.add('badge-error');
      certBadge.textContent      = 'Certificate expired';
      certStatusPath.textContent = certDetailLine(data);
    } else if (data.days_remaining <= 7) {
      certBadge.classList.add('badge-warning');
      certBadge.textContent      = `Expiring soon \u00b7 ${data.days_remaining}d`;
      certStatusPath.textContent = certDetailLine(data);
    } else {
      certBadge.classList.add('badge-success');
      certBadge.textContent      = 'Valid';
      certStatusPath.textContent = certDetailLine(data);
    }
    updateCertButtonLabel(btnFetchCert, data);
  } catch {
    certBadge.textContent = 'Status unknown';
  }
}

export function initCert(certLog) {
  const btnFetchCert = document.getElementById('btn-fetch-cert');
  if (!btnFetchCert) return;

  btnFetchCert.addEventListener('click', async () => {
    const url = document.getElementById('jira-url').value.trim();
    if (!url) {
      certLog.line('\u26A0 Enter the Jira URL in the fields above before fetching the certificate.', 'log-error');
      return;
    }
    btnFetchCert.disabled  = true;
    btnFetchCert.innerHTML = '<span class="spinner" aria-hidden="true"></span> Fetching\u2026';
    certLog.clear();
    certLog.line(`[ ${new Date().toLocaleTimeString()} ] Connecting to ${url} \u2026`, 'log-info');
    try {
      const data = await fetchCert(url);
      if (data.ok) {
        certLog.line(`\u2713 Certificate saved \u2192 ${data.path}`, 'log-ok');
      } else {
        certLog.line(`\u2717 ${data.error || 'Unknown error'}`, 'log-error');
      }
    } catch (err) {
      certLog.line(`\u2717 Request failed: ${err.message}`, 'log-error');
    } finally {
      btnFetchCert.disabled = false;
      await loadCertStatus();
    }
  });
}
