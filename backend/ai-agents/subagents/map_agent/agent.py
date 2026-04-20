from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from .prompt import MAP_INSTRUCTION
from .tools import search_place, get_directions

map_agent = LlmAgent(
    name="GoogleMapAgent",
    model=LiteLlm(
        model="openrouter/google/gemini-2.0-flash-001",
        fallbacks=["groq/llama-3.3-70b-versatile", "mistral/mistral-large-latest"],
        max_tokens=2000
    ),
    description="Finds locations, shows maps, and provides directions/navigation.",
    instruction=MAP_INSTRUCTION,
    tools=[search_place, get_directions]
)
