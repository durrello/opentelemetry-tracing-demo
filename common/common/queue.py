"""A tiny file-backed job queue used to demonstrate async context propagation.

This is deliberately minimal — a real system would use SQS, RabbitMQ, Kafka,
etc. The only thing that matters for this demo is that a *message* carries a
``trace_context`` field (a dict produced by ``inject_context``) alongside its
payload, so the consumer can re-parent its spans onto the producer's trace.
"""
from __future__ import annotations

import json
import os
import time
import uuid
from dataclasses import asdict, dataclass, field
from typing import Dict, List, Optional

QUEUE_DIR = os.getenv("QUEUE_DIR", "/tmp/otel-demo-queue")


@dataclass
class Message:
    payload: Dict
    trace_context: Dict[str, str] = field(default_factory=dict)
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


def _ensure_dir() -> None:
    os.makedirs(QUEUE_DIR, exist_ok=True)


def enqueue(message: Message) -> str:
    """Persist a message to the queue directory. Returns the message id."""
    _ensure_dir()
    path = os.path.join(QUEUE_DIR, f"{int(time.time() * 1000)}-{message.id}.json")
    with open(path, "w", encoding="utf-8") as fh:
        json.dump(asdict(message), fh)
    return message.id


def dequeue() -> Optional[Message]:
    """Pop the oldest message, or return None if the queue is empty."""
    _ensure_dir()
    files: List[str] = sorted(f for f in os.listdir(QUEUE_DIR) if f.endswith(".json"))
    if not files:
        return None
    path = os.path.join(QUEUE_DIR, files[0])
    with open(path, "r", encoding="utf-8") as fh:
        data = json.load(fh)
    os.remove(path)
    return Message(**data)
