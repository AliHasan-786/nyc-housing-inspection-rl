"""Domain models for the inspection-triage simulator."""

from dataclasses import dataclass

from nyc_housing_rl.domain import OutcomeLabel


@dataclass(frozen=True, slots=True)
class Complaint:
    """Decision-time complaint state plus a latent historical/simulated outcome.

    Policies never receive ``latent_outcome``. It is revealed only after an
    inspection succeeds and is used for retrospective simulation metrics.
    """

    complaint_id: str
    arrival_day: int
    borough: int
    risk_score: float
    prior_complaints: int = 0
    permit_overlap: bool = False
    equity_group: str = "unknown"
    latent_outcome: OutcomeLabel = OutcomeLabel.NO_ACTION

    def __post_init__(self) -> None:
        if self.arrival_day < 0:
            raise ValueError("arrival_day must be non-negative")
        if not 0 <= self.borough <= 4:
            raise ValueError("borough must be an integer from 0 through 4")
        if not 0.0 <= self.risk_score <= 1.0:
            raise ValueError("risk_score must be in [0, 1]")
        if self.prior_complaints < 0:
            raise ValueError("prior_complaints must be non-negative")


@dataclass(frozen=True, slots=True)
class SimulationConfig:
    """Explicit operations and safety assumptions for one scenario."""

    daily_capacity: int = 4
    max_drain_days: int = 30
    access_probability: float = 1.0
    defer_penalty: float = -25.0
    actionable_reward: float = 100.0
    inspection_cost: float = -5.0
    delay_penalty_per_day: float = -1.0

    def __post_init__(self) -> None:
        if self.daily_capacity <= 0:
            raise ValueError("daily_capacity must be positive")
        if self.max_drain_days < 0:
            raise ValueError("max_drain_days must be non-negative")
        if not 0.0 <= self.access_probability <= 1.0:
            raise ValueError("access_probability must be in [0, 1]")
