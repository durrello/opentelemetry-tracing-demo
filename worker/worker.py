"""Worker service — consumes jobs and "ships" the order.

This is the consumer side of the async boundary. For each message we *extract*
the trace context the backend injected, then start our span with that context as
the parent. The result: the worker's span appears under the same trace as the
gateway and backend — the trace does NOT break at the queue.
"""
import time

from common.propagation import extract_context
from common.queue import dequeue
from common.tracing import init_tracing

tracer = init_tracing("worker")

POLL_SECONDS = 1.0


def process_once() -> bool:
    """Process a single message if one is available. Returns True if it did."""
    message = dequeue()
    if message is None:
        return False

    parent_ctx = extract_context(message.trace_context)
    # Starting the span with the extracted context re-parents it onto the
    # producer's trace.
    with tracer.start_as_current_span("worker.ship_order", context=parent_ctx) as span:
        order_id = message.payload.get("order_id", "")
        span.set_attribute("order.id", str(order_id))
        span.add_event("shipping.started")
        time.sleep(0.05)  # pretend to do work
        span.add_event("shipping.completed")
        print(f"[worker] shipped order {order_id}")
    return True


def main() -> None:
    print("[worker] polling for jobs...")
    while True:
        if not process_once():
            time.sleep(POLL_SECONDS)


if __name__ == "__main__":
    main()
