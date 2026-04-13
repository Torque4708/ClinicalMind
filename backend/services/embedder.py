import logging
from typing import List
from sentence_transformers import SentenceTransformer

logger = logging.getLogger(__name__)

_model: SentenceTransformer = None


def _get_model() -> SentenceTransformer:
    global _model
    if _model is None:
        logger.info("Loading sentence-transformers model (all-MiniLM-L6-v2)...")
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        logger.info("Model loaded.")
    return _model


def embed_text(text: str) -> List[float]:
    """Embed a single text string, returns list of 384 floats."""
    model = _get_model()
    embedding = model.encode(text, normalize_embeddings=True)
    return embedding.tolist()


def embed_batch(texts: List[str]) -> List[List[float]]:
    """Embed a batch of texts, returns list of 384-dim vectors."""
    model = _get_model()
    embeddings = model.encode(texts, normalize_embeddings=True, batch_size=32, show_progress_bar=False)
    return [e.tolist() for e in embeddings]


def build_trial_text(trial_dict: dict) -> str:
    """Combine trial fields into a single text for embedding."""
    parts = []
    if trial_dict.get("title"):
        parts.append(f"Title: {trial_dict['title']}")
    conditions = trial_dict.get("conditions", [])
    if conditions:
        cond_str = ", ".join(str(c) for c in conditions)
        parts.append(f"Conditions: {cond_str}")
    if trial_dict.get("eligibility_criteria"):
        criteria = trial_dict["eligibility_criteria"][:1000]  # truncate for embedding
        parts.append(f"Eligibility: {criteria}")
    if trial_dict.get("summary"):
        parts.append(f"Summary: {trial_dict['summary'][:500]}")
    return " | ".join(parts)
