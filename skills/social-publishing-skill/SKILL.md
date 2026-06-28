# Social Media Publishing and Captioning Skill

This skill enables AI agents to generate SEO-optimized captions for all site articles and automatically publish them with geotags to Facebook, Instagram, and Pinterest.

## Scripts Included

- `generate_all_captions.py`: Scans site articles, summaries their content, appends hashtags/metadata, and stores them in a local JSON database (`all_captions.json`).
- `publish_to_meta.py`: Automatically publishes content with location tagging ("Västerås, Sweden") to linked Facebook, Instagram, and Pinterest profiles. Tracks history in `scratch/published_posts.json` to prevent duplicates.
- `clean_instagram_captions.py`: Utility script to clean up already published Instagram captions (e.g. replacing 'link below' references with 'link in bio' and removing non-functional URLs).
- `delete_all_instagram_posts.py`: Administrative utility to clean up/delete all Instagram posts via the API and reset their history.

## Instructions for AI Agents

### 1. Generating Captions
To generate structured social media posts for all site content:
1. Run the caption generator:
   ```bash
   python3 scripts/generate_all_captions.py
   ```
2. The script will look for missing captions and use OpenAI to summarize the article body, formatting it with engaging bullet points, target price (300 SEK/hour), Swedish tags (`#fönsterputs #västerås`), and the destination article link. All outputs are stored in `scratch/all_captions.json`.

### 2. Publishing to Social Media Channels (Automated Tracking)
To publish pending posts:
1. Run the publisher:
   ```bash
   python3 scripts/publish_to_meta.py
   ```
2. The script automatically:
   * Scans all generated images in `en/images/` and matches them with HTML articles.
   * Compares them against the local publication database (`scratch/published_posts.json`).
   * Fetches your boards from Pinterest and prompts you to select one.
   * Publishes all pending posts incrementally to Facebook Page (location ID `112463772102047`), Instagram Business Page (location ID `213063546`), and Pinterest (on the selected board), keeping the database updated to avoid duplicates.
