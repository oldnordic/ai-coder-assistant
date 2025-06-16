# src/core/ollama_client.py
import requests
import json
import logging

# --- FIXED: Use the new settings module for configuration ---
from ..config import settings

def get_ollama_models_list(**kwargs):
    """
    Fetches the list of available models from the Ollama API.
    """
    log_message_callback = kwargs.get('log_message_callback', print)
    try:
        log_message_callback("Requesting model list from Ollama...")
        response = requests.get(f"{settings.OLLAMA_API_BASE_URL}/tags")
        response.raise_for_status()
        models_data = response.json()
        model_names = [model['name'] for model in models_data.get('models', [])]
        log_message_callback(f"Found Ollama models: {', '.join(model_names)}")
        return model_names
    except requests.RequestException as e:
        error_message = f"API_ERROR: Could not connect to Ollama. Please ensure it is running. Details: {e}"
        log_message_callback(error_message)
        return error_message
    except Exception as e:
        error_message = f"API_ERROR: An unexpected error occurred: {e}"
        log_message_callback(error_message)
        return error_message

def get_ollama_response(prompt: str, model_name: str) -> str:
    """
    Sends a prompt to the Ollama API and gets a streaming response.
    """
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False # Set to False for a single complete response
        }
        response = requests.post(
            f"{settings.OLLAMA_API_BASE_URL}/generate", 
            json=payload, 
            timeout=120
        )
        response.raise_for_status()
        
        # Since stream=False, the response is a single JSON object
        response_data = response.json()
        return response_data.get("response", "").strip()

    except requests.Timeout:
        return "API_ERROR: Request to Ollama timed out. The model may be too large or the prompt too complex."
    except requests.RequestException as e:
        return f"API_ERROR: Could not get response from Ollama. Details: {e}"
    except Exception as e:
        return f"API_ERROR: An unexpected error occurred: {e}"