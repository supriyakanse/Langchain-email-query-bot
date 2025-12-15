import json
import os
from datetime import datetime

# Import the fetch_emails tool from agent_email_fetch
from agent_email_fetch import fetch_emails

# Import vector store building function from agent_email_vector
from agent_email_vector import build_vector_store

# Import configuration
from config import config


def run_email_workflow(start_date=None, end_date=None):
    """
    Orchestrates the email workflow:
    1. Fetches emails using the fetch_emails tool
    2. Builds a ChromaDB vector store from the fetched emails
    3. Returns the vector store for later use

    Args:
        start_date: Optional start date (YYYY-MM-DD), uses config if not provided
        end_date: Optional end date (YYYY-MM-DD), uses config if not provided

    Returns:
        ChromaDB vector store instance or None if no emails found

    Raises:
        ValueError: If configuration is invalid
        Exception: If email fetching or vector store creation fails
    """
    try:
        # Validate configuration
        config.validate()

        # Use provided dates or fall back to config
        start = start_date or config.START_DATE
        end = end_date or config.END_DATE

        print("=" * 50)
        print("EMAIL ASSISTANT - WORKFLOW")
        print("=" * 50)
        print(f"Email: {config.EMAIL_ID}")
        print(f"Date Range: {start} to {end}")
        print("=" * 50 + "\n")

        print("Step 1: Fetching emails...")

        # Directly invoke the fetch_emails tool
        # No need for agent pattern since we're just calling one tool directly
        result = fetch_emails.invoke(
            {
                "email_id": config.EMAIL_ID,
                "app_password": config.APP_PASSWORD,
                "start_date": start,
                "end_date": end,
            }
        )

        # Extract email list from result
        email_list = result.get("emails", [])

        if not email_list:
            print("⚠ No emails found in the specified date range")
            return None

        print(f"✓ Fetched {len(email_list)} emails")

        # email_list is already a list of dictionaries from the tool
        email_dicts = email_list

        # Save emails to JSON file for reference
        print("\nStep 1.5: Saving emails to JSON file...")
        data_dir = "data"
        os.makedirs(data_dir, exist_ok=True)

        # Create filename with date range
        filename = f"emails_{start}_{end}.json"
        filepath = os.path.join(data_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(
                {
                    "fetch_date": datetime.now().isoformat(),
                    "date_range": {"start": start, "end": end},
                    "email_count": len(email_dicts),
                    "emails": email_dicts,
                },
                f,
                indent=2,
                ensure_ascii=False,
            )

        print(f"✓ Saved {len(email_dicts)} emails to {filepath}")

        print("\nStep 2: Building ChromaDB vector store...")

        # Build the vector store from the emails
        vectorstore = build_vector_store(email_dicts)

        print(f"✓ Vector store created successfully")
        print(f"✓ Total documents in vector store: {vectorstore._collection.count()}")

        return vectorstore

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}")
        raise
    except Exception as e:
        print(f"\n❌ Workflow Error: {e}")
        raise
