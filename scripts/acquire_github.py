import requests
import os
import time
from urllib.parse import urlparse

def search_and_download_github_code(query, token, save_dir, max_files=50, log_message_callback=None, progress_callback=None):
    _log = log_message_callback if callable(log_message_callback) else print
    _log("Starting GitHub acquisition task...")

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
        response = requests.get(search_url, headers=headers, timeout=15)
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

        for i, item in enumerate(files_to_download):
            git_url = item.get('git_url')
            if not git_url: continue
            
            blob_response = requests.get(git_url, headers=headers, timeout=10).json()
            download_url = blob_response.get('download_url')

            if download_url:
                file_content_response = requests.get(download_url, timeout=10)
                file_content_response.raise_for_status()
                
                repo_name = item['repository']['name']
                file_name = os.path.basename(urlparse(download_url).path) or item.get('name', 'unknown_file')
                save_path = os.path.join(save_dir, f"github_{repo_name}_{file_name}.txt")

                with open(save_path, 'w', encoding='utf-8', errors='ignore') as f:
                    f.write(file_content_response.text)
                
                if progress_callback:
                    progress_callback(i + 1, total_files, f"Downloaded {i+1}/{total_files}: {file_name}")
                
                time.sleep(0.5)
        
        if progress_callback and total_files > 0:
            progress_callback(total_files, total_files, f"Finished downloading {total_files} files.")
        _log("GitHub code acquisition complete.")

    except requests.exceptions.RequestException as e:
        _log(f"A network error occurred: {e}")
        raise RuntimeError(f"Failed to connect to GitHub. Check your token and internet connection.") from e