#!/usr/bin/env python3
"""
check_orientation.py — Checks above-the-fold orientation quality: title tag,
meta description, H1 heading, and call-to-action presence.

Usage:
    python3 check_orientation.py --url "https://example.com"

Output:
    A JSON array of findings printed to stdout.
"""

import argparse
import json
import re
import sys

import requests
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 15

# Recommended meta description length (characters)
META_DESC_MIN = 50
META_DESC_MAX = 160

# Title tag recommended length (characters)
TITLE_MIN = 10
TITLE_MAX = 70

# Generic/placeholder title patterns
GENERIC_TITLE_PATTERNS = [
    r"^(home|homepage|welcome|untitled|document|page|website)$",
    r"^(react app|next\.?js app|my (site|app|website|page))$",
    r"^(index|default|main)$",
]

# CTA-like elements: buttons and links with action-oriented text
CTA_PATTERNS = [
    r"\b(get started|sign up|try free|start now|buy now|learn more|contact us)\b",
    r"\b(subscribe|download|request demo|book|schedule|explore|shop now)\b",
    r"\b(join|register|create account|free trial|see plans|view pricing)\b",
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


def check_title_tag(soup: BeautifulSoup, url: str) -> list[dict]:
    """Check the <title> tag quality."""
    findings = []
    title = soup.find("title")
    title_text = title.get_text(strip=True) if title else ""

    if not title_text:
        findings.append({
            "title": "Missing or empty <title> tag",
            "severity": "high",
            "evidence": (
                f"Page {url} has no <title> tag or it is empty. The title tag is the "
                f"primary label used by AI assistants, search engines, and browser tabs."
            ),
            "suggested_action": {
                "summary": "Add a descriptive <title> tag (10-70 characters) that includes the brand name and page purpose.",
                "priority": "high",
            },
        })
    else:
        # Check for generic/placeholder titles
        for pattern in GENERIC_TITLE_PATTERNS:
            if re.match(pattern, title_text, re.IGNORECASE):
                findings.append({
                    "title": f"Generic/placeholder title: '{title_text}'",
                    "severity": "high",
                    "evidence": (
                        f"Page {url} has a generic title '{title_text}' that doesn't describe "
                        f"the brand or page content. AI assistants use the title to identify "
                        f"and cite the page."
                    ),
                    "suggested_action": {
                        "summary": f"Replace the generic title '{title_text}' with a descriptive title that includes the brand name and a concise page description.",
                        "priority": "high",
                    },
                })
                break

        # Check title length
        if len(title_text) < TITLE_MIN:
            findings.append({
                "title": f"Title tag too short ({len(title_text)} characters)",
                "severity": "medium",
                "evidence": (
                    f"Title '{title_text}' is only {len(title_text)} characters. "
                    f"Recommended: {TITLE_MIN}-{TITLE_MAX} characters for optimal display."
                ),
                "suggested_action": {
                    "summary": f"Expand the title to {TITLE_MIN}-{TITLE_MAX} characters. Include the brand name, primary keyword, and page purpose.",
                    "priority": "medium",
                },
            })
        elif len(title_text) > TITLE_MAX:
            findings.append({
                "title": f"Title tag too long ({len(title_text)} characters)",
                "severity": "medium",
                "evidence": (
                    f"Title is {len(title_text)} characters, exceeding the recommended "
                    f"maximum of {TITLE_MAX}. It will be truncated in search results and AI citations."
                ),
                "suggested_action": {
                    "summary": f"Shorten the title to under {TITLE_MAX} characters while keeping the most important keywords at the beginning.",
                    "priority": "medium",
                },
            })

    return findings


def check_meta_description(soup: BeautifulSoup, url: str) -> list[dict]:
    """Check the <meta name='description'> tag."""
    findings = []

    meta_desc = soup.find("meta", attrs={"name": "description"})
    desc_content = meta_desc.get("content", "").strip() if meta_desc else ""

    if not desc_content:
        findings.append({
            "title": "Missing meta description",
            "severity": "medium",
            "evidence": (
                f"Page {url} has no <meta name='description'> tag or it is empty. "
                f"AI assistants and search engines use this for snippet generation."
            ),
            "suggested_action": {
                "summary": f"Add a <meta name='description'> tag with a compelling {META_DESC_MIN}-{META_DESC_MAX} character summary of the page content.",
                "priority": "medium",
            },
        })
    elif len(desc_content) < META_DESC_MIN:
        findings.append({
            "title": f"Meta description too short ({len(desc_content)} characters)",
            "severity": "medium",
            "evidence": (
                f"Meta description is only {len(desc_content)} characters: '{desc_content}'. "
                f"Recommended: {META_DESC_MIN}-{META_DESC_MAX} characters."
            ),
            "suggested_action": {
                "summary": f"Expand the meta description to {META_DESC_MIN}-{META_DESC_MAX} characters with a compelling summary of the page content.",
                "priority": "medium",
            },
        })

    return findings


def check_h1_heading(soup: BeautifulSoup, url: str) -> list[dict]:
    """Check for H1 heading presence and quality."""
    findings = []
    h1_tags = soup.find_all("h1")

    if not h1_tags:
        findings.append({
            "title": "No <h1> heading found",
            "severity": "high",
            "evidence": (
                f"Page {url} has no <h1> heading. The H1 is the most important on-page "
                f"signal for understanding the page topic. Visitors arriving from AI "
                f"referrals need immediate orientation."
            ),
            "suggested_action": {
                "summary": "Add a single, descriptive <h1> heading near the top of the page that clearly communicates what the page/brand offers.",
                "priority": "high",
            },
        })
    elif len(h1_tags) > 1:
        h1_texts = [h1.get_text(strip=True)[:50] for h1 in h1_tags]
        findings.append({
            "title": f"Multiple <h1> headings found ({len(h1_tags)})",
            "severity": "medium",
            "evidence": (
                f"Page {url} has {len(h1_tags)} <h1> tags: {h1_texts}. "
                f"Best practice is a single H1 per page for clear topic signaling."
            ),
            "suggested_action": {
                "summary": "Keep only one <h1> heading per page. Convert secondary headings to <h2> or <h3>.",
                "priority": "medium",
            },
        })
    else:
        h1_text = h1_tags[0].get_text(strip=True)
        if len(h1_text) < 3:
            findings.append({
                "title": "H1 heading is too short or empty",
                "severity": "medium",
                "evidence": f"The <h1> heading on {url} contains only '{h1_text}' — too brief to provide orientation.",
                "suggested_action": {
                    "summary": "Replace the H1 with a meaningful heading that describes the page content or value proposition.",
                    "priority": "medium",
                },
            })

    return findings


def check_cta_presence(soup: BeautifulSoup, url: str) -> list[dict]:
    """Check for call-to-action elements in the initial page section."""
    findings = []

    # Look for buttons and prominent links
    buttons = soup.find_all("button")
    links = soup.find_all("a")

    # Check buttons and links for CTA text
    all_interactive = []
    for btn in buttons:
        text = btn.get_text(strip=True).lower()
        if text:
            all_interactive.append(text)
    for link in links:
        text = link.get_text(strip=True).lower()
        # Only check links that look like CTAs (have class/role suggesting prominence)
        classes = " ".join(link.get("class", []))
        if "btn" in classes.lower() or "button" in classes.lower() or "cta" in classes.lower():
            all_interactive.append(text)
        elif text:
            all_interactive.append(text)

    has_cta = False
    for text in all_interactive:
        for pattern in CTA_PATTERNS:
            if re.search(pattern, text, re.IGNORECASE):
                has_cta = True
                break
        if has_cta:
            break

    if not has_cta and not buttons:
        findings.append({
            "title": "No clear call-to-action (CTA) found",
            "severity": "medium",
            "evidence": (
                f"Page {url} has no buttons or prominent action-oriented links "
                f"(e.g., 'Get Started', 'Sign Up', 'Learn More'). Visitors arriving "
                f"from AI referrals need a clear next step."
            ),
            "suggested_action": {
                "summary": "Add a prominent call-to-action button or link near the top of the page that guides visitors to the most important action.",
                "priority": "medium",
            },
        })

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Check above-the-fold orientation quality."
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    args = parser.parse_args()

    url = args.url
    all_findings = []

    html = fetch_page(url)
    if html is None:
        all_findings.append({
            "title": "Could not fetch page for orientation audit",
            "severity": "high",
            "evidence": f"Failed to fetch {url}.",
            "suggested_action": {
                "summary": "Ensure the page is accessible.",
                "priority": "high",
            },
        })
        print(json.dumps(all_findings, indent=2, ensure_ascii=False))
        return

    soup = BeautifulSoup(html, "html.parser")

    all_findings.extend(check_title_tag(soup, url))
    all_findings.extend(check_meta_description(soup, url))
    all_findings.extend(check_h1_heading(soup, url))
    all_findings.extend(check_cta_presence(soup, url))

    print(json.dumps(all_findings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
