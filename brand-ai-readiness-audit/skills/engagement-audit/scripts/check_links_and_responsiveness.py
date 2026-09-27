#!/usr/bin/env python3
"""
check_links_and_responsiveness.py — Checks internal link health (broken links,
click depth) and mobile/viewport readiness.

Usage:
    python3 check_links_and_responsiveness.py --url "https://example.com"

Output:
    A JSON array of findings printed to stdout.
"""

import argparse
import json
import re
import sys
import time
from collections import deque
from urllib.parse import urljoin, urlparse

import requests
from bs4 import BeautifulSoup

REQUEST_TIMEOUT = 10
MAX_LINKS_TO_CHECK = 50
MAX_DEPTH = 4
# Max page weight in bytes (5 MB)
MAX_PAGE_WEIGHT = 5 * 1024 * 1024


def fetch_page(url: str) -> tuple[str | None, int | None, float, int]:
    """Fetch page and return (html, status, load_time_seconds, content_length_bytes)."""
    try:
        start = time.time()
        response = requests.get(
            url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "BrandAuditBot/1.0 (read-only audit)"},
            allow_redirects=True,
        )
        load_time = time.time() - start
        content_length = len(response.content)

        if response.status_code == 200:
            return response.text, response.status_code, load_time, content_length
        return None, response.status_code, load_time, content_length

    except requests.RequestException:
        return None, None, 0, 0


def extract_internal_links(html: str, base_url: str) -> list[str]:
    """Extract unique internal links from HTML."""
    soup = BeautifulSoup(html, "html.parser")
    parsed_base = urlparse(base_url)
    links = set()

    for a_tag in soup.find_all("a", href=True):
        href = a_tag["href"].strip()

        # Skip non-HTTP links
        if any(href.startswith(p) for p in ["mailto:", "tel:", "javascript:", "#", "data:"]):
            continue

        # Resolve relative URLs
        full_url = urljoin(base_url, href)
        parsed = urlparse(full_url)

        # Only same-domain links
        if parsed.netloc != parsed_base.netloc:
            continue

        # Skip common non-content extensions
        path_lower = parsed.path.lower()
        if any(path_lower.endswith(ext) for ext in [".pdf", ".jpg", ".jpeg", ".png", ".gif", ".svg", ".css", ".js", ".xml", ".json"]):
            continue

        clean = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
        if clean.endswith("/"):
            clean = clean[:-1]
        if clean:
            links.add(clean)

    return list(links)


def check_broken_links(url: str, html: str) -> list[dict]:
    """Check internal links for broken (4xx/5xx) responses."""
    findings = []

    internal_links = extract_internal_links(html, url)
    if not internal_links:
        return findings

    broken_links = []
    checked = 0

    for link_url in internal_links[:MAX_LINKS_TO_CHECK]:
        checked += 1
        try:
            response = requests.head(
                link_url,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "BrandAuditBot/1.0 (read-only audit)"},
                allow_redirects=True,
            )
            if response.status_code >= 400:
                broken_links.append((link_url, response.status_code))
        except requests.RequestException:
            broken_links.append((link_url, "unreachable"))

    if broken_links:
        examples = broken_links[:5]
        examples_str = "; ".join(f"{url} (HTTP {status})" for url, status in examples)

        severity = "high" if len(broken_links) > 3 else "medium"
        findings.append({
            "title": f"{len(broken_links)} broken internal link(s) detected",
            "severity": severity,
            "evidence": (
                f"Checked {checked} internal links on {url}. "
                f"{len(broken_links)} returned errors. Examples: {examples_str}"
            ),
            "suggested_action": {
                "summary": (
                    f"Fix or remove {len(broken_links)} broken internal links. "
                    f"Broken links damage user experience and prevent AI crawlers from "
                    f"discovering content."
                ),
                "priority": severity,
            },
        })

    return findings


def check_click_depth(url: str, html: str) -> list[dict]:
    """Measure click depth using BFS from the homepage."""
    findings = []
    parsed_base = urlparse(url)

    visited = {url}
    # queue items: (url, depth)
    queue = deque()

    # Get links from homepage
    homepage_links = extract_internal_links(html, url)
    for link in homepage_links[:20]:  # Limit breadth
        if link not in visited:
            visited.add(link)
            queue.append((link, 1))

    deep_pages = []  # Pages requiring > 3 clicks
    max_depth_found = 0

    while queue and len(visited) < MAX_LINKS_TO_CHECK:
        current_url, depth = queue.popleft()
        max_depth_found = max(max_depth_found, depth)

        if depth > MAX_DEPTH:
            break

        if depth > 3:
            deep_pages.append((current_url, depth))
            continue

        # Fetch and discover deeper links
        try:
            response = requests.get(
                current_url,
                timeout=REQUEST_TIMEOUT,
                headers={"User-Agent": "BrandAuditBot/1.0 (read-only audit)"},
                allow_redirects=True,
            )
            if response.status_code == 200:
                sub_links = extract_internal_links(response.text, current_url)
                for link in sub_links[:10]:  # Limit breadth at each level
                    if link not in visited:
                        visited.add(link)
                        queue.append((link, depth + 1))
        except requests.RequestException:
            pass

    if deep_pages:
        examples = deep_pages[:3]
        examples_str = "; ".join(f"{url} (depth {d})" for url, d in examples)
        findings.append({
            "title": f"{len(deep_pages)} page(s) require more than 3 clicks to reach",
            "severity": "medium",
            "evidence": (
                f"BFS crawl from {url} found {len(deep_pages)} pages at click depth > 3. "
                f"Examples: {examples_str}. Deep pages are less likely to be discovered "
                f"by AI crawlers and users."
            ),
            "suggested_action": {
                "summary": "Improve internal linking so key pages are reachable within 3 clicks from the homepage. Add navigation links, breadcrumbs, or footer links.",
                "priority": "medium",
            },
        })

    return findings


def check_viewport_and_responsiveness(html: str, url: str, load_time: float, page_weight: int) -> list[dict]:
    """Check viewport meta tag and basic performance metrics."""
    findings = []
    soup = BeautifulSoup(html, "html.parser")

    # Check viewport meta tag
    viewport = soup.find("meta", attrs={"name": "viewport"})
    if not viewport:
        findings.append({
            "title": "Missing <meta name='viewport'> tag",
            "severity": "high",
            "evidence": (
                f"Page {url} has no viewport meta tag. Without it, the page will not "
                f"render correctly on mobile devices, leading to poor user experience "
                f"for mobile visitors."
            ),
            "suggested_action": {
                "summary": 'Add <meta name="viewport" content="width=device-width, initial-scale=1"> to the <head> section.',
                "priority": "high",
            },
        })
    else:
        content = viewport.get("content", "")
        if "width=device-width" not in content:
            findings.append({
                "title": "Viewport meta tag does not include width=device-width",
                "severity": "medium",
                "evidence": (
                    f"Viewport tag on {url} has content '{content}' but does not include "
                    f"'width=device-width', which is needed for proper mobile rendering."
                ),
                "suggested_action": {
                    "summary": 'Update viewport tag to: <meta name="viewport" content="width=device-width, initial-scale=1">',
                    "priority": "medium",
                },
            })

    # Check page load time
    if load_time > 5.0:
        findings.append({
            "title": f"Slow page load time ({load_time:.1f}s)",
            "severity": "high",
            "evidence": (
                f"Page {url} took {load_time:.1f} seconds to load (HTML response only). "
                f"Slow pages increase bounce rates and may cause AI crawlers to time out."
            ),
            "suggested_action": {
                "summary": "Optimize server response time. Target under 3 seconds for the initial HTML response. Check server configuration, database queries, and caching.",
                "priority": "high",
            },
        })
    elif load_time > 3.0:
        findings.append({
            "title": f"Moderate page load time ({load_time:.1f}s)",
            "severity": "medium",
            "evidence": f"Page {url} took {load_time:.1f} seconds to load. Recommended: under 3 seconds.",
            "suggested_action": {
                "summary": "Improve server response time to under 3 seconds through caching, CDN usage, or server optimization.",
                "priority": "medium",
            },
        })

    # Check page weight
    if page_weight > MAX_PAGE_WEIGHT:
        weight_mb = page_weight / (1024 * 1024)
        findings.append({
            "title": f"Excessive page weight ({weight_mb:.1f} MB)",
            "severity": "medium",
            "evidence": (
                f"Page {url} HTML response is {weight_mb:.1f} MB. Large pages slow down "
                f"rendering and increase data costs for mobile users."
            ),
            "suggested_action": {
                "summary": "Reduce page weight by optimizing images, minifying CSS/JS, and removing unused code. Target under 3 MB total page weight.",
                "priority": "medium",
            },
        })

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Check link health and mobile responsiveness."
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    args = parser.parse_args()

    url = args.url
    all_findings = []

    # Fetch homepage
    html, status, load_time, page_weight = fetch_page(url)
    if html is None:
        all_findings.append({
            "title": "Could not fetch page for link/responsiveness audit",
            "severity": "high",
            "evidence": f"Failed to fetch {url} (HTTP {status}).",
            "suggested_action": {
                "summary": "Ensure the page is accessible.",
                "priority": "high",
            },
        })
        print(json.dumps(all_findings, indent=2, ensure_ascii=False))
        return

    # Run checks
    all_findings.extend(check_broken_links(url, html))
    all_findings.extend(check_click_depth(url, html))
    all_findings.extend(check_viewport_and_responsiveness(html, url, load_time, page_weight))

    print(json.dumps(all_findings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
