#!/usr/bin/env python3
"""
check_robots.py — Checks whether a website's robots.txt blocks AI search
crawlers (GPTBot, ClaudeBot, PerplexityBot, Google-Extended).

Usage:
    python3 check_robots.py --url "https://example.com"

Output:
    A JSON array of findings printed to stdout.
"""

import argparse
import json
import sys
from urllib.parse import urljoin, urlparse
from urllib.robotparser import RobotFileParser

import requests

# AI crawler user-agents to check
AI_USER_AGENTS = [
    "GPTBot",
    "ClaudeBot",
    "PerplexityBot",
    "Google-Extended",
]

# Request timeout in seconds
REQUEST_TIMEOUT = 15


def fetch_robots_txt(url: str) -> tuple[str | None, int | None]:
    """Fetch robots.txt content from the target site.

    Returns:
        Tuple of (robots_txt_content, http_status_code).
        Content is None if the request failed entirely.
    """
    parsed = urlparse(url)
    robots_url = f"{parsed.scheme}://{parsed.netloc}/robots.txt"

    try:
        response = requests.get(
            robots_url,
            timeout=REQUEST_TIMEOUT,
            headers={"User-Agent": "BrandAuditBot/1.0 (read-only audit)"},
            allow_redirects=True,
        )
        return response.text, response.status_code
    except requests.RequestException as e:
        print(f"Warning: Could not fetch {robots_url}: {e}", file=sys.stderr)
        return None, None


def check_ai_blocks(url: str, robots_content: str) -> list[dict]:
    """Check which AI user-agents are blocked by robots.txt.

    Returns:
        List of finding dicts for blocked agents.
    """
    findings = []
    blocked_agents = []
    block_details = []

    parsed = urlparse(url)
    base_url = f"{parsed.scheme}://{parsed.netloc}"

    for agent in AI_USER_AGENTS:
        rp = RobotFileParser()
        rp.parse(robots_content.splitlines())

        # Check if the agent is allowed to fetch the main URL path
        test_paths = ["/", parsed.path or "/"]
        is_blocked = False

        for path in test_paths:
            full_url = urljoin(base_url, path)
            if not rp.can_fetch(agent, full_url):
                is_blocked = True
                break

        if is_blocked:
            blocked_agents.append(agent)

    if blocked_agents:
        # Extract the specific rules from robots.txt for evidence
        relevant_lines = []
        lines = robots_content.splitlines()
        current_agent_section = False
        for line in lines:
            stripped = line.strip().lower()
            if stripped.startswith("user-agent:"):
                agent_name = stripped.split(":", 1)[1].strip()
                # Check if this section applies to any blocked agent or all agents
                current_agent_section = (
                    agent_name == "*"
                    or any(a.lower() == agent_name for a in blocked_agents)
                )
            elif current_agent_section and stripped.startswith("disallow:"):
                relevant_lines.append(line.strip())

        evidence_rules = "; ".join(relevant_lines[:5]) if relevant_lines else "Disallow rules detected"

        if len(blocked_agents) == len(AI_USER_AGENTS):
            severity = "critical"
            title = "All major AI search crawlers blocked in robots.txt"
        elif len(blocked_agents) >= 2:
            severity = "critical"
            title = f"{len(blocked_agents)}/{len(AI_USER_AGENTS)} AI search crawlers blocked in robots.txt"
        else:
            severity = "high"
            title = f"AI search crawler {blocked_agents[0]} blocked in robots.txt"

        agents_list = ", ".join(blocked_agents)
        findings.append({
            "title": title,
            "severity": severity,
            "evidence": (
                f"robots.txt blocks the following AI user-agents: [{agents_list}]. "
                f"Relevant rules: {evidence_rules}"
            ),
            "suggested_action": {
                "summary": (
                    f"Update robots.txt to allow AI crawlers. Add explicit 'Allow: /' rules "
                    f"for: {agents_list}. Example:\n"
                    + "\n".join(f"User-agent: {a}\nAllow: /\n" for a in blocked_agents)
                ),
                "priority": severity,
            },
        })

    return findings


def check_robots_txt_missing(robots_content: str | None, status_code: int | None) -> list[dict]:
    """Check if robots.txt is entirely missing or returns an error."""
    findings = []

    if robots_content is None:
        findings.append({
            "title": "robots.txt is unreachable",
            "severity": "medium",
            "evidence": "Could not fetch robots.txt — the request failed entirely (connection error or timeout).",
            "suggested_action": {
                "summary": "Ensure robots.txt is accessible at the site root. A missing robots.txt means AI crawlers will assume full access, but it also means you cannot provide crawl guidance.",
                "priority": "medium",
            },
        })
    elif status_code and status_code >= 400:
        findings.append({
            "title": f"robots.txt returns HTTP {status_code}",
            "severity": "medium",
            "evidence": f"robots.txt returned HTTP status {status_code} instead of 200.",
            "suggested_action": {
                "summary": "Create a valid robots.txt file at the site root. Without it, you cannot guide AI crawlers on which pages to prioritize or avoid.",
                "priority": "medium",
            },
        })

    return findings


def main():
    parser = argparse.ArgumentParser(
        description="Check robots.txt for AI crawler blocks."
    )
    parser.add_argument("--url", required=True, help="Target website URL")
    args = parser.parse_args()

    url = args.url
    findings = []

    # Fetch robots.txt
    robots_content, status_code = fetch_robots_txt(url)

    # Check if robots.txt is missing/broken
    findings.extend(check_robots_txt_missing(robots_content, status_code))

    # If we got content, check for AI blocks
    if robots_content and status_code == 200:
        findings.extend(check_ai_blocks(url, robots_content))

    # Output findings as JSON
    print(json.dumps(findings, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
