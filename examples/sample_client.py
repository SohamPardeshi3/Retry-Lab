"""Run after starting RetryLab with RETRYLAB_UPSTREAM_URL set."""

import httpx

PROXY = "http://127.0.0.1:8080"

with httpx.Client(timeout=5) as client:
    for fault in (None, "latency:250", "server_error:503", "rate_limit"):
        headers = {"X-RetryLab-Fault": fault} if fault else {}
        response = client.get(f"{PROXY}/", headers=headers)
        print(f"fault={fault or 'none':18} status={response.status_code} injected={response.headers.get('X-RetryLab-Injected')}")
    print("metrics:", client.get(f"{PROXY}/__retrylab/metrics").json())
