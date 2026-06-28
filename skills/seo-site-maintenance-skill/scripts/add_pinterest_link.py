import os
import glob

def add_pinterest_to_footers():
    print("=== ADDING PINTEREST TO SOCIAL FOOTERS ===")
    
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    pinterest_link_class = '\n          <a href="https://se.pinterest.com/renfrojd_vasteras/" target="_blank" rel="noopener" aria-label="Pinterest" class="social-link">Pinterest</a>'
    pinterest_link_style = '\n          <a href="https://se.pinterest.com/renfrojd_vasteras/" target="_blank" rel="noopener" aria-label="Pinterest" style="color: var(--text-light); text-decoration: none; font-weight: 500;">Pinterest</a>'
    
    # 1. Update rust generator template
    generator_path = os.path.join(prefix, "generator/src/main.rs")
    if os.path.exists(generator_path):
        with open(generator_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Look for the footer brand links in Rust template
        old_pattern = 'class="social-link">Facebook</a>'
        new_pattern = 'class="social-link">Facebook</a>\n          <a href="https://se.pinterest.com/renfrojd_vasteras/" target="_blank" rel="noopener" aria-label="Pinterest" class="social-link">Pinterest</a>'
        
        if old_pattern in content and new_pattern not in content:
            content = content.replace(old_pattern, new_pattern)
            with open(generator_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print("Updated generator/src/main.rs")

    # Find all HTML files
    html_files = []
    for root, dirs, files in os.walk(prefix if prefix else "."):
        if any(p in root for p in ['.git', '.vercel', 'node_modules', 'target']):
            continue
        for f in files:
            if f.endswith('.html'):
                html_files.append(os.path.join(root, f))
                
    print(f"Scanning {len(html_files)} HTML files...")
    
    updated_count = 0
    for path in html_files:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Pattern A: class="social-link"
        pattern_a_old = 'aria-label="Facebook" class="social-link">Facebook</a>'
        pattern_a_new = 'aria-label="Facebook" class="social-link">Facebook</a>' + pinterest_link_class
        
        # Pattern B: inline styles (catalog index & generated articles)
        pattern_b_old = 'aria-label="Facebook" style="color: var(--text-light); text-decoration: none; font-weight: 500;">Facebook</a>'
        pattern_b_new = 'aria-label="Facebook" style="color: var(--text-light); text-decoration: none; margin-right: 15px; font-weight: 500;">Facebook</a>' + pinterest_link_style
        
        # Also handle margin-right if already present on facebook link
        pattern_c_old = 'aria-label="Facebook" style="color: var(--text-light); text-decoration: none; margin-right: 15px; font-weight: 500;">Facebook</a>'
        pattern_c_new = 'aria-label="Facebook" style="color: var(--text-light); text-decoration: none; margin-right: 15px; font-weight: 500;">Facebook</a>' + pinterest_link_style

        if pattern_a_old in content and 'se.pinterest.com/renfrojd_vasteras' not in content:
            content = content.replace(pattern_a_old, pattern_a_new)
        
        if pattern_b_old in content and 'se.pinterest.com/renfrojd_vasteras' not in content:
            content = content.replace(pattern_b_old, pattern_b_new)
            
        if pattern_c_old in content and 'se.pinterest.com/renfrojd_vasteras' not in content:
            content = content.replace(pattern_c_old, pattern_c_new)
            
        if content != original_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            updated_count += 1
            
    print(f"Successfully added Pinterest link to {updated_count} HTML pages.")

if __name__ == "__main__":
    add_pinterest_to_footers()
