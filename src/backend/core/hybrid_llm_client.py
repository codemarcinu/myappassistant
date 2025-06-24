import asyncio
import json
import logging
import os
import re
import time
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, AsyncGenerator, Dict, List, Optional, Tuple, Union

from pydantic import BaseModel, ConfigDict

from backend.core.language_detector import language_detector
from backend.core.llm_client import LLMCache, llm_client
from backend.core.model_selector import ModelTask, model_selector

logger = logging.getLogger(__name__)


class ModelComplexity(str, Enum):
    """Complexity levels for model selection"""

    SIMPLE = "simple"  # For simple queries, greetings
    STANDARD = "standard"  # For most conversational queries
    COMPLEX = "complex"  # For reasoning, coding, creative tasks
    CRITICAL = "critical"  # For safety-critical operations


class ModelConfig(BaseModel):
    """Configuration for a specific LLM model"""

    model_config = ConfigDict()
    name: str
    complexity_levels: List[ModelComplexity]
    max_tokens: int
    cost_per_token: float = 0.0  # Cost per 1000 tokens
    priority: int = 1  # Lower number means higher priority
    concurrency_limit: int = 10  # Max concurrent requests
    is_enabled: bool = True
    supports_streaming: bool = True
    supports_embedding: bool = False
    description: Optional[str] = None


class ModelUsageStats(BaseModel):
    """Usage statistics for a model"""

    total_requests: int = 0
    total_tokens: int = 0
    successful_requests: int = 0
    failed_requests: int = 0
    average_latency: float = 0.0
    last_error: Optional[str] = None
    last_used: datetime = datetime.now()


class ModelSelectionMetrics(BaseModel):
    """Metrics used for model selection decisions"""

    query_length: int
    complexity_score: float
    keyword_score: float
    priority_features: List[str]
    selected_model: str
    complexity_level: ModelComplexity
    selection_reason: str
    language: Optional[str] = None


class HybridLLMClient:
    """
    Enhanced LLM client with hybrid model selection, resource management,
    and automatic fallback.
    """

    fallback_model = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
    gemma_model = "gemma3:12b"  # Nowy model Gemma 3
    use_perplexity_fallback = True
    perplexity_client = None  # do mockowania w testach

    def __init__(self) -> None:
        """Initialize hybrid LLM client"""
        self.base_client = llm_client
        self.model_configs: Dict[str, ModelConfig] = self._init_model_configs()
        self.model_stats: Dict[str, ModelUsageStats] = {
            name: ModelUsageStats() for name in self.model_configs.keys()
        }

        # Create semaphores for each model
        self.semaphores: Dict[str, asyncio.Semaphore] = {
            name: asyncio.Semaphore(config.concurrency_limit)
            for name, config in self.model_configs.items()
        }

        # Create caches for each model
        self.caches: Dict[str, LLMCache] = {
            name: LLMCache(max_size=1000, ttl=3600)  # 1 hour TTL
            for name in self.model_configs.keys()
        }

        # For metrics collection
        self.selection_metrics: List[ModelSelectionMetrics] = []
        self.last_cleanup = datetime.now()

        # Inicjalizacja model_selector
        self.model_selector = model_selector
        logger.info("HybridLLMClient initialized with ModelSelector")

    @property
    def default_model(self) -> str:
        """Get the default model from config file or fallback to hardcoded value"""
        try:
            # Path to the LLM settings file
            llm_settings_path = os.path.join(
                os.path.dirname(os.path.dirname(os.path.dirname(__file__))),
                "..",
                "data",
                "config",
                "llm_settings.json",
            )

            if os.path.exists(llm_settings_path):
                with open(llm_settings_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    selected_model = data.get("selected_model", "")
                    if selected_model and selected_model in self.model_configs:
                        logger.info(
                            f"Using selected model from config: {selected_model}"
                        )
                        return selected_model

            # Fallback to hardcoded default
            fallback_default = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
            logger.info(
                f"No valid selected model in config, using fallback: {fallback_default}"
            )
            return fallback_default

        except Exception as e:
            logger.warning(f"Error reading selected model from config: {e}")
            fallback_default = "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0"
            logger.info(f"Using fallback default model: {fallback_default}")
            return fallback_default

    def _init_model_configs(self) -> Dict[str, ModelConfig]:
        """Initialize model configs with their capabilities"""
        return {
            "SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0": ModelConfig(
                name="SpeakLeash/bielik-4.5b-v3.0-instruct:Q8_0",
                complexity_levels=[
                    ModelComplexity.SIMPLE,
                    ModelComplexity.STANDARD,
                    ModelComplexity.COMPLEX,
                    ModelComplexity.CRITICAL,
                ],
                max_tokens=32768,
                cost_per_token=0.10,
                priority=1,  # Najwyższy priorytet - nowy domyślny model
                concurrency_limit=3,
                supports_embedding=True,
                description="Polish language specialized model v3 - primary model",
            ),
            "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M": ModelConfig(
                name="SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M",
                complexity_levels=[
                    ModelComplexity.SIMPLE,
                    ModelComplexity.STANDARD,
                    ModelComplexity.COMPLEX,
                    ModelComplexity.CRITICAL,
                ],
                max_tokens=32768,
                cost_per_token=0.15,
                priority=2,  # Obniżony priorytet - model zapasowy
                concurrency_limit=2,
                supports_embedding=True,
                description="Polish language specialized model - fallback model",
            ),
            "nomic-embed-text": ModelConfig(
                name="nomic-embed-text",
                complexity_levels=[ModelComplexity.SIMPLE],
                max_tokens=8192,
                cost_per_token=0.0,
                priority=4,
                concurrency_limit=10,
                supports_embedding=True,
                supports_streaming=False,
                description="Embedding model",
            ),
            "gemma3:12b": ModelConfig(
                name="gemma3:12b",
                complexity_levels=[
                    ModelComplexity.SIMPLE,
                    ModelComplexity.STANDARD,
                    ModelComplexity.COMPLEX,
                    ModelComplexity.CRITICAL,  # Potrafimy obsłużyć operacje krytyczne
                ],
                max_tokens=8192,  # Zwiększony kontekst
                cost_per_token=0.02,
                priority=1,  # Wysoki priorytet - domyślny dla międzynarodowych użytkowników
                concurrency_limit=5,  # Ograniczona liczba równoczesnych zapytań ze względu na większe wymagania
                supports_embedding=True,
                supports_streaming=True,
                description="State-of-the-art model with multimodal capabilities",
            ),
        }

    async def _get_complexity_level(
        self, messages: List[Dict[str, str]], system_prompt: Optional[str] = None
    ) -> Tuple[ModelComplexity, float, List[str]]:
        """
        Determine complexity of the query for appropriate model selection.
        Returns: (complexity_level, complexity_score, priority_features)
        """
        query = next(
            (msg.get("content", "") for msg in messages if msg.get("role") == "user"),
            "",
        )

        # Wykrywanie języka dla wyboru modelu
        detected_language = "en"
        if query:
            detected_language, _ = language_detector.detect_language(query)
            logger.info(
                f"Detected language: {detected_language} for query: {query[:50]}..."
            )

        # Initialize score and features
        complexity_score = 0.0
        priority_features = []

        # 1. Length-based complexity
        query_length = len(query)
        if query_length < 50:
            complexity_score += 0.2
        elif query_length < 200:
            complexity_score += 0.5
            priority_features.append("medium_length")
        else:
            complexity_score += 0.8
            priority_features.append("long_query")

        # 2. Keyword-based complexity
        complex_keywords = [
            "wyjaśnij",
            "porównaj",
            "przeanalizuj",
            "uzasadnij",
            "zaprojektuj",
            "utwórz",
            "zaimplementuj",
            "kod",
            "program",
            "algorytm",
            "dlaczego",
            "jakie są przyczyny",
            "co by się stało gdyby",
        ]

        critical_keywords = [
            "pilne",
            "krytyczne",
            "ważne",
            "pomoc medyczna",
            "zagrożenie",
            "alert",
            "przeprowadź analizę",
            "złożony problem",
            "optymalizacja",
            "zrównoleglenie",
        ]

        keyword_score = 0.0

        for keyword in complex_keywords:
            if keyword.lower() in query.lower():
                keyword_score += 0.2
                priority_features.append(f"complex_term:{keyword}")

        for keyword in critical_keywords:
            if keyword.lower() in query.lower():
                keyword_score += 0.4
                priority_features.append(f"critical_term:{keyword}")

        # Cap keyword score
        keyword_score = min(1.0, keyword_score)
        complexity_score += keyword_score

        # 3. Pattern-based complexity
        if re.search(r"[\[\]\(\)\{\}]", query):  # Code-like characters
            complexity_score += 0.3
            priority_features.append("code_syntax")

        if query.count("\n") > 3:  # Multi-line text often indicates complex request
            complexity_score += 0.3
            priority_features.append("multi_line")

        if re.search(
            r"\d+[\.,]\d+", query
        ):  # Numbers with decimals often in technical content
            complexity_score += 0.2
            priority_features.append("technical_numbers")

        # 4. System prompt complexity (if provided)
        if system_prompt:
            if len(system_prompt) > 200:
                complexity_score += 0.3
                priority_features.append("complex_system_prompt")

        # 5. History complexity (not implemented yet - would need full conversation history)

        # Normalize final score (0.0 - 1.0)
        normalized_score = min(1.0, complexity_score / 3.0)

        # Map score to complexity level
        if normalized_score < 0.3:
            complexity_level = ModelComplexity.SIMPLE
        elif normalized_score < 0.6:
            complexity_level = ModelComplexity.STANDARD
        elif normalized_score < 0.85:
            complexity_level = ModelComplexity.COMPLEX
        else:
            complexity_level = ModelComplexity.CRITICAL

        # Add language as a priority feature
        priority_features.append(f"language_{detected_language}")

        return complexity_level, normalized_score, priority_features

    def _select_model(
        self,
        complexity_level: ModelComplexity,
        complexity_score: float,
        priority_features: List[str],
    ) -> Tuple[str, str]:
        """
        Select appropriate model based on complexity level, language, and available resources
        Returns: (model_name, selection_reason)
        """
        # Get query from priority features
        query = ""
        for feature in priority_features:
            if feature.startswith("query_"):
                query = feature[6:]
                break

        # Map complexity to ModelTask
        task = ModelTask.TEXT_ONLY
        if complexity_level == ModelComplexity.COMPLEX:
            task = ModelTask.CREATIVE
        elif complexity_level == ModelComplexity.CRITICAL:
            task = ModelTask.STRUCTURED_OUTPUT

        # Check for available models
        available_models = [
            name
            for name, config in self.model_configs.items()
            if config.is_enabled and self.semaphores[name]._value > 0
        ]

        if not available_models:
            # Jeśli wszystkie modele zajęte, używamy domyślnego
            available_models = [
                name for name, config in self.model_configs.items() if config.is_enabled
            ]
            if not available_models:
                logger.warning("No models available, falling back to default")
                return self.default_model, "No models available"

        # Użyj nowego selektora modeli
        best_model = model_selector.select_model(
            query=query,
            task=task,
            complexity=complexity_score,
            contains_images=False,  # Na razie obsługa obrazów nie jest zaimplementowana
            available_models=available_models,
        )

        reason = f"Selected {best_model} using ModelSelector (task: {task}, complexity: {complexity_score:.2f})"
        logger.info(reason)
        return best_model, reason

    async def chat(
        self,
        messages: List[Dict[str, str]],
        model: Optional[str] = None,
        stream: bool = False,
        system_prompt: Optional[str] = None,
        options: Optional[Dict[str, Any]] = None,
        force_complexity: Optional[ModelComplexity] = None,
        use_bielik: Optional[bool] = None,
        use_perplexity: Optional[bool] = None,
        task: Optional[ModelTask] = None,  # Nowy parametr
        contains_images: bool = False,  # Nowy parametr
        **kwargs,
    ) -> Union[Dict[str, Any], AsyncGenerator[Dict[str, Any], None]]:
        """
        Enhanced chat method with automatic model selection and explicit model toggling
        """
        start_time = time.time()

        # 1. Perplexity override
        if use_perplexity:
            if self.perplexity_client:
                return await self.perplexity_client.chat(
                    messages=messages, stream=stream
                )
            raise NotImplementedError("Perplexity client not configured")

        # 2. Model selection by toggle
        if use_bielik is not None:
            model = self.default_model if use_bielik else self.gemma_model

        # Get the query for model selection
        query = next(
            (msg.get("content", "") for msg in messages if msg.get("role") == "user"),
            "",
        )

        try:
            # Auto-determine model if not explicitly provided
            if not model:
                # Define task if not provided
                if not task:
                    if force_complexity:
                        task = (
                            ModelTask.STRUCTURED_OUTPUT
                            if force_complexity == ModelComplexity.CRITICAL
                            else ModelTask.TEXT_ONLY
                        )
                    else:
                        # Determine basic task based on message content
                        if any("```" in msg.get("content", "") for msg in messages):
                            task = ModelTask.CODE_GENERATION
                        else:
                            task = ModelTask.TEXT_ONLY

                # Get available models
                available_models = [
                    name
                    for name, config in self.model_configs.items()
                    if config.is_enabled
                ]

                # Select model using new selector
                complexity = 0.5
                if force_complexity:
                    complexity = (
                        1.0 if force_complexity == ModelComplexity.CRITICAL else 0.5
                    )

                model = model_selector.select_model(
                    query=query,
                    task=task,
                    complexity=complexity,
                    contains_images=contains_images,
                    available_models=available_models,
                )

                selection_reason = f"Selected {model} using ModelSelector (task: {task}, complexity: {complexity:.2f}, images: {contains_images})"
                logger.info(selection_reason)

                # Record selection metrics
                detected_language, _ = language_detector.detect_language(query)

                self.selection_metrics.append(
                    ModelSelectionMetrics(
                        query_length=len(query),
                        complexity_score=complexity,
                        keyword_score=complexity,  # Simplified
                        priority_features=[
                            f"task_{task}",
                            f"language_{detected_language}",
                            f"images_{contains_images}",
                        ],
                        selected_model=model,
                        complexity_level=(
                            ModelComplexity.COMPLEX
                            if complexity > 0.7
                            else ModelComplexity.STANDARD
                        ),
                        selection_reason=selection_reason,
                        language=detected_language,
                    )
                )
            else:
                # Ensure the model exists in our configs
                if model not in self.model_configs:
                    logger.warning(f"Unknown model: {model}, falling back to default")
                    model = self.default_model

            # Ensure model is not None at this point
            if not model:
                model = self.default_model

            # Check model stats for disabled models
            if not self.model_configs[model].is_enabled:
                fallback_model = self.default_model
                logger.warning(
                    f"Model {model} is disabled, falling back to {fallback_model}"
                )
                model = fallback_model

            # Update usage stats
            model_stats = self.model_stats[model]
            model_stats.total_requests += 1
            model_stats.last_used = datetime.now()

            # If system prompt provided, integrate it into messages
            if system_prompt and not any(
                msg.get("role") == "system" for msg in messages
            ):
                messages = [{"role": "system", "content": system_prompt}] + messages

            # Process with resource limiting
            async with self.semaphores[model]:
                if stream:
                    # For streaming, we need to wrap the generator
                    return self._wrap_streaming_response(model, messages, options)
                else:
                    # For normal requests
                    response = await self.base_client.chat(
                        model=model, messages=messages, stream=False, options=options
                    )

                    # Update success stats
                    if response and not isinstance(response, Exception):
                        model_stats.successful_requests += 1
                        # Estimate tokens (rough approximation)
                        if "message" in response and "content" in response["message"]:
                            tokens = len(response["message"]["content"]) // 4
                            model_stats.total_tokens += tokens
                    else:
                        model_stats.failed_requests += 1
                        if isinstance(response, Exception):
                            model_stats.last_error = str(response)

                    # Update latency
                    latency = time.time() - start_time
                    model_stats.average_latency = (
                        (
                            model_stats.average_latency
                            * (model_stats.successful_requests - 1)
                            + latency
                        )
                        / model_stats.successful_requests
                        if model_stats.successful_requests > 0
                        else latency
                    )

                    return response

        except Exception as error_msg:
            logger.error(f"Error in hybrid chat: {str(error_msg)}")

            if model and model in self.model_stats:
                self.model_stats[model].failed_requests += 1
                self.model_stats[model].last_error = str(error_msg)

            # Return error response in expected format
            error_message = f"Error processing request: {str(error_msg)}"
            return {
                "message": {"content": error_message},
                "response": error_message,
                "error_type": type(error_msg).__name__,
                "timestamp": datetime.now().isoformat(),
            }

    async def _wrap_streaming_response(
        self,
        model: str,
        messages: List[Dict[str, str]],
        options: Optional[Dict[str, Any]] = None,
    ) -> AsyncGenerator[Dict[str, Any], None]:
        """Wrap streaming response with stats tracking"""
        start_time = time.time()
        chunks_count = 0
        total_length = 0

        try:
            # Get streaming response from base client
            stream = await self.base_client.chat(
                model=model, messages=messages, stream=True, options=options
            )

            # Process each chunk
            async for chunk in stream:
                chunks_count += 1
                if (
                    isinstance(chunk, dict)
                    and "message" in chunk
                    and "content" in chunk["message"]
                ):
                    total_length += len(chunk["message"]["content"])
                yield chunk

            # Update success stats
            self.model_stats[model].successful_requests += 1
            # Estimate tokens (rough approximation)
            tokens = total_length // 4
            self.model_stats[model].total_tokens += tokens

            # Update latency
            latency = time.time() - start_time
            model_stats = self.model_stats[model]
            model_stats.average_latency = (
                (
                    model_stats.average_latency * (model_stats.successful_requests - 1)
                    + latency
                )
                / model_stats.successful_requests
                if model_stats.successful_requests > 0
                else latency
            )

        except Exception as error_msg:
            logger.error(f"Error in streaming response: {str(error_msg)}")

            if model and model in self.model_stats:
                self.model_stats[model].failed_requests += 1
                self.model_stats[model].last_error = str(error_msg)

            # Yield an error response that matches the expected format
            error_message = f"Error in streaming response: {str(error_msg)}"
            yield {
                "message": {"content": error_message},
                "text": error_message,
                "error_type": type(error_msg).__name__,
                "timestamp": datetime.now().isoformat(),
            }

    async def embed(self, text: str, model: Optional[str] = None) -> List[float]:
        """Get embeddings with automatic model selection"""
        if not model:
            # Use Bielik as default embedding model
            embedding_models = [
                name
                for name, config in self.model_configs.items()
                if config.is_enabled and config.supports_embedding
            ]

            if embedding_models:
                # Prefer Bielik for embeddings
                if "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M" in embedding_models:
                    model = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"
                else:
                    model = embedding_models[0]
            else:
                # Default to Bielik
                model = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"

        # Ensure the model exists
        if model not in self.model_configs:
            logger.warning(f"Unknown embedding model: {model}, falling back to Bielik")
            model = "SpeakLeash/bielik-11b-v2.3-instruct:Q5_K_M"

        # Update usage stats
        self.model_stats[model].total_requests += 1
        self.model_stats[model].last_used = datetime.now()

        try:
            # Use semaphore for resource control
            async with self.semaphores[model]:
                embeddings = await self.base_client.embed(model=model, text=text)

                # Update success stats
                self.model_stats[model].successful_requests += 1

                return embeddings
        except Exception as e:
            logger.error(f"Error generating embeddings: {str(e)}")
            self.model_stats[model].failed_requests += 1
            self.model_stats[model].last_error = str(e)
            return []

    def get_models_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all models"""
        status = {}

        for name, config in self.model_configs.items():
            stats = self.model_stats[name]
            semaphore = self.semaphores[name]

            status[name] = {
                "enabled": config.is_enabled,
                "available_slots": semaphore._value,
                "max_concurrency": config.concurrency_limit,
                "total_requests": stats.total_requests,
                "success_rate": (
                    stats.successful_requests / stats.total_requests
                    if stats.total_requests > 0
                    else 1.0
                ),
                "average_latency": stats.average_latency,
                "last_used": stats.last_used.isoformat(),
                "complexity_levels": [
                    level.value for level in config.complexity_levels
                ],
            }

        return status

    def maintenance(self) -> Dict[str, Any]:
        """Perform maintenance tasks and return stats"""
        # Cleanup old metrics
        now = datetime.now()
        if now - self.last_cleanup > timedelta(hours=1):
            # Keep only the last 100 metrics
            if len(self.selection_metrics) > 100:
                self.selection_metrics = self.selection_metrics[-100:]
            self.last_cleanup = now

        # Collect stats
        return {
            "models": self.get_models_status(),
            "total_requests": sum(
                stats.total_requests for stats in self.model_stats.values()
            ),
            "total_tokens": sum(
                stats.total_tokens for stats in self.model_stats.values()
            ),
            "metrics_collected": len(self.selection_metrics),
        }

    async def with_retry_fallback(
        self,
        messages: List[Dict[str, str]],
        primary_model: Optional[str] = None,
        fallback_model: Optional[str] = None,
        max_retries: int = 2,
        stream: bool = False,
    ) -> Any:
        """Try with primary model, falling back to simpler model if necessary"""

        # Get the query for model selection
        query = next(
            (msg.get("content", "") for msg in messages if msg.get("role") == "user"),
            "",
        )

        # Determine primary model if none provided
        if not primary_model:
            # Use model selector to pick the best model
            task = ModelTask.TEXT_ONLY
            if any("```" in msg.get("content", "") for msg in messages):
                task = ModelTask.CODE_GENERATION

            available_models = [
                name for name, config in self.model_configs.items() if config.is_enabled
            ]

            primary_model = model_selector.select_model(
                query=query,
                task=task,
                complexity=0.5,
                contains_images=False,
                available_models=available_models,
            )

            logger.info(f"Selected primary model {primary_model} using ModelSelector")

        # Try primary model
        for attempt in range(max_retries):
            try:
                return await self.chat(
                    messages=messages, model=primary_model, stream=stream
                )
            except Exception as e:
                logger.warning(
                    f"Error with primary model {primary_model}, attempt {attempt+1}: {str(e)}"
                )
                await asyncio.sleep(0.5 * (2**attempt))

        # If fallback model not specified, choose one with model selector
        if not fallback_model:
            # Wykryj język dla wyboru fallbacku
            detected_language, _ = language_detector.detect_language(query)

            # Dla polskich zapytań preferuj Bielika jako fallback
            if detected_language == "pl":
                fallback_model = self.default_model
                logger.info(
                    f"Using Polish-specific model {fallback_model} as fallback for Polish query"
                )
            else:
                # Wybierz model z wyłączeniem primary_model
                available_models = [
                    name
                    for name, config in self.model_configs.items()
                    if config.is_enabled and name != primary_model
                ]

                if available_models:
                    task = ModelTask.TEXT_ONLY  # Simplified task for fallback
                    fallback_model = model_selector.select_model(
                        query=query,
                        task=task,
                        complexity=0.3,  # Lower complexity for fallback
                        available_models=available_models,
                    )
                else:
                    fallback_model = self.default_model

        # Try fallback model
        logger.warning(
            f"Falling back to {fallback_model} after {max_retries} failed attempts with {primary_model}"
        )

        try:
            return await self.chat(
                messages=messages, model=fallback_model, stream=stream
            )
        except Exception as e:
            logger.error(f"Error with fallback model {fallback_model}: {str(e)}")
            # If all else fails, return error
            return {
                "message": {
                    "content": f"Error processing request with all models: {str(e)}"
                },
                "response": f"Error processing request with all models: {str(e)}",
            }

    def get_available_models(self) -> List[str]:
        return list(self.model_configs.keys()) + ["perplexity"]

    def get_model_info(self, model_name: str) -> Dict[str, Any]:
        if model_name == "perplexity":
            return {"name": "perplexity", "type": "api", "default": False}
        if model_name in self.model_configs:
            config = self.model_configs[model_name]
            return {
                "name": config.name,
                "type": "local",
                "default": model_name == self.default_model,
                "description": config.description,
            }
        raise ValueError(f"Unknown model: {model_name}")


# Initialize hybrid client
hybrid_llm_client = HybridLLMClient()
