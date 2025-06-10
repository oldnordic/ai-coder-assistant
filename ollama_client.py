import requests
import json

# A more general base URL for the Ollama API
OLLAMA_API_BASE_URL = "http://localhost:11434/api"

def list_ollama_models():
    """
    Fetches the list of locally available models from the Ollama service.
    
    Returns:
        A list of model names, or a list with an error message if it fails.
    """
    try:
        # The correct endpoint for listing installed models is /tags
        response = requests.get(f"{OLLAMA_API_BASE_URL}/tags", timeout=10)
        response.raise_for_status()
        models_data = response.json().get("models", [])
        
        # Return an empty list if no models are found, otherwise return their names
        return [model["name"] for model in models_data] if models_data else []

    except requests.exceptions.ConnectionError:
        print("Connection Error: Could not connect to Ollama service.")
        # Return a specific message for the UI dropdown
        return ["Error: Ollama not running?"]
    except Exception as e:
        print(f"An error occurred while listing Ollama models: {e}")
        return [] # Return an empty list for other errors

def get_ollama_analysis(prompt, model_name="llama3"):
    """
    Sends a prompt to a locally running Ollama model and gets a response.
    
    Returns:
        A string containing the model's response, or an error message.
    """
    try:
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
        }
        
        # The correct endpoint for generation is /generate
        response = requests.post(f"{OLLAMA_API_BASE_URL}/generate", json=payload, timeout=90)
        response.raise_for_status()
        
        response_data = response.json()
        return response_data.get("response", "No response content found.")

    except requests.exceptions.ConnectionError:
        return ("Error: Could not connect to the Ollama service.\n"
                "Please ensure the Ollama application is running on your machine.")
    except requests.exceptions.RequestException as e:
        return f"An API error occurred: {e}"