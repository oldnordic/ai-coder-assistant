# ollama_client.py
import requests
import json
import config

def get_ollama_models_list(**kwargs):
    """
    Fetches the list of available models from the Ollama API.
    Designed to be run in a worker thread.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    try:
        log_message_callback("Requesting model list from Ollama...")
        response = requests.get(f"{config.OLLAMA_API_BASE_URL}/tags", timeout=5)
        response.raise_for_status()
        models_data = response.json()
        model_names = [model['name'] for model in models_data.get('models', [])]
        log_message_callback(f"Found Ollama models: {', '.join(model_names)}")
        return model_names
    except requests.exceptions.RequestException as e:
        log_message_callback(f"Ollama API Error: {e}")
        return f"API_ERROR: {e}"

def get_ollama_response(prompt, model_name, **kwargs):
    log_message_callback = kwargs.get('log_message_callback', print)
    try:
        log_message_callback(f"Sending prompt to Ollama model: {model_name}")
        response = requests.post(
            f"{config.OLLAMA_API_BASE_URL}/generate",
            json={"model": model_name, "prompt": prompt, "stream": False},
            timeout=60
        )
        response.raise_for_status()
        return response.json().get('response', '')
    except requests.exceptions.RequestException as e:
        log_message_callback(f"Ollama API Error: {e}")
        return f"API_ERROR: {e}"

def enhance_with_ollama(filepath, issue_line, model_name, **kwargs):
    """
    Generates a code suggestion using an Ollama model.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    with open(filepath, 'r', encoding='utf-8') as f:
        code_content = f.read()
    
    # --- THIS IS THE FIX ---
    # The multi-line f-string that was causing a SyntaxError has been
    # replaced by joining a list of strings. This is more robust.
    prompt_lines = [
        f"You are an expert Python programmer. Analyze the following code from the file '{filepath}'.",
        f"A static analysis tool reported this issue: '{issue_line}'.",
        "Focus on the line of code relevant to the issue. Provide a direct code replacement for the incorrect line.",
        "Do not explain your reasoning, just provide the corrected line of code.",
        "",
        "Full code for context:",
        "```python",
        code_content,
        "```",
        "",
        f"Correct the line related to the issue: '{issue_line}'"
    ]
    prompt = "\n".join(prompt_lines)
    
    suggestion = get_ollama_response(prompt, model_name, log_message_callback=log_message_callback)
    return suggestion