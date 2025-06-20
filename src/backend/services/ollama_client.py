"""
Ollama client service module.
"""

import logging
import httpx
from typing import List, Dict, Any
import asyncio
import requests
import json
import re

logger = logging.getLogger(__name__)

class OllamaClient:
    """Client for interacting with Ollama API."""
    
    def __init__(self, base_url: str = "http://localhost:11434"):
        self.base_url = base_url.rstrip('/')
        self.client = httpx.AsyncClient(base_url=self.base_url, timeout=180.0)
    
    async def list_models(self) -> List[Dict[str, Any]]:
        """List available models with their details."""
        try:
            response = await self.client.get("/api/tags")
            response.raise_for_status()
            data = response.json()
            return data.get("models", [])
        except Exception as e:
            logger.error(f"Error listing Ollama models: {e}")
            raise Exception(f"Error listing Ollama models: {e}")
    
    async def delete_model(self, model_name: str) -> bool:
        """Delete a model from Ollama."""
        try:
            # httpx's delete method doesn't directly support a json body.
            # We use the general `request` method instead.
            response = await self.client.request(
                "DELETE",
                "/api/delete",
                json={"name": model_name}
            )
            response.raise_for_status()
            logger.info(f"Successfully deleted model: {model_name}")
            return True
        except httpx.HTTPStatusError as e:
            logger.error(f"Error deleting Ollama model {model_name}: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"An unexpected error occurred while deleting model {model_name}: {e}")
            return False
    
    async def generate(self, model: str, prompt: str, stream: bool = False, temperature: float = 0.7) -> str:
        """Generate text using specified model."""
        try:
            data: Dict[str, object] = {
                "model": model,
                "prompt": prompt,
                "stream": stream,
                "temperature": temperature
            }
            response = await self.client.post("/api/generate", json=data)
            response.raise_for_status()
            return response.json().get("response", "")
        except Exception as e:
            logger.error(f"Error generating with Ollama: {e}")
            raise Exception(f"Error generating with Ollama: {e}")
    
    async def close(self):
        """Close the client session."""
        await self.client.aclose()

# Global instance
_global_ollama_client = OllamaClient()

def get_available_models_sync() -> List[str]:
    """Get list of available Ollama models synchronously."""
    try:
        # Try to connect to Ollama service
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            logger.error(f"Failed to connect to Ollama service: {response.status_code}")
            return []
            
        # Parse response
        data: Dict[str, List[Dict[str, str]]] = response.json()
        if not isinstance(data, dict) or 'models' not in data:
            logger.error("Invalid response format from Ollama service")
            return []
            
        # Extract model names with proper type hints
        models: List[str] = []
        for model_data in data['models']:
            if isinstance(model_data, dict) and 'name' in model_data and isinstance(model_data['name'], str):
                models.append(model_data['name'])
                
        if not models:
            logger.warning("No models found in Ollama service")
            
        return models
        
    except requests.exceptions.ConnectionError:
        logger.error("Failed to connect to Ollama service - is it running?")
        return []
    except Exception as e:
        logger.error(f"Error getting Ollama models: {e}")
        return []

def _extract_json_from_response(response_text: str) -> str:
    """Extracts JSON string from a response that might contain other text."""
    # Pattern to find JSON block within triple backticks
    pattern = r"```json\s*([\s\S]*?)\s*```"
    match = re.search(pattern, response_text)
    if match:
        return match.group(1).strip()

    # Fallback for responses without backticks
    # Find the start of the JSON - it can be an object or an array
    json_start = -1
    first_brace = response_text.find('{')
    first_bracket = response_text.find('[')

    if first_brace != -1 and first_bracket != -1:
        json_start = min(first_brace, first_bracket)
    elif first_brace != -1:
        json_start = first_brace
    else:
        json_start = first_bracket

    if json_start == -1:
        return "" # No JSON found

    # Find the end of the JSON by balancing brackets/braces
    # This is a simplified implementation and might not cover all edge cases
    open_brackets = 0
    open_braces = 0
    in_string = False
    
    for i in range(json_start, len(response_text)):
        char = response_text[i]
        
        if char == '"' and (i == 0 or response_text[i-1] != '\\'):
            in_string = not in_string
        
        if not in_string:
            if char == '[':
                open_brackets += 1
            elif char == ']':
                open_brackets -= 1
            elif char == '{':
                open_braces += 1
            elif char == '}':
                open_braces -= 1

            if open_brackets == 0 and open_braces == 0 and (open_braces > 0 or open_brackets > 0):
                return response_text[json_start:i+1]
    
    return "" # Unbalanced JSON

async def analyze_code(client: OllamaClient, content: str, model_name: str) -> List[Dict[str, Any]]:
    """Analyze code using Ollama model (async).
    
    Args:
        client: An instance of OllamaClient.
        content: The code content to analyze.
        model_name: Name of the Ollama model to use.
        
    Returns:
        List of issues found in the code.
    """
    prompt = f"""Analyze the following code and identify potential issues, improvements, and best practices:

{content}

Provide your analysis in a valid JSON format. The JSON should be an array of objects, where each object represents a single issue. Example format:
[
    {{
        "line_number": <line number>,
        "description": "<description of the issue>",
        "severity": "<low|medium|high>",
        "suggestion": "<suggestion for improvement>",
        "code_snippet": "<relevant code snippet>",
        "context": "<additional context>"
    }}
]
"""
    try:
        response_text = await client.generate(
            model=model_name,
            prompt=prompt,
            temperature=0.2 # Lower temperature for more predictable, structured output
        )
        
        if not response_text or not response_text.strip():
            logger.error("Ollama API returned empty response text")
            return []

        # Extract JSON from potentially conversational response
        json_text = _extract_json_from_response(response_text)
        if not json_text:
            logger.error("Could not extract JSON from model response.")
            logger.debug(f"Full response text: {response_text}")
            return []

        results = json.loads(json_text)
        
        # If the model returns a single object, wrap it in a list
        if isinstance(results, dict):
            logger.warning("Model returned a single dictionary, wrapping in a list.")
            return [results]
            
        if not isinstance(results, list):
            logger.error(f"Model returned non-list/non-dict results: {type(results)}")
            return []
        
        return results
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse model response as JSON: {e}")
        logger.debug(f"Response text that failed to parse: {response_text}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during code analysis: {e}", exc_info=True)
        return []

async def get_suggestion_for_issue(client: OllamaClient, issue: Dict[str, Any], model_name: str) -> str:
    """Gets an AI-powered suggestion for a single code issue."""
    
    code_snippet = issue.get('code_snippet', '')
    description = issue.get('description', '')
    file_path = issue.get('file_path', '')
    
    prompt = f"""Given the following code snippet from the file '{file_path}':
```
{code_snippet}
```
An issue was detected: "{description}".

Please provide a concise code suggestion to fix this issue.
Only provide the corrected code, without any additional explanation or formatting.
"""

    try:
        suggestion = await client.generate(
            model=model_name,
            prompt=prompt,
            temperature=0.2 
        )
        return suggestion.strip()
    except Exception as e:
        logger.error(f"Error getting suggestion from Ollama: {e}")
        return "Suggestion not available."

async def get_suggestions_for_issues_batch(client: OllamaClient, issues: List[Dict[str, Any]], model_name: str) -> List[Dict[str, Any]]:
    """Gets AI-powered suggestions for a batch of code issues."""
    
    issue_list_str = ""
    for i, issue in enumerate(issues):
        code_snippet = issue.get('code_snippet', '').replace('`', '\\`')
        description = issue.get('description', '')
        file_path = issue.get('file_path', '')
        issue_list_str += f"Issue {i+1}:\nFile: {file_path}\nDescription: {description}\nCode:\n```\n{code_snippet}\n```\n\n"

    prompt = f"""Given the following list of code issues, provide a detailed analysis and suggestion for each.
{issue_list_str}
For each issue, please provide a "description", "severity" (high, medium, or low), and a "suggested_improvement".
Respond with a single JSON object containing a key "suggestions" which is a list of JSON objects, one for each issue. For example:
{{
  "suggestions": [
    {{
      "original_issue_index": 0,
      "description": "...",
      "severity": "...",
      "suggested_improvement": "..."
    }},
    ...
  ]
}}
"""

    try:
        logger.info(f"Sending batch of {len(issues)} issues to {model_name}.")
        response = await client.generate(model=model_name, prompt=prompt, stream=False)
        response_text = ''
        if isinstance(response, dict):
            response_text = response.get('response', '{}')
        else:
            response_text = str(response)
        suggestions: List[Dict[str, Any]] = []
        try:
            loaded = json.loads(response_text)
            if isinstance(loaded, dict):
                raw_suggestions = loaded.get('suggestions', [])
                if isinstance(raw_suggestions, list):
                    suggestions = [s for s in raw_suggestions if isinstance(s, dict)]
            elif isinstance(loaded, list):
                suggestions = [s for s in loaded if isinstance(s, dict)]
        except Exception as e:
            logger.error(f"Failed to parse suggestions JSON: {e}")
        return suggestions
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from Ollama: {e}")
        logger.debug(f"Ollama response text: {response_text}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during batch suggestion: {e}", exc_info=True)
        return []