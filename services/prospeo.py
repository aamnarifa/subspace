import requests
from config import PROSPEO_API_KEY, PROSPEO_API_ENDPOINT, ENRICH_MAX_RETRIES, ENRICH_BACKOFF_FACTOR
from utils.logger import logger
from utils.http_client import execute_request
from utils.credit_tracker import get_credit_tracker

def get_contacts(domain):
    """
    Search people at a company using Prospeo Search Person API.
    Uses centralized HTTP client and tracks credits.
    """
    import config
    if config.MOCK_MODE:
        logger.info(f"[MOCK] Simulating Prospeo search for: {domain}")
        mock_contacts = [
            {
                "name": "Sarah Connor",
                "title": "Director of Operations",
                "linkedin": "https://www.linkedin.com/in/sarahconnor-mock",
                "person_id": "person_12345",
                "company_name": domain.split(".")[0].capitalize(),
                "company_domain": domain
            },
            {
                "name": "John Doe",
                "title": "Head of Engineering",
                "linkedin": "https://www.linkedin.com/in/johndoe-mock",
                "person_id": "person_67890",
                "company_name": domain.split(".")[0].capitalize(),
                "company_domain": domain
            }
        ]
        logger.info(f"[MOCK] Found {len(mock_contacts)} mock contacts for {domain}")
        return mock_contacts

    if not PROSPEO_API_KEY:
        logger.error("Prospeo API key is not configured.")
        return []

    logger.info(f"Retrieving Prospeo contacts for domain: {domain}")

    headers = {
        "X-KEY": PROSPEO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "page": 1,
        "filters": {
            "company": {
                "websites": {
                    "include": [
                        domain
                    ]
                }
            }
        }
    }

    try:
        response = execute_request(
            method="POST",
            url=PROSPEO_API_ENDPOINT,
            headers=headers,
            json_payload=payload,
            timeout=30,
            max_retries=ENRICH_MAX_RETRIES,
            backoff_factor=ENRICH_BACKOFF_FACTOR
        )

        try:
            data = response.json()
        except ValueError:
            data = {}

        if response.status_code == 400 and data.get("error_code") == "NO_RESULTS":
            logger.info(f"Prospeo returned no results for domain: {domain}")
            return []

        response.raise_for_status()

        print("\n========== PROSPEO RESPONSE ==========")
        print(data)
        print("======================================\n")

        credits_spent = data.get("credits_spent", 0)

        tracker = get_credit_tracker()

        if tracker:
            tracker.consume(
                credits_spent,
                f"Prospeo Search Person ({domain})"
            )

        contacts = []

        results = (
            data.get("results")
            or data.get("people")
            or data.get("data")
            or []
        )

        logger.info(f"Prospeo Results Found: {len(results)}")

        for item in results:

            person = item.get("person") or item
            company = item.get("company", {})

            first_name = person.get("first_name", "")
            last_name = person.get("last_name", "")

            full_name = (
                person.get("full_name")
                or f"{first_name} {last_name}".strip()
                or "Unknown"
            )

            title = (
                person.get("job_title")
                or person.get("title")
                or "Unknown"
            )

            linkedin = (
                person.get("linkedin_url")
                or person.get("linkedin")
                or ""
            )

            person_id = (
                person.get("person_id")
                or person.get("id")
                or ""
            )

            contacts.append(
                {
                    "name": full_name,
                    "title": title,
                    "linkedin": linkedin,
                    "person_id": person_id,
                    "company_name": company.get("name", ""),
                    "company_domain": company.get("domain", domain)
                }
            )

        logger.info(
            f"Retrieved {len(contacts)} contacts from {domain} via Prospeo"
        )

        return contacts

    except requests.exceptions.HTTPError as e:
        logger.warning(f"Prospeo unavailable for {domain}: HTTP error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.warning(f"Prospeo unavailable for {domain}: Request error: {e}")
        return []
    except Exception as e:
        logger.warning(f"Prospeo unavailable for {domain}: Unexpected error: {e}")
        return []