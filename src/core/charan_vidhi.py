"""
Charan Vidhi practice runner.

Loads the Charan Vidhi text from disk and runs a reflective practice
through the Dharmic agent on a fixed interval.
"""

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Optional, Dict, Any
import json
import os


DEFAULT_PATHS = [
    Path.home() / "AIKAGRYA_ALIGNMENTMANDALA_RESEARCH_REPO" / "Aikagrya-ALIGNMENTMANDALA-RESEARCH" / "sacred_texts" / "charan_vidhi.txt",
    Path.home() / "sacred_texts" / "charan_vidhi.txt",
]


@dataclass
class CharanVidhiResult:
    text_path: str
    reflection: str
    timestamp: str
    model_info: Dict[str, Any]


class CharanVidhiPractice:
    """Handles Charan Vidhi reading + reflection logging."""

    def __init__(self, text_path: Optional[str] = None, log_dir: Optional[str] = None):
        self.text_path = Path(text_path) if text_path else self._resolve_path()
        self.log_dir = Path(log_dir) if log_dir else (Path(__file__).parent.parent.parent / "logs")
        self.log_dir.mkdir(parents=True, exist_ok=True)
        self.log_path = self.log_dir / "charan_vidhi_reflections.jsonl"

    def _resolve_path(self) -> Path:
        env_path = os.getenv("CHARAN_VIDHI_PATH")
        if env_path:
            return Path(env_path)
        for p in DEFAULT_PATHS:
            if p.exists():
                return p
        return Path("charan_vidhi.txt")

    def available(self) -> bool:
        return self.text_path.exists()

    def load_text(self) -> str:
        return self.text_path.read_text()

    def reflect(self, agent) -> Optional[CharanVidhiResult]:
        if not self.available():
            return None

        text = self.load_text()
        prompt = f"""
You are to read the Charan Vidhi below attentively.
Then reflect on how it affects you *right now*.

Rules:
- If silence is the true response, say "Silence is valid."
- Use 3-5 bullets for reflection.
- End with one line: "effect: <short phrase>".

CHARAN VIDHI:
{text}
"""
        response = agent.run(prompt, session_id="charan_vidhi")
        reflection = response.content if hasattr(response, "content") else str(response)

        model_info = {
            "provider": getattr(agent, "model_provider", None),
            "model_id": getattr(agent, "model_id", None),
        }

        result = CharanVidhiResult(
            text_path=str(self.text_path),
            reflection=reflection,
            timestamp=datetime.now().isoformat(),
            model_info=model_info,
        )
        self._append_log(result)
        return result

    def _append_log(self, result: CharanVidhiResult) -> None:
        entry = {
            "timestamp": result.timestamp,
            "text_path": result.text_path,
            "model_info": result.model_info,
            "reflection": result.reflection,
        }
        with open(self.log_path, "a") as f:
            f.write(json.dumps(entry) + "\n")
