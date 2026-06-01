"""Trace-context propagation helpers for async (non-HTTP) boundaries.

HTTP propagation is handled automatically by the Flask/requests
instrumentation. But auto-instrumentation can't see a custom message bus, so
when one service enqueues work for another you must carry the trace context
*in the message yourself* — otherwise the trace "breaks at the queue" and the
consumer's spans land in a separate, disconnected trace.

These two helpers are the whole trick:

- ``inject_context(carrier)`` writes the current span's W3C ``traceparent`` (and
  related fields) into a plain dict you can attach to your message.
- ``extract_context(carrier)`` reads that dict back into a Context the consumer
  can use as the parent of its spans.

They wrap the OpenTelemetry propagation API so application code (and tests) stay
small and explicit.
"""
from __future__ import annotations

from typing import Dict

from opentelemetry import context as otel_context
from opentelemetry import propagate


def inject_context(carrier: Dict[str, str] | None = None) -> Dict[str, str]:
    """Inject the current trace context into (and return) a string->string carrier.

    Call this in the *producer* right before enqueuing a message, then attach the
    returned dict to the message (e.g. as headers/attributes).
    """
    carrier = carrier if carrier is not None else {}
    propagate.inject(carrier)
    return carrier


def extract_context(carrier: Dict[str, str]) -> otel_context.Context:
    """Extract a trace context from a carrier produced by :func:`inject_context`.

    Call this in the *consumer* and pass the result as ``context=`` when starting
    the span, so the consumer's span becomes a child of the producer's span.
    """
    return propagate.extract(carrier or {})
