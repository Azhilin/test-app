---
name: dau-survey
description: Use when working on the DAU survey page (ui/dau_survey.html), DAU response JSON files, or compute_dau_metrics(). Guides work across the client-side UI, JSON schema, and metrics computation without loading unrelated repo context.
---

Use this skill for DAU survey UI or DAU metrics computation changes.

**1. Open the smallest relevant context:**

- `ui/dau_survey.html` — client-side survey page
- `app/core/metrics.py` (`compute_dau_metrics` function and `_DAU_SCORE_MAP`)
- `app/core/config.py` (`DAU_RESPONSES_DIR` constant)
- `tests/unit/` (files matching `test_dau*`)

**2. Understand the File System Access API pattern:**

- Saves `dau_<username>_<timestamp>.json` directly to the local filesystem via the File System Access API
- Download fallback triggers automatically when the API is unavailable
- Username is persisted to `localStorage` between visits
- No server endpoint exists; this is entirely client-side

**3. Response JSON schema:**

```json
{
  "username":  "alice123",
  "role":      "Developer",
  "usage":     "Every day (5 days)",
  "score":     5,
  "timestamp": "2026-03-27T13:03:40+00:00",
  "week":      "2026-W13"
}
```

**4. `_DAU_SCORE_MAP` — single source of truth for scoring:**

- `"Every day (5 days)"` → 5.0
- `"Most days (3–4 days)"` → 3.5
- `"Rarely (1–2 days)"` → 1.5
- `"Not used"` → 0.0

**5. `compute_dau_metrics()` contract:**

- Scans `responses_dir` for all `dau_*.json` files
- Returns `{team_avg: float|None, response_count: int, by_role: [{role, avg, count}], breakdown: [{answer, count}]}`
- `team_avg` is `None` when `response_count == 0`; both reporters treat this as "no data"
- Preserve this contract — reporters depend on it

**6. Run DAU tests:**

```bash
.venv/Scripts/pytest tests/ -v -k "dau"
```

**Token-efficiency:** do not load reporter/template files unless the DAU output shape changes; DAU computation is independent of Jira sprint data.
