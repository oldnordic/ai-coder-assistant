"""
acquire_github.py

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

import requests
import os
import time
from urllib.parse import urlparse
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from typing import Optional, Callable

def download_github_file(item, token, save_dir, log_message_callback=None):
    """
    Download a single GitHub file in a thread-safe manner.
    Returns (filename, success)
    """
    _log = log_message_callback if callable(log_message_callback) else print
    
    try:
        git_url = item.get('git_url')
        if not git_url: 
            return None, False
        
        blob_response = requests.get(git_url, headers={'Authorization': f'token {token}'}, timeout=10, verify=True).json()
        download_url = blob_response.get('download_url')

        if download_url:
            file_content_response = requests.get(download_url, timeout=10, verify=True)
            file_content_response.raise_for_status()
            
            repo_name = item['repository']['name']
            file_name = os.path.basename(urlparse(download_url).path) or item.get('name', 'unknown_file')
            save_path = os.path.join(save_dir, f"github_{repo_name}_{file_name}.txt")

            with open(save_path, 'w', encoding='utf-8', errors='ignore') as f:
                f.write(file_content_response.text)
            
            return file_name, True
        else:
            return None, False
            
    except Exception as e:
        _log(f"Error downloading file: {e}")
        return None, False

def search_and_download_github_code(query, token, save_dir, max_files=50, log_message_callback=None, progress_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    _log("Starting GitHub acquisition task with multi-threading...")

    if not token:
        raise ValueError("GitHub Personal Access Token is required.")

    if not os.path.exists(save_dir):
        os.makedirs(save_dir)
        _log(f"Created directory for GitHub code: {save_dir}")

    headers = {
        "Accept": "application/vnd.github.v3.text-match+json",
        "Authorization": f"token {token}"
    }
    search_url = f"https://api.github.com/search/code?q={query}+language:python&per_page=100"
    
    try:
        _log(f"Attempting to connect to GitHub API with query: {query}")
        response = requests.get(search_url, headers=headers, timeout=15, verify=True)
        response.raise_for_status()
        _log("API connection successful.")
        data = response.json()
        
        if 'items' not in data or not data['items']:
            _log("No code files found on GitHub for the given query.")
            if progress_callback: progress_callback(1, 1, "No files found.")
            return

        files_to_download = data['items'][:max_files]
        total_files = len(files_to_download)
        _log(f"Found {total_files} files to download.")

        # Thread-safe progress tracking
        progress_lock = threading.Lock()
        downloaded_count = 0
        
        def update_progress(filename: str):
            nonlocal downloaded_count
            with progress_lock:
                downloaded_count += 1
                if progress_callback:
                    progress_callback(downloaded_count, total_files, f"Downloaded {downloaded_count}/{total_files}: {filename}")

        # Determine optimal number of workers
        import multiprocessing
        max_workers = min(multiprocessing.cpu_count(), total_files, 8)  # Cap at 8 threads
        _log(f"Using {max_workers} worker threads for parallel downloading")

        # Download files in parallel
        successful_downloads = 0
        with ThreadPoolExecutor(max_workers=max_workers) as executor:
            # Submit all download tasks
            future_to_item = {}
            
            for item in files_to_download:
                future = executor.submit(download_github_file, item, token, save_dir, log_message_callback)
                future_to_item[future] = item
            
            # Collect results as they complete
            for future in as_completed(future_to_item):
                try:
                    filename, success = future.result()
                    if success:
                        successful_downloads += 1
                        update_progress(filename)
                    else:
                        update_progress("failed")
                except Exception as e:
                    _log(f"Error processing download: {e}")
                    update_progress("error")
                
                # Rate limiting - small delay between requests
                time.sleep(0.1)
        
        if progress_callback and total_files > 0:
            progress_callback(total_files, total_files, f"Finished downloading {successful_downloads}/{total_files} files.")
        _log(f"GitHub code acquisition complete. Successfully downloaded {successful_downloads}/{total_files} files.")

    except requests.exceptions.RequestException as e:
        _log(f"A network error occurred: {e}")
        raise RuntimeError(f"Failed to connect to GitHub. Check your token and internet connection.") from e