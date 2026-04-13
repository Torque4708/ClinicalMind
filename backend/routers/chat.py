from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from backend.database import get_db
from backend.models.user import User
from backend.schemas.trial import ChatRequest, ChatResponse
from backend.services.rag_service import rag_answer
from backend.utils.jwt_utils import get_current_user

router = APIRouter(prefix="/chat", tags=["RAG Chat"])


@router.post("/", response_model=ChatResponse)
async def chat(
    req: ChatRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """
    Answer a user question grounded in clinical trial documents via RAG.
    Optionally filter to a specific trial by NCT ID.
    """
    result = await rag_answer(
        question=req.question,
        db_session=db,
        nct_id=req.nct_id,
    )
    return ChatResponse(
        answer=result["answer"],
        source_trial_ids=result["source_trial_ids"],
    )
