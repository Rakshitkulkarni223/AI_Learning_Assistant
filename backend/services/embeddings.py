import os
from pathlib import Path

from dotenv import load_dotenv

load_dotenv()

import chromadb
from chromadb.utils.embedding_functions import OpenAIEmbeddingFunction

BASE_DIR = Path(__file__).parent.parent.parent
CHROMA_DIR = Path(os.getenv("CHROMA_DIR", str(BASE_DIR / "chroma")))

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "nomic-embed-text")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL", "http://localhost:11434/v1")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "ollama")

COLLECTION_NAME = "knowledge"

_chroma_client = None
_embedding_function = None


def get_embedding_function():
    """Return a shared embedding function that talks to Ollama's OpenAI endpoint."""
    global _embedding_function
    try:
        if _embedding_function is None:
            _embedding_function = OpenAIEmbeddingFunction(
                api_key=OPENAI_API_KEY,
                api_base=OPENAI_BASE_URL,
                model_name=EMBEDDING_MODEL,
            )
        return _embedding_function
    except Exception as exc:
        raise RuntimeError(f"Failed to load embedding function: {exc}")


def get_collection():
    """Return the ChromaDB knowledge collection."""
    global _chroma_client
    try:
        if _chroma_client is None:
            _chroma_client = chromadb.PersistentClient(path=str(CHROMA_DIR))

        return _chroma_client.get_or_create_collection(
            name=COLLECTION_NAME,
            embedding_function=get_embedding_function(),
        )
    except Exception as exc:
        raise RuntimeError(f"Failed to load ChromaDB collection: {exc}")
