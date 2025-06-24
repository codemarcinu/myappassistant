import asyncio
import os
import time
from datetime import datetime
from typing import Any, AsyncGenerator, Dict, List, Optional, Union

import ollama
import requests  # type: ignore
import structlog

logger = structlog.get_logger()

# Configure ollama client to use the correct host
ollama_host = os.getenv("OLLAMA_HOST", "localhost")
ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434")

# Set the host for the ollama library
if ollama_host != "localhost":
    # The ollama library uses OLLAMA_HOST environment variable
    os.environ["OLLAMA_HOST"] = ollama_host
    logger.info(f"Configured ollama client to use host: {ollama_host}")
    logger.info(f"Ollama URL: {ollama_url}")

# Create a configured ollama client instance
ollama_client = ollama.Client(base_url=ollama_url)
logger.info(f"Configured ollama client to use URL: {ollama_url}")


# Test Ollama connection on startup
def test_ollama_connection() -> bool:
    """Test if Ollama server is accessible"""
    try:
        response = requests.get(f"{ollama_url}/api/version", timeout=5)
        if response.status_code == 200:
            logger.info("Ollama server is accessible")
            return True
        else:
            logger.warning(f"Ollama server returned status {response.status_code}")
            return False
    except Exception as e:
        logger.warning(f"Ollama server not accessible: {e}")
        return False


# Test connection on module import
OLLAMA_AVAILABLE = test_ollama_connection()


class LLMCache:
    """Simple cache for LLM responses to avoid duplicate API calls"""

    def __init__(self, max_size: int = 100, ttl: int = 3600) -> None:
        """Initialize LLM cache with max size and TTL (in seconds)"""
        self.cache: Dict[str, Dict[str, Any]] = {}
        self.max_size = max_size
        self.ttl = ttl  # Time-to-live in seconds
        self.last_cleanup = datetime.now()

    def get(self, key: str) -> Optional[Any]:
        """Get value from cache if it exists and is not expired"""
        if key in self.cache:
            entry = self.cache[key]
            if (datetime.now() - entry["timestamp"]).total_seconds() < self.ttl:
                return entry["value"]
            else:
                # Remove expired entry
                del self.cache[key]
        return None

    def set(self, key: str, value: Any) -> None:
        """Set value in cache with current timestamp"""
        # Cleanup if cache is full
        if len(self.cache) >= self.max_size:
            self._cleanup()

        self.cache[key] = {"value": value, "timestamp": datetime.now()}

    def _cleanup(self) -> None:
        """Remove expired entries and trim cache if needed"""
        now = datetime.now()
        # Remove expired entries
        expired_keys = [
            k
            for k, v in self.cache.items()
            if (now - v["timestamp"]).total_seconds() >= self.ttl
        ]
        for k in expired_keys:
            del self.cache[k]

        # If still too large, remove oldest entries
        if len(self.cache) >= self.max_size:
            sorted_keys = sorted(
                self.cache.keys(), key=lambda k: self.cache[k]["timestamp"]
            )
            for k in sorted_keys[
                : len(self.cache) - self.max_size + 10
            ]:  # Remove batch
                del self.cache[k]


class EnhancedLLMClient:
    """Enhanced LLM client with caching and improved error handling"""

    def __init__(self) -> None:
        """Initialize enhanced LLM client"""
        self.cache = LLMCache(max_size=1000, ttl=3600)  # 1 hour cache
        self.embedding_cache = LLMCache(max_size=5000, ttl=86400)  # 24 hour cache
        self.models_info: Dict[str, Any] = {}
        self.last_error: Optional[str] = None
        self.error_count = 0
        self.last_request_time = datetime.now()
        self.connection_retries = 3
        self.retry_delay = 1.0

    async def _check_ollama_availability(self) -> bool:
        """Check if Ollama is available with retries"""
        for attempt in range(self.connection_retries):
            try:
                response = requests.get(f"{ollama_url}/api/version", timeout=5)
                if response.status_code == 200:
                    return True
            except Exception as e:
                logger.debug(
                    f"Ollama availability check attempt {attempt + 1} failed: {e}"
                )
                if attempt < self.connection_retries - 1:
                    await asyncio.sleep(self.retry_delay)
        return False

    async def chat(
        self,
        model: str,
        messages: List[Dict[str, str]],
        stream: bool = False,
        options: Optional[Dict[str, Any]] = None,
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Send chat messages to the LLM

        Args:
            model: Model name
            messages: List of message dicts with role and content
            stream: Whether to stream the response
            options: Additional options to pass to the model

        Returns:
            Response dict or async generator for streaming
        """
        start_time = time.time()
        options = options or {}

        # Check if Ollama is available
        if not await self._check_ollama_availability():
            logger.error(f"Ollama server not available for model {model}")
            fallback_response = {
                "message": {
                    "role": "assistant",
                    "content": "I'm sorry, but the language model service is currently unavailable. Please try again later.",
                },
                "response": "I'm sorry, but the language model service is currently unavailable. Please try again later.",
                "error": "Ollama server not available",
            }
            if stream:

                async def fallback_stream():
                    yield fallback_response

                return fallback_stream()
            else:
                return fallback_response

        # For non-streaming, check cache
        if not stream:
            cache_key = f"{model}_{str(messages)}_{str(options)}"
            cached = self.cache.get(cache_key)
            if cached:
                logger.debug(f"Cache hit for {model}")
                return cached

        try:
            self.last_request_time = datetime.now()

            # Format messages for Ollama
            formatted_messages = []
            for msg in messages:
                if msg["role"] == "system":
                    # Add system message as a special parameter
                    options["system"] = msg["content"]
                else:
                    formatted_messages.append(msg)

            if stream:
                # Return streaming generator
                return self._stream_response(model, formatted_messages, options)
            else:
                # For non-streaming, get complete response
                response = await asyncio.to_thread(
                    ollama_client.chat,
                    model=model,
                    messages=[
                        {"role": m["role"], "content": m["content"]}
                        for m in formatted_messages
                    ],
                    options=options,
                )

                # Format response to standard structure
                result = {
                    "message": {
                        "role": "assistant",
                        "content": response["message"]["content"],
                    },
                    "response": response["message"]["content"],
                }

                # Cache the result
                self.cache.set(cache_key, result)

                logger.debug(
                    f"LLM request to {model} completed in {time.time() - start_time:.2f}s"
                )
                return result

        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            logger.error(f"Error in LLM request to {model}: {str(e)}")

            # Return a fallback response instead of raising an exception
            fallback_response = {
                "message": {
                    "role": "assistant",
                    "content": "I'm sorry, but I'm currently unable to process your request. Please try again later.",
                },
                "response": "I'm sorry, but I'm currently unable to process your request. Please try again later.",
                "error": str(e),
            }

            # Cache the fallback response to avoid repeated failures
            if not stream:
                self.cache.set(cache_key, fallback_response)

            return fallback_response

    async def _stream_response(
        self, model: str, messages: List[Dict[str, str]], options: Dict[str, Any]
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Stream response from LLM"""
        try:
            # Call Ollama's streaming API - no await needed for stream=True
            response_stream = ollama_client.chat(
                model=model,
                messages=[
                    {"role": m["role"], "content": m["content"]} for m in messages
                ],
                options=options,
                stream=True,
            )

            # Process and yield each chunk
            for chunk in response_stream:
                yield {
                    "message": {
                        "role": "assistant",
                        "content": chunk["message"]["content"],
                    },
                    "response": chunk["message"]["content"],
                }

        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            logger.error(f"Error in streaming LLM request to {model}: {str(e)}")

            # Yield a fallback response instead of an error
            fallback_message = "I'm sorry, but I'm currently unable to process your request. Please try again later."
            yield {
                "message": {"role": "assistant", "content": fallback_message},
                "response": fallback_message,
                "error": str(e),
            }

    async def embed(
        self, model: str, text: str, options: Optional[Dict[str, Any]] = None
    ) -> List[float]:
        """Get embeddings from the model"""
        start_time = time.time()
        options = options or {}

        # Check cache first
        cache_key = f"embed_{model}_{text}_{str(options)}"
        cached = self.embedding_cache.get(cache_key)
        if cached:
            logger.debug(f"Embedding cache hit for {model}")
            return cached

        # Check if Ollama is available
        if not await self._check_ollama_availability():
            logger.error(f"Ollama server not available for embedding model {model}")
            # Return zero vector as fallback
            return [0.0] * 384  # Default embedding size

        try:
            self.last_request_time = datetime.now()

            # Get embeddings
            embeddings = await asyncio.to_thread(
                ollama_client.embeddings,
                model=model,
                prompt=text,
                options=options,
            )

            # Cache the result
            self.embedding_cache.set(cache_key, embeddings["embedding"])

            logger.debug(
                f"Embedding request to {model} completed in {time.time() - start_time:.2f}s"
            )
            return embeddings["embedding"]

        except Exception as e:
            self.last_error = str(e)
            self.error_count += 1
            logger.error(f"Error in embedding request to {model}: {str(e)}")

            # Return zero vector as fallback
            return [0.0] * 384

    async def get_models(self) -> List[Dict[str, Any]]:
        """Get list of available models"""
        try:
            if not await self._check_ollama_availability():
                logger.warning(
                    "Ollama server not available, returning empty model list"
                )
                return []

            models = await asyncio.to_thread(ollama_client.list)
            return models.get("models", [])
        except Exception as e:
            logger.error(f"Error getting models: {str(e)}")
            return []

    async def generate_stream(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response from model"""
        async for chunk in self._stream_response(model, messages, options or {}):
            yield chunk

    async def generate_stream_from_prompt(
        self,
        model: str,
        prompt: str,
        system_prompt: str = "",
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Generate streaming response from prompt and system prompt"""
        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        messages.append({"role": "user", "content": prompt})

        async for chunk in self._stream_response(model, messages, options or {}):
            yield chunk

    def get_health_status(self) -> Dict[str, Any]:
        """Get health status of the LLM client"""
        return {
            "ollama_available": OLLAMA_AVAILABLE,
            "last_error": self.last_error,
            "error_count": self.error_count,
            "last_request_time": self.last_request_time.isoformat(),
            "cache_size": len(self.cache.cache),
            "embedding_cache_size": len(self.embedding_cache.cache),
        }


# Global instance
llm_client = EnhancedLLMClient()
LLMClient = EnhancedLLMClient  # Alias for backwards compatibility
