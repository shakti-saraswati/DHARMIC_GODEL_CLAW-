#!/usr/bin/env python3
"""
Multi-Model Comparison Tool

Sends the same prompt to multiple models and compares responses.
Useful for getting diverse perspectives on complex questions.

Usage:
    python3 multi_model_compare.py "Your question here"
    python3 multi_model_compare.py --file prompt.txt
    python3 multi_model_compare.py "question" --models kimi,claude,qwen
"""

import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# =============================================================================
# MODEL CONFIGURATIONS
# =============================================================================

MODELS = {
    # === API Models (via OpenClaw/Clawdbot) ===
    "kimi": {
        "id": "moonshot/kimi-k2.5",
        "name": "Kimi K2.5",
        "strengths": "128k context, fast, good at analysis",
        "cost": "low"
    },
    "claude": {
        "id": "anthropic/claude-sonnet-4-5-20250929",
        "name": "Claude Sonnet 4.5",
        "strengths": "Nuanced reasoning, safety-aware",
        "cost": "medium"
    },
    "gpt4": {
        "id": "openrouter/openai/gpt-4.1",
        "name": "GPT-4.1",
        "strengths": "Broad knowledge, reliable",
        "cost": "medium"
    },

    # === Ollama Cloud Models (no local storage) ===
    "deepseek": {
        "id": "ollama/deepseek-v3.2:cloud",
        "name": "DeepSeek V3.2 (Cloud)",
        "strengths": "Latest DeepSeek, superior reasoning",
        "cost": "free (cloud)"
    },
    "deepseek-v3.1": {
        "id": "ollama/deepseek-v3.1:671b-cloud",
        "name": "DeepSeek V3.1 671B (Cloud)",
        "strengths": "Hybrid thinking/non-thinking modes",
        "cost": "free (cloud)"
    },
    "qwen": {
        "id": "ollama/qwen3-coder:480b-cloud",
        "name": "Qwen3 Coder 480B (Cloud)",
        "strengths": "Code generation, technical depth, 128k context",
        "cost": "free (cloud)"
    },
    "glm": {
        "id": "ollama/glm-4.7:cloud",
        "name": "GLM-4.7 (Cloud)",
        "strengths": "Agentic, multi-step reasoning, 30B-class leader",
        "cost": "free (cloud)"
    },
    "glm-4.6": {
        "id": "ollama/glm-4.6:cloud",
        "name": "GLM-4.6 (Cloud)",
        "strengths": "Autonomous agent tasks, reasoning",
        "cost": "free (cloud)"
    },
    "mistral-large": {
        "id": "ollama/mistral-large-3:675b-cloud",
        "name": "Mistral Large 3 675B (Cloud)",
        "strengths": "Multimodal MoE, broad capabilities",
        "cost": "free (cloud)"
    },
    "gpt-oss": {
        "id": "ollama/gpt-oss:120b-cloud",
        "name": "GPT-OSS 120B (Cloud)",
        "strengths": "OpenAI open-weight, reasoning, agentic",
        "cost": "free (cloud)"
    },

    # === Local Models ===
    "local": {
        "id": "ollama/mistral:latest",
        "name": "Mistral 7B (Local)",
        "strengths": "No API cost, private, fast",
        "cost": "free"
    }
}

DEFAULT_MODELS = ["kimi", "deepseek", "glm"]  # Fast, diverse perspectives

# =============================================================================
# QUERY FUNCTIONS
# =============================================================================

def query_openclaw(prompt: str, model_id: str, timeout: int = 60) -> Dict[str, Any]:
    """Query a model via openclaw CLI."""
    try:
        # Use openclaw if available, fallback to clawdbot
        cli = "openclaw" if subprocess.run(["which", "openclaw"], capture_output=True).returncode == 0 else "clawdbot"

        result = subprocess.run(
            [cli, "agent", "--agent", "main", "--message", prompt, "--local", "--json"],
            capture_output=True,
            text=True,
            timeout=timeout,
            env={**dict(__import__('os').environ)}
        )

        if result.returncode != 0:
            return {"error": f"CLI error: {result.stderr[:200]}"}

        # Parse JSON from output (skip any doctor warnings)
        output = result.stdout
        json_start = output.find('{')
        if json_start == -1:
            return {"error": "No JSON in output"}

        data = json.loads(output[json_start:])
        return {
            "response": data.get("payloads", [{}])[0].get("text", ""),
            "model": data.get("meta", {}).get("agentMeta", {}).get("model", "unknown"),
            "tokens": data.get("meta", {}).get("agentMeta", {}).get("usage", {}),
            "duration_ms": data.get("meta", {}).get("durationMs", 0)
        }

    except subprocess.TimeoutExpired:
        return {"error": f"Timeout after {timeout}s"}
    except json.JSONDecodeError as e:
        return {"error": f"JSON parse error: {e}"}
    except Exception as e:
        return {"error": str(e)}


def query_ollama_direct(prompt: str, model: str, timeout: int = 60) -> Dict[str, Any]:
    """Query Ollama directly for local/cloud models."""
    import urllib.request
    import urllib.error

    try:
        data = json.dumps({
            "model": model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False
        }).encode()

        req = urllib.request.Request(
            "http://localhost:11434/api/chat",
            data=data,
            headers={"Content-Type": "application/json"}
        )

        with urllib.request.urlopen(req, timeout=timeout) as resp:
            result = json.loads(resp.read().decode())
            return {
                "response": result.get("message", {}).get("content", ""),
                "model": model,
                "tokens": {
                    "input": result.get("prompt_eval_count", 0),
                    "output": result.get("eval_count", 0)
                },
                "duration_ms": int(result.get("total_duration", 0) / 1_000_000)
            }

    except urllib.error.URLError as e:
        return {"error": f"Ollama not reachable: {e}"}
    except Exception as e:
        return {"error": str(e)}


def query_model(prompt: str, model_key: str) -> Dict[str, Any]:
    """Query a model by key."""
    if model_key not in MODELS:
        return {"error": f"Unknown model: {model_key}"}

    model_config = MODELS[model_key]
    model_id = model_config["id"]

    # Route based on model type
    if model_id.startswith("ollama/"):
        ollama_model = model_id.replace("ollama/", "")
        return query_ollama_direct(prompt, ollama_model)
    else:
        # Use openclaw/clawdbot for API models
        # First set the model, then query
        cli = "openclaw" if subprocess.run(["which", "openclaw"], capture_output=True).returncode == 0 else "clawdbot"
        subprocess.run([cli, "models", "set", model_id], capture_output=True)
        return query_openclaw(prompt, model_id)


# =============================================================================
# COMPARISON LOGIC
# =============================================================================

def run_comparison(prompt: str, model_keys: List[str]) -> Dict[str, Any]:
    """Run prompt through multiple models and compare."""
    results = {
        "prompt": prompt,
        "timestamp": datetime.utcnow().isoformat(),
        "models_queried": model_keys,
        "responses": {}
    }

    print(f"\n{'='*60}")
    print("MULTI-MODEL COMPARISON")
    print(f"{'='*60}")
    print(f"Prompt: {prompt[:100]}{'...' if len(prompt) > 100 else ''}")
    print(f"Models: {', '.join(model_keys)}")
    print(f"{'='*60}\n")

    for key in model_keys:
        model_config = MODELS.get(key, {})
        print(f"[{key.upper()}] Querying {model_config.get('name', key)}...")

        result = query_model(prompt, key)
        results["responses"][key] = result

        if "error" in result:
            print(f"  ERROR: {result['error']}\n")
        else:
            response_preview = result.get("response", "")[:200]
            print(f"  Response: {response_preview}{'...' if len(result.get('response', '')) > 200 else ''}")
            print(f"  Duration: {result.get('duration_ms', 0)}ms")
            print(f"  Tokens: {result.get('tokens', {})}\n")

    return results


def save_comparison(results: Dict[str, Any], output_dir: Path = None):
    """Save comparison results to file."""
    if output_dir is None:
        output_dir = Path.home() / "DHARMIC_GODEL_CLAW" / "logs" / "comparisons"

    output_dir.mkdir(parents=True, exist_ok=True)

    timestamp = datetime.utcnow().strftime("%Y%m%d_%H%M%S")
    output_file = output_dir / f"comparison_{timestamp}.json"

    with open(output_file, "w") as f:
        json.dump(results, f, indent=2)

    print(f"\nResults saved to: {output_file}")
    return output_file


def print_summary(results: Dict[str, Any]):
    """Print a summary comparison."""
    print(f"\n{'='*60}")
    print("SUMMARY COMPARISON")
    print(f"{'='*60}\n")

    responses = results.get("responses", {})

    for key, result in responses.items():
        model_config = MODELS.get(key, {})
        print(f"### {model_config.get('name', key).upper()} ###")
        print(f"Strengths: {model_config.get('strengths', 'N/A')}")
        print(f"Cost: {model_config.get('cost', 'N/A')}")

        if "error" in result:
            print(f"Status: ERROR - {result['error']}")
        else:
            print(f"Duration: {result.get('duration_ms', 0)}ms")
            print(f"\nResponse:\n{result.get('response', 'No response')[:500]}")

        print(f"\n{'-'*40}\n")


# =============================================================================
# CLI
# =============================================================================

def main():
    parser = argparse.ArgumentParser(
        description="Compare responses from multiple AI models",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
    python3 multi_model_compare.py "What is consciousness?"
    python3 multi_model_compare.py "Explain R_V contraction" --models kimi,claude
    python3 multi_model_compare.py --file question.txt --models kimi,deepseek,qwen

Available models:
    API Models:
      kimi          - Kimi K2.5 (128k context, fast)
      claude        - Claude Sonnet 4.5 (nuanced reasoning)
      gpt4          - GPT-4.1 (broad knowledge)

    Ollama Cloud (free, no local storage):
      deepseek      - DeepSeek V3.2 (superior reasoning)
      deepseek-v3.1 - DeepSeek V3.1 671B (hybrid modes)
      qwen          - Qwen3 Coder 480B (code, 128k context)
      glm           - GLM-4.7 (agentic, 30B-class leader)
      glm-4.6       - GLM-4.6 (autonomous tasks)
      mistral-large - Mistral Large 3 675B (multimodal MoE)
      gpt-oss       - GPT-OSS 120B (OpenAI open-weight)

    Local:
      local         - Mistral 7B (free, private)
        """
    )

    parser.add_argument("prompt", nargs="?", help="The prompt to send")
    parser.add_argument("--file", "-f", help="Read prompt from file")
    parser.add_argument(
        "--models", "-m",
        default=",".join(DEFAULT_MODELS),
        help=f"Comma-separated model keys (default: {','.join(DEFAULT_MODELS)})"
    )
    parser.add_argument("--save", "-s", action="store_true", help="Save results to file")
    parser.add_argument("--list", "-l", action="store_true", help="List available models")

    args = parser.parse_args()

    if args.list:
        print("\nAvailable Models:")
        print("-" * 60)
        for key, config in MODELS.items():
            print(f"  {key:10} - {config['name']}")
            print(f"             {config['strengths']}")
            print(f"             Cost: {config['cost']}\n")
        return

    # Get prompt
    if args.file:
        prompt = Path(args.file).read_text().strip()
    elif args.prompt:
        prompt = args.prompt
    else:
        print("Error: Provide a prompt or use --file")
        parser.print_help()
        sys.exit(1)

    # Parse models
    model_keys = [m.strip() for m in args.models.split(",")]

    # Validate models
    invalid = [m for m in model_keys if m not in MODELS]
    if invalid:
        print(f"Error: Unknown models: {invalid}")
        print(f"Available: {list(MODELS.keys())}")
        sys.exit(1)

    # Run comparison
    results = run_comparison(prompt, model_keys)

    # Print summary
    print_summary(results)

    # Save if requested
    if args.save:
        save_comparison(results)


if __name__ == "__main__":
    main()
