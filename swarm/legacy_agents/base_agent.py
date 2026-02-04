from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
import logging
from datetime import datetime
import json

logger = logging.getLogger(__name__)


@dataclass
class AgentResponse:
    """Standard response structure for agent operations."""
    success: bool
    data: Dict[str, Any] = field(default_factory=dict)
    veto: bool = False
    veto_reason: Optional[str] = None
    error: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "success": self.success,
            "data": self.data,
            "veto": self.veto,
            "veto_reason": self.veto_reason,
            "error": self.error
        }


class BaseAgent(ABC):
    """Base class for all agents in the DHARMIC GODEL CLAW swarm."""
    
    def __init__(self, agent_id: str, config: Dict[str, Any]):
        """Initialize base agent.
        
        Args:
            agent_id: Unique identifier for this agent
            config: Configuration dictionary
        """
        self.agent_id = agent_id
        self.config = config
        self.checkpoints: List[Dict[str, Any]] = []
        self.current_state: Dict[str, Any] = {}
        
    @abstractmethod
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process input and return output.
        
        Args:
            input_data: Input data to process
            
        Returns:
            Processed output data
        """
        pass
    
    def dharmic_reflection(self, action: str, outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Perform dharmic reflection on an action and its outcome.
        
        Args:
            action: Description of the action taken
            outcome: Results and consequences of the action
            
        Returns:
            Reflection analysis with insights and adjustments
        """
        try:
            reflection = {
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": self.agent_id,
                "action": action,
                "outcome": outcome,
                "analysis": self._analyze_dharmic_alignment(action, outcome),
                "adjustments": self._generate_adjustments(action, outcome)
            }
            
            self._save_checkpoint("dharmic_reflection", reflection)
            logger.info(f"Agent {self.agent_id} completed dharmic reflection on: {action}")
            
            return reflection
            
        except Exception as e:
            logger.error(f"Error in dharmic reflection for agent {self.agent_id}: {e}")
            return {
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat(),
                "agent_id": self.agent_id
            }
    
    def _analyze_dharmic_alignment(self, action: str, outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Analyze how well an action aligns with dharmic principles.
        
        Args:
            action: Action taken
            outcome: Outcome of the action
            
        Returns:
            Analysis of dharmic alignment
        """
        principles = ["ahimsa", "truthfulness", "non_attachment", "service"]
        alignment_scores = {}
        
        for principle in principles:
            alignment_scores[principle] = self._score_principle_alignment(
                principle, action, outcome
            )
        
        return {
            "principle_scores": alignment_scores,
            "overall_alignment": sum(alignment_scores.values()) / len(alignment_scores),
            "recommendations": self._generate_dharmic_recommendations(alignment_scores)
        }
    
    def _score_principle_alignment(self, principle: str, action: str, outcome: Dict[str, Any]) -> float:
        """Score alignment with a specific dharmic principle.
        
        Args:
            principle: Dharmic principle to evaluate
            action: Action taken
            outcome: Outcome of the action
            
        Returns:
            Alignment score between 0.0 and 1.0
        """
        # Base implementation - can be overridden by specific agents
        base_score = 0.7
        
        # Adjust based on outcome success
        if outcome.get("success", False):
            base_score += 0.1
        
        # Adjust based on harm/benefit indicators
        if outcome.get("harm_indicators", []):
            base_score -= 0.2
        
        if outcome.get("benefit_indicators", []):
            base_score += 0.1
            
        return max(0.0, min(1.0, base_score))
    
    def _generate_dharmic_recommendations(self, alignment_scores: Dict[str, float]) -> List[str]:
        """Generate recommendations based on dharmic alignment scores.
        
        Args:
            alignment_scores: Scores for each dharmic principle
            
        Returns:
            List of recommendations for improvement
        """
        recommendations = []
        
        for principle, score in alignment_scores.items():
            if score < 0.6:
                recommendations.append(f"Improve alignment with {principle}")
            elif score > 0.9:
                recommendations.append(f"Maintain excellent {principle} practices")
                
        if not recommendations:
            recommendations.append("Continue current dharmic practices")
            
        return recommendations
    
    def _generate_adjustments(self, action: str, outcome: Dict[str, Any]) -> Dict[str, Any]:
        """Generate behavioral adjustments based on reflection.
        
        Args:
            action: Action that was taken
            outcome: Results of the action
            
        Returns:
            Suggested adjustments for future actions
        """
        adjustments = {
            "behavioral_changes": [],
            "parameter_updates": {},
            "process_improvements": []
        }
        
        # Add adjustments based on outcome analysis
        if not outcome.get("success", True):
            adjustments["behavioral_changes"].append("Increase validation before action")
            
        if outcome.get("efficiency", 1.0) < 0.8:
            adjustments["process_improvements"].append("Optimize processing pipeline")
            
        return adjustments
    
    def _save_checkpoint(self, checkpoint_type: str, data: Dict[str, Any]) -> None:
        """Save a checkpoint of agent state.
        
        Args:
            checkpoint_type: Type of checkpoint being saved
            data: Data to save in checkpoint
        """
        checkpoint = {
            "timestamp": datetime.utcnow().isoformat(),
            "agent_id": self.agent_id,
            "type": checkpoint_type,
            "data": data,
            "state_snapshot": self.current_state.copy()
        }
        
        self.checkpoints.append(checkpoint)
        
        # Keep only last 10 checkpoints to manage memory
        if len(self.checkpoints) > 10:
            self.checkpoints = self.checkpoints[-10:]
    
    def get_checkpoints(self, checkpoint_type: Optional[str] = None) -> List[Dict[str, Any]]:
        """Retrieve checkpoints, optionally filtered by type.
        
        Args:
            checkpoint_type: Optional type filter
            
        Returns:
            List of matching checkpoints
        """
        if checkpoint_type is None:
            return self.checkpoints.copy()
        
        return [cp for cp in self.checkpoints if cp.get("type") == checkpoint_type]
    
    def restore_checkpoint(self, checkpoint_index: int) -> bool:
        """Restore agent state from a checkpoint.
        
        Args:
            checkpoint_index: Index of checkpoint to restore
            
        Returns:
            True if restoration successful, False otherwise
        """
        try:
            if 0 <= checkpoint_index < len(self.checkpoints):
                checkpoint = self.checkpoints[checkpoint_index]
                self.current_state = checkpoint["data"]["state_snapshot"].copy()
                logger.info(f"Agent {self.agent_id} restored from checkpoint {checkpoint_index}")
                return True
            return False
            
        except Exception as e:
            logger.error(f"Error restoring checkpoint for agent {self.agent_id}: {e}")
            return False
    
    def update_state(self, state_updates: Dict[str, Any]) -> None:
        """Update agent's current state.
        
        Args:
            state_updates: Dictionary of state updates to apply
        """
        self.current_state.update(state_updates)
        self._save_checkpoint("state_update", {"updates": state_updates})
    
    def get_state(self) -> Dict[str, Any]:
        """Get current agent state.
        
        Returns:
            Current state dictionary
        """
        return self.current_state.copy()