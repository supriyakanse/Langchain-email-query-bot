#!/usr/bin/env python3
"""
Email Assistant - Main CLI Application

This is the main entry point for the Email Assistant system.
It orchestrates the complete workflow: fetch → vector store → query
"""

import argparse
import os
import sys
from datetime import datetime

from agent_email_query import SimpleConversationMemory, load_vector_store, query_emails
from agent_email_workflow import run_email_workflow
from config import config


def print_banner():
    """Print application banner."""
    print("\n" + "=" * 60)
    print("           EMAIL ASSISTANT - AI-Powered Email Query")
    print("=" * 60 + "\n")


def check_vector_store_exists():
    """Check if vector store exists."""
    return os.path.exists(config.CHROMA_PERSIST_DIRECTORY) and os.path.isdir(
        config.CHROMA_PERSIST_DIRECTORY
    )


def get_vector_store_info():
    """Get information about the existing vector store."""
    try:
        vectorstore = load_vector_store()
        count = vectorstore._collection.count()
        return count
    except Exception as e:
        return None


def cmd_status():
    """Display status of the email assistant system."""
    print_banner()
    print("System Status:")
    print("-" * 60)

    # Check configuration
    try:
        config.validate()
        print("✓ Configuration: Valid")
        print(f"  - Email: {config.EMAIL_ID}")
        print(f"  - Date Range: {config.START_DATE} to {config.END_DATE}")
    except ValueError as e:
        print(f"✗ Configuration: Invalid")
        print(f"  Error: {e}")
        return

    # Check vector store
    if check_vector_store_exists():
        count = get_vector_store_info()
        if count is not None:
            print(f"✓ Vector Store: Ready")
            print(f"  - Location: {config.CHROMA_PERSIST_DIRECTORY}")
            print(f"  - Total Emails: {count}")
        else:
            print(f"✗ Vector Store: Error loading")
    else:
        print(f"✗ Vector Store: Not found")
        print(f"  Run 'python email_assistant.py refresh' to fetch and index emails")

    print("-" * 60 + "\n")


def cmd_refresh(start_date=None, end_date=None):
    """Fetch fresh emails and rebuild vector store."""
    print_banner()

    try:
        # Validate configuration
        config.validate()

        # Run the workflow
        vectorstore = run_email_workflow(start_date, end_date)

        if vectorstore:
            print("\n" + "=" * 60)
            print("✓ Email refresh completed successfully!")
            print(f"✓ Total emails indexed: {vectorstore._collection.count()}")
            print("=" * 60 + "\n")
            print("You can now query your emails using:")
            print("  python email_assistant.py query")
            print()
        else:
            print("\n" + "=" * 60)
            print("⚠ No emails found in the specified date range")
            print("=" * 60 + "\n")

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}\n")
        print("Please check your .env file and ensure all required fields are set.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


def cmd_query(interactive=True, question=None):
    """Query the email vector store."""
    print_banner()

    try:
        # Check if vector store exists
        if not check_vector_store_exists():
            print("❌ Vector store not found!\n")
            print("Please run the following command first:")
            print("  python email_assistant.py refresh\n")
            sys.exit(1)

        # Load the vector store
        print("Loading vector store...")
        vectorstore = load_vector_store()
        count = vectorstore._collection.count()
        print(f"✓ Loaded {count} emails\n")

        if not interactive and question:
            # Single query mode (no memory for single queries)
            print(f"Question: {question}\n")
            print("Searching and generating response...\n")
            response = query_emails(vectorstore, question)
            print(f"Answer: {response}\n")
            return

        # Interactive mode with memory
        print("=" * 60)
        print("INTERACTIVE QUERY MODE")
        print("=" * 60)

        # Initialize memory for this session
        memory = SimpleConversationMemory()

        # Example queries
        example_queries = [
            "How many emails did I receive?",
            "Summarize my emails",
            "Did I receive any important emails?",
            "List all senders",
        ]

        print("\nExample queries you can try:")
        for i, q in enumerate(example_queries, 1):
            print(f"  {i}. {q}")

        print("\n" + "=" * 60 + "\n")

        # Interactive query loop
        while True:
            try:
                user_input = input(
                    "Ask a question about your emails (or 'quit' to exit): "
                ).strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!\n")
                    break

                if not user_input:
                    continue

                print("\nSearching and generating response...\n")
                response = query_emails(vectorstore, user_input, memory=memory)
                print(f"Answer: {response}\n")
                print("-" * 60 + "\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye!\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
                print("-" * 60 + "\n")

    except FileNotFoundError as e:
        print(f"\n❌ {e}\n")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


def cmd_workflow():
    """Run the complete workflow: fetch → vector → query."""
    print_banner()
    print("Running complete workflow: Fetch → Index → Query\n")

    try:
        # Step 1: Fetch and index emails
        print("Phase 1: Fetching and indexing emails")
        print("-" * 60)
        vectorstore = run_email_workflow()

        if not vectorstore:
            print("\n⚠ No emails found. Cannot proceed to query phase.\n")
            sys.exit(0)

        print("\n" + "=" * 60)
        print("Phase 2: Interactive Query Mode")
        print("=" * 60 + "\n")

        # Step 2: Query mode
        count = vectorstore._collection.count()
        print(f"✓ Ready to query {count} emails\n")

        # Initialize memory for this session
        memory = SimpleConversationMemory()

        # Example queries
        example_queries = [
            "How many emails did I receive?",
            "Summarize my emails",
            "Did I receive any important emails?",
            "List all senders",
        ]

        print("Example queries you can try:")
        for i, q in enumerate(example_queries, 1):
            print(f"  {i}. {q}")

        print("\n" + "=" * 60 + "\n")

        # Interactive query loop
        while True:
            try:
                user_input = input(
                    "Ask a question about your emails (or 'quit' to exit): "
                ).strip()

                if user_input.lower() in ["quit", "exit", "q"]:
                    print("\nGoodbye!\n")
                    break

                if not user_input:
                    continue

                print("\nSearching and generating response...\n")
                response = query_emails(vectorstore, user_input, memory=memory)
                print(f"Answer: {response}\n")
                print("-" * 60 + "\n")

            except KeyboardInterrupt:
                print("\n\nGoodbye!\n")
                break
            except Exception as e:
                print(f"❌ Error: {e}\n")
                print("-" * 60 + "\n")

    except ValueError as e:
        print(f"\n❌ Configuration Error: {e}\n")
        print("Please check your .env file and ensure all required fields are set.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}\n")
        sys.exit(1)


def main():
    """Main entry point for the Email Assistant CLI."""
    parser = argparse.ArgumentParser(
        description="Email Assistant - AI-Powered Email Query System",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Check system status
  python email_assistant.py status

  # Fetch and index emails (use dates from .env)
  python email_assistant.py refresh

  # Fetch emails for custom date range
  python email_assistant.py refresh --start 2025-11-01 --end 2025-11-28

  # Query emails interactively
  python email_assistant.py query

  # Query with a single question
  python email_assistant.py query --question "Summarize my emails"

  # Run complete workflow (fetch + query)
  python email_assistant.py workflow
        """,
    )

    parser.add_argument(
        "command",
        choices=["status", "refresh", "query", "workflow"],
        help="Command to execute",
    )

    parser.add_argument(
        "--start",
        type=str,
        help="Start date for email fetching (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--end",
        type=str,
        help="End date for email fetching (YYYY-MM-DD)",
    )

    parser.add_argument(
        "--question",
        "-q",
        type=str,
        help="Single question to ask (non-interactive mode)",
    )

    args = parser.parse_args()

    # Validate date format if provided
    if args.start:
        try:
            datetime.strptime(args.start, "%Y-%m-%d")
        except ValueError:
            print("❌ Invalid start date format. Use YYYY-MM-DD\n")
            sys.exit(1)

    if args.end:
        try:
            datetime.strptime(args.end, "%Y-%m-%d")
        except ValueError:
            print("❌ Invalid end date format. Use YYYY-MM-DD\n")
            sys.exit(1)

    # Execute command
    if args.command == "status":
        cmd_status()
    elif args.command == "refresh":
        cmd_refresh(args.start, args.end)
    elif args.command == "query":
        cmd_query(interactive=(not args.question), question=args.question)
    elif args.command == "workflow":
        cmd_workflow()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\nInterrupted by user. Goodbye!\n")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Unexpected error: {e}\n")
        sys.exit(1)
