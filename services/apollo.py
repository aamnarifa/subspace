import requests

import config

from utils.http_client import execute_request
from utils.logger import logger


def get_apollo_contacts(domain: str):
    """
    Search people at a company using Apollo People Search API.
    """
    if config.MOCK_MODE:
        logger.info(f"[MOCK] Simulating Apollo search for: {domain}")
        mock_contacts = [
            {
                "name": "Jane Miller",
                "title": "Operations Manager",
                "email": f"jane.miller@{domain}",
                "linkedin": "https://www.linkedin.com/in/janemiller-mock",
                "person_id": "apollo_11111",
                "company_domain": domain
            }
        ]
        logger.info(f"[MOCK] Apollo returned {len(mock_contacts)} mock contacts for {domain}")
        return mock_contacts

    if not config.APOLLO_API_KEY:

        logger.warning(
            "Apollo API key not configured."
        )

        return []

    logger.info(
        f"Apollo search started for {domain}"
    )

    headers = {
        "X-Api-Key": config.APOLLO_API_KEY,
        "Content-Type": "application/json",
        "Accept": "application/json"
    }

    payload = {
        "q_organization_domains_list": [
            domain
        ],
        "page": 1,
        "per_page": 25
    }

    try:

        response = execute_request(
            method="POST",
            url=config.APOLLO_API_ENDPOINT,
            headers=headers,
            json_payload=payload,
            timeout=30,
            max_retries=3,
            backoff_factor=2
        )

        response.raise_for_status()

        data = response.json()
        logger.info(f"Apollo Raw Response: {data}")

        people = (
            data.get("people")
            or data.get("data")
            or data.get("results")
            or []
        )

        contacts = []

        for person in people:

            full_name = (
                person.get("name")
                or (
                    f"{person.get('first_name', '')} "
                    f"{person.get('last_name', '')}"
                ).strip()
                or "Unknown"
            )

            contacts.append(
                {
                    "name": full_name,
                    "title": (
                        person.get("title")
                        or "Unknown"
                    ),
                    "email": (
                        person.get("email")
                        or ""
                    ),
                    "linkedin": (
                        person.get("linkedin_url")
                        or ""
                    ),
                    "person_id": (
                        person.get("id")
                        or ""
                    ),
                    "company_domain": domain
                }
            )

        logger.info(
            f"Apollo returned {len(contacts)} contacts for {domain}"
        )

        return contacts

    except requests.exceptions.Timeout as e:

        logger.error(
            f"Apollo timeout for {domain}: {e}"
        )

        return []

    except requests.exceptions.ConnectionError as e:

        logger.error(
            f"Apollo connection error for {domain}: {e}"
        )

        return []

    except requests.exceptions.HTTPError as e:

        logger.error(
            f"Apollo HTTP error for {domain}: {e}"
        )

        return []

    except ValueError as e:

        logger.error(
            f"Apollo JSON parse error for {domain}: {e}"
        )

        return []

    except Exception as e:

        logger.error(
            f"Apollo unexpected error for {domain}: {e}"
        )

        return []