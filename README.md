# Hybrid A2UI Chatbot (Agentic RAG) ![Cron job status](https://api.cron-job.org/jobs/7489226/0956a0a9d057bb35/status-1.svg)

A production-ready, highly modular AI Chatbot featuring **Agentic RAG** (Retrieval-Augmented Generation) and full **Email & Calendar**

### 🧠 Hybrid A2UI v2 (Adaptive UI)
The chatbot uses a sophisticated **Hybrid A2UI protocol** to blend natural language with interactive, structured components:

- **Interactive Buttons**: Confirm or discard actions (Send Email, Create Event) with a single click.
- **Status Badges**: Real-time visual feedback for item states (e.g., `Read`, `Urgent`, `Success`).
- **Proficiency Bars**: Elegant metrics for skill levels and project progress.
- **Auto-Repair Parser**: The backend automatically fixes common LLM formatting issues (like trailing commas) before rendering.

**Example A2UI v2 Block:**
```json
{
  "data_view": {
    "text": "Email Draft",
    "layout": "list",
    "items": [{ "To": "ashok@example.com", "Status": "Draft" }],
    "actions": [
      { "label": "Send Now", "message": "Yes, send it.", "variant": "primary" }
    ]
  }
}
```
orchestration. This system uses a **Hybrid A2UI Protocol**, allowing the assistant to interleave natural text with rich, interactive UI components.

## 🌟 Key Features

*   **🎨 Hybrid A2UI Protocol**: Seamlessly embeds React components (grids, cards, layouts) directly into conversational responses.
*   **📧 Email Agent**: Full integration with **Gmail** and **Microsoft Outlook** to list, read, and send emails.
*   **📅 Scheduler Agent**: Full integration with **Google Calendar** and **Microsoft Calendar** to list, create, and delete events.
*   **🔍 Modular RAG Pipeline**: Intelligent portfolio search using Pinecone v3 Serverless and OpenRouter (LiteLLM).
*   **🤖 Multi-Agent Orchestration**: A central `CoordinatorAgent` intelligently routes queries to specialized subagents for RAG, Email, or Scheduling.
*   **🛡️ Secure OAuth 2.0 Integration**: Uses base64-encoded token caching for robust authentication across personal Google and Microsoft accounts in production.

---

## 🏗️ Architecture Overview

The system is organized into a modular package-based structure:

### 1. `backend/ai-agents/` (The Brain)
- **Coordinator Agent**: The root agent that routes user intent.
- **Subagents (`subagents/`)**: Each subagent is an isolated package with its own:
    - `agent.py`: Agent definition and tool wiring.
    - `tools.py`: Function definitions (Gmail, Outlook, Calendar, Pinecone).
    - `prompt.py`: Specialized system instructions.

### 2. `frontend/widget/` (The UI)
A React-based widget bundled into a single `widget.js` for universal integration on any website via a simple `<script>` tag.

---

## 🚀 Setup & Deployment

### 1. Environment Variables
Ensure the following are set in your `.env` (local) and Render Dashboard (production):

| Key | Description |
| :--- | :--- |
| `OPENROUTER_API_KEY` | Primary LLM provider (Gemini 2.0 Flash) |
| `PINECONE_API_KEY` | Vector database for Portfolio RAG |
| `GOOGLE_TOKEN_JSON_B64` | Base64 encoded `token.json` for Google services |
| `AZURE_CLIENT_ID` | Microsoft Azure Application (Client) ID |
| `AZURE_TOKEN_CACHE_B64` | Base64 encoded MSAL token cache for MS services |

### 2. One-Time OAuth Setup
To connect your personal accounts, you must run these setup scripts **locally** once and copy the resulting base64 strings to your environment:

```bash
# For Gmail & Google Calendar
# 1. Place 'cred.json' in backend/scripts/
# 2. Run:
python backend/scripts/setup_google_oauth.py

# For Outlook & Microsoft Calendar
# 1. Set AZURE_CLIENT_ID / SECRET in .env
# 2. Run:
python backend/scripts/setup_microsoft_oauth.py
```

---

## 🛠️ Local Development

### Backend
```bash
# Install dependencies
pip install -r backend/requirements.txt

# Start FastAPI server
uvicorn backend.app:app --reload --port 8000
```

### Frontend
```bash
cd frontend/widget
npm install
npm run dev
```

---

## 🧪 Testing the Agents

You can test the multi-agent routing using these sample prompts:

- **RAG**: "What are your top technical skills?"
- **Email**: "List my latest 5 emails from Gmail."
- **Calendar**: "What meetings do I have on Google Calendar for today?"
- **Combined**: "Find the projects in your portfolio about AI, and email them to test@example.com."

---

## 🔒 Security
The backend uses a strict `ALLOWED_ORIGINS` middleware. Update this in your production environment to restrict access only to your authorized domains.
