# ai_tools.py
import os
import requests
from bs4 import BeautifulSoup
import yt_dlp
from yt_dlp import YoutubeDL # Ensure this is imported correctly
import whisper # This import is present but not used in the provided transcribe_youtube_tool logic.
import faiss
import numpy as np
import json
from sentence_transformers import SentenceTransformer
import config
import re
from youtube_transcript_api import YouTubeTranscriptApi # Ensure this is imported correctly


# --- File System Tools ---
def read_file_tool(filepath: str, project_root: str) -> str:
    """
    Reads the content of a file.
    Args:
        filepath (str): The path to the file relative to the project_root.
        project_root (str): The root directory of the current project.
    Returns:
        str: The content of the file, or an error message.
    """
    try:
        # Construct absolute path and ensure it's within the project root for security
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
    """
    Writes content to a file. Creates directories if they don't exist.
    Args:
        filepath (str): The path to the file relative to the project_root.
        content (str): The content to write to the file.
        project_root (str): The root directory of the current project.
    Returns:
        str: Success message or error message.
    """
    try:
        # Construct absolute path and ensure it's within the project root for security
        abs_filepath = os.path.abspath(os.path.join(project_root, filepath))
        if not abs_filepath.startswith(os.path.abspath(project_root)):
            return f"Error: Access denied. Cannot write outside of project root: {filepath}"

        os.makedirs(os.path.dirname(abs_filepath), exist_ok=True)
        with open(abs_filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"File written successfully to {filepath}."
    except Exception as e:
        return f"Error writing file {filepath}: {e}"

# --- Web Browse Tool ---
def browse_web_tool(url: str, log_message_callback=None) -> str:
    """
    Browses a given URL, extracts and returns a summary of its text content.
    Args:
        url (str): The URL to browse.
        log_message_callback (callable, optional): Callback for logging messages.
    Returns:
        str: A summary of the web page text content, or an error message.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    try:
        _log(f"Browse URL: {url}")
        headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'}
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() # Raise HTTPError for bad responses (4xx or 5xx)
        
        soup = BeautifulSoup(response.text, 'html.parser')
        # Remove script and style elements to get cleaner text
        for script_or_style in soup(['script', 'style', 'nav', 'footer', 'header', 'aside']):
            script_or_style.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        # Limit the text length to avoid overwhelming the LLM
        return text[:4000] + "..." if len(text) > 4000 else text
    except requests.exceptions.RequestException as e:
        _log(f"Error Browse {url}: {e}")
        return f"Error Browse {url}: {e}"
    except Exception as e:
        _log(f"An unexpected error occurred during web Browse: {e}")
        return f"Error during web Browse: {e}"

# --- YouTube Transcription Tool ---
# MODIFIED: Added progress_callback
def transcribe_youtube_tool(youtube_url: str, saving_callback=None, log_message_callback=None, progress_callback=None) -> str:
    """
    Transcribes a YouTube video using YouTube Transcript API or yt-dlp fallback.
    Args:
        youtube_url (str): The URL of the YouTube video.
        saving_callback (callable, optional): A callback function to save the transcribed text.
        log_message_callback (callable, optional): Callback for logging messages.
        progress_callback (callable, optional): Callback for reporting progress.
    Returns:
        str: The full transcription of the video, or an error message.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    _progress = progress_callback if callable(progress_callback) else (lambda current, total, msg: None) # Default no-op
    
    try:
        video_id_match = re.search(r"(?:v=|\/)([0-9A-Za-z_-]{11}).*", youtube_url)
        if not video_id_match:
            _log(f"Error: Could not extract video ID from URL: {youtube_url}")
            return "Could not extract video ID from URL."
        video_id = video_id_match.group(1)

        transcript_text = ""
        _progress(0, 100, "Attempting API Transcription...")

        # --- Primary Attempt: youtube-transcript-api ---
        try:
            _log(f"Attempting transcription via YouTube Transcript API for {video_id}...")
            transcript_list = YouTubeTranscriptApi.list_transcripts(video_id)
            
            target_lang_codes_yt_api = ['en', 'a.en', 'en-US', 'en-GB'] 
            found_lang = None
            for lang_code in target_lang_codes_yt_api:
                if lang_code in transcript_list._manually_created_transcripts:
                    found_lang = lang_code
                    _log(f"Found manually created '{lang_code}' transcript.")
                    break
                elif lang_code in transcript_list._generated_transcripts:
                    found_lang = lang_code
                    _log(f"Found auto-generated '{lang_code}' transcript.")
                    break
            
            if found_lang:
                transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[found_lang])
            else:
                available_languages = list(transcript_list._data.keys())
                if available_languages:
                    _log(f"No specific English transcript found via API. Fetching first available: {available_languages[0]}.")
                    transcript_data = YouTubeTranscriptApi.get_transcript(video_id, languages=[available_languages[0]])
                else:
                    _log(f"No transcripts found via YouTube Transcript API for {video_id}.")
                    transcript_data = []

            transcript_text = " ".join([entry['text'] for entry in transcript_data])
            
            if transcript_text:
                _progress(100, 100, "Transcription complete (API).")
                _log(f"Successfully transcribed video {video_id} via YouTube Transcript API (length: {len(transcript_text)}).")
                if saving_callback:
                    saving_callback(transcript_text, youtube_url)
                return transcript_text
            else:
                _log(f"YouTube Transcript API returned empty or no transcript for {video_id}. Proceeding to yt-dlp fallback.")

        except Exception as api_e:
            _log(f"Error fetching transcript via YouTube Transcript API ({api_e}). Proceeding to yt-dlp fallback.")

        # --- Fallback Attempt: yt-dlp for direct subtitle download ---
        _progress(0, 100, "Falling back to yt-dlp (Extracting Info)...")
        _log(f"Attempting yt-dlp fallback for subtitles for {video_id}...")
        ydl_opts = {
            'writesubtitles': True,
            'subtitleslangs': ['en', 'en.*'], # Request English and auto-generated English
            'skip_download': True, # Only extract info, don't download video
            'outtmpl': 'temp_yt_dlp_subtitle', # Temporary name if it needed to create a file
            'quiet': True, # Suppress yt-dlp output
            'no_warnings': True,
            'extractor_args': {'youtube': {'skip_hls_manifest': True}},
            'retries': 2, # Reduce retries to speed up failure
            'socket_timeout': 10 
        }
        
        info_dict = None
        try:
            with YoutubeDL(ydl_opts) as ydl:
                info_dict = ydl.extract_info(youtube_url, download=False)
        except yt_dlp.utils.DownloadError as download_e:
            _log(f"yt-dlp DownloadError (often due to no suitable subs found or network issue): {download_e}")
            _progress(100, 100, "Transcription failed (No English Subs).")
            return f"No suitable English subtitles found via yt-dlp (DownloadError: {download_e})."
        except Exception as e:
            _log(f"Generic error during yt-dlp info extraction for {video_id}: {e}")
            _progress(100, 100, "Transcription failed (Info Extract Error).")
            return f"Failed to extract video info via yt-dlp: {e}"

        if info_dict:
            _progress(50, 100, "Finding Subtitle URL...")
            subtitle_url = None
            target_lang_codes_yt_dlp = ['en', 'en-orig', 'en-US', 'a.en', 'en-GB'] 

            for lang_code in target_lang_codes_yt_dlp:
                if 'subtitles' in info_dict and lang_code in info_dict['subtitles']:
                    for sub_track in info_dict['subtitles'][lang_code]:
                        if sub_track.get('url'):
                            subtitle_url = sub_track['url']
                            _log(f"Found {lang_code} subtitle URL via yt-dlp for {video_id}: {subtitle_url[:100]}...")
                            break
                if subtitle_url: break 

            if subtitle_url:
                _progress(75, 100, "Downloading & Parsing Subtitles...")
                try:
                    response = requests.get(subtitle_url, timeout=15)
                    response.raise_for_status()
                    
                    lines = response.text.splitlines()
                    cleaned_lines = []
                    for line in lines:
                        if re.match(r'^[0-9:\.,-]+ --> [0-9:\.,-]+$', line) or re.match(r'^[0-9]+$', line) or line.strip() == '':
                            continue
                        cleaned_lines.append(line.strip())
                    
                    transcript_text = " ".join(cleaned_lines).replace("  ", " ").strip()
                    _progress(100, 100, "Transcription complete (yt-dlp).")
                    _log(f"Successfully transcribed video {video_id} via yt-dlp direct subtitle download (length: {len(transcript_text)}).")
                    
                    if saving_callback:
                        saving_callback(transcript_text, youtube_url)
                    return transcript_text
                except requests.exceptions.RequestException as req_e:
                    _log(f"Error downloading subtitle from URL for {video_id}: {req_e}")
                    _progress(100, 100, "Transcription failed (Sub Download Error).")
                    return f"Failed to download subtitle from yt-dlp URL: {req_e}"
                except Exception as parse_e:
                    _log(f"Error parsing downloaded subtitle for {video_id}: {parse_e}")
                    _progress(100, 100, "Transcription failed (Sub Parse Error).")
                    return f"Failed to parse downloaded subtitle: {parse_e}"
            else:
                _log(f"yt-dlp could not find any suitable English subtitle URL for {video_id} after info extraction. Available subs: {info_dict.get('subtitles', 'None')}")
                _progress(100, 100, "Transcription failed (No English Subs URL).")
                return "No suitable English subtitles found via yt-dlp after initial info scan."
        else:
            _log(f"yt-dlp failed to extract info for {video_id} or no info_dict was returned.")
            _progress(100, 100, "Transcription failed (No Info Dict).")
            return "Failed to extract video info via yt-dlp."
        
    except Exception as e:
        _log(f"An unexpected error occurred during YouTube transcription for {video_id}: {e}")
        _progress(100, 100, "Transcription failed (Unexpected Error).")
        return f"Transcription failed: {e}"

# --- The "Brain" / RAG Tool using FAISS ---
def query_knowledge_base(query_text: str, log_message_callback=None) -> str:
    """
    Searches the local knowledge base (FAISS index) for information
    relevant to the user's query and returns the context.
    Args:
        query_text (str): The user's query.
        log_message_callback (callable, optional): Callback for logging messages.
    Returns:
        str: Relevant context from the knowledge base, or an error/info message.
    """
    _log = log_message_callback if callable(log_message_callback) else print
    try:
        if not os.path.exists(config.FAISS_INDEX_PATH) or not os.path.exists(config.FAISS_METADATA_PATH):
            _log("Knowledge base not found. Please run 'Pre-process All Docs' on the 'Data & Training' tab first.")
            return "Knowledge base not found. Please run 'Pre-process All Docs' on the 'Data & Training' tab first."

        _log("Loading FAISS index and documents...")
        index = faiss.read_index(config.FAISS_INDEX_PATH)
        
        with open(config.FAISS_METADATA_PATH, 'r', encoding='utf-8') as f:
            documents = json.load(f)

        _log("Loading embedding model...")
        model = SentenceTransformer(config.EMBEDDING_MODEL_NAME)
        
        _log(f"Encoding query: '{query_text[:50]}...'")
        query_embedding = model.encode([query_text]).astype('float32')
        
        k = 5 # Retrieve top 5 relevant chunks
        _log(f"Searching FAISS index for top {k} results...")
        distances, indices = index.search(query_embedding, k)
        
        results = []
        for i, dist in zip(indices[0], distances[0]):
            if i < len(documents): 
                results.append(documents[i])
            else:
                _log(f"Warning: FAISS returned out-of-bounds index {i}. Document list size: {len(documents)}")

        if results:
            context = "\n\n---\n\n".join(results)
            _log(f"Retrieved {len(results)} relevant context chunks.")
            return f"Context from knowledge base:\n{context}"
        else:
            _log("No relevant context found in the knowledge base.")
            return "No relevant context found in the knowledge base for your query."

    except Exception as e:
        _log(f"Error querying knowledge base: {e}")
        return f"Error querying knowledge base: {e}"

# --- List of available tools for AI Agent ---
AVAILABLE_TOOLS = {
    "query_knowledge_base": query_knowledge_base,
    "read_file": read_file_tool,
    "write_file": write_file_tool,
    "browse_web": browse_web_tool,
    "transcribe_youtube": transcribe_youtube_tool,
}