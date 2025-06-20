"""
providers.py

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <https://www.gnu.org/licenses/>.

Copyright (C) 2024 AI Coder Assistant Contributors
"""

"""
LLM Provider implementations for different AI services.
Supports OpenAI, Google Gemini, Claude, and Ollama.
"""

import json
import asyncio
import logging
import os
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from pathlib import Path
from typing import Dict, List, Optional, Any
import aiohttp
import google.generativeai as genai
import httpx
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

from src.backend.services.models import (
    ChatCompletionRequest,
    ChatCompletionResponse,
    ModelConfig,
    ProviderConfig,
    ProviderType,
    ModelType,
)

logger = logging.getLogger(__name__)


class BaseProvider(ABC):
    """Base class for all LLM providers."""

    def __init__(self, config: ProviderConfig):
        self.config = config
        self.client = None
        self._setup_client()

    @abstractmethod
    def _setup_client(self):
        """Setup the provider client."""
        pass

    @abstractmethod
    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request."""
        pass

    @abstractmethod
    async def list_models(self) -> List[ModelConfig]:
        """List available models."""
        pass

    @abstractmethod
    def calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate cost for token usage."""
        pass

    async def health_check(self) -> bool:
        """Check if the provider is healthy."""
        try:
            models = await self.list_models()
            return len(models) > 0
        except Exception:
            return False


class OpenAIProvider(BaseProvider):
    """OpenAI provider implementation."""

    def _setup_client(self):
        """Setup OpenAI client."""
        self.client = AsyncOpenAI(
            api_key=self.config.api_key,
            base_url=self.config.base_url,
            organization=self.config.organization,
            timeout=self.config.timeout,
        )

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request to OpenAI."""
        start_time = time.time()

        try:
            # Convert messages to OpenAI format
            messages = []
            for msg in request.messages:
                message_dict = {"role": msg.role, "content": msg.content}
                if msg.name:
                    message_dict["name"] = msg.name
                if msg.function_call:
                    message_dict["function_call"] = msg.function_call
                messages.append(message_dict)

            # Prepare parameters
            params: Dict[str, Any] = {
                "model": request.model,
                "messages": messages,
                "stream": request.stream,
            }

            if request.temperature is not None:
                params["temperature"] = request.temperature
            if request.max_tokens is not None:
                params["max_tokens"] = request.max_tokens
            if request.top_p is not None:
                params["top_p"] = request.top_p
            if request.frequency_penalty is not None:
                params["frequency_penalty"] = request.frequency_penalty
            if request.presence_penalty is not None:
                params["presence_penalty"] = request.presence_penalty
            if request.stop:
                params["stop"] = request.stop
            if request.functions:
                params["functions"] = request.functions
            if request.function_call:
                params["function_call"] = request.function_call

            # Make request
            response = await self.client.chat.completions.create(**params)

            response_time = time.time() - start_time

            # Calculate cost
            usage = response.usage.dict() if response.usage else None
            cost = self.calculate_cost(usage, request.model) if usage else None

            return ChatCompletionResponse(
                id=response.id,
                model=response.model,
                created=datetime.fromtimestamp(response.created),
                choices=[choice.dict() for choice in response.choices],
                usage=usage,
                finish_reason=(
                    response.choices[0].finish_reason if response.choices else None
                ),
                provider=ProviderType.OPENAI,
                response_time=response_time,
                cost=cost,
            )

        except Exception as e:
            raise Exception(f"OpenAI API error: {str(e)}")

    async def list_models(self) -> List[ModelConfig]:
        """List available OpenAI models."""
        try:
            response = await self.client.models.list()
            models = []

            for model in response.data:
                model_config = ModelConfig(
                    name=model.id,
                    provider=ProviderType.OPENAI,
                    model_type=(
                        ModelType.CHAT if "gpt" in model.id else ModelType.COMPLETION
                    ),
                    context_length=self._get_context_length(model.id),
                    cost_per_1k_tokens=self._get_cost_per_1k_tokens(model.id),
                    capabilities=self._get_capabilities(model.id),
                )
                models.append(model_config)

            return models

        except Exception as e:
            raise Exception(f"Error listing OpenAI models: {str(e)}")

    def calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate cost for OpenAI token usage."""
        if not usage:
            return 0.0

        # OpenAI pricing (as of 2024)
        pricing = {
            "gpt-4": {"input": 0.03, "output": 0.06},
            "gpt-4-turbo": {"input": 0.01, "output": 0.03},
            "gpt-3.5-turbo": {"input": 0.0015, "output": 0.002},
            "gpt-3.5-turbo-16k": {"input": 0.003, "output": 0.004},
        }

        model_pricing = pricing.get(model, {"input": 0.002, "output": 0.002})

        input_cost = (usage.get("prompt_tokens", 0) / 1000) * model_pricing["input"]
        output_cost = (usage.get("completion_tokens", 0) / 1000) * model_pricing[
            "output"
        ]

        return input_cost + output_cost

    def _get_context_length(self, model: str) -> Optional[int]:
        """Get context length for model."""
        context_lengths = {
            "gpt-4": 8192,
            "gpt-4-turbo": 128000,
            "gpt-3.5-turbo": 4096,
            "gpt-3.5-turbo-16k": 16384,
        }
        return context_lengths.get(model)

    def _get_cost_per_1k_tokens(self, model: str) -> Optional[float]:
        """Get cost per 1k tokens for model."""
        costs = {
            "gpt-4": 0.03,
            "gpt-4-turbo": 0.01,
            "gpt-3.5-turbo": 0.0015,
            "gpt-3.5-turbo-16k": 0.003,
        }
        return costs.get(model)

    def _get_capabilities(self, model: str) -> List[str]:
        """Get capabilities for model."""
        capabilities = ["chat"]
        if "gpt-4" in model:
            capabilities.extend(["vision", "function_calling"])
        return capabilities


class GoogleGeminiProvider(BaseProvider):
    """Google Gemini provider implementation."""

    def _setup_client(self):
        """Setup Google Gemini client."""
        genai.configure(api_key=self.config.api_key)
        self.client = genai

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request to Google Gemini."""
        start_time = time.time()

        try:
            # Convert messages to Gemini format
            messages = []
            for msg in request.messages:
                if msg.role == "system":
                    # Gemini doesn't support system messages, prepend to first user
                    # message
                    continue
                elif msg.role == "user":
                    messages.append({"role": "user", "parts": [{"text": msg.content}]})
                elif msg.role == "assistant":
                    messages.append({"role": "model", "parts": [{"text": msg.content}]})

            # Get model
            model = self.client.GenerativeModel(request.model)

            # Prepare generation config
            generation_config = {}
            if request.temperature is not None:
                generation_config["temperature"] = request.temperature
            if request.max_tokens is not None:
                generation_config["max_output_tokens"] = request.max_tokens
            if request.top_p is not None:
                generation_config["top_p"] = request.top_p

            # Start chat
            chat = model.start_chat(history=messages[:-1] if len(messages) > 1 else [])

            # Send message
            response = await chat.send_message_async(
                messages[-1]["parts"][0]["text"], generation_config=generation_config
            )

            response_time = time.time() - start_time

            # Create response
            return ChatCompletionResponse(
                id=f"gemini_{int(start_time)}",
                model=request.model,
                created=datetime.fromtimestamp(int(start_time)),
                choices=[
                    {
                        "message": {"role": "assistant", "content": response.text},
                        "finish_reason": "stop",
                    }
                ],
                usage={
                    "prompt_tokens": len(str(messages)),
                    "completion_tokens": len(response.text),
                },
                finish_reason="stop",
                provider=ProviderType.GOOGLE_GEMINI,
                response_time=response_time,
                cost=self.calculate_cost(
                    {
                        "prompt_tokens": len(str(messages)),
                        "completion_tokens": len(response.text),
                    },
                    request.model,
                ),
            )

        except Exception as e:
            raise Exception(f"Google Gemini API error: {str(e)}")

    async def list_models(self) -> List[ModelConfig]:
        """List available Google Gemini models."""
        try:
            models = []

            # Gemini models
            gemini_models = [
                ("gemini-pro", ModelType.CHAT, 32768, 0.0005),
                ("gemini-pro-vision", ModelType.VISION, 32768, 0.0005),
                ("gemini-1.5-pro", ModelType.CHAT, 1000000, 0.0025),
                ("gemini-1.5-flash", ModelType.CHAT, 1000000, 0.00075),
            ]

            for model_name, model_type, context_length, cost in gemini_models:
                model_config = ModelConfig(
                    name=model_name,
                    provider=ProviderType.GOOGLE_GEMINI,
                    model_type=model_type,
                    context_length=context_length,
                    cost_per_1k_tokens=cost,
                    capabilities=(
                        ["chat", "vision"] if "vision" in model_name else ["chat"]
                    ),
                )
                models.append(model_config)

            return models

        except Exception as e:
            raise Exception(f"Error listing Google Gemini models: {str(e)}")

    def calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate cost for Google Gemini token usage."""
        if not usage:
            return 0.0

        # Gemini pricing (as of 2024)
        pricing = {
            "gemini-pro": 0.0005,
            "gemini-pro-vision": 0.0005,
            "gemini-1.5-pro": 0.0025,
            "gemini-1.5-flash": 0.00075,
        }

        cost_per_1k = pricing.get(model, 0.001)
        total_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

        return (total_tokens / 1000) * cost_per_1k


class ClaudeProvider(BaseProvider):
    """Anthropic Claude provider implementation."""

    def _setup_client(self):
        """Setup Claude client."""
        self.client = AsyncAnthropic(
            api_key=self.config.api_key, base_url=self.config.base_url
        )

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request to Claude."""
        start_time = time.time()

        try:
            # Convert messages to Claude format
            messages = []
            for msg in request.messages:
                if msg.role == "system":
                    # Claude uses system message differently
                    continue
                elif msg.role == "user":
                    messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    messages.append({"role": "assistant", "content": msg.content})

            # Prepare parameters
            params = {
                "model": request.model,
                "messages": messages,
                "max_tokens": request.max_tokens or 4096,
            }

            if request.temperature is not None:
                params["temperature"] = request.temperature
            if request.top_p is not None:
                params["top_p"] = request.top_p
            if request.stop:
                params["stop_sequences"] = request.stop

            # Make request
            response = await self.client.messages.create(**params)

            response_time = time.time() - start_time

            # Calculate cost
            usage = {
                "prompt_tokens": response.usage.input_tokens,
                "completion_tokens": response.usage.output_tokens,
            }
            cost = self.calculate_cost(usage, request.model)

            return ChatCompletionResponse(
                id=response.id,
                model=response.model,
                created=datetime.fromtimestamp(int(start_time)),
                choices=[
                    {
                        "message": {
                            "role": "assistant",
                            "content": response.content[0].text,
                        },
                        "finish_reason": response.stop_reason,
                    }
                ],
                usage=usage,
                finish_reason=response.stop_reason,
                provider=ProviderType.CLAUDE,
                response_time=response_time,
                cost=cost,
            )

        except Exception as e:
            raise Exception(f"Claude API error: {str(e)}")

    async def list_models(self) -> List[ModelConfig]:
        """List available Claude models."""
        try:
            models = []

            # Claude models
            claude_models = [
                ("claude-3-opus-20240229", ModelType.CHAT, 200000, 0.015),
                ("claude-3-sonnet-20240229", ModelType.CHAT, 200000, 0.003),
                ("claude-3-haiku-20240307", ModelType.CHAT, 200000, 0.00025),
                ("claude-3.5-sonnet-20241022", ModelType.CHAT, 200000, 0.003),
                ("claude-3.5-haiku-20241022", ModelType.CHAT, 200000, 0.00025),
            ]

            for model_name, model_type, context_length, cost in claude_models:
                model_config = ModelConfig(
                    name=model_name,
                    provider=ProviderType.CLAUDE,
                    model_type=model_type,
                    context_length=context_length,
                    cost_per_1k_tokens=cost,
                    capabilities=["chat", "vision", "function_calling"],
                )
                models.append(model_config)

            return models

        except Exception as e:
            raise Exception(f"Error listing Claude models: {str(e)}")

    def calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate cost for Claude token usage."""
        if not usage:
            return 0.0

        # Claude pricing (as of 2024)
        pricing = {
            "claude-3-opus-20240229": 0.015,
            "claude-3-sonnet-20240229": 0.003,
            "claude-3-haiku-20240307": 0.00025,
            "claude-3.5-sonnet-20241022": 0.003,
            "claude-3.5-haiku-20241022": 0.00025,
        }

        cost_per_1k = pricing.get(model, 0.001)
        total_tokens = usage.get("prompt_tokens", 0) + usage.get("completion_tokens", 0)

        return (total_tokens / 1000) * cost_per_1k


class OllamaProvider(BaseProvider):
    """Ollama provider implementation for local and remote models."""

    def _setup_client(self):
        """Setup Ollama client with support for remote instances."""
        self.base_url = self.config.base_url or "http://localhost:11434"

        # Prepare headers for authentication if needed
        headers = {}
        if self.config.api_key:
            headers["Authorization"] = f"Bearer {self.config.api_key}"

        # Add custom headers from metadata if present
        if self.config.metadata and "headers" in self.config.metadata:
            headers.update(self.config.metadata["headers"])

        # Create client with authentication support
        self.client = httpx.AsyncClient(
            base_url=self.base_url, timeout=self.config.timeout, headers=headers
        )

        # Store additional configuration
        self.verify_ssl = self.config.metadata.get("verify_ssl", True)
        self.custom_endpoints = self.config.metadata.get("custom_endpoints", {})

    async def chat_completion(
        self, request: ChatCompletionRequest
    ) -> ChatCompletionResponse:
        """Send chat completion request to Ollama."""
        start_time = time.time()

        try:
            # Convert messages to Ollama format
            messages = []
            for msg in request.messages:
                if msg.role == "system":
                    messages.append({"role": "system", "content": msg.content})
                elif msg.role == "user":
                    messages.append({"role": "user", "content": msg.content})
                elif msg.role == "assistant":
                    messages.append({"role": "assistant", "content": msg.content})

            # Prepare request
            data = {
                "model": request.model,
                "messages": messages,
                "stream": request.stream,
            }

            if request.temperature is not None:
                data["options"] = {"temperature": request.temperature}
            if request.top_p is not None:
                if "options" not in data:
                    data["options"] = {}
                data["options"]["top_p"] = request.top_p

            # Use custom endpoint if specified
            endpoint = self.custom_endpoints.get("chat", "/api/chat")

            # Make request
            response = await self.client.post(endpoint, json=data)
            response.raise_for_status()
            result = response.json()

            response_time = time.time() - start_time

            return ChatCompletionResponse(
                id=f"ollama_{int(start_time)}",
                model=request.model,
                created=datetime.fromtimestamp(int(start_time)),
                choices=[
                    {
                        "message": {
                            "role": "assistant",
                            "content": result["message"]["content"],
                        },
                        "finish_reason": "stop",
                    }
                ],
                usage=result.get("usage", {}),
                finish_reason="stop",
                provider=ProviderType.OLLAMA,
                response_time=response_time,
                cost=0.0,  # Local models have no cost
            )

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception(f"Ollama authentication failed: {str(e)}")
            elif e.response.status_code == 404:
                raise Exception(f"Ollama model not found: {request.model}")
            else:
                raise Exception(f"Ollama HTTP error {e.response.status_code}: {str(e)}")
        except httpx.ConnectError as e:
            raise Exception(f"Ollama connection failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Ollama API error: {str(e)}")

    async def list_models(self) -> List[ModelConfig]:
        """List available Ollama models."""
        try:
            # Use custom endpoint if specified
            endpoint = self.custom_endpoints.get("list_models", "/api/tags")

            response = await self.client.get(endpoint)
            response.raise_for_status()
            result = response.json()

            models = []
            for model_info in result.get("models", []):
                model_config = ModelConfig(
                    name=model_info["name"],
                    provider=ProviderType.OLLAMA,
                    model_type=ModelType.CHAT,
                    context_length=model_info.get("size", 4096),
                    cost_per_1k_tokens=0.0,  # Local models are free
                    capabilities=["chat"],
                )
                models.append(model_config)

            return models

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception(f"Ollama authentication failed: {str(e)}")
            else:
                raise Exception(f"Ollama HTTP error {e.response.status_code}: {str(e)}")
        except httpx.ConnectError as e:
            raise Exception(f"Ollama connection failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error listing Ollama models: {str(e)}")

    async def health_check(self) -> bool:
        """Check if Ollama instance is healthy."""
        try:
            # Use custom health endpoint if specified
            endpoint = self.custom_endpoints.get("health", "/api/tags")

            response = await self.client.get(endpoint)
            response.raise_for_status()
            return True
        except Exception as e:
            logger.error(f"Ollama health check failed: {e}")
            return False

    async def delete_model(self, model_name: str) -> bool:
        """Delete an Ollama model."""
        try:
            # Use custom endpoint if specified
            endpoint = self.custom_endpoints.get("delete_model", "/api/delete")

            # Make request using the more general `request` method
            response = await self.client.request(
                "DELETE", endpoint, json={"name": model_name}
            )
            response.raise_for_status()
            return True

        except httpx.HTTPStatusError as e:
            if e.response.status_code == 401:
                raise Exception(f"Ollama authentication failed: {str(e)}")
            elif e.response.status_code == 404:
                raise Exception(f"Ollama model not found: {model_name}")
            else:
                raise Exception(f"Ollama HTTP error {e.response.status_code}: {str(e)}")
        except httpx.ConnectError as e:
            raise Exception(f"Ollama connection failed: {str(e)}")
        except Exception as e:
            raise Exception(f"Error deleting Ollama model: {str(e)}")

    def calculate_cost(self, usage: Dict[str, int], model: str) -> float:
        """Calculate cost for Ollama token usage (always 0 for local models)."""
        return 0.0
