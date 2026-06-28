import os
import re
import csv
import urllib.request
import urllib.parse
import json
import ssl
import time

# Disable SSL verification for simple image downloading if needed
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

def call_gemini(prompt, system_instruction=None, json_mode=False):
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
        
    generation_config = {}
    if json_mode:
        generation_config["responseMimeType"] = "application/json"
    
    if generation_config:
        data["generationConfig"] = generation_config
        
    req = urllib.request.Request(
        url,
        data=json.dumps(data).encode('utf-8'),
        headers={'Content-Type': 'application/json'},
        method='POST'
    )
    
    max_retries = 6
    backoff_factor = 2
    initial_delay = 5  # start with 5 seconds delay
    
    for attempt in range(max_retries):
        try:
            with urllib.request.urlopen(req, context=ssl_context) as response:
                res_data = json.loads(response.read().decode('utf-8'))
                text = res_data['candidates'][0]['content']['parts'][0]['text']
                return text
        except Exception as e:
            is_429 = False
            if hasattr(e, 'code') and e.code == 429:
                is_429 = True
            elif "429" in str(e):
                is_429 = True
                
            if is_429 and attempt < max_retries - 1:
                delay = initial_delay * (backoff_factor ** attempt)
                print(f"Rate limited (429). Retrying in {delay} seconds (attempt {attempt + 1}/{max_retries})...")
                time.sleep(delay)
            else:
                print(f"Error calling Gemini: {e}")
                if attempt < max_retries - 1:
                    time.sleep(3)
                    continue
                return None
    return None

def parse_intents():
    file_path = "../keyword_intents.md"
    if not os.path.exists(file_path):
        file_path = "keyword_intents.md"
        
    if not os.path.exists(file_path):
        print(f"Error: {file_path} not found.")
        return []
        
    keywords_data = []
    current_group = ""
    
    with open(file_path, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith("## "):
                current_group = line.replace("## ", "").strip()
            elif "|" in line:
                parts = [p.strip() for p in line.split("|")]
                if len(parts) >= 6 and parts[1].isdigit():
                    # Parse keyword cleanly by removing backticks if present
                    keyword = parts[2].replace('`', '').strip()
                    searches = int(parts[3]) if parts[3].isdigit() else 0
                    intent_desc = parts[4]
                    
                    lsi = parts[5].replace('`', '').strip()
                    
                    img_prompt = ""
                    if len(parts) >= 7:
                        img_prompt = parts[6].replace('`', '').strip()
                        
                    keywords_data.append({
                        "keyword": keyword,
                        "searches": searches,
                        "intent": intent_desc,
                        "lsi": lsi,
                        "img_prompt": img_prompt,
                        "group": current_group
                    })
    return keywords_data

def sanitize_slug(keyword):
    slug = keyword.lower().strip()
    slug = re.sub(r'[^a-z0-9\s-]', '', slug)
    slug = re.sub(r'[\s_]+', '-', slug)
    slug = re.sub(r'-+', '-', slug)
    return slug

def verify_url(url):
    # We only verify HTTP/HTTPS urls
    if not url.startswith("http"):
        return False
        
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9,sv;q=0.8',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1'
    }
    
    try:
        req = urllib.request.Request(
            url, 
            headers=headers,
            method='HEAD'
        )
        with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
            if response.status in [200, 301, 302]:
                return True
    except Exception:
        # Fallback to GET if HEAD is not allowed or blocked
        try:
            req = urllib.request.Request(
                url, 
                headers=headers
            )
            with urllib.request.urlopen(req, timeout=5, context=ssl_context) as response:
                if response.status in [200, 301, 302]:
                    return True
        except Exception:
            pass
    return False

def run_researcher(keyword, intent, lsi, group, notebook_research=None):
    system_instruction = (
        "You are an expert SEO Researcher representing the 'Research_Agent' in the SEO_AI_Content_Factory (v2.5). "
        "Your job is to analyze the keyword and prepare a structured, comprehensive briefing document for the writer agent focusing on real data, numbers, and reliable sources."
    )
    
    extra_prompt = ""
    if notebook_research:
        extra_prompt = f"\n\nCRITICAL SOURCE DATA: The user has provided custom research and fact-checked statistics/URLs from Google NotebookLM:\n{notebook_research}\n\nYou MUST use these verified facts, numbers, and source URLs as the primary foundation for your brief."
        
    prompt = f"""
    {{
        "primary_keyword": "{keyword}",
        "search_intent": "{intent}",
        "secondary_keywords": {json.dumps(lsi.split(', '))},
        "country": "SE",
        "language": "EN",
        "word_count_target": 1000,
        "global_constraints": {{
            "no_fabricated_facts": true,
            "no_fabricated_urls": true,
            "intent_is_primary_signal": true,
            "entity_first_reasoning": true
        }}
    }}
    
    Please provide a detailed SEO content brief containing:
    1. The core target search query intent and how to answer it directly in the first paragraph (under 100 words).
    2. Recommended H2 and H3 headings.
    3. Natural ways to weave in the LSI keywords.
    4. At least 3 specific statistics, pricing figures, or data points relevant to this topic (e.g. RUT-avdrag savings percentages, average window cleaning times, Swedish climate stats, or dust accumulation rates).
    5. Specific high-authority REAL URLs to cite and link to for each figure/statistic (e.g. Skatteverket, SCB, Arbetsmiljöverket, or major scientific/news publications). Only suggest actual existing URLs.
    6. The best promotional angle for Ren Fröjd's local cleaning services in Västerås.{extra_prompt}
    
    Output the brief in clear markdown format.
    """
    return call_gemini(prompt, system_instruction)

def run_writer(brief, keyword, lsi):
    system_instruction = (
        "You are an elite SEO Copywriter ('Writer' Agent). Your style is professional, engaging, highly informative, "
        "and optimized for premium Scandinavian local business Ren Fröjd (Västerås, Sweden). "
        "You output only the clean HTML content that goes inside the article body."
    )
    prompt = f"""
    Based on this SEO Brief:
    {brief}
    
    Write a comprehensive, premium, long-form SEO article in English (around 800-1200 words).
    
    Requirements:
    1. Do NOT include H1 tag (H1 is already on the page). Use only H2, H3, and paragraph tags.
    2. Answer the search query directly and clearly in the first 100 words of the article.
    3. Seamlessly incorporate the following LSI keywords: {lsi}. CRITICAL: The article must be written 100% in English. Do NOT mix Swedish words (such as 'fönsterputs', 'städfirma', 'flyttstädning', etc.) directly in the English sentences. If any LSI keywords are in Swedish, you MUST translate or adapt them into natural English equivalents in the text (e.g., translate 'fönsterputs Västerås' to 'window cleaning Västerås' or 'window cleaning in Västerås').
    4. You MUST include concrete numbers, percentages, or statistics in the text.
    5. CRITICAL: Every single number, percentage, pricing figure, or statistic mentioned MUST have an outbound link showing where that figure/source came from. For example: `<a href="https://www.skatteverket.se/..." target="_blank" rel="nofollow noopener">Skatteverket</a>` or other official sources.
    6. MANDATORY INTERNAL LINK: You MUST include exactly one prominent link to the main window cleaning service page to pass link juice and encourage booking: `<a href="../window-cleaning.html">professional window cleaning services in Västerås</a>`. This link must be placed naturally in a paragraph promoting Ren Fröjd's services.
    7. OTHER SERVICE INTERNAL LINKS: If you mention other services like 'home cleaning', 'maid service', or 'move out cleaning' / 'flyttstädning' in the text, you MUST link them to the services section of the homepage using: `<a href="../#services">home cleaning</a>` or `<a href="../#services">move out cleaning</a>`.
    8. MANDATORY BOOKING CTA: Ensure there is at least one clear call-to-action button prompting the user to book. Place this button naturally **in the middle of the article** (e.g., right after the second H2 section or the third H3 section), rather than at the very end of the text. This prevents the button from stacking directly on top of the static booking card at the bottom of the page.
    9. CTA BUTTON STYLE: For any call-to-action (CTA) buttons, do NOT use custom inline styles (e.g. background-color, border-radius). Instead, use the website's native CSS classes. Format them exactly like this:
       `<div style="text-align: center; margin: 30px 0;"><a href="../window-cleaning.html#book" class="btn btn-primary">[Button Text]</a></div>` (or class="btn btn-secondary").
    10. KEYWORD DENSITY: The primary keyword '{keyword}' must be used naturally, but its density must be strictly controlled between 1% and 2.5% (never exceed 3% to prevent search engine spam filters).
    11. Include a callout box highlighting a helpful cleaning tip using this exact HTML structure:
       `<div class="service-notice" style="margin: 20px 0;"><p>💡 <strong>Tip:</strong> [Tip content here]</p></div>`
    12. FACTUAL AND NUMERICAL CONSISTENCY: Every number, statistic, percentage, or price mentioned in the article MUST be completely consistent and match the facts provided in the research brief. Do NOT make up, mismatch, or contradict any numbers between different sections of the text.
    13. READING TIME INDICATOR: Start the article body with a small reading time paragraph using this exact HTML: `<p style="font-size: 0.9rem; color: var(--text-light); margin-bottom: 20px;">⏱️ [X] min read</p>` (estimate [X] based on length, usually 4-5 min).
    14. SCAN-FRIENDLY FORMATTING: Make the text highly readable by using bold text (`<strong>`) for key terms, breaking paragraphs into short chunks (max 3-4 sentences), using bulleted lists (`<ul>`/`<li>`) where appropriate, and including comparison/pricing HTML tables (`<table>`, `<tr>`, `<th>`, `<td>`) to present pricing packages, tool comparisons, or schedules beautifully if it fits the article's topic. Do NOT write raw markdown tables; only use standard HTML table elements.
    15. LOCAL VÄSTERÅS NEIGHBORHOODS: Naturally mention one or two Västerås neighborhoods (e.g. Erikslund, Bäckby, Önsta-Gryta, Rönnby, Skallberget, or Lillåudden) in the body to boost local search authority.
    16. MINI-FAQ SECTION: End the article with a small FAQ section containing 2-3 common questions and answers relevant to the topic using structured heading tags (H3 for questions, and paragraphs for answers).
    17. The style must feel premium, showcasing 'Ukrainian precision and attention to detail' (a key selling point of Ren Fröjd).
    
    Provide ONLY the raw HTML content (no ```html wrapper, no markdown wrapper).
    """
    return call_gemini(prompt, system_instruction)

def run_reviewer(draft, keyword, intent, lsi):
    system_instruction = (
        "You are a strict SEO Editor and Quality Auditor ('SEO_Optimizer' and 'Fact_Checker' Agent). You inspect drafts, verify links using python checks, and output the finalized, "
        "optimized version in JSON format containing the optimized title, description, and HTML content."
    )
    prompt = f"""
    Review this draft for keyword '{keyword}':
    {draft}
    
    Checklist:
    - Are LSI keywords ({lsi}) used naturally?
    - Is the article 100% in English? There should be NO Swedish words (like fönsterputs, flyttstädning, städfirma, etc.) inside the English sentences. If they are present, translate them to English (e.g., replace 'fönsterputs' with 'window cleaning').
    - Does the first paragraph answer the intent '{intent}' directly?
    - Does the article start with the `⏱️ [X] min read` paragraph?
    - Is the text formatted with short paragraphs, bold text (`<strong>`), lists, and tables (if any)? There must be NO markdown bold (`**`) or markdown tables in the final output; all must be standard HTML.
    - Does it naturally mention any Västerås neighborhoods?
    - Does the article end with a mini-FAQ section containing 2-3 H3 questions and answers?
    - Are there actual numbers, figures, or statistics?
    - Does every mentioned number/statistic have a corresponding outbound link to its source? (This is mandatory)
    - Is the mandatory internal link pointing to `../window-cleaning.html` included to pass SEO link juice?
    - Are mentions of home cleaning, maid service, or move out cleaning linked to `../#services`?
    - Do all call-to-action buttons use `class="btn btn-primary"` or `class="btn btn-secondary"` with no inline custom CSS styles (like background-color, padding, etc.)?
    - Is the call-to-action button placed naturally in the middle of the article text? It must NOT be at the very end of the text.
    - Do all numbers, prices, percentages, and statistics mentioned in the draft exactly match the facts provided in the research brief? There must be no contradictions, hallucinations, or mismatched numbers in the text.
    - Is the keyword density of '{keyword}' within the 1-2.5% range and strictly below 3%? If not, reduce the occurrences of the keyword.
    - Are links properly formatted?
    - Is there a callout box?
    - Is the tone premium and matching the local brand Ren Fröjd?
    
    Adjust the content to fix any gaps or add missing source links for statistics. Then output the result in JSON format with these exact keys:
    {{
        "title": "Optimized Page Title (max 60 chars)",
        "meta_description": "Optimized meta description (150-160 chars)",
        "html_content": "The final clean, reviewed HTML content of the article"
    }}
    """
    res = call_gemini(prompt, system_instruction, json_mode=True)
    
    # We will do verification of links inside the main loop after parsing this JSON
    try:
        return json.loads(res)
    except Exception as e:
        print(f"Error parsing JSON from reviewer: {e}")
        # Fallback parsing
        return {
            "title": f"{keyword.title()} | Ren Fröjd Västerås",
            "meta_description": f"Professional guide on {keyword}. Read our tips and book local cleaning in Västerås.",
            "html_content": draft
        }

def update_html_file(slug, review_data):
    file_dir = "../en/artiklar"
    if not os.path.exists("../index.html"):
        file_dir = "en/artiklar"
        
    file_path = os.path.join(file_dir, f"{slug}.html")
    if not os.path.exists(file_path):
        print(f"Skeleton file not found: {file_path}")
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    # Replace Title
    content = re.sub(
        r'<title>[^<]+</title>',
        f'<title>{review_data["title"]}</title>',
        content
    )
    
    # Replace Meta Description
    content = re.sub(
        r'<meta name="description" content="[^"]+">',
        f'<meta name="description" content="{review_data["meta_description"]}">',
        content
    )
    
    # Replace Schema JSON-LD details
    content = re.sub(
        r'"headline": "[^"]+"',
        f'"headline": "{review_data["title"]}"',
        content
    )
    content = re.sub(
        r'"description": "[^"]+"',
        f'"description": "{review_data["meta_description"]}"',
        content
    )
    
    # Add JSON-LD Breadcrumb Schema right before </head> if not already present
    if "BreadcrumbList" not in content:
        article_title = review_data["title"].split("|")[0].strip()
        breadcrumb_schema = f"""
  <!-- JSON-LD Breadcrumb Schema -->
  <script type="application/ld+json">
  {{
    "@context": "https://schema.org",
    "@type": "BreadcrumbList",
    "itemListElement": [
      {{
        "@type": "ListItem",
        "position": 1,
        "name": "Home",
        "item": "https://vasteras-puts.se/en/"
      }},
      {{
        "@type": "ListItem",
        "position": 2,
        "name": "Articles",
        "item": "https://vasteras-puts.se/en/artiklar/"
      }},
      {{
        "@type": "ListItem",
        "position": 3,
        "name": "{article_title}",
        "item": "https://vasteras-puts.se/en/artiklar/{slug}.html"
      }}
    ]
  }}
  </script>
"""
        content = content.replace("</head>", f"{breadcrumb_schema}\n</head>")
    
    # Replace Article Content with visual breadcrumbs included
    article_title = review_data["title"].split("|")[0].strip()
    article_pattern = r'<article class="article-content">.*?</article>'
    breadcrumbs_html = f"""<!-- Breadcrumbs -->
      <nav class="breadcrumbs" aria-label="Breadcrumb" style="margin-bottom: 25px; font-size: 0.9rem; color: var(--text-light, #64748b); font-weight: 500;">
        <a href="../" style="color: var(--text-light, #64748b); text-decoration: none; transition: color 0.2s;">Home</a>
        <span style="margin: 0 8px; color: var(--border, #e2e8f0);">/</span>
        <a href="./" style="color: var(--text-light, #64748b); text-decoration: none; transition: color 0.2s;">Articles</a>
        <span style="margin: 0 8px; color: var(--border, #e2e8f0);">/</span>
        <span style="color: var(--text, #334155);">{article_title}</span>
      </nav>"""
      
    replacement = f'<article class="article-content">\n      {breadcrumbs_html}\n      <h1>{article_title}</h1>\n      {review_data["html_content"]}\n    </article>'
    content = re.sub(article_pattern, replacement, content, flags=re.DOTALL)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
        
    print(f"Successfully updated HTML file with breadcrumbs: {file_path}")
    return True

def main():
    # SET TO True IF YOU WANT TO FORCE RE-GENERATE ALL ARTICLES (OVERWRITE EXISTING)
    FORCE_REGENERATE = False
    
    print("Starting Multi-Agent SEO Generation System (SEO_AI_Content_Factory v2.5)...")
    keywords = parse_intents()
    if not keywords:
        print("No keywords parsed. Exiting.")
        return
        
    print(f"Parsed {len(keywords)} keywords from keyword_intents.md")
    
    # Process all keywords
    print(f"Generating articles for all {len(keywords)} keywords...")
    keywords_to_process = keywords
        
    # Fallback map for common broken links
    fallback_links = {
        "skatteverket": "https://www.skatteverket.se/privat/fastigheterochbostad/rutochrotavdrag.4.2ef05ad311d990ec2258000bcd.html",
        "scb": "https://www.scb.se/",
        "arbetsmiljo": "https://www.av.se/",
        "issa": "https://www.issa.com/",
        "default": "https://www.skatteverket.se/"
    }
    
    briefs_dir = "../research_briefs"
    if not os.path.exists("../index.html"):
        briefs_dir = "research_briefs"
        
    for idx, item in enumerate(keywords_to_process, 1):
        keyword = item["keyword"]
        intent = item["intent"]
        lsi = item["lsi"]
        group = item["group"]
        
        slug = sanitize_slug(keyword)
        
        # Check if the file is already processed and populated
        file_dir = "../en/artiklar"
        if not os.path.exists("../index.html"):
            file_dir = "en/artiklar"
        file_path = os.path.join(file_dir, f"{slug}.html")
        
        if not FORCE_REGENERATE and os.path.exists(file_path):
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            if "Here you can write the article about" not in html_content:
                print(f"[{idx}/{len(keywords_to_process)}] Skipping {keyword} (already generated: {file_path})")
                continue
                
        print(f"\n--- [{idx}/{len(keywords_to_process)}] Processing: {keyword} (Slug: {slug}) ---")
        
        # Load custom research brief (JSON, TXT, or MD) if it exists
        notebook_research = None
        json_bp = os.path.join(briefs_dir, f"{slug}.json")
        brief_urls = {}
        
        if os.path.exists(json_bp):
            print(f"Loading custom JSON research from: {json_bp}")
            try:
                with open(json_bp, 'r', encoding='utf-8') as jf:
                    brief_data = json.load(jf)
                parts = []
                if "analysis_and_insights" in brief_data:
                    parts.append(f"Analysis & Insights:\n{brief_data['analysis_and_insights']}")
                if "facts_and_statistics" in brief_data:
                    parts.append("Verified Facts & Source URLs:")
                    for fact in brief_data["facts_and_statistics"]:
                        url = fact.get('url')
                        source_name = fact.get('source_name', '').lower()
                        if url and source_name:
                            brief_urls[source_name] = url
                        parts.append(f"- {fact.get('description')} (Source: {fact.get('source_name')}, URL: {url})")
                if "lsi_concepts" in brief_data:
                    lsi = ", ".join(brief_data["lsi_concepts"])
                notebook_research = "\n\n".join(parts)
            except Exception as e:
                print(f"Error parsing JSON brief: {e}")
        else:
            brief_paths = [
                os.path.join(briefs_dir, f"{slug}.txt"),
                os.path.join(briefs_dir, f"{slug}.md")
            ]
            for bp in brief_paths:
                if os.path.exists(bp):
                    print(f"Loading custom text/markdown research from: {bp}")
                    with open(bp, 'r', encoding='utf-8') as bf:
                        notebook_research = bf.read()
                    break
        
        # 1. Researcher Agent
        print("Agent 1 [Researcher]: Planning & Outlining with sources...")
        brief = run_researcher(keyword, intent, lsi, group, notebook_research=notebook_research)
        if not brief:
            print(f"Skipping {keyword} due to failure in Researcher Agent.")
            continue
        
        # 2. Writer Agent
        print("Agent 2 [Writer]: Drafting content with statistics and links...")
        draft = run_writer(brief, keyword, lsi)
        if not draft:
            print(f"Skipping {keyword} due to failure in Writer Agent.")
            continue
        
        # 3. Reviewer Agent
        print("Agent 3 [SEO Reviewer]: Auditing and optimizing links...")
        review_data = run_reviewer(draft, keyword, intent, lsi)
        if not review_data or not review_data.get("html_content"):
            print(f"Skipping {keyword} due to failure in Reviewer Agent.")
            continue
        
        # 4. Link Verification Step
        html = review_data.get("html_content", "")
        links = re.findall(r'href="([^"]+)"', html)
        print(f"Verifying {len(links)} links found in content...")
        
        modified_html = html
        for link in links:
            if link.startswith("http"):
                print(f" - Testing URL: {link}")
                if verify_url(link):
                    print(f"   [OK] Valid link: {link}")
                else:
                    found_fallback = False
                    
                    # 1. Try to repair using verified URLs from the JSON research brief
                    for key, verified_url in brief_urls.items():
                        if key in link.lower():
                            print(f"   [REPAIR] Link failed. Repairing with verified URL from brief: {verified_url}")
                            modified_html = modified_html.replace(link, verified_url)
                            found_fallback = True
                            break
                    
                    # 2. Try generic fallbacks if not matched in the brief
                    if not found_fallback:
                        for key, fallback in fallback_links.items():
                            if key in link.lower():
                                print(f"   [WARNING] URL failed. Repairing with fallback: {fallback}")
                                modified_html = modified_html.replace(link, fallback)
                                found_fallback = True
                                break
                                
                    if not found_fallback:
                        fallback = fallback_links["default"]
                        print(f"   [WARNING] URL failed. Repairing with default fallback: {fallback}")
                        modified_html = modified_html.replace(link, fallback)
        
        # Convert markdown bold **text** to HTML <strong>text</strong>
        modified_html = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', modified_html)
        
        review_data["html_content"] = modified_html
        
        # 5. Save HTML
        update_html_file(slug, review_data)
        
    print("\nPilot run of SEO_AI_Content_Factory v2.5 completed successfully!")

if __name__ == "__main__":
    main()
