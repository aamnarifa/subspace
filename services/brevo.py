import requests
from config import (
    BREVO_API_KEY,
    BREVO_API_ENDPOINT,
    SENDER_NAME,
    SENDER_EMAIL
)
from utils.logger import logger
from utils.http_client import execute_request

def send_email(
    recipient_email,
    subject,
    body
):
    """
    Send an email using the Brevo Transactional Email API via the centralized HTTP client.

    Returns:
        int | None
            HTTP status code on success/failure.
            None if request could not be completed.
    """
    import config
    if config.MOCK_MODE:
        logger.info(f"[MOCK] Simulating sending outreach email to {recipient_email} with subject '{subject}'")
        return 201

    if not BREVO_API_KEY:
        logger.error("Brevo API key is not configured.")
        return None

    logger.info(f"Sending outreach email to {recipient_email} with subject '{subject}'")

    headers = {
        "accept": "application/json",
        "api-key": BREVO_API_KEY,
        "content-type": "application/json"
    }

    payload = {
        "sender": {
            "name": SENDER_NAME,
            "email": SENDER_EMAIL
        },
        "to": [
            {
                "email": recipient_email
            }
        ],
        "subject": subject,
        "htmlContent": body
    }

    logger.info(f"Brevo Endpoint: {BREVO_API_ENDPOINT}")
    logger.info(f"Sender: {SENDER_EMAIL}")
    logger.info(f"Recipient: {recipient_email}")
    logger.info(f"Subject: {subject}")

    try:
        response = execute_request(
            method="POST",
            url=BREVO_API_ENDPOINT,
            headers=headers,
            json_payload=payload,
            timeout=30,
            max_retries=3,  # Transient retries for transactional email sending
            backoff_factor=2.0
        )

        status_code = response.status_code
        logger.info(f"Brevo Status Code: {status_code}")

        if status_code in (200, 201):
            logger.info(f"Email successfully sent to {recipient_email}")
            return status_code
        elif status_code == 400:
            logger.error("Brevo rejected the payload. Check sender, recipient, subject, and HTML content.")
        elif status_code == 401:
            logger.error("Brevo API key is invalid.")
        elif status_code == 403:
            logger.error("Sender email is not verified in Brevo or transactional limits reached.")
        elif status_code == 429:
            logger.error("Brevo rate limit exceeded.")
        else:
            logger.error(f"Brevo returned unexpected status code: {status_code}")

        return status_code

    except (requests.exceptions.Timeout, requests.exceptions.ConnectionError) as e:
        logger.error(f"Brevo connection/timeout error: {e}")
        return None
    except requests.exceptions.RequestException as e:
        logger.error(f"Brevo request failed: {e}")
        return None
    except Exception as e:
        logger.error(f"Unexpected Brevo error: {e}")
        return None