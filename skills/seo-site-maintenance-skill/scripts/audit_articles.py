import os
import glob
import re

def audit():
    print("=== STARTING TECHNICAL AUDIT OF 150 ARTICLES ===")
    
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    articles_glob = os.path.join(prefix, "en/artiklar/*.html")
    files = glob.glob(articles_glob)
    
    total = 0
    empty_skeletons = 0
    has_markdown_bolds = 0
    total_words = 0
    keyword_densities = []
    
    print(f"Auditing {len(files)} files...\n")
    print(f"{'Filename':<45} | {'Words':<6} | {'Links':<5} | {'Bolds OK?':<9} | {'Status':<10}")
    print("-" * 85)
    
    for path in sorted(files):
        filename = os.path.basename(path)
        if filename == "index.html":
            continue
            
        total += 1
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Check if skeleton placeholder exists
        is_skeleton = "Here you can write the article about" in content
        if is_skeleton:
            empty_skeletons += 1
            status = "SKELETON (EMPTY)"
        else:
            status = "OK"
            
        # Extract text within <article> to count words and links accurately
        article_match = re.search(r'<article class="article-content">(.*?)</article>', content, re.DOTALL)
        if article_match:
            article_body = article_match.group(1)
            # Remove HTML tags to count words
            text_only = re.sub(r'<[^>]+>', ' ', article_body)
            words = len(text_only.split())
            total_words += words
            
            # Count links
            links_count = len(re.findall(r'href="[^"]+"', article_body))
        else:
            words = 0
            links_count = 0
            
        # Check for remaining markdown bold
        has_bold_md = "**" in content
        if has_bold_md:
            has_markdown_bolds += 1
            bolds_ok = "FAILED"
        else:
            bolds_ok = "YES"
            
        print(f"{filename:<45} | {words:<6} | {links_count:<5} | {bolds_ok:<9} | {status:<10}")
        
    print("\n" + "="*50)
    print("AUDIT SUMMARY:")
    print(f"Total articles audited: {total}")
    print(f"Fully populated articles: {total - empty_skeletons}")
    print(f"Empty skeleton placeholders: {empty_skeletons}")
    print(f"Articles containing raw markdown '**': {has_markdown_bolds}")
    if total - empty_skeletons > 0:
        print(f"Average word count: {int(total_words / (total - empty_skeletons))} words")
    print("="*50)

if __name__ == "__main__":
    audit()
