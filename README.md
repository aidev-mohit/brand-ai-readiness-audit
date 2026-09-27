# Brand AI-Readiness Audit

> **Adobe University Hackathon 2026 — Team Elite Stack**  
> CLI-based Agent Skill Marketplace for auditing a website's AI-readiness.

## Overview

**Brand AI-Readiness Audit** is an Agent Skill Marketplace that evaluates how well a brand website can be discovered, crawled, interpreted, verified, and used by AI-powered search and assistant systems.

The project is intentionally **CLI-first**. The agent interaction itself is the interface: a target URL is supplied, the audit orchestrator runs the marketplace skills, and the system produces an evidence-backed JSON report with prioritized findings and recommended fixes.

The marketplace is composed of **5 Agent Skills**:

1. `audit-orchestrator` — entrypoint and report merger
2. `crawl-render-audit` — AI crawler access and rendering checks
3. `structured-data-audit` — JSON-LD, Schema.org, and fact readability checks
4. `corroboration-entity-audit` — external corroboration and entity disambiguation
5. `engagement-audit` — orientation, links, click depth, and mobile readiness

---

## 🎯 Problem

AI assistants increasingly rely on websites as sources of information. A website can be technically online and still be difficult for AI systems to:

- discover,
- crawl,
- render,
- understand,
- identify as the correct entity,
- verify,
- and confidently use in an answer.

Traditional website audits often focus on conventional SEO and page-level technical issues. This project focuses specifically on **AI-readiness signals** and converts those signals into actionable findings.

---

## 💡 Solution

The system takes a website URL and runs a sequence of specialized audit skills.

```text
Target Website URL
        │
        ▼
┌──────────────────────┐
│  Audit Orchestrator  │
└──────────┬───────────┘
           │
           ├───────────────────────┐
           │                       │
           ▼                       ▼
┌────────────────────┐   ┌──────────────────────┐
│ Crawl & Render     │   │ Structured Data      │
│ Audit              │   │ Audit                │
└─────────┬──────────┘   └──────────┬───────────┘
          │                         │
          └────────────┬────────────┘
                       │
          ┌────────────┴────────────┐
          ▼                         ▼
┌──────────────────────┐   ┌──────────────────────┐
│ Corroboration &      │   │ Engagement &          │
│ Entity Audit         │   │ Technical Integrity   │
└──────────┬───────────┘   └──────────┬───────────┘
           │                          │
           └────────────┬─────────────┘
                        ▼
              ┌───────────────────┐
              │ Findings Merger   │
              └─────────┬─────────┘
                        ▼
              ┌───────────────────┐
              │ JSON Audit Report │
              └───────────────────┘
```

Each finding contains evidence and a suggested action so the output is not just a score.

---

## 🧩 Agent Skills

### 1. Audit Orchestrator

**Path:**

```text
skills/audit-orchestrator/
```

This is the marketplace entrypoint.

It sequentially invokes the four specialized audit skills, collects their JSON findings, normalizes finding IDs, calculates severity counts, and emits the final report.

---

### 2. Crawl & Render Audit

**Path:**

```text
skills/crawl-render-audit/
```

Checks whether automated AI/search crawlers can reach and read the website.

It evaluates:

- `robots.txt`
- AI crawler access
- GPTBot
- ClaudeBot
- PerplexityBot
- Google-Extended
- JavaScript rendering gaps
- raw HTML vs rendered DOM content
- HTTP status and redirect issues

The rendering check compares content available without JavaScript against content available after browser rendering.

---

### 3. Structured Data Audit

**Path:**

```text
skills/structured-data-audit/
```

Evaluates whether important website information is machine-readable.

It checks:

- JSON-LD
- Schema.org types
- Organization data
- Product data
- Offer data
- FAQPage
- WebSite
- BreadcrumbList
- required structured-data properties
- coverage across internal pages
- important facts stated in visible text
- information potentially locked inside images
- image `alt` text

---

### 4. Corroboration & Entity Audit

**Path:**

```text
skills/corroboration-entity-audit/
```

Evaluates whether important factual claims can be independently corroborated and whether the brand can be distinguished from similarly named entities.

It checks:

- factual claims
- external corroboration
- Organization identity
- `sameAs` links
- Wikidata
- Wikipedia
- LinkedIn
- social profiles
- potential brand-name collision risk

---

### 5. Engagement Audit

**Path:**

```text
skills/engagement-audit/
```

Evaluates the experience of a user who arrives on the website from an AI assistant or search result.

It checks:

- page title
- meta description
- H1
- above-the-fold orientation
- value proposition
- calls to action
- internal links
- broken links
- click depth
- viewport/mobile configuration
- basic page load and page-weight signals

---

## 🔄 Audit Flow

A normal audit follows this flow:

```text
1. Receive target URL
        ↓
2. Run Crawl & Render Audit
        ↓
3. Run Structured Data Audit
        ↓
4. Run Corroboration & Entity Audit
        ↓
5. Run Engagement Audit
        ↓
6. Merge findings
        ↓
7. Assign normalized IDs
        ↓
8. Calculate severity summary
        ↓
9. Emit final JSON report
```

The orchestrator is the only skill intended to be invoked directly.

---

## 📁 Project Structure

```text
brand-ai-readiness-audit/
│
├── marketplace.json
├── run_audit.py
├── requirements.txt
├── README.md
├── REPLAY_EliteStack.txt
├── report.json
│
└── skills/
    │
    ├── audit-orchestrator/
    │   ├── SKILL.md
    │   ├── references/
    │   │   └── scoring_and_severity_rubric.md
    │   └── scripts/
    │       └── merge_findings.py
    │
    ├── crawl-render-audit/
    │   ├── SKILL.md
    │   ├── references/
    │   │   └── ai_crawlers_rubric.md
    │   └── scripts/
    │       ├── check_robots.py
    │       └── check_js_render_gap.py
    │
    ├── structured-data-audit/
    │   ├── SKILL.md
    │   ├── references/
    │   │   └── schema_requirements.md
    │   └── scripts/
    │       ├── extract_jsonld.py
    │       └── check_plain_text_facts.py
    │
    ├── corroboration-entity-audit/
    │   ├── SKILL.md
    │   ├── references/
    │   │   └── knowledge_graph_authorities.md
    │   └── scripts/
    │       ├── check_corroboration.py
    │       └── check_entity_disambiguation.py
    │
    └── engagement-audit/
        ├── SKILL.md
        ├── references/
        │   └── on_site_orientation_heuristics.md
        └── scripts/
            ├── check_links_and_responsiveness.py
            └── check_orientation.py
```

---

## ⚙️ Requirements

- Python **3.10+**
- Internet access for live website audits
- Chromium for Playwright-based rendering

Python dependencies are listed in:

```text
requirements.txt
```

Current dependencies include:

```text
requests
beautifulsoup4
playwright
extruct
lxml
```

---

## 🚀 Installation

Clone the repository:

```bash
git clone https://github.com/aidev-mohit/brand-ai-readiness-audit.git
cd brand-ai-readiness-audit
```

Install Python dependencies:

```bash
pip install -r requirements.txt
```

Install the Playwright Chromium browser:

```bash
playwright install chromium
```

### Windows — Git Bash

Create a virtual environment:

```bash
py -m venv .venv
```

Activate it:

```bash
source .venv/Scripts/activate
```

Then install dependencies:

```bash
pip install -r requirements.txt
playwright install chromium
```

### Windows — PowerShell

```powershell
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
playwright install chromium
```

---

## ▶️ Run the CLI Audit

Run an audit against a website:

```bash
python run_audit.py --url "https://example.com"
```

Save the final JSON report:

```bash
python run_audit.py --url "https://stripe.com" --output report.json
```

Output JSON directly:

```bash
python run_audit.py --url "https://stripe.com" --json
```

The CLI displays the audit stages and then renders a readable findings summary.

---

## 🧪 Example CLI Session

```text
Elite Stack · Brand AI-Readiness Audit System

Auditing target: https://stripe.com

✔ Crawl & Render Audit
✔ Structured Data & Fact Graph Audit
✔ Corroboration & Entity Disambiguation
✔ Engagement & Technical Integrity Audit

Audit Summary
Target URL: https://stripe.com
Findings: 6 total
0 Critical · 3 High · 3 Medium

Detailed Findings:

[HIGH] F-001 Majority of pages lack JSON-LD structured data
Evidence:
Only 2/11 crawled pages contain JSON-LD structured data.

Recommended Fix:
Extend JSON-LD structured data coverage to all key pages.

[HIGH] F-002 Missing Organization/LocalBusiness structured data
Evidence:
No Organization or LocalBusiness JSON-LD type detected.

Recommended Fix:
Add Organization JSON-LD with name, URL, logo, and sameAs.

...
```

The exact findings depend on the website being audited.

---

## 📊 Report Format

The orchestrator produces a JSON report similar to:

```json
{
  "site": "example.com",
  "audited_at": "2026-09-27T10:23:28Z",
  "summary": {
    "total_findings": 6,
    "critical": 0,
    "high": 3,
    "medium": 3
  },
  "findings": [
    {
      "id": "F-001",
      "title": "Example finding",
      "severity": "high",
      "evidence": "Observed evidence...",
      "suggested_action": {
        "summary": "Recommended fix...",
        "priority": "high"
      }
    }
  ]
}
```

### Finding Model

Each finding contains:

| Field | Description |
|---|---|
| `id` | Normalized finding identifier |
| `title` | Short description of the issue |
| `severity` | `critical`, `high`, or `medium` |
| `evidence` | Observed website evidence |
| `suggested_action` | Recommended remediation |
| `priority` | Priority of the recommended action |

---

## 🔎 Evidence-Backed Findings

The project is designed around the principle:

```text
Observed Signal
      ↓
Evidence
      ↓
Finding
      ↓
Recommended Action
```

For example:

```text
Observed:
Only 2/11 crawled pages contain JSON-LD.

        ↓

Finding:
Majority of pages lack structured data.

        ↓

Action:
Extend structured-data coverage to key pages.
```

This makes the audit output explainable and useful for remediation.

---

## 🛡️ Project Constraints

The marketplace follows these implementation constraints:

- **Read-only:** audit skills do not modify the live website.
- **Robots-aware:** live HTTP requests respect the project's robots.txt requirement.
- **Deterministic:** the same input should produce reproducible audit signals.
- **Runtime target:** less than 5 minutes per website audit.
- **Package target:** no bundled model weights and package size target below 50 MB.

---

## 🤖 Agent / IDE Usage

The marketplace can also be used through an agent harness such as Codex or an IDE agent.

Open the project directory and instruct the agent to use the marketplace entrypoint:

```text
Read marketplace.json and run the audit-orchestrator skill on https://stripe.com
```

The agent should use:

```text
skills/audit-orchestrator/SKILL.md
```

as the entrypoint and allow the orchestrator to compose the four helper skills.

---

## 🔁 Reproducibility

The project includes:

```text
REPLAY_EliteStack.txt
```

which documents the intended replay environment, test URLs, setup commands, CLI invocation, and expected output.

Typical replay:

```bash
git clone <repo-url>
cd brand-ai-readiness-audit
pip install -r requirements.txt
playwright install chromium
python run_audit.py --url "https://stripe.com" --output report.json
```

Expected output:

```text
report.json
```

---

## 📦 Marketplace Manifest

The marketplace is described by:

```text
marketplace.json
```

The manifest identifies:

- marketplace name
- version
- description
- entrypoint skill
- helper skills

Current marketplace version:

```text
1.0.0
```

---

## 🏆 Hackathon Context

**Team:** Elite Stack

**Project:** Brand AI-Readiness Audit

**Event:** Adobe University Hackathon 2026

**Round:** Prototype / Agent Skill Marketplace

The prototype is designed to demonstrate the audit through an **AI-agent/CLI interaction rather than a graphical web application**.

---

## 🔮 Future Improvements

Potential extensions include:

- richer multi-page crawling
- additional AI crawler policies
- broader structured-data validation
- stronger external claim corroboration
- more detailed entity-graph analysis
- historical freshness tracking
- additional remediation templates
- export formats beyond JSON

These are extensions to the current marketplace and are not required for the core audit flow.

---

## 👥 Team

**Elite Stack**

Built for the Adobe Hackathon.

---

## 📄 License
NA
