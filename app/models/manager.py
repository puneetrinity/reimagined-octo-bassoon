"""
ModelManager - Intelligent model lifecycle management with cost optimization.
Handles model loading, selection, fallbacks, and performance tracking.
"""
import asyncio
import time
import threading
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Set

from app.core.config import MODEL_ASSIGNMENTS, PRIORITY_TIERS
from app.core.logging import get_correlation_id, get_logger, log_performance
from app.core.memory_manager import A5000MemoryManager
from app.models.ollama_client import (
    ModelResult,
    ModelStatus,
    OllamaClient,
    OllamaException,
)

logger = get_logger("models.manager")


class TaskType(str, Enum):
    """Task types for model selection."""
    SIMPLE_CLASSIFICATION = "simple_classification"
    QA_AND_SUMMARY = "qa_and_summary"
    ANALYTICAL_REASONING = "analytical_reasoning"
    DEEP_RESEARCH = "deep_research"
    CODE_TASKS = "code_tasks"
    MULTILINGUAL = "multilingual"
    CREATIVE_WRITING = "creative_writing"
    CONVERSATION = "conversation"


class QualityLevel(str, Enum):
    """Quality requirements for model selection."""
    MINIMAL = "minimal"      # Fastest response, basic quality
    BALANCED = "balanced"    # Good balance of speed and quality
    HIGH = "high"           # High quality, reasonable speed
    PREMIUM = "premium"     # Best quality, may be slower/expensive


@dataclass
class ModelInfo:
    """Information about a model including performance metrics."""
    name: str
    status: ModelStatus = ModelStatus.UNKNOWN
    last_used: datetime = field(default_factory=datetime.now)
    load_time: float = 0.0
    total_requests: int = 0
    total_cost: float = 0.0
    avg_response_time: float = 0.0
    avg_tokens_per_second: float = 0.0
    memory_usage_mb: float = 0.0
    tier: str = "T2"  # T0=always loaded, T1=keep warm, T2=load on demand
    success_rate: float = 1.0
    confidence_scores: List[float] = field(default_factory=list)

    def update_stats(self, result: ModelResult, confidence: float = 0.0):
        """Update model performance statistics."""
        self.total_requests += 1
        self.last_used = datetime.now()

        if result.success:
            # Update response time (exponential moving average)
            alpha = 0.1
            if self.avg_response_time == 0:
                self.avg_response_time = result.execution_time
            else:
                self.avg_response_time = (alpha * result.execution_time +
                                          (1 - alpha) * self.avg_response_time)

            # Update tokens per second
            if result.tokens_per_second:
                if self.avg_tokens_per_second == 0:
                    self.avg_tokens_per_second = result.tokens_per_second
                else:
                    self.avg_tokens_per_second = (alpha * result.tokens_per_second +
                                                  (1 - alpha) * self.avg_tokens_per_second)

            # Track confidence scores
            if confidence > 0:
                self.confidence_scores.append(confidence)
                # Keep only last 100 scores
                if len(self.confidence_scores) > 100:
                    self.confidence_scores = self.confidence_scores[-100:]

        # Update success rate
        recent_requests = min(self.total_requests, 20)  # Consider last 20 requests
        if hasattr(self, '_recent_successes'):
            self._recent_successes.append(result.success)
            if len(self._recent_successes) > recent_requests:
                self._recent_successes = self._recent_successes[-recent_requests:]
        else:
            self._recent_successes = [result.success]

        self.success_rate = sum(self._recent_successes) / len(self._recent_successes)

    @property
    def avg_confidence(self) -> float:
        """Calculate average confidence score."""
        if not self.confidence_scores:
            return 0.0
        return sum(self.confidence_scores) / len(self.confidence_scores)

    @property
    def performance_score(self) -> float:
        """Calculate overall performance score (0-1)."""
        # Weighted combination of metrics
        speed_score = min((
            1.0,
            10.0 / max(self.avg_response_time,
            0.1)
        ))  # 10s = 0 score
        quality_score = self.avg_confidence
        reliability_score = self.success_rate

        return (0.4 * speed_score + 0.3 * quality_score + 0.3 * reliability_score)


class ModelManager:
    """
    Intelligent model lifecycle manager with optimization and fallback strategies.

    Features:
    - Smart model selection based on task type and quality requirements
    - Automatic model loading and unloading based on usage patterns
    - Performance tracking and optimization recommendations
    - Fallback strategies for model failures
    - Cost optimization and budget management
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self, ollama_host: str = "http://localhost:11434"):
        self.ollama_client = OllamaClient(base_url=ollama_host)

        # Model registry and performance tracking
        self.models: Dict[str, ModelInfo] = {}
        self.loaded_models: Set[str] = set()
        self.metrics = {}
        self._refresh_task = None
        self._shutdown_event = None

        # Use config-based assignments and tiers
        self.model_assignments = MODEL_ASSIGNMENTS.copy()
        self.priority_tiers = PRIORITY_TIERS.copy()
        self.quality_overrides = {}  # No quality overrides by default

        # Add per-model loading locks for thread safety (initialized lazily)
        self._loading_locks = {}
        
        # Initialize A5000 memory manager
        self.memory_manager = A5000MemoryManager()

        logger.info(
            "ModelManager initialized",
            ollama_host=ollama_host,
            model_assignments=len(self.model_assignments),
            correlation_id=get_correlation_id()
        )

    @classmethod
    def get_instance(cls):
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    async def initialize(self) -> None:
        """Initialize the model manager and load priority models."""
        correlation_id = get_correlation_id()

        logger.info("Initializing ModelManager", correlation_id=correlation_id)

        try:
            # Initialize Ollama client
            await self.ollama_client.initialize()

            # Check Ollama health
            if not await self.ollama_client.health_check():
                logger.error("Ollama service is not healthy",
                             correlation_id=correlation_id)
                raise OllamaException("Ollama service is not available")

            # Load available models from Ollama
            await self._discover_models()

            # Preload T0 models (always loaded)
            await self._preload_priority_models()

            logger.info(
                "ModelManager initialization completed",
                total_models=len(self.models),
                loaded_models=len(self.loaded_models),
                correlation_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "ModelManager initialization failed",
                error=str(e),
                correlation_id=correlation_id,
                exc_info=True
            )
            raise

    @log_performance("model_discovery")
    async def _discover_models(self) -> None:
        """Discover available models and initialize model info."""
        correlation_id = get_correlation_id()

        try:
            # Always force refresh to avoid stale cache during test/debug
            available_models = await asyncio.wait_for(
                self.ollama_client.list_models(force_refresh=True),
                timeout=30  # 30 seconds timeout for model discovery
            )
            
            # Validate response structure
            if not isinstance(available_models, list):
                logger.error(
                    "Invalid response from ollama list_models",
                    response_type=type(available_models),
                    correlation_id=correlation_id
                )
                raise OllamaException("Invalid model list response from Ollama")
                
            logger.debug(
                "Ollama returned models (forced refresh)",
                ollama_models=[m.get("name") if isinstance(m, dict) else str(m) for m in available_models],
                correlation_id=correlation_id
            )
            print("[DEBUG] Ollama returned models:", [m.get("name") if isinstance(m, dict) else str(m)
                  for m in available_models])
                  
            for model_data in available_models:
                # Validate model data structure
                if not isinstance(model_data, dict):
                    logger.warning(
                        "Skipping invalid model data",
                        model_data=str(model_data),
                        correlation_id=correlation_id
                    )
                    continue
                    
                model_name = model_data.get("name")
                if not model_name or not isinstance(model_name, str):
                    logger.warning(
                        "Skipping model with invalid name",
                        model_data=model_data,
                        correlation_id=correlation_id
                    )
                    continue

                # Determine tier based on configuration
                tier = "T2"  # Default
                for tier_name, tier_models in self.priority_tiers.items():
                    if any(model_name.startswith(tm.split(':')[0]) for tm in tier_models):
                        tier = tier_name
                        break

                self.models[model_name] = ModelInfo(
                    name=model_name,
                    status=ModelStatus.READY,  # Assume ready if listed
                    tier=tier
                )

            logger.info(
                "Model discovery completed",
                discovered_models=len(self.models),
                model_names=list(self.models.keys()),
                correlation_id=correlation_id
            )
            print("[DEBUG] ModelManager self.models after discovery:",
                  list(self.models.keys()))
            logger.debug(
                "ModelManager self.models after discovery",
                model_keys=list(self.models.keys()),
                correlation_id=correlation_id
            )
            # ADDED: Print and log model status for phi3:mini
            phi3_status = self.models.get("phi3:mini")
            print("[DEBUG] phi3:mini status:", phi3_status)
            logger.debug(
                "phi3:mini status after discovery",
                phi3_status=str(phi3_status),
                correlation_id=correlation_id
            )

        except asyncio.TimeoutError:
            logger.error(
                "Model discovery timeout",
                correlation_id=correlation_id
            )
            raise OllamaException("Model discovery timed out after 30 seconds")
        except Exception as e:
            logger.error(
                "Model discovery failed",
                error=str(e),
                correlation_id=correlation_id,
                exc_info=True
            )
            raise

    async def _preload_priority_models(self) -> None:
        """Preload T0 priority models for instant availability."""
        correlation_id = get_correlation_id()

        t0_models = self.priority_tiers.get("T0", [])

        for model_pattern in t0_models:
            # Find matching models
            matching_models = [
                name for name in self.models.keys()
                if name.startswith(model_pattern.split(':')[0])
            ]

            for model_name in matching_models:
                try:
                    await self._ensure_model_loaded(model_name)
                    logger.info(
                        "Priority model preloaded",
                        model_name=model_name,
                        tier="T0",
                        correlation_id=correlation_id
                    )
                except Exception as e:
                    logger.warning(
                        "Failed to preload priority model",
                        model_name=model_name,
                        error=str(e),
                        correlation_id=correlation_id
                    )

    def select_optimal_model(
        self,
        task_type: TaskType,
        quality_requirement: QualityLevel = QualityLevel.BALANCED,
        context: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Select the optimal model for a given task and quality requirement.

        Args:
            task_type: Type of task to perform
            quality_requirement: Required quality level
            context: Additional context for selection (user tier, budget, etc.)

        Returns:
            str: Selected model name
        """
        correlation_id = get_correlation_id()

        # Ensure enum/string consistency for assignment lookup
        assignment_key = task_type.value if isinstance(task_type, Enum) else str(task_type)
        logger.debug(
            "[select_optimal_model] ENTRY",
            task_type=task_type,
            assignment_key=assignment_key,
            model_assignments=self.model_assignments,
            all_models=list(self.models.keys()),
            correlation_id=correlation_id
        )
        if not self.models:
            logger.critical(
                "[select_optimal_model] Model registry is EMPTY! Failing fast.",
                correlation_id=correlation_id
            )
            raise OllamaException("No models available: Model registry is empty!")

        # Assignment lookup
        base_model = self.model_assignments.get(assignment_key, "llama2:7b")
        logger.debug(
            "[select_optimal_model] After assignment lookup",
            assignment_key=assignment_key,
            base_model=base_model,
            all_models=list(self.models.keys()),
            correlation_id=correlation_id
        )

        # Apply quality overrides
        if quality_requirement in self.quality_overrides:
            quality_overrides = self.quality_overrides[quality_requirement]
            if assignment_key in quality_overrides:
                base_model = quality_overrides[assignment_key]
                logger.debug(
                    "[select_optimal_model] After quality override",
                    assignment_key=assignment_key,
                    base_model=base_model,
                    correlation_id=correlation_id
                )

        # 1. Try exact match first
        exact_matches = [name for name in self.models.keys() if name == base_model]
        logger.debug(
            "[select_optimal_model] Exact match results",
            base_model=base_model,
            exact_matches=exact_matches,
            correlation_id=correlation_id
        )
        if exact_matches:
            selected_model = self._select_best_variant(exact_matches)
            logger.info(
                "[select_optimal_model] Selected exact match",
                selected_model=selected_model,
                correlation_id=correlation_id
            )
            return selected_model

        # 2. Fuzzy match (by prefix, e.g., phi3:mini matches phi3:mini:latest)
        fuzzy_matches = [
            name for name in self.models.keys()
            if name.split(":")[0] == base_model.split(":")[0]
        ]
        logger.debug(
            "[select_optimal_model] Fuzzy match results",
            base_model=base_model,
            fuzzy_matches=fuzzy_matches,
            correlation_id=correlation_id
        )
        if fuzzy_matches:
            selected_model = self._select_best_variant(fuzzy_matches)
            logger.info(
                "[select_optimal_model] Selected fuzzy match",
                selected_model=selected_model,
                correlation_id=correlation_id
            )
            return selected_model

        # Fallback to any available model
        fallback_model = self._select_fallback_model(task_type)
        logger.warning(
            "[select_optimal_model] No match found, using fallback",
            preferred_model=base_model,
            fallback_model=fallback_model,
            task_type=assignment_key,
            correlation_id=correlation_id
        )
        return fallback_model

    def _select_fallback_model(self, task_type: TaskType) -> str:
        """Select a fallback model when preferred model is unavailable."""
        # Fallback hierarchy
        fallback_hierarchy = [
            "llama2:7b", "phi:mini", "mistral:7b"
        ]

        for fallback in fallback_hierarchy:
            available = [name for name in self.models.keys()
                         if name.startswith(fallback.split(':')[0])]
            if available:
                return available[0]

        # Last resort - return first available model
        if self.models:
            return list(self.models.keys())[0]

        raise OllamaException("No models available")

    def _select_best_variant(self, available_models: List[str]) -> str:
        """Select the best performing variant from available models."""
        if len(available_models) == 1:
            return available_models[0]

        # Score models based on performance metrics
        scored_models = []
        for model_name in available_models:
            model_info = self.models.get(model_name)
            if model_info:
                score = model_info.performance_score
                scored_models.append((model_name, score))

        if scored_models:
            # Sort by score (highest first)
            scored_models.sort(key=lambda x: x[1], reverse=True)
            return scored_models[0][0]

        return available_models[0]

    @log_performance("model_generation")
    async def generate(
        self,
        model_name: str,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        fallback: bool = True,
        **kwargs
    ) -> ModelResult:
        """
        Generate text using specified model with automatic fallback.

        Args:
            model_name: Model to use for generation
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            fallback: Enable fallback to alternative models
            **kwargs: Additional generation parameters

        Returns:
            ModelResult: Generation result with metadata
        """
        correlation_id = get_correlation_id()
        print(f"[PRINT][ModelManager] generate called for {model_name} | correlation_id={correlation_id}")
        try:
            print(f"[PRINT][ModelManager] about to ensure model loaded for {model_name}")
            await self._ensure_model_loaded(model_name)
            print(f"[PRINT][ModelManager] model loaded successfully for {model_name}")
            print(f"[PRINT][ModelManager] about to call ollama_client.generate for {model_name}")
            result = await self.ollama_client.generate(
                model_name=model_name,
                prompt=prompt,
                max_tokens=max_tokens,
                temperature=temperature,
                **kwargs
            )
            print(f"[PRINT][ModelManager] ollama_client returned: success={getattr(result, 'success', None)} text={getattr(result, 'text', None)}")
            
            # Update model stats if result is valid
            if isinstance(result, ModelResult) and model_name in self.models:
                self.models[model_name].update_stats(result, confidence=0.8)
            
            # Try fallback if primary failed and fallback enabled
            if not result.success and fallback:
                logger.warning(
                    "Primary model failed, trying fallback",
                    model_name=model_name,
                    error=result.error,
                    correlation_id=correlation_id
                )
                result = await self._try_fallback_generation(
                    model_name, prompt, max_tokens, temperature, **kwargs
                )
            
            return result
            
        except OllamaException as e:
            logger.error(
                "Ollama-specific error in generation",
                model_name=model_name,
                error=str(e),
                correlation_id=correlation_id
            )
            if fallback:
                return await self._try_fallback_generation(
                    model_name, prompt, max_tokens, temperature, **kwargs
                )
            return ModelResult(success=False, error=str(e), model_used=model_name)
            
        except Exception as e:
            logger.error(
                "Unexpected error in generation",
                model_name=model_name,
                error=str(e),
                correlation_id=correlation_id,
                exc_info=True
            )
            print(f"[PRINT][ModelManager] EXCEPTION: {e}")
            
            # Mark model as problematic
            if model_name in self.models:
                self.models[model_name].status = ModelStatus.ERROR
                
            if fallback:
                return await self._try_fallback_generation(
                    model_name, prompt, max_tokens, temperature, **kwargs
                )
            return ModelResult(success=False, error=str(e), model_used=model_name)

    async def _try_fallback_generation(
        self,
        original_model: str,
        prompt: str,
        max_tokens: int = 300,
        temperature: float = 0.7,
        **kwargs
    ) -> ModelResult:
        """
        Try fallback models when primary model fails.

        Args:
            original_model: The model that failed
            prompt: Input prompt
            max_tokens: Maximum tokens to generate
            temperature: Sampling temperature
            **kwargs: Additional generation parameters

        Returns:
            ModelResult: Generation result from fallback model
        """
        correlation_id = get_correlation_id()

        # Get list of fallback models (exclude the failed one)
        fallback_models = [
            name for name in self.models.keys()
            if name != original_model and self.models[name].status == ModelStatus.READY
        ]

        if not fallback_models:
            # Try to use any available model as fallback
            try:
                available_models = await self.ollama_client.list_models()
                fallback_models = [
                    model["name"] for model in available_models
                    if model["name"] != original_model
                ]
            except Exception:
                fallback_models = []

        if not fallback_models:
            return ModelResult(
                success=False,
                model_used=original_model,
                error="No fallback models available"
            )

        # Try fallback models one by one
        for fallback_model in fallback_models[:3]:  # Limit to 3 attempts
            try:
                logger.debug(
                    "Trying fallback model",
                    original_model=original_model,
                    fallback_model=fallback_model,
                    correlation_id=correlation_id
                )
                await self._ensure_model_loaded(fallback_model)
                result = await self.ollama_client.generate(
                    model_name=fallback_model,
                    prompt=prompt,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    **kwargs
                )
                # Only update stats if result is a ModelResult
                if isinstance(result, ModelResult):
                    if result.success:
                        logger.info(
                            "Fallback generation successful",
                            original_model=original_model,
                            fallback_model=fallback_model,
                            correlation_id=correlation_id
                        )
                        if fallback_model in self.models:
                            self.models[fallback_model].update_stats(
                                result, confidence=0.7)
                            result.cost = 0.0
                        return result
                    else:
                        logger.warning(
                            "Fallback model also failed",
                            fallback_model=fallback_model,
                            error=result.error,
                            correlation_id=correlation_id
                        )
                        continue
                else:
                    logger.warning(
                        "Fallback model returned non-ModelResult",
                        fallback_model=fallback_model,
                        result_type=str(type(result)),
                        correlation_id=correlation_id
                    )
                    continue
            except Exception as e:
                logger.warning(
                    "Fallback model exception",
                    fallback_model=fallback_model,
                    error=str(e),
                    correlation_id=correlation_id
                )
                continue
        # All fallbacks failed
        return ModelResult(
            success=False,
            model_used=original_model,
            error=f"All fallback attempts failed. Original model: {original_model}"
        )

    async def _ensure_model_loaded(self, model_name: str, required_models: Optional[List[str]] = None) -> None:
        """Ensure a model is loaded and ready for inference with A5000 memory management."""
        correlation_id = get_correlation_id()

        # Use memory manager for intelligent loading
        success = await self.memory_manager.ensure_model_loaded(model_name, required_models)
        
        if not success:
            raise OllamaException(f"Failed to load model {model_name} due to memory constraints")

        # Check if already loaded in Ollama
        if model_name in self.loaded_models:
            return

        # Use lock to prevent concurrent loading of same model
        if model_name not in self._loading_locks:
            try:
                self._loading_locks[model_name] = asyncio.Lock()
            except RuntimeError:
                # No event loop, will synchronize at task level
                self._loading_locks[model_name] = None

        if self._loading_locks[model_name] is not None:
            async with self._loading_locks[model_name]:
                # Double-check after acquiring lock
                if model_name in self.loaded_models:
                    return
                await self._load_model_impl(model_name, correlation_id)
        else:
            # No async lock available, proceed without lock (startup scenario)
            await self._load_model_impl(model_name, correlation_id)

    async def _load_model_impl(self, model_name: str, correlation_id: str) -> None:
        """Implementation of model loading logic."""
        logger.info(
            "Loading model in Ollama",
            model_name=model_name,
            correlation_id=correlation_id
        )

        start_time = time.time()
        try:
            # Check if model exists in Ollama
            status = await self.ollama_client.check_model_status(model_name)

            if status == ModelStatus.UNKNOWN:
                # Try to pull the model with timeout
                logger.info(
                    "Model not found, attempting to pull",
                    model_name=model_name,
                    correlation_id=correlation_id
                )
                try:
                    # Add timeout to prevent hanging
                    await asyncio.wait_for(
                        self.ollama_client.pull_model(model_name),
                        timeout=300  # 5 minutes max for model pull
                    )
                except asyncio.TimeoutError:
                    logger.error(
                        "Model pull timeout",
                        model_name=model_name,
                        correlation_id=correlation_id
                    )
                    raise OllamaException(f"Model {model_name} pull timed out after 5 minutes")

            # Verify model is ready with timeout
            status = await asyncio.wait_for(
                self.ollama_client.check_model_status(model_name),
                timeout=30  # 30 seconds to check status
            )
            if status != ModelStatus.READY:
                logger.error(
                    "[_ensure_model_loaded] Model failed to load",
                    model_name=model_name,
                    status=status.value if status else "unknown",
                    timestamp=time.time(),
                    correlation_id=correlation_id
                )
                raise OllamaException(f"Model {model_name} failed to load properly (status: {status})")

            # Model successfully loaded
            self.loaded_models.add(model_name)
            load_time = time.time() - start_time

            if model_name in self.models:
                self.models[model_name].load_time = load_time
                self.models[model_name].status = ModelStatus.READY

            logger.info(
                "Model loaded successfully",
                model_name=model_name,
                load_time=round(load_time, 2),
                correlation_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "Model loading failed",
                model_name=model_name,
                error=str(e),
                correlation_id=correlation_id,
                exc_info=True
            )

            # Clean up partial state
            if model_name in self.loaded_models:
                self.loaded_models.discard(model_name)
                
            if model_name in self.models:
                self.models[model_name].status = ModelStatus.ERROR
                
            # Remove from memory manager if it was being loaded
            try:
                await self.memory_manager.unload_model(model_name)
            except Exception as cleanup_error:
                logger.debug(
                    "Error during model cleanup",
                    model_name=model_name,
                    cleanup_error=str(cleanup_error),
                    correlation_id=correlation_id
                )

            raise

    async def preload_models(self, model_names: List[str]) -> Dict[str, bool]:
        """
        Preload multiple models concurrently.

        Args:
            model_names: List of model names to preload

        Returns:
            Dict mapping model names to success status
        """
        correlation_id = get_correlation_id()

        logger.info(
            "Preloading models",
            model_names=model_names,
            correlation_id=correlation_id
        )

        results = {}

        # Load models concurrently
        tasks = []
        for model_name in model_names:
            task = asyncio.create_task(
                self._preload_single_model(model_name),
                name=f"preload_{model_name}"
            )
            tasks.append((model_name, task))

        # Wait for all tasks to complete
        for model_name, task in tasks:
            try:
                await task
                results[model_name] = True
            except Exception as e:
                logger.error(
                    "Model preload failed",
                    model_name=model_name,
                    error=str(e),
                    correlation_id=correlation_id
                )
                results[model_name] = False

        successful_loads = sum(results.values())

        logger.info(
            "Model preloading completed",
            total_models=len(model_names),
            successful_loads=successful_loads,
            failed_loads=len(model_names) - successful_loads,
            correlation_id=correlation_id
        )

        return results

    async def _preload_single_model(self, model_name: str) -> None:
        """Preload a single model with error handling."""
        try:
            await self._ensure_model_loaded(model_name)
        except Exception as e:
            logger.warning(
                "Single model preload failed",
                model_name=model_name,
                error=str(e),
                correlation_id=get_correlation_id()
            )
            raise

    async def preload_recruitment_models(self) -> Dict[str, bool]:
        """Preload models optimized for recruitment workflows"""
        return await self.memory_manager.preload_priority_models()
    
    async def optimize_for_recruitment_batch(self, task_types: List[str]) -> Dict[str, Any]:
        """Optimize model loading for recruitment batch processing"""
        try:
            from app.core.recruitment_router import RecruitmentModelRouter
            
            router = RecruitmentModelRouter()
            optimization = router.optimize_for_batch_processing(task_types)
            
            # Preload the recommended models
            if optimization.get('preload_models'):
                await self.preload_models(optimization['preload_models'])
            
            return optimization
        except ImportError as e:
            logger.warning(
                "RecruitmentModelRouter not available",
                error=str(e),
                correlation_id=get_correlation_id()
            )
            # Fallback: preload common recruitment models
            common_models = ["phi3:mini", "deepseek-llm:7b", "mistral"]
            await self.preload_models(common_models)
            return {
                "preload_models": common_models,
                "optimization_strategy": "fallback",
                "note": "RecruitmentModelRouter unavailable, using default models"
            }
    
    def get_recruitment_memory_stats(self) -> Dict[str, Any]:
        """Get A5000-specific memory statistics"""
        return self.memory_manager.get_memory_stats()

    def get_model_stats(self) -> Dict[str, Any]:
        """Get comprehensive model statistics."""
        base_stats = {
            "total_models": len(self.models),
            "loaded_models": len(self.loaded_models),
            "model_details": {},
            "performance_summary": {
                "avg_response_time": 0.0,
                "avg_success_rate": 0.0,
                "total_requests": 0
            }
        }

        total_response_time = 0.0
        total_success_rate = 0.0
        total_requests = 0

        for model_name, model_info in self.models.items():
            base_stats["model_details"][model_name] = {
                "status": model_info.status.value,
                "tier": model_info.tier,
                "total_requests": model_info.total_requests,
                "avg_response_time": round(model_info.avg_response_time, 3),
                "avg_tokens_per_second": round(
                    model_info.avg_tokens_per_second,
                    2
                ),
                "success_rate": round(model_info.success_rate, 3),
                "avg_confidence": round(model_info.avg_confidence, 3),
                "performance_score": round(model_info.performance_score, 3),
                "last_used": model_info.last_used.isoformat(),
                "is_loaded": model_name in self.loaded_models
            }

            if model_info.total_requests > 0:
                total_response_time += model_info.avg_response_time
                total_success_rate += model_info.success_rate
                total_requests += model_info.total_requests

        # Calculate averages
        if self.models:
            base_stats["performance_summary"]["avg_response_time"] = round(
                total_response_time / len(self.models), 3
            )
            base_stats["performance_summary"]["avg_success_rate"] = round(
                total_success_rate / len(self.models), 3
            )

        base_stats["performance_summary"]["total_requests"] = total_requests

        # Add A5000 memory stats if available
        try:
            memory_stats = self.memory_manager.get_memory_stats()
            base_stats["memory_management"] = memory_stats
        except Exception as e:
            logger.debug(f"Could not get memory stats: {e}")
        
        return base_stats

    def get_model_recommendations(
        self,
        context: Optional[Dict[str,
        Any]] = None
    ) -> Dict[str, Any]:
        """Get model optimization recommendations."""
        recommendations = {
            "performance_optimizations": [],
            "cost_optimizations": [],
            "reliability_improvements": []
        }

        for model_name, model_info in self.models.items():
            # Performance recommendations
            if model_info.avg_response_time > 10.0:
                recommendations["performance_optimizations"].append(
                    f"Model {model_name} has slow response time ({model_info.avg_response_time:.1f}s). "
                    "Consider using a faster model for simple tasks."
                )

            # Reliability recommendations
            if model_info.success_rate < 0.9 and model_info.total_requests > 5:
                recommendations["reliability_improvements"].append(
                    f"Model {model_name} has low success rate ({model_info.success_rate:.1%}). "
                    "Check model health or consider alternative."
                )

            # Cost optimizations (for future API model integration)
            if model_info.total_cost > 0:
                recommendations["cost_optimizations"].append(
                    f"Model {model_name} has incurred costs. Consider local alternatives."
                )

        return recommendations

    async def cleanup(self) -> None:
        """Clean up resources and close connections."""
        correlation_id = get_correlation_id()

        logger.info("Cleaning up ModelManager", correlation_id=correlation_id)

        try:
            await self.ollama_client.close()
            self.loaded_models.clear()
            self._loading_locks.clear()

            logger.info(
                "ModelManager cleanup completed",
                correlation_id=correlation_id
            )

        except Exception as e:
            logger.error(
                "ModelManager cleanup failed",
                error=str(e),
                correlation_id=correlation_id
            )

    async def shutdown(self) -> None:
        """Shutdown the model manager and clean up resources."""
        await self.cleanup()
        logger.info("ModelManager shutdown completed")

    async def start_periodic_refresh(self, interval=300):
        if self._refresh_task:
            return  # Already running
        if self._shutdown_event is None:
            self._shutdown_event = asyncio.Event()
        async def refresh_loop():
            while not self._shutdown_event.is_set():
                try:
                    await self._discover_models()
                except Exception as e:
                    logger.error("Periodic model discovery failed", error=str(e))
                await asyncio.sleep(interval)
        self._refresh_task = asyncio.create_task(refresh_loop())

    def reset(self):
        self.models.clear()
        self.loaded_models.clear()
        self.metrics.clear()
        self._refresh_task = None
        self._shutdown_event = None


# Export main classes and types
__all__ = [
    'ModelManager',
    'ModelInfo',
    'TaskType',
    'QualityLevel'
]
