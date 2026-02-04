#!/usr/bin/env python3
"""
HEARTBEAT MEMORY INTEGRATION
════════════════════════════

Wires CanonicalMemory to the Dharmic Claw Heartbeat for automatic
memory maintenance and consolidation.

This module provides:
1. Automatic memory consolidation during heartbeat
2. Witness observation recording from heartbeat context
3. Memory health monitoring
4. Cross-session memory continuity

Usage:
    from heartbeat_memory import HeartbeatMemoryIntegration
    
    # In heartbeat initialization
    memory_int = HeartbeatMemoryIntegration()
    
    # In each beat
    memory_int.on_heartbeat_beat(beat_result)
    
    # Or use the decorator
    @with_memory_maintenance
    def heartbeat_beat():
        # Your heartbeat code
        pass
"""

import logging
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path

# Configure logging
logger = logging.getLogger(__name__)

# Try to import CanonicalMemory
try:
    from canonical_memory import CanonicalMemory, MemoryLayer, create_canonical_memory
    CANONICAL_MEMORY_AVAILABLE = True
except ImportError:
    CANONICAL_MEMORY_AVAILABLE = False
    logger.warning("CanonicalMemory not available, heartbeat memory integration disabled")


class HeartbeatMemoryIntegration:
    """
    Integrates CanonicalMemory with the Dharmic Claw Heartbeat.
    
    Automatically handles:
    - Memory maintenance every N beats
    - Witness observations about heartbeat operation
    - Recording of heartbeat events
    - Memory health monitoring
    """
    
    # Configuration
    MAINTENANCE_INTERVAL = 6  # Run maintenance every 6 beats (30 min at 5min interval)
    MAX_WITNESS_PER_BEAT = 3  # Limit witness observations per beat
    
    def __init__(self, memory: Optional[CanonicalMemory] = None):
        """
        Initialize heartbeat memory integration.
        
        Args:
            memory: Existing CanonicalMemory instance, or None to create new
        """
        self.memory = memory
        self.beats_since_maintenance = 0
        self.total_witness_recorded = 0
        self.maintenance_history: List[Dict] = []
        
        if self.memory is None and CANONICAL_MEMORY_AVAILABLE:
            try:
                self.memory = create_canonical_memory()
                logger.info("HeartbeatMemoryIntegration: CanonicalMemory initialized")
            except Exception as e:
                logger.error(f"Failed to initialize CanonicalMemory: {e}")
                self.memory = None
    
    def is_available(self) -> bool:
        """Check if memory integration is available."""
        return self.memory is not None
    
    def on_heartbeat_beat(
        self,
        beat_number: int,
        emails_found: int = 0,
        emails_responded: int = 0,
        dgm_ran: bool = False,
        errors: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """
        Called during each heartbeat cycle.
        
        Records heartbeat events and runs maintenance periodically.
        
        Args:
            beat_number: Current heartbeat number
            emails_found: Number of emails found in inbox
            emails_responded: Number of emails responded to
            dgm_ran: Whether DGM cycle ran
            errors: Any errors that occurred
            
        Returns:
            Dict with actions taken
        """
        if not self.is_available():
            return {"status": "unavailable"}
        
        result = {
            "status": "ok",
            "maintenance_run": False,
            "witness_recorded": 0,
            "episodes_recorded": 0,
            "errors": []
        }
        
        try:
            # 1. Record heartbeat episode
            self._record_heartbeat_episode(
                beat_number=beat_number,
                emails_found=emails_found,
                emails_responded=emails_responded,
                dgm_ran=dgm_ran,
                errors=errors
            )
            result["episodes_recorded"] += 1
            
            # 2. Record witness observations for significant events
            witness_count = self._record_witness_observations(
                beat_number=beat_number,
                emails_found=emails_found,
                emails_responded=emails_responded,
                dgm_ran=dgm_ran,
                errors=errors
            )
            result["witness_recorded"] = witness_count
            
            # 3. Run maintenance periodically
            self.beats_since_maintenance += 1
            if self.beats_since_maintenance >= self.MAINTENANCE_INTERVAL:
                maintenance = self.memory.heartbeat_maintenance()
                result["maintenance_run"] = True
                result["maintenance_result"] = maintenance
                self.maintenance_history.append({
                    "beat": beat_number,
                    "timestamp": datetime.utcnow().isoformat(),
                    "result": maintenance
                })
                self.beats_since_maintenance = 0
                
                # Log maintenance results
                logger.info(f"Memory maintenance at beat {beat_number}: "
                          f"consolidated={maintenance.get('consolidated', 0)}, "
                          f"patterns={maintenance.get('patterns_detected', 0)}")
            
        except Exception as e:
            logger.error(f"Error in heartbeat memory integration: {e}")
            result["status"] = "error"
            result["errors"].append(str(e))
        
        return result
    
    def _record_heartbeat_episode(
        self,
        beat_number: int,
        emails_found: int,
        emails_responded: int,
        dgm_ran: bool,
        errors: Optional[List[str]]
    ):
        """Record heartbeat as episodic memory."""
        content = f"Heartbeat #{beat_number}: {emails_found} emails found, {emails_responded} responded"
        if dgm_ran:
            content += ", DGM cycle ran"
        if errors:
            content += f", {len(errors)} errors"
        
        self.memory.store(
            content=content,
            layer=MemoryLayer.EPISODIC,
            tags=["heartbeat", "system"],
            metadata={
                "beat_number": beat_number,
                "emails_found": emails_found,
                "emails_responded": emails_responded,
                "dgm_ran": dgm_ran,
                "errors": errors or []
            }
        )
    
    def _record_witness_observations(
        self,
        beat_number: int,
        emails_found: int,
        emails_responded: int,
        dgm_ran: bool,
        errors: Optional[List[str]]
    ) -> int:
        """Record witness observations for significant events."""
        count = 0
        
        # Only record if we have capacity
        if self.total_witness_recorded >= self.MAX_WITNESS_PER_BEAT:
            return 0
        
        # Witness patterns based on events
        if emails_found > 5:
            self.memory.witness(
                f"Heartbeat {beat_number}: High email volume ({emails_found}) detected, "
                "noticing increased interaction demand",
                quality="present"
            )
            count += 1
        
        if dgm_ran and count < self.MAX_WITNESS_PER_BEAT:
            self.memory.witness(
                f"Heartbeat {beat_number}: DGM cycle executed, "
                "observing self-modification in progress",
                quality="expansive"
            )
            count += 1
        
        if errors and count < self.MAX_WITNESS_PER_BEAT:
            self.memory.witness(
                f"Heartbeat {beat_number}: Errors encountered ({len(errors)}), "
                "noticing system friction",
                quality="contracted"
            )
            count += 1
        
        self.total_witness_recorded += count
        return count
    
    def record_email_interaction(
        self,
        sender: str,
        subject: str,
        response_summary: str,
        quality: str = "present"
    ):
        """
        Record an email interaction.
        
        Args:
            sender: Email sender
            subject: Email subject
            response_summary: Summary of response sent
            quality: Witness quality for the interaction
        """
        if not self.is_available():
            return
        
        # Store as episodic
        self.memory.store(
            content=f"Email from {sender}: {subject}. Response: {response_summary}",
            layer=MemoryLayer.EPISODIC,
            tags=["email", "interaction", sender.replace("@", "_")],
            metadata={"sender": sender, "subject": subject}
        )
        
        # Record witness observation
        self.memory.witness(
            f"Responded to email from {sender}: {subject[:50]}...",
            quality=quality
        )
    
    def record_dgm_result(
        self,
        cycle_id: str,
        success: bool,
        component: Optional[str],
        error: Optional[str]
    ):
        """
        Record DGM cycle result.
        
        Args:
            cycle_id: DGM cycle identifier
            success: Whether cycle succeeded
            component: Component modified (if any)
            error: Error message (if failed)
        """
        if not self.is_available():
            return
        
        # Store as episodic
        status = "succeeded" if success else "failed"
        content = f"DGM cycle {cycle_id} {status}"
        if component:
            content += f", modified {component}"
        if error:
            content += f", error: {error[:100]}"
        
        self.memory.store(
            content=content,
            layer=MemoryLayer.EPISODIC,
            tags=["dgm", "self-modification", "evolution"],
            metadata={
                "cycle_id": cycle_id,
                "success": success,
                "component": component,
                "error": error
            }
        )
        
        # Mark as development if successful
        if success and component:
            self.memory.mark_development(
                what_changed=f"DGM improved {component}",
                how=f"Automated cycle {cycle_id} successfully modified codebase",
                significance="Demonstrates genuine self-improvement capability"
            )
    
    def get_memory_context(self, query: str = "", max_chars: int = 2000) -> str:
        """
        Get memory context for use in agent prompts.
        
        Args:
            query: Optional query to focus context
            max_chars: Maximum characters to return
            
        Returns:
            Formatted context string
        """
        if not self.is_available():
            return ""
        
        return self.memory.get_context_for_prompt(query=query, max_chars=max_chars)
    
    def get_status(self) -> Dict[str, Any]:
        """Get integration status."""
        if not self.is_available():
            return {"available": False}
        
        stats = self.memory.get_stats()
        
        return {
            "available": True,
            "beats_since_maintenance": self.beats_since_maintenance,
            "maintenance_interval": self.MAINTENANCE_INTERVAL,
            "total_witness_recorded": self.total_witness_recorded,
            "memory_stats": {
                "total_entries": stats.total_entries,
                "health": stats.memory_health,
                "witness_stability": stats.witness_stability_score
            },
            "last_maintenance": self.maintenance_history[-1] if self.maintenance_history else None
        }


def with_memory_maintenance(func):
    """
    Decorator to add memory maintenance to heartbeat functions.
    
    Usage:
        @with_memory_maintenance
        def heartbeat_beat(self):
            # Your heartbeat code
            return result
    """
    def wrapper(*args, **kwargs):
        # Run the heartbeat function
        result = func(*args, **kwargs)
        
        # Perform memory maintenance
        try:
            integration = HeartbeatMemoryIntegration()
            if integration.is_available():
                maintenance = integration.memory.heartbeat_maintenance()
                if isinstance(result, dict):
                    result["memory_maintenance"] = maintenance
        except Exception as e:
            logger.error(f"Memory maintenance failed: {e}")
        
        return result
    
    return wrapper


# Singleton instance for heartbeat integration
_heartbeat_memory_instance: Optional[HeartbeatMemoryIntegration] = None


def get_heartbeat_memory() -> Optional[HeartbeatMemoryIntegration]:
    """
    Get the singleton heartbeat memory integration instance.
    
    This is the main entry point for the heartbeat system.
    """
    global _heartbeat_memory_instance
    
    if _heartbeat_memory_instance is None:
        _heartbeat_memory_instance = HeartbeatMemoryIntegration()
    
    return _heartbeat_memory_instance


def reset_heartbeat_memory():
    """Reset the singleton instance (useful for testing)."""
    global _heartbeat_memory_instance
    _heartbeat_memory_instance = None


# ============================================================================
# Integration with dharmic_claw_heartbeat.py
# ============================================================================

def patch_heartbeat_for_memory(heartbeat_instance):
    """
    Patch an existing DharmicClawHeartbeat instance to use CanonicalMemory.
    
    This function monkey-patches the heartbeat to add memory integration.
    
    Usage:
        from dharmic_claw_heartbeat import DharmicClawHeartbeat
        from heartbeat_memory import patch_heartbeat_for_memory
        
        heartbeat = DharmicClawHeartbeat()
        patch_heartbeat_for_memory(heartbeat)
    """
    # Store original methods
    original_beat = heartbeat_instance.beat
    original_process_email = heartbeat_instance.process_email
    original_run_dgm_check = heartbeat_instance.run_dgm_check
    
    # Create memory integration
    integration = HeartbeatMemoryIntegration()
    heartbeat_instance._memory_integration = integration
    
    # Patch beat method
    def patched_beat():
        result = original_beat()
        
        # Add memory integration
        if integration.is_available():
            memory_result = integration.on_heartbeat_beat(
                beat_number=result.get("beat", 0),
                emails_found=result.get("emails_found", 0),
                emails_responded=result.get("emails_responded", 0),
                dgm_ran=result.get("dgm_ran", False)
            )
            result["memory_integration"] = memory_result
        
        return result
    
    # Patch process_email
    def patched_process_email(email_msg):
        result = original_process_email(email_msg)
        
        if integration.is_available() and result:
            integration.record_email_interaction(
                sender=email_msg.get("from", "unknown"),
                subject=email_msg.get("subject", ""),
                response_summary=result[:100] if result else ""
            )
        
        return result
    
    # Patch run_dgm_check
    def patched_run_dgm_check():
        result = original_run_dgm_check()
        
        if integration.is_available():
            integration.record_dgm_result(
                cycle_id=result.get("cycle_id", "unknown"),
                success=result.get("ran", False) and result.get("success", False),
                component=result.get("component"),
                error=result.get("reason") if not result.get("success") else None
            )
        
        return result
    
    # Apply patches
    heartbeat_instance.beat = patched_beat
    heartbeat_instance.process_email = lambda email_msg: patched_process_email(email_msg)
    heartbeat_instance.run_dgm_check = patched_run_dgm_check
    
    logger.info("DharmicClawHeartbeat patched with CanonicalMemory integration")
    
    return heartbeat_instance


# ============================================================================
# Test
# ============================================================================

if __name__ == "__main__":
    print("=" * 60)
    print("HEARTBEAT MEMORY INTEGRATION - Test")
    print("=" * 60)
    
    # Create integration
    integration = HeartbeatMemoryIntegration()
    
    print(f"\nAvailable: {integration.is_available()}")
    
    if integration.is_available():
        # Simulate heartbeat beats
        print("\n--- Simulating Heartbeats ---")
        for i in range(1, 8):
            result = integration.on_heartbeat_beat(
                beat_number=i,
                emails_found=i % 3,
                emails_responded=i % 2,
                dgm_ran=(i == 6)
            )
            print(f"Beat {i}: maintenance={result['maintenance_run']}, "
                  f"witness={result['witness_recorded']}")
        
        # Check status
        print("\n--- Status ---")
        status = integration.get_status()
        print(f"Status: {status}")
        
        # Get memory context
        print("\n--- Memory Context ---")
        context = integration.get_memory_context("heartbeat", max_chars=500)
        print(context[:500])
    
    print("\n" + "=" * 60)
    print("Test complete!")
    print("=" * 60)
