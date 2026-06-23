"""GitHub integration — pull development velocity metrics to enrich the product profile.

This is a PULL tool: before each diagnostic wave, it polls the GitHub REST API
for the configured repository and boosts evidence tiers on product-readiness
fields that code activity can verify.

Signals collected (last 30 days):
  - Commit frequency (commits/week)
  - Pull request velocity (merged PRs/week)
  - Issue closure rate (% issues closed)

How they map to the StartupProfile:
  - Active commits → boost evidence_tier for offer.product_stage to T3
  - High PR velocity → upgrade evidence_tier for offer.product_stage to T3
  - Issues present → evidence of basic bug-tracking (ops quality)
"""
from __future__ import annotations

import logging
from datetime import datetime, timezone
from typing import Any

import httpx

from ...base import ProfilePatch, TestResult, ToolIntegration
from ...registry import register

logger = logging.getLogger("moufida.tools.github")

_GH_API = "https://api.github.com"
_LOOKBACK_DAYS = 30


@register
class GitHubTool(ToolIntegration):
    slug = "github"
    label = "GitHub"
    domain = "development"
    direction = "pull"

    config_schema = {
        "type": "object",
        "properties": {
            "personal_access_token": {
                "type": "string",
                "title": "Personal Access Token",
                "description": "GitHub PAT with repo read scope (Settings → Developer settings → Tokens)",
                "format": "password",
            },
            "owner": {
                "type": "string",
                "title": "Repository owner",
                "description": "GitHub username or organisation name",
            },
            "repo": {
                "type": "string",
                "title": "Repository name",
                "description": "The repository to monitor (without the owner prefix)",
            },
        },
        "required": ["personal_access_token", "owner", "repo"],
    }

    async def test_connection(self, config: dict) -> TestResult:
        token = config.get("personal_access_token", "").strip()
        owner = config.get("owner", "").strip()
        repo = config.get("repo", "").strip()
        if not token:
            return TestResult(ok=False, message="Personal Access Token is required")
        if not owner or not repo:
            return TestResult(ok=False, message="Repository owner and name are required")
        try:
            async with httpx.AsyncClient(timeout=10.0, headers=_headers(token)) as client:
                resp = await client.get(f"{_GH_API}/repos/{owner}/{repo}")
            if resp.status_code == 404:
                return TestResult(ok=False, message=f"Repository {owner}/{repo} not found or not accessible")
            if resp.status_code != 200:
                return TestResult(ok=False, message=f"GitHub API returned {resp.status_code}")
            data = resp.json()
            return TestResult(ok=True, message=f"Connected — {data.get('full_name')} ({data.get('stargazers_count', 0)} stars)")
        except httpx.HTTPError as exc:
            return TestResult(ok=False, message=str(exc))

    async def enrich_profile(self, profile: dict, config: dict) -> ProfilePatch:
        token = config.get("personal_access_token", "").strip()
        owner = config.get("owner", "").strip()
        repo = config.get("repo", "").strip()
        if not token or not owner or not repo:
            return ProfilePatch()

        try:
            metrics = await _fetch_repo_metrics(token, owner, repo)
        except Exception as exc:
            logger.warning("GitHub fetch failed for %s/%s: %s", owner, repo, exc)
            return ProfilePatch()

        patch = ProfilePatch(metadata={"github": metrics})

        # Active development (≥1 commit in last 30 days) is T3 evidence that
        # the product is past the concept stage.
        if metrics.get("commits_last_30d", 0) > 0:
            patch.evidence_tiers["product_stage"] = "T3"

        # If the profile doesn't yet report a product stage, infer one from
        # the commit history as a blank-fill only.
        offer = profile.get("offer") or {}
        if not offer.get("product_stage"):
            inferred = _infer_product_stage(metrics)
            if inferred:
                patch.fields["offer"] = {**offer, "product_stage": inferred}

        return patch


# ------------------------------------------------------------------ #
# GitHub REST helpers                                                  #
# ------------------------------------------------------------------ #

def _headers(token: str) -> dict:
    return {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }


async def _fetch_repo_metrics(token: str, owner: str, repo: str) -> dict[str, Any]:
    since = datetime.now(timezone.utc).replace(
        day=datetime.now(timezone.utc).day - min(_LOOKBACK_DAYS, datetime.now(timezone.utc).day - 1)
    )
    # Use ISO 8601 for the since param
    since_iso = (
        datetime.now(timezone.utc)
        .replace(hour=0, minute=0, second=0, microsecond=0)
        .__class__(
            datetime.now(timezone.utc).year,
            datetime.now(timezone.utc).month,
            max(1, datetime.now(timezone.utc).day - _LOOKBACK_DAYS),
            tzinfo=timezone.utc,
        )
        .isoformat()
        .replace("+00:00", "Z")
    )

    async with httpx.AsyncClient(timeout=15.0, headers=_headers(token)) as client:
        # Commits in the last 30 days
        commits_resp = await client.get(
            f"{_GH_API}/repos/{owner}/{repo}/commits",
            params={"since": since_iso, "per_page": 100},
        )
        commits_resp.raise_for_status()
        commits = commits_resp.json() if commits_resp.status_code == 200 else []

        # Merged PRs
        prs_resp = await client.get(
            f"{_GH_API}/repos/{owner}/{repo}/pulls",
            params={"state": "closed", "per_page": 50, "sort": "updated", "direction": "desc"},
        )
        prs_resp.raise_for_status()
        prs = prs_resp.json() if prs_resp.status_code == 200 else []

        # Open issues
        issues_resp = await client.get(
            f"{_GH_API}/repos/{owner}/{repo}/issues",
            params={"state": "all", "per_page": 50, "sort": "updated"},
        )
        issues_resp.raise_for_status()
        issues = issues_resp.json() if issues_resp.status_code == 200 else []

    # Only count actual PRs (issues API returns both)
    open_issues = [i for i in issues if "pull_request" not in i and i.get("state") == "open"]
    closed_issues = [i for i in issues if "pull_request" not in i and i.get("state") == "closed"]
    merged_prs = [p for p in prs if p.get("merged_at")]

    total_issues = len(open_issues) + len(closed_issues)
    closure_rate = len(closed_issues) / total_issues if total_issues > 0 else 0

    return {
        "commits_last_30d": len(commits),
        "commits_per_week": round(len(commits) / (_LOOKBACK_DAYS / 7), 1),
        "merged_prs_last_30d": len(merged_prs),
        "open_issues": len(open_issues),
        "issue_closure_rate": round(closure_rate, 2),
        "repo": f"{owner}/{repo}",
    }


def _infer_product_stage(metrics: dict) -> str | None:
    commits = metrics.get("commits_last_30d", 0)
    prs = metrics.get("merged_prs_last_30d", 0)
    if commits == 0:
        return None
    if commits >= 50 and prs >= 10:
        return "live"
    if commits >= 20 and prs >= 3:
        return "beta"
    if commits >= 5:
        return "prototype"
    return "concept"
