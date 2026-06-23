"""Central registry of all ToolIntegration classes.

Tools self-register via the @register decorator.  The registry is keyed by
slug so that the manager can look up tools by their DB slug string.
"""
from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from .base import ToolIntegration

_REGISTRY: dict[str, type[ToolIntegration]] = {}


def register(cls: type[ToolIntegration]) -> type[ToolIntegration]:
    """Class decorator — add the tool to the global registry."""
    _REGISTRY[cls.slug] = cls
    return cls


def get_all() -> list[type[ToolIntegration]]:
    return list(_REGISTRY.values())


def get(slug: str) -> type[ToolIntegration] | None:
    return _REGISTRY.get(slug)


def slugs() -> list[str]:
    return list(_REGISTRY.keys())
