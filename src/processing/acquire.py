# src/processing/acquire.py
import os
import re
from urllib.parse import urlparse
from ..config import settings

"""Utilities for scraping documentation from the web."""

# --- FIXED: Use relative imports for modules within the same package ---
from ..core.ai_tools import browse_web_tool

def crawl_docs(urls: list, output_dir: str, **kwargs):
    """
    Crawls a list of URLs, scrapes their text content, and saves each to a file.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)

    os.makedirs(output_dir, exist_ok=True)
    total_urls = len(urls)
    log_message_callback(f"Starting crawl of {total_urls} URLs...")

    for i, url in enumerate(urls):
        progress_callback(i + 1, total_urls, f"Scraping {url}")
        try:
            log_message_callback(f"Scraping content from: {url}")
            content = browse_web_tool(url, log_message_callback=log_message_callback)

            if content and not content.startswith("Error"):
                # Create a safe filename from the URL
                parsed_url = urlparse(url)
                # Take the domain and path, replace special chars
                filename = f"{parsed_url.netloc}{parsed_url.path}".strip("/\\")
                filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
                # Truncate if too long
                filename = (filename[:100] + '..') if len(filename) > 100 else filename
                filepath = os.path.join(output_dir, f"{filename}.txt")

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                log_message_callback(f"Saved content to {filepath}")
            else:
                log_message_callback(f"Failed to scrape or no content found for: {url}")

        except Exception as e:
            log_message_callback(f"An error occurred while processing {url}: {e}")

    log_message_callback("Web scraping process complete.")
    return "Success"
