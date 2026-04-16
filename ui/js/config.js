export const IS_SERVED = location.protocol !== 'file:';

export const STORE_KEYS = {
  JIRA_URL:                  'jira_url',
  JIRA_EMAIL:                'jira_email',
  JIRA_API_TOKEN:            'jira_api_token',
  JIRA_BOARD_ID:             'jira_board_id',
  JIRA_FILTER_ID:            'jira_filter_id',
  JIRA_SPRINT_COUNT:         'jira_sprint_count',
  JIRA_PROJECT:              'jira_project',
  JIRA_TEAM_ID:              'jira_team_id',
  JIRA_ISSUE_TYPES:          'jira_issue_types',
  JIRA_CLOSED_SPRINTS_ONLY:  'jira_closed_sprints_only',
  JIRA_FILTER_PAGE_SIZE:     'jira_filter_page_size',
  AI_ASSISTED_LABEL:         'ai_assisted_label',
  AI_EXCLUDE_LABELS:         'ai_exclude_labels',
  AI_TOOL_LABELS:            'ai_tool_labels',
  AI_ACTION_LABELS:          'ai_action_labels',
  REPORTS:                   'jira_reports_list',
  FILTERS:                   'jira_saved_filters',
  JIRA_SCHEMA:               'jira_schema_name',
};

export const FIELD_DEFAULTS = {
  JIRA_SPRINT_COUNT:        '10',
  JIRA_CLOSED_SPRINTS_ONLY: 'true',
  JIRA_FILTER_PAGE_SIZE:    '100',
  AI_ASSISTED_LABEL:        'AI_assistance',
  AI_TOOL_LABELS:           'AI_Tool_Copilot,AI_Tool_ChatGPT,AI_Tool_Gemini',
  AI_ACTION_LABELS:         'AI_Case_CodeGen,AI_Case_Review,AI_Case_Testing',
};

export const REPORT_OPTS_STORAGE_KEY = 'report-options';
export const FILTER_OPTS_STORAGE_KEY = 'filter-options';

export const RPT_METRIC_IDS = {
  METRIC_VELOCITY:            'rpt-metric-velocity',
  METRIC_AI_ASSISTANCE_TREND: 'rpt-metric-ai-trend',
  METRIC_AI_USAGE_DETAILS:    'rpt-metric-ai-usage',
  METRIC_DAU:                 'rpt-metric-dau',
  METRIC_DAU_TREND:           'rpt-metric-dau-trend',
};
