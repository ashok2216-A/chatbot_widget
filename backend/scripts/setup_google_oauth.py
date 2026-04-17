"""
setup_google_oauth.py
=====================
Run this ONCE locally to authorize your Google account (Gmail + Calendar).
It will open a browser for consent, then save token.json and print the
base64 string you paste into your .env file.

Usage:
    cd e:\\mychatbot_widget\\chatbot_widget
    python backend/scripts/setup_google_oauth.py

Requirements:
    pip install google-auth-oauthlib google-auth-httplib2 google-api-python-client
"""

import os
import base64
import json
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from google.oauth2.credentials import Credentials

# Scopes needed by EmailAgent + SchedulerAgent
SCOPES = [
    "https://www.googleapis.com/auth/gmail.modify",      # read + send Gmail
    "https://www.googleapis.com/auth/calendar",           # full Calendar access
]

# Resolve paths relative to this script's directory
_SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_FILE = os.path.join(_SCRIPT_DIR, "cred.json") 
TOKEN_FILE = os.path.join(_SCRIPT_DIR, "token.json")


def main():
    print("\n=== Google OAuth Setup ===\n")

    if not os.path.exists(CREDENTIALS_FILE):
        print(f"ERROR: '{CREDENTIALS_FILE}' not found in the current directory.")
        print("\nSteps to get it:")
        print("  1. Go to https://console.cloud.google.com/")
        print("  2. Create / select a project")
        print("  3. Enable: Gmail API  +  Google Calendar API")
        print("  4. Go to APIs & Services → Credentials → + Create Credentials")
        print("  5. Choose: OAuth client ID → Desktop app")
        print("  6. Download the JSON file and rename it 'credentials.json'")
        print("  7. Place it in this directory and re-run this script.\n")
        return

    creds = None

    # Try loading an existing token
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)

    # Refresh or run the full OAuth flow
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CREDENTIALS_FILE, SCOPES)
            # Opens browser tab for user consent
            creds = flow.run_local_server(port=0)

    # Save token.json
    with open(TOKEN_FILE, "w") as f:
        f.write(creds.to_json())

    print(f"✅  token.json saved.\n")

    # Base64-encode and print the value
    with open(TOKEN_FILE, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()

    print("Copy the value below and set it as GOOGLE_TOKEN_JSON_B64 in your .env\n")
    print("─" * 60)
    print(b64)
    print("─" * 60)
    print("\nAlso add it to your Render dashboard → portfolio-backend → Environment.\n")


if __name__ == "__main__":
    main()
