import sys
from pipeline import run_pipeline, CreditBudgetExceededError
from utils.logger import logger
from services.brevo import send_email
from utils.email_template import create_email
from utils.credit_tracker import get_credit_tracker

def main():
    try:
        # User input domain
        domain = input("Enter company domain: ").strip()
        if not domain:
            print("Error: Domain cannot be empty.")
            sys.exit(1)

        # Execute local discovery pipeline (Stages 1-3)
        contacts = run_pipeline(domain)

        if not contacts:
            print("\nNo qualified contacts found. Exiting.")
            sys.exit(0)

        # [4/6] Stage: Review Safety Checkpoint
        print("\n" + "="*50)
        print(" [4/6] Stage: Safety Checkpoint & Review")
        print("="*50)

        # Extract stats
        unique_companies = list(set(c.get("company") for c in contacts if c.get("company")))
        total_contacts = len(contacts)
        
        # Retrieve actual credits consumed from global tracker
        tracker = get_credit_tracker()
        credits_used = tracker.get_consumed() if tracker else total_contacts

        print(f"Companies Discovered: {len(unique_companies)} ({', '.join(unique_companies)})")
        print(f"Contacts Discovered:  {total_contacts}")
        print(f"Actual Credits Used:  {credits_used}")
        print("\nTop Lead Matches:")
        
        # Display top leads (up to 10)
        for i, contact in enumerate(contacts[:10]):
            print(f"  {i+1}. {contact.get('name')} | {contact.get('title')} | {contact.get('email')} ({contact.get('company')}) - Score: {contact.get('score')}")

        # Prompt before dispatching
        choice = input("\nProceed with sending emails? (y/n): ").strip().lower()
        if choice != "y":
            print("\nOutreach aborted. Leads have been saved to CSV. Done.")
            logger.info("Email outreach aborted by user.")
            sys.exit(0)

        # [5/6] Stage: Sending Email Outreach
        print("\n" + "="*50)
        print(" [5/6] Stage: Sending Outreach Emails")
        print("="*50)

        emails_sent = 0
        emails_failed = 0

        for contact in contacts:
            recipient = contact.get("email")
            if not recipient:
                logger.warning(f"Skipping contact '{contact.get('name')}' (missing email)")
                continue

            print(f"Generating and sending email to {contact.get('name')} ({recipient})...")
            logger.info(f"Preparing email for {recipient}")
            
            body = create_email(contact, contact.get("company"))
            status = send_email(recipient, "Quick Question", body)

            if status in (200, 201):
                emails_sent += 1
                logger.info(f"Outreach email sent successfully to {recipient}")
            else:
                emails_failed += 1
                logger.error(f"Outreach email failed for {recipient} with status {status}")

        # [6/6] Stage: Complete & Summary
        print("\n" + "="*50)
        print(" [6/6] Stage: Campaign Complete")
        print("="*50)
        
        print("\nCampaign Summary:")
        print(f"  - Total companies processed: {len(unique_companies)}")
        print(f"  - Total contacts retrieved:  {total_contacts}")
        print(f"  - Successful emails sent:    {emails_sent}")
        print(f"  - Failed email attempts:     {emails_failed}")
        print(f"  - Credits consumed:          {credits_used}")
        print("\nAll logs written to logs/run.log. Done.")
        logger.info(f"Campaign complete. Sent: {emails_sent} | Failed: {emails_failed} | Credits: {credits_used}")

    except KeyboardInterrupt:
        print("\n\nProcess interrupted by user. Exiting.")
        sys.exit(0)
    except CreditBudgetExceededError as e:
        print(f"\nPipeline stopped: {e}")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"Unhandled exception in CLI runtime: {e}", exc_info=True)
        print(f"\nAn unexpected critical error occurred: {e}. See logs/run.log for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()