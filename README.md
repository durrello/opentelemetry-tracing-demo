# OpenTelemetry Distributed Tracing Demo

A small, runnable demo of **end-to-end distributed tracing** across multiple services with
[OpenTelemetry](https://opentelemetry.io/) — the vendor-neutral standard for traces, metrics, and
logs. It shows the thing that actually trips people up in practice: **propagating trace context
across service and async boundaries** so one user request appears as **one connected trace**, not
three disconnected ones.

Traces are exported to **Grafana Tempo** and viewed in **Grafana**, all wired up with Docker Compose.

> Built by [Durrell Gemuh](https://durrellgemuh.com) — DevOps & Cloud Engineer, AWS Community Builder.
> Companion to the [observability-stack](https://github.com/durrello/observability-stack) repo.

## What it demonstrates

- **Auto + manual instrumentation** with the OpenTelemetry SDK for Python (Flask + requests).
- **Context propagation over HTTP** (W3C `traceparent`) so `gateway → backend` is one trace.
- **Context propagation over an async boundary** — the backend enqueues a job and the worker picks
  it up, with the trace context carried in the message so the worker's span joins the same trace.
- **A backend collector** (the OpenTelemetry Collector) receiving OTLP and exporting to Tempo —
  the production pattern, instead of apps talking to a backend directly.
- **Custom spans and attributes** (e.g. `order.id`, `payment.amount`) that make traces useful for
  debugging real problems.

## Architecture

```
              ┌─────────┐      HTTP + traceparent      ┌─────────┐
  client ───▶ │ gateway │ ───────────────────────────▶ │ backend │
              └────┬────┘                               └────┬────┘
                   │                                         │ enqueue job
                   │ OTLP                                    │ (trace ctx in message)
                   ▼                                         ▼
            ┌──────────────┐                            ┌────────┐
            │ OTel          │◀────────── OTLP ───────────│ worker │
            │ Collector     │                            └────────┘
            └──────┬───────┘
                   │ OTLP
                   ▼
              ┌────────┐         ┌──────────┐
              │ Tempo  │ ◀────── │ Grafana  │  (view traces)
              └────────┘         └──────────┘
```

All three services and the worker send spans to the **Collector**, which forwards them to **Tempo**.
Because the trace context flows from `gateway → backend → worker`, the four sets of spans stitch into
a single trace you can explore in Grafana.

## Quick start

Requirements: Docker + Docker Compose.

```bash
docker compose up --build
```

Then generate a request:

```bash
curl -X POST localhost:8080/checkout -H 'content-type: application/json' \
  -d '{"order_id": "A-1001", "amount": 42.50}'
```

Open Grafana at <http://localhost:3000> (anonymous access is enabled), go to **Explore → Tempo**, and
**Search** for traces. You'll see one trace spanning `gateway`, `backend`, and `worker`.

## Project layout

```
.
├── gateway/        # public entry — receives the request, calls backend
├── backend/        # validates the order, enqueues a job for the worker
├── worker/         # consumes the job, "ships" the order (async span)
├── common/         # shared OTel setup (tracer provider, propagation helpers)
├── otel-collector-config.yaml
├── tempo.yaml
├── grafana/        # datasource provisioning (Tempo)
├── docker-compose.yml
└── tests/          # unit tests for the propagation helpers
```

## How context propagation works

The whole point of this repo. Two cases:

**Over HTTP (automatic).** The `requests` and Flask auto-instrumentation inject and extract the W3C
`traceparent` header for you — so `gateway`'s outbound call and `backend`'s inbound handler share the
same trace automatically.

**Over a queue (manual).** Auto-instrumentation can't see your custom message bus, so you carry the
context yourself: inject it into the message on the way out, extract it on the way in. That's the
`inject_context` / `extract_context` helpers in [`common/propagation.py`](common/common/propagation.py),
tested in [`tests/`](tests). This is the pattern that fixes the classic "my trace breaks at the queue"
problem.

## Run the tests

```bash
pip install -r requirements-dev.txt
pytest -q
```

## Why this matters

In a distributed system, the hard question during an incident is *"where did the time go across this
whole request?"* A single connected trace answers it in seconds; disconnected spans answer it never.
The skill that makes tracing actually work in production is **propagation** — and the place it most
often breaks is async boundaries. This repo is a minimal, correct reference for getting both right
with OpenTelemetry, so you can point any OTLP backend (Tempo, Jaeger, Datadog, AWS X-Ray via ADOT) at
it without changing your code.

## Related

- [observability-stack](https://github.com/durrello/observability-stack) — full metrics/logs/traces stack
- [kubernetes-monitoring-helm-chart](https://github.com/durrello/kubernetes-monitoring-helm-chart) — observable-by-default app chart
- Blog: *Observability for Serverless: Tracing Lambda with X-Ray and OpenTelemetry* on
  [durrellgemuh.com](https://durrellgemuh.com)

## License

MIT — see [LICENSE](LICENSE).
