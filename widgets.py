"""Reusable widgets, helpers, tooltips and input parsing for PageSim v2."""
import tkinter as tk

import theme
from theme import ACCENT, BORDER, CARD, CARD2, FONT, PANEL, TEXT

# ---- easing / colour -------------------------------------------------------
def ease(t):
    t = max(0.0, min(1.0, t))
    return t * t * (3 - 2 * t)


def ease_out(t):
    t = max(0.0, min(1.0, t))
    return 1 - (1 - t) ** 3


def lerp(a, b, t):
    return a + (b - a) * t


def lerp_color(c1, c2, t):
    c1, c2 = c1.lstrip("#"), c2.lstrip("#")
    return "#%02x%02x%02x" % tuple(
        int(round(lerp(int(c1[i:i + 2], 16), int(c2[i:i + 2], 16), t)))
        for i in (0, 2, 4)
    )


def rrect(c, x0, y0, x1, y1, r=12, **kw):
    r = max(0, min(r, abs(x1 - x0) / 2, abs(y1 - y0) / 2))
    pts = [x0 + r, y0, x1 - r, y0, x1, y0, x1, y0 + r, x1, y1 - r, x1, y1,
           x1 - r, y1, x0 + r, y1, x0, y1, x0, y1 - r, x0, y0 + r, x0, y0]
    return c.create_polygon(pts, smooth=True, **kw)


def parse_pages(text):
    """Turn input into page numbers.

    '7 0 1 2', '7,0,1,2' and '7012' all become [7, 0, 1, 2].
    A run of digits with no separator is treated as individual pages.
    """
    tokens = text.replace(",", " ").split()
    if not tokens:
        raise ValueError("empty")
    out = []
    for token in tokens:
        if not token.isdigit():
            raise ValueError(token)
        if len(token) > 1:
            out.extend(int(ch) for ch in token)
        else:
            out.append(int(token))
    if len(out) > 40:
        raise ValueError("too many")
    return out


# ---- tooltip ---------------------------------------------------------------
class ToolTip:
    """Small hover tooltip that follows the current palette."""

    def __init__(self, widget, text, delay=420):
        self.widget, self.text, self.delay = widget, text, delay
        self.tip = None
        self.job = None
        widget.bind("<Enter>", self._enter, add="+")
        widget.bind("<Leave>", self._leave, add="+")
        widget.bind("<Motion>", self._motion, add="+")

    def _enter(self, e):
        self._cancel()
        self.job = self.widget.after(self.delay, lambda: self._show(e))

    def _motion(self, e):
        if self.tip:
            self.tip.geometry(f"+{e.x_root + 16}+{e.y_root + 16}")

    def _leave(self, _):
        self._cancel()
        self._hide()

    def _cancel(self):
        if self.job:
            self.widget.after_cancel(self.job)
            self.job = None

    def _show(self, e):
        if self.tip:
            return
        self.tip = tk.Toplevel(self.widget)
        self.tip.overrideredirect(True)
        self.tip.attributes("-topmost", True)
        frame = tk.Frame(self.tip, bg=theme.BORDER, padx=1, pady=1)
        frame.pack()
        tk.Label(frame, text=self.text, bg=theme.PANEL, fg=theme.TEXT,
                 font=(FONT, 9), padx=9, pady=5).pack()
        self.tip.geometry(f"+{e.x_root + 16}+{e.y_root + 16}")

    def _hide(self):
        if self.tip:
            self.tip.destroy()
            self.tip = None


def add_tooltip(widget, text):
    return ToolTip(widget, text)


# ---- flat button with hover + click animation ------------------------------
class FlatButton(tk.Label):
    """Flat button with animated hover and a brief press flash."""

    def __init__(self, master, text, command, bg=None, hover=None, fg=None,
                 size=10, padx=14, pady=7, hint="", on_hint=None, **kw):
        bg = bg or CARD
        hover = hover or CARD2
        fg = fg or TEXT
        super().__init__(
            master, text=text, bg=bg, fg=fg, cursor="hand2",
            font=(FONT, size, "bold"), padx=padx, pady=pady,
            highlightthickness=0, **kw
        )
        self.cmd = command
        self.base, self.hover = bg, hover
        self.hint, self.on_hint = hint, on_hint
        self._hover_job = None
        self._press_job = None
        self.bind("<Enter>", self._enter, add="+")
        self.bind("<Leave>", self._leave, add="+")
        self.bind("<ButtonPress-1>", self._press, add="+")
        self.bind("<ButtonRelease-1>", self._release, add="+")

    def _animate_bg(self, target):
        if self._hover_job:
            self.after_cancel(self._hover_job)
        start = self["bg"]
        steps, k = 6, 0

        def tick():
            nonlocal k
            k += 1
            try:
                self.config(bg=lerp_color(start, target, ease(k / steps)))
            except (tk.TclError, ValueError):
                self._hover_job = None
                return
            if k < steps:
                self._hover_job = self.after(16, tick)
            else:
                self._hover_job = None
        tick()

    def _enter(self, _):
        self._animate_bg(self.hover)
        if self.on_hint:
            self.on_hint(self.hint)

    def _leave(self, _):
        self._animate_bg(self.base)
        if self.on_hint:
            self.on_hint("")

    def _press(self, _):
        if self._press_job:
            self.after_cancel(self._press_job)
        self.config(bg=lerp_color(self.hover, "#000000", 0.18))

    def _release(self, e):
        if self._press_job:
            self.after_cancel(self._press_job)
        self._press_job = self.after(110, lambda: self.config(bg=self.base))
        if 0 <= e.x <= self.winfo_width() and 0 <= e.y <= self.winfo_height():
            self.cmd()

    def set_colors(self, base, hover):
        self.base, self.hover = base, hover
        self.config(bg=base)

    def set_text(self, text):
        self.config(text=text)


# ---- animated switch -------------------------------------------------------
class Switch(tk.Canvas):
    """Small animated on/off switch."""

    def __init__(self, master, value=True, command=None, width=46, height=26):
        super().__init__(master, width=width, height=height,
                         bg=master["bg"], highlightthickness=0)
        self._value = bool(value)
        self._command = command
        self._sw, self._sh = width, height
        self._anim = None
        self.bind("<Button-1>", self.toggle)
        self.draw(1.0 if self._value else 0.0)

    def get(self):
        return self._value

    def set(self, value, silent=False):
        value = bool(value)
        if value == self._value and not silent:
            return
        self._value = value
        self.animate(1.0 if value else 0.0)
        if self._command and not silent:
            self._command()

    def toggle(self, _=None):
        self.set(not self._value)

    def animate(self, target):
        if self._anim:
            self.after_cancel(self._anim)
        steps, k = 8, 0
        pos_now = 1.0 - target

        def tick():
            nonlocal k
            k += 1
            self.draw(pos_now + (target - pos_now) * ease(k / steps))
            if k < steps:
                self._anim = self.after(18, tick)
            else:
                self._anim = None
        tick()

    def draw(self, pos):
        self.delete("all")
        w, h, pad = self._sw, self._sh, 3
        self.configure(bg=theme.PANEL)
        rrect(self, 0, 2, w, h - 2, r=(h - 4) / 2,
              fill=lerp_color(theme.CARD2, theme.ACCENT, pos), outline="")
        d = h - 2 * pad
        x0 = pad + (w - 2 * pad - d) * pos
        self.create_oval(x0, pad + 2, x0 + d, pad + 2 + d, fill="#ffffff", outline="")
