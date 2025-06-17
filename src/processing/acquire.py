# src/processing/acquire.py
import os
import re
from urllib.parse import urlparse
from ..config import settings

# --- FIXED: Use relative imports for modules within the same package ---
from ..core.ai_tools import browse_web_tool

def crawl_docs(urls: list, output_dir: str, **kwargs):
    """
    Enhanced crawler that scrapes documentation with multiple hyperlinks,
    navigation elements, and pagination.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)
    
    # Enhanced scraping parameters
    max_pages = kwargs.get('max_pages', 15)  # Increased from default 10
    max_depth = kwargs.get('max_depth', 4)   # Increased from default 3
    same_domain_only = kwargs.get('same_domain_only', True)

    os.makedirs(output_dir, exist_ok=True)
    total_urls = len(urls)
    log_message_callback(f"Starting enhanced crawl of {total_urls} URLs...")
    log_message_callback(f"Configuration: max_pages={max_pages}, max_depth={max_depth}, same_domain_only={same_domain_only}")

    for i, url in enumerate(urls):
        progress_callback(i + 1, total_urls, f"Enhanced scraping {url}")
        try:
            log_message_callback(f"Enhanced scraping content from: {url}")
            
            # Use enhanced web scraping with configurable parameters
            content = browse_web_tool(
                url, 
                log_message_callback=log_message_callback,
                max_pages=max_pages,
                max_depth=max_depth,
                same_domain_only=same_domain_only
            )

            if content and not content.startswith("Error"):
                # Create a safe filename from the URL
                parsed_url = urlparse(url)
                # Take the domain and path, replace special chars
                filename = f"{parsed_url.netloc}{parsed_url.path}".strip("/\\")
                filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
                # Truncate if too long
                filename = (filename[:100] + '..') if len(filename) > 100 else filename
                filepath = os.path.join(output_dir, f"{filename}_enhanced.txt")

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                log_message_callback(f"Saved enhanced content to {filepath}")
                
                # Log content statistics
                content_length = len(content)
                pages_estimate = content.count("=== MAIN PAGE ===") + content.count("=== RELATED PAGE ===")
                log_message_callback(f"Content stats: {content_length} characters, approximately {pages_estimate} pages")
            else:
                log_message_callback(f"Failed to scrape or no content found for: {url}")

        except Exception as e:
            log_message_callback(f"An error occurred while processing {url}: {e}")

    log_message_callback("Enhanced web scraping process complete.")
    return "Success"

def crawl_docs_simple(urls: list, output_dir: str, **kwargs):
    """
    Simple crawler for basic web scraping (original functionality).
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)

    os.makedirs(output_dir, exist_ok=True)
    total_urls = len(urls)
    log_message_callback(f"Starting simple crawl of {total_urls} URLs...")

    for i, url in enumerate(urls):
        progress_callback(i + 1, total_urls, f"Simple scraping {url}")
        try:
            log_message_callback(f"Simple scraping content from: {url}")
            
            # Use basic web scraping (original behavior)
            content = browse_web_tool(
                url, 
                log_message_callback=log_message_callback,
                max_pages=1,  # Only scrape the main page
                max_depth=0   # Don't follow any links
            )

            if content and not content.startswith("Error"):
                # Create a safe filename from the URL
                parsed_url = urlparse(url)
                filename = f"{parsed_url.netloc}{parsed_url.path}".strip("/\\")
                filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
                filename = (filename[:100] + '..') if len(filename) > 100 else filename
                filepath = os.path.join(output_dir, f"{filename}_simple.txt")

                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                log_message_callback(f"Saved simple content to {filepath}")
            else:
                log_message_callback(f"Failed to scrape or no content found for: {url}")

        except Exception as e:
            log_message_callback(f"An error occurred while processing {url}: {e}")

    log_message_callback("Simple web scraping process complete.")
    return "Success"