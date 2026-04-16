import { IS_SERVED, REPORT_OPTS_STORAGE_KEY, RPT_METRIC_IDS } from './config.js';
import { openGenerateStream } from './api.js';
import { addReport } from './reports.js';

const GENERATE_BTN_IDLE = `<svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.2" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><polygon points="5 3 19 12 5 21 5 3"/></svg> Generate Report`;

function sleep(ms) { return new Promise((r) => setTimeout(r, ms)); }

function getReportOptions() {
  const metrics = {};
  for (const [key, elId] of Object.entries(RPT_METRIC_IDS)) {
    const cb = document.getElementById(elId);
    metrics[key] = cb ? cb.checked : true;
  }
  return metrics;
}

function buildReportQueryString(filterFilename) {
  const params = new URLSearchParams();
  params.set('filter', filterFilename);
  const opts = getReportOptions();
  for (const [k, v] of Object.entries(opts)) {
    params.set(k, typeof v === 'boolean' ? (v ? '1' : '0') : v);
  }
  return params.toString();
}

function saveReportOptions() {
  try { localStorage.setItem(REPORT_OPTS_STORAGE_KEY, JSON.stringify(getReportOptions())); } catch (_) {}
}

function restoreReportOptions() {
  try {
    const raw = localStorage.getItem(REPORT_OPTS_STORAGE_KEY);
    if (!raw) return;
    const opts = JSON.parse(raw);
    for (const [key, elId] of Object.entries(RPT_METRIC_IDS)) {
      if (key in opts) {
        const cb = document.getElementById(elId);
        if (cb) cb.checked = !!opts[key];
      }
    }
  } catch (_) {}
}

export function initGenerate(mainLog) {
  const btnGenerate          = document.getElementById('btn-generate');
  const errNoMetrics         = document.getElementById('err-no-metrics');
  const generateFilterSelect = document.getElementById('generate-filter-select');
  const errGenerateFilter    = document.getElementById('err-generate-filter');
  if (!btnGenerate || !generateFilterSelect) return;

  function updateGenerateButtonState() {
    const anyChecked = Object.values(RPT_METRIC_IDS).some(
      elId => document.getElementById(elId)?.checked
    );
    if (anyChecked) {
      btnGenerate.disabled = false;
      errNoMetrics.classList.remove('visible');
    } else {
      btnGenerate.disabled = true;
      errNoMetrics.classList.add('visible');
    }
  }

  function resetBtn() {
    btnGenerate.innerHTML = GENERATE_BTN_IDLE;
    updateGenerateButtonState();
  }

  function setBusy() {
    btnGenerate.disabled = true;
    btnGenerate.innerHTML = `<span class="spinner" aria-hidden="true"></span> Generating…`;
  }

  document.getElementById('report-options').addEventListener('change', () => {
    saveReportOptions();
    updateGenerateButtonState();
  });
  restoreReportOptions();
  updateGenerateButtonState();

  generateFilterSelect.addEventListener('change', () => {
    if (generateFilterSelect.value) {
      generateFilterSelect.classList.remove('invalid');
      errGenerateFilter.classList.remove('visible');
    }
  });

  document.getElementById('goto-filter-tab').addEventListener('click', (e) => {
    e.preventDefault();
    const filterTab = document.getElementById('tab-filter');
    if (filterTab) filterTab.click();
  });

  btnGenerate.addEventListener('click', () => {
    if (!generateFilterSelect.value) {
      generateFilterSelect.classList.add('invalid');
      errGenerateFilter.classList.add('visible');
      generateFilterSelect.focus();
      return;
    }
    generateFilterSelect.classList.remove('invalid');
    errGenerateFilter.classList.remove('visible');
    if (!IS_SERVED) {
      runGenerateSimulation(mainLog, generateFilterSelect, setBusy, resetBtn);
    } else {
      runGenerateSSE(mainLog, generateFilterSelect, setBusy, resetBtn);
    }
  });
}

function runGenerateSSE(log, select, setBusy, resetBtn) {
  const filterFilename = select.value;
  const filterName     = select.options[select.selectedIndex]?.text || '';

  setBusy();
  log.clear();
  log.line(`[${new Date().toLocaleTimeString()}] Starting report generation…`, 'log-info');
  if (filterName) log.line(`Filter: ${filterName}`, 'log-muted');

  let lastReportTs = null;
  let lastHtmlFile = null;
  let lastMdFile   = null;
  const evtSource  = openGenerateStream(buildReportQueryString(filterFilename));

  evtSource.onmessage = (e) => {
    const data = e.data;
    const tsMatch = data.match(/generated[\\/]reports[\\/]([\dT:-]+)[\\/]/);
    if (tsMatch) lastReportTs = tsMatch[1];

    if (/reports written/i.test(data)) {
      const htmlMatch = data.match(/([^\/\\,\s]+\.html)/i);
      if (htmlMatch) lastHtmlFile = htmlMatch[1];
      const mdMatch = data.match(/([^\/\\,\s]+\.md)/i);
      if (mdMatch) lastMdFile = mdMatch[1];
    }

    const cls = /error|exception|traceback/i.test(data) ? 'log-error'
              : /done|written|✓/i.test(data)            ? 'log-ok'
              : '';
    log.line(data, cls);
  };

  evtSource.addEventListener('done', () => {
    evtSource.close();
    log.line('✓ Done.', 'log-ok');
    if (lastReportTs) addReport(lastReportTs, lastHtmlFile, lastMdFile);
    resetBtn();
  });

  evtSource.addEventListener('error', (e) => {
    evtSource.close();
    const msg = (e.data || '').replace(/^__error__:/, '');
    if (msg) log.line(msg, 'log-error');
    resetBtn();
  });

  // Server emits `event: close` in its finally block — guaranteed terminal
  // event that re-enables the button even if done/error were missed.
  evtSource.addEventListener('close', () => {
    evtSource.close();
    resetBtn();
  });

  evtSource.onerror = () => {
    if (evtSource.readyState === EventSource.CLOSED) {
      resetBtn();
      return;
    }
    evtSource.close();
    log.line('Connection to server lost. Is server.py still running?', 'log-error');
    resetBtn();
  };
}

async function runGenerateSimulation(log, select, setBusy, resetBtn) {
  const filterName = select.options[select.selectedIndex]?.text || '(none)';
  const filterJql  = select.options[select.selectedIndex]?.dataset?.jql || '';

  const rawSlug = filterName === '(none)' ? ''
    : filterName.toLowerCase().replace(/\s+/g, '_').replace(/[^a-z0-9_\-]/g, '').replace(/^[_\-]+|[_\-]+$/g, '').slice(0, 60);
  const stem = rawSlug ? `ai_adoption_report_${rawSlug}` : 'ai_adoption_report';

  setBusy();
  log.clear();
  log.line('⚠ File:// mode — output is simulated. Run python server.py for live generation.', 'log-error');
  await sleep(200);

  const ts      = new Date().toISOString().slice(0, 19).replace(/:/g, '-');
  const outPath = `generated/reports/${ts}/`;

  log.line(`[${new Date().toLocaleTimeString()}] Starting report generation…`, 'log-info');
  log.line(`Filter: ${filterName}`, 'log-muted');
  if (filterJql) log.line(`JQL: ${filterJql}`, 'log-muted');
  log.line('Reading Jira configuration…', 'log-muted');
  await sleep(420);
  log.line('Connecting to Jira Cloud…', 'log-muted');
  await sleep(600);
  log.line('Fetching board and sprint list…', 'log-muted');
  await sleep(500);
  log.line('Processing sprint data…', 'log-muted');
  await sleep(700);
  log.line('Computing metrics…', 'log-muted');
  await sleep(400);
  log.line(`Rendering HTML report → ${outPath}${stem}.html`, 'log-ok');
  await sleep(200);
  log.line(`Rendering Markdown report → ${outPath}${stem}.md`, 'log-ok');
  await sleep(150);
  log.line(`Done. ✓  Output written to ${outPath}`, 'log-ok');
  addReport(ts, `${stem}.html`, `${stem}.md`);
  resetBtn();
}
