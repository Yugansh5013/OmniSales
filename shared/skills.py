"""Shared Skill Framework — Structured, discoverable skills for OmniSales agents.

Each skill is a callable unit with:
- A name, description, and input/output JSON schema (A2A-compatible)
- An async execute() method that wraps LLM + MCP tool calls
- Registration with an agent's skill registry for discoverability
"""

from __future__ import annotations

import json
import logging
from dataclasses import dataclass, field
from typing import Any, Callable, Awaitable, Optional

logger = logging.getLogger(__name__)


@dataclass
class SkillInput:
    """JSON Schema definition for a skill's input."""
    properties: dict[str, dict]
    required: list[str] = field(default_factory=list)

    def to_schema(self) -> dict:
        return {
            "type": "object",
            "properties": self.properties,
            "required": self.required,
        }


@dataclass
class Skill:
    """A structured, callable agent skill.

    Compatible with Google A2A protocol agent card format.
    """
    name: str
    description: str
    agent: str  # Which agent owns this skill
    input_schema: SkillInput
    execute_fn: Callable[..., Awaitable[dict]] | None = None
    tags: list[str] = field(default_factory=list)

    def to_a2a_skill(self) -> dict:
        """Convert to A2A-compatible skill definition."""
        return {
            "name": self.name,
            "description": self.description,
            "tags": self.tags,
            "inputSchema": self.input_schema.to_schema(),
        }

    async def execute(self, **kwargs) -> dict:
        """Execute the skill with the given inputs."""
        if self.execute_fn is None:
            return {"error": f"Skill '{self.name}' has no execute function"}
        try:
            return await self.execute_fn(**kwargs)
        except Exception as e:
            logger.exception("Skill %s failed", self.name)
            return {"error": str(e), "skill": self.name}


class SkillRegistry:
    """Registry of skills for an agent. Supports lookup, listing, and A2A card generation."""

    def __init__(self, agent_name: str, agent_description: str, agent_url: str, version: str = "1.0.0"):
        self.agent_name = agent_name
        self.agent_description = agent_description
        self.agent_url = agent_url
        self.version = version
        self._skills: dict[str, Skill] = {}

    def register(self, skill: Skill) -> None:
        """Register a skill with the agent."""
        self._skills[skill.name] = skill
        logger.info("Registered skill: %s.%s", self.agent_name, skill.name)

    def get(self, name: str) -> Skill | None:
        """Look up a skill by name."""
        return self._skills.get(name)

    def list_skills(self) -> list[Skill]:
        """List all registered skills."""
        return list(self._skills.values())

    def to_agent_card(self) -> dict:
        """Generate an A2A-compatible agent card with all skills."""
        return {
            "name": self.agent_name,
            "description": self.agent_description,
            "url": self.agent_url,
            "version": self.version,
            "capabilities": {
                "streaming": False,
                "pushNotifications": False,
            },
            "skills": [s.to_a2a_skill() for s in self._skills.values()],
        }

    async def execute_skill(self, skill_name: str, **kwargs) -> dict:
        """Execute a skill by name with the given inputs."""
        skill = self.get(skill_name)
        if not skill:
            return {"error": f"Skill '{skill_name}' not found on agent '{self.agent_name}'"}
        return await skill.execute(**kwargs)
