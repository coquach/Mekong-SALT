"""SQLAlchemy type helpers for model definitions."""

from enum import Enum as PythonEnum

from sqlalchemy import Enum


def enum_type(enum_cls: type[PythonEnum], name: str) -> Enum:
    """Persist enum values instead of enum member names."""
    return Enum(
        enum_cls,
        name=name,
        values_callable=lambda enum_members: [member.value for member in enum_members],
    )

