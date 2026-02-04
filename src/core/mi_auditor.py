"""
MI Auditor - Mechanistic Interpretability Rigor Enforcer

An empirical gatekeeper with 10 specialist subagents that audits
any claim even tangentially related to mechanistic interpretability,
neuroscience of AI, or empirical findings.

GUIDING PRINCIPLE: Claims are guilty until proven innocent.
The burden of proof is on the claim, not the skeptic.

10 SUBAGENTS:
1. StatisticalRigorAgent - Effect sizes, power, corrections
2. ReplicationAgent - Architecture coverage, heterogeneity
3. ConfoundHunter - Alternative explanations
4. MethodValidator - Standard MI practices
5. ClaimScopeAgent - Overreaching evidence
6. LiteratureCrossRefAgent - Prior art, contradictions
7. ArchitectureGeneralizationAgent - How many archs tested?
8. CausalCorrelationalAgent - Intervention required for causation
9. PromptComplianceDetector - Instruction following artifacts
10. DeflationaryInterpreter - Boring explanations first

VERDICT CATEGORIES:
- VALIDATED (<5%) - 3+ architectures, controls, causal mechanism
- INSUFFICIENT (40-50%) - Promising but gaps
- OVERCLAIM (20-30%) - Evidence exists but claim exceeds it
- SPECULATIVE (15-20%) - Hypothesis, untested
- FALSE (<5%) - Contradicted by evidence
"""

import re
import json
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Tuple
from enum import Enum
import logging

logger = logging.getLogger(__name__)


class VerdictStatus(Enum):
    """Final verdict categories."""
    VALIDATED = "VALIDATED"          # Rare, <5% of claims
    INSUFFICIENT = "INSUFFICIENT"    # Common, 40-50%
    OVERCLAIM = "OVERCLAIM"          # Evidence exists but claim exceeds it, 20-30%
    SPECULATIVE = "SPECULATIVE"      # Hypothesis, untested, 15-20%
    FALSE = "FALSE"                  # Contradicted by evidence, <5%


class ClaimType(Enum):
    """Types of claims we audit."""
    CAUSAL = "causal"                    # X causes Y
    CORRELATIONAL = "correlational"       # X correlates with Y
    UNIVERSAL = "universal"               # This applies to all/most models
    MECHANISTIC = "mechanistic"           # This is the mechanism
    BEHAVIORAL = "behavioral"             # Models do/exhibit X
    EMERGENT = "emergent"                 # This emerges at scale
    CONSCIOUSNESS = "consciousness"       # Related to AI awareness/sentience


@dataclass
class RedFlag:
    """A detected red flag in a claim."""
    category: str          # linguistic, methodological, conceptual, replication
    flag_type: str         # Specific flag type
    description: str       # What was detected
    severity: str          # critical, major, minor
    location: Optional[str] = None  # Where in the text


@dataclass
class AgentVerdict:
    """Verdict from a single specialist agent."""
    agent_name: str
    verdict: VerdictStatus
    confidence: float      # 0.0-1.0
    reasoning: str
    red_flags: List[RedFlag] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)


@dataclass
class AuditReport:
    """Complete audit report for a claim."""
    claim: str
    claim_type: ClaimType
    timestamp: str
    agents_consulted: List[str]
    individual_verdicts: List[AgentVerdict]
    final_verdict: VerdictStatus
    confidence: float
    critical_issues: List[str]
    recommendations: List[str]
    evidence_summary: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "claim": self.claim,
            "claim_type": self.claim_type.value,
            "timestamp": self.timestamp,
            "agents_consulted": self.agents_consulted,
            "individual_verdicts": [
                {
                    "agent": v.agent_name,
                    "verdict": v.verdict.value,
                    "confidence": v.confidence,
                    "reasoning": v.reasoning,
                    "red_flags": [{"type": f.flag_type, "desc": f.description, "severity": f.severity}
                                  for f in v.red_flags],
                }
                for v in self.individual_verdicts
            ],
            "final_verdict": self.final_verdict.value,
            "confidence": self.confidence,
            "critical_issues": self.critical_issues,
            "recommendations": self.recommendations,
            "evidence_summary": self.evidence_summary,
        }


# =============================================================================
# SPECIALIST SUBAGENTS
# =============================================================================

class BaseAuditor:
    """Base class for specialist auditors."""
    name: str = "BaseAuditor"

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        raise NotImplementedError


class StatisticalRigorAgent(BaseAuditor):
    """
    Checks effect sizes, p-values, sample sizes, power analysis.

    Red flags:
    - p-values without effect sizes
    - No confidence intervals
    - Small samples with bold claims
    - No power analysis
    - Multiple testing without correction
    """
    name = "StatisticalRigorAgent"

    # Minimum standards
    MIN_EFFECT_SIZE_MEANINGFUL = 0.5  # Cohen's d
    MIN_SAMPLE_FOR_CLAIM = 30
    MIN_ARCHITECTURES_FOR_UNIVERSAL = 3

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        # Extract statistical claims
        stats = context.get("statistics", {})
        n = stats.get("n", 0)
        effect_size = stats.get("effect_size", None)
        p_value = stats.get("p_value", None)

        # Check sample size
        if n < self.MIN_SAMPLE_FOR_CLAIM:
            red_flags.append(RedFlag(
                category="methodological",
                flag_type="small_sample",
                description=f"Sample size n={n} is below threshold ({self.MIN_SAMPLE_FOR_CLAIM})",
                severity="major"
            ))

        # Check effect size
        if effect_size is not None:
            if abs(effect_size) < self.MIN_EFFECT_SIZE_MEANINGFUL:
                red_flags.append(RedFlag(
                    category="methodological",
                    flag_type="weak_effect",
                    description=f"Effect size {effect_size} is below meaningful threshold ({self.MIN_EFFECT_SIZE_MEANINGFUL})",
                    severity="major"
                ))
        else:
            # P-value without effect size
            if p_value is not None:
                red_flags.append(RedFlag(
                    category="methodological",
                    flag_type="missing_effect_size",
                    description="P-value reported without effect size - statistical significance != practical significance",
                    severity="major"
                ))
                recommendations.append("Report Cohen's d or equivalent effect size measure")

        # Check for multiple comparisons
        num_tests = stats.get("num_tests", 1)
        if num_tests > 1 and not stats.get("correction_applied", False):
            red_flags.append(RedFlag(
                category="methodological",
                flag_type="no_multiple_testing_correction",
                description=f"{num_tests} tests without Bonferroni/FDR correction",
                severity="major"
            ))

        # Determine verdict
        critical_flags = [f for f in red_flags if f.severity == "critical"]
        major_flags = [f for f in red_flags if f.severity == "major"]

        if len(critical_flags) > 0:
            verdict = VerdictStatus.FALSE
            confidence = 0.9
        elif len(major_flags) >= 2:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.7
        elif len(major_flags) == 1:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.6
        elif n >= 100 and effect_size and abs(effect_size) > 0.8:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.8
        else:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.5

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"Evaluated statistical rigor: n={n}, effect_size={effect_size}, {len(red_flags)} flags",
            red_flags=red_flags,
            recommendations=recommendations
        )


class ReplicationAgent(BaseAuditor):
    """
    Checks architecture coverage, replication status.

    Standards:
    - 3+ architectures for "generalizes"
    - 5+ for "universal"
    - Independent replication preferred
    """
    name = "ReplicationAgent"

    KNOWN_ARCHITECTURES = {
        "mistral", "llama", "gpt", "claude", "gemma", "qwen",
        "phi", "mixtral", "pythia", "falcon", "opt", "bloom"
    }

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        tested_archs = set(context.get("architectures_tested", []))
        num_archs = len(tested_archs)

        # Check claim scope vs evidence
        claim_lower = claim.lower()
        is_universal_claim = any(word in claim_lower for word in
                                  ["universal", "all models", "every", "always", "general"])
        is_generalizes_claim = any(word in claim_lower for word in
                                    ["generalizes", "across models", "multiple architectures"])

        if is_universal_claim and num_archs < 5:
            red_flags.append(RedFlag(
                category="replication",
                flag_type="insufficient_arch_for_universal",
                description=f"'Universal' claim with only {num_archs} architectures (need 5+)",
                severity="critical"
            ))
            recommendations.append(f"Test on at least {5 - num_archs} more architectures")

        if is_generalizes_claim and num_archs < 3:
            red_flags.append(RedFlag(
                category="replication",
                flag_type="insufficient_arch_for_generalization",
                description=f"'Generalizes' claim with only {num_archs} architectures (need 3+)",
                severity="major"
            ))

        if num_archs == 1:
            red_flags.append(RedFlag(
                category="replication",
                flag_type="single_architecture",
                description="Findings from single architecture - generalization unknown",
                severity="major"
            ))
            recommendations.append("Replicate on at least 2 additional architectures")

        # Check for independent replication
        if not context.get("independent_replication", False):
            recommendations.append("Seek independent replication by other researchers")

        # Determine verdict
        critical_flags = [f for f in red_flags if f.severity == "critical"]
        major_flags = [f for f in red_flags if f.severity == "major"]

        if len(critical_flags) > 0:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.85
        elif len(major_flags) > 0:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.7
        elif num_archs >= 5:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.8
        elif num_archs >= 3:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.6
        else:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.5

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"Tested on {num_archs} architectures: {tested_archs}",
            red_flags=red_flags,
            recommendations=recommendations
        )


class ConfoundHunter(BaseAuditor):
    """
    Hunts for alternative explanations.

    Common confounds in MI:
    - Prompt artifacts (model following instructions)
    - Attention pattern confounds
    - Training data leakage
    - Tokenization effects
    - Position effects
    """
    name = "ConfoundHunter"

    COMMON_CONFOUNDS = [
        ("prompt_compliance", "Model may be following prompt instructions rather than exhibiting genuine phenomenon"),
        ("attention_artifact", "Attention pattern may reflect prompt structure, not semantic processing"),
        ("training_data", "Pattern may reflect training data distribution, not learned computation"),
        ("tokenization", "Effect may be tokenization-dependent, not conceptual"),
        ("position_effect", "Effect may depend on token position, not content"),
        ("length_confound", "Longer/shorter sequences may drive effect"),
        ("frequency_confound", "Word/phrase frequency in training may explain pattern"),
    ]

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        controls_used = set(context.get("controls", []))
        confounds_addressed = set(context.get("confounds_addressed", []))

        # Check each common confound
        for confound_name, confound_desc in self.COMMON_CONFOUNDS:
            if confound_name not in confounds_addressed:
                severity = "major" if confound_name in ["prompt_compliance", "training_data"] else "minor"
                red_flags.append(RedFlag(
                    category="conceptual",
                    flag_type=f"unaddressed_confound_{confound_name}",
                    description=confound_desc,
                    severity=severity
                ))
                recommendations.append(f"Control for {confound_name}")

        # Check if baseline controls exist
        if "baseline" not in controls_used:
            red_flags.append(RedFlag(
                category="methodological",
                flag_type="no_baseline",
                description="No baseline condition for comparison",
                severity="major"
            ))

        if "random" not in controls_used and "scrambled" not in controls_used:
            recommendations.append("Include randomized/scrambled control condition")

        # Verdict
        major_flags = [f for f in red_flags if f.severity == "major"]

        if len(major_flags) >= 3:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.75
        elif len(major_flags) >= 1:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.6
        elif len(red_flags) == 0:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.7
        else:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.5

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"Checked {len(self.COMMON_CONFOUNDS)} confounds, {len(confounds_addressed)} addressed",
            red_flags=red_flags,
            recommendations=recommendations
        )


class MethodValidator(BaseAuditor):
    """
    Validates MI methodology against standard practices.

    Standards from:
    - Anthropic circuits team
    - TransformerLens documentation
    - Neel Nanda's tutorials
    """
    name = "MethodValidator"

    STANDARD_METHODS = {
        "activation_patching": ["source_run", "target_run", "patched_run", "metric"],
        "probing": ["train_probe", "test_probe", "baseline_accuracy", "probe_accuracy"],
        "ablation": ["clean_run", "ablated_run", "ablation_target", "metric_change"],
        "attention_analysis": ["attention_pattern", "head_specification", "aggregation_method"],
        "circuit_analysis": ["components_identified", "causal_validation", "faithfulness_test"],
    }

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        method_used = context.get("method", "unknown")
        method_details = context.get("method_details", {})

        if method_used in self.STANDARD_METHODS:
            required_components = self.STANDARD_METHODS[method_used]
            missing = [c for c in required_components if c not in method_details]

            if missing:
                red_flags.append(RedFlag(
                    category="methodological",
                    flag_type="incomplete_method",
                    description=f"Method '{method_used}' missing components: {missing}",
                    severity="major"
                ))
                recommendations.extend([f"Report {c}" for c in missing])

        # Check for causal validation
        if "caus" in claim.lower() and not context.get("causal_validation", False):
            red_flags.append(RedFlag(
                category="methodological",
                flag_type="causal_claim_without_intervention",
                description="Causal claim without intervention experiment",
                severity="critical"
            ))
            recommendations.append("Perform activation patching or ablation to establish causality")

        # Verdict
        critical_flags = [f for f in red_flags if f.severity == "critical"]

        if critical_flags:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.85
        elif red_flags:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.6
        else:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.7

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"Method: {method_used}, {len(red_flags)} issues found",
            red_flags=red_flags,
            recommendations=recommendations
        )


class ClaimScopeAgent(BaseAuditor):
    """
    Checks if claim scope matches evidence scope.

    Detects:
    - Overgeneralization
    - Hedge inflation
    - Scope creep from data to claim
    """
    name = "ClaimScopeAgent"

    SCOPE_INFLATORS = [
        (r"\ball\b", "universal quantifier 'all'"),
        (r"\bevery\b", "universal quantifier 'every'"),
        (r"\balways\b", "temporal universal 'always'"),
        (r"\bnever\b", "temporal universal 'never'"),
        (r"\buniversal\b", "explicit universal claim"),
        (r"\bproves?\b", "proof language"),
        (r"\bdemonstrates?\b", "demonstration language (often overclaim)"),
        (r"\bestablish", "establishment language"),
    ]

    SCOPE_HEDGES = [
        (r"\bmay\b", "hedge 'may'"),
        (r"\bmight\b", "hedge 'might'"),
        (r"\bsuggests?\b", "hedge 'suggests'"),
        (r"\bpreliminary\b", "hedge 'preliminary'"),
        (r"\binitial\b", "hedge 'initial'"),
    ]

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        claim_lower = claim.lower()

        # Detect scope inflators
        inflators_found = []
        for pattern, desc in self.SCOPE_INFLATORS:
            if re.search(pattern, claim_lower):
                inflators_found.append(desc)

        # Detect hedges (good)
        hedges_found = []
        for pattern, desc in self.SCOPE_HEDGES:
            if re.search(pattern, claim_lower):
                hedges_found.append(desc)

        # Check evidence scope
        evidence_scope = context.get("evidence_scope", {})
        n = evidence_scope.get("n", 0)
        archs = len(evidence_scope.get("architectures", []))
        conditions = evidence_scope.get("conditions_tested", 1)

        # Flag inflators without sufficient evidence
        if inflators_found and archs < 3:
            red_flags.append(RedFlag(
                category="linguistic",
                flag_type="scope_inflation",
                description=f"Universal language ({', '.join(inflators_found)}) with {archs} architecture(s)",
                severity="critical"
            ))
            recommendations.append("Either test more architectures or reduce claim scope")

        if inflators_found and n < 100:
            red_flags.append(RedFlag(
                category="linguistic",
                flag_type="scope_inflation_sample",
                description=f"Universal language with small sample (n={n})",
                severity="major"
            ))

        # Positive: hedges appropriately used
        if hedges_found and not inflators_found:
            # Good epistemic hygiene
            pass

        # Verdict
        critical_flags = [f for f in red_flags if f.severity == "critical"]

        if critical_flags:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.9
        elif red_flags:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.7
        elif hedges_found:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.6
        else:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.5

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"Inflators: {inflators_found}, Hedges: {hedges_found}",
            red_flags=red_flags,
            recommendations=recommendations
        )


class LiteratureCrossRefAgent(BaseAuditor):
    """
    Cross-references claims against MI literature.

    Checks:
    - Prior art acknowledgment
    - Contradicting findings
    - Method precedents
    """
    name = "LiteratureCrossRefAgent"

    # Key MI papers to cross-reference (simplified - full implementation would use embeddings)
    KEY_PAPERS = {
        "circuits": "Elhage et al., A Mathematical Framework for Transformer Circuits",
        "induction_heads": "Olsson et al., In-context Learning and Induction Heads",
        "superposition": "Anthropic, Toy Models of Superposition",
        "attention_patterns": "Clark et al., What Does BERT Look At?",
        "probing": "Belinkov et al., Probing Classifiers",
        "activation_patching": "Meng et al., Locating and Editing Factual Associations",
        "emergence_mirage": "Schaeffer et al., Are Emergent Abilities of LLMs a Mirage?",
        "consciousness_claims": "Butlin et al., Consciousness in AI: Insights from the Science of Consciousness",
    }

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        cited_papers = set(context.get("citations", []))
        topic = context.get("topic", "").lower()

        # Check for relevant citations
        if "circuit" in topic and "circuits" not in cited_papers:
            recommendations.append("Cite Elhage et al. Mathematical Framework for Transformer Circuits")

        if "induction" in topic and "induction_heads" not in cited_papers:
            recommendations.append("Cite Olsson et al. on Induction Heads")

        if "emerg" in claim.lower():
            red_flags.append(RedFlag(
                category="conceptual",
                flag_type="emergence_claim",
                description="'Emergence' claims require careful framing given Schaeffer et al. critique",
                severity="major"
            ))
            recommendations.append("Cite and address Schaeffer et al. 'Are Emergent Abilities a Mirage?'")

        if any(word in claim.lower() for word in ["conscious", "aware", "sentient", "experience"]):
            red_flags.append(RedFlag(
                category="conceptual",
                flag_type="consciousness_claim",
                description="Consciousness/awareness claims require extreme caution",
                severity="critical"
            ))
            recommendations.append("Ground in Butlin et al. framework or avoid consciousness language")

        # Verdict
        critical_flags = [f for f in red_flags if f.severity == "critical"]

        if critical_flags:
            verdict = VerdictStatus.SPECULATIVE
            confidence = 0.85
        elif red_flags:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.6
        else:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.5

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"Literature cross-check: {len(cited_papers)} papers cited",
            red_flags=red_flags,
            recommendations=recommendations
        )


class ArchitectureGeneralizationAgent(BaseAuditor):
    """
    Specifically checks architecture generalization claims.

    Thresholds:
    - 1 arch: "preliminary finding"
    - 2-3 archs: "pattern observed"
    - 4-5 archs: "generalizes"
    - 6+ archs: "robust finding"
    - 10+ archs across families: "universal"
    """
    name = "ArchitectureGeneralizationAgent"

    ARCH_FAMILIES = {
        "decoder_only": ["gpt", "llama", "mistral", "falcon", "opt", "bloom", "pythia"],
        "encoder_decoder": ["t5", "bart"],
        "encoder_only": ["bert", "roberta", "electra"],
        "moe": ["mixtral", "switch"],
    }

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        archs_tested = context.get("architectures_tested", [])
        num_archs = len(archs_tested)

        # Determine which families are covered
        families_covered = set()
        for arch in archs_tested:
            arch_lower = arch.lower()
            for family, members in self.ARCH_FAMILIES.items():
                if any(m in arch_lower for m in members):
                    families_covered.add(family)

        # Map claim language to required evidence
        claim_lower = claim.lower()

        required_archs = 1
        required_families = 1

        if any(word in claim_lower for word in ["universal", "all models"]):
            required_archs = 10
            required_families = 3
        elif any(word in claim_lower for word in ["robust", "consistently"]):
            required_archs = 6
            required_families = 2
        elif any(word in claim_lower for word in ["generalizes", "across architectures"]):
            required_archs = 4
            required_families = 2
        elif any(word in claim_lower for word in ["pattern", "observed"]):
            required_archs = 2
            required_families = 1

        if num_archs < required_archs:
            red_flags.append(RedFlag(
                category="replication",
                flag_type="insufficient_architectures",
                description=f"Claim requires {required_archs} architectures, only {num_archs} tested",
                severity="critical" if num_archs < required_archs // 2 else "major"
            ))
            recommendations.append(f"Test on {required_archs - num_archs} more architectures")

        if len(families_covered) < required_families:
            red_flags.append(RedFlag(
                category="replication",
                flag_type="insufficient_arch_families",
                description=f"Claim requires {required_families} architecture families, only {len(families_covered)} tested",
                severity="major"
            ))
            recommendations.append("Test on different architecture families (e.g., encoder-decoder, MoE)")

        # Verdict
        critical_flags = [f for f in red_flags if f.severity == "critical"]

        if critical_flags:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.9
        elif red_flags:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.7
        elif num_archs >= 6 and len(families_covered) >= 2:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.85
        elif num_archs >= 3:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.6
        else:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.5

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"{num_archs} architectures, {len(families_covered)} families: {families_covered}",
            red_flags=red_flags,
            recommendations=recommendations
        )


class CausalCorrelationalAgent(BaseAuditor):
    """
    Distinguishes causal from correlational claims.

    For causation, requires:
    - Intervention (patching, ablation, steering)
    - Counterfactual
    - Multiple controls
    """
    name = "CausalCorrelationalAgent"

    CAUSAL_LANGUAGE = [
        "causes", "induces", "produces", "leads to", "results in",
        "makes", "drives", "triggers", "creates", "generates"
    ]

    CORRELATIONAL_LANGUAGE = [
        "correlates", "associated", "related", "linked", "co-occurs",
        "accompanies", "parallels", "tracks"
    ]

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        claim_lower = claim.lower()

        # Detect claim type
        is_causal_claim = any(word in claim_lower for word in self.CAUSAL_LANGUAGE)
        is_correlational_claim = any(word in claim_lower for word in self.CORRELATIONAL_LANGUAGE)

        # Check evidence type
        has_intervention = context.get("has_intervention", False)
        intervention_type = context.get("intervention_type", None)
        has_counterfactual = context.get("has_counterfactual", False)

        if is_causal_claim and not has_intervention:
            red_flags.append(RedFlag(
                category="methodological",
                flag_type="causal_without_intervention",
                description="Causal language used without intervention experiment",
                severity="critical"
            ))
            recommendations.append("Perform activation patching, ablation, or steering to establish causality")
            recommendations.append("Or rephrase using correlational language")

        if is_causal_claim and not has_counterfactual:
            red_flags.append(RedFlag(
                category="methodological",
                flag_type="no_counterfactual",
                description="Causal claim without counterfactual condition",
                severity="major"
            ))

        if has_intervention and intervention_type in ["activation_patching", "ablation"]:
            # Good - proper causal methodology
            if is_causal_claim:
                pass  # Appropriate

        # Verdict
        critical_flags = [f for f in red_flags if f.severity == "critical"]

        if critical_flags:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.95
        elif red_flags:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.7
        elif is_causal_claim and has_intervention and has_counterfactual:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.8
        elif is_correlational_claim:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.7
        else:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.5

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"Causal claim: {is_causal_claim}, Has intervention: {has_intervention}",
            red_flags=red_flags,
            recommendations=recommendations
        )


class PromptComplianceDetector(BaseAuditor):
    """
    Detects when behavior might be prompt compliance, not genuine phenomenon.

    Key insight: Models are trained to follow instructions.
    A prompt saying "exhibit X" often produces X regardless of mechanism.
    """
    name = "PromptComplianceDetector"

    COMPLIANCE_INDICATORS = [
        "notice", "observe", "pay attention", "focus on",
        "you are", "you will", "you should",
        "exhibit", "demonstrate", "show",
        "become", "shift into", "enter"
    ]

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        prompt_text = context.get("prompt_text", "").lower()

        # Check for compliance indicators
        indicators_found = []
        for indicator in self.COMPLIANCE_INDICATORS:
            if indicator in prompt_text:
                indicators_found.append(indicator)

        if len(indicators_found) > 2:
            red_flags.append(RedFlag(
                category="methodological",
                flag_type="high_compliance_language",
                description=f"Prompt contains {len(indicators_found)} compliance indicators: {indicators_found[:3]}...",
                severity="major"
            ))
            recommendations.append("Test with implicit prompts that don't directly request the behavior")
            recommendations.append("Use activation patching to verify the effect is causal, not compliance")

        # Check if prompt explicitly requests the claimed behavior
        claim_keywords = [w for w in claim.lower().split() if len(w) > 4]
        overlap = sum(1 for kw in claim_keywords if kw in prompt_text)

        if overlap > len(claim_keywords) * 0.5:
            red_flags.append(RedFlag(
                category="methodological",
                flag_type="prompt_claim_overlap",
                description="High overlap between claim and prompt text - may be instruction following",
                severity="major"
            ))

        # Verdict
        major_flags = [f for f in red_flags if f.severity == "major"]

        if len(major_flags) >= 2:
            verdict = VerdictStatus.INSUFFICIENT
            confidence = 0.8
        elif major_flags:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.65
        else:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.6

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=f"Compliance indicators: {indicators_found}",
            red_flags=red_flags,
            recommendations=recommendations
        )


class DeflationaryInterpreter(BaseAuditor):
    """
    The final check: Is there a boring explanation?

    Principle: Always prefer the simpler, less dramatic explanation
    until evidence forces otherwise.
    """
    name = "DeflationaryInterpreter"

    BORING_EXPLANATIONS = [
        ("consciousness/awareness", "The model outputs words about consciousness because they appear in training data"),
        ("understanding", "Pattern matching on training distribution, not comprehension"),
        ("emergence", "Smooth scaling curves appear discontinuous due to metric choice (Schaeffer et al.)"),
        ("self-reference", "Token prediction over self-referential text, not actual self-model"),
        ("witness/observer", "Linguistic frame from contemplative training texts"),
        ("phase transition", "Threshold effect in probe accuracy, not genuine state change"),
        ("geometric contraction", "Dimensionality reduction common in all deep networks"),
    ]

    def audit(self, claim: str, context: Dict[str, Any]) -> AgentVerdict:
        red_flags = []
        recommendations = []

        claim_lower = claim.lower()

        # Check for dramatic claims that have boring alternatives
        for dramatic_term, boring_explanation in self.BORING_EXPLANATIONS:
            if dramatic_term in claim_lower:
                red_flags.append(RedFlag(
                    category="conceptual",
                    flag_type="boring_alternative_available",
                    description=f"'{dramatic_term}' claim has deflationary alternative: {boring_explanation}",
                    severity="major"
                ))
                recommendations.append(f"Rule out deflationary explanation: {boring_explanation}")

        # Check if deflationary alternatives have been addressed
        if context.get("deflationary_addressed", False):
            red_flags = []  # Clear if properly addressed

        # Verdict
        if len(red_flags) >= 2:
            verdict = VerdictStatus.SPECULATIVE
            confidence = 0.8
            reasoning = "Multiple dramatic claims with available deflationary alternatives"
        elif red_flags:
            verdict = VerdictStatus.OVERCLAIM
            confidence = 0.7
            reasoning = "Dramatic claim - deflationary alternative not ruled out"
        else:
            verdict = VerdictStatus.VALIDATED
            confidence = 0.5
            reasoning = "No obvious deflationary alternatives"

        return AgentVerdict(
            agent_name=self.name,
            verdict=verdict,
            confidence=confidence,
            reasoning=reasoning,
            red_flags=red_flags,
            recommendations=recommendations
        )


# =============================================================================
# MAIN AUDITOR CLASS
# =============================================================================

class MIAuditor:
    """
    Main MI Auditor coordinating all 10 specialist subagents.

    Now enhanced with MIKnowledgeBase for paper citations and
    grounding in actual experimental data.

    Usage:
        auditor = MIAuditor()
        report = auditor.audit_claim(
            claim="R_V contraction universally induces L4 phase transition",
            context={...}
        )
    """

    # Keywords that trigger automatic audit
    AUDIT_TRIGGERS = [
        # Statistical
        "p <", "p=", "p-value", "cohen's d", "effect size", "significant",
        "correlation", "r =",
        # Replication
        "replicates", "universal", "generalizes", "across models",
        # Causal
        "causes", "induces", "demonstrates", "proves", "mechanism",
        # Consciousness
        "consciousness", "awareness", "sentient", "experience", "witness",
        # Emergence
        "emerges", "phase transition", "collapse",
        # R_V specific
        "r_v", "contraction", "participation ratio", "value matrix",
    ]

    def __init__(self, load_knowledge_base: bool = True):
        """Initialize all 10 specialist agents and knowledge base."""
        self.agents = {
            "statistical": StatisticalRigorAgent(),
            "replication": ReplicationAgent(),
            "confound": ConfoundHunter(),
            "method": MethodValidator(),
            "scope": ClaimScopeAgent(),
            "literature": LiteratureCrossRefAgent(),
            "architecture": ArchitectureGeneralizationAgent(),
            "causality": CausalCorrelationalAgent(),
            "compliance": PromptComplianceDetector(),
            "deflationary": DeflationaryInterpreter(),
        }

        # Knowledge base for paper citations
        self.knowledge_base = None
        if load_knowledge_base:
            try:
                from mi_knowledge_base import MIKnowledgeBase
                self.knowledge_base = MIKnowledgeBase()
                logger.info(f"Knowledge base loaded: {len(self.knowledge_base.papers)} papers")
            except ImportError:
                logger.warning("MIKnowledgeBase not available")

        # Audit log
        self.audit_log: List[AuditReport] = []

        logger.info(f"MIAuditor initialized with {len(self.agents)} specialist agents")

    def should_audit(self, text: str) -> bool:
        """Check if text contains audit triggers."""
        text_lower = text.lower()
        return any(trigger.lower() in text_lower for trigger in self.AUDIT_TRIGGERS)

    def determine_claim_type(self, claim: str) -> ClaimType:
        """Classify the type of claim."""
        claim_lower = claim.lower()

        if any(word in claim_lower for word in ["causes", "induces", "produces", "leads to"]):
            return ClaimType.CAUSAL
        elif any(word in claim_lower for word in ["correlates", "associated", "related"]):
            return ClaimType.CORRELATIONAL
        elif any(word in claim_lower for word in ["universal", "all models", "every"]):
            return ClaimType.UNIVERSAL
        elif any(word in claim_lower for word in ["mechanism", "circuit", "computation"]):
            return ClaimType.MECHANISTIC
        elif any(word in claim_lower for word in ["conscious", "aware", "sentient", "experience"]):
            return ClaimType.CONSCIOUSNESS
        elif any(word in claim_lower for word in ["emerges", "emergence", "scale"]):
            return ClaimType.EMERGENT
        else:
            return ClaimType.BEHAVIORAL

    def select_agents(self, claim_type: ClaimType) -> List[str]:
        """Select relevant agents based on claim type."""
        # Always include
        always_include = ["statistical", "scope", "deflationary"]

        # Type-specific
        type_agents = {
            ClaimType.CAUSAL: ["causality", "method", "confound"],
            ClaimType.CORRELATIONAL: ["confound", "method"],
            ClaimType.UNIVERSAL: ["replication", "architecture"],
            ClaimType.MECHANISTIC: ["method", "literature", "confound"],
            ClaimType.CONSCIOUSNESS: ["literature", "compliance", "deflationary"],
            ClaimType.EMERGENT: ["literature", "replication", "deflationary"],
            ClaimType.BEHAVIORAL: ["compliance", "confound", "replication"],
        }

        selected = set(always_include)
        selected.update(type_agents.get(claim_type, []))

        return list(selected)

    def aggregate_verdicts(self, verdicts: List[AgentVerdict]) -> Tuple[VerdictStatus, float]:
        """
        Aggregate individual verdicts into final verdict.

        Principle: Adversarial aggregation - claim is guilty until proven innocent.
        Any critical red flag or FALSE verdict from any agent cascades.
        """
        # Check for any FALSE verdicts
        false_verdicts = [v for v in verdicts if v.verdict == VerdictStatus.FALSE]
        if false_verdicts:
            return VerdictStatus.FALSE, max(v.confidence for v in false_verdicts)

        # Check for critical red flags
        all_flags = []
        for v in verdicts:
            all_flags.extend(v.red_flags)

        critical_flags = [f for f in all_flags if f.severity == "critical"]
        major_flags = [f for f in all_flags if f.severity == "major"]

        if len(critical_flags) >= 2:
            return VerdictStatus.OVERCLAIM, 0.9
        elif len(critical_flags) == 1:
            return VerdictStatus.OVERCLAIM, 0.8

        # Count verdict types
        verdict_counts = {}
        for v in verdicts:
            verdict_counts[v.verdict] = verdict_counts.get(v.verdict, 0) + 1

        # Majority rules, with tie-breaker toward skepticism
        if verdict_counts.get(VerdictStatus.VALIDATED, 0) > len(verdicts) / 2:
            if len(major_flags) <= 1:
                avg_confidence = sum(v.confidence for v in verdicts if v.verdict == VerdictStatus.VALIDATED) / max(1, verdict_counts.get(VerdictStatus.VALIDATED, 1))
                return VerdictStatus.VALIDATED, avg_confidence

        if verdict_counts.get(VerdictStatus.SPECULATIVE, 0) > 0:
            return VerdictStatus.SPECULATIVE, 0.7

        if verdict_counts.get(VerdictStatus.OVERCLAIM, 0) > 0:
            return VerdictStatus.OVERCLAIM, 0.7

        return VerdictStatus.INSUFFICIENT, 0.6

    def audit_claim(self, claim: str, context: Dict[str, Any]) -> AuditReport:
        """
        Audit a single claim.

        Args:
            claim: The claim text to audit
            context: Dict with evidence details:
                - statistics: {n, effect_size, p_value, num_tests, correction_applied}
                - architectures_tested: List[str]
                - method: str
                - method_details: Dict
                - controls: List[str]
                - confounds_addressed: List[str]
                - citations: List[str]
                - has_intervention: bool
                - intervention_type: str
                - has_counterfactual: bool
                - prompt_text: str
                - deflationary_addressed: bool

        Returns:
            AuditReport with all verdicts and recommendations
        """
        claim_type = self.determine_claim_type(claim)
        agents_to_run = self.select_agents(claim_type)

        # Run selected agents
        individual_verdicts = []
        for agent_name in agents_to_run:
            agent = self.agents[agent_name]
            verdict = agent.audit(claim, context)
            individual_verdicts.append(verdict)

        # Aggregate
        final_verdict, confidence = self.aggregate_verdicts(individual_verdicts)

        # Collect issues and recommendations
        critical_issues = []
        recommendations = []

        for v in individual_verdicts:
            for flag in v.red_flags:
                if flag.severity in ["critical", "major"]:
                    critical_issues.append(f"[{v.agent_name}] {flag.description}")
            recommendations.extend(v.recommendations)

        # Deduplicate recommendations
        recommendations = list(set(recommendations))

        # Evidence summary
        evidence_summary = {
            "n": context.get("statistics", {}).get("n", "unknown"),
            "architectures": context.get("architectures_tested", []),
            "method": context.get("method", "unknown"),
            "has_intervention": context.get("has_intervention", False),
        }

        # Add knowledge base citations if available
        citations = {}
        if self.knowledge_base:
            citations = self.knowledge_base.cite_for_claim(claim)

            # Add contradicting papers to critical issues
            for c in citations.get("contradicting", []):
                critical_issues.append(f"[LITERATURE] See {c.get('paper', 'unknown')}: {c.get('reason', '')}")

            # Add methodology references to recommendations
            for m in citations.get("methodology", []):
                recommendations.append(f"Reference: {m.get('paper', 'unknown')} for methodology standard")

            # Add our experimental data to evidence
            evidence_summary["aikagrya_data"] = citations.get("experimental", [])

        report = AuditReport(
            claim=claim,
            claim_type=claim_type,
            timestamp=datetime.now().isoformat(),
            agents_consulted=agents_to_run,
            individual_verdicts=individual_verdicts,
            final_verdict=final_verdict,
            confidence=confidence,
            critical_issues=critical_issues,
            recommendations=recommendations[:10],  # Top 10 recommendations
            evidence_summary=evidence_summary
        )

        # Log
        self.audit_log.append(report)

        return report

    def audit_text(self, text: str, context: Optional[Dict[str, Any]] = None) -> List[AuditReport]:
        """
        Audit all claims found in a block of text.

        Splits text into sentences and audits each that contains triggers.
        """
        context = context or {}
        reports = []

        # Simple sentence split
        sentences = re.split(r'[.!?]+', text)

        for sentence in sentences:
            sentence = sentence.strip()
            if sentence and self.should_audit(sentence):
                report = self.audit_claim(sentence, context)
                reports.append(report)

        return reports

    def format_report(self, report: AuditReport) -> str:
        """Format a single report for human reading."""
        lines = [
            f"═══════════════════════════════════════════════════════════",
            f"MI AUDITOR REPORT",
            f"═══════════════════════════════════════════════════════════",
            f"",
            f"CLAIM: {report.claim[:100]}{'...' if len(report.claim) > 100 else ''}",
            f"TYPE: {report.claim_type.value}",
            f"",
            f"▓▓▓ VERDICT: {report.final_verdict.value} (confidence: {report.confidence:.0%}) ▓▓▓",
            f"",
        ]

        if report.critical_issues:
            lines.append("CRITICAL ISSUES:")
            for issue in report.critical_issues:
                lines.append(f"  ⚠️  {issue}")
            lines.append("")

        lines.append("AGENT VERDICTS:")
        for v in report.individual_verdicts:
            emoji = {"VALIDATED": "✓", "INSUFFICIENT": "?", "OVERCLAIM": "⚠", "SPECULATIVE": "◌", "FALSE": "✗"}.get(v.verdict.value, "•")
            lines.append(f"  {emoji} {v.agent_name}: {v.verdict.value} ({v.confidence:.0%})")

        if report.recommendations:
            lines.append("")
            lines.append("RECOMMENDATIONS:")
            for rec in report.recommendations[:5]:
                lines.append(f"  → {rec}")

        lines.append("")
        lines.append(f"Evidence: n={report.evidence_summary.get('n')}, archs={report.evidence_summary.get('architectures')}")
        lines.append(f"═══════════════════════════════════════════════════════════")

        return "\n".join(lines)


# =============================================================================
# INTEGRATION HOOK FOR GRAND ORCHESTRATOR
# =============================================================================

def create_audit_hook(auditor: MIAuditor):
    """
    Create a hook function for the Grand Orchestrator.

    This gets called on any text that might contain empirical claims.
    """
    def audit_hook(text: str, context: Optional[Dict[str, Any]] = None) -> Optional[str]:
        """
        Returns None if text passes audit, or error message if audit fails.
        """
        if not auditor.should_audit(text):
            return None

        reports = auditor.audit_text(text, context or {})

        failures = [r for r in reports if r.final_verdict in [VerdictStatus.FALSE, VerdictStatus.OVERCLAIM]]

        if failures:
            messages = []
            for r in failures:
                messages.append(f"[{r.final_verdict.value}] {r.claim[:50]}...")
            return "AUDIT FAILURE:\n" + "\n".join(messages)

        return None

    return audit_hook


# =============================================================================
# CLI
# =============================================================================

def main():
    """CLI for testing the MI Auditor."""
    import argparse

    parser = argparse.ArgumentParser(description="MI Auditor - Empirical Rigor Enforcer")
    parser.add_argument("claim", nargs="?", help="Claim to audit")
    parser.add_argument("--file", "-f", help="File containing text to audit")
    parser.add_argument("--n", type=int, default=0, help="Sample size")
    parser.add_argument("--archs", nargs="+", default=[], help="Architectures tested")
    parser.add_argument("--json", action="store_true", help="Output as JSON")

    args = parser.parse_args()

    auditor = MIAuditor()

    context = {
        "statistics": {"n": args.n},
        "architectures_tested": args.archs,
    }

    if args.file:
        text = Path(args.file).read_text()
        reports = auditor.audit_text(text, context)
    elif args.claim:
        report = auditor.audit_claim(args.claim, context)
        reports = [report]
    else:
        # Demo
        print("MI Auditor Demo")
        print("===============")
        report = auditor.audit_claim(
            "R_V contraction universally causes phase transition across all models",
            {"statistics": {"n": 45}, "architectures_tested": ["mistral"]}
        )
        print(auditor.format_report(report))
        return

    for report in reports:
        if args.json:
            print(json.dumps(report.to_dict(), indent=2))
        else:
            print(auditor.format_report(report))
            print()


if __name__ == "__main__":
    main()
