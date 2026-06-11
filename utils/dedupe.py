import re
from typing import List, Dict, Any
from utils.logger import logger

# Simple regex checking for a basic 'name@domain.ext' structure
EMAIL_REGEX = re.compile(r"^[^@]+@[^@]+\.[^@]+$")

def deduplicate_leads(leads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Deduplicates a list of leads based on unique email addresses as primary key.
    If enrichment was rate limited or failed, preserves the lead but deduplicates
    based on person_id or name/linkedin.
    """
    before_count = len(leads)
    seen_emails = set()
    seen_identifiers = set()
    unique_leads = []
    
    for lead in leads:
        name = lead.get("name") or "Unknown"
        person_id = lead.get("person_id") or ""
        linkedin = lead.get("linkedin") or ""
        status = lead.get("enrichment_status") or "unknown"
        email = lead.get("email")
        
        # Check if the lead is truly unusable
        if not email and name == "Unknown" and not person_id and not linkedin:
            logger.info("Filtered out lead - Truly unusable (no name, email, person_id, or linkedin).")
            continue
            
        if not email:
            # If enrichment failed or was rate limited, keep the lead
            if status in ("failed", "rate_limited", "no_id", "unknown"):
                # Deduplicate by identifier
                identifier = person_id or linkedin or name
                if identifier in seen_identifiers:
                    logger.info(f"Duplicate lead skipped (no email, matched by identifier): {identifier}")
                    continue
                seen_identifiers.add(identifier)
                unique_leads.append(lead)
            else:
                logger.info(f"Filtered out lead '{name}' - Missing email address with status '{status}'.")
            continue
            
        email = email.strip().lower()
        
        # Syntax check
        if not EMAIL_REGEX.match(email):
            logger.info(f"Filtered out lead '{name}' - Invalid email address format: {email}")
            continue
            
        # Deduplication check
        if email in seen_emails:
            logger.info(f"Duplicate email skipped: {email}")
            continue
            
        seen_emails.add(email)
        # Normalize email in dict
        lead["email"] = email
        unique_leads.append(lead)
        
    after_count = len(unique_leads)
    
    print(f"Before Deduplication: {before_count}")
    print(f"After Deduplication: {after_count}")
    
    logger.info(f"Deduplication finished. Before Deduplication: {before_count} | After Deduplication: {after_count}")
    return unique_leads

