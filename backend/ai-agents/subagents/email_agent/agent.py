from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from .prompt import EMAIL_INSTRUCTION  # type: ignore
from .tools import (        # type: ignore
    list_gmail_emails,
    get_gmail_email_detail,
    send_gmail_email,
    list_outlook_emails,
    get_outlook_email_detail,
    send_outlook_email,
    disconnect_accounts,
)

email_agent = LlmAgent(
    name="EmailComponent",
    model=LiteLlm(
        model="openrouter/google/gemini-2.0-flash-001",
        fallbacks=["groq/llama-3.3-70b-versatile", "mistral/mistral-large-latest", "mistral/mistral-small", "mistral/mistral-medium"],
        max_tokens=4000,
    ),
    description=(
        "Handles all email tasks: reading and sending messages via Gmail "
        "and Microsoft Outlook. Also handles account disconnection/logout."
    ),
    instruction=EMAIL_INSTRUCTION,
    tools=[
        list_gmail_emails,
        get_gmail_email_detail,
        send_gmail_email,
        list_outlook_emails,
        get_outlook_email_detail,
        send_outlook_email,
        disconnect_accounts,
    ],
)
