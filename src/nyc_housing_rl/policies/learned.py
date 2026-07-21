"""Small, reproducible learned policies for the simulator benchmark.

These are deliberately tabular rather than production models. They establish an
auditable RL baseline before a larger function approximator is considered.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import Literal

import numpy as np

from nyc_housing_rl.domain import DecisionAction
from nyc_housing_rl.simulation.environment import InspectionTriageEnv

LearningKind = Literal["contextual_bandit", "tabular_q_learning"]
State = tuple[int, int, int, int, int]


def discretize(observation: np.ndarray) -> State:
    """Keep only decision-time state and coarsen it before tabular learning."""

    return (
        min(4, int(float(observation[0]) * 5)),
        min(3, int(observation[1])),
        int(bool(observation[2])),
        int(float(observation[4]) < 0.5),
        min(3, int(float(observation[5]) // 5)),
    )


@dataclass(slots=True)
class LearnedPolicy:
    name: str
    q_values: dict[State, np.ndarray]

    def act(self, observation: np.ndarray) -> DecisionAction:
        values = self.q_values.get(discretize(observation))
        if values is None:
            return DecisionAction.ROUTINE
        return DecisionAction(int(np.argmax(values)))


def train_tabular_policy(
    env: InspectionTriageEnv,
    *,
    kind: LearningKind,
    seed: int,
    episodes: int = 200,
    learning_rate: float = 0.15,
    gamma: float = 0.95,
    epsilon: float = 0.15,
) -> LearnedPolicy:
    """Train either a myopic contextual bandit or one-step tabular Q learner.

    Training is restricted by the caller to a temporally earlier scenario. This
    function never sees a future evaluation environment.
    """

    rng = np.random.default_rng(seed)
    values: defaultdict[State, np.ndarray] = defaultdict(
        lambda: np.zeros(len(DecisionAction), dtype=np.float64)
    )
    for episode in range(episodes):
        observation, _ = env.reset(seed=seed + episode)
        terminated = False
        while not terminated:
            state = discretize(observation)
            action = (
                int(rng.integers(len(DecisionAction)))
                if rng.random() < epsilon
                else int(np.argmax(values[state]))
            )
            next_observation, reward, terminated, _, _ = env.step(action)
            target = reward
            if kind == "tabular_q_learning" and not terminated:
                target += gamma * float(np.max(values[discretize(next_observation)]))
            values[state][action] += learning_rate * (target - values[state][action])
            observation = next_observation
    return LearnedPolicy(name=kind, q_values=dict(values))
