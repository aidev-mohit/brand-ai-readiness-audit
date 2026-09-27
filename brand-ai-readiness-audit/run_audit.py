#!/usr/bin/env python3
"""
run_audit.py — Brand AI-Readiness Audit CLI

A rich terminal interface with ASCII art, real-time progress indicators,
and structured findings reporting.

Usage:
    python3 run_audit.py --url "https://example.com"
    python3 run_audit.py --url "https://stripe.com" --output report.json
    python3 run_audit.py --url "https://example.com" --json
"""

import argparse
import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

ROOT_DIR = Path(__file__).resolve().parent
SKILLS_DIR = ROOT_DIR / "skills"

# ANSI Color Codes & Helpers
def rgb(r, g, b):
    return f"\033[38;2;{r};{g};{b}m"

RST = "\033[0m"
BOLD = "\033[1m"
DIM = "\033[2m"
ITALIC = "\033[3m"
CYAN = "\033[36m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
RED = "\033[31m"
MAGENTA = "\033[35m"
BLUE = "\033[34m"

def print_banner():
    """Prints the Elite Stack ASCII art logo with mountain peak, sun, flag, and perfectly aligned gradient typography."""
    import re
    ansi_regex = re.compile(r"\033\[[0-9;]*m")

    def vlen(text):
        return len(ansi_regex.sub("", text))

    def pad_visible(text, target_width):
        curr = vlen(text)
        return text + (" " * (target_width - curr)) if curr < target_width else text

    # Palette definition matching the Elite Stack artwork
    GOLD   = rgb(255, 225, 50)
    ORANGE = rgb(255, 130, 45)
    CORAL  = rgb(255, 75, 75)
    PINK   = rgb(240, 55, 135)
    PURPLE = rgb(170, 50, 215)
    INDIGO = rgb(80, 50, 190)
    DEEP   = rgb(25, 35, 120)
    BLUE   = rgb(40, 110, 240)
    CYAN   = rgb(0, 220, 255)

    # Sun
    SY = rgb(255, 230, 60)
    SO = rgb(255, 140, 40)
    SR = rgb(245, 65, 70)

    # Flag
    FY = rgb(255, 230, 50)
    FO = rgb(255, 110, 50)
    FR = rgb(240, 60, 70)

    # Clouds
    CL = rgb(0, 215, 250)

    # Mountain raw art
    raw_mtn = [
        f"           {FY}█{FO}██{FR}█{RST}",
        f"           {FY}█{FO}██{RST}",
        f"           {FY}█{RST}",
        f"  {SY}▄██▄{RST}     {GOLD}█{RST}   {CL}▄▄{RST}",
        f" {SY}██████{RST}   {GOLD}███{RST} {CL}▀▀▀▀{RST}",
        f" {SO}██████{RST}  {ORANGE}██{GOLD}█{ORANGE}██{RST}",
        f"  {SR}▀██▀{RST}  {CORAL}██{ORANGE}█{CORAL}██{RST}",
        f"       {PINK}██{DEEP}█{PINK}██{RST}",
        f"      {PURPLE}██{DEEP}███{PURPLE}██{RST}",
        f"{CYAN}▄{RST}    {INDIGO}██{DEEP}█████{INDIGO}██{RST}   {CYAN}▄{RST}",
        f"{CYAN}██▄{BLUE}══{BLUE}██{DEEP}██{BLUE}█{DEEP}██{BLUE}██{BLUE}══{CYAN}▄██{RST}",
    ]

    MTN_WIDTH = 25
    mtn_padded = [pad_visible(row, MTN_WIDTH) for row in raw_mtn]

    # Typography letters colors (horizontal rainbow gradient)
    c = [
        rgb(0, 235, 255),   # E
        rgb(0, 195, 250),   # L
        rgb(50, 145, 255),  # I
        rgb(120, 85, 255),  # T
        rgb(180, 65, 245),  # E
        rgb(245, 60, 145),  # S
        rgb(255, 95, 85),   # T
        rgb(255, 150, 55),  # A
        rgb(255, 200, 50),  # C
        rgb(255, 235, 55),  # K
    ]

    # 5x3 / 5x5 uniform pixel font for each letter
    letters = [
        # E (3 wide)
        ["███", "█  ", "███", "█  ", "███"],
        # L (3 wide)
        ["█  ", "█  ", "█  ", "█  ", "███"],
        # I (3 wide)
        ["███", " █ ", " █ ", " █ ", "███"],
        # T (5 wide)
        ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
        # E (3 wide)
        ["███", "█  ", "███", "█  ", "███"],
        # S (3 wide)
        ["███", "█  ", "███", "  █", "███"],
        # T (5 wide)
        ["█████", "  █  ", "  █  ", "  █  ", "  █  "],
        # A (3 wide)
        ["███", "█ █", "███", "█ █", "█ █"],
        # C (3 wide)
        ["███", "█  ", "█  ", "█  ", "███"],
        # K (4 wide)
        ["█  █", "█ █ ", "██  ", "█ █ ", "█  █"],
    ]

    txt_rows = []
    for row_idx in range(5):
        elite = " ".join(f"{c[j]}{letters[j][row_idx]}{RST}" for j in range(5))
        stack = " ".join(f"{c[5 + j]}{letters[5 + j][row_idx]}{RST}" for j in range(5))
        txt_rows.append(f"{elite}   {stack}")

    print()
    for i in range(len(mtn_padded)):
        m = mtn_padded[i]
        if 3 <= i <= 7:
            t = txt_rows[i - 3]
            print(f"  {m}    {t}")
        else:
            print(f"  {m}")
    print()

    # Dynamic gradient divider line
    grad_line = ""
    steps = [
        (0, 235, 255), (0, 195, 250), (50, 145, 255), (120, 85, 255),
        (180, 65, 245), (245, 60, 145), (255, 95, 85), (255, 150, 55),
        (255, 200, 50), (255, 235, 55)
    ]
    for seg_idx in range(len(steps) - 1):
        c1 = steps[seg_idx]
        c2 = steps[seg_idx + 1]
        for step in range(8):
            r = int(c1[0] + (c2[0] - c1[0]) * (step / 8))
            g = int(c1[1] + (c2[1] - c1[1]) * (step / 8))
            b = int(c1[2] + (c2[2] - c1[2]) * (step / 8))
            grad_line += f"{rgb(r, g, b)}━{RST}"

    print(f"  {BOLD}Elite Stack{RST} · {DIM}Brand AI-Readiness Audit System v1.0.0{RST}")
    print(f"  {DIM}Autonomous LLM Knowledge Graph & Search Crawlability Inspector{RST}")
    print(f"  {grad_line}")
    print()


def run_script(script_path: Path, url: str) -> list:
    """Run an individual audit script and return parsed JSON findings list."""
    if not script_path.exists():
        return []

    cmd = [sys.executable, str(script_path), "--url", url]
    try:
        res = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=45,
            cwd=str(ROOT_DIR),
        )
        output = res.stdout.strip()
        if not output:
            return []
        try:
            parsed = json.loads(output)
            if isinstance(parsed, list):
                return parsed
            elif isinstance(parsed, dict) and "findings" in parsed:
                return parsed["findings"]
            return []
        except json.JSONDecodeError:
            return []
    except Exception:
        return []


def print_step(icon: str, color: str, title: str, status: str = "done"):
    bullet = f"{color}{icon}{RST}"
    status_str = f"{DIM}(complete){RST}" if status == "done" else f"{YELLOW}(running...){RST}"
    print(f"  {bullet}  {BOLD}{title}{RST} {status_str}")


def render_findings_ui(report: dict):
    """Renders clean, styled terminal cards for the audit report."""
    summary = report.get("summary", {})
    total = summary.get("total_findings", 0)
    crit = summary.get("critical", 0)
    high = summary.get("high", 0)
    med = summary.get("medium", 0)
    site = report.get("site", "target")
    audited_at = report.get("audited_at", "")

    # Summary Card
    print()
    print(f"  {BOLD}╭── Audit Summary: {CYAN}{site}{RST} {BOLD}{'─' * max(2, 40 - len(site))}╮{RST}")
    print(f"  {BOLD}│{RST}  Target URL:  {BOLD}{site}{RST}")
    print(f"  {BOLD}│{RST}  Timestamp:   {DIM}{audited_at}{RST}")
    print(f"  {BOLD}│{RST}  Findings:    {BOLD}{total} total{RST}  "
          f"({RED}● {crit} Critical{RST}  {YELLOW}● {high} High{RST}  {CYAN}● {med} Medium{RST})")
    print(f"  {BOLD}╰{'─' * 56}╯{RST}")
    print()

    # Findings Cards
    findings = report.get("findings", [])
    if not findings:
        print(f"  {GREEN}✔ No issues detected. Brand is 100% AI-Ready!{RST}\n")
        return

    print(f"  {BOLD}Detailed Findings:{RST}\n")
    for f in findings:
        fid = f.get("id", "F-???")
        title = f.get("title", "Finding")
        severity = f.get("severity", "medium").lower()

        if severity == "critical":
            badge = f"\033[41;97;1m CRITICAL \033[0m"
            color = RED
        elif severity == "high":
            badge = f"\033[43;30;1m   HIGH   \033[0m"
            color = YELLOW
        else:
            badge = f"\033[46;30;1m  MEDIUM  \033[0m"
            color = CYAN

        print(f"  {badge}  {BOLD}{color}[{fid}]{RST} {BOLD}{title}{RST}")
        
        # Evidence snippet
        evidence = f.get("evidence", "").strip()
        if evidence:
            lines = evidence.split("\n")
            for i, line in enumerate(lines[:3]):
                prefix = "     ├─ Evidence: " if i == 0 else "     │            "
                print(f"  {DIM}{prefix}{line}{RST}")
            if len(lines) > 3:
                print(f"  {DIM}     │            ... ({len(lines) - 3} more lines){RST}")

        # Action snippet
        action = f.get("suggested_action", {})
        if isinstance(action, dict):
            summary_text = action.get("summary", "")
        else:
            summary_text = str(action)
        
        if summary_text:
            first_line = summary_text.split("\n")[0]
            print(f"  {GREEN}     └─ Recommended Fix: {RST}{first_line[:90]}")
        print()

    # Proactive Strategic Recommendations (Beyond Defects)
    proactive = report.get("proactive_recommendations", [])
    if proactive:
        print(f"  {BOLD}{MAGENTA}✨ Proactive Strategic Improvements (Beyond Detected Defects):{RST}\n")
        for rec in proactive:
            area = rec.get("area", "Opportunity")
            rtitle = rec.get("title", "")
            rationale = rec.get("rationale", "")
            action = rec.get("suggested_action", "")
            print(f"  {BOLD}{MAGENTA}● [{area}]{RST} {BOLD}{rtitle}{RST}")
            if rationale:
                print(f"  {DIM}     ├─ Rationale: {rationale}{RST}")
            if action:
                print(f"  {GREEN}     └─ Suggested Proactive Step: {RST}{action}")
            print()


def main():
    parser = argparse.ArgumentParser(
        description="Brand AI-Readiness Audit — Autonomous Multi-Agent Inspector"
    )
    parser.add_argument("--url", required=True, help="Target website URL to audit")
    parser.add_argument("--output", help="Save the JSON report to file")
    parser.add_argument("--json", action="store_true", help="Output raw JSON only")
    args = parser.parse_args()

    url = args.url

    if not args.json:
        print_banner()
        print(f"  {DIM}Auditing target:{RST} {BOLD}{url}{RST}\n")

    # 1. Crawl & Render Audit
    if not args.json:
        print_step("◐", CYAN, "Crawl & Render Audit", "running")
    t0 = time.time()
    crawl_findings = []
    crawl_findings.extend(run_script(SKILLS_DIR / "crawl-render-audit/scripts/check_robots.py", url))
    crawl_findings.extend(run_script(SKILLS_DIR / "crawl-render-audit/scripts/check_js_render_gap.py", url))
    if not args.json:
        print(f"\033[A\r", end="")
        print_step("✔", GREEN, f"Crawl & Render Audit  {DIM}({len(crawl_findings)} finding(s)){RST}")

    # 2. Structured Data Audit
    if not args.json:
        print_step("◐", CYAN, "Structured Data & Fact Graph Audit", "running")
    struct_findings = []
    struct_findings.extend(run_script(SKILLS_DIR / "structured-data-audit/scripts/extract_jsonld.py", url))
    struct_findings.extend(run_script(SKILLS_DIR / "structured-data-audit/scripts/check_plain_text_facts.py", url))
    if not args.json:
        print(f"\033[A\r", end="")
        print_step("✔", GREEN, f"Structured Data & Fact Graph Audit  {DIM}({len(struct_findings)} finding(s)){RST}")

    # 3. Corroboration & Entity Audit
    if not args.json:
        print_step("◐", CYAN, "Corroboration & Entity Disambiguation", "running")
    corr_findings = []
    corr_findings.extend(run_script(SKILLS_DIR / "corroboration-entity-audit/scripts/check_entity_disambiguation.py", url))
    corr_findings.extend(run_script(SKILLS_DIR / "corroboration-entity-audit/scripts/check_corroboration.py", url))
    if not args.json:
        print(f"\033[A\r", end="")
        print_step("✔", GREEN, f"Corroboration & Entity Disambiguation  {DIM}({len(corr_findings)} finding(s)){RST}")

    # 4. Engagement Audit
    if not args.json:
        print_step("◐", CYAN, "Engagement & Technical Integrity Audit", "running")
    engage_findings = []
    engage_findings.extend(run_script(SKILLS_DIR / "engagement-audit/scripts/check_orientation.py", url))
    engage_findings.extend(run_script(SKILLS_DIR / "engagement-audit/scripts/check_links_and_responsiveness.py", url))
    if not args.json:
        print(f"\033[A\r", end="")
        print_step("✔", GREEN, f"Engagement & Technical Integrity Audit  {DIM}({len(engage_findings)} finding(s)){RST}")

    # Merge findings
    merge_script = SKILLS_DIR / "audit-orchestrator/scripts/merge_findings.py"
    with tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f_crawl, \
         tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f_struct, \
         tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f_corr, \
         tempfile.NamedTemporaryFile("w+", suffix=".json", delete=False) as f_engage:

        json.dump(crawl_findings, f_crawl)
        f_crawl.flush()
        json.dump(struct_findings, f_struct)
        f_struct.flush()
        json.dump(corr_findings, f_corr)
        f_corr.flush()
        json.dump(engage_findings, f_engage)
        f_engage.flush()

        tmp_crawl = f_crawl.name
        tmp_struct = f_struct.name
        tmp_corr = f_corr.name
        tmp_engage = f_engage.name

    try:
        cmd = [
            sys.executable,
            str(merge_script),
            "--url", url,
            "--crawl-file", tmp_crawl,
            "--structured-file", tmp_struct,
            "--corroboration-file", tmp_corr,
            "--engagement-file", tmp_engage,
        ]
        res = subprocess.run(cmd, stdout=subprocess.PIPE, text=True)
        report_json_str = res.stdout.strip()
        report_data = json.loads(report_json_str)
    except Exception as e:
        report_data = {
            "site": url,
            "error": str(e),
            "summary": {"total_findings": 0, "critical": 0, "high": 0, "medium": 0},
            "findings": []
        }
        report_json_str = json.dumps(report_data, indent=2)
    finally:
        for p in (tmp_crawl, tmp_struct, tmp_corr, tmp_engage):
            try:
                os.remove(p)
            except OSError:
                pass

    # Save to file if requested
    if args.output:
        with open(args.output, "w", encoding="utf-8") as f:
            f.write(report_json_str)

    # Output Presentation
    if args.json:
        print(report_json_str)
    else:
        render_findings_ui(report_data)
        if args.output:
            print(f"  {GREEN}✔ Saved full JSON report to:{RST} {BOLD}{args.output}{RST}\n")
        else:
            print(f"  {DIM}Tip: Run with --output report.json or --json to export raw data.{RST}\n")


if __name__ == "__main__":
    main()
