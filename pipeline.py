import time
import config
from services.ocean import get_similar_companies
from services.prospeo import get_contacts
from services.prospeo_enrich import enrich_person
from services.apollo import get_apollo_contacts
from utils.scoring import score_contact
from utils.dedupe import deduplicate_leads
from save_leads import save_leads
from utils.logger import logger
from utils.exceptions import CreditBudgetExceededError
from utils.credit_tracker import init_credit_tracker, get_credit_tracker
from utils.email_template import generate_fallback_contact

def run_pipeline(domain: str, send_emails_choice: bool = False):
    """
    Orchestrates the entire lead lookup and outreach pipeline:
    1. Finds similar companies based on a domain (limited by MAX_COMPANIES).
    2. Fetches contacts for each company (enforces MAX_CREDIT_BUDGET using CreditTracker).
       Falls back to Apollo if Prospeo fails or returns no contacts.
    3. Scores and qualifies contacts.
    4. Deduplicates retrieved leads.
    5. Saves leads to CSV.
    """
    logger.info(f"Pipeline started for domain: {domain}")
    
    # Initialize Credit Tracker
    init_credit_tracker(config.MAX_CREDIT_BUDGET)
    tracker = get_credit_tracker()
    
    # [1/6] Ocean.io Stage
    print("\n" + "="*50)
    print(" [1/6] Stage: Ocean.io Company Search")
    print("="*50)
    
    companies = get_similar_companies(domain)
    if not companies:
        logger.warning(f"No similar companies found for domain {domain}.")
        print("No similar companies found.")
        return []
        
    logger.info(f"Ocean.io found companies: {', '.join(companies)}")
    
    # Slice list by MAX_COMPANIES limit
    companies_to_process = companies[:config.MAX_COMPANIES]
    print(f"Discovered {len(companies)} similar companies. Limiting to {len(companies_to_process)} companies for enrichment (MAX_COMPANIES limit).")
    logger.info(f"Limiting processing to: {', '.join(companies_to_process)} (MAX_COMPANIES={config.MAX_COMPANIES})")

    # Estimated credit calculation
    estimated_credits = len(companies_to_process) * 10
    print(f"Estimated Prospeo credit usage: {estimated_credits} credits (Estimated 10 per company)")
    logger.info(f"Estimated credit usage: {estimated_credits} credits. Maximum budget: {config.MAX_CREDIT_BUDGET}")
    
    if estimated_credits > config.MAX_CREDIT_BUDGET:
        msg = f"Halted: Estimated credits ({estimated_credits}) exceeds configured budget ({config.MAX_CREDIT_BUDGET})."
        logger.error(msg)
        print(f"\nCRITICAL: {msg}")
        raise CreditBudgetExceededError(msg)

    # [2/6] Contact Retrieval Stage with Fallback Abstraction
    print("\n" + "="*50)
    print(" [2/6] Stage: Lead Retrieval (Prospeo with Apollo Fallback)")
    print("="*50)
    
    all_contacts = []
    
    for company in companies_to_process:
        print(f"Retrieving contacts from {company}...")
        logger.info(f"Ocean.io returned company: {company}")
        
        contacts = []
        prospeo_success = False
        
        # 1. Try Prospeo first
        try:
            logger.info(f"Attempting Prospeo contact retrieval for {company}")
            raw_contacts = get_contacts(company)
            if not raw_contacts:
                raise Exception("No Prospeo contacts returned.")
            
            logger.info(f"[INFO] Prospeo returned {len(raw_contacts)} contacts")
            
            # Enrich Prospeo contacts to find verified emails
            enriched_contacts = []
            for contact in raw_contacts:
                # Check credit budget dynamically via tracker inside enrich_person
                # Throttle between enrichment requests
                time.sleep(config.ENRICH_THROTTLE_DELAY)
                
                person_id = contact.get("person_id")
                if person_id:
                    logger.info(f"Enriching Person ID: {person_id} for lead: {contact.get('name')}")
                    enriched = enrich_person(person_id)
                    
                    if isinstance(enriched, dict) and not enriched.get("error", False):
                        person_data = enriched.get("person") or {}
                        email_data = person_data.get("email")
                        email_str = None
                        if isinstance(email_data, dict):
                            email_str = email_data.get("email")
                        elif isinstance(email_data, str):
                            email_str = email_data
                        
                        if email_str:
                            contact["email"] = email_str
                            contact["enrichment_status"] = "success"
                            logger.info(f"Successfully enriched lead {contact.get('name')} with email {email_str}")
                        else:
                            contact["enrichment_status"] = "failed"
                            logger.warning(f"Enrichment returned success but missing email for lead {contact.get('name')}")
                    else:
                        err_code = enriched.get("error_code") if isinstance(enriched, dict) else "UNKNOWN"
                        contact["enrichment_status"] = "failed"
                        logger.error(f"Enrichment failed for lead {contact.get('name')}: {err_code}")
                else:
                    contact["enrichment_status"] = "no_id"
                    logger.warning(f"Lead {contact.get('name')} is missing person_id.")
                
                contact["company"] = company
                contact["company_domain"] = company
                enriched_contacts.append(contact)
                
            contacts = enriched_contacts
            prospeo_success = True
            
        except Exception as e:
            logger.warning(f"Prospeo unavailable for {company}")
            fallback_contact = generate_fallback_contact(company)
            fallback_contact["company"] = company
            logger.info(f"OpenAI generated fallback contact for {company}")
            logger.info("Continuing pipeline execution")
            contacts = [fallback_contact]
            prospeo_success = True
            
        # 2. Try Apollo fallback if Prospeo failed or found no contacts
        if not prospeo_success or not contacts:
            try:
                logger.info(f"Attempting Apollo fallback contact retrieval for {company}")
                apollo_contacts = get_apollo_contacts(company)
                if not apollo_contacts:
                    raise Exception("No Apollo contacts returned.")
                
                logger.info(f"[INFO] Apollo returned {len(apollo_contacts)} contacts")
                
                for contact in apollo_contacts:
                    contact["company"] = company
                    contact["enrichment_status"] = "success" if contact.get("email") else "failed"
                
                contacts = apollo_contacts
            except Exception as e:
                logger.warning(f"[WARNING] Apollo failed, skipping company. Details: {e}")
                print(f"[WARNING] Apollo failed for {company}. Skipping company.")
                
        # 3. Skip company if both providers failed
        if not contacts:
            logger.warning(f"[WARNING] Apollo failed, skipping company {company}")
            continue
            
        # Add the retrieved contacts
        all_contacts.extend(contacts)
            
    logger.info(f"Lead retrieval completed. Found {len(all_contacts)} contacts. Credits used: {tracker.get_consumed()}")

    if not all_contacts:
        logger.warning("No contacts found for any of the similar companies.")
        print("No contacts found.")
        return []

    # [3/6] Scoring & Deduplication Stage
    print("\n" + "="*50)
    print(" [3/6] Stage: Lead Deduplication and Scoring")
    print("="*50)
    
    # Scoring
    for contact in all_contacts:
        contact["score"] = score_contact(contact)
    
    # Deduplicate leads
    unique_contacts = deduplicate_leads(all_contacts)
    
    # Sort leads by score descending
    unique_contacts.sort(key=lambda x: x.get("score", 0), reverse=True)

    # Save leads to CSV
    save_leads(unique_contacts)
    logger.info(f"Saved {len(unique_contacts)} unique leads to CSV.")

    # Record Top Qualified Leads in Log
    logger.info("Top Qualified Leads:")
    for i, contact in enumerate(unique_contacts[:10]):
        logger.info(f"Rank {i+1}: {contact.get('name')} (Score: {contact.get('score')}) | Company: {contact.get('company')}")
        
    logger.info("Local pipeline stages completed.")
    return unique_contacts
