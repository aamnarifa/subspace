# pyrefly: ignore [missing-import]
from openai import OpenAI
import config
from utils.logger import logger

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
