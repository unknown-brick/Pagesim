"""Two-stage welcome flow for PageSim v2.

Stage 1: a calm hero with a short description and one button (Let's go).
Stage 2: a single clean setup screen - reference string, frames, algorithms.

Generated reference strings always contain 9-15 pages.
"""
import math
import random
import tkinter as tk

from algorithms import fifo
from theme import *
from widgets import FlatButton, add_tooltip, ease, lerp_color, parse_pages, rrect

DESCRIPTION = (
    "When a page is missing from memory and every frame is full, the operating "
    "system must decide what to evict. Watch FIFO, LRU and Optimal make that "
    "choice one step at a time — then see who faults least."
)
DEMO_REFS = [7, 0, 1, 2, 0, 3, 0, 4, 2, 3, 0, 3]
CARD_H = 318


class WelcomeScreen(tk.Frame):
    def __init__(self, master, on_start, on_settings=None, init_text="", init_frames=3):
        super().__init__(master, bg=BG)
        self.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.on_start, self.on_settings = on_start, on_settings
        self.init_text = init_text
        self.frames = min(8, max(1, int(init_frames)))
        self.algos = set(ALL_ALGOS)
        self.mode = "TYPE"
        self.gen_text = ""
        self.err_text = tk.StringVar()

        self._steps = fifo(DEMO_REFS, 3)["steps"]
        self._k, self._t = 0, 0
        self._bg_job = None
        self._demo_job = None
        self._card_targets = []

        self._build_background()
        self.intro = tk.Frame(self, bg=BG)
        self.setup = tk.Frame(self, bg=BG)
        self._build_intro()
        self._build_setup()
        self._show_intro()
        self.after(500, self.show_first_tip)

    # ------------------------------------------------------------------ background
    def _build_background(self):
        self.bg = tk.Canvas(self, bg=BG, highlightthickness=0)
        self.bg.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.bg.bind("<Configure>", lambda e: self._draw_bg())

    def _draw_bg(self):
        c = self.bg
        c.delete("blob")
        w, h = c.winfo_width(), c.winfo_height()
        if w < 10:
            return
        blobs = [
            (int(w * 0.12), int(h * 0.18), 190, "#e9edff"),
            (int(w * 0.86), int(h * 0.24), 230, "#e7f7ef"),
            (int(w * 0.70), int(h * 0.88), 260, "#fff1e6"),
            (int(w * 0.25), int(h * 0.92), 170, "#f1eaff"),
        ]
        for x, y, r, col in blobs:
            c.create_oval(x - r, y - r, x + r, y + r, fill=col, outline="", tags="blob")

    def _animate_bg(self):
        self._t += 0.02
        offsets = [math.sin(self._t + i) * 14 for i in range(4)]
        items = self.bg.find_withtag("blob")
        coords = [self.bg.coords(i) for i in items]
        for i, (box, off) in enumerate(zip(coords, offsets)):
            if len(box) == 4:
                dx, dy = off, off * 0.6
                self.bg.coords(items[i], box[0] + dx, box[1] + dy, box[2] + dx, box[3] + dy)
        self._bg_job = self.after(60, self._animate_bg)

    # ------------------------------------------------------------------ stage 1
    def _build_intro(self):
        box = tk.Frame(self.intro, bg=BG)
        box.place(relx=0.5, rely=0.48, anchor="center")

        FlatButton(self.intro, "⚙", self._settings, size=15, padx=10, pady=6,
                   bg=BG, hover=CARD).pack(anchor="ne", padx=18, pady=14)

        tk.Label(box, text="PT 101  ·  FINAL PROJECT", font=(FONT, 10, "bold"),
                 fg=MUTED, bg=BG).pack()
        tk.Label(box, text="Welcome to", font=(FONT, 17), fg=MUTED, bg=BG).pack(pady=(10, 0))
        tk.Label(box, text="PageSim", font=(FONT, 54, "bold"), fg=TEXT, bg=BG).pack()
        tk.Label(box, text="Page replacement, made visible.", font=(FONT, 20),
                 fg=ACCENT, bg=BG).pack(pady=(2, 12))

        self.demo = tk.Canvas(box, width=720, height=132, bg=STAGE,
                              highlightthickness=1, highlightbackground=BORDER)
        self.demo.pack()

        tk.Label(box, text=DESCRIPTION, font=(FONT, 12), fg=TEXT, bg=BG,
                 wraplength=680, justify="center").pack(pady=(16, 4))
        tk.Label(box, text="FIFO  ·  LRU  ·  OPTIMAL", font=(FONT, 10, "bold"),
                 fg=MUTED, bg=BG).pack()

        self.go_btn = FlatButton(box, "Let's go    →", self._to_setup,
                                 bg=ACCENT, hover=ACCENT_H, size=15,
                                 padx=52, pady=12)
        self.go_btn.pack(pady=(22, 6))
        add_tooltip(self.go_btn, "Open the setup card")
        tk.Label(box, text="two quick steps · about 20 seconds", font=(FONT, 9),
                 fg=MUTED, bg=BG).pack()

        self._pulse = 0
        self._pulse_go()

    def _pulse_go(self):
        if not self.winfo_exists():
            return
        self._pulse += 0.06
        col = lerp_color(ACCENT, ACCENT_H, (math.sin(self._pulse) + 1) / 2)
        self.go_btn.set_colors(col, ACCENT_H)
        if self.intro.winfo_ismapped():
            self._pulse_job = self.after(90, self._pulse_go)

    def _chip(self, cx, cy, page, r=20):
        self.demo.create_oval(cx - r, cy - r, cx + r, cy + r,
                              fill=PAGE_COLORS[page % 10], outline="#ffffff", width=2)
        self.demo.create_text(cx, cy, text=str(page), font=(FONT, 14, "bold"), fill=INK)

    def _demo_tick(self):
        if not self.demo.winfo_exists():
            return
        d = self.demo
        if not self.intro.winfo_ismapped():
            self._demo_job = self.after(200, self._demo_tick)
            return
        s = self._steps[self._k]
        d.delete("all")
        d.create_text(64, 18, text="INCOMING", fill=MUTED, font=(FONT, 8, "bold"))
        self._chip(64, 72, s["page"], 22)
        d.create_text(132, 18, text="RAM FRAMES", anchor="w", fill=MUTED, font=(FONT, 8, "bold"))
        for k in range(3):
            x = 132 + k * 138
            glow = (HIT if s["hit"] else FAULT) if k == s["slot"] else BORDER
            rrect(d, x, 34, x + 116, 108, r=16, fill=PANEL, outline=glow, width=3 if glow != BORDER else 1)
            if s["frames"][k] is not None:
                self._chip(x + 58, 71, s["frames"][k], 19)
            else:
                d.create_text(x + 58, 71, text="empty", fill=MUTED, font=(FONT, 9, "italic"))
        label = "HIT" if s["hit"] else "PAGE FAULT"
        col = HIT if s["hit"] else FAULT
        rrect(d, 566, 48, 694, 92, r=12, fill=HIT_BG if s["hit"] else FAULT_BG, outline="")
        d.create_text(630, 70, text=label, fill=col, font=(FONT, 13, "bold"))
        d.create_text(630, 116, text=f"step {self._k + 1} / {len(self._steps)}",
                      fill=MUTED, font=(FONT, 8))
        self._k = (self._k + 1) % len(self._steps)
        self._demo_job = self.after(900, self._demo_tick)

    # ------------------------------------------------------------------ stage 2
    def _build_setup(self):
        top = tk.Frame(self.setup, bg=BG)
        top.pack(fill="x", padx=22, pady=(14, 0))
        FlatButton(top, "←  Back", self._to_intro, size=10, padx=10, pady=5,
                   bg=BG, hover=CARD).pack(side="left")
        tk.Label(top, text="STEP 2 OF 2", font=(FONT, 10, "bold"), fg=MUTED,
                 bg=BG).pack(side="left", padx=12)
        FlatButton(top, "⚙", self._settings, size=15, padx=10, pady=4,
                   bg=BG, hover=CARD).pack(side="right")

        head = tk.Frame(self.setup, bg=BG)
        head.place(relx=0.5, rely=0.17, anchor="center")
        tk.Label(head, text="Make it yours", font=(FONT, 34, "bold"), fg=TEXT, bg=BG).pack()
        tk.Label(head, text="Three small choices. No scrolling, no clutter.",
                 font=(FONT, 12), fg=MUTED, bg=BG).pack(pady=(2, 0))

        self.cards_frame = tk.Frame(self.setup, bg=BG)
        self.cards_frame.place(relx=0.5, rely=0.55, anchor="center", width=1160, height=CARD_H)
        self.cards_frame.bind("<Configure>", lambda e: self._layout_cards())

        self.card_refs = self._make_card("01", "REFERENCE STRING")
        self.card_frames = self._make_card("02", "PAGE FRAMES")
        self.card_algos = self._make_card("03", "ALGORITHMS")
        self.cards = [self.card_refs, self.card_frames, self.card_algos]
        self._build_refs_card()
        self._build_frames_card()
        self._build_algos_card()

        bottom = tk.Frame(self.setup, bg=BG)
        bottom.place(relx=0.5, rely=0.90, anchor="center")
        self.start_btn = FlatButton(bottom, "Start simulation    →", self.start,
                                    bg=ACCENT, hover=ACCENT_H, size=14,
                                    padx=44, pady=11)
        self.start_btn.pack()
        tk.Label(bottom, textvariable=self.err_text, font=(FONT, 10, "bold"),
                 fg=FAULT, bg=BG).pack(pady=(6, 0))

    def _make_card(self, number, title):
        card = tk.Frame(self.cards_frame, bg=PANEL,
                        highlightbackground=BORDER, highlightthickness=1)
        tk.Label(card, text=number, font=(FONT, 10, "bold"), fg=ACCENT,
                 bg=PANEL).pack(anchor="w", pady=(18, 0), padx=22)
        tk.Label(card, text=title, font=(FONT, 13, "bold"), fg=TEXT,
                 bg=PANEL).pack(anchor="w", padx=22)
        tk.Frame(card, bg=BORDER, height=1).pack(fill="x", padx=22, pady=12)
        body = tk.Frame(card, bg=PANEL)
        body.pack(fill="both", expand=True, padx=22, pady=(0, 18))
        card.body = body
        return card

    def _layout_cards(self):
        w = self.cards_frame.winfo_width()
        if w < 100:
            return
        gap = 18
        cw = max(240, (w - gap * (len(self.cards) - 1)) // len(self.cards))
        self._card_targets = [(i * (cw + gap), 0, cw, CARD_H) for i in range(len(self.cards))]
        for card, (x, y, cw_, h) in zip(self.cards, self._card_targets):
            card.place(x=x, y=y, width=cw_, height=h)

    def _build_refs_card(self):
        body = self.card_refs.body
        seg = tk.Frame(body, bg=CARD)
        seg.pack(fill="x", pady=(2, 10))
        self.btn_type = FlatButton(seg, "Type my own", lambda: self.set_ref_mode("TYPE"),
                                   size=10, padx=14, pady=6)
        self.btn_gen = FlatButton(seg, "Generate", lambda: self.set_ref_mode("GENERATE"),
                                  size=10, padx=14, pady=6)
        self.btn_type.pack(side="left", fill="x", expand=True, padx=2, pady=2)
        self.btn_gen.pack(side="left", fill="x", expand=True, padx=2, pady=2)

        self.ref_var = tk.StringVar(value=self.init_text)
        self.entry = tk.Entry(body, textvariable=self.ref_var, font=(MONO, 13),
                              bg=STAGE, fg=TEXT, insertbackground=ACCENT,
                              relief="flat", highlightthickness=1,
                              highlightbackground=BORDER, highlightcolor=ACCENT)
        self.entry.pack(fill="x", ipady=8, pady=(0, 6))

        self.gen_row = tk.Frame(body, bg=PANEL)
        self.gen_label = tk.Label(self.gen_row, font=(MONO, 12), fg=TEXT, bg=PANEL,
                                  wraplength=300, justify="left", anchor="w")
        self.gen_label.pack(fill="x", pady=(2, 6))
        shuffle = FlatButton(self.gen_row, "↻   Shuffle", self.roll, size=10, padx=12, pady=5,
                             bg=CARD, hover=CARD2)
        shuffle.pack(anchor="w")
        add_tooltip(shuffle, "Generate another 9-15 reference string")

        self.ref_hint = tk.Label(body, text="Digits, spaces or commas. 7012 = 7 0 1 2. Max 40.",
                                 font=(FONT, 9), fg=MUTED, bg=PANEL,
                                 wraplength=300, justify="left", anchor="w")
        self.ref_hint.pack(fill="x", pady=(8, 0))
        self.roll()
        self.set_ref_mode("TYPE")

    def _build_frames_card(self):
        body = self.card_frames.body
        pills = tk.Frame(body, bg=PANEL)
        pills.pack(fill="x", pady=(2, 8))
        self.frame_btns = {}
        for n in range(1, 6):
            b = FlatButton(pills, str(n), lambda n=n: self.pick_frames(n),
                           size=11, padx=13, pady=6)
            b.pack(side="left", padx=(0, 5))
            self.frame_btns[n] = b
        self.custom_btn = FlatButton(pills, "Custom", self._toggle_custom,
                                     size=10, padx=10, pady=6)
        self.custom_btn.pack(side="left")

        self.custom_row = tk.Frame(body, bg=PANEL)
        tk.Label(self.custom_row, text="Frames:", font=(FONT, 10), fg=MUTED,
                 bg=PANEL).pack(side="left")
        self.custom_var = tk.StringVar(value="4")
        self.spin = tk.Spinbox(self.custom_row, from_=1, to=8, width=5,
                               textvariable=self.custom_var, font=(FONT, 11),
                               bg=STAGE, fg=TEXT, relief="flat",
                               highlightthickness=1, highlightbackground=BORDER)
        self.spin.pack(side="left", padx=8)
        self.frame_hint = tk.Label(body, text="3 frames is a good place to start.",
                                   font=(FONT, 9), fg=MUTED, bg=PANEL,
                                   wraplength=300, justify="left", anchor="w")
        self.frame_hint.pack(fill="x", pady=(10, 0))
        self.pick_frames(self.frames)

    def _build_algos_card(self):
        body = self.card_algos.body
        self.algo_btns = {}
        for name in ALL_ALGOS:
            b = FlatButton(body, f"●   {name}", lambda n=name: self.toggle_algo(n),
                           size=11, padx=14, pady=9)
            b.pack(fill="x", pady=(0, 7))
            self.algo_btns[name] = b
        tk.Label(body, text="Pick one or more. Compare appears when you pick two or more.",
                 font=(FONT, 9), fg=MUTED, bg=PANEL, wraplength=300,
                 justify="left", anchor="w").pack(fill="x", pady=(4, 0))
        self._refresh_algos()

    # ------------------------------------------------------------ choice logic
    def set_ref_mode(self, mode):
        self.mode = mode
        for b, on in ((self.btn_type, mode == "TYPE"), (self.btn_gen, mode == "GENERATE")):
            b.set_colors(ACCENT if on else CARD, ACCENT_H if on else CARD2)
            b.config(fg=TEXT if on else MUTED)
        if mode == "GENERATE":
            self.entry.pack_forget()
            self.gen_row.pack(fill="x", pady=(2, 6))
            self.ref_hint.config(text="Generated length: 9–15 references.")
            self.roll()
        else:
            self.gen_row.pack_forget()
            self.entry.pack(fill="x", ipady=8, pady=(0, 6))
            self.ref_hint.config(text="Digits, spaces or commas. 7012 = 7 0 1 2. Max 40.")
            self.entry.focus_set()

    def roll(self):
        length = random.randint(9, 15)
        pages = random.randint(3, 6)
        self.gen_text = " ".join(str(random.randint(0, pages - 1)) for _ in range(length))
        self.gen_label.config(text=self.gen_text)

    def pick_frames(self, n):
        self.frames = n
        self.custom_row.pack_forget()
        self.custom_btn.set_colors(CARD, CARD2)
        for k, b in self.frame_btns.items():
            b.set_colors(ACCENT if k == n else CARD, ACCENT_H if k == n else CARD2)

    def _toggle_custom(self):
        self.custom_row.pack(fill="x", pady=(2, 4))
        self.custom_btn.set_colors(ACCENT, ACCENT_H)
        for b in self.frame_btns.values():
            b.set_colors(CARD, CARD2)
        self.spin.focus_set()

    def toggle_algo(self, name):
        if name in self.algos and len(self.algos) == 1:
            self.err_text.set("Keep at least one algorithm.")
            return
        if name in self.algos:
            self.algos.remove(name)
        else:
            self.algos.add(name)
        self.err_text.set("")
        self._refresh_algos()

    def _refresh_algos(self):
        for name, b in self.algo_btns.items():
            on = name in self.algos
            col = ALGO_COL[name]
            b.set_colors(ACCENT_SOFT if on else CARD, ACCENT_SOFT if on else CARD2)
            b.config(fg=col if on else MUTED,
                     text=("●   " if on else "○   ") + name)

    def _settings(self):
        if self.on_settings:
            self.on_settings()

    # -------------------------------------------------------------- transitions
    def _show_intro(self):
        self.setup.place_forget()
        self.intro.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.intro.lift()
        if self._bg_job is None:
            self._animate_bg()
        if self._demo_job is None:
            self._demo_tick()

    def _to_setup(self):
        self.intro.place_forget()
        self.setup.place(relx=0, rely=0, relwidth=1, relheight=1)
        self.setup.lift()
        self._layout_cards()
        self._animate_cards()

    def _to_intro(self):
        self.err_text.set("")
        self._show_intro()

    def _animate_cards(self):
        for k, card in enumerate(self.cards):
            if not self._card_targets:
                continue
            _, _, cw, h = self._card_targets[k]
            card.place(y=26)
            self.after(k * 90, lambda c=card, idx=k: self._slide_card(c, idx))

    def _slide_card(self, card, idx):
        if not card.winfo_exists() or not self._card_targets:
            return
        x, y, cw, h = self._card_targets[idx]
        steps, k = 8, 0

        def tick():
            nonlocal k
            k += 1
            t = ease(k / steps)
            card.place(x=x, y=int(y + 26 * (1 - t)), width=cw, height=h)
            if k < steps:
                self.after(18, tick)
        tick()

    # ------------------------------------------------------------------ submit
    def start(self):
        try:
            pages = parse_pages(self.gen_text if self.mode == "GENERATE" else self.ref_var.get())
        except ValueError as exc:
            msg = str(exc)
            if msg == "empty":
                return self.err_text.set("Enter a reference string or choose Generate.")
            if msg == "too many":
                return self.err_text.set("Keep it to 40 references or fewer.")
            return self.err_text.set(f"'{msg}' is not a page number — use digits.")
        if self.custom_btn["bg"] == ACCENT:
            try:
                n = int(self.custom_var.get())
                if not 1 <= n <= 8:
                    raise ValueError
            except ValueError:
                return self.err_text.set("Custom frames must be a number from 1 to 8.")
            self.frames = n
        if not self.algos:
            return self.err_text.set("Choose at least one algorithm.")
        self.err_text.set("")
        self.on_start(" ".join(map(str, pages)), self.frames, list(self.algos))

    def show_first_tip(self):
        """One-time helper bubble on the first open."""
        if getattr(self, "_tip_shown", False) or not self.winfo_exists():
            return
        self._tip_shown = True
        win = tk.Toplevel(self)
        win.overrideredirect(True)
        win.attributes("-topmost", True)
        frame = tk.Frame(win, bg=BORDER if "BORDER" in globals() else CARD2, padx=1, pady=1)
        frame.pack()
        inner = tk.Frame(frame, bg=PANEL, padx=14, pady=10)
        inner.pack()
        tk.Label(inner, text="Tip", font=(FONT, 10, "bold"), fg=ACCENT,
                 bg=PANEL).pack(anchor="w")
        tk.Label(inner, text="Hover any button for help. Generate always makes 9–15 refs.",
                 font=(FONT, 9), fg=TEXT, bg=PANEL, wraplength=240).pack(anchor="w")
        FlatButton(inner, "Got it", lambda: win.destroy(), size=9, padx=10,
                   pady=4, bg=CARD, hover=CARD2).pack(anchor="e", pady=(8, 0))
        self.update_idletasks()
        x = self.go_btn.winfo_rootx() + self.go_btn.winfo_width() + 14
        y = self.go_btn.winfo_rooty()
        win.geometry(f"+{max(8, x)}+{max(8, y)}")
        self._first_tip = win
        self.after(6500, lambda: win.winfo_exists() and win.destroy())

    def retheme(self):
        """Redraw canvases after a palette switch."""
        self._draw_bg()
        self._demo_tick()

    def destroy(self):
        for job in (self._bg_job, self._demo_job, getattr(self, "_pulse_job", None)):
            if job:
                try:
                    self.after_cancel(job)
                except tk.TclError:
                    pass
        super().destroy()
