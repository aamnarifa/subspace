import requests
from config import OCEAN_API_KEY, OCEAN_API_ENDPOINT
from utils.logger import logger
from utils.http_client import execute_request

# Common personal/free email domains and generic domains to filter out
LOW_QUALITY_DOMAINS = {
    "gmail.com", "yahoo.com", "hotmail.com", "outlook.com", "aol.com", "zoho.com", 
    "protonmail.com", "icloud.com", "mail.com", "yandex.com", "live.com", 
    "ocean.io", "example.com", "test.com"
}

def is_high_quality_domain(domain: str) -> bool:
    """
    Returns True if the domain is valid, non-empty, and not a known low-quality domain.
    """
    if not domain:
        return False
    domain = domain.strip().lower()
    
    # Check simple syntax rules
    if "." not in domain or len(domain) < 4:
        return False
        
    # Check against known low-quality domains
    if domain in LOW_QUALITY_DOMAINS:
        return False
        
    return True

def get_similar_companies(domain: str):
    """
    Fetch lookalike companies from Ocean.io using centralized http client.
    """
    if not OCEAN_API_KEY:
        logger.error("Ocean API key not configured.")
        return []

    logger.info(f"Searching Ocean.io for similar companies: {domain}")

    headers = {
        "x-api-token": OCEAN_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "size": 10,
        "companiesFilters": {
            "lookalikeDomains": [
                domain
            ]
        }
    }

    try:
        response = execute_request(
            method="POST",
            url=OCEAN_API_ENDPOINT,
            headers=headers,
            json_payload=payload,
            timeout=30
        )

        response.raise_for_status()
        data = response.json()

        companies = []
        raw_companies = data.get("companies", [])

        if raw_companies:
            logger.info(f"First Company Structure: {raw_companies[0]}")

        for item in raw_companies:
            try:
                company_data = item.get("company", {})
                domain_name = company_data.get("domain")

                if domain_name and isinstance(domain_name, str):
                    cleaned_domain = domain_name.strip()
                    if is_high_quality_domain(cleaned_domain):
                        companies.append(cleaned_domain)
                    else:
                        logger.info(f"Filtered out low-quality domain: {cleaned_domain}")
            except Exception as e:
                logger.warning(f"Skipping malformed company record: {e}")
                continue

        # Remove duplicates preserving order
        companies = list(dict.fromkeys(companies))

        logger.info(f"Found {len(companies)} high-quality companies: {companies}")
        return companies

    except requests.exceptions.HTTPError as e:
        logger.error(f"Ocean HTTP Error: {e}")
        return []
    except requests.exceptions.RequestException as e:
        logger.error(f"Ocean Request Error: {e}")
        return []
    except Exception as e:
        logger.error(f"Ocean Parsing Error: {e}")
        return []