from datetime import datetime
from typing import Optional, Any, Dict
from pydantic import BaseModel, Field


class PatientProfileCreate(BaseModel):
    raw_description: str = Field(..., min_length=10)


class PatientProfileUpdate(BaseModel):
    extracted_entities: Optional[Dict[str, Any]] = None


class PatientProfileOut(BaseModel):
    id: int
    user_id: int
    raw_description: str
    extracted_entities: Optional[Dict[str, Any]] = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}
