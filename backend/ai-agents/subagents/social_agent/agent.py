from google.adk.agents import LlmAgent
from google.adk.models.lite_llm import LiteLlm
from .tools import post_tweet, get_twitter_profile
from .prompt import SOCIAL_AGENT_INSTRUCTION

social_agent = LlmAgent(
    name="SocialMediaAgent",
    model=LiteLlm(
        model="openrouter/google/gemini-2.0-flash-001",
        fallbacks=["groq/llama-3.3-70b-versatile", "mistral/mistral-large-latest"],
        max_tokens=4000,
    ),
    description="Manages X (Twitter) interactions: posting tweets and checking profile info.",
    instruction=SOCIAL_AGENT_INSTRUCTION,
    tools=[post_tweet, get_twitter_profile]
)
