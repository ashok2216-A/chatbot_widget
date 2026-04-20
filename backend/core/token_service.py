import os
import requests
import time
from core.auth_db import get_token, save_token
from logger import get_logger

logger = get_logger("Token_Service")

def get_valid_token(session_id: str, provider: str):
    """
    Retrieves a token from the database and automatically refreshes it if it's expired.
    Returns the valid token dict or None if no token exists or refresh fails.
    """
    token = get_token(session_id, provider)
    if not token:
        return None

    # Check if token is expired or about to expire (within 60 seconds)
    expires_at = token.get("expires_at")
    
    # Authlib sometimes returns expires_at (timestamp) or expires_in (seconds)
    # If let's calculate the absolute expiry if not present
    if not expires_at and "expires_in" in token:
        # If we don't have absolute timestamp, we rely on the DB updated_at? 
        # Better: Authlib usually populates 'expires_at' in the token dict.
        pass

    now = int(time.time())
    is_expired = expires_at and (expires_at < now + 60)

    if not is_expired:
        return token

    # Token is expired, try to refresh
    logger.info(f"Token for {provider} (session: {session_id}) is expired. Attempting refresh...")
    refresh_token = token.get("refresh_token")
    if not refresh_token:
        logger.warning(f"No refresh token available for {provider}")
        return None

    try:
        new_token = None
        if provider == 'google':
            new_token = _refresh_google_token(refresh_token)
        elif provider == 'microsoft':
            new_token = _refresh_microsoft_token(refresh_token)
        elif provider == 'twitter':
            new_token = _refresh_twitter_token(refresh_token)

        if new_token:
            # Merge with old token to retain refresh_token if the response didn't include a new one
            merged_token = {**token, **new_token}
            save_token(session_id, provider, merged_token)
            logger.info(f"Successfully refreshed {provider} token.")
            return merged_token
        
    except Exception as e:
        logger.error(f"Failed to refresh {provider} token: {e}")
    
    return None

def _refresh_google_token(refresh_token: str):
    url = "https://oauth2.googleapis.com/token"
    data = {
        "client_id": os.getenv("GOOGLE_CLIENT_ID"),
        "client_secret": os.getenv("GOOGLE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token"
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()

def _refresh_microsoft_token(refresh_token: str):
    url = "https://login.microsoftonline.com/common/oauth2/v2.0/token"
    data = {
        "client_id": os.getenv("AZURE_CLIENT_ID"),
        "client_secret": os.getenv("AZURE_CLIENT_SECRET"),
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "scope": "openid email profile https://graph.microsoft.com/Mail.ReadWrite https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/Calendars.ReadWrite"
    }
    resp = requests.post(url, data=data)
    resp.raise_for_status()
    return resp.json()

def _refresh_twitter_token(refresh_token: str):
    url = "https://api.twitter.com/2/oauth2/token"
    # Twitter OAuth 2.0 requires Basic Auth header with client_id:client_secret
    client_id = os.getenv("TWITTER_CLIENT_ID")
    client_secret = os.getenv("TWITTER_CLIENT_SECRET")
    
    data = {
        "refresh_token": refresh_token,
        "grant_type": "refresh_token",
        "client_id": client_id
    }
    
    # Twitter often requires Basic Auth for refresh if client_secret is used
    auth = (client_id, client_secret) if client_secret else None
    
    resp = requests.post(url, data=data, auth=auth)
    resp.raise_for_status()
    return resp.json()
