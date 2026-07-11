import numpy as np
from gymnasium.utils.env_checker import check_env

from nyc_housing_rl.domain import DecisionAction, OutcomeLabel
from nyc_housing_rl.simulation.environment import InspectionTriageEnv
from nyc_housing_rl.simulation.types import Complaint, SimulationConfig


def _complaints() -> list[Complaint]:
    return [
        Complaint("a", 0, 0, 0.9, equity_group="A", latent_outcome=OutcomeLabel.ACTIONABLE),
        Complaint("b", 0, 1, 0.2, equity_group="B", latent_outcome=OutcomeLabel.NO_ACTION),
        Complaint("c", 1, 2, 0.8, equity_group="B", latent_outcome=OutcomeLabel.ACTIONABLE),
    ]


def test_environment_is_gymnasium_compliant() -> None:
    env = InspectionTriageEnv(_complaints(), SimulationConfig(daily_capacity=1))
    check_env(env, skip_render_check=True)


def test_capacity_persists_and_backlog_is_drained() -> None:
    env = InspectionTriageEnv(_complaints(), SimulationConfig(daily_capacity=1))
    observation, _ = env.reset(seed=7)
    assert np.isclose(observation[4], 1.0)
    for action in [DecisionAction.ROUTINE, DecisionAction.ROUTINE, DecisionAction.ROUTINE]:
        observation, _, terminated, _, _ = env.step(int(action))
    assert terminated
    result = env.result()
    assert result["inspected"] == 3
    assert result["actionable_found"] == 2
    assert result["max_queue_depth"] >= 1


def test_deferred_actionable_complaint_is_measured_as_missed() -> None:
    env = InspectionTriageEnv(_complaints()[:1], SimulationConfig(daily_capacity=1))
    env.reset(seed=7)
    _, reward, terminated, _, _ = env.step(int(DecisionAction.DEFER))
    assert terminated
    assert reward < 0
    assert env.result()["actionable_missed"] == 1
