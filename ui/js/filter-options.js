import { FILTER_OPTS_STORAGE_KEY } from './config.js';

function saveFilterOptions() {
  try {
    const pt = document.querySelector('input[name="filter-project-type"]:checked')?.value || 'SCRUM';
    const et = document.querySelector('input[name="filter-estimation-type"]:checked')?.value || 'StoryPoints';
    localStorage.setItem(FILTER_OPTS_STORAGE_KEY, JSON.stringify({ projectType: pt, estimationType: et }));
  } catch (_) {}
}

function restoreFilterOptions() {
  try {
    const raw = localStorage.getItem(FILTER_OPTS_STORAGE_KEY);
    if (!raw) return;
    const opts = JSON.parse(raw);
    if (opts.projectType) {
      const r = document.querySelector(`input[name="filter-project-type"][value="${opts.projectType}"]`);
      if (r) r.checked = true;
    }
    if (opts.estimationType) {
      const r = document.querySelector(`input[name="filter-estimation-type"][value="${opts.estimationType}"]`);
      if (r) r.checked = true;
    }
  } catch (_) {}
}

export function initFilterOptions() {
  document.querySelectorAll('input[name="filter-project-type"], input[name="filter-estimation-type"]').forEach(r => {
    r.addEventListener('change', saveFilterOptions);
  });
  restoreFilterOptions();
}
