# Brand AI-Readiness Audit

> **Adobe University Hackathon 2026 — Round 3**
> An Agent Skill Marketplace that audits any website's AI-readiness and emits an actionable JSON report.

---

## Overview

This marketplace package contains **5 Agent Skills** conforming to the [agentskills.io](https://agentskills.io) specification. Given a target URL, the entrypoint skill orchestrates four specialized audit skills and produces a unified findings report.

## Skills

### 1. `audit-orchestrator` *(Entrypoint)*
Receives the target URL, sequentially invokes all four audit skills below, merges their findings into a single JSON report with normalized IDs and severity summary counts.

### 2. `crawl-render-audit`
Checks whether AI search crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended) can access the site. Detects `robots.txt` blocks, JavaScript rendering gaps (content invisible without JS execution), and HTTP error responses.

### 3. `structured-data-audit`
Validates the presence and completeness of JSON-LD / schema.org structured data. Checks whether key business facts (price, availability, organization identity) are stated in plain text or locked inside images without alt text.

### 4. `corroboration-entity-audit`
Evaluates whether bold factual claims on the site are corroborated by independent external sources. Checks for entity disambiguation via `sameAs` links to Wikidata, Wikipedia, or LinkedIn to prevent brand-name confusion.

### 5. `engagement-audit`
Assesses on-site user experience: above-the-fold orientation (heading, value proposition, CTA), internal link health (broken links, click depth), and mobile/viewport readiness.

## Composition Flow

```
Grader invokes → audit-orchestrator (entrypoint), passes a URL
                        ↓
        orchestrator calls each helper skill in turn
    ┌───────────────┬───────────────┬───────────────────┐
    ↓               ↓               ↓                   ↓
crawl-render-   structured-data-  corroboration-     engagement-
audit           audit             entity-audit       audit
    ↓               ↓               ↓                   ↓
 findings[]     findings[]        findings[]         findings[]
    └───────────────┴───────────────┴───────────────────┘
                        ↓
     orchestrator merges, assigns IDs, counts by severity,
              emits final JSON report
```

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt
playwright install chromium

# The agent invokes the entrypoint skill with a target URL:
# "Run the audit-orchestrator skill on https://example.com"
```

## Requirements

- Python 3.10+
- See `requirements.txt` for Python package dependencies

## Constraints

- **Read-only** — no skill ever modifies a live site
- **Respects `robots.txt`** for all live HTTP requests
- **Deterministic** — same input produces same findings
- **Runtime < 5 minutes** per site audit
- **Package ≤ 50 MB**, no bundled model weights
