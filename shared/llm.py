"""Groq LLM instances with multi-key rotation."""

from __future__ import annotations

import itertools
import logging
from typing import Literal

from langchain_groq import ChatGroq

from .config import get_settings

logger = logging.getLogger(__name__)

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
        model="llama-3.3-70b-versatile",
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
        model="llama-3.1-8b-instant",
        api_key=_get_next_key(),
        temperature=0.1,
        max_tokens=2048,
    )


def get_llm(complexity: Literal["complex", "fast"] = "complex") -> ChatGroq:
    """Convenience router — pick model by task complexity."""
    if complexity == "fast":
        return get_fast_llm()
    return get_complex_llm()
