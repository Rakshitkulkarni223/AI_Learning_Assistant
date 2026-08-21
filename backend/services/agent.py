import json

from services.llm import call_llm
from services.long_term_memory import get_preferences
from services.tools import get_user_courses, search_courses, search_knowledge

ALLOWED_TOOLS = {
    "search_knowledge": search_knowledge,
    "search_courses": search_courses,
    "get_user_courses": get_user_courses,
}

ALLOWED_TOOL_NAMES = list(ALLOWED_TOOLS.keys())

TOOL_SCHEMA_PROMPT = (
    "You are an assistant that calls tools by outputting JSON.\n"
    "Only the following tools are allowed:\n"
    "- search_knowledge(query): answer study questions from documents\n"
    "- search_courses(query): list available courses matching a keyword\n"
    "- get_user_courses(): list the user's enrolled courses\n\n"
    "Respond with a single JSON object in this exact format and nothing else:\n"
    '{"tool": "<tool_name>", "arguments": {"<arg_name>": "<value>"}}\n\n'
    "If get_user_courses is used, arguments must be {}.\n"
)


def _build_contextual_query(history: list, query: str) -> str:
    """Combine previous messages with the current question."""
    try:
        if not history:
            return query

        lines = []
        for message in history:
            role = "User" if message["role"] == "user" else "Assistant"
            lines.append(f"{role}: {message['content']}")
        lines.append(f"User: {query}")

        return "\n".join(lines)
    except Exception:
        return query


def _extract_json(text: str) -> dict | None:
    """Pull the first JSON object out of the LLM response."""
    try:
        start = text.find("{")
        end = text.rfind("}")
        if start == -1 or end == -1 or end <= start:
            return None
        return json.loads(text[start : end + 1])
    except Exception:
        return None


def _request_tool_call(contextual_query: str) -> dict:
    """Ask the LLM which tool to call, in JSON form."""
    try:
        prompt = f"User question: {contextual_query}\nTool call JSON:"
        raw = call_llm(prompt, system_prompt=TOOL_SCHEMA_PROMPT, temperature=0.0)[
            "answer"
        ]
        parsed = _extract_json(raw)

        if not parsed or parsed.get("tool") not in ALLOWED_TOOLS:
            return {
                "tool": "search_knowledge",
                "arguments": {"query": contextual_query},
            }

        return parsed
    except Exception:
        return {"tool": "search_knowledge", "arguments": {"query": contextual_query}}


def _execute_tool(tool_name: str, arguments: dict, contextual_query: str) -> dict:
    """Validate the tool name and run the matching function."""
    try:
        if tool_name not in ALLOWED_TOOLS:
            return {
                "answer": f"Invalid tool '{tool_name}'. Allowed tools: {ALLOWED_TOOL_NAMES}",
                "sources": [],
                "retrieval_time_ms": 0.0,
            }

        if tool_name == "get_user_courses":
            return ALLOWED_TOOLS[tool_name]()
        elif tool_name == "search_courses":
            return ALLOWED_TOOLS[tool_name](arguments.get("query", ""))
        else:
            return ALLOWED_TOOLS[tool_name](
                arguments.get("query", contextual_query)
            )
    except Exception as exc:
        return {
            "answer": f"Tool execution error: {exc}",
            "sources": [],
            "retrieval_time_ms": 0.0,
        }


def _build_profile_text(preferences: dict) -> str:
    """Format stored preferences for the final answer prompt."""
    try:
        if not preferences:
            return "User profile: none saved."

        lines = "User profile:\n" + "\n".join(
            f"- {key}: {value}" for key, value in preferences.items()
        )
        return lines
    except Exception:
        return "User profile: none saved."


def _summarize(
    tool_name: str, tool_result: dict, query: str, history: list, preferences: dict
) -> str:
    """Send the tool result and profile back to the LLM and ask for a final answer."""
    try:
        profile_text = _build_profile_text(preferences)

        prompt = (
            f"{profile_text}\n\n"
            f"Tool used: {tool_name}\n"
            f"Tool result: {tool_result['answer']}\n\n"
            f"Question: {query}\n\n"
            "Provide a concise final answer to the user. "
            "When the question asks about the user's preferences, use the profile above."
        )
        result = call_llm(
            prompt,
            system_prompt="You are a helpful assistant. Use the conversation history, tool result, and user profile when you answer.",
            history=history,
        )
        return result["answer"]
    except Exception:
        return tool_result["answer"]


def handle_user_query(query: str, history: list | None = None) -> dict:
    """Run one cycle: request tool call, execute it, summarize the result."""
    try:
        history = history or []
        preferences = get_preferences()
        contextual_query = _build_contextual_query(history, query)

        tool_call = _request_tool_call(contextual_query)
        tool_name = tool_call.get("tool", "search_knowledge")
        arguments = tool_call.get("arguments", {})

        if not isinstance(arguments, dict):
            arguments = {}

        tool_result = _execute_tool(tool_name, arguments, contextual_query)
        final_answer = _summarize(tool_name, tool_result, query, history, preferences)

        return {
            "answer": final_answer,
            "sources": tool_result.get("sources", []),
            "retrieval_time_ms": tool_result.get("retrieval_time_ms", 0.0),
        }
    except Exception as exc:
        return {
            "answer": f"Agent error: {exc}",
            "sources": [],
            "retrieval_time_ms": 0.0,
        }
