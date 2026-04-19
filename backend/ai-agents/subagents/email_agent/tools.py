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

from core.auth_db import get_token
from core.context import current_session_id

def _get_gmail_service():
    """Returns (service, error_message). Fetching from DB for multi-tenant support."""
    session_id = current_session_id.get()
    token_data = get_token(session_id, "google")
    
    if not token_data:
        # Specialized error message that the agent can recognize
        return None, (
            "AUTH_REQUIRED: Gmail account disconnected. "
            "Please provide an A2UI button with url='/auth/login?provider=google' for the user."
        )

    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.exceptions import RefreshError

        # Data structure from Authlib/OAuth callback
        # We need to adapt it for Google Credentials
        creds = Credentials(
            token=token_data.get('access_token'),
            refresh_token=token_data.get('refresh_token'),
            token_uri=token_data.get('token_uri', 'https://oauth2.googleapis.com/token'),
            client_id=os.getenv("GOOGLE_CLIENT_ID"),
            client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
            scopes=token_data.get('scope', '').split(' ')
        )
        
        service = build("gmail", "v1", credentials=creds)
        return service, None
    except RefreshError as rerr:
        logger.error(f"Gmail token refresh failed: {rerr}")
        return None, "AUTH_REQUIRED: Google session expired. Please reconnect your account."
    except Exception as exc:
        logger.error(f"Gmail auth error: {exc}")
        return None, f"[AUTH ERROR] Gmail authentication failed: {str(exc)}"


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
    """Returns (access_token, error_message). Using DB for multi-tenant support."""
    session_id = current_session_id.get()
    token_data = get_token(session_id, "microsoft")
    
    if not token_data:
        return None, (
            "AUTH_REQUIRED: Outlook account disconnected. "
            "Please provide an A2UI button with url='/auth/login?provider=microsoft' for the user."
        )

    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")

    try:
        import msal
        
        # In a real SaaS, you'd use a more robust MSAL cache strategy.
        # For this POC, we check if the token_data we have is still valid or use RToken.
        app = msal.ConfidentialClientApplication(
            client_id,
            authority="https://login.microsoftonline.com/common",
            client_credential=client_secret,
        )

        # Try to refresh using the refresh_token from the DB
        refresh_token = token_data.get('refresh_token')
        if not refresh_token:
             # Fallback to access_token if no refresh token (might be expired soon)
             return token_data.get('access_token'), None

        result = app.acquire_token_by_refresh_token(
            refresh_token,
            scopes=["https://graph.microsoft.com/Mail.ReadWrite", "https://graph.microsoft.com/Mail.Send"]
        )

        if "access_token" in result:
            # We should technically save the new tokens back to DB if they changed
            # save_token(session_id, "microsoft", result)
            return result["access_token"], None

        return None, "AUTH_REQUIRED: Microsoft session expired. Please reconnect."
        
    except Exception as exc:
        logger.error(f"MS auth error: {exc}")
        return None, f"[AUTH ERROR] Microsoft Outlook authentication failed: {str(exc)}"


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
