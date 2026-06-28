import os
import glob
import re

def add_breadcrumbs_to_file(file_path):
    filename = os.path.basename(file_path)
    if filename == "index.html":
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    modified = False
    
    # 1. Extract Article Title
    title_match = re.search(r'<title>([^<]+)</title>', content)
    if not title_match:
        return False
    title = title_match.group(1).split("|")[0].strip()
    slug = filename.replace(".html", "")
    
    # 2. Add JSON-LD Breadcrumb Schema if not present
    if "BreadcrumbList" not in content:
        schema_html = f"""
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
        "name": "{title}",
        "item": "https://vasteras-puts.se/en/artiklar/{filename}"
      }}
    ]
  }}
  </script>
"""
        content = content.replace("</head>", f"{schema_html}\n</head>")
        modified = True
        
    # 3. Add visual HTML breadcrumbs if not present
    if 'class="breadcrumbs"' not in content:
        breadcrumbs_html = f"""<!-- Breadcrumbs -->
      <nav class="breadcrumbs" aria-label="Breadcrumb" style="margin-bottom: 25px; font-size: 0.9rem; color: var(--text-light, #64748b); font-weight: 500;">
        <a href="../" style="color: var(--text-light, #64748b); text-decoration: none; transition: color 0.2s;">Home</a>
        <span style="margin: 0 8px; color: var(--border, #e2e8f0);">/</span>
        <a href="./" style="color: var(--text-light, #64748b); text-decoration: none; transition: color 0.2s;">Articles</a>
        <span style="margin: 0 8px; color: var(--border, #e2e8f0);">/</span>
        <span style="color: var(--text, #334155);">{title}</span>
      </nav>"""
        
        # Insert right after <article class="article-content">
        article_start = '<article class="article-content">'
        if article_start in content:
            content = content.replace(article_start, f"{article_start}\n      {breadcrumbs_html}")
            modified = True
        else:
            # Fallback if class differs
            h1_start = '<h1>'
            if h1_start in content:
                content = content.replace(h1_start, f"{breadcrumbs_html}\n      {h1_start}")
                modified = True
                
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    print("=== ADDING BREADCRUMBS TO ALL ARTICLES ===")
    
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    artiklar_dir = os.path.join(prefix, "en/artiklar")
    html_files = glob.glob(os.path.join(artiklar_dir, "*.html"))
    
    updated_count = 0
    for path in html_files:
        if add_breadcrumbs_to_file(path):
            updated_count += 1
            
    print(f"Completed! Added breadcrumbs to {updated_count} out of {len(html_files) - 1} article files.")

if __name__ == "__main__":
    main()
