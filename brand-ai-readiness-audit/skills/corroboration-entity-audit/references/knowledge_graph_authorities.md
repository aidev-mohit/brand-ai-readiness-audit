# Knowledge Graph Authorities Reference

This reference documents the external authoritative sources that AI systems
use to disambiguate and verify brand entities. The `sameAs` property in
JSON-LD links a brand to these sources.

## Tier 1: Critical Authorities

These sources are directly consumed by major LLMs and search engines:

| Source | URL Pattern | Why It Matters |
|---|---|---|
| **Wikidata** | `https://www.wikidata.org/wiki/Q{id}` | Google Knowledge Graph, ChatGPT, Claude, and Perplexity all use Wikidata as a primary entity resolution source. |
| **Wikipedia** | `https://en.wikipedia.org/wiki/{title}` | The single most-cited source in LLM training data. Having a Wikipedia page dramatically increases accurate AI representation. |
| **LinkedIn** | `https://www.linkedin.com/company/{slug}` | Primary professional identity. Used by AI for company verification. |

## Tier 2: Strong Authorities

| Source | URL Pattern | Why It Matters |
|---|---|---|
| **Crunchbase** | `https://www.crunchbase.com/organization/{slug}` | Funding, founding date, and team data. Frequently cited by AI for startup info. |
| **Google Knowledge Panel** | (Auto-generated from Wikidata + sameAs) | The sidebar panel in Google Search — powered by the entity graph. |
| **Bloomberg** | `https://www.bloomberg.com/profile/company/{ticker}` | Financial and corporate data for public companies. |

## Tier 3: Domain-Specific Authorities

| Source | URL Pattern | Use Case |
|---|---|---|
| **GitHub** | `https://github.com/{org}` | Developer tools / open-source brands |
| **Glassdoor** | `https://www.glassdoor.com/Overview/{slug}` | Employer branding |
| **App Store** | `https://apps.apple.com/app/{id}` | Mobile app brands |
| **Google Play** | `https://play.google.com/store/apps/details?id={pkg}` | Mobile app brands |
| **X (Twitter)** | `https://x.com/{handle}` | Social presence verification |
| **Facebook** | `https://www.facebook.com/{page}` | Social presence verification |

## How sameAs Prevents AI Hallucination

Without `sameAs` links, an AI assistant cannot distinguish between:
- **Apple Inc.** (the tech company) vs **Apple Records** (the Beatles' label)
- **Amazon** (the retailer) vs **Amazon River** (the waterway)
- **Mercury** (the planet) vs **Mercury Insurance** vs **Mercury Drug**

When a brand includes `sameAs` links to Wikidata and LinkedIn, the AI can
resolve the entity to the correct Knowledge Graph node with high confidence.

## Creating a Wikidata Entity

If your brand does not have a Wikidata entry:

1. Go to https://www.wikidata.org/wiki/Special:NewItem
2. Fill in: Label (brand name), Description (e.g., "American SaaS company"),
   and add properties:
   - `P856` (official website URL)
   - `P571` (inception / founding date)
   - `P159` (headquarters location)
   - `P112` (founder)
   - `P452` (industry)
3. Add your brand's Wikipedia, LinkedIn, and Crunchbase URLs as identifiers.
