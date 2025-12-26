"""
Confidence tracking and calibration for metacognition.

This module tracks the system's confidence in its beliefs and conclusions,
and provides mechanisms for calibrating confidence based on outcomes.

Key concepts:
- Calibration: How well confidence matches actual accuracy
- Overconfidence/Underconfidence detection
- Confidence updating based on evidence
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import math
import uuid


@dataclass
class ConfidenceRecord:
    """A record of a confidence judgment and its outcome."""
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    claim: str = ""
    confidence: float = 0.5
    outcome: Optional[bool] = None  # True if correct, False if incorrect, None if unknown
    domain: str = "general"
    timestamp: datetime = field(default_factory=datetime.now)
    metadata: Dict[str, Any] = field(default_factory=dict)


class ConfidenceTracker:
    """
    Tracks confidence judgments and their outcomes for calibration analysis.

    This enables the system to learn about its own reliability in different
    domains and adjust future confidence judgments accordingly.
    """

    def __init__(self):
        self.records: List[ConfidenceRecord] = []
        self.calibration_cache: Dict[str, Dict[str, float]] = {}
        self._domain_adjustments: Dict[str, float] = {}

    def record_judgment(self, claim: str, confidence: float,
                       domain: str = "general",
                       metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Record a confidence judgment.

        Args:
            claim: The claim or proposition
            confidence: Confidence level (0 to 1)
            domain: Domain of the claim for calibration
            metadata: Additional context

        Returns:
            The record ID for later outcome recording
        """
        record = ConfidenceRecord(
            claim=claim,
            confidence=max(0.0, min(1.0, confidence)),
            domain=domain,
            metadata=metadata or {}
        )
        self.records.append(record)
        return record.id

    def record_outcome(self, record_id: str, correct: bool) -> None:
        """Record the outcome of a previous judgment."""
        for record in self.records:
            if record.id == record_id:
                record.outcome = correct
                self._invalidate_calibration_cache(record.domain)
                break

    def get_calibration(self, domain: Optional[str] = None,
                       num_bins: int = 10) -> Dict[str, Any]:
        """
        Compute calibration statistics.

        Calibration measures how well confidence matches actual accuracy.
        Perfect calibration means claims with 80% confidence are correct 80% of time.

        Args:
            domain: Optional domain filter
            num_bins: Number of confidence bins

        Returns:
            Dictionary with calibration statistics
        """
        # Filter records with outcomes
        records = [r for r in self.records if r.outcome is not None]
        if domain:
            records = [r for r in records if r.domain == domain]

        if not records:
            return {
                "calibrated": None,
                "calibration_error": None,
                "num_records": 0,
                "bins": []
            }

        # Bin the records by confidence
        bins = [[] for _ in range(num_bins)]
        for record in records:
            bin_idx = min(int(record.confidence * num_bins), num_bins - 1)
            bins[bin_idx].append(record)

        # Compute calibration for each bin
        bin_results = []
        total_calibration_error = 0.0
        total_weight = 0

        for i, bin_records in enumerate(bins):
            if not bin_records:
                continue

            expected_accuracy = (i + 0.5) / num_bins
            actual_accuracy = sum(1 for r in bin_records if r.outcome) / len(bin_records)
            error = abs(expected_accuracy - actual_accuracy)

            bin_results.append({
                "confidence_range": (i / num_bins, (i + 1) / num_bins),
                "expected_accuracy": expected_accuracy,
                "actual_accuracy": actual_accuracy,
                "count": len(bin_records),
                "calibration_error": error
            })

            total_calibration_error += error * len(bin_records)
            total_weight += len(bin_records)

        overall_calibration_error = (total_calibration_error / total_weight
                                     if total_weight > 0 else None)

        # Determine if well-calibrated (error < 0.1 is good)
        calibrated = overall_calibration_error < 0.1 if overall_calibration_error else None

        return {
            "calibrated": calibrated,
            "calibration_error": overall_calibration_error,
            "num_records": len(records),
            "bins": bin_results
        }

    def get_bias(self, domain: Optional[str] = None) -> Dict[str, Any]:
        """
        Analyze confidence bias (over/under-confidence).

        Returns:
            Dictionary with bias analysis
        """
        records = [r for r in self.records if r.outcome is not None]
        if domain:
            records = [r for r in records if r.domain == domain]

        if not records:
            return {"bias": None, "direction": None, "magnitude": 0}

        avg_confidence = sum(r.confidence for r in records) / len(records)
        accuracy = sum(1 for r in records if r.outcome) / len(records)

        bias = avg_confidence - accuracy

        return {
            "bias": bias,
            "direction": "overconfident" if bias > 0.05 else (
                "underconfident" if bias < -0.05 else "well-calibrated"
            ),
            "magnitude": abs(bias),
            "average_confidence": avg_confidence,
            "actual_accuracy": accuracy
        }

    def suggest_adjustment(self, raw_confidence: float,
                          domain: str = "general") -> float:
        """
        Suggest an adjusted confidence based on past calibration.

        This helps correct for systematic over/under-confidence.
        """
        if domain in self._domain_adjustments:
            adjustment = self._domain_adjustments[domain]
        else:
            bias = self.get_bias(domain)
            if bias["bias"] is not None:
                adjustment = -bias["bias"]
                self._domain_adjustments[domain] = adjustment
            else:
                adjustment = 0.0

        adjusted = raw_confidence + adjustment
        return max(0.0, min(1.0, adjusted))

    def get_domain_reliability(self, domain: str) -> Dict[str, Any]:
        """Get reliability statistics for a specific domain."""
        records = [r for r in self.records
                   if r.domain == domain and r.outcome is not None]

        if not records:
            return {
                "domain": domain,
                "reliable": None,
                "sample_size": 0
            }

        accuracy = sum(1 for r in records if r.outcome) / len(records)
        avg_confidence = sum(r.confidence for r in records) / len(records)

        return {
            "domain": domain,
            "reliable": accuracy >= 0.7,  # Threshold for reliability
            "accuracy": accuracy,
            "average_confidence": avg_confidence,
            "sample_size": len(records)
        }

    def get_uncertain_domains(self) -> List[str]:
        """Identify domains where the system is consistently uncertain."""
        domain_stats = {}
        for record in self.records:
            if record.domain not in domain_stats:
                domain_stats[record.domain] = []
            domain_stats[record.domain].append(record.confidence)

        uncertain = []
        for domain, confidences in domain_stats.items():
            avg = sum(confidences) / len(confidences)
            if avg < 0.5:
                uncertain.append(domain)

        return uncertain

    def _invalidate_calibration_cache(self, domain: str) -> None:
        """Invalidate cached calibration data for a domain."""
        if domain in self.calibration_cache:
            del self.calibration_cache[domain]
        if "general" in self.calibration_cache:
            del self.calibration_cache["general"]

    def summary(self) -> str:
        """Generate a summary of confidence tracking."""
        lines = ["Confidence Tracking Summary:"]

        total_records = len(self.records)
        resolved = len([r for r in self.records if r.outcome is not None])
        lines.append(f"  Total judgments: {total_records} ({resolved} resolved)")

        if resolved > 0:
            calibration = self.get_calibration()
            if calibration["calibration_error"] is not None:
                lines.append(f"  Calibration error: {calibration['calibration_error']:.3f}")

            bias = self.get_bias()
            lines.append(f"  Bias: {bias['direction']} (magnitude: {bias['magnitude']:.3f})")

        # Domain breakdown
        domains = set(r.domain for r in self.records)
        if len(domains) > 1:
            lines.append("  Domains tracked:")
            for domain in domains:
                reliability = self.get_domain_reliability(domain)
                if reliability["sample_size"] > 0:
                    lines.append(
                        f"    {domain}: {reliability['accuracy']:.1%} accuracy "
                        f"({reliability['sample_size']} samples)"
                    )

        return "\n".join(lines)


class BayesianConfidenceUpdater:
    """
    Updates confidence using Bayesian reasoning.

    This provides a principled way to update confidence when new evidence arrives.
    """

    @staticmethod
    def update(prior: float, likelihood_if_true: float,
               likelihood_if_false: float) -> float:
        """
        Update confidence using Bayes' theorem.

        Args:
            prior: Prior confidence P(H)
            likelihood_if_true: P(E|H) - probability of evidence if hypothesis true
            likelihood_if_false: P(E|not H) - probability of evidence if hypothesis false

        Returns:
            Posterior confidence P(H|E)
        """
        # Bayes' theorem: P(H|E) = P(E|H) * P(H) / P(E)
        # where P(E) = P(E|H) * P(H) + P(E|not H) * P(not H)

        p_evidence = (likelihood_if_true * prior +
                     likelihood_if_false * (1 - prior))

        if p_evidence == 0:
            return prior  # No update if evidence impossible

        posterior = (likelihood_if_true * prior) / p_evidence
        return max(0.0, min(1.0, posterior))

    @staticmethod
    def update_from_source(prior: float, source_reliability: float,
                          source_says_true: bool) -> float:
        """
        Update confidence based on what a source claims.

        Args:
            prior: Prior confidence
            source_reliability: How reliable the source is (0 to 1)
            source_says_true: Whether the source claims the proposition is true

        Returns:
            Updated confidence
        """
        if source_says_true:
            likelihood_if_true = source_reliability
            likelihood_if_false = 1 - source_reliability
        else:
            likelihood_if_true = 1 - source_reliability
            likelihood_if_false = source_reliability

        return BayesianConfidenceUpdater.update(
            prior, likelihood_if_true, likelihood_if_false
        )

    @staticmethod
    def combine_independent(confidences: List[float]) -> float:
        """
        Combine independent confidence estimates.

        Uses the independence assumption to combine multiple estimates.
        """
        if not confidences:
            return 0.5

        # Convert to odds and multiply
        odds = [p / (1 - p) if p < 1 else float('inf') for p in confidences]

        # Start with equal prior odds (1:1)
        combined_odds = 1.0
        for o in odds:
            if o == float('inf'):
                return 1.0
            combined_odds *= o

        # Convert back to probability
        return combined_odds / (1 + combined_odds)
