---
name: audit-orchestrator
description: >
  Entrypoint skill for the Brand AI-Readiness Audit marketplace. Given a target
  website URL, sequentially invokes crawl-render-audit, structured-data-audit,
  corroboration-entity-audit, and engagement-audit, then merges all findings
  into a single deterministic JSON report with normalized IDs and severity
  summary counts.
license: MIT
compatibility: Python 3.10+
allowed-tools:
  - bash
  - python
  - web_fetch
---

# Audit Orchestrator

## When to Use

Activate this skill when the user provides a website URL and asks for a brand
AI-readiness audit. This is the **only** skill invoked directly — it composes
all other skills in the marketplace.

## Inputs

- `url` (string, required): The fully qualified URL of the website to audit
  (e.g., `https://example.com`).

## Procedure

Follow these steps **exactly and sequentially**:

### Step 1 — Invoke `crawl-render-audit`

Read and execute the skill at `../crawl-render-audit/SKILL.md`, passing the
target `url`. Collect the returned JSON array of findings.

### Step 2 — Invoke `structured-data-audit`

Read and execute the skill at `../structured-data-audit/SKILL.md`, passing the
target `url`. Collect the returned JSON array of findings.

### Step 3 — Invoke `corroboration-entity-audit`

Read and execute the skill at `../corroboration-entity-audit/SKILL.md`, passing
the target `url`. Collect the returned JSON array of findings.

### Step 4 — Invoke `engagement-audit`

Read and execute the skill at `../engagement-audit/SKILL.md`, passing the
target `url`. Collect the returned JSON array of findings.

### Step 5 — Merge and Emit Final Report

Save each skill's JSON findings to temporary files, then run the merge script:

```bash
python3 scripts/merge_findings.py \
  --url "<url>" \
  --crawl-file /tmp/crawl_findings.json \
  --structured-file /tmp/structured_findings.json \
  --corroboration-file /tmp/corroboration_findings.json \
  --engagement-file /tmp/engagement_findings.json
```

The script will:
1. Load all finding arrays from the four JSON files.
2. Re-assign sequential IDs (`F-001`, `F-002`, ...).
3. Compute severity summary counts (`critical`, `high`, `medium`).
4. Emit the final JSON report to stdout.

**Present the full JSON output as the final audit report.**

## Output Schema

The merged report conforms to this schema:

```json
{
  "site": "example.com",
  "audited_at": "2026-09-20T14:32:00Z",
  "summary": {
    "total_findings": 6,
    "critical": 1,
    "high": 2,
    "medium": 3
  },
  "findings": [
    {
      "id": "F-001",
      "title": "...",
      "severity": "critical | high | medium",
      "evidence": "...",
      "suggested_action": {
        "summary": "...",
        "priority": "critical | high | medium"
      }
    }
  ]
}
```

## References

- [Scoring & Severity Rubric](references/scoring_and_severity_rubric.md): Detailed definitions for critical, high, and medium severity classifications, ID numbering schemes, and proactive recommendation guidelines.
