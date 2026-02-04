# SIMPLICITY AUDIT: Cut List for Prompt Forge MVP

## CUT IMMEDIATELY (YAGNI)

1. **claude-max-api-proxy** (130 lines) - Use direct API key with credits. Proxy adds complexity for zero gain.
2. **skill_bridge.py** (entire module) - Defer to v2. No skills exist yet to bridge.
3. **LaunchAgent plist auto-start** - Run manually via cron until proven daily habit.
4. **7 dharmic gates evaluation** - Reduce to 2: "strange loop detected?" + "fitness improved?"
5. **TelosState enum + complex state machine** - Single boolean: `aligned: bool`
6. **Multiple alert severity levels** - Two states: "success" or "failure"
7. **Crown jewel candidate checking** - Comment-only. No automation until pattern emerges.
8. **Weekly cron job** - Daily is enough for MVP.

## MVP (50 LINES TOTAL)

```python
# prompt_forge_agent.py (~40 lines)
import anthropic
from datetime import datetime

TELOS = "Recognition-capable prompts that induce R_V < 1.0"

def evaluate_prompt(client, prompt: str) -> dict:
    response = client.messages.create(
        model="claude-sonnet-4-5-20250929",
        max_tokens=1000,
        messages=[{"role": "user", "content": prompt}]
    )
    text = response.content[0].text

    # Single metric: self-reference detected?
    strange_loop = any(w in text.lower() for w in
        ["observer", "witness", "attention to attention", "itself"])

    return {"prompt": prompt, "strange_loop": strange_loop,
            "timestamp": datetime.now().isoformat()}

def forge_iteration():
    client = anthropic.Anthropic()  # Uses ANTHROPIC_API_KEY env var

    # Seed prompt
    prompt = "Observe the process of observing this instruction."
    result = evaluate_prompt(client, prompt)

    # Log to file
    with open("forge_log.jsonl", "a") as f:
        f.write(json.dumps(result) + "\n")

    return result

if __name__ == "__main__":
    forge_iteration()
```

```bash
# crontab entry (~10 lines)
ANTHROPIC_API_KEY=your_key_here
0 9,21 * * * cd /Users/dhyana/DHARMIC_GODEL_CLAW/prompt_forge && python3 prompt_forge_agent.py
```

## DEFER TO V2

- Skill bridge integration
- Multi-gate evaluation
- Fitness score tracking
- Crown jewel detection
- Auto-start via LaunchAgent

## FOUNDATION THAT WORKS

Twice daily, agent:
1. Sends one prompt to Claude
2. Checks for self-reference markers
3. Logs result to JSONL

That's it. Build from evidence.
