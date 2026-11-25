"""PageSim v2 - uncluttered Tkinter UI for FIFO / LRU / Optimal page replacement.

Run:  python main.py
Only Python + Tkinter are required (Pillow is optional, for the PNG export).
"""
import math
import os
import random
import sys
import tkinter as tk
from tkinter import filedialog, messagebox

import reports
import test_cases
import theme as theme_mod
from algorithms import run_all
from theme import *
from welcome import WelcomeScreen
from widgets import (FlatButton, Switch, add_tooltip, ease, ease_out,
                     lerp_color, parse_pages, rrect)


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title(f"{APP_TITLE} — Page Replacement Simulator")
        self.configure(bg=BG)
        self.geometry("1360x860")
        self.minsize(1040, 700)
        self.update_idletasks()
        x = (self.winfo_screenwidth() - 1360) // 2
        y = max(0, (self.winfo_screenheight() - 860) // 2 - 20)
        self.geometry(f"+{x}+{y}")

        # ---- state -------------------------------------------------------
        self.refs, self.n = [], 3
        self.results_all, self.results = {}, {}
        self.algos = list(ALL_ALGOS)
        self.mode, self.idx = "FIFO", -1
        self.playing, self.busy, self.token = False, False, 0
        self.speed, self.effects = 1.0, True
        self.zoom, self.fit, self.focus_mode = 1.0, True, False
        self.dark = False
        self._progress_frac, self._progress_job = 0.0, None
        self.IN_X, self.Y0, self.SH = 86, 56, 92
        self.cy = self.Y0 + self.SH / 2
        self.W, self.sw, self.R, self.slot_x = 1000, 100, 30, []
        self.blurb_text = BLURB["FIFO"]
        self.welcome, self.welcome_on = None, False
        self.settings = None
        self._rz, self._tl_job, self._flash_id = None, None, 0
        self._tl_state, self._pt = None, (0, 0)

        # ---- layout ------------------------------------------------------
        self._build_sidebar()
        self.content = tk.Frame(self, bg=BG)
        self.content.pack(side="left", fill="both", expand=True)
        self._build_header()
        self._build_tabs()
        self._build_stage()
        self._build_readout()
        self._build_controls()
        self._build_status()
        self._build_table()
        self._bind_keys()

        self.update_idletasks()
        self.run(refs=[7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3], frames=3,
                 algos=ALL_ALGOS, autoplay=False)
        self.show_welcome()

    # =========================================================== sidebar
    def _build_sidebar(self):
        side = tk.Frame(self, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER, width=86)
        side.pack(side="left", fill="y")
        side.pack_propagate(False)
        self.sidebar = side
        tk.Label(side, text=APP_TITLE, font=(FONT, 12, "bold"), fg=ACCENT,
                 bg=PANEL).pack(pady=(16, 10))

        items = [
            ("＋", "New", self.open_new_card, "Open the new-simulation card"),
            ("⇄", "Compare", self._sidebar_compare, "Compare selected algorithms"),
            ("↺", "Reset", self.reset, "Back to the first reference"),
            ("✓", "Tests", self.show_tests, "Show expected vs actual results"),
            ("?", "Help", self.show_help, "How to use PageSim"),
            ("◐", "Theme", self.toggle_theme, "Switch light / dark mode"),
            ("⚙", "Settings", self.open_settings, "Playback, table and exports"),
        ]
        self.side_btns = []
        for icon, label, cmd, tip in items:
            b = FlatButton(side, f"{icon}\n{label}", cmd, size=9, padx=8,
                           pady=8, bg=PANEL, hover=CARD)
            b.pack(fill="x", padx=8, pady=3)
            add_tooltip(b, tip)
            self.side_btns.append(b)

    def _sidebar_compare(self):
        if "COMPARE" in getattr(self, "tab_btns", {}):
            self.set_mode("COMPARE")
        else:
            self.flash("Select two or more algorithms to compare.", GOLD)

    # =========================================================== small helpers
    def mk(self, parent, text, cmd, **kw):
        return FlatButton(parent, text, cmd, **kw)

    def _build_header(self):
        h = tk.Frame(self.content, bg=BG)
        h.pack(fill="x", padx=24, pady=(16, 6))
        tk.Label(h, text=APP_TITLE, font=(FONT, 23, "bold"), fg=TEXT, bg=BG).pack(side="left")
        tk.Label(h, text="  " + COURSE_TAG, font=(FONT, 10), fg=MUTED, bg=BG).pack(
            side="left", pady=(8, 0))
        tk.Frame(h, bg=BG).pack(side="left", expand=True, fill="x")
        self.gear = FlatButton(h, "⚙", self.open_settings, size=15, padx=11, pady=5,
                               bg=CARD, hover=CARD2)
        self.gear.pack(side="right")
        add_tooltip(self.gear, "Settings: speed, table, exports, theme")

    def _build_tabs(self):
        self.tabbar = tk.Frame(self.content, bg=BG)
        self.tabbar.pack(fill="x", padx=24, pady=(0, 6))
        self.progress = tk.Canvas(self.content, height=6, bg=BG,
                                  highlightthickness=0)
        self.progress.pack(fill="x", padx=24, pady=(0, 4))

    def _rebuild_tabs(self):
        for w in self.tabbar.winfo_children():
            w.destroy()
        self.tab_btns = {}
        names = list(self.algos) + (["COMPARE"] if len(self.algos) > 1 else [])
        for name in names:
            tip = ("Compare all selected algorithms" if name == "COMPARE"
                   else f"Step through {name}")
            b = FlatButton(self.tabbar, name, lambda n=name: self.set_mode(n),
                           size=10, padx=17, pady=6)
            b.pack(side="left", padx=(0, 7))
            add_tooltip(b, tip)
            self.tab_btns[name] = b

    def _build_stage(self):
        strip_card = tk.Frame(self.content, bg=PANEL, highlightthickness=1,
                              highlightbackground=BORDER)
        strip_card.pack(fill="x", padx=24, pady=(0, 4))
        tk.Label(strip_card, text="REFERENCE STRING", font=(FONT, 9, "bold"),
                 fg=MUTED, bg=PANEL).pack(side="left", padx=(14, 8))
        self.ref_strip = tk.Canvas(strip_card, height=28, bg=PANEL,
                                   highlightthickness=0)
        self.ref_strip.pack(side="left", fill="x", expand=True, pady=5)
        self.ref_strip.bind("<Configure>", lambda e: self._draw_ref_strip())

        self.stage = tk.Canvas(self.content, height=236, bg=STAGE,
                               highlightthickness=1, highlightbackground=BORDER)
        self.stage.pack(fill="x", padx=24, pady=2)
        self.stage.bind("<Configure>", self._on_stage_resize)

    def _build_readout(self):
        card = tk.Frame(self.content, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
        card.pack(fill="x", padx=24, pady=6)
        self.readout = card
        left = tk.Frame(card, bg=PANEL)
        left.pack(side="left", fill="x", expand=True, padx=18, pady=9)
        self.step_lbl = tk.Label(left, font=(FONT, 11, "bold"), fg=ACCENT,
                                 bg=PANEL, anchor="w")
        self.step_lbl.pack(fill="x")
        self.reason_lbl = tk.Label(left, font=(FONT, 10), fg=TEXT, bg=PANEL,
                                   anchor="w", justify="left", wraplength=820, height=2)
        self.reason_lbl.pack(fill="x")
        right = tk.Frame(card, bg=PANEL)
        right.pack(side="right", padx=18, pady=9)
        self.hits_lbl = tk.Label(right, font=(FONT, 14, "bold"), fg=HIT,
                                 bg=PANEL, width=9, anchor="w")
        self.hits_lbl.grid(row=0, column=0)
        self.faults_lbl = tk.Label(right, font=(FONT, 14, "bold"), fg=FAULT,
                                   bg=PANEL, width=11, anchor="w")
        self.faults_lbl.grid(row=0, column=1)
        self.bar = tk.Canvas(right, width=230, height=9, bg=CARD,
                             highlightthickness=0)
        self.bar.grid(row=1, column=0, columnspan=2, pady=(4, 0))
        self.rate_lbl = tk.Label(right, font=(FONT, 9), fg=MUTED, bg=PANEL)
        self.rate_lbl.grid(row=2, column=0, columnspan=2)

    def _build_controls(self):
        f = tk.Frame(self.content, bg=BG)
        f.pack(side="bottom", fill="x", padx=24, pady=(4, 6))
        reset_btn = self.mk(f, "↺", self.reset, size=13, padx=10, pady=5,
                            bg=CARD, hover=CARD2)
        reset_btn.pack(side="left", padx=(0, 5))
        add_tooltip(reset_btn, "Reset to the first reference (Home)")

        back_btn = self.mk(f, "‹", self.btn_back, size=15, padx=12, pady=5,
                           bg=CARD, hover=CARD2)
        back_btn.pack(side="left", padx=3)
        add_tooltip(back_btn, "Previous reference (←)")

        self.play_btn = self.mk(f, "▶", self.toggle_play, size=14, padx=20, pady=5,
                                bg=ACCENT, hover=ACCENT_H, fg="#ffffff")
        self.play_btn.pack(side="left", padx=3)
        add_tooltip(self.play_btn, "Play or pause the animation (Space)")

        next_btn = self.mk(f, "›", self.btn_next, size=15, padx=12, pady=5,
                           bg=CARD, hover=CARD2)
        next_btn.pack(side="left", padx=3)
        add_tooltip(next_btn, "Next reference (→)")

        tk.Frame(f, bg=BG, width=14).pack(side="left")
        self.scrub = tk.Canvas(f, height=22, bg=BG, highlightthickness=0)
        self.scrub.pack(side="left", fill="x", expand=True)
        add_tooltip(self.scrub, "Drag the scrubber to jump to any step")
        self.scrub.bind("<ButtonPress-1>", self._scrub_press)
        self.scrub.bind("<B1-Motion>", self._scrub_drag)
        self.scrub.bind("<ButtonRelease-1>", self._scrub_release)
        self.step_count = tk.Label(f, font=(FONT, 10, "bold"), fg=MUTED,
                                   bg=BG, width=9, anchor="e")
        self.step_count.pack(side="left", padx=(10, 0))

    def _build_status(self):
        self.status_lbl = tk.Label(self.content, text=DEFAULT_STATUS, font=(FONT, 9),
                                   fg=MUTED, bg=BG, anchor="w", padx=24, pady=3)
        self.status_lbl.pack(side="bottom", fill="x")

    def _build_table(self):
        outer = tk.Frame(self.content, bg=BG)
        outer.pack(fill="both", expand=True, padx=24, pady=(0, 8))
        hdr = tk.Frame(outer, bg=BG)
        hdr.grid(row=0, column=0, columnspan=3, sticky="ew", pady=(0, 4))
        tk.Label(hdr, text="TRACE TABLE", font=(FONT, 10, "bold"), fg=TEXT,
                 bg=BG).pack(side="left")
        tk.Label(hdr, text="   wheel · drag · click a column to jump",
                 font=(FONT, 9), fg=MUTED, bg=BG).pack(side="left")

        self.lab = tk.Canvas(outer, width=96, bg=STAGE,
                             highlightthickness=1, highlightbackground=BORDER)
        self.lab.grid(row=1, column=0, sticky="ns")
        self.tl = tk.Canvas(outer, bg=STAGE, height=200,
                            highlightthickness=1, highlightbackground=BORDER,
                            xscrollincrement=20, yscrollincrement=20)
        self.tl.grid(row=1, column=1, sticky="nsew")
        self.vsb = tk.Scrollbar(outer, orient="vertical", command=self.tl.yview)
        self.vsb.grid(row=1, column=2, sticky="ns")
        self.hsb = tk.Scrollbar(outer, orient="horizontal", command=self.tl.xview)
        self.hsb.grid(row=2, column=1, sticky="ew")
        outer.grid_rowconfigure(1, weight=1)
        outer.grid_columnconfigure(1, weight=1)
        self.tl.configure(xscrollcommand=self.hsb.set, yscrollcommand=self._on_yscroll)

        for w in (self.tl, self.lab):
            w.bind("<MouseWheel>", self._wheel)
            w.bind("<Button-4>", self._wheel)
            w.bind("<Button-5>", self._wheel)
            w.bind("<ButtonPress-1>", self._press)
            w.bind("<B1-Motion>", lambda e: self.tl.scan_dragto(e.x, e.y, gain=1))
            w.bind("<ButtonRelease-1>", self._release)
        self.tl.bind("<Configure>", self._on_table_resize)

    def _bind_keys(self):
        def guard(fn):
            return lambda e: None if (self.welcome_on or self._typing()) else fn()
        self.bind("<space>", guard(self.toggle_play))
        self.bind("<Right>", guard(self.btn_next))
        self.bind("<Left>", guard(self.btn_back))
        self.bind("<Home>", guard(self.reset))
        self.bind("<End>", guard(self.skip_end))
        self.bind("<Return>", lambda e: self.show_welcome() if self.welcome_on else self.toggle_play())
        self.bind("<F1>", lambda e: self.show_help())
        for k, name in enumerate(ALL_ALGOS, start=1):
            self.bind(str(k), guard(lambda n=name: self.set_mode(n)))
        if len(self.algos) > 1:
            self.bind("4", guard(lambda: self.set_mode("COMPARE")))

    def _typing(self):
        w = self.focus_get()
        return isinstance(w, (tk.Entry, tk.Spinbox)) or w is self.settings

    # =========================================================== status / feedback
    def hint(self, text):
        self.status_lbl.config(text=text or DEFAULT_STATUS, fg=MUTED)

    def flash(self, msg, color=FAULT):
        self._flash_id += 1
        fid = self._flash_id
        self.status_lbl.config(text=msg, fg=color)
        self.after(4000, lambda: fid == self._flash_id and
                   self.status_lbl.config(text=DEFAULT_STATUS, fg=MUTED))

    # =========================================================== welcome / run
    def show_welcome(self):
        if self.welcome_on:
            return
        self.pause()
        self.token += 1
        self.busy = False
        self.welcome_on = True
        self.welcome = WelcomeScreen(
            self, self._start_from_welcome, self.open_settings,
            " ".join(map(str, self.refs)), self.n
        )

    def _start_from_welcome(self, text, frames, algos):
        if self.welcome:
            self.welcome.destroy()
        self.welcome, self.welcome_on = None, False
        self.run(refs=parse_pages(text), frames=frames,
                 algos=algos, autoplay=True)

    def run(self, refs=None, frames=None, algos=None, autoplay=True):
        if refs is None:
            try:
                refs = parse_pages(self.refs_var.get()) if hasattr(self, "refs_var") else []
            except ValueError:
                return self.flash("Enter digits, spaces or commas only.")
            if not refs:
                return self.flash("Enter a reference string first.")
        if any(not isinstance(p, int) or p < 0 for p in refs):
            return self.flash("Page numbers must be whole numbers.")
        self.refs = list(refs)
        self.n = int(frames or self.n)
        self.algos = list(algos or self.algos)
        self.results_all = run_all(self.refs, self.n)
        self.results = {a: self.results_all[a] for a in self.algos}
        self.mode = self.algos[0]
        self.blurb_text = BLURB[self.mode]
        self.pause()
        self.token += 1
        self.busy = False
        self.idx = -1
        self._tl_state = None
        self._rebuild_tabs()
        self.set_mode(self.mode)
        if autoplay:
            self.after(420, self.toggle_play)

    def set_mode(self, key):
        if key not in self.results and key != "COMPARE":
            return
        self.mode = key
        self.blurb_text = BLURB.get(key, "")
        for k, b in getattr(self, "tab_btns", {}).items():
            on = k == key
            b.set_colors(ACCENT if on else CARD, ACCENT_H if on else CARD2)
            b.config(fg="#ffffff" if on else TEXT)
        self.token += 1
        self.busy = False
        self.refresh()

    def refresh(self):
        self.render_stage(self.idx)
        self.update_info(self.idx)
        self.draw_timeline(self.idx)
        self._draw_scrub()
        self._draw_ref_strip()
        self.animate_progress(0 if self.idx < 0 else (self.idx + 1) / len(self.refs))

    # =========================================================== resize helpers
    def _on_stage_resize(self, _=None):
        if self._rz:
            self.after_cancel(self._rz)
        self._rz = self.after(110, self._stage_resized)

    def _stage_resized(self):
        self._rz = None
        if not self.busy and self.results:
            self.render_stage(self.idx)

    # =========================================================== animation core
    def tween(self, ms, fn, done=None, cancelable=True):
        tok = self.token
        total = max(1, int(ms / self.speed / 16))

        def tick(k):
            if cancelable and tok != self.token:
                return
            fn(k / total)
            if k < total:
                self.after(16, tick, k + 1)
            elif done:
                done()
        tick(0)

    # =========================================================== stage drawing
    def layout(self):
        self.W = max(self.stage.winfo_width(), 760)
        left, region, gap = 112, self.W - 170, 14
        self.sw = max(44, min(104, region / self.n - gap))
        total = self.n * self.sw + (self.n - 1) * gap
        x0 = left + (region - total) / 2
        self.slot_x = [x0 + k * (self.sw + gap) for k in range(self.n)]
        self.R = min(self.sw, self.SH) * 0.32

    def chip(self, cx, cy, page, r, tag="dyn", ring=None, scale=1.0):
        r = max(2, r * scale)
        c = self.stage
        c.create_oval(cx - r, cy - r, cx + r, cy + r,
                      fill=PAGE_COLORS[page % 10], outline=ring or "#ffffff",
                      width=4 if ring else 2, tags=tag)
        if r > 10:
            c.create_text(cx, cy, text=str(page),
                          font=(FONT, max(9, int(r * 0.78)), "bold"),
                          fill=INK, tags=tag)

    def banner(self, text, color, scale=1.0):
        self.stage.delete("banner")
        size = max(12, int(20 * scale))
        self.stage.create_text(self.W / 2, 26, text=text, fill=color,
                               font=(FONT, size, "bold"), tags="banner")

    def draw_base(self, frames, glow=None):
        c = self.stage
        c.delete("base")
        for k in range(self.n):
            x = self.slot_x[k]
            col = (glow or {}).get(k)
            rrect(c, x, self.Y0, x + self.sw, self.Y0 + self.SH, r=16,
                  fill=PANEL, outline=col or BORDER, width=4 if col else 1, tags="base")
            if frames[k] is not None:
                self.chip(x + self.sw / 2, self.cy, frames[k], self.R, tag="base")
            else:
                c.create_text(x + self.sw / 2, self.cy, text="empty", fill=MUTED,
                              font=(FONT, 9, "italic"), tags="base")
            c.create_text(x + self.sw / 2, self.Y0 + self.SH + 16,
                          text=f"Frame {k + 1}", fill=MUTED, font=(FONT, 9), tags="base")

    def render_stage(self, i):
        c = self.stage
        c.delete("all")
        self.layout()
        if self.mode == "COMPARE":
            return self.render_compare(i)

        steps = self.results[self.mode]["steps"]
        c.create_text(self.IN_X, self.Y0 - 14, text="INCOMING", fill=MUTED,
                      font=(FONT, 8, "bold"))
        c.create_text(self.slot_x[0], self.Y0 - 14, text="RAM FRAMES", anchor="w",
                      fill=MUTED, font=(FONT, 8, "bold"))
        c.create_text(self.W / 2, 188, text=self.blurb_text, fill=MUTED,
                      font=(FONT, 9), width=self.W - 70, justify="center")
        c.create_text(self.W / 2, 213,
                      text="green = HIT      red = PAGE FAULT", fill=MUTED,
                      font=(FONT, 8))

        if i < 0:
            self.draw_base([None] * self.n)
            return self.banner("Press play to begin", MUTED)

        s = steps[i]
        self.draw_base(s["frames"], {s["slot"]: HIT if s["hit"] else FAULT})
        self.chip(self.IN_X, self.cy, s["page"], self.R)
        self.banner("HIT!" if s["hit"] else "PAGE FAULT!", HIT if s["hit"] else FAULT)

        if i == len(steps) - 1 and not self.playing and not self.busy:
            r = self.results[self.mode]
            self.banner(f"DONE  ·  {r['hits']} hits / {r['faults']} faults", GOLD)

    def render_compare(self, i, t=1.0, prev_i=None):
        c = self.stage
        c.delete("all")
        W = self.W
        algos = self.algos
        x0, x1 = 180, W - 250
        best = min(r["faults"] for r in self.results.values())
        finished = i == len(self.refs) - 1 and t >= 1 and prev_i is None
        title, col = "RACE TO THE FEWEST PAGE FAULTS", MUTED
        if finished:
            winners = " & ".join(a for a in algos if self.results[a]["faults"] == best)
            title, col = "BEST: " + winners, GOLD
        self.banner(title, col, scale=0.95)

        for k, name in enumerate(algos):
            y = 56 + k * 54
            steps = self.results[name]["steps"]
            cur = steps[i]["cum_faults"] if i >= 0 else 0
            hits = steps[i]["cum_hits"] if i >= 0 else 0
            if prev_i is not None:
                prv = steps[prev_i]["cum_faults"] if prev_i >= 0 else 0
                val = prv + (cur - prv) * ease(t)
            else:
                val = cur
            c.create_text(26, y + 16, text=name, anchor="w", fill=ALGO_COL[name],
                          font=(FONT, 13, "bold"))
            rrect(c, x0, y, x1, y + 32, r=10, fill=CARD, outline="")
            w = (x1 - x0) * val / max(1, len(self.refs))
            if w > 22:
                rrect(c, x0, y, x0 + w, y + 32, r=10, fill=ALGO_COL[name], outline="")
            elif w > 2:
                c.create_rectangle(x0, y, x0 + w, y + 32, fill=ALGO_COL[name], outline="")
            c.create_text(x1 + 14, y + 16, text=f"{cur}F / {hits}H", anchor="w",
                          fill=TEXT, font=(FONT, 11, "bold"))
            if finished and self.results[name]["faults"] == best:
                c.create_text(26, y + 45, text="★ BEST", anchor="w", fill=GOLD,
                              font=(FONT, 9, "bold"))

    def confetti(self):
        if not self.effects:
            return
        c, W = self.stage, self.W
        parts = [[random.uniform(0, W), random.uniform(-120, 0),
                  random.uniform(-1.2, 1.2), random.uniform(2, 5),
                  random.choice(PAGE_COLORS + [GOLD])] for _ in range(70)]
        ids = [c.create_rectangle(0, -20, 8, -12, fill=p[4], outline="", tags="confetti")
               for p in parts]

        def upd(t):
            for p, i in zip(parts, ids):
                x = p[0] + p[2] * t * 70
                y = p[1] + p[3] * t * 70
                try:
                    c.coords(i, x, y, x + 8, y + 8)
                except tk.TclError:
                    pass
        self.tween(2000, upd, lambda: c.delete("confetti"), cancelable=False)

    # =========================================================== step animation
    def step_to(self, i, done=None):
        # The progress bar fills while the step animation plays.
        self.animate_progress(0 if i < 0 else (i + 1) / max(1, len(self.refs)))
        if self.mode == "COMPARE":
            self.animate_compare(i, done)
        else:
            self.animate_step(i, done)

    def _settle(self, i, done):
        self.busy = False
        self.render_stage(i)
        self.update_info(i)
        self.draw_timeline(i, full=False)
        self._draw_scrub()
        self._draw_ref_strip()
        if done:
            done()

    def animate_compare(self, i, done=None):
        self.token += 1
        self.busy = True
        self.layout()
        self.tween(380, lambda t: self.render_compare(i, t, i - 1),
                   lambda: self._settle(i, done))

    def animate_step(self, i, done=None):
        self.token += 1
        self.busy = True
        self.layout()
        steps = self.results[self.mode]["steps"]
        s = steps[i]
        prev = [None] * self.n if i == 0 else steps[i - 1]["frames"]
        slot, page, victim, hit = s["slot"], s["page"], s["victim"], s["hit"]
        cx, cy, R = self.IN_X, self.cy, self.R
        sx = self.slot_x[slot] + self.sw / 2
        col = HIT if hit else FAULT
        self.banner("HIT!" if hit else "PAGE FAULT!", col, scale=0.85)

        def pop(t):
            self.stage.delete("dyn")
            self.draw_base(prev)
            e = ease_out(t)
            self.chip(cx, cy, page, R, scale=0.35 + 0.65 * e)
            if hit:
                pulse = R * (1 + 0.55 * math.sin(math.pi * t))
                self.stage.create_oval(sx - pulse, cy - pulse, sx + pulse, cy + pulse,
                                       outline=HIT, width=2, tags="dyn")

        def fly_phase(base_frames):
            def f(t):
                e = ease(t)
                x = cx + (sx - cx) * e
                y = cy - 52 * math.sin(math.pi * e)
                self.stage.delete("dyn")
                self.draw_base(base_frames, {slot: col} if t > 0.82 else None)
                if self.effects and 0.15 < t < 0.9:
                    for q in range(1, 4):
                        tq = max(0, e - q * 0.055)
                        qx = cx + (sx - cx) * tq
                        qy = cy - 52 * math.sin(math.pi * tq)
                        self.chip(qx, qy, page, R * (0.3 + 0.1 * q),
                                  ring=lerp_color(col, "#ffffff", 0.55))
                self.chip(x, y, page, R)
            self.tween(520, f, lambda: self._settle(i, done))

        def evict_phase():
            frames = list(prev)
            frames[slot] = None

            def f(t):
                e = ease(t)
                self.stage.delete("dyn")
                self.draw_base(frames, {slot: FAULT})
                self.chip(cx, cy, page, R)
                self.chip(sx, cy - 62 * e, victim, R * (1 - 0.55 * e), ring=FAULT)
                self.stage.create_text(sx, cy - 62 * e - R - 12, text="EVICTED",
                                       fill=FAULT, font=(FONT, 9, "bold"), tags="dyn")
            self.tween(460, f, lambda: fly_phase(frames))

        if not self.effects:
            return self._settle(i, done)
        self.tween(240, pop, lambda: evict_phase() if victim is not None else fly_phase(prev))

    # =========================================================== readout
    def update_info(self, i):
        N = len(self.refs)
        self.bar.delete("all")
        if i < 0:
            self.step_lbl.config(text=f"READY  ·  {N} references, {self.n} frames")
            self.reason_lbl.config(text="Press play, or drag the scrubber to explore any step.")
            self.hits_lbl.config(text="HITS  0")
            self.faults_lbl.config(text="FAULTS  0")
            self.rate_lbl.config(text="")
            return
        if self.mode == "COMPARE":
            parts = [f"{a}: {'HIT' if self.results[a]['steps'][i]['hit'] else 'FAULT'}"
                     for a in self.algos]
            self.step_lbl.config(text=f"STEP {i + 1} / {N}  ·  reference {self.refs[i]}")
            self.reason_lbl.config(text="     |     ".join(parts))
            for w in (self.hits_lbl, self.faults_lbl, self.rate_lbl):
                w.config(text="")
            return
        s = self.results[self.mode]["steps"][i]
        self.step_lbl.config(text=f"STEP {i + 1} / {N}  ·  reference {s['page']}")
        self.reason_lbl.config(text=s["reason"])
        self.hits_lbl.config(text=f"HITS  {s['cum_hits']}")
        self.faults_lbl.config(text=f"FAULTS  {s['cum_faults']}")
        done = i + 1
        hw = 230 * s["cum_hits"] / done
        self.bar.create_rectangle(0, 0, hw, 9, fill=HIT, outline="")
        self.bar.create_rectangle(hw, 0, 230, 9, fill=FAULT, outline="")
        self.rate_lbl.config(
            text=f"hit {s['cum_hits'] / done * 100:.1f}%   ·   fault {s['cum_faults'] / done * 100:.1f}%")

    # =========================================================== progress + strip
    def _draw_progress(self):
        c = self.progress
        c.delete("all")
        w = c.winfo_width()
        if w < 20:
            return
        frac = self._progress_frac
        c.create_line(0, 3, w, 3, fill=CARD2, width=6, capstyle="round")
        if frac > 0:
            c.create_line(0, 3, w * frac, 3, fill=ACCENT, width=6, capstyle="round")

    def animate_progress(self, target):
        if self._progress_job:
            self.after_cancel(self._progress_job)
        start = self._progress_frac
        steps, k = 8, 0

        def tick():
            nonlocal k
            k += 1
            self._progress_frac = start + (target - start) * ease_out(k / steps)
            self._draw_progress()
            if k < steps:
                self._progress_job = self.after(18, tick)
            else:
                self._progress_job = None
        tick()

    def _draw_ref_strip(self):
        c = self.ref_strip
        c.delete("all")
        w = c.winfo_width()
        if w < 30 or not self.refs:
            return
        n = len(self.refs)
        cw = min(34, (w - 12) / n)
        total = cw * n
        x0 = (w - total) / 2
        for k, page in enumerate(self.refs):
            x = x0 + k * cw
            fill = ACCENT_SOFT if k == self.idx else CARD
            fg = ACCENT if k == self.idx else TEXT
            rrect(c, x + 1, 3, x + cw - 1, 25, r=6, fill=fill, outline="")
            c.create_text(x + cw / 2, 14, text=str(page), fill=fg,
                          font=(FONT, 9, "bold"))

    # =========================================================== scrubber
    def _draw_scrub(self):
        c = self.scrub
        c.delete("all")
        w = c.winfo_width()
        if w < 40:
            return
        x0, x1 = 10, w - 10
        y = 11
        c.create_line(x0, y, x1, y, fill=CARD2, width=4, capstyle="round")
        frac = 0 if self.idx < 0 else (self.idx + 1) / max(1, len(self.refs))
        if frac > 0:
            c.create_line(x0, y, x0 + (x1 - x0) * frac, y, fill=ACCENT,
                          width=4, capstyle="round")
        hx = x0 + (x1 - x0) * frac
        c.create_oval(hx - 7, y - 7, hx + 7, y + 7, fill=ACCENT, outline="#ffffff", width=2)
        self.step_count.config(text=f"{max(0, self.idx + 1)} / {len(self.refs)}")

    def _scrub_press(self, e):
        self.scrub_widget = True
        self._scrub_apply(e.x)

    def _scrub_drag(self, e):
        if getattr(self, "scrub_widget", False):
            self._scrub_apply(e.x)

    def _scrub_release(self, _):
        self.scrub_widget = False

    def _scrub_apply(self, x):
        if not self.refs:
            return
        w = self.scrub.winfo_width()
        x0, x1 = 10, max(11, w - 10)
        frac = max(0.0, min(1.0, (x - x0) / (x1 - x0)))
        self.pause()
        self.token += 1
        self.busy = False
        self.idx = -1 if frac < 0.02 else min(len(self.refs) - 1, int(frac * len(self.refs) - 1))
        self.refresh()

    # =========================================================== trace table
    def metrics(self):
        if self.fit and self.refs and self.tl.winfo_width() > 40:
            cw = max(42, min(116, (self.tl.winfo_width() - 20) // len(self.refs)))
        else:
            cw = int(60 * self.zoom)
        return cw, int(42 * self.zoom), max(8, int(13 * self.zoom))

    def _on_table_resize(self, e):
        if self._tl_job:
            self.after_cancel(self._tl_job)
        self._tl_job = self.after(90, self._table_resized)

    def _table_resized(self):
        self._tl_job = None
        if self.fit:
            self.draw_timeline(self.idx, full=True)
        else:
            self._draw_scrub()

    def _on_yscroll(self, a, b):
        self.vsb.set(a, b)
        self.lab.yview_moveto(a)

    def _wheel(self, e):
        step = -3 if (e.num == 4 or e.delta > 0) else 3
        if e.state & 0x1:
            self.tl.xview_scroll(step, "units")
        else:
            self.tl.yview_scroll(step, "units")

    def _press(self, e):
        self._pt = (e.x, e.y)
        self.tl.scan_mark(e.x, e.y)

    def _release(self, e):
        if self.mode == "COMPARE" or not self.results or e.widget is not self.tl:
            return
        if abs(e.x - self._pt[0]) > 4 or abs(e.y - self._pt[1]) > 4:
            return
        cw, _, _ = self.metrics()
        col = int(self.tl.canvasx(e.x) // cw)
        if 0 <= col < len(self.refs):
            self.pause()
            self.token += 1
            self.busy = False
            self.idx = col
            self.refresh()

    def set_zoom(self, d):
        self.zoom = min(1.8, max(0.65, self.zoom + d))
        self.draw_timeline(self.idx, full=True)

    def toggle_focus(self, value=None):
        if value is not None:
            self.focus_mode = value
        else:
            self.focus_mode = not self.focus_mode
        if self.focus_mode:
            self.stage.pack_forget()
        elif not self.stage.winfo_manager():
            self.stage.pack(fill="x", padx=24, pady=2, before=self.readout)
        self.after(60, lambda: self.draw_timeline(self.idx, full=True))

    def draw_timeline(self, i, full=True):
        c = self.tl
        if not self.results:
            return
        if self.mode == "COMPARE":
            self._tl_state = None
            return self._timeline_compare(i)

        self.lab.grid()
        steps = self.results[self.mode]["steps"]
        N, n = len(steps), self.n
        cw, rh, fs = self.metrics()
        key = (self.mode, id(self.results[self.mode]), self.zoom, cw)
        if (not full) and self._tl_state == (key, i - 1) and i >= 0:
            self._draw_col(i)
        else:
            c.delete("all")
            self.lab.delete("all")
            height, width = rh * (n + 2) + 14, N * cw + 28
            c.config(scrollregion=(0, 0, width, height))
            self.lab.config(scrollregion=(0, 0, 96, height))
            names = ["REF"] + [f"Frame {k + 1}" for k in range(n)] + ["RESULT"]
            for r, text in enumerate(names):
                self.lab.create_text(10, 5 + r * rh + (rh - 5) / 2, text=text,
                                     anchor="w", fill=MUTED,
                                     font=(FONT, max(8, fs - 3), "bold"))
            for col in range(N):
                if col <= i:
                    self._draw_col(col)
                else:
                    x, rad = col * cw + 4, (min(cw - 8, rh - 5) / 2) - 2
                    ccx, ccy = x + (cw - 8) / 2, 5 + (rh - 5) / 2
                    c.create_oval(ccx - rad, ccy - rad, ccx + rad, ccy + rad,
                                  outline=CARD2, width=1, tags=f"g{col}")
                    c.create_text(ccx, ccy, text=str(self.refs[col]), fill=MUTED,
                                  font=(FONT, fs - 2, "bold"), tags=f"g{col}")
        self._tl_state = (key, i)
        c.delete("hl")
        if i >= 0:
            rrect(c, i * cw, 1, i * cw + cw, rh * (n + 2) + 8, r=9,
                  fill=HL_BG, outline=ACCENT, width=2, tags="hl")
            c.tag_lower("hl")
            left, right = c.xview()[0] * (N * cw + 28), c.xview()[1] * (N * cw + 28)
            if i * cw < left + cw or i * cw + cw > right - cw:
                c.xview_moveto(max(0, i * cw - c.winfo_width() / 2) / (N * cw + 28))

    def _draw_col(self, col):
        c = self.tl
        s, n = self.results[self.mode]["steps"][col], self.n
        cw, rh, fs = self.metrics()
        c.delete(f"g{col}")
        x, w, h = col * cw + 4, cw - 8, rh - 5
        rad = max(2, min(w, h) / 2 - 2)
        page = s["page"]
        c.create_oval(x + w / 2 - rad, 5 + h / 2 - rad, x + w / 2 + rad, 5 + h / 2 + rad,
                      fill=PAGE_COLORS[page % 10], outline="")
        c.create_text(x + w / 2, 5 + h / 2, text=str(page), fill=INK,
                      font=(FONT, fs - 1, "bold"))
        for r in range(n):
            y = 5 + (r + 1) * rh
            fill, outline = PANEL, BORDER
            if s["slot"] == r:
                fill, outline = (HIT_BG, HIT) if s["hit"] else (FAULT_BG, FAULT)
            rrect(c, x, y, x + w, y + h, r=7, fill=fill,
                  outline=outline, width=2 if outline != BORDER else 1)
            v = s["frames"][r]
            if v is not None:
                c.create_text(x + w / 2, y + h / 2, text=str(v),
                              fill=PAGE_COLORS[v % 10], font=(FONT, fs, "bold"))
        y = 5 + (n + 1) * rh
        rrect(c, x, y, x + w, y + h, r=9,
              fill=HIT if s["hit"] else FAULT, outline="")
        c.create_text(x + w / 2, y + h / 2, text="HIT" if s["hit"] else "FAULT",
                      fill="#ffffff", font=(FONT, max(7, fs - 4), "bold"))

    def _timeline_compare(self, i):
        c = self.tl
        c.delete("all")
        self.lab.grid_remove()
        algos = self.algos
        height = 58 + len(algos) * 44 + 20
        c.config(scrollregion=(0, 0, 1080, height))
        c.xview_moveto(0)
        c.yview_moveto(0)
        xs = [24, 176, 262, 354, 448]
        for x, h in zip(xs, ["ALGORITHM", "HITS", "FAULTS", "HIT %", "FAULT %"]):
            c.create_text(x, 20, text=h, anchor="w", fill=MUTED,
                          font=(FONT, 9, "bold"))
        best = min(r["faults"] for r in self.results.values())
        finished = i == len(self.refs) - 1
        for k, name in enumerate(algos):
            y = 60 + k * 44
            win = finished and self.results[name]["faults"] == best
            rrect(c, 12, y - 19, 570, y + 19, r=10, fill=PANEL,
                  outline=GOLD if win else BORDER, width=2 if win else 1)
            if i >= 0:
                s = self.results[name]["steps"][i]
                h, f, tot = s["cum_hits"], s["cum_faults"], i + 1
            else:
                h, f, tot = 0, 0, 1
            vals = [name, h, f, f"{h / tot * 100:.1f}%", f"{f / tot * 100:.1f}%"]
            for x, v, col in zip(xs, vals, [ALGO_COL[name], HIT, FAULT, TEXT, TEXT]):
                c.create_text(x, y, text=str(v), anchor="w", fill=col,
                              font=(FONT, 12, "bold"))
        self._draw_chart(i, 600, 8, 440, height - 20)

    def _draw_chart(self, i, x0, y0, w, h):
        c = self.tl
        N = len(self.refs)
        maxf = max(1, max(r["faults"] for r in self.results.values()))
        px0, py0, px1, py1 = x0 + 36, y0 + 34, x0 + w - 14, y0 + h - 24
        rrect(c, x0, y0, x0 + w, y0 + h, r=10, fill=PANEL, outline=BORDER)
        c.create_text(x0 + 14, y0 + 16, text="CUMULATIVE PAGE FAULTS",
                      anchor="w", fill=MUTED, font=(FONT, 8, "bold"))
        for k in range(5):
            y = py1 - (py1 - py0) * k / 4
            c.create_line(px0, y, px1, y, fill=BORDER)
            c.create_text(px0 - 6, y, text=str(round(maxf * k / 4)),
                          anchor="e", fill=MUTED, font=(FONT, 8))
        c.create_text(px1, py1 + 12, text=f"{N} refs", anchor="e",
                      fill=MUTED, font=(FONT, 8))
        lx = x0 + w - 14
        for name in reversed(self.algos):
            c.create_text(lx, y0 + 16, text=name, anchor="e",
                          fill=ALGO_COL[name], font=(FONT, 8, "bold"))
            lx -= 14 + 7 * len(name)
        if i < 0:
            return
        for name in self.algos:
            steps = self.results[name]["steps"]
            pts = [px0, py1]
            for s_i in range(i + 1):
                pts += [px0 + (px1 - px0) * (s_i + 1) / N,
                        py1 - (py1 - py0) * steps[s_i]["cum_faults"] / maxf]
            c.create_line(*pts, fill=ALGO_COL[name], width=2)
            c.create_oval(pts[-2] - 3, pts[-1] - 3, pts[-2] + 3, pts[-1] + 3,
                          fill=ALGO_COL[name], outline="")

    # =========================================================== playback
    def toggle_play(self):
        if not self.results:
            return
        if self.playing:
            return self.pause()
        if self.idx >= len(self.refs) - 1:
            self.token += 1
            self.busy = False
            self.idx = -1
            self.refresh()
        self.playing = True
        self.play_btn.config(text="❚❚")
        self.advance()

    def pause(self):
        self.playing = False
        if hasattr(self, "play_btn"):
            self.play_btn.config(text="▶")

    def advance(self):
        if not self.playing:
            return
        if self.idx + 1 >= len(self.refs):
            self.pause()
            return self.on_complete()
        self.next_step(lambda: self.after(int(300 / self.speed), self.advance))

    def next_step(self, done=None):
        if self.busy:
            self.token += 1
            self.busy = False
            self.refresh()
        if self.idx + 1 >= len(self.refs):
            return
        self.idx += 1
        self.step_to(self.idx, done)

    def btn_next(self):
        self.pause()
        self.next_step()

    def btn_back(self):
        self.pause()
        self.token += 1
        self.busy = False
        self.idx = max(-1, self.idx - 1)
        self.refresh()

    def reset(self):
        self.pause()
        self.token += 1
        self.busy = False
        self.idx = -1
        self.refresh()

    def skip_end(self):
        self.pause()
        self.token += 1
        self.busy = False
        self.idx = len(self.refs) - 1
        self.refresh()
        self.on_complete()

    def on_complete(self):
        self.refresh()
        if self.mode == "COMPARE" or self.results[self.mode]["faults"] <= min(
                r["faults"] for r in self.results.values()):
            self.confetti()

    # =========================================================== new-simulation card
    def open_new_card(self):
        """Compact card for starting a new run without returning to the welcome."""
        win = tk.Toplevel(self)
        win.title("New simulation")
        win.configure(bg=BG)
        win.resizable(False, False)
        win.transient(self)
        win.attributes("-topmost", True)
        win.geometry("560x448")
        x = self.winfo_rootx() + (self.winfo_width() - 560) // 2
        y = self.winfo_rooty() + 120
        win.geometry(f"+{max(8, x)}+{max(8, y)}")
        self.new_card = win

        outer = tk.Frame(win, bg=BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        card = tk.Frame(outer, bg=PANEL, highlightthickness=1,
                        highlightbackground=BORDER)
        card.pack(fill="both", expand=True)
        card.bind("<Enter>", lambda e: card.config(highlightbackground=ACCENT))
        card.bind("<Leave>", lambda e: card.config(highlightbackground=BORDER))

        top = tk.Frame(card, bg=PANEL)
        top.pack(fill="x", padx=20, pady=(16, 6))
        tk.Label(top, text="New simulation", font=(FONT, 16, "bold"),
                 fg=TEXT, bg=PANEL).pack(side="left")
        close_btn = FlatButton(top, "×", win.destroy, size=14, padx=9, pady=2,
                               bg=PANEL, hover=CARD)
        close_btn.pack(side="right")
        add_tooltip(close_btn, "Close this card")

        state = {"frames": self.n, "algos": list(self.algos), "custom": False}

        # Reference string + generate button side by side
        rrow = tk.Frame(card, bg=PANEL)
        rrow.pack(fill="x", padx=20, pady=(12, 2))
        tk.Label(rrow, text="REFERENCE STRING", font=(FONT, 9, "bold"),
                 fg=MUTED, bg=PANEL).pack(anchor="w")
        row = tk.Frame(card, bg=PANEL)
        row.pack(fill="x", padx=20, pady=(4, 0))
        var = tk.StringVar(value=" ".join(map(str, self.refs)))
        entry = tk.Entry(row, textvariable=var, font=(MONO, 12), bg=STAGE,
                         fg=TEXT, insertbackground=ACCENT, relief="flat",
                         highlightthickness=1, highlightbackground=BORDER)
        entry.pack(side="left", fill="x", expand=True, ipady=7)
        gen = FlatButton(row, "Generate", lambda: var.set(self._random_string()),
                         size=10, padx=12, pady=7, bg=CARD, hover=CARD2)
        gen.pack(side="left", padx=(8, 0))
        add_tooltip(gen, "Create a random 9-15 reference string")
        err = tk.Label(card, text="", font=(FONT, 9, "bold"), fg=FAULT,
                       bg=PANEL, anchor="w")
        err.pack(fill="x", padx=20)
        tk.Label(card, text="Tip: 7012 is read as 7 0 1 2.",
                 font=(FONT, 9), fg=MUTED, bg=PANEL).pack(anchor="w", padx=20)

        # Frames
        tk.Label(card, text="FRAME SIZE", font=(FONT, 9, "bold"), fg=MUTED,
                 bg=PANEL).pack(anchor="w", padx=20, pady=(14, 2))
        frow = tk.Frame(card, bg=PANEL)
        frow.pack(fill="x", padx=20)
        frame_btns = {}

        def pick(n):
            state["frames"] = n
            state["custom"] = False
            spin_row.pack_forget()
            custom_btn.set_colors(CARD, CARD2)
            for k, b in frame_btns.items():
                b.set_colors(ACCENT if k == n else CARD,
                             ACCENT_H if k == n else CARD2)

        for n in range(1, 6):
            b = FlatButton(frow, str(n), lambda n=n: pick(n), size=10,
                           padx=12, pady=6, bg=CARD, hover=CARD2)
            b.pack(side="left", padx=(0, 6))
            add_tooltip(b, f"Use {n} frame{'s' if n != 1 else ''}")
            frame_btns[n] = b

        def use_custom():
            state["custom"] = True
            spin_row.pack(fill="x", pady=(6, 0))
            custom_btn.set_colors(ACCENT, ACCENT_H)
            for b in frame_btns.values():
                b.set_colors(CARD, CARD2)

        custom_btn = FlatButton(frow, "Custom", use_custom, size=10,
                                padx=10, pady=6, bg=CARD, hover=CARD2)
        custom_btn.pack(side="left")
        add_tooltip(custom_btn, "Enter 1-8 frames manually")
        spin_row = tk.Frame(card, bg=PANEL)
        spin_var = tk.StringVar(value="4")
        tk.Label(spin_row, text="Frames (1-8):", font=(FONT, 10), fg=MUTED,
                 bg=PANEL).pack(side="left")
        tk.Spinbox(spin_row, from_=1, to=8, width=5, textvariable=spin_var,
                   font=(FONT, 11), bg=STAGE, fg=TEXT, relief="flat",
                   highlightthickness=1, highlightbackground=BORDER).pack(side="left", padx=8)
        pick(self.n if 1 <= self.n <= 5 else 3)

        # Algorithms
        tk.Label(card, text="ALGORITHMS", font=(FONT, 9, "bold"), fg=MUTED,
                 bg=PANEL).pack(anchor="w", padx=20, pady=(14, 2))
        arow = tk.Frame(card, bg=PANEL)
        arow.pack(fill="x", padx=20)
        algo_btns = {}

        def refresh_algos():
            for name, b in algo_btns.items():
                on = name in state["algos"]
                b.set_colors(ACCENT_SOFT if on else CARD,
                             ACCENT_SOFT if on else CARD2)
                b.config(fg=ALGO_COL[name] if on else MUTED,
                         text=("●   " if on else "○   ") + name)

        def toggle_algo(name):
            if name in state["algos"] and len(state["algos"]) == 1:
                return err.config(text="Keep at least one algorithm.")
            if name in state["algos"]:
                state["algos"].remove(name)
            else:
                state["algos"].append(name)
            err.config(text="")
            refresh_algos()

        for name in ALL_ALGOS:
            b = FlatButton(arow, "", lambda n=name: toggle_algo(n), size=10,
                           padx=12, pady=6)
            b.pack(side="left", padx=(0, 8))
            add_tooltip(b, f"Include or skip {name}")
            algo_btns[name] = b
        refresh_algos()

        def start():
            try:
                pages = parse_pages(var.get())
            except ValueError as exc:
                return err.config(text=f"Invalid input: {exc}")
            if state["custom"]:
                try:
                    n = int(spin_var.get())
                    if not 1 <= n <= 8:
                        raise ValueError
                except ValueError:
                    return err.config(text="Custom frames must be 1-8.")
                state["frames"] = n
            win.destroy()
            self.run(refs=pages, frames=state["frames"],
                     algos=state["algos"], autoplay=True)

        start_btn = FlatButton(card, "Start simulation   →", start, bg=ACCENT,
                               hover=ACCENT_H, fg="#ffffff", size=12,
                               padx=30, pady=9)
        start_btn.pack(pady=(18, 16))
        add_tooltip(start_btn, "Run this reference string now")
        entry.focus_set()

    def _random_string(self):
        length = random.randint(9, 15)
        pages = random.randint(3, 6)
        return " ".join(str(random.randint(0, pages - 1)) for _ in range(length))

    # =========================================================== theme
    def toggle_theme(self):
        # Capture the *current* palette before switching. Option-specific maps
        # avoid collisions such as white meaning both PANEL background and INK.
        current = dict(theme_mod.DARK if self.dark else theme_mod.LIGHT)
        self.dark = not self.dark
        pal = theme_mod.apply_palette("dark" if self.dark else "light")

        for mod in (sys.modules[__name__], sys.modules["welcome"],
                    sys.modules["widgets"]):
            for key, value in pal.items():
                setattr(mod, key, value)

        bg_keys = ("BG", "PANEL", "CARD", "CARD2", "STAGE", "BORDER", "SHADOW",
                   "HIT_BG", "FAULT_BG", "HL_BG", "ACCENT", "ACCENT_H",
                   "ACCENT_SOFT")
        fg_keys = ("TEXT", "MUTED", "INK", "HIT", "FAULT", "GOLD",
                   "ACCENT", "ACCENT_H")

        def build(keys):
            return {current[k]: pal[k] for k in keys
                    if isinstance(current[k], str) and isinstance(pal[k], str)}

        self._bg_map, self._fg_map = build(bg_keys), build(fg_keys)
        self._accent_old = (current["ACCENT"], current["ACCENT_H"])

        for w in self._all_widgets():
            self._retheme_widget(w)
        if self.welcome:
            self.welcome.retheme()
        self.refresh()
        self.flash(f"{'Dark' if self.dark else 'Light'} mode enabled", ACCENT)

    def _all_widgets(self):
        seen = set()

        def walk(w):
            if w in seen:
                return
            seen.add(w)
            yield w
            for child in w.winfo_children():
                yield from walk(child)
        return list(walk(self))

    def _retheme_widget(self, w):
        bg_opts = {"bg", "highlightbackground", "activebackground",
                   "troughcolor", "selectbackground", "readonlybackground"}
        fg_opts = {"fg", "disabledforeground"}
        changes = {}
        for opt in ("bg", "fg", "highlightbackground", "activebackground",
                    "troughcolor", "selectbackground", "readonlybackground",
                    "disabledforeground"):
            try:
                val = w.cget(opt)
            except (tk.TclError, KeyError):
                continue
            if opt in bg_opts:
                new = self._bg_map.get(val)
            elif opt in fg_opts:
                # White text on an accent button stays white in both themes.
                if val == "#ffffff" and getattr(w, "base", None) in self._accent_old:
                    continue
                new = self._fg_map.get(val)
            else:
                new = None
            if new:
                changes[opt] = new
        if changes:
            try:
                w.configure(**changes)
            except tk.TclError:
                pass
        if hasattr(w, "base"):
            w.base = self._bg_map.get(w.base, w.base)
        if hasattr(w, "hover"):
            w.hover = self._bg_map.get(w.hover, w.hover)
        if isinstance(w, Switch):
            w.draw(1.0 if w.get() else 0.0)

    # =========================================================== settings
    def open_settings(self):
        if self.settings is not None and self.settings.winfo_exists():
            self.settings.lift()
            self.settings.attributes("-topmost", True)
            return
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.configure(bg=BORDER)
        win.attributes("-topmost", True)
        self.settings = win

        gx = self.gear.winfo_rootx() - 316
        gy = self.gear.winfo_rooty() + 44
        win.geometry(f"320x466+{max(8, gx)}+{gy}")

        outer = tk.Frame(win, bg=BORDER, padx=1, pady=1)
        outer.pack(fill="both", expand=True)
        card = tk.Frame(outer, bg=PANEL)
        card.pack(fill="both", expand=True)

        top = tk.Frame(card, bg=PANEL)
        top.pack(fill="x", padx=18, pady=(14, 4))
        tk.Label(top, text="Settings", font=(FONT, 15, "bold"), fg=TEXT,
                 bg=PANEL).pack(side="left")
        FlatButton(top, "×", self.close_settings, size=14, padx=9, pady=2,
                   bg=PANEL, hover=CARD).pack(side="right")

        def section(label):
            f = tk.Frame(card, bg=PANEL)
            f.pack(fill="x", padx=18, pady=(10, 0))
            tk.Label(f, text=label.upper(), font=(FONT, 9, "bold"), fg=MUTED,
                     bg=PANEL).pack(anchor="w")
            return f

        play = section("Playback")
        row = tk.Frame(play, bg=PANEL)
        row.pack(fill="x", pady=(6, 0))
        tk.Label(row, text="Speed", font=(FONT, 10), fg=TEXT, bg=PANEL).pack(side="left")
        tk.Scale(row, from_=0.5, to=3.0, resolution=0.25, orient="horizontal",
                 length=170, bg=PANEL, fg=TEXT, troughcolor=CARD,
                 highlightthickness=0, bd=0, activebackground=ACCENT,
                 command=lambda v: setattr(self, "speed", float(v))).pack(side="right")
        row2 = tk.Frame(play, bg=PANEL)
        row2.pack(fill="x", pady=(8, 0))
        tk.Label(row2, text="Animations", font=(FONT, 10), fg=TEXT,
                 bg=PANEL).pack(side="left")
        anim = Switch(row2, value=self.effects, command=lambda: setattr(self, "effects", anim.get()))
        anim.pack(side="right")

        table = section("Trace table")
        row3 = tk.Frame(table, bg=PANEL)
        row3.pack(fill="x", pady=(6, 0))
        tk.Label(row3, text="Fit to width", font=(FONT, 10), fg=TEXT,
                 bg=PANEL).pack(side="left")
        fit_sw = Switch(row3, value=self.fit,
                        command=lambda: (setattr(self, "fit", fit_sw.get()),
                                         self.draw_timeline(self.idx, full=True)))
        fit_sw.pack(side="right")
        row4 = tk.Frame(table, bg=PANEL)
        row4.pack(fill="x", pady=(8, 0))
        tk.Label(row4, text="Cell size", font=(FONT, 10), fg=TEXT, bg=PANEL).pack(side="left")
        tk.Scale(row4, from_=0.65, to=1.8, resolution=0.05, orient="horizontal",
                 length=170, bg=PANEL, fg=TEXT, troughcolor=CARD,
                 highlightthickness=0, bd=0, activebackground=ACCENT,
                 command=lambda v: self._set_zoom(float(v))).pack(side="right")
        row5 = tk.Frame(table, bg=PANEL)
        row5.pack(fill="x", pady=(8, 0))
        tk.Label(row5, text="Focus mode", font=(FONT, 10), fg=TEXT,
                 bg=PANEL).pack(side="left")
        focus_sw = Switch(row5, value=self.focus_mode,
                          command=lambda: self.toggle_focus(focus_sw.get()))
        focus_sw.pack(side="right")

        work = section("Workspace")
        wb = tk.Frame(work, bg=PANEL)
        wb.pack(fill="x", pady=(6, 0))
        for text, cmd, tip in (
            ("CSV", self.export_csv, "Export trace as CSV"),
            ("TXT", self.export_txt, "Export report as text"),
            ("PNG", self.save_screenshot, "Save a screenshot"),
            ("Tests", self.show_tests, "Open test cases"),
            ("Help", self.show_help, "Open the guide"),
        ):
            b = FlatButton(wb, text, cmd, size=9, padx=8, pady=5,
                           bg=CARD, hover=CARD2)
            b.pack(side="left", padx=(0, 5))
            add_tooltip(b, tip)

        FlatButton(card, "New simulation  ↗", lambda: (self.close_settings(),
                                                       self.open_new_card()),
                   bg=ACCENT_SOFT, hover=CARD2, size=10, padx=14, pady=7
                   ).pack(fill="x", padx=18, pady=(14, 16))

    def close_settings(self):
        if self.settings is not None:
            self.settings.destroy()
            self.settings = None

    def _set_zoom(self, value):
        self.zoom = value
        self.fit = False
        self.draw_timeline(self.idx, full=True)

    # =========================================================== export
    def _ask(self, title, ext, kind, default):
        return filedialog.asksaveasfilename(
            title=title, defaultextension=ext,
            filetypes=[(kind, f"*{ext}")], initialfile=default)

    def export_csv(self):
        path = self._ask("Export trace table", ".csv", "CSV file", "pagesim_trace.csv")
        if path:
            reports.write_csv(path, self.refs, self.n, self.results)
            self.flash(f"Saved {os.path.basename(path)}", HIT)

    def export_txt(self):
        path = self._ask("Export report", ".txt", "Text file", "pagesim_report.txt")
        if path:
            reports.write_text(path, self.refs, self.n, self.results)
            self.flash(f"Saved {os.path.basename(path)}", HIT)

    def save_screenshot(self):
        try:
            from PIL import ImageGrab
        except ImportError:
            return self.flash("Screenshots need Pillow:  pip install pillow", GOLD)
        path = self._ask("Save screenshot", ".png", "PNG image", "pagesim.png")
        if path:
            self.update()
            x, y = self.winfo_rootx(), self.winfo_rooty()
            ImageGrab.grab(bbox=(x, y, x + self.winfo_width(),
                                 y + self.winfo_height())).save(path)
            self.flash(f"Saved {os.path.basename(path)}", HIT)

    # =========================================================== dialogs
    def _text_window(self, title, size):
        win = tk.Toplevel(self)
        win.title(title)
        win.configure(bg=BG)
        win.geometry(size)
        txt = tk.Text(win, bg=PANEL, fg=TEXT, font=(MONO, 11), relief="flat",
                      padx=16, pady=14, wrap="word", cursor="arrow",
                      highlightthickness=0)
        sb = tk.Scrollbar(win, command=txt.yview)
        txt.config(yscrollcommand=sb.set)
        sb.pack(side="right", fill="y")
        txt.pack(fill="both", expand=True, padx=12, pady=12)
        txt.tag_config("muted", foreground=MUTED)
        txt.tag_config("title", foreground=ACCENT, font=(MONO, 12, "bold"))
        txt.tag_config("pass", foreground=HIT, font=(MONO, 11, "bold"))
        txt.tag_config("fail", foreground=FAULT, font=(MONO, 11, "bold"))
        txt.tag_config("summary", foreground=GOLD, font=(MONO, 13, "bold"))
        return win, txt

    def show_help(self):
        _, txt = self._text_window("How to use PageSim", "760x620")
        txt.insert("end", HELP_TEXT)
        txt.config(state="disabled")

    def show_tests(self):
        win, txt = self._text_window("Test cases — expected vs actual", "800x620")
        results = test_cases.run_tests()
        total = sum(len(c["rows"]) for c in results)
        passed = sum(r[3] for c in results for r in c["rows"])
        txt.insert("end", f"{passed}/{total} checks passed\n", "summary")
        txt.insert("end", "Click any test title to load it into the simulator.\n\n", "muted")
        for k, c in enumerate(results):
            tag = f"case{k}"
            txt.insert("end", c["name"] + "\n", ("title", tag))
            txt.insert("end", f"   refs: {' '.join(map(str, c['refs']))}   frames: {c['frames']}\n", "muted")
            txt.insert("end", f"   {'Algorithm':<10}{'Expected':>10}{'Actual':>10}   Result\n", "muted")
            for algo, exp, act, ok in c["rows"]:
                txt.insert("end", f"   {algo:<10}{exp:>10}{act:>10}   ")
                txt.insert("end", "PASS\n" if ok else "FAIL\n", "pass" if ok else "fail")
            txt.insert("end", "\n")
            txt.tag_bind(tag, "<Button-1>", lambda e, c=c: self._load_case(c))
            txt.tag_bind(tag, "<Enter>", lambda e: txt.config(cursor="hand2"))
            txt.tag_bind(tag, "<Leave>", lambda e: txt.config(cursor="arrow"))
        txt.config(state="disabled")

    def _load_case(self, case):
        self.run(refs=case["refs"], frames=case["frames"],
                 algos=list(self.algos), autoplay=False)
        self.flash(f"Loaded {case['name'].split('  ')[0]}", ACCENT)


if __name__ == "__main__":
    App().mainloop()
