import json
import logging
from typing import Any, Dict
from langchain_groq import ChatGroq
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from backend.config import settings

logger = logging.getLogger(__name__)

ENTITY_EXTRACTION_PROMPT = PromptTemplate(
    input_variables=["description"],
    template="""You are a medical entity extraction AI. Extract structured medical information from the patient description below.

Return ONLY a valid JSON object with exactly these keys:
{{
  "diagnosis": "primary diagnosis or condition (string)",
  "age": "patient age or age range (string or null)",
  "gender": "patient gender (string or null)",
  "prior_treatments": ["list of prior treatments or medications"],
  "exclusion_factors": ["list of factors that might exclude from trials"]
}}

Patient Description:
{description}

JSON Response:""",
)


def _get_llm() -> ChatGroq:
    return ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name="llama3-70b-8192",
        temperature=0.0,
    )


async def extract_entities(description: str) -> Dict[str, Any]:
    """Extract structured medical entities from raw patient description."""
    try:
        llm = _get_llm()
        chain = LLMChain(llm=llm, prompt=ENTITY_EXTRACTION_PROMPT)
        result = await chain.arun(description=description)
        # Clean the result - remove markdown code blocks if present
        cleaned = result.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            cleaned = "\n".join(lines[1:-1]) if lines[-1].strip() == "```" else "\n".join(lines[1:])
        entities = json.loads(cleaned)
        return entities
    except json.JSONDecodeError as e:
        logger.error(f"Failed to parse entity extraction JSON: {e}. Raw: {result}")
        return {
            "diagnosis": description[:100],
            "age": None,
            "gender": None,
            "prior_treatments": [],
            "exclusion_factors": [],
        }
    except Exception as e:
        logger.error(f"Entity extraction failed: {e}")
        return {
            "diagnosis": description[:100],
            "age": None,
            "gender": None,
            "prior_treatments": [],
            "exclusion_factors": [],
        }
