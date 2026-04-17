"""
setup_microsoft_oauth.py
========================
Run this ONCE locally to authorize your Microsoft account (Outlook + Calendar).
Opens a browser window for login — no Azure "mobile" setting required.
Saves the MSAL token cache and prints the base64 string you paste into .env.

BEFORE running, add this redirect URI in portal.azure.com:
  App registrations → [your app] → Authentication
  → + Add a platform → Mobile and desktop applications
  → check: http://localhost
  → Save

Usage:
    cd e:\\mychatbot_widget\\chatbot_widget
    python backend/scripts/setup_microsoft_oauth.py

Requirements:
    pip install msal
"""

import base64
import os
import msal

CLIENT_ID     = os.getenv("AZURE_CLIENT_ID", "")
CLIENT_SECRET = os.getenv("AZURE_CLIENT_SECRET", "")
TENANT_ID     = os.getenv("AZURE_TENANT_ID", "")

# Graph API scopes — MSAL adds offline_access/openid/profile automatically
SCOPES = [
    "https://graph.microsoft.com/Mail.ReadWrite",
    "https://graph.microsoft.com/Mail.Send",
    "https://graph.microsoft.com/Calendars.ReadWrite",
]

CACHE_FILE = "msal_token_cache.json"


def main():
    print("\n=== Microsoft OAuth Setup ===\n")

    global CLIENT_ID, CLIENT_SECRET, TENANT_ID
    if not CLIENT_ID:
        CLIENT_ID = input("Azure Client ID     : ").strip()
    if not CLIENT_SECRET:
        CLIENT_SECRET = input("Azure Client Secret : ").strip()
    if not TENANT_ID:
        TENANT_ID = input("Azure Tenant ID     : ").strip()

    if not all([CLIENT_ID, CLIENT_SECRET, TENANT_ID]):
        print("\nERROR: All three Azure values are required.\n")
        return

    # Load existing cache if present
    cache = msal.SerializableTokenCache()
    if os.path.exists(CACHE_FILE):
        with open(CACHE_FILE) as f:
            cache.deserialize(f.read())

    # PublicClientApplication — required for interactive / delegated flows
    app = msal.PublicClientApplication(
        CLIENT_ID,
        authority="https://login.microsoftonline.com/consumers",
        token_cache=cache,
    )

    result = None

    # 1. Try silent (from cache)
    accounts = app.get_accounts()
    if accounts:
        print(f"Found cached account: {accounts[0]['username']} — refreshing token silently...")
        result = app.acquire_token_silent(SCOPES, account=accounts[0])

    # 2. Interactive browser flow (opens http://localhost in your default browser)
    if not result:
        print("Opening browser for Microsoft login...")
        print("(A browser window will open — sign in and grant access, then return here)\n")
        try:
            result = app.acquire_token_interactive(
                scopes=SCOPES,
                port=8080,           # redirect to http://localhost:8080
            )
        except Exception as exc:
            print(f"\nBrowser flow failed: {exc}")
            print("\nFix: In portal.azure.com → App registrations → Authentication")
            print("     → + Add a platform → Mobile and desktop applications")
            print("     → check 'http://localhost' → Save\n")
            return

    if not result or "access_token" not in result:
        err = result.get("error_description", "Unknown error") if result else "No result"
        print(f"\nERROR: {err}\n")
        return

    print("\n✅  Authentication successful!\n")

    # Save the token cache
    with open(CACHE_FILE, "w") as f:
        f.write(cache.serialize())

    # Base64-encode and print
    b64 = base64.b64encode(cache.serialize().encode()).decode()

    print("Copy the value below and set it as AZURE_TOKEN_CACHE_B64 in your .env\n")
    print("─" * 60)
    print(b64)
    print("─" * 60)
    print("\nAlso ensure these are set in your .env and Render dashboard:")
    print(f"  AZURE_CLIENT_ID={CLIENT_ID}")
    print(f"  AZURE_CLIENT_SECRET=<your secret>")
    print(f"  AZURE_TENANT_ID={TENANT_ID}")
    print("  AZURE_TOKEN_CACHE_B64=<the value above>\n")


if __name__ == "__main__":
    main()
