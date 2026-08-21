import os

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI Learning Assistant. "
    "Keep answers clear, concise, and beginner-friendly."
)


def call_llm(
    user_message: str,
    system_prompt: str | None = None,
    history: list[dict] | None = None,
    temperature: float = 0.7,
) -> str:
    """Send a user message to an OpenAI-compatible API and return the text answer."""
    try:
        api_key = os.getenv("OPENAI_API_KEY")

        if not api_key:
            raise ValueError("OPENAI_API_KEY environment variable is not set")

        client_kwargs = {"api_key": api_key}
        if OPENAI_BASE_URL:
            client_kwargs["base_url"] = OPENAI_BASE_URL

        client = OpenAI(**client_kwargs)

        messages = []
        if system_prompt:
            messages.append({"role": "system", "content": system_prompt})
        else:
            messages.append({"role": "system", "content": DEFAULT_SYSTEM_PROMPT})

        if history:
            messages.extend(history)

        messages.append({"role": "user", "content": user_message})

        response = client.chat.completions.create(
            model=LLM_MODEL,
            messages=messages,
            temperature=temperature,
        )

        return response.choices[0].message.content.strip()
    except Exception as exc:
        return f"LLM error: {exc}"
