#!/usr/bin/env python3
"""
Integration test for OpenClaw ↔ Codex CLI Bridge

Tests the complete lifecycle:
1. Queue a task
2. Run bridge_exec.py (dry-run mode)
3. Verify result appears in outbox/
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

# Add bridge directory to path for imports
BRIDGE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BRIDGE_DIR))

import bridge_queue


class TestBridgeIntegration(unittest.TestCase):
    """Integration tests for the Codex bridge."""

    @classmethod
    def setUpClass(cls):
        """Save original directories and create test isolation."""
        cls.original_inbox = bridge_queue.INBOX_DIR
        cls.original_outbox = bridge_queue.OUTBOX_DIR
        cls.original_state = bridge_queue.STATE_DIR
        cls.original_done = bridge_queue.DONE_DIR

    def setUp(self):
        """Create fresh test directories before each test."""
        self.test_dir = Path(tempfile.mkdtemp(prefix="bridge_test_"))
        
        # Override module-level directories for isolation
        bridge_queue.INBOX_DIR = self.test_dir / "inbox"
        bridge_queue.OUTBOX_DIR = self.test_dir / "outbox"
        bridge_queue.STATE_DIR = self.test_dir / "state"
        bridge_queue.DONE_DIR = self.test_dir / "state" / "done"
        
        bridge_queue.init_dirs()

    def tearDown(self):
        """Clean up test directories after each test."""
        # Restore original directories
        bridge_queue.INBOX_DIR = self.original_inbox
        bridge_queue.OUTBOX_DIR = self.original_outbox
        bridge_queue.STATE_DIR = self.original_state
        bridge_queue.DONE_DIR = self.original_done
        
        # Remove test directory
        if self.test_dir.exists():
            shutil.rmtree(self.test_dir)

    def test_01_init_creates_directories(self):
        """Test that init creates all required directories."""
        self.assertTrue(bridge_queue.INBOX_DIR.exists())
        self.assertTrue(bridge_queue.OUTBOX_DIR.exists())
        self.assertTrue(bridge_queue.STATE_DIR.exists())
        self.assertTrue(bridge_queue.DONE_DIR.exists())

    def test_02_enqueue_creates_task(self):
        """Test that enqueue creates a task file in inbox."""
        task = bridge_queue.enqueue_task(
            task="Test task for integration",
            sender="test-runner",
            scope=["src/core"],
            output=["report"],
            constraints=["read_only"],
        )
        
        self.assertIn("id", task)
        self.assertEqual(task["status"], "queued")
        self.assertEqual(task["task"], "Test task for integration")
        
        # Verify file exists
        task_path = bridge_queue.INBOX_DIR / f"{task['id']}.json"
        self.assertTrue(task_path.exists())
        
        # Verify content
        stored = json.loads(task_path.read_text())
        self.assertEqual(stored["id"], task["id"])
        self.assertEqual(stored["task"], "Test task for integration")

    def test_03_list_pending_shows_queued_tasks(self):
        """Test that list_pending returns queued tasks."""
        # Queue multiple tasks
        task1 = bridge_queue.enqueue_task(task="Task 1")
        task2 = bridge_queue.enqueue_task(task="Task 2")
        
        pending = bridge_queue.list_pending()
        self.assertEqual(len(pending), 2)
        
        task_ids = [t["id"] for t in pending]
        self.assertIn(task1["id"], task_ids)
        self.assertIn(task2["id"], task_ids)

    def test_04_claim_moves_task_to_state(self):
        """Test that claim moves task from inbox to state."""
        task = bridge_queue.enqueue_task(task="Task to claim")
        
        claimed = bridge_queue.claim_task(claimed_by="test-agent")
        
        self.assertIsNotNone(claimed)
        self.assertEqual(claimed["id"], task["id"])
        self.assertEqual(claimed["status"], "in_progress")
        self.assertIn("claimed_at", claimed)
        
        # Verify moved from inbox to state
        self.assertFalse((bridge_queue.INBOX_DIR / f"{task['id']}.json").exists())
        self.assertTrue((bridge_queue.STATE_DIR / f"{task['id']}.json").exists())

    def test_05_respond_creates_result(self):
        """Test that respond creates result in outbox."""
        task = bridge_queue.enqueue_task(task="Task for response")
        claimed = bridge_queue.claim_task()
        
        response = bridge_queue.respond_task(
            task_id=claimed["id"],
            status="done",
            summary="Task completed successfully",
            report_path=f"outbox/{claimed['id']}.md",
        )
        
        self.assertEqual(response["id"], claimed["id"])
        self.assertEqual(response["status"], "done")
        
        # Verify response file exists
        response_path = bridge_queue.OUTBOX_DIR / f"{claimed['id']}.json"
        self.assertTrue(response_path.exists())
        
        # Verify task moved to done
        self.assertFalse((bridge_queue.STATE_DIR / f"{claimed['id']}.json").exists())
        self.assertTrue((bridge_queue.DONE_DIR / f"{claimed['id']}.json").exists())

    def test_06_full_lifecycle_integration(self):
        """Full integration test: enqueue → claim → respond → verify."""
        # 1. Enqueue
        task = bridge_queue.enqueue_task(
            task="Audit DGM integration gaps",
            sender="integration-test",
            scope=["src/core", "analysis"],
            output=["report", "recommendations"],
            constraints=["read_only", "cite_paths"],
            payload={"priority": "high", "deadline": "2024-01-15"},
        )
        
        task_id = task["id"]
        self.assertEqual(task["status"], "queued")
        
        # 2. Claim
        claimed = bridge_queue.claim_task(claimed_by="codex-agent")
        self.assertEqual(claimed["id"], task_id)
        self.assertEqual(claimed["status"], "in_progress")
        
        # 3. Respond with result
        report_content = "# Integration Report\n\nGaps identified:\n- Gap A\n- Gap B"
        report_path = bridge_queue.OUTBOX_DIR / f"{task_id}.md"
        report_path.write_text(report_content)
        
        response = bridge_queue.respond_task(
            task_id=task_id,
            status="done",
            summary="Audit complete. 2 gaps identified.",
            report_path=str(report_path),
        )
        
        # 4. Verify results
        self.assertEqual(response["status"], "done")
        
        # Verify response JSON
        response_json = bridge_queue.OUTBOX_DIR / f"{task_id}.json"
        self.assertTrue(response_json.exists())
        
        result = json.loads(response_json.read_text())
        self.assertEqual(result["summary"], "Audit complete. 2 gaps identified.")
        
        # Verify report exists
        self.assertTrue(report_path.exists())
        self.assertEqual(report_path.read_text(), report_content)
        
        # Verify done record
        done_path = bridge_queue.DONE_DIR / f"{task_id}.json"
        self.assertTrue(done_path.exists())
        done = json.loads(done_path.read_text())
        self.assertEqual(done["status"], "done")


class TestBridgeExecIntegration(unittest.TestCase):
    """Integration tests using bridge_exec.py subprocess."""

    def setUp(self):
        """Initialize bridge directories."""
        bridge_queue.init_dirs()
        # Clean inbox for fresh test
        for f in bridge_queue.INBOX_DIR.glob("*.json"):
            f.unlink()

    def test_bridge_exec_dry_run(self):
        """Test bridge_exec.py in dry-run mode."""
        # 1. Queue a task via CLI
        result = subprocess.run(
            [
                sys.executable, str(BRIDGE_DIR / "bridge_queue.py"),
                "enqueue",
                "--task", "Test dry-run execution",
                "--from", "pytest",
                "--scope", "src/test",
                "--output", "prompt",
            ],
            capture_output=True,
            text=True,
            cwd=str(BRIDGE_DIR),
        )
        
        self.assertEqual(result.returncode, 0, f"Enqueue failed: {result.stderr}")
        task = json.loads(result.stdout)
        task_id = task["id"]
        
        # 2. Run bridge_exec.py --dry-run
        result = subprocess.run(
            [
                sys.executable, str(BRIDGE_DIR / "bridge_exec.py"),
                "--dry-run",
            ],
            capture_output=True,
            text=True,
            cwd=str(BRIDGE_DIR),
        )
        
        self.assertEqual(result.returncode, 0, f"bridge_exec failed: {result.stderr}")
        
        # 3. Verify prompt file created in outbox
        prompt_path = bridge_queue.OUTBOX_DIR / f"{task_id}.prompt.md"
        self.assertTrue(prompt_path.exists(), f"Prompt not found at {prompt_path}")
        
        prompt_content = prompt_path.read_text()
        self.assertIn("Test dry-run execution", prompt_content)
        self.assertIn("src/test", prompt_content)
        
        # 4. Verify response JSON
        response_path = bridge_queue.OUTBOX_DIR / f"{task_id}.json"
        self.assertTrue(response_path.exists(), f"Response not found at {response_path}")
        
        response = json.loads(response_path.read_text())
        self.assertEqual(response["status"], "needs_run")
        self.assertIn("Prompt written", response["summary"])


class TestBridgeCLI(unittest.TestCase):
    """Test CLI interface of bridge_queue.py."""

    def setUp(self):
        """Initialize and clean directories."""
        bridge_queue.init_dirs()
        for f in bridge_queue.INBOX_DIR.glob("*.json"):
            f.unlink()
        for f in bridge_queue.STATE_DIR.glob("*.json"):
            f.unlink()

    def test_cli_init(self):
        """Test 'init' command."""
        result = subprocess.run(
            [sys.executable, str(BRIDGE_DIR / "bridge_queue.py"), "init"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        output = json.loads(result.stdout)
        self.assertTrue(output["ok"])

    def test_cli_enqueue_list_claim_respond(self):
        """Test full CLI workflow."""
        # Enqueue
        result = subprocess.run(
            [
                sys.executable, str(BRIDGE_DIR / "bridge_queue.py"),
                "enqueue", "--task", "CLI test task",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        task = json.loads(result.stdout)
        task_id = task["id"]
        
        # List
        result = subprocess.run(
            [sys.executable, str(BRIDGE_DIR / "bridge_queue.py"), "list"],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        tasks = json.loads(result.stdout)
        self.assertEqual(len(tasks), 1)
        
        # Claim
        result = subprocess.run(
            [
                sys.executable, str(BRIDGE_DIR / "bridge_queue.py"),
                "claim", "--by", "test-agent",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        claimed = json.loads(result.stdout)
        self.assertEqual(claimed["id"], task_id)
        
        # Respond
        result = subprocess.run(
            [
                sys.executable, str(BRIDGE_DIR / "bridge_queue.py"),
                "respond",
                "--id", task_id,
                "--status", "done",
                "--summary", "Test complete",
            ],
            capture_output=True,
            text=True,
        )
        self.assertEqual(result.returncode, 0)
        response = json.loads(result.stdout)
        self.assertEqual(response["status"], "done")


def run_quick_smoke_test():
    """Quick smoke test that can be run standalone."""
    print("🔧 Running Codex Bridge Smoke Test...\n")
    
    bridge_queue.init_dirs()
    
    # Clean slate
    for f in bridge_queue.INBOX_DIR.glob("*.json"):
        f.unlink()
    
    # 1. Enqueue
    print("1️⃣ Enqueueing task...")
    task = bridge_queue.enqueue_task(
        task="Smoke test: verify bridge works",
        sender="smoke-test",
        scope=["ops/bridge"],
        output=["confirmation"],
    )
    print(f"   ✅ Task queued: {task['id']}")
    
    # 2. List pending
    print("\n2️⃣ Listing pending tasks...")
    pending = bridge_queue.list_pending()
    print(f"   ✅ Found {len(pending)} pending task(s)")
    
    # 3. Claim
    print("\n3️⃣ Claiming task...")
    claimed = bridge_queue.claim_task(claimed_by="smoke-test-agent")
    print(f"   ✅ Claimed task: {claimed['id']}")
    
    # 4. Respond
    print("\n4️⃣ Responding to task...")
    response = bridge_queue.respond_task(
        task_id=claimed["id"],
        status="done",
        summary="Smoke test passed!",
    )
    print(f"   ✅ Response recorded: status={response['status']}")
    
    # 5. Verify results
    print("\n5️⃣ Verifying results in outbox/...")
    response_path = bridge_queue.OUTBOX_DIR / f"{task['id']}.json"
    if response_path.exists():
        result = json.loads(response_path.read_text())
        print(f"   ✅ Result found: {result['summary']}")
    else:
        print(f"   ❌ Result not found at {response_path}")
        return False
    
    print("\n" + "="*50)
    print("🎉 SMOKE TEST PASSED!")
    print("="*50)
    return True


if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == "--smoke":
        # Quick smoke test
        success = run_quick_smoke_test()
        sys.exit(0 if success else 1)
    else:
        # Full test suite
        unittest.main(verbosity=2)
