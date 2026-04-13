from datetime import datetime
from sqlalchemy import String, Text, DateTime
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column
from pgvector.sqlalchemy import Vector
from backend.database import Base


class Trial(Base):
    __tablename__ = "trials"

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    nct_id: Mapped[str] = mapped_column(String(20), unique=True, index=True, nullable=False)
    title: Mapped[str] = mapped_column(Text, nullable=True)
    status: Mapped[str] = mapped_column(String(100), nullable=True)
    phase: Mapped[str] = mapped_column(String(100), nullable=True)
    conditions: Mapped[list] = mapped_column(JSONB, nullable=True, default=list)
    interventions: Mapped[list] = mapped_column(JSONB, nullable=True, default=list)
    eligibility_criteria: Mapped[str] = mapped_column(Text, nullable=True)
    summary: Mapped[str] = mapped_column(Text, nullable=True)
    embedding: Mapped[list] = mapped_column(Vector(384), nullable=True)
    last_synced: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), default=datetime.utcnow, nullable=False
    )
