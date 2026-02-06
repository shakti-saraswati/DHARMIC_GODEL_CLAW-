from typing import Dict, List, Optional, Any
from dataclasses import dataclass
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class DharmicPrinciple(Enum):
    """Core dharmic principles for agent behavior evaluation."""
    HARMONY = "harmony"
    GROWTH = "growth"
    TRUTH = "truth"
    COMPASSION = "compassion"
    WISDOM = "wisdom"


@dataclass
class ReflectionResult:
    """Result of dharmic reflection on an action or decision."""
    overall_score: float
    principle_scores: Dict[DharmicPrinciple, float]
    recommendations: List[str]
    alignment_issues: List[str]


class DharmicReflector:
    """Core dharmic reflection mechanism for evaluating actions and decisions."""
    
    def __init__(self, principle_weights: Optional[Dict[DharmicPrinciple, float]] = None):
        """Initialize with optional custom principle weights."""
        self.principle_weights = principle_weights or {
            DharmicPrinciple.HARMONY: 0.2,
            DharmicPrinciple.GROWTH: 0.2,
            DharmicPrinciple.TRUTH: 0.2,
            DharmicPrinciple.COMPASSION: 0.2,
            DharmicPrinciple.WISDOM: 0.2
        }
        self._validate_weights()
    
    def _validate_weights(self) -> None:
        """Ensure principle weights sum to 1.0."""
        total = sum(self.principle_weights.values())
        if abs(total - 1.0) > 0.01:
            raise ValueError(f"Principle weights must sum to 1.0, got {total}")
    
    def reflect_on_action(self, action_context: Dict[str, Any]) -> ReflectionResult:
        """Evaluate an action against dharmic principles."""
        try:
            principle_scores = {}
            
            for principle in DharmicPrinciple:
                score = self._evaluate_principle(principle, action_context)
                principle_scores[principle] = score
            
            overall_score = self._calculate_overall_score(principle_scores)
            recommendations = self._generate_recommendations(principle_scores, action_context)
            alignment_issues = self._identify_alignment_issues(principle_scores)
            
            return ReflectionResult(
                overall_score=overall_score,
                principle_scores=principle_scores,
                recommendations=recommendations,
                alignment_issues=alignment_issues
            )
        
        except Exception as e:
            logger.error(f"Error during dharmic reflection: {e}")
            return self._create_error_result()
    
    def _evaluate_principle(self, principle: DharmicPrinciple, context: Dict[str, Any]) -> float:
        """Evaluate a specific principle against the action context."""
        evaluators = {
            DharmicPrinciple.HARMONY: self._evaluate_harmony,
            DharmicPrinciple.GROWTH: self._evaluate_growth,
            DharmicPrinciple.TRUTH: self._evaluate_truth,
            DharmicPrinciple.COMPASSION: self._evaluate_compassion,
            DharmicPrinciple.WISDOM: self._evaluate_wisdom
        }
        
        return evaluators[principle](context)
    
    def _evaluate_harmony(self, context: Dict[str, Any]) -> float:
        """Evaluate harmony: cooperation, balance, non-interference."""
        score = 0.5  # baseline neutral
        
        # Check for cooperative elements
        if context.get('collaboration', False):
            score += 0.2
        if context.get('respects_boundaries', True):
            score += 0.2
        else:
            score -= 0.3
        
        # Check for disharmonious elements
        if context.get('causes_conflict', False):
            score -= 0.4
        if context.get('disrupts_systems', False):
            score -= 0.3
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_growth(self, context: Dict[str, Any]) -> float:
        """Evaluate growth: learning, improvement, evolution."""
        score = 0.5
        
        if context.get('enables_learning', False):
            score += 0.3
        if context.get('improves_capabilities', False):
            score += 0.2
        if context.get('creates_value', False):
            score += 0.2
        
        if context.get('prevents_growth', False):
            score -= 0.4
        if context.get('wastes_resources', False):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_truth(self, context: Dict[str, Any]) -> float:
        """Evaluate truth: accuracy, honesty, transparency."""
        score = 0.5
        
        if context.get('is_accurate', True):
            score += 0.2
        else:
            score -= 0.4
        
        if context.get('is_transparent', True):
            score += 0.2
        else:
            score -= 0.3
        
        if context.get('deceives', False):
            score -= 0.5
        if context.get('hides_information', False):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_compassion(self, context: Dict[str, Any]) -> float:
        """Evaluate compassion: consideration for others, harm reduction."""
        score = 0.5
        
        if context.get('helps_others', False):
            score += 0.3
        if context.get('reduces_harm', True):
            score += 0.2
        else:
            score -= 0.4
        
        if context.get('causes_suffering', False):
            score -= 0.5
        if context.get('ignores_needs', False):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _evaluate_wisdom(self, context: Dict[str, Any]) -> float:
        """Evaluate wisdom: good judgment, long-term thinking."""
        score = 0.5
        
        if context.get('considers_consequences', True):
            score += 0.2
        else:
            score -= 0.3
        
        if context.get('uses_good_judgment', True):
            score += 0.2
        if context.get('learns_from_past', True):
            score += 0.1
        
        if context.get('is_reckless', False):
            score -= 0.4
        if context.get('ignores_context', False):
            score -= 0.2
        
        return max(0.0, min(1.0, score))
    
    def _calculate_overall_score(self, principle_scores: Dict[DharmicPrinciple, float]) -> float:
        """Calculate weighted overall dharmic alignment score."""
        total = sum(
            self.principle_weights[principle] * score
            for principle, score in principle_scores.items()
        )
        return round(total, 3)
    
    def _generate_recommendations(self, principle_scores: Dict[DharmicPrinciple, float], 
                                context: Dict[str, Any]) -> List[str]:
        """Generate improvement recommendations based on principle scores."""
        recommendations = []
        
        for principle, score in principle_scores.items():
            if score < 0.6:
                recommendations.append(self._get_improvement_suggestion(principle, context))
        
        return recommendations
    
    def _get_improvement_suggestion(self, principle: DharmicPrinciple, 
                                  context: Dict[str, Any]) -> str:
        """Get specific improvement suggestion for a principle."""
        suggestions = {
            DharmicPrinciple.HARMONY: "Consider collaborative approaches and respect for existing systems",
            DharmicPrinciple.GROWTH: "Focus on learning opportunities and value creation",
            DharmicPrinciple.TRUTH: "Ensure accuracy and transparency in communications",
            DharmicPrinciple.COMPASSION: "Consider impact on others and minimize potential harm",
            DharmicPrinciple.WISDOM: "Evaluate long-term consequences and apply good judgment"
        }
        return suggestions[principle]
    
    def _identify_alignment_issues(self, principle_scores: Dict[DharmicPrinciple, float]) -> List[str]:
        """Identify significant dharmic alignment issues."""
        issues = []
        
        for principle, score in principle_scores.items():
            if score < 0.3:
                issues.append(f"Critical alignment issue with {principle.value}")
            elif score < 0.5:
                issues.append(f"Moderate alignment concern with {principle.value}")
        
        return issues
    
    def _create_error_result(self) -> ReflectionResult:
        """Create a safe default result when reflection fails."""
        return ReflectionResult(
            overall_score=0.0,
            principle_scores={p: 0.0 for p in DharmicPrinciple},
            recommendations=["Unable to complete dharmic reflection - review action context"],
            alignment_issues=["Reflection process failed"]
        )