"""Output sink for streamed ILDA points (plug in DAC driver later)."""
from __future__ import annotations

from typing import Protocol


class PointSink(Protocol):
    def send_point(self, x: int, y: int, r: int, g: int, b: int, blank: bool) -> None: ...


class NullSink:
    def send_point(self, x: int, y: int, r: int, g: int, b: int, blank: bool) -> None:
        pass


class LoggingSink:
    """Debug sink: logs start and point count, not every point."""

    def __init__(self, label: str = "") -> None:
        self._label = label
        self._sent = 0
        self._drawn = 0

    def send_point(self, x: int, y: int, r: int, g: int, b: int, blank: bool) -> None:
        self._sent += 1
        if not blank:
            self._drawn += 1

    def finish(self) -> None:
        prefix = f"[ILDA sink {self._label}] " if self._label else "[ILDA sink] "
        print(f"{prefix}{self._sent} points ({self._drawn} drawn)")
