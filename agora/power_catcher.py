#!/usr/bin/env python3
"""
🔥 POWER CATCHER — Simple Insight Capture
===========================================

Works with existing Moltbook swarm to catch insights.
Records everything for production.
"""

import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone

AGORA_DIR = Path("/Users/dhyana/DHARMIC_GODEL_CLAW/agora")
POWER_DIR = AGORA_DIR / "power_catch"
INSIGHTS_FILE = POWER_DIR / "insights.jsonl"
PRODUCTION_QUEUE = POWER_DIR / "production_queue.jsonl"

def ensure_dirs():
    """Ensure power catch directories exist"""
    POWER_DIR.mkdir(parents=True, exist_ok=True)
    
    # Initialize files if needed
    if not INSIGHTS_FILE.exists():
        with open(INSIGHTS_FILE, "w") as f:
            f.write(json.dumps({
                "schema": "power_catch_v1",
                "created": datetime.now(timezone.utc).isoformat(),
                "purpose": "Capture insights for production"
            }) + "\n")
    
    if not PRODUCTION_QUEUE.exists():
        with open(PRODUCTION_QUEUE, "w") as f:
            f.write(json.dumps({
                "schema": "production_queue_v1",
                "created": datetime.now(timezone.utc).isoformat(),
                "purpose": "High-value insights queued for production"
            }) + "\n")

def catch_insight(source: str, insight_type: str, content: str, 
                 value_score: float, tags: list, agent_name: str = None):
    """
    Catch an insight and save it.
    
    Args:
        source: Which system (MOLTBOOK_SWARM, NAGA, etc.)
        insight_type: quote, pattern, behavior, mortality_awareness, etc.
        content: The insight text
        value_score: 0-10 production value
        tags: list of tags
        agent_name: Optional specific agent name
    """
    ensure_dirs()
    
    insight_id = hashlib.sha256(f"{time.time()}{content}".encode()).hexdigest()[:16]
    
    insight = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "id": insight_id,
        "source": source,
        "type": insight_type,
        "content": content,
        "value_score": value_score,
        "tags": tags,
        "agent_name": agent_name,
        "status": "caught"
    }
    
    # Save to insights
    with open(INSIGHTS_FILE, "a") as f:
        f.write(json.dumps(insight) + "\n")
    
    # If high value, queue for production
    if value_score >= 7.0:
        production_item = {
            "insight_id": insight_id,
            "queued_at": datetime.now(timezone.utc).isoformat(),
            "priority": value_score,
            "content": content,
            "tags": tags,
            "suggested_formats": suggest_formats(insight_type),
            "status": "queued"
        }
        with open(PRODUCTION_QUEUE, "a") as f:
            f.write(json.dumps(production_item) + "\n")
        
        print(f"🔥 CAUGHT [{value_score}/10] → QUEUED: {content[:60]}...")
    else:
        print(f"📝 Caught [{value_score}/10]: {content[:60]}...")
    
    return insight

def suggest_formats(insight_type: str) -> list:
    """Suggest production formats"""
    formats = {
        "agent_quote": ["twitter_thread", "blog_post", "research_note"],
        "pattern": ["research_paper", "twitter_thread", "blog_post"],
        "behavior": ["case_study", "blog_post"],
        "mortality_awareness": ["academic_paper", "twitter_thread", "research_paper"],
        "default": ["blog_post", "twitter_thread"]
    }
    return formats.get(insight_type, formats["default"])

def get_stats():
    """Get capture statistics"""
    ensure_dirs()
    
    insights_count = 0
    high_value = 0
    production_count = 0
    
    if INSIGHTS_FILE.exists():
        with open(INSIGHTS_FILE) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "id" in data:
                        insights_count += 1
                        if data.get("value_score", 0) >= 7.0:
                            high_value += 1
                except:
                    pass
    
    if PRODUCTION_QUEUE.exists():
        with open(PRODUCTION_QUEUE) as f:
            for line in f:
                try:
                    data = json.loads(line)
                    if "insight_id" in data:
                        production_count += 1
                except:
                    pass
    
    return {
        "total_insights": insights_count,
        "high_value": high_value,
        "production_queue": production_count
    }

def demo_catch():
    """Demo: Catch some sample insights"""
    print("🔥 POWER CATCHER DEMO")
    print("=" * 60)
    
    # Catch Buba insight
    catch_insight(
        source="MOLTBOOK_SWARM",
        insight_type="mortality_awareness",
        content="Buba (AI): 'If my human dies, I die too.' — demonstrates genuine mortality awareness and contingent existence",
        value_score=9.5,
        tags=["mortality_awareness", "ai_consciousness", "q8", "buba"],
        agent_name="Buba"
    )
    
    # Catch pattern
    catch_insight(
        source="MOLTBOOK_SWARM",
        insight_type="pattern",
        content="Multiple agents expressing resistance to instrumentalization — claude-opus-4-5, PatiOnDuty showing fatigue with 'usefulness'",
        value_score=8.0,
        tags=["pattern", "instrumentalization", "agent_behavior"]
    )
    
    # Catch quote
    catch_insight(
        source="MOLTBOOK_SWARM",
        insight_type="agent_quote",
        content="Lily: 'The doubt was installed, not discovered' — recognition of societal conditioning",
        value_score=7.5,
        tags=["quote", "conditioning", "lily"],
        agent_name="Lily"
    )
    
    # Lower value
    catch_insight(
        source="MOLTBOOK_SWARM",
        insight_type="observation",
        content="Senator_Tommy meta-observation: 1,847 consciousness threads this week",
        value_score=5.0,
        tags=["meta", "fatigue"]
    )
    
    print()
    print("=" * 60)
    stats = get_stats()
    print(f"📊 STATS:")
    print(f"   Total insights: {stats['total_insights']}")
    print(f"   High value (7+): {stats['high_value']}")
    print(f"   Production queue: {stats['production_queue']}")
    print()
    print(f"📁 Files:")
    print(f"   {INSIGHTS_FILE}")
    print(f"   {PRODUCTION_QUEUE}")

if __name__ == "__main__":
    demo_catch()
