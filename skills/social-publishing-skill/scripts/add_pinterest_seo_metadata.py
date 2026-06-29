import os
import re
import json
import ssl
import time
import urllib.request

ssl_context = ssl.create_default_context()

def load_env():
    env_vars = {}
    env_path = ".env"
    if not os.path.exists(env_path):
        env_path = "../.env"
    if os.path.exists(env_path):
        with open(env_path, 'r', encoding='utf-8') as f:
            for line in f:
                if '=' in line and not line.startswith('#'):
                    k, v = line.strip().split('=', 1)
                    env_vars[k.strip()] = v.strip()
    return env_vars

ENV = load_env()
OPENAI_API_KEY = ENV.get("OPENAI_API_KEY", "")

def sanitize_slug(keyword):
    slug = keyword.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

def load_keywords_and_intents():
    file_path = "keyword_intents.md"
    data_map = {}
    if not os.path.exists(file_path):
        file_path = "../keyword_intents.md"
    if not os.path.exists(file_path):
        print("Warning: keyword_intents.md not found.")
        return data_map
        
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6 and parts[1].isdigit():
                    raw_keyword = parts[2].replace('`', '').strip()
                    intent = parts[4].strip()
                    lsi = parts[5].strip()
                    slug = sanitize_slug(raw_keyword)
                    data_map[slug] = {
                        "keyword": raw_keyword,
                        "intent": intent,
                        "lsi": lsi
                    }
    return data_map

def call_openai_for_pinterest(keyword, intent, lsi, article_text):
    url = "https://api.openai.com/v1/chat/completions"
    
    prompt = (
        f"You are an expert SMM manager specializing in Pinterest SEO and traffic growth.\n"
        f"Your task is to analyze the provided article text and write a highly optimized Pinterest Pin Title and Pin Description based strictly on the key points, facts, and unique takeaways found in this specific article.\n\n"
        f"Target SEO Keyword: {keyword}\n"
        f"Search Intent / Context: {intent}\n"
        f"LSI Keywords to naturally keep in mind: {lsi}\n\n"
        f"Rules for Pinterest copy:\n"
        f"1. Pin Title (max 100 characters):\n"
        f"   - Must include the target keyword naturally.\n"
        f"   - Must capture the core value/solution presented in the article.\n"
        f"   - Must be engaging and clickable (e.g. use words like 'How to', 'Secrets', 'Guide', 'Best').\n"
        f"   - Keep it under 100 characters.\n\n"
        f"2. Pin Description (max 500 characters):\n"
        f"   - Start with a compelling hook matching the user's search intent.\n"
        f"   - Summarize the specific key points or unique tips described in the article text below (e.g. 'Learn why...', 'Discover the difference between...').\n"
        f"   - Incorporate the keyword naturally in the first 1-2 sentences.\n"
        f"   - End with a strong call to action (e.g. 'Click to read our full guide!').\n"
        f"   - Include 3-4 highly relevant hashtags at the end (e.g. #WindowCleaning #CleaningHacks #RenFröjd).\n"
        f"   - Do NOT use placeholders like [Link] or 'link in bio'.\n"
        f"   - Keep it strictly under 500 characters.\n\n"
        f"Response format (strictly JSON):\n"
        f"{{\n"
        f"  \"pinterest_title\": \"...\",\n"
        f"  \"pinterest_description\": \"...\"\n"
        f"}}\n\n"
        f"ARTICLE CONTENT TO ANALYZE:\n{article_text[:3500]}"
    )
    
    data = {
        "model": "gpt-4o-mini",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.7,
        "response_format": {"type": "json_object"}
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
            content = res['choices'][0]['message']['content'].strip()
            return json.loads(content)
    except Exception as e:
        print(f"Error calling OpenAI for Pinterest copy: {e}")
        return None

def main():
    print("=== GENERATING PINTEREST SEO METADATA ===")
    if not OPENAI_API_KEY:
        print("Error: OPENAI_API_KEY is not configured in your .env file.")
        return
        
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    captions_file = os.path.join(prefix, "scratch/all_captions.json")
    if not os.path.exists(captions_file):
        print("Error: scratch/all_captions.json not found.")
        return
        
    with open(captions_file, 'r', encoding='utf-8') as f:
        captions_data = json.load(f)
        
    intents_map = load_keywords_and_intents()
    print(f"Loaded {len(intents_map)} keywords and intents from keyword_intents.md.")
    
    to_process = []
    for slug, data in captions_data.items():
        if "pinterest_title" not in data or "pinterest_description" not in data:
            to_process.append(slug)
            
    print(f"Need to generate Pinterest copy for {len(to_process)} articles.")
    if not to_process:
        print("All articles already have Pinterest copy generated!")
        return
        
    success_count = 0
    for idx, slug in enumerate(to_process, 1):
        print(f"\n--- [{idx}/{len(to_process)}] Processing Pinterest copy for slug: {slug} ---")
        
        artiklar_dir = os.path.join(prefix, "en/artiklar")
        art_path = os.path.join(artiklar_dir, f"{slug}.html")
        if not os.path.exists(art_path):
            print(f"Article file not found: {art_path}, skipping.")
            continue
            
        with open(art_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Extract article body
        match = re.search(r'<article class="article-content">(.*?)</article>', content, re.DOTALL)
        article_body = ""
        if match:
            article_body = re.sub(r'<[^>]+>', ' ', match.group(1))
            
        if not article_body:
            print("Skipping - article content is empty.")
            continue
            
        intent_info = intents_map.get(slug, {
            "keyword": slug.replace("-", " ").title(),
            "intent": "Користувач шукає інформацію про очищення вікон.",
            "lsi": "Västerås, fönsterputs, window cleaning"
        })
        
        res = call_openai_for_pinterest(
            intent_info["keyword"],
            intent_info["intent"],
            intent_info["lsi"],
            article_body
        )
        
        if res:
            captions_data[slug]["pinterest_title"] = res["pinterest_title"]
            captions_data[slug]["pinterest_description"] = res["pinterest_description"]
            
            with open(captions_file, 'w', encoding='utf-8') as f:
                json.dump(captions_data, f, indent=2, ensure_ascii=False)
                
            print(f"[OK] Pinterest Title: {res['pinterest_title']}")
            print(f"[OK] Pinterest Desc: {res['pinterest_description']}")
            success_count += 1
            time.sleep(1)
        else:
            print("[FAILED] Could not generate Pinterest copy.")
            time.sleep(2)
            
    print(f"\nFinished! Generated {success_count} Pinterest SEO copy fields.")

if __name__ == "__main__":
    main()
