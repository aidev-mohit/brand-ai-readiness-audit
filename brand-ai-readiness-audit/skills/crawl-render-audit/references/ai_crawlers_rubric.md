# AI Crawler Directives Reference

This reference lists the known AI crawlers and their `robots.txt` user-agent
tokens as of mid-2026. Use this to verify whether a site's `robots.txt` is
correctly guiding or blocking AI discovery agents.

## Known AI Crawler User-Agent Tokens

| AI System | User-Agent Token | Owner | Purpose |
|---|---|---|---|
| ChatGPT / SearchGPT | `GPTBot` | OpenAI | Training & real-time retrieval |
| ChatGPT Plugins | `ChatGPT-User` | OpenAI | Plugin web browsing |
| Claude | `ClaudeBot` | Anthropic | Training & retrieval |
| Claude Web Search | `ClaudeBot-SearchPreview` | Anthropic | Search grounding |
| Perplexity | `PerplexityBot` | Perplexity AI | Answer engine |
| Google Gemini | `Google-Extended` | Google | Gemini training |
| Google AI Overviews | `Googlebot` | Google | Search + AI Overviews |
| Cohere | `cohere-ai` | Cohere | RAG retrieval |
| Meta AI | `Meta-ExternalAgent` | Meta | Training & retrieval |
| Apple Intelligence | `Applebot-Extended` | Apple | Siri / Apple Intelligence |
| Microsoft Copilot | `bingbot` | Microsoft | Copilot grounding |
| Amazon Q | `Amazonbot` | Amazon | Alexa / Q retrieval |
| You.com | `YouBot` | You.com | Search retrieval |

## Recommended robots.txt Configuration

```text
# Allow all AI crawlers to index your site
User-agent: GPTBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: Applebot-Extended
Allow: /

# Block sensitive areas
User-agent: *
Disallow: /admin/
Disallow: /api/
Disallow: /internal/
```

## The llms.txt Standard (Emerging)

Some brands now publish an `/llms.txt` file at the site root (similar to
`robots.txt`) that provides a structured machine-readable summary of the brand,
its products, and key facts. This helps LLMs ground their answers in
authoritative brand-provided data.

Reference: https://llmstxt.org/
