import os
import json
import urllib.request
import urllib.parse
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
IG_ACCOUNT_ID = ENV.get("IG_ACCOUNT_ID", "")

if not META_ACCESS_TOKEN or not IG_ACCOUNT_ID:
    print("Error: META_ACCESS_TOKEN or IG_ACCOUNT_ID not found in .env")
    exit(1)

def get_instagram_media():
    url = f"https://graph.facebook.com/v19.0/{IG_ACCOUNT_ID}/media?fields=id,caption&access_token={META_ACCESS_TOKEN}&limit=100"
    req = urllib.request.Request(url, method='GET')
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            res = json.loads(r.read().decode())
            return res.get("data", [])
    except Exception as e:
        print(f"Failed to fetch media: {e}")
        return []

def delete_instagram_media(media_id):
    url = f"https://graph.facebook.com/v19.0/{media_id}?access_token={META_ACCESS_TOKEN}"
    req = urllib.request.Request(url, method='DELETE')
    try:
        with urllib.request.urlopen(req, context=ssl_context, timeout=30) as r:
            res = json.loads(r.read().decode())
            return res.get("success", False)
    except Exception as e:
        if hasattr(e, 'read'):
            print(f"Failed to delete media {media_id}: {e.read().decode()}")
        else:
            print(f"Failed to delete media {media_id}: {e}")
        return False

def reset_published_posts_instagram():
    tracking_file = "scratch/published_posts.json"
    if os.path.exists(tracking_file):
        try:
            with open(tracking_file, 'r', encoding='utf-8') as f:
                data = json.load(f)
            
            # Reset instagram status
            for k in data:
                if "instagram" in data[k]:
                    data[k]["instagram"] = False
            
            with open(tracking_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print("Successfully reset Instagram status in published_posts.json.")
        except Exception as e:
            print(f"Failed to update published_posts.json: {e}")

def main():
    print("=== STARTING INSTAGRAM POST DELETION ===")
    media_list = get_instagram_media()
    print(f"Found {len(media_list)} posts to delete.")
    
    deleted_count = 0
    for media in media_list:
        media_id = media["id"]
        caption_snippet = media.get("caption", "")[:40].replace('\n', ' ')
        print(f"Deleting post ID {media_id} ({caption_snippet})...")
        if delete_instagram_media(media_id):
            print("✅ Deleted!")
            deleted_count += 1
        else:
            print("❌ Failed to delete.")
            
    print(f"\n=== DELETION COMPLETE: Deleted {deleted_count} posts. ===")
    reset_published_posts_instagram()

if __name__ == "__main__":
    main()
