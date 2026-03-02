"""Biostatistics phase nodes: agent, diagnostic tool, coding agent.

The coding node auto-executes generated Python scripts via OpenAI Code
Interpreter and returns computed results.  Users can request source code
(Python/R/STATA) as a follow-up.
"""

from __future__ import annotations

import logging
import re

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage

from app.agents.helpers import build_input_text, get_latest_user_message
from app.agents.prompt_composer import get_prompt
from app.agents.prompts import BIOSTATS_PROMPT, CODING_PROMPT, DIAGNOSTIC_PROMPT
from app.agents.state import BiostatisticsOutput, CodingOutput, ResearchState
from app.services.code_executor import execute_python
from app.services.llm import get_chat_model
from app.services.memory import trim_messages

_logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# 1. BiostatisticsAgent -- power/sample size, clarification loop
# ---------------------------------------------------------------------------

async def biostatistics_node(state: ResearchState) -> dict:
    """Guide through statistical lifecycle: power analysis, study design, interpretation.

    If the agent sets ``diagnostic_query``, the diagnostic tool is called automatically
    and its recommendation is appended to the response.
    """

    llm = get_chat_model("biostatistics").with_structured_output(BiostatisticsOutput)

    expertise = state.get("expertise_level", "advanced")
    user_text = build_input_text(state)
    messages = [
        SystemMessage(content=get_prompt(BIOSTATS_PROMPT, expertise, "biostatistics")),
        *trim_messages(state["messages"]),
        HumanMessage(content=user_text),
    ]

    result: BiostatisticsOutput = await llm.ainvoke(messages)

    response_text = result.direct_response_to_user

    # Auto-call diagnostic tool if the agent requested it
    if result.diagnostic_query:
        diagnostic_result = await run_diagnostic(
            result.diagnostic_query, expertise,
        )
        response_text = (
            f"{response_text}\n\n"
            f"### Diagnostic Tool Recommendation\n\n{diagnostic_result}"
        )

    return {
        "messages": [AIMessage(content=response_text)],
        "need_info": result.need_info,
        "forwarded_message": result.forwarded_message,
    }


# ---------------------------------------------------------------------------
# 2. DiagnosticTool -- statistical test selection (used as tool by biostats)
# ---------------------------------------------------------------------------

async def run_diagnostic(query: str, expertise_level: str = "advanced") -> str:
    """Run the diagnostic tool to recommend a statistical test.

    Called as a tool by the biostatistics agent, not as a standalone graph node.
    """

    llm = get_chat_model("diagnostic")

    system_prompt = get_prompt(DIAGNOSTIC_PROMPT, expertise_level, "diagnostic")
    messages = [
        SystemMessage(content=system_prompt),
        HumanMessage(content=query),
    ]

    response = await llm.ainvoke(messages)
    return response.content


# ---------------------------------------------------------------------------
# 3. CodingAgent -- generate & execute OR serve code
# ---------------------------------------------------------------------------

# Patterns that signal the user is requesting source code
# Priority order: python checked first, then r, then stata
_CODE_LANG_PATTERNS = {
    "python": re.compile(r"\bpython\b", re.IGNORECASE),
    "r": re.compile(
        r"\b[Rr]\s+(code|script|version)\b"
        r"|\bin\s+[Rr]\b"
        r"|\b[Rr]\b(?=.*\b(?:code|script)\b)",
    ),
    "stata": re.compile(r"\bstata\b", re.IGNORECASE),
}

_CODE_REQUEST_PATTERN = re.compile(
    r"\b(show|see|give|get|view|display|send)\b.*\b(code|script|program)\b"
    r"|\bcode\b.*\b(python|r\b|stata)\b"
    r"|\bhow\s+(did\s+you|I)\s+calculat"
    r"|\bsee\s+how",
    re.IGNORECASE,
)


def _is_code_request(message: str) -> bool:
    """Return True if the message asks to see source code."""
    return bool(_CODE_REQUEST_PATTERN.search(message))


def _detect_language(message: str) -> str:
    """Detect the requested code language from the user message.

    Defaults to ``"python"`` when no specific language is mentioned.
    """
    for lang, pattern in _CODE_LANG_PATTERNS.items():
        if pattern.search(message):
            return lang
    return "python"


def _format_execution_results(execution_result: dict) -> str:
    """Format code execution results for display to the user."""
    if not execution_result:
        return ""
    if execution_result.get("success"):
        stdout = execution_result.get("stdout", "").strip()
        if not stdout:
            return ""
        return f"\n\n---\n\n**Computed Results**\n\n```text\n{stdout}\n```"
    return (
        f"\n\n*Code execution encountered an issue: "
        f"{execution_result.get('error_message', 'unknown error')}. "
        f"You can ask me for the code to run it yourself.*"
    )


async def _serve_code(
    state: ResearchState,
    language: str,
) -> dict:
    """Return the stored script in the requested language.

    If the language is not Python, translates via LLM.
    """
    stored_script = state.get("stored_python_script", "")

    if not stored_script:
        return {
            "messages": [AIMessage(content="No code is available yet. Let me run the calculation first.")],
            "has_pending_code": False,
            "agent_to_route_to": "",
            "current_phase": "biostatistics",
            "forwarded_message": "",
        }

    if language == "python":
        final_script = stored_script
    else:
        # Translate Python -> R or STATA via LLM
        llm = get_chat_model("coding")
        translate_prompt = (
            f"Translate this Python script to {language.upper()}. "
            f"Return ONLY the translated code, no explanations.\n\n"
            f"```python\n{stored_script}\n```"
        )
        response = await llm.ainvoke([HumanMessage(content=translate_prompt)])
        final_script = response.content

    code_output = {
        "session_id": state.get("session_id", ""),
        "language": language,
        "script": final_script,
    }

    lang_display = language.upper() if language != "r" else "R"

    return {
        "messages": [AIMessage(content=f"Here is the {lang_display} code:")],
        "code_output": code_output,
        "has_pending_code": False,
        "agent_to_route_to": "",
        "current_phase": "biostatistics",
        "forwarded_message": "",
    }


async def coding_node(state: ResearchState) -> dict:
    """Generate & execute Python code, or serve code on follow-up request.

    Path A -- Generate & Execute (default):
      LLM generates a Python script, Code Interpreter executes it,
      results are shown to the user, code is stored for follow-up.

    Path B -- Serve Code (when has_pending_code and user asks for code):
      Returns the stored script in the requested language.
    """

    # Path B: serve previously generated code
    if state.get("has_pending_code") and _is_code_request(
        get_latest_user_message(state),
    ):
        language = _detect_language(get_latest_user_message(state))
        return await _serve_code(state, language)

    # Path A: generate & execute
    llm = get_chat_model("coding").with_structured_output(CodingOutput)

    expertise = state.get("expertise_level", "advanced")
    instruction = state.get("forwarded_message", "")
    messages = [
        SystemMessage(content=get_prompt(CODING_PROMPT, expertise, "coding")),
        *trim_messages(state["messages"]),
        HumanMessage(content=f"Instruction: {instruction}"),
    ]

    result: CodingOutput = await llm.ainvoke(messages)

    response_text = result.direct_response_to_user
    exec_result: dict = {}
    stored_script = ""
    has_pending = False

    if result.python_script:
        execution = await execute_python(result.python_script)
        exec_result = {
            "success": execution.success,
            "stdout": execution.stdout,
            "error_message": execution.error_message,
        }
        response_text += _format_execution_results(exec_result)
        stored_script = result.python_script
        has_pending = True

    return {
        "messages": [AIMessage(content=response_text)],
        "code_output": {},
        "execution_result": exec_result,
        "stored_python_script": stored_script,
        "has_pending_code": has_pending,
        "agent_to_route_to": result.agent_to_route_to,
        "current_phase": result.agent_to_route_to or "biostatistics",
        "forwarded_message": result.forwarded_message,
    }
