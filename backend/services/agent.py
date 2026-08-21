import json

from services.llm import call_llm
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


def _request_tool_call(query: str) -> dict:
    """Ask the LLM which tool to call, in JSON form."""
    try:
        prompt = f"User question: {query}\nTool call JSON:"
        raw = call_llm(prompt, system_prompt=TOOL_SCHEMA_PROMPT)
        parsed = _extract_json(raw)

        if not parsed or parsed.get("tool") not in ALLOWED_TOOLS:
            return {"tool": "search_knowledge", "arguments": {"query": query}}

        return parsed
    except Exception:
        return {"tool": "search_knowledge", "arguments": {"query": query}}


def _execute_tool(tool_name: str, arguments: dict, fallback_query: str) -> dict:
    """Validate the tool name and run the matching function."""
    try:
        if tool_name not in ALLOWED_TOOLS:
            return {
                "answer": f"Invalid tool '{tool_name}'. Allowed tools: {ALLOWED_TOOL_NAMES}",
                "sources": [],
            }

        if tool_name == "get_user_courses":
            return ALLOWED_TOOLS[tool_name]()
        elif tool_name == "search_courses":
            return ALLOWED_TOOLS[tool_name](arguments.get("query", ""))
        else:
            return ALLOWED_TOOLS[tool_name](
                arguments.get("query", fallback_query)
            )
    except Exception as exc:
        return {"answer": f"Tool execution error: {exc}", "sources": []}


def _summarize(tool_name: str, tool_result: dict, query: str) -> str:
    """Send the tool result back to the LLM and ask for a final answer."""
    try:
        prompt = (
            f"User question: {query}\n"
            f"Tool used: {tool_name}\n"
            f"Tool result: {tool_result['answer']}\n\n"
            "Provide a concise final answer to the user."
        )
        return call_llm(
            prompt,
            system_prompt="You are a helpful assistant. Answer using the tool result.",
        )
    except Exception:
        return tool_result["answer"]


def handle_user_query(query: str) -> dict:
    """Run one cycle: request tool call, execute it, summarize the result."""
    try:
        tool_call = _request_tool_call(query)
        tool_name = tool_call.get("tool", "search_knowledge")
        arguments = tool_call.get("arguments", {})

        if not isinstance(arguments, dict):
            arguments = {}

        tool_result = _execute_tool(tool_name, arguments, query)
        final_answer = _summarize(tool_name, tool_result, query)

        return {"answer": final_answer, "sources": tool_result.get("sources", [])}
    except Exception as exc:
        return {"answer": f"Agent error: {exc}", "sources": []}
