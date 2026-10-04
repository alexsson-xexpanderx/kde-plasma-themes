#!/usr/bin/env python3
"""Size settings for the pixel dashboard.

    ./dashboard_settings.py

Two sliders, the panel's width and its text size, written into
configs/dashboard.conf and lua/dashboard.lua when you press Apply, which then
restarts this dashboard (and only this one) so the change shows at once.

The sliders and buttons are the pixel Orrery's colour editor's, from the
folder next to this one, so the two windows look alike.
"""

import importlib.util
import os
import re
import shutil
import subprocess
import sys
import tkinter as tk
from tkinter import messagebox

HERE = os.path.dirname(os.path.abspath(__file__))
CONF = os.path.join(HERE, "configs", "dashboard.conf")
SCRIPT = os.path.join(HERE, "lua", "dashboard.lua")
START = os.path.join(HERE, "start_conky.sh")

spec = importlib.util.spec_from_file_location(
    "orrery_colors", os.path.join(HERE, "..", "conky-orrery-pixel", "orrery_colors.py"))
ui = importlib.util.module_from_spec(spec)
spec.loader.exec_module(ui)

# Setting: label, file, pattern, range, step, how it is shown, how it is written.
SETTINGS = [
    ("width", "Panel width", CONF,
     re.compile(r'(CONKY_DASHBOARD_WIDTH"\)\)\s*or\s*)([0-9]+)'),
     300, 700, 10, "%d px", "%d"),
    ("font_scale", "Text size", SCRIPT,
     re.compile(r'^(\s*font_scale\s*=\s*)([0-9.]+)', re.M),
     0.8, 2.0, 0.05, "%.2fx", "%.2f"),
]


def read(path):
    with open(path, encoding="utf-8") as handle:
        return handle.read()


def current():
    values = {}
    for key, _, path, pattern, *_ in SETTINGS:
        m = pattern.search(read(path))
        if not m:
            raise SystemExit("could not find %s in %s" % (key, path))
        values[key] = float(m.group(2))
    return values


def write(values):
    """Change only the numbers, keeping a .bak of each file."""
    for key, _, path, pattern, _, _, _, _, written in SETTINGS:
        text = read(path)
        new = pattern.sub(lambda m: m.group(1) + written % values[key], text, count=1)
        if new != text:
            shutil.copy2(path, path + ".bak")
            with open(path, "w", encoding="utf-8") as handle:
                handle.write(new)


class Settings(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Conky dashboard settings (pixel)")
        self.configure(bg=ui.BG)
        self.resizable(False, False)
        self.saved = current()
        self.values = dict(self.saved)

        root = tk.Frame(self, bg=ui.BG, padx=16, pady=14)
        root.pack(fill="both", expand=True)
        head = tk.Frame(root, bg=ui.BG)
        head.pack(fill="x", pady=(0, 6))
        tk.Label(head, text="SIZE", bg=ui.BG, fg=ui.FAINT, font=(ui.FONT, 8, "bold")).pack(
            side="left")
        tk.Frame(head, bg=ui.BORDER, height=1).pack(side="left", fill="x", expand=True,
                                                    padx=(10, 0), pady=(1, 0))

        card = tk.Frame(root, bg=ui.SURFACE, highlightthickness=1,
                        highlightbackground=ui.BORDER, padx=14, pady=14)
        card.pack(fill="x")
        self.sliders, self.shown = {}, {}
        for i, (key, label, _, _, low, high, step, shown, _) in enumerate(SETTINGS):
            line = tk.Frame(card, bg=ui.SURFACE)
            line.pack(fill="x", pady=(0 if i == 0 else 10, 0))
            tk.Label(line, text=label, bg=ui.SURFACE, fg=ui.TEXT, font=ui.F_BODY).pack(
                side="left")
            self.shown[key] = tk.Label(line, text=shown % self.values[key], bg=ui.SURFACE,
                                       fg=ui.ACCENT, font=ui.F_MONO)
            self.shown[key].pack(side="right")
            slider = ui.Slider(card, low, high, self.values[key], width=404,
                               command=lambda v, k=key, s=step, f=shown: self.set(k, v, s, f))
            slider.configure(bg=ui.SURFACE)
            slider.pack(fill="x")
            self.sliders[key] = slider
        tk.Label(card, text="Text grows in steps, since the font comes in whole sizes. If "
                            "the panel gets too tall for the screen, the text is stepped "
                            "back down to fit.",
                 bg=ui.SURFACE, fg=ui.MUTED, font=ui.F_SMALL, justify="left",
                 wraplength=400).pack(anchor="w", pady=(12, 0))

        bar = tk.Frame(root, bg=ui.BG)
        bar.pack(fill="x", pady=(16, 0))
        self.status = tk.Label(bar, text="", bg=ui.BG, fg=ui.ACCENT, font=ui.F_SMALL)
        self.status.pack(side="left")
        ui.Button(bar, "Apply and restart dashboard", self.apply, primary=True).pack(
            side="right")
        ui.Button(bar, "Revert", self.revert, width=86).pack(side="right", padx=8)

    def set(self, key, value, step, shown):
        value = round(round(value / step) * step, 2)
        self.values[key] = value
        self.shown[key].configure(text=shown % value)
        self.status.configure(text="")

    def revert(self):
        self.values = dict(self.saved)
        for key, *_ in SETTINGS:
            self.sliders[key].set(self.values[key])
            shown = next(s[7] for s in SETTINGS if s[0] == key)
            self.shown[key].configure(text=shown % self.values[key])
        self.status.configure(text="reverted")

    def apply(self):
        try:
            write(self.values)
        except OSError as problem:
            messagebox.showerror("Could not save", str(problem), parent=self)
            return
        self.saved = dict(self.values)
        # start_conky.sh replaces a dashboard already running from this folder.
        subprocess.Popen([START], cwd=HERE, stdin=subprocess.DEVNULL,
                         stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                         start_new_session=True)
        self.status.configure(text="saved - dashboard restarted")


if __name__ == "__main__":
    if not os.path.exists(CONF) or not os.path.exists(SCRIPT):
        sys.exit("run this from the conky-dashboard-pixel folder it came in")
    Settings().mainloop()
