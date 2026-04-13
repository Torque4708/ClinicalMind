from datetime import datetime
from typing import List
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from backend.database import get_db
from backend.models.patient_profile import PatientProfile
from backend.models.user import User
from backend.schemas.patient_profile import PatientProfileCreate, PatientProfileOut
from backend.services.entity_extractor import extract_entities
from backend.utils.jwt_utils import get_current_user

router = APIRouter(prefix="/profile", tags=["Patient Profiles"])


@router.post("/", response_model=PatientProfileOut, status_code=status.HTTP_201_CREATED)
async def create_profile(
    profile_data: PatientProfileCreate,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Create a patient profile and auto-extract medical entities via LLM."""
    entities = await extract_entities(profile_data.raw_description)
    now = datetime.utcnow()
    profile = PatientProfile(
        user_id=current_user.id,
        raw_description=profile_data.raw_description,
        extracted_entities=entities,
        created_at=now,
        updated_at=now,
    )
    db.add(profile)
    await db.commit()
    await db.refresh(profile)
    return profile


@router.get("/my/all", response_model=List[PatientProfileOut])
async def get_my_profiles(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get all patient profiles for the current user."""
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.user_id == current_user.id)
        .order_by(PatientProfile.created_at.desc())
    )
    return result.scalars().all()


@router.get("/{profile_id}", response_model=PatientProfileOut)
async def get_profile(
    profile_id: int,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get a single patient profile by ID."""
    result = await db.execute(
        select(PatientProfile).where(PatientProfile.id == profile_id)
    )
    profile = result.scalar_one_or_none()
    if not profile:
        raise HTTPException(status_code=404, detail="Profile not found")
    # Allow admins or the owner
    from backend.models.user import UserRole
    if profile.user_id != current_user.id and current_user.role != UserRole.admin:
        raise HTTPException(status_code=403, detail="Access denied")
    return profile
