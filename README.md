# AI Portfolio Chatbot (RAG Architecture)

A production-ready, embeddable AI Chat Widget and RAG (Retrieval-Augmented Generation) backend. It intelligently scrapes your portfolio, embeds the data into a vector database, and uses an explicitly orchestrated AI agent to answer user queries safely and strictly based on your context.

## 🌟 Features
* **Modern UI Widget:** A beautiful, responsive glassmorphism chat widget deployable via a single `<script>` tag.
* **Intelligent Ingestion:** Automated scraping of your portfolio/website. Uses MD5 hashing to prevent duplicate embedding insertions.
* **Serverless Vector DB:** Fully integrated with Pinecone v3 Serverless architecture.
* **Provider Agnostic (LiteLLM & OpenRouter):** The entire stack is built to route through OpenRouter—meaning you can instantly swap between OpenAI, Anthropic, or Meta models without changing any code.
* **Strict Security:** Custom FastAPI middleware validates `Origin` and `Referer` headers, ensuring the API can *only* be accessed from your actual deployed website domain.

---

## 🏗️ Architecture Overview

### 1. `widget/` (Frontend)
Contains the embeddable chat widget script (`widget.js`) and UI components. Deploy this to **Vercel** or any static hosting, or inject it directly into your portfolio HTML.

### 2. `backend/ingestion-service/` (Cron / Pipeline)
* Scrapes the target URL (`scraper.py`).
* Chunks text and generates 1536-dimensional vectors using `openai/text-embedding-3-small` via OpenRouter (`embedder.py`).
* Upserts context to your Pinecone Serverless Database.

### 3. `backend/rag-service/` (AI Engine)
* Uses a custom LiteLLM ReAct tool-calling loop.
* Intercepts chat queries, generates a search vector, and retrieves context from Pinecone (`tools/retriever.py`).
* Injects context into the prompt and returns a personalized answer.

### 4. `backend/app.py` (API Gateway)
The entry point deployed to **Render**. It exposes the secure `/chat` endpoint for the frontend widget and acts as the gatekeeper for the internal `rag-service`.

---

## 🚀 Deployment & Usage

### 1. Environment Setup
Create a `.env` file in the `backend/` directory:
```env
OPENROUTER_API_KEY=sk-or-v1-...
ALLOWED_ORIGIN=https://your-portfolio-domain.com
PINECONE_API_KEY=pcsk_...
PINECONE_ENV=us-east-1
PINECONE_INDEX_NAME=ashok-chatbot
```

### 2. Install Dependencies
```bash
pip install -r backend/requirements.txt
pip install -r backend/ingestion-service/requirements.txt
```

### 3. Run Ingestion (Populate Database)
You must run this at least once before querying the bot!
```bash
python backend/ingestion-service/main.py
```

### 4. Start the API Server
```bash
uvicorn backend.app:app --host 0.0.0.0 --port 8000
```

*(Note: When deploying to Render, the start command is `uvicorn app:app --host 0.0.0.0 --port 8000` assuming the root directory is set to `backend`)*

---

## 🔒 Security Note
The API is currently locked by `ALLOWED_ORIGIN`. If you test locally, ensure your `.env` has `ALLOWED_ORIGIN=http://localhost` or disable the middleware in `app.py` during development!
