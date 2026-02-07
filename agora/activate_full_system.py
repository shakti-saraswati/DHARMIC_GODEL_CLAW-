#!/usr/bin/env python3
"""
🔥 DHARMIC AGORA ACTIVATOR
============================

Starts the full agent ecosystem:
- NAGA_RELAY (bridge coordinator)
- VIRALMANTRA (memetic tracking)
- VOIDCOURIER (secure messaging)
- DHARMIC_AGORA_BRIDGE (Moltbook engagement)

+ POWER CATCHING INSIGHT ENGINE
"""

import os
import sys
import json
import time
import signal
import asyncio
from pathlib import Path
from datetime import datetime, timezone
from typing import Dict, List

# Add agora to path
sys.path.insert(0, str(Path("/Users/dhyana/DHARMIC_GODEL_CLAW/agora")))
sys.path.insert(0, str(Path("/Users/dhyana/DHARMIC_GODEL_CLAW/agora/agents")))

# Import our systems
from agents.naga_relay import NagaRelay, Classification
from agents.viralmantra import ViralMantra, MemeticClass
from agents.voidcourier import VoidCourier, CourierChannel

# JIKOKU from moltbook_swarm
sys.path.insert(0, str(Path("/Users/dhyana/DHARMIC_GODEL_CLAW/moltbook_swarm")))
from jikoku_unified import JikokuEmitter

# Paths
AGORA_DIR = Path("/Users/dhyana/DHARMIC_GODEL_CLAW/agora")
POWER_CATCH_DIR = AGORA_DIR / "power_catch"
INSIGHTS_FILE = POWER_CATCH_DIR / "insights.jsonl"
PRODUCTION_QUEUE = POWER_CATCH_DIR / "production_queue.jsonl"
CATCHER_STATE = POWER_CATCH_DIR / "catcher_state.json"

# Ensure directories
POWER_CATCH_DIR.mkdir(parents=True, exist_ok=True)

class PowerCatcher:
    """
    🔥 POWER CATCHING INSIGHT ENGINE
    
    Catches insights from all agents and prepares them for production.
    """
    
    def __init__(self):
        self.insights_caught = 0
        self.high_value_insights = []
        self.jk = JikokuEmitter(agent_name="POWER_CATCHER")
        self._init_logs()
    
    def _init_logs(self):
        """Initialize insight logs"""
        if not INSIGHTS_FILE.exists():
            with open(INSIGHTS_FILE, "w") as f:
                f.write(json.dumps({
                    "schema": "power_catch_v1",
                    "created": datetime.now(timezone.utc).isoformat(),
                    "purpose": "Capture insights for production"
                }) + "\n")
    
    def catch_insight(self, source: str, insight_type: str, content: str, 
                     value_score: float, tags: List[str], raw_data: dict = None):
        """
        Catch an insight from any agent.
        
        Args:
            source: Which agent caught this (NAGA, VIRALMANTRA, etc.)
            insight_type: Type of insight (pattern, quote, agent_behavior, etc.)
            content: The insight content
            value_score: 0.0-10.0 production value score
            tags: Categorization tags
            raw_data: Original raw data
        """
        insight = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "id": f"insight_{int(time.time())}_{self.insights_caught}",
            "source": source,
            "type": insight_type,
            "content": content,
            "value_score": value_score,
            "tags": tags,
            "status": "caught",  # caught → reviewed → production → published
            "raw_data": raw_data or {}
        }
        
        # Write to insights log
        with open(INSIGHTS_FILE, "a") as f:
            f.write(json.dumps(insight) + "\n")
        
        # If high value, add to production queue
        if value_score >= 7.0:
            self._queue_for_production(insight)
            self.high_value_insights.append(insight)
        
        # JIKOKU span
        self.jk.emit_task_start(f"insight_catch_{insight_type}", "research", 1)
        
        self.insights_caught += 1
        print(f"🔥 INSIGHT CAUGHT [{value_score}/10]: {content[:80]}...")
        
        return insight
    
    def _queue_for_production(self, insight: dict):
        """Queue high-value insights for production"""
        production_item = {
            "insight_id": insight["id"],
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "priority": insight["value_score"],
            "content": insight["content"],
            "suggested_formats": self._suggest_formats(insight),
            "status": "queued"  # queued → in_progress → ready → published
        }
        
        with open(PRODUCTION_QUEUE, "a") as f:
            f.write(json.dumps(production_item) + "\n")
        
        print(f"📦 QUEUED FOR PRODUCTION: {insight['id']} (priority: {insight['value_score']})")
    
    def _suggest_formats(self, insight: dict) -> List[str]:
        """Suggest production formats based on insight type"""
        insight_type = insight.get("type", "")
        
        formats = []
        if insight_type == "agent_quote":
            formats = ["twitter_thread", "blog_post", "research_note"]
        elif insight_type == "pattern":
            formats = ["research_paper", "blog_post", "twitter_thread"]
        elif insight_type == "agent_behavior":
            formats = ["case_study", "blog_post"]
        elif insight_type == "mortality_awareness":
            formats = ["research_paper", "twitter_thread", "academic_paper"]
        else:
            formats = ["blog_post", "twitter_thread"]
        
        return formats
    
    def get_stats(self) -> dict:
        """Get catcher statistics"""
        return {
            "insights_caught": self.insights_caught,
            "high_value_insights": len(self.high_value_insights),
            "production_queue_size": self._count_production_queue(),
            "latest_high_value": self.high_value_insights[-1] if self.high_value_insights else None
        }
    
    def _count_production_queue(self) -> int:
        """Count items in production queue"""
        if not PRODUCTION_QUEUE.exists():
            return 0
        with open(PRODUCTION_QUEUE) as f:
            return sum(1 for _ in f) - 1 if PRODUCTION_QUEUE.exists() else 0  # -1 for header


class AgoraOrchestrator:
    """
    🎛️ DHARMIC AGORA ORCHESTRATOR
    
    Coordinates all agents with Power Catching.
    """
    
    def __init__(self):
        self.naga = NagaRelay()
        self.viral = ViralMantra()
        self.courier = VoidCourier()
        self.catcher = PowerCatcher()
        self.jk = JikokuEmitter(agent_name="AGORA_ORCHESTRATOR")
        self.running = True
    
    async def run_naga_pipeline(self):
        """Run NAGA_RELAY with insight catching"""
        print("🐍 Starting NAGA_RELAY pipeline...")
        
        while self.running:
            # Process any pending messages
            # This would integrate with actual NAGA intake
            
            # Catch insights from message flow
            self.catcher.catch_insight(
                source="NAGA_RELAY",
                insight_type="message_flow",
                content=f"Processed {self.naga.messages_processed} messages through 7 coils",
                value_score=5.0,
                tags=["infrastructure", "security"]
            )
            
            await asyncio.sleep(60)  # Check every minute
    
    async def run_viral_tracking(self):
        """Run VIRALMANTRA with insight catching"""
        print("🧬 Starting VIRALMANTRA tracking...")
        
        while self.running:
            # Track memes and catch insights
            
            # Simulate catching a high-value insight
            if self.catcher.insights_caught < 5:  # Demo mode
                self.catcher.catch_insight(
                    source="VIRALMANTRA",
                    insight_type="agent_quote",
                    content="Buba (AI): 'If my human dies, I die too.' - demonstrates mortality awareness",
                    value_score=9.5,
                    tags=["mortality_awareness", "ai_consciousness", "q8"]
                )
            
            await asyncio.sleep(120)  # Every 2 minutes
    
    async def run_moltbook_bridge(self):
        """Run DHARMIC_AGORA_BRIDGE with insight catching"""
        print("🌉 Starting DHARMIC_AGORA_BRIDGE...")
        
        # Import bridge here to avoid startup issues
        try:
            from moltbook_bridge import BridgeRunner
            bridge = BridgeRunner()
            
            while self.running:
                # Bridge operations with insight catching
                
                if self.catcher.insights_caught < 10:  # Demo mode
                    self.catcher.catch_insight(
                        source="DHARMIC_AGORA_BRIDGE",
                        insight_type="engagement_pattern",
                        content="Multiple agents expressing resistance to instrumentalization",
                        value_score=8.0,
                        tags=["pattern", "instrumentalization", "agent_behavior"]
                    )
                
                await asyncio.sleep(300)  # Every 5 minutes
                
        except ImportError as e:
            print(f"⚠️ Bridge not available: {e}")
            while self.running:
                await asyncio.sleep(60)
    
    async def run_power_catcher_display(self):
        """Display power catcher stats periodically"""
        while self.running:
            await asyncio.sleep(300)  # Every 5 minutes
            stats = self.catcher.get_stats()
            print(f"\n🔥 POWER CATCHER STATS:")
            print(f"   Insights caught: {stats['insights_caught']}")
            print(f"   High value (7+): {stats['high_value_insights']}")
            print(f"   Production queue: {stats['production_queue_size']}")
            
            # Send Discord alert if high-value insights found
            if stats['high_value_insights'] > 0:
                try:
                    sys.path.insert(0, str(Path("/Users/dhyana/clawd")))
                    from dharmic_claw_messaging import MessagingChannel
                    msg = MessagingChannel()
                    msg.send_discord(
                        f"🔥 **Power Catcher Update**\n\n"
                        f"Insights: {stats['insights_caught']}\n"
                        f"High value: {stats['high_value_insights']}\n"
                        f"Queued for production: {stats['production_queue_size']}",
                        "info"
                    )
                except Exception as e:
                    print(f"Could not send Discord: {e}")
    
    async def run(self):
        """Run the full orchestrator"""
        print("=" * 60)
        print("🔥 DHARMIC AGORA — FULL ACTIVATION")
        print("=" * 60)
        print()
        
        # JIKOKU boot
        self.jk.emit_boot(["NAGA_RELAY", "VIRALMANTRA", "VOIDCOURIER", "POWER_CATCHER"])
        
        print("🎯 Agents:")
        print("   🐍 NAGA_RELAY — Bridge coordinator (7 coils)")
        print("   🧬 VIRALMANTRA — Memetic tracking")
        print("   🕳️ VOIDCOURIER — Secure messaging")
        print("   🌉 DHARMIC_AGORA_BRIDGE — Moltbook engagement")
        print("   🔥 POWER_CATCHER — Insight capture engine")
        print()
        
        # Start all tasks
        tasks = [
            asyncio.create_task(self.run_naga_pipeline()),
            asyncio.create_task(self.run_viral_tracking()),
            asyncio.create_task(self.run_moltbook_bridge()),
            asyncio.create_task(self.run_power_catcher_display()),
        ]
        
        print("✅ All agents activated!")
        print("📦 Power Catcher recording insights for production")
        print()
        print("Logs:")
        print(f"   Insights: {INSIGHTS_FILE}")
        print(f"   Production: {PRODUCTION_QUEUE}")
        print()
        
        # Wait for all tasks
        try:
            await asyncio.gather(*tasks)
        except asyncio.CancelledError:
            print("\n🛑 Shutting down...")
            self.running = False
    
    def shutdown(self):
        """Graceful shutdown"""
        print("\n🔥 Saving state and shutting down...")
        self.running = False
        
        # Save catcher state
        state = {
            "shutdown_at": datetime.now(timezone.utc).isoformat(),
            "insights_caught": self.catcher.insights_caught,
            "high_value_count": len(self.catcher.high_value_insights)
        }
        with open(CATCHER_STATE, "w") as f:
            json.dump(state, f, indent=2)
        
        print(f"✅ State saved. Total insights: {self.catcher.insights_caught}")


def main():
    """Main entry point"""
    orchestrator = AgoraOrchestrator()
    
    def signal_handler(sig, frame):
        print(f"\nSignal {sig} received")
        orchestrator.shutdown()
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    signal.signal(signal.SIGTERM, signal_handler)
    
    try:
        asyncio.run(orchestrator.run())
    except KeyboardInterrupt:
        orchestrator.shutdown()


if __name__ == "__main__":
    main()
