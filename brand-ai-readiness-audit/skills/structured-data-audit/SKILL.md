---
name: structured-data-audit
description: >
  Validates the presence and completeness of JSON-LD / schema.org structured
  data on a website. Checks whether key business facts (price, availability,
  organization identity) are stated in plain text or locked inside images
  without alt text. Detects missing, invalid, or incomplete structured data
  that prevents AI assistants from accurately representing the brand.
license: MIT
compatibility: Python 3.10+, requests, beautifulsoup4, extruct
allowed-tools:
  - bash
  - python
  - web_fetch
---

# Structured Data Audit

## When to Use

Activate this skill when evaluating whether a website's content is
machine-formalized with schema.org structured data, or at minimum clearly
stated in plain text so AI systems can extract facts without guessing.

## Inputs

- `url` (string, required): The fully qualified URL of the website to audit
  (e.g., `https://example.com`).

## Procedure

### Step 1 — Extract and Validate JSON-LD

Run the JSON-LD extraction script:

```bash
python3 scripts/extract_jsonld.py --url "<url>"
```

This script:
1. Fetches the page HTML.
2. Parses all `<script type="application/ld+json">` blocks.
3. Validates each block as valid JSON.
4. Checks for expected schema.org types (`Organization`, `Product`, `Offer`,
   `FAQPage`, `WebSite`, `BreadcrumbList`).
5. For each type found, checks completeness of required properties (e.g.,
   `Product` should have `name`, `price`, `availability`; `Organization`
   should have `name`, `url`, `logo`).
6. Crawls up to 10 internal pages to check for structured data presence
   across the site, not just the homepage.
7. Outputs JSON findings for missing or incomplete structured data.

### Step 2 — Check Plain-Text Fact Clarity

Run the plain-text fact checker:

```bash
python3 scripts/check_plain_text_facts.py --url "<url>"
```

This script:
1. Extracts all visible text from the page using BeautifulSoup.
2. Checks whether key business facts are explicitly stated in readable text:
   - Organization/brand name in a heading or prominent position
   - Pricing information (currency symbols, numeric values)
   - Contact information (email, phone, address patterns)
3. Detects images that likely contain text data (product specs, pricing
   tables) but lack descriptive `alt` attributes.
4. Outputs JSON findings for vague, missing, or image-locked facts.

### Step 3 — Collect Findings

Combine the JSON outputs from Steps 1 and 2 into a single JSON array.
Save this array to `/tmp/structured_findings.json`.

## Output Schema

```json
[
  {
    "id": "STRUCT-01",
    "title": "No JSON-LD structured data on product pages",
    "severity": "high",
    "evidence": "Crawled 12 product pages; 0/12 contain <script type='application/ld+json'>. Missing required Schema.org/Product properties: [name, price, availability].",
    "suggested_action": {
      "summary": "Add Product/Offer JSON-LD to every product page with at minimum: name, price, priceCurrency, availability.",
      "priority": "high"
    }
  }
]
```

## References

- [Schema.org Structured Data Requirements](references/schema_requirements.md): Minimum viable JSON-LD structured data specifications for Organization, Product, WebSite, and FAQPage schemas.
