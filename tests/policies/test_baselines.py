import numpy as np

from nyc_housing_rl.domain import DecisionAction
from nyc_housing_rl.policies.baselines import AlwaysExpedite, Fifo, NeverInspect, RiskTier


def test_baseline_actions_are_explainable_and_deterministic() -> None:
    observation = np.array([0.8, 0, 0, 0, 1, 0, 0, 0], dtype=np.float32)
    assert Fifo().act(observation) is DecisionAction.ROUTINE
    assert AlwaysExpedite().act(observation) is DecisionAction.EXPEDITED
    assert NeverInspect().act(observation) is DecisionAction.DEFER
    assert RiskTier().act(observation) is DecisionAction.EXPEDITED


def test_risk_tier_does_not_expedite_known_permitted_work() -> None:
    observation = np.array([0.9, 0, 1, 0, 1, 0, 0, 0], dtype=np.float32)
    assert RiskTier().act(observation) is DecisionAction.ROUTINE
