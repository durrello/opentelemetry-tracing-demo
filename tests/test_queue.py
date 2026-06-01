"""Tests for the tiny file-backed demo queue."""
import os
import tempfile

import common.queue as q
from common.queue import Message, dequeue, enqueue


def setup_function(_):
    # Point the queue at a fresh temp dir for each test.
    q.QUEUE_DIR = tempfile.mkdtemp(prefix="otel-q-test-")


def test_enqueue_then_dequeue_round_trips_payload_and_context():
    msg = Message(payload={"order_id": "A-1"}, trace_context={"traceparent": "x"})
    enqueue(msg)
    got = dequeue()
    assert got is not None
    assert got.payload["order_id"] == "A-1"
    assert got.trace_context["traceparent"] == "x"


def test_dequeue_empty_returns_none():
    assert dequeue() is None


def test_fifo_order():
    enqueue(Message(payload={"n": 1}))
    enqueue(Message(payload={"n": 2}))
    assert dequeue().payload["n"] == 1
    assert dequeue().payload["n"] == 2
