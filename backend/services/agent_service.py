import json
import logging
from typing import Any, Dict, Optional
from langchain_groq import ChatGroq
from langchain.agents import AgentExecutor, create_tool_calling_agent
from langchain.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain.tools import tool
from backend.config import settings
from backend.services.trial_fetcher import (
    fetch_trial_by_nct_id,
    search_trials_by_keyword,
)

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = """You are a clinical trial eligibility expert AI assistant.
Your job is to help patients and doctors understand clinical trial eligibility.
Use the available tools to search for trials, get trial details, and assess eligibility.
Always be accurate, compassionate, and clear in your explanations.
When checking eligibility, look at inclusion/exclusion criteria carefully."""


@tool
def search_trials_tool(keyword: str) -> str:
    """Search for clinical trials by a medical keyword or condition name."""
    trials = search_trials_by_keyword(keyword, page_size=5)
    if not trials:
        return "No trials found for the given keyword."
    results = []
    for t in trials[:5]:
        results.append(
            f"NCT ID: {t['nct_id']} | Title: {t['title']} | Status: {t['status']} | Phase: {t['phase']}"
        )
    return "\n".join(results)


@tool
def get_trial_details_tool(nct_id: str) -> str:
    """Get the full details of a clinical trial by its NCT ID (e.g., NCT04292899)."""
    trial = fetch_trial_by_nct_id(nct_id)
    if not trial:
        return f"Trial {nct_id} not found."
    return (
        f"NCT ID: {trial['nct_id']}\n"
        f"Title: {trial['title']}\n"
        f"Status: {trial['status']}\n"
        f"Phase: {trial['phase']}\n"
        f"Conditions: {', '.join(trial['conditions'])}\n"
        f"Summary: {(trial['summary'] or '')[:500]}\n"
        f"Eligibility Criteria:\n{(trial['eligibility_criteria'] or '')[:1000]}"
    )


@tool
def check_eligibility_tool(input_json: str) -> str:
    """
    Check if a patient is eligible for a trial.
    Input must be a JSON string with keys:
    'patient_entities' (dict with diagnosis, age, gender, prior_treatments, exclusion_factors)
    and 'nct_id' (string).
    Returns ELIGIBLE, PARTIALLY_ELIGIBLE, or NOT_ELIGIBLE with reasons.
    """
    try:
        data = json.loads(input_json)
        nct_id = data.get("nct_id")
        entities = data.get("patient_entities", {})
    except (json.JSONDecodeError, KeyError) as e:
        return f"Invalid input JSON: {e}"

    trial = fetch_trial_by_nct_id(nct_id)
    if not trial:
        return f"Trial {nct_id} not found."

    criteria = trial.get("eligibility_criteria", "") or ""
    diagnosis = entities.get("diagnosis", "unknown")
    age = entities.get("age", "unknown")
    gender = entities.get("gender", "unknown")
    prior_treatments = entities.get("prior_treatments", [])
    exclusion_factors = entities.get("exclusion_factors", [])

    analysis = (
        f"Patient Profile:\n"
        f"- Diagnosis: {diagnosis}\n"
        f"- Age: {age}\n"
        f"- Gender: {gender}\n"
        f"- Prior Treatments: {', '.join(str(p) for p in prior_treatments)}\n"
        f"- Potential Exclusion Factors: {', '.join(str(e) for e in exclusion_factors)}\n\n"
        f"Trial Eligibility Criteria (excerpt):\n{criteria[:1500]}\n\n"
        f"Based on this comparison, provide a preliminary eligibility assessment."
    )
    return analysis


def _get_agent_executor() -> AgentExecutor:
    llm = ChatGroq(
        api_key=settings.GROQ_API_KEY,
        model_name="llama3-70b-8192",
        temperature=0.0,
    )
    tools = [search_trials_tool, get_trial_details_tool, check_eligibility_tool]
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", SYSTEM_PROMPT),
            MessagesPlaceholder(variable_name="chat_history", optional=True),
            ("human", "{input}"),
            MessagesPlaceholder(variable_name="agent_scratchpad"),
        ]
    )
    agent = create_tool_calling_agent(llm, tools, prompt)
    return AgentExecutor(agent=agent, tools=tools, verbose=True, max_iterations=6)


async def run_eligibility_agent(
    question: str,
    patient_entities: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Run the LangChain agent to answer eligibility questions."""
    executor = _get_agent_executor()
    full_input = question
    if patient_entities:
        patient_str = json.dumps(patient_entities)
        full_input = f"Patient profile: {patient_str}\n\nQuestion: {question}"
    try:
        result = await executor.ainvoke({"input": full_input})
        return {
            "answer": result.get("output", ""),
            "intermediate_steps": len(result.get("intermediate_steps", [])),
        }
    except Exception as e:
        logger.error(f"Agent execution failed: {e}")
        return {"answer": f"Agent error: {str(e)}", "intermediate_steps": 0}
