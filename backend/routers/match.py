from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.patient_profile import PatientProfile
from backend.models.user import User
from backend.schemas.trial import MatchRequest, ExplainRequest, TrialMatchResult, TrialOut
from backend.services.matcher import match_trials
from backend.services.agent_service import run_eligibility_agent
from backend.utils.jwt_utils import get_current_user
import logging

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/match", tags=["Trial Matching"])


async def _get_profile(profile_id: int, current_user: User, db: AsyncSession) -> PatientProfile:
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    from backend.models.user import UserRole
    if profile.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return profile


@router.post("/", response_model=List[TrialMatchResult])
async def match(
    req: MatchRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Match a patient profile to the top-k most relevant clinical trials."""
    profile = await _get_profile(req.profile_id, current_user, db)
    entities = profile.extracted_entities or {}

    if not entities.get("diagnosis"):
        raise HTTPException(
            status_code=400,
            detail="Profile has no extracted entities. Please re-create the profile.",
        )

    matched = await match_trials(db, entities, top_k=req.top_k)

    results = []
    for m in matched:
        from datetime import datetime
        trial_out = TrialOut(
            id=m["id"],
            nct_id=m["nct_id"],
            title=m["title"],
            status=m["status"],
            phase=m["phase"],
            conditions=m["conditions"],
            interventions=m["interventions"],
            eligibility_criteria=m["eligibility_criteria"],
            summary=m["summary"],
            last_synced=m["last_synced"] or datetime.utcnow(),
        )
        results.append(
            TrialMatchResult(
                trial=trial_out,
                similarity_score=round(m["similarity"], 4),
                explanation=None,
            )
        )
    return results


@router.post("/explain")
async def explain_eligibility(
    req: ExplainRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Use the LangChain agent to explain eligibility for a specific trial."""
    profile = await _get_profile(req.profile_id, current_user, db)
    entities = profile.extracted_entities or {}

    question = (
        f"Please check my eligibility for clinical trial {req.nct_id}. "
        f"Get the full trial details and compare them to my patient profile. "
        f"Provide a detailed assessment: am I ELIGIBLE, PARTIALLY_ELIGIBLE, or NOT_ELIGIBLE? "
        f"List the specific reasons for your assessment."
    )

    agent_result = await run_eligibility_agent(
        question=question,
        patient_entities=entities,
    )
    return {
        "nct_id": req.nct_id,
        "profile_id": req.profile_id,
        "assessment": agent_result.get("answer", ""),
        "tool_calls_made": agent_result.get("intermediate_steps", 0),
    }
