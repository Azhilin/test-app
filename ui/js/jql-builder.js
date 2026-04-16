import { getActiveTeamJqlName } from './schema.js';

export function buildJqlLocally(params) {
  const rawProject = (params.JIRA_PROJECT || '').trim();
  const projects   = rawProject.split(',').map((p) => p.trim()).filter(Boolean);
  if (!projects.length) return '';

  const jqlQuote = (v) => {
    if ((v.startsWith('"') && v.endsWith('"')) || (v.startsWith("'") && v.endsWith("'"))) return v;
    if (/[ (),=<>]/.test(v)) return `"${v}"`;
    return v;
  };

  const clauses = projects.length === 1
    ? [`project = ${projects[0]}`]
    : [`project IN (${projects.join(', ')})`];

  const rawTeamId = (params.JIRA_TEAM_ID || '').trim();
  const teamIds   = rawTeamId.split(',').map((t) => t.trim()).filter(Boolean);
  if (teamIds.length) {
    const quoted = teamIds.map(jqlQuote);
    const teamField = getActiveTeamJqlName();
    const teamJql = `"${teamField}"`;
    clauses.push(quoted.length === 1
      ? `${teamJql} = ${quoted[0]}`
      : `${teamJql} IN (${quoted.join(', ')})`);
  }

  clauses.push('status = Done');

  const rawTypes = (params.JIRA_ISSUE_TYPES || '').trim();
  const types    = rawTypes.split(',').map((t) => t.trim()).filter(Boolean);
  if (types.length) clauses.push(`type IN (${types.map(jqlQuote).join(', ')})`);

  const closedOnly = (params.JIRA_CLOSED_SPRINTS_ONLY || 'true').trim().toLowerCase();
  if (['1', 'true', 'yes', 'on'].includes(closedOnly)) clauses.push('sprint in closedSprints()');

  return clauses.join(' AND ');
}

export function initJqlBuilderVisibility() {
  const filterIdInput = document.getElementById('filter-id');
  const jqlBuilderEl  = document.getElementById('filter-jql-builder');
  if (!filterIdInput || !jqlBuilderEl) return () => {};

  function sync() {
    const hasFilterId = filterIdInput.value.trim() !== '';
    jqlBuilderEl.hidden = hasFilterId;
    if (hasFilterId) { jqlBuilderEl.open = false; }
  }
  filterIdInput.addEventListener('input', sync);
  return sync;
}
