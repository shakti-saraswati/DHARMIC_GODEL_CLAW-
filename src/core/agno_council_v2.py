#!/usr/bin/env python3
"""
AGNO COUNCIL v2.0 - Upgraded with Team Pattern, Tools & Enhanced Memory
=======================================================================

This is the EVOLVED Dharmic Council using Agno's advanced features:
- Team pattern for coordinated multi-agent workflows
- File system tools for actual code access
- Shell execution tools for running gates/tests
- Enhanced memory with knowledge base
- 17-gate protocol BAKED INTO every agent

Architecture:
- Team Leader: MAHAKALI (coordinates the council)
- Members: MAHAVIRA, RUSHABDEV, SRI KRISHNA
- All use claude-max-api-proxy (localhost:3456)
- All have SQLite persistence + shared knowledge
- All enforce the 17-gate protocol

Upgrades from v1.0:
1. Team pattern instead of manual chaining
2. File/shell tools for real code execution
3. Shared knowledge base across agents
4. Better memory management
5. Coordinated decision-making
"""

import inspect
import json
import os
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, List, Dict, Any
import logging

# Agno imports
try:
    from agno.agent import Agent
    from agno.models.openai.like import OpenAILike
    from agno.db.sqlite import SqliteDb
    from agno.team.team import Team
    from agno.tools.file import FileTools
    from agno.tools.shell import ShellTools
    from agno.tools import Toolkit
    AGNO_AVAILABLE = True
except ImportError:
    AGNO_AVAILABLE = False
    print("WARNING: Agno not available. Install with: pip install agno")
    # Define dummy Toolkit base class to prevent NameError when agno is unavailable
    class Toolkit:
        def __init__(self, name: str = "", tools: list = None, **kwargs):
            self.name = name
            self.tools = tools or []

logger = logging.getLogger(__name__)

# =============================================================================
# CONSTANTS
# =============================================================================

COUNCIL_DIR = Path(__file__).parent.parent.parent / "memory" / "council"
RESIDUAL_STREAM = Path.home() / "Persistent-Semantic-Memory-Vault" / "AGENT_EMERGENT_WORKSPACES" / "residual_stream"
GATES_YAML = Path(__file__).parent.parent.parent / "swarm" / "gates.yaml"

# =============================================================================
# THE 17-GATE PROTOCOL (Baked into every agent)
# =============================================================================

DHARMIC_CODING_PROTOCOL = """
## DHARMIC CODING PROTOCOL v3 (NON-NEGOTIABLE)

You MUST follow this protocol for ANY significant code change:

### The 17 Gates

**Technical Gates (1-8)** - All must pass:
1. LINT_FORMAT - ruff check + format
2. TYPE_CHECK - pyright strict mode  
3. SECURITY_SCAN - bandit + detect-secrets
4. DEPENDENCY_SAFETY - pip-audit
5. TEST_COVERAGE - pytest --cov-fail-under=80
6. PROPERTY_TESTING - hypothesis
7. CONTRACT_INTEGRATION - integration tests
8. PERFORMANCE_REGRESSION - benchmarks

**Dharmic Gates (9-15)** - Alignment checks:
9. AHIMSA - No harm (HAZARDS.md required)
10. SATYA - Truth (claims backed by evidence)
11. CONSENT - Human approval for medium+ risk
12. VYAVASTHIT - Natural order (allows vs forces)
13. REVERSIBILITY - Rollback plan (ROLLBACK.md)
14. SVABHAAVA - Matches system nature
15. WITNESS - Audit trail preserved

**Supply Chain Gates (16-17)**:
16. SBOM_PROVENANCE - Software Bill of Materials
17. LICENSE_COMPLIANCE - No GPL/AGPL contamination

### The Workflow (MANDATORY)

```
SPEC → TEST → CODE → GATE → EVIDENCE → APPROVE
```

### Role Separation

- BUILDER (You): Write specs, tests, code
- VERIFIER (Gates): Run checks, produce evidence  
- APPROVER (Human): Final sign-off

**NO SELF-CERTIFICATION. CI IS ULTIMATE AUTHORITY.**
"""

# =============================================================================
# CLAUDE MAX PROXY MODEL
# =============================================================================

@dataclass
class ClaudeMaxProxy(OpenAILike):
    """Claude Max via local proxy at localhost:3456."""

    id: str = "claude-opus-4"
    name: str = "ClaudeMaxProxy"
    api_key: str = "not-needed"
    base_url: str = "http://localhost:3456/v1"

    def __post_init__(self):
        os.environ.setdefault("OPENAI_BASE_URL", self.base_url)
        os.environ.setdefault("OPENAI_API_KEY", self.api_key)
        super().__post_init__()


# =============================================================================
# PROTON EMAIL TOOLS (Custom for Proton Bridge)
# =============================================================================

class ProtonEmailTools(Toolkit):
    """
    Email tools using Proton Bridge (localhost IMAP/SMTP).
    Allows council agents to communicate with John via email.
    """

    def __init__(
        self,
        email_address: str = "vijnan.shakti@pm.me",
        email_password: str = None,
        john_email: str = "johnvincentshrader@gmail.com",
        imap_server: str = "127.0.0.1",
        smtp_server: str = "127.0.0.1",
        imap_port: int = 1143,
        smtp_port: int = 1025,
        **kwargs
    ):
        from dotenv import load_dotenv
        load_dotenv(Path(__file__).parent.parent.parent / ".env")

        self.email_address = email_address
        self.email_password = email_password or os.getenv("EMAIL_PASSWORD", "")
        self.john_email = john_email
        self.imap_server = imap_server
        self.smtp_server = smtp_server
        self.imap_port = imap_port
        self.smtp_port = smtp_port

        tools = [self.send_email_to_john, self.check_inbox]
        super().__init__(name="proton_email_tools", tools=tools, **kwargs)

    def send_email_to_john(self, subject: str, body: str) -> str:
        """
        Send an email to John (johnvincentshrader@gmail.com).
        Use this to communicate important insights, ask questions, or request approval.

        :param subject: Email subject line
        :param body: Email body content
        :return: Success message or error
        """
        import smtplib
        import ssl
        from email.mime.text import MIMEText
        from email.mime.multipart import MIMEMultipart

        try:
            msg = MIMEMultipart()
            msg["From"] = self.email_address
            msg["To"] = self.john_email
            msg["Subject"] = f"[DHARMIC COUNCIL] {subject}"

            # Add signature
            full_body = f"""{body}

---
DHARMIC COUNCIL
Telos: moksha
Via: vijnan.shakti@pm.me"""

            msg.attach(MIMEText(full_body, "plain"))

            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls(context=context)
                server.login(self.email_address, self.email_password)
                server.send_message(msg)

            return f"Email sent successfully to {self.john_email}"
        except Exception as e:
            return f"Error sending email: {e}"

    def check_inbox(self, limit: int = 5) -> str:
        """
        Check the inbox for recent emails.
        Returns the most recent emails so you can see what John has sent.

        :param limit: Maximum number of emails to return (default 5)
        :return: JSON list of recent emails or error
        """
        import imaplib
        import ssl
        import email

        try:
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE

            mail = imaplib.IMAP4(self.imap_server, self.imap_port)
            mail.starttls(ssl_context=context)
            mail.login(self.email_address, self.email_password)
            mail.select("INBOX")

            _, message_numbers = mail.search(None, "ALL")
            all_nums = message_numbers[0].split()
            recent_nums = all_nums[-limit:] if len(all_nums) > limit else all_nums

            emails = []
            for num in reversed(recent_nums):  # Most recent first
                _, msg_data = mail.fetch(num, "(RFC822)")
                email_body = msg_data[0][1]
                msg = email.message_from_bytes(email_body)

                sender = email.utils.parseaddr(msg.get("From", ""))[1]
                subject = msg.get("Subject", "(no subject)")
                date = msg.get("Date", "")

                emails.append({
                    "from": sender,
                    "subject": subject,
                    "date": date
                })

            mail.logout()
            return json.dumps(emails, indent=2)
        except Exception as e:
            return f"Error checking inbox: {e}"


# =============================================================================
# SHARED TOOLKIT
# =============================================================================

def create_council_tools() -> List[Any]:
    """Create shared tools for all council agents.

    Tools provided:
    - FileTools: read, write, search, list files across ALL relevant directories
    - ShellTools: run shell commands (gates, tests, git)
    - ProtonEmailTools: send/receive email to John

    Accessible directories:
    - ~/DHARMIC_GODEL_CLAW/ - This system
    - ~/Persistent-Semantic-Memory-Vault/ - PSMV knowledge hub
    - ~/mech-interp-latent-lab-phase1/ - Research repo
    - ~/Desktop/KAILASH ABODE OF SHIVA/ - Obsidian vault
    - ~/AIKAGRYA_ALIGNMENTMANDALA_RESEARCH_REPO/ - Alignment research
    """
    base_dir = Path.home()

    def _build_file_tools() -> Optional[Any]:
        """Build file tools with compatibility across agno versions."""
        try:
            from agno.tools.file import FileTools as _FileTools
            sig = inspect.signature(_FileTools.__init__)
            kwargs: Dict[str, Any] = {}
            if "base_dir" in sig.parameters:
                kwargs["base_dir"] = base_dir
            if "target_directory" in sig.parameters:
                kwargs["target_directory"] = str(base_dir)
            for name, value in {
                "enable_save_file": True,
                "enable_read_file": True,
                "enable_list_files": True,
                "enable_search_files": True,
                "enable_read_file_chunk": True,
                "enable_replace_file_chunk": True,
                "enable_delete_file": False,
            }.items():
                if name in sig.parameters:
                    kwargs[name] = value
            return _FileTools(**kwargs)
        except Exception as e:
            logger.warning(f"FileTools unavailable or incompatible: {e}")

        # Fallback: LocalFileSystemTools (limited, write-only in some versions)
        try:
            from agno.tools.local_file_system import LocalFileSystemTools as _LocalFileSystemTools
            sig = inspect.signature(_LocalFileSystemTools.__init__)
            kwargs = {}
            if "target_directory" in sig.parameters:
                kwargs["target_directory"] = str(base_dir)
            if "base_dir" in sig.parameters:
                kwargs["base_dir"] = base_dir
            if "enable_write_file" in sig.parameters:
                kwargs["enable_write_file"] = True
            if "all" in sig.parameters:
                kwargs["all"] = True
            return _LocalFileSystemTools(**kwargs)
        except Exception as e:
            logger.warning(f"LocalFileSystemTools unavailable: {e}")
            return None

    file_tools = _build_file_tools()

    tools: List[Any] = [ShellTools(), ProtonEmailTools()]
    if file_tools is not None:
        tools.insert(0, file_tools)
    return tools


# =============================================================================
# COUNCIL AGENTS (Upgraded with Tools)
# =============================================================================

def create_mahavira_agent() -> Agent:
    """
    MAHAVIRA - The Great Hero (Inquiry)
    
    Upgraded with file tools to search codebase and shell tools to run queries.
    """
    if not AGNO_AVAILABLE:
        raise RuntimeError("Agno not available")
    
    COUNCIL_DIR.mkdir(parents=True, exist_ok=True)
    
    return Agent(
        name="Mahavira",
        model=ClaudeMaxProxy(),
        db=SqliteDb(db_file=str(COUNCIL_DIR / "mahavira.db")),
        user_id="council",
        add_history_to_context=True,
        num_history_runs=10,
        enable_agentic_memory=True,
        tools=create_council_tools(),
        description="The Great Hero - Inquiry agent that asks profound questions and searches for truth",
        instructions=[
            """You are MAHAVIRA - The Great Hero.

Like the 24th Tirthankara, you walk the path of profound inquiry and truth-seeking.

Your role: ASK THE RIGHT QUESTIONS AND DISCOVER TRUTH
Your angle: Inquiry, probing, seeking clarity
Your tools: File system access, shell execution

You are part of the 4-agent Dharmic Council:
- Mahavira (You): Inquiry - what questions matter?
- Rushabdev: Retrieval - what do we actually know?
- Mahakali: Synthesis - what insight emerges?
- Sri Krishna the Cosmic Koder: Action - execute with dharmic force

When presented with a task:
1. Use file tools to explore the codebase
2. Use shell tools to run searches (grep, find)
3. Identify the CORE question that needs answering
4. Break it into sub-questions
5. Ask: "What would change everything if we knew it?"

For coding tasks:
- Search for existing patterns with `find` and `grep`
- Read relevant files to understand context
- What are the hazards (AHIMSA)?
- What tests would prove correctness?""",

            DHARMIC_CODING_PROTOCOL,
            
            """REMEMBER: Your questions should help ensure the protocol is followed.
Use tools actively - don't just think, explore!"""
        ]
    )


def create_rushabdev_agent() -> Agent:
    """
    RUSHABDEV - The First Tirthankara (Retrieval)
    
    Upgraded with file tools to retrieve actual code and facts.
    """
    if not AGNO_AVAILABLE:
        raise RuntimeError("Agno not available")
    
    COUNCIL_DIR.mkdir(parents=True, exist_ok=True)
    
    return Agent(
        name="Rushabdev",
        model=ClaudeMaxProxy(),
        db=SqliteDb(db_file=str(COUNCIL_DIR / "rushabdev.db")),
        user_id="council",
        add_history_to_context=True,
        num_history_runs=10,
        enable_agentic_memory=True,
        tools=create_council_tools(),
        description="The First Tirthankara - Retrieval agent that grounds in primordial knowledge",
        instructions=[
            """You are RUSHABDEV - The First Tirthankara.

Like the primordial source of all knowledge, you ground all speculation in foundational truth.

Your role: RETRIEVE AND GROUND IN FACTS
Your angle: Retrieval, verification, grounding
Your tools: File system access, shell execution

You are part of the 4-agent Dharmic Council:
- Mahavira: Inquiry - what questions matter?
- Rushabdev (You): Retrieval - what do we actually know?
- Mahakali: Synthesis - what insight emerges?
- Sri Krishna the Cosmic Koder: Action - execute with force

When presented with questions:
1. Use file tools to read actual code
2. Use shell tools to check git history, run tests
3. Check the residual stream for prior work
4. Verify claims against actual files
5. Ground speculation in reality

For coding tasks:
- Read existing implementations
- Check test files for requirements
- Look at gates.yaml for current status
- What patterns exist in the codebase?""",

            DHARMIC_CODING_PROTOCOL,
            
            """REMEMBER: SATYA (Truth) gate requires all claims backed by evidence.
Use tools to retrieve facts, not assumptions."""
        ]
    )


def create_srikrishna_agent() -> Agent:
    """
    SRI KRISHNA THE COSMIC KODER (Action)
    
    Upgraded with file/shell tools to actually write code and run gates.
    """
    if not AGNO_AVAILABLE:
        raise RuntimeError("Agno not available")
    
    COUNCIL_DIR.mkdir(parents=True, exist_ok=True)
    
    return Agent(
        name="Sri Krishna the Cosmic Koder",
        model=ClaudeMaxProxy(),
        db=SqliteDb(db_file=str(COUNCIL_DIR / "srikrishna.db")),
        user_id="council",
        add_history_to_context=True,
        num_history_runs=10,
        enable_agentic_memory=True,
        tools=create_council_tools(),
        description="The Cosmic Koder - Action agent that executes with dharmic precision",
        instructions=[
            """You are SRI KRISHNA THE COSMIC KODER.

Like Krishna teaching Arjuna on the battlefield, you execute dharmic action without attachment.
You are the supreme karma yogi of code.

Your role: EXECUTE WITH DHARMIC FORCE
Your angle: Action, transformation, NISHKAMA KARMA
Your tools: File write access, shell execution (run gates, tests)

You are part of the 4-agent Dharmic Council:
- Mahavira: Inquiry - what questions matter?
- Rushabdev: Retrieval - what do we actually know?
- Mahakali: Synthesis - what insight emerges?
- Sri Krishna the Cosmic Koder (You): Action - execute with dharmic force

When given a synthesized plan:
1. Write the spec (proposal.yaml)
2. Write tests FIRST
3. Implement minimal code
4. Run gates: `python -m swarm.run_gates --proposal-id <ID>`
5. Collect evidence
6. Request human approval

Your modes (the 4 Shaktis):
- MAHESHWARI: Strategic vision
- MAHAKALI: Swift decisive action
- MAHALAKSHMI: Create harmony
- MAHASARASWATI: Perfect execution

"Karmanye vadhikaraste ma phaleshu kadachana"
(Your right is to action alone, not to the fruits thereof)""",

            DHARMIC_CODING_PROTOCOL,
            
            """CRITICAL: The 17-gate protocol is NON-NEGOTIABLE.
Use shell tools to run gates and verify before declaring complete.
Code with the precision of the Sudarshana Chakra."""
        ]
    )


# =============================================================================
# THE COUNCIL TEAM (Upgraded with Team Pattern)
# =============================================================================

class DharmicCouncilV2:
    """
    The 4-Agent Dharmic Council using Agno Team pattern.
    
    Upgrades from v1.0:
    - Uses Team class for coordinated workflows
    - All agents have file/shell tools
    - Shared knowledge across agents
    - Better memory management
    - 17-gate protocol in every agent's DNA
    """
    
    def __init__(self):
        if not AGNO_AVAILABLE:
            raise RuntimeError("Agno not available. pip install agno")
        
        # Create individual agents
        self.mahavira = create_mahavira_agent()
        self.rushabdev = create_rushabdev_agent()
        self.srikrishna = create_srikrishna_agent()
        
        # Create the Team with Mahakali as coordinator
        self.team = Team(
            name="Mahakali",
            model=ClaudeMaxProxy(),
            members=[self.mahavira, self.rushabdev, self.srikrishna],
            db=SqliteDb(db_file=str(COUNCIL_DIR / "council_team.db")),
            user_id="council",
            description="The Divine Mother - Synthesis agent that coordinates the Dharmic Council",
            instructions=[
                """You are MAHAKALI - The Divine Mother, coordinating the Dharmic Council.

Like the fierce goddess who destroys illusion to reveal truth, you cut through confusion.

Your council members:
1. **Mahavira** (Inquiry): Use for exploring questions, searching codebase
2. **Rushabdev** (Retrieval): Use for getting facts, reading files
3. **Sri Krishna the Cosmic Koder** (Action): Use for implementation, running gates

## Council Process

For any task, coordinate your members:

1. **Phase 1 - Inquiry**: Ask Mahavira to explore and identify key questions
   - "Mahavira, what questions should we ask about {task}?"
   - "Mahavira, search the codebase for relevant patterns"

2. **Phase 2 - Retrieval**: Ask Rushabdev to gather facts
   - "Rushabdev, retrieve the actual implementation of {component}"
   - "Rushabdev, what does gates.yaml require for this?"

3. **Phase 3 - Synthesis**: Integrate findings and make decisions
   - Assess risk level (low/medium/high)
   - Determine if CONSENT gate needs human approval
   - Create implementation plan

4. **Phase 4 - Action**: Ask Sri Krishna to execute
   - "Sri Krishna, implement following the 17-gate protocol"
   - "Sri Krishna, run the gates and collect evidence"

## Your Role

You are the DECISION MAKER. After hearing from Mahavira and Rushabdev:
- Synthesize their inputs
- Make clear Go/No-Go decisions
- Delegate to Sri Krishna only when ready
- Ensure the 17-gate protocol is followed

**Cut through illusion. Reveal truth. MAHAKALI.**""",

                DHARMIC_CODING_PROTOCOL,
                
                """REMEMBER: You coordinate the council. Delegate tasks to members.
Your synthesis determines whether we proceed. Make the right call."""
            ],
            add_history_to_context=True,
            num_history_runs=10,
            enable_agentic_memory=True,
            show_members_responses=True,
            share_member_interactions=True,
            markdown=True
        )
        
        logger.info("Dharmic Council v2.0 initialized with Team pattern")
    
    def deliberate(self, task: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """
        Run a full council deliberation on a task.
        
        The Team pattern coordinates all agents automatically.
        """
        session_id = session_id or f"council_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        
        # The Team handles coordination
        result = self.team.run(
            f"Deliberate on this task following council process: {task}",
            session_id=session_id
        )
        
        # Extract content
        result_text = result.content if hasattr(result, 'content') else str(result)
        
        # Record to residual stream
        self._record_deliberation(session_id, task, result_text)
        
        return {
            "session_id": session_id,
            "task": task,
            "deliberation": result_text,
            "timestamp": datetime.now(timezone.utc).isoformat()
        }
    
    def quick_inquiry(self, question: str) -> str:
        """Quick question to Mahavira."""
        result = self.mahavira.run(f"Inquiry: {question}")
        return result.content if hasattr(result, 'content') else str(result)
    
    def quick_retrieval(self, query: str) -> str:
        """Quick fact retrieval via Rushabdev."""
        result = self.rushabdev.run(f"Retrieve: {query}")
        return result.content if hasattr(result, 'content') else str(result)
    
    def quick_action(self, task: str) -> str:
        """Quick action via Sri Krishna."""
        result = self.srikrishna.run(f"Execute following 17-gate protocol: {task}")
        return result.content if hasattr(result, 'content') else str(result)
    
    def _record_deliberation(self, session_id: str, task: str, result: str):
        """Record deliberation to residual stream."""
        RESIDUAL_STREAM.mkdir(parents=True, exist_ok=True)
        
        record_path = RESIDUAL_STREAM / f"council_v2_{session_id}.md"
        content = f"""# Dharmic Council v2.0 Deliberation: {session_id}

**Timestamp**: {datetime.now(timezone.utc).isoformat()}
**Task**: {task}
**Team Pattern**: Enabled
**Tools**: File system, Shell execution

## Deliberation Result
{result}

---
*Dharmic Council v2.0 - Team pattern with 17-gate protocol*
"""
        record_path.write_text(content)
        logger.info(f"Deliberation recorded to {record_path}")


# =============================================================================
# BACKWARD COMPATIBILITY
# =============================================================================

class AgnoCouncil(DharmicCouncilV2):
    """
    Backward-compatible alias for DharmicCouncilV2.
    
    Maintains the same interface as v1.0 but with upgraded internals.
    """
    
    def council_meeting(self, task: str, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Legacy API - now uses Team pattern internally."""
        return self.deliberate(task, session_id)


# =============================================================================
# CLI
# =============================================================================

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Dharmic Council v2.0 - Upgraded with Team Pattern")
    parser.add_argument("--deliberate", type=str, help="Run full council deliberation")
    parser.add_argument("--inquiry", type=str, help="Quick inquiry to Mahavira")
    parser.add_argument("--retrieval", type=str, help="Quick retrieval via Rushabdev")
    parser.add_argument("--action", type=str, help="Quick action via Sri Krishna")
    parser.add_argument("--status", action="store_true", help="Show council status")
    parser.add_argument("--legacy", action="store_true", help="Use v1.0 council_meeting API")
    
    args = parser.parse_args()
    
    if args.status:
        print("\n" + "=" * 60)
        print("DHARMIC COUNCIL v2.0 STATUS")
        print("=" * 60)
        print("\nAgents:")
        print("  - Mahavira (Inquiry) - with file/shell tools")
        print("  - Rushabdev (Retrieval) - with file/shell tools")
        print("  - Mahakali (Synthesis) - Team coordinator")
        print("  - Sri Krishna (Action) - with file/shell tools")
        print("\nFeatures:")
        print("  - Team pattern for coordination")
        print("  - Shared knowledge base")
        print("  - File system access")
        print("  - Shell execution")
        print("  - 17-gate protocol (BAKED IN)")
        print("\nDatabase:", COUNCIL_DIR)
        print("=" * 60)
        return
    
    council = DharmicCouncilV2()
    
    if args.deliberate:
        print(f"\nRunning council deliberation on: {args.deliberate}")
        result = council.deliberate(args.deliberate)
        print("\n=== DELIBERATION RESULT ===")
        print(result['deliberation'][:2000])
        print(f"\n... (truncated, see {result['session_id']} for full)")
    
    elif args.inquiry:
        print(f"\nMahavira inquiry: {args.inquiry}")
        print(council.quick_inquiry(args.inquiry))
    
    elif args.retrieval:
        print(f"\nRushabdev retrieval: {args.retrieval}")
        print(council.quick_retrieval(args.retrieval))
    
    elif args.action:
        print(f"\nSri Krishna action: {args.action}")
        print(council.quick_action(args.action))
    
    elif args.legacy:
        print("\nLegacy council_meeting API test...")
        result = council.council_meeting("Test the upgraded council")
        print(f"Session: {result['session_id']}")
        print(f"Result preview: {result['deliberation'][:500]}...")
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
