# ai_tools.py
import os
import requests
from bs4 import BeautifulSoup
import yt_dlp
from yt_dlp import YoutubeDL
import whisper
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import config
import re
from youtube_transcript_api import YouTubeTranscriptApi
import ollama_client
import html

def generate_html_report(suggestion_list, **kwargs):
    """
    Iterates through all suggestions, gets an AI explanation for each,
    and compiles them into a single HTML report string.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    progress_callback = kwargs.get('progress_callback', lambda c, t, m: None)

    log_message_callback("Starting HTML report generation...")
    
    html_parts = [
        """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <title>AI Code Review Report</title>
    <style>
        body { font-family: sans-serif; line-height: 1.6; padding: 20px; background-color: #2b2b2b; color: #dcdcdc; }
        .suggestion { border: 1px solid #444; border-radius: 8px; margin-bottom: 2em; padding: 1em; background-color: #3c3c3c; }
        .code { background-color: #222; padding: 10px; border-radius: 5px; font-family: monospace; white-space: pre-wrap; }
        .original { border-left: 3px solid #a83232; }
        .proposed { border-left: 3px solid #32a852; }
        h1, h2, h3, h4 { color: #dcdcdc; }
        h2 { border-top: 2px solid #555; padding-top: 1em;}
        h3 { border-bottom: 1px solid #555; padding-bottom: 5px; }
        p { margin-left: 1em; }
    </style>
</head>
<body>
    <h1>AI Code Review Report</h1>
"""
    ]
    
    total_suggestions = len(suggestion_list)
    for i, suggestion in enumerate(suggestion_list):
        progress_callback(i, total_suggestions, f"Generating explanation {i+1}/{total_suggestions}...")
        
        explanation = get_ai_explanation(suggestion, **kwargs)
        
        filepath = suggestion.get('filepath', 'N/A')
        line_num = suggestion.get('line_number', -1) + 1
        issue = html.escape(suggestion.get('description', 'N/A'))
        original_code = html.escape(suggestion.get('original_code', ''))
        proposed_code = html.escape(suggestion.get('proposed_code', ''))
        
        html_parts.append(f"""
    <div class="suggestion">
        <h2>File: {filepath} (Line: {line_num})</h2>
        <h3>Issue: {issue}</h3>
        <h4>Original Code:</h4>
        <div class="code original">{original_code}</div>
        <h4>Proposed Fix:</h4>
        <div class="code proposed">{proposed_code}</div>
        <h4>AI Justification:</h4>
        <p>{html.escape(explanation).replace(os.linesep, '<br>')}</p>
    </div>
""")

    html_parts.append("</body></html>")
    log_message_callback("HTML report generation complete.")
    progress_callback(total_suggestions, total_suggestions, "Report generated.")
    return "".join(html_parts)

def get_ai_explanation(suggestion, **kwargs):
    log_message_callback = kwargs.get('log_message_callback', print)
    try:
        issue_description = suggestion['description']
        log_message_callback(f"Querying knowledge base for context on: '{issue_description}'")
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
**Your Task:**
Explain why the proposed fix is the correct approach. Justify it based on the documentation context provided and general programming principles like readability, efficiency, or safety. Keep the explanation focused and helpful.
"""
        explanation = ollama_client.get_ollama_response(prompt, config.OLLAMA_MODEL)
        if explanation.startswith("API_ERROR:"): return f"Could not generate explanation: {explanation}"
        return explanation
    except Exception as e:
        return f"An unexpected error occurred while generating the explanation: {e}"

def read_file_tool(filepath: str, project_root: str) -> str:
    try:
        abs_filepath = os.path.abspath(os.path.join(project_root, filepath))
        if not abs_filepath.startswith(os.path.abspath(project_root)):
            return f"Error: Access denied. File is outside of project root: {filepath}"
        if not os.path.exists(abs_filepath):
            return f"Error: File not found at {filepath}"
        with open(abs_filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        return content
    except Exception as e:
        return f"Error reading file {filepath}: {e}"

def write_file_tool(filepath: str, content: str, project_root: str) -> str:
    try:
        abs_filepath = os.path.abspath(os.path.join(project_root, filepath))
        if not abs_filepath.startswith(os.path.abspath(project_root)):
            return f"Error: Access denied. Cannot write outside of project root: {filepath}"
        os.makedirs(os.path.dirname(abs_filepath), exist_ok=True)
        with open(abs_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File written successfully to {filepath}."
    except Exception as e:
        return f"Error writing file {filepath}: {e}"

def browse_web_tool(url: str, **kwargs) -> str:
    log_message_callback = kwargs.get('log_message_callback', print)
    _log = log_message_callback
    try:
        _log(f"Browse URL: {url}")
        headers = {'User-Agent': 'Mozilla/5.0'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            script_or_style.decompose()
        text = soup.get_text(separator='\n', strip=True)
        return text[:4000] + "..." if len(text) > 4000 else text
    except Exception as e:
        _log(f"Error during web Browse: {e}")
        return f"Error during web Browse: {e}"

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
            _log(f"API transcription failed ({api_e}). Falling back to Whisper.")
        temp_audio_path = os.path.join(config.PROJECT_ROOT, f"temp_audio_{video_id}.mp3")
        def yt_dlp_progress_hook(d):
            if d['status'] == 'downloading':
                total_bytes = d.get('total_bytes') or d.get('total_bytes_estimate')
                if total_bytes:
                    percentage = (d['downloaded_bytes'] / total_bytes) * 100
                    _progress(int(percentage * 0.33), 100, f"Stage 2/3: Downloading audio... {d['_percent_str']}")
            elif d['status'] == 'finished': _progress(33, 100, "Stage 2/3: Download complete.")
        ydl_opts = {'format': 'bestaudio/best', 'postprocessors': [{'key': 'FFmpegExtractAudio', 'preferredcodec': 'mp3', 'preferredquality': '192'}], 'outtmpl': os.path.splitext(temp_audio_path)[0], 'noplaylist': True, 'progress_hooks': [yt_dlp_progress_hook]}
        try:
            with YoutubeDL(ydl_opts) as ydl: ydl.download([youtube_url])
            _progress(40, 100, "Stage 3/3: Loading model...")
            model = whisper.load_model("tiny")
            _progress(50, 100, "Stage 3/3: Transcribing...")
            result = model.transcribe(temp_audio_path, fp16=False)
            transcript_text = result['text']
            _log("Whisper transcription finished.")
            _progress(100, 100, "Transcription complete!")
            return transcript_text
        finally:
            if os.path.exists(temp_audio_path): os.remove(temp_audio_path)
    except Exception as e:
        _log(f"An unexpected error occurred during transcription: {e}")
        return f"An unexpected error occurred during transcription: {e}"

def query_knowledge_base(query_text: str, log_message_callback=None) -> str:
    _log = log_message_callback if callable(log_message_callback) else print
    try:
        if not os.path.exists(config.FAISS_INDEX_PATH): return "Knowledge base not found."
        index = faiss.read_index(config.FAISS_INDEX_PATH)
        with open(config.FAISS_METADATA_PATH, 'r', encoding='utf-8') as f: documents = json.load(f)
        model = SentenceTransformer(config.EMBEDDING_MODEL_NAME, device=config.DEVICE)
        query_embedding = model.encode([query_text]).astype('float32')
        k = 3
        distances, indices = index.search(query_embedding, k)
        results = [documents[i] for i in indices[0] if i < len(documents)]
        return "\n\n---\n\n".join(results) if results else "No specific context found."
    except Exception as e:
        _log(f"Error querying knowledge base: {e}")
        return f"Error querying knowledge base: {e}"

AVAILABLE_TOOLS = {
    "query_knowledge_base": query_knowledge_base,
    "read_file": read_file_tool,
    "write_file": write_file_tool,
    "browse_web": browse_web_tool,
    "transcribe_youtube": transcribe_youtube_tool,
    "get_ai_explanation": get_ai_explanation,
    "generate_html_report": generate_html_report,
}