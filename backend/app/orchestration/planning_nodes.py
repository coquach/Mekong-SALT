"""Internal node services for agent planning orchestration.

This module is internal-only: it exposes node-sized functions used by the
planning graph so each stage can be unit-tested independently.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Mapping

from sqlalchemy.ext.asyncio import AsyncSession

from app.core.salinity_units import dsm_to_gl
from app.agents.policy_guard import validate_generated_plan
from app.agents.providers import PlanProvider
from app.db.redis import RedisManager
from app.repositories.region import RegionRepository
from app.schemas.retrieval import RetrievalContext
from app.schemas.risk import RiskEvaluationFilters
from app.services.earth_engine_service import get_or_fetch_earth_engine_context
from app.services.rag import retrieve_ranked_knowledge_context
from app.services.risk_service import RiskEvaluationBundle, evaluate_current_risk


@dataclass(slots=True)
class PlanningNodeServices:
    """Dependencies required by planning graph node services."""

    session: AsyncSession
    redis_manager: RedisManager | None
    provider: PlanProvider


async def observe_request_node(state: Mapping[str, Any]) -> dict[str, Any]:
    """Build filters and normalized objective from the incoming request."""
    request = state["request"]
    return {
        "filters": RiskEvaluationFilters(
            station_id=request.station_id,
            station_code=request.station_code,
            region_id=request.region_id,
            region_code=request.region_code,
        ),
        "objective": request.objective
        or "Bảo vệ chất lượng nước tưới và giảm rủi ro độ mặn.",
    }


async def assess_risk_node(
    state: Mapping[str, Any],
    *,
    services: PlanningNodeServices,
) -> dict[str, Any]:
    """Resolve risk context unless an upstream caller already provided it."""
    if state.get("risk_bundle") is not None:
        return {}

    bundle = await evaluate_current_risk(
        services.session,
        filters=state["filters"],
        redis_manager=services.redis_manager,
        trigger_source="agent.plan.workflow",
        trigger_payload={"workflow": "langgraph_planning"},
    )
    return {"risk_bundle": bundle}


async def retrieve_context_node(
    state: Mapping[str, Any],
    *,
    services: PlanningNodeServices,
) -> dict[str, Any]:
    """Load region metadata and build planner context from risk observations."""
    risk_bundle: RiskEvaluationBundle = state["risk_bundle"]
    region_repo = RegionRepository(services.session)
    region = await region_repo.get(risk_bundle.assessment.region_id)
    objective = state.get("objective") or "Bảo vệ chất lượng nước tưới và giảm rủi ro độ mặn."
    retrieval_context = _validate_retrieval_context_contract(
        await retrieve_ranked_knowledge_context(
            services.session,
            objective=objective,
            risk_bundle=risk_bundle,
        )
    )
    retrieval_context_payload = retrieval_context.model_dump(mode="json")
    knowledge_context = retrieval_context_payload["evidence"]
    retrieval_trace = {
        "total_evidence": len(knowledge_context),
        "source_counts": retrieval_context_payload["provenance"]["source_counts"],
        "top_citations": retrieval_context_payload["ranking_metadata"]["top_citations"],
    }

    earth_engine_context = await get_or_fetch_earth_engine_context(
        region=region,
        station=risk_bundle.reading.station,
        weather_snapshot=risk_bundle.weather_snapshot,
        redis_manager=services.redis_manager,
    )
    if earth_engine_context is not None:
        retrieval_trace["earth_engine"] = {
            "source": earth_engine_context.get("source"),
            "fallback_used": earth_engine_context.get("fallback_used", False),
            "dataset": earth_engine_context.get("dataset"),
        }

    retrieved_context = {
        "region": {
            "id": str(risk_bundle.assessment.region_id),
            "code": getattr(region, "code", None),
            "name": getattr(region, "name", None),
            "province": getattr(region, "province", None),
            "crop_profile": getattr(region, "crop_profile", None),
        },
        "reading": {
            "station_code": risk_bundle.reading.station.code,
            "recorded_at": risk_bundle.reading.recorded_at.isoformat(),
            "salinity_dsm": str(risk_bundle.reading.salinity_dsm),
            "salinity_gl": str(dsm_to_gl(risk_bundle.reading.salinity_dsm)),
            "water_level_m": str(risk_bundle.reading.water_level_m),
        },
        "assessment": {
            "risk_level": risk_bundle.assessment.risk_level.value,
            "trend_direction": risk_bundle.assessment.trend_direction.value,
            "trend_delta_dsm": (
                str(risk_bundle.assessment.trend_delta_dsm)
                if risk_bundle.assessment.trend_delta_dsm is not None
                else None
            ),
            "trend_delta_gl": (
                str(dsm_to_gl(risk_bundle.assessment.trend_delta_dsm))
                if risk_bundle.assessment.trend_delta_dsm is not None
                else None
            ),
            "summary": risk_bundle.assessment.summary,
            "rationale": risk_bundle.assessment.rationale,
        },
        "weather_snapshot": (
            {
                "observed_at": risk_bundle.weather_snapshot.observed_at.isoformat(),
                "wind_speed_mps": (
                    str(risk_bundle.weather_snapshot.wind_speed_mps)
                    if risk_bundle.weather_snapshot.wind_speed_mps is not None
                    else None
                ),
                "tide_level_m": (
                    str(risk_bundle.weather_snapshot.tide_level_m)
                    if risk_bundle.weather_snapshot.tide_level_m is not None
                    else None
                ),
                "condition_summary": risk_bundle.weather_snapshot.condition_summary,
            }
            if risk_bundle.weather_snapshot is not None
            else None
        ),
        "earth_engine_context": earth_engine_context,
        "retrieval_context": retrieval_context_payload,
        "knowledge_context": knowledge_context,
        "retrieval_trace": retrieval_trace,
    }
    return {"retrieved_context": retrieved_context}


async def draft_plan_node(
    state: Mapping[str, Any],
    *,
    services: PlanningNodeServices,
) -> dict[str, Any]:
    """Generate a structured draft plan from objective + retrieved context."""
    draft_plan = await services.provider.generate_plan(
        objective=state["objective"],
        context=state["retrieved_context"],
    )
    return {"draft_plan": draft_plan}


async def validate_plan_node(state: Mapping[str, Any]) -> dict[str, Any]:
    """Validate a draft plan against deterministic policy guard rules."""
    validation_result = validate_generated_plan(
        state["draft_plan"],
        risk_level=state["risk_bundle"].assessment.risk_level,
    )
    return {"validation_result": validation_result}


def _validate_retrieval_context_contract(payload: RetrievalContext) -> RetrievalContext:
    """Keep retrieval contract explicit at planning boundary."""
    return payload
