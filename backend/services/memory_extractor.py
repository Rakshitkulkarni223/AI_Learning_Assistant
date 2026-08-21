import json

from services.llm import call_llm

EXTRACTION_PROMPT = (
    "You extract structured user preferences from natural language. "
    "Reply with exactly one JSON object in this format:\n"
    '{"key": "<snake_case_key>", "value": "<value>"}\n\n'
    "Use short snake_case keys such as:\n"
    "- first_to_learn (user says 'first learn X' or 'start with X')\n"
    "- current_focus (user says 'learn X' without 'first' or 'I want')\n"
    "- primary_goal (only when the user explicitly states a long-term goal like 'I want to learn X overall')\n"
    "- note (anything else)\n\n"
    "Do not default to primary_goal. Pick the most specific key for the input. "
    "If the input overrides an earlier preference, use the same key. "
    "Do not add explanations."
)


def extract_preference(fact: str) -> tuple[str, str]:
    """Turn a natural-language fact into a (key, value) pair."""
    try:
        raw = call_llm(fact.strip(), system_prompt=EXTRACTION_PROMPT, temperature=0.0)[
            "answer"
        ]
        text = raw.strip().splitlines()[0] if raw.strip() else ""

        if text.startswith("{"):
            parsed = json.loads(text)
        else:
            parsed = {}

        if not isinstance(parsed, dict):
            parsed = {}

        key = str(parsed.get("key", "note")).strip().lower().replace(" ", "_")
        value = str(parsed.get("value", fact)).strip()

        if not key or not value:
            return "note", fact.strip()

        return key, value
    except Exception:
        return "note", fact.strip()
