# Site Link Audit Skill

This skill enables AI agents to crawl any webpage (including category, article, or competitor pages) and analyze their link weight distribution to detect external dofollow weight leakages.

## Scripts Included

- `audit_external_page.py`: Fetches any HTML page, parses links, divides them into internal/external, and identifies dofollow/nofollow status.

## Instructions for AI Agents

### 1. Auditing a Page
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
