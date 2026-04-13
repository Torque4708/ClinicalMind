from datetime import datetime
from typing import List, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func, text
from backend.database import get_db
from backend.models.trial import Trial
from backend.models.user import User
from backend.schemas.trial import TrialOut, TrialStats
from backend.utils.jwt_utils import get_current_user, get_admin_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/trials", tags=["Clinical Trials"])


@router.get("/stats", response_model=TrialStats)
async def get_trial_stats(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get trial statistics: total count, last sync, phase distribution."""
    total_result = await db.execute(select(func.count(Trial.id)))
    total = total_result.scalar() or 0

    last_sync_result = await db.execute(
        select(func.max(Trial.last_synced))
    )
    last_synced = last_sync_result.scalar()

    phase_result = await db.execute(
        select(Trial.phase, func.count(Trial.id)).group_by(Trial.phase)
    )
    phase_dist = {row[0] or "Unknown": row[1] for row in phase_result.all()}

    return TrialStats(
        total_trials=total,
        last_synced=last_synced,
        phase_distribution=phase_dist,
    )


@router.get("/", response_model=List[TrialOut])
async def list_trials(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    condition: Optional[str] = Query(None),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List trials with pagination and optional condition filter."""
    query = select(Trial).order_by(Trial.last_synced.desc()).offset(skip).limit(limit)
    if condition:
        query = query.where(
            Trial.conditions.cast(text("text")).ilike(f"%{condition}%")  # type: ignore
        )
    result = await db.execute(query)
    return result.scalars().all()


@router.get("/{nct_id}", response_model=TrialOut)
async def get_trial(
    nct_id: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single trial by NCT ID."""
    result = await db.execute(select(Trial).where(Trial.nct_id == nct_id))
    trial = result.scalar_one_or_none()
    if not trial:
        raise HTTPException(status_code=404, detail=f"Trial {nct_id} not found")
    return trial


@router.post("/sync")
async def trigger_sync(
    admin_user: User = Depends(get_admin_user),
    db: AsyncSession = Depends(get_db),
):
    """Admin only: trigger manual ETL sync via Celery."""
    from backend.tasks.etl_tasks import sync_trials_task
    task = sync_trials_task.delay()
    return {
        "message": "Trial sync triggered",
        "task_id": task.id,
        "triggered_by": admin_user.username,
        "triggered_at": datetime.utcnow().isoformat(),
    }
