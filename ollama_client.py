import requests
import json
import xml.etree.ElementTree as ET

OLLAMA_API_BASE_URL = "http://localhost:11434/api"

def list_ollama_models():
    """Fetches the list of locally available models from the Ollama service."""
    try:
        response = requests.get(f"{OLLAMA_API_BASE_URL}/tags", timeout=10)
        response.raise_for_status()
        models_data = response.json().get("models", [])
        return [model["name"] for model in models_data] if models_data else []
    except requests.exceptions.ConnectionError:
        return ["Error: Ollama not running?"]
    except Exception as e:
        print(f"An error occurred while listing Ollama models: {e}")
        return []

def get_ollama_response(prompt, model_name="llama3"):
    """Sends a single prompt to a model and gets a single response."""
    try:
        payload = {"model": model_name, "prompt": prompt, "stream": False}
        response = requests.post(f"{OLLAMA_API_BASE_URL}/generate", json=payload, timeout=90)
        response.raise_for_status()
        response_data = response.json()
        return response_data.get("response", "No response content found.")
    except requests.exceptions.ConnectionError:
        return ("Error: Could not connect to the Ollama service.\n"
                "Please ensure the Ollama application is running on your machine.")
    except requests.exceptions.RequestException as e:
        return f"An API error occurred: {e}"

def parse_tool_call(response_text):
    """Parses the model's response to check for a tool call XML block."""
    try:
        # Find the <tool_call> block and parse it
        if "<tool_call>" in response_text:
            root = ET.fromstring(response_text[response_text.find("<tool_call>"):response_text.find("</tool_call>") + 11])
            tool_name = root.find("tool_name").text.strip()
            parameters = {param.tag: param.text.strip() for param in root.find("parameters")}
            return tool_name, parameters
    except Exception:
        return None, None
    return None, None