#!/usr/bin/env python3
"""
check_js_render_gap.py — Detects JavaScript rendering gaps by comparing raw
HTML content with the fully rendered DOM. Also checks for HTTP errors and
redirect issues.

Usage:
    python3 check_js_render_gap.py --url "https://example.com"

Output:
    A JSON array of findings printed to stdout.

Requires:
    pip install requests beautifulsoup4 playwright
    playwright install chromium
"""

import argparse
import json
import re
import sys
import time

import requests
from bs4 import BeautifulSoup

# Request timeout in seconds
REQUEST_TIMEOUT = 15
# Playwright page timeout in ms
PLAYWRIGHT_TIMEOUT = 15000
# Threshold: if rendered text has >30% more words, flag it
JS_GAP_THRESHOLD = 0.30
# Max pages to check beyond the homepage
MAX_PAGES_TO_CHECK = 3


def extract_visible_text(html: str) -> str:
    """Extract visible text from HTML, ignoring script/style tags."""
    soup = BeautifulSoup(html, "html.parser")

    # Remove script and style elements
    for tag in soup(["script", "style", "noscript", "meta", "link", "head"]):
        tag.decompose()

    text = soup.get_text(separator=" ", strip=True)
    # Normalize whitespace
    text = re.sub(r"\s+", " ", text).strip()
    return text


def count_words(text: str) -> int:
    """Count the number of words in a text string."""
    return len(text.split()) if text else 0


def fetch_raw_html(url: str) -> tuple[str | None, int | None, list[dict]]:
    """Fetch raw HTML without JS execution.

    Returns:
        Tuple of (html_content, status_code, findings).
    """
    findings = []
    try:
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={
                "User-Agent": "BrandAuditBot/1.0 (read-only audit)",
                "Accept": "text/html",
            },
            allow_redirects=True,
        )

        # Check for non-200 status
        if response.status_code >= 400:
            findings.append({
                "title": f"Page returns HTTP {response.status_code} error",
                "severity": "critical" if response.status_code >= 500 else "high",
                "evidence": (
                    f"GET {url} returned HTTP {response.status_code}. "
                    f"AI crawlers and search engines cannot index error pages."
                ),
                "suggested_action": {
                    "summary": f"Fix the HTTP {response.status_code} error on {url}. Ensure the page returns a 200 OK response with valid content.",
                    "priority": "critical" if response.status_code >= 500 else "high",
                },
            })

        # Check for excessive redirects
        if len(response.history) > 3:
            chain = " → ".join(str(r.status_code) + " " + r.url for r in response.history)
            findings.append({
                "title": "Excessive redirect chain detected",
                "severity": "medium",
                "evidence": (
                    f"URL {url} went through {len(response.history)} redirects: {chain}. "
                    f"Long redirect chains slow down crawlers and may cause them to abandon the page."
                ),
                "suggested_action": {
                    "summary": "Reduce the redirect chain to at most 1-2 hops. Update internal links to point directly to the final URL.",
                    "priority": "medium",
                },
            })

        return response.text, response.status_code, findings

    except requests.exceptions.TooManyRedirects:
        findings.append({
            "title": "Redirect loop detected",
            "severity": "critical",
            "evidence": f"URL {url} causes an infinite redirect loop. The page is completely inaccessible.",
            "suggested_action": {
                "summary": "Fix the redirect loop. Check server configuration and ensure redirects terminate at a valid page.",
                "priority": "critical",
            },
        })
        return None, None, findings

    except requests.RequestException as e:
        findings.append({
            "title": "Page is unreachable",
            "severity": "critical",
            "evidence": f"Could not fetch {url}: {type(e).__name__}: {e}",
            "suggested_action": {
                "summary": "Ensure the page is accessible. Check DNS, SSL certificates, and server availability.",
                "priority": "critical",
            },
        })
        return None, None, findings


def fetch_rendered_html(url: str) -> str | None:
    """Fetch fully rendered HTML using Playwright (JS execution).

    Returns:
        Rendered HTML content, or None if Playwright is not available.
    """
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print(
            "Warning: Playwright not installed. Skipping JS render gap check. "
            "Install with: pip install playwright && playwright install chromium",
            file=sys.stderr,
        )
        return None

    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            page = browser.new_page()
            page.set_default_timeout(PLAYWRIGHT_TIMEOUT)

            page.goto(url, wait_until="networkidle", timeout=PLAYWRIGHT_TIMEOUT)
            # Wait a bit for any remaining JS to finish
            page.wait_for_timeout(2000)

            content = page.content()
            browser.close()
            return content

    except Exception as e:
        print(f"Warning: Playwright rendering failed for {url}: {e}", file=sys.stderr)
        return None


def check_js_render_gap(url: str, raw_html: str, rendered_html: str | None) -> list[dict]:
    """Compare raw vs rendered HTML to detect JS rendering gaps."""
    findings = []

    if rendered_html is None:
        # Cannot perform comparison without rendered HTML
        return findings

    raw_text = extract_visible_text(raw_html)
    rendered_text = extract_visible_text(rendered_html)

    raw_words = count_words(raw_text)
    rendered_words = count_words(rendered_text)

    if raw_words == 0 and rendered_words == 0:
        findings.append({
            "title": "Page has no visible text content",
            "severity": "high",
            "evidence": (
                f"Both raw HTML and rendered DOM of {url} contain 0 words of visible text. "
                f"AI crawlers cannot extract any meaningful content from this page."
            ),
            "suggested_action": {
                "summary": "Add visible text content to the page. Ensure key information is not solely in images, videos, or interactive widgets without text alternatives.",
                "priority": "high",
            },
        })
        return findings

    if raw_words == 0 and rendered_words > 0:
        gap_percent = 100.0
    elif raw_words > 0:
        gap_percent = ((rendered_words - raw_words) / raw_words) * 100
    else:
        gap_percent = 0

    if gap_percent > (JS_GAP_THRESHOLD * 100):
        severity = "critical" if gap_percent > 80 else "high"
        findings.append({
            "title": "Significant JavaScript rendering gap detected",
            "severity": severity,
            "evidence": (
                f"Raw HTML contains {raw_words} words, but the JS-rendered page contains "
                f"{rendered_words} words — a {gap_percent:.0f}% increase. This means "
                f"{rendered_words - raw_words} words of content are invisible to AI crawlers "
                f"that do not execute JavaScript (e.g., GPTBot, ClaudeBot)."
            ),
            "suggested_action": {
                "summary": (
                    "Implement Server-Side Rendering (SSR) or Static Site Generation (SSG) "
                    "to ensure critical content is present in the initial HTML response. "
                    "Alternatively, use pre-rendering for bot user-agents. Key content like "
                    "product descriptions, prices, and navigation should not rely solely on "
                    "client-side JavaScript."
                ),
                "priority": severity,
            },
        })
    elif raw_words > 0 and gap_percent < 5:
        # No significant gap — site is well-rendered server-side (no finding needed)
        pass

    return findings


def discover_subpages(url: str, html: str) -> list[str]:
    """Extract a few internal subpage URLs for additional checking."""
    soup = BeautifulSoup(html, "html.parser")
    parsed_base = urlparse(url)
    base_domain = parsed_base.netloc

    subpages = set()
    for link in soup.find_all("a", href=True):
        href = link["href"]

        # Resolve relative URLs
        if href.startswith("/"):
            href = f"{parsed_base.scheme}://{base_domain}{href}"
        elif not href.startswith("http"):
            continue

        parsed_href = urlparse(href)
        # Only same-domain links
        if parsed_href.netloc != base_domain:
            continue
        # Skip anchors, mailto, tel, javascript
        if any(href.startswith(p) for p in ["mailto:", "tel:", "javascript:"]):
            continue
        # Skip common non-content paths
        path_lower = parsed_href.path.lower()
        if any(skip in path_lower for skip in ["/cdn-cgi/", "/wp-admin/", "/wp-login", ".xml", ".json", ".css", ".js"]):
            continue

        clean_url = f"{parsed_href.scheme}://{parsed_href.netloc}{parsed_href.path}"
        if clean_url != url and clean_url not in subpages:
            subpages.add(clean_url)

        if len(subpages) >= MAX_PAGES_TO_CHECK:
            break

    return list(subpages)[:MAX_PAGES_TO_CHECK]


def main():
    parser = argparse.ArgumentParser(
        description="Detect JavaScript rendering gaps and HTTP issues."
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    args = parser.parse_args()

    url = args.url
    all_findings = []

    # Step 1: Fetch raw HTML and check HTTP status
    raw_html, status_code, http_findings = fetch_raw_html(url)
    all_findings.extend(http_findings)

    if raw_html is None:
        # Can't proceed without raw HTML
        print(json.dumps(all_findings, indent=2, ensure_ascii=False))
        return

    # Step 2: Fetch rendered HTML via Playwright
    rendered_html = fetch_rendered_html(url)

    # Step 3: Compare raw vs rendered for JS gap
    gap_findings = check_js_render_gap(url, raw_html, rendered_html)
    all_findings.extend(gap_findings)

    # Step 4: Quick check on a couple of subpages for HTTP errors
    subpages = discover_subpages(url, raw_html)
    for subpage_url in subpages:
        _, sub_status, sub_findings = fetch_raw_html(subpage_url)
        all_findings.extend(sub_findings)

    # Output findings as JSON
    print(json.dumps(all_findings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
