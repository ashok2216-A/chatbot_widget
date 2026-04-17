"""
email/tools.py
--------------
Pure Python ADK function tools for Gmail and Microsoft Outlook.
All tools fail gracefully with a clear message if credentials are absent.

Required environment variables
-------------------------------
Gmail:
  GOOGLE_TOKEN_JSON_B64  — base64-encoded contents of token.json (Google OAuth)

Outlook / Microsoft Calendar:
  AZURE_CLIENT_ID        — Azure AD app client ID
  AZURE_CLIENT_SECRET    — Azure AD app client secret
  AZURE_TENANT_ID        — Azure AD tenant ID
  AZURE_TOKEN_CACHE_B64  — base64-encoded MSAL token cache (obtained via setup script)
"""

import os
import sys
import base64
import json
import email.mime.text
import email.mime.multipart
import requests
from typing import Optional, Tuple

# ── Logger ────────────────────────────────────────────────────────────────────
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _BACKEND_DIR)
from logger import get_logger  # type: ignore

logger = get_logger("Email_Tools")


# ══════════════════════════════════════════════════════════════════════════════
#  GMAIL
# ══════════════════════════════════════════════════════════════════════════════

def _get_gmail_service():
    """Returns (service, error_message). error_message is None on success."""
    token_b64 = os.getenv("GOOGLE_TOKEN_JSON_B64")
    if not token_b64:
        return None, (
            "Gmail is not configured. "
            "Set the GOOGLE_TOKEN_JSON_B64 environment variable "
            "(base64-encoded contents of your Google token.json)."
        )
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build

        token_data = json.loads(base64.b64decode(token_b64).decode())
        creds = Credentials.from_authorized_user_info(token_data)
        service = build("gmail", "v1", credentials=creds)
        return service, None
    except Exception as exc:
        logger.error(f"Gmail auth error: {exc}")
        return None, f"Gmail authentication failed: {exc}"


def list_gmail_emails(max_results: int = 5) -> str:
    """Lists the most recent emails from the Gmail inbox.

    Args:
        max_results: Number of emails to retrieve. Default 5, maximum 20.
    """
    service, err = _get_gmail_service()
    if err:
        return err

    try:
        results = (
            service.users()
            .messages()
            .list(userId="me", maxResults=min(max_results, 20), labelIds=["INBOX"])
            .execute()
        )
        messages = results.get("messages", [])
        if not messages:
            return "No emails found in your Gmail inbox."

        email_list = []
        for msg in messages:
            detail = (
                service.users()
                .messages()
                .get(
                    userId="me",
                    id=msg["id"],
                    format="metadata",
                    metadataHeaders=["From", "Subject", "Date"],
                )
                .execute()
            )
            headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}
            email_list.append(
                {
                    "id": msg["id"],
                    "from": headers.get("From", "Unknown"),
                    "subject": headers.get("Subject", "(No Subject)"),
                    "date": headers.get("Date", ""),
                    "snippet": detail.get("snippet", "")[:200],
                }
            )

        logger.info(f"Listed {len(email_list)} Gmail emails.")
        return json.dumps(email_list, indent=2)
    except Exception as exc:
        logger.error(f"list_gmail_emails error: {exc}")
        return f"Error listing Gmail emails: {exc}"


def get_gmail_email_detail(message_id: str) -> str:
    """Gets the full content of a specific Gmail email.

    Args:
        message_id: The Gmail message ID returned by list_gmail_emails.
    """
    service, err = _get_gmail_service()
    if err:
        return err

    try:
        detail = (
            service.users()
            .messages()
            .get(userId="me", id=message_id, format="full")
            .execute()
        )
        headers = {h["name"]: h["value"] for h in detail["payload"]["headers"]}

        # Extract plain text body
        body = ""
        payload = detail.get("payload", {})
        if "parts" in payload:
            for part in payload["parts"]:
                if part.get("mimeType") == "text/plain" and "data" in part.get("body", {}):
                    body = base64.urlsafe_b64decode(part["body"]["data"]).decode(
                        errors="replace"
                    )
                    break
        elif "body" in payload and "data" in payload["body"]:
            body = base64.urlsafe_b64decode(payload["body"]["data"]).decode(
                errors="replace"
            )

        return json.dumps(
            {
                "from": headers.get("From", "Unknown"),
                "to": headers.get("To", ""),
                "subject": headers.get("Subject", ""),
                "date": headers.get("Date", ""),
                "body": body[:4000],
            },
            indent=2,
        )
    except Exception as exc:
        logger.error(f"get_gmail_email_detail error: {exc}")
        return f"Error reading Gmail email: {exc}"


def send_gmail_email(to: str, subject: str, body: str) -> str:
    """Sends an email via Gmail.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body (plain text).
    """
    service, err = _get_gmail_service()
    if err:
        return err

    try:
        msg = email.mime.multipart.MIMEMultipart()
        msg["To"] = to
        msg["Subject"] = subject
        msg.attach(email.mime.text.MIMEText(body, "plain"))
        raw = base64.urlsafe_b64encode(msg.as_bytes()).decode()
        service.users().messages().send(userId="me", body={"raw": raw}).execute()
        logger.info(f"Gmail email sent to {to}")
        return f"Email sent successfully to {to} via Gmail."
    except Exception as exc:
        logger.error(f"send_gmail_email error: {exc}")
        return f"Error sending Gmail email: {exc}"


# ══════════════════════════════════════════════════════════════════════════════
#  MICROSOFT OUTLOOK  (Microsoft Graph API via MSAL)
# ══════════════════════════════════════════════════════════════════════════════

def _get_ms_token() -> Tuple[Optional[str], Optional[str]]:
    """Returns (access_token, error_message). Uses MSAL with a serialized cache."""
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    token_cache_b64 = os.getenv("AZURE_TOKEN_CACHE_B64")

    if not all([client_id, client_secret, tenant_id]):
        return None, (
            "Outlook is not configured. "
            "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID."
        )

    try:
        import msal  # type: ignore

        cache = msal.SerializableTokenCache()
        if token_cache_b64:
            cache.deserialize(base64.b64decode(token_cache_b64).decode())

        app = msal.ConfidentialClientApplication(
            client_id,
            authority=f"https://login.microsoftonline.com/{tenant_id}",
            client_credential=client_secret,
            token_cache=cache,
        )

        # Try silent (from cache) first, then client-credentials flow
        accounts = app.get_accounts()
        scopes = ["https://graph.microsoft.com/.default"]
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])
        else:
            result = app.acquire_token_for_client(scopes=scopes)

        if result and "access_token" in result:
            return result["access_token"], None

        return None, (
            f"Microsoft token acquisition failed: "
            f"{result.get('error_description', 'Unknown error')}"
        )
    except Exception as exc:
        logger.error(f"MS auth error: {exc}")
        return None, f"Microsoft authentication error: {exc}"


def _ms_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def list_outlook_emails(max_results: int = 5) -> str:
    """Lists the most recent emails from the Outlook / Microsoft inbox.

    Args:
        max_results: Number of emails to retrieve. Default 5, maximum 20.
    """
    token, err = _get_ms_token()
    if err:
        return err

    try:
        params = {
            "$top": min(max_results, 20),
            "$select": "id,subject,from,receivedDateTime,bodyPreview",
            "$orderby": "receivedDateTime DESC",
        }
        resp = requests.get(
            "https://graph.microsoft.com/v1.0/me/messages",
            headers=_ms_headers(token),
            params=params,
        )
        resp.raise_for_status()

        emails = []
        for msg in resp.json().get("value", []):
            emails.append(
                {
                    "id": msg["id"],
                    "from": msg["from"]["emailAddress"]["address"],
                    "subject": msg.get("subject", "(No Subject)"),
                    "date": msg.get("receivedDateTime", ""),
                    "snippet": msg.get("bodyPreview", "")[:200],
                }
            )

        if not emails:
            return "No emails found in your Outlook inbox."

        logger.info(f"Listed {len(emails)} Outlook emails.")
        return json.dumps(emails, indent=2)
    except Exception as exc:
        logger.error(f"list_outlook_emails error: {exc}")
        return f"Error listing Outlook emails: {exc}"


def get_outlook_email_detail(message_id: str) -> str:
    """Gets the full content of a specific Outlook email.

    Args:
        message_id: The message ID returned by list_outlook_emails.
    """
    token, err = _get_ms_token()
    if err:
        return err

    try:
        resp = requests.get(
            f"https://graph.microsoft.com/v1.0/me/messages/{message_id}",
            headers=_ms_headers(token),
            params={"$select": "subject,from,toRecipients,receivedDateTime,body"},
        )
        resp.raise_for_status()
        msg = resp.json()
        return json.dumps(
            {
                "from": msg["from"]["emailAddress"]["address"],
                "to": [
                    r["emailAddress"]["address"]
                    for r in msg.get("toRecipients", [])
                ],
                "subject": msg.get("subject", ""),
                "date": msg.get("receivedDateTime", ""),
                "body": msg.get("body", {}).get("content", "")[:4000],
            },
            indent=2,
        )
    except Exception as exc:
        logger.error(f"get_outlook_email_detail error: {exc}")
        return f"Error reading Outlook email: {exc}"


def send_outlook_email(to: str, subject: str, body: str) -> str:
    """Sends an email via Microsoft Outlook.

    Args:
        to: Recipient email address.
        subject: Email subject line.
        body: Email body (plain text).
    """
    token, err = _get_ms_token()
    if err:
        return err

    try:
        payload = {
            "message": {
                "subject": subject,
                "body": {"contentType": "Text", "content": body},
                "toRecipients": [{"emailAddress": {"address": to}}],
            }
        }
        resp = requests.post(
            "https://graph.microsoft.com/v1.0/me/sendMail",
            headers=_ms_headers(token),
            json=payload,
        )
        resp.raise_for_status()
        logger.info(f"Outlook email sent to {to}")
        return f"Email sent successfully to {to} via Outlook."
    except Exception as exc:
        logger.error(f"send_outlook_email error: {exc}")
        return f"Error sending Outlook email: {exc}"
