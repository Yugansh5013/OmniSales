"""Approval Queue MCP Server — powers HITL interrupt/resume pattern."""

import json
import logging
from datetime import datetime
from uuid import UUID, uuid4

import asyncpg
import redis.asyncio as redis
from fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

mcp = FastMCP("Approval Queue MCP")

# ── Connection globals ──

_pool: asyncpg.Pool | None = None
_redis: redis.Redis | None = None

DEFAULT_ORG_ID = "a0000000-0000-0000-0000-000000000001"


def _safe_uuid(val: str | None, fallback: str | None = None) -> UUID | None:
    """Safely parse a string to UUID, returning fallback UUID or None on failure."""
    if not val or val == "":
        if fallback:
            return UUID(fallback)
        return None
    try:
        return UUID(str(val))
    except (ValueError, AttributeError):
        if fallback:
            return UUID(fallback)
        return None


async def _get_pool() -> asyncpg.Pool:
    global _pool
    if _pool is None:
        import os
        _pool = await asyncpg.create_pool(
            dsn=os.environ.get("DATABASE_URL", ""),
            min_size=2, max_size=5,
            ssl="require",
        )
    return _pool


async def _get_conn(pool: asyncpg.Pool) -> asyncpg.Connection:
    """Acquire a connection with RLS org_id set so inserts/selects pass the RLS policy."""
    conn = await pool.acquire()
    await conn.execute(f"SET app.current_org_id = '{DEFAULT_ORG_ID}'")
    return conn


async def _get_redis() -> redis.Redis:
    global _redis
    if _redis is None:
        import os
        _redis = redis.from_url(os.environ.get("REDIS_URL", "redis://redis:6379"))
    return _redis


# ── MCP Tools ──


@mcp.tool()
async def queue_for_approval(
    org_id: str,
    agent_name: str,
    task_type: str,
    target_id: str,
    target_name: str,
    draft: str,
    reasoning: str,
    thread_id: str,
    model_used: str = "llama-3.3-70b-versatile",
    tokens_used: int = 0,
    cost: float = 0.0,
) -> dict:
    """Queue a draft for human approval. Creates an agent_task with status=pending_approval.

    Returns the created task ID and status.
    """
    pool = await _get_pool()
    task_uuid = uuid4()
    org_uuid = _safe_uuid(org_id, DEFAULT_ORG_ID)
    target_uuid = _safe_uuid(target_id)  # None is fine — column is nullable

    conn = await _get_conn(pool)
    try:
        await conn.execute(
            """
            INSERT INTO agent_tasks (id, org_id, agent_name, task_type, status, target_id, target_name,
                                     draft, reasoning, thread_id, model_used, tokens_used, cost)
            VALUES ($1, $2, $3, $4, 'pending_approval', $5, $6, $7, $8, $9, $10, $11, $12)
            """,
            task_uuid, org_uuid, agent_name, task_type, target_uuid, target_name,
            draft, reasoning, thread_id, model_used, tokens_used, cost,
        )
        logger.info("✅ Queued approval: %s from %s for %s", task_uuid, agent_name, target_name)
    except Exception as e:
        logger.exception("❌ Failed to insert agent_task: %s", e)
        return {"error": str(e), "task_id": str(task_uuid), "status": "error"}
    finally:
        await pool.release(conn)

    # Broadcast to WebSocket clients via Redis pub/sub
    try:
        r = await _get_redis()
        await r.publish("omnisales:approvals", json.dumps({
            "event": "new_approval",
            "task_id": str(task_uuid),
            "agent_name": agent_name,
            "task_type": task_type,
            "target_name": target_name,
            "timestamp": datetime.utcnow().isoformat(),
        }))
    except Exception as e:
        logger.warning("Redis publish failed (non-fatal): %s", e)

    return {"task_id": str(task_uuid), "status": "pending_approval"}


@mcp.tool()
async def get_approval_status(task_id: str) -> dict:
    """Check the current approval status of a queued task.

    Returns the task details including status, draft, and any feedback.
    """
    pool = await _get_pool()
    task_uuid = _safe_uuid(task_id)
    if not task_uuid:
        return {"error": f"Invalid task_id: {task_id}"}

    conn = await _get_conn(pool)
    try:
        row = await conn.fetchrow(
            "SELECT id, agent_name, task_type, status, target_name, draft, reasoning, feedback, created_at "
            "FROM agent_tasks WHERE id = $1",
            task_uuid,
        )
    finally:
        await pool.release(conn)

    if not row:
        return {"error": f"Task {task_id} not found"}
    result = dict(row)
    # Convert UUID/datetime to strings for JSON serialization
    result["id"] = str(result["id"])
    if result.get("created_at"):
        result["created_at"] = result["created_at"].isoformat()
    return result


@mcp.tool()
async def update_approval(task_id: str, status: str, feedback: str = "") -> dict:
    """Update the approval status of a task.

    Args:
        task_id: UUID of the agent task
        status: 'approved' or 'rejected'
        feedback: Optional human feedback (especially on rejections)

    Returns the updated task status.
    """
    if status not in ("approved", "rejected"):
        return {"error": "Status must be 'approved' or 'rejected'"}

    task_uuid = _safe_uuid(task_id)
    if not task_uuid:
        return {"error": f"Invalid task_id: {task_id}"}

    pool = await _get_pool()
    conn = await _get_conn(pool)
    try:
        await conn.execute(
            "UPDATE agent_tasks SET status = $1, feedback = $2, updated_at = NOW() WHERE id = $3",
            status, feedback, task_uuid,
        )
    finally:
        await pool.release(conn)

    # Broadcast update
    try:
        r = await _get_redis()
        await r.publish("omnisales:approvals", json.dumps({
            "event": "approval_updated",
            "task_id": str(task_uuid),
            "status": status,
            "timestamp": datetime.utcnow().isoformat(),
        }))
    except Exception as e:
        logger.warning("Redis publish failed (non-fatal): %s", e)

    logger.info("Approval updated: %s -> %s", task_id, status)
    return {"task_id": str(task_uuid), "status": status}


@mcp.tool()
async def list_pending_approvals(org_id: str) -> list[dict]:
    """List all pending approval tasks for an organization.

    Returns a list of tasks with status=pending_approval.
    """
    pool = await _get_pool()
    conn = await _get_conn(pool)
    try:
        rows = await conn.fetch(
            """
            SELECT id, agent_name, task_type, status, target_name, draft, reasoning, created_at
            FROM agent_tasks
            WHERE status = 'pending_approval'
            ORDER BY created_at DESC
            """,
        )
    finally:
        await pool.release(conn)

    results = []
    for r in rows:
        d = dict(r)
        d["id"] = str(d["id"])
        if d.get("created_at"):
            d["created_at"] = d["created_at"].isoformat()
        results.append(d)
    return results


if __name__ == "__main__":
    import uvicorn
    mcp_app = mcp.http_app(path="/mcp")
    uvicorn.run(mcp_app, host="0.0.0.0", port=8004)
