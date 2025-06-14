# acquire_docs.py
import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import config
import time

def crawl_and_extract_docs(source_config, save_base_dir, progress_callback=None, log_message_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    
    start_url = source_config['start_url']
    source_name = source_config['name']
    save_dir = os.path.join(save_base_dir, source_name)
    os.makedirs(save_dir, exist_ok=True)
    
    _log(f"Starting crawl for '{source_name}' from {start_url}")

    urls_to_visit = [start_url]
    visited_urls = set()
    crawl_limit = source_config.get('crawl_limit', 50)
    base_domain = urlparse(start_url).netloc
    
    page_count = 0
    while urls_to_visit and page_count < crawl_limit:
        current_url = urls_to_visit.pop(0)
        if current_url in visited_urls:
            continue

        try:
            response = requests.get(current_url, timeout=15)
            response.raise_for_status()
            visited_urls.add(current_url)
            page_count += 1
            
            if progress_callback:
                progress_callback(page_count, crawl_limit, f"Crawling {source_name}: {page_count}/{crawl_limit}")

            soup = BeautifulSoup(response.text, 'lxml')
            content_element = soup.select_one(source_config['content_selector'])
            text_content = content_element.get_text(separator='\n', strip=True) if content_element else "Content not found."
            
            filename_base = urlparse(current_url).path.strip('/').replace('/', '_').replace('.html', '') or "index"
            safe_filename = "".join([c for c in filename_base if c.isalpha() or c.isdigit() or c in ('_','-')]).rstrip()
            if not safe_filename: safe_filename = f"page_{page_count}"

            with open(os.path.join(save_dir, f"{safe_filename}.txt"), 'w', encoding='utf-8') as f:
                f.write(text_content)
                
            for link in soup.find_all('a', href=True):
                full_url = urljoin(current_url, link['href'])
                if urlparse(full_url).netloc == base_domain and full_url not in visited_urls and full_url not in urls_to_visit:
                    urls_to_visit.append(full_url)
            
            time.sleep(0.1) 

        except requests.RequestException as e:
            _log(f"Could not fetch {current_url}: {e}")

    _log(f"Finished crawling '{source_name}'. Visited {page_count} pages.")

def acquire_docs_for_language(language, progress_callback=None, log_message_callback=None):
    """Acquires all documentation for a specified language from the sources in config."""
    _log = log_message_callback if callable(log_message_callback) else print
    
    if language not in config.DOCUMENTATION_SOURCES:
        _log(f"Error: Language '{language}' not found in config.py")
        return

    sources = config.DOCUMENTATION_SOURCES[language]
    _log(f"Starting documentation acquisition for {language}...")

    for source_config in sources:
        crawl_and_extract_docs(source_config, config.BASE_DOCS_SAVE_DIR, progress_callback, _log)

    _log(f"All documentation acquisition processes for {language} completed.")