"""PageSim v2 theme manager: light + dark palettes and shared text."""

LIGHT = {
    "BG": "#f5f7fc", "PANEL": "#ffffff", "CARD": "#eef2f9", "CARD2": "#d8e0ed",
    "STAGE": "#fcfdff", "BORDER": "#dfe5f0", "SHADOW": "#ccd5e4",
    "TEXT": "#1b2436", "MUTED": "#6c7a91", "INK": "#ffffff",
    "HIT": "#18a058", "FAULT": "#e05252", "GOLD": "#d98a00",
    "ACCENT": "#4f46e5", "ACCENT_H": "#6d63f3", "ACCENT_SOFT": "#edf0ff",
    "HIT_BG": "#e7f7ef", "FAULT_BG": "#fdeaea", "HL_BG": "#eef1ff",
    "PAGE_COLORS": ["#ef4444", "#f97316", "#eab308", "#65a30d", "#10b981",
                    "#06b6d4", "#3b82f6", "#8b5cf6", "#ec4899", "#64748b"],
    "ALGO_COL": {"FIFO": "#f97316", "LRU": "#3b82f6", "OPTIMAL": "#10b981"},
}

DARK = {
    "BG": "#0d1424", "PANEL": "#151f33", "CARD": "#1d2940", "CARD2": "#2d3b55",
    "STAGE": "#0f182b", "BORDER": "#293650", "SHADOW": "#070c16",
    "TEXT": "#e8eef9", "MUTED": "#93a2b9", "INK": "#0b1220",
    "HIT": "#38d39f", "FAULT": "#ff6b6b", "GOLD": "#ffb347",
    "ACCENT": "#7c8cff", "ACCENT_H": "#9aa6ff", "ACCENT_SOFT": "#222f52",
    "HIT_BG": "#15382f", "FAULT_BG": "#3d2029", "HL_BG": "#1d2b4d",
    "PAGE_COLORS": ["#ff6b6b", "#ff9f43", "#ffd166", "#a3e635", "#34d399",
                    "#22d3ee", "#60a5fa", "#a78bfa", "#f472b6", "#cbd5e1"],
    "ALGO_COL": {"FIFO": "#ff9f43", "LRU": "#60a5fa", "OPTIMAL": "#34d399"},
}

# Module-level names stay available for `from theme import *`.
for _k, _v in LIGHT.items():
    globals()[_k] = _v

FONT, MONO = "Segoe UI", "Consolas"

APP_TITLE = "PageSim"
COURSE_TAG = "PT 101 · Platform Technologies · Topic 2"
APP_CREDITS = "Group members: (edit APP_CREDITS in theme.py)\nBatangas State University — CICS, Alangilan Campus"

ALL_ALGOS = ["FIFO", "LRU", "OPTIMAL"]
TABS = [("FIFO", "FIFO"), ("LRU", "LRU"), ("OPTIMAL", "OPTIMAL"), ("COMPARE", "COMPARE")]

BLURB = {
    "FIFO": "First In, First Out — evicts the page that has waited longest in memory.",
    "LRU": "Least Recently Used — evicts the page untouched for the longest time.",
    "OPTIMAL": "Optimal — evicts the page needed farthest in the future (the benchmark).",
    "COMPARE": "Same input, three strategies. Fewer faults means a better fit for this workload.",
}

DEFAULT_STATUS = "Ready · SPACE play/pause · ←/→ step · click a column to jump"

PRESETS = {
    "Textbook (20 refs, 3 frames)": ("7 0 1 2 0 3 0 4 2 3 0 3 2 1 2 0 1 7 0 1", 3),
    "Belady's anomaly (3 vs 4 frames)": ("1 2 3 4 1 2 5 1 2 3 4 5", 3),
    "Locality of reference": ("1 2 1 2 3 1 2 1 2 3 4 1 2 1 2", 3),
    "Thrashing (5 pages, 3 frames)": ("1 2 3 4 5 1 2 3 4 5 1 2 3 4 5", 3),
}

HELP_TEXT = """HOW TO USE PAGESIM

1. START
   Let's go > setup card > choose a reference string, frame count and algorithms.
   Typing digits without spaces (e.g. 70123) is split into 7 0 1 2 3.
   Generated strings always contain 9-15 references.

2. WATCH
   The incoming page flies into RAM. A green glow is a HIT; a red glow is a
   PAGE FAULT. If a frame is full, the evicted page slides out with a reason.

3. NAVIGATE
   Use the stepper (prev / play / next) or drag the progress scrubber.
   Click a trace-table column to jump to that reference. Mouse wheel scrolls;
   Shift + wheel scrolls sideways. Fit / size / focus live in Settings.

4. READ THE TABLE
   REF row    : the reference string; the highlighted column is the current step
   Frame rows : frame contents after each reference
   RESULT row : HIT or FAULT
   Hit %      : hits / references      Fault % : faults / references

5. SIDEBAR & SETTINGS
   Sidebar: New simulation, Compare, Reset, Tests, Help, Theme, Settings.
   Settings: playback speed, animations, table size/focus, exports, new card.

SHORTCUTS
   SPACE play/pause | ←/→ step | Home reset | End skip | Enter run | 1-4 algorithm | F1 help
"""


def apply_palette(mode):
    """Switch module colours in place and return the active palette dict."""
    pal = DARK if mode == "dark" else LIGHT
    globals().update(pal)
    return dict(pal)
