# Image Optimization and Generation Skill

This skill enables AI agents to automatically generate stock-style articles cover images and convert all site content images into lightweight WebP format, while keeping HTML pages synchronized.

## Scripts Included

- `generate_all_images.py`: Automatic stock image generator using DALL-E or Gemini Imagen APIs.
- `convert_all_site_images_to_webp.py`: Scans the website root, converts content PNGs to `.webp`, and rewrites references in all HTML files.

## Instructions for AI Agents

### 1. Generating Images for Keywords
If the site has new articles or missing images:
1. Ensure the Google Imagen or OpenAI API key is set in `.env`.
2. Run the script from the command line:
   ```bash
   python3 scripts/generate_all_images.py
   ```
3. The script will automatically parse articles, find keywords, and generate missing images in the `en/images/` directory.

### 2. Converting Existing Images to WebP
To optimize page loading speed and SEO performance:
1. Run the image conversion script:
   ```bash
   python3 scripts/convert_all_site_images_to_webp.py
   ```
2. The script converts all raw PNGs (covers, banners, article images) into WebP format, deletes the old PNGs, and updates all `<img>`, `<meta property="og:image">`, and JSON-LD schema tags inside your HTML files to point to `.webp`.
