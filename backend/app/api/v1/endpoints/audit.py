"""Audit log endpoints."""

import uuid
from datetime import datetime, timedelta
from typing import Any, Optional

from fastapi import APIRouter, Depends, Query
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import Pagination, get_current_user, get_pagination
from app.db.session import get_db
from app.models.audit_log import AuditLog
from app.models.user import User
from app.schemas.audit import AuditLogListResponse, AuditLogResponse, AuditStats

router = APIRouter()


@router.get("", response_model=AuditLogListResponse)
async def list_audit_logs(
    action: Optional[str] = None,
    entity_type: Optional[str] = None,
    status_filter: Optional[str] = Query(None, alias="status", pattern="^(success|failure|error)$"),
    date_from: Optional[datetime] = None,
    date_to: Optional[datetime] = None,
    pagination: Pagination = Depends(get_pagination),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """List audit logs for current user."""
    query = select(AuditLog).where(AuditLog.user_id == current_user.id)
    count_query = select(func.count(AuditLog.id)).where(AuditLog.user_id == current_user.id)

    if action:
        query = query.where(AuditLog.action == action)
        count_query = count_query.where(AuditLog.action == action)

    if entity_type:
        query = query.where(AuditLog.entity_type == entity_type)
        count_query = count_query.where(AuditLog.entity_type == entity_type)

    if status_filter:
        query = query.where(AuditLog.status == status_filter)
        count_query = count_query.where(AuditLog.status == status_filter)

    if date_from:
        query = query.where(AuditLog.created_at >= date_from)
        count_query = count_query.where(AuditLog.created_at >= date_from)

    if date_to:
        query = query.where(AuditLog.created_at <= date_to)
        count_query = count_query.where(AuditLog.created_at <= date_to)

    # Get total count
    total_result = await db.execute(count_query)
    total = total_result.scalar()

    # Get paginated results
    query = query.order_by(AuditLog.created_at.desc())
    query = query.offset(pagination.offset).limit(pagination.limit)

    result = await db.execute(query)
    logs = result.scalars().all()

    total_pages = (total + pagination.page_size - 1) // pagination.page_size

    return AuditLogListResponse(
        items=logs,
        total=total,
        page=pagination.page,
        page_size=pagination.page_size,
        total_pages=total_pages,
    )


@router.get("/stats", response_model=AuditStats)
async def get_audit_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get audit statistics."""
    now = datetime.utcnow()
    today_start = now.replace(hour=0, minute=0, second=0, microsecond=0)
    week_start = today_start - timedelta(days=today_start.weekday())
    month_start = today_start.replace(day=1)

    # Total actions
    total_result = await db.execute(
        select(func.count(AuditLog.id)).where(AuditLog.user_id == current_user.id)
    )
    total_actions = total_result.scalar() or 0

    # Actions today
    today_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == current_user.id,
            AuditLog.created_at >= today_start,
        )
    )
    actions_today = today_result.scalar() or 0

    # Actions this week
    week_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == current_user.id,
            AuditLog.created_at >= week_start,
        )
    )
    actions_this_week = week_result.scalar() or 0

    # Actions this month
    month_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == current_user.id,
            AuditLog.created_at >= month_start,
        )
    )
    actions_this_month = month_result.scalar() or 0

    # Success rate
    success_result = await db.execute(
        select(func.count(AuditLog.id)).where(
            AuditLog.user_id == current_user.id,
            AuditLog.status == "success",
        )
    )
    success_count = success_result.scalar() or 0
    success_rate = (success_count / total_actions * 100) if total_actions > 0 else 100.0

    # Most common actions
    common_actions_result = await db.execute(
        select(AuditLog.action, func.count(AuditLog.id).label("count"))
        .where(AuditLog.user_id == current_user.id)
        .group_by(AuditLog.action)
        .order_by(func.count(AuditLog.id).desc())
        .limit(5)
    )
    most_common_actions = [
        {"action": row[0], "count": row[1]} for row in common_actions_result.fetchall()
    ]

    # Recent errors
    errors_result = await db.execute(
        select(AuditLog)
        .where(
            AuditLog.user_id == current_user.id,
            AuditLog.status.in_(["failure", "error"]),
        )
        .order_by(AuditLog.created_at.desc())
        .limit(5)
    )
    recent_errors = errors_result.scalars().all()

    return AuditStats(
        total_actions=total_actions,
        actions_today=actions_today,
        actions_this_week=actions_this_week,
        actions_this_month=actions_this_month,
        success_rate=success_rate,
        most_common_actions=most_common_actions,
        recent_errors=recent_errors,
    )


@router.get("/actions")
async def get_available_actions(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get list of all action types in audit logs."""
    result = await db.execute(
        select(AuditLog.action)
        .where(AuditLog.user_id == current_user.id)
        .distinct()
        .order_by(AuditLog.action)
    )
    actions = [row[0] for row in result.fetchall()]

    return {"actions": actions}


@router.get("/entity-types")
async def get_entity_types(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get list of all entity types in audit logs."""
    result = await db.execute(
        select(AuditLog.entity_type)
        .where(
            AuditLog.user_id == current_user.id,
            AuditLog.entity_type.isnot(None),
        )
        .distinct()
        .order_by(AuditLog.entity_type)
    )
    entity_types = [row[0] for row in result.fetchall()]

    return {"entity_types": entity_types}


@router.get("/{log_id}", response_model=AuditLogResponse)
async def get_audit_log(
    log_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> Any:
    """Get specific audit log entry."""
    result = await db.execute(
        select(AuditLog).where(
            AuditLog.id == log_id,
            AuditLog.user_id == current_user.id,
        )
    )
    log = result.scalar_one_or_none()

    if not log:
        from fastapi import HTTPException

        raise HTTPException(
            status_code=404,
            detail="Audit log not found",
        )

    return log
