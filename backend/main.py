import uuid

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from services.agent import handle_user_query
from services.embeddings import get_collection
from services.long_term_memory import clear_facts, get_facts, store_fact
from services.short_term_memory import add_message, get_messages

app = FastAPI(title="AI Learning Assistant", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    session_id: str | None = None


class SearchRequest(BaseModel):
    query: str


class MemoryRequest(BaseModel):
    fact: str


@app.get("/health")
def health_check():
    """Return a simple health status."""
    try:
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/chat")
def chat(request: ChatRequest):
    """Route the user message through the agent with short-term memory."""
    try:
        user_message = request.message.strip()

        if not user_message:
            return {
                "answer": "Please send a message.",
                "sources": [],
                "session_id": request.session_id or "",
            }

        session_id = request.session_id or str(uuid.uuid4())

        add_message(session_id, "user", user_message)
        history = get_messages(session_id)[:-1]

        result = handle_user_query(user_message, history=history)

        add_message(session_id, "assistant", result["answer"])

        return {
            "answer": result["answer"],
            "sources": result.get("sources", []),
            "session_id": session_id,
        }
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/search")
def search(request: SearchRequest):
    """Find the most similar chunks for the user's query."""
    try:
        query = request.query.strip()

        if not query:
            return {"results": []}

        collection = get_collection()
        matches = collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        results = []
        for i, doc in enumerate(matches["documents"][0]):
            results.append(
                {
                    "document": matches["metadatas"][0][i]["source"],
                    "text": doc,
                    "score": matches["distances"][0][i],
                }
            )

        return {"results": results}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.post("/memory")
def store_memory(request: MemoryRequest):
    """Save a user fact to long-term memory."""
    try:
        fact = request.fact.strip()
        if not fact:
            raise HTTPException(status_code=400, detail="Fact cannot be empty")

        store_fact(fact)
        return {"status": "ok"}
    except HTTPException:
        raise
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.get("/memory")
def read_memory():
    """Return all saved user facts."""
    try:
        return {"facts": get_facts()}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))


@app.delete("/memory")
def delete_memory():
    """Clear all saved user facts."""
    try:
        clear_facts()
        return {"status": "ok"}
    except Exception as exc:
        raise HTTPException(status_code=500, detail=str(exc))
