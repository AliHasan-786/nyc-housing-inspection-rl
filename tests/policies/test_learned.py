from nyc_housing_rl.domain import OutcomeLabel
from nyc_housing_rl.policies.learned import train_tabular_policy
from nyc_housing_rl.simulation.environment import InspectionTriageEnv
from nyc_housing_rl.simulation.types import Complaint, SimulationConfig


def test_learned_policies_train_and_choose_valid_actions() -> None:
    complaints = [
        Complaint("a", 0, 0, 0.9, latent_outcome=OutcomeLabel.ACTIONABLE),
        Complaint("b", 1, 0, 0.1, latent_outcome=OutcomeLabel.NO_ACTION),
    ]
    env = InspectionTriageEnv(complaints, SimulationConfig(daily_capacity=1))
    for kind in ("contextual_bandit", "tabular_q_learning"):
        policy = train_tabular_policy(env, kind=kind, seed=7, episodes=4)
        observation, _ = env.reset(seed=1)
        assert int(policy.act(observation)) in {0, 1, 2}
