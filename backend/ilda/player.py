"""ILDA scene playback: stream points from .ild files, then advance the sequencer."""
from __future__ import annotations

import threading
from pathlib import Path

from ilda.playback import DEFAULT_POINTS_PER_SECOND, play_ild_file_async
from ilda.sink import LoggingSink
from models.ildascene import IldaScene


class IldaPlayer:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._ilda_scene_id: str | None = None
        self._frame_ids: list[str] = []
        self._frame_index = 0
        self._beat_synced = True
        self._time_step = 0.1
        self._points_per_second = DEFAULT_POINTS_PER_SECOND
        self._animation_speed = 1.0
        self._dwell_seconds = 0.0
        self._running = False
        self._busy = False
        self._current_path: str | None = None
        self._play_stop = threading.Event()
        self._play_thread: threading.Thread | None = None

    def is_beat_synced(self) -> bool:
        with self._lock:
            return self._beat_synced

    def is_busy(self) -> bool:
        with self._lock:
            return self._busy

    def stop(self) -> None:
        self._play_stop.set()
        play_thread = None
        with self._lock:
            play_thread = self._play_thread
            self._play_thread = None
            self._running = False
            self._busy = False
            self._ilda_scene_id = None
            self._frame_ids = []
            self._frame_index = 0
            self._current_path = None
        if play_thread and play_thread.is_alive():
            play_thread.join(timeout=3.0)
        self._play_stop.clear()

    def _resolve_path(self, frame_id: str) -> Path | None:
        from routes.data import load_ilda_frames

        frames = {f.id: f for f in load_ilda_frames()}
        frame = frames.get(frame_id)
        if not frame or not (frame.path or "").strip():
            return None
        path = Path(frame.path.strip())
        if not path.is_file():
            print(f"[ILDA] Frame file not found: {path}")
            return None
        return path

    def _on_play_done(self, ok: bool) -> None:
        with self._lock:
            self._busy = False
            self._play_thread = None
            self._current_path = None
            running = self._running and ok
            beat_synced = self._beat_synced
        if not running or beat_synced:
            return
        frame_id = self._advance_frame_index()
        if frame_id is not None:
            self._play_frame_id(frame_id)

    def _start_play_path(self, path: Path, frame_id: str) -> bool:
        with self._lock:
            if not self._running:
                return False
            pps = self._points_per_second
            speed = self._animation_speed
            dwell = self._dwell_seconds
        self._play_stop.clear()
        print(
            f"[ILDA] Streaming {path.name!r} ({frame_id!r}) "
            f"@ {pps:.0f} pps × {speed:.2f} speed"
        )
        with self._lock:
            self._busy = True
            self._current_path = str(path)
        sink = LoggingSink(label=frame_id)
        self._play_thread = play_ild_file_async(
            path,
            speed=speed,
            points_per_second=pps,
            dwell_seconds=dwell,
            sink=sink,
            stop_event=self._play_stop,
            on_done=self._on_play_done,
        )
        return True

    def _play_frame_id(self, frame_id: str) -> bool:
        path = self._resolve_path(frame_id)
        if not path:
            print(f"[ILDA] Unknown or missing frame: {frame_id!r}")
            return False
        return self._start_play_path(path, frame_id)

    def _advance_frame_index(self) -> str | None:
        with self._lock:
            if not self._running or not self._frame_ids:
                return None
            self._frame_index = (self._frame_index + 1) % len(self._frame_ids)
            return self._frame_ids[self._frame_index]

    def start_scene(self, ilda_scene: IldaScene | None) -> None:
        self.stop()
        if not ilda_scene or not ilda_scene.ilda_frames:
            return
        with self._lock:
            self._ilda_scene_id = ilda_scene.id
            self._frame_ids = list(ilda_scene.ilda_frames)
            self._frame_index = 0
            self._beat_synced = bool(ilda_scene.beat_synced)
            self._time_step = float(ilda_scene.time_step or 0.1)
            self._points_per_second = float(
                ilda_scene.points_per_second or DEFAULT_POINTS_PER_SECOND
            )
            self._animation_speed = float(ilda_scene.animation_speed or 1.0)
            self._dwell_seconds = float(ilda_scene.dwell_seconds or 0.0)
            self._running = True
            first = self._frame_ids[0]
            mode = "beat" if self._beat_synced else "stream"
        print(
            f"[ILDA] Scene {ilda_scene.id!r} started ({mode}, "
            f"{self._points_per_second:.0f} pps, {self._animation_speed:.2f}×)"
        )
        self._play_frame_id(first)

    def advance_beat(self) -> str | None:
        """Advance one frame on beat after the current stream finishes."""
        with self._lock:
            if not self._running or not self._beat_synced or not self._frame_ids:
                return None
            if self._busy:
                return None
            self._frame_index = (self._frame_index + 1) % len(self._frame_ids)
            frame_id = self._frame_ids[self._frame_index]
        self._play_frame_id(frame_id)
        return frame_id

    def get_state(self) -> dict:
        with self._lock:
            frame_id = (
                self._frame_ids[self._frame_index]
                if self._frame_ids and 0 <= self._frame_index < len(self._frame_ids)
                else ""
            )
            return {
                "ilda_scene_id": self._ilda_scene_id,
                "frame_index": self._frame_index,
                "frame_id": frame_id,
                "beat_synced": self._beat_synced,
                "time_step": self._time_step,
                "points_per_second": self._points_per_second,
                "animation_speed": self._animation_speed,
                "dwell_seconds": self._dwell_seconds,
                "busy": self._busy,
                "current_path": self._current_path or "",
            }


PLAYER = IldaPlayer()
