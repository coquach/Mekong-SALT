"""Seed the database with minimal realistic sample data."""

import asyncio
import logging
from datetime import UTC, datetime, timedelta
from decimal import Decimal

from app.core.config import get_settings
from app.core.logging import configure_logging
from app.db.session import AsyncSessionFactory, close_database_engine
from app.models import (
    ActionExecution,
    ActionPlan,
    AlertEvent,
    DecisionLog,
    EmbeddedChunk,
    KnowledgeDocument,
    Region,
    RiskAssessment,
    SensorReading,
    SensorStation,
    WeatherSnapshot,
)
from app.models.enums import (
    ActionPlanStatus,
    ActionType,
    DecisionActorType,
    ExecutionStatus,
    RiskLevel,
    StationStatus,
    TrendDirection,
)
from app.repositories.region import RegionRepository
from app.repositories.sensor import SensorStationRepository

logger = logging.getLogger(__name__)


async def run_seed() -> None:
    """Insert a minimal yet connected dataset for local development."""
    settings = get_settings()
    configure_logging(settings.log_level)
    now = datetime.now(UTC)

    async with AsyncSessionFactory() as session:
        region_repo = RegionRepository(session)
        station_repo = SensorStationRepository(session)
        existing_region = await region_repo.get_by_code("TIEN-GIANG-GO-CONG")

        if existing_region is not None:
            logger.info("Seed data already present for region %s", existing_region.code)
            return

        region = await region_repo.add(
            Region(
                code="TIEN-GIANG-GO-CONG",
                name="Go Cong Coastal Belt",
                province="Tien Giang",
                description="Representative coastal zone for salinity intrusion monitoring.",
                crop_profile={
                    "dominant_crops": ["rice", "dragon fruit"],
                    "irrigation_priority": "high",
                    "salinity_tolerance_dsm": 1.5,
                },
            )
        )

        station_a = await station_repo.add(
            SensorStation(
                region_id=region.id,
                code="GOCONG-01",
                name="Go Cong East Intake Gate",
                station_type="salinity-water-level",
                status=StationStatus.ACTIVE,
                latitude=Decimal("10.365421"),
                longitude=Decimal("106.742189"),
                location_description="Primary intake near estuary gate.",
                installed_at=now - timedelta(days=180),
                station_metadata={"owner": "Mekong-SALT MVP", "connectivity": "simulated"},
            )
        )
        station_b = await station_repo.add(
            SensorStation(
                region_id=region.id,
                code="GOCONG-02",
                name="Go Cong Inner Canal",
                station_type="salinity-water-level",
                status=StationStatus.ACTIVE,
                latitude=Decimal("10.352114"),
                longitude=Decimal("106.715403"),
                location_description="Secondary observation station inland.",
                installed_at=now - timedelta(days=150),
            )
        )

        reading_a = SensorReading(
            station_id=station_a.id,
            recorded_at=now - timedelta(minutes=30),
            salinity_dsm=Decimal("4.80"),
            water_level_m=Decimal("1.62"),
            temperature_c=Decimal("29.40"),
            battery_level_pct=Decimal("88.00"),
            context_payload={"source": "simulated-sensor", "quality": "good"},
        )
        reading_b = SensorReading(
            station_id=station_b.id,
            recorded_at=now - timedelta(minutes=20),
            salinity_dsm=Decimal("3.10"),
            water_level_m=Decimal("1.25"),
            temperature_c=Decimal("29.10"),
            battery_level_pct=Decimal("91.50"),
            context_payload={"source": "simulated-sensor", "quality": "good"},
        )
        session.add_all([reading_a, reading_b])
        await session.flush()

        weather = WeatherSnapshot(
            region_id=region.id,
            observed_at=now - timedelta(minutes=25),
            wind_speed_mps=Decimal("6.40"),
            wind_direction_deg=135,
            tide_level_m=Decimal("1.72"),
            rainfall_mm=Decimal("0.00"),
            condition_summary="Onshore wind with rising tide",
            source_payload={"provider": "simulated-weather-feed"},
        )
        session.add(weather)
        await session.flush()

        risk = RiskAssessment(
            region_id=region.id,
            station_id=station_a.id,
            based_on_reading_id=reading_a.id,
            based_on_weather_id=weather.id,
            assessed_at=now - timedelta(minutes=15),
            risk_level=RiskLevel.DANGER,
            salinity_dsm=Decimal("4.80"),
            trend_direction=TrendDirection.RISING,
            trend_delta_dsm=Decimal("0.90"),
            rule_version="v1",
            summary="Salinity is above irrigation tolerance and continues to rise.",
            rationale={
                "salinity_threshold_dsm": 4.0,
                "wind_factor": "supporting inland movement",
                "tide_factor": "high tide window",
            },
        )
        session.add(risk)
        await session.flush()

        alert = AlertEvent(
            region_id=region.id,
            risk_assessment_id=risk.id,
            triggered_at=now - timedelta(minutes=14),
            severity=RiskLevel.DANGER,
            title="Danger salinity intrusion alert",
            message="Observed salinity exceeds crop tolerance near primary intake gate.",
        )
        session.add(alert)
        await session.flush()

        plan = ActionPlan(
            region_id=region.id,
            risk_assessment_id=risk.id,
            status=ActionPlanStatus.VALIDATED,
            objective="Reduce saline water intake during the active high-risk window.",
            generated_by="phase-2-seed",
            summary="Notify stakeholders, pause intake, and simulate gate closure until safer conditions return.",
            assumptions={
                "crop_profile": region.crop_profile,
                "tide_window_minutes": 90,
            },
            plan_steps=[
                {"step": 1, "action": ActionType.NOTIFY_FARMERS.value, "reason": "Warn field operators immediately."},
                {"step": 2, "action": ActionType.WAIT_SAFE_WINDOW.value, "reason": "Avoid intake during peak salinity."},
                {"step": 3, "action": ActionType.CLOSE_GATE_SIMULATED.value, "reason": "Simulate protective gate closure."},
            ],
            validation_result={"approved": True, "policy": "simulated-actions-only"},
        )
        session.add(plan)
        await session.flush()

        execution = ActionExecution(
            plan_id=plan.id,
            region_id=region.id,
            action_type=ActionType.CLOSE_GATE_SIMULATED,
            status=ExecutionStatus.SUCCEEDED,
            simulated=True,
            step_index=3,
            started_at=now - timedelta(minutes=10),
            completed_at=now - timedelta(minutes=8),
            result_summary="Simulated gate closure completed.",
            result_payload={"estimated_effect": "reduced saline inflow", "confidence": "medium"},
        )
        session.add(execution)
        await session.flush()

        document = KnowledgeDocument(
            title="Mekong salinity response guideline",
            source_uri="mekong-salt://knowledge/guideline-001",
            document_type="guideline",
            summary="General response actions for high salinity intrusion episodes.",
            content_text=(
                "During high salinity events, pause intake, notify operators, monitor tide, "
                "and resume only when readings return below crop tolerance."
            ),
            tags=["salinity", "response", "irrigation"],
            metadata_payload={"language": "en", "source": "internal-seed"},
        )
        session.add(document)
        await session.flush()

        chunk = EmbeddedChunk(
            document_id=document.id,
            chunk_index=0,
            content_text=document.content_text,
            token_count=29,
            embedding=[0.001] * 768,
            metadata_payload={"section": "overview"},
        )
        session.add(chunk)
        await session.flush()

        decision_log = DecisionLog(
            region_id=region.id,
            risk_assessment_id=risk.id,
            action_plan_id=plan.id,
            action_execution_id=execution.id,
            logged_at=now - timedelta(minutes=7),
            actor_type=DecisionActorType.SYSTEM,
            actor_name="phase-2-seed",
            summary="Seeded scenario links assessment, plan, and simulated execution.",
            outcome="simulated-success",
            details={
                "alert_id": str(alert.id),
                "document_id": str(document.id),
                "notes": "Used for local development and persistence validation.",
            },
            store_as_memory=False,
        )
        session.add(decision_log)

        await session.commit()

    logger.info("Phase 2 seed completed with realistic sample records.")
    await close_database_engine()


if __name__ == "__main__":
    asyncio.run(run_seed())
