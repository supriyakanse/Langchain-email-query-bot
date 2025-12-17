# Email Assistant — AI-Powered Email Query

An CLI tool that fetches your Gmail messages, builds a Chroma vector store, and lets you query your emails using an LLM (Ollama or Google Gemini).

✅ Features
- Fetch emails from Gmail (IMAP) within a date range
- Clean and normalize email bodies 
- Index emails into a persistent Chroma vector store
- Query emails with a conversational LLM-powered assistant (interactive or single-shot)
- Support for Ollama (local) or Google Gemini (cloud)

---

## Quick Start ✨

1. Clone the repo:

```bash
git clone https://github.com/supriyakanse/Langchain-email-query-bot.git
cd Langchain-email-query-bot
```

2. Create a virtual environment and install dependencies:

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

3. Create a `.env` file (see **Configuration** below) with your email and LLM provider settings.

4. Fetch and index emails (uses date range in `.env` by default):

```bash
python email_assistant.py refresh
```

5. Query your emails interactively:

```bash
python email_assistant.py query
```

Or run a single non-interactive question:

```bash
python email_assistant.py query --question "Summarize my emails"
```

---

## Configuration 🔧

Create a `.env` file at the project root with the following variables:

```env
# Gmail (use an app password for Gmail accounts)
EMAIL_ID=your-email@gmail.com
APP_PASSWORD=your-app-password

# Date range for fetching emails (YYYY-MM-DD)
START_DATE=2025-01-01
END_DATE=2025-01-31

# LLM_PROVIDER: 'ollama' (local) or 'gemini' (Google Gemini)
LLM_PROVIDER=ollama

# Ollama settings (if using Ollama)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_LLM_MODEL=llama3.1:8b
OLLAMA_EMBEDDING_MODEL=llama3.1:8b

# Google Gemini (if using Gemini)
GOOGLE_API_KEY=your-google-api-key

# Chroma persistence directory
CHROMA_PERSIST_DIRECTORY=chroma_store
CHROMA_COLLECTION_NAME=emails

# Tweak defaults
LLM_TEMPERATURE=0.2
DEFAULT_RETRIEVAL_COUNT=50
```

Important: keep your `.env` out of version control. Do NOT commit secrets (app passwords or API keys).

---

## Commands & Usage 🧭

- status: Check config and whether a vector store exists
	- `python email_assistant.py status`
- refresh: Fetch emails and build/rebuild the vector store
	- `python email_assistant.py refresh` (or `--start` / `--end` to override dates)
- query: Interactive query mode (with memory) or single question
	- `python email_assistant.py query`
	- `python email_assistant.py query --question "Did I receive any invoices?"`
- workflow: Run fetch → index → interactive query in one flow
	- `python email_assistant.py workflow`

Outputs & persistence:
- Raw fetched emails are saved to `data/emails_{start}_{end}.json`.
- The Chroma vector store defaults to `chroma_store` (configurable via `.env`).

---



## Architecture & Implementation Notes 🔎

- agent_email_fetch.py: IMAP-based Gmail fetcher (tool: `fetch_emails`). Handles multipart emails, HTML fallback, and basic sanitization.
- agent_email_vector.py: Cleans email bodies (removes HTML, reply chains) and builds a Chroma vector store with provider-specific embeddings (Ollama or Gemini).
- agent_email_query.py: Loads the vector store, retrieves relevant emails via similarity search, and asks an LLM to answer the user's questions. Supports short-term conversational memory.
- agent_email_workflow.py: Orchestrates fetch → save raw JSON → vectorize and persist store.
- email_assistant.py: CLI entry point with `status`, `refresh`, `query`, and `workflow` commands.

---

## Providers & Switching between LLMs 💡

- Ollama (local): set `LLM_PROVIDER=ollama` and configure `OLLAMA_BASE_URL`, `OLLAMA_LLM_MODEL`, `OLLAMA_EMBEDDING_MODEL`.
- Gemini (Google): set `LLM_PROVIDER=gemini` and provide `GOOGLE_API_KEY`.

The code automatically chooses embedding and LLM implementations based on `LLM_PROVIDER`.

---

## Troubleshooting & Tips ⚠️

- If the vector store is missing, run `python email_assistant.py refresh`.
- For Ollama, ensure the Ollama server is running and accessible at `OLLAMA_BASE_URL`.
- For Gmail, create an App Password (recommended) and set it in `APP_PASSWORD`.
- If you see errors when loading the vector store, ensure the `CHROMA_PERSIST_DIRECTORY` exists and is readable.

---

## POW — Proof of Workflow ✅

Below is an example run of the `workflow` command (Fetch → Index → Query) demonstrating the assistant in action.

```text
============================================================
           EMAIL ASSISTANT - AI-Powered Email Query
============================================================

Running complete workflow: Fetch → Index → Query

Phase 1: Fetching and indexing emails
------------------------------------------------------------
==================================================
EMAIL ASSISTANT - WORKFLOW
==================================================
Email: kansesup@gmail.com
Date Range: 2025-12-15 to 2025-12-17
==================================================

Step 1: Fetching emails...
✓ Fetched 11 emails

Step 1.5: Saving emails to JSON file...
✓ Saved 11 emails to data/emails_2025-12-15_2025-12-17.json

Step 2: Building ChromaDB vector store...
✓ Vector store created successfully
✓ Total documents in vector store: 11

============================================================
Phase 2: Interactive Query Mode
============================================================

✓ Ready to query 11 emails

Example queries you can try:
  1. How many emails did I receive?
  2. Summarize my emails
  3. Did I receive any important emails?
  4. List all senders

Ask a question about your emails (or 'quit' to exit): how many emails did i receive

Searching and generating response...

Answer: You received 11 emails.
------------------------------------------------------------

Ask a question about your emails (or 'quit' to exit): summarize my emails

Searching and generating response...

Answer: Here's a summary of your emails:

Email 1: Job listings and career advice  
Email 2: ZipRecruiter job alerts  
Email 3: Canva promotional email  
Email 4: Agentic AI learning opportunity  
Email 5: EduHub license renewal reminder  
Email 6: School PTM reminder  
Email 7: LLM environment configuration  
Email 8: Zomato promotional email
------------------------------------------------------------

Ask a question about your emails (or 'quit' to exit): did i receive any important email

Answer: Yes, you received an important email regarding a license renewal expiring on January 1, 2026.
------------------------------------------------------------

Ask a question about your emails (or 'quit' to exit): exit

Goodbye!
```

---

## Contributing & License 🛠️

Contributions welcome — please open an issue or PR. Add tests and keep secrets out of commits.

---

If you'd like, I can also add a detailed example walkthrough, unit tests for the core parsing logic, or CI checks. 💬

---

Happy querying! ✅