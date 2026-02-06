#!/usr/bin/env python3
"""
Multi-Provider Backend with Comprehensive Fallback
===================================================

ALWAYS-ON architecture with 4-tier fallback:

Tier 1 - OpenRouter (cloud, paid):
  Claude Sonnet 4 → Kimi K2.5 → GPT-4.1 → Llama 3.3 70B

Tier 2 - Ollama Cloud via Local Daemon (cloud, free):
  gpt-oss:120b → deepseek-v3.1:671b → qwen3-coder:480b

Tier 3 - Ollama Cloud Direct API (cloud, free, no local daemon needed):
  gpt-oss:120b → deepseek-v3.1:671b

Tier 4 - Ollama Local (local, free):
  mistral → qwen2.5:7b → gemma3:4b

Usage:
    from openrouter_backend import get_client, call_claude_async
"""

import os
import asyncio
import httpx
from typing import Optional, List, Tuple

try:
    from openai import AsyncOpenAI
except ImportError:
    print("ERROR: pip install openai")
    raise

# =============================================================================
# MODEL FALLBACK CHAINS
# =============================================================================

# Tier 1: OpenRouter models (requires OPENROUTER_API_KEY)
OPENROUTER_MODELS = [
    "anthropic/claude-sonnet-4",
    "moonshotai/kimi-k2-instruct",
    "openai/gpt-4.1",
    "meta-llama/llama-3.3-70b-instruct",
]

# Tier 2: Ollama Cloud models via local daemon (requires ollama signin)
OLLAMA_CLOUD_MODELS = [
    "gpt-oss:120b-cloud",
    "deepseek-v3.1:671b-cloud",
    "qwen3-coder:480b-cloud",
]

# Tier 3: Ollama Cloud Direct API models (requires OLLAMA_API_KEY)
OLLAMA_DIRECT_MODELS = [
    "gpt-oss:120b",
    "deepseek-v3.1:671b",
]

# Tier 4: Ollama Local models (no auth needed, runs on local GPU/CPU)
OLLAMA_LOCAL_MODELS = [
    "mistral:latest",
    "qwen2.5:7b",
    "gemma3:4b",
]

DEFAULT_MODEL = OPENROUTER_MODELS[0]
OLLAMA_LOCAL_URL = "http://localhost:11434"
OLLAMA_CLOUD_URL = "https://ollama.com"

# =============================================================================
# CLIENTS
# =============================================================================

def get_api_key() -> str:
    """Get OpenRouter API key."""
    key = os.environ.get("OPENROUTER_API_KEY")
    if key:
        return key
    raise RuntimeError("No OPENROUTER_API_KEY found")


def get_ollama_api_key() -> Optional[str]:
    """Get Ollama cloud API key."""
    return os.environ.get("OLLAMA_API_KEY")


def get_client() -> AsyncOpenAI:
    """Get OpenRouter API client (Tier 1)."""
    return AsyncOpenAI(
        api_key=get_api_key(),
        base_url="https://openrouter.ai/api/v1",
        default_headers={
            "HTTP-Referer": "https://github.com/dharmic-godel-claw",
            "X-Title": "DHARMIC_GODEL_CLAW Night Cycle"
        }
    )


# =============================================================================
# OLLAMA CALLS
# =============================================================================

async def call_ollama(
    model: str,
    system: str,
    user: str,
    max_tokens: int = 2048,
    temperature: float = 0.7,
    base_url: str = OLLAMA_LOCAL_URL,
    api_key: Optional[str] = None
) -> str:
    """Call Ollama API (local or cloud)."""
    headers = {}
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    
    async with httpx.AsyncClient(timeout=120.0, headers=headers) as client:
        response = await client.post(
            f"{base_url}/api/chat",
            json={
                "model": model,
                "messages": [
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ],
                "stream": False,
                "options": {
                    "num_predict": max_tokens,
                    "temperature": temperature
                }
            }
        )
        response.raise_for_status()
        return response.json()["message"]["content"]


# =============================================================================
# UNIFIED FALLBACK CALLER
# =============================================================================

async def call_with_full_fallback(
    system: str,
    user: str,
    max_tokens: int = 2048,
    temperature: float = 0.7
) -> Tuple[str, str, str]:
    """
    Call with full 4-tier fallback.
    
    Returns: (response_text, model_used, tier_used)
    """
    errors = []
    
    # Tier 1: OpenRouter
    try:
        client = get_client()
        for model in OPENROUTER_MODELS:
            try:
                response = await client.chat.completions.create(
                    model=model,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    messages=[
                        {"role": "system", "content": system},
                        {"role": "user", "content": user}
                    ]
                )
                return response.choices[0].message.content, model, "openrouter"
            except Exception as e:
                errors.append(f"OpenRouter/{model}: {e}")
                continue
    except Exception as e:
        errors.append(f"OpenRouter init: {e}")
    
    # Tier 2: Ollama Cloud via local daemon
    for model in OLLAMA_CLOUD_MODELS:
        try:
            response = await call_ollama(model, system, user, max_tokens, temperature)
            return response, model, "ollama-cloud-local"
        except Exception as e:
            errors.append(f"Ollama-Cloud-Local/{model}: {e}")
            continue
    
    # Tier 3: Ollama Cloud Direct API
    ollama_key = get_ollama_api_key()
    if ollama_key:
        for model in OLLAMA_DIRECT_MODELS:
            try:
                response = await call_ollama(
                    model, system, user, max_tokens, temperature,
                    base_url=OLLAMA_CLOUD_URL, api_key=ollama_key
                )
                return response, model, "ollama-cloud-direct"
            except Exception as e:
                errors.append(f"Ollama-Cloud-Direct/{model}: {e}")
                continue
    else:
        errors.append("Ollama-Cloud-Direct: No OLLAMA_API_KEY")
    
    # Tier 4: Ollama Local
    for model in OLLAMA_LOCAL_MODELS:
        try:
            response = await call_ollama(model, system, user, max_tokens, temperature)
            return response, model, "ollama-local"
        except Exception as e:
            errors.append(f"Ollama-Local/{model}: {e}")
            continue
    
    # All tiers exhausted
    raise RuntimeError("All models failed:\n" + "\n".join(errors))


async def call_with_fallback(
    client: AsyncOpenAI,
    system: str,
    user: str,
    max_tokens: int = 2048,
    models: List[str] = None,
    temperature: float = 0.7
) -> Tuple[str, str]:
    """
    OpenRouter-only fallback (backward compatible).
    
    Returns: (response_text, model_used)
    """
    models = models or OPENROUTER_MODELS
    last_error = None
    
    for model in models:
        try:
            response = await client.chat.completions.create(
                model=model,
                max_tokens=max_tokens,
                temperature=temperature,
                messages=[
                    {"role": "system", "content": system},
                    {"role": "user", "content": user}
                ]
            )
            return response.choices[0].message.content, model
        except Exception as e:
            last_error = e
            print(f"  Model {model} failed: {e}")
            continue
    
    # Try full fallback as last resort
    print("  OpenRouter exhausted, trying full fallback...")
    try:
        response, model, tier = await call_with_full_fallback(
            system, user, max_tokens, temperature
        )
        return response, f"{tier}/{model}"
    except Exception as e:
        raise RuntimeError(f"All fallbacks failed. Last: {e}")


async def call_claude_async(
    client: AsyncOpenAI,
    system: str,
    user: str,
    max_tokens: int = 2048,
    model: str = DEFAULT_MODEL,
    temperature: float = 0.7
) -> str:
    """
    Drop-in replacement with automatic multi-tier fallback.
    """
    # Build fallback chain starting with requested model
    models = [model] if model not in OPENROUTER_MODELS else []
    models.extend(OPENROUTER_MODELS)
    
    response, model_used = await call_with_fallback(
        client, system, user, max_tokens, models, temperature
    )
    
    if model_used != model:
        print(f"  [Fallback] Used {model_used} instead of {model}")
    
    return response


# =============================================================================
# TESTING
# =============================================================================

async def test_all_tiers():
    """Test all fallback tiers."""
    print("Testing 4-tier fallback system...\n")
    
    system = "You are a test assistant."
    user = "Say 'hello' and identify yourself in 10 words or less."
    
    # Test full fallback
    try:
        response, model, tier = await call_with_full_fallback(system, user, max_tokens=50)
        print(f"✓ Full fallback: {tier}/{model}")
        print(f"  Response: {response[:100]}")
    except Exception as e:
        print(f"✗ Full fallback failed: {e}")
    
    print("\nTesting individual tiers:\n")
    
    # Test Tier 1
    try:
        client = get_client()
        response = await client.chat.completions.create(
            model=OPENROUTER_MODELS[0],
            max_tokens=50,
            messages=[{"role": "user", "content": user}]
        )
        print(f"✓ Tier 1 (OpenRouter): {OPENROUTER_MODELS[0]}")
    except Exception as e:
        print(f"✗ Tier 1 (OpenRouter): {e}")
    
    # Test Tier 2
    try:
        response = await call_ollama(OLLAMA_CLOUD_MODELS[0], system, user, max_tokens=50)
        print(f"✓ Tier 2 (Ollama Cloud Local): {OLLAMA_CLOUD_MODELS[0]}")
    except Exception as e:
        print(f"✗ Tier 2 (Ollama Cloud Local): {e}")
    
    # Test Tier 3
    ollama_key = get_ollama_api_key()
    if ollama_key:
        try:
            response = await call_ollama(
                OLLAMA_DIRECT_MODELS[0], system, user, max_tokens=50,
                base_url=OLLAMA_CLOUD_URL, api_key=ollama_key
            )
            print(f"✓ Tier 3 (Ollama Cloud Direct): {OLLAMA_DIRECT_MODELS[0]}")
        except Exception as e:
            print(f"✗ Tier 3 (Ollama Cloud Direct): {e}")
    else:
        print("⚠ Tier 3 (Ollama Cloud Direct): No API key")
    
    # Test Tier 4
    try:
        response = await call_ollama(OLLAMA_LOCAL_MODELS[0], system, user, max_tokens=50)
        print(f"✓ Tier 4 (Ollama Local): {OLLAMA_LOCAL_MODELS[0]}")
    except Exception as e:
        print(f"✗ Tier 4 (Ollama Local): {e}")


if __name__ == "__main__":
    asyncio.run(test_all_tiers())


# Compatibility alias
AsyncAnthropic = AsyncOpenAI
