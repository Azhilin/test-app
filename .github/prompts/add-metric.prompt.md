---
name: add-metric
description: Add or change a metric in this repository with the right scope and validation.
agent: metrics-maintainer
argument-hint: Describe the metric, the expected output fields, and any files or tests you already know are relevant.
---

Work on a metric change for the AI Adoption Metrics Report repository.

Task: ${input:task:Describe the metric to add or change}
Relevant files: ${input:files:List specific files if known, for example app/core/metrics.py and tests/unit/test_metrics.py}
Validation preference: ${input:validation:Name the smallest test command or say targeted unit tests}

Requirements:

- Start with the smallest relevant file set.
- Preserve schema-driven behavior where applicable.
- Keep Markdown and HTML report outputs aligned if the metric becomes user-visible.
- Reuse existing helpers and test factories.
- Explain any contract changes to the metrics dictionary.
