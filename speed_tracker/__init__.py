from pathlib import Path
from typing import Optional

from aqt import gui_hooks, mw
from aqt.reviewer import Reviewer
from .tracker import SpeedTracker
from .overlay import SpeedOverlay

_STATE_PATH = Path(__file__).parent / "state.json"

tracker = SpeedTracker()
tracker.load(_STATE_PATH)
overlay: Optional[SpeedOverlay] = None


def _on_answer(reviewer: Reviewer, card, ease: int) -> None:
    tracker.record_answer()


def _on_show_question(card) -> None:
    global overlay
    tracker.resume()
    # Parent to mw (not mw.reviewer.web) so the widget renders above
    # the WebEngineView GPU surface without compositing issues.
    if overlay is None and mw.reviewer is not None:
        overlay = SpeedOverlay(mw, tracker)
        overlay.show()


def _on_reviewer_end() -> None:
    global overlay
    if overlay is not None:
        overlay.stop()
        overlay.hide()
        overlay.deleteLater()
        overlay = None
    tracker.pause()
    tracker.save(_STATE_PATH)


def _on_profile_will_close() -> None:
    tracker.reset()
    try:
        _STATE_PATH.unlink(missing_ok=True)
    except Exception:
        pass


gui_hooks.reviewer_did_answer_card.append(_on_answer)
gui_hooks.reviewer_did_show_question.append(_on_show_question)
gui_hooks.reviewer_will_end.append(_on_reviewer_end)
gui_hooks.profile_will_close.append(_on_profile_will_close)
