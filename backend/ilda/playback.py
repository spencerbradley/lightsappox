"""Stream ILDA points on a timer (true in-frame playback)."""
from __future__ import annotations

import threading
import time
from pathlib import Path
from typing import Callable

from ilda.reader import IldaFrameData, read_ild_file
from ilda.sink import LoggingSink, NullSink, PointSink

DEFAULT_POINTS_PER_SECOND = 30_000.0


def _clamp_speed(speed: float) -> float:
    if not speed or speed <= 0:
        return 1.0
    return max(0.05, min(8.0, float(speed)))


def _stream_points(
    points: list,
    *,
    points_per_second: float,
    speed: float,
    sink: PointSink,
    stop_event: threading.Event | None,
) -> bool:
    if not points:
        return True
    pps = max(100.0, float(points_per_second)) * _clamp_speed(speed)
    interval = 1.0 / pps
    for pt in points:
        if stop_event and stop_event.is_set():
            return False
        sink.send_point(pt.x, pt.y, pt.r, pt.g, pt.b, pt.blank)
        if interval > 0:
            time.sleep(interval)
    return True


def play_ild_file(
    path: Path | str,
    *,
    speed: float = 1.0,
    points_per_second: float = DEFAULT_POINTS_PER_SECOND,
    dwell_seconds: float = 0.0,
    frame_index: int | None = None,
    sink: PointSink | None = None,
    stop_event: threading.Event | None = None,
) -> bool:
    """
    Block until the frame(s) finish streaming (or stop_event is set).

    - frame_index=None: play every frame section in the file in order.
    - frame_index=N: play only that frame section.
    - dwell_seconds: extra hold after each section (scaled by 1/speed).
    """
    out = sink if sink is not None else NullSink()
    log_sink = isinstance(out, LoggingSink)
    try:
        sections = read_ild_file(path)
    except (OSError, ValueError) as e:
        print(f"[ILDA] Failed to read {path!r}: {e}")
        return False

    if frame_index is not None:
        if frame_index < 0 or frame_index >= len(sections):
            print(f"[ILDA] frame_index {frame_index} out of range (0..{len(sections) - 1})")
            return False
        sections = [sections[frame_index]]

    dwell = max(0.0, float(dwell_seconds)) / _clamp_speed(speed)
    for i, section in enumerate(sections):
        if stop_event and stop_event.is_set():
            return False
        if not _stream_points(
            section.points,
            points_per_second=points_per_second,
            speed=speed,
            sink=out,
            stop_event=stop_event,
        ):
            return False
        if dwell > 0:
            if stop_event and stop_event.wait(timeout=dwell):
                return False

    if log_sink:
        out.finish()
    return True


def play_ild_file_async(
    path: Path | str,
    *,
    speed: float = 1.0,
    points_per_second: float = DEFAULT_POINTS_PER_SECOND,
    dwell_seconds: float = 0.0,
    frame_index: int | None = None,
    sink: PointSink | None = None,
    stop_event: threading.Event | None = None,
    on_done: Callable[[bool], None] | None = None,
) -> threading.Thread:
    """Run play_ild_file on a daemon thread; optional on_done(ok) callback."""

    def run() -> None:
        ok = play_ild_file(
            path,
            speed=speed,
            points_per_second=points_per_second,
            dwell_seconds=dwell_seconds,
            frame_index=frame_index,
            sink=sink,
            stop_event=stop_event,
        )
        if on_done:
            on_done(ok)

    thread = threading.Thread(target=run, name="ilda-play-file", daemon=True)
    thread.start()
    return thread
