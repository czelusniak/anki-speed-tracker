from aqt import mw
from aqt.qt import (
    QWidget, QLabel, QVBoxLayout,
    Qt, QTimer, QEvent,
)
from .tracker import SpeedTracker
from .config import (
    UPDATE_INTERVAL_MS, OVERLAY_POSITION,
    OVERLAY_MARGIN, OVERLAY_BOTTOM_MARGIN, WINDOW_MINUTES,
)

# Qt5/Qt6 enum compatibility
try:
    _WA_Translucent = Qt.WidgetAttribute.WA_TranslucentBackground
    _WA_NoMouse = Qt.WidgetAttribute.WA_TransparentForMouseEvents
    _AlignRight = Qt.AlignmentFlag.AlignRight
    _ResizeEvent = QEvent.Type.Resize
except AttributeError:
    _WA_Translucent = Qt.WA_TranslucentBackground          # type: ignore[attr-defined]
    _WA_NoMouse = Qt.WA_TransparentForMouseEvents          # type: ignore[attr-defined]
    _AlignRight = Qt.AlignRight                            # type: ignore[attr-defined]
    _ResizeEvent = QEvent.Resize                           # type: ignore[attr-defined]

STYLE = """
    QWidget#SpeedOverlay {
        background-color: rgba(15, 15, 15, 170);
        border-radius: 8px;
    }
    QLabel {
        color: rgba(220, 220, 220, 215);
        background: transparent;
        font-size: 11px;
        font-family: monospace;
        padding: 1px 8px;
    }
    QLabel#NowLabel {
        color: rgba(255, 255, 255, 235);
        font-size: 12px;
        font-weight: bold;
    }
    QLabel#EtaLabel {
        color: rgba(180, 220, 255, 215);
    }
"""

_ROWS = ("now", "window", "session", "total", "eta")


def _fmt_duration(seconds: float) -> str:
    s = int(seconds)
    h, rem = divmod(s, 3600)
    m, sec = divmod(rem, 60)
    if h:
        return f"{h}:{m:02d}:{sec:02d}"
    return f"{m}:{sec:02d}"


def _remaining_cards() -> int:
    try:
        if mw and mw.col:
            counts = mw.col.sched.counts()
            return int(sum(counts))
    except Exception:
        pass
    return 0


class SpeedOverlay(QWidget):
    def __init__(self, parent: QWidget, tracker: SpeedTracker):
        super().__init__(parent)
        self.tracker = tracker
        self.setObjectName("SpeedOverlay")
        self.setAttribute(_WA_Translucent)
        self.setAttribute(_WA_NoMouse)
        self.setStyleSheet(STYLE)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(6, 6, 6, 6)
        layout.setSpacing(2)

        self._labels: dict = {}
        self._last_text: dict = {}
        for key in _ROWS:
            lbl = QLabel("—", self)
            lbl.setAlignment(_AlignRight)
            if key == "now":
                lbl.setObjectName("NowLabel")
            elif key == "eta":
                lbl.setObjectName("EtaLabel")
            layout.addWidget(lbl)
            self._labels[key] = lbl
            self._last_text[key] = ""

        self._timer = QTimer(self)
        self._timer.timeout.connect(self._refresh)
        self._timer.start(UPDATE_INTERVAL_MS)

        parent.installEventFilter(self)
        self._reposition()
        self._refresh()

    def _refresh(self) -> None:
        now_pace = self.tracker.current_pace()
        win_pace = self.tracker.window_pace(WINDOW_MINUTES)
        sess_pace = self.tracker.session_pace()
        summary = self.tracker.session_summary()
        remaining = _remaining_cards()
        eta = self.tracker.eta_minutes(remaining)

        win_label = f"{int(WINDOW_MINUTES)}m" if WINDOW_MINUTES.is_integer() else f"{WINDOW_MINUTES:g}m"

        texts = {
            "now":     f"now      {now_pace:5.1f} c/m",
            "window":  f"{win_label:<6}  {win_pace:5.1f} c/m",
            "session": f"session  {sess_pace:5.1f} c/m",
            "total":   f"total   {summary['cards']:>3} · {_fmt_duration(summary['elapsed_s'])}",
            "eta":     (f"ETA      ~{_fmt_duration(eta * 60)} ({remaining})"
                        if eta is not None else
                        f"ETA       —  ({remaining})"),
        }

        size_changed = False
        for key, text in texts.items():
            if text != self._last_text[key]:
                self._labels[key].setText(text)
                self._last_text[key] = text
                size_changed = True

        if size_changed:
            self.adjustSize()
            self._reposition()

    def _reposition(self) -> None:
        parent = self.parent()
        if not parent:
            return
        self.adjustSize()
        pw, ph = parent.width(), parent.height()
        ow, oh = self.width(), self.height()

        m = OVERLAY_MARGIN
        mb = OVERLAY_BOTTOM_MARGIN
        try:
            bw = mw.bottomWeb
            if bw and bw.isVisible():
                mb = max(bw.height() + OVERLAY_MARGIN, mb)
        except AttributeError:
            pass
        positions = {
            "bottom-right": (pw - ow - m,  ph - oh - mb),
            "bottom-left":  (m,             ph - oh - mb),
            "top-right":    (pw - ow - m,   m),
            "top-left":     (m,             m),
        }
        x, y = positions.get(OVERLAY_POSITION, positions["bottom-right"])
        self.move(x, y)
        self.raise_()

    def eventFilter(self, obj, event) -> bool:
        if obj is self.parent() and event.type() == _ResizeEvent:
            self._reposition()
        return False

    def stop(self) -> None:
        self._timer.stop()
