# src/core/ai_tools.py
import os
import requests
from bs4 import BeautifulSoup
import yt_dlp
from yt_dlp import YoutubeDL
import json
import re
from youtube_transcript_api import YouTubeTranscriptApi
import html
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from typing import Optional, List, Dict, Tuple

from ..config import settings
from . import ollama_client
from ..training import trainer as train_language_model

# Global cache for the embedding model to prevent re-downloading
_embedding_model_cache = None

def get_embedding_model(log_callback):
    """
    Lazily loads and caches the SentenceTransformer model.
    Only loads when actually needed for vector database operations.
    """
    global _embedding_model_cache
    if _embedding_model_cache is None:
        try:
            from sentence_transformers import SentenceTransformer
            log_callback(f"Loading embedding model '{settings.EMBEDDING_MODEL_NAME}' for the first time...")
            _embedding_model_cache = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device=settings.DEVICE)
            log_callback("Embedding model loaded.")
        except ImportError as e:
            log_callback(f"Embedding model dependencies not available: {e}")
            return None
    return _embedding_model_cache

def generate_with_own_model(
    model: GPT2LMHeadModel, 
    tokenizer: GPT2Tokenizer, 
    prompt: str,
    max_new_tokens: int = 50
) -> str:
    if model is None or tokenizer is None:
        return "Own model or tokenizer not loaded."

    device = model.device
    inputs = tokenizer(prompt, return_tensors="pt").to(device)
    
    model.eval()
    with torch.no_grad():
        output_ids = model.generate(
            **inputs,
            max_new_tokens=max_new_tokens,
            num_beams=5,
            early_stopping=True,
            no_repeat_ngram_size=2,
            pad_token_id=tokenizer.eos_token_id 
        )

    full_text = tokenizer.decode(output_ids[0], skip_special_tokens=True)
    
    if prompt in full_text:
        suggestion_part = full_text.replace(prompt, '').strip()
    else:
        if "[GOOD_CODE]" in full_text:
             suggestion_part = full_text.split("[GOOD_CODE]")[-1].strip()
        else:
             suggestion_part = "Failed to parse suggestion."

    first_line = suggestion_part.split('\n')[0].strip()

    return first_line if first_line else "Failed to generate valid suggestion."

def generate_report_and_training_data(suggestion_list, model_mode, model_ref, tokenizer_ref, **kwargs):
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)

    log_message_callback("Starting report and training data generation...")
    
    md_parts = ["# AI Code Review Report\n\n"]
    jsonl_parts = []
    
    total_suggestions = len(suggestion_list)
    for i, suggestion in enumerate(suggestion_list):
        progress_callback(i + 1, total_suggestions, f"Generating explanation {i+1}/{total_suggestions}...")
        
        explanation = get_ai_explanation(
            suggestion, model_mode, model_ref, tokenizer_ref, **kwargs
        )
        
        filepath = suggestion.get('file_path', 'N/A')
        line_num = suggestion.get('line_number', -1) + 1
        issue = suggestion.get('description', 'N/A')
        original_code = suggestion.get('code_snippet', '')
        proposed_code = suggestion.get('suggested_improvement', '')
        
        md_parts.append(f"## File: `{filepath}` (Line: {line_num})\n\n")
        md_parts.append(f"### Issue: {issue}\n\n")
        md_parts.append("#### Original Code:\n")
        md_parts.append(f"```python\n{original_code}\n```\n\n")
        md_parts.append("#### Proposed Fix:\n")
        md_parts.append(f"```python\n{proposed_code}\n```\n\n")
        md_parts.append("#### AI Justification:\n")
        md_parts.append(f"{explanation}\n\n---\n\n")

        training_record = {
            'issue': issue,
            'original_code': original_code,
            'user_feedback_or_code': proposed_code
        }
        jsonl_parts.append(json.dumps(training_record))

    log_message_callback("Report and training data generation complete.")
    progress_callback(total_suggestions, total_suggestions, "Report generated.")
    
    markdown_report = "".join(md_parts)
    jsonl_training_data = "\n".join(jsonl_parts)
    
    return markdown_report, jsonl_training_data

def get_ai_explanation(suggestion, model_mode, model_ref, tokenizer_ref, **kwargs):
    log_message_callback = kwargs.get('log_message_callback', print)
    
    if model_mode == "own_model":
        return "Justification from the local model is not yet implemented. Focus is on code suggestion quality first."

    try:
        issue_description = suggestion['description']
        context = query_knowledge_base(issue_description, log_message_callback)
        prompt = f"""You are an expert programming instructor. A developer has a piece of code with a known issue and a proposed fix.
Your task is to provide a clear, concise explanation of *why* the proposed fix is better, adhering to best practices.
**Context from Documentation:**
---
{context}
---
**Code Issue Details:**
- Issue: {suggestion['description']}
- Original Code: `{suggestion['code_snippet']}`
- Proposed Fix: `{suggestion['suggested_improvement']}`
**AI Justification:**
"""
        
        explanation = ollama_client.get_ollama_response(prompt, model_ref)
        if isinstance(explanation, str) and explanation.startswith("API_ERROR:"): 
            return f"Could not generate explanation: {explanation}"
        return explanation
    except Exception as e:
        return f"An unexpected error occurred while generating the explanation: {e}"

def query_knowledge_base(query_text: str, log_message_callback=None) -> str:
    _log = log_message_callback if callable(log_message_callback) else print
    try:
        # Check if FAISS dependencies are available
        try:
            import faiss
        except ImportError:
            return "Vector database not available. Knowledge base queries disabled."
        
        # Define FAISS paths dynamically to avoid startup issues
        faiss_index_path = os.path.join(settings.PROCESSED_DATA_DIR, "vector_store.faiss")
        faiss_metadata_path = os.path.join(settings.PROCESSED_DATA_DIR, "vector_store.json")
        
        if not os.path.exists(faiss_index_path): 
            return "Knowledge base not found. Please run preprocessing first."
        
        index = faiss.read_index(faiss_index_path)
        with open(faiss_metadata_path, 'r', encoding='utf-8', errors='ignore') as f: 
            documents = json.load(f)
        
        model = get_embedding_model(_log)
        if model is None:
            return "Embedding model not available. Knowledge base queries disabled."
        
        query_embedding = model.encode([query_text]).astype('float32')
        k = 3
        distances, indices = index.search(query_embedding, k)
        results = [documents[i] for i in indices[0] if i < len(documents)]
        return "\n\n---\n\n".join(results) if results else "No specific context found."
    except Exception as e:
        _log(f"Error querying knowledge base: {e}")
        return f"Error querying knowledge base: {e}"

def browse_web_tool(url: str, **kwargs) -> str:
    """
    Enhanced web scraping tool that can handle documentation with multiple hyperlinks,
    navigation elements, and pagination.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    max_pages = kwargs.get('max_pages', 10)  # Limit to prevent infinite crawling
    max_depth = kwargs.get('max_depth', 3)   # How deep to follow links
    same_domain_only = kwargs.get('same_domain_only', True)
    
    _log = log_message_callback
    
    try:
        _log(f"Starting enhanced web scraping of: {url}")
        
        # Track visited URLs to avoid duplicates
        visited_urls = set()
        scraped_content = []
        
        # Get the base domain for same-domain filtering
        from urllib.parse import urlparse
        base_domain = urlparse(url).netloc
        
        def should_follow_link(link_url: str, current_depth: int) -> bool:
            """Determine if we should follow a link based on various criteria."""
            if current_depth >= max_depth:
                return False
                
            if link_url in visited_urls:
                return False
                
            if same_domain_only:
                link_domain = urlparse(link_url).netloc
                if link_domain != base_domain:
                    return False
            
            # Skip common non-content URLs
            skip_patterns = [
                '/login', '/logout', '/admin', '/api/', '/search',
                '.pdf', '.zip', '.tar', '.gz', '.exe', '.dmg',
                'mailto:', 'tel:', 'javascript:', '#'
            ]
            
            for pattern in skip_patterns:
                if pattern in link_url.lower():
                    return False
            
            return True
        
        def extract_navigation_links(soup, current_url: str) -> list:
            """Extract navigation links that might lead to more content."""
            navigation_links = []
            
            # Common navigation selectors
            nav_selectors = [
                'nav a', '.navigation a', '.nav a', '.menu a',
                '.pagination a', '.pager a', '.next', '.prev',
                '.breadcrumb a', '.sidebar a', '.toc a',
                'a[rel="next"]', 'a[rel="prev"]',
                'a[aria-label*="next"]', 'a[aria-label*="previous"]',
                'a[title*="next"]', 'a[title*="previous"]'
            ]
            
            for selector in nav_selectors:
                links = soup.select(selector)
                for link in links:
                    href = link.get('href')
                    if href:
                        # Convert relative URLs to absolute
                        from urllib.parse import urljoin
                        absolute_url = urljoin(current_url, href)
                        if should_follow_link(absolute_url, 0):  # 0 for initial depth
                            navigation_links.append(absolute_url)
            
            # Also look for common "next page" indicators
            next_indicators = [
                'next', 'next page', 'continue', 'more', 'read more',
                'next chapter', 'next section', 'next article'
            ]
            
            for link in soup.find_all('a', href=True):
                link_text = link.get_text().lower().strip()
                if any(indicator in link_text for indicator in next_indicators):
                    href = link.get('href')
                    absolute_url = urljoin(current_url, href)
                    if should_follow_link(absolute_url, 0):
                        navigation_links.append(absolute_url)
            
            return list(set(navigation_links))  # Remove duplicates
        
        def scrape_single_page(page_url: str, depth: int = 0) -> tuple:
            """Scrape a single page and return content and navigation links."""
            if page_url in visited_urls or depth >= max_depth:
                return "", []
            
            visited_urls.add(page_url)
            _log(f"Scraping page {depth + 1}: {page_url}")
            
            try:
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(page_url, headers=headers, timeout=15)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # Remove unwanted elements
                for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'iframe']):
                    element.decompose()
                
                # Extract main content (prioritize main content areas)
                content_selectors = [
                    'main', 'article', '.content', '.main-content', 
                    '.post-content', '.entry-content', '.documentation',
                    '.docs-content', '.api-docs', '.guide-content'
                ]
                
                main_content = None
                for selector in content_selectors:
                    main_content = soup.select_one(selector)
                    if main_content:
                        break
                
                if not main_content:
                    main_content = soup.find('body') or soup
                
                # Extract text content
                text_content = main_content.get_text(separator='\n', strip=True)
                
                # Clean up the text
                lines = text_content.split('\n')
                cleaned_lines = []
                for line in lines:
                    line = line.strip()
                    if line and len(line) > 10:  # Skip very short lines
                        cleaned_lines.append(line)
                
                cleaned_content = '\n\n'.join(cleaned_lines)
                
                # Extract navigation links for further crawling
                nav_links = extract_navigation_links(soup, page_url)
                
                return cleaned_content, nav_links
                
            except Exception as e:
                _log(f"Error scraping {page_url}: {e}")
                return "", []
        
        # Start with the initial URL
        initial_content, initial_links = scrape_single_page(url, 0)
        if initial_content:
            scraped_content.append(f"=== MAIN PAGE ===\n{initial_content}\n")
        
        # Queue for breadth-first crawling
        from collections import deque
        link_queue = deque(initial_links)
        pages_scraped = 1
        
        # Crawl additional pages
        while link_queue and pages_scraped < max_pages:
            next_url = link_queue.popleft()
            
            if next_url in visited_urls:
                continue
            
            page_content, new_links = scrape_single_page(next_url, 1)
            
            if page_content:
                scraped_content.append(f"=== RELATED PAGE ===\n{page_content}\n")
                pages_scraped += 1
            
            # Add new links to queue
            for new_link in new_links:
                if new_link not in visited_urls and new_link not in link_queue:
                    link_queue.append(new_link)
        
        # Combine all content
        final_content = '\n\n'.join(scraped_content)
        
        # Truncate if too long (keep it reasonable for processing)
        if len(final_content) > 50000:  # 50KB limit
            final_content = final_content[:50000] + "\n\n[Content truncated due to length]"
        
        _log(f"Scraping complete. Scraped {pages_scraped} pages, {len(visited_urls)} total URLs visited.")
        return final_content
        
    except Exception as e:
        _log(f"Error during enhanced web scraping: {e}")
        return f"Error during enhanced web scraping: {e}"

def transcribe_youtube_tool(youtube_url: str, **kwargs) -> str:
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)
    _log = log_message_callback
    _progress = progress_callback
    try:
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", youtube_url)
        if not video_id_match: return "Error: Could not extract video ID from URL."
        video_id = video_id_match.group(1)
        try:
            transcript_list = YouTubeTranscriptApi.get_transcript(video_id, languages=['en', 'en-US'])
            transcript_text = " ".join([entry['text'] for entry in transcript_list])
            if transcript_text:
                _log("Fast API transcription successful.")
                _progress(100, 100, "Transcription complete!")
                return transcript_text
        except Exception as api_e:
            _log(f"API transcription failed ({api_e}). Falling back to local transcription.")
        
        temp_audio_path = os.path.join(settings.PROJECT_ROOT, f"temp_audio_{video_id}.mp3")
        def yt_dlp_progress_hook(d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                if total_bytes:
                    percentage = (d['downloaded_bytes'] / total_bytes) * 100
                    _progress(int(percentage * 0.33), 100, f"Downloading audio... {d['_percent_str']}")
            elif d['status'] == 'finished': _progress(33, 100, "Download complete.")
        
        ydl_opts = {
            'format': 'bestaudio/best', 
            'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 
            'outtmpl': os.path.splitext(temp_audio_path)[0], 
            'noplaylist': True, 
            'progress_hooks': [yt_dlp_progress_hook]
        }
        
        with YoutubeDL(ydl_opts) as ydl: 
            ydl.download([youtube_url])
        
        _log("Loading local model for fallback transcription...")
        from transformers import pipeline
        pipe = pipeline("automatic-speech-recognition", model="openai/whisper-tiny.en", device=settings.DEVICE)
        _progress(50, 100, "Transcribing...")
        transcript = pipe(temp_audio_path)
        transcript_text = transcript.get("text", "")

        _log("Local transcription finished.")
        _progress(100, 100, "Transcription complete!")
        return transcript_text
    except Exception as e:
        _log(f"An unexpected error occurred during transcription: {e}")
        return f"An unexpected error occurred during transcription: {e}"
    finally:
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path): 
            os.remove(temp_audio_path)