# Schema.org Structured Data Requirements

This reference documents the minimum viable JSON-LD structured data every
brand website should include for optimal AI discoverability.

## Priority 1: Organization Schema (Homepage)

Every brand homepage MUST include an `Organization` schema:

```json
{
  "@context": "https://schema.org",
  "@type": "Organization",
  "name": "Your Brand Name",
  "url": "https://yourbrand.com",
  "logo": "https://yourbrand.com/logo.png",
  "description": "One-sentence brand description.",
  "sameAs": [
    "https://www.linkedin.com/company/yourbrand",
    "https://www.wikidata.org/wiki/Q123456",
    "https://twitter.com/yourbrand",
    "https://www.crunchbase.com/organization/yourbrand"
  ],
  "contactPoint": {
    "@type": "ContactPoint",
    "telephone": "+1-800-555-0199",
    "contactType": "customer service"
  }
}
```

### Required Properties

| Property | Why It Matters |
|---|---|
| `name` | Primary brand identifier for AI systems |
| `url` | Canonical website URL |
| `logo` | Visual identity in AI-generated summaries |
| `sameAs` | Links to authoritative external sources for entity disambiguation |

### Recommended Properties

| Property | Why It Matters |
|---|---|
| `description` | Concise brand summary for AI snippet generation |
| `contactPoint` | Enables AI assistants to provide customer support info |
| `foundingDate` | Establishes brand longevity and trust |
| `founder` | E-E-A-T trust signal |
| `numberOfEmployees` | Business scale indicator |

## Priority 2: WebSite Schema (Homepage)

```json
{
  "@context": "https://schema.org",
  "@type": "WebSite",
  "name": "Your Brand Name",
  "url": "https://yourbrand.com",
  "potentialAction": {
    "@type": "SearchAction",
    "target": "https://yourbrand.com/search?q={search_term_string}",
    "query-input": "required name=search_term_string"
  }
}
```

## Priority 3: Product / Offer Schema (Product Pages)

Required for e-commerce and SaaS brands:

| Property | Required | Recommended |
|---|---|---|
| `name` | ✅ | |
| `description` | | ✅ |
| `image` | | ✅ |
| `offers.price` | ✅ | |
| `offers.priceCurrency` | ✅ | |
| `offers.availability` | | ✅ |
| `brand` | | ✅ |
| `sku` | | ✅ |
| `aggregateRating` | | ✅ |

## Priority 4: FAQPage Schema

FAQ pages should use `FAQPage` schema to enable AI assistants to directly
cite Q&A pairs:

```json
{
  "@context": "https://schema.org",
  "@type": "FAQPage",
  "mainEntity": [
    {
      "@type": "Question",
      "name": "What is your return policy?",
      "acceptedAnswer": {
        "@type": "Answer",
        "text": "We offer 30-day hassle-free returns."
      }
    }
  ]
}
```

## Validation Tools

- **Google Rich Results Test**: https://search.google.com/test/rich-results
- **Schema.org Validator**: https://validator.schema.org/
