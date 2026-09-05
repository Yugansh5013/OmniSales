"""Groq LLM instances with multi-key rotation."""

from __future__ import annotations

import itertools
import logging
from typing import Literal, Any

from langchain_groq import ChatGroq
from tenacity import retry, retry_if_exception_type, stop_after_attempt, wait_exponential

import os
from .config import get_settings

logger = logging.getLogger(__name__)

# ── LangSmith Tracing Initialization ──
_settings = get_settings()
if _settings.langsmith_api_key:
    os.environ["LANGCHAIN_TRACING_V2"] = "true"
    os.environ["LANGCHAIN_API_KEY"] = _settings.langsmith_api_key
    os.environ["LANGCHAIN_PROJECT"] = _settings.langchain_project or "omnisales"
    logger.info("🔭 LangSmith tracing enabled for project '%s'", os.environ["LANGCHAIN_PROJECT"])


# ── Key rotation pool ──

_key_cycle: itertools.cycle | None = None


def _get_next_key() -> str:
    """Round-robin through the GROQ_API_KEYS pool."""
    global _key_cycle
    settings = get_settings()
    keys = settings.groq_key_pool
    if not keys:
        raise ValueError("GROQ_API_KEYS is empty — set at least one key in .env")
    if _key_cycle is None:
        _key_cycle = itertools.cycle(keys)
    return next(_key_cycle)


# ── LLM Factories ──


def get_complex_llm() -> ChatGroq:
    """Return the 70B model for complex reasoning tasks.

    Used for: risk classification, email drafting, objection handling,
    retention play generation, outreach personalization.
    """
    return ChatGroq(
        model="openai/gpt-oss-120b",
        api_key=_get_next_key(),
        temperature=0.3,
        max_tokens=4096,
    )


def get_fast_llm() -> ChatGroq:
    """Return the 8B model for simple/fast tasks.

    Used for: ICP scoring, churn scoring, entity extraction,
    classification, summarization.
    """
    return ChatGroq(
        model="openai/gpt-oss-20b",
        api_key=_get_next_key(),
        temperature=0.1,
        max_tokens=2048,
    )


def get_llm(complexity: Literal["complex", "fast"] = "complex") -> ChatGroq:
    """Convenience router — pick model by task complexity."""
    if complexity == "fast":
        return get_fast_llm()
    return get_complex_llm()


# Groq published per-token pricing (USD), as of their public pricing page.
_MODEL_RATES = {
    "openai/gpt-oss-120b": {"input": 0.15e-6, "output": 0.75e-6},
    "openai/gpt-oss-20b": {"input": 0.10e-6, "output": 0.50e-6},
}


def usage_from_response(response, model: str = "openai/gpt-oss-120b") -> dict:
    """Extract real token usage + cost from a ChatGroq AIMessage's usage_metadata.

    Returns zeros if the provider didn't attach usage metadata (never invents numbers).
    """
    usage = getattr(response, "usage_metadata", None) or {}
    input_tokens = usage.get("input_tokens", 0) or 0
    output_tokens = usage.get("output_tokens", 0) or 0
    total_tokens = usage.get("total_tokens", input_tokens + output_tokens) or 0
    rates = _MODEL_RATES.get(model, _MODEL_RATES["openai/gpt-oss-120b"])
    cost = input_tokens * rates["input"] + output_tokens * rates["output"]
    return {"tokens_used": total_tokens, "cost": round(cost, 6), "model_used": model}


def build_feedback_block(metadata: dict) -> str:
    """Build a prompt section asking the LLM to revise a rejected draft per human feedback.

    Returns "" when there's no revision feedback in state — the caller's prompt
    template has a bare {feedback_block} slot that collapses to nothing.
    """
    feedback = metadata.get("revision_feedback")
    if not feedback:
        return ""
    previous_draft = metadata.get("previous_draft", "")
    return f"""
## Human Feedback on Previous Draft (you MUST address this)
Previous draft that was rejected:
{previous_draft}

Rep's feedback: {feedback}

Revise the draft to directly address this feedback while still following all instructions below.
"""


@retry(
    stop=stop_after_attempt(4),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    reraise=True,
)
async def ainvoke_with_retry(llm: ChatGroq, messages: Any, **kwargs) -> Any:
    """Invoke LLM with exponential backoff retry to gracefully withstand 429 rate limits."""
    try:
        return await llm.ainvoke(messages, **kwargs)
    except Exception as e:
        err_msg = str(e).lower()
        if "429" in err_msg or "rate limit" in err_msg or "too many requests" in err_msg or "timeout" in err_msg:
            logger.warning("LLM rate limit encountered (%s). Rotating key and retrying with backoff...", e)
            try:
                llm.api_key = _get_next_key()
            except Exception:
                pass
        raise


async def synthesize_natural_reasoning(
    agent_name: str,
    task_type: str,
    target_name: str,
    raw_trace: list[str] | str,
    context: dict | None = None,
) -> str:
    """Use the fast 20B model (openai/gpt-oss-20b) to convert technical execution traces
    into clear, executive-grade natural language strategy and reasoning.
    """
    if isinstance(raw_trace, list):
        trace_text = "\n".join(str(s) for s in raw_trace if s)
    else:
        trace_text = str(raw_trace or "")

    if not trace_text.strip():
        return f"Autonomous {agent_name} agent formulated strategy for {target_name} based on real-time CRM telemetry."

    llm = get_fast_llm()
    ctx_str = f" Context: {context}" if context else ""
    prompt = f"""You are an autonomous enterprise sales AI explaining your strategy to an executive sales director.
Convert the following technical agent execution trace into a concise, professional, executive-grade strategic reasoning briefing (2 to 3 sentences in natural business prose).

Instructions:
- Explain what you observed about the company/deal, the key friction or opportunity, and why you formulated this specific response or strategy.
- STRICT PROHIBITION: Do NOT include JSON, code, dictionary syntax, bullet points, or raw variable names (never output 'Action=', 'Signals=', 'Risk Score=', or brackets).
- Write in confident, persuasive, articulate natural English.

Agent: {agent_name}
Target: {target_name}
Task: {task_type}{ctx_str}

Technical Execution Trace:
{trace_text}

Executive Strategic Reasoning:"""

    try:
        res = await ainvoke_with_retry(llm, prompt)
        content = res.content.strip() if hasattr(res, "content") else str(res).strip()
        if (content.startswith('"') and content.endswith('"')) or (content.startswith("'") and content.endswith("'")):
            content = content[1:-1].strip()
        return content if content else trace_text
    except Exception as e:
        logger.warning("Failed to synthesize natural reasoning with 20b model: %s. Using formatted fallback.", e)
        cleaned = trace_text.replace("Signals=[", "Key signals: ").replace("]", "").replace("'", "")
        return cleaned

