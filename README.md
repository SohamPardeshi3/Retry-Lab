# RetryLab

**A local HTTP fault-injection proxy for testing retry and resilience behavior.**

RetryLab sits in front of a development service and lets you deliberately introduce latency, server errors, rate limits, and simulated timeouts. Use it to answer practical questions: Does your client retry too aggressively? Does it respect `Retry-After`? Does a circuit breaker open? How much extra traffic do retries create?

> **Development tool, not a production gateway.** Use only against services you own or are authorized to test. V1 keeps metrics in memory and does not yet implement authentication, persistent metrics, or a production-grade streaming proxy.

## V1 features

- Reverse-proxy requests to `RETRYLAB_UPSTREAM_URL`.
- Per-request fault selection using `X-RetryLab-Fault`.
- Deterministic `latency`, `server_error`, `rate_limit`, and simulated `timeout` scenarios.
- `/__retrylab/health` and `/__retrylab/metrics` endpoints.
- Bounded fault parameters to avoid accidentally creating unbounded delays.
- Unit tests, Dockerfile, Compose example, and GitHub Actions CI.

## Quick start

Requires Python 3.11+.

```bash
git clone https://github.com/SohamPardeshi3/Retry-Lab.git
cd Retry-Lab
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -e '.[dev]'
export RETRYLAB_UPSTREAM_URL=http://127.0.0.1:9000
retrylab
```

Run a test service on port `9000`, then call the proxy on `8080`:

```bash
curl -i http://127.0.0.1:8080/health
curl -i -H 'X-RetryLab-Fault: latency:250' http://127.0.0.1:8080/health
curl -i -H 'X-RetryLab-Fault: server_error:503' http://127.0.0.1:8080/health
curl -i -H 'X-RetryLab-Fault: rate_limit' http://127.0.0.1:8080/health
curl -i -H 'X-RetryLab-Fault: timeout:1500' http://127.0.0.1:8080/health
curl -s http://127.0.0.1:8080/__retrylab/metrics | python -m json.tool
```

Fault parameters are bounded: latency 1–10,000 ms, simulated timeout 1–30,000 ms, and server errors 500–599. Invalid values return HTTP 400.

## Docker

```bash
cp .env.example .env
# Edit RETRYLAB_UPSTREAM_URL for your environment
docker compose up --build
```

The published port is bound to `127.0.0.1` by default. The special hostname `host.docker.internal` is available on Docker Desktop; on Linux, configure a reachable service hostname or use an appropriate host-gateway mapping.

## Fault behavior

| Header value | Behavior | Expected status |
|---|---|---:|
| *(omitted)* | Forward to upstream | Upstream response |
| `latency:250` | Wait 250 ms, then forward | Upstream response |
| `server_error:503` | Return a synthetic server error without calling upstream | 503 |
| `rate_limit` | Return a synthetic rate limit and `Retry-After: 1` | 429 |
| `timeout:1500` | Wait 1.5 seconds and return a simulated timeout response | 504 |

The `timeout` scenario is deliberately a **simulated HTTP 504**, not an upstream socket timeout. This keeps V1 deterministic; a later version can add upstream connection/read timeout injection.

## Metrics

`GET /__retrylab/metrics` returns total requests, response counts by status, injected fault counts, and a small latency summary. Metrics are process-local and reset at restart. This is intentionally simple for local experiments, not a replacement for Prometheus or durable telemetry.

## Test and lint

```bash
pytest
ruff check .
```

## Roadmap

- **V1:** deterministic per-request faults and local metrics.
- **V2:** scenario files, repeatable load/retry experiments, better integration tests, and more precise timeout/connection fault modes.
- **V3:** release hardening, CI coverage, documentation, and benchmark examples with reproducible conditions.

## Safety notes

- Run locally or in a controlled test environment.
- Do not point it at systems without authorization.
- Do not expose the proxy to an untrusted network: V1 has no authentication or request-level access controls.
- The tool does not claim to emulate all TCP, TLS, proxy, or production-network failure modes.

## License

MIT. See [LICENSE](LICENSE).
