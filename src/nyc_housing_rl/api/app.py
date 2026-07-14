"""FastAPI entry point for the bounded public Policy Lab API."""

from __future__ import annotations

from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from nyc_housing_rl.api.schemas import GroupMetric, PolicyRunRequest, PolicyRunResponse
from nyc_housing_rl.api.service import run_scenario
from nyc_housing_rl.evaluation.artifacts import _limitations


def create_app(
    *, data_root: Path = Path("data"), artifact_root: Path = Path("artifacts")
) -> FastAPI:
    app = FastAPI(
        title="Civic Inspection Lab Policy API",
        version="0.1.0",
        description="Bounded counterfactual policy scenarios; never a live dispatch system.",
    )
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
        allow_methods=["GET", "POST"],
        allow_headers=["content-type"],
    )

    @app.get("/healthz")
    def healthz() -> dict[str, str]:
        return {"status": "ok", "service": "civic-inspection-policy-api"}

    @app.post("/v1/policy-runs", response_model=PolicyRunResponse)
    def create_policy_run(request: PolicyRunRequest) -> PolicyRunResponse:
        try:
            artifact_id, result = run_scenario(
                request, data_root=data_root, artifact_root=artifact_root
            )
        except FileNotFoundError as error:
            raise HTTPException(status_code=404, detail=str(error)) from error
        return PolicyRunResponse(
            artifactId=artifact_id,
            policy=request.policy,
            snapshotDate=request.snapshot_date,
            isCounterfactual=True,
            totalReward=float(result["total_reward"]),
            inspected=int(result["inspected"]),
            actionableFound=int(result["actionable_found"]),
            actionableMissed=int(result["actionable_missed"]),
            meanDelayDays=float(result["mean_delay_days"]),
            maxQueueDepth=int(result["max_queue_depth"]),
            groupMetrics={
                key: GroupMetric(**value) for key, value in result["group_metrics"].items()
            },
            limitations=_limitations(),
        )

    return app


app = create_app()
