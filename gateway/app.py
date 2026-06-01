"""Gateway service — the public entry point.

Receives a /checkout request and calls the backend over HTTP. Trace context is
propagated to the backend *automatically* by the requests instrumentation
(W3C traceparent header), so the gateway span and the backend span share one
trace with no manual work.
"""
import os

import requests
from flask import Flask, jsonify, request
from opentelemetry.instrumentation.flask import FlaskInstrumentor
from opentelemetry.instrumentation.requests import RequestsInstrumentor

from common.tracing import init_tracing

BACKEND_URL = os.getenv("BACKEND_URL", "http://localhost:8081")

tracer = init_tracing("gateway")
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)
RequestsInstrumentor().instrument()


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.post("/checkout")
def checkout():
    body = request.get_json(force=True, silent=True) or {}
    with tracer.start_as_current_span("gateway.checkout") as span:
        span.set_attribute("order.id", str(body.get("order_id", "")))
        # The outbound call is auto-instrumented: traceparent is injected for us.
        resp = requests.post(f"{BACKEND_URL}/orders", json=body, timeout=5)
        span.set_attribute("backend.status_code", resp.status_code)
        return jsonify(gateway="ok", backend=resp.json()), resp.status_code


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8080)
