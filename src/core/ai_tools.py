# src/core/ai_tools.py
import os
import requests
from bs4 import BeautifulSoup
import yt_dlp
from yt_dlp import YoutubeDL
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import re
from youtube_transcript_api import YouTubeTranscriptApi
import html
import torch
from transformers import GPT2LMHeadModel, GPT2Tokenizer
from typing import Optional, List, Dict, Tuple

from ..config import settings
from . import ollama_client
from ..training import trainer as train_language_model

"""Collection of helper routines used by the AI code assistant."""

# Global cache for the embedding model to prevent re-downloading
_embedding_model_cache = None

def get_embedding_model(log_callback):
    """
    Lazily loads and caches the SentenceTransformer model.
    """
    global _embedding_model_cache
    if _embedding_model_cache is None:
        log_callback(f"Loading embedding model '{settings.EMBEDDING_MODEL_NAME}' for the first time...")
        _embedding_model_cache = SentenceTransformer(settings.EMBEDDING_MODEL_NAME, device=settings.DEVICE)
        log_callback("Embedding model loaded.")
    return _embedding_model_cache

def generate_with_own_model(
    model: GPT2LMHeadModel,
    tokenizer: GPT2Tokenizer,
    prompt: str,
    max_new_tokens: int = 50
) -> str:
    """Generate a code suggestion using the locally trained model."""
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
    """Build a Markdown review report and JSONL training file from suggestions."""
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
        
        filepath = suggestion.get('filepath', 'N/A')
        line_num = suggestion.get('line_number', -1) + 1
        issue = suggestion.get('description', 'N/A')
        original_code = suggestion.get('original_code', '')
        proposed_code = suggestion.get('proposed_code', '')
        
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
    """Ask the model to explain why the proposed code change fixes the issue."""

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
- Original Code: `{suggestion['original_code']}`
- Proposed Fix: `{suggestion['proposed_code']}`
**AI Justification:**
"""
        
        explanation = ollama_client.get_ollama_response(prompt, model_ref)
        if isinstance(explanation, str) and explanation.startswith("API_ERROR:"): 
            return f"Could not generate explanation: {explanation}"
        return explanation
    except Exception as e:
        return f"An unexpected error occurred while generating the explanation: {e}"

def query_knowledge_base(query_text: str, log_message_callback=None) -> str:
    """Retrieve documentation snippets relevant to *query_text* from FAISS."""

    _log = log_message_callback if callable(log_message_callback) else print
    try:
        if not os.path.exists(settings.FAISS_INDEX_PATH): return "Knowledge base not found."
        index = faiss.read_index(settings.FAISS_INDEX_PATH)
        with open(settings.FAISS_METADATA_PATH, 'r', encoding='utf-8', errors='ignore') as f: documents = json.load(f)
        
        model = get_embedding_model(_log)
        
        query_embedding = model.encode([query_text]).astype('float32')
        k = 3
        distances, indices = index.search(query_embedding, k)
        results = [documents[i] for i in indices[0] if i < len(documents)]
        return "\n\n---\n\n".join(results) if results else "No specific context found."
    except Exception as e:
        _log(f"Error querying knowledge base: {e}")
        return f"Error querying knowledge base: {e}"

def browse_web_tool(url: str, **kwargs) -> str:
    """Fetch and return cleaned text content from a web page."""

    log_message_callback = kwargs.get('log_message_callback', print)
    _log = log_message_callback
    try:
        _log(f"Attempting to browse URL: {url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            script_or_style.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return text[:4000] + "..." if len(text) > 4000 else text
    except Exception as e:
        _log(f"Error during web browse: {e}")
        return f"Error during web browse: {e}"

def transcribe_youtube_tool(youtube_url: str, **kwargs) -> str:
    """Download and transcribe audio from a YouTube video."""

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
