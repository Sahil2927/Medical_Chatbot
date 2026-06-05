"""Serve Vite production build (frontend/dist) as SPA from FastAPI."""

from __future__ import annotations

import logging
import os
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse

logger = logging.getLogger(__name__)

_RESERVED_EXACT = frozenset({"health", "docs", "redoc", "openapi.json"})
_RESERVED_PREFIXES = ("api/", "static/")


def resolve_frontend_dist(base_dir: Path) -> Path | None:
    """Return dist path when index.html exists, else None."""
    override = os.getenv("FRONTEND_DIST", "").strip()
    dist = Path(override) if override else base_dir / "frontend" / "dist"
    index = dist / "index.html"
    if index.is_file():
        return dist
    return None


def register_production_frontend(application: FastAPI, base_dir: Path) -> bool:
    """
    Register routes to serve the React SPA from frontend/dist.
    Returns True when registered; False when dist is missing (legacy UI stays on /).
    """
    force = os.getenv("SERVE_FRONTEND", "").lower() in ("1", "true", "yes", "force")
    dist = resolve_frontend_dist(base_dir)
    if dist is None:
        if force:
            logger.warning(
                "SERVE_FRONTEND is set but %s is missing — run: cd frontend && npm run build",
                base_dir / "frontend" / "dist",
            )
        return False

    logger.info("Serving MediAssist UI from %s", dist)

    @application.get("/", include_in_schema=False)
    async def spa_root() -> FileResponse:
        return FileResponse(dist / "index.html")

    @application.get("/{full_path:path}", include_in_schema=False)
    async def spa_fallback(full_path: str) -> FileResponse:
        if full_path in _RESERVED_EXACT or full_path.startswith(_RESERVED_PREFIXES):
            raise HTTPException(status_code=404, detail="Not Found")
        candidate = dist / full_path
        if candidate.is_file():
            return FileResponse(candidate)
        return FileResponse(dist / "index.html")

    return True
