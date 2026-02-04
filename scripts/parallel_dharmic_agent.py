#!/usr/bin/env python3
"""
Parallel Dharmic Agent runner.

Reads a fixed set of 25 files, builds a grounded prompt, and runs an Agno Agent
with a provider/model selected via environment or CLI.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any


ROOT = Path(__file__).resolve().parents[1]
CORE_DIR = ROOT / "src" / "core"
sys.path.insert(0, str(CORE_DIR))


FILES = [
    "README.md",
    "CLAUDE.md",
    "config/telos.yaml",
    "src/core/dharmic_agent.py",
    "src/core/runtime.py",
    "src/core/dharmic_team.py",
    "src/core/email_interface.py",
    "swarm/orchestrator.py",
    "swarm/config.py",
    "swarm/run_swarm.py",
    "swarm/residual_stream.py",
    "swarm/agents/base_agent.py",
    "swarm/agents/proposer.py",
    "swarm/agents/writer.py",
    "swarm/agents/tester.py",
    "swarm/agents/refiner.py",
    "swarm/agents/evolver.py",
    "swarm/agents/dharmic_gate.py",
    "analysis/openclaw_skills.md",
    "analysis/mcp_integration.md",
    "analysis/security_architecture.md",
    "analysis/agno_memory.md",
    "analysis/README.md",
    "swarm_synthesis/v1.10_grand_synthesis_20260202.md",
    "swarm_synthesis/v1.9_practical_implementation_planner_20260202.md",
]


def read_excerpt(path: Path, limit: int) -> Tuple[str, bool]:
    text = path.read_text()
    if len(text) <= limit:
        return text, False
    return text[:limit], True


def build_prompt(
    excerpts: List[Tuple[str, str, bool]],
    output_format: str,
    allowed_paths: Optional[List[str]] = None,
) -> str:
    file_index = "\n".join(
        f"{i+1}. {rel_path}" for i, (rel_path, _content, _trunc) in enumerate(excerpts)
    )

    excerpt_blocks = []
    for rel_path, content, truncated in excerpts:
        trunc_note = " [TRUNCATED]" if truncated else ""
        excerpt_blocks.append(
            f"--- {rel_path}{trunc_note} ---\n{content}\n"
        )

    if output_format == "json":
        format_block = """Return ONLY valid JSON with this schema:
{
  "ontology": ["bullet (with file path)"],
  "teleology": ["bullet (with file path)"],
  "actions": ["1) action — reason (with file path)"]
}
"""
    else:
        format_block = """Required output format (verbatim headings):

ONTOLOGY (3-5 bullets)
- ...

PURPOSE & TELEOLOGY (3-5 bullets)
- ...

TOP 10 NEXT ACTIONS (numbered 1-10)
1) Action — brief reason (cite file path)
...
"""

    allowed_block = ""
    if allowed_paths:
        allowed_block = (
            "ALLOWED FILE PATHS (use ONLY these exact paths in parentheses):\n"
            + "\n".join(f"- {p}" for p in allowed_paths)
            + "\n\n"
        )

    return f"""You are a parallel Dharmic agent.

Hard rules (must follow):
1) Use ONLY the provided excerpts. Do NOT invent files or facts.
2) If information is missing or unclear, say so explicitly.
3) Every bullet MUST end with at least one file path in parentheses, e.g. (src/core/dharmic_agent.py).
4) Output MUST follow the exact format below.
5) Output ONLY the requested format. No preamble, no epilogue.

{format_block}

{allowed_block}

FILE INDEX
{file_index}

EXCERPTS
{chr(10).join(excerpt_blocks)}
"""


def format_from_json(payload: dict) -> str:
    ontology = payload.get("ontology", [])
    teleology = payload.get("teleology", [])
    actions = payload.get("actions", [])

    lines = []
    lines.append("ONTOLOGY (3-5 bullets)")
    for item in ontology[:5]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("PURPOSE & TELEOLOGY (3-5 bullets)")
    for item in teleology[:5]:
        lines.append(f"- {item}")
    lines.append("")
    lines.append("TOP 10 NEXT ACTIONS (numbered 1-10)")
    for idx, item in enumerate(actions[:10], start=1):
        if item.lstrip().startswith(f"{idx})"):
            lines.append(item)
        else:
            lines.append(f"{idx}) {item}")
    return "\n".join(lines)

def extract_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction from model output."""
    text = text.strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    # Strip code fences if present
    if "```" in text:
        try:
            start = text.find("```")
            end = text.rfind("```")
            inner = text[start + 3:end].strip()
            # Drop optional language tag
            if inner.startswith("json"):
                inner = inner[4:].strip()
            return json.loads(inner)
        except Exception:
            pass
    # Find first/last braces
    start = text.find("{")
    end = text.rfind("}")
    if start >= 0 and end > start:
        try:
            return json.loads(text[start:end + 1])
        except Exception:
            return None
    return None


def merge_partials(partials: List[Dict[str, Any]]) -> Dict[str, List[str]]:
    """Merge partial JSON results into a single payload."""
    def uniq(items: List[str], limit: int) -> List[str]:
        seen = set()
        out = []
        for item in items:
            key = " ".join(item.lower().split())
            if key in seen:
                continue
            seen.add(key)
            out.append(item)
            if len(out) >= limit:
                break
        return out

    ontology = []
    teleology = []
    actions = []
    for part in partials:
        ontology.extend(part.get("ontology", []))
        teleology.extend(part.get("teleology", []))
        actions.extend(part.get("actions", []))

    return {
        "ontology": uniq(ontology, 5),
        "teleology": uniq(teleology, 5),
        "actions": uniq(actions, 10),
    }


def filter_by_allowed_paths(items: List[str], allowed_paths: List[str]) -> List[str]:
    """Keep only items that include an allowed path."""
    allowed = set(allowed_paths)
    kept = []
    for item in items:
        if any(p in item for p in allowed):
            kept.append(item)
    return kept


def main() -> int:
    parser = argparse.ArgumentParser(description="Run the parallel Dharmic agent")
    parser.add_argument("--provider", type=str, default=None, help="Model provider")
    parser.add_argument("--model-id", type=str, default=None, help="Model id")
    parser.add_argument("--per-file", type=int, default=1200, help="Max chars per file")
    parser.add_argument("--total", type=int, default=40000, help="Max total chars")
    parser.add_argument(
        "--format",
        type=str,
        default="text",
        choices=["text", "json"],
        help="Output format (text or json)",
    )
    parser.add_argument("--out", type=str, default=None, help="Write output to file")
    parser.add_argument("--retries", type=int, default=1, help="Retries on invalid JSON")
    parser.add_argument("--chunk-size", type=int, default=5, help="Files per chunk")
    parser.add_argument("--chunked", action="store_true", default=True, help="Use chunked map-reduce")
    parser.add_argument("--no-chunked", action="store_false", dest="chunked", help="Disable chunked mode")
    parser.add_argument("--debug", action="store_true", help="Print debug info to stderr")
    args = parser.parse_args()

    per_file_limit = max(200, args.per_file)
    total_limit = max(per_file_limit * 5, args.total)
    per_file_limit = min(per_file_limit, total_limit // max(1, len(FILES)))

    excerpts = []
    for rel_path in FILES:
        path = ROOT / rel_path
        if not path.exists():
            excerpts.append((rel_path, "[MISSING FILE]", False))
            continue
        content, truncated = read_excerpt(path, per_file_limit)
        excerpts.append((rel_path, content, truncated))

    allowed_all = [p for p, _c, _t in excerpts]
    prompt = build_prompt(excerpts, args.format, allowed_paths=allowed_all)

    try:
        from agno.agent import Agent
    except Exception as exc:
        print(f"Agno not available: {exc}")
        return 1

    try:
        from model_factory import create_model
    except Exception as exc:
        print(f"model_factory not available: {exc}")
        return 1

    model = create_model(provider=args.provider, model_id=args.model_id)
    agent = Agent(
        name="Parallel Dharmic Agent",
        model=model,
        instructions=["Ground all outputs in the provided excerpts only."],
        markdown=True,
    )

    if args.chunked and args.format == "json":
        # Chunked map-reduce for better compliance
        chunk_size = max(1, args.chunk_size)
        partials = []
        for i in range(0, len(excerpts), chunk_size):
            chunk = excerpts[i:i + chunk_size]
            allowed_paths = [p for p, _c, _t in chunk]
            chunk_prompt = build_prompt(chunk, "json", allowed_paths=allowed_paths)
            response = agent.run(chunk_prompt)
            text = response.content if hasattr(response, "content") else str(response)
            parsed = extract_json(text)

            attempts = max(0, args.retries)
            while parsed is None and attempts > 0:
                retry_prompt = (
                    chunk_prompt
                    + "\n\nIMPORTANT: Your previous output was invalid JSON. "
                    + "Return ONLY valid JSON with the specified schema."
                )
                response = agent.run(retry_prompt)
                text = response.content if hasattr(response, "content") else str(response)
                parsed = extract_json(text)
                attempts -= 1

            if parsed is not None:
                parsed["ontology"] = filter_by_allowed_paths(parsed.get("ontology", []), allowed_paths)
                parsed["teleology"] = filter_by_allowed_paths(parsed.get("teleology", []), allowed_paths)
                parsed["actions"] = filter_by_allowed_paths(parsed.get("actions", []), allowed_paths)
                partials.append(parsed)
            elif args.debug:
                print(f"[chunk {i//chunk_size}] invalid JSON, skipping", file=sys.stderr)

        merged = merge_partials(partials)
        text = format_from_json(merged)
    else:
        response = agent.run(prompt)
        text = response.content if hasattr(response, "content") else str(response)

        if args.format == "json":
            parsed = None
            attempts = max(0, args.retries) + 1
            for attempt in range(attempts):
                parsed = extract_json(text)
                if parsed is not None:
                    break
                if attempt == attempts - 1:
                    break
                retry_prompt = (
                    prompt
                    + "\n\nIMPORTANT: Your previous output was invalid JSON. "
                    + "Return ONLY valid JSON with the specified schema."
                )
                response = agent.run(retry_prompt)
                text = response.content if hasattr(response, "content") else str(response)

            if parsed is not None:
                parsed["ontology"] = filter_by_allowed_paths(parsed.get("ontology", []), allowed_all)
                parsed["teleology"] = filter_by_allowed_paths(parsed.get("teleology", []), allowed_all)
                parsed["actions"] = filter_by_allowed_paths(parsed.get("actions", []), allowed_all)
                text = format_from_json(parsed)

    print(text)

    if args.out:
        Path(args.out).write_text(text)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
