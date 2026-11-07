"""Bounded in-memory OSC send history; UDP send is NOT a delivery acknowledgement."""
from __future__ import annotations
from collections import deque
from dataclasses import dataclass
from datetime import datetime

@dataclass(frozen=True)
class SendRecord:
    time: str
    kind: str
    destination: str
    result: str
    preview: str

class SendHistory:
    def __init__(self, limit: int = 100):
        self.records = deque(maxlen=limit)

    def add(self, kind: str, host: str, port: int, message: str, *, error: str = "") -> SendRecord:
        record = SendRecord(datetime.now().strftime("%H:%M:%S"), kind, f"{host}:{port}",
                            f"Error: {error}" if error else "UDP sent (unconfirmed)", message[:100].replace("\n", " / "))
        self.records.appendleft(record)
        return record

    def lines(self) -> list[str]:
        return [f"{r.time} | {r.kind} | {r.destination} | {r.result} | {r.preview}" for r in self.records]
