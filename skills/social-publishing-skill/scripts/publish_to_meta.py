import os
import re
import json
import ssl
import urllib.request
import urllib.parse
import sys
import time

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
PINTEREST_ACCESS_TOKEN = ENV.get("PINTEREST_ACCESS_TOKEN", "")

# Public URL base where your images and articles are hosted
GITHUB_IMAGE_BASE = "https://vasteras-puts.se/en/images"
SITE_ARTICLE_BASE = "https://vasteras-puts.se/en/artiklar"
TRACKING_FILE = "scratch/published_posts.json"

if not os.path.exists("scratch") and os.path.exists("../scratch"):
    TRACKING_FILE = "../scratch/published_posts.json"

def load_published_history():
    if os.path.exists(TRACKING_FILE):
        try:
            with open(TRACKING_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception:
            return {}
    return {}

def save_published_history(history):
    os.makedirs(os.path.dirname(TRACKING_FILE), exist_ok=True)
    with open(TRACKING_FILE, 'w', encoding='utf-8') as f:
        json.dump(history, f, indent=2, ensure_ascii=False)

def mark_as_published(slug, platform):
    history = load_published_history()
    if slug not in history:
        history[slug] = {}
    history[slug][platform] = True
    save_published_history(history)

def customize_hashtags(caption, post_keyword):
    # Remove any existing hashtags
    caption_no_tags = re.sub(r'#\S+', '', caption).strip()
    
    # Base hashtags
    tags = ["#RenFröjd"]
    
    # Clean the post's specific keyword to create a hashtag (keeping Swedish characters)
    clean_kw = re.sub(r'[^\w\s]', '', post_keyword).replace('_', '')
    kw_tag = '#' + ''.join(word.capitalize() for word in clean_kw.split())
    if len(kw_tag) > 1 and len(kw_tag) < 35:
        tags.append(kw_tag)
        
    # Top keywords from the CSV
    top_csv_tags = [
        "#WindowCleaning",
        "#WindowWashing",
        "#ProfessionalWindowCleaning",
        "#ResidentialWindowCleaning",
        "#CommercialWindowCleaning",
        "#LocalWindowCleaners",
        "#BestWindowCleaner"
    ]
    
    # Add from top_csv_tags until we have 6 tags
    for t in top_csv_tags:
        if len(tags) >= 6:
            break
        if t.lower() not in [x.lower() for x in tags]:
            tags.append(t)
            
    hashtags_str = " ".join(tags)
    
    # Find any Read more link
    read_more_match = re.search(r'(Read more:\s*https?://\S+)', caption_no_tags, re.IGNORECASE)
    if read_more_match:
        read_more_line = read_more_match.group(1)
        caption_no_tags = caption_no_tags.replace(read_more_line, '').strip()
        # Clean up any trailing pointing emojis
        caption_no_tags = re.sub(r'👉\s*$', '', caption_no_tags).strip()
        caption_no_tags = re.sub(r'👇\s*$', '', caption_no_tags).strip()
        caption_no_tags = re.sub(r'🔗\s*$', '', caption_no_tags).strip()
        return f"{caption_no_tags.strip()}\n\n{hashtags_str}\n\n{read_more_line}"
    else:
        return f"{caption_no_tags.strip()}\n\n{hashtags_str}"

def is_published(slug, platform):
    history = load_published_history()
    return history.get(slug, {}).get(platform, False)

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
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
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
        body = re.sub(r'<[^>]+>', ' ', body)
        return body
    return None

def publish_to_facebook(image_url, caption, article_url, slug):
    if is_published(slug, "facebook"):
        print("Facebook: Already published, skipping.")
        return True
        
    print("Publishing photo to Facebook Page...")
    # Only append the article link if it's not already in the caption
    if "read more" not in caption.lower() and "http" not in caption.lower():
        full_caption = f"{caption}\n\nRead more: {article_url}"
    else:
        full_caption = caption

    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
    local_image_path = os.path.join(prefix, f"en/images/{slug}.webp")

    if not os.path.exists(local_image_path):
        print(f"Error: Local image path not found: {local_image_path}")
        return False

    with open(local_image_path, "rb") as f:
        image_data = f.read()

    boundary = b'----WebKitFormBoundary7MA4YWxkTrZu0gW'
    body = []
    
    fields = {
        "caption": full_caption,
        "access_token": META_ACCESS_TOKEN
    }
    for key, value in fields.items():
        body.append(b'--' + boundary)
        body.append(f'Content-Disposition: form-data; name="{key}"'.encode('utf-8'))
        body.append(b'')
        body.append(str(value).encode('utf-8'))
        
    filename = f"{slug}.webp"
    body.append(b'--' + boundary)
    body.append(f'Content-Disposition: form-data; name="source"; filename="{filename}"'.encode('utf-8'))
    body.append(b'Content-Type: image/webp')
    body.append(b'')
    body.append(image_data)
    
    body.append(b'--' + boundary + b'--')
    body.append(b'')
    
    url = f"https://graph.facebook.com/v19.0/{FB_PAGE_ID}/photos"
    req = urllib.request.Request(
        url,
        data=b'\r\n'.join(body),
        headers={
            'Content-Type': f'multipart/form-data; boundary={boundary.decode("utf-8")}'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            res = json.loads(r.read().decode())
            print("Successfully published to Facebook Page!")
            mark_as_published(slug, "facebook")
            return True
    except Exception as e:
        if hasattr(e, 'read'):
            print("FB Error Details:", e.read().decode())
        print(f"Failed to publish to Facebook: {e}")
        return False

def publish_to_instagram(image_url, caption, slug):
    if not IG_ACCOUNT_ID:
        return False
    if is_published(slug, "instagram"):
        print("Instagram: Already published, skipping.")
        return True
        
    # Clean the caption for Instagram (remove links and placeholders)
    clean_caption = re.sub(r'click the link below', 'click the link in our bio', caption, flags=re.IGNORECASE)
    clean_caption = re.sub(r'link(?:s)? below', 'link in our bio', clean_caption, flags=re.IGNORECASE)
    clean_caption = re.sub(r'Read more:\s*https?://\S+', '', clean_caption)
    
    placeholders = [
        r'\[Your Booking Link\]',
        r'\[Link\]',
        r'\[Insert Link\]',
        r'\[Your Link Here\]',
        r'\[Link to your service\]',
        r'\[Book Now\]',
        r'\[Book Now\]\(#\)',
        r'👉\s*\[[^\]]+\]',
        r'👉\s*Link',
        r'(?m)^\s*👉\s*$',
        r'(?m)^\s*👇\s*$',
        r'(?m)^\s*⬇️\s*$',
        r'👉\s*$',
        r'👇\s*$',
        r'⬇️'
    ]
    for p in placeholders:
        clean_caption = re.sub(p, '', clean_caption, flags=re.IGNORECASE)
    clean_caption = re.sub(r'\n{3,}', '\n\n', clean_caption).strip()

    print("Publishing photo to Instagram...")
    url_container = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media"
    payload_container = urllib.parse.urlencode({
        "image_url": image_url,
        "caption": clean_caption,
        "access_token": META_ACCESS_TOKEN
    }).encode('utf-8')
    
    req_container = urllib.request.Request(url_container, data=payload_container, method='POST')
    try:
        with urllib.request.urlopen(req_container, context=ssl_context, timeout=30) as r:
            res_container = json.loads(r.read().decode())
            container_id = res_container["id"]
            
        # Wait 10 seconds for Instagram to download and process the image
        print("Waiting 10 seconds for Instagram to process the image container...")
        time.sleep(10)
            
        url_publish = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media_publish"
        payload_publish = urllib.parse.urlencode({
            "creation_id": container_id,
            "access_token": META_ACCESS_TOKEN
        }).encode('utf-8')
        
        req_publish = urllib.request.Request(url_publish, data=payload_publish, method='POST')
        with urllib.request.urlopen(req_publish, context=ssl_context, timeout=30) as r:
            res_publish = json.loads(r.read().decode())
            print("Successfully published to Instagram!")
            mark_as_published(slug, "instagram")
            return True
    except Exception as e:
        if hasattr(e, 'read'):
            print("IG Error Details:", e.read().decode())
        print(f"Failed to publish to Instagram: {e}")
        return False

def fetch_pinterest_boards():
    if not PINTEREST_ACCESS_TOKEN:
        return []
    print("Fetching Pinterest boards...")
    url = "https://api.pinterest.com/v5/boards"
    req = urllib.request.Request(
        url,
        headers={
            'Authorization': f'Bearer {PINTEREST_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        },
        method='GET'
    )
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            res = json.loads(r.read().decode())
            return res.get("items", [])
    except urllib.error.HTTPError as e:
        if e.code == 401:
            print("\n⚠️ [Pinterest Warning] Authentication failed (401). Your developer application might still be pending approval. Pinterest publishing will be skipped.")
        else:
            print(f"\n⚠️ [Pinterest Warning] HTTP Error {e.code} fetching boards: {e.reason}")
        return []
    except Exception as e:
        print(f"\n⚠️ [Pinterest Warning] Failed to fetch Pinterest boards: {e}")
        return []

def publish_to_pinterest(board_id, image_url, title, description, article_url, slug):
    if is_published(slug, "pinterest"):
        print("Pinterest: Already published, skipping.")
        return True
        
    print("Creating Pin on Pinterest...")
    url = "https://api.pinterest.com/v5/pins"
    
    clean_desc = re.sub(r'<[^>]+>', ' ', description).strip()
    if len(clean_desc) > 500:
        clean_desc = clean_desc[:497] + "..."
        
    data = {
        "link": article_url,
        "title": title[:100],
        "description": clean_desc,
        "media_source": {
            "source_type": "image_url",
            "url": image_url
        },
        "board_id": board_id
    }
    
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={
            'Authorization': f'Bearer {PINTEREST_ACCESS_TOKEN}',
            'Content-Type': 'application/json'
        },
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            res = json.loads(r.read().decode())
            print("Successfully created Pin on Pinterest!")
            mark_as_published(slug, "pinterest")
            return True
    except Exception as e:
        if hasattr(e, 'read'):
            print("Pinterest Pin Error Details:", e.read().decode())
        print(f"Failed to create Pin on Pinterest: {e}")
        return False

def get_keywords_from_intents():
    file_path = "../keyword_intents.md"
    if not os.path.exists(file_path):
        file_path = "keyword_intents.md"
    if not os.path.exists(file_path):
        return {}
        
    keywords_map = {}
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6 and parts[1].isdigit():
                    keyword = parts[2].replace('`', '').strip()
                    slug = sanitize_slug(keyword)
                    keywords_map[slug] = keyword
    return keywords_map

def main():
    print("=== META & PINTEREST AUTOMATED PUBLISHING FACTORY ===")
    
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    images_dir = os.path.join(prefix, "en/images")
    articles_dir = os.path.join(prefix, "en/artiklar")
    
    if not os.path.exists(images_dir) or not os.path.exists(articles_dir):
        print("Error: en/images or en/artiklar directory not found.")
        return
        
    keywords_map = get_keywords_from_intents()
    
    # Load pre-generated captions to avoid calling OpenAI
    captions_file = os.path.join(prefix, "scratch/all_captions.json")
    all_captions = {}
    if os.path.exists(captions_file):
        try:
            with open(captions_file, 'r', encoding='utf-8') as f:
                all_captions = json.load(f)
            print(f"Loaded {len(all_captions)} pre-generated captions from {captions_file}.")
        except Exception as e:
            print(f"Could not load captions file: {e}")

    # Scan all generated images to see what is ready to publish
    available_slugs = []
    for file in os.listdir(images_dir):
        if file.endswith('.webp'):
            slug = os.path.splitext(file)[0]
            # Verify article also exists
            if os.path.exists(os.path.join(articles_dir, f"{slug}.html")):
                available_slugs.append(slug)
                
    print(f"Found {len(available_slugs)} articles with generated cover images.")
    
    # Filter out already published ones
    to_publish = []
    for slug in available_slugs:
        pub_fb = is_published(slug, "facebook")
        pub_ig = is_published(slug, "instagram") if IG_ACCOUNT_ID else True
        pub_pin = is_published(slug, "pinterest") if PINTEREST_ACCESS_TOKEN else True
        
        if not (pub_fb and pub_ig and pub_pin):
            to_publish.append(slug)
            
    print(f"Pending publication: {len(to_publish)} articles.")
    
    if not to_publish:
        print("Everything has already been published! Nothing to do.")
        return
        
    # Get Pinterest board if publishing there
    board_id = None
    if PINTEREST_ACCESS_TOKEN:
        boards = fetch_pinterest_boards()
        if boards:
            print("\nAvailable Pinterest Boards:")
            for i, board in enumerate(boards, 1):
                print(f" [{i}] {board['name']} (ID: {board['id']})")
            choice = input(f"Choose Pinterest board (1-{len(boards)}, default 1): ").strip()
            try:
                idx = int(choice) - 1 if choice else 0
                if idx < 0 or idx >= len(boards):
                    idx = 0
            except ValueError:
                idx = 0
            board_id = boards[idx]['id']
            print(f"Selected Board: {boards[idx]['name']}\n")
            
    try:
        confirm = input(f"Would you like to start publishing the {len(to_publish)} pending posts? (yes/no): ").strip().lower()
    except UnicodeDecodeError:
        import sys
        raw_input = sys.stdin.buffer.readline()
        confirm = raw_input.decode('utf-8', errors='ignore').strip().lower()
    except Exception:
        confirm = 'no'
        
    if confirm not in ['yes', 'y', 'да', 'так']:
        print("Exiting.")
        return
        
    # Process one by one
    for idx, slug in enumerate(to_publish, 1):
        keyword = keywords_map.get(slug, slug.replace('-', ' ').capitalize())
        print(f"\n--- [{idx}/{len(to_publish)}] Publishing: {keyword} (Slug: {slug}) ---")
        
        article_body = read_article_body(slug)
        if not article_body:
            print("Skipping - article body empty.")
            continue
            
        image_url = f"{GITHUB_IMAGE_BASE}/{slug}.webp"
        article_url = f"{SITE_ARTICLE_BASE}/{slug}.html"

        # Check for pre-generated caption
        caption = None
        if slug in all_captions and all_captions[slug].get("caption"):
            caption = all_captions[slug]["caption"]
            print("Using pre-generated caption from cache.")
        else:
            caption_raw = call_openai_to_summarize(article_body, keyword)
            caption = f"{caption_raw}\n\nRead more: {article_url}"
            
        caption = customize_hashtags(caption, keyword)
        
        # Publish and track success
        fb_ok = True
        ig_ok = True
        pin_ok = True
        
        if META_ACCESS_TOKEN and FB_PAGE_ID:
            fb_ok = publish_to_facebook(image_url, caption, article_url, slug)
            if IG_ACCOUNT_ID:
                ig_ok = publish_to_instagram(image_url, caption, slug)
            
        if PINTEREST_ACCESS_TOKEN and board_id:
            title = f"{keyword.capitalize()} in Västerås"
            pin_ok = publish_to_pinterest(board_id, image_url, title, caption, article_url, slug)
            
        if fb_ok and ig_ok and pin_ok:
            print(f"✅ [OK] Completed: {slug}")
        else:
            status_parts = []
            if not fb_ok: status_parts.append("Facebook FAILED")
            if not ig_ok: status_parts.append("Instagram FAILED")
            if not pin_ok: status_parts.append("Pinterest FAILED")
            print(f"❌ [PARTIAL FAILURE] {slug}: {', '.join(status_parts)}")
            
        # Brief sleep between posts to respect API rate limits
        time.sleep(3)

if __name__ == "__main__":
    main()
