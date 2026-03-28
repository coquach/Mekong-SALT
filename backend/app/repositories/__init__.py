"""Repository package for persistence abstractions."""

from app.repositories.base import AsyncRepository
from app.repositories.region import RegionRepository
from app.repositories.risk import AlertEventRepository, RiskAssessmentRepository
from app.repositories.sensor import SensorReadingRepository, SensorStationRepository
from app.repositories.weather import WeatherSnapshotRepository

__all__ = [
    "AlertEventRepository",
    "AsyncRepository",
    "RegionRepository",
    "RiskAssessmentRepository",
    "SensorReadingRepository",
    "SensorStationRepository",
    "WeatherSnapshotRepository",
]

