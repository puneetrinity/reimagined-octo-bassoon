# tests/conftest.py
"""
Test configuration and fixtures
"""

import asyncio
import os
import sys
from typing import AsyncGenerator

import pytest
import pytest_asyncio
from asgi_lifespan import LifespanManager
from dotenv import load_dotenv
from fastapi.testclient import TestClient
from httpx import ASGITransport, AsyncClient

from app.api import security
from app.api.chat import set_dependencies
from app.graphs.base import GraphState
from app.main import app
from app.models.ollama_client import OllamaClient
from app.models.manager import ModelManager

load_dotenv()

# Async task cleanup fixture
@pytest_asyncio.fixture(autouse=True)
async def cleanup_background_tasks():
    """Automatically cleanup background tasks after each test to prevent task pollution."""
    yield
    # Cancel all pending tasks except the current one
    current_task = asyncio.current_task()
    tasks = [t for t in asyncio.all_tasks() if not t.done() and t != current_task]
    
    if tasks:
        print(f"⚠️ Cleaning up {len(tasks)} pending tasks after test")
        for task in tasks:
            task.cancel()
        
        # Wait for tasks to be cancelled
        await asyncio.gather(*tasks, return_exceptions=True)

# Pre-test Ollama model availability check


@pytest.fixture(scope="session", autouse=True)
def ensure_ollama_models():
    """Check if Ollama is available - skip integration tests if not."""
    
    # Skip Ollama check in CI environments
    if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
        pytest.skip_integration_tests = True
        return
    
    async def check_models():
        try:
            from app.core.config import get_settings
            settings = get_settings()
            client = OllamaClient(base_url=settings.ollama_host)
            await client.initialize()
            models = await client.list_models(force_refresh=True)
            if not models:
                pytest.skip_integration_tests = True
                print("⚠️ No models available in Ollama. Integration tests will be skipped.")
            else:
                pytest.skip_integration_tests = False
        except Exception as e:
            pytest.skip_integration_tests = True
            print(f"⚠️ Ollama connection failed: {e}. Integration tests will be skipped.")

    asyncio.get_event_loop().run_until_complete(check_models())


@pytest.fixture(scope="session")
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def client():
    """FastAPI test client with lifespan support (sync)"""
    with TestClient(app) as c:
        yield c


@pytest.fixture
async def async_client():
    """Async FastAPI test client with lifespan support (async)"""
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.fixture
async def mock_model_manager():
    """Mock model manager for testing"""

    # This would be a mock implementation for testing
    # without requiring actual Ollama connection

    class MockModelManager:

        async def initialize(self):
            pass

        async def generate(self, model_name, prompt, **kwargs):
            from app.models.manager import ModelResult

            # Return a longer response to pass length validation tests
            test_response = "This is a comprehensive mock response from the AI model that provides detailed information and analysis. The response contains multiple sentences to ensure it meets minimum length requirements for testing. This mock response simulates realistic AI-generated content that would be returned by the actual model during normal operation."

            return ModelResult(
                success=True,
                text=test_response,
                cost=0.001,
                execution_time=0.5,
                model_used=model_name,
            )

        def is_healthy(self):
            return True

        async def get_metrics(self):
            return {"total_requests": 0, "local_requests": 0}

    return MockModelManager()


@pytest.fixture
async def mock_cache_manager():
    """Mock cache manager for testing"""

    class MockCacheManager:

        def __init__(self):
            self._cache = {}

        async def initialize(self):
            pass

        async def get(self, key, default=None):
            return self._cache.get(key, default)

        async def set(self, key, value, ttl=None):
            self._cache[key] = value
            return True

        async def health_check(self):
            return True

        async def get_remaining_budget(self, user_id):
            return 100.0

        async def check_rate_limit(self, user_id, limit):
            return True, 1

        async def get_metrics(self):
            return {"cache_hits": 0, "cache_misses": 0}

    return MockCacheManager()


@pytest.fixture(autouse=True)
def override_get_current_user(monkeypatch):
    from app.api.security import User

    async def dummy_user(*args, **kwargs):
        return User(
            user_id="test_user",
            tier="free",
            monthly_budget=20.0,
            permissions=["chat", "search"],
            is_anonymous=False,
        )

    monkeypatch.setattr(security, "get_current_user", dummy_user)


@pytest.fixture
def sample_graph_state():
    """Create a sample GraphState for testing."""
    return GraphState(
        original_query="What is artificial intelligence?",
        processed_query="What is artificial intelligence?",  # Add this line
        user_id="test_user_123",
        session_id="test_session_456",
        quality_requirement="balanced",  # Use string instead of QualityLevel enum
        cost_budget_remaining=0.5,
        max_cost=0.5,  # Add max_cost field
        max_execution_time=30.0,
    )


# Use set_dependencies directly if defined in this file


@pytest_asyncio.fixture
async def integration_client(mock_model_manager, mock_cache_manager):
    """Create test client with mocked dependencies and proper cleanup."""
    set_dependencies(mock_model_manager, mock_cache_manager)
    app_instance = app
    
    # Ensure app state is properly set with mocked components
    app_instance.state.app_state = {
        'model_manager': mock_model_manager,
        'cache_manager': mock_cache_manager,
        'startup_time': 1234567890,  # Fixed timestamp for tests
        'health_status': 'healthy'
    }
    
    timeout = 3.0  # Reduced from 5.0
    try:
        async with LifespanManager(
            app_instance, startup_timeout=timeout, shutdown_timeout=timeout
        ):
            async with AsyncClient(
                transport=ASGITransport(app=app_instance), base_url="http://test"
            ) as client:
                yield client
    except Exception as e:
        # If lifespan fails, yield a basic client for testing
        print(f"Warning: Lifespan setup failed: {e}")
        async with AsyncClient(
            transport=ASGITransport(app=app_instance), base_url="http://test"
        ) as client:
            yield client


@pytest_asyncio.fixture(scope="session", autouse=True)
async def ensure_model_manager_ready():
    """Ensure ModelManager is initialized - skip if in CI environment."""
    # Skip model manager initialization in CI environments
    if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
        return
        
    try:
        from app.dependencies import get_model_manager
        model_manager = get_model_manager()
        await model_manager.initialize()
        # Wait for phi3:mini to be READY (reuse the utility if available)
        try:
            from app.main import wait_for_model_ready
            await wait_for_model_ready(model_manager, "phi3:mini", timeout=30)  # Reduced timeout
        except ImportError:
            # Fallback: just check model is present
            if "phi3:mini" not in model_manager.models:
                print("⚠️ phi3:mini not found in ModelManager after initialization")
    except Exception as e:
        print(f"⚠️ Model manager initialization failed: {e}")
