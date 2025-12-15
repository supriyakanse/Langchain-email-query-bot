import email
import imaplib
import re
from datetime import datetime, timedelta
from email.header import decode_header

from langchain.tools import tool


def decode(value):
    if isinstance(value, bytes):
        value = value.decode(errors="ignore")
    parts = decode_header(value)
    decoded = ""
    for item, enc in parts:
        if isinstance(item, bytes):
            decoded += item.decode(enc or "utf-8", errors="ignore")
        else:
            decoded += item
    return decoded


@tool("fetch_emails")
def fetch_emails(email_id: str, app_password: str, start_date: str, end_date: str):
    """
    Fetch all emails between start_date and end_date (inclusive).

    Args:
        email_id: Gmail address
        app_password: Gmail app password
        start_date: Start date in YYYY-MM-DD format
        end_date: End date in YYYY-MM-DD format

    Returns:
        Dictionary with 'emails' key containing list of email dictionaries

    Raises:
        Exception: If authentication fails or connection issues occur
    """
    imap = None
    try:
        # Connect and login
        imap = imaplib.IMAP4_SSL("imap.gmail.com")
        imap.login(email_id, app_password)
        imap.select("INBOX")

        # Format for IMAP (DD-Mon-YYYY)
        # Add 1 day to end_date to make it inclusive (BEFORE is exclusive)
        end_dt = datetime.strptime(end_date, "%Y-%m-%d")
        end_dt_plus_one = (end_dt + timedelta(days=1)).strftime("%d-%b-%Y")
        sd = datetime.strptime(start_date, "%Y-%m-%d").strftime("%d-%b-%Y")

        query = f'(SINCE "{sd}" BEFORE "{end_dt_plus_one}")'
        status, data = imap.search(None, query)

        if status != "OK":
            return {"emails": []}

        email_list = []

        for num in data[0].split():
            status, msg_data = imap.fetch(num, "(RFC822)")
            if status != "OK":
                continue

            msg = email.message_from_bytes(msg_data[0][1])

            sender = decode(msg.get("From"))
            subject = decode(msg.get("Subject"))
            date = msg.get("Date")

            body = ""
            html_body = ""

            if msg.is_multipart():
                for part in msg.walk():
                    content_type = part.get_content_type()
                    if content_type == "text/plain":
                        try:
                            body = part.get_payload(decode=True).decode(errors="ignore")
                            break  # Prefer plain text
                        except:
                            pass
                    elif content_type == "text/html" and not body:
                        # Fallback to HTML if no plain text found
                        try:
                            html_body = part.get_payload(decode=True).decode(
                                errors="ignore"
                            )
                        except:
                            pass
            else:
                content_type = msg.get_content_type()
                try:
                    payload = msg.get_payload(decode=True)
                    if payload:
                        decoded = payload.decode(errors="ignore")
                        if content_type == "text/html":
                            html_body = decoded
                        else:
                            body = decoded
                except:
                    body = ""

            # If we only got HTML, strip HTML tags and CSS
            if not body and html_body:
                # Remove style and script tags with their contents
                html_body = re.sub(
                    r"<style[^>]*>.*?</style>",
                    "",
                    html_body,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                html_body = re.sub(
                    r"<script[^>]*>.*?</script>",
                    "",
                    html_body,
                    flags=re.DOTALL | re.IGNORECASE,
                )
                # Remove all remaining HTML tags
                body = re.sub(r"<[^>]+>", "", html_body)
                # Decode HTML entities
                body = (
                    body.replace("&nbsp;", " ")
                    .replace("&amp;", "&")
                    .replace("&lt;", "<")
                    .replace("&gt;", ">")
                )
                body = (
                    body.replace("&quot;", '"')
                    .replace("&#39;", "'")
                    .replace("&apos;", "'")
                )
                body = (
                    body.replace("&mdash;", "—")
                    .replace("&ndash;", "–")
                    .replace("&hellip;", "...")
                )
                # Remove HTML/CSS comments
                html_body = re.sub(r"<!--.*?-->", "", html_body, flags=re.DOTALL)
                html_body = re.sub(r"/\*.*?\*/", "", html_body, flags=re.DOTALL)
                # Remove CSS-like patterns (property: value;)
                body = re.sub(r"\b[a-zA-Z-]+\s*:\s*[^;{}\n]+;", "", body)
                # Remove CSS braces
                body = re.sub(r"\{[^{}]*\}", "", body)
                # Clean up whitespace
                body = " ".join(body.split())

            email_list.append(
                {
                    "sender": sender,
                    "subject": subject,
                    "date": date,
                    "body": body,
                }
            )

        return {"emails": email_list}

    except imaplib.IMAP4.error as e:
        raise Exception(f"IMAP authentication failed: {e}")
    except Exception as e:
        raise Exception(f"Failed to fetch emails: {e}")
    finally:
        # Ensure proper cleanup
        if imap:
            try:
                imap.close()
                imap.logout()
            except:
                pass


from langchain.agents import create_agent
from langchain.agents.structured_output import ToolStrategy
from langchain_core.messages import HumanMessage
from langchain_google_genai import ChatGoogleGenerativeAI

if __name__ == "__main__":
    llm = ChatGoogleGenerativeAI(model="gemini-2.5-flash", temperature=0.2)

    email_agent = create_agent(
        llm, tools=[fetch_emails], response_format=ToolStrategy(EmailResponse)
    )

    response = email_agent.invoke(
        {
            "messages": [
                HumanMessage(
                    content="Fetch my emails. Email: email, "
                    "App Password: password, "
                    "Start: 2025-11-20, End: 2025-11-22"
                )
            ]
        }
    )

    print(response["structured_response"])
