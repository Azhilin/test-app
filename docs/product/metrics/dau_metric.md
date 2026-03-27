# DAU Metric — Daily Active Usage

## Overview

The Daily Active Usage (DAU) metric measures the average number of working days per week that
team members actively use AI tools (e.g. GitHub Copilot, Gemini Assist). It is collected weekly
via a self-reported survey and produces a single team-level average score on a 0–5 scale.

The metric is a **weekly snapshot** — it reflects the most recently submitted responses for each
team member and is not a rolling or cumulative average.

---

## Scoring

Respondents select one of four usage-frequency options. Each option maps to a days-per-week score:

| Survey Answer | Days / week score |
|---|---|
| Every day (5 days) | 5 |
| Most days (3–4 days) | 3.5 |
| Rarely (1–2 days) | 1.5 |
| Not used | 0 |

**Midpoint rationale:** "Most days" is scored 3.5 (midpoint of 3–4) and "Rarely" is scored 1.5
(midpoint of 1–2). This avoids overstating or understating the actual frequency when a range is
reported.

---

## Team DAU Average

$$\text{Team DAU} = \frac{\sum \text{scores}}{\text{count(respondents)}}$$

- **Unit:** average working days per week per person (0–5 scale)
- **Scope:** all response files found in the configured responses directory (see [Storage](#storage-convention))
- **Edge case:** if no response files are present, the metric returns `None` for all numeric
  fields and `0` for counts; both report renderers treat this as "no data" and skip the section

---

## Data Schema

Each survey submission is stored as a single JSON file with the following shape:

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

| Field | Type | Description |
|---|---|---|
| `username` | string | Alphanumeric identifier, min 2 chars; used to identify the respondent |
| `role` | string | Selected role from the dropdown |
| `usage` | string | Raw survey answer text (one of the four scoring options) |
| `score` | number | Mapped days-per-week score (0, 1.5, 3.5, or 5) |
| `timestamp` | string | ISO-8601 with UTC offset (`+00:00`) |
| `week` | string | ISO week string computed from the submission time (e.g. `2026-W13`) |

---

## Storage Convention

Response files are stored in the `generated/` directory (default). The filename encodes the
respondent and submission time:

```
dau_<username>_<timestamp>.json
```

**Example:** `dau_alice123_20260327T130340Z.json`

- **One file per submission** — multiple submissions by the same user in the same week are each
  stored as separate files; the metrics computation aggregates all files found in the directory.
- **Configurable path:** the `DAU_RESPONSES_DIR` environment variable overrides the default
  `generated/` directory.
- **Version control:** all `dau_*.json` files are listed in `.gitignore` and are never committed
  to the repository.

---

## `compute_dau_metrics()` Output Shape

`compute_dau_metrics(responses_dir)` reads all `dau_*.json` files from `responses_dir` and
returns the following dict:

```python
{
    "team_avg":       float | None,   # None if response_count == 0
    "response_count": int,
    "by_role": [
        {"role": str, "avg": float, "count": int}
    ],
    "breakdown": [
        {"answer": str, "count": int}
    ]
}
```

| Key | Description |
|---|---|
| `team_avg` | Average score across all respondents; `None` when `response_count` is 0 |
| `response_count` | Total number of response files read |
| `by_role` | Per-role averages; one entry per distinct role, sorted alphabetically |
| `breakdown` | Per-answer counts; one entry per distinct usage answer, sorted by descending count |
