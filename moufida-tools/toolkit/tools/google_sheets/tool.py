"""Google Sheets integration — export financial forecasts and unit economics.

Uses a service account JSON key (uploaded by the user) to write to a
designated spreadsheet.  All I/O is wrapped in asyncio.to_thread so
the synchronous gspread library never blocks the event loop.
"""
from __future__ import annotations

import asyncio
import json
import logging
from datetime import datetime

from ...base import ProfilePatch, TestResult, ToolIntegration
from ...registry import register

logger = logging.getLogger("moufida.tools.google_sheets")

_SCOPES = [
    "https://www.googleapis.com/auth/spreadsheets",
    "https://www.googleapis.com/auth/drive.file",
]

_HEADERS = [
    "Diagnostic Date",
    "Project ID",
    "Sector",
    "Stage",
    "CAC (TND)",
    "LTV (TND)",
    "LTV/CAC Ratio",
    "Gross Margin %",
    "Runway (months)",
    "Burn Rate (TND/mo)",
    "MRR (TND)",
    "Score Market",
    "Score Commercial Offer",
    "Score Innovation",
    "Score Scalability",
    "Score Green",
    "Critical Blockers",
]


@register
class GoogleSheetsTool(ToolIntegration):
    slug = "google_sheets"
    label = "Google Sheets"
    domain = "finance"
    direction = "push"

    config_schema = {
        "type": "object",
        "properties": {
            "service_account_json": {
                "type": "string",
                "title": "Service Account JSON",
                "description": "Paste the full content of your Google service account key JSON file",
                "format": "textarea",
            },
            "spreadsheet_id": {
                "type": "string",
                "title": "Spreadsheet ID",
                "description": "The ID from the spreadsheet URL: docs.google.com/spreadsheets/d/<ID>/",
            },
            "sheet_name": {
                "type": "string",
                "title": "Sheet tab name",
                "description": "Name of the sheet tab to write to",
                "default": "Moufida",
            },
        },
        "required": ["service_account_json", "spreadsheet_id"],
    }

    async def test_connection(self, config: dict) -> TestResult:
        sa_json = config.get("service_account_json", "").strip()
        spreadsheet_id = config.get("spreadsheet_id", "").strip()
        if not sa_json:
            return TestResult(ok=False, message="Service account JSON is required")
        if not spreadsheet_id:
            return TestResult(ok=False, message="Spreadsheet ID is required")
        try:
            key_data = json.loads(sa_json)
        except json.JSONDecodeError as exc:
            return TestResult(ok=False, message=f"Invalid JSON: {exc}")
        try:
            title = await asyncio.to_thread(_open_spreadsheet_title, key_data, spreadsheet_id)
            return TestResult(ok=True, message=f"Connected — spreadsheet: «{title}»")
        except Exception as exc:
            return TestResult(ok=False, message=str(exc))

    async def on_diagnostic_complete(self, project_id, profile, scores, blockers, roadmap, config):
        sa_json = config.get("service_account_json", "").strip()
        spreadsheet_id = config.get("spreadsheet_id", "").strip()
        sheet_name = config.get("sheet_name", "Moufida")
        if not sa_json or not spreadsheet_id:
            return
        try:
            key_data = json.loads(sa_json)
        except json.JSONDecodeError as exc:
            logger.error("Google Sheets — invalid service account JSON: %s", exc)
            return

        row = _build_row(project_id, profile, scores, blockers)
        try:
            await asyncio.to_thread(
                _append_row, key_data, spreadsheet_id, sheet_name, row
            )
        except Exception as exc:
            logger.error("Google Sheets write failed for project=%s: %s", project_id, exc)
            raise


# ------------------------------------------------------------------ #
# Sync helpers (run in thread pool via asyncio.to_thread)            #
# ------------------------------------------------------------------ #

def _get_client(key_data: dict):
    import gspread
    from google.oauth2.service_account import Credentials
    creds = Credentials.from_service_account_info(key_data, scopes=_SCOPES)
    return gspread.authorize(creds)


def _open_spreadsheet_title(key_data: dict, spreadsheet_id: str) -> str:
    gc = _get_client(key_data)
    sh = gc.open_by_key(spreadsheet_id)
    return sh.title


def _append_row(key_data: dict, spreadsheet_id: str, sheet_name: str, row: list) -> None:
    gc = _get_client(key_data)
    sh = gc.open_by_key(spreadsheet_id)
    try:
        ws = sh.worksheet(sheet_name)
    except Exception:
        ws = sh.add_worksheet(title=sheet_name, rows=1000, cols=len(_HEADERS))
        ws.append_row(_HEADERS)
    ws.append_row(row)


def _build_row(project_id: str, profile: dict, scores: dict, blockers: list) -> list:
    finance = profile.get("finance") or {}
    market = profile.get("market") or {}
    cac = finance.get("cac") or 0
    ltv = finance.get("ltv") or 0
    ratio = round(ltv / cac, 2) if cac else 0
    critical_count = sum(1 for b in blockers if b.get("severity") == "critical")
    return [
        datetime.utcnow().strftime("%Y-%m-%d %H:%M"),
        project_id[:8] + "…",
        profile.get("sector", ""),
        profile.get("self_assessed_stage", ""),
        cac,
        ltv,
        ratio,
        finance.get("gross_margin") or 0,
        finance.get("runway_months") or 0,
        finance.get("burn_rate") or 0,
        market.get("mrr") or 0,
        scores.get("market", ""),
        scores.get("commercial_offer", ""),
        scores.get("innovation", ""),
        scores.get("scalability", ""),
        scores.get("green", ""),
        critical_count,
    ]
