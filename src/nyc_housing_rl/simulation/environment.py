"""Gymnasium-compatible, capacity-constrained complaint triage environment."""

from __future__ import annotations

from collections import Counter, deque
from dataclasses import asdict
from typing import Any

import gymnasium as gym
import numpy as np
from gymnasium import spaces

from nyc_housing_rl.domain import DecisionAction, OutcomeLabel
from nyc_housing_rl.simulation.types import Complaint, SimulationConfig


class InspectionTriageEnv(gym.Env[np.ndarray, int]):
    """A sequential dispatch environment with persistent daily capacity.

    The next arriving complaint receives ``defer``, ``routine``, or ``expedited``.
    Routine work joins the back of the service queue while expedited work joins the
    front. A completed inspection reveals the complaint's latent outcome. This is a
    counterfactual simulator, not a model of the causal effect of inspection.
    """

    metadata: dict[str, list[str]] = {"render_modes": []}  # noqa: RUF012

    def __init__(self, complaints: list[Complaint], config: SimulationConfig) -> None:
        super().__init__()
        if not complaints:
            raise ValueError("At least one complaint is required")
        self.complaints = sorted(complaints, key=lambda item: (item.arrival_day, item.complaint_id))
        self.config = config
        self.action_space = spaces.Discrete(len(DecisionAction))
        self.observation_space = spaces.Box(
            low=np.array([0, 0, 0, 0, 0, 0, 0, 0], dtype=np.float32),
            high=np.array([1, 100, 1, 100, 1, 10_000, 4, 10_000], dtype=np.float32),
            dtype=np.float32,
        )
        self._reset_state()

    def _reset_state(self) -> None:
        self._index = 0
        self._day = self.complaints[0].arrival_day
        self._capacity = self.config.daily_capacity
        self._routine: deque[Complaint] = deque()
        self._expedited: deque[Complaint] = deque()
        self._decisions: list[dict[str, Any]] = []
        self._outcomes: list[dict[str, Any]] = []
        self._deferred: list[Complaint] = []
        self._total_reward = 0.0
        self._queue_depths: list[int] = []

    def reset(
        self, *, seed: int | None = None, options: dict[str, Any] | None = None
    ) -> tuple[np.ndarray, dict[str, Any]]:
        super().reset(seed=seed)
        self._reset_state()
        return self._observation(), self._info()

    def step(self, action: int) -> tuple[np.ndarray, float, bool, bool, dict[str, Any]]:
        if not self.action_space.contains(action):
            raise ValueError(f"Invalid action {action}")
        if self._index >= len(self.complaints):
            raise RuntimeError("Episode is complete; call reset()")

        complaint = self.complaints[self._index]
        reward = self._advance_to(complaint.arrival_day)
        chosen = DecisionAction(action)
        self._decisions.append(
            {
                "complaint_id": complaint.complaint_id,
                "day": self._day,
                "action": chosen.name.lower(),
            }
        )
        if chosen is DecisionAction.DEFER:
            self._deferred.append(complaint)
            reward += (
                self.config.defer_penalty
                if complaint.latent_outcome is OutcomeLabel.ACTIONABLE
                else 0.0
            )
        elif chosen is DecisionAction.EXPEDITED:
            self._expedited.append(complaint)
        else:
            self._routine.append(complaint)

        reward += self._serve_today()
        self._index += 1
        self._total_reward += reward
        self._queue_depths.append(len(self._routine) + len(self._expedited))
        terminated = self._index >= len(self.complaints)
        if terminated:
            reward += self._drain()
            self._total_reward += reward
        return self._observation(), float(reward), terminated, False, self._info()

    def _advance_to(self, target_day: int) -> float:
        reward = 0.0
        while self._day < target_day:
            self._day += 1
            self._capacity = self.config.daily_capacity
            reward += self._serve_today()
            self._queue_depths.append(len(self._routine) + len(self._expedited))
        return reward

    def _serve_today(self) -> float:
        reward = 0.0
        while self._capacity and (self._expedited or self._routine):
            complaint = self._expedited.popleft() if self._expedited else self._routine.popleft()
            self._capacity -= 1
            delay = self._day - complaint.arrival_day
            accessible = bool(self.np_random.random() <= self.config.access_probability)
            observed = complaint.latent_outcome if accessible else OutcomeLabel.INACCESSIBLE
            reward += self.config.inspection_cost + self.config.delay_penalty_per_day * delay
            if observed is OutcomeLabel.ACTIONABLE:
                reward += self.config.actionable_reward
            self._outcomes.append(
                {
                    "complaint_id": complaint.complaint_id,
                    "arrival_day": complaint.arrival_day,
                    "inspection_day": self._day,
                    "delay_days": delay,
                    "outcome": observed.value,
                    "equity_group": complaint.equity_group,
                }
            )
        return reward

    def _drain(self) -> float:
        reward = 0.0
        for _ in range(self.config.max_drain_days):
            if not self._routine and not self._expedited:
                return reward
            self._day += 1
            self._capacity = self.config.daily_capacity
            reward += self._serve_today()
        return reward

    def _observation(self) -> np.ndarray:
        if self._index >= len(self.complaints):
            return np.zeros(8, dtype=np.float32)
        complaint = self.complaints[self._index]
        queue_depth = len(self._routine) + len(self._expedited)
        return np.array(
            [
                complaint.risk_score,
                complaint.prior_complaints,
                float(complaint.permit_overlap),
                max(0, self._day - complaint.arrival_day),
                self._capacity / self.config.daily_capacity,
                queue_depth,
                complaint.borough,
                self._day,
            ],
            dtype=np.float32,
        )

    def _info(self) -> dict[str, Any]:
        counts = Counter(item["outcome"] for item in self._outcomes)
        return {
            "day": self._day,
            "capacity_remaining": self._capacity,
            "queue_depth": len(self._routine) + len(self._expedited),
            "deferred": len(self._deferred),
            "outcomes": dict(counts),
            "total_reward": self._total_reward,
        }

    def result(self) -> dict[str, Any]:
        if self._index < len(self.complaints):
            raise RuntimeError("Cannot create results before episode completion")
        by_group: dict[str, dict[str, float]] = {}
        groups = {item.equity_group for item in self.complaints}
        for group in groups:
            arrivals = [item for item in self.complaints if item.equity_group == group]
            inspections = [item for item in self._outcomes if item["equity_group"] == group]
            by_group[group] = {
                "arrivals": len(arrivals),
                "inspected": len(inspections),
                "service_rate": len(inspections) / len(arrivals) if arrivals else 0.0,
                "mean_delay_days": float(np.mean([item["delay_days"] for item in inspections]))
                if inspections
                else 0.0,
            }
        return {
            "config": asdict(self.config),
            "total_reward": self._total_reward,
            "complaints": len(self.complaints),
            "inspected": len(self._outcomes),
            "deferred": len(self._deferred),
            "actionable_found": sum(
                item["outcome"] == OutcomeLabel.ACTIONABLE.value for item in self._outcomes
            ),
            "actionable_missed": sum(
                item.latent_outcome is OutcomeLabel.ACTIONABLE for item in self._deferred
            ),
            "actionable_mean_delay_days": _actionable_mean_delay(self._outcomes),
            "mean_delay_days": float(np.mean([item["delay_days"] for item in self._outcomes]))
            if self._outcomes
            else 0.0,
            "max_queue_depth": max(self._queue_depths, default=0),
            "group_metrics": by_group,
            "decisions": self._decisions,
            "outcomes": self._outcomes,
        }


def _actionable_mean_delay(outcomes: list[dict[str, Any]]) -> float:
    delays = [item["delay_days"] for item in outcomes if item["outcome"] == "actionable"]
    return float(np.mean(delays)) if delays else 0.0
