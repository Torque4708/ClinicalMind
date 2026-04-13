import logging
from typing import List, Dict, Any, Optional
import requests

logger = logging.getLogger(__name__)

CLINICAL_TRIALS_API_BASE = "https://clinicaltrials.gov/api/v2/studies"


def _parse_study(study: Dict[str, Any]) -> Dict[str, Any]:
    """Parse a single study from ClinicalTrials.gov API v2 response."""
    protocol = study.get("protocolSection", {})
    identification = protocol.get("identificationModule", {})
    status_module = protocol.get("statusModule", {})
    description_module = protocol.get("descriptionModule", {})
    conditions_module = protocol.get("conditionsModule", {})
    interventions_module = protocol.get("armsInterventionsModule", {})
    eligibility_module = protocol.get("eligibilityModule", {})
    design_module = protocol.get("designModule", {})

    nct_id = identification.get("nctId", "")
    title = identification.get("briefTitle", "") or identification.get("officialTitle", "")
    status = status_module.get("overallStatus", "")
    phases = design_module.get("phases", [])
    phase = ", ".join(phases) if phases else "N/A"
    conditions = conditions_module.get("conditions", [])
    interventions_raw = interventions_module.get("interventions", [])
    interventions = [
        {"name": iv.get("name", ""), "type": iv.get("type", "")}
        for iv in interventions_raw
    ]
    eligibility_criteria = eligibility_module.get("eligibilityCriteria", "")
    summary = description_module.get("briefSummary", "")

    return {
        "nct_id": nct_id,
        "title": title,
        "status": status,
        "phase": phase,
        "conditions": conditions,
        "interventions": interventions,
        "eligibility_criteria": eligibility_criteria,
        "summary": summary,
    }


def fetch_recruiting_trials(
    page_size: int = 100,
    max_pages: int = 10,
    condition: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """
    Fetch RECRUITING trials from ClinicalTrials.gov v2 API.
    Handles pagination via nextPageToken.
    """
    trials = []
    params: Dict[str, Any] = {
        "pageSize": page_size,
        "filter.overallStatus": "RECRUITING",
        "format": "json",
    }
    if condition:
        params["query.cond"] = condition

    next_page_token: Optional[str] = None
    page_count = 0

    while page_count < max_pages:
        if next_page_token:
            params["pageToken"] = next_page_token
        elif "pageToken" in params:
            del params["pageToken"]

        try:
            response = requests.get(CLINICAL_TRIALS_API_BASE, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            logger.error(f"ClinicalTrials.gov API error: {e}")
            break

        studies = data.get("studies", [])
        for study in studies:
            parsed = _parse_study(study)
            if parsed["nct_id"]:
                trials.append(parsed)

        next_page_token = data.get("nextPageToken")
        page_count += 1
        logger.info(f"Fetched page {page_count}, total trials so far: {len(trials)}")

        if not next_page_token:
            break

    return trials


def fetch_trial_by_nct_id(nct_id: str) -> Optional[Dict[str, Any]]:
    """Fetch a single trial by NCT ID."""
    url = f"{CLINICAL_TRIALS_API_BASE}/{nct_id}"
    try:
        response = requests.get(url, timeout=15)
        response.raise_for_status()
        study = response.json()
        return _parse_study(study)
    except requests.RequestException as e:
        logger.error(f"Failed to fetch trial {nct_id}: {e}")
        return None


def search_trials_by_keyword(keyword: str, page_size: int = 10) -> List[Dict[str, Any]]:
    """Search trials by keyword using query.term param."""
    params = {
        "query.term": keyword,
        "pageSize": page_size,
        "format": "json",
    }
    try:
        response = requests.get(CLINICAL_TRIALS_API_BASE, params=params, timeout=15)
        response.raise_for_status()
        data = response.json()
        return [_parse_study(s) for s in data.get("studies", []) if s]
    except requests.RequestException as e:
        logger.error(f"Keyword search failed: {e}")
        return []
