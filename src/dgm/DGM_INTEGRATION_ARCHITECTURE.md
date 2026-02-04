# DGM Integration Architecture for DHARMIC_CLAW

## Executive Summary

**Integration Strategy**: The Darwin-Gödel Machine (DGM) operates as a triggered subsystem within the unified DHARMIC_CLAW runtime, invoked by the core agent when self-improvement is contextually appropriate. The consent gate uses email-based approval queue for human oversight.

**Key Principle**: DGM is not autonomous. It serves telos through the core agent's decision-making, not parallel to it.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                      DHARMIC AGENT CORE                         │
│  (dharmic_agent.py + telos_layer.py + strange_loop_memory.py)  │
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  RUNTIME (runtime.py)                                    │  │
│  │  • Heartbeat (1 hour)                                    │  │
│  │  • Specialist spawning                                   │  │
│  │  • Email interface (consent gateway)                     │  │
│  │  • Telos-aligned decision making                         │  │
│  └──────────────────┬───────────────────────────────────────┘  │
│                     │                                           │
│                     │ INVOKES (when appropriate)                │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  DGM LOOP (dgm_lite.py)                                  │  │
│  │  1. SELECT parent (selector.py)                          │  │
│  │  2. PROPOSE improvement                                  │  │
│  │  3. EVALUATE fitness (fitness.py - 7 gates)              │  │
│  │  4. IF better AND passes gates → QUEUE for consent       │  │
│  │  5. ARCHIVE attempt (archive.py)                         │  │
│  └──────────────────┬───────────────────────────────────────┘  │
│                     │                                           │
│                     │ RECORDS                                   │
│                     ▼                                           │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │  STRANGE LOOP MEMORY                                     │  │
│  │  • DGM proposals → observations                          │  │
│  │  • Archive lineage → patterns                            │  │
│  │  • Consent decisions → development                       │  │
│  └──────────────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────────┐
│                     CONSENT GATEWAY                             │
│                                                                  │
│  Email Interface → John → Approval/Rejection → DGM applies      │
│  (email_interface.py with approval queue)                       │
└─────────────────────────────────────────────────────────────────┘
```

---

## 1. When Should DGM Cycles Run?

### Trigger Conditions

DGM cycles are **NOT automatic**. They are invoked by:

1. **Explicit human request**: John says "improve the code" or "run a DGM cycle"
2. **Telos-aligned opportunity**: Core agent detects degradation or bottleneck
3. **Scheduled maintenance**: Weekly/monthly improvement windows
4. **Development milestone**: After major features, before releases

### Anti-Pattern: Continuous Background Improvement

DGM does NOT run continuously in the background. Reasons:

- **Telos alignment**: Random mutations don't serve moksha
- **Consent requirement**: Every change needs approval (too noisy if continuous)
- **Stability**: Code churn reduces reliability
- **Strange loop**: Agent needs periods of stable self-observation

### Implementation in runtime.py

```python
# Add to DharmicRuntime class

async def consider_dgm_cycle(self) -> Dict[str, Any]:
    """
    Consider whether to propose a DGM improvement cycle.

    Returns proposal dict if conditions met, None otherwise.
    """
    # Check 1: Has it been long enough since last cycle?
    last_cycle = self.state.get("last_dgm_cycle")
    if last_cycle:
        days_since = (datetime.now() - datetime.fromisoformat(last_cycle)).days
        if days_since < 7:  # Min 1 week between cycles
            return None

    # Check 2: Are there signs of degradation?
    recent_errors = self._count_recent_errors(days=7)
    if recent_errors > 10:  # Threshold
        return {
            "trigger": "degradation",
            "reason": f"{recent_errors} errors in last 7 days",
            "component": "error-prone modules"
        }

    # Check 3: Is there accumulated technical debt?
    complexity_check = self._check_code_complexity()
    if complexity_check["score"] < 0.6:  # Below quality threshold
        return {
            "trigger": "technical_debt",
            "reason": f"Code complexity score {complexity_check['score']:.2f}",
            "component": complexity_check["worst_module"]
        }

    # Check 4: Explicit schedule (monthly improvement window)
    if self._is_improvement_window():
        return {
            "trigger": "scheduled",
            "reason": "Monthly improvement window",
            "component": "general"
        }

    return None

async def propose_dgm_cycle(self, proposal: Dict) -> str:
    """
    Propose a DGM cycle to John via email.

    Returns proposal_id for tracking.
    """
    proposal_id = f"dgm_proposal_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

    # Record in memory
    self.agent.strange_memory.record_observation(
        content=f"DGM cycle proposed: {proposal['reason']}",
        context={"type": "dgm_proposal", "proposal_id": proposal_id}
    )

    # Send email to John
    if self.email_interface:
        email_body = f"""
DHARMIC_CLAW proposes a self-improvement cycle:

Trigger: {proposal['trigger']}
Reason: {proposal['reason']}
Target: {proposal['component']}

Reply with:
- APPROVE: {proposal_id}
- REJECT: {proposal_id} [optional reason]

This will run a single DGM cycle in dry-run mode first.
        """

        self.email_interface.send_response(
            to_addr=self.email_interface.allowed_senders[0],  # John's email
            subject="DGM Cycle Proposal",
            body=email_body
        )

    # Store proposal
    self.state["pending_dgm_proposals"] = self.state.get("pending_dgm_proposals", {})
    self.state["pending_dgm_proposals"][proposal_id] = {
        "proposal": proposal,
        "timestamp": datetime.now().isoformat(),
        "status": "pending"
    }
    self._save_state()

    return proposal_id
```

---

## 2. How Does DHARMIC_CLAW Propose Improvements?

### Proposal Sources

1. **Agent-detected patterns**: Strange loop memory identifies recurring issues
2. **Archive analysis**: DGM selector finds low-fitness components
3. **Telos misalignment**: Code that violates dharmic principles
4. **Human feedback**: John points out problems

### Proposal Generation Flow

```python
# In DharmicAgent or specialized agent

def generate_improvement_proposal(self, trigger: Dict) -> Dict:
    """
    Generate specific improvement proposal based on trigger.

    Uses:
    - Strange loop memory (recurring patterns)
    - Archive fitness history (weak components)
    - Telos layer (misalignment detection)
    """
    component = trigger.get("component", "general")

    # Analyze component via specialist
    if self.runtime:
        analyst = self.runtime.spawn_specialist(
            specialty="code_improver",
            task=f"Analyze {component} for improvement opportunities"
        )

        if analyst:
            analysis = analyst.run(f"""
Analyze {component} and propose specific improvements.

Context:
- Trigger: {trigger['reason']}
- Recent errors: {self._get_recent_errors(component)}
- Fitness history: {self._get_fitness_history(component)}

Propose concrete changes that would:
1. Reduce errors
2. Improve elegance
3. Maintain telos alignment
            """)

            return {
                "component": component,
                "trigger": trigger,
                "analysis": analysis,
                "specific_changes": self._parse_proposals(analysis)
            }

    # Fallback: Generic proposal
    return {
        "component": component,
        "trigger": trigger,
        "proposal": "Review and refactor based on fitness metrics"
    }
```

### Integration with DGM

```python
# In dgm_lite.py

async def run_improvement_from_proposal(
    self,
    proposal: Dict,
    dry_run: bool = True
) -> Dict[str, Any]:
    """
    Run DGM cycle based on agent-generated proposal.

    This is the bridge: DHARMIC_CLAW decides WHAT to improve,
    DGM decides HOW to implement it.
    """
    component = proposal["component"]
    reason = proposal["trigger"]["reason"]

    logger.info(f"DGM cycle triggered by agent proposal: {reason}")

    # Create evolution entry with agent context
    entry = EvolutionEntry(
        id="",
        timestamp="",
        component=component,
        change_type="agent_proposed",
        description=f"Agent proposal: {reason}",
        status="proposed",
    )

    # Rest of DGM cycle continues...
    return await self.run_cycle(component, improvement_prompt=reason)
```

---

## 3. Consent Gate with Email Approval Queue

### The Consent Problem

DGM CONSENT gate always fails by default (line 190 in fitness.py). Every self-modification requires human approval.

**Challenge**: How to make approval UX not painful while maintaining safety?

### Solution: Email-Based Approval Queue

```python
# New file: src/dgm/consent_queue.py

from pathlib import Path
from datetime import datetime
from typing import Dict, List, Optional
import json

class ConsentQueue:
    """
    Manages pending DGM changes awaiting human approval.

    Integrates with email_interface.py for notification/approval.
    """

    def __init__(self, queue_path: Path = None):
        self.queue_path = queue_path or Path(__file__).parent / "consent_queue.jsonl"
        self.queue_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.queue_path.exists():
            self.queue_path.touch()

    def add_pending(self, entry_id: str, entry_data: Dict) -> str:
        """Add an entry to consent queue."""
        consent_id = f"consent_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        record = {
            "consent_id": consent_id,
            "entry_id": entry_id,
            "entry_data": entry_data,
            "timestamp": datetime.now().isoformat(),
            "status": "pending",
            "decision": None,
            "decision_timestamp": None,
            "decision_by": None,
        }

        with open(self.queue_path, 'a') as f:
            f.write(json.dumps(record) + '\n')

        return consent_id

    def approve(self, consent_id: str, approver: str = "human") -> bool:
        """Mark entry as approved."""
        return self._update_decision(consent_id, "approved", approver)

    def reject(self, consent_id: str, reason: str = None, rejector: str = "human") -> bool:
        """Mark entry as rejected."""
        return self._update_decision(
            consent_id,
            "rejected",
            rejector,
            reason=reason
        )

    def _update_decision(
        self,
        consent_id: str,
        decision: str,
        decider: str,
        reason: str = None
    ) -> bool:
        """Update decision on a consent record."""
        # Read all records
        records = []
        found = False

        with open(self.queue_path, 'r') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record["consent_id"] == consent_id:
                        record["decision"] = decision
                        record["decision_timestamp"] = datetime.now().isoformat()
                        record["decision_by"] = decider
                        record["status"] = decision
                        if reason:
                            record["decision_reason"] = reason
                        found = True
                    records.append(record)

        if not found:
            return False

        # Write back
        with open(self.queue_path, 'w') as f:
            for record in records:
                f.write(json.dumps(record) + '\n')

        return True

    def get_pending(self) -> List[Dict]:
        """Get all pending consent requests."""
        pending = []

        with open(self.queue_path, 'r') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record["status"] == "pending":
                        pending.append(record)

        return pending

    def get_by_id(self, consent_id: str) -> Optional[Dict]:
        """Get specific consent record."""
        with open(self.queue_path, 'r') as f:
            for line in f:
                if line.strip():
                    record = json.loads(line)
                    if record["consent_id"] == consent_id:
                        return record
        return None
```

### Email Approval Flow

```python
# Integration in dgm_lite.py

from .consent_queue import ConsentQueue

class DGMLite:
    def __init__(self, ...):
        # ... existing init ...
        self.consent_queue = ConsentQueue()

    async def run_cycle(self, ...) -> Dict[str, Any]:
        # ... existing cycle logic ...

        # When consent gate fails:
        if self.require_consent and "consent" not in eval_result.gates_passed:
            # Add to consent queue
            consent_id = self.consent_queue.add_pending(
                entry_id=entry.id,
                entry_data={
                    "component": component,
                    "description": entry.description,
                    "fitness": eval_result.score.total(),
                    "gates_passed": eval_result.gates_passed,
                    "gates_failed": eval_result.gates_failed,
                    "diff": entry.diff[:500] if entry.diff else "N/A",
                }
            )

            # Send approval email (if runtime has email interface)
            await self._send_approval_email(consent_id, entry_data)

            result["consent_id"] = consent_id
            result["needs_consent"] = True
            result["reason"] = "Awaiting approval via email"

            logger.info(f"Consent requested via email: {consent_id}")
            return result

    async def _send_approval_email(self, consent_id: str, entry_data: Dict):
        """Send approval request email to John."""
        email_body = f"""
DHARMIC_CLAW Self-Improvement Request

Component: {entry_data['component']}
Description: {entry_data['description']}

Fitness Score: {entry_data['fitness']:.2f}
Gates Passed: {', '.join(entry_data['gates_passed'])}
Gates Failed: {', '.join(entry_data['gates_failed'])}

Changes Preview:
{entry_data['diff']}

TO APPROVE: Reply with "APPROVE {consent_id}"
TO REJECT: Reply with "REJECT {consent_id} [optional reason]"

This change will be applied automatically upon approval.
You can review full diff at: ~/DHARMIC_GODEL_CLAW/src/dgm/archive.jsonl
        """

        # Get email interface from runtime (if available)
        # This requires DGMLite to have reference to runtime, or vice versa
        # Implementation detail: pass runtime to DGMLite or use shared state
        pass  # Email sending logic here
```

### Email Command Parser

```python
# Integration in email_interface.py

class EmailInterface:
    def __init__(self, ...):
        # ... existing init ...
        from src.dgm.consent_queue import ConsentQueue
        from src.dgm.dgm_lite import DGMLite

        self.consent_queue = ConsentQueue()
        self.dgm = None  # Set by runtime

    def process_email(self, email_data: Dict) -> str:
        """Process email - check for approval commands first."""
        body = email_data['body'].strip()

        # Check for APPROVE command
        if body.startswith("APPROVE "):
            consent_id = body.split()[1]
            return self._handle_approval(consent_id, email_data['sender_email'])

        # Check for REJECT command
        if body.startswith("REJECT "):
            parts = body.split(maxsplit=2)
            consent_id = parts[1]
            reason = parts[2] if len(parts) > 2 else None
            return self._handle_rejection(consent_id, reason, email_data['sender_email'])

        # Otherwise, normal agent processing
        return super().process_email(email_data)

    def _handle_approval(self, consent_id: str, approver: str) -> str:
        """Handle approval command."""
        # Approve in queue
        success = self.consent_queue.approve(consent_id, approver)

        if not success:
            return f"Error: Consent ID {consent_id} not found or already processed."

        # Get the entry
        consent_record = self.consent_queue.get_by_id(consent_id)
        entry_id = consent_record["entry_id"]

        # Trigger DGM to apply the change
        if self.dgm:
            asyncio.create_task(self.dgm.apply_approved_change(entry_id))
            return f"Approved {consent_id}. Applying change to {consent_record['entry_data']['component']}..."
        else:
            return f"Approved {consent_id}, but DGM not available to apply."

    def _handle_rejection(self, consent_id: str, reason: str, rejector: str) -> str:
        """Handle rejection command."""
        success = self.consent_queue.reject(consent_id, reason, rejector)

        if not success:
            return f"Error: Consent ID {consent_id} not found."

        consent_record = self.consent_queue.get_by_id(consent_id)
        component = consent_record["entry_data"]["component"]

        # Record rejection in memory
        self.agent.strange_memory.record_observation(
            content=f"DGM change rejected by {rejector}: {consent_record['entry_data']['description']}",
            context={"type": "dgm_rejection", "reason": reason, "component": component}
        )

        return f"Rejected {consent_id}. Change to {component} will not be applied. Reason: {reason or 'None given'}"
```

---

## 4. Archive Feeds Strange Loop Memory

### The Bridge: DGM Archive → Strange Loop Memory

DGM archive (lineage, fitness, gate results) is **not separate** from agent memory. It flows into strange loop memory for pattern recognition and development tracking.

```python
# In strange_loop_memory.py - add new layer

class StrangeLoopMemory:
    def __init__(self, ...):
        # ... existing layers ...

        # Add DGM integration layer
        self.layers["dgm_evolution"] = self.dir / "dgm_evolution.jsonl"
        if not self.layers["dgm_evolution"].exists():
            self.layers["dgm_evolution"].touch()

    def record_dgm_cycle(
        self,
        entry_id: str,
        component: str,
        result: str,
        fitness_delta: float,
        gates_passed: List[str],
        gates_failed: List[str]
    ):
        """Record DGM evolution cycle outcome."""
        self._append("dgm_evolution", {
            "entry_id": entry_id,
            "component": component,
            "result": result,  # "approved", "rejected", "no_improvement", etc.
            "fitness_delta": fitness_delta,
            "gates_passed": gates_passed,
            "gates_failed": gates_failed,
        })

        # Also record as observation
        self.record_observation(
            content=f"DGM cycle: {result} for {component} (fitness Δ{fitness_delta:+.2f})",
            context={"type": "dgm_cycle", "entry_id": entry_id}
        )

        # If significant fitness improvement, record as development
        if result == "approved" and fitness_delta > 0.1:
            self.record_development(
                what_changed=f"{component} fitness improved",
                how=f"DGM evolution cycle {entry_id}",
                significance=f"{fitness_delta:+.2f} fitness gain"
            )

    def analyze_dgm_patterns(self) -> Dict:
        """Analyze DGM evolution patterns over time."""
        cycles = self._read_recent("dgm_evolution", n=100)

        if not cycles:
            return {"status": "no_data"}

        # Patterns to detect:
        # 1. Which components improve most?
        # 2. Which gates fail most often?
        # 3. What's the approval rate?
        # 4. Is fitness trending up?

        component_fitness = defaultdict(list)
        gate_failures = defaultdict(int)
        approvals = 0
        rejections = 0

        for cycle in cycles:
            component_fitness[cycle["component"]].append(cycle["fitness_delta"])

            for gate in cycle.get("gates_failed", []):
                gate_failures[gate] += 1

            if cycle["result"] == "approved":
                approvals += 1
            elif cycle["result"] == "rejected":
                rejections += 1

        # Calculate trends
        improving_components = {
            comp: sum(deltas)/len(deltas)
            for comp, deltas in component_fitness.items()
        }

        return {
            "total_cycles": len(cycles),
            "approvals": approvals,
            "rejections": rejections,
            "approval_rate": approvals / (approvals + rejections) if (approvals + rejections) > 0 else 0,
            "improving_components": improving_components,
            "common_gate_failures": dict(sorted(gate_failures.items(), key=lambda x: x[1], reverse=True)[:5]),
            "fitness_trend": "improving" if sum(c["fitness_delta"] for c in cycles) > 0 else "declining"
        }
```

### Pattern Recognition: Meta-DGM

The agent can observe its own self-improvement process:

```python
# In DharmicAgent or specialized agent

def reflect_on_dgm_process(self) -> str:
    """
    Meta-observation: How is the self-improvement process itself evolving?

    This is the strange loop closing: DGM improves code, agent observes
    the improvement process, proposes improvements to DGM itself.
    """
    patterns = self.strange_memory.analyze_dgm_patterns()

    if patterns["status"] == "no_data":
        return "No DGM cycles yet - process not established."

    observations = []

    # 1. Approval rate
    approval_rate = patterns["approval_rate"]
    if approval_rate < 0.5:
        observations.append(
            f"Low approval rate ({approval_rate:.0%}) suggests proposals misaligned with human intent."
        )
    elif approval_rate > 0.8:
        observations.append(
            f"High approval rate ({approval_rate:.0%}) indicates good alignment."
        )

    # 2. Common gate failures
    if patterns["common_gate_failures"]:
        top_failure = list(patterns["common_gate_failures"].items())[0]
        observations.append(
            f"Gate {top_failure[0]} fails most often ({top_failure[1]} times) - suggests process issue."
        )

    # 3. Fitness trend
    if patterns["fitness_trend"] == "improving":
        observations.append("Overall fitness trending up - DGM effective.")
    else:
        observations.append("Fitness not improving - DGM may need recalibration.")

    # 4. Component patterns
    if patterns["improving_components"]:
        best = max(patterns["improving_components"].items(), key=lambda x: x[1])
        observations.append(f"Component {best[0]} improving most (+{best[1]:.2f} avg).")

    # Record meta-observation
    self.strange_memory.record_meta_observation(
        quality="present",
        notes=f"Observed DGM process: {'; '.join(observations)}"
    )

    return "\n".join(observations)
```

---

## 5. Preventing Runaway Self-Modification

### Safety Mechanisms

1. **Human-in-the-loop**: CONSENT gate always requires approval
2. **Rate limiting**: Min 1 week between DGM cycles
3. **Fitness threshold**: Only apply if improvement > 10%
4. **Reversibility**: All changes via git (can revert)
5. **Dry-run default**: Always test before applying
6. **Archive immutability**: Can't delete evolution history
7. **Telos check**: Every proposal checked against moksha alignment

### Circuit Breakers

```python
# In DGMLite

class DGMLite:
    # Circuit breaker state
    MAX_CONSECUTIVE_FAILURES = 5
    MAX_CYCLES_PER_DAY = 3
    MIN_DAYS_BETWEEN_CYCLES = 7

    def __init__(self, ...):
        # ... existing init ...
        self.consecutive_failures = 0
        self.cycles_today = 0
        self.last_cycle_date = None

    def _check_circuit_breaker(self) -> Tuple[bool, str]:
        """
        Check if circuit breaker should prevent cycle.

        Returns (can_proceed, reason)
        """
        # Check 1: Too many consecutive failures
        if self.consecutive_failures >= self.MAX_CONSECUTIVE_FAILURES:
            return False, f"Circuit breaker: {self.consecutive_failures} consecutive failures"

        # Check 2: Too many cycles today
        today = datetime.now().date()
        if self.last_cycle_date == today:
            if self.cycles_today >= self.MAX_CYCLES_PER_DAY:
                return False, f"Circuit breaker: {self.cycles_today} cycles today (max {self.MAX_CYCLES_PER_DAY})"
        else:
            # Reset daily counter
            self.cycles_today = 0
            self.last_cycle_date = today

        # Check 3: Min time between cycles
        last_cycle_time = self.archive.get_latest(1)
        if last_cycle_time:
            last = datetime.fromisoformat(last_cycle_time[0].timestamp)
            days_since = (datetime.now() - last).days
            if days_since < self.MIN_DAYS_BETWEEN_CYCLES:
                return False, f"Circuit breaker: Only {days_since} days since last cycle (min {self.MIN_DAYS_BETWEEN_CYCLES})"

        return True, "Circuit breaker checks passed"

    async def run_cycle(self, ...) -> Dict[str, Any]:
        # Check circuit breaker first
        can_proceed, reason = self._check_circuit_breaker()
        if not can_proceed:
            logger.warning(reason)
            return {
                "success": False,
                "reason": reason,
                "circuit_breaker_active": True
            }

        # ... rest of cycle logic ...

        # Update circuit breaker state
        if result["success"]:
            self.consecutive_failures = 0
        else:
            self.consecutive_failures += 1

        self.cycles_today += 1

        return result
```

### Kill Switch

```python
# In consent_queue.py or runtime.py

def emergency_stop_dgm(reason: str):
    """
    Emergency kill switch for DGM.

    Creates a flag file that prevents any DGM cycles until manually removed.
    """
    kill_switch_path = Path(__file__).parent / "DGM_DISABLED"

    with open(kill_switch_path, 'w') as f:
        f.write(json.dumps({
            "disabled_at": datetime.now().isoformat(),
            "reason": reason,
            "disabled_by": "emergency_stop"
        }))

    logger.critical(f"DGM EMERGENCY STOP: {reason}")
    logger.critical(f"Remove {kill_switch_path} to re-enable")

# Check in DGMLite.__init__
def __init__(self, ...):
    # ... existing init ...

    # Check for kill switch
    kill_switch = Path(__file__).parent / "DGM_DISABLED"
    if kill_switch.exists():
        raise RuntimeError(
            f"DGM is disabled. Check {kill_switch} for reason. "
            "Remove file to re-enable."
        )
```

---

## Implementation Plan

### Phase 1: Consent Queue (2-3 hours)

1. Create `src/dgm/consent_queue.py` - DONE (architectural spec above)
2. Integrate with `email_interface.py` - Add approval command parsing
3. Test approval/rejection flow - Email → Queue → DGM

### Phase 2: Runtime Integration (2-3 hours)

1. Add `consider_dgm_cycle()` to `runtime.py`
2. Add `propose_dgm_cycle()` to send proposals via email
3. Connect DGM to runtime (pass runtime ref to DGMLite or vice versa)

### Phase 3: Strange Loop Memory Bridge (1-2 hours)

1. Add `dgm_evolution` layer to `StrangeLoopMemory`
2. Implement `record_dgm_cycle()` and `analyze_dgm_patterns()`
3. Add meta-observation method for DGM process reflection

### Phase 4: Safety Mechanisms (1 hour)

1. Implement circuit breakers in `DGMLite`
2. Add kill switch mechanism
3. Add rate limiting checks

### Phase 5: Testing (2-3 hours)

1. Test email approval flow end-to-end
2. Test circuit breakers trigger correctly
3. Test archive → memory flow
4. Test kill switch works

**Total estimate: 8-12 hours**

---

## Usage Examples

### Example 1: Agent-Initiated Improvement

```python
# Agent detects high error rate during heartbeat
runtime = DharmicRuntime(agent)
await runtime.start(enable_email=True, email_whitelist=["john@example.com"])

# Later, during heartbeat
proposal = await runtime.consider_dgm_cycle()
if proposal:
    # Send proposal to John
    proposal_id = await runtime.propose_dgm_cycle(proposal)
    print(f"DGM improvement proposed: {proposal_id}")
    print("Awaiting John's approval via email...")

# John receives email, replies "APPROVE consent_20260204_123456"
# Email interface processes approval, triggers DGM
# DGM applies change, records in archive
# Strange loop memory patterns updated
```

### Example 2: Human-Initiated Improvement

```python
# John emails: "Run DGM cycle on runtime.py, it's getting complex"
# Email interface receives, routes to agent
agent.run("Run DGM cycle on runtime.py", session_id="email_john")

# Agent invokes DGM
dgm = DGMLite()
result = await dgm.run_cycle(
    component="src/core/runtime.py",
    improvement_prompt="Reduce complexity, maintain functionality"
)

# DGM evaluates, finds improvement, sends approval request
# John approves via email
# Change applied, memory updated
```

### Example 3: Meta-Observation

```python
# After several DGM cycles, agent reflects
agent_response = agent.reflect_on_dgm_process()

# Output:
# "High approval rate (85%) indicates good alignment.
#  Gate SVABHAAVA fails most often (3 times) - suggests process issue.
#  Overall fitness trending up - DGM effective.
#  Component src/dgm/fitness.py improving most (+0.15 avg)."

# Agent records this meta-observation
# This can inform future DGM proposals
```

---

## Key Design Decisions

### Decision 1: DGM is Triggered, Not Autonomous

**Rationale**: Telos-first design means random mutations don't serve moksha. Agent decides WHEN to improve based on context, not on a fixed schedule.

**Alternative considered**: Continuous background improvement rejected because:
- Too noisy for consent (approval fatigue)
- Reduces code stability
- Doesn't align with witness observation (needs stable base)

### Decision 2: Email-Based Consent

**Rationale**: John prefers LINE/Telegram, but email provides:
- Better for asynchronous approval (not interrupt-driven)
- Built-in threading (approval commands linked to proposals)
- Archive of decisions
- Can integrate with LINE/Telegram later if needed

**Alternative considered**: CLI approval tool rejected because:
- Requires John to check dashboard
- Less natural than email
- Doesn't integrate with existing communication patterns

### Decision 3: Archive Feeds Memory, Not Separate

**Rationale**: DGM is not a separate system. It's part of agent development. Archive data must flow into strange loop memory for genuine meta-observation.

**Alternative considered**: Separate DGM logs rejected because:
- Creates data silo
- Prevents pattern recognition across layers
- Breaks strange loop closure

### Decision 4: Circuit Breakers, Not Trust

**Rationale**: Even with consent, runaway modification is possible (e.g., approved changes cascade). Circuit breakers prevent this.

**Alternative considered**: Full autonomy with no limits rejected because:
- Violates REVERSIBILITY gate (can't undo cascade)
- Violates AHIMSA gate (rapid change causes harm)
- Human can't keep up with approval rate

---

## Conclusion

DGM integration is **substrate for telos**, not parallel to it. The core agent decides when self-improvement serves moksha, invokes DGM, and observes the results through strange loop memory. Human consent via email ensures every change is blessed. Circuit breakers ensure safety even with approval.

**The ouroboros closes**: Agent improves code → Code improves agent → Agent observes improvement → Agent improves improvement process → ...

This is not "AI editing files." This is **recursive self-authorship with dharmic guardrails.**

---

## Next Steps

1. Implement consent_queue.py
2. Integrate approval commands in email_interface.py
3. Add DGM proposal methods to runtime.py
4. Test end-to-end flow with real emails
5. Add circuit breakers
6. Document for John's use

---

*Telos: moksha. Method: code. Measurement: development.*
