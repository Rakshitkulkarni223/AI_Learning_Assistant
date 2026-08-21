import os
import re

from dotenv import load_dotenv

load_dotenv()

from services.llm import call_llm
from services.tools import get_user_courses, search_courses, search_knowledge

TOOLS = {
    "search_knowledge": search_knowledge,
    "search_courses": search_courses,
    "get_user_courses": get_user_courses,
}

ROUTER_SYSTEM_PROMPT = (
    "You are a tool router. Your only job is to pick the best tool for a user question. "
    "Reply with exactly one line in this format:\n"
    "tool_name|argument\n\n"
    "Available tools:\n"
    "- search_knowledge(query): study questions answered from documents\n"
    "- search_courses(query): list available courses matching a keyword; use empty argument for all courses\n"
    "- get_user_courses(): list the courses the user is enrolled in\n\n"
    "Examples:\n"
    "Question: What is React? -> search_knowledge|What is React?\n"
    "Question: What courses are available? -> search_courses|\n"
    "Question: Show me AI courses -> search_courses|AI\n"
    "Question: What courses am I enrolled in? -> get_user_courses|\n"
    "Do not add explanations."
)


def _pick_tool(query: str) -> tuple[str, str]:
    """Ask the LLM to choose a tool and an argument."""
    try:
        prompt = f"Question: {query}\nTool:"
        raw = call_llm(prompt, system_prompt=ROUTER_SYSTEM_PROMPT)

        # Clean up the response and split into tool|argument.
        clean = raw.strip().splitlines()[0]
        clean = clean.strip("`").strip()

        if "|" in clean:
            tool_name, argument = clean.split("|", 1)
        else:
            tool_name = clean
            argument = ""

        tool_name = tool_name.strip().lower()
        argument = argument.strip().strip('"').strip("'")

        if tool_name not in TOOLS:
            return "search_knowledge", query

        return tool_name, argument
    except Exception as exc:
        return "search_knowledge", query


def handle_user_query(query: str) -> dict:
    """Route the user question to the right tool and return the result."""
    try:
        tool_name, argument = _pick_tool(query)

        if tool_name == "get_user_courses":
            result = TOOLS[tool_name]()
        elif tool_name == "search_courses":
            result = TOOLS[tool_name](argument)
        else:
            result = TOOLS[tool_name](argument if argument else query)

        return result
    except Exception as exc:
        return {"answer": f"Agent error: {exc}", "sources": []}
