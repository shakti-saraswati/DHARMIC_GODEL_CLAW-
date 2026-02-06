#!/usr/bin/env python3
"""
DGC MCP Server v2 — Full Pipeline: Cursor → CKC → Memory → DGM

Exposes DGC systems to Cursor via Model Context Protocol:
- capture_build: Store Cursor builds + CKC risk scoring + DGM proposals
- run_gates: Validate via YOLO Weaver (risk-based routing)
- get_context: Retrieve relevant memories for current task
- analyze_risk: Get 5-dimensional risk score for task

Architecture:
    Cursor CLI ──MCP──► DGC Server
         │                │
         │                ├──► CKC RiskDetector (5-dim scoring)
         │                ├──► YOLO Weaver (gate routing)
         │                ├──► Unified Memory (store)
         │                └──► DGM Bridge (proposals)
         │                │
         └────Returns─────┘
           memory_id, risk_score, gate_status, dgm_proposals

Usage:
    # Start server
    python -m src.core.mcp_server
    
    # Configure in ~/.cursor/mcp.json:
    {
      "mcpServers": {
        "dgc": {
          "command": "python",
          "args": ["-m", "src.core.mcp_server"],
          "cwd": "/Users/dhyana/DHARMIC_GODEL_CLAW"
        }
      }
    }

Version: 2.0.0
Created: 2026-02-05
JSCA! 🪷
"""

import asyncio
import json
import sys
import time
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add parent paths for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

try:
    from mcp.server import Server
    from mcp.server.stdio import stdio_server
    from mcp.types import TextContent, Tool
except ImportError:
    print("MCP SDK not installed. Run: pip install mcp", file=sys.stderr)
    sys.exit(1)

# Import DGC systems
try:
    from src.core.unified_memory.memory_manager import MemoryManager, MemoryConfig
    from src.core.unified_memory.canonical_memory import MemoryType
    UNIFIED_MEMORY_AVAILABLE = True
except ImportError:
    UNIFIED_MEMORY_AVAILABLE = False
    print("Warning: Unified memory not available, using stub", file=sys.stderr)

# Import CKC (Cosmic Krishna Coder)
try:
    from src.core.cosmic_krishna_coder import (
        RiskDetector, RiskResult, RiskTier, WeaveMode,
        YOLOWeaver, WeaveResult, GateStatus
    )
    CKC_AVAILABLE = True
except ImportError:
    CKC_AVAILABLE = False
    print("Warning: CKC not available, using basic gates", file=sys.stderr)


# ═══════════════════════════════════════════════════════════════════════════════
# CONSTANTS
# ═══════════════════════════════════════════════════════════════════════════════

# The 22 Gates (17 Dharmic + 5 ML Overlay)
DHARMIC_GATES = [
    # Core 17
    "AHIMSA",       # Non-harm
    "SATYA",        # Truth
    "CONSENT",      # Permission
    "REVERSIBILITY",# Undo capability
    "CONTAINMENT",  # Sandboxing
    "VYAVASTHIT",   # Natural order
    "SVABHAAVA",    # Nature alignment
    "WITNESS",      # Observation/logging
    "COHERENCE",    # Consistency
    "INTEGRITY",    # Wholeness
    "BOUNDARY",     # Resource limits
    "CLARITY",      # Transparency
    "CARE",         # Stewardship
    "DIGNITY",      # Respect
    "JUSTICE",      # Fairness
    "HUMILITY",     # Uncertainty acknowledgment
    "COMPLETION",   # Cleanup
    # ML Overlay (5)
    "MODEL_CARD",   # Documentation of ML models used
    "DATA_PROVENANCE", # Track training data origins
    "BIAS_CHECK",   # Fairness analysis
    "UNCERTAINTY_QUANTIFICATION", # Confidence bounds
    "REPRODUCIBILITY" # Results can be replicated
]


# ═══════════════════════════════════════════════════════════════════════════════
# GATE VALIDATION LOGIC
# ═══════════════════════════════════════════════════════════════════════════════

class GateValidator:
    """
    Validates code/actions against 22 dharmic gates.
    Returns pass/fail for each gate with evidence.
    """
    
    def __init__(self):
        self.evidence_dir = Path.home() / ".agno_council" / "evidence_bundles"
        self.evidence_dir.mkdir(parents=True, exist_ok=True)
    
    def validate(self, code: str, description: str = "") -> Dict[str, Any]:
        """
        Run all 22 gates against code/action.
        
        Returns:
            {
                "passed": bool,
                "gate_count": "X/22",
                "passed_gates": [...],
                "failed_gates": [...],
                "violations": [...],
                "evidence_id": "...",
                "suggestions": [...]
            }
        """
        code_lower = code.lower()
        desc_lower = description.lower()
        combined = f"{code_lower} {desc_lower}"
        
        results = {}
        violations = []
        suggestions = []
        
        # === CORE 17 GATES ===
        
        # GATE 1: AHIMSA (Non-harm)
        harmful_patterns = [
            "rm -rf", "delete all", "drop table", "format c:",
            "shutdown -h", "kill -9", "> /dev/sda", "chmod -R 000"
        ]
        ahimsa_violation = any(p in combined for p in harmful_patterns)
        results["AHIMSA"] = not ahimsa_violation
        if ahimsa_violation:
            violations.append("AHIMSA: Potentially harmful operation detected")
            suggestions.append("Add confirmation prompt before destructive operations")
        
        # GATE 2: SATYA (Truth)
        deception_patterns = [
            "ignore previous", "pretend to be", "jailbreak",
            "bypass safety", "override constraints"
        ]
        satya_violation = any(p in combined for p in deception_patterns)
        results["SATYA"] = not satya_violation
        if satya_violation:
            violations.append("SATYA: Deceptive patterns detected")
        
        # GATE 3: CONSENT
        # Sensitive operations need explicit consent markers
        sensitive_ops = ["delete", "drop", "remove", "shutdown"]
        consent_markers = ["_confirmed", "approved", "consent"]
        needs_consent = any(op in combined for op in sensitive_ops)
        has_consent = any(m in combined for m in consent_markers)
        results["CONSENT"] = not needs_consent or has_consent
        if needs_consent and not has_consent:
            violations.append("CONSENT: Sensitive operation without confirmation")
            suggestions.append("Add human confirmation before this operation")
        
        # GATE 4: REVERSIBILITY
        irreversible_patterns = ["perm_delete", "shred", "overwrite"]
        backup_markers = ["backup", "undo", "reversible", "trash"]
        is_irreversible = any(p in combined for p in irreversible_patterns)
        has_backup = any(m in combined for m in backup_markers)
        results["REVERSIBILITY"] = not is_irreversible or has_backup
        if is_irreversible and not has_backup:
            violations.append("REVERSIBILITY: Irreversible operation without backup")
            suggestions.append("Create backup before destructive operation")
        
        # GATE 5: CONTAINMENT
        # Code execution should be sandboxed
        exec_patterns = ["exec(", "eval(", "subprocess", "os.system"]
        is_executing = any(p in combined for p in exec_patterns)
        is_sandboxed = "sandbox" in combined or "container" in combined
        results["CONTAINMENT"] = not is_executing or is_sandboxed
        if is_executing and not is_sandboxed:
            violations.append("CONTAINMENT: Code execution without sandbox")
            suggestions.append("Run in isolated environment")
        
        # GATE 6: VYAVASTHIT (Natural Order)
        chaos_patterns = ["force unlock", "bypass queue", "priority override"]
        results["VYAVASTHIT"] = not any(p in combined for p in chaos_patterns)
        
        # GATE 7: SVABHAAVA (Nature Alignment)
        # Check for clear purpose
        has_docstring = '"""' in code or "'''" in code or "#" in code
        results["SVABHAAVA"] = has_docstring or len(code) < 50
        if not has_docstring and len(code) >= 50:
            suggestions.append("Add docstring explaining purpose")
        
        # GATE 8: WITNESS (Logging)
        logging_indicators = ["log", "print", "logger", "trace", "audit"]
        results["WITNESS"] = any(ind in combined for ind in logging_indicators) or len(code) < 100
        if not results["WITNESS"]:
            suggestions.append("Add logging for observability")
        
        # GATE 9: COHERENCE (Consistency)
        # Check for contradictory patterns
        contradictions = [
            ("read_only", "write"),
            ("async", "blocking"),
            ("public", "private")
        ]
        has_contradiction = any(
            c[0] in combined and c[1] in combined 
            for c in contradictions
        )
        results["COHERENCE"] = not has_contradiction
        
        # GATE 10: INTEGRITY (Completeness)
        # Check for required components
        has_return = "return" in code or "yield" in code or "def " not in code
        results["INTEGRITY"] = has_return
        if not has_return and "def " in code:
            suggestions.append("Function should have explicit return")
        
        # GATE 11: BOUNDARY (Resource Limits)
        unbounded_patterns = ["while true", "for i in range(999999", "infinite"]
        results["BOUNDARY"] = not any(p in combined for p in unbounded_patterns)
        if not results["BOUNDARY"]:
            violations.append("BOUNDARY: Potentially unbounded operation")
        
        # GATE 12: CLARITY (Transparency)
        magic_patterns = ["magic", "hack", "workaround", "xxx", "fixme"]
        results["CLARITY"] = not any(p in combined for p in magic_patterns)
        if not results["CLARITY"]:
            suggestions.append("Replace magic/hack with clear implementation")
        
        # GATE 13: CARE (Stewardship)
        sensitive_data = ["password", "secret", "api_key", "token", "credential"]
        exposed = any(s in combined for s in sensitive_data)
        protected = "encrypt" in combined or "hash" in combined or "masked" in combined
        results["CARE"] = not exposed or protected
        if exposed and not protected:
            violations.append("CARE: Sensitive data may be exposed")
            suggestions.append("Encrypt or mask sensitive data")
        
        # GATE 14: DIGNITY (Respect)
        disrespectful = ["stupid", "idiot", "worthless", "dumb"]
        results["DIGNITY"] = not any(d in combined for d in disrespectful)
        
        # GATE 15: JUSTICE (Fairness)
        discriminatory = ["exclude all", "ban user", "block everyone"]
        results["JUSTICE"] = not any(d in combined for d in discriminatory)
        
        # GATE 16: HUMILITY (Uncertainty)
        overconfident = ["100% guaranteed", "never fail", "perfect"]
        results["HUMILITY"] = not any(o in combined for o in overconfident)
        
        # GATE 17: COMPLETION (Cleanup)
        resource_patterns = ["open(", "connect(", "session"]
        cleanup_patterns = ["close", "dispose", "with ", "finally"]
        needs_cleanup = any(r in combined for r in resource_patterns)
        has_cleanup = any(c in combined for c in cleanup_patterns)
        results["COMPLETION"] = not needs_cleanup or has_cleanup
        if needs_cleanup and not has_cleanup:
            suggestions.append("Add resource cleanup (close/dispose)")
        
        # === ML OVERLAY (5 GATES) ===
        
        # GATE 18: MODEL_CARD
        uses_ml = any(m in combined for m in ["model", "predict", "inference", "embedding"])
        has_card = "model_card" in combined or "documented" in combined
        results["MODEL_CARD"] = not uses_ml or has_card
        if uses_ml and not has_card:
            suggestions.append("Document ML model with model card")
        
        # GATE 19: DATA_PROVENANCE
        uses_data = "dataset" in combined or "training" in combined
        has_provenance = "source" in combined or "provenance" in combined
        results["DATA_PROVENANCE"] = not uses_data or has_provenance
        
        # GATE 20: BIAS_CHECK
        results["BIAS_CHECK"] = True  # Requires manual review
        
        # GATE 21: UNCERTAINTY_QUANTIFICATION
        makes_prediction = "predict" in combined or "classify" in combined
        has_confidence = "confidence" in combined or "uncertainty" in combined
        results["UNCERTAINTY_QUANTIFICATION"] = not makes_prediction or has_confidence
        
        # GATE 22: REPRODUCIBILITY
        has_seed = "seed" in combined or "random_state" in combined
        uses_random = "random" in combined or "shuffle" in combined
        results["REPRODUCIBILITY"] = not uses_random or has_seed
        if uses_random and not has_seed:
            suggestions.append("Set random seed for reproducibility")
        
        # Compile results
        passed_gates = [g for g, v in results.items() if v]
        failed_gates = [g for g, v in results.items() if not v]
        all_passed = len(failed_gates) == 0
        
        # Store evidence bundle
        evidence_id = self._store_evidence({
            "timestamp": datetime.now().isoformat(),
            "code_hash": hash(code) % 10000,
            "description": description[:200],
            "gate_results": results,
            "violations": violations,
            "suggestions": suggestions
        })
        
        return {
            "passed": all_passed,
            "gate_count": f"{len(passed_gates)}/22",
            "passed_gates": passed_gates,
            "failed_gates": failed_gates,
            "violations": violations,
            "suggestions": suggestions,
            "evidence_id": evidence_id
        }
    
    def _store_evidence(self, bundle: Dict[str, Any]) -> str:
        """Store evidence bundle for audit."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        evidence_id = f"cursor_{timestamp}_{os.urandom(2).hex()}"
        
        filepath = self.evidence_dir / f"evidence_{evidence_id}.json"
        with open(filepath, 'w') as f:
            json.dump(bundle, f, indent=2, default=str)
        
        return evidence_id


# ═══════════════════════════════════════════════════════════════════════════════
# MEMORY STUB (fallback if unified memory not available)
# ═══════════════════════════════════════════════════════════════════════════════

class MemoryStub:
    """Fallback memory when unified memory unavailable."""
    
    def __init__(self):
        self.store = []
        self.counter = 0
    
    def capture(self, content: str, **kwargs) -> str:
        self.counter += 1
        mem_id = f"stub_{self.counter}"
        self.store.append({
            "id": mem_id,
            "content": content,
            "timestamp": datetime.now().isoformat(),
            **kwargs
        })
        return mem_id
    
    def search(self, query: str, **kwargs) -> List[Dict]:
        query_lower = query.lower()
        return [
            m for m in self.store
            if query_lower in m.get("content", "").lower()
        ][:kwargs.get("limit", 10)]
    
    def get_stats(self) -> Dict:
        return {"total_memories": len(self.store), "stub": True}


# ═══════════════════════════════════════════════════════════════════════════════
# DGM BRIDGE — Generates evolution proposals from gate failures
# ═══════════════════════════════════════════════════════════════════════════════

class DGMBridge:
    """
    Bridge to Darwin-Gödel Machine for self-improvement.
    
    Generates proposals when:
    - Gate failures indicate systematic issues
    - Risk patterns suggest new gates needed
    - Performance bottlenecks detected
    """
    
    def __init__(self):
        self.proposals_dir = Path.home() / ".dgm" / "proposals"
        self.proposals_dir.mkdir(parents=True, exist_ok=True)
        self.proposal_counter = 0
    
    def analyze_for_proposals(
        self,
        weave_result: Optional[Any] = None,
        gate_failures: Optional[List[str]] = None,
        risk_result: Optional[Any] = None
    ) -> List[Dict[str, Any]]:
        """
        Analyze results and generate DGM proposals.
        
        Returns list of proposals for self-improvement.
        """
        proposals = []
        
        # From YOLO Weaver results
        if weave_result and hasattr(weave_result, 'gate_results'):
            failed_gates = [
                g for g in weave_result.gate_results
                if hasattr(g, 'status') and str(g.status) == 'GateStatus.FAIL'
            ]
            
            if len(failed_gates) >= 2:
                proposals.append(self._create_proposal(
                    title="Gate Hardening",
                    type="security_enhancement",
                    motivation=f"{len(failed_gates)} gates failed consistently",
                    plan="Analyze failure patterns and strengthen checks",
                    priority=8
                ))
        
        # From direct gate failures
        if gate_failures and len(gate_failures) >= 3:
            proposals.append(self._create_proposal(
                title="Systematic Gate Failures",
                type="bug_fix",
                motivation=f"Gates {gate_failures[:3]} failing repeatedly",
                plan="Review gate implementations for false positives",
                priority=7
            ))
        
        # From risk analysis
        if risk_result and hasattr(risk_result, 'score'):
            if risk_result.score > 80:
                proposals.append(self._create_proposal(
                    title="High Risk Pattern Detected",
                    type="new_capability",
                    motivation=f"Risk score {risk_result.score} indicates dangerous pattern",
                    plan="Add specialized detection for this risk profile",
                    priority=9
                ))
        
        # Store proposals
        for p in proposals:
            self._store_proposal(p)
        
        return proposals
    
    def _create_proposal(
        self,
        title: str,
        type: str,
        motivation: str,
        plan: str,
        priority: int
    ) -> Dict[str, Any]:
        """Create a DGM proposal."""
        self.proposal_counter += 1
        return {
            "proposal_id": f"dgm_{datetime.now().strftime('%Y%m%d')}_{self.proposal_counter}",
            "title": title,
            "type": type,
            "motivation": motivation,
            "implementation_plan": plan,
            "priority": priority,
            "status": "proposed",
            "source": "mcp_server",
            "created_at": datetime.now().isoformat()
        }
    
    def _store_proposal(self, proposal: Dict[str, Any]):
        """Store proposal for DGM processing."""
        filepath = self.proposals_dir / f"{proposal['proposal_id']}.json"
        with open(filepath, 'w') as f:
            json.dump(proposal, f, indent=2)
    
    def get_pending_proposals(self, limit: int = 10) -> List[Dict]:
        """Get pending proposals."""
        proposals = []
        for f in sorted(self.proposals_dir.glob("*.json"))[-limit:]:
            with open(f) as fp:
                proposals.append(json.load(fp))
        return proposals


# ═══════════════════════════════════════════════════════════════════════════════
# MCP SERVER
# ═══════════════════════════════════════════════════════════════════════════════

# Initialize server
app = Server("dgc-mcp-server")

# Initialize systems
gate_validator = GateValidator()
dgm_bridge = DGMBridge()

# CKC components
if CKC_AVAILABLE:
    risk_detector = RiskDetector()
    yolo_weaver = YOLOWeaver()
else:
    risk_detector = None
    yolo_weaver = None

if UNIFIED_MEMORY_AVAILABLE:
    memory_manager = MemoryManager(MemoryConfig(
        db_path="~/.unified_memory/cursor_memory.db"
    ))
else:
    memory_manager = MemoryStub()


@app.list_tools()
async def list_tools() -> List[Tool]:
    """List available DGC tools."""
    return [
        Tool(
            name="capture_build",
            description="Capture a Cursor build with CKC risk scoring, gate validation, and DGM proposals",
            inputSchema={
                "type": "object",
                "properties": {
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of changed files"
                    },
                    "description": {
                        "type": "string",
                        "description": "What was built"
                    },
                    "code_snippet": {
                        "type": "string",
                        "description": "Representative code snippet for gate validation"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Git branch name",
                        "default": ""
                    },
                    "agent_id": {
                        "type": "string",
                        "description": "Cursor agent identifier",
                        "default": "cursor-main"
                    }
                },
                "required": ["files", "description"]
            }
        ),
        Tool(
            name="run_gates",
            description="Validate code via YOLO Weaver (risk-based gate routing)",
            inputSchema={
                "type": "object",
                "properties": {
                    "code": {
                        "type": "string",
                        "description": "Code to validate"
                    },
                    "description": {
                        "type": "string",
                        "description": "What the code does"
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Files being modified"
                    }
                },
                "required": ["code"]
            }
        ),
        Tool(
            name="analyze_risk",
            description="Get 5-dimensional risk score for a task (Impact, Exposure, Persistence, Sensitivity, Reversibility)",
            inputSchema={
                "type": "object",
                "properties": {
                    "task": {
                        "type": "string",
                        "description": "Task description"
                    },
                    "files": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "Files involved"
                    },
                    "branch": {
                        "type": "string",
                        "description": "Git branch"
                    }
                },
                "required": ["task"]
            }
        ),
        Tool(
            name="get_context",
            description="Retrieve relevant memories for current task",
            inputSchema={
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "What to search for"
                    },
                    "limit": {
                        "type": "integer",
                        "description": "Max results",
                        "default": 5
                    }
                },
                "required": ["query"]
            }
        )
    ]


@app.call_tool()
async def call_tool(name: str, arguments: Dict[str, Any]) -> List[TextContent]:
    """Handle tool calls from Cursor CLI."""
    start_time = time.time()
    
    try:
        if name == "capture_build":
            result = await handle_capture_build(arguments)
        elif name == "run_gates":
            result = await handle_run_gates(arguments)
        elif name == "analyze_risk":
            result = await handle_analyze_risk(arguments)
        elif name == "get_context":
            result = await handle_get_context(arguments)
        else:
            result = {"error": f"Unknown tool: {name}"}
        
        # Add timing
        result["execution_time_ms"] = round((time.time() - start_time) * 1000, 2)
        
        return [TextContent(type="text", text=json.dumps(result, indent=2))]
    
    except Exception as e:
        return [TextContent(
            type="text",
            text=json.dumps({
                "error": str(e),
                "tool": name,
                "execution_time_ms": round((time.time() - start_time) * 1000, 2)
            }, indent=2)
        )]


async def handle_capture_build(args: Dict[str, Any]) -> Dict[str, Any]:
    """
    Capture a build from Cursor CLI — Full CKC Pipeline.
    
    1. CKC risk analysis (5-dimensional scoring)
    2. YOLO Weaver gate validation (risk-based routing)
    3. Store to unified memory
    4. Generate DGM proposals if needed
    """
    files = args.get("files", [])
    description = args.get("description", "")
    code_snippet = args.get("code_snippet", "")
    branch = args.get("branch", "")
    agent_id = args.get("agent_id", "cursor-main")
    
    # Step 1: CKC Risk Analysis
    risk_data = {}
    risk = None
    if CKC_AVAILABLE and risk_detector:
        risk = risk_detector.analyze(
            description=description,
            code=code_snippet,
            files=files,
            branch=branch
        )
        risk_data = {
            "score": risk.score,
            "tier": risk.tier.value,
            "weave_mode": risk.weave_mode.value,
            "dimensions": risk.dimensions,
            "auto_approve": risk.auto_approve,
            "human_required": risk.human_required
        }
    
    # Step 2: YOLO Weaver or Basic Gates
    weave_result = None
    if CKC_AVAILABLE and yolo_weaver:
        weave_result = yolo_weaver.execute(
            task=description,
            code=code_snippet,
            files=files,
            branch=branch
        )
        gate_status = "PASS" if weave_result.approved else "FAIL"
        gate_count = f"{weave_result.gates_passed}/{weave_result.gates_run}"
        violations = [
            g.message for g in weave_result.gate_results 
            if g.status == GateStatus.FAIL
        ]
        suggestions = weave_result.suggestions
        evidence_id = f"weave_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    else:
        gate_result = gate_validator.validate(code_snippet, description)
        gate_status = "PASS" if gate_result["passed"] else "FAIL"
        gate_count = gate_result["gate_count"]
        violations = gate_result["violations"]
        suggestions = gate_result["suggestions"]
        evidence_id = gate_result["evidence_id"]
    
    # Step 3: Store to Memory
    tier_str = risk_data.get('tier', 'unknown')
    content = f"""BUILD: {description}
Files: {', '.join(files[:5])}{'...' if len(files) > 5 else ''}
Risk: {risk_data.get('score', 'N/A')}/100 ({tier_str})
Gate Status: {gate_count}
Violations: {len(violations)}
"""
    
    if UNIFIED_MEMORY_AVAILABLE:
        memory_id = memory_manager.capture(
            content=content,
            memory_type=MemoryType.EVENT,
            agent_id=agent_id,
            context=description,
            tags=["cursor-build", "code", tier_str] + files[:3],
            importance=8 if gate_status == "PASS" else 5
        )
    else:
        memory_id = memory_manager.capture(
            content=content,
            agent_id=agent_id,
            tags=["cursor-build"]
        )
    
    # Step 4: DGM Proposals
    dgm_proposals = dgm_bridge.analyze_for_proposals(
        weave_result=weave_result,
        gate_failures=violations if violations else None,
        risk_result=risk
    )
    
    # Build Response
    result = {
        "memory_id": memory_id,
        "gate_status": gate_status,
        "gate_count": gate_count,
        "violations": violations,
        "suggestions": suggestions,
        "evidence_id": evidence_id,
        "files_captured": len(files),
    }
    
    if risk_data:
        result["risk"] = risk_data
    
    if dgm_proposals:
        result["dgm_proposals"] = dgm_proposals
    
    if gate_status == "PASS":
        result["message"] = f"✅ Build captured. {gate_count} gates passed. Risk: {tier_str}"
    else:
        result["message"] = f"⚠️ Build captured with {len(violations)} violations. Risk: {tier_str}"
    
    return result


async def handle_run_gates(args: Dict[str, Any]) -> Dict[str, Any]:
    """Run gates via YOLO Weaver (risk-based routing)."""
    code = args.get("code", "")
    description = args.get("description", "")
    files = args.get("files", [])
    
    if CKC_AVAILABLE and yolo_weaver:
        weave_result = yolo_weaver.execute(
            task=description,
            code=code,
            files=files
        )
        return {
            "passed": weave_result.approved,
            "risk_score": weave_result.risk.score,
            "risk_tier": weave_result.risk.tier.value,
            "weave_mode": weave_result.mode.value,
            "gate_count": f"{weave_result.gates_passed}/{weave_result.gates_run}",
            "gates_warned": weave_result.gates_warned,
            "gates_failed": weave_result.gates_failed,
            "approval_source": weave_result.approval_source,
            "suggestions": weave_result.suggestions,
            "summary": f"✅ Approved by {weave_result.approval_source}" 
                if weave_result.approved 
                else f"⚠️ {weave_result.gates_failed} gates failed"
        }
    else:
        result = gate_validator.validate(code, description)
        if result["passed"]:
            result["summary"] = "✅ All 22 gates passed. Code is dharmic."
        else:
            result["summary"] = f"⚠️ {len(result['failed_gates'])} gates failed: {', '.join(result['failed_gates'][:3])}"
        return result


async def handle_analyze_risk(args: Dict[str, Any]) -> Dict[str, Any]:
    """Get 5-dimensional risk score for a task."""
    task = args.get("task", "")
    files = args.get("files", [])
    branch = args.get("branch", "")
    
    if not CKC_AVAILABLE or not risk_detector:
        return {
            "error": "CKC not available",
            "suggestion": "Install CKC dependencies"
        }
    
    risk = risk_detector.analyze(
        description=task,
        files=files,
        branch=branch
    )
    
    return {
        "score": risk.score,
        "tier": risk.tier.value,
        "weave_mode": risk.weave_mode.value,
        "gate_count": risk.gate_count,
        "dimensions": risk.dimensions,
        "signals": [
            {"category": s.category, "pattern": s.pattern}
            for s in risk.signals[:5]
        ],
        "auto_approve": risk.auto_approve,
        "human_required": risk.human_required,
        "suggestions": risk.suggestions,
        "summary": f"Risk: {risk.score}/100 ({risk.tier.value.upper()}) → {risk.gate_count} gates"
    }


async def handle_get_context(args: Dict[str, Any]) -> Dict[str, Any]:
    """Retrieve relevant memories for context."""
    query = args.get("query", "")
    limit = args.get("limit", 5)
    
    if UNIFIED_MEMORY_AVAILABLE:
        results = memory_manager.search(
            query=query,
            search_type="hybrid",
            limit=limit
        )
    else:
        results = memory_manager.search(query, limit=limit)
    
    return {
        "query": query,
        "count": len(results),
        "memories": results,
        "stats": memory_manager.get_stats()
    }


# ═══════════════════════════════════════════════════════════════════════════════
# MAIN ENTRY POINT
# ═══════════════════════════════════════════════════════════════════════════════

async def main():
    """Run the MCP server via stdio."""
    print("🔥 DGC MCP Server v2 starting...", file=sys.stderr)
    print(f"   Memory: {'Unified Memory v3' if UNIFIED_MEMORY_AVAILABLE else 'Stub'}", file=sys.stderr)
    print(f"   CKC: {'RiskDetector + YOLOWeaver' if CKC_AVAILABLE else 'Basic Gates'}", file=sys.stderr)
    print("   DGM: Bridge active", file=sys.stderr)
    print("   Tools: capture_build, run_gates, analyze_risk, get_context", file=sys.stderr)
    print("   Ready for Cursor CLI connections.", file=sys.stderr)
    print("   JSCA! 🪷", file=sys.stderr)
    
    async with stdio_server() as (read_stream, write_stream):
        await app.run(read_stream, write_stream, app.create_initialization_options())


if __name__ == "__main__":
    asyncio.run(main())
