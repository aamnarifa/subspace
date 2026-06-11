import os
import csv
from utils.logger import logger

def save_leads(contacts, filepath="data/leads.csv"):
    """
    Saves a list of contact dictionaries to a CSV file.
    Maps contact attributes to first_name, last_name, email, domain, title, linkedin, and score.
    """
    logger.info(f"Saving {len(contacts)} leads to {filepath}")
    
    # Ensure directory exists
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    
    # Define fields
    fields = ["first_name", "last_name", "email", "domain", "title", "linkedin", "score"]
    
    try:
        with open(filepath, mode="w", newline="", encoding="utf-8") as f:
            writer = csv.DictWriter(f, fieldnames=fields)
            writer.writeheader()
            
            for contact in contacts:
                # Split name into first and last name
                name = contact.get("name", "").strip()
                name_parts = name.split(" ", 1)
                first_name = name_parts[0]
                last_name = name_parts[1] if len(name_parts) > 1 else ""
                
                writer.writerow({
                    "first_name": first_name,
                    "last_name": last_name,
                    "email": contact.get("email", ""),
                    "domain": ( contact.get("company_domain")
                    or contact.get("company")
                    or ""),
                    "title": contact.get("title", ""),
                    "linkedin": contact.get("linkedin", ""),
                    "score": contact.get("score", 0)
                })
                
        logger.info(f"Successfully saved {len(contacts)} leads to {filepath}")
        return True
    except Exception as e:
        logger.error(f"Failed to save leads to CSV file: {e}")
        return False
