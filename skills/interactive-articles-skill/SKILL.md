# Interactive Articles Injection Skill

This skill enables AI agents to batch-inject interactive features into SEO articles to increase user engagement (dwell time), improve readability, and boost conversions.

## Features Injected

1. **Before/After Image Slider**:
   - A dual-image overlay wrapper allowing users to drag a slider handle left-right to preview dirty vs clean window results.
   - Uses SEO-optimized, localized file names: `fonsterputsning-vasteras-fore.webp`/`fonsterputsning-vasteras-efter.webp` (Swedish) and `window-cleaning-vasteras-before.webp`/`window-cleaning-vasteras-after.webp` (English).

2. **Collapsible FAQ Accordions**:
   - Converts standard, text-heavy `<h3>` (question) and `<p>` (answer) elements under the FAQ header into lightweight HTML `<details>` toggles.

3. **Interactive Price Estimator (RUT Calculator)**:
   - A range slider that estimates standard prices vs post-RUT prices (300 SEK/hour + travel fee) in real-time, illustrating the 50% discount value.

4. **Client Testimonial Cards**:
   - Injects a stylized testimonial quote from a local Västerås client (e.g., in Lillåudden) to build trust.

---

## Instructions for AI Agents

1. **Setup Assets**:
   Make sure the following WebP assets are stored in the website's `images/` directory:
   - `fonsterputsning-vasteras-fore.webp`
   - `fonsterputsning-vasteras-efter.webp`
   - `window-cleaning-vasteras-before.webp`
   - `window-cleaning-vasteras-after.webp`

2. **Execute Batch Injection**:
   Run the injection script from the project root:
   ```bash
   python3 skills/interactive-articles-skill/scripts/inject_interactive_features.py
   ```

3. **Validation**:
   Always run HTML validation scripts to ensure tag matching integrity after executing the batch script.
