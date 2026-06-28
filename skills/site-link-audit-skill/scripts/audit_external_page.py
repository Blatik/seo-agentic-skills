import sys
import urllib.request
import urllib.parse
import ssl
import re
from html.parser import HTMLParser

# Bypass SSL certificate verification issues
ssl_context = ssl._create_unverified_context()

class LinkParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.base_domain = urllib.parse.urlparse(base_url).netloc
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href', '').strip()
            if not href or href.startswith(('javascript:', 'mailto:', 'tel:', '#')):
                return
                
            # Resolve relative URLs
            full_url = urllib.parse.urljoin(self.base_url, href)
            target_domain = urllib.parse.urlparse(full_url).netloc
            
            # Determine if internal or external
            is_internal = (target_domain == self.base_domain)
            
            # Check rel attribute for nofollow
            rel = attrs_dict.get('rel', '').lower()
            is_nofollow = 'nofollow' in rel
            
            self.links.append({
                'raw_href': href,
                'url': full_url,
                'domain': target_domain,
                'is_internal': is_internal,
                'is_nofollow': is_nofollow,
                'anchor_text': ''
            })

    def handle_data(self, data):
        if self.links:
            # Append text to the last parsed link
            self.links[-1]['anchor_text'] += data.strip()

def audit_page_links(url):
    print("\n" + "="*80)
    print(f"🕵️‍♂️ АНАЛІЗ ЗОВНІШНІХ ТА ВНУТРІШНІХ ПОСИЛАНЬ ДЛЯ СТОРІНКИ:")
    print(f"🔗 URL: {url}")
    print("="*80)
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, context=ssl_context) as response:
            html = response.read().decode('utf-8', errors='ignore')
    except Exception as e:
        print(f"❌ Помилка при завантаженні сторінки: {e}")
        return
    
    parser = LinkParser(url)
    parser.feed(html)
    
    links = parser.links
    
    # Calculate statistics
    total_links = len(links)
    internal_dofollow = sum(1 for l in links if l['is_internal'] and not l['is_nofollow'])
    internal_nofollow = sum(1 for l in links if l['is_internal'] and l['is_nofollow'])
    external_dofollow = sum(1 for l in links if not l['is_internal'] and not l['is_nofollow'])
    external_nofollow = sum(1 for l in links if not l['is_internal'] and l['is_nofollow'])
    
    print("\n📊 ЗАГАЛЬНА СТАТИСТИКА ПОСИЛАНЬ:")
    print("-" * 50)
    print(f"• Всього знайдено посилань:         {total_links}")
    print(f"• Внутрішні Dofollow (тримають вагу):  {internal_dofollow}")
    print(f"• Внутрішні Nofollow (безпечні):       {internal_nofollow}")
    print(f"• Зовнішні Dofollow (віддають вагу!):  {external_dofollow}")
    print(f"• Зовнішні Nofollow (не передають):   {external_nofollow}")
    print("-" * 50)
    
    # 1. External Dofollow (Passing SEO authority out)
    print("\n🔴 ЗОВНІШНІ DOFOLLOW ПОСИЛАННЯ (Вихідна сила сайту):")
    print("⚠️  Ці лінки передають авторитет вашого домену іншим сайтам!")
    print("=" * 80)
    ext_dofollow_list = [l for l in links if not l['is_internal'] and not l['is_nofollow']]
    if ext_dofollow_list:
        for idx, l in enumerate(ext_dofollow_list, 1):
            anchor = l['anchor_text'].replace('\n', ' ').strip() or "[Зображення або порожній анкор]"
            print(f" [{idx}] URL: {l['url']}")
            print(f"     Анкор-текст: \"{anchor}\"")
            print("-" * 80)
    else:
        print("✅ Не знайдено жодного зовнішнього dofollow посилання. Сила сайту не втрачається!")
        print("=" * 80)
        
    # 2. All External Links (Detailed table)
    print("\n📋 ПОВНИЙ СПИСОК УСІХ ЗОВНІШНІХ ПОСИЛАНЬ (Dofollow та Nofollow):")
    print("=" * 80)
    ext_all = [l for l in links if not l['is_internal']]
    if ext_all:
        for idx, l in enumerate(ext_all, 1):
            rel_type = "🔴 DOFOLLOW" if not l['is_nofollow'] else "🟢 NOFOLLOW"
            anchor = l['anchor_text'].replace('\n', ' ').strip() or "[Зображення/Порожньо]"
            print(f" [{idx}] Тип: {rel_type}")
            print(f"     Ціль: {l['url']}")
            print(f"     Текст: \"{anchor}\"")
            print("-" * 80)
    else:
        print("Зовнішніх посилань не знайдено.")
        print("=" * 80)

if __name__ == "__main__":
    if len(sys.argv) > 1:
        target_url = sys.argv[1]
    else:
        user_input = input("Введіть URL сторінки для аналізу лінків (або натисніть Enter для дефолтного https://renfrojd.nu/category/mat-dryck/): ").strip()
        target_url = user_input if user_input else "https://renfrojd.nu/category/mat-dryck/"
    audit_page_links(target_url)
