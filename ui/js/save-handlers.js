import { IS_SERVED, STORE_KEYS } from './config.js';
import { store } from './store.js';
import { saveConfig } from './api.js';
import { flashConfirm } from './connection.js';

export function initSaveHandlers() {
  const btnSaveAi = document.getElementById('btn-save-ai-labels');
  if (btnSaveAi) {
    btnSaveAi.addEventListener('click', () => {
      const aiAssisted = document.getElementById('ai-assisted-label').value.trim();
      const aiExclude  = document.getElementById('ai-exclude-labels').value.trim();
      const aiTools    = document.getElementById('ai-tool-labels').value.trim();
      const aiActions  = document.getElementById('ai-action-labels').value.trim();
      store.set(STORE_KEYS.AI_ASSISTED_LABEL, aiAssisted);
      store.set(STORE_KEYS.AI_EXCLUDE_LABELS, aiExclude);
      store.set(STORE_KEYS.AI_TOOL_LABELS,    aiTools);
      store.set(STORE_KEYS.AI_ACTION_LABELS,  aiActions);
      flashConfirm('save-confirm-ai');
      if (IS_SERVED) {
        saveConfig({
          AI_ASSISTED_LABEL: aiAssisted,
          AI_EXCLUDE_LABELS: aiExclude,
          AI_TOOL_LABELS:    aiTools,
          AI_ACTION_LABELS:  aiActions,
        });
      }
    });
  }
}
