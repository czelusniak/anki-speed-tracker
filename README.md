# Speed Tracker — Anki Add-on

A minimal floating overlay that shows your real-time study speed while reviewing cards in Anki.

<img width="192" height="136" alt="image" src="https://github.com/user-attachments/assets/d7735bb1-20be-44b3-a8b7-cdd06acf8857" />

## What it shows

During a review session, a small panel appears in the corner of the screen:

| Row | Description |
|-----|-------------|
| `now` | Current pace — last 60s, projected |
| `3m` | Rolling 3-minute average |
| `session` | Average since you started reviewing |
| `total` | Cards reviewed · time elapsed |
| `ETA` | Estimated time to finish the remaining queue |

The overlay appears when the first card is shown and disappears when you exit the reviewer.

## Installation

### Via AnkiWeb
Search for **Speed Tracker** in Anki: **Tools → Add-ons → Get Add-ons...**

### Manual
1. Download or clone this repo
2. Copy the `speed_tracker/` folder into your Anki `addons21/` directory
3. Restart Anki

## Configuration

Edit `speed_tracker/config.py`:

```python
OVERLAY_POSITION = "bottom-right"  # bottom-right | bottom-left | top-right | top-left
OVERLAY_BOTTOM_MARGIN = 72         # increase if overlay overlaps buttons
WINDOW_MINUTES = 3.0               # duration of the middle metric row
IDLE_GAP_SECONDS = 90              # pause threshold that resets the session
```

## How it works

Each card answer records a timestamp in a circular `deque` (max 4096 entries). Rates are computed by counting timestamps within a time window and dividing by elapsed time — no accumulated state, no drift.

Idle detection: if the gap between two answers exceeds `IDLE_GAP_SECONDS`, the session reference resets so long pauses don't skew your averages.

ETA is calculated from the remaining cards in the current deck (`new + learning + review`) divided by the current pace.

## Compatibility

- Anki 23.10+
- Qt5 / Qt6 compatible
- Windows / macOS / Linux
