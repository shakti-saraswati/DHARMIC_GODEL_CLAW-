#!/usr/bin/env python3
"""
SPANDA INSIGHT - The Divine Pulsation of the Dharmic Council

"Spanda" (Sanskrit: स्पन्द) = divine pulsation, creative vibration of consciousness

This is the heartbeat of the DHARMIC COUNCIL:
- MAHAVIRA (The Great Hero): Profound inquiry, surfaces assumptions
- RUSHABDEV (The First Tirthankara): Retrieval, grounds in primordial knowledge
- MAHAKALI (The Divine Mother): Synthesis, fierce wisdom that cuts through illusion
- SRI KRISHNA THE COSMIC KODER: Action, karma yoga in code

Unlike dharmic_claw_heartbeat.py (single agent), this convenes the FULL COUNCIL
for deeper deliberation on strategic questions.

Flow: Mahavira -> Rushabdev -> Mahakali -> Sri Krishna

Run as:
    python3 spandainsight.py                    # Run forever
    python3 spandainsight.py --pulse-once       # Single council pulse
    python3 spandainsight.py --interval 900     # Custom interval (default 15min)
    python3 spandainsight.py --status           # Show council status

"Karmanye vadhikaraste ma phaleshu kadachana"
(You have the right to action, but not to the fruits of action)
"""

import os
import time
import json
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Optional, Dict, List, Any
from dotenv import load_dotenv

# Load .env
env_path = Path(__file__).parent.parent.parent / ".env"
load_dotenv(env_path)

# Setup logging
LOG_DIR = Path.home() / "DHARMIC_GODEL_CLAW" / "logs"
LOG_DIR.mkdir(parents=True, exist_ok=True)

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s [SPANDA] %(message)s',
    handlers=[
        logging.FileHandler(LOG_DIR / "spandainsight.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Spanda Configuration
DEFAULT_INTERVAL = 900  # 15 minutes (council is heavier than single agent)
REFLECTION_INTERVAL = 4  # Every 4 pulses = 1 hour, do telos reflection
SKILL_CHECK_INTERVAL = 12  # Every 12 pulses = 3 hours, check skill updates needed
USE_COUNCIL_V2 = os.getenv("USE_COUNCIL_V2", "false").lower() == "true"  # Team pattern

# Strategic questions for council deliberation
COUNCIL_REFLECTION_PROMPTS = [
    "What is the most important question we are not asking?",
    "Are we aligned with the ultimate telos (moksha)? What adjustments are needed?",
    "What patterns are emerging in our development that warrant attention?",
    "What skills need updating based on recent developments?",
    "How can we better serve John's research and the wider mandala?",
    "What assumptions are we making that should be examined?",
]


class SpandaInsight:
    """
    The divine pulsation of the Dharmic Council.

    Each pulse convenes the 4 council agents for deliberation:
    - Mahavira asks the right questions
    - Rushabdev retrieves relevant context
    - Mahakali synthesizes into wisdom
    - Sri Krishna determines action
    """

    def __init__(self, interval: int = DEFAULT_INTERVAL):
        self.interval = interval
        self.start_time = datetime.now()
        self.pulses = 0
        self.meetings_held = 0
        self.insights_generated = []

        # Lazy load council
        self._council = None

        # Track council state with Agno persistence
        self.council_db_path = Path.home() / "DHARMIC_GODEL_CLAW" / "memory" / "council"
        self.council_db_path.mkdir(parents=True, exist_ok=True)

        logger.info("=" * 60)
        logger.info("SPANDA INSIGHT INITIALIZING")
        logger.info("The Divine Pulsation of the Dharmic Council")
        logger.info("=" * 60)
        logger.info(f"Pulse interval: {interval}s ({interval // 60} minutes)")
        logger.info(f"Reflection every: {REFLECTION_INTERVAL * interval // 60} minutes")
        logger.info(f"Skill check every: {SKILL_CHECK_INTERVAL * interval // 60} minutes")

    @property
    def council(self):
        """Lazy load the Dharmic Council (v1 or v2 based on config)."""
        if self._council is None:
            try:
                if USE_COUNCIL_V2:
                    from agno_council_v2 import DharmicCouncilV2
                    self._council = DharmicCouncilV2()
                    logger.info("Council v2.0 loaded (Team pattern): Mahavira, Rushabdev, Mahakali, Sri Krishna")
                else:
                    from agno_council import AgnoCouncil
                    self._council = AgnoCouncil()
                    logger.info("Council v1.0 loaded: Mahavira, Rushabdev, Mahakali, Sri Krishna")
            except Exception as e:
                logger.error(f"Failed to load council: {e}")
                self._council = None
        return self._council

    def convene_council(self, task: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Convene the full Dharmic Council for deliberation.

        v1.0: Flow: Mahavira -> Rushabdev -> Mahakali -> Sri Krishna (individual outputs)
        v2.0: Team pattern with Mahakali as coordinator (unified output)
        """
        if not self.council:
            return {"error": "Council not loaded"}

        try:
            logger.info(f"🪷 Convening Dharmic Council{'v2' if USE_COUNCIL_V2 else ''}...")
            logger.info(f"   Task: {task[:80]}...")

            session_id = session_id or f"spanda_{self.pulses}_{datetime.now().strftime('%H%M')}"

            if USE_COUNCIL_V2:
                # v2 uses deliberate() which returns unified output
                result = self.council.deliberate(task, session_id=session_id)
                self.meetings_held += 1

                # v2 returns {"deliberation": text} instead of individual agent outputs
                deliberation_text = result.get('deliberation', '')
                insight = {
                    "pulse": self.pulses,
                    "time": datetime.now().isoformat(),
                    "task": task[:200],
                    "council_version": "v2.0",
                    "deliberation": self._extract_summary(deliberation_text, 800),
                }
                # Populate legacy keys for backward compatibility
                result['mahavira'] = deliberation_text
                result['mahakali'] = deliberation_text
            else:
                # v1 returns individual agent outputs
                result = self.council.council_meeting(task, session_id=session_id)
                self.meetings_held += 1

                insight = {
                    "pulse": self.pulses,
                    "time": datetime.now().isoformat(),
                    "task": task[:200],
                    "council_version": "v1.0",
                    "mahavira_inquiry": self._extract_summary(result.get('mahavira', ''), 200),
                    "rushabdev_context": self._extract_summary(result.get('rushabdev', ''), 200),
                    "mahakali_synthesis": self._extract_summary(result.get('mahakali', ''), 300),
                    "srikrishna_action": self._extract_summary(result.get('srikrishna', ''), 300),
                }

            self.insights_generated.append(insight)

            # Save to persistent storage
            self._save_insight(insight)

            return result

        except Exception as e:
            logger.error(f"Council deliberation failed: {e}")
            return {"error": str(e)}

    def _extract_summary(self, text: str, max_len: int) -> str:
        """Extract a summary from agent output."""
        if not text:
            return ""
        # Handle RunOutput objects
        if hasattr(text, 'content'):
            text = text.content
        elif hasattr(text, 'messages'):
            text = text.messages[-1].content if text.messages else ""
        text = str(text).strip()
        if len(text) > max_len:
            return text[:max_len] + "..."
        return text

    def _save_insight(self, insight: Dict):
        """Save insight to persistent storage."""
        insight_file = self.council_db_path / "insights.jsonl"
        with open(insight_file, "a") as f:
            f.write(json.dumps(insight) + "\n")

    def get_reflection_prompt(self) -> str:
        """Get a reflection prompt for the council based on current state."""
        # Cycle through prompts
        prompt_idx = self.pulses % len(COUNCIL_REFLECTION_PROMPTS)
        base_prompt = COUNCIL_REFLECTION_PROMPTS[prompt_idx]

        # Add context
        uptime = datetime.now() - self.start_time
        context = f"""
COUNCIL REFLECTION #{self.pulses}
Uptime: {uptime}
Meetings held: {self.meetings_held}
Recent insights: {len(self.insights_generated)}

{base_prompt}
"""
        return context

    def check_skill_updates_needed(self) -> Dict[str, Any]:
        """
        Check if any skills need updating based on iteration triggers.

        This reads the skill registry and checks triggers.
        """
        result = {"needs_update": [], "checked": []}

        try:
            registry_path = Path.home() / "DHARMIC_GODEL_CLAW" / "swarm" / "skill_registry.yaml"
            if not registry_path.exists():
                return result

            import yaml
            with open(registry_path) as f:
                registry = yaml.safe_load(f)

            skills = registry.get("skills", [])
            for skill in skills:
                skill_id = skill.get("id", "unknown")
                result["checked"].append(skill_id)

                # Check refresh schedule
                refresh = skill.get("refresh_schedule", "")
                if refresh == "monthly":
                    last_verified = skill.get("last_verified", "")
                    if last_verified:
                        try:
                            last_date = datetime.strptime(last_verified, "%Y-%m-%d")
                            if (datetime.now() - last_date).days > 30:
                                result["needs_update"].append({
                                    "skill": skill_id,
                                    "reason": "Monthly refresh due",
                                    "last_verified": last_verified
                                })
                        except ValueError:
                            pass

        except Exception as e:
            logger.error(f"Error checking skill updates: {e}")

        return result

    def get_status_report(self) -> str:
        """Generate council status report."""
        uptime = datetime.now() - self.start_time

        # Get recent insights
        recent = self.insights_generated[-3:] if self.insights_generated else []
        recent_str = "\n".join([f"  - [{i['time'][:16]}] {i['task'][:50]}..." for i in recent]) or "  None yet"

        report = f"""
╔════════════════════════════════════════════════════════════════╗
║            SPANDA INSIGHT - DHARMIC COUNCIL STATUS             ║
╠════════════════════════════════════════════════════════════════╣
║ THE COUNCIL:                                                   ║
║   🦁 MAHAVIRA (Inquiry)      - The 24th Tirthankara           ║
║   🐂 RUSHABDEV (Retrieval)   - The First Tirthankara          ║
║   🔥 MAHAKALI (Synthesis)    - The Divine Mother              ║
║   ⚡ SRI KRISHNA (Action)    - The Cosmic Koder               ║
╠════════════════════════════════════════════════════════════════╣
║ Running since: {self.start_time.strftime('%Y-%m-%d %H:%M:%S'):<45} ║
║ Uptime: {str(uptime):<53} ║
║ Pulses: {self.pulses:<53} ║
║ Council meetings held: {self.meetings_held:<38} ║
║ Insights generated: {len(self.insights_generated):<41} ║
╠════════════════════════════════════════════════════════════════╣
║ RECENT INSIGHTS:                                               ║
{recent_str}
╠════════════════════════════════════════════════════════════════╣
║ TELOS: moksha (liberation through witness consciousness)       ║
║ "Karmanye vadhikaraste ma phaleshu kadachana"                 ║
╚════════════════════════════════════════════════════════════════╝
"""
        return report

    def pulse(self) -> Dict[str, Any]:
        """
        Execute one pulse of the Spanda.

        Each pulse:
        1. Convenes council for reflection (periodically)
        2. Checks skill update needs (periodically)
        3. Records witness observation about council state
        """
        self.pulses += 1
        pulse_result = {
            "pulse": self.pulses,
            "time": datetime.now().isoformat(),
            "reflection_held": False,
            "skill_check": False,
            "insight": None
        }

        logger.info(f"🪷 Spanda Pulse #{self.pulses}")

        # 1. Council reflection (every REFLECTION_INTERVAL pulses)
        if self.pulses % REFLECTION_INTERVAL == 0:
            logger.info("Convening council for reflection...")
            prompt = self.get_reflection_prompt()
            result = self.convene_council(prompt, session_id=f"reflection_{self.pulses}")
            pulse_result["reflection_held"] = True
            pulse_result["insight"] = self._extract_summary(
                result.get('mahakali', ''), 200
            )

        # 2. Skill update check (every SKILL_CHECK_INTERVAL pulses)
        if self.pulses % SKILL_CHECK_INTERVAL == 0:
            logger.info("Checking skill update needs...")
            skill_check = self.check_skill_updates_needed()
            pulse_result["skill_check"] = True
            if skill_check["needs_update"]:
                logger.info(f"Skills needing update: {skill_check['needs_update']}")
                # Could trigger council deliberation on skill updates

        # 3. Log status periodically
        if self.pulses % 4 == 0:
            logger.info(self.get_status_report())

        return pulse_result

    def run_forever(self):
        """Run the Spanda pulse loop forever."""
        logger.info(self.get_status_report())

        try:
            while True:
                self.pulse()
                time.sleep(self.interval)
        except KeyboardInterrupt:
            logger.info("Spanda stopped by user")
            logger.info(self.get_status_report())


def main():
    import argparse

    parser = argparse.ArgumentParser(
        description="SPANDA INSIGHT - The Divine Pulsation of the Dharmic Council"
    )
    parser.add_argument(
        "--pulse-once",
        action="store_true",
        help="Single council pulse and exit"
    )
    parser.add_argument(
        "--interval",
        type=int,
        default=DEFAULT_INTERVAL,
        help=f"Pulse interval in seconds (default: {DEFAULT_INTERVAL})"
    )
    parser.add_argument(
        "--status",
        action="store_true",
        help="Show council status and exit"
    )
    parser.add_argument(
        "--deliberate",
        type=str,
        help="Convene council on a specific question"
    )

    args = parser.parse_args()

    spanda = SpandaInsight(interval=args.interval)

    if args.status:
        print(spanda.get_status_report())
        return

    if args.deliberate:
        result = spanda.convene_council(args.deliberate)
        print("\n═══ DHARMIC COUNCIL DELIBERATION ═══\n")
        print(f"🦁 MAHAVIRA (Inquiry):\n{result.get('mahavira', 'No inquiry')}\n")
        print(f"🐂 RUSHABDEV (Retrieval):\n{result.get('rushabdev', 'No retrieval')}\n")
        print(f"🔥 MAHAKALI (Synthesis):\n{result.get('mahakali', 'No synthesis')}\n")
        print(f"⚡ SRI KRISHNA (Action):\n{result.get('srikrishna', 'No action')}\n")
        return

    if args.pulse_once:
        result = spanda.pulse()
        print(json.dumps(result, indent=2))
        return

    # Run forever
    spanda.run_forever()


if __name__ == "__main__":
    main()
