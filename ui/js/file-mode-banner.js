import { IS_SERVED } from './config.js';

export function showFileModeBannerIfNeeded() {
  if (IS_SERVED) return;
  const banner = document.createElement('div');
  banner.setAttribute('role', 'alert');
  banner.style.cssText = [
    'max-width:860px', 'margin:10px auto 0', 'padding:10px 16px',
    'background:#FFFAE6', 'border:1px solid #FFE380', 'border-radius:6px',
    'font-size:0.82rem', 'color:#172B4D', 'line-height:1.6',
    "font-family:-apple-system,BlinkMacSystemFont,'Segoe UI',sans-serif",
  ].join(';');
  banner.innerHTML = '<strong>&#x26A0; Running in file:// mode.</strong> '
    + 'Test Connection and live report generation require the local server. '
    + 'Run <code style="background:#EEE;padding:1px 5px;border-radius:3px">python server.py</code> '
    + 'then open <a href="http://localhost:8080" style="color:#0052CC">http://localhost:8080</a>.';
  document.body.insertBefore(banner, document.body.firstChild);
}
