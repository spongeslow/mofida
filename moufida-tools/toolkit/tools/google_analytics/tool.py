"""Google Analytics 4 integration — pull web metrics to enrich the marketing profile.

This is a PULL tool: before each diagnostic wave, it fetches the last 30 days
of GA4 data and upgrades the evidence tier on marketing-related profile fields
that GA4 can verify (e.g., mrr proxy, traffic existence).

GA4 data is used to:
  - Boost evidence_tier for market.mrr to T3 if sessions > 0
  - Populate market.nps (proxy via engagement rate) when blank
  - Attach raw GA4 metrics as _tool_metadata for downstream logging
"""
from __future__ import annotations

import asyncio
import json
import logging

from ...base import ProfilePatch, TestResult, ToolIntegration
from ...registry import register

logger = logging.getLogger("moufida.tools.google_analytics")


@register
class GoogleAnalyticsTool(ToolIntegration):
    slug = "google_analytics"
    label = "Google Analytics"
    domain = "marketing"
    direction = "pull"

    config_schema = {
        "type": "object",
        "properties": {
            "service_account_json": {
                "type": "string",
                "title": "Service Account JSON",
                "description": "Paste the full content of your Google service account key JSON (needs Analytics Data API access)",
                "format": "textarea",
            },
            "property_id": {
                "type": "string",
                "title": "GA4 Property ID",
                "description": "Numeric property ID from Google Analytics admin (e.g. 123456789)",
            },
            "lookback_days": {
                "type": "integer",
                "title": "Lookback window (days)",
                "description": "How many days of data to pull",
                "default": 30,
                "minimum": 7,
                "maximum": 90,
            },
        },
        "required": ["service_account_json", "property_id"],
    }

    async def test_connection(self, config: dict) -> TestResult:
        sa_json = config.get("service_account_json", "").strip()
        property_id = config.get("property_id", "").strip()
        if not sa_json:
            return TestResult(ok=False, message="Service account JSON is required")
        if not property_id:
            return TestResult(ok=False, message="GA4 Property ID is required")
        try:
            key_data = json.loads(sa_json)
        except json.JSONDecodeError as exc:
            return TestResult(ok=False, message=f"Invalid JSON: {exc}")
        try:
            metrics = await asyncio.to_thread(_fetch_ga4_summary, key_data, property_id, 7)
            sessions = metrics.get("sessions", 0)
            return TestResult(ok=True, message=f"Connected — {sessions} sessions in the last 7 days")
        except Exception as exc:
            return TestResult(ok=False, message=str(exc))

    async def enrich_profile(self, profile: dict, config: dict) -> ProfilePatch:
        sa_json = config.get("service_account_json", "").strip()
        property_id = config.get("property_id", "").strip()
        days = int(config.get("lookback_days", 30))
        if not sa_json or not property_id:
            return ProfilePatch()
        try:
            key_data = json.loads(sa_json)
        except json.JSONDecodeError:
            return ProfilePatch()

        try:
            metrics = await asyncio.to_thread(_fetch_ga4_summary, key_data, property_id, days)
        except Exception as exc:
            logger.warning("GA4 fetch failed: %s", exc)
            return ProfilePatch()

        patch = ProfilePatch(metadata={"ga4": metrics})

        # Boost evidence tier on mrr if there is measurable web traffic —
        # traffic existence is daemon-level (T3) evidence for market activity.
        if metrics.get("sessions", 0) > 0:
            patch.evidence_tiers["mrr"] = "T3"

        # If the profile has no NPS value, use engagement_rate as a weak proxy.
        # Engagement rate >= 0.5 → NPS-equivalent of ~30, which signals basic
        # product-market fit. Only fills blanks, never overwrites user data.
        market = profile.get("market") or {}
        if not market.get("nps") and metrics.get("engagement_rate", 0) >= 0.5:
            patch.fields["market"] = {**market, "nps": 30}

        return patch


# ------------------------------------------------------------------ #
# Sync helper (runs in thread pool)                                   #
# ------------------------------------------------------------------ #

def _fetch_ga4_summary(key_data: dict, property_id: str, days: int) -> dict:
    try:
        from google.analytics.data_v1beta import BetaAnalyticsDataClient
        from google.analytics.data_v1beta.types import (
            DateRange,
            Dimension,
            Metric,
            RunReportRequest,
        )
        from google.oauth2.service_account import Credentials
    except ImportError as exc:
        raise RuntimeError(f"google-analytics-data not installed: {exc}") from exc

    scopes = ["https://www.googleapis.com/auth/analytics.readonly"]
    creds = Credentials.from_service_account_info(key_data, scopes=scopes)
    client = BetaAnalyticsDataClient(credentials=creds)

    request = RunReportRequest(
        property=f"properties/{property_id}",
        date_ranges=[DateRange(start_date=f"{days}daysAgo", end_date="today")],
        dimensions=[Dimension(name="date")],
        metrics=[
            Metric(name="sessions"),
            Metric(name="activeUsers"),
            Metric(name="engagementRate"),
            Metric(name="conversions"),
        ],
    )
    response = client.run_report(request)

    sessions = active_users = conversions = engagement_sum = row_count = 0
    for row in response.rows:
        sessions += int(row.metric_values[0].value or 0)
        active_users += int(row.metric_values[1].value or 0)
        engagement_sum += float(row.metric_values[2].value or 0)
        conversions += int(row.metric_values[3].value or 0)
        row_count += 1

    return {
        "sessions": sessions,
        "active_users": active_users,
        "engagement_rate": round(engagement_sum / row_count, 4) if row_count else 0,
        "conversions": conversions,
        "lookback_days": days,
    }
