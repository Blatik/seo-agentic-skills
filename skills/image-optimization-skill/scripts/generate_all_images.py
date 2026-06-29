import os
import re
import json
import ssl
import urllib.request
import base64
import time

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
GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")
OPENAI_API_KEY = ENV.get("OPENAI_API_KEY", "")

def sanitize_slug(keyword):
    slug = keyword.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

def parse_intents():
    file_path = "../keyword_intents.md"
    if not os.path.exists(file_path):
        file_path = "keyword_intents.md"
        
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []
        
    keywords_data = []
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6 and parts[1].isdigit():
                    keyword = parts[2].replace('`', '').strip()
                    lsi = parts[5].replace('`', '').strip()
                    
                    img_prompt = ""
                    if len(parts) >= 7:
                        img_prompt = parts[6].replace('`', '').strip()
                        
                    keywords_data.append({
                        "keyword": keyword,
                        "slug": sanitize_slug(keyword),
                        "img_prompt": img_prompt
                    })
    return keywords_data

def generate_image_gemini(prompt, output_path):
    print(f"Generating image using Gemini Imagen 4.0: {output_path}")
    url = "https://generativelanguage.googleapis.com/v1beta/models/imagen-4.0-generate-001:predict"
    
    # Strip Midjourney parameters like --ar 16:9
    clean_prompt = re.sub(r'--ar\s+\d+:\d+', '', prompt).strip()
    
    # Enforce black uniform with Ren Fröjd logo and European/Ukrainian appearance for any person in the prompt
    person_keywords = ["cleaner", "washer", "worker", "man", "woman", "person", "people", "uniform"]
    if any(k in clean_prompt.lower() for k in person_keywords):
        clean_prompt += ", the person must be a professional cleaner of European (Ukrainian) appearance, wearing a premium black uniform t-shirt with the Ren Fröjd brand logo printed on the chest. The logo is a stylized water droplet shape with a light blue upper half and a yellow lower half, outlined in dark navy blue, with the text 'REN FRÖJD' written horizontally across the middle of the droplet in a bold, modern, geometric sans-serif font in dark navy blue capital letters"
    
    data = {
        "instances": [
            {"prompt": clean_prompt}
        ],
        "parameters": {
            "sampleCount": 1,
            "aspectRatio": "16:9",
            "outputMimeType": "image/png"
        }
    }
    
    try:
        req = urllib.request.Request(
            url,
            data=json.dumps(data).encode('utf-8'),
            headers={'Content-Type': 'application/json', 'x-goog-api-key': GEMINI_API_KEY},
            method='POST'
        )
    except Exception as e:
        print(f"Error creating request: {e}")
        return False
        
    retries = 4
    delay = 15
    for attempt in range(retries):
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                img_b64 = res_data['predictions'][0]['bytesBase64Encoded']
                img_data = base64.b64decode(img_b64)
                from PIL import Image
                import io
                img = Image.open(io.BytesIO(img_data))
                img.save(output_path, "WEBP", quality=85)
                return True
        except urllib.error.HTTPError as e:
            if e.code == 429:
                print(f"[429] Rate limit hit on attempt {attempt + 1}. Waiting {delay} seconds before retry...")
                time.sleep(delay)
                delay *= 2
            elif e.code in [500, 503]:
                print(f"[{e.code}] Temporary server error on attempt {attempt + 1}. Waiting 5 seconds before retry...")
                time.sleep(5)
            else:
                try:
                    print(f"HTTP Error {e.code}: {e.read().decode()}")
                except Exception:
                    print(f"HTTP Error {e.code}")
                return False
        except Exception as e:
            print(f"Error on attempt {attempt + 1}: {e}")
            time.sleep(3)
            
    return False

def generate_image_openai(prompt, output_path):
    print(f"Generating image using OpenAI: {output_path}")
    url = "https://api.openai.com/v1/images/generations"
    
    clean_prompt = re.sub(r'--ar\s+\d+:\d+', '', prompt).strip()
    person_keywords = ["cleaner", "washer", "worker", "man", "woman", "person", "people", "uniform"]
    if any(k in clean_prompt.lower() for k in person_keywords):
        clean_prompt += ", the person must be a professional cleaner of European (Ukrainian) appearance, wearing a premium black uniform t-shirt with the Ren Fröjd brand logo printed on the chest. The logo is a stylized water droplet shape with a light blue upper half and a yellow lower half, outlined in dark navy blue, with the text 'REN FRÖJD' written horizontally across the middle of the droplet in a bold, modern, geometric sans-serif font in dark navy blue capital letters"
    
    # Try gpt-image-2 first (Widescreen 16:9)
    try:
        print("Attempting gpt-image-2...")
        data = {
            "model": "gpt-image-2",
            "prompt": clean_prompt,
            "n": 1,
            "size": "1792x1024"
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
        
        with urllib.request.urlopen(req, context=ssl_context) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            img_b64 = res_data['data'][0]['b64_json']
            img_data = base64.b64decode(img_b64)
            from PIL import Image
            import io
            img = Image.open(io.BytesIO(img_data))
            img.save(output_path, "WEBP", quality=85)
            return True
            
    except Exception as e:
        err_body = ""
        try:
            if hasattr(e, 'read'):
                err_body = e.read().decode('utf-8')
        except Exception:
            pass
            
        # Check if gpt-image-2 is unavailable/does not exist, try gpt-image-1
        if "does not exist" in err_body.lower() or "gpt-image-2" in err_body.lower():
            print("gpt-image-2 not available on this account. Falling back to gpt-image-1 (1024x1024)...")
            try:
                data_fallback = {
                    "model": "gpt-image-1",
                    "prompt": clean_prompt,
                    "n": 1,
                    "size": "1024x1024"
                }
                
                req_fallback = urllib.request.Request(
                    url,
                    data=json.dumps(data_fallback).encode('utf-8'),
                    headers={
                        'Content-Type': 'application/json',
                        'Authorization': f'Bearer {OPENAI_API_KEY}'
                    },
                    method='POST'
                )
                
                with urllib.request.urlopen(req_fallback, context=ssl_context) as response:
                    res_data = json.loads(response.read().decode('utf-8'))
                    img_b64 = res_data['data'][0]['b64_json']
                    img_data = base64.b64decode(img_b64)
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(img_data))
                    img.save(output_path, "WEBP", quality=85)
                    return True
            except Exception as e2:
                try:
                    if hasattr(e2, 'read'):
                        print("gpt-image-1 Error Details:", e2.read().decode('utf-8'))
                except Exception:
                    pass
                print(f"Failed to generate via gpt-image-1: {e2}")
                return False
        
        # Check for quota limits on original gpt-image-2 error
        quota_exceeded = "quota" in err_body.lower() or "billing" in err_body.lower() or "limit" in err_body.lower()
        if quota_exceeded:
            print("\n[LIMIT REACHED] OpenAI Quota or Rate Limit exceeded. Please update the OPENAI_API_KEY in your .env file and run the script again.")
            import sys
            sys.exit(0)
            
        print(f"Error generating via OpenAI: {e}")
        if err_body:
            print("Error Details:", err_body)
        return False

def main():
    print("=== AUTOMATIC IMAGE GENERATION FACTORY ===")
    
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    images_dir = os.path.join(prefix, "en/images")
    os.makedirs(images_dir, exist_ok=True)
    
    items = parse_intents()
    if not items:
        print("No image prompts found. Exiting.")
        return
        
    print(f"Found {len(items)} keywords/prompts.")
    
    # Filter only those that don't have images generated yet
    to_generate = []
    for item in items:
        out_path = os.path.join(images_dir, f"{item['slug']}.webp")
        if os.path.exists(out_path):
            continue
        if not item['img_prompt']:
            print(f"Skipping slug {item['slug']} - no prompt available.")
            continue
        to_generate.append((item, out_path))
        
    print(f"{len(to_generate)} images need to be generated.")
    
    if not to_generate:
        print("All images are already generated!")
        return
        
    for idx, (item, out_path) in enumerate(to_generate, 1):
        print(f"\n--- [{idx}/{len(to_generate)}] Processing: {item['keyword']} ---")
        
        success = False
        if GEMINI_API_KEY:
            success = generate_image_gemini(item['img_prompt'], out_path)
        else:
            print("Error: GEMINI_API_KEY not found in .env.")
            return
            
        if success:
            print(f"[OK] Generated: {out_path}")
            # No delay as requested
        else:
            print(f"[LIMIT REACHED / FAILED] Could not generate image using Gemini. Terminating script.")
            import sys
            sys.exit(0)

if __name__ == "__main__":
    main()
