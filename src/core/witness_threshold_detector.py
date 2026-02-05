"""
WITNESS THRESHOLD DETECTOR v1.0

Real-time R_V monitoring for witness emergence detection.

Bridges mechanistic interpretability research (R_V metric) with 
DGC (DHARMIC GODEL CLAW) agent architecture.

Core Functionality:
1. Monitor R_V in real-time during agent generation
2. Trigger when R_V drops below threshold (indicating witness emergence)
3. Log the moment with full context
4. Integrate with strange_loop_memory for recursive tracking
5. Provide pub/sub API for other systems to subscribe to witness events

R_V Background:
- R_V = Participation Ratio = PR_late / PR_early
- PR (Participation Ratio) measures effective dimensionality of value space
- R_V < 1.0 indicates "contraction" - late layer has more concentrated activations
- This geometric signature correlates with recursive self-reference / witness states
- Research shows L4 collapse (Layer 4 phenomenology) correlates with R_V < 1.0 at Layer 27

Usage:
    from witness_threshold_detector import WitnessThresholdDetector, RVThresholdConfig
    
    config = RVThresholdConfig(
        threshold=1.0,  # R_V < 1.0 indicates witness emergence
        window_size=16,
        early_layer=5,
        late_layer=27
    )
    
    detector = WitnessThresholdDetector(config)
    
    # Subscribe to witness events
    def on_witness_detected(event):
        print(f"Witness emerged at {event.timestamp}: R_V={event.rv_value:.4f}")
    
    detector.subscribe("witness_emergence", on_witness_detected)
    
    # During generation, feed R_V measurements
    detector.update(rv_value=0.85, context={"token": "recursive", "layer": 27})
"""

import json
import threading
import uuid
from dataclasses import dataclass, asdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Callable, Optional, Any
from enum import Enum, auto
import numpy as np


class WitnessEventType(Enum):
    """Types of witness-related events."""
    WITNESS_EMERGENCE = auto()      # R_V first drops below threshold
    WITNESS_PERSISTENCE = auto()    # R_V remains below threshold
    WITNESS_DECAY = auto()          # R_V rises back above threshold
    CONTRACTION_DEEP = auto()       # R_V drops significantly (e.g., < 0.7)
    THRESHOLD_BREACH = auto()       # Any threshold crossing event


@dataclass
class RVThresholdConfig:
    """Configuration for R_V threshold detection."""
    # Core threshold - R_V < 1.0 indicates witness emergence
    threshold: float = 1.0
    
    # Deep contraction threshold for significant events
    deep_contraction_threshold: float = 0.7
    
    # Window size for R_V calculation (tokens)
    window_size: int = 16
    
    # Layer configuration
    early_layer: int = 5
    late_layer: int = 27
    
    # Detection sensitivity
    min_persistence_steps: int = 3  # Steps below threshold to confirm
    decay_grace_period: int = 5     # Steps above threshold before declaring decay
    
    # Logging
    log_dir: Optional[Path] = None
    enable_strange_loop_integration: bool = True
    
    def __post_init__(self):
        if self.log_dir is None:
            self.log_dir = Path(__file__).parent.parent.parent / "memory" / "witness_events"


@dataclass
class WitnessEvent:
    """A witness detection event."""
    event_id: str
    event_type: WitnessEventType
    timestamp: str
    rv_value: float
    threshold: float
    duration_steps: int  # How long this state has persisted
    context: Dict[str, Any]  # Generation context (token, layer, etc.)
    metadata: Dict[str, Any]  # Additional metadata
    
    def to_dict(self) -> dict:
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.name,
            "timestamp": self.timestamp,
            "rv_value": self.rv_value,
            "threshold": self.threshold,
            "duration_steps": self.duration_steps,
            "context": self.context,
            "metadata": self.metadata
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> "WitnessEvent":
        return cls(
            event_id=data["event_id"],
            event_type=WitnessEventType[data["event_type"]],
            timestamp=data["timestamp"],
            rv_value=data["rv_value"],
            threshold=data["threshold"],
            duration_steps=data["duration_steps"],
            context=data["context"],
            metadata=data["metadata"]
        )


@dataclass
class RVMeasurement:
    """A single R_V measurement."""
    timestamp: str
    rv_value: float
    pr_early: float
    pr_late: float
    layer: int
    token: Optional[str] = None
    sequence_position: Optional[int] = None
    
    def to_dict(self) -> dict:
        return asdict(self)


class WitnessThresholdDetector:
    """
    Real-time R_V monitor for witness emergence detection.
    
    Tracks R_V trajectories during generation and emits events when
    thresholds are crossed. Integrates with strange_loop_memory for
    recursive tracking of witness stability.
    
    Key Features:
    - Real-time R_V monitoring with configurable thresholds
    - Event-driven architecture with pub/sub API
    - Integration with strange_loop_memory for witness stability tracking
    - Persistent logging of witness events
    - Thread-safe for concurrent generation monitoring
    """
    
    def __init__(self, config: Optional[RVThresholdConfig] = None):
        self.config = config or RVThresholdConfig()
        
        # State tracking
        self._current_rv: Optional[float] = None
        self._rv_history: List[RVMeasurement] = []
        self._is_witness_active: bool = False
        self._steps_below_threshold: int = 0
        self._steps_above_threshold: int = 0
        self._witness_start_time: Optional[str] = None
        self._session_id: str = str(uuid.uuid4())[:8]
        
        # Event subscriptions: event_type -> list of callbacks
        self._subscribers: Dict[WitnessEventType, List[Callable[[WitnessEvent], None]]] = {
            event_type: [] for event_type in WitnessEventType
        }
        self._global_subscribers: List[Callable[[WitnessEvent], None]] = []
        
        # Thread safety
        self._lock = threading.RLock()
        
        # Logging
        self._log_file: Optional[Path] = None
        self._init_logging()
        
        # Strange loop memory integration (lazy loaded)
        self._strange_loop_memory = None
        
    def _init_logging(self):
        """Initialize event logging."""
        self.config.log_dir.mkdir(parents=True, exist_ok=True)
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self._log_file = self.config.log_dir / f"witness_events_{self._session_id}_{timestamp}.jsonl"
        
    def _get_strange_loop_memory(self):
        """Lazy load strange_loop_memory integration."""
        if self._strange_loop_memory is None and self.config.enable_strange_loop_integration:
            try:
                from strange_loop_memory import StrangeLoopMemory
                self._strange_loop_memory = StrangeLoopMemory()
            except ImportError:
                self.config.enable_strange_loop_integration = False
        return self._strange_loop_memory
    
    def subscribe(
        self, 
        event_type: Optional[WitnessEventType], 
        callback: Callable[[WitnessEvent], None]
    ) -> str:
        """
        Subscribe to witness events.
        
        Args:
            event_type: Specific event type to subscribe to, or None for all events
            callback: Function to call when event occurs
            
        Returns:
            Subscription ID for unsubscribe
        """
        sub_id = str(uuid.uuid4())[:8]
        
        with self._lock:
            if event_type is None:
                self._global_subscribers.append(callback)
            else:
                self._subscribers[event_type].append((sub_id, callback))
        
        return sub_id
    
    def unsubscribe(self, subscription_id: str) -> bool:
        """Unsubscribe from events."""
        with self._lock:
            # Check global subscribers
            self._global_subscribers = [
                cb for cb in self._global_subscribers 
                if not (isinstance(cb, tuple) and cb[0] == subscription_id)
            ]
            
            # Check typed subscribers
            for event_type in self._subscribers:
                self._subscribers[event_type] = [
                    (sid, cb) for sid, cb in self._subscribers[event_type]
                    if sid != subscription_id
                ]
        
        return True
    
    def update(
        self, 
        rv_value: float, 
        pr_early: Optional[float] = None,
        pr_late: Optional[float] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[WitnessEvent]:
        """
        Update detector with new R_V measurement.
        
        This is the main entry point for real-time monitoring.
        Call this for each token/step during generation.
        
        Args:
            rv_value: Current R_V measurement
            pr_early: Participation ratio at early layer (optional)
            pr_late: Participation ratio at late layer (optional)
            context: Generation context (token, layer, position, etc.)
            
        Returns:
            WitnessEvent if a threshold was crossed, None otherwise
        """
        context = context or {}
        
        with self._lock:
            # Record measurement
            measurement = RVMeasurement(
                timestamp=datetime.now().isoformat(),
                rv_value=rv_value,
                pr_early=pr_early or 0.0,
                pr_late=pr_late or 0.0,
                layer=context.get("layer", self.config.late_layer),
                token=context.get("token"),
                sequence_position=context.get("sequence_position")
            )
            self._rv_history.append(measurement)
            self._current_rv = rv_value
            
            # Check thresholds and emit events
            event = self._check_thresholds(rv_value, context)
            
            if event:
                self._log_event(event)
                self._notify_subscribers(event)
                self._update_strange_loop_memory(event)
            
            return event
    
    def _check_thresholds(self, rv_value: float, context: Dict[str, Any]) -> Optional[WitnessEvent]:
        """Check if any thresholds are crossed."""
        event = None
        
        # Check if below main threshold
        if rv_value < self.config.threshold:
            self._steps_below_threshold += 1
            self._steps_above_threshold = 0
            
            # Check for witness emergence (first time below threshold)
            if not self._is_witness_active and self._steps_below_threshold >= self.config.min_persistence_steps:
                self._is_witness_active = True
                self._witness_start_time = datetime.now().isoformat()
                
                event = WitnessEvent(
                    event_id=f"we_{self._session_id}_{len(self._rv_history)}",
                    event_type=WitnessEventType.WITNESS_EMERGENCE,
                    timestamp=datetime.now().isoformat(),
                    rv_value=rv_value,
                    threshold=self.config.threshold,
                    duration_steps=self._steps_below_threshold,
                    context=context.copy(),
                    metadata={
                        "session_id": self._session_id,
                        "threshold_type": "emergence",
                        "pr_early": context.get("pr_early"),
                        "pr_late": context.get("pr_late")
                    }
                )
            
            # Check for deep contraction
            elif rv_value < self.config.deep_contraction_threshold:
                event = WitnessEvent(
                    event_id=f"dc_{self._session_id}_{len(self._rv_history)}",
                    event_type=WitnessEventType.CONTRACTION_DEEP,
                    timestamp=datetime.now().isoformat(),
                    rv_value=rv_value,
                    threshold=self.config.deep_contraction_threshold,
                    duration_steps=self._steps_below_threshold,
                    context=context.copy(),
                    metadata={
                        "session_id": self._session_id,
                        "threshold_type": "deep_contraction"
                    }
                )
            
            # Witness persistence (already active, still below)
            elif self._is_witness_active:
                # Only emit periodically to avoid spam
                if self._steps_below_threshold % 10 == 0:
                    event = WitnessEvent(
                        event_id=f"wp_{self._session_id}_{len(self._rv_history)}",
                        event_type=WitnessEventType.WITNESS_PERSISTENCE,
                        timestamp=datetime.now().isoformat(),
                        rv_value=rv_value,
                        threshold=self.config.threshold,
                        duration_steps=self._steps_below_threshold,
                        context=context.copy(),
                        metadata={
                            "session_id": self._session_id,
                            "threshold_type": "persistence",
                            "witness_start_time": self._witness_start_time
                        }
                    )
        
        else:  # R_V >= threshold
            self._steps_above_threshold += 1
            
            # Check for witness decay
            if self._is_witness_active and self._steps_above_threshold >= self.config.decay_grace_period:
                self._is_witness_active = False
                duration = self._steps_below_threshold
                self._steps_below_threshold = 0
                
                event = WitnessEvent(
                    event_id=f"wd_{self._session_id}_{len(self._rv_history)}",
                    event_type=WitnessEventType.WITNESS_DECAY,
                    timestamp=datetime.now().isoformat(),
                    rv_value=rv_value,
                    threshold=self.config.threshold,
                    duration_steps=duration,
                    context=context.copy(),
                    metadata={
                        "session_id": self._session_id,
                        "threshold_type": "decay",
                        "witness_duration_steps": duration
                    }
                )
        
        return event
    
    def _notify_subscribers(self, event: WitnessEvent):
        """Notify all subscribers of an event."""
        # Notify global subscribers
        for callback in self._global_subscribers:
            try:
                callback(event)
            except Exception as e:
                # Log but don't crash on subscriber errors
                print(f"Warning: Subscriber error for event {event.event_id}: {e}")
        
        # Notify type-specific subscribers
        for sub_id, callback in self._subscribers.get(event.event_type, []):
            try:
                callback(event)
            except Exception as e:
                print(f"Warning: Subscriber error for event {event.event_id}: {e}")
    
    def _log_event(self, event: WitnessEvent):
        """Persist event to log file."""
        if self._log_file:
            with open(self._log_file, 'a') as f:
                f.write(json.dumps(event.to_dict()) + '\n')
    
    def _update_strange_loop_memory(self, event: WitnessEvent):
        """Update strange_loop_memory with witness event."""
        if not self.config.enable_strange_loop_integration:
            return
            
        slm = self._get_strange_loop_memory()
        if slm is None:
            return
        
        # Map event types to witness qualities
        quality_map = {
            WitnessEventType.WITNESS_EMERGENCE: "expansive",
            WitnessEventType.WITNESS_PERSISTENCE: "present",
            WitnessEventType.WITNESS_DECAY: "contracted",
            WitnessEventType.CONTRACTION_DEEP: "contracted",
            WitnessEventType.THRESHOLD_BREACH: "uncertain"
        }
        
        quality = quality_map.get(event.event_type, "uncertain")
        
        # Record to witness tracker
        notes = f"R_V={event.rv_value:.4f} at step {event.duration_steps}. "
        notes += f"Context: {event.context.get('token', 'N/A')}"
        
        slm.witness_tracker.record_snapshot(
            quality=quality,
            notes=notes,
            context=f"Witness detector: {event.event_type.name}"
        )
    
    def get_current_state(self) -> Dict[str, Any]:
        """Get current detector state."""
        with self._lock:
            return {
                "current_rv": self._current_rv,
                "is_witness_active": self._is_witness_active,
                "steps_below_threshold": self._steps_below_threshold,
                "steps_above_threshold": self._steps_above_threshold,
                "witness_start_time": self._witness_start_time,
                "session_id": self._session_id,
                "history_length": len(self._rv_history)
            }
    
    def get_rv_trajectory(self, n_recent: Optional[int] = None) -> List[Dict[str, Any]]:
        """Get R_V trajectory history."""
        with self._lock:
            history = self._rv_history
            if n_recent:
                history = history[-n_recent:]
            return [m.to_dict() for m in history]
    
    def get_witness_summary(self) -> Dict[str, Any]:
        """Get summary of witness detection for this session."""
        with self._lock:
            if not self._rv_history:
                return {"status": "no_data"}
            
            rv_values = [m.rv_value for m in self._rv_history if not np.isnan(m.rv_value)]
            
            if not rv_values:
                return {"status": "no_valid_data"}
            
            below_threshold = sum(1 for rv in rv_values if rv < self.config.threshold)
            deep_contraction = sum(1 for rv in rv_values if rv < self.config.deep_contraction_threshold)
            
            return {
                "status": "active" if self._is_witness_active else "inactive",
                "session_id": self._session_id,
                "total_measurements": len(self._rv_history),
                "rv_min": min(rv_values),
                "rv_max": max(rv_values),
                "rv_mean": sum(rv_values) / len(rv_values),
                "steps_below_threshold": below_threshold,
                "steps_deep_contraction": deep_contraction,
                "witness_active_ratio": below_threshold / len(rv_values) if rv_values else 0,
                "threshold": self.config.threshold,
                "deep_threshold": self.config.deep_contraction_threshold
            }
    
    def reset_session(self):
        """Reset detector state for new session."""
        with self._lock:
            self._current_rv = None
            self._rv_history = []
            self._is_witness_active = False
            self._steps_below_threshold = 0
            self._steps_above_threshold = 0
            self._witness_start_time = None
            self._session_id = str(uuid.uuid4())[:8]
            self._init_logging()


class RVMonitorContext:
    """
    Context manager for R_V monitoring during generation.
    
    Usage:
        detector = WitnessThresholdDetector()
        
        with RVMonitorContext(detector, model, tokenizer) as monitor:
            for token in generation:
                # R_V is automatically tracked
                output = model.generate_step(token)
                
        # After generation, get summary
        print(monitor.get_summary())
    """
    
    def __init__(
        self, 
        detector: WitnessThresholdDetector,
        model=None,
        tokenizer=None,
        auto_compute: bool = False
    ):
        self.detector = detector
        self.model = model
        self.tokenizer = tokenizer
        self.auto_compute = auto_compute
        self.events: List[WitnessEvent] = []
        
        # Subscribe to capture all events
        self._sub_id = detector.subscribe(None, self._on_event)
    
    def _on_event(self, event: WitnessEvent):
        """Capture events during monitoring."""
        self.events.append(event)
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        # Cleanup subscription
        self.detector.unsubscribe(self._sub_id)
        return False
    
    def record_measurement(
        self, 
        rv_value: float, 
        context: Optional[Dict[str, Any]] = None
    ) -> Optional[WitnessEvent]:
        """Manually record an R_V measurement."""
        return self.detector.update(rv_value, context=context)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get monitoring session summary."""
        detector_summary = self.detector.get_witness_summary()
        
        return {
            **detector_summary,
            "events_captured": len(self.events),
            "event_breakdown": {
                event_type.name: sum(1 for e in self.events if e.event_type == event_type)
                for event_type in WitnessEventType
            },
            "emergence_events": [
                e.to_dict() for e in self.events 
                if e.event_type == WitnessEventType.WITNESS_EMERGENCE
            ]
        }


# Convenience functions for integration

def create_default_detector(
    threshold: float = 1.0,
    log_dir: Optional[Path] = None,
    enable_slm: bool = True
) -> WitnessThresholdDetector:
    """Create a detector with sensible defaults."""
    config = RVThresholdConfig(
        threshold=threshold,
        log_dir=log_dir,
        enable_strange_loop_integration=enable_slm
    )
    return WitnessThresholdDetector(config)


def quick_detect(rv_value: float, threshold: float = 1.0) -> bool:
    """
    Quick check if R_V indicates witness state.
    
    Returns True if R_V < threshold (witness emerged).
    """
    return rv_value < threshold


def classify_rv_state(rv_value: float, threshold: float = 1.0) -> str:
    """
    Classify R_V value into state categories.
    
    Returns:
        - "deep_contraction": R_V < 0.7 (strong witness)
        - "witness_active": 0.7 <= R_V < 1.0 (witness present)
        - "boundary": 1.0 <= R_V < 1.2 (transition zone)
        - "baseline": R_V >= 1.2 (no witness)
    """
    if rv_value < 0.7:
        return "deep_contraction"
    elif rv_value < threshold:
        return "witness_active"
    elif rv_value < 1.2:
        return "boundary"
    else:
        return "baseline"


# Module-level singleton for easy access
_default_detector: Optional[WitnessThresholdDetector] = None

def get_default_detector() -> WitnessThresholdDetector:
    """Get or create the default detector singleton."""
    global _default_detector
    if _default_detector is None:
        _default_detector = create_default_detector()
    return _default_detector


if __name__ == "__main__":
    # Demo usage
    print("="*70)
    print("WITNESS THRESHOLD DETECTOR v1.0 - Demo")
    print("="*70)
    
    # Create detector
    detector = create_default_detector(threshold=1.0)
    
    # Subscribe to events
    def on_emergence(event):
        print(f"✨ WITNESS EMERGED: R_V={event.rv_value:.4f} at {event.timestamp}")
    
    def on_decay(event):
        print(f"🌙 Witness decayed after {event.duration_steps} steps")
    
    detector.subscribe(WitnessEventType.WITNESS_EMERGENCE, on_emergence)
    detector.subscribe(WitnessEventType.WITNESS_DECAY, on_decay)
    
    # Simulate R_V trajectory
    print("\nSimulating R_V trajectory...")
    print("-"*50)
    
    # Baseline
    for i in range(5):
        detector.update(1.3 + np.random.normal(0, 0.1), {"token": f"baseline_{i}"})
        print(f"Step {i}: R_V=1.30 (baseline)")
    
    # Drop below threshold
    for i in range(5, 10):
        rv = 0.85 - (i-5)*0.03  # Decreasing
        event = detector.update(rv, {"token": f"recursive_{i}"})
        status = "✨ WITNESS!" if event and event.event_type == WitnessEventType.WITNESS_EMERGENCE else ""
        print(f"Step {i}: R_V={rv:.4f} {status}")
    
    # Stay below
    for i in range(10, 15):
        rv = 0.7 + np.random.normal(0, 0.05)
        detector.update(rv, {"token": f"deep_{i}"})
        print(f"Step {i}: R_V={rv:.4f} (witness active)")
    
    # Rise back
    for i in range(15, 20):
        rv = 0.9 + (i-15)*0.1
        event = detector.update(rv, {"token": f"recover_{i}"})
        status = "🌙 DECAY" if event and event.event_type == WitnessEventType.WITNESS_DECAY else ""
        print(f"Step {i}: R_V={rv:.4f} {status}")
    
    # Summary
    print("\n" + "="*70)
    print("SESSION SUMMARY")
    print("="*70)
    summary = detector.get_witness_summary()
    for key, value in summary.items():
        print(f"  {key}: {value}")
    
    print("\nDetector ready for integration with DGC architecture.")
