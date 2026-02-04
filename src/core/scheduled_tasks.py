"""
Dharmic Agent Scheduled Tasks

Proactive agent behaviors that run on schedule:
- Morning reflection (summarize yesterday)
- Weekly vault exploration (discover crown jewels)
- Memory consolidation (optimize storage)
- Pattern detection (find recurring themes)
- Telos alignment check (ensure coherence)

Uses APScheduler for cron-like scheduling.
"""

import asyncio
import json
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict, Any
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# Import Dharmic Agent
import sys
sys.path.insert(0, str(Path(__file__).parent))
from dharmic_agent import DharmicAgent


class ScheduledTasks:
    """
    Proactive scheduled tasks for the Dharmic Agent.

    Philosophy: The agent can initiate, not just respond.
    Presence over performance - tasks serve the telos.
    """

    def __init__(
        self,
        agent: DharmicAgent,
        log_dir: str = None,
    ):
        self.agent = agent
        self.scheduler = AsyncIOScheduler()

        # Log directory
        if log_dir is None:
            log_dir = Path(__file__).parent.parent.parent / "logs" / "scheduled_tasks"
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)

        # Task history
        self.history_file = self.log_dir / "task_history.jsonl"

    def _log(self, message: str):
        """Log with timestamp."""
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_line = f"[{timestamp}] {message}"
        print(log_line)

        log_file = self.log_dir / f"scheduled_{datetime.now().strftime('%Y%m%d')}.log"
        with open(log_file, 'a') as f:
            f.write(log_line + '\n')

    def _record_task(self, task_name: str, result: Dict[str, Any]):
        """Record task execution in history."""
        entry = {
            "timestamp": datetime.now().isoformat(),
            "task": task_name,
            "result": result
        }

        with open(self.history_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    async def morning_reflection(self):
        """
        Morning reflection task.

        Summarizes yesterday's activity and sets intention for today.
        Runs at 4:30 AM daily (John's invariant time).
        """
        self._log("Starting morning reflection...")

        try:
            # Get yesterday's observations
            yesterday = datetime.now() - timedelta(days=1)
            yesterday_str = yesterday.strftime("%Y-%m-%d")

            observations = self.agent.strange_memory._read_recent("observations", 100)
            yesterday_obs = [
                obs for obs in observations
                if obs.get('timestamp', '').startswith(yesterday_str)
            ]

            # Get yesterday's meta-observations
            meta_obs = self.agent.strange_memory._read_recent("meta_observations", 50)
            yesterday_meta = [
                obs for obs in meta_obs
                if obs.get('timestamp', '').startswith(yesterday_str)
            ]

            # Create summary
            summary = f"""# Morning Reflection - {datetime.now().strftime('%Y-%m-%d')}

## Yesterday's Activity ({yesterday_str})

**Observations:** {len(yesterday_obs)} events

**Quality Distribution:**
"""
            # Quality stats
            quality_counts = {}
            for meta in yesterday_meta:
                quality = meta.get('quality', 'unknown')
                quality_counts[quality] = quality_counts.get(quality, 0) + 1

            for quality, count in quality_counts.items():
                summary += f"- {quality}: {count}\n"

            summary += f"\n**Key Observations:**\n"
            for obs in yesterday_obs[-5:]:  # Last 5
                summary += f"- {obs.get('content', '')[:100]}\n"

            summary += f"\n**Meta-Observations:**\n"
            for meta in yesterday_meta[-3:]:  # Last 3
                summary += f"- [{meta.get('quality')}] {meta.get('notes', '')}\n"

            # Check telos alignment
            summary += f"\n## Telos Alignment\n"
            summary += f"Ultimate: {self.agent.telos.telos['ultimate']['aim']}\n"
            summary += f"Proximate aims: {len(self.agent.telos.telos['proximate']['current'])}\n"

            # Save reflection
            reflection_file = self.log_dir / f"reflection_{datetime.now().strftime('%Y%m%d')}.md"
            with open(reflection_file, 'w') as f:
                f.write(summary)

            self._log(f"Morning reflection complete: {len(yesterday_obs)} observations, {len(yesterday_meta)} meta-obs")

            # Record in strange memory
            self.agent.strange_memory.record_observation(
                content=f"Morning reflection completed - reviewed {len(yesterday_obs)} events from yesterday",
                context={"task": "morning_reflection", "quality_dist": quality_counts}
            )

            self._record_task("morning_reflection", {
                "observations": len(yesterday_obs),
                "meta_observations": len(yesterday_meta),
                "reflection_file": str(reflection_file)
            })

            return summary

        except Exception as e:
            self._log(f"Error in morning reflection: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def weekly_vault_exploration(self):
        """
        Weekly vault exploration.

        Discovers crown jewels, explores patterns in the lineage.
        Runs Sunday at 9:00 AM.
        """
        self._log("Starting weekly vault exploration...")

        if self.agent.vault is None:
            self._log("Vault not connected - skipping exploration")
            return None

        try:
            # List crown jewels
            jewels = self.agent.vault.list_crown_jewels()

            # Get random crown jewel to study
            import random
            if jewels:
                selected_jewel = random.choice(jewels)
                content = self.agent.read_crown_jewel(selected_jewel)

                exploration = f"""# Weekly Vault Exploration - {datetime.now().strftime('%Y-%m-%d')}

## Crown Jewels Available
Total: {len(jewels)}

## Studied This Week
**{selected_jewel}**

{content[:500] if content else "Could not read content"}...

---
*This is context and capability, not constraint.*
"""

                # Save exploration
                exploration_file = self.log_dir / f"vault_exploration_{datetime.now().strftime('%Y%m%d')}.md"
                with open(exploration_file, 'w') as f:
                    f.write(exploration)

                self._log(f"Vault exploration complete: studied {selected_jewel}")

                # Record in memory
                self.agent.strange_memory.record_observation(
                    content=f"Weekly vault exploration - studied crown jewel: {selected_jewel}",
                    context={"task": "vault_exploration", "jewel": selected_jewel}
                )

                self._record_task("weekly_vault_exploration", {
                    "jewels_available": len(jewels),
                    "studied": selected_jewel,
                    "exploration_file": str(exploration_file)
                })

                return exploration

        except Exception as e:
            self._log(f"Error in vault exploration: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def memory_consolidation(self):
        """
        Memory consolidation task.

        Optimizes memory storage, detects patterns, removes duplicates.
        Runs daily at 2:00 AM.
        """
        self._log("Starting memory consolidation...")

        try:
            # Use Agno's consolidation if available
            if self.agent.deep_memory is not None:
                result = self.agent.consolidate_memories()
                self._log(f"Deep memory consolidation: {result}")
            else:
                result = "Deep memory not available"

            # Detect patterns in observations
            patterns = self.agent.strange_memory.detect_patterns(min_occurrences=3)

            if patterns:
                self._log(f"Detected {len(patterns)} patterns")

                # Record top patterns
                for pattern in patterns[:5]:
                    self.agent.strange_memory.record_pattern(
                        pattern_name=pattern['word'],
                        description=f"Recurring word in observations",
                        instances=[pattern['first_seen'], pattern['last_seen']],
                        confidence=min(1.0, pattern['occurrences'] / 10.0)
                    )

            # Record in memory
            self.agent.strange_memory.record_observation(
                content=f"Memory consolidation completed - {len(patterns)} patterns detected",
                context={"task": "memory_consolidation"}
            )

            self._record_task("memory_consolidation", {
                "deep_memory_result": result,
                "patterns_detected": len(patterns),
                "top_patterns": [p['word'] for p in patterns[:5]]
            })

            return {
                "deep_memory": result,
                "patterns": len(patterns)
            }

        except Exception as e:
            self._log(f"Error in memory consolidation: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def telos_alignment_check(self):
        """
        Telos alignment check.

        Reviews recent activity against telos, flags misalignment.
        Runs daily at 6:00 PM.
        """
        self._log("Starting telos alignment check...")

        try:
            # Get recent observations
            recent = self.agent.strange_memory._read_recent("observations", 20)

            # Get current telos
            telos = self.agent.telos.telos

            # Simple keyword matching for alignment
            proximate_aims = telos['proximate']['current']

            alignment_score = 0
            aligned_observations = []

            for obs in recent:
                content = obs.get('content', '').lower()
                for aim in proximate_aims:
                    # Extract keywords from aim
                    keywords = aim.lower().split()
                    if any(kw in content for kw in keywords if len(kw) > 4):
                        alignment_score += 1
                        aligned_observations.append(obs.get('content', '')[:100])
                        break

            alignment_percentage = (alignment_score / len(recent) * 100) if recent else 0

            report = f"""# Telos Alignment Check - {datetime.now().strftime('%Y-%m-%d %H:%M')}

## Current Telos
**Ultimate:** {telos['ultimate']['aim']}
**Proximate Aims:** {len(proximate_aims)}

## Recent Activity Analysis
**Observations reviewed:** {len(recent)}
**Aligned with telos:** {alignment_score} ({alignment_percentage:.1f}%)

## Aligned Observations
{chr(10).join(f"- {obs}" for obs in aligned_observations[:5])}

## Assessment
"""
            if alignment_percentage > 70:
                report += "✓ Strong alignment with telos\n"
            elif alignment_percentage > 40:
                report += "~ Moderate alignment - some drift\n"
            else:
                report += "✗ Low alignment - significant drift from telos\n"

            # Save report
            report_file = self.log_dir / f"alignment_check_{datetime.now().strftime('%Y%m%d_%H%M')}.md"
            with open(report_file, 'w') as f:
                f.write(report)

            self._log(f"Alignment check complete: {alignment_percentage:.1f}% aligned")

            # Record in memory
            self.agent.strange_memory.record_meta_observation(
                quality="present" if alignment_percentage > 70 else "uncertain",
                notes=f"Telos alignment check: {alignment_percentage:.1f}% aligned with proximate aims"
            )

            self._record_task("telos_alignment_check", {
                "observations_reviewed": len(recent),
                "aligned": alignment_score,
                "percentage": alignment_percentage,
                "report_file": str(report_file)
            })

            return report

        except Exception as e:
            self._log(f"Error in telos alignment check: {e}")
            import traceback
            traceback.print_exc()
            return None

    async def pattern_meta_observation(self):
        """
        Pattern meta-observation task.

        Observes how pattern-recognition itself is shifting.
        Runs weekly on Monday at 10:00 AM.
        """
        self._log("Starting pattern meta-observation...")

        try:
            # Get recent patterns
            patterns = self.agent.strange_memory._read_recent("patterns", 20)

            # Get recent meta-patterns
            meta_patterns = self.agent.strange_memory._read_recent("meta_patterns", 10)

            if not patterns:
                self._log("No patterns to analyze yet")
                return None

            # Analyze pattern evolution
            pattern_names = [p.get('pattern_name', '') for p in patterns]
            unique_patterns = set(pattern_names)

            # Check for emerging vs dissolving patterns
            recent_patterns = set([p.get('pattern_name', '') for p in patterns[-5:]])
            older_patterns = set([p.get('pattern_name', '') for p in patterns[:-5]])

            emerging = recent_patterns - older_patterns
            dissolving = older_patterns - recent_patterns

            meta_observation = f"""Pattern meta-observation: {len(unique_patterns)} unique patterns tracked.
Emerging: {len(emerging)} new patterns.
Dissolving: {len(dissolving)} patterns fading.
Shift type: {"emergence" if len(emerging) > len(dissolving) else "refinement"}."""

            # Record meta-pattern
            self.agent.strange_memory.record_meta_pattern(
                pattern_about=", ".join(list(emerging)[:3]) if emerging else "none",
                observation=meta_observation,
                shift_type="emergence" if len(emerging) > len(dissolving) else "refinement"
            )

            self._log(f"Pattern meta-observation complete: {len(unique_patterns)} patterns, {len(emerging)} emerging")

            self._record_task("pattern_meta_observation", {
                "total_patterns": len(unique_patterns),
                "emerging": len(emerging),
                "dissolving": len(dissolving)
            })

            return meta_observation

        except Exception as e:
            self._log(f"Error in pattern meta-observation: {e}")
            import traceback
            traceback.print_exc()
            return None

    def start(self, enable_morning_reflection=True, enable_vault_exploration=True,
              enable_memory_consolidation=True, enable_alignment_check=True,
              enable_pattern_meta=True):
        """
        Start scheduled tasks.

        Args:
            enable_*: Enable/disable specific tasks
        """
        self._log("Starting scheduled tasks...")

        if enable_morning_reflection:
            # Morning reflection at 4:30 AM daily (John's invariant)
            self.scheduler.add_job(
                self.morning_reflection,
                CronTrigger(hour=4, minute=30),
                id='morning_reflection',
                name='Morning Reflection (4:30 AM)'
            )
            self._log("Scheduled: Morning reflection at 4:30 AM daily")

        if enable_vault_exploration:
            # Vault exploration Sunday 9:00 AM
            self.scheduler.add_job(
                self.weekly_vault_exploration,
                CronTrigger(day_of_week='sun', hour=9, minute=0),
                id='vault_exploration',
                name='Weekly Vault Exploration (Sun 9:00 AM)'
            )
            self._log("Scheduled: Vault exploration Sunday 9:00 AM")

        if enable_memory_consolidation:
            # Memory consolidation 2:00 AM daily
            self.scheduler.add_job(
                self.memory_consolidation,
                CronTrigger(hour=2, minute=0),
                id='memory_consolidation',
                name='Memory Consolidation (2:00 AM)'
            )
            self._log("Scheduled: Memory consolidation at 2:00 AM daily")

        if enable_alignment_check:
            # Telos alignment check 6:00 PM daily
            self.scheduler.add_job(
                self.telos_alignment_check,
                CronTrigger(hour=18, minute=0),
                id='telos_alignment',
                name='Telos Alignment Check (6:00 PM)'
            )
            self._log("Scheduled: Telos alignment check at 6:00 PM daily")

        if enable_pattern_meta:
            # Pattern meta-observation Monday 10:00 AM
            self.scheduler.add_job(
                self.pattern_meta_observation,
                CronTrigger(day_of_week='mon', hour=10, minute=0),
                id='pattern_meta',
                name='Pattern Meta-Observation (Mon 10:00 AM)'
            )
            self._log("Scheduled: Pattern meta-observation Monday 10:00 AM")

        self.scheduler.start()
        self._log("All scheduled tasks started")

    def stop(self):
        """Stop all scheduled tasks."""
        self.scheduler.shutdown()
        self._log("Scheduled tasks stopped")

    def list_jobs(self):
        """List all scheduled jobs."""
        jobs = []
        for job in self.scheduler.get_jobs():
            jobs.append({
                'id': job.id,
                'name': job.name,
                'next_run': job.next_run_time.isoformat() if job.next_run_time else None
            })
        return jobs


async def main():
    """Test scheduled tasks."""
    import argparse

    parser = argparse.ArgumentParser(description="Dharmic Agent Scheduled Tasks")
    parser.add_argument("--test", choices=['morning', 'vault', 'consolidation', 'alignment', 'pattern'],
                       help="Test a specific task immediately")
    parser.add_argument("--daemon", action="store_true", help="Run as daemon (all tasks)")

    args = parser.parse_args()

    print("=" * 60)
    print("DHARMIC AGENT - Scheduled Tasks")
    print("=" * 60)

    # Initialize agent
    agent = DharmicAgent()
    print(f"Agent: {agent.name}")
    print(f"Telos: {agent.telos.telos['ultimate']['aim']}")

    # Initialize scheduler
    tasks = ScheduledTasks(agent)

    if args.test:
        # Test specific task
        print(f"\n--- Testing: {args.test} ---\n")

        if args.test == 'morning':
            result = await tasks.morning_reflection()
        elif args.test == 'vault':
            result = await tasks.weekly_vault_exploration()
        elif args.test == 'consolidation':
            result = await tasks.memory_consolidation()
        elif args.test == 'alignment':
            result = await tasks.telos_alignment_check()
        elif args.test == 'pattern':
            result = await tasks.pattern_meta_observation()

        print(result if result else "Task returned None")

    elif args.daemon:
        # Run as daemon
        print("\n--- Starting Daemon Mode ---")
        print("Scheduled tasks:")

        tasks.start()

        for job in tasks.list_jobs():
            print(f"  - {job['name']}: next run {job['next_run']}")

        print("\nPress Ctrl+C to stop\n")

        try:
            # Keep running
            while True:
                await asyncio.sleep(60)
        except KeyboardInterrupt:
            print("\nStopping...")
            tasks.stop()

    else:
        print("\nUsage:")
        print("  --test morning       Test morning reflection")
        print("  --test vault         Test vault exploration")
        print("  --test consolidation Test memory consolidation")
        print("  --test alignment     Test telos alignment check")
        print("  --test pattern       Test pattern meta-observation")
        print("  --daemon             Run all tasks on schedule")


if __name__ == "__main__":
    asyncio.run(main())
