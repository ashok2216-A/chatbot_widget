from fastapi import APIRouter, Request, HTTPException
from fastapi.responses import RedirectResponse, HTMLResponse
from authlib.integrations.starlette_client import OAuth
import os
import json
import base64
from itsdangerous import URLSafeSerializer
from core.auth_db import save_token
from logger import get_logger

logger = get_logger("Auth_Gateway")
router = APIRouter(prefix="/auth", tags=["auth"])

# State serializer to prevent CSRF and carry session context
SECRET_KEY = os.getenv("SECRET_KEY", "super-secret-key-123")
serializer = URLSafeSerializer(SECRET_KEY)

oauth = OAuth()

# ── Google Setup ─────────────────────────────────────────────────────────────
oauth.register(
    name='google',
    client_id=os.getenv("GOOGLE_CLIENT_ID"),
    client_secret=os.getenv("GOOGLE_CLIENT_SECRET"),
    server_metadata_url='https://accounts.google.com/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://www.googleapis.com/auth/gmail.modify https://www.googleapis.com/auth/calendar',
        'token_endpoint_auth_method': 'client_secret_post'
    }
)

# ── Microsoft Setup ──────────────────────────────────────────────────────────
# Using 'common' endpoint for multi-tenant / personal accounts
oauth.register(
    name='microsoft',
    client_id=os.getenv("AZURE_CLIENT_ID"),
    client_secret=os.getenv("AZURE_CLIENT_SECRET"),
    server_metadata_url='https://login.microsoftonline.com/common/v2.0/.well-known/openid-configuration',
    client_kwargs={
        'scope': 'openid email profile https://graph.microsoft.com/Mail.ReadWrite https://graph.microsoft.com/Mail.Send https://graph.microsoft.com/Calendars.ReadWrite',
        'token_endpoint_auth_method': 'client_secret_post'
    }
)

@router.get("/login")
async def login(request: Request, provider: str, session_id: str):
    """
    Initializes the OAuth flow.
    Encodes session_id into the 'state' parameter.
    """
    if provider not in ['google', 'microsoft']:
        raise HTTPException(status_code=400, detail="Invalid provider")

    state_data = {
        "session_id": session_id,
        "provider": provider
    }
    state = serializer.dumps(state_data)
    
    # We construct the exact redirect_uri based on the logic below
    # Important: This MUST match what is registered in Google/MS consoles.
    redirect_uri = request.url_for('auth_callback')
    
    client = oauth.create_client(provider)
    # Add prompt='select_account' for Google/MS to force the account picker
    return await client.authorize_redirect(request, str(redirect_uri), state=state, prompt='select_account')

@router.get("/callback")
async def auth_callback(request: Request):
    """
    Handles the redirect back from the provider.
    Saves the token and notifies the widget window.
    """
    error = request.query_params.get("error")
    if error:
        logger.error(f"OAuth Error: {error}")
        return HTMLResponse("<html><body><script>window.close();</script>Authentication failed.</body></html>")

    state_token = request.query_params.get("state")
    code = request.query_params.get("code")

    try:
        # 1. Recover context from state
        context = serializer.loads(state_token)
        session_id = context["session_id"]
        provider = context["provider"]
        
        # 2. Exchange code for token
        client = oauth.create_client(provider)
        token = await client.authorize_access_token(request)
        
        # 3. Securely store the token
        save_token(session_id, provider, token)
        logger.info(f"Successfully connected {provider} for session {session_id}")

        # 4. Success Response: Notify parent window and close popup
        return HTMLResponse("""
            <html>
                <body style="font-family: sans-serif; display: flex; align-items: center; justify-content: center; height: 100vh; background: #0f172a; color: white;">
                    <div style="text-align: center;">
                        <h2 style="color: #4ade80;">✓ Connection Successful!</h2>
                        <p>You can close this window now.</p>
                        <script>
                            if (window.opener) {
                                window.opener.postMessage({ type: 'AUTH_SUCCESS', provider: '""" + provider + """' }, "*");
                            }
                            setTimeout(() => window.close(), 1500);
                        </script>
                    </div>
                </body>
            </html>
        """)

    except Exception as exc:
        logger.error(f"Callback processing failed: {exc}")
        return HTMLResponse(f"<html><body>Error during callback: {str(exc)}</body></html>")
