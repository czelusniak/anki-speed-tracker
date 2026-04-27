from typing import Optional

UPDATE_INTERVAL_MS = 1000
OVERLAY_POSITION = "bottom-right"  # "bottom-left", "top-right", "top-left"
OVERLAY_MARGIN = 14
OVERLAY_BOTTOM_MARGIN = 72  # clears the Anki answer buttons bar

# Gap (seconds) between answers above which session_start is reset.
# Prevents long pauses from polluting the "session" metric.
IDLE_GAP_SECONDS = 90

# Window for the medium-term rate row, in minutes.
WINDOW_MINUTES: float = 3.0
