import os
import json
import re
import urllib.request
import urllib.parse
import ssl

ssl_context = ssl.create_default_context()

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
IG_ACCOUNT_ID = ENV.get("IG_ACCOUNT_ID", "")

if not META_ACCESS_TOKEN or not IG_ACCOUNT_ID:
    print("Error: META_ACCESS_TOKEN or IG_ACCOUNT_ID not found in .env")
    exit(1)

def clean_caption_text(caption):
    if not caption:
        return None
    
    original = caption
    
    # Replace link below references
    caption = re.sub(r'click the link below', 'click the link in our bio', caption, flags=re.IGNORECASE)
    caption = re.sub(r'link(?:s)? below', 'link in our bio', caption, flags=re.IGNORECASE)

    # Remove "Read more: http..."
    caption = re.sub(r'Read more:\s*https?://\S+', '', caption)
    
    # List of placeholder regexes to remove
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
        caption = re.sub(p, '', caption, flags=re.IGNORECASE)
        
    # Clean up empty lines and trailing/leading spaces
    caption = re.sub(r'\n{3,}', '\n\n', caption)
    caption = caption.strip()
    
    return caption if caption != original else None

def get_instagram_media():
    url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media?fields=id,caption&access_token={META_ACCESS_TOKEN}&limit=50"
    req = urllib.request.Request(url, method='GET')
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            res = json.loads(r.read().decode())
            return res.get("data", [])
    except Exception as e:
        print(f"Failed to fetch media: {e}")
        return []

def update_instagram_caption(media_id, new_caption):
    url = f"https://graph.facebook.com/v19.0/{media_id}"
    payload = urllib.parse.urlencode({
        "caption": new_caption,
        "comment_enabled": "true",
        "access_token": META_ACCESS_TOKEN
    }).encode('utf-8')
    req = urllib.request.Request(url, data=payload, method='POST')
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            res = json.loads(r.read().decode())
            return res.get("success", False)
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.read().decode('utf-8')}")
        return False
    except Exception as e:
        print(f"Failed to update media {media_id}: {e}")
        return False

def main():
    print("=== STARTING INSTAGRAM CAPTION CLEANUP ===")
    media_list = get_instagram_media()
    print(f"Found {len(media_list)} recent posts.")
    
    updated_count = 0
    for media in media_list:
        media_id = media["id"]
        caption = media.get("caption", "")
        
        new_caption = clean_caption_text(caption)
        if new_caption is not None:
            print(f"\nCleaning post ID {media_id}...")
            print("Old Caption snippet:\n", caption[-100:].replace('\n', ' '))
            print("New Caption snippet:\n", new_caption[-100:].replace('\n', ' '))
            
            success = update_instagram_caption(media_id, new_caption)
            if success:
                print("✅ Successfully updated caption!")
                updated_count += 1
            else:
                print("❌ Failed to update caption.")
        else:
            print(f"Post ID {media_id} is already clean.")
            
    print(f"\n=== CLEANUP COMPLETE: Updated {updated_count} posts. ===")

if __name__ == "__main__":
    main()
