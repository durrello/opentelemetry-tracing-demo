"""Backend service — validates the order and enqueues an async job.

Inbound HTTP context is extracted automatically (Flask instrumentation), so the
backend's spans join the gateway's trace. The interesting part is the *outbound*
async hop: there's no auto-instrumentation for our custom queue, so we manually
inject the current trace context into the message. That's what lets the worker's
spans land in the *same* trace instead of a disconnected one.
"""
from flask import Flask, jsonify, request
from opentelemetry.instrumentation.flask import FlaskInstrumentor

from common.propagation import inject_context
from common.queue import Message, enqueue
from common.tracing import init_tracing

tracer = init_tracing("backend")
app = Flask(__name__)
FlaskInstrumentor().instrument_app(app)


@app.get("/healthz")
def healthz():
    return jsonify(status="ok")


@app.post("/orders")
def create_order():
    body = request.get_json(force=True, silent=True) or {}
    order_id = str(body.get("order_id", ""))
    amount = float(body.get("amount", 0) or 0)

    with tracer.start_as_current_span("backend.create_order") as span:
        span.set_attribute("order.id", order_id)
        span.set_attribute("payment.amount", amount)

        if not order_id:
            span.set_attribute("order.valid", False)
            return jsonify(error="order_id required"), 400
        span.set_attribute("order.valid", True)

        # Manually propagate trace context across the async boundary.
        carrier = inject_context()
        enqueue(Message(payload={"order_id": order_id, "amount": amount},
                        trace_context=carrier))
        span.add_event("job.enqueued", {"order.id": order_id})

    return jsonify(status="accepted", order_id=order_id), 202


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8081)
