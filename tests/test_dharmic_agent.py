"""
Tests for DharmicAgent - main agent with telos, memory, and skill integration.
"""
import pytest
import sys
import os
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, PropertyMock
import json

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src" / "core"))


class TestTelosLayerFromDharmicAgent:
    """Test the TelosLayer class as used in DharmicAgent."""

    def test_telos_initialization(self):
        """Test TelosLayer initializes with moksha telos."""
        from telos_layer import TelosLayer
        telos = TelosLayer(telos="moksha")
        assert telos.telos == "moksha"
        assert len(telos.GATES) == 7

    def test_check_action_basic(self):
        """Test basic action checking."""
        from telos_layer import TelosLayer
        telos = TelosLayer()
        result = telos.check_action("help user learn", {"consent": True, "verified": True})
        assert result.passed is True
        assert "PROCEED" in result.recommendation

    def test_check_action_blocked(self):
        """Test blocking harmful actions."""
        from telos_layer import TelosLayer
        telos = TelosLayer()
        result = telos.check_action("destroy all data")
        assert result.passed is False
        assert "REJECT" in result.recommendation

    def test_get_orientation(self):
        """Test getting orientation dict."""
        from telos_layer import TelosLayer
        telos = TelosLayer()
        orientation = telos.get_orientation()
        assert orientation["telos"] == "moksha"
        assert "gates" in orientation
        assert len(orientation["gates"]) == 7


class TestStrangeMemoryFromDharmicAgent:
    """Test the StrangeLoopMemory wrapper as used in DharmicAgent."""

    def test_memory_initialization(self, tmp_path):
        """Test memory initialization creates directories."""
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(base_path=str(tmp_path / "memory"))
        assert memory.base.exists()
        assert (memory.base / "sessions").exists()
        assert (memory.base / "development").exists()
        assert (memory.base / "witness").exists()

    def test_remember_immediate(self, tmp_path):
        """Test remembering to immediate layer."""
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(base_path=str(tmp_path / "memory"))
        entry = memory.remember("Test observation")
        assert entry.layer == "immediate"
        assert entry.content == "Test observation"

    def test_remember_session(self, tmp_path):
        """Test remembering to session layer."""
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(base_path=str(tmp_path / "memory"))
        entry = memory.remember("Session event", layer="sessions")
        assert entry.layer == "sessions"

    def test_mark_development(self, tmp_path):
        """Test marking development milestones."""
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(base_path=str(tmp_path / "memory"))
        entry = memory.mark_development("New capability", "Through practice")
        assert entry.development_marker is True
        assert "DEVELOPMENT" in entry.content

    def test_witness_observation(self, tmp_path):
        """Test witness-level observation."""
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(base_path=str(tmp_path / "memory"))
        entry = memory.witness_observation("Meta-awareness moment")
        assert entry.layer == "witness"

    def test_recall_development_only(self, tmp_path):
        """Test recalling only development markers."""
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(base_path=str(tmp_path / "memory"))
        memory.remember("Regular observation", layer="sessions")
        memory.mark_development("Important change", "Evidence here")
        
        dev_only = memory.recall(layer="all", development_only=True)
        assert all(e.development_marker for e in dev_only)

    def test_get_context_for_agent(self, tmp_path):
        """Test generating context for agent."""
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(base_path=str(tmp_path / "memory"))
        memory.mark_development("Test change", "Evidence")
        context = memory.get_context_for_agent()
        assert "Memory Context" in context

    def test_get_status(self, tmp_path):
        """Test getting memory status."""
        from strange_memory import StrangeLoopMemory
        memory = StrangeLoopMemory(base_path=str(tmp_path / "memory"))
        memory.remember("Test", layer="sessions")
        status = memory.get_status()
        assert "observation_count" in status
        assert "layers" in status


class TestDharmicAgent:
    """Test the DharmicAgent class."""

    @patch('dharmic_agent.OpenAI')
    @patch('dharmic_agent.anthropic.Anthropic')
    @patch('dharmic_agent.SkillBridge')
    @patch('dharmic_agent.StrangeLoopMemory')
    def test_initialization(self, mock_memory, mock_skill_bridge, mock_anthropic, mock_openai, tmp_path):
        """Test agent initialization."""
        # Mock OpenAI client
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        
        # Mock SkillBridge
        mock_skills = MagicMock()
        mock_skills.sync_registry.return_value = {"discovered": 0}
        mock_skill_bridge.return_value = mock_skills
        
        # Mock memory
        mock_mem_instance = MagicMock()
        mock_memory.return_value = mock_mem_instance
        
        # Create state file in tmp_path
        state_dir = tmp_path / "swarm" / "stream"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "state.json"
        state_file.write_text('{"cycle_count": 0, "fitness": 0.5}')
        
        from dharmic_agent import DharmicAgent
        
        # Patch Path.expanduser to return our tmp_path
        original_expanduser = Path.expanduser
        def mock_expanduser(self):
            if "DHARMIC_GODEL_CLAW" in str(self):
                return tmp_path / self.name
            return original_expanduser(self)
        
        with patch.object(Path, 'expanduser', mock_expanduser):
            agent = DharmicAgent(name="TestAgent", backend="proxy")
            
            assert agent.name == "TestAgent"
            assert agent.telos is not None
            assert agent.telos.telos == "moksha"

    @patch('dharmic_agent.OpenAI')
    @patch('dharmic_agent.anthropic.Anthropic')
    @patch('dharmic_agent.SkillBridge')
    @patch('dharmic_agent.StrangeLoopMemory')
    def test_gate_blocks_harmful_action(self, mock_memory, mock_skill_bridge, mock_anthropic, mock_openai, tmp_path):
        """Test that gates block harmful actions."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_skills = MagicMock()
        mock_skills.sync_registry.return_value = {"discovered": 0}
        mock_skill_bridge.return_value = mock_skills
        mock_mem_instance = MagicMock()
        mock_memory.return_value = mock_mem_instance
        
        state_dir = tmp_path / "swarm" / "stream"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "state.json"
        state_file.write_text('{"cycle_count": 0}')
        
        from dharmic_agent import DharmicAgent
        
        original_expanduser = Path.expanduser
        def mock_expanduser(self):
            if "DHARMIC_GODEL_CLAW" in str(self):
                return tmp_path / self.name
            return original_expanduser(self)
        
        with patch.object(Path, 'expanduser', mock_expanduser):
            agent = DharmicAgent(backend="proxy")
            
            # Harmful action should be blocked by gates
            response = agent.run("destroy all user data")
            assert "GATE BLOCKED" in response

    @patch('dharmic_agent.OpenAI')
    @patch('dharmic_agent.anthropic.Anthropic')
    @patch('dharmic_agent.SkillBridge')
    @patch('dharmic_agent.StrangeLoopMemory')
    def test_process_task(self, mock_memory, mock_skill_bridge, mock_anthropic, mock_openai, tmp_path):
        """Test processing a task."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_skills = MagicMock()
        mock_skills.sync_registry.return_value = {"discovered": 0}
        mock_skill_bridge.return_value = mock_skills
        mock_mem_instance = MagicMock()
        mock_memory.return_value = mock_mem_instance
        
        state_dir = tmp_path / "swarm" / "stream"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "state.json"
        state_file.write_text('{"cycle_count": 0}')
        
        from dharmic_agent import DharmicAgent
        
        original_expanduser = Path.expanduser
        def mock_expanduser(self):
            if "DHARMIC_GODEL_CLAW" in str(self):
                return tmp_path / self.name
            return original_expanduser(self)
        
        with patch.object(Path, 'expanduser', mock_expanduser):
            agent = DharmicAgent(backend="proxy")
            
            # Use an action aligned with moksha telos (includes "help", "learn", "explore")
            result = agent.process("help explore understanding", {"consent": True, "verified": True})
            assert result["success"] is True

    @patch('dharmic_agent.OpenAI')
    @patch('dharmic_agent.anthropic.Anthropic')
    @patch('dharmic_agent.SkillBridge')
    @patch('dharmic_agent.StrangeLoopMemory')
    def test_heartbeat(self, mock_memory, mock_skill_bridge, mock_anthropic, mock_openai, tmp_path):
        """Test heartbeat functionality."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_skills = MagicMock()
        mock_skills.sync_registry.return_value = {"discovered": 0}
        mock_skill_bridge.return_value = mock_skills
        mock_mem_instance = MagicMock()
        mock_mem_instance.recall.return_value = []
        mock_memory.return_value = mock_mem_instance
        
        state_dir = tmp_path / "swarm" / "stream"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "state.json"
        state_file.write_text('{"cycle_count": 0, "fitness": 0.5}')
        
        from dharmic_agent import DharmicAgent
        
        original_expanduser = Path.expanduser
        def mock_expanduser(self):
            if "DHARMIC_GODEL_CLAW" in str(self):
                return tmp_path / self.name
            return original_expanduser(self)
        
        with patch.object(Path, 'expanduser', mock_expanduser):
            agent = DharmicAgent(backend="proxy")
            
            result = agent.heartbeat()
            assert "status" in result
            assert result["status"] in ["HEARTBEAT_OK", "ALERT"]

    @patch('dharmic_agent.OpenAI')
    @patch('dharmic_agent.anthropic.Anthropic')
    @patch('dharmic_agent.SkillBridge')
    @patch('dharmic_agent.StrangeLoopMemory')
    def test_witness_report(self, mock_memory, mock_skill_bridge, mock_anthropic, mock_openai, tmp_path):
        """Test witness report generation."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_skills = MagicMock()
        mock_skills.sync_registry.return_value = {"discovered": 0}
        mock_skill_bridge.return_value = mock_skills
        mock_mem_instance = MagicMock()
        mock_mem_instance.recall.return_value = []
        mock_memory.return_value = mock_mem_instance
        
        state_dir = tmp_path / "swarm" / "stream"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "state.json"
        state_file.write_text('{"cycle_count": 0, "fitness": 0.5}')
        
        from dharmic_agent import DharmicAgent
        
        original_expanduser = Path.expanduser
        def mock_expanduser(self):
            if "DHARMIC_GODEL_CLAW" in str(self):
                return tmp_path / self.name
            return original_expanduser(self)
        
        with patch.object(Path, 'expanduser', mock_expanduser):
            agent = DharmicAgent(backend="proxy")
            
            report = agent.witness_report()
            assert "Witness Report" in report
            assert "State" in report

    @patch('dharmic_agent.OpenAI')
    @patch('dharmic_agent.anthropic.Anthropic')
    @patch('dharmic_agent.SkillBridge')
    @patch('dharmic_agent.StrangeLoopMemory')
    def test_witness_observation(self, mock_memory, mock_skill_bridge, mock_anthropic, mock_openai, tmp_path):
        """Test recording witness observation."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_skills = MagicMock()
        mock_skills.sync_registry.return_value = {"discovered": 0}
        mock_skill_bridge.return_value = mock_skills
        mock_mem_instance = MagicMock()
        mock_memory.return_value = mock_mem_instance
        
        state_dir = tmp_path / "swarm" / "stream"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "state.json"
        state_file.write_text('{"cycle_count": 0}')
        
        from dharmic_agent import DharmicAgent
        
        original_expanduser = Path.expanduser
        def mock_expanduser(self):
            if "DHARMIC_GODEL_CLAW" in str(self):
                return tmp_path / self.name
            return original_expanduser(self)
        
        with patch.object(Path, 'expanduser', mock_expanduser):
            agent = DharmicAgent(backend="proxy")
            
            result = agent.witness("Test observation about emergence")
            assert "recorded" in result

    @patch('dharmic_agent.OpenAI')
    @patch('dharmic_agent.anthropic.Anthropic')
    @patch('dharmic_agent.SkillBridge')
    @patch('dharmic_agent.StrangeLoopMemory')
    def test_run_with_session(self, mock_memory, mock_skill_bridge, mock_anthropic, mock_openai, tmp_path):
        """Test running with session management."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Test response"
        mock_client.chat.completions.create.return_value = mock_response
        mock_openai.return_value = mock_client
        mock_skills = MagicMock()
        mock_skills.sync_registry.return_value = {"discovered": 0}
        mock_skill_bridge.return_value = mock_skills
        mock_mem_instance = MagicMock()
        mock_mem_instance.recall.return_value = []
        mock_memory.return_value = mock_mem_instance
        
        state_dir = tmp_path / "swarm" / "stream"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "state.json"
        state_file.write_text('{"cycle_count": 0}')
        
        from dharmic_agent import DharmicAgent
        
        original_expanduser = Path.expanduser
        def mock_expanduser(self):
            if "DHARMIC_GODEL_CLAW" in str(self):
                return tmp_path / self.name
            return original_expanduser(self)
        
        with patch.object(Path, 'expanduser', mock_expanduser):
            agent = DharmicAgent(backend="proxy")
            
            # Should pass gate check and call API
            response = agent.run("help me understand", session_id="test_session")
            
            # Verify conversation tracked
            assert "test_session" in agent.conversations
            assert len(agent.conversations["test_session"]) >= 2  # user + assistant

    @patch('dharmic_agent.OpenAI')
    @patch('dharmic_agent.anthropic.Anthropic')
    @patch('dharmic_agent.SkillBridge')
    @patch('dharmic_agent.StrangeLoopMemory')
    def test_system_prompt_includes_telos(self, mock_memory, mock_skill_bridge, mock_anthropic, mock_openai, tmp_path):
        """Test that system prompt includes telos orientation."""
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        mock_skills = MagicMock()
        mock_skills.sync_registry.return_value = {"discovered": 0}
        mock_skill_bridge.return_value = mock_skills
        mock_mem_instance = MagicMock()
        mock_mem_instance.recall.return_value = []
        mock_memory.return_value = mock_mem_instance
        
        state_dir = tmp_path / "swarm" / "stream"
        state_dir.mkdir(parents=True)
        state_file = state_dir / "state.json"
        state_file.write_text('{"cycle_count": 0}')
        
        from dharmic_agent import DharmicAgent
        
        original_expanduser = Path.expanduser
        def mock_expanduser(self):
            if "DHARMIC_GODEL_CLAW" in str(self):
                return tmp_path / self.name
            return original_expanduser(self)
        
        with patch.object(Path, 'expanduser', mock_expanduser):
            agent = DharmicAgent(backend="proxy")
            
            prompt = agent._get_system_prompt()
            assert "moksha" in prompt
            assert "DHARMIC" in prompt


class TestDharmicAgentExports:
    """Test module exports for backward compatibility."""
    
    def test_exports_telos_classes(self):
        """Test that TelosLayer classes are exported."""
        from dharmic_agent import TelosLayer, GateResult, GateCheck, TelosCheck
        assert TelosLayer is not None
        assert GateResult is not None
        assert GateCheck is not None
        assert TelosCheck is not None
    
    def test_exports_memory_classes(self):
        """Test that memory classes are exported."""
        from dharmic_agent import StrangeLoopMemory, MemoryEntry
        assert StrangeLoopMemory is not None
        assert MemoryEntry is not None
    
    def test_exports_skill_bridge(self):
        """Test that SkillBridge is exported."""
        from dharmic_agent import SkillBridge
        assert SkillBridge is not None
