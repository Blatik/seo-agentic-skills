# SEO Content Generation Skill

This skill enables AI agents to automate keyword research, compile technical briefs, analyze LSI keywords, and generate SEO-optimized articles based on structured templates.

## Scripts Included

- `generate_all_json_briefs.py`: Compiles search intent, keywords, and structural outlines into JSON briefs for each target keyword.
- `generate_unique_lsi.py`: Extracts and filters LSI (Latent Semantic Indexing) keywords to prevent keyword stuffing.
- `generate_articles.py`: Direct article generator that reads JSON briefs and drafts SEO-friendly HTML articles with structured microdata.

## Instructions for AI Agents

### 1. Preparing the Briefs
Before writing any articles:
1. Ensure your semantic core or keywords list is ready.
2. Run the brief generator:
   ```bash
   python3 scripts/generate_all_json_briefs.py
   ```
3. This creates keyword-specific JSON outlines in `research_briefs/`.

### 2. Generating Articles
To draft and save SEO-compliant articles in bulk:
1. Run the article compiler:
   ```bash
   python3 scripts/generate_articles.py
   ```
2. The agent reads the briefs, calls LLMs to write quality content, and structures it into beautiful HTML using components like JSON-LD schema, navigation links, and styled lists.
