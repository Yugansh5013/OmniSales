"""Async PostgreSQL connection pool with RLS support."""

from __future__ import annotations

import logging
from contextlib import asynccontextmanager
from typing import Any

import asyncpg

from .config import get_settings

logger = logging.getLogger(__name__)

_pool: asyncpg.Pool | None = None


import asyncio

async def get_pool() -> asyncpg.Pool:
    """Get or create the global connection pool (singleton) with retry resilience."""
    global _pool
    if _pool is None or getattr(_pool, "_closed", False):
        settings = get_settings()
        for attempt in range(1, 6):
            try:
                _pool = await asyncpg.create_pool(
                    dsn=settings.database_url,
                    min_size=2,
                    max_size=10,
                    ssl="require",  # Required for Neon cloud PostgreSQL
                )
                logger.info("PostgreSQL pool created successfully")
                break
            except Exception as e:
                logger.warning(f"Failed to create PostgreSQL pool (attempt {attempt}/5): {e}")
                if attempt == 5:
                    raise
                await asyncio.sleep(attempt * 1.5)
    return _pool


async def close_pool() -> None:
    """Gracefully close the connection pool."""
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        logger.info("PostgreSQL pool closed")


@asynccontextmanager
async def get_connection(org_id: str | None = None):
    """Acquire a connection with optional RLS org_id set.

    Usage:
        async with get_connection(org_id="org_xyz") as conn:
            rows = await conn.fetch("SELECT * FROM deals")
    """
    pool = await get_pool()
    conn: asyncpg.Connection = await pool.acquire()
    try:
        if org_id:
            try:
                from uuid import UUID
                safe_org_id = str(UUID(str(org_id).strip()))
            except (ValueError, TypeError):
                import re
                if not re.match(r"^[a-zA-Z0-9_\-]+$", str(org_id).strip()):
                    raise ValueError(f"Invalid org_id parameter: {org_id!r}")
                safe_org_id = str(org_id).strip()
            await conn.execute(
                f"SET app.current_org_id = '{safe_org_id}'"
            )
        yield conn
    finally:
        await pool.release(conn)


async def execute(query: str, *args: Any, org_id: str | None = None) -> str:
    """Execute a query (INSERT/UPDATE/DELETE) and return status."""
    async with get_connection(org_id) as conn:
        return await conn.execute(query, *args)


async def fetch_one(query: str, *args: Any, org_id: str | None = None) -> dict | None:
    """Fetch a single row as a dict."""
    async with get_connection(org_id) as conn:
        row = await conn.fetchrow(query, *args)
        return dict(row) if row else None


async def fetch_all(query: str, *args: Any, org_id: str | None = None) -> list[dict]:
    """Fetch multiple rows as a list of dicts."""
    async with get_connection(org_id) as conn:
        rows = await conn.fetch(query, *args)
        return [dict(r) for r in rows]
