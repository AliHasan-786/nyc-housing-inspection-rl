"""Public API contracts. JSON uses camelCase to match the web client."""

from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

PolicyName = Literal[
    "fifo_routine", "always_expedite", "never_inspect", "random", "risk_tier", "safety_floor"
]


class PolicyRunRequest(BaseModel):
    """A bounded scenario request; this endpoint is not a dispatch interface."""

    model_config = ConfigDict(populate_by_name=True, extra="forbid")

    snapshot_date: date = Field(alias="snapshotDate")
    daily_capacity: int = Field(alias="dailyCapacity", ge=1, le=100)
    access_probability: float = Field(alias="accessProbability", ge=0.0, le=1.0)
    safety_priority: float = Field(alias="safetyPriority", ge=0.2, le=1.0)
    policy: PolicyName
    seed: int = Field(ge=0, le=2_147_483_647)


class GroupMetric(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    arrivals: int
    inspected: int
    service_rate: float = Field(alias="serviceRate")
    mean_delay_days: float = Field(alias="meanDelayDays")


class PolicyRunResponse(BaseModel):
    model_config = ConfigDict(populate_by_name=True)

    artifact_id: str = Field(alias="artifactId")
    policy: PolicyName
    snapshot_date: date = Field(alias="snapshotDate")
    is_counterfactual: Literal[True] = Field(alias="isCounterfactual")
    total_reward: float = Field(alias="totalReward")
    inspected: int
    actionable_found: int = Field(alias="actionableFound")
    actionable_missed: int = Field(alias="actionableMissed")
    mean_delay_days: float = Field(alias="meanDelayDays")
    max_queue_depth: int = Field(alias="maxQueueDepth")
    group_metrics: dict[str, GroupMetric] = Field(alias="groupMetrics")
    limitations: list[str]
