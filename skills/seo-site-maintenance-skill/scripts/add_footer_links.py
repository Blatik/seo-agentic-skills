import os
import glob
import re

def update_file(path, target_pattern, replacement, optional_message=""):
    if not os.path.exists(path):
        print(f"File not found: {path}")
        return False
        
    with open(path, 'r', encoding='utf-8') as f:
        content = f.read()
        
    if target_pattern in content:
        # Check if the replacement was already added
        if replacement in content:
            print(f"Skipping (link already present): {path}")
            return True
            
        new_content = content.replace(target_pattern, target_pattern + "\n        " + replacement)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully updated: {path} {optional_message}")
        return True
    else:
        print(f"Target pattern not found in: {path}")
        return False

def main():
    print("=== ADDING SEO-OPTIMIZED FOOTER LINKS ===")
    
    # Check if we are running from root or scratch
    prefix = ""
    if not os.path.exists("index.html") and os.path.exists("../index.html"):
        prefix = "../"
        
    # 1. Update root index.html (Swedish version)
    update_file(
        os.path.join(prefix, "index.html"),
        '<a href="#book">Boka städning</a>',
        '<a href="en/artiklar/index.html">Städtips & fönsterputsningsguider</a>',
        "(Swedish Home Page)"
    )
    
    # 2. Update en/index.html (English version)
    update_file(
        os.path.join(prefix, "en/index.html"),
        '<a href="#book">Book Cleaning</a>',
        '<a href="artiklar/index.html">Window Cleaning Guides & Tips</a>',
        "(English Home Page)"
    )
    
    # 3. Update en/window-cleaning.html (English services page)
    update_file(
        os.path.join(prefix, "en/window-cleaning.html"),
        '<a href="#book">Book Cleaning</a>',
        '<a href="artiklar/index.html">Window Cleaning Guides & Tips</a>',
        "(English Services Page)"
    )
    
    # 4. Update en/artiklar/index.html (Articles directory page)
    # The articles list directory page has a simplified footer, let's update it completely
    articles_index_path = os.path.join(prefix, "en/artiklar/index.html")
    if os.path.exists(articles_index_path):
        with open(articles_index_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        full_footer_pattern = """  <!-- Footer -->
  <footer class="main-footer">
    <div class="footer-bottom text-center">
      <p>&copy; 2026 Ren Fröjd. All rights reserved.</p>
    </div>
  </footer>"""
        
        replacement_footer = """  <!-- Footer -->
  <footer class="main-footer">
    <div class="container footer-container">
      <div class="footer-brand">
        <div class="logo">
          <span class="icon-sparkle">✨</span>
          <span class="logo-text">Ren Fröjd</span>
        </div>
        <p>Professional home cleaning, move out cleaning and window cleaning in Västerås with Ukrainian attention to detail.</p>
      </div>

      <div class="footer-links">
        <h4>Quick Links</h4>
        <a href="../#services">Services</a>
        <a href="../#prices">Prices</a>
        <a href="../#about">About Us</a>
        <a href="index.html">Window Cleaning Guides & Tips</a>
      </div>

      <div class="footer-contact">
        <h4>Contact</h4>
        <p>📱 WhatsApp: <a href="https://wa.me/46737348390" target="_blank">+46 73 734 83 90</a></p>
        <p>📍 Address: <a href="https://www.google.com/maps/search/?api=1&query=Flottiljgatan+4,+723+48+Västerås" target="_blank" rel="noopener">Flottiljgatan 4, 723 48 Västerås</a></p>
        <p>💼 Approved for F-tax</p>
        <p>📧 Email: <a href="mailto:info@vasteras-puts.se">info@vasteras-puts.se</a></p>
      </div>
    </div>
    
    <div class="footer-bottom text-center">
      <p>&copy; 2026 Ren Fröjd. All rights reserved. Website created with care.</p>
    </div>
  </footer>"""
        
        if full_footer_pattern in content:
            content = content.replace(full_footer_pattern, replacement_footer)
            with open(articles_index_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Successfully updated full footer in en/artiklar/index.html")
        elif "Window Cleaning Guides & Tips" in content:
            print("Skipping (already updated) en/artiklar/index.html")
        else:
            print("Custom footer pattern not found in en/artiklar/index.html")
            
    # 5. Update all individual article HTML files in en/artiklar/
    articles_glob = os.path.join(prefix, "en/artiklar/*.html")
    article_files = glob.glob(articles_glob)
    
    updated_count = 0
    skipped_count = 0
    
    for path in article_files:
        # Skip the index.html page itself as we handled it separately
        if os.path.basename(path) == "index.html":
            continue
            
        success = update_file(
            path,
            '<a href="../#book">Book Cleaning</a>',
            '<a href="index.html">Window Cleaning Guides & Tips</a>'
        )
        if success:
            updated_count += 1
        else:
            skipped_count += 1
            
    print(f"\nDone! Updated {updated_count} individual articles, skipped/already present: {skipped_count}")

if __name__ == "__main__":
    main()
