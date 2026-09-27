#!/usr/bin/env python3
"""
check_corroboration.py — Identifies bold factual claims on a website and checks
whether they are corroborated by independent external sources.

Usage:
    python3 check_corroboration.py --url "https://example.com"

Output:
    A JSON array of findings printed to stdout.

Note:
    This script uses web search to verify claims. It is designed to be
    defensive — network failures or rate limits will not crash the audit.
"""

import argparse
import json
import re
import sys
from urllib.parse import quote_plus, urlparse

import requests
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 15
MAX_CLAIMS_TO_CHECK = 5

# Patterns that indicate a factual claim worth verifying
CLAIM_PATTERNS = [
    # Rankings and awards
    r"(?:#\s?\d+|number\s+(?:one|1))\s+\w+",
    r"\b(?:award[- ]?winning|best[- ]?selling|top[- ]?rated|leading|largest|fastest)\b",
    r"\bvoted\s+(?:#?\d+|best|top)\b",

    # Statistics and percentages
    r"\b\d+%\s+(?:faster|better|more|less|increase|decrease|reduction|improvement|growth)\b",
    r"\b(?:over|more than|up to)\s+\d[\d,]*\s+(?:customers|users|clients|companies|downloads)\b",

    # Specific claims
    r"\b(?:clinically\s+)?proven\b",
    r"\b(?:patented|patent[- ]?pending)\b",
    r"\bfounded\s+(?:in\s+)?\d{4}\b",
    r"\b(?:certified|accredited)\s+by\b",
    r"\b(?:trusted\s+by|used\s+by|chosen\s+by)\s+(?:over\s+)?\d",

    # Superlatives
    r"\bworld'?s?\s+(?:first|best|largest|fastest|most|only)\b",
    r"\b(?:industry|market)\s+leader\b",
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


def extract_claims(html: str) -> list[dict]:
    """Extract factual claims from page text.

    Returns list of dicts with 'text' (the surrounding sentence) and 'pattern' (what matched).
    """
    soup = BeautifulSoup(html, "html.parser")
    for tag in soup(["script", "style", "noscript"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)

    # Split into sentences (rough)
    sentences = re.split(r"[.!?\n]+", text)
    claims = []
    seen_claims = set()

    for sentence in sentences:
        sentence = sentence.strip()
        if len(sentence) < 10 or len(sentence) > 300:
            continue

        for pattern in CLAIM_PATTERNS:
            match = re.search(pattern, sentence, re.IGNORECASE)
            if match:
                # Normalize to avoid duplicates
                claim_key = sentence[:80].lower().strip()
                if claim_key not in seen_claims:
                    seen_claims.add(claim_key)
                    claims.append({
                        "text": sentence.strip(),
                        "matched_pattern": match.group(),
                    })
                break

        if len(claims) >= MAX_CLAIMS_TO_CHECK * 2:
            break

    return claims[:MAX_CLAIMS_TO_CHECK]


def search_for_corroboration(claim_text: str, target_domain: str) -> dict:
    """Search the web to check if a claim exists on sites other than the target.

    Returns dict with 'corroborated' (bool) and 'details' (str).

    This uses a simple heuristic: search for the claim's key phrases and check
    if results come from domains other than the target.
    """
    # Extract the most specific part of the claim for searching
    # Remove common filler words
    search_query = claim_text[:150]

    try:
        # Use a simple web search via DuckDuckGo HTML (no API key needed)
        search_url = f"https://html.duckduckgo.com/html/?q={quote_plus(search_query)}"
        response = requests.get(
            search_url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "Mozilla/5.0 (compatible; BrandAuditBot/1.0)",
            },
        )

        if response.status_code != 200:
            return {
                "corroborated": None,  # Unknown
                "details": f"Search returned HTTP {response.status_code}",
            }

        soup = BeautifulSoup(response.text, "html.parser")
        results = soup.find_all("a", class_="result__a")

        external_sources = []
        for result in results[:10]:
            href = result.get("href", "")
            result_domain = urlparse(href).netloc.replace("www.", "")
            if result_domain and result_domain != target_domain.replace("www.", ""):
                external_sources.append(result_domain)

        if external_sources:
            return {
                "corroborated": True,
                "details": f"Found on external domains: {', '.join(external_sources[:3])}",
            }
        else:
            return {
                "corroborated": False,
                "details": "No independent external sources found for this claim.",
            }

    except requests.RequestException as e:
        return {
            "corroborated": None,
            "details": f"Search failed: {type(e).__name__}",
        }


def main():
    parser = argparse.ArgumentParser(
        description="Check external corroboration of factual claims."
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    args = parser.parse_args()

    url = args.url
    target_domain = urlparse(url).netloc
    all_findings = []

    html = fetch_page(url)
    if html is None:
        all_findings.append({
            "title": "Could not fetch page for corroboration audit",
            "severity": "medium",
            "evidence": f"Failed to fetch {url}.",
            "suggested_action": {
                "summary": "Ensure the page is accessible.",
                "priority": "medium",
            },
        })
        print(json.dumps(all_findings, indent=2, ensure_ascii=False))
        return

    # Extract claims
    claims = extract_claims(html)

    if not claims:
        # No bold claims found — not necessarily a problem
        print(json.dumps(all_findings, indent=2, ensure_ascii=False))
        return

    # Check each claim for corroboration
    uncorroborated_claims = []
    for claim in claims:
        result = search_for_corroboration(claim["text"], target_domain)

        if result["corroborated"] is False:
            uncorroborated_claims.append({
                "claim": claim["text"],
                "matched": claim["matched_pattern"],
                "details": result["details"],
            })

    # Generate findings for uncorroborated claims
    if uncorroborated_claims:
        for i, uc in enumerate(uncorroborated_claims):
            all_findings.append({
                "title": "Non-corroborated factual claim",
                "severity": "medium",
                "evidence": (
                    f"Claim: \"{uc['claim']}\"\n"
                    f"Matched pattern: '{uc['matched']}'\n"
                    f"Result: {uc['details']}\n"
                    f"This claim appears only on {target_domain} with no independent "
                    f"external sources confirming it."
                ),
                "suggested_action": {
                    "summary": (
                        "Either cite the independent source that supports this claim "
                        "(link to the award body, study, review site) or rephrase the "
                        "claim to be verifiable. Non-corroborated claims may be ignored "
                        "or flagged as unreliable by AI assistants."
                    ),
                    "priority": "medium",
                },
            })

    print(json.dumps(all_findings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
