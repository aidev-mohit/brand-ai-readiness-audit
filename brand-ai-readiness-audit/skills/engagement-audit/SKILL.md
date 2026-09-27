---
name: engagement-audit
description: >
  Assesses on-site user experience for visitors arriving via AI referrals.
  Checks above-the-fold orientation (heading, value proposition, CTA),
  internal link health (broken links, excessive click depth), and
  mobile/viewport readiness.
license: MIT
compatibility: Python 3.10+, requests, beautifulsoup4
allowed-tools:
  - bash
  - python
  - web_fetch
---

# Engagement Audit

## When to Use

Activate this skill when evaluating whether a website retains visitors who
arrive via AI assistant referrals or search results. This skill answers:
**"When a user lands on this site, do they stay or bounce?"**

## Inputs

- `url` (string, required): The fully qualified URL of the website to audit
  (e.g., `https://example.com`).

## Procedure

### Step 1 — Check Above-the-Fold Orientation

Run the orientation checker:

```bash
python3 scripts/check_orientation.py --url "<url>"
```

This script:
1. Fetches the page HTML.
2. Checks for presence and quality of:
   - `<title>` tag (non-empty, descriptive, not generic)
   - `<meta name="description">` (non-empty, within recommended length)
   - `<h1>` heading (exists, non-empty, appears early in the DOM)
   - Call-to-action elements (buttons or prominent links) in the first
     section of the page
3. Evaluates whether the page provides immediate orientation: does a
   visitor instantly understand what the site/brand offers?
4. Outputs JSON findings for missing or weak orientation elements.

### Step 2 — Check Link Health and Responsiveness

Run the link and responsiveness checker:

```bash
python3 scripts/check_links_and_responsiveness.py --url "<url>"
```

This script:
1. Extracts all internal links from the page.
2. Tests each link for HTTP status (identifies broken links returning
   4xx/5xx responses).
3. Measures click depth — how many clicks from the homepage to reach
   key pages (flags pages requiring >3 clicks).
4. Checks for `<meta name="viewport">` tag for mobile responsiveness.
5. Measures basic page load time and total page weight.
6. Outputs JSON findings for broken links, deep pages, and missing
   viewport configuration.

### Step 3 — Collect Findings

Combine the JSON outputs from Steps 1 and 2 into a single JSON array.
Save this array to `/tmp/engagement_findings.json`.

## Output Schema

```json
[
  {
    "id": "ENGAGE-01",
    "title": "Missing meta description",
    "severity": "medium",
    "evidence": "Page has no <meta name='description'> tag. AI assistants and search engines use this for snippet generation.",
    "suggested_action": {
      "summary": "Add a <meta name='description'> tag with a compelling 150-160 character summary of the page content.",
      "priority": "medium"
    }
  }
]
```

## References

- [On-Site Orientation & Engagement Heuristics](references/on_site_orientation_heuristics.md): Evaluation criteria for value propositions, above-the-fold clarity, CTA presence, link integrity, and mobile responsiveness.
