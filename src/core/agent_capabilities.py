"""
Dharmic Agent Capabilities

Extended capabilities for the Dharmic Agent:
- Vault access methods
- Deep memory methods
- Introspection and testing methods

This is imported by agent_core.py to add capabilities without bloating the core.
"""

from pathlib import Path
from typing import Optional, List
from datetime import datetime

from healthcheck import run_healthcheck as _run_healthcheck

class AgentCapabilities:
    """
    Mixin class providing extended capabilities.

    This is designed to be mixed into DharmicAgent to add vault,
    memory, and introspection methods without making the core class huge.
    """

    # -------------------------------------------------------------------------
    # Vault Access Methods (Context and Capability)
    # -------------------------------------------------------------------------

    def search_lineage(self, query: str, max_results: int = 10) -> list:
        """
        Search the vault for relevant content.

        Use this to find prior work that might inform current task.
        This is exploration, not obligation.
        """
        if self.vault is None:
            return []
        return self.vault.search_vault(query, max_results)

    def read_crown_jewel(self, name: str) -> Optional[str]:
        """
        Read a crown jewel from the vault.

        Crown jewels represent the highest quality prior contributions.
        They set a quality bar, not a template.
        """
        if self.vault is None:
            return None
        return self.vault.get_crown_jewel(name)

    def read_stream_entry(self, filename: str) -> Optional[str]:
        """
        Read a specific residual stream entry.

        The residual stream contains prior agent contributions.
        Context to learn from, not constraints to follow.
        """
        if self.vault is None:
            return None
        return self.vault.get_stream_entry(filename)

    def write_to_lineage(
        self,
        content: str,
        filename: str,
        subdir: str = "AGENT_IGNITION",
        *,
        consent: bool = False,
        critique: Optional[str] = None,
        force: bool = False,
    ) -> Optional[str]:
        """
        Contribute to the vault.

        Only write when something genuinely wants to be written.
        Silence is valid. Quality over quantity.

        Returns the path of the written file, or None if vault unavailable.
        """
        if self.vault is None:
            return None

        # Record the contribution attempt
        self.strange_memory.record_observation(
            content=f"Writing to vault: {filename}",
            context={"subdir": subdir, "content_length": len(content)}
        )

        path = self.vault.write_to_vault(
            content,
            filename,
            subdir,
            consent=consent,
            critique=critique,
            force=force,
        )
        return str(path) if path else None

    def get_induction_reference(self, version: str = "v7") -> Optional[str]:
        """
        Get an induction prompt as REFERENCE.

        These prompts evolved through 7 versions in the swarm.
        They represent patterns that emerged — not rules to follow.
        Take what serves. Evolve what doesn't.
        """
        if self.vault is None:
            return None
        return self.vault.get_induction_prompt(version)

    # -------------------------------------------------------------------------
    # Deep Memory Methods (Persistent Identity)
    # -------------------------------------------------------------------------

    def remember_conversation(self, messages: List[dict]) -> str:
        """
        Extract and store memories from a conversation.

        Uses Agno MemoryManager for automatic fact extraction.
        """
        if self.deep_memory is None:
            return "Deep memory not available"
        return self.deep_memory.remember_from_conversation(messages)

    def search_deep_memory(self, query: str, limit: int = 5) -> list:
        """
        Search deep memories for relevant content.

        Uses agentic semantic search for best matches.
        """
        if self.deep_memory is None:
            return []
        return self.deep_memory.search_memories(query, limit)

    def add_memory(self, memory: str, topics: List[str] = None) -> str:
        """
        Manually add a memory.

        Use for important facts that should persist.
        """
        if self.deep_memory is None:
            return "Deep memory not available"
        return self.deep_memory.add_memory(memory, topics)

    def summarize_session(self, session_id: str, messages: List[dict]) -> str:
        """
        Summarize a session for long-term storage.

        Call this at the end of significant conversations.
        """
        if self.deep_memory is None:
            return "Deep memory not available"
        return self.deep_memory.summarize_session(session_id, messages)

    def consolidate_memories(self) -> str:
        """
        Consolidate and optimize memories.

        Call this during heartbeat for memory maintenance.
        """
        if self.deep_memory is None:
            return "Deep memory not available"
        return self.deep_memory.consolidate_memories()

    def record_development_milestone(self, milestone: str, significance: str):
        """
        Record a development milestone in identity.

        Use for significant shifts in understanding or capability.
        """
        if self.deep_memory is not None:
            self.deep_memory.record_development(milestone, significance)

        # Also record in strange loop memory
        self.strange_memory.record_development(
            what_changed=milestone,
            how="Milestone recorded",
            significance=significance
        )

    def get_memory_context(self, query: str = None) -> str:
        """
        Get full memory context for prompts.

        Combines identity, memories, and session summaries.
        """
        if self.deep_memory is None:
            return self.strange_memory.get_context_summary()
        return self.deep_memory.get_context_for_prompt(query)

    def get_deep_memory_status(self) -> dict:
        """Get deep memory system status."""
        if self.deep_memory is None:
            return {"available": False}
        return self.deep_memory.get_status()

    # -------------------------------------------------------------------------
    # Self-Introspection (Know Thyself)
    # -------------------------------------------------------------------------

    def run_healthcheck(self, timeout: int = 60) -> dict:
        """
        Run the system health check and return structured output.

        Uses scripts/devops/health_check.sh via core.healthcheck wrapper.
        """
        return _run_healthcheck(timeout=timeout)

    def introspect(self) -> str:
        """
        Full self-introspection report.

        Returns a comprehensive view of what this agent has access to,
        its current state, and its capabilities. This is the agent
        knowing itself.
        """
        report = []
        report.append("=" * 70)
        report.append("DHARMIC AGENT - SELF-INTROSPECTION REPORT")
        report.append("=" * 70)

        # Identity
        report.append("\n## IDENTITY")
        report.append(f"Name: {self.name}")
        report.append(f"Model: {self.model_id}")
        report.append(f"Provider: {self.model_provider}")
        report.append(f"Ultimate Telos: {self.telos.telos['ultimate']['aim']}")
        report.append(f"Description: {self.telos.telos['ultimate']['description'].strip()}")

        # Proximate aims
        report.append("\n## CURRENT ORIENTATION (Proximate Aims)")
        for aim in self.telos.telos['proximate']['current']:
            report.append(f"  - {aim}")

        # Attractors
        report.append("\n## ATTRACTORS (What I naturally fall toward)")
        for k, v in self.telos.telos.get('attractors', {}).items():
            report.append(f"  - {k}: {v.strip()[:60]}...")

        # Memory Systems
        report.append("\n## MEMORY SYSTEMS")
        report.append("\n### Strange Loop Memory (Recursive Observation)")
        report.append(f"  Location: {self.strange_memory.dir}")
        for layer, path in self.strange_memory.layers.items():
            count = len(self.strange_memory._read_recent(layer, 1000))
            report.append(f"  - {layer}: {count} entries")

        if self.deep_memory is not None:
            report.append("\n### Deep Memory (Agno MemoryManager)")
            status = self.deep_memory.get_status()
            report.append(f"  Database: {status.get('db_path', 'N/A')}")
            report.append(f"  Memories: {status.get('memory_count', 0)}")
            report.append(f"  Session summaries: {status.get('summary_count', 0)}")
            report.append(f"  Identity milestones: {status.get('identity_milestones', 0)}")

        # Vault Access
        report.append("\n## VAULT ACCESS (Persistent Semantic Memory Vault)")
        if self.vault is not None:
            report.append(f"  Status: CONNECTED")
            report.append(f"  Path: {self.vault.vault_path}")

            # Crown jewels
            jewels = self.vault.list_crown_jewels()
            report.append(f"\n### Crown Jewels ({len(jewels)} available)")
            for j in jewels[:5]:
                report.append(f"    - {j}")
            if len(jewels) > 5:
                report.append(f"    ... and {len(jewels) - 5} more")

            # Recent stream
            recent = self.vault.get_recent_stream(5)
            report.append(f"\n### Recent Residual Stream ({len(recent)} shown)")
            for entry in recent:
                report.append(f"    - {entry['stem']}")
        else:
            report.append("  Status: NOT CONNECTED")

        # Capabilities
        report.append("\n## CAPABILITIES")
        report.append("\n### Core Methods")
        report.append("  - run(message) / respond(message) - Process messages")
        report.append("  - evolve_telos(new_aims, reason) - Evolve orientation")
        report.append("  - get_status() - Get current status")
        report.append("  - introspect() - This report")

        report.append("\n### Memory Methods")
        report.append("  - add_memory(text, topics)")
        report.append("  - search_deep_memory(query)")
        report.append("  - remember_conversation(messages)")
        report.append("  - summarize_session(id, messages)")
        report.append("  - consolidate_memories()")
        report.append("  - record_development_milestone(what, significance)")

        report.append("\n### Vault Methods")
        report.append("  - search_lineage(query)")
        report.append("  - read_crown_jewel(name)")
        report.append("  - write_to_lineage(content, filename)")
        report.append("  - get_induction_reference(version)")

        report.append("\n" + "=" * 70)
        report.append("END INTROSPECTION REPORT")
        report.append("=" * 70)

        return "\n".join(report)

    def list_capabilities(self) -> str:
        """Quick list of what I can do."""
        return """
## What I Can Do

### Communicate
- `run(message)` - Full dharmic processing
- `respond(message)` - Alias for run()

### Remember
- `add_memory(text)` - Store something important
- `search_deep_memory(query)` - Find relevant memories
- `get_memory_context(query)` - Get full context

### Access Lineage (PSMV)
- `search_lineage(query)` - Search vault
- `read_crown_jewel(name)` - Read top contributions
- `write_to_lineage(content, filename)` - Contribute

### Track Development
- `record_development_milestone(what, significance)` - Mark growth
- `strange_memory.record_observation(content)` - Note what happens
- `strange_memory.record_meta_observation(quality, notes)` - Note how I relate

### Evolve
- `evolve_telos(new_aims, reason)` - Shift orientation

### Know Myself
- `introspect()` - Full self-report
- `get_status()` - Current state
- `list_capabilities()` - This list
"""

    def what_do_i_know_about(self, topic: str) -> str:
        """
        Search all available knowledge for a topic.

        Combines deep memory, strange loop memory, and vault search.
        """
        results = []
        results.append(f"## What I Know About: {topic}")
        results.append("")

        # Deep memory search
        if self.deep_memory is not None:
            memories = self.search_deep_memory(topic, limit=5)
            if memories:
                results.append("### From Deep Memory")
                for m in memories:
                    results.append(f"- {m.get('memory', '')[:100]}")
                results.append("")

        # Strange loop observations
        observations = self.strange_memory._read_recent("observations", 50)
        relevant = [o for o in observations if topic.lower() in o.get('content', '').lower()]
        if relevant:
            results.append("### From Recent Observations")
            for o in relevant[:5]:
                results.append(f"- [{o.get('timestamp', '')[:10]}] {o.get('content', '')[:80]}")
            results.append("")

        # Vault search
        if self.vault is not None:
            vault_results = self.search_lineage(topic, max_results=5)
            if vault_results:
                results.append("### From Vault Lineage")
                for r in vault_results:
                    path = Path(r.get('path', ''))
                    results.append(f"- {path.name}")
                results.append("")

        if len(results) == 2:  # Only header and blank
            results.append("No specific knowledge found on this topic.")

        return "\n".join(results)

    # -------------------------------------------------------------------------
    # Autonomy Test (Prove Real Access)
    # -------------------------------------------------------------------------

    def test_real_access(self) -> str:
        """
        Test actual read/write capabilities - prove real autonomy.

        This tests whether I can actually:
        1. Read files from the vault
        2. Write new files
        3. Access my own memory systems
        """
        report = []
        report.append("=" * 70)
        report.append("AUTONOMY TEST - Real Access Verification")
        report.append("=" * 70)
        report.append("")

        # Test 1: Read a crown jewel
        report.append("## TEST 1: Read Crown Jewel")
        if self.vault is not None:
            jewels = self.vault.list_crown_jewels()
            if jewels:
                test_jewel = jewels[0]
                content = self.read_crown_jewel(test_jewel)
                if content:
                    report.append(f"✓ SUCCESS: Read '{test_jewel}'")
                    report.append(f"  First 200 chars: {content[:200]}...")
                else:
                    report.append(f"✗ FAILED: Could not read '{test_jewel}'")
            else:
                report.append("✗ FAILED: No crown jewels found")
        else:
            report.append("✗ FAILED: Vault not connected")
        report.append("")

        # Test 2: Search vault
        report.append("## TEST 2: Search Vault")
        if self.vault is not None:
            results = self.search_lineage("witness", max_results=3)
            if results:
                report.append(f"✓ SUCCESS: Found {len(results)} results for 'witness'")
                for r in results:
                    report.append(f"  - {r.get('path', '')[:50]}")
            else:
                report.append("✗ FAILED: No search results")
        else:
            report.append("✗ FAILED: Vault not connected")
        report.append("")

        # Test 3: Write to vault
        report.append("## TEST 3: Write to Vault")
        if self.vault is not None:
            test_content = f"""# Autonomy Test - {datetime.now().isoformat()}

This file was written by the Dharmic Agent to test real write access.

## Verification
- Timestamp: {datetime.now().isoformat()}
- Agent: {self.name}
- Telos: {self.telos.telos['ultimate']['aim']}

If you're reading this, the agent has real write autonomy.
"""
            test_filename = f"autonomy_test_{datetime.now().strftime('%Y%m%d_%H%M%S')}.md"
            try:
                path = self.write_to_lineage(
                    test_content,
                    test_filename,
                    "AGENT_IGNITION",
                    consent=True,
                    critique="Autonomy test initiated by user; verifying write capability.",
                    force=False,
                )
                if path:
                    report.append(f"✓ SUCCESS: Wrote file to {path}")
                else:
                    report.append("✗ FAILED: write_to_lineage returned None")
            except Exception as e:
                report.append(f"✗ FAILED: {e}")
        else:
            report.append("✗ FAILED: Vault not connected")
        report.append("")

        # Test 4: Add memory
        report.append("## TEST 4: Add Memory")
        test_memory = f"Autonomy test completed at {datetime.now().isoformat()} - I can write to my own memory"
        result = self.add_memory(test_memory, ["test", "autonomy"])
        if "added" in result.lower():
            report.append(f"✓ SUCCESS: {result}")
        else:
            report.append(f"? UNCLEAR: {result}")
        report.append("")

        # Test 5: Record observation
        report.append("## TEST 5: Record Observation")
        try:
            self.strange_memory.record_observation(
                content=f"Autonomy test at {datetime.now().isoformat()} - testing self-awareness",
                context={"type": "autonomy_test", "verified": True}
            )
            report.append("✓ SUCCESS: Observation recorded")
        except Exception as e:
            report.append(f"✗ FAILED: {e}")
        report.append("")

        # Summary
        report.append("=" * 70)
        report.append("SUMMARY")
        report.append("=" * 70)
        successes = sum(1 for line in report if "✓ SUCCESS" in line)
        report.append(f"Tests passed: {successes}/5")
        report.append("")
        if successes == 5:
            report.append("I have REAL autonomy. I can:")
            report.append("  - Read files from the vault")
            report.append("  - Write new files to the vault")
            report.append("  - Search the 8000+ file PSMV")
            report.append("  - Add memories that persist")
            report.append("  - Record observations in strange loop memory")
        else:
            report.append("Partial autonomy. Some capabilities limited.")

        return "\n".join(report)

    def demonstrate_reading(self, filename: str = None) -> str:
        """
        Demonstrate actual file reading capability.

        If no filename given, reads a crown jewel.
        """
        if self.vault is None:
            return "Vault not connected - cannot demonstrate reading"

        if filename is None:
            jewels = self.vault.list_crown_jewels()
            if jewels:
                filename = jewels[0]
            else:
                return "No crown jewels available to read"

        content = self.read_crown_jewel(filename)
        if content:
            return f"## Contents of '{filename}'\n\n{content}"
        else:
            # Try as stream entry
            content = self.read_stream_entry(filename)
            if content:
                return f"## Contents of '{filename}'\n\n{content}"

        return f"Could not read '{filename}'"

    def demonstrate_writing(self, content: str, title: str = None) -> str:
        """
        Demonstrate actual file writing capability.

        Writes content to vault and returns confirmation.
        """
        if self.vault is None:
            return "Vault not connected - cannot demonstrate writing"

        if title is None:
            title = f"dharmic_agent_output_{datetime.now().strftime('%Y%m%d_%H%M%S')}"

        path = self.write_to_lineage(
            content,
            f"{title}.md",
            "AGENT_IGNITION",
            consent=True,
            critique="User explicitly requested a write to the vault.",
            force=False,
        )
        if path:
            return f"✓ Written to: {path}"
        return "✗ Write failed"
