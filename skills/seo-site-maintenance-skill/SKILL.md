# SEO Site Maintenance and Optimization Skill

This skill enables AI agents to perform batch operations across all HTML pages, such as injecting JSON-LD breadcrumbs, updating global navigation footers, correcting broken external links, and optimizing CTA (Call-to-Action) sections.

## Scripts Included

- `add_breadcrumbs_to_all.py`: Injects structured JSON-LD Breadcrumb schemas into all HTML files.
- `add_footer_links.py`: Dynamically injects/updates custom footer navigation menus.
- `update_ctas.py`: Batch modifies booking anchors and CTA links.
- `replace_broken_links.py`: Scans external links and resolves/removes broken links to prevent domain authority drainage.
- `audit_articles.py`: Audit tool to verify page formatting and check for schema inconsistencies.

## Instructions for AI Agents

### 1. Injecting Schema/Breadcrumbs
To run a batch update for breadcrumb navigation schemas:
```bash
python3 scripts/add_breadcrumbs_to_all.py
```

### 2. Updating Calls to Action (CTAs)
To dynamically change target commercial urls or booking buttons:
```bash
python3 scripts/update_ctas.py
```

### 3. Healing Broken Links
To check and clean up broken redirects or links:
```bash
python3 scripts/replace_broken_links.py
```
