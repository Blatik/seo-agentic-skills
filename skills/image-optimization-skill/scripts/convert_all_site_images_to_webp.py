import os
import glob
import re
from PIL import Image

def convert_all_images_to_webp():
    print("=== CONVERTING ALL SITE CONTENT IMAGES TO WEBP ===")
    
    prefix = ""
    if not os.path.exists("en") and os.path.exists("../en"):
        prefix = "../"
        
    # 1. Target images in the root directory (excluding favicons and system icons)
    root_png_to_convert = [
        "stadfirma-vasteras-cover.png",
        "professional-window-cleaning-vasteras.png",
        "ren-frojd-window-cleaning-service-vasteras.png",
        "ren-frojd-stadning-ukrainsk-noggrannhet-vasteras.png",
        "professionell-hemstadning-vasteras-ren-frojd.png",
        "local-window-cleaner-vasteras-sweden.png",
        "window-cleaner-vasteras-ren-frojd.png",
        "fonsterputsning-vasteras-ren-frojd.jpg" # Also convert the Swedish main JPG image!
    ]
    
    converted_mapping = {} # maps old_filename -> new_filename
    
    for filename in root_png_to_convert:
        base_name = filename.rsplit(".", 1)[0]
        converted_mapping[filename] = base_name + ".webp"
        
        file_path = os.path.join(prefix, filename)
        if os.path.exists(file_path):
            webp_path = os.path.join(prefix, base_name + ".webp")
            try:
                with Image.open(file_path) as img:
                    img.save(webp_path, "WEBP", quality=85)
                os.remove(file_path)
                print(f"Converted root image: {filename} -> {base_name}.webp")
            except Exception as e:
                print(f"Error converting {filename}: {e}")
                
    # 2. Convert images in en/images/
    images_dir = os.path.join(prefix, "en/images")
    if os.path.exists(images_dir):
        png_files = glob.glob(os.path.join(images_dir, "*.png"))
        print(f"Found {len(png_files)} PNG images in en/images to convert.")
        for png_path in png_files:
            webp_path = png_path.rsplit(".", 1)[0] + ".webp"
            filename = os.path.basename(png_path)
            base_name = filename.rsplit(".", 1)[0]
            try:
                with Image.open(png_path) as img:
                    img.save(webp_path, "WEBP", quality=85)
                os.remove(png_path)
                converted_mapping[f"en/images/{filename}"] = f"en/images/{base_name}.webp"
                converted_mapping[f"images/{filename}"] = f"images/{base_name}.webp"
                converted_mapping[filename] = base_name + ".webp"
                print(f"Converted article image: {filename} -> {base_name}.webp")
            except Exception as e:
                print(f"Error converting {filename}: {e}")

    # 3. Scan and update all HTML files
    html_files = []
    for root, dirs, files in os.walk(prefix if prefix else "."):
        # Prune dirs in place to avoid recursing into ignored directories
        dirs[:] = [d for d in dirs if d not in ['.git', '.vercel', 'node_modules', 'target', '__pycache__']]
        for f in files:
            if f.endswith('.html'):
                html_files.append(os.path.join(root, f))
                
    print(f"Scanning {len(html_files)} HTML files to update image extensions...")
    
    updated_html_count = 0
    for path in html_files:
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        original_content = content
        
        # Replace occurrences of converted filenames in HTML
        for old_img, new_img in converted_mapping.items():
            # Match exact filenames in quotes, src tags or og:image tags
            content = content.replace(old_img, new_img)
            
        # Standard replacements for any generic .png matches inside articles (except favicons)
        if "artiklar" in path:
            # Replace standard image source inside generated articles
            content = re.sub(r'src="\.\./images/([^"]+)\.png"', r'src="../images/\1.webp"', content)
            # Replace schema image source
            content = re.sub(r'"image":\s*"https://vasteras-puts\.se/en/images/([^"]+)\.png"', r'"image": "https://vasteras-puts.se/en/images/\1.webp"', content)
            
        if content != original_content:
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content)
            updated_html_count += 1
            print(f"Updated HTML file: {os.path.basename(path)}")
            
    print(f"Successfully converted images and updated {updated_html_count} HTML files!")

if __name__ == "__main__":
    convert_all_images_to_webp()
