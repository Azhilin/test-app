import { initTabs } from './tabs.js';
import { createLogStream } from './log-stream.js';
import { initConnection } from './connection.js';
import { initCert } from './cert.js';
import { initFilters } from './filters.js';
import { initJqlBuilderVisibility } from './jql-builder.js';
import { initSchema } from './schema.js';
import { initGenerate } from './generate.js';
import { initFilterOptions } from './filter-options.js';
import { initSaveHandlers } from './save-handlers.js';
import { showFileModeBannerIfNeeded } from './file-mode-banner.js';
import { restoreValues } from './restore.js';

try {
  const { activate: activateTab } = initTabs();

  const mainLog = createLogStream(
    document.getElementById('log-output'),
    document.getElementById('btn-clear-log'),
  );
  const filterLog = createLogStream(
    document.getElementById('filter-log-output'),
    document.getElementById('btn-clear-filter-log'),
  );
  const certLog = createLogStream(
    document.getElementById('cert-log-output'),
    document.getElementById('btn-clear-cert-log'),
  );

  initConnection();
  initCert(certLog);
  initFilters(filterLog);
  const syncJqlBuilderVisibility = initJqlBuilderVisibility();
  initSchema();
  initGenerate(mainLog);
  initFilterOptions();
  initSaveHandlers();
  showFileModeBannerIfNeeded();

  window.restoreValuesReady = false;
  restoreValues(activateTab)
    .then(() => { window.restoreValuesReady = true; syncJqlBuilderVisibility(); })
    .catch((err) => { console.error('restoreValues error:', err); window.restoreValuesReady = true; });
} catch (err) {
  console.error('Script initialization error:', err);
}
