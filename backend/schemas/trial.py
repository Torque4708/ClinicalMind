from datetime import datetime
from typing import Optional, List, Any, Dict
from pydantic import BaseModel


class TrialOut(BaseModel):
    id: int
    nct_id: str
    title: Optional[str] = None
    status: Optional[str] = None
    phase: Optional[str] = None
    conditions: Optional[List[Any]] = None
    interventions: Optional[List[Any]] = None
    eligibility_criteria: Optional[str] = None
    summary: Optional[str] = None
    last_synced: datetime

    model_config = {"from_attributes": True}


class TrialMatchResult(BaseModel):
    trial: TrialOut
    similarity_score: float
    explanation: Optional[str] = None


class TrialStats(BaseModel):
    total_trials: int
    last_synced: Optional[datetime] = None
    phase_distribution: Dict[str, int]


class ChatRequest(BaseModel):
    question: str
    nct_id: Optional[str] = None


class ChatResponse(BaseModel):
    answer: str
    source_trial_ids: List[str] = []


class MatchRequest(BaseModel):
    profile_id: int
    top_k: int = 5


class ExplainRequest(BaseModel):
    profile_id: int
    nct_id: str
