"""Simple, explainable baselines that every advanced policy must beat."""

from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np

from nyc_housing_rl.domain import DecisionAction


class Fifo:
    name = "fifo_routine"

    def act(self, observation: np.ndarray) -> DecisionAction:
        del observation
        return DecisionAction.ROUTINE


class AlwaysExpedite:
    name = "always_expedite"

    def act(self, observation: np.ndarray) -> DecisionAction:
        del observation
        return DecisionAction.EXPEDITED


class NeverInspect:
    name = "never_inspect"

    def act(self, observation: np.ndarray) -> DecisionAction:
        del observation
        return DecisionAction.DEFER


@dataclass(slots=True)
class RandomPolicy:
    seed: int = 0
    name: str = "random"
    _rng: np.random.Generator = field(init=False, repr=False)

    def __post_init__(self) -> None:
        self._rng = np.random.default_rng(self.seed)

    def act(self, observation: np.ndarray) -> DecisionAction:
        del observation
        return DecisionAction(int(self._rng.integers(0, len(DecisionAction))))


@dataclass(frozen=True, slots=True)
class RiskTier:
    """Product-readable triage rule based exclusively on decision-time features."""

    expedite_threshold: float = 0.4
    defer_threshold: float = 0.15
    name: str = "risk_tier"

    def act(self, observation: np.ndarray) -> DecisionAction:
        risk_score = float(observation[0])
        permit_overlap = bool(observation[2])
        if risk_score >= self.expedite_threshold and not permit_overlap:
            return DecisionAction.EXPEDITED
        if risk_score <= self.defer_threshold:
            return DecisionAction.DEFER
        return DecisionAction.ROUTINE
