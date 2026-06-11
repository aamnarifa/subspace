import time
import requests
from utils.logger import logger

def execute_request(
    method: str,
    url: str,
    headers: dict = None,
    json_payload: dict = None,
    params: dict = None,
    timeout: int = 30,
    max_retries: int = 3,
    backoff_factor: float = 2.0
) -> requests.Response:
    """
    Executes an HTTP request with centralized logging, error handling, and robust retry logic.
    Retries only on:
    - Connection errors / Timeouts
    - HTTP 429 (Rate Limits)
    - HTTP 500+ (Server Errors)
    Never retries on:
    - HTTP 400, 401, 403, 404
    - NO_RESULTS responses
    """
    headers = headers or {}
    redacted_headers = {}
    for k, v in headers.items():
        if k.lower() in ("x-key", "api-key", "authorization", "x-api-token", "api-key"):
            redacted_headers[k] = "<REDACTED>"
        else:
            redacted_headers[k] = v

    last_exception = None
    for attempt in range(max_retries + 1):
        logger.info(f"API Request [{method.upper()}] URL: {url} | Attempt {attempt}/{max_retries}")
        logger.info(f"API Request Headers: {redacted_headers}")
        if json_payload is not None:
            logger.info(f"API Request Payload: {json_payload}")
        if params is not None:
            logger.info(f"API Request Params: {params}")

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                json=json_payload,
                params=params,
                timeout=timeout
            )

            status_code = response.status_code
            logger.info(f"API Response Status Code: {status_code}")
            logger.info(f"API Response Body: {response.text[:1000]}")

            if 200 <= status_code < 300:
                return response

            if status_code == 429 or status_code >= 500:
                if attempt < max_retries:
                    retry_after = response.headers.get("Retry-After")
                    try:
                        wait_time = float(retry_after) if retry_after else None
                    except ValueError:
                        wait_time = None

                    if wait_time is None or wait_time <= 0:
                        wait_time = backoff_factor * (2 ** attempt)

                    if wait_time > 15.0:
                        wait_time = 15.0

                    logger.warning(
                        f"Transient HTTP error ({status_code}). Retrying in {wait_time:.1f}s... "
                        f"(Attempt {attempt + 1}/{max_retries})"
                    )
                    time.sleep(wait_time)
                    continue
                else:
                    logger.error(f"HTTP error ({status_code}) persisted after {max_retries} retries.")
                    return response
            else:
                # Non-retryable error (e.g. 400, 401, 403, 404)
                logger.error(f"Non-retryable HTTP error status {status_code} received.")
                return response

        except (requests.exceptions.ConnectionError, requests.exceptions.Timeout) as e:
            last_exception = e
            if attempt < max_retries:
                wait_time = backoff_factor * (2 ** attempt)
                if wait_time > 15.0:
                    wait_time = 15.0
                logger.warning(
                    f"Connection or timeout error: {e}. Retrying in {wait_time:.1f}s... "
                    f"(Attempt {attempt + 1}/{max_retries})"
                )
                time.sleep(wait_time)
                continue
            else:
                logger.error(f"Network error persisted after {max_retries} retries: {e}")
                raise e
        except requests.exceptions.RequestException as e:
            logger.error(f"Requests request failed: {e}")
            raise e

    # Return dummy/empty response or raise if it shouldn't be reached
    raise requests.exceptions.RequestException("Max retries exceeded with errors.", request=None, response=None)
