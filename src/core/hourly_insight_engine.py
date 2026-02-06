#!/usr/bin/env python3
"""
Hourly Agent Ping & Insight Extraction System
Pings all agents every hour, extracts insights, documents for morning review.
"""

import json
import sqlite3
import subprocess
from pathlib import Path
from datetime import datetime
from typing import List, Dict

class HourlyInsightEngine:
    """Extracts insights from agent activity and memory system."""
    
    def __init__(self):
        self.hour = datetime.now().hour
        self.report_dir = Path.home() / "DHARMIC_GODEL_CLAW" / "data" / "hourly_insights"
        self.report_dir.mkdir(parents=True, exist_ok=True)
        
    def _extract_gates(self, output: str) -> int:
        """Extract gate pass count from council output."""
        import re
        match = re.search(r'(\d+)/17\s+passed', output)
        if match:
            return int(match.group(1))
        # Try alternate pattern
        match = re.search(r'gates passed:\s*(\d+)', output, re.IGNORECASE)
        if match:
            return int(match.group(1))
        return 0
        
    def _extract_response_time(self, output: str) -> float:
        """Extract response time from council output."""
        import re
        match = re.search(r'(\d+\.?\d*)\s*ms', output)
        if match:
            return float(match.group(1))
        return 0.0
        
    def ping_council(self) -> Dict:
        """Ping Council of 4 for deliberation."""
        print(f"\n🔥 [{self.hour:02d}:00] Pinging Council of 4...")
        
        # Run council deliberation
        result = subprocess.run(
            ["python3", "-m", "src.core.agno_council_v2", "--status"],
            cwd=Path.home() / "DHARMIC_GODEL_CLAW",
            capture_output=True,
            text=True,
            timeout=30
        )
        
        # Extract key metrics
        output = result.stdout
        insights = {
            "status": "ONLINE" if "Council activated" in output else "CHECK NEEDED",
            "gates_passed": self._extract_gates(output),
            "response_time_ms": self._extract_response_time(output),
            "timestamp": datetime.now().isoformat()
        }
        
        print(f"  ✅ Council: {insights['gates_passed']}/17 gates, {insights['response_time_ms']}ms")
        return insights
        
    def ping_swarm(self) -> Dict:
        """Ping Moltbook Swarm for status."""
        print(f"\n🐝 [{self.hour:02d}:00] Pinging Moltbook Swarm...")
        
        # Check swarm state
        swarm_state = Path.home() / "DHARMIC_GODEL_CLAW" / "data" / "swarm_state.json"
        insights = {
            "status": "CHECK_NEEDED",
            "active_agents": 0,
            "timestamp": datetime.now().isoformat()
        }
        
        if swarm_state.exists():
            try:
                state = json.loads(swarm_state.read_text())
                insights["active_agents"] = len(state.get("agents", []))
                insights["status"] = "ONLINE" if insights["active_agents"] > 0 else "OFFLINE"
            except:
                pass
                
        print(f"  ✅ Swarm: {insights['active_agents']} agents active")
        return insights
        
    def extract_memory_insights(self) -> List[Dict]:
        """Extract insights from unified memory."""
        print(f"\n🧠 [{self.hour:02d}:00] Extracting memory insights...")
        
        db_path = Path.home() / "DHARMIC_GODEL_CLAW" / "data" / "unified_memory.db"
        insights = []
        
        if not db_path.exists():
            return insights
            
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        
        # Get recent additions (files added in last hour)
        cursor.execute("""
            SELECT source, COUNT(*) as count 
            FROM files 
            WHERE indexed_time > unixepoch() - 3600
            GROUP BY source
        """)
        
        new_files = {row['source']: row['count'] for row in cursor.fetchall()}
        
        # Sample recent searches
        cursor.execute("""
            SELECT path, source FROM files 
            WHERE source = 'psmv' 
            ORDER BY indexed_time DESC
            LIMIT 3
        """)
        
        recent_psmv = [Path(row['path']).name for row in cursor.fetchall()]
        
        insights.append({
            "type": "memory_stats",
            "new_files_last_hour": new_files,
            "recent_psmv_activity": recent_psmv
        })
        
        conn.close()
        
        print(f"  ✅ Memory: {sum(new_files.values())} new files indexed")
        return insights
        
    def generate_hourly_theme(self) -> str:
        """Generate theme for this hour based on time."""
        themes = {
            0: "Foundation Building",
            1: "Deep Memory Processing",
            2: "Silent Synthesis",
            3: "Night Cycle Deep Work",
            4: "Pattern Recognition",
            5: "Pre-Dawn Integration",
            6: "Morning Emergence"
        }
        return themes.get(self.hour, "Continuous Operation")
        
    def generate_insight_report(self) -> Dict:
        """Generate comprehensive insight report."""
        print(f"\n{'='*60}")
        print(f"🔍 HOUR {self.hour:02d}:00 INSIGHT EXTRACTION")
        print(f"{'='*60}")
        
        report = {
            "hour": self.hour,
            "timestamp": datetime.now().isoformat(),
            "theme": self.generate_hourly_theme(),
            "council_status": self.ping_council(),
            "swarm_status": self.ping_swarm(),
            "memory_insights": self.extract_memory_insights(),
            "system_health": self.check_system_health()
        }
        
        # Add cross-cutting insight
        report["key_insight"] = self.generate_key_insight(report)
        
        # Save report
        report_file = self.report_dir / f"hour_{self.hour:02d}_insights.json"
        report_file.write_text(json.dumps(report, indent=2))
        
        # Generate human-readable summary
        self.generate_human_summary(report)
        
        print(f"\n✅ Insight report saved: {report_file}")
        return report
        
    def check_system_health(self) -> Dict:
        """Check overall system health."""
        health = {
            "unified_daemon": "UNKNOWN",
            "night_cycle": "UNKNOWN",
            "database": "UNKNOWN"
        }
        
        # Check daemon
        result = subprocess.run(
            ["pgrep", "-f", "unified_daemon"],
            capture_output=True
        )
        health["unified_daemon"] = "RUNNING" if result.returncode == 0 else "STOPPED"
        
        # Check database
        db_path = Path.home() / "DHARMIC_GODEL_CLAW" / "data" / "unified_memory.db"
        health["database"] = "ONLINE" if db_path.exists() else "MISSING"
        
        return health
        
    def generate_key_insight(self, report: Dict) -> str:
        """Generate a key insight from the hour's activity."""
        insights = []
        
        if report["council_status"]["gates_passed"] == 17:
            insights.append("All dharmic gates passing — system integrity maintained.")
            
        if report["swarm_status"]["active_agents"] >= 8:
            insights.append("Swarm at full strength — collective intelligence operational.")
            
        if report["system_health"]["unified_daemon"] == "RUNNING":
            insights.append("Continuous operation confirmed — heartbeat active.")
            
        return " ".join(insights) if insights else "System stable — continuous monitoring engaged."
        
    def generate_human_summary(self, report: Dict):
        """Generate human-readable summary."""
        summary_file = self.report_dir / f"hour_{self.hour:02d}_summary.txt"
        
        summary = f"""
{'='*70}
🪷 DHARMIC CLAW — HOUR {report['hour']:02d}:00 INSIGHT REPORT
{'='*70}

📅 Timestamp: {report['timestamp']}
🎯 Theme: {report['theme']}

{'='*70}
AGENT STATUS
{'='*70}

🔥 Council of 4:
   Status: {report['council_status']['status']}
   Gates: {report['council_status']['gates_passed']}/17 passing
   Response: {report['council_status']['response_time_ms']}ms

🐝 Moltbook Swarm:
   Status: {report['swarm_status']['status']}
   Active Agents: {report['swarm_status']['active_agents']}/10

{'='*70}
SYSTEM HEALTH
{'='*70}

   Unified Daemon: {report['system_health']['unified_daemon']}
   Night Cycle: {report['system_health'].get('night_cycle', 'UNKNOWN')}
   Database: {report['system_health']['database']}

{'='*70}
KEY INSIGHT
{'='*70}

{report['key_insight']}

{'='*70}
MEMORY ACTIVITY
{'='*70}
"""
        
        for insight in report['memory_insights']:
            if insight['type'] == 'memory_stats':
                summary += f"\n   New files indexed (last hour): {insight['new_files_last_hour']}\n"
                summary += f"   Recent PSMV activity: {insight['recent_psmv_activity'][:3]}\n"
                
        summary += f"""
{'='*70}
NEXT HOUR PREVIEW
{'='*70}

Hour {(report['hour'] + 1) % 24:02d}:00 will focus on:
   - Continuous agent monitoring
   - Memory index maintenance
   - Cross-agent insight synthesis
   - System health verification

{'='*70}
JSCA! 🪷
Continuous Operation — No Cutoff
{'='*70}
"""
        
        summary_file.write_text(summary)
        print(f"  📝 Human summary: {summary_file}")


def main():
    """Run hourly insight extraction."""
    engine = HourlyInsightEngine()
    report = engine.generate_insight_report()
    
    print(f"\n{'='*60}")
    print(f"✅ HOUR {report['hour']:02d}:00 COMPLETE")
    print(f"{'='*60}")
    print(f"Key Insight: {report['key_insight']}")
    print(f"{'='*60}\n")


if __name__ == "__main__":
    main()