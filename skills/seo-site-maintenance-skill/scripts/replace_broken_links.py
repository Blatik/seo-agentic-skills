import os
import glob
import re

def replace_links():
    print("=== REPLACING BROKEN EXTERNAL LINKS WITH CLEAN GENERAL LINKS ===")
    
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    articles_glob = os.path.join(prefix, "en/artiklar/*.html")
    article_files = glob.glob(articles_glob)
    
    # Mapping of domain keywords to clean, verified general URLs
    url_mapping = {
        "skatteverket.se": "https://www.skatteverket.se/privat/fastigheterochbostad/rutochrotavdrag.4.2ef05ad311d990ec2258000bcd.html",
        "scb.se": "https://www.scb.se/",
        "av.se": "https://www.av.se/",
        "arbetsmiljo": "https://www.av.se/",
        "who.int": "https://www.who.int/",
        "issa.com": "https://www.issa.com/"
    }
    
    updated_files_count = 0
    total_links_replaced = 0
    
    for path in article_files:
        if os.path.basename(path) == "index.html":
            continue
            
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        # Find all href links
        links = re.findall(r'href="([^"]+)"', content)
        modified = False
        new_content = content
        
        for link in links:
            # We only touch external links (starting with http)
            if link.startswith("http"):
                # Check if this link contains any of our target domains
                for domain, clean_url in url_mapping.items():
                    if domain in link.lower() and link != clean_url:
                        new_content = new_content.replace(f'href="{link}"', f'href="{clean_url}"')
                        print(f"[{os.path.basename(path)}] Replaced: {link} -> {clean_url}")
                        total_links_replaced += 1
                        modified = True
                        break
                        
        if modified:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_content)
            updated_files_count += 1
            
    print(f"\nDone! Updated {updated_files_count} files, replacing {total_links_replaced} links in total.")

if __name__ == "__main__":
    replace_links()
