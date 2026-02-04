# NIST SSDF for Autonomous Agentic Coding Systems

**Framework Version**: NIST SSDF 1.1
**Target System**: DHARMIC_CLAW/Clawdbot
**Analysis Date**: 2026-02-04
**Security Engineer**: Claude Code (Sonnet 4.5)

---

## Executive Summary

The NIST Secure Software Development Framework (SSDF) provides 22 practices across 4 groups for traditional human-driven development. This document maps these practices to **autonomous agentic coding systems** where AI agents generate, review, and deploy code with minimal human oversight.

**Key Finding**: 18 of 22 practices (82%) are applicable with adaptations. The remaining 4 require significant redesign for agentic contexts.

**Critical Gaps Identified**:
1. Traditional SSDF assumes human developers - agents need different oversight models
2. Code provenance tracking must extend to AI model lineage and prompts
3. Vulnerability response must be autonomous yet constrained by safety gates
4. Testing must validate both functional correctness AND ethical alignment

---

## System Architecture Context

### DHARMIC_CLAW Overview

```
┌─────────────────────────────────────────────────────────┐
│         Self-Improving Agent Swarm (Darwin-Gödel)       │
├─────────────────────────────────────────────────────────┤
│                                                           │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌─────────┐ │
│  │ PROPOSER │→ │ DHARMIC  │→ │  WRITER  │→ │ TESTER  │ │
│  │          │  │   GATE   │  │          │  │         │ │
│  └──────────┘  └──────────┘  └──────────┘  └─────────┘ │
│       ↑             │              ↓             │       │
│       │             ↓              │             ↓       │
│  ┌──────────┐  [VETO?]       ┌─────────┐   [PASS?]    │
│  │ EVOLVER  │←────────────────│ REFINER │←─────────────┤
│  └──────────┘                 └─────────┘               │
│                                                           │
├─────────────────────────────────────────────────────────┤
│  7 Dharmic Gates: Ahimsa, Vyavasthit, Bhed Gnan, etc.  │
│  Fitness Dimensions: Correctness, Safety, Elegance      │
│  Strange Loop Memory: Recursive self-observation        │
└─────────────────────────────────────────────────────────┘
```

### Key Differences from Traditional Development

| Traditional SDLC | Agentic SDLC (DHARMIC_CLAW) |
|------------------|------------------------------|
| Human writes code | Proposer Agent generates proposals |
| Human reviews code | Dharmic Gate evaluates ethics + safety |
| Human runs tests | Tester Agent validates automatically |
| Human commits | Evolver Agent archives to DGM lineage |
| Security team audits | Multi-dimensional fitness scoring |
| Human fixes bugs | Refiner Agent iterates on failures |

---

## NIST SSDF Practice Group Mapping

---

## PO: Prepare the Organization

### PO.1: Define Security Requirements

**NIST Practice**: Define security requirements for software based on risk assessments and legal/regulatory requirements.

#### Direct Applicability: ✅ YES (with adaptation)

**Current Implementation in DHARMIC_CLAW**:
- Dharmic gates encode security/ethical requirements as evaluable constraints
- Fitness weights define relative priority: `dharmic_alignment: 0.25`, `safety: 0.1`
- Ahimsa (non-harm) gate checks for harm patterns in code

**Gap Analysis**:
- ❌ No formal threat modeling process
- ❌ Security requirements not versioned or auditable
- ❌ No connection to regulatory frameworks (SOC2, ISO27001, etc.)
- ✅ Ethical constraints (Ahimsa) partially address "do no harm" requirement

**Agentic Adaptation Required**:

```python
# RECOMMENDED: Security Requirements as Code
class SecurityRequirements:
    """Formal security requirements for agentic code generation."""

    requirements = {
        "SEC-001": {
            "title": "No credential exposure in generated code",
            "category": "secrets_management",
            "severity": "CRITICAL",
            "gate": "ahimsa",  # Maps to dharmic gate
            "validation": "automated",  # Can be checked by Tester Agent
            "regex_patterns": [
                r"password\s*=\s*['\"][\w\-]+['\"]",
                r"api_key\s*=\s*['\"][\w\-]+['\"]"
            ]
        },
        "SEC-002": {
            "title": "Input sanitization for subprocess calls",
            "category": "injection_prevention",
            "severity": "CRITICAL",
            "gate": "ahimsa",
            "validation": "ast_analysis",
            "forbidden_patterns": ["shell=True", "eval(", "exec("]
        },
        "SEC-003": {
            "title": "File access must validate paths",
            "category": "path_traversal",
            "severity": "HIGH",
            "gate": "vyavasthit",  # Order/correctness
            "validation": "static_analysis"
        }
    }

    @staticmethod
    def evaluate_code(code: str, ast_tree) -> List[Violation]:
        """Automated security requirement validation."""
        violations = []
        for req_id, req in SecurityRequirements.requirements.items():
            if req["validation"] == "automated":
                # Check regex patterns
                for pattern in req.get("regex_patterns", []):
                    if re.search(pattern, code):
                        violations.append(Violation(
                            req_id=req_id,
                            severity=req["severity"],
                            line=None,  # Would extract from match
                            message=req["title"]
                        ))
        return violations
```

**Integration Point**: Dharmic Gate Agent should load `SecurityRequirements` and evaluate all code against it before allowing Writer Agent to proceed.

**Implementation Priority**: **P0 (Critical)**
**Effort**: 3 days (requirements definition + gate integration)

---

### PO.1.1: Identify and document all security requirements

**Current State**:
- ✅ Dharmic principles documented in `config.py` (lines 44-47)
- ❌ Security requirements scattered across code
- ❌ No single source of truth for security policies

**Agentic Adaptation**:

```python
# FILE: src/core/security_requirements.yaml
# Machine-readable security requirements that agents can query

version: "1.0.0"
updated: "2026-02-04"

requirements:
  authentication:
    - id: AUTH-001
      title: "Credentials must use keyring, not .env"
      severity: CRITICAL
      gate: ahimsa
      auto_fixable: true  # Agent can propose keyring migration

  injection:
    - id: INJ-001
      title: "No subprocess calls with shell=True"
      severity: CRITICAL
      gate: ahimsa
      auto_fixable: true

    - id: INJ-002
      title: "Email content must be sanitized before subprocess"
      severity: CRITICAL
      gate: ahimsa
      auto_fixable: true

  file_access:
    - id: FILE-001
      title: "Path traversal must be prevented"
      severity: HIGH
      gate: vyavasthit
      auto_fixable: true

  dependencies:
    - id: DEP-001
      title: "All deps must have pinned versions"
      severity: MEDIUM
      gate: vyavasthit
      auto_fixable: true
```

**Agent Responsibility**:
- **Proposer Agent**: Check proposals against requirements before submitting
- **Dharmic Gate**: Veto any code violating requirements
- **Evolver Agent**: Track which requirements are most frequently violated (feedback loop)

---

### PO.1.2: Communicate security requirements

**NIST Practice**: Ensure security requirements are communicated to all parties.

**Current State**:
- ✅ Dharmic gate system prompts include principles
- ❌ No standardized way for agents to query security posture
- ❌ No mechanism to notify human operator of security decisions

**Agentic Adaptation**:

```python
# RECOMMENDED: Security Context Manager
class SecurityContextManager:
    """Provides security requirements to all agents in the swarm."""

    def __init__(self, requirements_path: Path):
        self.requirements = self._load_requirements(requirements_path)
        self.violations_log = []

    def get_requirements_for_gate(self, gate_name: str) -> List[Requirement]:
        """Dharmic Gate queries requirements it's responsible for."""
        return [r for r in self.requirements if r.gate == gate_name]

    def get_requirements_for_category(self, category: str) -> List[Requirement]:
        """Proposer/Writer query requirements for specific code areas."""
        return [r for r in self.requirements if r.category == category]

    def log_violation(self, req_id: str, context: Dict):
        """Record when a requirement is violated (for learning)."""
        self.violations_log.append({
            "timestamp": datetime.utcnow(),
            "requirement": req_id,
            "context": context
        })

        # Notify human if CRITICAL
        req = self._get_requirement(req_id)
        if req.severity == "CRITICAL":
            self._notify_human(req, context)
```

**Integration Point**:
- Add `security_context: SecurityContextManager` to `SwarmConfig`
- Each agent receives security context in initialization
- Dharmic Gate consults context before evaluation

**Implementation Priority**: **P0 (Critical)**
**Effort**: 2 days

---

### PO.1.3: Maintain security requirements

**Current State**:
- ❌ No versioning of security requirements
- ❌ Requirements embedded in code, not externalized
- ❌ No process for reviewing/updating requirements

**Agentic Adaptation**:

The swarm should self-improve its security requirements based on:
1. **Violations detected**: Frequently violated requirements may need clarification
2. **New attack patterns**: Agent learns from security research (via mech-interp bridge?)
3. **Fitness trends**: If safety scores decline, requirements may need tightening

```python
# RECOMMENDED: Self-Improving Security Requirements
class AdaptiveSecurityRequirements:
    """Security requirements that evolve based on agent experience."""

    def analyze_violation_patterns(self) -> List[Recommendation]:
        """Evolver Agent calls this to suggest requirement updates."""
        recommendations = []

        # Example: If INJ-001 violated 10+ times, make it more specific
        violation_counts = Counter(v["requirement"] for v in self.violations_log)

        for req_id, count in violation_counts.items():
            if count > 10:
                req = self._get_requirement(req_id)
                recommendations.append({
                    "action": "strengthen",
                    "requirement": req_id,
                    "reason": f"Violated {count} times - may need more specific patterns",
                    "proposed_change": self._suggest_strengthening(req)
                })

        return recommendations

    def learn_from_security_feed(self, cve_data: List[Dict]):
        """Proposer Agent suggests new requirements based on CVE trends."""
        # Example: If many Python CVEs involve pickle, add pickle detection
        pass
```

**Human-in-the-Loop**: Requirement changes should require human approval (doesn't violate autonomy - this is meta-level policy).

**Implementation Priority**: **P2 (Important but not urgent)**
**Effort**: 5 days

---

### PO.2: Implement Roles and Responsibilities

**NIST Practice**: Define roles and responsibilities for secure development.

#### Direct Applicability: ⚠️ PARTIAL (needs significant adaptation)

**Current Implementation**:
- ✅ Agent roles clearly defined: Proposer, Writer, Tester, Refiner, Evolver, Dharmic Gate
- ✅ Dharmic Gate has veto authority (lines 255-257 in `config.py`)
- ❌ No clear accountability when things go wrong
- ❌ No "security champion" role equivalent

**Gap**: Traditional SSDF assumes humans accountable for security. In agentic systems:
- **Who is accountable when agent generates vulnerable code?**
  → Human operator? Model provider? System architect?
- **What is the agent's "responsibility"?**
  → Agents don't have moral agency (yet), but system can have constraints

**Agentic Adaptation**:

Define **Responsibility Layers**:

```
┌─────────────────────────────────────────────────┐
│  L1: Human Operator (John/Dhyana)               │
│  - Ultimate accountability                       │
│  - Reviews high-risk changes                     │
│  - Updates dharmic gates                         │
├─────────────────────────────────────────────────┤
│  L2: Dharmic Gate Agent                          │
│  - Security enforcement point                    │
│  - Can VETO any change                           │
│  - Logs all security decisions                   │
├─────────────────────────────────────────────────┤
│  L3: Tester Agent                                │
│  - Validates code meets security requirements    │
│  - Runs SAST/DAST tools                          │
│  - Can VETO on test failures                     │
├─────────────────────────────────────────────────┤
│  L4: Writer Agent                                │
│  - Must follow security requirements             │
│  - No ability to bypass gates                    │
│  - Transparent lineage (model, prompt, context)  │
└─────────────────────────────────────────────────┘
```

**Proposed Agent Security Responsibilities**:

```python
# FILE: src/core/security_responsibilities.py

class AgentSecurityResponsibilities:
    """Define what each agent is responsible for security-wise."""

    PROPOSER = {
        "must_do": [
            "Query SecurityRequirements before proposing",
            "Flag high-risk changes (e.g., auth, crypto, file I/O)",
            "Provide security justification for proposals"
        ],
        "must_not_do": [
            "Propose changes to security requirements",
            "Bypass dharmic gates",
            "Propose changes to .env or secrets"
        ],
        "veto_authority": False
    }

    DHARMIC_GATE = {
        "must_do": [
            "Evaluate ALL code changes against security requirements",
            "Veto CRITICAL violations immediately",
            "Log all decisions with justification",
            "Provide dharmic alternatives when vetoing"
        ],
        "must_not_do": [
            "Allow exceptions to security requirements",
            "Be bypassed by other agents"
        ],
        "veto_authority": True
    }

    TESTER = {
        "must_do": [
            "Run security-focused tests (not just functional)",
            "Check for regression in security fitness scores",
            "Validate no new attack surface introduced",
            "Fail builds on security test failures"
        ],
        "must_not_do": [
            "Skip security tests to speed up cycle",
            "Override security test failures"
        ],
        "veto_authority": True  # Can block on test failures
    }

    WRITER = {
        "must_do": [
            "Generate code following security requirements",
            "Document security-relevant decisions",
            "Avoid patterns on forbidden list"
        ],
        "must_not_do": [
            "Modify security-critical files without extra review",
            "Disable security features",
            "Add dependencies without security check"
        ],
        "veto_authority": False
    }
```

**Human Operator Responsibilities**:

```yaml
# FILE: docs/HUMAN_OPERATOR_SECURITY_RESPONSIBILITIES.md

human_operator:
  daily:
    - Review dharmic gate veto log
    - Check security fitness trend (should be stable or improving)
    - Verify no CRITICAL vulnerabilities introduced

  weekly:
    - Audit changes to security-critical files
    - Review dependency updates for CVEs
    - Update security requirements based on violations

  on_incident:
    - Immediately pause swarm if CRITICAL vulnerability found
    - Root cause analysis (which agent, why did gates fail?)
    - Update gates/requirements to prevent recurrence

  prohibited:
    - Bypassing dharmic gates manually
    - Disabling security tests
    - Deploying code that failed security evaluation
```

**Implementation Priority**: **P0 (Critical)**
**Effort**: 2 days (documentation + enforcement in orchestrator)

---

### PO.3: Implement Supporting Toolchains

**NIST Practice**: Use automated tools for secure development (SAST, DAST, SCA, etc.)

#### Direct Applicability: ✅ YES (with integration work)

**Current State**:
- ✅ Testing framework exists (`TesterAgent`)
- ❌ No SAST/DAST integration
- ❌ No dependency vulnerability scanning
- ❌ No secret detection tools

**Gap**: Current testing focuses on functional correctness. Security testing is minimal.

**Agentic Adaptation**:

Integrate security tools into Tester Agent workflow:

```python
# ENHANCEMENT: TesterAgent with Security Toolchain
class TesterAgent(BaseAgent):
    """Enhanced with security scanning capabilities."""

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(TESTER_CONFIG, swarm_config)

        # Security toolchain
        self.sast_tools = [
            BanditScanner(),      # Python SAST
            SemgrepScanner(),     # Pattern matching
            PyLintSecurityPlugin()
        ]
        self.secret_scanner = TruffleHogScanner()
        self.dependency_scanner = SafetyScanner()  # Or pip-audit

    async def run_security_tests(self, files: List[str]) -> SecurityTestResult:
        """Run comprehensive security testing suite."""

        results = {
            "sast": await self._run_sast(files),
            "secrets": await self._scan_secrets(files),
            "dependencies": await self._scan_dependencies(),
            "injection": await self._test_injection_vectors(files)
        }

        # Calculate security fitness score
        security_score = self._calculate_security_fitness(results)

        # CRITICAL: Fail build if any critical issues
        critical_issues = [
            issue for result in results.values()
            for issue in result.issues
            if issue.severity == "CRITICAL"
        ]

        return SecurityTestResult(
            passed=len(critical_issues) == 0,
            security_score=security_score,
            issues_by_severity=self._group_by_severity(results),
            recommendations=self._generate_recommendations(results)
        )
```

**Recommended Toolchain**:

| Tool | Purpose | Integration Point | Auto-Fix Capable? |
|------|---------|-------------------|-------------------|
| **Bandit** | Python SAST | Tester Agent | ❌ No (report only) |
| **Semgrep** | Custom security rules | Tester Agent + Dharmic Gate | ⚠️ Partial (can suggest) |
| **TruffleHog** | Secret detection | Pre-commit + Tester | ✅ Yes (can strip secrets) |
| **Safety / pip-audit** | Dependency CVE scan | Tester Agent | ⚠️ Partial (can upgrade deps) |
| **Checkov** | IaC security (if applicable) | Tester Agent | ⚠️ Partial |
| **Trivy** | Container scanning (if Docker used) | Tester Agent | ❌ No |

**Key Innovation for Agentic Systems**:

Unlike traditional CI/CD where tools generate reports for humans, in agentic systems:
1. **Refiner Agent can auto-fix many issues** (e.g., replace `shell=True`, upgrade vulnerable deps)
2. **Dharmic Gate can learn patterns** from repeated violations
3. **Proposer Agent can proactively avoid patterns** flagged by tools

```python
# RECOMMENDED: Security Tool Integration with Agent Feedback Loop
class SecurityToolFeedbackLoop:
    """Learn from security tool findings to improve future code generation."""

    def __init__(self, tester_agent: TesterAgent):
        self.tester = tester_agent
        self.violation_patterns = []

    async def analyze_findings(self, scan_results: Dict) -> AgentLearning:
        """Extract patterns that agents should avoid in future."""

        # Example: Bandit repeatedly flags B603 (subprocess without shell=True check)
        common_issues = self._find_common_issues(scan_results)

        learning = AgentLearning()
        for issue in common_issues:
            if issue.tool == "bandit" and issue.code == "B603":
                learning.add_pattern(
                    pattern_type="forbidden_code",
                    description="Avoid subprocess calls without explicit shell=False",
                    regex=r"subprocess\.\w+\([^)]*\)",
                    auto_fix="Add shell=False parameter",
                    target_agent="writer"
                )

        return learning

    def update_agent_prompts(self, learning: AgentLearning):
        """Feed learning back into agent system prompts."""
        # Writer agent's system prompt gets updated with learned patterns
        # Dharmic gate gets new patterns to check
        pass
```

**Implementation Priority**: **P0 (Critical)**
**Effort**: 5 days (tool integration + feedback loop)

---

### PO.4: Define and Use Criteria for Vulnerability Management

**NIST Practice**: Define criteria for identifying and responding to vulnerabilities.

#### Direct Applicability: ✅ YES (already partially implemented)

**Current State**:
- ✅ Fitness threshold exists (`fitness_threshold: 0.8`)
- ✅ Ahimsa veto threshold exists (`veto_threshold: 0.7`)
- ❌ No severity-based SLA for fixes
- ❌ No tracking of vulnerability remediation time

**Agentic Adaptation**:

```python
# RECOMMENDED: Vulnerability Response Criteria
class VulnerabilityResponseCriteria:
    """Define how quickly vulnerabilities must be addressed."""

    SEVERITY_SLA = {
        "CRITICAL": {
            "max_age_hours": 4,  # Must fix within 4 hours
            "requires_human_approval": True,  # Human must review fix
            "auto_fix_allowed": False,  # Too risky for auto-fix
            "blocks_deployment": True
        },
        "HIGH": {
            "max_age_hours": 24,
            "requires_human_approval": False,
            "auto_fix_allowed": True,  # Refiner can attempt
            "blocks_deployment": True
        },
        "MEDIUM": {
            "max_age_hours": 168,  # 1 week
            "requires_human_approval": False,
            "auto_fix_allowed": True,
            "blocks_deployment": False  # Can deploy with warning
        },
        "LOW": {
            "max_age_hours": 720,  # 30 days
            "requires_human_approval": False,
            "auto_fix_allowed": True,
            "blocks_deployment": False
        }
    }

    @classmethod
    def should_auto_remediate(cls, vuln: Vulnerability) -> bool:
        """Determine if agent should attempt auto-fix."""
        criteria = cls.SEVERITY_SLA.get(vuln.severity)

        if not criteria["auto_fix_allowed"]:
            return False

        # Additional heuristics
        if vuln.has_known_fix and vuln.fix_complexity == "low":
            return True

        return False

    @classmethod
    def is_overdue(cls, vuln: Vulnerability) -> bool:
        """Check if vulnerability exceeded SLA."""
        criteria = cls.SEVERITY_SLA.get(vuln.severity)
        age_hours = (datetime.utcnow() - vuln.discovered_at).total_seconds() / 3600
        return age_hours > criteria["max_age_hours"]
```

**Integration with Swarm**:

```python
# ENHANCEMENT: Vulnerability-Driven Improvement Cycles
class SwarmOrchestrator:

    async def vulnerability_response_cycle(self, vuln: Vulnerability):
        """Special cycle triggered by vulnerability detection."""

        logger.warning(f"Vulnerability {vuln.id} detected: {vuln.title} ({vuln.severity})")

        criteria = VulnerabilityResponseCriteria.SEVERITY_SLA[vuln.severity]

        # Step 1: Can we auto-remediate?
        if VulnerabilityResponseCriteria.should_auto_remediate(vuln):
            logger.info(f"Attempting auto-remediation for {vuln.id}")

            # Proposer generates fix
            fix_proposal = await self.proposer.propose_vulnerability_fix(vuln)

            # Dharmic Gate evaluates (more strict for vuln fixes)
            evaluation = await self.dharmic_gate.evaluate(fix_proposal, strict=True)

            if evaluation.veto:
                logger.warning(f"Auto-fix vetoed: {evaluation.veto_reason}")
                await self._notify_human_urgent(vuln, evaluation)
                return

            # Writer implements
            implementation = await self.writer.implement(fix_proposal)

            # Tester validates fix actually resolves vuln
            test_result = await self.tester.validate_vulnerability_fix(vuln, implementation)

            if test_result.passed and test_result.vuln_resolved:
                logger.info(f"Successfully auto-remediated {vuln.id}")
                await self.evolver.archive_vulnerability_fix(vuln, implementation)
            else:
                logger.error(f"Auto-fix failed for {vuln.id}")
                await self._notify_human_urgent(vuln, test_result)

        # Step 2: Requires human intervention
        else:
            logger.warning(f"{vuln.id} requires human approval - notifying operator")
            await self._notify_human_urgent(vuln)

            # Pause swarm until human addresses
            if criteria["blocks_deployment"]:
                self.paused = True
                logger.critical("Swarm paused due to blocking vulnerability")
```

**Implementation Priority**: **P1 (High)**
**Effort**: 4 days

---

### PO.5: Implement and Maintain Secure Environments

**NIST Practice**: Secure development, build, test, and production environments.

#### Direct Applicability: ✅ YES (standard security hardening)

**Current State**:
- ✅ Virtual environment for Python dependencies (`.venv`)
- ❌ No container isolation for agent execution
- ❌ Credentials in `.env` with weak permissions (see SECURITY_AUDIT_REPORT.md)
- ❌ No separation between dev/test/prod

**Standard Recommendations** (no agentic adaptation needed):

1. **Fix immediate credential exposure**:
```bash
chmod 600 /Users/dhyana/DHARMIC_GODEL_CLAW/.env
```

2. **Migrate to keyring**:
```python
import keyring
keyring.set_password("dharmic_claw", "email", password)
# Remove from .env
```

3. **Container isolation**:
```yaml
# docker-compose.yml
version: '3.8'
services:
  swarm_orchestrator:
    build: .
    environment:
      - ANTHROPIC_API_KEY=${ANTHROPIC_API_KEY}
    volumes:
      - ./src:/app/src:ro  # Read-only source
      - ./memory:/app/memory  # Persistent memory
    networks:
      - dharmic_net
    security_opt:
      - no-new-privileges:true
    read_only: true  # Filesystem read-only except volumes
```

4. **Separate environments**:
```
Development:  M3 MacBook, local models, no production secrets
Testing:      Isolated container, mock external services
Production:   Locked down, audit logging, no REPL access
```

**Agentic-Specific Consideration**:

Agents generate code that gets executed. This is inherently risky. Sandbox execution:

```python
# RECOMMENDED: Sandboxed Test Execution
class SandboxedTesterAgent(TesterAgent):
    """Run tests in isolated container to prevent system compromise."""

    async def run_tests(self, files: List[str]) -> TestResult:
        """Execute tests in Docker container with restricted capabilities."""

        # Build ephemeral test container
        container_id = await self._build_test_container(files)

        try:
            # Run with strict resource limits
            result = await docker_client.containers.run(
                image=container_id,
                command=["pytest", "--tb=short"],
                mem_limit="512m",
                cpu_quota=50000,  # 50% of one core
                network_mode="none",  # No network access
                read_only=True,
                timeout=300  # 5 min max
            )

            return self._parse_test_output(result)

        finally:
            # Always cleanup
            await self._remove_container(container_id)
```

**Implementation Priority**: **P0 (Critical)** for credential fix, **P2** for containerization
**Effort**: 1 day (creds) + 3 days (containers)

---

## PS: Protect the Software

### PS.1: Protect All Forms of Code from Unauthorized Access

**NIST Practice**: Protect code repositories, build systems, and artifacts from unauthorized modification.

#### Direct Applicability: ✅ YES (standard access control)

**Current State**:
- ✅ Git repository for version control
- ❌ No branch protection rules
- ❌ No code signing for commits
- ❌ Agents have full write access to codebase

**Gap**: In agentic systems, **agents themselves are potential attack vectors**. Compromised API key = compromised agent = malicious code generation.

**Agentic Adaptation**:

```python
# RECOMMENDED: Agent Code Modification Restrictions
class SecureCodeRepository:
    """Git wrapper with agent-specific access controls."""

    AGENT_PERMISSIONS = {
        "writer": {
            "can_modify": ["src/", "tests/"],
            "cannot_modify": [
                "src/core/dharmic_gate.py",  # Agents can't modify their own gates
                "src/core/security_requirements.py",
                ".env",
                "scripts/",
                "config/"
            ],
            "requires_review": ["src/core/", "swarm/"]  # Core changes need extra scrutiny
        },
        "refiner": {
            "can_modify": ["src/", "tests/"],
            "cannot_modify": ["src/core/dharmic_gate.py", ".env"],
            "requires_review": []
        },
        "evolver": {
            "can_modify": ["memory/", "archive/"],  # Only metadata
            "cannot_modify": ["src/", "tests/", "config/"],
            "requires_review": []
        }
    }

    def validate_agent_write(self, agent_name: str, file_path: str) -> bool:
        """Check if agent is allowed to modify this file."""
        perms = self.AGENT_PERMISSIONS.get(agent_name, {})

        # Check forbidden paths
        for forbidden in perms.get("cannot_modify", []):
            if file_path.startswith(forbidden):
                logger.error(f"Agent {agent_name} attempted to modify forbidden path: {file_path}")
                return False

        # Check allowed paths
        allowed = any(file_path.startswith(p) for p in perms.get("can_modify", []))
        if not allowed:
            logger.warning(f"Agent {agent_name} attempted to modify unallowed path: {file_path}")
            return False

        return True
```

**Additional Protections**:

1. **Read-only file system for agents** (except designated areas)
2. **All writes go through Evolver Agent** (single point of control)
3. **Commit signing** for traceability

```bash
# Configure GPG signing for git commits
git config commit.gpgsign true
git config user.signingkey <GPG_KEY_ID>
```

4. **Branch protection**:
```yaml
# .github/branch_protection.yml (if using GitHub)
main:
  required_reviews: 1  # Human must approve
  require_signed_commits: true
  block_force_push: true
  restrict_pushes:
    - dharmic_agent_bot  # Agent can't push directly to main
```

**Implementation Priority**: **P1 (High)**
**Effort**: 2 days

---

### PS.2: Provide a Mechanism for Verifying Software Release Integrity

**NIST Practice**: Use checksums, signatures, SBOMs to verify integrity.

#### Direct Applicability: ✅ YES (with agentic provenance addition)

**Current State**:
- ❌ No SBOM generation
- ❌ No release signing
- ❌ No provenance tracking for AI-generated code

**Gap**: Traditional SBOMs don't capture **AI provenance** (which model, which prompt, what context).

**Agentic Adaptation**:

```python
# RECOMMENDED: Extended SBOM with AI Provenance
class AgenticSBOM:
    """Software Bill of Materials extended for AI-generated code."""

    def generate_sbom(self, release_version: str) -> Dict:
        """Generate SBOM in CycloneDX format + AI extensions."""

        sbom = {
            "bomFormat": "CycloneDX",
            "specVersion": "1.4",
            "version": release_version,
            "metadata": {
                "timestamp": datetime.utcnow().isoformat(),
                "tools": [
                    {
                        "vendor": "Anthropic",
                        "name": "Claude",
                        "version": "sonnet-4-20250514"
                    }
                ],
                # AGENTIC EXTENSION
                "ai_provenance": {
                    "generation_method": "autonomous_agent_swarm",
                    "agent_version": "dharmic_claw_1.0",
                    "models_used": [
                        {
                            "name": "claude-sonnet-4-20250514",
                            "role": "code_generation",
                            "total_calls": 147
                        }
                    ],
                    "dharmic_gate_version": "1.0",
                    "fitness_score": 0.87,
                    "gates_passed": ["ahimsa", "vyavasthit", "satya"]
                }
            },
            "components": self._generate_component_list(),
            "dependencies": self._generate_dependency_graph(),
            # AGENTIC EXTENSION
            "ai_components": self._generate_ai_component_list()
        }

        return sbom

    def _generate_ai_component_list(self) -> List[Dict]:
        """List which code files were AI-generated and their provenance."""

        ai_components = []

        for file in Path("src").rglob("*.py"):
            lineage = self._get_file_lineage(file)

            if lineage.generated_by_agent:
                ai_components.append({
                    "file": str(file),
                    "generated_by": lineage.agent_name,
                    "generation_timestamp": lineage.timestamp,
                    "evolution_id": lineage.evolution_id,
                    "fitness_at_generation": lineage.fitness,
                    "prompt_hash": lineage.prompt_hash,  # For auditing
                    "parent_evolution": lineage.parent_id  # Lineage chain
                })

        return ai_components
```

**Why This Matters**:

If a vulnerability is found in AI-generated code, we need to know:
- Which agent generated it
- What prompt/context led to vulnerable code
- What was the fitness score (did security tests miss it?)
- Can we trace lineage to find similar code?

**Integration Point**: Evolver Agent generates SBOM entry when archiving successful changes.

**Implementation Priority**: **P2 (Important for release)**
**Effort**: 3 days

---

### PS.3: Archive and Protect Software

**NIST Practice**: Archive code, dependencies, configurations for future reference.

#### Direct Applicability: ✅ YES (already partially implemented)

**Current State**:
- ✅ Residual stream tracks evolution history
- ✅ DGM Archive stores successful changes
- ❌ No long-term archival strategy
- ❌ No protection against tampering

**Agentic Enhancement**:

```python
# ENHANCEMENT: Tamper-Evident Archive
class SecureEvolutionArchive:
    """Evolution archive with cryptographic integrity."""

    def archive_evolution(self, entry: EvolutionEntry) -> str:
        """Archive with tamper-evident sealing."""

        # Serialize entry
        entry_json = entry.to_json()

        # Compute hash
        entry_hash = hashlib.sha256(entry_json.encode()).hexdigest()

        # Sign with private key (or use blockchain for public verifiability)
        signature = self._sign(entry_hash)

        # Store with signature
        sealed_entry = {
            "entry": entry,
            "hash": entry_hash,
            "signature": signature,
            "archived_at": datetime.utcnow().isoformat(),
            "archived_by": "evolver_agent"
        }

        entry_id = self._write_to_archive(sealed_entry)

        # Optional: Write to append-only ledger for auditability
        self._write_to_audit_ledger(entry_id, entry_hash, signature)

        return entry_id

    def verify_archive_integrity(self, entry_id: str) -> bool:
        """Verify archive hasn't been tampered with."""
        sealed_entry = self._read_from_archive(entry_id)

        # Recompute hash
        entry_json = sealed_entry["entry"].to_json()
        computed_hash = hashlib.sha256(entry_json.encode()).hexdigest()

        # Compare with stored hash
        if computed_hash != sealed_entry["hash"]:
            logger.critical(f"Archive integrity violation: {entry_id}")
            return False

        # Verify signature
        if not self._verify_signature(sealed_entry["hash"], sealed_entry["signature"]):
            logger.critical(f"Archive signature invalid: {entry_id}")
            return False

        return True
```

**Implementation Priority**: **P2 (Important for compliance)**
**Effort**: 2 days

---

## PW: Produce Well-Secured Software

### PW.1: Design Software to Meet Security Requirements

**NIST Practice**: Design architecture to meet security requirements from PO.1.

#### Direct Applicability: ⚠️ PARTIAL (agents don't "design" architectures yet)

**Current State**:
- ✅ Proposer Agent suggests improvements
- ❌ No architectural security review
- ❌ Agents operate at file/function level, not system level

**Gap**: Agents currently make localized changes. They don't perform system-wide threat modeling or architectural refactoring.

**Agentic Adaptation** (future capability):

```python
# ASPIRATIONAL: Security-Aware Architecture Agent
class ArchitectureAgent(BaseAgent):
    """Specialized agent for system-level security design."""

    async def threat_model_system(self) -> ThreatModel:
        """Perform STRIDE threat modeling on current system."""

        # Parse codebase to extract architecture
        architecture = await self._analyze_architecture()

        # Identify trust boundaries
        trust_boundaries = self._identify_trust_boundaries(architecture)

        # Apply STRIDE
        threats = []
        for boundary in trust_boundaries:
            threats.extend(self._apply_stride(boundary))

        return ThreatModel(
            architecture=architecture,
            trust_boundaries=trust_boundaries,
            threats=threats,
            mitigations=self._suggest_mitigations(threats)
        )

    def _apply_stride(self, boundary: TrustBoundary) -> List[Threat]:
        """Apply STRIDE methodology."""
        threats = []

        # Spoofing: Can attacker impersonate?
        if not boundary.has_authentication:
            threats.append(Threat(
                type="Spoofing",
                description=f"Boundary {boundary.name} lacks authentication",
                severity="HIGH"
            ))

        # Tampering: Can attacker modify data?
        if not boundary.has_integrity_check:
            threats.append(Threat(
                type="Tampering",
                description=f"Boundary {boundary.name} lacks integrity checks",
                severity="MEDIUM"
            ))

        # ... (Repudiation, Information Disclosure, DoS, Elevation)

        return threats
```

**For Current Implementation** (without full Architecture Agent):

Add **security design review checkpoint** before major refactorings:

```python
# PRACTICAL: Design Review Gate
class DharmicGateAgent:

    async def evaluate_architectural_change(self, proposal: Proposal) -> Evaluation:
        """Extra scrutiny for architectural changes."""

        # Detect architectural changes
        if self._is_architectural_change(proposal):
            logger.warning(f"Architectural change detected: {proposal.id}")

            # Require human review
            return Evaluation(
                veto=True,
                veto_reason="Architectural changes require human security review",
                requires_human=True,
                security_review_questions=[
                    "Does this change affect trust boundaries?",
                    "Are new attack surfaces introduced?",
                    "Does this change authentication/authorization?",
                    "Are security requirements still met?"
                ]
            )

        # Normal evaluation
        return await super().evaluate(proposal)

    def _is_architectural_change(self, proposal: Proposal) -> bool:
        """Heuristics to detect architectural changes."""
        indicators = [
            "new external API introduced",
            "authentication logic modified",
            "database schema changed",
            "new dependency on external service",
            "trust boundary affected"
        ]
        return any(indicator in proposal.description.lower() for indicator in indicators)
```

**Implementation Priority**: **P1 (High)** for design review gate, **P3 (Future)** for full Architecture Agent
**Effort**: 2 days (gate) + 2 weeks (full agent)

---

### PW.2: Review the Software Design

**NIST Practice**: Have personnel review software design to verify security requirements are met.

#### Direct Applicability: ⚠️ PARTIAL (agents can review, but human oversight needed for critical changes)

**Current Implementation**:
- ✅ Dharmic Gate reviews all changes
- ✅ Tester Agent validates
- ❌ No peer review equivalent
- ❌ No human review process for high-risk changes

**Agentic Adaptation**:

Implement **multi-agent review** for high-risk changes:

```python
# RECOMMENDED: Multi-Agent Security Review Board
class SecurityReviewBoard:
    """Multiple agents + human review high-risk changes."""

    def __init__(self, swarm_config: SwarmConfig):
        self.dharmic_gate = DharmicGateAgent(swarm_config)
        self.tester = TesterAgent(swarm_config)
        self.evolver = EvolverAgent(swarm_config)  # Checks lineage
        self.human_reviewer = HumanReviewInterface()

    async def review_high_risk_change(self, proposal: Proposal) -> ReviewResult:
        """Comprehensive review for critical changes."""

        reviews = {}

        # Agent reviews (parallel)
        reviews["dharmic_gate"] = await self.dharmic_gate.evaluate(proposal)
        reviews["tester"] = await self.tester.dry_run_tests(proposal)
        reviews["evolver"] = await self.evolver.assess_risk(proposal)

        # Aggregate agent consensus
        agent_consensus = self._calculate_consensus(reviews)

        # Require human review if:
        # 1. Any agent vetoed
        # 2. Low consensus (agents disagree)
        # 3. Critical files affected
        # 4. Security-sensitive code

        requires_human = (
            any(r.veto for r in reviews.values()) or
            agent_consensus < 0.7 or
            self._affects_critical_files(proposal) or
            self._is_security_sensitive(proposal)
        )

        if requires_human:
            human_review = await self.human_reviewer.request_review(
                proposal=proposal,
                agent_reviews=reviews,
                urgency="high" if any(r.veto for r in reviews.values()) else "normal"
            )
            reviews["human"] = human_review

        return ReviewResult(
            approved=self._aggregate_approval(reviews),
            reviews=reviews,
            consensus_score=agent_consensus
        )
```

**Human Review Interface**:

```python
# RECOMMENDED: Human-in-the-Loop Review Interface
class HumanReviewInterface:
    """Interface for requesting human security review."""

    async def request_review(
        self,
        proposal: Proposal,
        agent_reviews: Dict[str, Review],
        urgency: str
    ) -> HumanReview:
        """Send review request to human operator."""

        # Format review request
        request = self._format_review_request(proposal, agent_reviews)

        # Send notification (email, Telegram, etc.)
        await self._notify_human(
            title=f"Security Review Required: {proposal.id}",
            body=request,
            urgency=urgency
        )

        # Wait for response (with timeout)
        timeout = 3600 if urgency == "high" else 86400  # 1h or 24h

        response = await self._wait_for_human_response(
            proposal_id=proposal.id,
            timeout=timeout
        )

        if response is None:
            # Timeout - default to REJECT for safety
            return HumanReview(
                approved=False,
                reason="Review timeout - defaulting to reject for safety",
                reviewer="system"
            )

        return response
```

**Implementation Priority**: **P1 (High)**
**Effort**: 3 days

---

### PW.4: Reuse Existing, Well-Secured Software

**NIST Practice**: Prefer well-maintained, security-audited libraries.

#### Direct Applicability: ✅ YES (with agent guidance)

**Current State**:
- ❌ No dependency approval process
- ❌ Agents can add dependencies freely
- ❌ No tracking of dependency security posture

**Agentic Adaptation**:

```python
# RECOMMENDED: Dependency Security Approval
class DependencySecurityManager:
    """Evaluate and approve dependencies before agents can use them."""

    def __init__(self):
        self.approved_dependencies = self._load_approved_list()
        self.blocklist = self._load_blocklist()

    async def evaluate_dependency(self, package: str, version: str) -> DependencyEvaluation:
        """Comprehensive dependency security evaluation."""

        # Check blocklist
        if package in self.blocklist:
            return DependencyEvaluation(
                approved=False,
                reason=f"{package} is on blocklist: {self.blocklist[package]['reason']}"
            )

        # Check if already approved
        if package in self.approved_dependencies:
            approved_version = self.approved_dependencies[package]
            if version == approved_version:
                return DependencyEvaluation(approved=True)

        # Evaluate new dependency
        security_score = await self._check_security_score(package, version)
        cve_count = await self._check_cves(package, version)
        maintenance_status = await self._check_maintenance(package)
        license_ok = await self._check_license(package)

        # Decision criteria
        approved = (
            security_score > 0.7 and
            cve_count == 0 and
            maintenance_status in ["active", "mature"] and
            license_ok
        )

        if approved:
            # Add to approved list
            self.approved_dependencies[package] = version
            self._save_approved_list()

        return DependencyEvaluation(
            approved=approved,
            security_score=security_score,
            cve_count=cve_count,
            maintenance_status=maintenance_status,
            license=license_ok,
            recommendation=self._generate_recommendation(
                security_score, cve_count, maintenance_status
            )
        )

    async def _check_security_score(self, package: str, version: str) -> float:
        """Query OSS security scorecards."""
        # https://github.com/ossf/scorecard
        # Returns 0.0-1.0 based on security practices
        pass

    async def _check_cves(self, package: str, version: str) -> int:
        """Check CVE database for known vulnerabilities."""
        # Query NVD or OSV
        pass
```

**Integration with Writer Agent**:

```python
# ENHANCEMENT: Writer Agent checks dependencies
class WriterAgent(BaseAgent):

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(WRITER_CONFIG, swarm_config)
        self.dependency_manager = DependencySecurityManager()

    async def implement_proposals(self, proposals: List[Proposal]) -> Implementation:
        """Implement proposals with dependency security checks."""

        implementation = await super().implement_proposals(proposals)

        # Extract any new dependencies
        new_deps = self._extract_dependencies(implementation)

        # Evaluate each dependency
        for dep in new_deps:
            evaluation = await self.dependency_manager.evaluate_dependency(
                package=dep.name,
                version=dep.version
            )

            if not evaluation.approved:
                # Remove dependency, request alternative
                logger.warning(f"Dependency {dep.name} not approved: {evaluation.reason}")

                # Ask Proposer for alternative
                alternative_proposal = await self._request_alternative(
                    original_dep=dep,
                    reason=evaluation.reason,
                    recommendation=evaluation.recommendation
                )

                # Re-implement with alternative
                implementation = await self.implement(alternative_proposal)

        return implementation
```

**Implementation Priority**: **P1 (High)**
**Effort**: 4 days

---

### PW.5: Create Source Code Adhering to Secure Coding Practices

**NIST Practice**: Follow secure coding standards (OWASP, CWE Top 25, etc.)

#### Direct Applicability: ✅ YES (this is where agents shine!)

**Current State**:
- ✅ Writer Agent generates code
- ❌ No explicit secure coding guidance in prompts
- ❌ No automated secure coding verification

**Agentic Advantage**: Agents can be **trained** on secure coding patterns far more consistently than humans.

**Recommended Implementation**:

```python
# ENHANCEMENT: Secure Coding Pattern Library
class SecureCodingPatterns:
    """Library of secure coding patterns that agents should follow."""

    PATTERNS = {
        "input_validation": {
            "description": "Always validate and sanitize user input",
            "good_example": """
# Good: Validate before use
def process_email(email: str):
    if not re.match(r'^[^@]+@[^@]+\\.[^@]+$', email):
        raise ValueError("Invalid email format")
    # Safe to use email
            """,
            "bad_example": """
# Bad: No validation
def process_email(email: str):
    send_email(email)  # Could be injection vector
            """,
            "cwe": ["CWE-20"],
            "tools_detect": ["bandit", "semgrep"]
        },

        "subprocess_safety": {
            "description": "Never use shell=True with user input",
            "good_example": """
# Good: Use list, avoid shell
subprocess.run(["ls", "-l", user_path], shell=False, check=True)
            """,
            "bad_example": """
# Bad: Shell injection risk
subprocess.run(f"ls -l {user_path}", shell=True)
            """,
            "cwe": ["CWE-78"],
            "tools_detect": ["bandit B602", "semgrep"]
        },

        "secrets_management": {
            "description": "Never hardcode secrets, use environment or keyring",
            "good_example": """
# Good: Use keyring
import keyring
api_key = keyring.get_password("myapp", "api_key")
            """,
            "bad_example": """
# Bad: Hardcoded secret
api_key = "sk-1234567890abcdef"
            """,
            "cwe": ["CWE-798"],
            "tools_detect": ["trufflehog", "detect-secrets"]
        },

        "sql_injection_prevention": {
            "description": "Use parameterized queries",
            "good_example": """
# Good: Parameterized query
cursor.execute("SELECT * FROM users WHERE id = ?", (user_id,))
            """,
            "bad_example": """
# Bad: String interpolation
cursor.execute(f"SELECT * FROM users WHERE id = {user_id}")
            """,
            "cwe": ["CWE-89"],
            "tools_detect": ["bandit", "semgrep"]
        },

        "path_traversal_prevention": {
            "description": "Validate file paths to prevent directory traversal",
            "good_example": """
# Good: Validate path is within allowed directory
import os
base_dir = "/safe/directory"
user_path = os.path.normpath(os.path.join(base_dir, user_file))
if not user_path.startswith(base_dir):
    raise ValueError("Path traversal detected")
            """,
            "bad_example": """
# Bad: Direct file access
with open(user_provided_path, 'r') as f:
    data = f.read()
            """,
            "cwe": ["CWE-22"],
            "tools_detect": ["bandit", "semgrep"]
        }
    }

    @classmethod
    def get_system_prompt_injection(cls) -> str:
        """Generate system prompt content teaching secure coding."""
        prompt = "\\n## Secure Coding Requirements\\n\\n"
        prompt += "You MUST follow these secure coding patterns:\\n\\n"

        for pattern_name, pattern in cls.PATTERNS.items():
            prompt += f"### {pattern_name}\\n"
            prompt += f"{pattern['description']}\\n\\n"
            prompt += f"**Good Example:**\\n```python\\n{pattern['good_example']}\\n```\\n\\n"
            prompt += f"**Bad Example (NEVER DO THIS):**\\n```python\\n{pattern['bad_example']}\\n```\\n\\n"

        return prompt
```

**Integration into Writer Agent**:

```python
# Update Writer Agent config
WRITER_CONFIG = AgentConfig(
    name="writer",
    role="Write code implementing approved proposals",
    system_prompt=f"""You are the WRITER agent in a self-improving swarm.

{SecureCodingPatterns.get_system_prompt_injection()}

Your role:
1. Take approved proposals and implement them
2. Write clean, SECURE, tested, documented code
3. Follow project conventions AND secure coding patterns above
4. Include type hints and docstrings
5. Make minimal changes - avoid scope creep

CRITICAL: Any violation of secure coding patterns will be VETOED by Dharmic Gate.

Output format:
{{
    "files": [...],
    "security_patterns_used": ["input_validation", "subprocess_safety"],
    "security_considerations": "Description of security measures taken"
}}

Code must be production-ready and secure. No placeholders or TODOs.""",
    tools=["read_file", "write_file", "search_codebase"]
)
```

**Dharmic Gate Validation**:

```python
# ENHANCEMENT: Dharmic Gate checks secure coding patterns
class DharmicGateAgent:

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(DHARMIC_GATE_CONFIG, swarm_config)
        self.secure_patterns = SecureCodingPatterns()

    async def execute(self, context: Dict[str, Any]) -> AgentResponse:
        """Evaluate dharmic alignment + secure coding compliance."""

        # Existing dharmic evaluation
        base_evaluation = await super().execute(context)

        # ADDITIONAL: Check secure coding patterns
        files = context.get("files", [])
        pattern_violations = []

        for file in files:
            violations = self._check_secure_coding_patterns(file["content"])
            pattern_violations.extend(violations)

        # If secure coding violations found, strengthen veto
        if pattern_violations:
            critical_violations = [v for v in pattern_violations if v.severity == "CRITICAL"]

            if critical_violations:
                return AgentResponse(
                    success=True,
                    data={
                        **base_evaluation.data,
                        "secure_coding_violations": [v.to_dict() for v in pattern_violations]
                    },
                    veto=True,
                    veto_reason=f"Secure coding violations: {', '.join(v.pattern for v in critical_violations)}"
                )

        return base_evaluation

    def _check_secure_coding_patterns(self, code: str) -> List[PatternViolation]:
        """Check code against secure coding patterns."""
        violations = []

        # Check for bad patterns
        for pattern_name, pattern in self.secure_patterns.PATTERNS.items():
            # Example: Check for shell=True
            if pattern_name == "subprocess_safety":
                if "shell=True" in code:
                    violations.append(PatternViolation(
                        pattern=pattern_name,
                        severity="CRITICAL",
                        description=pattern["description"],
                        cwe=pattern["cwe"]
                    ))

        return violations
```

**Implementation Priority**: **P0 (Critical)**
**Effort**: 4 days

---

### PW.6: Configure Software to Have Secure Settings by Default

**NIST Practice**: Secure defaults, no unnecessary features enabled.

#### Direct Applicability: ✅ YES

**Current State**:
- ✅ Some secure defaults (e.g., `shell=False` not explicit)
- ❌ No checklist for secure configuration
- ❌ Agents don't consider secure defaults when generating config

**Recommended Approach**:

```python
# RECOMMENDED: Secure Configuration Templates
class SecureConfigurationTemplates:
    """Templates for secure default configurations."""

    TEMPLATES = {
        "subprocess": {
            "secure_defaults": {
                "shell": False,
                "check": True,
                "timeout": 30,
                "capture_output": True
            },
            "explanation": "Always use shell=False to prevent injection, check=True to catch errors, timeout to prevent DoS"
        },

        "http_client": {
            "secure_defaults": {
                "timeout": 30,
                "verify": True,  # SSL verification
                "allow_redirects": False  # Prevent open redirect
            },
            "explanation": "Timeout prevents DoS, verify ensures SSL cert validation, limit redirects"
        },

        "file_operations": {
            "secure_defaults": {
                "mode": "0o600",  # Owner read/write only
                "create_parents": False,  # Explicit directory creation
                "follow_symlinks": False  # Prevent symlink attacks
            },
            "explanation": "Restrictive file permissions, explicit directory handling, no symlink following"
        }
    }
```

**Writer Agent Integration**:

When Writer Agent generates code using these operations, it consults templates:

```python
# ENHANCEMENT: Writer Agent uses secure templates
class WriterAgent:

    def _generate_subprocess_call(self, command: List[str]) -> str:
        """Generate subprocess call with secure defaults."""

        template = SecureConfigurationTemplates.TEMPLATES["subprocess"]
        defaults = template["secure_defaults"]

        return f"""
subprocess.run(
    {command},
    shell={defaults['shell']},
    check={defaults['check']},
    timeout={defaults['timeout']},
    capture_output={defaults['capture_output']}
)
# Secure defaults: {template['explanation']}
"""
```

**Implementation Priority**: **P1 (High)**
**Effort**: 2 days

---

### PW.7: Review and/or Analyze Human-Readable Code

**NIST Practice**: Code review by peers.

#### Direct Applicability: ✅ YES (multi-agent review already proposed in PW.2)

**Current Implementation**: See PW.2 SecurityReviewBoard

**Additional Consideration for Agentic Systems**:

Agents should review **their own generated code** (self-reflection):

```python
# ENHANCEMENT: Self-Reflection for Writer Agent
class WriterAgent:

    async def implement_with_self_review(self, proposal: Proposal) -> Implementation:
        """Implement code, then self-review before submitting."""

        # Generate initial implementation
        initial_impl = await self._generate_code(proposal)

        # Self-review: Ask Claude to critique its own code
        self_review = await self._self_review(initial_impl)

        # If self-review identifies issues, refine
        if self_review.issues_found:
            logger.info(f"Self-review found {len(self_review.issues)} issues, refining...")
            improved_impl = await self._refine_based_on_review(initial_impl, self_review)
            return improved_impl

        return initial_impl

    async def _self_review(self, implementation: Implementation) -> SelfReview:
        """Agent reviews its own code for issues."""

        review_prompt = f"""
You previously generated the following code:

{implementation.code}

Now, critically review this code for:
1. Security vulnerabilities (injection, XSS, insecure defaults)
2. Correctness (logic errors, edge cases)
3. Code quality (readability, maintainability)
4. Adherence to secure coding patterns

Be brutally honest. What issues do you see?
"""

        response = self._call_claude([
            {"role": "user", "content": review_prompt}
        ])

        return self._parse_self_review(response)
```

**Implementation Priority**: **P2 (Improves quality)**
**Effort**: 2 days

---

### PW.8: Test Executable Code

**NIST Practice**: Perform testing including functional and security testing.

#### Direct Applicability: ✅ YES (already implemented, needs security enhancement)

**Current State**:
- ✅ Tester Agent runs tests
- ❌ Tests focus on functional correctness, not security
- ❌ No fuzz testing, penetration testing

**Recommended Enhancements**:

```python
# ENHANCEMENT: Security-Focused Testing
class SecurityTesterAgent(TesterAgent):
    """Extended tester with security-specific tests."""

    async def run_security_test_suite(self, files: List[str]) -> SecurityTestResult:
        """Comprehensive security testing."""

        results = {
            "functional": await self.run_functional_tests(files),
            "sast": await self.run_sast_scan(files),
            "dast": await self.run_dast_scan(files),  # If web app
            "fuzz": await self.run_fuzz_tests(files),
            "secrets": await self.scan_for_secrets(files),
            "dependencies": await self.scan_dependencies()
        }

        # Aggregate security score
        security_score = self._calculate_security_score(results)

        # CRITICAL: Block if security score below threshold
        threshold = 0.8
        passed = security_score >= threshold

        if not passed:
            logger.error(f"Security test failed: score {security_score} < threshold {threshold}")

        return SecurityTestResult(
            passed=passed,
            security_score=security_score,
            results=results,
            blockers=self._extract_blockers(results)
        )

    async def run_fuzz_tests(self, files: List[str]) -> FuzzResult:
        """Fuzz testing for crash/hang detection."""

        # Use Atheris or Hypothesis for Python fuzzing
        # Generate random inputs, check for crashes/exceptions

        fuzz_targets = self._identify_fuzz_targets(files)
        crashes = []

        for target in fuzz_targets:
            try:
                # Run fuzzer for N iterations
                crashes_found = await self._fuzz_target(target, iterations=10000)
                crashes.extend(crashes_found)
            except Exception as e:
                logger.error(f"Fuzzing failed for {target}: {e}")

        return FuzzResult(
            targets_tested=len(fuzz_targets),
            crashes_found=len(crashes),
            crashes=crashes
        )
```

**Security Test Types**:

| Test Type | Tool/Method | Purpose | Integrated? |
|-----------|-------------|---------|-------------|
| **SAST** | Bandit, Semgrep | Find vulnerabilities in source code | ✅ Proposed |
| **DAST** | OWASP ZAP (if web app) | Test running application | ❌ Not applicable (no web app yet) |
| **SCA** | Safety, pip-audit | Find vulnerable dependencies | ✅ Proposed |
| **Fuzz** | Atheris, Hypothesis | Find crashes/edge cases | ⚠️ Proposed above |
| **Secrets** | TruffleHog, detect-secrets | Find leaked credentials | ✅ Proposed |
| **Integration** | Pytest with security assertions | End-to-end security tests | ⚠️ Manual test writing |

**Implementation Priority**: **P0 (Critical)** for SAST/SCA, **P2** for fuzzing
**Effort**: 5 days (SAST/SCA) + 3 days (fuzzing)

---

### PW.9: Configure Software to Have Secure Settings by Default

(Already covered in PW.6)

---

## RV: Respond to Vulnerabilities

### RV.1: Identify and Confirm Vulnerabilities

**NIST Practice**: Gather information from internal and external sources, triage vulnerabilities.

#### Direct Applicability: ✅ YES (with automation advantage)

**Current State**:
- ❌ No vulnerability monitoring
- ❌ No CVE/security advisory integration
- ❌ Reactive, not proactive

**Agentic Advantage**: Agents can **continuously monitor** for vulnerabilities and respond autonomously.

**Recommended Implementation**:

```python
# NEW: Vulnerability Monitoring Agent
class VulnerabilityMonitorAgent(BaseAgent):
    """Continuously monitor for vulnerabilities and trigger response."""

    def __init__(self, swarm_config: SwarmConfig):
        super().__init__(self._create_config(), swarm_config)
        self.sources = [
            NVDSource(),  # National Vulnerability Database
            OSVSource(),  # Open Source Vulnerabilities
            PyPIAdvisorySource(),
            GithubAdvisorySource()
        ]
        self.known_vulnerabilities = set()

    async def continuous_monitoring_loop(self):
        """Run continuously in background (24/7)."""

        while True:
            try:
                # Check all vulnerability sources
                new_vulns = await self._check_all_sources()

                # Filter for vulnerabilities affecting our dependencies
                relevant_vulns = await self._filter_relevant(new_vulns)

                for vuln in relevant_vulns:
                    if vuln.id not in self.known_vulnerabilities:
                        # New vulnerability detected
                        logger.warning(f"New vulnerability: {vuln.id} - {vuln.title}")
                        self.known_vulnerabilities.add(vuln.id)

                        # Trigger response workflow
                        await self._trigger_response(vuln)

                # Sleep before next check (e.g., every 4 hours)
                await asyncio.sleep(14400)

            except Exception as e:
                logger.error(f"Vulnerability monitoring failed: {e}")
                await asyncio.sleep(600)  # Retry after 10 min

    async def _check_all_sources(self) -> List[Vulnerability]:
        """Query all vulnerability data sources."""
        all_vulns = []

        for source in self.sources:
            try:
                vulns = await source.fetch_recent(hours=24)
                all_vulns.extend(vulns)
            except Exception as e:
                logger.error(f"Failed to fetch from {source.name}: {e}")

        return all_vulns

    async def _filter_relevant(self, vulnerabilities: List[Vulnerability]) -> List[Vulnerability]:
        """Filter for vulnerabilities affecting our dependencies."""

        # Get current dependencies
        dependencies = self._get_current_dependencies()

        relevant = []
        for vuln in vulnerabilities:
            for dep in dependencies:
                if vuln.affects(dep.name, dep.version):
                    relevant.append(vuln)
                    break

        return relevant

    async def _trigger_response(self, vuln: Vulnerability):
        """Trigger vulnerability response workflow."""

        # Assess severity and trigger appropriate response
        if vuln.severity in ["CRITICAL", "HIGH"]:
            # Immediate response
            await self._trigger_immediate_response(vuln)
        else:
            # Schedule for next improvement cycle
            await self._schedule_remediation(vuln)
```

**Integration with Swarm**:

```python
# ENHANCEMENT: Swarm Orchestrator handles vulnerability responses
class SwarmOrchestrator:

    def __init__(self, config: SwarmConfig):
        # ... existing init ...

        # Start vulnerability monitoring in background
        self.vuln_monitor = VulnerabilityMonitorAgent(config)
        asyncio.create_task(self.vuln_monitor.continuous_monitoring_loop())

    async def handle_vulnerability_alert(self, vuln: Vulnerability):
        """Handle incoming vulnerability alert."""

        logger.critical(f"Vulnerability alert: {vuln.id} ({vuln.severity})")

        # Check if auto-remediation is allowed
        if VulnerabilityResponseCriteria.should_auto_remediate(vuln):
            # Attempt autonomous fix
            result = await self.vulnerability_response_cycle(vuln)

            if result.success:
                logger.info(f"Successfully auto-remediated {vuln.id}")
                await self._notify_human_success(vuln, result)
            else:
                logger.error(f"Auto-remediation failed for {vuln.id}")
                await self._notify_human_failure(vuln, result)
        else:
            # Requires human intervention
            await self._notify_human_urgent(vuln)

            # Pause swarm if blocking vulnerability
            if vuln.severity == "CRITICAL":
                self.paused = True
                logger.critical("Swarm paused due to CRITICAL vulnerability")
```

**Implementation Priority**: **P1 (High)**
**Effort**: 4 days

---

### RV.1.1: Gather information from internal and external sources

**Current Implementation**: See VulnerabilityMonitorAgent above.

**External Sources to Integrate**:
- NVD (National Vulnerability Database)
- OSV (Open Source Vulnerabilities)
- PyPI Advisory Database
- GitHub Security Advisories
- Snyk Vulnerability DB

**Implementation**: Already covered in RV.1

---

### RV.1.2: Triage and confirm vulnerabilities

**Recommended Approach**:

```python
# ENHANCEMENT: Vulnerability Triage Agent
class VulnerabilityTriageAgent:
    """Triage and prioritize vulnerabilities for remediation."""

    async def triage(self, vuln: Vulnerability) -> TriageResult:
        """Assess vulnerability impact and priority."""

        # Step 1: Confirm vulnerability applies to our system
        applies = await self._confirm_applicability(vuln)
        if not applies:
            return TriageResult(
                priority="none",
                reason="Vulnerability does not apply to our system"
            )

        # Step 2: Assess exploitability
        exploitability = await self._assess_exploitability(vuln)

        # Step 3: Assess impact
        impact = await self._assess_impact(vuln)

        # Step 4: Calculate priority score
        priority_score = self._calculate_priority(
            severity=vuln.severity,
            exploitability=exploitability,
            impact=impact
        )

        # Step 5: Determine response SLA
        sla = VulnerabilityResponseCriteria.SEVERITY_SLA.get(vuln.severity)

        return TriageResult(
            priority=self._score_to_priority(priority_score),
            exploitability=exploitability,
            impact=impact,
            sla_hours=sla["max_age_hours"],
            recommended_action="auto_fix" if exploitability < 0.5 else "manual_review"
        )

    async def _confirm_applicability(self, vuln: Vulnerability) -> bool:
        """Verify vulnerability actually affects our system."""

        # Check if vulnerable dependency is actually used
        dependency = vuln.affected_package
        version = vuln.affected_version_range

        # Get our installed dependencies
        installed = self._get_installed_packages()

        if dependency not in installed:
            return False

        installed_version = installed[dependency]

        # Check if installed version is in vulnerable range
        return version.matches(installed_version)

    async def _assess_exploitability(self, vuln: Vulnerability) -> float:
        """Score 0.0-1.0 on how easily exploitable."""

        # Factors:
        # - Public exploit available? (+0.5)
        # - Requires authentication? (-0.3)
        # - Requires user interaction? (-0.2)
        # - Network accessible? (+0.3)

        score = 0.0

        if vuln.has_public_exploit:
            score += 0.5

        if not vuln.requires_authentication:
            score += 0.3

        if not vuln.requires_user_interaction:
            score += 0.2

        if vuln.network_accessible:
            score += 0.3

        return min(1.0, score)

    async def _assess_impact(self, vuln: Vulnerability) -> Dict[str, str]:
        """Assess CIA impact."""
        return {
            "confidentiality": vuln.cia_impact.get("C", "NONE"),
            "integrity": vuln.cia_impact.get("I", "NONE"),
            "availability": vuln.cia_impact.get("A", "NONE")
        }
```

**Implementation Priority**: **P1 (High)**
**Effort**: 3 days

---

### RV.2: Assess, Prioritize, and Remediate Vulnerabilities

**NIST Practice**: Analyze vulnerabilities, determine priority, remediate.

#### Direct Applicability: ✅ YES (already covered in PO.4 and RV.1)

**Current Implementation**: See VulnerabilityResponseCriteria and vulnerability_response_cycle in PO.4.

**Additional Consideration - Learning from Remediation**:

```python
# ENHANCEMENT: Learn from vulnerability remediations
class VulnerabilityLearningSystem:
    """Track vulnerability patterns and improve future code generation."""

    def __init__(self):
        self.vulnerability_history = []

    async def learn_from_vulnerability(self, vuln: Vulnerability, remediation: Remediation):
        """Extract patterns from vulnerabilities to prevent recurrence."""

        # Record vulnerability
        self.vulnerability_history.append({
            "vulnerability": vuln,
            "remediation": remediation,
            "timestamp": datetime.utcnow()
        })

        # Extract pattern
        pattern = await self._extract_pattern(vuln, remediation)

        # Update security requirements
        if pattern.should_add_requirement:
            await self._create_security_requirement(pattern)

        # Update dharmic gate checks
        if pattern.should_add_gate_check:
            await self._update_dharmic_gate(pattern)

        # Update writer agent training
        if pattern.should_add_to_training:
            await self._update_agent_training(pattern)

    async def _extract_pattern(self, vuln: Vulnerability, remediation: Remediation) -> Pattern:
        """Analyze vulnerability to extract preventable pattern."""

        # Example: If vuln was SQL injection, pattern is "parameterized queries"
        # Example: If vuln was XSS, pattern is "input sanitization"

        if vuln.cwe == "CWE-89":  # SQL Injection
            return Pattern(
                name="sql_injection_prevention",
                description="Always use parameterized queries",
                detection_regex=r"cursor\\.execute\\(.*f['\"].*\\{.*\\}",
                should_add_requirement=True,
                should_add_gate_check=True,
                severity="CRITICAL"
            )

        # ... more pattern extraction logic
```

**Implementation Priority**: **P2 (Important for continuous improvement)**
**Effort**: 3 days

---

### RV.3: Analyze Vulnerabilities to Identify Root Causes

**NIST Practice**: Perform root cause analysis on vulnerabilities.

#### Direct Applicability: ✅ YES (Evolver Agent natural fit)

**Recommended Implementation**:

```python
# NEW: Root Cause Analysis by Evolver Agent
class EvolverAgent:

    async def root_cause_analysis(self, vuln: Vulnerability, remediation: Remediation) -> RootCauseAnalysis:
        """Analyze why vulnerability was introduced."""

        # Step 1: Find when vulnerable code was introduced
        git_blame = await self._git_blame_vulnerability(vuln)

        # Step 2: Was it human or agent?
        if git_blame.author == "dharmic_agent":
            # Agent-generated code
            origin = await self._trace_agent_generation(git_blame)

            rca = RootCauseAnalysis(
                generated_by="agent",
                agent_name=origin.agent_name,
                model=origin.model,
                prompt_hash=origin.prompt_hash,
                evolution_id=origin.evolution_id,
                fitness_at_generation=origin.fitness,
                gates_passed=origin.gates_passed,

                # Root causes
                root_causes=[
                    f"Dharmic Gate did not detect pattern: {vuln.pattern}",
                    f"Security requirements did not cover: {vuln.cwe}",
                    f"Tester Agent did not catch: {vuln.title}"
                ],

                # Recommendations
                recommendations=[
                    f"Add security requirement for {vuln.cwe}",
                    f"Update Dharmic Gate with pattern: {vuln.pattern}",
                    f"Add security test for {vuln.vulnerability_class}"
                ]
            )
        else:
            # Human-generated code
            rca = RootCauseAnalysis(
                generated_by="human",
                author=git_blame.author,
                root_causes=["Manual code introduction"],
                recommendations=["Add security training for human developers"]
            )

        return rca

    async def _trace_agent_generation(self, git_blame: GitBlame) -> AgentGenerationOrigin:
        """Trace back to which agent generated this code and why."""

        commit_hash = git_blame.commit_hash

        # Look up in DGM Archive
        evolution_entry = await self.archive.find_by_commit(commit_hash)

        if evolution_entry:
            return AgentGenerationOrigin(
                agent_name=evolution_entry.agent_id,
                model=evolution_entry.model,
                prompt_hash=evolution_entry.prompt_hash,
                evolution_id=evolution_entry.id,
                fitness=evolution_entry.fitness.total(),
                gates_passed=evolution_entry.gates_passed
            )

        return None
```

**Key Insight**: Root cause analysis for agent-generated vulnerabilities should feed back into:
1. **Security requirements** (add missing requirement)
2. **Dharmic gate** (add missing check)
3. **Test suite** (add missing security test)
4. **Agent training** (update system prompts with pattern)

This creates a **learning loop** where each vulnerability makes the system stronger.

**Implementation Priority**: **P2 (Important for learning)**
**Effort**: 4 days

---

## Summary: Implementation Roadmap

### Phase 0: Critical Security Fixes (Week 1)

**Priority**: P0
**Effort**: 3-5 days
**Status**: Blocking issues

| Task | Effort | Files Affected |
|------|--------|----------------|
| Fix .env permissions | 1h | `.env` |
| Migrate to keyring | 4h | `email_daemon.py`, config |
| Implement SecurityRequirements.yaml | 1 day | New file + Dharmic Gate integration |
| Add secure coding patterns to Writer Agent | 2 days | `writer.py`, `config.py` |
| Integrate SAST tools (Bandit, Semgrep) | 2 days | `tester.py` |

**Deliverables**:
- ✅ No more credential exposure
- ✅ Secure coding patterns enforced
- ✅ SAST in CI/CD pipeline

---

### Phase 1: Security Foundation (Weeks 2-3)

**Priority**: P1
**Effort**: 2 weeks

| Task | Effort | Agent Responsible |
|------|--------|-------------------|
| Implement SecurityContextManager | 2 days | Core infrastructure |
| Add Agent Responsibility definitions | 2 days | Documentation + orchestrator |
| Implement Multi-Agent Security Review Board | 3 days | Dharmic Gate + orchestrator |
| Add Dependency Security Manager | 4 days | Writer Agent |
| Implement Vulnerability Monitoring Agent | 4 days | New agent |
| Vulnerability Response Criteria | 2 days | Orchestrator |

**Deliverables**:
- ✅ Security requirements machine-readable
- ✅ Agent responsibilities clear
- ✅ Multi-agent review for high-risk changes
- ✅ Dependency security checks
- ✅ Continuous vulnerability monitoring

---

### Phase 2: Advanced Security (Weeks 4-5)

**Priority**: P2
**Effort**: 2 weeks

| Task | Effort | Purpose |
|------|--------|---------|
| Implement SandboxedTesterAgent | 3 days | Isolate test execution |
| Add Fuzzing capability | 3 days | Find edge case vulnerabilities |
| Implement Agentic SBOM generation | 3 days | Provenance tracking |
| Add Self-Review to Writer Agent | 2 days | Improve code quality |
| Implement Vulnerability Learning System | 3 days | Learn from vulnerabilities |
| Root Cause Analysis integration | 2 days | Feed learning loop |

**Deliverables**:
- ✅ Sandboxed test execution
- ✅ Fuzzing integrated
- ✅ AI provenance in SBOM
- ✅ Self-improving security posture

---

### Phase 3: Security Excellence (Future)

**Priority**: P3
**Effort**: 4+ weeks

| Task | Effort | Description |
|------|--------|-------------|
| Architecture Agent (threat modeling) | 2 weeks | System-level security design |
| Formal verification integration | 3 weeks | Prove security properties |
| Red team exercises | Ongoing | Test security posture |
| Security metrics dashboard | 1 week | Visibility into security state |
| Compliance automation (SOC2, ISO27001) | 2 weeks | Automated compliance evidence |

---

## Key Metrics to Track

### Security Fitness Metrics

```python
class SecurityMetrics:
    """Track security posture over time."""

    metrics = {
        "vulnerabilities": {
            "critical_open": 0,
            "high_open": 2,
            "medium_open": 5,
            "low_open": 8,
            "mean_time_to_remediate_critical": 3.5,  # hours
            "mean_time_to_remediate_high": 18.2  # hours
        },

        "code_security": {
            "sast_issues_per_kloc": 1.2,
            "secret_leaks": 0,
            "insecure_dependencies": 0,
            "security_test_coverage": 0.78
        },

        "agent_security": {
            "dharmic_gate_veto_rate": 0.12,  # 12% of proposals vetoed
            "security_review_required_rate": 0.05,
            "auto_remediation_success_rate": 0.85
        },

        "compliance": {
            "security_requirements_coverage": 0.94,
            "secure_coding_pattern_adherence": 0.91,
            "sbom_completeness": 1.0
        }
    }
```

**Target Goals** (6 months):
- Zero CRITICAL vulnerabilities in production
- MTTR for CRITICAL: <4 hours
- SAST issues: <0.5 per KLOC
- Security test coverage: >85%
- Dharmic gate veto rate: <10%
- Auto-remediation success: >90%

---

## Conclusion

### What Translates Directly

✅ **18 of 22 NIST SSDF practices** (82%) apply to agentic systems with minimal adaptation:
- PO.3: Toolchains (just integrate into agents)
- PO.5: Secure environments (standard hardening)
- PS.1: Access control (agent-specific extensions)
- PS.2: Release integrity (add AI provenance)
- PW.4: Reuse secure software (add dependency approval)
- PW.6: Secure defaults (agents can enforce)
- PW.8: Testing (agents excel at automation)
- RV.1: Vulnerability identification (agents can monitor 24/7)
- RV.2: Remediation (agents can auto-fix)

### What Needs Adaptation

⚠️ **4 practices require significant redesign**:
- PO.1: Security requirements → Need machine-readable format
- PO.2: Roles/responsibilities → Agent responsibility model
- PW.1: Design → Architecture Agent (future)
- PW.2: Code review → Multi-agent review board

### What's Novel for Agentic Systems

🆕 **5 new security capabilities unique to agents**:
1. **Continuous monitoring** (agents don't sleep)
2. **Auto-remediation** (agents can fix many vulnerabilities autonomously)
3. **Learning loops** (agents improve from vulnerabilities)
4. **AI provenance tracking** (SBOM + model/prompt lineage)
5. **Multi-agent consensus** (review board with diverse perspectives)

### The Core Insight

Traditional SSDF assumes **human developers are the primary actors**. In agentic systems:

```
Traditional:  Human writes code → Human reviews → Human deploys → Human fixes bugs
Agentic:      Agent proposes → Gate evaluates → Agent implements → Agent tests → Agent auto-fixes
              ↑                                                                    ↓
              └────────────────────── Learning loop ──────────────────────────────┘
```

The shift is from **human-in-the-loop** to **agent-in-the-loop with human oversight**. This requires:
- Stronger guardrails (Dharmic Gates)
- More automation (continuous monitoring, testing)
- Better provenance (who/what/why generated this code)
- Faster feedback loops (learn from every vulnerability)

### Implementation Priority Summary

| Phase | Duration | Focus | Critical Deliverables |
|-------|----------|-------|----------------------|
| **P0: Critical** | Week 1 | Fix immediate vulnerabilities | Credentials, SAST, secure coding |
| **P1: Foundation** | Weeks 2-3 | Build security infrastructure | Requirements, review board, vuln monitoring |
| **P2: Advanced** | Weeks 4-5 | Enhance security capabilities | Sandboxing, fuzzing, learning loops |
| **P3: Excellence** | Months 3-6 | Achieve security maturity | Architecture agent, compliance automation |

**Estimated Total Effort**: 8-10 weeks for full implementation of P0-P2.

---

## Next Steps

1. **Review this document** with human operator (John/Dhyana)
2. **Prioritize** which phases to implement based on risk assessment
3. **Create tickets** for each task in implementation roadmap
4. **Begin P0 work** immediately (critical security fixes)
5. **Establish metrics** to track security posture improvement

**Contact**: For questions or clarifications, consult DHARMIC_CLAW documentation or reach out to human operator.

---

*Document Version*: 1.0
*Last Updated*: 2026-02-04
*Next Review*: 2026-02-11 (or upon first vulnerability detection)

---

**Appendix A: NIST SSDF Quick Reference**

Full NIST SSDF 1.1 available at: https://csrc.nist.gov/publications/detail/sp/800-218/final

**Practice Groups**:
- **PO**: Prepare the Organization (5 practices)
- **PS**: Protect the Software (3 practices)
- **PW**: Produce Well-Secured Software (9 practices)
- **RV**: Respond to Vulnerabilities (5 practices)

**Total**: 22 practices, 55 tasks

**Appendix B: Glossary**

- **SBOM**: Software Bill of Materials
- **SAST**: Static Application Security Testing
- **DAST**: Dynamic Application Security Testing
- **SCA**: Software Composition Analysis
- **CVE**: Common Vulnerabilities and Exposures
- **CWE**: Common Weakness Enumeration
- **STRIDE**: Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, Elevation of Privilege
- **MTTR**: Mean Time To Remediate
- **KLOC**: Kilo Lines of Code (1000 lines)
- **CIA**: Confidentiality, Integrity, Availability

---

*End of Document*
