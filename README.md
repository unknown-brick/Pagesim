# PageSim v2 — Page Replacement Simulator

**PT 101 · Platform Technologies · Topic 2: Page Replacement (FIFO, LRU, Optimal)**

A clean Tkinter simulator with a two-step welcome flow, an animated frame view,
a fit-to-width trace table, a sidebar, tooltips, light/dark themes and a single
settings popover.

## Run

```bash
python main.py
```

Python 3.9+ with Tkinter is required. Pillow is optional (only for the PNG
screenshot button).

## What changed

| Area | Change |
|---|---|
| Input | `7012` is read as `7 0 1 2`; no spaces required. The full string is shown together in one framed reference strip, not as separate frame inputs. |
| Window | Larger 1360 × 860 start size; the welcome flow uses the full window. |
| Welcome 1 | “Welcome to PageSim” hero, short description, animated FIFO demo, one **Let’s go →** button and a one-time tip bubble. |
| Welcome 2 | One setup screen: reference string (type or generate **9–15** refs), frames (1–5 or custom 1–8), algorithms (pick any of FIFO / LRU / Optimal). |
| New card | **Sidebar → New** opens a compact hover-animated card with the reference input and **Generate** button side by side, frame size, and algorithm toggles. It no longer returns to the welcome screen. |
| Sidebar | New / Compare / Reset / Tests / Help / Theme / Settings, each with a tooltip. |
| Theme | **Sidebar → Theme** switches between refined light and dark palettes; canvas animations and tooltips follow the active palette. |
| Tooltips & feedback | Every main button has a hover tooltip; buttons animate on hover and press. |
| Progress | A progress bar fills during each algorithm step animation, alongside the scrubber. |
| Settings | Speed, animations, fit-to-width, cell size, focus mode, CSV/TXT/PNG export, tests, help and the new card. |
| Table | Auto fit-to-width, drag-to-pan, wheel/Shift-wheel scroll, click-to-jump and adjustable cell size. |
| Animation | Page pop-in, arced flight with a short trail, eviction slide-out, hit pulse, animated comparison bars and a confetti finish. |

## How to use

1. **Welcome → Let’s go**
   - Choose **Type my own** or **Generate**. Generated strings always have 9–15 references; press **↻ Shuffle** for another.
   - Pick 1–5 frames, or **Custom** and enter 1–8.
   - Toggle the algorithms you want. Pick one, two or all three.
   - Press **Start simulation**.
2. **Watch**
   - Play/pause with the centre button or `Space`; step with `‹` / `›` or arrow keys.
   - Drag the scrubber or watch the thin progress bar to jump/track any reference.
   - Click a column in the trace table to inspect that step.
3. **Compare** (appears when two or more algorithms are selected)
   - Shows racing fault bars and a cumulative-fault chart.
4. **Sidebar & settings**
   - Use **New** for a fresh run without replaying the welcome flow.
   - Use **Theme** for light/dark, and **Settings** for playback/table/export options.

## Reading the trace table

| Row | Meaning |
|---|---|
| REF | The reference string; highlighted column = current step |
| Frame 1…n | Frame contents after that reference |
| RESULT | `HIT` (already in memory) or `FAULT` (had to be loaded) |

`Hit % = hits / references`, `Fault % = faults / references`.

## Files

| File | Purpose |
|---|---|
| `main.py` | Starts the app |
| `app.py` | Main window, sidebar, animation, progress bar, table, settings, theme switch |
| `welcome.py` | Two-stage welcome/setup flow |
| `theme.py` | Light/dark palettes, labels, presets, help text |
| `widgets.py` | Flat button, animated switch, tooltips, input parsing, drawing helpers |
| `algorithms.py` | FIFO / LRU / Optimal logic |
| `reports.py` | CSV and TXT export |
| `test_cases.py` | 6 expected-vs-actual cases (18 checks, all pass) |

## Shortcuts

`Space` play/pause · `←/→` step · `Home` reset · `End` skip to end ·
`1–3` algorithm · `4` compare (if enabled) · `F1` help

## References

- Silberschatz, Galvin & Gagne, *Operating System Concepts* — page replacement chapter.
- Course materials for PT 101, Batangas State University.
