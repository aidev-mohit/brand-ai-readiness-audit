#!/usr/bin/env python3
"""
extract_jsonld.py — Extracts and validates JSON-LD structured data from a
website. Checks for presence, valid JSON, correct schema.org types, and
completeness of required properties.

Usage:
    python3 extract_jsonld.py --url "https://example.com"

Output:
    A JSON array of findings printed to stdout.
"""

import argparse
import json
import re
import sys
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 15
MAX_PAGES_TO_CRAWL = 10

# Expected schema.org types and their important properties
SCHEMA_TYPE_REQUIREMENTS = {
    "Organization": {
        "required": ["name", "url"],
        "recommended": ["logo", "description", "sameAs", "contactPoint"],
    },
    "WebSite": {
        "required": ["name", "url"],
        "recommended": ["description", "potentialAction"],
    },
    "Product": {
        "required": ["name"],
        "recommended": ["description", "image", "offers", "brand", "sku"],
    },
    "Offer": {
        "required": ["price", "priceCurrency"],
        "recommended": ["availability", "url", "itemCondition"],
    },
    "LocalBusiness": {
        "required": ["name", "address"],
        "recommended": ["telephone", "openingHours", "geo", "url"],
    },
    "Article": {
        "required": ["headline", "author"],
        "recommended": ["datePublished", "image", "publisher"],
    },
    "FAQPage": {
        "required": ["mainEntity"],
        "recommended": [],
    },
    "BreadcrumbList": {
        "required": ["itemListElement"],
        "recommended": [],
    },
}


def fetch_page(url: str) -> str | None:
    """Fetch a page's HTML content."""
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "BrandAuditBot/1.0 (read-only audit)"},
            allow_redirects=True,
        )
        if response.status_code == 200:
            return response.text
        return None
    except requests.RequestException:
        return None


def extract_jsonld_blocks(html: str) -> list[dict]:
    """Extract all JSON-LD blocks from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    blocks = []

    for script in soup.find_all("script", type="application/ld+json"):
        text = script.string
        if not text:
            continue
        try:
            data = json.loads(text)
            if isinstance(data, list):
                blocks.extend(data)
            else:
                blocks.append(data)
        except json.JSONDecodeError:
            # Record invalid JSON-LD separately
            blocks.append({"_invalid_json": True, "_raw": text[:200]})

    return blocks


def get_schema_types(block: dict) -> list[str]:
    """Extract the @type(s) from a JSON-LD block."""
    if block.get("_invalid_json"):
        return []

    type_val = block.get("@type", "")
    if isinstance(type_val, list):
        return type_val
    return [type_val] if type_val else []


def check_property_completeness(block: dict, schema_type: str) -> dict:
    """Check if a JSON-LD block has the required/recommended properties."""
    requirements = SCHEMA_TYPE_REQUIREMENTS.get(schema_type)
    if not requirements:
        return {"missing_required": [], "missing_recommended": []}

    missing_required = []
    missing_recommended = []

    for prop in requirements["required"]:
        # Handle nested properties (e.g., offers might be nested)
        if prop not in block or block[prop] is None or block[prop] == "":
            missing_required.append(prop)

    for prop in requirements["recommended"]:
        if prop not in block or block[prop] is None or block[prop] == "":
            missing_recommended.append(prop)

    return {
        "missing_required": missing_required,
        "missing_recommended": missing_recommended,
    }


def discover_internal_urls(base_url: str, html: str) -> list[str]:
    """Discover internal URLs for crawling."""
    soup = BeautifulSoup(html, "html.parser")
    parsed_base = urlparse(base_url)
    urls = set()

    for link in soup.find_all("a", href=True):
        href = link["href"]
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        if parsed.netloc == parsed_base.netloc:
            clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            if clean != base_url:
                urls.add(clean)

    return list(urls)[:MAX_PAGES_TO_CRAWL]


def audit_page_jsonld(url: str, html: str) -> tuple[list[dict], list[dict]]:
    """Audit a single page's JSON-LD. Returns (jsonld_blocks, findings)."""
    findings = []
    blocks = extract_jsonld_blocks(html)

    # Check for invalid JSON-LD
    invalid_blocks = [b for b in blocks if b.get("_invalid_json")]
    valid_blocks = [b for b in blocks if not b.get("_invalid_json")]

    for inv in invalid_blocks:
        findings.append({
            "title": "Invalid JSON-LD block (malformed JSON)",
            "severity": "high",
            "evidence": (
                f"Page {url} contains a <script type='application/ld+json'> block with "
                f"invalid JSON that cannot be parsed. Preview: {inv.get('_raw', 'N/A')}"
            ),
            "suggested_action": {
                "summary": "Fix the JSON syntax in the JSON-LD script block. Validate using https://validator.schema.org/ or https://search.google.com/test/rich-results",
                "priority": "high",
            },
        })

    # Check completeness of each valid block
    for block in valid_blocks:
        types = get_schema_types(block)
        for schema_type in types:
            if schema_type in SCHEMA_TYPE_REQUIREMENTS:
                completeness = check_property_completeness(block, schema_type)
                if completeness["missing_required"]:
                    props = ", ".join(completeness["missing_required"])
                    findings.append({
                        "title": f"Incomplete {schema_type} structured data — missing required properties",
                        "severity": "high",
                        "evidence": (
                            f"Page {url} has a {schema_type} JSON-LD block but is missing "
                            f"required properties: [{props}]."
                        ),
                        "suggested_action": {
                            "summary": (
                                f"Add the missing properties [{props}] to the {schema_type} "
                                f"JSON-LD block on {url}."
                            ),
                            "priority": "high",
                        },
                    })
                if completeness["missing_recommended"]:
                    props = ", ".join(completeness["missing_recommended"])
                    findings.append({
                        "title": f"{schema_type} structured data missing recommended properties",
                        "severity": "medium",
                        "evidence": (
                            f"Page {url} has a {schema_type} JSON-LD block but is missing "
                            f"recommended properties: [{props}]. Adding these improves how "
                            f"AI assistants and search engines represent the brand."
                        ),
                        "suggested_action": {
                            "summary": (
                                f"Add the recommended properties [{props}] to the {schema_type} "
                                f"JSON-LD block to provide richer context for AI assistants."
                            ),
                            "priority": "medium",
                        },
                    })

    return valid_blocks, findings


def main():
    parser = argparse.ArgumentParser(
        description="Extract and validate JSON-LD structured data."
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    args = parser.parse_args()

    url = args.url
    all_findings = []

    # Fetch homepage
    homepage_html = fetch_page(url)
    if homepage_html is None:
        all_findings.append({
            "title": "Could not fetch page for structured data audit",
            "severity": "high",
            "evidence": f"Failed to fetch {url} — cannot check for JSON-LD structured data.",
            "suggested_action": {
                "summary": "Ensure the page is accessible and returns valid HTML.",
                "priority": "high",
            },
        })
        print(json.dumps(all_findings, indent=2, ensure_ascii=False))
        return

    # Audit homepage JSON-LD
    homepage_blocks, homepage_findings = audit_page_jsonld(url, homepage_html)
    all_findings.extend(homepage_findings)

    # Discover and audit internal pages
    internal_urls = discover_internal_urls(url, homepage_html)
    all_page_blocks = {url: homepage_blocks}

    pages_with_jsonld = 1 if homepage_blocks else 0
    pages_checked = 1

    for page_url in internal_urls:
        pages_checked += 1
        html = fetch_page(page_url)
        if html:
            blocks, page_findings = audit_page_jsonld(page_url, html)
            all_findings.extend(page_findings)
            all_page_blocks[page_url] = blocks
            if blocks:
                pages_with_jsonld += 1

    # Check if the site has NO structured data at all
    total_blocks = sum(len(b) for b in all_page_blocks.values())
    if total_blocks == 0:
        all_findings.insert(0, {
            "title": "No JSON-LD structured data found on any page",
            "severity": "critical",
            "evidence": (
                f"Crawled {pages_checked} pages; 0/{pages_checked} contain "
                f"<script type='application/ld+json'>. Without structured data, AI "
                f"assistants must guess or infer facts about the brand, increasing "
                f"the risk of hallucination or omission."
            ),
            "suggested_action": {
                "summary": (
                    "Add JSON-LD structured data to key pages. At minimum, add an "
                    "Organization schema to the homepage:\n"
                    '{\n  "@context": "https://schema.org",\n  "@type": "Organization",\n'
                    '  "name": "Your Brand",\n  "url": "https://example.com",\n'
                    '  "logo": "https://example.com/logo.png",\n'
                    '  "sameAs": ["https://linkedin.com/company/...", '
                    '"https://twitter.com/..."]\n}'
                ),
                "priority": "critical",
            },
        })
    elif pages_with_jsonld < pages_checked and pages_checked > 1:
        # Some pages have it, some don't
        pages_without = pages_checked - pages_with_jsonld
        if pages_without > pages_checked * 0.5:
            all_findings.append({
                "title": "Majority of pages lack JSON-LD structured data",
                "severity": "high",
                "evidence": (
                    f"Only {pages_with_jsonld}/{pages_checked} crawled pages contain "
                    f"JSON-LD structured data. {pages_without} pages have no structured data."
                ),
                "suggested_action": {
                    "summary": (
                        f"Extend JSON-LD structured data coverage to all key pages. "
                        f"Currently {pages_without}/{pages_checked} pages are missing structured data."
                    ),
                    "priority": "high",
                },
            })

    # Check for missing Organization schema specifically
    has_org_schema = False
    for page_blocks in all_page_blocks.values():
        for block in page_blocks:
            types = get_schema_types(block)
            if "Organization" in types or "LocalBusiness" in types:
                has_org_schema = True
                break
        if has_org_schema:
            break

    if not has_org_schema and total_blocks > 0:
        all_findings.append({
            "title": "Missing Organization/LocalBusiness structured data",
            "severity": "high",
            "evidence": (
                f"The site has {total_blocks} JSON-LD block(s) but none use the "
                f"Organization or LocalBusiness type. Without this, AI assistants "
                f"cannot reliably identify the brand entity behind the site."
            ),
            "suggested_action": {
                "summary": (
                    "Add Organization JSON-LD to the homepage with at minimum: "
                    "name, url, logo, and sameAs (linking to social profiles and Wikidata)."
                ),
                "priority": "high",
            },
        })

    print(json.dumps(all_findings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
