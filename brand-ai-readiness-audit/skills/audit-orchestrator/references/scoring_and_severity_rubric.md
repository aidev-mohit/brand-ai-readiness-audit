# Scoring & Severity Rubric

This reference documents the severity classification rubric used by the
Brand AI-Readiness Audit to assign finding severity levels.

## Severity Levels

### Critical

A finding is **Critical** when the brand is effectively **invisible or
misrepresented** to AI systems. The issue will cause AI hallucination,
omission, or incorrect answers about the brand.

**Examples:**
- No JSON-LD structured data on any page
- AI crawlers (GPTBot, ClaudeBot) explicitly blocked in robots.txt
- Entire site content locked behind JavaScript with no SSR/pre-rendering
- Key facts (pricing, contact) exist only in images/PDFs, not in text

### High

A finding is **High** when the brand is **partially discoverable** but
missing critical signals that prevent reliable AI representation.

**Examples:**
- Organization schema exists but has no `sameAs` links (no entity disambiguation)
- Missing `<title>` tag on the homepage
- Unverifiable superlative claims ("World's #1") with no external corroboration
- Key pages return 4xx/5xx errors

### Medium

A finding is **Medium** when the brand is discoverable but could improve
its AI representation with straightforward optimizations.

**Examples:**
- Missing `<meta description>` on important pages
- Missing `robots.txt` file (not blocking, just absent)
- No `<h1>` heading on the page
- Copyright date is stale (>1 year old)
- No breadcrumb navigation schema

## Proactive Recommendations (Beyond-Problem)

Even when no defect is found, the audit may include proactive
recommendations to strengthen AI representation:

| Recommendation | Category | Priority |
|---|---|---|
| Create an `llms.txt` file | Discoverability | Medium |
| Add `sameAs` link to Wikidata entity | Entity Authority | High |
| Add Author/Person schemas for E-E-A-T | Trust Signals | Medium |
| Add FAQ schema to support pages | Content Depth | Medium |
| Add `potentialAction` SearchAction to WebSite schema | Engagement | Medium |

## ID Assignment

All findings across all sub-skills are merged and assigned sequential IDs
in the format `F-001`, `F-002`, etc., by the `merge_findings.py` script.
This ensures a stable, deterministic ordering regardless of which sub-skill
discovered each finding.
