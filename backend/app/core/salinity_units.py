"""Shared salinity unit conversion helpers and threshold constants.

Canonical storage/evaluation unit in backend remains dS/m.
g/L is exposed as a communication/display equivalent for proposal alignment.
"""

from __future__ import annotations

from decimal import Decimal, ROUND_HALF_UP

SALINITY_G_PER_L_PER_DSM = Decimal("0.64")
SALINITY_DSM_QUANT = Decimal("0.01")
SALINITY_GL_QUANT = Decimal("0.01")
SALINITY_GL_MATCH_TOLERANCE = Decimal("0.05")

SALINITY_SAFE_THRESHOLD_DSM = Decimal("1.00")
SALINITY_WARNING_THRESHOLD_DSM = Decimal("2.50")
SALINITY_DANGER_THRESHOLD_DSM = Decimal("4.00")


def normalize_salinity_dsm(value: Decimal) -> Decimal:
    """Round one salinity value to persisted dS/m precision."""
    return Decimal(value).quantize(SALINITY_DSM_QUANT, rounding=ROUND_HALF_UP)


def normalize_salinity_gl(value: Decimal) -> Decimal:
    """Round one salinity value to display g/L precision."""
    return Decimal(value).quantize(SALINITY_GL_QUANT, rounding=ROUND_HALF_UP)


def dsm_to_gl(value_dsm: Decimal | None) -> Decimal | None:
    """Convert salinity from dS/m to g/L with display rounding."""
    if value_dsm is None:
        return None
    return normalize_salinity_gl(Decimal(value_dsm) * SALINITY_G_PER_L_PER_DSM)


def gl_to_dsm(value_gl: Decimal | None) -> Decimal | None:
    """Convert salinity from g/L to dS/m with storage rounding."""
    if value_gl is None:
        return None
    if SALINITY_G_PER_L_PER_DSM == 0:
        raise ValueError("SALINITY_G_PER_L_PER_DSM must be non-zero.")
    return normalize_salinity_dsm(Decimal(value_gl) / SALINITY_G_PER_L_PER_DSM)


def are_units_consistent(
    *,
    salinity_dsm: Decimal,
    salinity_gl: Decimal,
    tolerance_gl: Decimal = SALINITY_GL_MATCH_TOLERANCE,
) -> bool:
    """Check whether provided dS/m and g/L values are equivalent within tolerance."""
    expected_gl = dsm_to_gl(salinity_dsm)
    if expected_gl is None:
        return False
    return abs(expected_gl - normalize_salinity_gl(salinity_gl)) <= tolerance_gl
