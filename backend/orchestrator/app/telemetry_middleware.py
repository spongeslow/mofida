"""HTTP middleware that records every orchestrator request to ``api_requests``
and seeds the ``request_id`` / ``project_id`` ContextVars so downstream LLM calls
correlate to the request (Phase H, H4)."""
from __future__ import annotations

import asyncio
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from . import telemetry


class TelemetryMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        request_id = request.headers.get("x-request-id") or str(uuid.uuid4())
        project_id = telemetry.extract_project_id(request.url.path)
        rid_token = telemetry.request_id_var.set(request_id)
        pid_token = telemetry.project_id_var.set(project_id)
        timer = telemetry.now_timer()

        status_code = 500
        try:
            response = await call_next(request)
            status_code = response.status_code
            response.headers["X-Request-ID"] = request_id
            return response
        finally:
            duration_ms = timer.elapsed_ms()
            # Skip the noisy SSE stream + health endpoints.
            path = request.url.path
            if not (path.endswith("/events") or path.endswith("/health")
                    or path.startswith("/api/admin/logs")):
                asyncio.create_task(
                    telemetry.record_api_request(
                        request_id, request.method, path, status_code,
                        duration_ms, project_id,
                    )
                )
            telemetry.request_id_var.reset(rid_token)
            telemetry.project_id_var.reset(pid_token)
