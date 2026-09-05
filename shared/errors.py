"""Standardized error envelope for all OmniSales FastAPI & FastMCP (Starlette) services.

Ensures every service returns errors formatted as:
{
    "error": {
        "code": "...",
        "message": "...",
        "service": "...",
        "status_code": ...
    }
}

NOTE: FastMCP protocol endpoints (routes starting with /mcp) are intentionally bypassed
so standard JSON-RPC protocol error structures are preserved for MCP clients.
"""

from __future__ import annotations

import logging
from typing import Any

from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.requests import Request
from starlette.responses import JSONResponse

logger = logging.getLogger(__name__)


def setup_error_handlers(app: Any, service_name: str = "service") -> None:
    """Register standardized error handlers using add_exception_handler (compatible with FastAPI and Starlette)."""

    async def http_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Bypass MCP protocol endpoint to preserve JSON-RPC format
        if request.url.path.startswith("/mcp"):
            raise exc

        status_code = getattr(exc, "status_code", 500)
        detail = getattr(exc, "detail", str(exc))
        code = f"HTTP_{status_code}"

        return JSONResponse(
            status_code=status_code,
            content={
                "error": {
                    "code": code,
                    "message": detail if isinstance(detail, (str, dict, list)) else str(detail),
                    "service": service_name,
                    "status_code": status_code,
                }
            },
        )

    async def validation_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Bypass MCP protocol endpoint
        if request.url.path.startswith("/mcp"):
            raise exc

        errors = getattr(exc, "errors", lambda: str(exc))()
        return JSONResponse(
            status_code=422,
            content={
                "error": {
                    "code": "VALIDATION_ERROR",
                    "message": "Request validation failed",
                    "details": errors,
                    "service": service_name,
                    "status_code": 422,
                }
            },
        )

    async def unhandled_exception_handler(request: Request, exc: Exception) -> JSONResponse:
        # Bypass MCP protocol endpoint
        if request.url.path.startswith("/mcp"):
            raise exc

        logger.exception("Unhandled error on %s %s in %s: %s", request.method, request.url.path, service_name, exc)
        return JSONResponse(
            status_code=500,
            content={
                "error": {
                    "code": "INTERNAL_SERVER_ERROR",
                    "message": str(exc) or "An internal server error occurred",
                    "service": service_name,
                    "status_code": 500,
                }
            },
        )

    # Register handlers on Starlette/FastAPI app instance
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
    app.add_exception_handler(500, unhandled_exception_handler)
    app.add_exception_handler(Exception, unhandled_exception_handler)

    # FastAPI-specific HTTPException & ValidationError if available
    try:
        from fastapi import HTTPException as FastAPIHTTPException
        from fastapi.exceptions import RequestValidationError

        app.add_exception_handler(FastAPIHTTPException, http_exception_handler)
        app.add_exception_handler(RequestValidationError, validation_exception_handler)
    except ImportError:
        pass
