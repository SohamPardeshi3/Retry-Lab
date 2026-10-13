""""FastAPI reverse proxy with explicit per-request fault injection."""

from __future__ import annotations

import os
import time
from collections.abc import Iterable

import httpx
from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse, Response

from retrylab.faults import FaultScenario
from retrylab.metrics import Metrics

HOP_BY_HOP_HEADERS = {
    "connection", "keep-alive", "proxy-authenticate", "proxy-authorization",
    "te", "trailers", "transfer-encoding", "upgrade", "host",
}


def _filtered_headers(headers: Iterable[tuple[str, str]]) -> dict[str, str]:
    return {key: value for key, value in headers if key.lower() not in HOP_BY_HOP_HEADERS}


def create_app(upstream_url: str | None = None, *, client_factory=None) -> FastAPI:
    """Create an app; dependency injection makes upstream behavior testable."""
    upstream = (upstream_url or os.getenv("RETRYLAB_UPSTREAM_URL", "")).rstrip("/")
    metrics = Metrics()
    app = FastAPI(title="RetryLab", version="0.1.0", description="HTTP fault-injection proxy")
    app.state.metrics = metrics

    @app.get("/__retrylab/health")
    async def health() -> dict[str, str]:
        return {"status": "ok", "service": "retrylab", "upstream_configured": str(bool(upstream)).lower()}

    @app.get("/__retrylab/metrics")
    async def get_metrics() -> dict:
        return metrics.snapshot()

    async def proxy(request: Request, path: str = "") -> Response:
        started = time.perf_counter()
        fault = "none"
        try:
            scenario = FaultScenario.from_header(request.headers.get("X-RetryLab-Fault"))
        except ValueError as exc:
            return JSONResponse({"error": "invalid_fault_header", "detail": str(exc)}, status_code=400)

        if not upstream:
            return JSONResponse(
                {"error": "upstream_not_configured", "detail": "Set RETRYLAB_UPSTREAM_URL before starting RetryLab."},
                status_code=503,
            )

        fault = scenario.kind
        try:
            if scenario.kind in {"server_error", "rate_limit", "timeout"}:
                if scenario.kind == "timeout":
                    import asyncio
                    await asyncio.sleep(scenario.delay_ms / 1000)
                headers = {"X-RetryLab-Injected": scenario.kind}
                if scenario.kind == "rate_limit":
                    headers["Retry-After"] = str(scenario.retry_after_seconds)
                response = JSONResponse(
                    {"error": "injected_fault", "fault": scenario.kind, "message": "Response intentionally injected by RetryLab."},
                    status_code=scenario.status_code,
                    headers=headers,
                )
            else:
                await scenario.before_upstream()
                query = request.url.query
                target = f"{upstream}/{path}" if path else upstream
                if query:
                    target = f"{target}?{query}"
                body = await request.body()
                headers = _filtered_headers(request.headers.items())
                headers.pop("x-retrylab-fault", None)
                factory = client_factory or httpx.AsyncClient
                async with factory(timeout=10.0, follow_redirects=False) as client:
                    upstream_response = await client.request(
                        method=request.method,
                        url=target,
                        headers=headers,
                        content=body,
                    )
                response_headers = _filtered_headers(upstream_response.headers.items())
                response_headers["X-RetryLab-Injected"] = fault
                response = Response(
                    content=upstream_response.content,
                    status_code=upstream_response.status_code,
                    headers=response_headers,
                    media_type=upstream_response.headers.get("content-type"),
                )
        except httpx.TimeoutException:
            response = JSONResponse({"error": "upstream_timeout"}, status_code=504)
        except httpx.RequestError as exc:
            response = JSONResponse({"error": "upstream_unavailable", "detail": str(exc)}, status_code=502)

        metrics.record(
            status_code=response.status_code,
            fault=fault,
            duration_ms=(time.perf_counter() - started) * 1000,
        )
        return response

    methods = ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS", "HEAD"]

    @app.api_route("/{path:path}", methods=methods, include_in_schema=True)
    async def proxy_path(path: str, request: Request) -> Response:
        if path.startswith("__retrylab/"):
            return JSONResponse({"error": "reserved_path"}, status_code=404)
        return await proxy(request, path)

    @app.api_route("/", methods=methods, include_in_schema=True)
    async def proxy_root(request: Request) -> Response:
        return await proxy(request)

    return app


app = create_app()
