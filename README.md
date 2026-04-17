# Hybrid A2UI Chatbot (Agentic RAG) ![Cron job status](https://api.cron-job.org/jobs/7489226/0956a0a9d057bb35/status-1.svg)

A production-ready, highly configurable AI Chat Widget and Agentic RAG (Retrieval-Augmented Generation) backend. This system features a unique **Hybrid A2UI Protocol**, allowing the assistant to seamlessly interleave natural conversational text with rich, interactive UI components (grids, cards, and adaptive layouts).

## 🌟 Key Features

*   **🎨 Hybrid A2UI Protocol**: Unlike standard chatbots, this agent can embed rich React components directly into its messages using a resilient JSON-parsing engine.
*   **🚀 Universal Single-Script Integration**: Deploy the entire widget—styles and logic—via a single `<script>` tag. No manual CSS linking required.
*   **🧠 Dynamic Adaptive Engine**: A subject-agnostic UI renderer that automatically visualizes any structured data (skills, projects, products) in the most appropriate layout.
*   **🔍 Intelligent RAG Pipeline**: Automated scraping and vectorization of your website/portfolio using Pinecone v3 Serverless and OpenRouter (LiteLLM).
*   **🛡️ Production-Grade Security**: Custom FastAPI middleware validates origins and referrers to prevent unauthorized usage of your LLM tokens.
*   **☁️ Render Native**: Comes pre-configured with a `render.yaml` Blueprint for one-click deployment.

---

## 🏗️ Architecture Overview

### 1. `frontend/widget` (The Plugin)
A React-based widget optimized into a single `widget.js` bundle using Vite. It exposes a global `window.ChatWidget` object for runtime configuration.

### 2. `backend/app.py` (The Gateway)
A FastAPI server that acts as the secure entry point. It parses raw AI responses, extracts A2UI blocks, and enforces security policies.

### 3. `backend/ai-agents/` (The Brain)
Orchestrates the conversation flow. Uses Few-Shot instruction tuning to ensure the LLM consistently utilizes the Hybrid UI blocks for data-heavy responses.

---

## 🚀 Deployment & Integration

### 1. The "Single-Script" Integration
To embed the widget in any website, add these three lines:

```html
<!-- Load the widget -->
<script type="module" src="https://your-host.com/assets/widget.js"></script>

<!-- Initialize with your branding -->
<script>
    document.addEventListener('DOMContentLoaded', () => {
        window.ChatWidget.init({
            botName: "F.R.I.D.A.Y",
            apiUrl: "https://your-backend.onrender.com/chat",
            welcomeMessage: "Hi! Ask me about my projects or technical stack."
        });
    });
</script>
```

### 2. Render Deployment (One-Click)
1. Push this repository to GitHub.
2. In the Render Dashboard, click **New +** -> **Blueprint**.
3. Connect your repository. Render will automatically detect `render.yaml` and set up your backend and static site.
4. Provide your `OPENROUTER_API_KEY` and `PINECONE_API_KEY` in the dashboard.

---

## 🛠️ Local Development

### Backend Setup
```bash
# Create venv and install
python -m venv .venv
source .venv/bin/activate  # .venv\Scripts\activate on Windows
pip install -r backend/requirements.txt

# Start dev server
uvicorn backend.app:app --reload
```

### Frontend Setup
```bash
cd frontend/widget
npm install
npm run dev # Access via http://localhost:5173/dev-test.html
```

---

## 🔒 Security Configuration
The API is currently locked by `ALLOWED_ORIGINS`. Update your `.env` or Render environment variables:
```env
ALLOWED_ORIGINS=https://your-portfolio-domain.com,http://localhost:5173
```
