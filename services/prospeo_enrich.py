import requests
from config import PROSPEO_API_KEY, ENRICH_MAX_RETRIES, ENRICH_BACKOFF_FACTOR
from utils.logger import logger
from utils.http_client import execute_request
from utils.credit_tracker import get_credit_tracker

def enrich_person(person_id):
    """
    Enriches a person using Prospeo Enrich Person API.
    Uses centralized HTTP client and tracks credits.
    """
    import config
    if config.MOCK_MODE:
        logger.info(f"[MOCK] Simulating Prospeo enrichment for person_id: {person_id}")
        mock_email = "sarah.connor@mock-enterprise.com" if "12345" in person_id else "john.doe@mock-tech-labs.io"
        return {
            "error": False,
            "credits_spent": 1,
            "person": {
                "email": {
                    "email": mock_email,
                    "status": "valid"
                }
            }
        }

    url = "https://api.prospeo.io/enrich-person"
    if not PROSPEO_API_KEY:
        logger.error("Prospeo API key is not configured.")
        return {"error": True, "error_code": "API_KEY_MISSING", "message": "Prospeo API key is missing."}

    headers = {
        "X-KEY": PROSPEO_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "data": {
            "person_id": person_id
        }
    }

    try:
        response = execute_request(
            method="POST",
            url=url,
            headers=headers,
            json_payload=payload,
            timeout=30,
            max_retries=ENRICH_MAX_RETRIES,
            backoff_factor=ENRICH_BACKOFF_FACTOR
        )

        response.raise_for_status()
        data = response.json()

        # Track credit usage immediately
        credits_spent = data.get("credits_spent", 0)
        tracker = get_credit_tracker()
        if tracker:
            tracker.consume(credits_spent, f"Prospeo Enrich Person ({person_id})")

        return data

    except requests.exceptions.HTTPError as e:
        logger.error(f"Prospeo Enrich Person HTTP error for person_id {person_id}: {e}")
        return {"error": True, "error_code": "HTTP_ERROR", "message": str(e)}
    except requests.exceptions.RequestException as e:
        logger.error(f"Prospeo Enrich Person request error for person_id {person_id}: {e}")
        return {"error": True, "error_code": "REQUEST_FAILED", "message": str(e)}
    except Exception as e:
        logger.error(f"Prospeo Enrich Person parsing error for person_id {person_id}: {e}")
        return {"error": True, "error_code": "PARSING_ERROR", "message": str(e)}