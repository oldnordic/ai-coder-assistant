"""
Ollama client service module.
"""

import logging
import httpx
from typing import List, Dict, Any
import requests
import json
import re
import asyncio

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

def get_ollama_response(prompt: str, model_name: str) -> str:
    """Generate text using Ollama model synchronously.
    
    Args:
        prompt: The prompt to send to the model
        model_name: Name of the Ollama model to use
        
    Returns:
        The generated response text
    """
    try:
        # Use asyncio to run the async generate method
        return asyncio.run(_global_ollama_client.generate(model_name, prompt))
    except Exception as e:
        logger.error(f"Error in get_ollama_response: {e}")
        return f"API_ERROR: {str(e)}"

def get_available_models_sync() -> List[str]:
    """Get list of available Ollama models synchronously."""
    try:
        # Try to connect to Ollama service
        response = requests.get("http://localhost:11434/api/tags")
        if response.status_code != 200:
            logger.error(f"Failed to connect to Ollama service: {response.status_code}")
            return []
            
        # Parse response
        data = response.json()
        if 'models' not in data:
            logger.error("Invalid response format from Ollama service")
            return []
            
        # Extract model names
        models: List[str] = [
            model_data['name'] 
            for model_data in data.get('models', []) 
            if 'name' in model_data
        ]
                
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
    if not response_text or not response_text.strip():
        return ""
    
    # 1. Try to find a JSON block within ```
    match = re.search(r"```(json)?\s*([\s\S]*?)\s*```", response_text, re.DOTALL)
    if match:
        json_text = match.group(2).strip()
        # Try to parse it to validate
        try:
            json.loads(json_text)
            return json_text
        except json.JSONDecodeError:
            pass  # Continue to other extraction methods

    # 2. If no ``` block, find the content between the first { or [ and the last } or ]
    start_chars = ['{', '[']
    end_chars = ['}', ']']
    
    start_index = -1
    for char in start_chars:
        idx = response_text.find(char)
        if idx != -1:
            if start_index == -1 or idx < start_index:
                start_index = idx

    if start_index == -1:
        return "" # No JSON object or array found

    end_index = -1
    for char in end_chars:
        idx = response_text.rfind(char)
        if idx > end_index:
            end_index = idx

    if end_index == -1 or end_index < start_index:
        return "" # No valid end found

    json_text = response_text[start_index : end_index + 1].strip()
    
    # Try to fix common JSON issues
    try:
        # Try to parse as-is first
        json.loads(json_text)
        return json_text
    except json.JSONDecodeError:
        # Try to fix common issues
        fixed_json = _fix_common_json_issues(json_text)
        try:
            json.loads(fixed_json)
            return fixed_json
        except json.JSONDecodeError:
            # If still failing, return empty string
            logger.warning(f"Could not fix JSON issues in response: {json_text[:200]}...")
            return ""
    
    return ""

def _fix_common_json_issues(json_text: str) -> str:
    """Attempt to fix common JSON formatting issues."""
    # Remove trailing commas
    json_text = re.sub(r',(\s*[}\]])', r'\1', json_text)
    
    # Fix unescaped quotes in strings
    json_text = re.sub(r'(?<!\\)"(?=.*":)', r'\\"', json_text)
    
    # Fix missing quotes around keys
    json_text = re.sub(r'(\s*)(\w+)(\s*):', r'\1"\2"\3:', json_text)
    
    # Fix single quotes to double quotes
    json_text = json_text.replace("'", '"')
    
    return json_text

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
    response_text = ""
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
        logger.debug(f"Response text that failed to parse: {response_text[:500]}...")
        
        # Try to extract any useful information from the response
        fallback_results = _extract_fallback_results(response_text)
        if fallback_results:
            logger.info("Using fallback results from malformed JSON response")
            return fallback_results
        
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during code analysis: {e}", exc_info=True)
        return []

def _extract_fallback_results(response_text: str) -> List[Dict[str, Any]]:
    """Extract useful information from malformed JSON responses."""
    results: List[Dict[str, Any]] = []
    
    # Look for patterns that might indicate issues
    lines = response_text.split('\n')
    current_issue: Dict[str, Any] = {}
    
    for line in lines:
        line = line.strip()
        if not line:
            continue
            
        # Look for line numbers
        line_match = re.search(r'line\s+(\d+)', line, re.IGNORECASE)
        if line_match:
            if current_issue:
                results.append(current_issue)
            current_issue = {'line_number': int(line_match.group(1))}
            continue
            
        # Look for severity indicators
        if any(severity in line.lower() for severity in ['error', 'warning', 'info', 'critical']):
            if 'error' in line.lower() or 'critical' in line.lower():
                current_issue['severity'] = 'high'
            elif 'warning' in line.lower():
                current_issue['severity'] = 'medium'
            else:
                current_issue['severity'] = 'low'
            continue
            
        # Look for descriptions
        if len(line) > 20 and not line.startswith('```') and not line.startswith('{') and not line.startswith('['):
            current_issue['description'] = line[:200]  # Limit length
            continue
    
    # Add the last issue if it exists
    if current_issue:
        results.append(current_issue)
    
    return results

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

def get_suggestion_for_issue_sync(client: OllamaClient, issue: Dict[str, Any], model_name: str) -> str:
    """Synchronous wrapper for get_suggestion_for_issue."""
    # This is a simple way to run an async function from sync code.
    # Be mindful of running this in an environment that already has an
    # asyncio event loop (like a running PyQt application's main thread).
    # Since we run this in a ThreadPoolExecutor, it's safe.
    try:
        return asyncio.run(get_suggestion_for_issue(client, issue, model_name))
    except Exception as e:
        logger.error(f"Error in sync wrapper for get_suggestion_for_issue: {e}")
        return "Error generating suggestion."

async def get_suggestions_for_issues_batch(client: OllamaClient, issues: List[Dict[str, Any]], model_name: str) -> List[Dict[str, Any]]:
    """Gets AI-powered suggestions for a batch of code issues."""
    updated_issues = []
    
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
        updated_issues.extend(suggestions)
        return updated_issues
    except json.JSONDecodeError as e:
        logger.error(f"Failed to decode JSON response from Ollama: {e}")
        logger.debug(f"Ollama response text: {response_text}")
        return []
    except Exception as e:
        logger.error(f"An unexpected error occurred during batch suggestion: {e}", exc_info=True)
        return []