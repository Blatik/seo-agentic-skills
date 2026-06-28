import os
import re
import json
import ssl
import urllib.request
import urllib.parse

ssl_context = ssl._create_unverified_context()

def load_env():
    env_vars = {}
    env_path = "../.env"
    if not os.path.exists(env_path):
        env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars

ENV = load_env()
OPENAI_API_KEY = ENV.get("OPENAI_API_KEY", "")
META_ACCESS_TOKEN = ENV.get("META_ACCESS_TOKEN", "")
FB_PAGE_ID = ENV.get("FB_PAGE_ID", "")
IG_ACCOUNT_ID = ENV.get("IG_ACCOUNT_ID", "")

# Public URL base where your images and articles are hosted
GITHUB_IMAGE_BASE = "https://raw.githubusercontent.com/Blatik/vasteras-puts/main/en/images"
SITE_ARTICLE_BASE = "https://vasteras-puts.se/en/artiklar"

def sanitize_slug(keyword):
    slug = keyword.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

def call_openai_to_summarize(article_text, keyword):
    print("Generating social media post caption using OpenAI...")
    url = "https://api.openai.com/v1/chat/completions"
    
    prompt = (
        f"You are an expert copywriter specializing in high-conversion social media marketing. "
        f"Write an engaging, persuasive social media post (Facebook/Instagram) based on a blog post about '{keyword}' "
        f"for 'Ren Fröjd'—a premium window cleaning service in Västerås.\n\n"
        "Your goal is to make local residents click the link and book a service. Follow these rules:\n"
        "1. Write a hook: Start with an engaging question or a relatable pain point (e.g., dirty windows blocking the sun, lack of time).\n"
        "2. Value proposition: Emphasize that Ren Fröjd offers crystal-clear, streak-free window cleaning with professional quality.\n"
        "3. Pricing: Highlight the highly competitive price of only 300 SEK/hour (very affordable for premium service!). Do not mention RUT-avdrag.\n"
        "4. Strong Call-to-Action: Urge them to click the link below to read the full guide and book their slot.\n"
        "5. Style: Keep it friendly, professional, punchy, and under 300 characters. Use emojis (e.g., 🇸🇪, ✨, 🪟) and relevant hashtags (e.g. #fönsterputs #västerås #renfröjd #renthem).\n"
        "6. Write in English.\n\n"
        f"Article content:\n{article_text[:4000]}"
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Content-Type': 'application/json',
            'Authorization': f'Bearer {OPENAI_API_KEY}'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as r:
            res = json.loads(r.read().decode())
            return res['choices'][0]['message']['content'].strip()
    except Exception as e:
        print(f"Error calling OpenAI: {e}")
        return f"Looking for streak-free windows in Västerås? 🇸🇪 Premium quality window cleaning for just 300 SEK/hour! Click to read our guide and book with Ren Fröjd today! ✨🪟"

def read_article_body(slug):
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    path = os.path.join(prefix, f"en/artiklar/{slug}.html")
    if not os.path.exists(path):
        return None
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Extract text inside <article>
    match = re.search(r'<article class="article-content">(.*?)</article>', content, re.DOTALL)
    if match:
        body = match.group(1)
        # remove html tags
        body = re.sub(r'<[^>]+>', ' ', body)
        return body
    return None

def publish_to_facebook(image_url, caption, article_url):
    print("Publishing photo to Facebook Page...")
    # Appending article link to caption
    full_caption = f"{caption}\n\nRead more: {article_url}"
    
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    payload = urllib.parse.urlencode({
        "url": image_url,
        "caption": full_caption,
        "place": "112463772102047",  # Västerås, Sweden Place ID
        "access_token": META_ACCESS_TOKEN
    }).encode('utf-8')
    
    req = urllib.request.Request(url, data=payload, method='POST')
    try:
        with urllib.request.urlopen(req, context=ssl_context) as r:
            res = json.loads(r.read().decode())
            print("Successfully published to Facebook Page!")
            print("FB Post ID:", res.get("post_id", res.get("id")))
            return True
    except Exception as e:
        if hasattr(e, 'read'):
            print("FB Error Details:", e.read().decode())
        print(f"Failed to publish to Facebook: {e}")
        return False

def publish_to_instagram(image_url, caption):
    if not IG_ACCOUNT_ID:
        print("Instagram account ID not configured, skipping Instagram.")
        return False
        
    print("Publishing photo to Instagram...")
    # Step 1: Create media container
    url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
    payload_container = urllib.parse.urlencode({
        "image_url": image_url,
        "caption": caption,
        "location_id": "213063546",  # Västerås, Sweden Location ID
        "access_token": META_ACCESS_TOKEN
    }).encode('utf-8')
    
    req_container = urllib.request.Request(url_container, data=payload_container, method='POST')
    try:
        with urllib.request.urlopen(req_container, context=ssl_context) as r:
            res_container = json.loads(r.read().decode())
            container_id = res_container["id"]
            
        # Step 2: Publish container
        url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
        payload_publish = urllib.parse.urlencode({
            "creation_id": container_id,
            "access_token": META_ACCESS_TOKEN
        }).encode('utf-8')
        
        req_publish = urllib.request.Request(url_publish, data=payload_publish, method='POST')
        with urllib.request.urlopen(req_publish, context=ssl_context) as r:
            res_publish = json.loads(r.read().decode())
            print("Successfully published to Instagram!")
            print("Instagram Media ID:", res_publish.get("id"))
            return True
    except Exception as e:
        if hasattr(e, 'read'):
            print("IG Error Details:", e.read().decode())
        print(f"Failed to publish to Instagram: {e}")
        return False

def main():
    print("=== META SOCIAL PUBLISHING SYSTEM ===")
    
    if not META_ACCESS_TOKEN or not FB_PAGE_ID:
        print("Error: META_ACCESS_TOKEN and FB_PAGE_ID must be set in .env")
        return
        
    # Get user input for keyword
    keyword = input("Enter the article keyword/topic to publish (e.g. 'window cleaning cost'): ").strip()
    if not keyword:
        print("No keyword entered. Exiting.")
        return
        
    slug = sanitize_slug(keyword)
    article_body = read_article_body(slug)
    
    if not article_body:
        print(f"Error: Could not find HTML article file for '{keyword}' (Slug: {slug})")
        return
        
    # Auto-generate caption
    caption = call_openai_to_summarize(article_body, keyword)
    print(f"\nGenerated Caption:\n{caption}\n")
    
    # URLs for the public image and article
    image_url = f"{GITHUB_IMAGE_BASE}/{slug}.webp"
    article_url = f"{SITE_ARTICLE_BASE}/{slug}.html"
    
    print(f"Image Source URL: {image_url}")
    print(f"Article Link URL: {article_url}\n")
    
    confirm = input("Do you want to publish this to your social media channels? (yes/no): ").strip().lower()
    if confirm != 'yes' and confirm != 'y':
        print("Publishing cancelled.")
        return
        
    # Publish to FB and IG
    publish_to_facebook(image_url, caption, article_url)
    publish_to_instagram(image_url, caption)

if __name__ == "__main__":
    main()
