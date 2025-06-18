"""
ai_tools.py

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
from typing import Optional, List, Dict, Tuple, Any
import hashlib
import pickle
from pathlib import Path
import time
import threading
import subprocess
import tempfile
import shutil
from urllib.parse import urlparse, urljoin

from ..utils import settings
from . import ollama_client
from .trainer import train_model as train_language_model
from ...utils.constants import (
    CACHE_EXPIRY_SECONDS, DEFAULT_USER_AGENT, MAX_CONTENT_SIZE, 
    PROGRESS_COMPLETE, PROGRESS_WEIGHT_DOWNLOAD,
    PROGRESS_MAX, PROGRESS_MIN, MAX_FILE_SIZE_KB, MAX_DESCRIPTION_LENGTH,
    DEFAULT_MAX_PAGES, DEFAULT_MAX_DEPTH, DEFAULT_LINKS_PER_PAGE,
    PERCENTAGE_MULTIPLIER
)

# Global cache for the embedding model to prevent re-downloading
_embedding_model_cache = None

# AI Response Cache for performance optimization
class AICache:
    def __init__(self, cache_dir: str = None):
        if cache_dir is None:
            cache_dir = os.path.join(os.path.dirname(__file__), "..", "tmp", "ai_cache")
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def _get_cache_key(self, prompt: str, model_name: str) -> str:
        """Generate a cache key for the prompt and model."""
        content = f"{prompt}_{model_name}"
        return hashlib.sha256(content.encode()).hexdigest()
    
    def get_cached_response(self, prompt: str, model_name: str) -> Optional[str]:
        """Get cached response if available."""
        try:
            cache_key = self._get_cache_key(prompt, model_name)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            if cache_file.exists():
                with open(cache_file, 'rb') as f:
                    cached_data = pickle.load(f)
                    # Check if cache is not too old (7 days)
                    if cached_data.get('timestamp', 0) > (time.time() - CACHE_EXPIRY_SECONDS):
                        return cached_data.get('response')
        except Exception:
            pass
        return None
    
    def cache_response(self, prompt: str, model_name: str, response: str):
        """Cache the AI response."""
        try:
            cache_key = self._get_cache_key(prompt, model_name)
            cache_file = self.cache_dir / f"{cache_key}.pkl"
            
            cached_data = {
                'prompt': prompt,
                'model_name': model_name,
                'response': response,
                'timestamp': time.time()
            }
            
            with open(cache_file, 'wb') as f:
                pickle.dump(cached_data, f)
        except Exception:
            pass

# Global AI cache instance
_ai_cache = AICache()

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

    log_message_callback("=== REPORT GENERATION START ===")
    log_message_callback(f"Starting optimized report and training data generation...")
    log_message_callback(f"Input: {len(suggestion_list)} suggestions")
    log_message_callback(f"Model mode: {model_mode}")
    log_message_callback(f"Model ref: {type(model_ref).__name__}")
    
    if not suggestion_list:
        log_message_callback("No suggestions provided, returning empty report")
        return "# AI Code Review Report\n\nNo issues found.", ""
    
    # Limit the number of suggestions to prevent timeout
    max_suggestions = 50  # Limit to prevent long processing
    if len(suggestion_list) > max_suggestions:
        log_message_callback(f"Limiting suggestions to {max_suggestions} to prevent timeout...")
        suggestion_list = suggestion_list[:max_suggestions]
    
    # Use batch processing for explanations with timeout
    log_message_callback("=== STARTING AI EXPLANATIONS ===")
    log_message_callback("Generating AI explanations in batches...")
    
    try:
        explanations = batch_process_suggestions(
            suggestion_list, model_mode, model_ref, tokenizer_ref, 
            log_message_callback=log_message_callback,
            progress_callback=progress_callback
        )
        log_message_callback(f"AI explanations completed: {len(explanations)} explanations generated")
    except Exception as e:
        log_message_callback(f"ERROR in AI explanations: {e}")
        import traceback
        log_message_callback(f"Traceback: {traceback.format_exc()}")
        # Fallback to simple explanations
        explanations = [f"AI analysis for issue: {s.get('description', 'Unknown issue')}" for s in suggestion_list]
    
    # Build report incrementally to reduce memory usage
    log_message_callback("=== BUILDING REPORT ===")
    log_message_callback("Building report incrementally...")
    md_parts = ["# AI Code Review Report\n\n"]
    jsonl_parts = []
    
    # Add summary statistics
    log_message_callback("Calculating summary statistics...")
    total_issues = len(suggestion_list)
    issues_by_type = {}
    issues_by_severity = {}
    
    for suggestion in suggestion_list:
        issue_type = suggestion.get('issue_type', 'unknown')
        severity = suggestion.get('severity', 'medium')
        
        issues_by_type[issue_type] = issues_by_type.get(issue_type, 0) + 1
        issues_by_severity[severity] = issues_by_severity.get(severity, 0) + 1
    
    log_message_callback(f"Summary stats: {len(issues_by_type)} types, {len(issues_by_severity)} severities")
    
    # Add executive summary
    log_message_callback("Adding executive summary...")
    md_parts.append("## Executive Summary\n\n")
    md_parts.append(f"**Total Issues Found:** {total_issues}\n\n")
    
    md_parts.append("### Issues by Type:\n")
    for issue_type, count in sorted(issues_by_type.items()):
        md_parts.append(f"- **{issue_type.replace('_', ' ').title()}:** {count}\n")
    
    md_parts.append("\n### Issues by Severity:\n")
    severity_order = ['critical', 'high', 'medium', 'low']
    for severity in severity_order:
        if severity in issues_by_severity:
            md_parts.append(f"- **{severity.title()}:** {issues_by_severity[severity]}\n")
    
    md_parts.append("\n---\n\n## Detailed Analysis\n\n")
    
    # Process each suggestion with its explanation
    log_message_callback("=== PROCESSING INDIVIDUAL ISSUES ===")
    for i, (suggestion, explanation) in enumerate(zip(suggestion_list, explanations)):
        log_message_callback(f"Processing issue {i+1}/{total_issues}: {suggestion.get('description', 'Unknown')[:50]}...")
        progress_callback(i + 1, total_issues, f"Building report section {i+1}/{total_issues}...")
        
        filepath = suggestion.get('file_path', 'N/A')
        line_num = suggestion.get('line_number', -1) + 1
        issue = suggestion.get('description', 'N/A')
        original_code = suggestion.get('code_snippet', '')
        proposed_code = suggestion.get('suggested_improvement', '')
        issue_type = suggestion.get('issue_type', 'unknown')
        severity = suggestion.get('severity', 'medium')
        
        # Add issue section
        md_parts.append(f"### {i+1}. {issue_type.replace('_', ' ').title()} - {severity.title()} Severity\n\n")
        md_parts.append(f"**File:** `{filepath}` (Line: {line_num})\n\n")
        md_parts.append(f"**Issue:** {issue}\n\n")
        
        if original_code:
            md_parts.append("#### Original Code:\n")
            md_parts.append(f"```{suggestion.get('language', 'text')}\n{original_code}\n```\n\n")
        
        if proposed_code and proposed_code != 'No suggestion available':
            md_parts.append("#### Proposed Fix:\n")
            md_parts.append(f"```{suggestion.get('language', 'text')}\n{proposed_code}\n```\n\n")
        
        md_parts.append("#### AI Justification:\n")
        md_parts.append(f"{explanation}\n\n---\n\n")

        # Add to training data
        training_record = {
            'issue': issue,
            'original_code': original_code,
            'user_feedback_or_code': proposed_code,
            'issue_type': issue_type,
            'severity': severity,
            'file_path': filepath,
            'line_number': line_num
        }
        jsonl_parts.append(json.dumps(training_record))

    log_message_callback("=== REPORT GENERATION COMPLETE ===")
    log_message_callback("Report and training data generation complete.")
    progress_callback(total_issues, total_issues, "Report generated successfully.")
    
    markdown_report = "".join(md_parts)
    jsonl_training_data = "\n".join(jsonl_parts)
    
    log_message_callback(f"Final report size: {len(markdown_report)} characters")
    log_message_callback(f"Training data records: {len(jsonl_parts)}")
    
    return markdown_report, jsonl_training_data

def get_ai_explanation(suggestion, model_mode, model_ref, tokenizer_ref, **kwargs):
    """Get AI explanation for a suggestion with comprehensive logging."""
    log_message_callback = kwargs.get('log_message_callback', print)
    
    log_message_callback(f"=== AI EXPLANATION START ===")
    log_message_callback(f"Model mode: {model_mode}")
    log_message_callback(f"Model ref type: {type(model_ref).__name__}")
    log_message_callback(f"Suggestion type: {suggestion.get('issue_type', 'unknown')}")
    
    try:
        # Check cache first
        cache_key = f"{suggestion['description']}_{suggestion.get('issue_type', 'unknown')}"
        cached_explanation = _ai_cache.get_cached_response(cache_key, model_ref)
        
        if cached_explanation:
            log_message_callback("Using cached explanation")
            return cached_explanation
        
        log_message_callback("No cache hit, generating new explanation")
        
        # Generate explanation based on model mode
        if model_mode == 'ollama':
            log_message_callback("Using Ollama for explanation")
            explanation = _generate_ollama_explanation(suggestion, model_ref, log_message_callback)
        elif model_mode == 'own_model':
            log_message_callback("Using own model for explanation")
            explanation = _generate_own_model_explanation(suggestion, model_ref, tokenizer_ref, log_message_callback)
        else:
            log_message_callback("Using fallback explanation")
            explanation = _generate_fallback_explanation(suggestion)
        
        # Cache the response
        _ai_cache.cache_response(cache_key, model_ref, explanation)
        
        log_message_callback(f"Explanation generated: {len(explanation)} characters")
        return explanation
        
    except Exception as e:
        log_message_callback(f"ERROR in AI explanation: {e}")
        import traceback
        log_message_callback(f"AI explanation traceback: {traceback.format_exc()}")
        return _generate_fallback_explanation(suggestion)

def _generate_fallback_explanation(suggestion):
    """Generate a fallback explanation when AI model is unavailable."""
    issue_type = suggestion.get('issue_type', 'unknown')
    description = suggestion.get('description', '')
    original_code = suggestion.get('code_snippet', '')
    suggested_code = suggestion.get('suggested_improvement', '')
    
    # Create a basic explanation based on the issue type
    fallback_explanations = {
        'security_vulnerability': f"This fix addresses a security concern in the original code. The suggested improvement {description.lower()} to make the code more secure and prevent potential vulnerabilities.",
        'performance_issue': f"This optimization improves the performance of the code. The suggested change {description.lower()} to make the code more efficient.",
        'code_smell': f"This refactoring improves code quality and readability. The suggested improvement {description.lower()} to follow better coding practices.",
        'maintainability_issue': f"This change improves code maintainability. The suggested modification {description.lower()} to make the code easier to understand and maintain.",
        'linter_error': f"This fix addresses a code style or linting issue. The suggested change {description.lower()} to comply with coding standards.",
        'best_practice_violation': f"This improvement follows established best practices. The suggested modification {description.lower()} to align with recommended coding patterns."
    }
    
    # Get the appropriate fallback explanation
    fallback = fallback_explanations.get(issue_type, f"This suggested improvement addresses the identified issue: {description}")
    
    # Add a note about the AI model
    fallback += "\n\nNote: This is a fallback explanation as the AI model is currently unavailable. The suggestion is based on static analysis and best practices."
    
    return fallback

def browse_web_tool(url: str, **kwargs) -> str:
    """
    Enhanced web scraping tool with configurable parameters and timeout handling.
    Parameters:
        url: str - The starting URL.
        max_pages: int - Maximum number of pages to scrape (default 10).
        max_depth: int - Maximum link-following depth (default 3).
        same_domain_only: bool - Only follow links on the same domain (default True).
        timeout: int - Timeout in seconds (default 15).
        links_per_page: int - Maximum number of links to follow per page (default 50).
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)
    cancellation_callback = kwargs.get('cancellation_callback', lambda: False)
    max_pages = kwargs.get('max_pages', 10)
    max_depth = kwargs.get('max_depth', 3)
    same_domain_only = kwargs.get('same_domain_only', True)
    timeout = kwargs.get('timeout', 15)
    links_per_page = kwargs.get('links_per_page', 50)
    
    def _progress(current, total, message):
        if progress_callback:
            progress_callback(current, total, message)
    
    try:
        _progress(PROGRESS_MIN, PROGRESS_MAX, f"Starting enhanced web scraping of {url}")
        log_message_callback(f"=== WEB SCRAPING START ===")
        log_message_callback(f"URL: {url}")
        log_message_callback(f"Max pages: {max_pages}, Max depth: {max_depth}")
        log_message_callback(f"Timeout: {timeout} seconds")
        
        # Enhanced scraping with navigation and timeout
        all_content = []
        visited_urls = set()
        pages_scraped = 0
        start_time = time.time()
        
        def extract_navigation_links(soup, current_url: str) -> list:
            """Extract navigation links from the page."""
            links = []
            try:
                for a_tag in soup.find_all('a', href=True):
                    href = a_tag['href']
                    full_url = urljoin(current_url, href)
                    if (full_url.startswith('http') and 
                        not any(skip in full_url.lower() for skip in [
                            '#', 'javascript:', 'mailto:', 'tel:', 'pdf', 'zip', 'rar',
                            'jpg', 'jpeg', 'png', 'gif', 'svg', 'ico', 'css', 'js'
                        ])):
                        links.append(full_url)
                log_message_callback(f"Extracted {len(links)} links from {current_url}:")
                for l in links:
                    log_message_callback(f"  LINK: {l}")
            except Exception as e:
                log_message_callback(f"Error extracting links: {e}")
            return links[:links_per_page]  # Use user-configurable limit
        
        def should_follow_link(link_url: str, current_depth: int) -> bool:
            if current_depth >= max_depth:
                log_message_callback(f"SKIP: {link_url} (max depth {max_depth} reached)")
                return False
            if link_url in visited_urls:
                log_message_callback(f"SKIP: {link_url} (already visited)")
                return False
            if same_domain_only:
                parsed_main = urlparse(url)
                parsed_link = urlparse(link_url)
                if parsed_main.netloc != parsed_link.netloc:
                    log_message_callback(f"SKIP: {link_url} (different domain)")
                    return False
            log_message_callback(f"FOLLOW: {link_url}")
            return True
        
        def scrape_single_page(page_url: str, depth: int = 0) -> tuple:
            """Scrape a single page and return content and links with timeout."""
            try:
                # Check cancellation more frequently
                if cancellation_callback():
                    log_message_callback("Web scraping cancelled by user")
                    return "", []
                
                # Check timeout more frequently
                if time.time() - start_time > timeout:
                    log_message_callback(f"Timeout reached after {timeout} seconds")
                    return "", []
                
                log_message_callback(f"Scraping page: {page_url}")
                
                headers = {
                    'User-Agent': DEFAULT_USER_AGENT
                }
                
                # Use shorter timeout for individual requests
                request_timeout = min(5, timeout // 3)  # Reduced from 10 to 5 seconds
                response = requests.get(page_url, headers=headers, timeout=request_timeout)
                response.raise_for_status()
                
                # Check cancellation after request
                if cancellation_callback():
                    log_message_callback("Web scraping cancelled by user")
                    return "", []
                
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # Remove script and style elements
                for script in soup(["script", "style", "nav", "footer", "header", "aside"]):
                    script.decompose()
                
                # Extract text content
                text_content = soup.get_text(separator='\n', strip=True)
                
                # Clean up text
                lines = [line.strip() for line in text_content.split('\n') if line.strip()]
                cleaned_text = '\n'.join(lines)
                
                # Extract navigation links
                links = extract_navigation_links(soup, page_url) if depth < max_depth else []
                
                log_message_callback(f"Successfully scraped {len(cleaned_text)} characters from {page_url}")
                return cleaned_text, links
                
            except requests.exceptions.Timeout:
                log_message_callback(f"Timeout scraping {page_url}")
                return "", []
            except requests.exceptions.RequestException as e:
                log_message_callback(f"Request error scraping {page_url}: {e}")
                return "", []
            except Exception as e:
                log_message_callback(f"Error scraping {page_url}: {e}")
                return "", []
        
        # Start with the main URL
        log_message_callback("Scraping main page...")
        main_content, main_links = scrape_single_page(url, 0)
        if main_content:
            all_content.append(f"=== MAIN PAGE ===\n{main_content}\n")
            pages_scraped += 1
            visited_urls.add(url)
            log_message_callback(f"Main page scraped successfully ({len(main_content)} characters)")
        else:
            log_message_callback("Failed to scrape main page")
            return f"Error: Failed to scrape main page {url}"
        
        # Follow links if we haven't reached the page limit
        links_to_visit = main_links[:max_pages - 1]  # Reserve one slot for main page
        current_depth = 1
        
        while links_to_visit and pages_scraped < max_pages and current_depth <= max_depth:
            # Check cancellation more frequently
            if cancellation_callback():
                log_message_callback("Web scraping cancelled by user")
                break
            
            # Check timeout more frequently
            if time.time() - start_time > timeout:
                log_message_callback(f"Timeout reached during link following after {timeout} seconds")
                break
            
            current_links = links_to_visit[:max_pages - pages_scraped]
            links_to_visit = links_to_visit[max_pages - pages_scraped:]
            
            log_message_callback(f"Processing {len(current_links)} links at depth {current_depth}")
            
            for link in current_links:
                # Check cancellation before each request
                if cancellation_callback():
                    log_message_callback("Web scraping cancelled by user")
                    break
                
                if pages_scraped >= max_pages:
                    break
                if link in visited_urls:
                    continue
                
                # Check timeout before each request
                if time.time() - start_time > timeout:
                    log_message_callback(f"Timeout reached before processing {link}")
                    break
                
                _progress(pages_scraped, max_pages, f"Scraping page {pages_scraped + 1}/{max_pages}: {link}")
                
                content, new_links = scrape_single_page(link, current_depth)
                if content:
                    all_content.append(f"=== RELATED PAGE ===\n{content}\n")
                    pages_scraped += 1
                    visited_urls.add(link)
                    log_message_callback(f"Visited: {link}")
                    
                    # Add new links for next iteration
                    for new_link in new_links:
                        if should_follow_link(new_link, current_depth + 1):
                            links_to_visit.append(new_link)
                
                # Check cancellation after each page
                if cancellation_callback():
                    log_message_callback("Web scraping cancelled by user")
                    break
                
                # Small delay to prevent overwhelming servers
                time.sleep(0.05)  # Reduced from 0.1 to 0.05 seconds
            
            # Check cancellation after processing batch
            if cancellation_callback():
                log_message_callback("Web scraping cancelled by user")
                break
            
            current_depth += 1
        
        # Combine all content
        final_content = '\n'.join(all_content)
        
        # Limit content size to prevent memory issues
        if len(final_content) > MAX_CONTENT_SIZE:  # 50KB limit
            final_content = final_content[:MAX_CONTENT_SIZE] + "\n\n[Content truncated due to length]"
        
        elapsed_time = time.time() - start_time
        log_message_callback(f"=== WEB SCRAPING COMPLETE ===")
        log_message_callback(f"Pages scraped: {pages_scraped}")
        log_message_callback(f"Total content: {len(final_content)} characters")
        log_message_callback(f"Time elapsed: {elapsed_time:.2f} seconds")
        
        _progress(PROGRESS_COMPLETE, PROGRESS_MAX, f"Web scraping completed: {pages_scraped} pages")
        return final_content
        
    except Exception as e:
        error_msg = f"Error during web scraping: {e}"
        log_message_callback(error_msg)
        return f"Error: {error_msg}"

def transcribe_youtube_tool(youtube_url: str, **kwargs) -> str:
    """
    Transcribe YouTube videos using yt-dlp and whisper.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)
    
    def _progress(current, total, message):
        if progress_callback:
            progress_callback(current, total, message)
    
    try:
        _progress(PROGRESS_MIN, PROGRESS_MAX, "Starting YouTube transcription...")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Download audio using yt-dlp
            def yt_dlp_progress_hook(d):
                if d['status'] == 'downloading':
                    total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                    if total_bytes > 0:
                        percentage = (d['downloaded_bytes'] / total_bytes) * PERCENTAGE_MULTIPLIER
                        _progress(int(percentage * PROGRESS_WEIGHT_DOWNLOAD), PROGRESS_MAX, f"Downloading audio... {d['_percent_str']}")
            
            # Download audio
            audio_path = os.path.join(temp_dir, "audio.mp3")
            yt_dlp_cmd = [
                'yt-dlp',
                '--extract-audio',
                '--audio-format', 'mp3',
                '--audio-quality', '0',
                '--output', audio_path,
                '--progress-hook', 'python -c "import sys; exec(sys.stdin.read())"',
                youtube_url
            ]
            
            # ... existing code ...

    except Exception as e:
        return f"An unexpected error occurred during transcription: {e}"
    finally:
        if 'temp_audio_path' in locals() and os.path.exists(temp_audio_path): 
            os.remove(temp_audio_path)

def batch_process_suggestions(suggestions: List[dict], model_mode: str, model_ref: str, tokenizer_ref: Any = None, **kwargs) -> List[str]:
    """Process multiple suggestions in batches for better performance."""
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)
    
    log_message_callback("=== BATCH PROCESSING START ===")
    log_message_callback(f"Processing {len(suggestions)} suggestions in batches")
    
    if not suggestions:
        log_message_callback("No suggestions to process")
        return []
    
    # Limit batch size to prevent timeout
    batch_size = 10  # Process 10 suggestions at a time
    total_suggestions = len(suggestions)
    explanations = []
    
    log_message_callback(f"Processing {total_suggestions} suggestions in batches of {batch_size}...")
    
    for batch_num, i in enumerate(range(0, total_suggestions, batch_size)):
        batch = suggestions[i:i + batch_size]
        batch_num += 1
        total_batches = (total_suggestions + batch_size - 1) // batch_size
        
        log_message_callback(f"=== PROCESSING BATCH {batch_num}/{total_batches} ===")
        log_message_callback(f"Batch {batch_num}: {len(batch)} suggestions")
        
        try:
            batch_explanations = _process_suggestion_batch(batch, model_mode, model_ref, tokenizer_ref, **kwargs)
            explanations.extend(batch_explanations)
            log_message_callback(f"Batch {batch_num} completed: {len(batch_explanations)} explanations generated")
        except Exception as e:
            log_message_callback(f"ERROR in batch {batch_num}: {e}")
            import traceback
            log_message_callback(f"Batch {batch_num} traceback: {traceback.format_exc()}")
            # Add fallback explanations for this batch
            fallback_explanations = [f"AI analysis for issue: {s.get('description', 'Unknown issue')}" for s in batch]
            explanations.extend(fallback_explanations)
        
        # Update progress
        progress_callback(i + len(batch), total_suggestions, f"Processed batch {batch_num}/{total_batches}")
        
        # Add small delay to prevent overwhelming the system
        log_message_callback(f"Batch {batch_num} delay: 0.1 seconds")
        time.sleep(0.1)
    
    log_message_callback(f"=== BATCH PROCESSING COMPLETE ===")
    log_message_callback(f"Total explanations generated: {len(explanations)}")
    
    return explanations

def _process_suggestion_batch(suggestions: List[dict], model_mode: str, model_ref: str, tokenizer_ref: Any = None, **kwargs) -> List[str]:
    """Process a batch of suggestions with AI explanations."""
    log_message_callback = kwargs.get('log_message_callback', print)
    
    log_message_callback(f"=== PROCESSING SUGGESTION BATCH ===")
    log_message_callback(f"Batch size: {len(suggestions)}")
    
    explanations = []
    
    for i, suggestion in enumerate(suggestions):
        try:
            log_message_callback(f"Processing suggestion {i+1}/{len(suggestions)}: {suggestion.get('description', 'Unknown')[:50]}...")
            
            explanation = get_ai_explanation(suggestion, model_mode, model_ref, tokenizer_ref, **kwargs)
            explanations.append(explanation)
            
            log_message_callback(f"Suggestion {i+1} completed: {len(explanation)} characters")
            
        except Exception as e:
            log_message_callback(f"Error processing suggestion {i+1}: {e}")
            import traceback
            log_message_callback(f"Suggestion {i+1} traceback: {traceback.format_exc()}")
            explanations.append("Error generating explanation.")
    
    log_message_callback(f"Batch processing complete: {len(explanations)} explanations")
    return explanations

class AITools:
    """
    AI Tools class that provides a unified interface for AI-powered code analysis.
    Wraps the existing functions for compatibility with PR and other modules.
    """
    
    def __init__(self):
        self.cache = AICache()
    
    def generate_explanation(self, suggestion: dict, model_mode: str, model_ref: str, tokenizer_ref: Any = None, **kwargs) -> str:
        """Generate AI explanation for a suggestion."""
        return get_ai_explanation(suggestion, model_mode, model_ref, tokenizer_ref, **kwargs)
    
    def generate_with_own_model(self, model, tokenizer, prompt: str, max_new_tokens: int = 50) -> str:
        """Generate text using the own trained model."""
        return generate_with_own_model(model, tokenizer, prompt, max_new_tokens)
    
    def browse_web(self, url: str, **kwargs) -> str:
        """Browse web content."""
        return browse_web_tool(url, **kwargs)
    
    def transcribe_youtube(self, youtube_url: str, **kwargs) -> str:
        """Transcribe YouTube video."""
        return transcribe_youtube_tool(youtube_url, **kwargs)
    
    def batch_process_suggestions(self, suggestions: List[dict], model_mode: str, model_ref: str, tokenizer_ref: Any = None, **kwargs) -> List[str]:
        """Process multiple suggestions in batches."""
        return batch_process_suggestions(suggestions, model_mode, model_ref, tokenizer_ref, **kwargs)
    
    def generate_report_and_training_data(self, suggestion_list, model_mode, model_ref, tokenizer_ref, **kwargs):
        """Generate report and training data."""
        return generate_report_and_training_data(suggestion_list, model_mode, model_ref, tokenizer_ref, **kwargs)

def _generate_ollama_explanation(suggestion, model_ref, log_message_callback):
    """Generate explanation using Ollama."""
    try:
        log_message_callback("Generating Ollama explanation...")
        issue_description = suggestion['description']
        prompt = f"""You are an expert programming instructor. A developer has a piece of code with a known issue and a proposed fix.
Your task is to provide a clear, concise explanation of *why* the proposed fix is better, adhering to best practices.

**Code Issue Details:**
- Issue: {suggestion['description']}
- Original Code: `{suggestion['code_snippet']}`
- Proposed Fix: `{suggestion['suggested_improvement']}`
**AI Justification:**
"""
        
        explanation = ollama_client.get_ollama_response(prompt, model_ref)
        if isinstance(explanation, str) and explanation.startswith("API_ERROR:"): 
            log_message_callback("Ollama API error, using fallback")
            return _generate_fallback_explanation(suggestion)
        
        return explanation
    except Exception as e:
        log_message_callback(f"Ollama explanation error: {e}")
        return _generate_fallback_explanation(suggestion)

def _generate_own_model_explanation(suggestion, model_ref, tokenizer_ref, log_message_callback):
    """Generate explanation using own model."""
    try:
        log_message_callback("Generating own model explanation...")
        return "Justification from the local model is not yet implemented. Focus is on code suggestion quality first."
    except Exception as e:
        log_message_callback(f"Own model explanation error: {e}")
        return _generate_fallback_explanation(suggestion)