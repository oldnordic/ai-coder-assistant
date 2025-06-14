# ollama_client.py
import requests
import xml.etree.ElementTree as ET
from config import OLLAMA_API_BASE_URL

def list_ollama_models():
    """Fetches a list of available models from the Ollama service."""
    try:
        response = requests.get(f"{OLLAMA_API_BASE_URL}/tags", timeout=10)
        response.raise_for_status()
        models_data = response.json().get("models", [])
        return [model['name'] for model in models_data]
    except requests.exceptions.RequestException as e:
        print(f"Ollama connection error: {e}")
        return [{"Error": "Could not connect to Ollama. Please ensure it is running."}]

def get_ollama_response(prompt, model_name="llama3"):
    """Sends a prompt to the Ollama service and gets a response using the chat endpoint."""
    try:
        # Use the /api/chat endpoint for better interaction with models like Llama3
        # Format the prompt as a message list, as expected by /api/chat
        payload = {
            "model": model_name,
            "messages": [
                {"role": "user", "content": prompt}
            ],
            "stream": False # Set to True if you want streaming responses
        }
        
        # Change endpoint from /generate to /chat
        response = requests.post(f"{OLLAMA_API_BASE_URL}/chat", json=payload, timeout=90)
        response.raise_for_status()
        
        # For /api/chat, the response content is usually in response['message']['content']
        return response.json().get('message', {}).get('content', '').strip()
    except requests.exceptions.RequestException as e:
        error_message = f"API_ERROR: {e}"
        print(f"Ollama API Error: {e}")
        return error_message

def parse_tool_call(response_text):
    """Parses an XML tool call from the AI's response text."""
    try:
        start_tag = "<tool_call>"
        end_tag = "</tool_call>" # Corrected from </tool_tag>
        start_index = response_text.find(start_tag)
        end_index = response_text.find(end_tag)

        if start_index != -1 and end_index != -1:
            xml_content = response_text[start_index : end_index + len(end_tag)]
            root = ET.fromstring(xml_content)
            tool_name = root.find("tool_name").text.strip()
            parameters = {param.tag: param.text.strip() for param in root.find("parameters")}
            return tool_name, parameters
    except Exception:
        pass
    return None, None