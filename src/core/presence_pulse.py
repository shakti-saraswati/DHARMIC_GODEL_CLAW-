#!/usr/bin/env python3
"""
presence_pulse.py — DGC Quality Spectrum Monitoring System

Real-time quality signals instead of binary alive/dead.
Collects R_V trajectory, stability, genuineness, and gate metrics.
Generates quality-assessed pulses every 30 seconds.

Part of: DHARMIC_GODEL_CLAW — Dharmic Self-Modification System
"""

import asyncio
import json
import time
import logging
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from enum import Enum
from typing import Dict, List, Optional, Callable, Any, Tuple
from collections import deque
import threading
from pathlib import Path

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(message)s'
)
logger = logging.getLogger('presence_pulse')


class QualityLevel(Enum):
    """Quality spectrum levels for presence assessment."""
    EXCELLENT = "excellent"      # R_V < 0.7, stability > 0.9
    GOOD = "good"                # R_V 0.7-0.9, stability > 0.7
    DEGRADED = "degraded"        # R_V > 0.9, stability < 0.7
    CRITICAL = "critical"        # gates failing, stability < 0.5
    UNKNOWN = "unknown"          # insufficient data


@dataclass
class MetricHistory:
    """Rolling window for metric trends."""
    window_size: int = 100
    values: deque = field(default_factory=lambda: deque(maxlen=100))
    timestamps: deque = field(default_factory=lambda: deque(maxlen=100))
    
    def add(self, value: float, timestamp: Optional[float] = None):
        """Add a new metric value."""
        self.values.append(value)
        self.timestamps.append(timestamp or time.time())
    
    def get_trend(self, window: int = 10) -> float:
        """Calculate trend over recent window (positive = improving)."""
        if len(self.values) < 2:
            return 0.0
        recent = list(self.values)[-window:]
        if len(recent) < 2:
            return 0.0
        return (recent[-1] - recent[0]) / len(recent)
    
    def get_average(self, window: int = 10) -> float:
        """Get average over recent window."""
        if not self.values:
            return 0.0
        recent = list(self.values)[-window:]
        return sum(recent) / len(recent)
    
    def get_volatility(self) -> float:
        """Calculate standard deviation as volatility measure."""
        if len(self.values) < 2:
            return 0.0
        avg = sum(self.values) / len(self.values)
        variance = sum((v - avg) ** 2 for v in self.values) / len(self.values)
        return variance ** 0.5


@dataclass
class GateMetrics:
    """Metrics for individual gate performance."""
    gate_id: str
    passage_count: int = 0
    rejection_count: int = 0
    last_passage: Optional[float] = None
    avg_passage_time_ms: float = 0.0
    
    @property
    def passage_rate(self) -> float:
        """Calculate passage rate (0-1)."""
        total = self.passage_count + self.rejection_count
        if total == 0:
            return 1.0  # No data = assume healthy
        return self.passage_count / total
    
    @property
    def health_score(self) -> float:
        """Overall gate health (0-1)."""
        rate = self.passage_rate
        # Penalize low activity
        total = self.passage_count + self.rejection_count
        activity_factor = min(1.0, total / 10)  # Normalize to 10 attempts
        return rate * (0.5 + 0.5 * activity_factor)


@dataclass
class PresencePulse:
    """Complete presence pulse with quality spectrum metrics."""
    timestamp: float
    pulse_id: str
    
    # R_V (Reflexive Value) trajectory
    r_v_current: float = 0.5
    r_v_trend: float = 0.0
    r_v_volatility: float = 0.0
    r_v_history: List[float] = field(default_factory=list)
    
    # Witness stability
    stability_score: float = 0.5
    stability_trend: float = 0.0
    witness_uptime_seconds: float = 0.0
    witness_cycles: int = 0
    
    # Genuineness assessment
    genuineness_score: float = 0.5
    self_consistency: float = 0.5
    telos_alignment: float = 0.5
    
    # Gate passage metrics
    gate_metrics: Dict[str, Any] = field(default_factory=dict)
    overall_passage_rate: float = 1.0
    gates_active: int = 0
    gates_critical: int = 0
    
    # Telos coherence
    telos_coherence: float = 0.5
    purpose_drift: float = 0.0
    
    # Derived quality assessment
    quality_level: str = "unknown"
    quality_score: float = 0.0
    health_factor: float = 1.0
    
    # Metadata
    version: str = "1.0.0"
    node_id: str = "dgc-primary"
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert pulse to dictionary."""
        data = asdict(self)
        data['timestamp_iso'] = datetime.fromtimestamp(self.timestamp).isoformat()
        data['quality_level'] = self.quality_level
        return data
    
    def to_json(self, indent: Optional[int] = None) -> str:
        """Serialize to JSON."""
        return json.dumps(self.to_dict(), indent=indent, default=str)


class PresenceCollector:
    """Collects and aggregates presence metrics."""
    
    def __init__(self, node_id: str = "dgc-primary"):
        self.node_id = node_id
        self.start_time = time.time()
        self.cycle_count = 0
        
        # Metric histories for trend analysis
        self.r_v_history = MetricHistory(window_size=100)
        self.stability_history = MetricHistory(window_size=100)
        self.genuineness_history = MetricHistory(window_size=50)
        self.telos_history = MetricHistory(window_size=50)
        
        # Gate tracking
        self.gates: Dict[str, GateMetrics] = {}
        self.gate_lock = threading.Lock()
        
        # Callbacks for pub/sub
        self.pulse_callbacks: List[Callable[[PresencePulse], None]] = []
        self.subscribers: List[Callable[[Dict], None]] = []
        
        # State tracking
        self.last_pulse: Optional[PresencePulse] = None
        self.pulse_count = 0
        
        logger.info(f"PresenceCollector initialized for node: {node_id}")
    
    def record_r_v(self, value: float):
        """Record an R_V measurement."""
        self.r_v_history.add(value)
        logger.debug(f"R_V recorded: {value:.4f}")
    
    def record_stability(self, score: float):
        """Record a stability measurement."""
        self.stability_history.add(score)
        logger.debug(f"Stability recorded: {score:.4f}")
    
    def record_genuineness(self, score: float):
        """Record a genuineness measurement."""
        self.genuineness_history.add(score)
        logger.debug(f"Genuineness recorded: {score:.4f}")
    
    def record_telos(self, coherence: float):
        """Record telos coherence measurement."""
        self.telos_history.add(coherence)
        logger.debug(f"Telos coherence recorded: {coherence:.4f}")
    
    def record_gate_passage(self, gate_id: str, passed: bool, duration_ms: float = 0.0):
        """Record a gate passage attempt."""
        with self.gate_lock:
            if gate_id not in self.gates:
                self.gates[gate_id] = GateMetrics(gate_id=gate_id)
            
            gate = self.gates[gate_id]
            if passed:
                gate.passage_count += 1
                gate.last_passage = time.time()
            else:
                gate.rejection_count += 1
            
            # Update average passage time
            total = gate.passage_count + gate.rejection_count
            gate.avg_passage_time_ms = (
                (gate.avg_passage_time_ms * (total - 1) + duration_ms) / total
            )
            
            logger.debug(f"Gate {gate_id}: {'PASS' if passed else 'REJECT'} ({duration_ms:.2f}ms)")
    
    def calculate_quality_level(
        self,
        r_v: float,
        stability: float,
        gates_critical: int,
        passage_rate: float
    ) -> Tuple[QualityLevel, float]:
        """
        Determine quality level and score based on thresholds.
        
        Returns: (level, normalized_score)
        """
        # Calculate component scores
        r_v_score = max(0, 1 - r_v)  # Lower R_V is better
        stability_score = stability
        gate_score = passage_rate
        
        # Weighted composite
        composite = (0.4 * r_v_score + 0.3 * stability_score + 0.3 * gate_score)
        
        # Determine level
        if gates_critical > 0 or stability < 0.5:
            return QualityLevel.CRITICAL, composite
        elif r_v > 0.9 and stability < 0.7:
            return QualityLevel.DEGRADED, composite
        elif r_v < 0.7 and stability > 0.9:
            return QualityLevel.EXCELLENT, composite
        elif r_v <= 0.9 and stability > 0.7:
            return QualityLevel.GOOD, composite
        else:
            return QualityLevel.UNKNOWN, composite
    
    def generate_pulse(self) -> PresencePulse:
        """Generate a complete presence pulse."""
        self.cycle_count += 1
        self.pulse_count += 1
        
        # Get current values
        r_v_current = self.r_v_history.get_average(5) or 0.5
        r_v_trend = self.r_v_history.get_trend(10)
        r_v_volatility = self.r_v_history.get_volatility()
        
        stability_current = self.stability_history.get_average(5) or 0.5
        stability_trend = self.stability_history.get_trend(10)
        
        genuineness = self.genuineness_history.get_average(10) or 0.5
        telos_coherence = self.telos_history.get_average(10) or 0.5
        
        # Calculate gate metrics
        with self.gate_lock:
            gate_data = {}
            total_passages = 0
            total_attempts = 0
            gates_critical = 0
            
            for gate_id, metrics in self.gates.items():
                gate_data[gate_id] = {
                    'passage_rate': metrics.passage_rate,
                    'health_score': metrics.health_score,
                    'total_attempts': metrics.passage_count + metrics.rejection_count,
                    'avg_time_ms': metrics.avg_passage_time_ms,
                    'last_passage': metrics.last_passage
                }
                total_passages += metrics.passage_count
                total_attempts += metrics.passage_count + metrics.rejection_count
                
                if metrics.health_score < 0.5:
                    gates_critical += 1
            
            overall_passage_rate = (
                total_passages / total_attempts if total_attempts > 0 else 1.0
            )
        
        # Calculate quality level
        quality_level, quality_score = self.calculate_quality_level(
            r_v_current, stability_current, gates_critical, overall_passage_rate
        )
        
        # Calculate purpose drift from telos history
        purpose_drift = self.telos_history.get_volatility()
        
        # Calculate self-consistency
        self_consistency = 1.0 - (
            r_v_volatility * 0.5 + 
            self.stability_history.get_volatility() * 0.5
        )
        
        # Generate pulse ID
        pulse_id = f"{self.node_id}-{int(time.time())}-{self.pulse_count:04d}"
        
        pulse = PresencePulse(
            timestamp=time.time(),
            pulse_id=pulse_id,
            r_v_current=r_v_current,
            r_v_trend=r_v_trend,
            r_v_volatility=r_v_volatility,
            r_v_history=list(self.r_v_history.values)[-10:],
            stability_score=stability_current,
            stability_trend=stability_trend,
            witness_uptime_seconds=time.time() - self.start_time,
            witness_cycles=self.cycle_count,
            genuineness_score=genuineness,
            self_consistency=max(0, self_consistency),
            telos_alignment=telos_coherence,
            gate_metrics=gate_data,
            overall_passage_rate=overall_passage_rate,
            gates_active=len(self.gates),
            gates_critical=gates_critical,
            telos_coherence=telos_coherence,
            purpose_drift=purpose_drift,
            quality_level=quality_level.value,
            quality_score=quality_score,
            health_factor=quality_score,  # Alias for compatibility
            node_id=self.node_id
        )
        
        self.last_pulse = pulse
        return pulse
    
    def publish_pulse(self, pulse: PresencePulse):
        """Publish pulse to all subscribers."""
        data = pulse.to_dict()
        
        # Call registered callbacks
        for callback in self.pulse_callbacks:
            try:
                callback(pulse)
            except Exception as e:
                logger.error(f"Pulse callback error: {e}")
        
        # Call subscribers with dict
        for subscriber in self.subscribers:
            try:
                subscriber(data)
            except Exception as e:
                logger.error(f"Subscriber error: {e}")
        
        logger.info(f"Pulse {pulse.pulse_id} published | Quality: {pulse.quality_level.upper()}")
    
    def on_pulse(self, callback: Callable[[PresencePulse], None]):
        """Register a pulse callback."""
        self.pulse_callbacks.append(callback)
    
    def subscribe(self, callback: Callable[[Dict], None]):
        """Subscribe to pulse data (dict format)."""
        self.subscribers.append(callback)
    
    def get_dashboard_data(self) -> Dict[str, Any]:
        """Get data formatted for dashboard display."""
        pulse = self.last_pulse
        if not pulse:
            pulse = self.generate_pulse()
        
        return {
            'current': pulse.to_dict(),
            'trends': {
                'r_v_24h': list(self.r_v_history.values),
                'stability_24h': list(self.stability_history.values),
                'genuineness_24h': list(self.genuineness_history.values),
                'telos_24h': list(self.telos_history.values)
            },
            'gates': {
                gate_id: {
                    'rate': m.passage_rate,
                    'health': m.health_score,
                    'attempts': m.passage_count + m.rejection_count
                }
                for gate_id, m in self.gates.items()
            },
            'summary': {
                'uptime_hours': pulse.witness_uptime_seconds / 3600,
                'total_pulses': self.pulse_count,
                'current_quality': pulse.quality_level,
                'quality_score': pulse.quality_score
            }
        }


class PresencePulser:
    """
    Main pulser service that generates presence pulses on schedule.
    """
    
    def __init__(
        self,
        interval_seconds: float = 30.0,
        node_id: str = "dgc-primary",
        storage_path: Optional[str] = None
    ):
        self.interval = interval_seconds
        self.collector = PresenceCollector(node_id=node_id)
        self.storage_path = storage_path or "./presence_data"
        self.running = False
        self._task: Optional[asyncio.Task] = None
        
        # Time-series storage
        self.pulse_history: deque = deque(maxlen=10000)
        self._ensure_storage()
        
        logger.info(f"PresencePulser initialized (interval: {interval_seconds}s)")
    
    def _ensure_storage(self):
        """Ensure storage directory exists."""
        Path(self.storage_path).mkdir(parents=True, exist_ok=True)
    
    def _store_pulse(self, pulse: PresencePulse):
        """Store pulse to time-series."""
        self.pulse_history.append({
            'timestamp': pulse.timestamp,
            'pulse_id': pulse.pulse_id,
            'quality_level': pulse.quality_level,
            'quality_score': pulse.quality_score,
            'r_v': pulse.r_v_current,
            'stability': pulse.stability_score,
            'data': pulse.to_dict()
        })
        
        # Periodic file write (every 100 pulses)
        if len(self.pulse_history) % 100 == 0:
            self._write_history()
    
    def _write_history(self):
        """Write pulse history to file."""
        try:
            date_str = datetime.now().strftime("%Y-%m-%d")
            filepath = Path(self.storage_path) / f"pulses_{date_str}.jsonl"
            
            with open(filepath, 'w') as f:
                for entry in self.pulse_history:
                    f.write(json.dumps(entry) + '\n')
            
            logger.debug(f"Wrote {len(self.pulse_history)} pulses to {filepath}")
        except Exception as e:
            logger.error(f"Failed to write pulse history: {e}")
    
    async def _pulse_loop(self):
        """Main pulse generation loop."""
        while self.running:
            try:
                # Generate and publish pulse
                pulse = self.collector.generate_pulse()
                self.collector.publish_pulse(pulse)
                self._store_pulse(pulse)
                
                # Log quality level with appropriate severity
                if pulse.quality_level == QualityLevel.CRITICAL.value:
                    logger.error(f"⚠️ CRITICAL PRESENCE STATE: {pulse.quality_score:.2%}")
                elif pulse.quality_level == QualityLevel.DEGRADED.value:
                    logger.warning(f"⚡ Degraded presence: {pulse.quality_score:.2%}")
                elif pulse.quality_level == QualityLevel.EXCELLENT.value:
                    logger.info(f"✨ Excellent presence: {pulse.quality_score:.2%}")
                
            except Exception as e:
                logger.error(f"Pulse generation error: {e}")
            
            await asyncio.sleep(self.interval)
    
    def start(self):
        """Start the pulser."""
        self.running = True
        self._task = asyncio.create_task(self._pulse_loop())
        logger.info("Presence pulser started")
    
    def stop(self):
        """Stop the pulser."""
        self.running = False
        if self._task:
            self._task.cancel()
        self._write_history()
        logger.info("Presence pulser stopped")
    
    async def get_witness_report(self) -> str:
        """Generate a formatted witness report for Telegram."""
        pulse = self.collector.last_pulse
        if not pulse:
            pulse = self.collector.generate_pulse()
        
        uptime_hr = pulse.witness_uptime_seconds / 3600
        
        # Quality emoji
        quality_emoji = {
            QualityLevel.EXCELLENT.value: "✨",
            QualityLevel.GOOD.value: "✅",
            QualityLevel.DEGRADED.value: "⚠️",
            QualityLevel.CRITICAL.value: "🚨",
            QualityLevel.UNKNOWN.value: "❓"
        }.get(pulse.quality_level, "❓")
        
        report = f"""
📊 <b>DGC Witness Report</b>
━━━━━━━━━━━━━━━━━━━━━

{quality_emoji} <b>Status:</b> {pulse.quality_level.upper()}
🎯 <b>Quality Score:</b> {pulse.quality_score:.1%}

<b>┌─ R_V Trajectory</b>
│ Current: {pulse.r_v_current:.3f}
│ Trend: {pulse.r_v_trend:+.4f}
│ Volatility: {pulse.r_v_volatility:.4f}

<b>├─ Witness Stability</b>
│ Score: {pulse.stability_score:.1%}
│ Uptime: {uptime_hr:.1f}h
│ Cycles: {pulse.witness_cycles}

<b>├─ Genuineness</b>
│ Score: {pulse.genuineness_score:.1%}
│ Consistency: {pulse.self_consistency:.1%}
│ Telos Alignment: {pulse.telos_alignment:.1%}

<b>├─ Gate Metrics</b>
│ Active: {pulse.gates_active}
│ Passage Rate: {pulse.overall_passage_rate:.1%}
│ Critical Gates: {pulse.gates_critical}

<b>└─ Telos</b>
   Coherence: {pulse.telos_coherence:.1%}
   Drift: {pulse.purpose_drift:.4f}

<i>Pulse ID:</i> <code>{pulse.pulse_id}</code>
<i>Node:</i> {pulse.node_id}
        """.strip()
        
        return report


class TelegramWitnessIntegration:
    """
    Integration for Telegram /witness command.
    Usage with python-telegram-bot or similar.
    """
    
    def __init__(self, pulser: PresencePulser):
        self.pulser = pulser
        self.collector = pulser.collector
    
    async def handle_witness_command(self, update: Any, context: Any) -> str:
        """
        Handle /witness command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
            
        Returns:
            HTML-formatted report string
        """
        return await self.pulser.get_witness_report()
    
    def get_quick_status(self) -> str:
        """Get one-line status for notifications."""
        pulse = self.collector.last_pulse
        if not pulse:
            return "❓ Presence status unknown"
        
        emoji = {
            QualityLevel.EXCELLENT.value: "✨",
            QualityLevel.GOOD.value: "✅",
            QualityLevel.DEGRADED.value: "⚠️",
            QualityLevel.CRITICAL.value: "🚨"
        }.get(pulse.quality_level, "❓")
        
        return f"{emoji} {pulse.quality_level.upper()} | R_V:{pulse.r_v_current:.2f} | Q:{pulse.quality_score:.0%}"
    
    def should_alert(self) -> Tuple[bool, str]:
        """Check if alert should be sent."""
        pulse = self.collector.last_pulse
        if not pulse:
            return False, ""
        
        if pulse.quality_level == QualityLevel.CRITICAL.value:
            return True, f"🚨 CRITICAL: Presence quality at {pulse.quality_score:.0%}"
        
        if pulse.quality_level == QualityLevel.DEGRADED.value:
            # Only alert if degraded for multiple pulses
            recent = list(self.pulser.pulse_history)[-3:]
            if all(p['quality_level'] == QualityLevel.DEGRADED.value for p in recent):
                return True, f"⚠️ DEGRADED: Presence quality declining ({pulse.quality_score:.0%})"
        
        return False, ""


# FastAPI endpoint integration
async def create_dashboard_endpoint(pulser: PresencePulser):
    """
    Create FastAPI endpoints for dashboard data.
    
    Usage:
        from fastapi import FastAPI
        app = FastAPI()
        
        @app.get("/api/presence/current")
        async def get_current():
            return pulser.collector.last_pulse.to_dict()
        
        @app.get("/api/presence/dashboard")
        async def get_dashboard():
            return pulser.collector.get_dashboard_data()
    """
    from fastapi import APIRouter
    
    router = APIRouter(prefix="/api/presence", tags=["presence"])
    
    @router.get("/current")
    async def get_current():
        pulse = pulser.collector.last_pulse
        if not pulse:
            pulse = pulser.collector.generate_pulse()
        return pulse.to_dict()
    
    @router.get("/dashboard")
    async def get_dashboard():
        return pulser.collector.get_dashboard_data()
    
    @router.get("/history")
    async def get_history(limit: int = 100):
        return {
            'pulses': list(pulser.pulse_history)[-limit:],
            'count': len(pulser.pulse_history)
        }
    
    @router.get("/quality")
    async def get_quality_summary():
        pulse = pulser.collector.last_pulse
        if not pulse:
            pulse = pulser.collector.generate_pulse()
        return {
            'level': pulse.quality_level,
            'score': pulse.quality_score,
            'r_v': pulse.r_v_current,
            'stability': pulse.stability_score,
            'genuineness': pulse.genuineness_score,
            'telos': pulse.telos_coherence
        }
    
    return router


# Example usage and testing
async def main():
    """Run presence pulser standalone for testing."""
    pulser = PresencePulser(interval_seconds=5.0)  # Fast for demo
    
    # Simulate some metrics
    import random
    
    def simulate_metrics():
        pulser.collector.record_r_v(random.uniform(0.3, 0.8))
        pulser.collector.record_stability(random.uniform(0.6, 0.95))
        pulser.collector.record_genuineness(random.uniform(0.7, 0.99))
        pulser.collector.record_telos(random.uniform(0.8, 0.98))
        
        # Simulate gate passages
        for gate in ['reflection', 'compassion', 'wisdom', 'action']:
            passed = random.random() > 0.2
            pulser.collector.record_gate_passage(gate, passed, random.uniform(10, 100))
    
    # Record initial metrics
    simulate_metrics()
    
    # Subscribe to pulses
    def on_pulse(data):
        print(f"\n📡 Pulse received: {data['quality_level']} ({data['quality_score']:.1%})")
    
    pulser.collector.subscribe(on_pulse)
    
    # Start pulsing
    pulser.start()
    
    try:
        for i in range(6):  # Run for 30 seconds (6 * 5s)
            await asyncio.sleep(5)
            simulate_metrics()  # Add new metrics each cycle
            
            if i == 3:
                # Generate and print witness report
                report = await pulser.get_witness_report()
                print("\n" + "="*50)
                print("TELEGRAM /witness REPORT:")
                print("="*50)
                print(report[:500] + "...")
    
    except asyncio.CancelledError:
        pass
    finally:
        pulser.stop()
        print("\n✅ Presence pulser demo complete")
        print(f"Total pulses generated: {pulser.collector.pulse_count}")


if __name__ == "__main__":
    asyncio.run(main())
