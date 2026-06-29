import os
import json
import re
import urllib.request
import ssl

ssl_context = ssl._create_unverified_context()

def load_env():
    env_vars = {}
    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars

ENV = load_env()
META_ACCESS_TOKEN = ENV.get("META_ACCESS_TOKEN", "")
FB_PAGE_ID = ENV.get("FB_PAGE_ID", "")
IG_ACCOUNT_ID = ENV.get("IG_ACCOUNT_ID", "")

if not META_ACCESS_TOKEN or not FB_PAGE_ID:
    print("Error: META_ACCESS_TOKEN or FB_PAGE_ID not found in .env")
    exit(1)

def fetch_facebook_published_slugs():
    slugs = set()
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/feed?fields=message&access_token={META_ACCESS_TOKEN}&limit=100"
    req = urllib.request.Request(url, method='GET')
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            data = json.loads(r.read().decode()).get("data", [])
            for item in data:
                message = item.get("message") or ""
                match = re.search(r'/en/artiklar/([^/.]+)\.html', message)
                if match:
                    slugs.add(match.group(1))
    except Exception as e:
        print(f"Failed to fetch Facebook feed: {e}")
    return slugs

def find_best_match(instagram_caption, all_captions):
    # Strip everything that is not an alphanumeric character
    def clean(text):
        return re.sub(r'[^a-z0-9]', '', text.lower())
    
    clean_ig = clean(instagram_caption)
    if not clean_ig:
        return None
        
    best_slug = None
    best_ratio = 0
    
    for slug, details in all_captions.items():
        cached = details.get("caption", "")
        if not cached:
            continue
        
        # Clean cached caption
        cached_clean = re.sub(r'Read more:\s*https?://\S+', '', cached)
        clean_cached = clean(cached_clean)
        
        if clean_cached in clean_ig or clean_ig in clean_cached:
            return slug
            
        ig_words = set(re.findall(r'\w+', instagram_caption.lower()))
        cached_words = set(re.findall(r'\w+', cached_clean.lower()))
        if ig_words and cached_words:
            overlap = len(ig_words.intersection(cached_words)) / max(len(ig_words), len(cached_words))
            if overlap > best_ratio:
                best_ratio = overlap
                best_slug = slug
                
    if best_ratio > 0.6:
        return best_slug
    return None

def fetch_instagram_published_slugs(all_captions):
    slugs = set()
    if not IG_ACCOUNT_ID:
        return slugs
        
    url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media?fields=caption&access_token={META_ACCESS_TOKEN}&limit=100"
    req = urllib.request.Request(url, method='GET')
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            data = json.loads(r.read().decode()).get("data", [])
            for item in data:
                caption = item.get("caption") or ""
                if not caption:
                    continue
                
                slug = find_best_match(caption, all_captions)
                if slug:
                    slugs.add(slug)
    except Exception as e:
        print(f"Failed to fetch Instagram media: {e}")
    return slugs

def main():
    print("=== STARTING LIVE HISTORY SYNCHRONIZATION ===")
    
    # Load cached captions
    captions_file = "scratch/all_captions.json"
    all_captions = {}
    if os.path.exists(captions_file):
        with open(captions_file, 'r', encoding='utf-8') as f:
            all_captions = json.load(f)
            
    print("Fetching published posts from Facebook Page...")
    fb_slugs = fetch_facebook_published_slugs()
    print(f"Found {len(fb_slugs)} posts on Facebook.")
    
    print("Fetching published posts from Instagram Business Account...")
    ig_slugs = fetch_instagram_published_slugs(all_captions)
    print(f"Found {len(ig_slugs)} posts on Instagram.")
    
    # Merge and update published_posts.json
    history = {}
    
    # Add Facebook status
    for slug in fb_slugs:
        if slug not in history:
            history[slug] = {}
        history[slug]["facebook"] = True
        
    # Add Instagram status
    for slug in ig_slugs:
        if slug not in history:
            history[slug] = {}
        history[slug]["instagram"] = True
        
    # Fill in defaults (false) for other platforms if one is true
    for slug in history:
        if "facebook" not in history[slug]:
            history[slug]["facebook"] = False
        if "instagram" not in history[slug]:
            history[slug]["instagram"] = False
            
    # Save history
    tracking_file = "scratch/published_posts.json"
    with open(tracking_file, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)
        
    print(f"\n✅ Synchronization complete! Saved state for {len(history)} articles to {tracking_file}.")
    print("You are ready to run publish_to_meta.py safely!")

if __name__ == "__main__":
    main()
