#!/usr/bin/env python3
"""
check_plain_text_facts.py — Checks whether key business facts are stated
explicitly in plain text or are vague/missing/locked inside images.

Usage:
    python3 check_plain_text_facts.py --url "https://example.com"

Output:
    A JSON array of findings printed to stdout.
"""

import argparse
from datetime import datetime
import json
import re
import sys
from urllib.parse import urlparse

import requests
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 15

# Patterns to detect explicit business facts in text
PRICE_PATTERNS = [
    r"\$\s?\d+",           # $99, $ 99
    r"€\s?\d+",            # €99
    r"£\s?\d+",            # £99
    r"₹\s?\d+",            # ₹99
    r"\d+\.\d{2}\s?(USD|EUR|GBP|INR|CAD|AUD)",  # 99.00 USD
    r"(price|cost|fee|pricing)\s*[:=]\s*",       # price: ...
]

CONTACT_PATTERNS = [
    r"[\w.+-]+@[\w-]+\.[\w.-]+",           # email
    r"\+?\d[\d\s\-().]{7,}\d",             # phone number
    r"\d{1,5}\s\w+\s(street|st|ave|avenue|road|rd|blvd|drive|dr|lane|ln)",  # address
]

# Image patterns that suggest informational content
INFO_IMAGE_PATTERNS = [
    r"(price|pricing|spec|specification|feature|comparison|plan|table|chart|menu|rate)",
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


def extract_text_content(html: str) -> str:
    """Extract visible text from the page."""
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()
    return soup.get_text(separator=" ", strip=True)


def check_brand_name_prominence(html: str, url: str) -> list[dict]:
    """Check if the brand/organization name is prominently stated."""
    findings = []
    soup = BeautifulSoup(html, "html.parser")

    # Get the domain name as a proxy for brand name
    parsed = urlparse(url)
    domain_parts = parsed.netloc.replace("www.", "").split(".")
    brand_hint = domain_parts[0] if domain_parts else ""

    # Check title tag
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""

    # Check h1
    h1 = soup.find("h1")
    h1_text = h1.get_text(strip=True) if h1 else ""

    # Check meta og:site_name or og:title
    og_site = soup.find("meta", property="og:site_name")
    og_title = soup.find("meta", property="og:title")

    has_brand_in_heading = bool(h1_text)
    has_brand_in_title = bool(title_text)

    if not has_brand_in_title:
        findings.append({
            "title": "Missing or empty <title> tag",
            "severity": "high",
            "evidence": (
                f"Page {url} has no <title> tag or it is empty. "
                f"AI assistants and search engines use the title as the primary identifier."
            ),
            "suggested_action": {
                "summary": "Add a descriptive <title> tag that includes the brand name and a concise description of the page content.",
                "priority": "high",
            },
        })

    if not has_brand_in_heading:
        findings.append({
            "title": "No <h1> heading on the page",
            "severity": "medium",
            "evidence": (
                f"Page {url} has no <h1> heading. The <h1> is the most important "
                f"on-page signal for both search engines and AI assistants to understand "
                f"what the page is about."
            ),
            "suggested_action": {
                "summary": "Add a single, descriptive <h1> heading near the top of the page that clearly states the brand or page topic.",
                "priority": "medium",
            },
        })

    return findings


def check_pricing_in_text(text: str, url: str) -> list[dict]:
    """Check if pricing information is present in plain text.

    Note: Not all sites need pricing. This is a soft check.
    """
    # Only flag if the page seems commerce-related but has no prices
    commerce_signals = [
        r"\b(buy|purchase|order|shop|cart|checkout|add to cart)\b",
        r"\b(product|item|plan|subscription|pricing|price)\b",
    ]

    is_commerce = any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in commerce_signals
    )

    if not is_commerce:
        return []  # Not a commerce page, no finding needed

    has_price = any(
        re.search(pattern, text, re.IGNORECASE)
        for pattern in PRICE_PATTERNS
    )

    findings = []
    if not has_price:
        findings.append({
            "title": "Commerce-related page lacks explicit pricing in text",
            "severity": "medium",
            "evidence": (
                f"Page {url} contains commerce-related terms (buy, product, pricing, etc.) "
                f"but no explicit prices in plain text. Without machine-readable prices, "
                f"AI assistants cannot accurately quote costs to users."
            ),
            "suggested_action": {
                "summary": (
                    "State prices explicitly in plain text (e.g., '$49/month' or '€199'). "
                    "Also add Product/Offer JSON-LD with price and priceCurrency properties."
                ),
                "priority": "medium",
            },
        })

    return findings


def check_image_locked_info(html: str, url: str) -> list[dict]:
    """Detect images that likely contain informational content but lack alt text."""
    soup = BeautifulSoup(html, "html.parser")
    findings = []

    images_missing_alt = []
    info_images_no_alt = []

    for img in soup.find_all("img"):
        src = img.get("src", "")
        alt = img.get("alt", "").strip()

        if not alt:
            images_missing_alt.append(src)

            # Check if the image filename suggests informational content
            src_lower = src.lower()
            for pattern in INFO_IMAGE_PATTERNS:
                if re.search(pattern, src_lower):
                    info_images_no_alt.append(src)
                    break

    # Flag images that likely contain information but have no alt text
    if info_images_no_alt:
        examples = info_images_no_alt[:3]
        examples_str = ", ".join(f"'{e}'" for e in examples)
        findings.append({
            "title": "Informational images lack alt text (image-locked data)",
            "severity": "high",
            "evidence": (
                f"Page {url} contains {len(info_images_no_alt)} image(s) with "
                f"filenames suggesting informational content (prices, specs, comparisons) "
                f"but no alt text. Examples: {examples_str}. AI crawlers cannot read "
                f"content embedded in images without alt text."
            ),
            "suggested_action": {
                "summary": (
                    "Add descriptive alt text to all informational images. Better yet, "
                    "convert image-based tables, pricing, and specs into HTML text so AI "
                    "crawlers and screen readers can access the data."
                ),
                "priority": "high",
            },
        })

    # General alt text coverage check
    total_images = len(soup.find_all("img"))
    if total_images > 0:
        missing_pct = (len(images_missing_alt) / total_images) * 100
        if missing_pct > 50 and len(images_missing_alt) > 3:
            findings.append({
                "title": "Majority of images lack alt text",
                "severity": "medium",
                "evidence": (
                    f"Page {url} has {total_images} images, of which "
                    f"{len(images_missing_alt)} ({missing_pct:.0f}%) are missing alt text."
                ),
                "suggested_action": {
                    "summary": "Add meaningful alt text to all images that convey information. Decorative images should have empty alt='' attributes.",
                    "priority": "medium",
                },
            })

    return findings


def check_dates_and_freshness(html: str, text: str, url: str) -> list[dict]:
    """Detect stale copyright notices and contradictory publication dates."""
    findings = []
    current_year = datetime.now().year

    # 1. Search for copyright notices in HTML
    # e.g., "© 2019-2022", "Copyright 2021", "&copy; 2020", "(c) 2018"
    copyright_matches = re.findall(
        r"(?:©|&copy;|copyright|\(c\))\s*(?:(?:19|20)\d{2}\s*[-–—/]\s*)?((?:19|20)\d{2})",
        html,
        re.IGNORECASE,
    )

    # 2. Search for structured date metadata (e.g. article:published_time, datePublished, etc.)
    soup = BeautifulSoup(html, "html.parser")
    meta_dates = []
    for meta in soup.find_all("meta"):
        prop = (meta.get("property", "") or meta.get("name", "")).lower()
        if any(d in prop for d in ["date", "time", "published", "modified"]):
            content = meta.get("content", "")
            year_match = re.search(r"((?:19|20)\d{2})", content)
            if year_match:
                meta_dates.append(int(year_match.group(1)))

    if copyright_matches:
        years = [int(y) for y in copyright_matches if 1990 <= int(y) <= current_year + 1]
        if years:
            latest_copy_year = max(years)
            if latest_copy_year < current_year - 1:
                years_behind = current_year - latest_copy_year
                severity = "high" if years_behind >= 3 else "medium"
                findings.append({
                    "title": f"Stale copyright date detected ({latest_copy_year})",
                    "severity": severity,
                    "evidence": (
                        f"Page {url} displays a copyright year of {latest_copy_year} "
                        f"(current year: {current_year}). Outdated copyright dates are a strong "
                        f"negative freshness heuristic used by AI search engines (ChatGPT, Perplexity, Claude), "
                        f"causing them to treat brand information as potentially obsolete or dormant."
                    ),
                    "suggested_action": {
                        "summary": (
                            f"Update the copyright notice to {current_year} (ideally using a dynamic template "
                            f"or build script). Ensure structured publication and modification dates reflect current updates."
                        ),
                        "priority": severity,
                    },
                })

            if meta_dates:
                latest_meta_year = max(meta_dates)
                if abs(latest_meta_year - latest_copy_year) >= 3:
                    findings.append({
                        "title": "Contradictory date signals between metadata and page content",
                        "severity": "medium",
                        "evidence": (
                            f"Page metadata indicates content from year {latest_meta_year}, but footer/text "
                            f"declares copyright year {latest_copy_year}. Conflicting date signals confuse "
                            f"AI crawlers attempting to establish fact recency and source authority."
                        ),
                        "suggested_action": {
                            "summary": (
                                "Align on-page visible dates, structured JSON-LD dateModified/datePublished, "
                                "and footer copyright years so AI models can confidently determine content currency."
                            ),
                            "priority": "medium",
                        },
                    })

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Check plain-text fact clarity, freshness, and image-locked data."
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    args = parser.parse_args()

    url = args.url
    all_findings = []

    html = fetch_page(url)
    if html is None:
        all_findings.append({
            "title": "Could not fetch page for plain-text fact audit",
            "severity": "high",
            "evidence": f"Failed to fetch {url}.",
            "suggested_action": {
                "summary": "Ensure the page is accessible.",
                "priority": "high",
            },
        })
        print(json.dumps(all_findings, indent=2, ensure_ascii=False))
        return

    text = extract_text_content(html)

    # Run checks
    all_findings.extend(check_brand_name_prominence(html, url))
    all_findings.extend(check_pricing_in_text(text, url))
    all_findings.extend(check_image_locked_info(html, url))
    all_findings.extend(check_dates_and_freshness(html, text, url))

    print(json.dumps(all_findings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
