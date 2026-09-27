#!/usr/bin/env python3
"""
check_entity_disambiguation.py — Checks whether the brand entity is
unambiguously identifiable. Validates Organization schema sameAs links
and checks for brand name collisions.

Usage:
    python3 check_entity_disambiguation.py --url "https://example.com"

Output:
    A JSON array of findings printed to stdout.
"""

import argparse
import json
import re
import sys
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 15

# Authoritative sameAs domains
SAMEAS_DOMAINS = [
    "wikidata.org",
    "wikipedia.org",
    "linkedin.com",
    "twitter.com",
    "x.com",
    "facebook.com",
    "instagram.com",
    "youtube.com",
    "github.com",
    "crunchbase.com",
]


def fetch_page(url: str) -> str | None:
    """Fetch page HTML."""
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


def extract_brand_name(html: str, url: str) -> str:
    """Extract the brand/organization name from the page."""
    soup = BeautifulSoup(html, "html.parser")

    # Try JSON-LD Organization schema first
    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            if isinstance(data, list):
                for item in data:
                    if isinstance(item, dict) and item.get("@type") in ("Organization", "LocalBusiness"):
                        name = item.get("name", "")
                        if name:
                            return name
            elif isinstance(data, dict):
                if data.get("@type") in ("Organization", "LocalBusiness"):
                    name = data.get("name", "")
                    if name:
                        return name
        except json.JSONDecodeError:
            continue

    # Try og:site_name
    og_site = soup.find("meta", property="og:site_name")
    if og_site and og_site.get("content", "").strip():
        return og_site["content"].strip()

    # Try title tag (first part before separator)
    title = soup.find("title")
    if title:
        title_text = title.get_text(strip=True)
        # Common pattern: "Brand Name | Page Title" or "Brand Name - Page Title"
        for sep in ["|", " - ", " – ", " — ", ":"]:
            if sep in title_text:
                parts = title_text.split(sep)
                # Brand is usually the last part for page-first titles,
                # or first part for brand-first titles
                brand = parts[0].strip()
                if len(brand) > 2:
                    return brand
        if title_text and len(title_text) < 50:
            return title_text

    # Fallback: use domain name
    parsed = urlparse(url)
    domain = parsed.netloc.replace("www.", "")
    return domain.split(".")[0].capitalize()


def extract_sameas_links(html: str) -> list[str]:
    """Extract sameAs links from JSON-LD schema."""
    soup = BeautifulSoup(html, "html.parser")
    sameas_links = []

    for script in soup.find_all("script", type="application/ld+json"):
        try:
            data = json.loads(script.string or "")
            items = data if isinstance(data, list) else [data]
            for item in items:
                if not isinstance(item, dict):
                    continue
                same_as = item.get("sameAs", [])
                if isinstance(same_as, str):
                    same_as = [same_as]
                if isinstance(same_as, list):
                    sameas_links.extend(same_as)
        except json.JSONDecodeError:
            continue

    return sameas_links


def check_sameas_coverage(sameas_links: list[str], brand_name: str, url: str) -> list[dict]:
    """Check sameAs link coverage and quality."""
    findings = []

    if not sameas_links:
        findings.append({
            "title": "No sameAs links in Organization schema",
            "severity": "high",
            "evidence": (
                f"The site {url} has no sameAs links in its JSON-LD schema. "
                f"Without sameAs links to authoritative sources (Wikidata, LinkedIn, "
                f"Wikipedia), AI assistants cannot reliably distinguish '{brand_name}' "
                f"from other entities with the same or similar name."
            ),
            "suggested_action": {
                "summary": (
                    f"Add sameAs links to the Organization JSON-LD schema. At minimum, link to:\n"
                    f"- LinkedIn company page\n"
                    f"- Wikidata entity (create one if it doesn't exist)\n"
                    f"- Official social media profiles\n"
                    f"Example: \"sameAs\": [\"https://linkedin.com/company/{brand_name.lower()}\", "
                    f"\"https://www.wikidata.org/wiki/Q...\"]"
                ),
                "priority": "high",
            },
        })
        return findings

    # Check which authoritative domains are covered
    covered_domains = set()
    for link in sameas_links:
        parsed = urlparse(link)
        domain = parsed.netloc.replace("www.", "")
        for auth_domain in SAMEAS_DOMAINS:
            if domain.endswith(auth_domain):
                covered_domains.add(auth_domain)
                break

    # Check for critical missing sameAs
    critical_missing = []
    if "wikidata.org" not in covered_domains and "wikipedia.org" not in covered_domains:
        critical_missing.append("Wikidata/Wikipedia")
    if "linkedin.com" not in covered_domains:
        critical_missing.append("LinkedIn")

    if critical_missing:
        missing_str = ", ".join(critical_missing)
        findings.append({
            "title": f"Organization schema missing key sameAs links: {missing_str}",
            "severity": "medium",
            "evidence": (
                f"Organization schema has {len(sameas_links)} sameAs link(s) "
                f"({', '.join(covered_domains) if covered_domains else 'none recognized'}) "
                f"but is missing links to: {missing_str}. These are the most important "
                f"sources for AI entity disambiguation."
            ),
            "suggested_action": {
                "summary": f"Add sameAs links for: {missing_str}. Wikidata is especially important for AI knowledge graph matching.",
                "priority": "medium",
            },
        })

    return findings


def check_name_collision(brand_name: str, url: str) -> list[dict]:
    """Check if the brand name is ambiguous (collides with other entities)."""
    findings = []

    # Heuristic: short, common-word brand names are high collision risk
    common_words = {
        "apple", "amazon", "shell", "dove", "jaguar", "delta", "nova", "atlas",
        "phoenix", "pioneer", "summit", "apex", "prime", "core", "spark",
        "pulse", "wave", "hub", "nest", "bloom", "stripe", "bolt", "dash",
        "flow", "grid", "hive", "loop", "node", "path", "sage", "vine",
    }

    brand_lower = brand_name.lower().strip()

    # Check if brand name is a single common English word
    is_common_word = brand_lower in common_words or len(brand_lower) <= 3

    if is_common_word:
        findings.append({
            "title": f"Brand name '{brand_name}' has high collision risk",
            "severity": "medium",
            "evidence": (
                f"The brand name '{brand_name}' is a common word or very short name "
                f"that is likely shared by multiple unrelated entities. AI assistants "
                f"may confuse this brand with other entities named '{brand_name}'."
            ),
            "suggested_action": {
                "summary": (
                    f"Strengthen entity disambiguation for '{brand_name}':\n"
                    f"1. Add Organization JSON-LD with sameAs links to Wikidata and LinkedIn\n"
                    f"2. Use the full legal name in structured data (e.g., '{brand_name} Inc.' or '{brand_name} Technologies')\n"
                    f"3. Ensure the Wikidata entry clearly distinguishes this entity"
                ),
                "priority": "medium",
            },
        })

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Check entity disambiguation and sameAs coverage."
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    args = parser.parse_args()

    url = args.url
    all_findings = []

    html = fetch_page(url)
    if html is None:
        all_findings.append({
            "title": "Could not fetch page for entity audit",
            "severity": "medium",
            "evidence": f"Failed to fetch {url}.",
            "suggested_action": {
                "summary": "Ensure the page is accessible.",
                "priority": "medium",
            },
        })
        print(json.dumps(all_findings, indent=2, ensure_ascii=False))
        return

    # Extract brand name
    brand_name = extract_brand_name(html, url)

    # Check sameAs coverage
    sameas_links = extract_sameas_links(html)
    all_findings.extend(check_sameas_coverage(sameas_links, brand_name, url))

    # Check name collision risk
    all_findings.extend(check_name_collision(brand_name, url))

    print(json.dumps(all_findings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
