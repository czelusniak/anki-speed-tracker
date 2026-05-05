import json
from collections import deque
from pathlib import Path
from time import time
from typing import Optional


_PERSIST_MAX_AGE_S = 7200  # discard timestamps older than 2 h on save/load


class SpeedTracker:
    def __init__(self):
        self._timestamps: deque = deque(maxlen=4096)
        self._session_start: Optional[float] = None
        self._last_answer: Optional[float] = None
        self._total_paused_s: float = 0.0
        self._paused_at: Optional[float] = None

    def pause(self) -> None:
        if self._session_start is not None and self._paused_at is None:
            self._paused_at = time()

    def resume(self) -> None:
        if self._paused_at is not None:
            self._total_paused_s += time() - self._paused_at
            self._paused_at = None

    def _active_elapsed_s(self) -> float:
        if self._session_start is None:
            return 0.0
        now = time()
        elapsed = now - self._session_start - self._total_paused_s
        if self._paused_at is not None:
            elapsed -= now - self._paused_at
        return max(elapsed, 0.0)

    def record_answer(self) -> None:
        now = time()
        if self._session_start is None:
            self._session_start = now
        self._last_answer = now
        self._timestamps.append(now)

    def _rate_in_window(self, window_seconds: float) -> float:
        if not self._timestamps or self._session_start is None:
            return 0.0
        now = time()
        cutoff = now - window_seconds
        effective_start = max(cutoff, self._session_start)
        elapsed_min = (now - effective_start) / 60
        if elapsed_min < 0.05:
            return 0.0
        count = sum(1 for t in self._timestamps if t >= effective_start)
        return count / elapsed_min

    def current_pace(self) -> float:
        return self._rate_in_window(60)

    def window_pace(self, minutes: float) -> float:
        return self._rate_in_window(minutes * 60)

    def session_pace(self) -> float:
        if self._session_start is None or not self._timestamps:
            return 0.0
        elapsed_min = self._active_elapsed_s() / 60
        if elapsed_min < 0.05:
            return 0.0
        count = sum(1 for t in self._timestamps if t >= self._session_start)
        return count / elapsed_min

    def session_summary(self) -> dict:
        if self._session_start is None:
            return {"cards": 0, "elapsed_s": 0.0}
        cards = sum(1 for t in self._timestamps if t >= self._session_start)
        return {"cards": cards, "elapsed_s": self._active_elapsed_s()}

    def eta_minutes(self, remaining_cards: int) -> Optional[float]:
        if remaining_cards <= 0:
            return None
        rate = self.current_pace()
        if rate < 0.1:
            return None
        return remaining_cards / rate

    def save(self, path: Path) -> None:
        now = time()
        try:
            data = {
                "timestamps": [t for t in self._timestamps if now - t <= _PERSIST_MAX_AGE_S],
                "session_start": self._session_start,
                "last_answer": self._last_answer,
                "total_paused_s": self._total_paused_s,
            }
            path.write_text(json.dumps(data))
        except Exception:
            pass

    def load(self, path: Path) -> None:
        try:
            data = json.loads(path.read_text())
            now = time()
            timestamps = [t for t in data.get("timestamps", []) if now - t <= _PERSIST_MAX_AGE_S]
            self._timestamps = deque(timestamps, maxlen=4096)
            last_answer = data.get("last_answer")
            if last_answer and (now - last_answer) <= _PERSIST_MAX_AGE_S:
                self._session_start = data.get("session_start")
                self._last_answer = last_answer
                self._total_paused_s = data.get("total_paused_s", 0.0)
        except Exception:
            pass

    def reset(self) -> None:
        self._timestamps.clear()
        self._session_start = None
        self._last_answer = None
        self._total_paused_s = 0.0
        self._paused_at = None
