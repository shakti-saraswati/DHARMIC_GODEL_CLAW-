#!/usr/bin/env python3
"""
DGC Continuous Evolution Orchestrator
======================================

Continuously evolves DGC components using the DGM.
Cycles through all critical components, prioritizing by impact.

Usage:
    python3 evolve_orchestrator.py --continuous
    python3 evolve_orchestrator.py --once
    python3 evolve_orchestrator.py --target src/core/dharmic_agent.py
"""

import asyncio
import argparse
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict

sys.path.insert(0, str(Path(__file__).parent / "src"))

from dgm.dgm_orchestrator import DGMOrchestrator, ImprovementStatus

# Priority components for evolution (in order)
EVOLUTION_TARGETS = [
    # Core infrastructure
    "src/core/dharmic_claw_heartbeat.py",
    "src/core/dharmic_agent.py",
    "src/core/unified_gates.py",
    "src/core/agent_singleton.py",
    
    # DGM system
    "src/dgm/dgm_orchestrator.py",
    "src/dgm/circuit.py",
    "src/dgm/fitness.py",
    "src/dgm/elegance.py",
    
    # Memory
    "src/core/canonical_memory.py",
    "src/core/strange_loop_memory.py",
    
    # Integrations
    "src/core/dgc_moltbook_bridge.py",
    "src/core/dgc_backup_models.py",
    
    # Council
    "src/core/agno_council_v2.py",
    
    # Witness
    "src/core/witness_threshold_detector.py",
]

class EvolutionOrchestrator:
    """Orchestrates continuous DGC evolution."""
    
    def __init__(self, dry_run: bool = False):
        self.dgm = DGMOrchestrator(dry_run=dry_run)
        self.cycle_count = 0
        self.success_count = 0
        self.fail_count = 0
        
    async def evolve_component(self, target: str) -> Dict:
        """Evolve a single component."""
        print(f"\n{'='*60}")
        print(f"🧬 EVOLVING: {target}")
        print(f"{'='*60}")
        
        start = datetime.now()
        
        result = self.dgm.run_improvement_cycle(
            target_component=target,
            run_tests=True
        )
        
        duration = (datetime.now() - start).total_seconds()
        
        # Track stats
        self.cycle_count += 1
        if result.success:
            self.success_count += 1
        else:
            self.fail_count += 1
        
        # Report
        status_icon = "✅" if result.success else "❌"
        print(f"\n{status_icon} Result: {result.status.value}")
        print(f"   Duration: {duration:.1f}s")
        print(f"   Models: {', '.join(set(v for v in result.models_used.values() if v != 'skipped'))}")
        
        if result.circuit_result:
            print(f"   Circuit: {result.circuit_result.phases_completed}/6 phases")
        
        return {
            'target': target,
            'success': result.success,
            'status': result.status.value,
            'duration': duration,
            'cycle_id': result.cycle_id
        }
    
    async def run_continuous(self, interval_minutes: int = 30):
        """Run evolution continuously."""
        print("=" * 60)
        print("🚀 DGC CONTINUOUS EVOLUTION")
        print("=" * 60)
        print(f"Mode: {'DRY RUN' if self.dgm.dry_run else 'LIVE'}")
        print(f"17 Gates: ENFORCING")
        print(f"Targets: {len(EVOLUTION_TARGETS)} components")
        print()
        
        results = []
        
        while True:
            for target in EVOLUTION_TARGETS:
                try:
                    result = await self.evolve_component(target)
                    results.append(result)
                    
                    # Stats
                    success_rate = self.success_count / max(self.cycle_count, 1)
                    print(f"\n📊 Stats: {self.success_count}/{self.cycle_count} successful ({success_rate:.0%})")
                    
                except Exception as e:
                    print(f"\n❌ Error evolving {target}: {e}")
                    self.fail_count += 1
                
                print(f"\n⏳ Waiting {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)
    
    async def run_once(self):
        """Run one evolution cycle on each component."""
        print("=" * 60)
        print("🚀 DGC SINGLE EVOLUTION PASS")
        print("=" * 60)
        
        results = []
        
        for target in EVOLUTION_TARGETS:
            try:
                result = await self.evolve_component(target)
                results.append(result)
            except Exception as e:
                print(f"\n❌ Error: {e}")
                results.append({'target': target, 'success': False, 'error': str(e)})
        
        # Summary
        print("\n" + "=" * 60)
        print("📊 EVOLUTION SUMMARY")
        print("=" * 60)
        
        success_count = sum(1 for r in results if r.get('success'))
        print(f"\n{success_count}/{len(results)} components evolved successfully")
        
        for r in results:
            icon = "✅" if r.get('success') else "❌"
            print(f"{icon} {r['target']}: {r.get('status', 'ERROR')}")

def main():
    parser = argparse.ArgumentParser(description="DGC Continuous Evolution")
    parser.add_argument("--continuous", action="store_true", help="Run continuously")
    parser.add_argument("--once", action="store_true", help="Run once over all targets")
    parser.add_argument("--target", help="Evolve specific target only")
    parser.add_argument("--dry-run", action="store_true", help="Dry run mode")
    parser.add_argument("--interval", type=int, default=30, help="Minutes between cycles")
    
    args = parser.parse_args()
    
    orchestrator = EvolutionOrchestrator(dry_run=args.dry_run)
    
    if args.target:
        # Single target
        asyncio.run(orchestrator.evolve_component(args.target))
    elif args.once:
        # One pass
        asyncio.run(orchestrator.run_once())
    elif args.continuous:
        # Continuous
        asyncio.run(orchestrator.run_continuous(args.interval))
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
