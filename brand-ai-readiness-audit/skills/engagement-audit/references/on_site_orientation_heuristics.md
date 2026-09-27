# On-Site Orientation & Engagement Heuristics

This reference documents the heuristics used to evaluate whether a website
effectively orients both human visitors and AI crawlers toward understanding
the brand's core value proposition.

## Above-the-Fold Orientation Check

The first 500 words of visible text on a homepage (approximately the
above-the-fold content) must answer these questions:

| Question | Signal Checked | Severity if Missing |
|---|---|---|
| **What does this brand do?** | `<h1>` contains a clear value proposition | High |
| **Who is it for?** | Target audience mentioned in first 500 words | Medium |
| **What action should I take?** | Primary CTA visible (button, link) | Medium |

### Why This Matters for AI

When an AI assistant is asked *"What does [Brand] do?"*, it typically:
1. Fetches the homepage.
2. Reads the `<title>`, `<h1>`, and `<meta description>`.
3. Scans the first paragraph of body text.

If these elements are vague, image-only, or JavaScript-rendered, the AI will
either hallucinate an answer or say *"I couldn't find information about this
company."*

## Navigation & Internal Linking

| Check | Why It Matters |
|---|---|
| **Descriptive link text** | AI crawlers cannot interpret "Click here" or "Learn more" — they need links like "View pricing plans" or "Read our API documentation" |
| **Flat information architecture** | Key pages (About, Pricing, Contact, Docs) should be ≤2 clicks from homepage |
| **Breadcrumb navigation** | Helps AI understand page hierarchy and relationships |

## Meta Description Quality

The `<meta name="description">` tag should be:
- **50–160 characters** long
- **Unique per page** (not duplicated across all pages)
- **Factual, not promotional** (AI systems prefer objective descriptions)
- **Include the brand name** for entity association

## Responsive Design Signals

| Signal | Why It Matters |
|---|---|
| **Viewport meta tag** | `<meta name="viewport" content="width=device-width">` — indicates mobile-friendly |
| **No horizontal scroll** | Content fits within viewport |
| **Readable font sizes** | Minimum 14px body text |

## Content Freshness Indicators

| Signal | Check | Severity |
|---|---|---|
| **Copyright date** | Footer copyright year should be current year (2026) or ≤1 year old | Medium |
| **Last modified dates** | Articles/blog posts should show recent publication dates | Medium |
| **Stale content** | A "2024 Guide" still live in 2026 without updates signals staleness | Medium |

AI systems deprioritize content they believe is outdated. A copyright
footer showing "© 2021" on a page claiming to be a market leader raises
contradiction flags in LLM reasoning chains.
