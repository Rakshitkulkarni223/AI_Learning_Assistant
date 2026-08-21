# AI Learning Assistant

A small, fully local project for learning and interview preparation.

It covers the practical flow of building an AI assistant that can chat, retrieve knowledge from documents, choose tools, remember user facts, and measure its own cost and latency.

This project is intentionally simple. It does not use production infrastructure like Redis, Kubernetes, Terraform, or managed cloud services.

---

## What you will learn

- How an LLM API is called from Python
- What embeddings are and how they enable semantic search
- How chunking, retrieval, and context windows affect RAG quality
- How hallucinations can be reduced with a similarity threshold
- How a simple AI agent routes to tools
- Why tool allowlists matter for safety
- The difference between short-term and long-term memory
- Why rate limiting is needed
- How to track tokens, cost, and latency for every request
- How to add simple observability without Prometheus or Grafana

---

## Tech Stack

### Frontend

- React
- TypeScript
- Vite
- Plain CSS (no Tailwind)

### Backend

- Python 3.11+
- FastAPI

### Storage

- SQLite for long-term memory
- ChromaDB for vector search (runs locally)

### LLM

- Any OpenAI-compatible API via the `openai` Python SDK
- Works with local Ollama or Groq by setting `OPENAI_BASE_URL`

---

## Project Structure

```
AI_Coding/
├── backend/
│   ├── main.py                    # FastAPI entry point and routes
│   ├── services/
│   │   ├── llm.py                 # OpenAI-compatible LLM wrapper + metrics
│   │   ├── embeddings.py          # ChromaDB client and collection setup
│   │   ├── rag.py                 # Retrieval-Augmented Generation pipeline
│   │   ├── agent.py               # Tool routing and final answer synthesis
│   │   ├── tools.py               # Tool implementations
│   │   ├── short_term_memory.py   # In-memory conversation history
│   │   ├── long_term_memory.py    # SQLite key-value user preferences
│   │   ├── memory_extractor.py    # Natural language -> key/value extraction
│   │   ├── rate_limiter.py        # In-memory sliding-window rate limiter
│   │   └── observability.py       # In-memory request log and stats
│   ├── scripts/
│   │   ├── ingest.py              # Load documents and store embeddings
│   │   └── evaluate.py            # Compute Recall@1, @3, @5
│   ├── documents/                 # Text files used as the knowledge base
│   └── .env.example               # Environment variables template
├── frontend/
│   └── src/
│       ├── App.tsx                # Main React UI with tabs
│       ├── App.css                # Basic styles
│       └── main.tsx
├── memory.db                      # SQLite local memory (ignored by git)
└── chroma/                        # ChromaDB local files (ignored by git)
```

---

## Quick Start

### 1. Backend

```bash
cd backend
python -m venv .venv
source .venv/bin/activate   # or .venv\Scripts\activate on Windows
pip install -r requirements.txt
```

Copy the environment template:

```bash
cp .env.example .env
```

Start Ollama with an OpenAI-compatible server:

```bash
ollama run llama3
ollama serve
```

Then run the FastAPI app:

```bash
uvicorn main:app --reload --host 127.0.0.1 --port 8000
```

### 2. Ingest documents

```bash
cd backend
source .venv/bin/activate
python scripts/ingest.py
```

### 3. Frontend

```bash
cd frontend
npm install
npm run dev
```

Open `http://localhost:5173` in a browser.

---

## Core Architecture

### 1. Simple LLM

```
User -> React -> FastAPI -> LLM -> FastAPI -> React
```

`POST /chat` receives a message, calls the LLM, and returns the text answer.

`services/llm.py` keeps the LLM provider isolated so it can be replaced easily.

### 2. RAG

```
User question
   |
Embedding
   |
ChromaDB vector search
   |
Top 3 chunks
   |
Prompt with context
   |
LLM
   |
Answer + sources
```

`POST /search` shows retrieved chunks with similarity scores before the LLM is added.

### 3. Agent

```
User
 |
LLM chooses a tool
 |
Tool executes
 |
Tool result
 |
LLM gives final answer
```

Allowed tools:

- `search_knowledge(query)`
- `search_courses(query)`
- `get_user_courses()`

### 4. Memory

- **Short-term**: current conversation history per `session_id`
- **Long-term**: SQLite `preferences` table with key/value pairs

The agent loads stored preferences before answering.

---

## Phase Summary

### Phase 1 — Basic Chat

**What**: A React frontend posts to FastAPI, which returns a hardcoded response.

**Why**: Establish the request/response flow before adding the LLM.

**How**: `POST /chat` returns a static string.

### Phase 2 — Connect an LLM

**What**: Replace the hardcoded response with a real LLM call.

**Why**: Understand API keys, base URLs, system prompts, and token usage.

**How**: `services/llm.py` wraps `openai.chat.completions.create`.

### Phase 3 — Create a Local Knowledge Base

**What**: Load text files, split into chunks, embed, and store in ChromaDB.

**Why**: Documents are the source of truth for the RAG system.

**How**: `scripts/ingest.py` uses `langchain-text-splitters` and `sentence-transformers` embeddings.

### Phase 4 — Understand Embeddings

**What**: Add `POST /search` to view retrieved chunks and similarity scores.

**Why**: Visually see how an embedding query maps to relevant documents.

**How**: Query ChromaDB and return `document`, `text`, and `score`.

### Phase 5 — Build RAG

**What**: Feed the top chunks into the LLM prompt and answer only from the context.

**Why**: Ground the LLM in facts from your own documents.

**How**: `services/rag.py` builds a context prompt and calls the LLM. Sources are returned and displayed.

### Phase 6 — Experiment With Chunking

**What**: Make `CHUNK_SIZE` and `CHUNK_OVERLAP` configurable.

**Why**: Chunk size directly impacts retrieval quality.

**How**: Change `.env` values and re-run `ingest.py`.

### Phase 7 — Retrieval Evaluation

**What**: Compute `Recall@1`, `Recall@3`, and `Recall@5`.

**Why**: Measure whether the right document appears at the top of retrieval.

**How**: `scripts/evaluate.py` reads `evaluation.json` and checks the top results.

### Phase 8 — Hallucination Reduction

**What**: Add a `SIMILARITY_THRESHOLD`.

**Why**: Stop the LLM from answering when the retrieved chunks are not close enough.

**How**: If the best chunk score is worse than the threshold, return "I don't know based on the available documents."

### Phase 9 — Add an AI Agent

**What**: The agent decides between RAG, course search, and user courses.

**Why**: Different questions need different data sources.

**How**: `services/agent.py` asks the LLM to pick a tool.

### Phase 10 — Tool Calling

**What**: The LLM outputs a structured JSON tool call.

**Why**: Clearer and safer than raw text parsing.

**How**: The backend validates the tool name against an allowlist before executing.

### Phase 11 — Short-Term Memory

**What**: Remember the current conversation in memory.

**Why**: Handle follow-up questions like "explain that more".

**How**: `services/short_term_memory.py` stores messages by `session_id`.

### Phase 12 — Long-Term Memory

**What**: Store user preferences in SQLite.

**Why**: The assistant should remember facts about the user across sessions.

**How**: `POST /memory` extracts key/value pairs from natural language and stores them in a `preferences` table.

### Phase 13 — Rate Limit Simulation

**What**: In-memory sliding-window rate limiter.

**Why**: Protect the backend from accidental overload and practice a real concern.

**How**: `services/rate_limiter.py` tracks timestamps per IP and returns `HTTP 429` when the limit is exceeded.

### Phase 14 — Token and Cost Tracking

**What**: Track input/output tokens, latency, and estimated cost for every LLM call.

**Why**: LLM usage is billed per token, so understanding cost is essential.

**How**: `services/llm.py` records metrics and `/chat` returns an aggregated `metrics` object. If the provider does not return `usage`, a simple character-based estimate is used.

### Phase 15 — Simple AI Observability

**What**: In-memory request log with per-request latency, retrieval time, LLM time, tokens, and status.

**Why**: See whether the system is slow because of retrieval, the LLM, or something else.

**How**: `services/observability.py` and `GET /debug/stats` serve the data. The frontend has a `Debug` tab.

---

## Interview Questions and Answers

### LLM and Prompting

**Q1. What is a system prompt?**
A system prompt sets the model's role and behavior for the entire conversation. It is usually sent once at the top of the messages list.

**Q2. Why is it better to keep the API key on the backend?**
The API key should never be exposed in the browser. Keeping it on the backend prevents theft and lets you control usage, rate limits, and logging.

**Q3. Why do output tokens usually cost more than input tokens?**
Output tokens are generated one at a time, which is autoregressive and more compute-intensive. Input tokens can be processed in parallel.

### Embeddings and Retrieval

**Q4. What is an embedding?**
An embedding is a dense vector of numbers that represents the meaning of a piece of text. Similar texts have vectors that are close to each other.

**Q5. How does ChromaDB find the most relevant chunks?**
It converts the query into an embedding and compares it against stored chunk embeddings, usually using cosine or dot-product distance, then returns the nearest neighbors.

**Q6. What is the difference between lexical search and semantic search?**
Lexical search matches exact words. Semantic search compares meaning through embeddings, so it can find relevant results even when the wording differs.

### Chunking

**Q7. Why does chunk size matter?**
Chunks that are too small lose context. Chunks that are too large can include unrelated topics and dilute the answer.

**Q8. What is chunk overlap?**
Overlap replicates a few sentences between consecutive chunks so that ideas split at a boundary are not lost.

### RAG

**Q9. What is Retrieval-Augmented Generation?**
RAG retrieves relevant documents first, then gives them to the LLM as context, so the answer is grounded in a specific knowledge base.

**Q10. Why is it important to show sources in a RAG UI?**
Sources let the user verify the answer and help debug retrieval mistakes.

### Hallucinations

**Q11. How can RAG reduce hallucinations?**
By forcing the model to answer only from retrieved context and by rejecting questions whose retrieved chunks do not pass a similarity threshold.

**Q12. What is the downside of a very strict similarity threshold?**
The system may say "I don't know" too often, even for questions that could be answered with slightly lower-confidence retrieval.

### Agents and Tool Calling

**Q13. What is the role of the agent in this project?**
The agent reads the user's question, picks the most appropriate tool, executes it, and then asks the LLM to produce the final answer.

**Q14. Why is an allowlist important for tool calling?**
An allowlist prevents the LLM from asking the backend to run arbitrary or dangerous functions. Only explicitly registered tools can be executed.

**Q15. What happens if the LLM returns an invalid tool name?**
The backend rejects it and falls back to a safe default, such as `search_knowledge`.

### Memory

**Q16. What is the difference between short-term and long-term memory?**
Short-term memory is the current conversation and is lost when the session ends. Long-term memory persists across sessions and is stored in SQLite.

**Q17. Why did we switch from a flat list to key/value preferences?**
A flat list can hold contradictory facts. Key/value pairs let later statements overwrite earlier ones, so the assistant follows the user's latest intent.

### Rate Limiting and Cost

**Q18. Why do we need rate limiting even for a local project?**
It protects the backend and the LLM account from accidental loops or heavy usage. It also demonstrates a real production concern.

**Q19. What is a sliding-window rate limit?**
It counts requests within a fixed time window. As time passes, older requests slide out of the window and no longer count.

**Q20. How is cost estimated when the provider does not return token counts?**
Use a heuristic such as `len(text) // 4` for characters, or `len(text.split())` for words. This is not exact but is enough for local learning.

### Observability

**Q21. What is observability?**
Observability is the ability to understand what a system is doing internally by looking at its outputs, logs, and metrics, without needing to debug live code.

**Q22. Why split retrieval time from LLM time?**
It tells you which part of the pipeline is slow. If retrieval time is high, tune ChromaDB or embeddings. If LLM time is high, consider a smaller model or caching.

**Q23. What data is lost when an in-memory service restarts?**
In-memory logs, rate-limit histories, and short-term memory are lost. SQLite long-term memory and ChromaDB files persist because they are stored on disk.

---

## What is not included

The original plan also mentioned:

- **Phase 16 — MCP**: exposing tools through the Model Context Protocol. This is a great next step once the current flow is stable.
- **Phase 17 — Final Architecture**: splitting routes into `api/` modules and cleaning up the folder structure.

These are left as future learning exercises.

---

## Useful Commands

| Task | Command |
|---|---|
| Start backend | `cd backend && source .venv/bin/activate && uvicorn main:app --reload` |
| Ingest documents | `cd backend && python scripts/ingest.py` |
| Run retrieval evaluation | `cd backend && python scripts/evaluate.py` |
| Start frontend | `cd frontend && npm run dev` |
| Build frontend | `cd frontend && npm run build` |

---

## License

This project is for personal learning and interview preparation only.
