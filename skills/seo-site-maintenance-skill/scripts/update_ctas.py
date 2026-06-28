import os
import glob

def update_cta_in_file(file_path):
    filename = os.path.basename(file_path)
    if filename == "index.html":
        return False
        
    with open(file_path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    modified = False
    
    # Variations of target CTA links/texts
    targets = [
        ('href="../#book" class="btn btn-primary">Book Cleaning Now</a>', 'href="../window-cleaning.html#book" class="btn btn-primary">Book Window Cleaning</a>'),
        ('href="../#book" class="btn btn-primary">Book Cleaning</a>', 'href="../window-cleaning.html#book" class="btn btn-primary">Book Window Cleaning</a>'),
        ('href="../#book" class="btn btn-primary btn-lg">Book Cleaning Now</a>', 'href="../window-cleaning.html#book" class="btn btn-primary btn-lg">Book Window Cleaning</a>'),
        ('href="../#book" class="btn btn-primary btn-lg">Book Cleaning</a>', 'href="../window-cleaning.html#book" class="btn btn-primary btn-lg">Book Window Cleaning</a>'),
        ('href="../#book" class="button">Book Your Window Cleaning Service Today!</a>', 'href="../window-cleaning.html#book" class="button">Book Your Window Cleaning Service Today!</a>'),
    ]
    
    for old, new in targets:
        if old in content:
            content = content.replace(old, new)
            modified = True
            
    # Regex replacement fallback for any remaining href="../#book" inside article primary buttons
    # in case classes vary
    pattern = r'href="\.\./#book"([^>]*>)(Book Cleaning|Book Cleaning Now|Book Window Cleaning)'
    if re_match := re.search(pattern, content):
        content = re.sub(pattern, r'href="../window-cleaning.html#book"\1Book Window Cleaning', content)
        modified = True
        
    if modified:
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        return True
    return False

def main():
    import re
    global re
    
    print("=== UPDATING CTA BUTTONS IN ALL ARTICLES ===")
    
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    artiklar_dir = os.path.join(prefix, "en/artiklar")
    html_files = glob.glob(os.path.join(artiklar_dir, "*.html"))
    
    updated_count = 0
    for path in html_files:
        if update_cta_in_file(path):
            updated_count += 1
            
    print(f"Completed! Updated CTA buttons in {updated_count} out of {len(html_files) - 1} article files.")

if __name__ == "__main__":
    main()
