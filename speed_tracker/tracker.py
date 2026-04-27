import json
from collections import deque
from pathlib import Path
from time import time
from typing import Optional

from .config import IDLE_GAP_SECONDS

_PERSIST_MAX_AGE_S = 7200  # discard timestamps older than 2 h on save/load


class SpeedTracker:
    def __init__(self):
        self._timestamps: deque = deque(maxlen=4096)
        self._session_start: Optional[float] = None
        self._last_answer: Optional[float] = None

    def record_answer(self) -> None:
        now = time()
        if self._last_answer is None or (now - self._last_answer) > IDLE_GAP_SECONDS:
            # New (sub-)session: long pause invalidates prior session reference.
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
        """Reactive rate over the last 60s (projected if elapsed < 60s)."""
        return self._rate_in_window(60)

    def window_pace(self, minutes: float) -> float:
        return self._rate_in_window(minutes * 60)

    def session_pace(self) -> float:
        """Average since session start (idle-gap aware)."""
        if self._session_start is None or not self._timestamps:
            return 0.0
        elapsed_min = (time() - self._session_start) / 60
        if elapsed_min < 0.05:
            return 0.0
        count = sum(1 for t in self._timestamps if t >= self._session_start)
        return count / elapsed_min

    def session_summary(self) -> dict:
        if self._session_start is None:
            return {"cards": 0, "elapsed_s": 0.0}
        cards = sum(1 for t in self._timestamps if t >= self._session_start)
        return {"cards": cards, "elapsed_s": time() - self._session_start}

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
        except Exception:
            pass

    def reset(self) -> None:
        self._timestamps.clear()
        self._session_start = None
        self._last_answer = None
