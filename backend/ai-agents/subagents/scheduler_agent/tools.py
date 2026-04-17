"""
scheduler/tools.py
------------------
Pure Python ADK function tools for Google Calendar and Microsoft Calendar.
All tools fail gracefully with a helpful message if credentials are absent.

Required environment variables
-------------------------------
Google Calendar:
  GOOGLE_TOKEN_JSON_B64  — base64-encoded contents of token.json
                           (same credential used by Gmail, scopes must include Calendar)

Microsoft Calendar:
  AZURE_CLIENT_ID        — Azure AD app client ID
  AZURE_CLIENT_SECRET    — Azure AD app client secret
  AZURE_TENANT_ID        — Azure AD tenant ID
  AZURE_TOKEN_CACHE_B64  — base64-encoded MSAL token cache (from setup script)
"""

import os
import sys
import base64
import json
import requests
from datetime import datetime, timedelta, timezone
from typing import Optional, Tuple

# ── Logger ────────────────────────────────────────────────────────────────────
_BACKEND_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../.."))
sys.path.insert(0, _BACKEND_DIR)
from logger import get_logger  # type: ignore

logger = get_logger("Scheduler_Tools")


# ══════════════════════════════════════════════════════════════════════════════
#  GOOGLE CALENDAR
# ══════════════════════════════════════════════════════════════════════════════

def _get_google_calendar_service():
    """Returns (service, error_message). error_message is None on success."""
    token_b64 = os.getenv("GOOGLE_TOKEN_JSON_B64")
    if not token_b64:
        return None, (
            "[CONFIG ERROR] Google Calendar is not configured. "
            "Set GOOGLE_TOKEN_JSON_B64 in .env. "
            "You can generate this by running 'python backend/scripts/setup_google_oauth.py' locally."
        )
    try:
        from google.oauth2.credentials import Credentials
        from googleapiclient.discovery import build
        from google.auth.exceptions import RefreshError

        token_data = json.loads(base64.b64decode(token_b64).decode())
        creds = Credentials.from_authorized_user_info(token_data)
        
        # Test the credentials
        service = build("calendar", "v3", credentials=creds)
        return service, None
    except RefreshError as rerr:
        logger.error(f"Google Calendar token refresh failed: {rerr}")
        return None, "[AUTH ERROR] Your Google session has expired. Please run 'python backend/scripts/setup_google_oauth.py' to refresh."
    except Exception as exc:
        logger.error(f"Google Calendar auth error: {exc}")
        return None, f"[AUTH ERROR] Google Calendar authentication failed: {str(exc)}"


def list_google_calendar_events(days_ahead: int = 7) -> str:
    """Lists upcoming events from Google Calendar.

    Args:
        days_ahead: How many days ahead to look for events. Default 7, maximum 30.
    """
    service, err = _get_google_calendar_service()
    if err:
        return err

    try:
        now = datetime.now(timezone.utc)
        time_min = now.isoformat()
        time_max = (now + timedelta(days=min(days_ahead, 30))).isoformat()

        result = (
            service.events()
            .list(
                calendarId="primary",
                timeMin=time_min,
                timeMax=time_max,
                maxResults=20,
                singleEvents=True,
                orderBy="startTime",
            )
            .execute()
        )

        events = result.get("items", [])
        if not events:
            return f"No Google Calendar events found in the next {days_ahead} days."

        event_list = []
        for ev in events:
            start = ev["start"].get("dateTime", ev["start"].get("date", ""))
            end = ev["end"].get("dateTime", ev["end"].get("date", ""))
            event_list.append(
                {
                    "id": ev["id"],
                    "title": ev.get("summary", "(No Title)"),
                    "start": start,
                    "end": end,
                    "location": ev.get("location", ""),
                    "description": ev.get("description", "")[:300],
                }
            )

        logger.info(f"Listed {len(event_list)} Google Calendar events.")
        return json.dumps(event_list, indent=2)
    except Exception as exc:
        logger.error(f"list_google_calendar_events error: {exc}")
        return f"Error listing Google Calendar events: {exc}"


def create_google_calendar_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
) -> str:
    """Creates a new event in Google Calendar.

    Args:
        title: Event title / summary.
        start_datetime: Start time in ISO 8601 format (e.g. '2026-04-20T10:00:00').
        end_datetime: End time in ISO 8601 format   (e.g. '2026-04-20T11:00:00').
        description: Optional event description.
        location: Optional physical or virtual location.
    """
    service, err = _get_google_calendar_service()
    if err:
        return err

    try:
        body = {
            "summary": title,
            "description": description,
            "location": location,
            "start": {"dateTime": start_datetime, "timeZone": "UTC"},
            "end": {"dateTime": end_datetime, "timeZone": "UTC"},
        }
        created = service.events().insert(calendarId="primary", body=body).execute()
        logger.info(f"Created Google Calendar event: {created['id']}")
        return (
            f"Event '{title}' created successfully on Google Calendar. "
            f"Event ID: {created['id']}"
        )
    except Exception as exc:
        logger.error(f"create_google_calendar_event error: {exc}")
        return f"Error creating Google Calendar event: {exc}"


def delete_google_calendar_event(event_id: str) -> str:
    """Deletes an event from Google Calendar.

    Args:
        event_id: The event ID from list_google_calendar_events.
    """
    service, err = _get_google_calendar_service()
    if err:
        return err

    try:
        service.events().delete(calendarId="primary", eventId=event_id).execute()
        logger.info(f"Deleted Google Calendar event: {event_id}")
        return f"Event {event_id} has been deleted from Google Calendar."
    except Exception as exc:
        logger.error(f"delete_google_calendar_event error: {exc}")
        return f"Error deleting Google Calendar event: {exc}"


# ══════════════════════════════════════════════════════════════════════════════
#  MICROSOFT CALENDAR  (Microsoft Graph API via MSAL)
# ══════════════════════════════════════════════════════════════════════════════

def _get_ms_token() -> Tuple[Optional[str], Optional[str]]:
    """Returns (access_token, error_message)."""
    client_id = os.getenv("AZURE_CLIENT_ID")
    client_secret = os.getenv("AZURE_CLIENT_SECRET")
    tenant_id = os.getenv("AZURE_TENANT_ID")
    token_cache_b64 = os.getenv("AZURE_TOKEN_CACHE_B64")

    if not all([client_id, client_secret, tenant_id]):
        return None, (
            "[CONFIG ERROR] Microsoft Calendar is not configured. "
            "Set AZURE_CLIENT_ID, AZURE_CLIENT_SECRET, and AZURE_TENANT_ID in .env."
        )

    try:
        import msal  # type: ignore

        cache = msal.SerializableTokenCache()
        if token_cache_b64:
            try:
                cache.deserialize(base64.b64decode(token_cache_b64).decode())
            except Exception as e:
                logger.error(f"MS Calendar cache deserialize error: {e}")
                return None, "[AUTH ERROR] Microsoft token cache is corrupted. Please run 'python backend/scripts/setup_microsoft_oauth.py' again."

        app = msal.ConfidentialClientApplication(
            client_id,
            authority="https://login.microsoftonline.com/consumers",
            client_credential=client_secret,
            token_cache=cache,
        )

        scopes = ["https://graph.microsoft.com/.default"]
        accounts = app.get_accounts()
        
        result = None
        if accounts:
            result = app.acquire_token_silent(scopes, account=accounts[0])
        
        if not result or "access_token" not in result:
             result = app.acquire_token_for_client(scopes=scopes)

        if result and "access_token" in result:
            return result["access_token"], None

        err_msg = result.get('error_description', 'No refresh token available')
        return None, f"[AUTH ERROR] Microsoft Calendar session expired or invalid: {err_msg}. Please run 'python backend/scripts/setup_microsoft_oauth.py' locally."
        
    except Exception as exc:
        logger.error(f"MS Calendar auth error: {exc}")
        return None, f"[AUTH ERROR] Microsoft Calendar authentication error: {str(exc)}"


def _ms_headers(token: str) -> dict:
    return {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}


def list_microsoft_calendar_events(days_ahead: int = 7) -> str:
    """Lists upcoming events from Microsoft Calendar.

    Args:
        days_ahead: How many days ahead to look for events. Default 7, maximum 30.
    """
    token, err = _get_ms_token()
    if err:
        return err

    try:
        now = datetime.now(timezone.utc)
        start = now.strftime("%Y-%m-%dT%H:%M:%SZ")
        end = (now + timedelta(days=min(days_ahead, 30))).strftime("%Y-%m-%dT%H:%M:%SZ")

        resp = requests.get(
            "https://graph.microsoft.com/v1.0/me/calendarView",
            headers=_ms_headers(token),
            params={
                "startDateTime": start,
                "endDateTime": end,
                "$select": "id,subject,start,end,location,bodyPreview",
                "$orderby": "start/dateTime",
                "$top": 20,
            },
        )
        resp.raise_for_status()
        items = resp.json().get("value", [])

        if not items:
            return f"No Microsoft Calendar events found in the next {days_ahead} days."

        events = [
            {
                "id": ev["id"],
                "title": ev.get("subject", "(No Title)"),
                "start": ev["start"]["dateTime"],
                "end": ev["end"]["dateTime"],
                "location": ev.get("location", {}).get("displayName", ""),
                "description": ev.get("bodyPreview", "")[:300],
            }
            for ev in items
        ]

        logger.info(f"Listed {len(events)} Microsoft Calendar events.")
        return json.dumps(events, indent=2)
    except Exception as exc:
        logger.error(f"list_microsoft_calendar_events error: {exc}")
        return f"Error listing Microsoft Calendar events: {exc}"


def create_microsoft_calendar_event(
    title: str,
    start_datetime: str,
    end_datetime: str,
    description: str = "",
    location: str = "",
) -> str:
    """Creates a new event in Microsoft Calendar.

    Args:
        title: Event title.
        start_datetime: Start time in ISO 8601 format (e.g. '2026-04-20T10:00:00').
        end_datetime: End time in ISO 8601 format   (e.g. '2026-04-20T11:00:00').
        description: Optional event description.
        location: Optional physical or virtual location.
    """
    token, err = _get_ms_token()
    if err:
        return err

    try:
        payload = {
            "subject": title,
            "body": {"contentType": "Text", "content": description},
            "start": {"dateTime": start_datetime, "timeZone": "UTC"},
            "end": {"dateTime": end_datetime, "timeZone": "UTC"},
            "location": {"displayName": location},
        }
        resp = requests.post(
            "https://graph.microsoft.com/v1.0/me/events",
            headers=_ms_headers(token),
            json=payload,
        )
        resp.raise_for_status()
        ev = resp.json()
        logger.info(f"Created Microsoft Calendar event: {ev['id']}")
        return (
            f"Event '{title}' created successfully on Microsoft Calendar. "
            f"Event ID: {ev['id']}"
        )
    except Exception as exc:
        logger.error(f"create_microsoft_calendar_event error: {exc}")
        return f"Error creating Microsoft Calendar event: {exc}"


def delete_microsoft_calendar_event(event_id: str) -> str:
    """Deletes an event from Microsoft Calendar.

    Args:
        event_id: The event ID from list_microsoft_calendar_events.
    """
    token, err = _get_ms_token()
    if err:
        return err

    try:
        resp = requests.delete(
            f"https://graph.microsoft.com/v1.0/me/events/{event_id}",
            headers=_ms_headers(token),
        )
        resp.raise_for_status()
        logger.info(f"Deleted Microsoft Calendar event: {event_id}")
        return f"Event {event_id} has been deleted from Microsoft Calendar."
    except Exception as exc:
        logger.error(f"delete_microsoft_calendar_event error: {exc}")
        return f"Error deleting Microsoft Calendar event: {exc}"
