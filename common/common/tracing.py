"""Shared OpenTelemetry tracer setup.

Each service calls ``init_tracing(service_name)`` once at startup. Spans are
exported over OTLP/gRPC to the OpenTelemetry Collector (configured via the
``OTEL_EXPORTER_OTLP_ENDPOINT`` environment variable), which forwards them to
Tempo. Keeping the exporter pointed at the Collector — not directly at the
backend — is the production pattern: apps stay backend-agnostic, and you can
switch Tempo for Jaeger/Datadog/X-Ray by reconfiguring the Collector alone.
"""
from __future__ import annotations

import os

from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

_initialized = False


def init_tracing(service_name: str) -> trace.Tracer:
    """Initialise a global TracerProvider for ``service_name`` and return a tracer.

    Safe to call more than once; only the first call wins.
    """
    global _initialized
    if not _initialized:
        endpoint = os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        resource = Resource.create({SERVICE_NAME: service_name})
        provider = TracerProvider(resource=resource)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=endpoint, insecure=True))
        )
        trace.set_tracer_provider(provider)
        _initialized = True
    return trace.get_tracer(service_name)
