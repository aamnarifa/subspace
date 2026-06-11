# pyrefly: ignore [missing-import]
from dotenv import load_dotenv
import os
from utils.exceptions import ConfigurationError

# ==============================================================================
# Load Environment Variables
# ==============================================================================

load_dotenv()

# ==============================================================================
# Environment Variable Sanitization
# ==============================================================================

for key in list(os.environ.keys()):

    value = os.environ[key]

    if value is not None:

        cleaned_key = key.strip()

        cleaned_value = value.strip()

        if len(cleaned_value) >= 2 and (
            (
                cleaned_value.startswith('"')
                and cleaned_value.endswith('"')
            )
            or
            (
                cleaned_value.startswith("'")
                and cleaned_value.endswith("'")
            )
        ):

            cleaned_value = cleaned_value[1:-1].strip()

        if cleaned_key != key:

            del os.environ[key]

        os.environ[cleaned_key] = cleaned_value

# ==============================================================================
# Logging Configuration
# ==============================================================================

LOG_LEVEL = os.getenv(
    "LOG_LEVEL",
    "INFO"
)

LOG_FILE = os.getenv(
    "LOG_FILE",
    "logs/run.log"
)

# ==============================================================================
# Pipeline Limits
# ==============================================================================

MAX_COMPANIES = int(
    os.getenv(
        "MAX_COMPANIES",
        "1"
    )
)

MAX_CREDIT_BUDGET = int(
    os.getenv(
        "MAX_CREDIT_BUDGET",
        "100"
    )
)

# ==============================================================================
# Retry / Throttling Settings
# ==============================================================================

ENRICH_MAX_RETRIES = int(
    os.getenv(
        "ENRICH_MAX_RETRIES",
        "3"
    )
)

ENRICH_BACKOFF_FACTOR = float(
    os.getenv(
        "ENRICH_BACKOFF_FACTOR",
        "2.0"
    )
)

ENRICH_THROTTLE_DELAY = float(
    os.getenv(
        "ENRICH_THROTTLE_DELAY",
        "1.0"
    )
)

# ==============================================================================
# API Keys
# ==============================================================================

OCEAN_API_KEY = os.getenv(
    "OCEAN_API_KEY"
)

PROSPEO_API_KEY = os.getenv(
    "PROSPEO_API_KEY"
)

APOLLO_API_KEY = os.getenv(
    "APOLLO_API_KEY"
)

BREVO_API_KEY = os.getenv(
    "BREVO_API_KEY"
)

OPENAI_API_KEY = os.getenv(
    "OPENAI_API_KEY"
)

# ==============================================================================
# API Endpoints
# ==============================================================================

OCEAN_API_ENDPOINT = os.getenv(
    "OCEAN_API_ENDPOINT",
    "https://api.ocean.io/v3/search/companies"
)

PROSPEO_API_ENDPOINT = os.getenv(
    "PROSPEO_API_ENDPOINT",
    "https://api.prospeo.io/search-person"
)

APOLLO_API_ENDPOINT = os.getenv(
    "APOLLO_API_ENDPOINT",
    "https://api.apollo.io/api/v1/mixed_people/api_search"
)

APOLLO_ENRICH_ENDPOINT = os.getenv(
    "APOLLO_ENRICH_ENDPOINT",
    "https://api.apollo.io/api/v1/people/match"
)

BREVO_API_ENDPOINT = os.getenv(
    "BREVO_API_ENDPOINT",
    "https://api.brevo.com/v3/smtp/email"
)

# ==============================================================================
# Sender Details
# ==============================================================================

SENDER_NAME = os.getenv(
    "SENDER_NAME",
    "Subspace Outreach Team"
)

SENDER_EMAIL = os.getenv(
    "SENDER_EMAIL",
    "contact@aamna-rifa.xyz"
)

# ==============================================================================
# Validation Helpers
# ==============================================================================

PLACEHOLDERS = {
    "your_ocean_api_key_here",
    "your_prospeo_api_key_here",
    "your_apollo_api_key_here",
    "your_brevo_api_key_here",
    "your_openai_api_key_here",
    "you@yourdomain.com",
    "outreach@yourdomain.com"
}


def is_valid_key(value):

    if not value:
        return False

    if value.lower() in PLACEHOLDERS:
        return False

    return True


# ==============================================================================
# Startup Validation
# ==============================================================================

errors = []

if not is_valid_key(OCEAN_API_KEY):

    errors.append(
        "OCEAN_API_KEY is missing."
    )

if not is_valid_key(BREVO_API_KEY):

    errors.append(
        "BREVO_API_KEY is missing."
    )

has_lead_provider = any([
    is_valid_key(PROSPEO_API_KEY),
    is_valid_key(APOLLO_API_KEY)
])

if not has_lead_provider:

    errors.append(
        "At least one provider must be configured "
        "(PROSPEO_API_KEY or APOLLO_API_KEY)."
    )

if errors:

    raise ConfigurationError(
        "\n".join(errors)
    )

# ==============================================================================
# Data Paths
# ==============================================================================

DATA_DIR = "data"
LOG_DIR = "logs"

LEADS_FILE = os.path.join(
    DATA_DIR,
    "leads.csv"
)

SENT_EMAILS_FILE = os.path.join(
    DATA_DIR,
    "sent_emails.json"
)

# ==============================================================================
# Create Required Folders
# ==============================================================================

os.makedirs(
    DATA_DIR,
    exist_ok=True
)

os.makedirs(
    LOG_DIR,
    exist_ok=True
)