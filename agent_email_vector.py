import re
import uuid

from email_reply_parser import EmailReplyParser
from langchain.tools import tool
from langchain_community.vectorstores import Chroma
from langchain_ollama import OllamaEmbeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings

# Import configuration
from config import config

# from talon.signature import extract as extract_signature


def get_embeddings():
    """
    Initialize embeddings based on LLM_PROVIDER from config.

    Returns:
        Embeddings instance (OllamaEmbeddings or GoogleGenerativeAIEmbeddings)

    Raises:
        ValueError: If provider is not supported or configuration is invalid
    """
    if config.LLM_PROVIDER == "ollama":
        return OllamaEmbeddings(
            model=config.OLLAMA_EMBEDDING_MODEL,
            base_url=config.OLLAMA_BASE_URL,
        )
    elif config.LLM_PROVIDER == "gemini":
        return GoogleGenerativeAIEmbeddings(
            model="models/text-embedding-004",
            google_api_key=config.GOOGLE_API_KEY,
        )
    else:
        raise ValueError(
            f"Unsupported LLM_PROVIDER: {config.LLM_PROVIDER}. Must be 'ollama' or 'gemini'"
        )


def clean_email(email):
    body = email["body"]

    # 1. Remove style and script tags with their contents (in case any slipped through)
    body = re.sub(r'<style[^>]*>.*?</style>', '', body, flags=re.DOTALL | re.IGNORECASE)
    body = re.sub(r'<script[^>]*>.*?</script>', '', body, flags=re.DOTALL | re.IGNORECASE)
    
    # 2. Remove all remaining HTML tags
    body = re.sub(r'<[^>]+>', '', body)
    
    # 3. Decode HTML entities
    body = body.replace('&nbsp;', ' ').replace('&amp;', '&').replace('&lt;', '<')
    body = body.replace('&gt;', '>').replace('&quot;', '"').replace('&#39;', "'")
    body = body.replace('&apos;', "'").replace('&mdash;', '—').replace('&ndash;', '–')
    body = body.replace('&hellip;', '...').replace('&copy;', '(c)').replace('&reg;', '(R)')
    
    # 4. Remove HTML/CSS comments
    body = re.sub(r'<!--.*?-->', '', body, flags=re.DOTALL)
    body = re.sub(r'/\*.*?\*/', '', body, flags=re.DOTALL)
    
    # 5. Remove CSS-like patterns more carefully
    # Remove CSS properties (but be careful not to remove URLs or normal text)
    # Only remove if it looks like CSS: property:value; or property: value;
    body = re.sub(r'\b[a-zA-Z-]+\s*:\s*[^;{}\n]+;', '', body)
    # Remove CSS at-rules (@media, @font-face, etc.)
    body = re.sub(r'@[a-zA-Z-]+\s+[^{]*\{[^}]*\}', '', body)
    # Remove standalone CSS braces with content
    body = re.sub(r'\{[^{}]*\}', '', body)
    
    # 6. Remove standalone numbers that might be HTML entity codes
    body = re.sub(r'^\d+\s+', '', body)  # Remove leading numbers
    body = re.sub(r'\s+\d+\s+', ' ', body)  # Remove standalone number words
    
    # 7. Remove reply chain
    body = EmailReplyParser.parse_reply(body)

    # 8. Remove signature
    # body, sig = extract_signature(body)

    # 9. Normalize whitespace - collapse multiple spaces/newlines
    body = re.sub(r'\s+', ' ', body)
    body = body.strip()

    combined = (
        f"Sender: {email['sender']}\n"
        f"Subject: {email['subject']}\n"
        f"Date: {email['date']}\n\n"
        f"{body}"
    )

    return combined


def build_vector_store(email_list, persist_directory=None):
    """
    Build a ChromaDB vector store from a list of email dictionaries.

    Args:
        email_list: List of email dictionaries with keys: sender, subject, date, body
        persist_directory: Directory to persist the vector store (uses config if not provided)

    Returns:
        ChromaDB vector store instance

    Raises:
        ValueError: If email_list is empty or invalid
        Exception: If vector store creation fails
    """
    if not email_list:
        raise ValueError("Email list cannot be empty")

    persist_dir = persist_directory or config.CHROMA_PERSIST_DIRECTORY

    try:
        cleaned_texts = []
        metadatas = []

        for e in email_list:
            # Validate email structure
            if not all(key in e for key in ["sender", "subject", "date", "body"]):
                raise ValueError(
                    f"Invalid email structure. Required keys: sender, subject, date, body"
                )

            cleaned = clean_email(e)
            cleaned_texts.append(cleaned)
            metadatas.append(
                {
                    "sender": e["sender"],
                    "subject": e["subject"],
                    "date": e["date"],
                    "id": str(uuid.uuid4()),
                }
            )

        # Get embeddings based on provider
        embeddings = get_embeddings()

        vectorstore = Chroma.from_texts(
            texts=cleaned_texts,
            embedding=embeddings,
            metadatas=metadatas,
            collection_name=config.CHROMA_COLLECTION_NAME,
            persist_directory=persist_dir,
        )
        return vectorstore

    except Exception as e:
        raise Exception(f"Failed to build vector store: {e}")
