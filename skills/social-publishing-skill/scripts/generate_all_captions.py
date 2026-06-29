import os
import re
import json
import glob
import ssl
import time
import urllib.request

ssl_context = ssl.create_default_context()

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
GITHUB_IMAGE_BASE = "https://raw.githubusercontent.com/Blatik/vasteras-puts/main/en/images"
SITE_ARTICLE_BASE = "https://vasteras-puts.se/en/artiklar"

def call_openai_to_summarize(article_text, keyword):
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
        return None

def main():
    print("=== SOCIAL MEDIA CAPTION GENERATOR (OPENAI) ===")
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not configured in your .env file.")
        return
        
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    artiklar_dir = os.path.join(prefix, "en/artiklar")
    html_files = glob.glob(os.path.join(artiklar_dir, "*.html"))
    
    # Path to save generated captions
    captions_file = os.path.join(prefix, "scratch/all_captions.json")
    os.makedirs(os.path.dirname(captions_file), exist_ok=True)
    
    # Load existing captions to avoid regenerating
    captions_data = {}
    if os.path.exists(captions_file):
        try:
            with open(captions_file, 'r', encoding='utf-8') as f:
                captions_data = json.load(f)
            print(f"Loaded {len(captions_data)} existing captions from cache.")
        except Exception as e:
            print(f"Could not load cache: {e}. Starting fresh.")
            
    to_process = []
    for path in html_files:
        filename = os.path.basename(path)
        if filename == "index.html":
            continue
            
        slug = filename.replace(".html", "")
        if slug in captions_data and captions_data[slug].get("caption"):
            continue
            
        to_process.append((path, slug))
        
    print(f"Need to generate captions for {len(to_process)} articles.")
    if not to_process:
        print("All captions have already been generated!")
        return
        
    success_count = 0
    for idx, (path, slug) in enumerate(to_process, 1):
        print(f"\n--- [{idx}/{len(to_process)}] Generating for slug: {slug} ---")
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract title/keyword
        title_match = re.search(r'<title>([^<]+)</title>', content)
        title = title_match.group(1).split("|")[0].strip() if title_match else slug.replace("-", " ").title()
        
        # Extract article body
        match = re.search(r'<article class="article-content">(.*?)</article>', content, re.DOTALL)
        article_body = ""
        if match:
            article_body = re.sub(r'<[^>]+>', ' ', match.group(1))
            
        if not article_body:
            print(f"Skipping {slug} - empty article content.")
            continue
            
        caption = call_openai_to_summarize(article_body, title)
        if caption:
            # Combine caption and the article URL
            article_url = f"{SITE_ARTICLE_BASE}/{slug}.html"
            full_caption = f"{caption}\n\nRead more: {article_url}"
            image_url = f"{GITHUB_IMAGE_BASE}/{slug}.webp"
            
            captions_data[slug] = {
                "keyword": title,
                "caption": full_caption,
                "article_url": article_url,
                "image_url": image_url,
                "published": False
            }
            
            # Save progress immediately
            with open(captions_file, 'w', encoding='utf-8') as f:
                json.dump(captions_data, f, indent=2, ensure_ascii=False)
                
            print(f"[OK] Saved caption for: {slug}")
            success_count += 1
            
            # OpenAI is very fast, just a minor delay to prevent aggressive hit rate
            time.sleep(1)
        else:
            print(f"[FAILED] Could not generate caption for: {slug}.")
            time.sleep(2)
            
    print(f"\nFinished! Generated {success_count} new captions. Total cached: {len(captions_data)}")

if __name__ == "__main__":
    main()
