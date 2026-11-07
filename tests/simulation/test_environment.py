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
    assert env.result()["mean_delay_days"] is None


def test_terminal_reward_is_not_double_counted_and_accounting_reconciles() -> None:
    complaint = _complaints()[:1]
    env = InspectionTriageEnv(complaint, SimulationConfig(daily_capacity=1))
    env.reset(seed=7)
    _, reward, terminated, _, _ = env.step(int(DecisionAction.ROUTINE))
    assert terminated
    assert reward == 95.0
    result = env.result()
    assert result["total_reward"] == 95.0
    assert result["actionable_accounting"] == {
        "latent_actionable_total": 1,
        "found": 1,
        "deferred": 0,
        "inaccessible": 0,
        "queued_unserved": 0,
        "unfound": 0,
    }


def test_actionable_accounting_distinguishes_inaccessible_and_unserved() -> None:
    inaccessible_env = InspectionTriageEnv(
        _complaints()[:1], SimulationConfig(daily_capacity=1, access_probability=0.0)
    )
    inaccessible_env.reset(seed=7)
    inaccessible_env.step(int(DecisionAction.ROUTINE))
    inaccessible = inaccessible_env.result()
    assert inaccessible["actionable_found"] == 0
    assert inaccessible["actionable_inaccessible"] == 1
    assert inaccessible["actionable_missed"] == 1

    queued_env = InspectionTriageEnv(
        [
                Complaint("a-routine", 0, 0, 0.1, latent_outcome=OutcomeLabel.NO_ACTION),
                Complaint("z-actionable", 0, 0, 0.9, latent_outcome=OutcomeLabel.ACTIONABLE),
        ],
        SimulationConfig(daily_capacity=1, max_drain_days=0),
    )
    queued_env.reset(seed=7)
    queued_env.step(int(DecisionAction.ROUTINE))
    queued_env.step(int(DecisionAction.ROUTINE))
    queued = queued_env.result()
    assert queued["actionable_queued_unserved"] == 1
    assert queued["actionable_missed"] == 1
    assert queued["actionable_mean_delay_days"] is None
