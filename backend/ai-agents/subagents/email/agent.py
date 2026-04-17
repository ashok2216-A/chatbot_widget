import sys
import os
from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

# Expose siblings for direct import
sys.path.insert(0, os.path.dirname(__file__))
from prompt import EMAIL_INSTRUCTION  # type: ignore
from tools import (        # type: ignore
    list_gmail_emails,
    get_gmail_email_detail,
    send_gmail_email,
    list_outlook_emails,
    get_outlook_email_detail,
    send_outlook_email,
)

email_agent = LlmAgent(
    name="EmailAgent",
    model=LiteLlm(
        model="openrouter/google/gemini-2.0-flash-001",
        fallbacks=["groq/llama-3.3-70b-versatile", "mistral/mistral-large-latest"],
    ),
    description=(
        "Handles all email tasks: reading and sending messages via Gmail "
        "and Microsoft Outlook."
    ),
    instruction=EMAIL_INSTRUCTION,
    tools=[
        list_gmail_emails,
        get_gmail_email_detail,
        send_gmail_email,
        list_outlook_emails,
        get_outlook_email_detail,
        send_outlook_email,
    ],
)
