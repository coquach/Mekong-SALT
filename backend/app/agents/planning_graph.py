"""Initial LangGraph workflow for agent-assisted planning."""

from __future__ import annotations

from typing import Any, TypedDict

from langgraph.graph import END, START, StateGraph
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.policy_guard import validate_generated_plan
from app.agents.providers import PlanProvider
from app.db.redis import RedisManager
from app.repositories.region import RegionRepository
from app.schemas.agent import AgentPlanRequest, GeneratedActionPlan, PlanValidationResult
from app.services.risk_service import RiskEvaluationBundle, evaluate_current_risk
from app.schemas.risk import RiskEvaluationFilters


class PlanningState(TypedDict, total=False):
    """Mutable state carried through the LangGraph planning workflow."""

    request: AgentPlanRequest
    objective: str
    filters: RiskEvaluationFilters
    risk_bundle: RiskEvaluationBundle
    retrieved_context: dict[str, Any]
    draft_plan: GeneratedActionPlan
    validation_result: PlanValidationResult


class AgentPlanningWorkflow:
    """Initial observe -> assess_risk -> retrieve_context -> draft_plan -> validate_plan graph."""

    def __init__(
        self,
        *,
        session: AsyncSession,
        redis_manager: RedisManager | None,
        provider: PlanProvider,
    ) -> None:
        self._session = session
        self._redis_manager = redis_manager
        self._provider = provider
        self._graph = self._build_graph().compile()

    async def run(self, request: AgentPlanRequest) -> PlanningState:
        """Execute the initial planning workflow."""
        return await self._graph.ainvoke({"request": request})

    def _build_graph(self) -> StateGraph:
        graph = StateGraph(PlanningState)
        graph.add_node("observe", self._observe)
        graph.add_node("assess_risk", self._assess_risk)
        graph.add_node("retrieve_context", self._retrieve_context)
        graph.add_node("draft_plan", self._draft_plan)
        graph.add_node("validate_plan", self._validate_plan)
        graph.add_edge(START, "observe")
        graph.add_edge("observe", "assess_risk")
        graph.add_edge("assess_risk", "retrieve_context")
        graph.add_edge("retrieve_context", "draft_plan")
        graph.add_edge("draft_plan", "validate_plan")
        graph.add_edge("validate_plan", END)
        return graph

    async def _observe(self, state: PlanningState) -> PlanningState:
        request = state["request"]
        return {
            "filters": RiskEvaluationFilters(
                station_id=request.station_id,
                station_code=request.station_code,
                region_id=request.region_id,
                region_code=request.region_code,
            ),
            "objective": request.objective or "Protect irrigation water quality and reduce salinity risk.",
        }

    async def _assess_risk(self, state: PlanningState) -> PlanningState:
        bundle = await evaluate_current_risk(
            self._session,
            filters=state["filters"],
            redis_manager=self._redis_manager,
            trigger_source="agent.plan.workflow",
            trigger_payload={"workflow": "langgraph_planning"},
        )
        return {"risk_bundle": bundle}

    async def _retrieve_context(self, state: PlanningState) -> PlanningState:
        risk_bundle = state["risk_bundle"]
        region_repo = RegionRepository(self._session)
        region = await region_repo.get(risk_bundle.assessment.region_id)
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
            "knowledge_context": [],
        }
        return {"retrieved_context": retrieved_context}

    async def _draft_plan(self, state: PlanningState) -> PlanningState:
        draft_plan = await self._provider.generate_plan(
            objective=state["objective"],
            context=state["retrieved_context"],
        )
        return {"draft_plan": draft_plan}

    async def _validate_plan(self, state: PlanningState) -> PlanningState:
        validation_result = validate_generated_plan(
            state["draft_plan"],
            risk_level=state["risk_bundle"].assessment.risk_level,
        )
        return {"validation_result": validation_result}
