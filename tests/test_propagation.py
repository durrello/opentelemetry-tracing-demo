"""Tests for the async trace-context propagation helpers.

These verify the core guarantee of the demo: a span created in a "producer",
whose context is injected into a carrier and then extracted in a "consumer",
results in the consumer's span sharing the producer's trace id (i.e. the trace
does not break across the queue).
"""
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider

from common.propagation import extract_context, inject_context

# Set up a no-export provider once for the test process.
trace.set_tracer_provider(TracerProvider())
tracer = trace.get_tracer("test")


def test_inject_produces_traceparent():
    with tracer.start_as_current_span("producer"):
        carrier = inject_context()
    assert "traceparent" in carrier
    # W3C traceparent format: version-traceid-spanid-flags
    assert carrier["traceparent"].count("-") == 3


def test_inject_extract_round_trip_preserves_trace_id():
    # Producer side: create a span and capture its context.
    with tracer.start_as_current_span("producer") as producer_span:
        producer_trace_id = producer_span.get_span_context().trace_id
        carrier = inject_context()

    # Consumer side: extract and start a child span under that context.
    parent_ctx = extract_context(carrier)
    with tracer.start_as_current_span("consumer", context=parent_ctx) as consumer_span:
        consumer_trace_id = consumer_span.get_span_context().trace_id

    # The whole point: same trace id across the (simulated) async boundary.
    assert consumer_trace_id == producer_trace_id


def test_extract_empty_carrier_is_safe():
    # An empty/missing carrier must not raise — it just yields no parent.
    ctx = extract_context({})
    with tracer.start_as_current_span("orphan", context=ctx) as span:
        assert span.get_span_context().trace_id != 0
