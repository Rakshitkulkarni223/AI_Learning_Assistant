import os

from dotenv import load_dotenv

load_dotenv()

from services.embeddings import get_collection
from services.llm import call_llm

SIMILARITY_THRESHOLD = float(os.getenv("SIMILARITY_THRESHOLD", "0.3"))

RAG_SYSTEM_PROMPT = (
    "You are a helpful AI Learning Assistant. "
    "Answer only using the provided context. "
    "If the answer is not contained in the context, reply exactly: "
    "I don't know based on the available documents."
)


def answer_with_rag(query: str) -> dict:
    """Retrieve relevant chunks and ask the LLM to answer using only them."""
    try:
        collection = get_collection()

        matches = collection.query(
            query_texts=[query],
            n_results=3,
            include=["documents", "metadatas", "distances"],
        )

        if not matches["documents"] or not matches["documents"][0]:
            return {
                "answer": "I don't know based on the available documents.",
                "sources": [],
            }

        best_score = matches["distances"][0][0]

        if best_score > SIMILARITY_THRESHOLD:
            return {
                "answer": "I don't know based on the available documents.",
                "sources": [],
            }

        context = "\n\n---\n\n".join(matches["documents"][0])

        sources = []
        for i, meta in enumerate(matches["metadatas"][0]):
            sources.append(
                {
                    "document": meta["source"],
                    "score": matches["distances"][0][i],
                }
            )

        prompt = (
            f"CONTEXT:\n{context}\n\n"
            f"QUESTION:\n{query}\n\n"
            "If the answer is not in the context, say "
            "'I don't know based on the available documents.'"
        )

        answer = call_llm(prompt, system_prompt=RAG_SYSTEM_PROMPT)

        return {"answer": answer, "sources": sources}
    except Exception as exc:
        return {"answer": f"RAG error: {exc}", "sources": []}
