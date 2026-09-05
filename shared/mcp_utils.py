"""MCP Utility Helpers for unwrapping responses across all agents."""

from __future__ import annotations

import json
from typing import Any


def unwrap_mcp(result: Any) -> dict:
    """Unwrap MCP tool responses into a plain dict.

    Handles:
      - list of content blocks [{"type":"text","text":"..."}] or text objects
      - list of dicts (e.g. SQL rows)
      - JSON encoded string
      - plain dictionary
    """
    if isinstance(result, list):
        for block in result:
            if isinstance(block, dict) and "text" in block:
                try:
                    return json.loads(block["text"])
                except (json.JSONDecodeError, TypeError):
                    return block
            if hasattr(block, "text"):
                try:
                    return json.loads(block.text)
                except (json.JSONDecodeError, TypeError):
                    return {"raw": block.text}
        if result and isinstance(result[0], dict):
            return result[0]
        return {"raw": str(result)}

    if isinstance(result, str):
        try:
            return json.loads(result)
        except (json.JSONDecodeError, TypeError):
            return {"raw": result}

    if isinstance(result, dict):
        return result

    return {}
