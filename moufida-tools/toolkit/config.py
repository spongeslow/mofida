"""Pydantic models for the tool_integrations DB table and API responses."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from pydantic import BaseModel


class ToolState(BaseModel):
    """Full public state of one tool integration, as returned by the API."""
    slug: str
    label: str
    domain: str
    direction: str
    enabled: bool
    config: dict[str, Any]
    config_schema: dict
    last_sync_at: datetime | None = None
    last_error: str | None = None


class SaveToolRequest(BaseModel):
    enabled: bool
    config: dict[str, Any] = {}


class TestToolRequest(BaseModel):
    config: dict[str, Any]
