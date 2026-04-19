from contextvars import ContextVar

# Global context for tool execution to avoid circular imports
# This allows subagent tools to access the session_id set by the chat route
current_session_id: ContextVar[str] = ContextVar("session_id", default="guest")
