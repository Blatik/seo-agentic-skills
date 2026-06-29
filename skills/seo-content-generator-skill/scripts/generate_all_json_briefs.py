import os
import re
import urllib.request
import json
import ssl
import time

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
GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")

def call_gemini(prompt, system_instruction=None, json_mode=False):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in .env")
    
    url = "https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent"
    
    contents = [{"parts": [{"text": prompt}]}]
    data = {
        "contents": contents
    }
    
    if system_instruction:
        data["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
        
    generation_config = {}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"
    
    if generation_config:
        data["generationConfig"] = generation_config
        
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json', 'x-goog-api-key': GEMINI_API_KEY},
        method='POST'
    )
    
    try:
        with urllib.request.urlopen(req, context=ssl_context) as response:
            res_data = json.loads(response.read().decode('utf-8'))
            text = res_data['candidates'][0]['content']['parts'][0]['text']
            return text.strip()
    except Exception as e:
        print(f"Error calling Gemini: {e}")
        return None

def sanitize_slug(keyword):
    slug = keyword.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

def parse_intents():
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
                    intent_desc = parts[4].strip()
                    lsi = parts[5].replace('`', '').strip()
                    keywords_data.append({
                        "keyword": keyword,
                        "intent": intent_desc,
                        "lsi": lsi
                    })
    return keywords_data

def generate_json_brief(keyword, intent, lsi):
    system_instruction = (
        "You are an expert SEO Researcher. Generate a structured SEO Research Brief in JSON format for the given keyword. "
        "Your response must be a single, valid JSON object matching the requested schema. No markdown formatting outside the JSON."
    )
    
    prompt = f"""
    Keyword: {keyword}
    Intent: {intent}
    Initial LSI Keywords: {lsi}
    
    Please output a JSON object with this exact structure:
    {{
      "keyword": "{keyword}",
      "intent": "{intent}",
      "analysis_and_insights": "Detailed analysis of user intent and the technical importance of this service or product with regards to property maintenance and durability in Sweden (Västerås). Write at least 150-200 words.",
      "facts_and_statistics": [
        {{
          "description": "A fact or statistic about the topic. If it is about RUT-avdrag, link to Skatteverket. If it is about living standards/light, link to SCB. If it is about air quality/mold, link to WHO. If it is about cleaning industry standards, link to ISSA. You MUST embed the link in markdown style directly inside this text, e.g., 'According to [Skatteverket](https://www.skatteverket.se/...), ...'",
          "source_name": "Skatteverket or SCB or WHO or ISSA",
          "url": "Direct URL to the fact source"
        }}
      ],
      "lsi_concepts": [
        "LSI concept 1",
        "LSI concept 2",
        "LSI concept 3",
        "LSI concept 4",
        "LSI concept 5",
        "LSI concept 6",
        "LSI concept 7",
        "LSI concept 8"
      ]
    }}
    
    Ensure that you generate 3-4 specific facts in 'facts_and_statistics', each with actual, existing URLs from Skatteverket, SCB, WHO, or ISSA.
    """
    
    for _ in range(3):
        res = call_gemini(prompt, system_instruction, json_mode=True)
        if res:
            try:
                # Validate that it is indeed parseable JSON
                parsed = json.loads(res)
                return parsed
            except Exception:
                pass
        time.sleep(1)
    return None

def main():
    briefs_dir = "research_briefs"
    os.makedirs(briefs_dir, exist_ok=True)
    
    keywords = parse_intents()
    print(f"Loaded {len(keywords)} keywords from keyword_intents.md")
    
    # Process keywords that do NOT have a custom JSON brief yet
    missing_briefs = []
    for item in keywords:
        slug = sanitize_slug(item["keyword"])
        file_path = os.path.join(briefs_dir, f"{slug}.json")
        
        # Check if the file is empty or only a skeleton (less than 500 bytes is usually just a skeleton)
        is_skeleton = False
        if os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                try:
                    data = json.load(f)
                    if not data.get("analysis_and_insights"):
                        is_skeleton = True
                except Exception:
                    is_skeleton = True
                    
        if not os.path.exists(file_path) or is_skeleton:
            missing_briefs.append(item)
            
    print(f"Found {len(missing_briefs)} briefs that need to be generated.")
    
    if not missing_briefs:
        print("All research briefs are already populated!")
        return
        
    print("Starting generation. This will take some time due to API calls...")
    
    generated_count = 0
    for idx, item in enumerate(missing_briefs, 1):
        keyword = item["keyword"]
        intent = item["intent"]
        lsi = item["lsi"]
        slug = sanitize_slug(keyword)
        file_path = os.path.join(briefs_dir, f"{slug}.json")
        
        print(f"[{idx}/{len(missing_briefs)}] Generating brief for: '{keyword}'...")
        brief_json = generate_json_brief(keyword, intent, lsi)
        
        if brief_json:
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(brief_json, f, indent=2, ensure_ascii=False)
            print(f"  -> Saved to {file_path}")
            generated_count += 1
            # Add a small delay to avoid hitting rate limits
            time.sleep(1)
        else:
            print(f"  -> [FAILED] Could not generate brief for {keyword}")
            
    print(f"\nCompleted! Generated {generated_count} briefs in '{briefs_dir}/' folder.")

if __name__ == "__main__":
    main()
