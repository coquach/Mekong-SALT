"""Gate management endpoints."""

from uuid import UUID

from fastapi import APIRouter, Depends, Query, Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.responses import success_response
from app.db.session import get_db_session
from app.schemas.common import SuccessResponse
from app.schemas.gate import GateCollection, GateCreate, GateRead, GateUpdate
from app.services.gate_service import create_gate, get_gate, list_gates, update_gate

router = APIRouter(prefix="/gates", tags=["gates"])


@router.post("", response_model=SuccessResponse[GateRead], status_code=201)
async def create_gate_endpoint(
    payload: GateCreate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Register a gate."""
    gate = await create_gate(session, payload)
    return success_response(
        request=request,
        message="Tạo cống thành công.",
        data=GateRead.model_validate(gate),
        status_code=201,
    )


@router.get("", response_model=SuccessResponse[GateCollection])
async def list_gates_endpoint(
    request: Request,
    limit: int = Query(default=100, ge=1, le=500),
    region_code: str | None = Query(default=None, max_length=50),
    session: AsyncSession = Depends(get_db_session),
):
    """List gates."""
    gates = await list_gates(session, limit=limit, region_code=region_code)
    return success_response(
        request=request,
        message="Lấy danh sách cống thành công.",
        data=GateCollection(
            items=[GateRead.model_validate(gate) for gate in gates],
            count=len(gates),
        ),
    )


@router.get("/{gate_id}", response_model=SuccessResponse[GateRead])
async def get_gate_endpoint(
    gate_id: UUID,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Get a gate."""
    gate = await get_gate(session, gate_id)
    return success_response(
        request=request,
        message="Lấy chi tiết cống thành công.",
        data=GateRead.model_validate(gate),
    )


@router.patch("/{gate_id}", response_model=SuccessResponse[GateRead])
async def update_gate_endpoint(
    gate_id: UUID,
    payload: GateUpdate,
    request: Request,
    session: AsyncSession = Depends(get_db_session),
):
    """Update a gate."""
    gate = await update_gate(session, gate_id, payload)
    return success_response(
        request=request,
        message="Cập nhật cống thành công.",
        data=GateRead.model_validate(gate),
    )
