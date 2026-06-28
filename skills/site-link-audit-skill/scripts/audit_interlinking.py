import os
import re
import urllib.parse
from html.parser import HTMLParser

class LinkExtractor(HTMLParser):
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

def audit_interlinking(root_dir):
    print("=== STARTING SITE-WIDE INTERLINKING AUDIT ===")
    
    # Resolve paths
    html_files = []
    # Search for all HTML files recursively in the workspace
    for root, dirs, files in os.walk(root_dir):
        # Exclude directories like .git, node_modules, target, etc.
        dirs[:] = [d for d in dirs if d not in ['.git', 'node_modules', 'target', '.vercel', 'generator']]
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
                
    print(f"Found {len(html_files)} HTML files on the site.\n")
    
    # Map from relative file path on disk to list of outgoing links
    # and map from relative file path to set of incoming links.
    outgoing_links = {}
    incoming_links = {os.path.relpath(f, root_dir): set() for f in html_files}
    broken_links = []
    
    for file_path in html_files:
        rel_src = os.path.relpath(file_path, root_dir)
        outgoing_links[rel_src] = []
        
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
            
        parser = LinkExtractor()
        parser.feed(content)
        
        for link in parser.links:
            href = link['href'].strip()
            anchor_text = link['anchor'].strip()
            
            # Skip external links, anchors, mailto, tel, javascript, etc.
            if not href or href.startswith(('http://', 'https://', '#', 'mailto:', 'tel:', 'javascript:')):
                continue
                
            # Remove query parameters or hash from href
            clean_href = href.split('#')[0].split('?')[0]
            if not clean_href:
                continue
                
            # Resolve the path relative to the current file's directory
            file_dir = os.path.dirname(file_path)
            target_path = os.path.normpath(os.path.join(file_dir, clean_href))
            
            # Get relative path from root_dir
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
                
    # Analysis
    print("--- ANALYSIS SUMMARY ---")
    total_internal_links = sum(len(links) for links in outgoing_links.values())
    print(f"Total internal links found: {total_internal_links}")
    print(f"Broken internal links: {len(broken_links)}")
    
    if broken_links:
        print("\n❌ BROKEN INTERNAL LINKS:")
        # Show first 30 broken links to avoid spamming terminal
        for idx, bl in enumerate(broken_links[:30], 1):
            print(f"  [{idx}] In file: {bl['source']}")
            print(f"      Points to: {bl['href']}")
            print(f"      Anchor: \"{bl['anchor']}\"")
        if len(broken_links) > 30:
            print(f"  ... and {len(broken_links) - 30} more broken links.")
    else:
        print("\n✅ No broken internal links found!")
        
    # Check for orphans (0 incoming links)
    orphans = []
    poorly_linked = []
    
    for rel_path, in_set in incoming_links.items():
        # Skip main index files from being counted as orphans
        filename = os.path.basename(rel_path)
        if filename == 'index.html' and rel_path in ['index.html', 'en/index.html']:
            continue
            
        in_count = len(in_set)
        if in_count == 0:
            orphans.append(rel_path)
        elif in_count < 2:
            poorly_linked.append((rel_path, in_count))
            
    print(f"\n⚠️ ORPHAN PAGES ({len(orphans)} pages with 0 incoming links):")
    if orphans:
        for idx, path in enumerate(sorted(orphans), 1):
            print(f"  [{idx}] {path}")
    else:
        print("  None!")
        
    print(f"\n⚠️ POORLY LINKED PAGES ({len(poorly_linked)} pages with < 2 incoming links):")
    if poorly_linked:
        # Show up to 30 poorly linked pages
        for idx, (path, count) in enumerate(sorted(poorly_linked, key=lambda x: (x[1], x[0]))[:30], 1):
            print(f"  [{idx}] {path} (Incoming links: {count})")
        if len(poorly_linked) > 30:
            print(f"  ... and {len(poorly_linked) - 30} more poorly linked pages.")
    else:
        print("  None!")
        
    # Link distribution statistics
    print("\n📈 LINK DISTRIBUTION STATISTICS:")
    in_counts = [len(in_set) for in_set in incoming_links.values()]
    out_counts = [len(links) for links in outgoing_links.values()]
    
    if in_counts:
        print(f"  Incoming links per page: Min={min(in_counts)}, Max={max(in_counts)}, Avg={sum(in_counts)/len(in_counts):.1f}")
    if out_counts:
        print(f"  Outgoing links per page: Min={min(out_counts)}, Max={max(out_counts)}, Avg={sum(out_counts)/len(out_counts):.1f}")
        
    print("\n=== AUDIT COMPLETE ===")

if __name__ == "__main__":
    script_dir = os.path.dirname(os.path.abspath(__file__))
    workspace_root = os.path.abspath(os.path.join(script_dir, "..", "..", ".."))
    audit_interlinking(workspace_root)
