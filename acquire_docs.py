import os
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
from tqdm import tqdm
import time
import re
import config

DOC_SOURCES = [
    {"name": "Python Standard Library", "start_url": "https://docs.python.org/3/library/", "content_selector": "div.body", "crawl_limit": 100},
    {"name": "Requests Library", "start_url": "https://requests.readthedocs.io/en/latest/", "content_selector": "div.section", "crawl_limit": 50},
]

def crawl_and_extract_docs(source_config, save_base_dir, progress_callback=None, log_message_callback=None):
    start_url = source_config["start_url"]
    base_domain = urlparse(start_url).netloc
    content_selector = source_config["content_selector"]
    max_pages = source_config["crawl_limit"]
    source_name_sanitized = source_config["name"].replace(" ", "_").lower()
    save_dir = os.path.join(save_base_dir, source_name_sanitized)

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        if log_message_callback:
            log_message_callback(f"Created directory: {save_dir}/")

    visited_urls, urls_to_visit, page_count = set(), [start_url], 0
    if log_message_callback:
        log_message_callback(f"Starting crawl for {source_config['name']}...")

    total_pages = max_pages
    for i in range(max_pages):
        if not urls_to_visit:
            if log_message_callback:
                log_message_callback("No more URLs to crawl.")
            break
        
        current_url = urls_to_visit.pop(0)
        if current_url in visited_urls:
            continue
        
        visited_urls.add(current_url)
        
        if progress_callback:
            progress_callback(i + 1, total_pages, f"Crawling Page {i+1}/{total_pages}")
        
        try:
            response = requests.get(current_url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'lxml')
            content_element = soup.select_one(content_selector)
            text_content = content_element.get_text(separator='\n', strip=True) if content_element else "Content not found."
            
            filename_base = urlparse(current_url).path.strip('/').replace('/', '_').replace('.html', '') or "index"
            with open(os.path.join(save_dir, f"{filename_base}.txt"), 'w', encoding='utf-8') as f:
                f.write(text_content)

            for link in soup.find_all('a', href=True):
                full_url = urljoin(current_url, link['href'])
                if urlparse(full_url).netloc == base_domain and full_url not in visited_urls and full_url not in urls_to_visit:
                    urls_to_visit.append(full_url)
            
        except requests.exceptions.RequestException as e:
            if log_message_callback:
                log_message_callback(f"Request error for {current_url}: {e}")

    if log_message_callback:
        log_message_callback(f"Crawl for {source_config['name']} finished.")

def acquire_all_documentation(progress_callback=None, log_message_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    _log("Starting documentation acquisition...")
    for source_config in DOC_SOURCES:
        crawl_and_extract_docs(source_config, config.BASE_DOCS_SAVE_DIR, progress_callback, _log)
        time.sleep(1)
    _log("All documentation acquisition processes completed.")