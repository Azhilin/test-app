export function createLogStream(logEl, clearBtn) {
  function line(text, cls = '') {
    if (!logEl) return;
    const span = document.createElement('span');
    if (cls) span.className = cls;
    span.textContent = text;
    logEl.appendChild(span);
    logEl.appendChild(document.createTextNode('\n'));
    logEl.scrollTop = logEl.scrollHeight;
  }

  function clear() {
    if (logEl) logEl.innerHTML = '';
  }

  if (clearBtn) clearBtn.addEventListener('click', clear);

  return { el: logEl, line, clear };
}
