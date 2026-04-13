import logging
from typing import List, Tuple, Any, Dict
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text
from backend.services.embedder import embed_text
from backend.services.entity_extractor import extract_entities

logger = logging.getLogger(__name__)


def _build_patient_query_text(entities: Dict[str, Any]) -> str:
    """Build a query string from extracted patient entities."""
    parts = []
    if entities.get("diagnosis"):
        parts.append(f"Diagnosis: {entities['diagnosis']}")
    if entities.get("age"):
        parts.append(f"Age: {entities['age']}")
    if entities.get("gender"):
        parts.append(f"Gender: {entities['gender']}")
    prior = entities.get("prior_treatments", [])
    if prior:
        parts.append(f"Prior treatments: {', '.join(str(p) for p in prior)}")
    exclusions = entities.get("exclusion_factors", [])
    if exclusions:
        parts.append(f"Exclusion factors: {', '.join(str(e) for e in exclusions)}")
    return " | ".join(parts)


async def match_trials(
    db: AsyncSession,
    entities: Dict[str, Any],
    top_k: int = 5,
) -> List[Dict[str, Any]]:
    """
    Embed patient entities and perform pgvector cosine similarity search.
    Returns top_k trials with similarity scores.
    """
    query_text = _build_patient_query_text(entities)
    query_vector = embed_text(query_text)

    # Format as pgvector literal
    vector_literal = "[" + ",".join(str(f) for f in query_vector) + "]"

    sql = text(
        """
        SELECT
            id, nct_id, title, status, phase, conditions, interventions,
            eligibility_criteria, summary, last_synced,
            1 - (embedding <=> :query_vector::vector) AS similarity
        FROM trials
        WHERE embedding IS NOT NULL
        ORDER BY embedding <=> :query_vector::vector
        LIMIT :top_k
        """
    )

    result = await db.execute(
        sql,
        {"query_vector": vector_literal, "top_k": top_k},
    )
    rows = result.mappings().all()

    matches = []
    for row in rows:
        matches.append(
            {
                "id": row["id"],
                "nct_id": row["nct_id"],
                "title": row["title"],
                "status": row["status"],
                "phase": row["phase"],
                "conditions": row["conditions"],
                "interventions": row["interventions"],
                "eligibility_criteria": row["eligibility_criteria"],
                "summary": row["summary"],
                "last_synced": row["last_synced"],
                "similarity": float(row["similarity"]),
            }
        )
    return matches
