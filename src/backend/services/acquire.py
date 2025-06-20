"""
acquire.py

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

# src/processing/acquire.py
import os
import re
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed, Future
import threading
from typing import Optional, Tuple, Callable, List, Dict, Any
import multiprocessing

from backend.utils.constants import MAX_FILENAME_LENGTH

# --- FIXED: Use relative imports for modules within the same package ---
from backend.services.ai_tools import browse_web_tool

# Constants
MAX_FILENAME_LENGTH = 100

# Type aliases
ProgressCallback = Callable[[int, int, str], None]
LogCallback = Callable[[str], None]
CancellationCallback = Callable[[], bool]

def process_url_parallel(
    url: str,
    output_dir: str,
    max_pages: int,
    max_depth: int,
    same_domain_only: bool,
    log_message_callback: Optional[LogCallback] = None,
    cancellation_callback: Optional[CancellationCallback] = None
) -> Tuple[str, bool]:
    """
    Process a single URL in a thread-safe manner.
    Returns (filepath, success)
    """
    _log = log_message_callback if callable(log_message_callback) else print
    
    try:
        _log(f"Enhanced scraping content from: {url}")
        
        # Use enhanced web scraping with configurable parameters
        content = browse_web_tool(
            url, 
            log_message_callback=_log,
            max_pages=max_pages,
            max_depth=max_depth,
            same_domain_only=same_domain_only,
            cancellation_callback=cancellation_callback
        )

        if content and not content.startswith("Error"):
            # Create a safe filename from the URL
            parsed_url = urlparse(url)
            # Take the domain and path, replace special chars
            filename = f"{parsed_url.netloc}{parsed_url.path}".strip("/\\")
            filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
            # Truncate if too long
            filename = (filename[:MAX_FILENAME_LENGTH] + '..') if len(filename) > MAX_FILENAME_LENGTH else filename
            filepath = os.path.join(output_dir, f"{filename}_enhanced.txt")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            _log(f"Saved enhanced content to {filepath}")
            
            # Log content statistics
            content_length = len(content)
            pages_estimate = content.count("=== MAIN PAGE ===") + content.count("=== RELATED PAGE ===")
            _log(f"Content stats: {content_length} characters, approximately {pages_estimate} pages")
            
            return filepath, True
        else:
            _log(f"Failed to scrape or no content found for: {url}")
            if content and content.startswith("Error"):
                _log(f"Scraping error: {content}")
            return "", False

    except Exception as e:
        _log(f"An error occurred while processing {url}: {e}")
        return "", False

def crawl_docs(urls: List[str], output_dir: str, **kwargs: Any) -> Dict[str, Any]:
    """
    Enhanced crawler that scrapes documentation with multiple hyperlinks,
    navigation elements, and pagination using multi-threading.
    
    Args:
        urls: List of URLs to scrape
        output_dir: Directory to save scraped content
        **kwargs: Additional arguments including:
            - log_message_callback: Callable for logging messages
            - progress_callback: Callable for progress updates
            - cancellation_callback: Callable for checking if operation should be cancelled
            - max_pages: Maximum pages to scrape per URL
            - max_depth: Maximum depth to follow links
            - same_domain_only: Whether to only follow links on same domain
            - timeout: Timeout in seconds for each URL
    
    Returns:
        Dict containing:
            - success_count: Number of successfully scraped URLs
            - total: Total number of URLs attempted
            - files: List of saved file paths
            - urls: List of successfully scraped URLs
            - errors: List of error messages
    """
    log_message_callback: LogCallback = kwargs.get('log_message_callback', print)
    progress_callback: ProgressCallback = kwargs.get('progress_callback', lambda c, t, m: None)
    cancellation_callback: CancellationCallback = kwargs.get('cancellation_callback', lambda: False)
    
    # Enhanced scraping parameters
    max_pages = kwargs.get('max_pages', 15)  # Increased from default 10
    max_depth = kwargs.get('max_depth', 4)   # Increased from default 3
    same_domain_only = kwargs.get('same_domain_only', True)
    timeout = kwargs.get('timeout', 30)  # Added timeout parameter

    os.makedirs(output_dir, exist_ok=True)
    total_urls = len(urls)
    
    # Initial progress update
    progress_callback(0, total_urls, "Initializing web scraping...")
    log_message_callback(f"Starting enhanced crawl of {total_urls} URLs with multi-threading...")
    log_message_callback(f"Configuration: max_pages={max_pages}, max_depth={max_depth}, same_domain_only={same_domain_only}, timeout={timeout}")

    # Thread-safe progress tracking
    progress_lock = threading.Lock()
    processed_count = 0
    
    def update_progress(url: str, status: str = "Processing") -> None:
        nonlocal processed_count
        with progress_lock:
            progress_callback(processed_count, total_urls, f"{status} {url}")

    # Determine optimal number of workers
    max_workers = max(1, min(multiprocessing.cpu_count(), total_urls, 4))  # Cap at 4 threads for web scraping, minimum 1
    log_message_callback(f"Using {max_workers} worker threads for parallel web scraping")

    # Process URLs in parallel with proper cleanup
    successful_scrapes = 0
    errors: List[str] = []
    scraped_files: List[str] = []
    scraped_urls: List[str] = []
    
    # Create a ThreadPoolExecutor with a custom thread name prefix
    with ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="web_scraper") as executor:
        # Submit all URL processing tasks
        future_to_url: Dict[Future[Tuple[str, bool]], str] = {}
        
        for url in urls:
            if cancellation_callback():
                log_message_callback("Web scraping cancelled by user before processing all URLs")
                break
            
            # Update progress for URL submission    
            update_progress(url, "Queuing")
            
            future = executor.submit(
                process_url_parallel,
                url,
                output_dir,
                max_pages,
                max_depth,
                same_domain_only,
                log_message_callback,
                cancellation_callback
            )
            future_to_url[future] = url
        
        # Collect results as they complete with timeout
        for future in as_completed(future_to_url, timeout=timeout):
            # Check for cancellation
            if cancellation_callback():
                log_message_callback("Web scraping cancelled by user")
                # Cancel all pending futures
                for f in future_to_url:
                    if not f.done():
                        f.cancel()
                break
                
            url = future_to_url[future]
            try:
                # Update progress for current URL
                update_progress(url, "Scraping")
                
                filepath, success = future.result(timeout=timeout)
                if success:
                    successful_scrapes += 1
                    scraped_files.append(filepath)
                    scraped_urls.append(url)
                    processed_count += 1
                    update_progress(url, "Completed")
                else:
                    errors.append(f"No content for {url}")
                    processed_count += 1
                    update_progress(url, "Failed")
            except TimeoutError:
                log_message_callback(f"Timeout processing {url}")
                errors.append(f"Timeout for {url}")
                processed_count += 1
                update_progress(url, "Timeout")
            except Exception as e:
                log_message_callback(f"Error processing {url}: {e}")
                errors.append(f"Exception for {url}: {e}")
                processed_count += 1
                update_progress(url, "Error")

    # Final progress update
    progress_callback(total_urls, total_urls, "Web scraping complete")

    summary = {
        "success_count": successful_scrapes,
        "total": total_urls,
        "files": scraped_files,
        "urls": scraped_urls,
        "errors": errors
    }
    if successful_scrapes == 0:
        error_msg = f"No documents were acquired. Errors: {'; '.join(errors) if errors else 'Unknown error.'}"
        log_message_callback(error_msg)
        return summary
    log_message_callback(f"Enhanced web scraping process complete. Successfully scraped {successful_scrapes}/{total_urls} URLs.")
    return summary

def process_url_simple_parallel(url: str, output_dir: str, log_message_callback: Optional[Callable[[str], None]] = None, cancellation_callback: Optional[Callable[[], bool]] = None) -> Tuple[str, bool]:
    """
    Process a single URL with simple scraping in a thread-safe manner.
    Returns (filepath, success)
    """
    _log = log_message_callback if callable(log_message_callback) else print
    
    try:
        _log(f"Simple scraping content from: {url}")
        
        # Use basic web scraping (original behavior)
        content = browse_web_tool(
            url, 
            log_message_callback=_log,
            max_pages=1,  # Only scrape the main page
            max_depth=0,   # Don't follow any links
            cancellation_callback=cancellation_callback
        )

        if content and not content.startswith("Error"):
            # Create a safe filename from the URL
            parsed_url = urlparse(url)
            filename = f"{parsed_url.netloc}{parsed_url.path}".strip("/\\")
            filename = re.sub(r'[^a-zA-Z0-9_-]', '_', filename)
            filename = (filename[:MAX_FILENAME_LENGTH] + '..') if len(filename) > MAX_FILENAME_LENGTH else filename
            filepath = os.path.join(output_dir, f"{filename}_simple.txt")

            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            _log(f"Saved simple content to {filepath}")
            
            return filepath, True
        else:
            _log(f"Failed to scrape or no content found for: {url}")
            return "", False

    except Exception as e:
        _log(f"An error occurred while processing {url}: {e}")
        return "", False

def crawl_docs_simple(urls: list, output_dir: str, **kwargs):
    """
    Simple crawler for basic web scraping with multi-threading.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)
    cancellation_callback = kwargs.get('cancellation_callback', lambda: False)

    os.makedirs(output_dir, exist_ok=True)
    total_urls = len(urls)
    log_message_callback(f"Starting simple crawl of {total_urls} URLs with multi-threading...")

    # Thread-safe progress tracking
    progress_lock = threading.Lock()
    processed_count = 0
    
    def update_progress(url: str):
        nonlocal processed_count
        with progress_lock:
            processed_count += 1
            progress_callback(processed_count, total_urls, f"Simple scraping {url}")

    # Determine optimal number of workers
    max_workers = max(1, min(multiprocessing.cpu_count(), total_urls, 6))  # Cap at 6 threads for web scraping, minimum 1
    log_message_callback(f"Using {max_workers} worker threads for parallel web scraping")

    # Process URLs in parallel
    successful_scrapes = 0
    scraped_files = []
    scraped_urls = []
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all URL processing tasks
        future_to_url = {}
        
        for url in urls:
            future = executor.submit(
                process_url_simple_parallel,
                url,
                output_dir,
                log_message_callback,
                cancellation_callback
            )
            future_to_url[future] = url
        
        # Collect results as they complete
        for future in as_completed(future_to_url):
            # Check for cancellation
            if cancellation_callback():
                log_message_callback("Web scraping cancelled by user")
                break
                
            url = future_to_url[future]
            try:
                filepath, success = future.result()
                if success:
                    successful_scrapes += 1
                    scraped_files.append(filepath)
                    scraped_urls.append(url)
                update_progress(url)
            except Exception as e:
                log_message_callback(f"Error processing {url}: {e}")
                update_progress(url)

    summary = {
        "success_count": successful_scrapes,
        "total": total_urls,
        "files": scraped_files,
        "urls": scraped_urls
    }
    log_message_callback(f"Simple web scraping process complete. Successfully scraped {successful_scrapes}/{total_urls} URLs.")
    return summary