import os
import re
import json
import urllib.request
import ssl
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
GEMINI_API_KEY = ENV.get("GEMINI_API_KEY", "")

def call_gemini(prompt, system_instruction=None):
    if not GEMINI_API_KEY:
        raise ValueError("GEMINI_API_KEY is not set in .env")
    
    url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
    
    contents = [{"parts": [{"text": prompt}]}]
    data = {
        "contents": contents
    }
    if system_instruction:
        data["systemInstruction"] = {
            "parts": [{"text": system_instruction}]
        }
        
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
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

def main():
    file_path = "/Users/blatik/Documents/mama/keyword_intents.md"
    if not os.path.exists(file_path):
        print("Error: keyword_intents.md not found.")
        return

    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    new_lines = []
    count = 0
    
    for i, line in enumerate(lines):
        if line.startswith("|") and not line.strip().startswith("|---"):
            parts = [p.strip() for p in line.split("|")]
            # Check if parts[1] is a number (e.g. "1", "12")
            if len(parts) >= 6 and parts[1].isdigit():
                keyword = parts[2].replace('`', '').strip()
                old_lsi = parts[5].replace('`', '').strip()
                
                print(f"[{count+1}/150] Generating unique LSI for: {keyword} (Current: {old_lsi})")
                
                prompt = (
                    f"Generate 5-7 highly relevant LSI (latent semantic indexing) / thematic keywords or short search terms "
                    f"for the primary keyword '{keyword}'. The LSI words should be specific to this keyword and help write a "
                    f"comprehensive article about it. Output only the comma-separated list of LSI words/phrases, no other text, "
                    f"no quotes, no backticks, no markdown formatting."
                )
                
                new_lsi = None
                for attempt in range(3):
                    new_lsi = call_gemini(prompt)
                    if new_lsi:
                        # Clean up formatting if any
                        new_lsi = new_lsi.replace('`', '').replace('"', '').replace("'", "").strip()
                        if new_lsi.endswith('.'):
                            new_lsi = new_lsi[:-1]
                        break
                    time.sleep(1)
                
                if not new_lsi:
                    print(f"Failed to generate LSI for {keyword}, keeping old one.")
                    new_lsi = old_lsi
                
                print(f"   -> New LSI: {new_lsi}")
                
                # Reconstruct the line
                # The format is: | # | Keyword | Searches | Intent | LSI | Image Prompt | (if exists)
                parts[5] = f"`{new_lsi}`"
                new_line = " | ".join(parts) + "\n"
                new_lines.append(new_line)
                count += 1
                
                # Sleep a little to prevent rate limits
                time.sleep(0.2)
            else:
                new_lines.append(line)
        else:
            new_lines.append(line)

    with open(file_path, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
        
    print(f"Successfully processed {count} keywords.")

if __name__ == "__main__":
    main()
