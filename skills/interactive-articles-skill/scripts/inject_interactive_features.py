import os
import re

# CSS styles required for all interactive components
INTERACTIVE_CSS = """
/* --- Interactive Features --- */

/* --- Before/After Image Slider --- */
.before-after-slider {
  position: relative;
  width: 100%;
  max-width: 650px;
  margin: 40px auto;
  overflow: hidden;
  border-radius: 16px;
  box-shadow: 0 10px 25px rgba(0,0,0,0.08);
  aspect-ratio: 16 / 9;
}
.slider-image-container {
  position: relative;
  width: 100%;
  height: 100%;
}
.slider-image-container img {
  position: absolute;
  top: 0;
  left: 0;
  width: 100%;
  height: 100%;
  object-fit: cover;
  user-select: none;
}
.image-after-wrapper {
  position: absolute;
  top: 0;
  left: 0;
  height: 100%;
  overflow: hidden;
}
.image-after {
  width: 100%;
  height: 100%;
  object-fit: cover;
}
.slider-input {
  position: absolute;
  -webkit-appearance: none;
  appearance: none;
  width: 100%;
  height: 100%;
  background: transparent;
  opacity: 0;
  outline: none;
  margin: 0;
  cursor: ew-resize;
  z-index: 10;
}
.slider-handle {
  position: absolute;
  top: 0;
  bottom: 0;
  left: 50%;
  width: 4px;
  background: #ffffff;
  pointer-events: none;
  z-index: 5;
  box-shadow: 0 0 10px rgba(0,0,0,0.3);
}
.slider-handle::after {
  content: "↔";
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  width: 44px;
  height: 44px;
  background: #0ea5e9;
  color: #ffffff;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-weight: bold;
  font-size: 1.3rem;
  box-shadow: 0 4px 10px rgba(0,0,0,0.25);
  border: 2px solid #ffffff;
}

/* --- Collapsible Accordions (FAQ) --- */
.faq-accordion {
  background: #ffffff;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 12px;
  margin-bottom: 16px;
  overflow: hidden;
  transition: all 0.3s ease;
}
.faq-accordion[open] {
  box-shadow: var(--shadow-sm, 0 4px 6px rgba(0,0,0,0.05));
  border-color: #0ea5e9;
}
.faq-accordion summary {
  padding: 18px 24px;
  font-weight: 700;
  font-size: 1.1rem;
  cursor: pointer;
  list-style: none;
  position: relative;
  font-family: var(--font-heading);
  color: var(--secondary, #0f172a);
}
.faq-accordion summary::-webkit-details-marker {
  display: none;
}
.faq-accordion summary::after {
  content: "+";
  position: absolute;
  right: 24px;
  top: 50%;
  transform: translateY(-50%);
  font-size: 1.5rem;
  font-weight: 400;
  transition: transform 0.2s ease;
}
.faq-accordion[open] summary::after {
  content: "−";
  transform: translateY(-50%) rotate(180deg);
}
.faq-accordion-content {
  padding: 0 24px 20px 24px;
  line-height: 1.6;
  color: var(--text, #334155);
}

/* --- Interactive Testimonial Cards --- */
.article-testimonial {
  background: #f0fdfa; /* Light accent teal */
  border-left: 4px solid #14b8a6;
  border-radius: 0 16px 16px 0;
  padding: 24px 30px;
  margin: 35px 0;
}
.article-testimonial blockquote {
  font-style: italic;
  font-size: 1.05rem;
  color: var(--secondary, #0f172a);
  margin-bottom: 12px;
  border: none;
  padding: 0;
  background: transparent;
}
.article-testimonial-author {
  font-weight: 700;
  font-size: 0.95rem;
  color: #14b8a6;
  display: flex;
  align-items: center;
  gap: 8px;
}

/* --- Interactive RUT Calculator --- */
.rut-calculator {
  background: #ffffff;
  border: 1px solid var(--border, #e2e8f0);
  border-radius: 16px;
  padding: 30px;
  margin: 40px auto;
  max-width: 600px;
  box-shadow: 0 4px 6px rgba(0,0,0,0.02);
}
.rut-calc-header {
  text-align: center;
  margin-bottom: 24px;
}
.rut-calc-slider-container {
  margin-bottom: 24px;
}
.rut-calc-slider {
  width: 100%;
  margin-bottom: 8px;
}
.rut-calc-price-display {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  border-top: 1px solid #e2e8f0;
  padding-top: 20px;
}
.rut-calc-price-box {
  text-align: center;
  padding: 15px;
  border-radius: 12px;
}
.rut-calc-price-box.regular {
  background: #f8fafc;
}
.rut-calc-price-box.rut {
  background: #f0fdf4;
  border: 1px solid #bbf7d0;
  color: #16a34a;
}
.rut-calc-amount {
  font-size: 1.5rem;
  font-weight: 800;
  font-family: var(--font-heading);
}
"""

def inject_styles_to_css(styles_path):
    if not os.path.exists(styles_path):
        return
    with open(styles_path, 'r', encoding='utf-8') as f:
        content = f.read()
    
    if '/* --- Before/After Image Slider --- */' not in content:
        with open(styles_path, 'a', encoding='utf-8') as f:
            f.write("\n" + INTERACTIVE_CSS)
        print(f"Injected styles to {styles_path}")

def process_html_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        html = f.read()

    is_english = '/en/' in filepath
    
    # 1. Before/After Image Slider
    if 'before-after-slider' not in html:
        article_match = re.search(r'(<article class="article-content">.*?</nav>\s*<h1>.*?</h1>\s*<p[^>]*>⏱️.*?</p>\s*<p>.*?</p>)', html, re.DOTALL)
        if article_match:
            intro_p_block = article_match.group(1)
            if is_english:
                slider_html = """
    <!-- Interactive Before/After Image Slider -->
    <div class="before-after-slider">
      <div class="slider-image-container">
        <img class="image-before" src="../images/window-cleaning-vasteras-before.webp" alt="Window cleaning before - Ren Fröjd Västerås">
        <div class="image-after-wrapper" style="width: 50%;">
          <img class="image-after" src="../images/window-cleaning-vasteras-after.webp" alt="Window cleaning after - Ren Fröjd Västerås">
        </div>
        <input type="range" min="0" max="100" value="50" class="slider-input" aria-label="Before and after slider">
        <div class="slider-handle"></div>
      </div>
    </div>
"""
            else:
                slider_html = """
    <!-- Interactive Before/After Image Slider -->
    <div class="before-after-slider">
      <div class="slider-image-container">
        <img class="image-before" src="../images/fonsterputsning-vasteras-fore.webp" alt="Fönsterputsning före - Ren Fröjd Västerås">
        <div class="image-after-wrapper" style="width: 50%;">
          <img class="image-after" src="../images/fonsterputsning-vasteras-efter.webp" alt="Fönsterputsning efter - Ren Fröjd Västerås">
        </div>
        <input type="range" min="0" max="100" value="50" class="slider-input" aria-label="Före och efter skjutreglage">
        <div class="slider-handle"></div>
      </div>
    </div>
"""
            html = html.replace(intro_p_block, intro_p_block + "\n" + slider_html)
            print(f"  - Injected Before/After Slider")

    # 2. Testimonial Card Injection (before FAQs)
    if 'article-testimonial' not in html:
        # Locate H2 FAQ as anchor to insert testimonial before it
        faq_anchor = re.search(r'(<h2>(?:Vanliga frågor om fönsterputsning|Frequently Asked Questions).*?</h2>)', html)
        if faq_anchor:
            anchor_text = faq_anchor.group(1)
            if is_english:
                testimonial_html = """
    <!-- Interactive Client Testimonial -->
    <div class="article-testimonial">
      <blockquote>"Ren Fröjd does an amazing job with our windows in Västerås. Everything is super clean, no streaks, and the price of 300 SEK/hour is very transparent!"</blockquote>
      <div class="article-testimonial-author">
        <span>⭐ Anders L., Västerås (Lillåudden)</span>
      </div>
    </div>
"""
            else:
                testimonial_html = """
    <!-- Interactive Client Testimonial -->
    <div class="article-testimonial">
      <blockquote>"Ren Fröjd gör ett fantastiskt jobb med våra fönster i Västerås. Allt är superrent, inga ränder, och priset på 300 kr/timme är mycket transparent!"</blockquote>
      <div class="article-testimonial-author">
        <span>⭐ Anders L., Västerås (Lillåudden)</span>
      </div>
    </div>
"""
            html = html.replace(anchor_text, testimonial_html + "\n    " + anchor_text)
            print(f"  - Injected Testimonial Card")

    # 3. Interactive RUT Calculator
    if 'rut-calculator' not in html:
        # Insert RUT calculator before the booking CTA or closing article block
        book_anchor = re.search(r'(<div style="text-align: center; margin: 30px 0;"><a href=".*?#book" class="btn btn-primary">)', html)
        if book_anchor:
            anchor_text = book_anchor.group(1)
            if is_english:
                calc_html = """
    <!-- Interactive RUT Cost Calculator -->
    <div class="rut-calculator">
      <div class="rut-calc-header">
        <h3>Interactive Cleaning Price Estimator</h3>
        <p>Drag the slider to estimate standard rates vs. post-RUT deduction price</p>
      </div>
      <div class="rut-calc-slider-container">
        <label for="hours-slider" style="display:flex; justify-content:space-between; font-weight:600; margin-bottom:8px;">
          <span>Cleaning Hours:</span>
          <span class="hours-val">4 hours</span>
        </label>
        <input type="range" min="1" max="12" value="4" class="rut-calc-slider" id="hours-slider">
      </div>
      <div class="rut-calc-price-display">
        <div class="rut-calc-price-box regular">
          <div style="font-size:0.85rem; text-transform:uppercase; color:#64748b;">Standard Price</div>
          <div class="rut-calc-amount regular-val">2600 SEK</div>
          <div style="font-size:0.75rem; color:#64748b;">(Incl. travel fee)</div>
        </div>
        <div class="rut-calc-price-box rut">
          <div style="font-size:0.85rem; text-transform:uppercase; font-weight:700;">Your Post-RUT Price</div>
          <div class="rut-calc-amount rut-val">1300 SEK</div>
          <div style="font-size:0.75rem;">(Incl. travel fee)</div>
        </div>
      </div>
    </div>
"""
            else:
                calc_html = """
    <!-- Interactive RUT Cost Calculator -->
    <div class="rut-calculator">
      <div class="rut-calc-header">
        <h3>Interaktiv Prisberäknare</h3>
        <p>Dra i reglaget för att beräkna ordinarie pris vs. ditt pris efter RUT-avdrag</p>
      </div>
      <div class="rut-calc-slider-container">
        <label for="hours-slider" style="display:flex; justify-content:space-between; font-weight:600; margin-bottom:8px;">
          <span>Antal städtimmar:</span>
          <span class="hours-val">4 timmar</span>
        </label>
        <input type="range" min="1" max="12" value="4" class="rut-calc-slider" id="hours-slider">
      </div>
      <div class="rut-calc-price-display">
        <div class="rut-calc-price-box regular">
          <div style="font-size:0.85rem; text-transform:uppercase; color:#64748b;">Ordinarie pris</div>
          <div class="rut-calc-amount regular-val">2600 kr</div>
          <div style="font-size:0.75rem; color:#64748b;">(Inkl. resekostnad)</div>
        </div>
        <div class="rut-calc-price-box rut">
          <div style="font-size:0.85rem; text-transform:uppercase; font-weight:700;">Ditt pris efter RUT</div>
          <div class="rut-calc-amount rut-val">1300 kr</div>
          <div style="font-size:0.75rem;">(Inkl. resekostnad)</div>
        </div>
      </div>
    </div>
"""
            html = html.replace(anchor_text, calc_html + "\n    " + anchor_text)
            print(f"  - Injected RUT Calculator")

    # 4. FAQ Accordions Conversion
    faq_section_pattern = r'(<h2>(?:Vanliga frågor om fönsterputsning|Frequently Asked Questions).*?</h2>)(.*?)(<h2>|$|<!--)'
    faq_match = re.search(faq_section_pattern, html, re.DOTALL)
    if faq_match:
        faq_header = faq_match.group(1)
        faq_body = faq_match.group(2)
        faq_item_pattern = r'<h3>(.*?)</h3>\s*<p>(.*?)</p>'
        faq_items = re.findall(faq_item_pattern, faq_body, re.DOTALL)
        
        if faq_items:
            new_faq_body = "\n"
            for q, a in faq_items:
                new_faq_body += f'      <details class="faq-accordion">\n        <summary>{q.strip()}</summary>\n        <div class="faq-accordion-content">\n          <p>{a.strip()}</p>\n        </div>\n      </details>\n'
            html = html.replace(faq_header + faq_body, faq_header + "\n" + new_faq_body + "\n      ")
            print(f"  - Converted FAQs to Accordions")

    # 5. Injections of JavaScript Logics (Sliders + Calculator)
    if 'before-after-slider' in html and 'const sliders = document.querySelectorAll(".before-after-slider")' not in html:
        js_script = """
  <!-- Interactive Article Scripts -->
  <script>
    document.addEventListener("DOMContentLoaded", function() {
      // 1. Before/After Slider
      const sliders = document.querySelectorAll(".before-after-slider");
      sliders.forEach(function(slider) {
        const input = slider.querySelector(".slider-input");
        const wrapper = slider.querySelector(".image-after-wrapper");
        const handle = slider.querySelector(".slider-handle");
        input.addEventListener("input", function(e) {
          const value = e.target.value;
          wrapper.style.width = value + "%";
          handle.style.left = value + "%";
        });
      });

      // 2. Interactive RUT Calculator
      const calc = document.querySelector(".rut-calculator");
      if (calc) {
        const slider = calc.querySelector(".rut-calc-slider");
        const hoursDisplay = calc.querySelector(".hours-val");
        const regValDisplay = calc.querySelector(".regular-val");
        const rutValDisplay = calc.querySelector(".rut-val");

        const HOURLY_REGULAR = 600;
        const HOURLY_RUT = 300;
        const TRAVEL_REGULAR = 200;
        const TRAVEL_RUT = 100;

        function updatePrice() {
          const hours = parseInt(slider.value);
          const lang = document.documentElement.lang || "sv";
          hoursDisplay.textContent = hours + (lang === "en" ? " hours" : " timmar");
          
          const regTotal = (hours * HOURLY_REGULAR) + TRAVEL_REGULAR;
          const rutTotal = (hours * HOURLY_RUT) + TRAVEL_RUT;

          regValDisplay.textContent = regTotal + (lang === "en" ? " SEK" : " kr");
          rutValDisplay.textContent = rutTotal + (lang === "en" ? " SEK" : " kr");
        }

        slider.addEventListener("input", updatePrice);
        updatePrice();
      }
    });
  </script>
"""
        html = html.replace('</body>', js_script + '</body>')
        print(f"  - Injected Slider & Calculator Javascript")

    with open(filepath, 'w', encoding='utf-8') as f:
        f.write(html)

def run_batch():
    # Paths configuration
    paths = [
        ('/Users/blatik/Documents/mama/artiklar', '../'),
        ('/Users/blatik/Documents/mama/en/artiklar', '../../')
    ]
    
    # Inject styles
    inject_styles_to_css('/Users/blatik/Documents/mama/styles.css')
    
    total_processed = 0
    for folder, rel_root in paths:
        if not os.path.exists(folder):
            continue
        for filename in os.listdir(folder):
            if filename.endswith('.html') and filename != 'index.html':
                filepath = os.path.join(folder, filename)
                print(f"Processing {filename}...")
                process_html_file(filepath)
                
                # Correct image paths (e.g. if the relative root is different)
                with open(filepath, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                if rel_root == '../../':
                    content = content.replace('src="../images/window-cleaning-vasteras-before.webp"', 'src="../../images/window-cleaning-vasteras-before.webp"')
                    content = content.replace('src="../images/window-cleaning-vasteras-after.webp"', 'src="../../images/window-cleaning-vasteras-after.webp"')
                
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                total_processed += 1
                
    print(f"\nCompleted! Total processed: {total_processed} files.")

if __name__ == '__main__':
    run_batch()
