import os
import time

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

LLM_MODEL = os.getenv("LLM_MODEL", "llama3")
OPENAI_BASE_URL = os.getenv("OPENAI_BASE_URL")
INPUT_COST_PER_1K = float(os.getenv("INPUT_COST_PER_1K", "0.0005"))
OUTPUT_COST_PER_1K = float(os.getenv("OUTPUT_COST_PER_1K", "0.0015"))

DEFAULT_SYSTEM_PROMPT = (
    "You are a helpful AI Learning Assistant. "
    "Keep answers clear, concise, and beginner-friendly."
)

_METRICS = []


def reset_metrics() -> None:
    """Clear the in-memory list of LLM call metrics."""
    global _METRICS
    _METRICS = []


def get_metrics() -> list:
    """Return a copy of the recorded LLM call metrics."""
    return list(_METRICS)


def aggregate_metrics(metrics: list | None = None) -> dict:
    """Sum a list of LLM call metrics into one summary."""
    try:
        data = metrics if metrics is not None else _METRICS

        if not data:
            return {
                "input_tokens": 0,
                "output_tokens": 0,
                "total_tokens": 0,
                "latency_ms": 0.0,
                "cost_usd": 0.0,
                "calls": 0,
            }

        return {
            "input_tokens": sum(m["input_tokens"] for m in data),
            "output_tokens": sum(m["output_tokens"] for m in data),
            "total_tokens": sum(m["total_tokens"] for m in data),
            "latency_ms": round(sum(m["latency_ms"] for m in data), 2),
            "cost_usd": round(sum(m["cost_usd"] for m in data), 6),
            "calls": len(data),
        }
    except Exception:
        return {
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "latency_ms": 0.0,
            "cost_usd": 0.0,
            "calls": 0,
        }


def _estimate_tokens(text: str) -> int:
    """Estimate tokens when the API does not return usage."""
    return max(1, len(text) // 4)


def call_llm(
    user_message: str,
    system_prompt: str | None = None,
    history: list[dict] | None = None,
    temperature: float = 0.7,
) -> dict:
    """Send a user message to an OpenAI-compatible API and return answer + metrics."""
    try:
        start = time.time()

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

        latency_ms = (time.time() - start) * 1000
        answer = response.choices[0].message.content.strip()

        usage = response.usage
        if (
            usage
            and usage.prompt_tokens is not None
            and usage.completion_tokens is not None
        ):
            input_tokens = usage.prompt_tokens
            output_tokens = usage.completion_tokens
            total_tokens = usage.total_tokens or (input_tokens + output_tokens)
        else:
            input_text = "\n".join(m["content"] for m in messages)
            input_tokens = _estimate_tokens(input_text)
            output_tokens = _estimate_tokens(answer)
            total_tokens = input_tokens + output_tokens

        cost_usd = round(
            (input_tokens / 1000) * INPUT_COST_PER_1K
            + (output_tokens / 1000) * OUTPUT_COST_PER_1K,
            6,
        )

        metrics = {
            "input_tokens": input_tokens,
            "output_tokens": output_tokens,
            "total_tokens": total_tokens,
            "latency_ms": round(latency_ms, 2),
            "cost_usd": cost_usd,
        }
        _METRICS.append(metrics)

        return {"answer": answer, **metrics}
    except Exception as exc:
        return {
            "answer": f"LLM error: {exc}",
            "input_tokens": 0,
            "output_tokens": 0,
            "total_tokens": 0,
            "latency_ms": 0.0,
            "cost_usd": 0.0,
        }
