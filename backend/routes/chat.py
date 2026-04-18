from fastapi import APIRouter
import json
import asyncio
from google.genai import types
from schemas.chat import ChatRequest
from core.agent import runner, session_service
from utils.a2ui import parse_a2ui_chunks
from logger import get_logger

logger = get_logger("API_Gateway")
router = APIRouter()

# ── Error classifier ──────────────────────────────────────────────────────────

def classify_llm_error(error: Exception) -> dict:
    """Returns a user-friendly reply and log level based on the error type."""
    msg = str(error).lower()

    if "402" in msg or "payment" in msg or "credits" in msg or "afford" in msg:
        return {
            "level": "warning",
            "reply": (
                "⚠️ **API Credits Exhausted**: The primary AI model ran out of credits "
                "and all fallbacks are also unavailable. Please top up your OpenRouter balance "
                "at [openrouter.ai/settings/credits](https://openrouter.ai/settings/credits)."
            )
        }

    if "429" in msg or "rate limit" in msg or "rate_limit" in msg or "tpm" in msg:
        return {
            "level": "warning",
            "retry": True,
            "reply": (
                "⏳ **Rate limit reached** across all AI providers. "
                "Please wait a few seconds and try again."
            )
        }

    if "timeout" in msg or "timed out" in msg or "connection" in msg:
        return {
            "level": "error",
            "reply": "🔌 **Connection timeout**: The AI backend took too long to respond. Please try again."
        }

    if "auth" in msg or "401" in msg or "api key" in msg or "apikey" in msg:
        return {
            "level": "error",
            "reply": "🔑 **Authentication Error**: An API key is invalid or missing. Check your `.env` file."
        }

    return {
        "level": "error",
        "reply": "❌ **Unexpected Error**: Something went wrong on the backend. Please try again."
    }


# ── Chat endpoint ─────────────────────────────────────────────────────────────

MAX_RETRIES = 2
RETRY_DELAY_SECS = 5

@router.post("/chat")
async def chat(req: ChatRequest):
    logger.info(f"Received chat request for session: {req.session_id}")

    for attempt in range(1, MAX_RETRIES + 1):
        try:
            # Reuse or create an ADK session
            try:
                session = await session_service.get_session(
                    app_name="portfolio_chatbot",
                    user_id="web_user",
                    session_id=req.session_id
                )
            except Exception:
                session = None

            if not session:
                session = await session_service.create_session(
                    app_name="portfolio_chatbot",
                    user_id="web_user",
                    session_id=req.session_id
                )

            content = types.Content(role='user', parts=[types.Part(text=req.message)])
            final_answer = "I couldn't process your request."

            async for event in runner.run_async(
                user_id="web_user",
                session_id=req.session_id,
                new_message=content
            ):
                if event.author:
                    logger.info(f"→ Agent '{event.author}' started processing...")

                calls = event.get_function_calls()
                if calls:
                    for call in calls:
                        logger.info(f"  [Tool Call] {call.name} with args: {json.dumps(call.args)}")

                if event.is_final_response():
                    if event.content and event.content.parts:
                        final_answer = event.content.parts[0].text
                    break

            # ── Parse A2UI blocks ─────────────────────────────────────────────
            chunks = parse_a2ui_chunks(final_answer)
            logger.info(
                f"Response generated | session={req.session_id} | "
                f"chars={len(final_answer)} | chunks={len(chunks)} | attempt={attempt}"
            )
            return {
                "reply": final_answer,
                "chunks": chunks if chunks else [{"type": "text", "content": final_answer}]
            }

        except Exception as exc:
            classified = classify_llm_error(exc)
            log_fn = logger.warning if classified["level"] == "warning" else logger.error
            log_fn(
                f"Chat attempt {attempt}/{MAX_RETRIES} failed: {str(exc)[:300]}",
                exc_info=(classified["level"] == "error")
            )

            # Retry only for rate limit errors and only if we have attempts left
            if classified.get("retry") and attempt < MAX_RETRIES:
                logger.info(f"Rate limit hit — waiting {RETRY_DELAY_SECS}s before retry {attempt + 1}...")
                await asyncio.sleep(RETRY_DELAY_SECS)
                continue

            # All attempts exhausted or non-retryable error
            friendly_reply = classified["reply"]
            return {
                "reply": friendly_reply,
                "chunks": [{"type": "text", "content": friendly_reply}]
            }
