---
name: corroboration-entity-audit
description: >
  Evaluates whether bold factual claims on a website are corroborated by
  independent external sources. Checks for entity disambiguation via
  Organization schema sameAs links to Wikidata, Wikipedia, or LinkedIn to
  prevent brand-name confusion in AI responses.
license: MIT
compatibility: Python 3.10+, requests, beautifulsoup4
allowed-tools:
  - bash
  - python
  - web_fetch
---

# Corroboration & Entity Audit

## When to Use

Activate this skill when evaluating whether a brand's factual claims are
externally verifiable and whether the brand entity is unambiguously
distinguishable from other entities sharing the same or similar names.

## Inputs

- `url` (string, required): The fully qualified URL of the website to audit
  (e.g., `https://example.com`).

## Procedure

### Step 1 — Check External Corroboration of Claims

Run the corroboration checker:

```bash
python3 scripts/check_corroboration.py --url "<url>"
```

This script:
1. Extracts visible text from the page.
2. Identifies bold factual claims — statements containing specific numbers,
   statistics, rankings, awards, or superlatives (e.g., "#1 rated",
   "clinically proven", "40% faster", "founded in 1998").
3. For each claim, searches the web to check if the same fact appears on
   any domain other than the target site.
4. If a claim appears ONLY on the brand's own domain, it is flagged as
   non-corroborated.
5. Outputs JSON findings for non-corroborated claims.

### Step 2 — Check Entity Disambiguation

Run the entity disambiguation checker:

```bash
python3 scripts/check_entity_disambiguation.py --url "<url>"
```

This script:
1. Extracts the brand/organization name from the page (via `<title>`,
   `<meta>` tags, `Organization` schema, or prominent headings).
2. Checks whether `Organization` JSON-LD schema includes `sameAs` links
   to authoritative sources (Wikidata, Wikipedia, LinkedIn, social profiles).
3. Searches the brand name to detect if multiple unrelated entities share
   the same name (name collision risk).
4. Outputs JSON findings if `sameAs` links are missing or if high collision
   risk is detected.

### Step 3 — Collect Findings

Combine the JSON outputs from Steps 1 and 2 into a single JSON array.
Save this array to `/tmp/corroboration_findings.json`.

## Output Schema

```json
[
  {
    "id": "CORR-01",
    "title": "Non-corroborated factual claim",
    "severity": "medium",
    "evidence": "Claim 'voted #1 CRM platform in 2025' found only on example.com; no independent source confirms this.",
    "suggested_action": {
      "summary": "Link to or cite the independent source (award body, study, review site) that supports this claim, or remove the claim.",
      "priority": "medium"
    }
  }
]
```

## References

- [Knowledge Graph Authorities Reference](references/knowledge_graph_authorities.md): Authoritative external registries (Wikidata, Wikipedia, Crunchbase, official registries) used to corroborate brand claims and disambiguate entities.
