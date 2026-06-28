# Agentic SEO Automation Skills Framework

A modular, reusable framework of **AI Skills** designed to be executed by agentic AI coders (like Gemini, Claude, or custom LLM-based agents) to manage, scale, and automate **seo optimization**, content generation, image asset optimization, and social media distribution.

Whether you are looking for an automated **seo specialist** or a virtual **seo consultant** to handle your **seo website** tasks, this framework is designed to automate complex **seo search engine optimization** workflows.

## Why Use This Framework?
If you are running an **seo marketing** campaign, managing **local seo** for small businesses, or looking to scale operations like top-tier **seo companies**, this agentic framework provides modular capabilities to act as a complete **seo** toolkit:

* **Automate SEO Website Audits**: Find link leaks and optimize internal links.
* **On-Page SEO Optimization**: Automatically update headers, metadata, and JSON-LD markup.
* **Local SEO Automation**: Generate highly relevant local context, content, and schema markup (saving you from searching for an "**seo company near me**" to do repetitive edits).
* **Scale Content Marketing**: Let AI agents act as your digital **seo specialist**, generating briefs, LSI keywords, and search-optimized HTML pages.

## Framework Structure

This repository organizes automation tools as self-contained "Skills". Each skill has a `SKILL.md` instruction manual that explains to the AI how to use and run the associated Python scripts located in the `scripts/` directory.

```
seo-agentic-skills/
├── README.md                      # Framework entrypoint and overview
└── skills/
    ├── image-optimization-skill/  # Generates stock-style images and converts them to WebP
    ├── social-publishing-skill/   # Crafts captions and publishes posts to FB/Instagram/Pinterest
    ├── site-link-audit-skill/     # Audits internal and external links for PageRank weight leakages
    ├── seo-content-generator-skill/ # Generates briefs, LSI keywords, and target HTML articles
    └── seo-site-maintenance-skill/ # Updates CTAs, footer links, JSON-LD breadcrumbs, and heals links
```

## How to use this framework in your AI environment

1. **Scan Skills**: Instruct your AI assistant to read the `SKILL.md` files inside the `skills/` directory.
2. **Execute Scripts**: AI agents can run the specific scripts using standard commands (e.g., `python3 scripts/<script_name>.py`) inside each skill directory.
3. **Environment Configuration**: Make sure to supply a `.env` file containing required API keys at the root of the project where you execute these scripts.

---

*Authored by Ren Fröjd - Developer AI Automation.*
