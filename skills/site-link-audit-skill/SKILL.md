# Site Link Audit Skill

This skill enables AI agents to crawl any webpage (including category, article, or competitor pages) and analyze their link weight distribution to detect external dofollow weight leakages and internal link flows. Acting as an automated **seo specialist** or **seo consultant**, it is crucial for maintaining the link health of an **seo website**.

## Scripts Included

- `audit_external_page.py`: Fetches any HTML page, parses links, divides them into internal/external, and identifies dofollow/nofollow status.
- `audit_interlinking.py`: Performs a site-wide internal link (interlinking) audit. It parses all local HTML files, validates that all internal links point to existing files, detects orphan pages (0 incoming links), identifies poorly linked pages, and provides link distribution statistics.

## Instructions for AI Agents

### 1. Auditing External Page Link Leaks
To run a link audit on a target webpage:
1. Run the audit script:
   ```bash
   python3 scripts/audit_external_page.py <URL>
   ```
   *(If no URL is provided, it defaults to auditing `https://renfrojd.nu/category/mat-dryck/`)*.
2. The script outputs a detailed report containing:
   - Total link count.
   - Internal dofollow/nofollow counts.
   - External dofollow/nofollow counts.
   - A list of external links that are transmitting Domain Authority (dofollow link leaks) to other sites, highlighting potential places where link power is being lost.

### 2. Auditing Site-Wide Internal Linking (Interlinking)
To run a site-wide audit on internal links to improve **seo optimization** and avoid search visibility loss:
1. Run the interlinking audit script:
   ```bash
   python3 scripts/audit_interlinking.py
   ```
2. The script recursively analyzes all HTML files in the project and outputs:
   - Total internal links found.
   - Broken internal links (links pointing to non-existent files) that need to be healed.
   - Orphan pages (pages with 0 incoming internal links).
   - Poorly linked pages (pages with fewer than 2 incoming links).
   - Statistics on incoming and outgoing links per page.
