from nyc_housing_rl.domain import OutcomeLabel
from nyc_housing_rl.evaluation.runner import run_policy
from nyc_housing_rl.policies.baselines import Fifo
from nyc_housing_rl.simulation.environment import InspectionTriageEnv
from nyc_housing_rl.simulation.types import Complaint, SimulationConfig


def test_runner_returns_policy_labeled_metrics_and_decisions() -> None:
    env = InspectionTriageEnv(
        [Complaint("a", 0, 0, 0.8, latent_outcome=OutcomeLabel.ACTIONABLE)],
        SimulationConfig(daily_capacity=1),
    )
    result = run_policy(env, Fifo())
    assert result["policy"] == "fifo_routine"
    assert result["actionable_found"] == 1
    assert result["decisions"] == [{"complaint_id": "a", "day": 0, "action": "routine"}]
