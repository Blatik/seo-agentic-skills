import os
import sys
import re
import urllib.request
import urllib.parse
import ssl
from html.parser import HTMLParser
from collections import deque

# Bypass SSL certificate verification issues
ssl_context = ssl._create_unverified_context()

class LinkParser(HTMLParser):
    def __init__(self, base_url):
        super().__init__()
        self.base_url = base_url
        self.links = []
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href', '').strip()
            self.current_link = {
                'href': href,
                'anchor': ''
            }

    def handle_endtag(self, tag):
        if tag == 'a' and self.current_link is not None:
            self.links.append(self.current_link)
            self.current_link = None

    def handle_data(self, data):
        if self.current_link is not None:
            self.current_link['anchor'] += data


def check_url_status(url):
    """Sends a HEAD request (or GET if HEAD fails) to check if a URL is broken."""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    # Clean URL (remove fragment)
    clean_url = url.split('#')[0]
    
    try:
        # Try HEAD first
        req = urllib.request.Request(clean_url, headers=headers, method='HEAD')
        with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
            return response.status == 200
    except Exception:
        try:
            # Fallback to GET
            req = urllib.request.Request(clean_url, headers=headers, method='GET')
            with urllib.request.urlopen(req, context=ssl_context, timeout=5) as response:
                return response.status == 200
        except Exception:
            return False


# --- LOCAL FILE AUDIT MODE ---
class LocalLinkExtractor(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []
        self.current_link = None

    def handle_starttag(self, tag, attrs):
        if tag == 'a':
            attrs_dict = dict(attrs)
            href = attrs_dict.get('href', '').strip()
            self.current_link = {
                'href': href,
                'anchor': ''
            }

    def handle_endtag(self, tag):
        if tag == 'a' and self.current_link is not None:
            self.links.append(self.current_link)
            self.current_link = None

    def handle_data(self, data):
        if self.current_link is not None:
            self.current_link['anchor'] += data

def audit_local_files(root_dir):
    print(f"\n📁 ЗАПУСК ЛОКАЛЬНОГО АУДИТУ ФАЙЛІВ У ПАПЦІ: {root_dir}")
    print("=" * 80)
    
    html_files = []
    for root, dirs, files in os.walk(root_dir):
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'target', '.vercel', 'generator']]
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
                
    print(f"Знайдено {len(html_files)} HTML-файлів на диску.\n")
    
    outgoing_links = {}
    incoming_links = {os.path.relpath(f, root_dir): set() for f in html_files}
    broken_links = []
    
    for file_path in html_files:
        rel_src = os.path.relpath(file_path, root_dir)
        outgoing_links[rel_src] = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        parser = LocalLinkExtractor()
        parser.feed(content)
        
        for link in parser.links:
            href = link['href'].strip()
            anchor_text = link['anchor'].strip()
            
            if not href or href.startswith(('http://', 'https://', '#', 'mailto:', 'tel:', 'javascript:')):
                continue
                
            clean_href = href.split('#')[0].split('?')[0]
            if not clean_href:
                continue
                
            file_dir = os.path.dirname(file_path)
            target_path = os.path.normpath(os.path.join(file_dir, clean_href))
            rel_target = os.path.relpath(target_path, root_dir)
            
            link_info = {
                'raw_href': href,
                'rel_target': rel_target,
                'target_exists': os.path.exists(target_path),
                'anchor_text': anchor_text
            }
            
            outgoing_links[rel_src].append(link_info)
            
            if link_info['target_exists']:
                if rel_target in incoming_links:
                    incoming_links[rel_target].add(rel_src)
            else:
                broken_links.append({
                    'source': rel_src,
                    'href': href,
                    'anchor': anchor_text
                })
                
    # Show Summary
    print("--- АНАЛІЗ ЛОКАЛЬНИХ ПОСИЛАНЬ ---")
    total_internal_links = sum(len(links) for links in outgoing_links.values())
    print(f"• Всього знайдено внутрішніх посилань: {total_internal_links}")
    print(f"• Битих посилань (неіснуючі файли):    {len(broken_links)}")
    
    if broken_links:
        print("\n❌ БИТІ ВНУТРІШНІ ПОСИЛАННЯ:")
        for idx, bl in enumerate(broken_links[:30], 1):
            print(f"  [{idx}] У файлі: {bl['source']}")
            print(f"      Веде на:  {bl['href']}")
            print(f"      Анкор:    \"{bl['anchor']}\"")
    else:
        print("\n✅ Битих внутрішніх посилань не знайдено!")
        
    # Check for orphans
    orphans = []
    poorly_linked = []
    
    for rel_path, in_set in incoming_links.items():
        filename = os.path.basename(rel_path)
        if filename == 'index.html' and rel_path in ['index.html', 'en/index.html']:
            continue
            
        in_count = len(in_set)
        if in_count == 0:
            orphans.append(rel_path)
        elif in_count < 2:
            poorly_linked.append((rel_path, in_count))
            
    print(f"\n⚠️ СТОРІНКИ-СИРОТИ ({len(orphans)} сторінок без вхідних лінків):")
    if orphans:
        for idx, path in enumerate(sorted(orphans), 1):
            print(f"  [{idx}] {path}")
    else:
        print("  Жодної!")
        
    print(f"\n⚠️ СЛАБКО ПЕРЕЛІНКОВАНІ СТОРІНКИ ({len(poorly_linked)} сторінок з менш ніж 2 вхідними лінками):")
    if poorly_linked:
        for idx, (path, count) in enumerate(sorted(poorly_linked, key=lambda x: (x[1], x[0]))[:30], 1):
            print(f"  [{idx}] {path} (Вхідних лінків: {count})")
    else:
        print("  Жодної!")


# --- LIVE WEBSITE AUDIT MODE (CRAWLER) ---
def audit_live_website(start_url):
    print(f"\n🌐 ЗАПУСК АУДИТУ ЖИВОГО САЙТУ (CRAWLER): {start_url}")
    print("=" * 80)
    
    parsed_start = urllib.parse.urlparse(start_url)
    domain = parsed_start.netloc
    base_scheme = parsed_start.scheme
    
    # Store visited URLs and queues
    visited_pages = set()
    queue = deque([start_url])
    
    # Link relations: map page URL to list of found links (href, anchor)
    link_graph = {}
    # Track incoming links count: map target URL to set of source URLs
    incoming_links = {}
    
    # Track HTTP status codes of pages to check for broken links
    url_status_cache = {}
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
    }
    
    max_crawl_pages = 999999
    pages_crawled = 0
    
    print("Починаємо сканування сайту...")
    
    while queue:
        current_url = queue.popleft()
        
        # Clean fragment
        clean_current = current_url.split('#')[0]
        if clean_current in visited_pages:
            continue
            
        print(f"Скануємо [{pages_crawled + 1}]: {clean_current}")
        visited_pages.add(clean_current)
        pages_crawled += 1
        
        try:
            req = urllib.request.Request(clean_current, headers=headers)
            with urllib.request.urlopen(req, context=ssl_context, timeout=8) as response:
                if 'text/html' not in response.headers.get('Content-Type', '').lower():
                    continue
                final_url = response.geturl()
                html = response.read().decode('utf-8', errors='ignore')
                url_status_cache[clean_current] = 200
        except urllib.error.HTTPError as e:
            url_status_cache[clean_current] = e.code
            print(f"  ❌ Помилка завантаження: HTTP {e.code}")
            continue
        except Exception as e:
            url_status_cache[clean_current] = 0
            print(f"  ❌ Мережева помилка: {e}")
            continue
            
        parser = LinkParser(final_url)
        parser.feed(html)
        
        link_graph[clean_current] = []
        
        for link in parser.links:
            href = link['href'].strip()
            anchor_text = link['anchor'].strip().replace('\n', ' ')
            
            if not href or href.startswith(('mailto:', 'tel:', 'javascript:')):
                continue
                
            # Resolve full target URL relative to final redirected URL
            resolved_url = urllib.parse.urljoin(final_url, href)
            clean_resolved = resolved_url.split('#')[0]
            
            parsed_target = urllib.parse.urlparse(clean_resolved)
            is_internal = (parsed_target.netloc == domain)
            
            link_info = {
                'raw_href': href,
                'resolved_url': clean_resolved,
                'is_internal': is_internal,
                'anchor': anchor_text
            }
            
            link_graph[clean_current].append(link_info)
            
            # If internal page and not visited/queued, add to queue
            if is_internal and clean_resolved not in visited_pages and clean_resolved not in queue:
                # Make sure it's an HTML page (not image or zip)
                ext = os.path.splitext(parsed_target.path)[1].lower()
                if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.pdf', '.zip', '.xml', '.txt']:
                    queue.append(clean_resolved)
            
            # Track incoming links for internal URLs
            if is_internal:
                if clean_resolved not in incoming_links:
                    incoming_links[clean_resolved] = set()
                incoming_links[clean_resolved].add(clean_current)
                
    print("\nСканування завершено! Перевіряємо підозрілі посилання...")
    
    # Verify status of all linked URLs
    all_targets = set()
    for source_url, links in link_graph.items():
        for link in links:
            all_targets.add(link['resolved_url'])
            
    broken_links = []
    
    # Validate each link target
    for target in sorted(all_targets):
        if target in url_status_cache:
            status_ok = (url_status_cache[target] == 200)
        else:
            # Check target status live
            status_ok = check_url_status(target)
            url_status_cache[target] = 200 if status_ok else 404
            
        if not status_ok:
            # Find where this broken link was referenced
            for source, links in link_graph.items():
                for link in links:
                    if link['resolved_url'] == target:
                        broken_links.append({
                            'source': source,
                            'target': target,
                            'raw_href': link['raw_href'],
                            'anchor': link['anchor']
                        })
                        
    # Analysis
    print("\n" + "="*80)
    print("📊 ЗВІТ ПО САЙТУ (LIVE WEBSITE REPORT):")
    print("=" * 80)
    print(f"• Оброблено унікальних сторінок: {pages_crawled}")
    print(f"• Знайдено битих посилань (HTTP errors): {len(broken_links)}")
    
    if broken_links:
        print("\n❌ БИТІ ПОСИЛАННЯ НА САЙТІ:")
        for idx, bl in enumerate(broken_links[:40], 1):
            print(f"  [{idx}] На сторінці: {bl['source']}")
            print(f"      Веде на:     {bl['target']} (код: {url_status_cache.get(bl['target'], 'error')})")
            print(f"      Анкор:       \"{bl['anchor']}\"")
    else:
        print("\n✅ Битих посилань на живому сайті не знайдено!")
        
    # Check for orphans
    orphans = []
    poorly_linked = []
    
    # Internal pages crawled
    internal_crawled = [url for url in visited_pages if url_status_cache.get(url) == 200]
    
    for page in internal_crawled:
        # Skip the homepage
        if page.strip('/') == start_url.strip('/'):
            continue
            
        in_set = incoming_links.get(page, set())
        in_count = len(in_set)
        
        if in_count == 0:
            orphans.append(page)
        elif in_count < 2:
            poorly_linked.append((page, in_count))
            
    print(f"\n⚠️ СТОРІНКИ-СИРОТИ ({len(orphans)} сторінок без вхідних лінків):")
    if orphans:
        for idx, path in enumerate(sorted(orphans), 1):
            print(f"  [{idx}] {path}")
    else:
        print("  Жодної!")
        
    print(f"\n⚠️ СЛАБКО ПЕРЕЛІНКОВАНІ СТОРІНКИ ({len(poorly_linked)} сторінок з менш ніж 2 вхідними лінками):")
    if poorly_linked:
        for idx, (path, count) in enumerate(sorted(poorly_linked, key=lambda x: (x[1], x[0]))[:30], 1):
            print(f"  [{idx}] {path} (Вхідних лінків: {count})")
    else:
        print("  Жодної!")


if __name__ == "__main__":
    print("=== УНІВЕРСАЛЬНИЙ АУДИТ ПЕРЕЛІНКУВАННЯ ===")
    print("1. Локальний аудит файлів (на диску)")
    print("2. Живий аудит сайту (crawling live website)")
    
    try:
        choice = input("Оберіть режим роботи (1 або 2, за замовчуванням 1): ").strip()
        if not choice:
            choice = "1"
            
        if choice == "1":
            script_dir = os.path.dirname(os.path.abspath(__file__))
            default_path = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
            path_input = input(f"Введіть шлях до папки сайту (або натисніть Enter для {default_path}): ").strip()
            root_path = path_input if path_input else default_path
            audit_local_files(root_path)
            
        elif choice == "2":
            url_input = input("Введіть стартовий URL сайту (наприклад, https://vasteras-puts.se/): ").strip()
            if not url_input:
                url_input = "https://vasteras-puts.se/"
            # Ensure URL has scheme
            if not url_input.startswith(('http://', 'https://')):
                url_input = "https://" + url_input
            audit_live_website(url_input)
        else:
            print("Невірний вибір. Завершення роботи.")
    except KeyboardInterrupt:
        print("\nРобота перервана користувачем.")
