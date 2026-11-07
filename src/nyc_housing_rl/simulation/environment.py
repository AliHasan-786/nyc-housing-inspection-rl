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
        self._queue_depths.append(len(self._routine) + len(self._expedited))
        terminated = self._index >= len(self.complaints)
        if terminated:
            reward += self._drain()
        # Account for this transition exactly once.  In particular, terminal drain
        # rewards must not re-add the pre-drain portion of the final transition.
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
        by_group: dict[str, dict[str, float | int | None]] = {}
        groups = {item.equity_group for item in self.complaints}
        for group in groups:
            arrivals = [item for item in self.complaints if item.equity_group == group]
            inspections = [item for item in self._outcomes if item["equity_group"] == group]
            by_group[group] = {
                "arrivals": len(arrivals),
                "inspected": len(inspections),
                "service_rate": len(inspections) / len(arrivals) if arrivals else 0.0,
                "mean_delay_days": (
                    float(np.mean([item["delay_days"] for item in inspections]))
                    if inspections
                    else None
                ),
            }
        accounting = self._actionable_accounting()
        return {
            "config": asdict(self.config),
            "total_reward": self._total_reward,
            "complaints": len(self.complaints),
            "inspected": len(self._outcomes),
            "deferred": len(self._deferred),
            "latent_actionable_total": accounting["latent_actionable_total"],
            "actionable_found": accounting["found"],
            "actionable_deferred": accounting["deferred"],
            "actionable_inaccessible": accounting["inaccessible"],
            "actionable_queued_unserved": accounting["queued_unserved"],
            # Retained for backwards compatibility.  "Missed" means every latent
            # actionable that was not found, not merely an explicit deferral.
            "actionable_missed": accounting["unfound"],
            "actionable_unfound": accounting["unfound"],
            "actionable_mean_delay_days": _actionable_mean_delay(self._outcomes),
            "mean_delay_days": (
                float(np.mean([item["delay_days"] for item in self._outcomes]))
                if self._outcomes
                else None
            ),
            "max_queue_depth": max(self._queue_depths, default=0),
            "actionable_accounting": accounting,
            "group_metrics": by_group,
            "decisions": self._decisions,
            "outcomes": self._outcomes,
        }

    def _actionable_accounting(self) -> dict[str, int]:
        """Partition every latent actionable exactly once after an episode."""

        latent_actionable = {
            item.complaint_id
            for item in self.complaints
            if item.latent_outcome is OutcomeLabel.ACTIONABLE
        }
        deferred = {item.complaint_id for item in self._deferred} & latent_actionable
        outcome_by_id = {str(item["complaint_id"]): str(item["outcome"]) for item in self._outcomes}
        found = {
            complaint_id
            for complaint_id, outcome in outcome_by_id.items()
            if complaint_id in latent_actionable and outcome == OutcomeLabel.ACTIONABLE.value
        }
        inaccessible = {
            complaint_id
            for complaint_id, outcome in outcome_by_id.items()
            if complaint_id in latent_actionable and outcome == OutcomeLabel.INACCESSIBLE.value
        }
        queued_unserved = {
            item.complaint_id for item in (*self._routine, *self._expedited)
        } & latent_actionable
        components = (found, deferred, inaccessible, queued_unserved)
        has_overlap = any(
            left & right
            for index, left in enumerate(components)
            for right in components[index + 1 :]
        )
        if has_overlap:
            raise AssertionError("Actionable accounting categories must be disjoint")
        if set().union(*components) != latent_actionable:
            raise AssertionError("Actionable accounting must cover every latent actionable")
        unfound = len(deferred) + len(inaccessible) + len(queued_unserved)
        if len(found) + unfound != len(latent_actionable):
            raise AssertionError("Actionable accounting reconciliation failed")
        return {
            "latent_actionable_total": len(latent_actionable),
            "found": len(found),
            "deferred": len(deferred),
            "inaccessible": len(inaccessible),
            "queued_unserved": len(queued_unserved),
            "unfound": unfound,
        }


def _actionable_mean_delay(outcomes: list[dict[str, Any]]) -> float | None:
    delays = [item["delay_days"] for item in outcomes if item["outcome"] == "actionable"]
    return float(np.mean(delays)) if delays else None
