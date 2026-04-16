export function initTabs() {
  const tabs   = Array.from(document.querySelectorAll('[role="tab"]'));
  const panels = Array.from(document.querySelectorAll('[role="tabpanel"]'));

  function activate(tab) {
    tabs.forEach((t) => {
      const active = t === tab;
      t.setAttribute('aria-selected', String(active));
      t.tabIndex = active ? 0 : -1;
    });
    panels.forEach((p) => {
      p.hidden = p.id !== tab.getAttribute('aria-controls');
    });
    tab.focus();
  }

  tabs.forEach((tab) => {
    tab.addEventListener('click', () => activate(tab));
    tab.addEventListener('keydown', (e) => {
      let idx = tabs.indexOf(e.currentTarget);
      if (e.key === 'ArrowRight') { idx = (idx + 1) % tabs.length; activate(tabs[idx]); }
      else if (e.key === 'ArrowLeft') { idx = (idx - 1 + tabs.length) % tabs.length; activate(tabs[idx]); }
      else if (e.key === 'Home') { activate(tabs[0]); }
      else if (e.key === 'End')  { activate(tabs[tabs.length - 1]); }
    });
  });

  return { tabs, panels, activate };
}
