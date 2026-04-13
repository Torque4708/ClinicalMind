import logging
from typing import List, Dict, Any, Optional
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from backend.config import settings
from backend.services.embedder import embed_text

logger = logging.getLogger(__name__)

RAG_PROMPT = PromptTemplate(
    input_variables=["context", "question"],
    template="""You are a clinical trial assistant. Answer the user's question based ONLY on the provided trial context below.
If the context doesn't contain enough information, say so honestly.

Clinical Trial Context:
{context}

User Question: {question}

Answer:""",
)


def _get_llm() -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name="llama3-70b-8192",
        temperature=0.1,
    )


async def rag_answer(
    question: str,
    db_session,
    nct_id: Optional[str] = None,
) -> Dict[str, Any]:
    """
    RAG pipeline: embed question, retrieve top-4 trial chunks from pgvector,
    then answer with Groq LLM.
    """
    from sqlalchemy import text

    query_vector = embed_text(question)
    vector_literal = "[" + ",".join(str(f) for f in query_vector) + "]"

    if nct_id:
        # Filter to a specific trial
        sql = text(
            """
            SELECT nct_id, title, eligibility_criteria, summary
            FROM trials
            WHERE nct_id = :nct_id
            LIMIT 4
            """
        )
        result = await db_session.execute(sql, {"nct_id": nct_id})
    else:
        # Retrieve top-4 most relevant trials by embedding similarity
        sql = text(
            """
            SELECT nct_id, title, eligibility_criteria, summary
            FROM trials
            WHERE embedding IS NOT NULL
            ORDER BY embedding <=> :query_vector::vector
            LIMIT 4
            """
        )
        result = await db_session.execute(sql, {"query_vector": vector_literal})

    rows = result.mappings().all()

    if not rows:
        return {
            "answer": "No relevant clinical trial information found to answer your question.",
            "source_trial_ids": [],
        }

    # Build context from retrieved trials
    context_parts = []
    source_ids = []
    for row in rows:
        nct = row["nct_id"]
        source_ids.append(nct)
        title = row["title"] or "Untitled"
        summary = (row["summary"] or "")[:600]
        eligibility = (row["eligibility_criteria"] or "")[:600]
        context_parts.append(
            f"Trial {nct} — {title}\nSummary: {summary}\nEligibility: {eligibility}"
        )

    context = "\n\n---\n\n".join(context_parts)

    llm = _get_llm()
    chain = LLMChain(llm=llm, prompt=RAG_PROMPT)
    answer = await chain.arun(context=context, question=question)

    return {"answer": answer.strip(), "source_trial_ids": source_ids}
