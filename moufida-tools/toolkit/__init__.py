"""moufida-tools — pluggable external tool integrations for Moufida.

Import order matters: registry must load before tools so that
each @register decorator fires against an already-initialised dict.
Tools are imported lazily here so that optional third-party SDKs
(notion-client, gspread, …) don't prevent startup when not installed.
"""
from .registry import get_all, get  # noqa: F401
from .manager import ToolManager    # noqa: F401

__all__ = ["ToolManager", "get_all", "get"]
