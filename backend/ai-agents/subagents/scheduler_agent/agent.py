from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm

from .prompt import SCHEDULER_INSTRUCTION  # type: ignore
from .tools import (                       # type: ignore
    list_google_calendar_events,
    create_google_calendar_event,
    delete_google_calendar_event,
    list_microsoft_calendar_events,
    create_microsoft_calendar_event,
    delete_microsoft_calendar_event,
)

scheduler_agent = LlmAgent(
    name="SchedulerAgent",
    model=LiteLlm(
        model="openrouter/google/gemini-2.0-flash-001",
        fallbacks=["groq/llama-3.3-70b-versatile", "mistral/mistral-large-latest"],
        max_tokens=4000,
    ),
    description=(
        "Manages calendar events: listing, creating, and deleting events "
        "on Google Calendar and Microsoft Calendar."
    ),
    instruction=SCHEDULER_INSTRUCTION,
    tools=[
        list_google_calendar_events,
        create_google_calendar_event,
        delete_google_calendar_event,
        list_microsoft_calendar_events,
        create_microsoft_calendar_event,
        delete_microsoft_calendar_event,
    ],
)
