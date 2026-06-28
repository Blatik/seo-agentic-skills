# Social Media Publishing and Captioning Skill

This skill enables AI agents to generate SEO-optimized captions for all site articles and automatically publish them with geotags to Facebook, Instagram, and Pinterest.

## Scripts Included

- `generate_all_captions.py`: Scans site articles, summaries their content, appends hashtags/metadata, and stores them in a local JSON database (`all_captions.json`).
- `publish_to_meta.py`: Publishes selected content (images and text) with geotags ("Västerås, Sweden") to linked Facebook, Instagram, and Pinterest profiles.

## Instructions for AI Agents

### 1. Generating Captions
To generate structured social media posts for all site content:
1. Run the caption generator:
   ```bash
   python3 scripts/generate_all_captions.py
   ```
2. The script will look for missing captions and use OpenAI to summarize the article body, formatting it with engaging bullet points, target price (300 SEK/hour), Swedish tags (`#fönsterputs #västerås`), and the destination article link. All outputs are stored in `scratch/all_captions.json`.

### 2. Publishing to Social Media Channels
To publish a specific topic:
1. Run the publisher:
   ```bash
   python3 scripts/publish_to_meta.py
   ```
2. Enter the topic/keyword to publish. The script reads the body and caption, prompts for confirmation, and deploys it on Facebook Page (with location ID `112463772102047`) and Instagram Business Page (with location ID `213063546`), automatically tagging **Västerås, Sweden**!
