"""Run a policy in a simulator and return inspectable decisions and metrics."""

from __future__ import annotations

from typing import Protocol

import numpy as np

from nyc_housing_rl.domain import DecisionAction
from nyc_housing_rl.simulation.environment import InspectionTriageEnv


class Policy(Protocol):
    name: str

    def act(self, observation: np.ndarray) -> DecisionAction: ...


def run_policy(env: InspectionTriageEnv, policy: Policy, *, seed: int = 0) -> dict[str, object]:
    observation, _ = env.reset(seed=seed)
    terminated = False
    while not terminated:
        action = policy.act(observation)
        observation, _, terminated, _, _ = env.step(int(action))
    result = env.result()
    result["policy"] = policy.name
    result["seed"] = seed
    return result
