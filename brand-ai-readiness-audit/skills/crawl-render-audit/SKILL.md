---
name: crawl-render-audit
description: >
  Checks whether AI search crawlers (GPTBot, ClaudeBot, PerplexityBot,
  Google-Extended) can access a website. Detects robots.txt blocks,
  JavaScript rendering gaps where content is invisible without JS execution,
  and HTTP error responses on key pages.
license: MIT
compatibility: Python 3.10+, requests, playwright, beautifulsoup4
allowed-tools:
  - bash
  - python
  - web_fetch
---

# Crawl & Render Audit

## When to Use

Activate this skill when evaluating a website's technical accessibility for
AI web scrapers and search-indexing bots. This skill answers the question:
**"Can an automated AI spider actually reach and read the page content?"**

## Inputs

- `url` (string, required): The fully qualified URL of the website to audit
  (e.g., `https://example.com`).

## Procedure

### Step 1 — Check robots.txt for AI Crawler Blocks

Run the robots.txt checker script:

```bash
python3 scripts/check_robots.py --url "<url>"
```

This script:
1. Fetches `<url>/robots.txt`.
2. Parses it for `Disallow` rules targeting AI user-agents: `GPTBot`,
   `ClaudeBot`, `PerplexityBot`, `Google-Extended`.
3. Outputs a JSON finding if any AI crawlers are blocked.

### Step 2 — Detect JavaScript Rendering Gaps

Run the JS render gap detection script:

```bash
python3 scripts/check_js_render_gap.py --url "<url>"
```

This script:
1. Fetches the raw HTML of the page using `requests` (no JS execution).
2. Fetches the fully rendered DOM using Playwright (with JS execution).
3. Extracts visible text from both versions.
4. Computes the word-count ratio. If the rendered version has **>30% more
   words** than the raw version, it indicates a significant JS rendering gap.
5. Also checks for non-200 HTTP status codes and redirect issues.
6. Outputs JSON findings for any detected issues.

### Step 3 — Collect Findings

Combine the JSON outputs from Steps 1 and 2 into a single JSON array.
Save this array to `/tmp/crawl_findings.json`.

## Output Schema

A JSON array of finding objects:

```json
[
  {
    "id": "CRAWL-01",
    "title": "AI search crawlers blocked in robots.txt",
    "severity": "critical",
    "evidence": "robots.txt disallows GPTBot and ClaudeBot via 'User-agent: GPTBot\\nDisallow: /'",
    "suggested_action": {
      "summary": "Remove or relax Disallow rules for GPTBot and ClaudeBot in robots.txt to enable AI search citation.",
      "priority": "critical"
    }
  }
]
```

## References

- [AI Crawlers & Directives Rubric](references/ai_crawlers_rubric.md): Authoritative list of AI crawler user-agents (GPTBot, ClaudeBot, PerplexityBot, Google-Extended), robots.txt parsing rules, and severity guidelines.
