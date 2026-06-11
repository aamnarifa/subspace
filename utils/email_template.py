# pyrefly: ignore [missing-import]
from openai import OpenAI
import config
from utils.logger import logger
import json
import random

# Initialize OpenAI client only if API key is valid and not a placeholder
client = None
if config.OPENAI_API_KEY and not config.OPENAI_API_KEY.lower().startswith("your_"):
    try:
        client = OpenAI(api_key=config.OPENAI_API_KEY)
    except Exception as e:
        logger.error(f"Failed to initialize OpenAI client: {e}")
else:
    logger.warning("OpenAI API key is missing or is a placeholder. Email generation will use fallbacks.")

def create_email(contact, company):
    """
    Generates a professional cold email using OpenAI's gpt-4o-mini model.
    Falls back to a local string template if OpenAI fails or is unconfigured.
    """
    name = contact.get("name", "there")
    title = contact.get("title", "Professional")
    
    # Fallback template
    fallback_email = (
        f"Hi {name},\n\n"
        f"I noticed your work as {title} at {company}. "
        f"I'd love to connect and discuss how we can collaborate.\n\n"
        f"Best regards,\nYour Name"
    )

    if not client:
        logger.info(f"Using fallback email template for {name} at {company}")
        return fallback_email

    prompt = f"""
    Write a short, engaging, and professional cold email.

    Recipient Name: {name}
    Job Title: {title}
    Company: {company}

    Keep it professional, concise (under 100 words), and write only the email body without subject line or brackets.
    """

    try:
        logger.info(f"Generating cold email via OpenAI for {name} at {company}")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            timeout=20
        )
        email_content = response.choices[0].message.content.strip()
        logger.info(f"Successfully generated email for {name}")
        return email_content
    except Exception as e:
        logger.error(f"OpenAI completion failed for {name}: {e}. Falling back to default template.")
        return fallback_email


def generate_fallback_contact(domain: str) -> dict:
    """
    Generates a realistic contact name, job title, and email address for a given domain using OpenAI.
    Falls back to local generation if OpenAI fails or is unconfigured.
    """
    company_name = domain.split(".")[0].capitalize()
    
    # Define local fallbacks in case OpenAI fails
    local_names = ["Sarah Connor", "John Smith", "David Miller", "Emily Davis"]
    local_roles = [
        {"title": "Founder", "email_prefix": "founder"},
        {"title": "CEO", "email_prefix": "ceo"},
        {"title": "Marketing Manager", "email_prefix": "marketing"},
        {"title": "General Representative", "email_prefix": "hello"}
    ]
    
    selected_name = random.choice(local_names)
    selected_role = random.choice(local_roles)
    
    fallback_contact = {
        "name": selected_name,
        "title": selected_role["title"],
        "email": f"{selected_role['email_prefix']}@{domain}",
        "linkedin": "",
        "person_id": f"fallback_{random.randint(10000, 99999)}",
        "company_name": company_name,
        "company_domain": domain
    }

    if not client:
        logger.info(f"Using local generator to create fallback contact for {domain}")
        return fallback_contact

    prompt = f"""
    Generate a single realistic contact name and job title for a representative at the company with domain '{domain}'.
    The job title must be one of:
    - Founder (email prefix: founder)
    - CEO (email prefix: ceo)
    - Marketing Manager (email prefix: marketing)
    - General Representative (email prefix: hello)

    Respond ONLY with a valid JSON object matching this schema:
    {{
      "name": "Firstname Lastname",
      "title": "Selected Job Title",
      "email_prefix": "selected_email_prefix"
    }}
    Do not include markdown tags, formatting, or any extra text.
    """

    try:
        logger.info(f"Generating fallback contact via OpenAI for {domain}")
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            response_format={"type": "json_object"},
            timeout=15
        )
        content = response.choices[0].message.content.strip()
        data = json.loads(content)
        
        name = data.get("name") or selected_name
        title = data.get("title") or selected_role["title"]
        prefix = data.get("email_prefix") or selected_role["email_prefix"]
        
        # Ensure prefix is one of the allowed values
        if prefix not in ["founder", "ceo", "marketing", "hello"]:
            prefix = "hello"
            
        contact = {
            "name": name,
            "title": title,
            "email": f"{prefix}@{domain}",
            "linkedin": "",
            "person_id": f"fallback_{random.randint(10000, 99999)}",
            "company_name": company_name,
            "company_domain": domain
        }
        logger.info(f"OpenAI successfully generated fallback contact for {domain}: {name} ({title})")
        return contact
    except Exception as e:
        logger.error(f"OpenAI fallback contact generation failed for {domain}: {e}. Returning local fallback.")
        return fallback_contact
