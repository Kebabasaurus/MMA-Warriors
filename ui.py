import json
import inspect
import random
import sys
import traceback
import webbrowser
from datetime import datetime
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion
from rules_help import HELP_TOPICS, search_help_topics


class UIMixin:
    def focus_managed_window(self, key):
        """Focus a logical singleton window if it is still alive."""
        registry = getattr(self, "_managed_windows", {})
        window = registry.get(str(key))
        try:
            if window is not None and window.winfo_exists():
                window.deiconify()
                window.lift()
                window.focus_force()
                return window
        except tk.TclError:
            pass
        registry.pop(str(key), None)
        return None

    def create_managed_window(self, key=None, parent=None):
        """Create a call-site/entity keyed popup and replace stale duplicates."""
        caller = inspect.currentframe().f_back
        if key is None:
            key_parts = [caller.f_code.co_filename, str(caller.f_lineno)]
            for local_name in ("fighter", "item", "record", "sport", "member", "promo"):
                value = caller.f_locals.get(local_name)
                identity = getattr(value, "fighter_id", None) if value is not None else None
                if identity is None and isinstance(value, dict):
                    identity = value.get("fighter_id") or value.get("id") or value.get("name")
                if identity is None and isinstance(value, (str, int)):
                    identity = value
                if identity:
                    key_parts.extend((local_name, str(identity)))
            key = "popup:" + ":".join(key_parts)
        key = str(key)
        existing = self.focus_managed_window(key)
        if existing is not None:
            try:
                existing.destroy()
            except tk.TclError:
                pass
        window = tk.Toplevel(parent or self.root)
        registry = getattr(self, "_managed_windows", None)
        if registry is None:
            registry = self._managed_windows = {}
        registry[key] = window

        def unregister(event):
            if event.widget is window and registry.get(key) is window:
                registry.pop(key, None)

        window.bind("<Destroy>", unregister, add="+")
        return window

    def show_busy_overlay(self, title="Please wait", message="Working...", progress=0):
        """Show a modal, repaintable status panel before synchronous UI work begins."""
        existing = getattr(self, "_busy_overlay", None)
        if existing and existing.get("window") and existing["window"].winfo_exists():
            self.update_busy_overlay(message, progress)
            return existing

        root = self.root
        previous_cursor = root.cget("cursor")
        root.configure(cursor="wait")
        window = tk.Toplevel(root)
        window.title(str(title))
        window.transient(root)
        window.resizable(False, False)
        window.protocol("WM_DELETE_WINDOW", lambda: None)
        window.configure(bg=self.colors["chrome"])

        width, height = 480, 172
        root.update_idletasks()
        root_width = max(root.winfo_width(), root.winfo_reqwidth())
        root_height = max(root.winfo_height(), root.winfo_reqheight())
        x = root.winfo_rootx() + max(0, (root_width - width) // 2)
        y = root.winfo_rooty() + max(0, (root_height - height) // 2)
        window.geometry(f"{width}x{height}+{x}+{y}")

        border = tk.Frame(window, bg=self.colors["red"], padx=2, pady=2)
        border.pack(fill="both", expand=True)
        body = tk.Frame(border, bg=self.colors["panel"], padx=22, pady=18)
        body.pack(fill="both", expand=True)
        tk.Label(
            body,
            text=str(title).upper(),
            bg=self.colors["panel"],
            fg=self.colors["text"],
            font=("Arial", 15, "bold"),
            anchor="w",
        ).pack(fill="x")
        status = tk.StringVar(master=window, value=str(message))
        tk.Label(
            body,
            textvariable=status,
            bg=self.colors["panel"],
            fg=self.colors["muted"],
            font=("Tahoma", 9),
            anchor="w",
        ).pack(fill="x", pady=(10, 9))
        bar = ttk.Progressbar(
            body,
            mode="determinate",
            maximum=100,
            value=max(0, min(100, int(progress))),
            style="Activity.Horizontal.TProgressbar",
        )
        bar.pack(fill="x")

        overlay = {
            "window": window,
            "status": status,
            "progress": bar,
            "previous_cursor": previous_cursor,
        }
        self._busy_overlay = overlay
        window.grab_set()
        window.lift()
        window.update_idletasks()
        window.update()
        return overlay

    def update_busy_overlay(self, message, progress=None):
        """Refresh the active busy panel at a safe boundary in a long operation."""
        overlay = getattr(self, "_busy_overlay", None)
        if not overlay:
            return
        window = overlay.get("window")
        if not window or not window.winfo_exists():
            return
        overlay["status"].set(str(message))
        if progress is not None:
            overlay["progress"]["value"] = max(0, min(100, int(progress)))
        window.update_idletasks()

    def close_busy_overlay(self, overlay=None):
        """Close the active busy panel and restore the main-window cursor."""
        active = overlay or getattr(self, "_busy_overlay", None)
        if not active:
            return
        window = active.get("window")
        try:
            if window and window.winfo_exists():
                window.grab_release()
                window.destroy()
        except tk.TclError:
            pass
        try:
            self.root.configure(cursor=active.get("previous_cursor", ""))
        except tk.TclError:
            pass
        if getattr(self, "_busy_overlay", None) is active:
            self._busy_overlay = None

    @staticmethod
    def wcag_relative_luminance(color):
        """Return the WCAG 2.x relative luminance for a #RRGGBB color."""
        value = color.lstrip("#")
        channels = [int(value[index:index + 2], 16) / 255.0 for index in (0, 2, 4)]
        linear = [channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4 for channel in channels]
        return (0.2126 * linear[0]) + (0.7152 * linear[1]) + (0.0722 * linear[2])

    @classmethod
    def wcag_contrast_ratio(cls, foreground, background):
        """Return the WCAG contrast ratio between two #RRGGBB colors."""
        light, dark = sorted(
            (cls.wcag_relative_luminance(foreground), cls.wcag_relative_luminance(background)),
            reverse=True,
        )
        return (light + 0.05) / (dark + 0.05)

    @classmethod
    def accessible_tab_text(cls, background, preferred=None):
        """Keep branded text when it passes AA, otherwise choose a safe neutral."""
        if preferred and cls.wcag_contrast_ratio(preferred, background) >= 4.5:
            return preferred
        candidates = ("#ffffff", "#111111")
        return max(candidates, key=lambda color: cls.wcag_contrast_ratio(color, background))

    @classmethod
    def semantic_status_palette(cls, colors, background_key="tree"):
        """Return readable semantic row colours for the active theme.

        Older pages used the same pale accents on every palette, which made
        wins, warnings and active deals nearly disappear on Light Office.
        Keep meanings stable but choose dark foregrounds for light table
        surfaces and bright foregrounds for dark surfaces. Status words remain
        in each row so colour is never the sole cue.
        """
        background = colors.get(background_key, colors.get("tree", "#10151a"))
        light_surface = cls.wcag_relative_luminance(background) > 0.35
        if light_surface:
            return {
                "positive": "#176b3a",
                "negative": "#9f1f2d",
                "warning": "#6a4300",
                "info": "#005a70",
                "neutral": "#3f4650",
            }
        return {
            "positive": "#9de6a0",
            "negative": "#ff9b9b",
            "warning": "#ffe08a",
            "info": "#9de6ff",
            "neutral": "#b9c2cb",
        }

    @classmethod
    def tab_style_palette(cls, colors):
        """Build readable notebook states from the active game's theme colors."""
        inactive_bg = colors["button"]
        hover_bg = colors["panel_dark"]
        accents = (colors["red"], colors["gold"])
        selected_bg = max(accents, key=lambda color: cls.wcag_contrast_ratio(color, inactive_bg))
        selected_fg = cls.accessible_tab_text(selected_bg)
        disabled_bg = inactive_bg
        return {
            "inactive_bg": inactive_bg,
            "inactive_fg": cls.accessible_tab_text(inactive_bg, colors["button_text"]),
            "hover_bg": hover_bg,
            "hover_fg": cls.accessible_tab_text(hover_bg),
            "selected_bg": selected_bg,
            "selected_fg": selected_fg,
            "selected_border": selected_fg,
            "focus_border": selected_bg,
            "disabled_bg": disabled_bg,
            "disabled_fg": cls.accessible_tab_text(disabled_bg, colors["muted"]),
        }

    def configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        if not getattr(self, "_treeview_sort_binding", False):
            self.root.bind_class("Treeview", "<Button-1>", self._sort_unregistered_treeview_heading, add="+")
            self._treeview_sort_binding = True
        self.themes = {
            "Dark Mode": {
                "chrome": "#080a0d", "chrome2": "#12161b", "paper": "#171b20", "panel": "#20262d",
                "panel_dark": "#2b343e", "line": "#3d4a56", "cream": "#252d35", "red": "#b51f2a",
                "gold": "#e0b457", "text": "#edf2f6", "muted": "#aab6c1", "tree": "#10151a",
                "tree_head": "#323e4a", "button": "#29333d", "button_text": "#f5f7f9",
            },
            "Fight Night": {
                "chrome": "#0b0d10", "chrome2": "#151b22", "paper": "#171a1f", "panel": "#20252d",
                "panel_dark": "#2d3540", "line": "#384553", "cream": "#252b34", "red": "#9b1f2b",
                "gold": "#d5a84b", "text": "#e8edf2", "muted": "#a8b3bf", "tree": "#11161c",
                "tree_head": "#313b48", "button": "#28313c", "button_text": "#f3f6f8",
            },
            "Classic Green": {
                "chrome": "#061806", "chrome2": "#09300d", "paper": "#1b2019", "panel": "#243024",
                "panel_dark": "#0f4f17", "line": "#4e5a4c", "cream": "#172016", "red": "#064d0f",
                "gold": "#f0c44c", "text": "#f2f2ea", "muted": "#d2d8cf", "tree": "#10180f",
                "tree_head": "#0b4a14", "button": "#111111", "button_text": "#f6f6ed",
            },
            "Light Office": {
                "chrome": "#1c1c1c", "chrome2": "#343434", "paper": "#d8d2c7", "panel": "#bdb6aa",
                "panel_dark": "#5a564e", "line": "#252525", "cream": "#f2eee6", "red": "#8e1f1b",
                "gold": "#c3a45d", "text": "#111111", "muted": "#333333", "tree": "#eee9df",
                "tree_head": "#777268", "button": "#c8c0b3", "button_text": "#111111",
            },
            "Matrix": {
                "chrome": "#020604", "chrome2": "#06140c", "paper": "#07100a", "panel": "#0b1b10",
                "panel_dark": "#0f2b18", "line": "#1f6f3a", "cream": "#031007", "red": "#00b85a",
                "gold": "#8cffb0", "text": "#d8ffe4", "muted": "#77c98f", "tree": "#020b05",
                "tree_head": "#07551f", "button": "#0e2414", "button_text": "#c9ffd7",
            },
            "Champion": {
                "chrome": "#080604", "chrome2": "#1a1309", "paper": "#12100c", "panel": "#241d12",
                "panel_dark": "#3a2a12", "line": "#6f5426", "cream": "#21190f", "red": "#8f1616",
                "gold": "#f3c45f", "text": "#fff3dc", "muted": "#cdb889", "tree": "#0d0a06",
                "tree_head": "#7d5a20", "button": "#302312", "button_text": "#fff0cf",
            },
            "UFC": {
                "chrome": "#090909", "chrome2": "#171717", "paper": "#151515", "panel": "#222222",
                "panel_dark": "#3a3a3a", "line": "#4b4b4b", "cream": "#262626", "red": "#d20a0a",
                "gold": "#f4f4f4", "text": "#f3f3f3", "muted": "#bdbdbd", "tree": "#101010",
                "tree_head": "#d20a0a", "button": "#2c2c2c", "button_text": "#ffffff",
            },
            "Cage Warriors": {
                "chrome": "#060606", "chrome2": "#111820", "paper": "#131922", "panel": "#1d2631",
                "panel_dark": "#cc9b22", "line": "#394554", "cream": "#202936", "red": "#b78a1c",
                "gold": "#f3c94f", "text": "#f2f2ed", "muted": "#c8c0a5", "tree": "#101722",
                "tree_head": "#8b6a18", "button": "#28323f", "button_text": "#fff6dc",
            },
            "PFL": {
                "chrome": "#071018", "chrome2": "#0d2230", "paper": "#101821", "panel": "#182532",
                "panel_dark": "#0b6f86", "line": "#2f5260", "cream": "#202d39", "red": "#0c8fa8",
                "gold": "#f0f7ff", "text": "#ecf8ff", "muted": "#a8c7d3", "tree": "#0c141d",
                "tree_head": "#0a6d84", "button": "#1d3342", "button_text": "#f0fbff",
            },
            "BAMMA": {
                "chrome": "#10100f", "chrome2": "#24221e", "paper": "#181715", "panel": "#292722",
                "panel_dark": "#d66f16", "line": "#5a4b39", "cream": "#27251f", "red": "#e67e18",
                "gold": "#ffe0a6", "text": "#fff5e5", "muted": "#d2b98d", "tree": "#12110f",
                "tree_head": "#bc5b0c", "button": "#353026", "button_text": "#fff4e2",
            },
            "ONE Championship": {
                "chrome": "#080808", "chrome2": "#1b1b1b", "paper": "#141414", "panel": "#242424",
                "panel_dark": "#7a0d14", "line": "#4d4d4d", "cream": "#292929", "red": "#bd1020",
                "gold": "#f4d276", "text": "#f5f5f5", "muted": "#c6c6c6", "tree": "#101010",
                "tree_head": "#9f0c18", "button": "#303030", "button_text": "#ffffff",
            },
            "RIZIN": {
                "chrome": "#050505", "chrome2": "#221312", "paper": "#151111", "panel": "#28201f",
                "panel_dark": "#a81720", "line": "#61413c", "cream": "#2b2321", "red": "#c51c27",
                "gold": "#f0d4aa", "text": "#fff4e6", "muted": "#d7bdb2", "tree": "#100d0d",
                "tree_head": "#8f131b", "button": "#382a28", "button_text": "#fff3e3",
            },
            "KSW": {
                "chrome": "#08111d", "chrome2": "#122740", "paper": "#101925", "panel": "#1d2a38",
                "panel_dark": "#ca1d2c", "line": "#3d5872", "cream": "#202f3e", "red": "#d52030",
                "gold": "#e8f2ff", "text": "#edf6ff", "muted": "#b6cadc", "tree": "#0c1520",
                "tree_head": "#173f6b", "button": "#283c50", "button_text": "#eff7ff",
            },
            "LFA": {
                "chrome": "#071420", "chrome2": "#102c42", "paper": "#101d29", "panel": "#1b3144",
                "panel_dark": "#d33a35", "line": "#41657c", "cream": "#203b4e", "red": "#d63c36",
                "gold": "#e7f4ff", "text": "#edf8ff", "muted": "#b9d2e5", "tree": "#0d1a25",
                "tree_head": "#1c5272", "button": "#29485d", "button_text": "#f3fbff",
            },
            "Oktagon": {
                "chrome": "#0b0b0a", "chrome2": "#23231d", "paper": "#151512", "panel": "#292821",
                "panel_dark": "#c69a24", "line": "#645836", "cream": "#2d2b20", "red": "#bd8514",
                "gold": "#fff0b1", "text": "#fff8df", "muted": "#dfcea0", "tree": "#10100d",
                "tree_head": "#917119", "button": "#373423", "button_text": "#fff7de",
            },
            "BRAVE": {
                "chrome": "#07120e", "chrome2": "#103326", "paper": "#102019", "panel": "#193a2b",
                "panel_dark": "#b78b20", "line": "#3d6752", "cream": "#203c30", "red": "#b88c21",
                "gold": "#fff0a1", "text": "#f1fae9", "muted": "#b8d1bd", "tree": "#0b1912",
                "tree_head": "#17613f", "button": "#294c3b", "button_text": "#f7ffe9",
            },
            "ACA": {
                "chrome": "#0a0e0c", "chrome2": "#1d3025", "paper": "#121a15", "panel": "#23372a",
                "panel_dark": "#497c43", "line": "#47634e", "cream": "#293d2e", "red": "#b42c2d",
                "gold": "#e7e6c1", "text": "#eff5e9", "muted": "#bdccb9", "tree": "#0d1510",
                "tree_head": "#35683b", "button": "#314a37", "button_text": "#f4faee",
            },
            "Boxing": {
                "chrome": "#100b08", "chrome2": "#332016", "paper": "#1b120d", "panel": "#352117",
                "panel_dark": "#a72b1c", "line": "#6c4330", "cream": "#3b271d", "red": "#bd321f",
                "gold": "#f5c66d", "text": "#fff0d9", "muted": "#d6b28d", "tree": "#130c09",
                "tree_head": "#7f2017", "button": "#4a2e22", "button_text": "#fff0dc",
            },
            "Kickboxing": {
                "chrome": "#07141a", "chrome2": "#12343b", "paper": "#102126", "panel": "#1b3b40",
                "panel_dark": "#db5b20", "line": "#3c7073", "cream": "#23464a", "red": "#d85a20",
                "gold": "#f7e3a5", "text": "#ecfbfa", "muted": "#b6d7d5", "tree": "#0b191d",
                "tree_head": "#167078", "button": "#2b5356", "button_text": "#effffd",
            },
            "Muay Thai": {
                "chrome": "#170a08", "chrome2": "#3c1712", "paper": "#21100d", "panel": "#432119",
                "panel_dark": "#c84819", "line": "#7a3e2c", "cream": "#4a291f", "red": "#c84519",
                "gold": "#f3c45d", "text": "#fff0d7", "muted": "#dbb28b", "tree": "#180b09",
                "tree_head": "#8d2d18", "button": "#593225", "button_text": "#fff1dd",
            },
            "Wrestling": {
                "chrome": "#0a1422", "chrome2": "#173557", "paper": "#102039", "panel": "#1d3858",
                "panel_dark": "#d39a22", "line": "#42688d", "cream": "#294665", "red": "#b6322d",
                "gold": "#ffe79a", "text": "#edf6ff", "muted": "#bad0e5", "tree": "#0c192b",
                "tree_head": "#214e7c", "button": "#315675", "button_text": "#f2f9ff",
            },
            "BJJ": {
                "chrome": "#0a0d18", "chrome2": "#22264b", "paper": "#14172a", "panel": "#292e54",
                "panel_dark": "#7652aa", "line": "#4e5785", "cream": "#303761", "red": "#8a3e57",
                "gold": "#ddd5ff", "text": "#f0eeff", "muted": "#c3c1e1", "tree": "#0f1221",
                "tree_head": "#4c4386", "button": "#3b4371", "button_text": "#f5f3ff",
            },
            "Sky Sports": {
                "chrome": "#061535", "chrome2": "#102d64", "paper": "#0c1d40", "panel": "#173563",
                "panel_dark": "#1b5cba", "line": "#3c6ca7", "cream": "#1d4176", "red": "#e30613",
                "gold": "#eef5ff", "text": "#eff6ff", "muted": "#bfd3ef", "tree": "#08162f",
                "tree_head": "#174d9b", "button": "#28528a", "button_text": "#f4f8ff",
            },
            "ESPN": {
                "chrome": "#090909", "chrome2": "#202020", "paper": "#151515", "panel": "#2a2a2a",
                "panel_dark": "#9d9d9d", "line": "#4e4e4e", "cream": "#303030", "red": "#d71920",
                "gold": "#f1f1f1", "text": "#f4f4f4", "muted": "#c1c1c1", "tree": "#101010",
                "tree_head": "#ba171d", "button": "#393939", "button_text": "#ffffff",
            },
            "BBC Sport": {
                "chrome": "#101010", "chrome2": "#2a2a2a", "paper": "#181818", "panel": "#303030",
                "panel_dark": "#494949", "line": "#5a5a5a", "cream": "#353535", "red": "#bc1c21",
                "gold": "#ffe53b", "text": "#f5f5f5", "muted": "#c5c5c5", "tree": "#111111",
                "tree_head": "#bc1c21", "button": "#3e3e3e", "button_text": "#ffffff",
            },
        }
        self.colors = self.themes.get(getattr(self, "theme_name", "Fight Night"), self.themes["Fight Night"])
        style.configure(".", font=("Tahoma", 8), background=self.colors["paper"], foreground=self.colors["text"])
        style.configure("TFrame", background=self.colors["paper"])
        style.configure("Chrome.TFrame", background=self.colors["chrome"])
        style.configure("Panel.TFrame", background=self.colors["panel"], relief="flat", borderwidth=1)
        style.configure("Inset.TFrame", background=self.colors["cream"], relief="flat", borderwidth=1)
        style.configure("Header.TFrame", background=self.colors["red"])
        style.configure("TLabel", font=("Tahoma", 8), background=self.colors["paper"], foreground=self.colors["text"])
        style.configure("Chrome.TLabel", font=("Tahoma", 8), background=self.colors["chrome"], foreground=self.colors["muted"])
        style.configure("Title.TLabel", font=("Impact", 20), background=self.colors["chrome"], foreground=self.colors["gold"])
        style.configure("ScreenTitle.TLabel", font=("Impact", 15), background=self.colors["red"], foreground="#ffffff")
        style.configure("Section.TLabel", font=("Impact", 10), background=self.colors["panel_dark"], foreground="#ffffff")
        style.configure("Discovery.TFrame", background=self.colors["panel_dark"], relief="flat", borderwidth=1)
        discovery_text = self.accessible_tab_text(self.colors["panel_dark"], self.colors["gold"])
        style.configure("Discovery.TLabel", font=("Tahoma", 8, "bold"), background=self.colors["panel_dark"], foreground=discovery_text)
        style.configure("Panel.TLabel", background=self.colors["panel"], foreground=self.colors["text"])
        style.configure("Inset.TLabel", background=self.colors["cream"], foreground=self.colors["text"])
        style.configure("Stat.TLabel", font=("Tahoma", 8, "bold"), background=self.colors["chrome2"], foreground=self.colors["text"])
        style.configure("TButton", font=("Tahoma", 8, "bold"), padding=(8, 4), background=self.colors["button"], foreground=self.colors["button_text"], borderwidth=1)
        style.map("TButton", background=[("active", self.colors["panel_dark"])])
        style.configure("Accent.TButton", font=("Tahoma", 8, "bold"), background=self.colors["red"], foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", self.colors["gold"])], foreground=[("active", "#111111")])
        # Native progress bars fall back to a low-contrast grey-on-grey Windows
        # treatment. Give general activity and each fight corner a solid fill
        # over the same dark track so progress remains legible at a glance.
        progress_track = "#101318"
        progress_border = "#59636f"
        progress_styles = {
            "Activity.Horizontal.TProgressbar": self.colors["gold"],
            "RedCorner.Horizontal.TProgressbar": "#e0444e",
            "BlueCorner.Horizontal.TProgressbar": "#3d8cff",
        }
        for progress_style, fill_color in progress_styles.items():
            style.configure(
                progress_style,
                troughcolor=progress_track,
                background=fill_color,
                bordercolor=progress_border,
                lightcolor=fill_color,
                darkcolor=fill_color,
                thickness=14,
            )
        self.live_fight_condition_styles = {
            "red": "RedCorner.Horizontal.TProgressbar",
            "blue": "BlueCorner.Horizontal.TProgressbar",
        }
        # Sidebar navigation buttons: default look, plus a highlighted "active screen" look.
        style.configure("Nav.TButton", font=("Tahoma", 8, "bold"), padding=(8, 4), anchor="w", background=self.colors["button"], foreground=self.colors["button_text"], borderwidth=1)
        style.map("Nav.TButton", background=[("active", self.colors["panel_dark"])])
        style.configure("NavActive.TButton", font=("Tahoma", 8, "bold"), padding=(8, 4), anchor="w", background=self.colors["gold"], foreground="#111111", borderwidth=1)
        style.map("NavActive.TButton", background=[("active", self.colors["gold"])], foreground=[("active", "#111111")])
        input_bg = self.colors["cream"]
        input_fg = self.colors["text"]
        selected_bg = self.colors["red"]
        input_chrome = self.colors["panel"]
        style.configure("TEntry", fieldbackground=input_bg, background=input_bg, foreground=input_fg, insertcolor=input_fg, bordercolor=self.colors["line"], lightcolor=self.colors["line"], darkcolor=self.colors["line"])
        style.map("TEntry", fieldbackground=[("disabled", input_chrome), ("readonly", input_bg), ("focus", input_bg)], background=[("disabled", input_chrome), ("readonly", input_bg)], foreground=[("disabled", self.colors["muted"]), ("readonly", input_fg), ("focus", input_fg)])
        style.configure("TSpinbox", fieldbackground=input_bg, background=input_chrome, foreground=input_fg, insertcolor=input_fg, arrowcolor=input_fg, bordercolor=self.colors["line"], lightcolor=self.colors["line"], darkcolor=self.colors["line"])
        style.map("TSpinbox", fieldbackground=[("disabled", input_chrome), ("readonly", input_bg), ("focus", input_bg)], background=[("disabled", input_chrome), ("readonly", input_chrome), ("active", self.colors["panel_dark"])], foreground=[("disabled", self.colors["muted"]), ("readonly", input_fg), ("focus", input_fg)])
        style.configure("TCombobox", fieldbackground=input_bg, background=input_chrome, foreground=input_fg, arrowcolor=input_fg, selectbackground=selected_bg, selectforeground="#ffffff", bordercolor=self.colors["line"], lightcolor=self.colors["line"], darkcolor=self.colors["line"])
        style.map("TCombobox", fieldbackground=[("disabled", input_chrome), ("readonly", input_bg), ("focus", input_bg)], background=[("disabled", input_chrome), ("readonly", input_chrome), ("active", self.colors["panel_dark"])], foreground=[("disabled", self.colors["muted"]), ("readonly", input_fg), ("focus", input_fg)], selectbackground=[("readonly", selected_bg), ("focus", selected_bg)], selectforeground=[("readonly", "#ffffff"), ("focus", "#ffffff")])
        style.configure("TCheckbutton", background=self.colors["paper"], foreground=input_fg)
        style.map("TCheckbutton", background=[("active", self.colors["panel"]), ("disabled", self.colors["paper"])], foreground=[("disabled", self.colors["muted"])])
        style.configure("TRadiobutton", background=self.colors["paper"], foreground=input_fg)
        style.map("TRadiobutton", background=[("active", self.colors["panel"]), ("disabled", self.colors["paper"])], foreground=[("disabled", self.colors["muted"])])
        self.root.option_add("*Entry.background", input_bg)
        self.root.option_add("*Entry.foreground", input_fg)
        self.root.option_add("*Entry.insertBackground", input_fg)
        self.root.option_add("*Spinbox.background", input_bg)
        self.root.option_add("*Spinbox.foreground", input_fg)
        self.root.option_add("*Spinbox.insertBackground", input_fg)
        self.root.option_add("*TCombobox*Listbox.background", input_bg)
        self.root.option_add("*TCombobox*Listbox.foreground", input_fg)
        self.root.option_add("*TCombobox*Listbox.selectBackground", self.colors["red"])
        self.root.option_add("*TCombobox*Listbox.selectForeground", "#ffffff")
        # Every visible notebook shares these state-aware colors.  In ttk,
        # "selected" is the current/active tab while "active" is pointer hover.
        # The selected tab also gains a high-contrast outline and raised edge, so state is
        # not communicated by color alone.
        self.tab_colors = self.tab_style_palette(self.colors)
        style.configure("TNotebook", background=self.colors["chrome"], borderwidth=0, tabmargins=(0, 2, 0, 0))
        style.configure(
            "TNotebook.Tab",
            font=("Tahoma", 9, "bold"),
            padding=(16, 6),
            background=self.tab_colors["inactive_bg"],
            foreground=self.tab_colors["inactive_fg"],
            bordercolor=self.colors["line"],
            lightcolor=self.colors["line"],
            darkcolor=self.colors["chrome"],
            focuscolor=self.tab_colors["focus_border"],
            borderwidth=2,
            relief="flat",
        )
        style.map(
            "TNotebook.Tab",
            background=[
                ("disabled", self.tab_colors["disabled_bg"]),
                ("selected", self.tab_colors["selected_bg"]),
                ("active", self.tab_colors["hover_bg"]),
            ],
            foreground=[
                ("disabled", self.tab_colors["disabled_fg"]),
                ("selected", self.tab_colors["selected_fg"]),
                ("active", self.tab_colors["hover_fg"]),
            ],
            bordercolor=[
                ("selected", self.tab_colors["selected_border"]),
                ("focus", self.tab_colors["focus_border"]),
                ("active", self.colors["gold"]),
            ],
            lightcolor=[("selected", self.tab_colors["selected_border"])],
            darkcolor=[("selected", self.tab_colors["selected_border"])],
            relief=[("selected", "raised"), ("active", "raised")],
            expand=[("selected", (1, 1, 1, 0))],
        )
        style.configure("Hidden.TNotebook", background=self.colors["chrome"], borderwidth=0)
        style.layout("Hidden.TNotebook.Tab", [])
        style.configure("Treeview", font=("Tahoma", 8), background=self.colors["tree"], fieldbackground=self.colors["tree"], foreground=self.colors["text"], rowheight=22, borderwidth=0)
        style.configure("Treeview.Heading", font=("Tahoma", 8, "bold"), background=self.colors["tree_head"], foreground="#ffffff", relief="flat")
        style.configure("Profile.Treeview", font=("Tahoma", 9), background=self.colors["tree"],
                        fieldbackground=self.colors["tree"], foreground=self.colors["text"],
                        rowheight=27, borderwidth=0)
        style.configure("Profile.Treeview.Heading", font=("Tahoma", 8, "bold"),
                        background=self.colors["tree_head"], foreground="#ffffff",
                        padding=(7, 6), relief="flat")

    def scroll_active_page_with_arrow(self, event, axis, direction):
        """Scroll the hovered page without taking arrows from data-entry widgets."""
        native_arrow_widgets = (
            tk.Entry, tk.Text, tk.Listbox, tk.Spinbox, tk.Scale,
            ttk.Entry, ttk.Combobox, ttk.Treeview, ttk.Spinbox,
        )
        if isinstance(event.widget, native_arrow_widgets):
            return None
        active = getattr(self, "_active_scroll_wheel", None)
        if not active:
            return None
        canvas = active[0]
        try:
            if axis == "x":
                canvas.xview_scroll(direction * 3, "units")
            else:
                canvas.yview_scroll(direction * 3, "units")
        except tk.TclError:
            return None
        return "break"

    def create_scrollable_frame(self, parent, style="TFrame"):
        shell = ttk.Frame(parent, style=style)
        canvas = tk.Canvas(shell, bg=self.colors["paper"], highlightthickness=0, borderwidth=0)
        scroll = ttk.Scrollbar(shell, orient="vertical", command=canvas.yview)
        horizontal = ttk.Scrollbar(shell, orient="horizontal", command=canvas.xview)
        inner = ttk.Frame(canvas, style=style)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        fit_pending = [False]

        def fit_content_to_viewport():
            fit_pending[0] = False
            # Expand ordinary pages to the complete visible viewport so children
            # packed with expand=True (especially Treeviews) receive the unused
            # height. Preserve larger natural dimensions for genuinely long or
            # wide pages, which remain reachable through the page scrollbars.
            # Some dense screens contain their own responsive panes and table
            # scrollbars. They must remain fitted to the visible page instead
            # of making the entire management page wider than the viewport.
            force_viewport_width = bool(getattr(inner, "_force_viewport_width", False))
            width = max(1, canvas.winfo_width()) if force_viewport_width else max(1, canvas.winfo_width(), inner.winfo_reqwidth())
            height = max(1, canvas.winfo_height(), inner.winfo_reqheight())
            canvas.itemconfigure(window_id, width=width, height=height)
            canvas.configure(scrollregion=(0, 0, width, height))

        def schedule_fit(_event=None):
            if not fit_pending[0]:
                fit_pending[0] = True
                canvas.after_idle(fit_content_to_viewport)

        def wheel(event):
            delta = -1 if event.delta > 0 else 1
            if sys.platform == "darwin":
                delta = -event.delta
            # Treeviews, text boxes and listboxes already have correct native
            # wheel behaviour. Do not also move the containing page beneath them.
            if isinstance(event.widget, (ttk.Treeview, tk.Text, tk.Listbox)):
                return None
            canvas.yview_scroll(delta, "units")
            return "break"

        def linux_wheel(event, delta):
            if isinstance(event.widget, (ttk.Treeview, tk.Text, tk.Listbox)):
                return None
            canvas.yview_scroll(delta, "units")
            return "break"

        def activate_wheel(_event=None):
            self._active_scroll_wheel = (canvas, wheel, linux_wheel)

        def deactivate_wheel(_event=None):
            # This handler clears the attribute to None, so a later leave event
            # finds it present-but-None. A getattr default only covers a missing
            # attribute, never a None value, so check the value itself.
            active = getattr(self, "_active_scroll_wheel", None)
            if active and active[0] is canvas:
                self._active_scroll_wheel = None

        if not getattr(self, "_scroll_wheel_dispatch_installed", False):
            def dispatch_wheel(event):
                active = getattr(self, "_active_scroll_wheel", None)
                if not active:
                    return None
                return active[1](event)

            def dispatch_linux_wheel(event, delta):
                active = getattr(self, "_active_scroll_wheel", None)
                if not active:
                    return None
                return active[2](event, delta)

            self.root.bind_all("<MouseWheel>", dispatch_wheel, add="+")
            self.root.bind_all("<Button-4>", lambda event: dispatch_linux_wheel(event, -1), add="+")
            self.root.bind_all("<Button-5>", lambda event: dispatch_linux_wheel(event, 1), add="+")
            self._scroll_wheel_dispatch_installed = True

        if not getattr(self, "_arrow_scroll_dispatch_installed", False):
            self.root.bind_all("<Up>", lambda event: self.scroll_active_page_with_arrow(event, "y", -1), add="+")
            self.root.bind_all("<Down>", lambda event: self.scroll_active_page_with_arrow(event, "y", 1), add="+")
            self.root.bind_all("<Left>", lambda event: self.scroll_active_page_with_arrow(event, "x", -1), add="+")
            self.root.bind_all("<Right>", lambda event: self.scroll_active_page_with_arrow(event, "x", 1), add="+")
            self._arrow_scroll_dispatch_installed = True

        inner.bind("<Configure>", schedule_fit)
        canvas.bind("<Configure>", schedule_fit)
        shell.bind("<Enter>", activate_wheel)
        shell.bind("<Leave>", deactivate_wheel)
        canvas.configure(yscrollcommand=scroll.set, xscrollcommand=horizontal.set)
        shell.rowconfigure(0, weight=1)
        shell.columnconfigure(0, weight=1)
        canvas.grid(row=0, column=0, sticky="nsew")
        scroll.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        if not hasattr(self, "scrollable_canvases"):
            self.scrollable_canvases = []
        self.scrollable_canvases.append(canvas)
        shell._scroll_canvas = canvas
        shell._scroll_inner = inner
        return shell, inner

    def create_main_tab(self):
        page, content = self.create_scrollable_frame(self.tabs)
        return page, content

    def build_layout(self):
        report_startup = getattr(self, "report_startup_progress", lambda *_args: None)
        report_startup(79, "Building the promoter office...")
        shell = ttk.Frame(self.root, style="Chrome.TFrame")
        shell.pack(fill="both", expand=True)

        titlebar = ttk.Frame(shell, style="Chrome.TFrame")
        titlebar.pack(fill="x")
        self.logo_canvas = tk.Canvas(titlebar, width=76, height=42, bg=self.colors["chrome"], highlightthickness=0)
        self.logo_canvas.pack(side="left", padx=(12, 4), pady=5)
        self.draw_logo()
        ttk.Label(titlebar, text=GAME_NAME.upper(), style="Title.TLabel").pack(side="left", padx=8, pady=8)
        ttk.Button(titlebar, text="Tutorial", command=self.open_tutorial_guide).pack(side="right", padx=(2, 10))
        self.theme_name_var = tk.StringVar(value=getattr(self, "theme_name", "Fight Night"))
        ttk.Button(titlebar, text="Apply Theme", command=self.apply_selected_theme).pack(side="right", padx=(2, 10))
        ttk.Combobox(titlebar, values=list(self.themes.keys()), textvariable=self.theme_name_var, state="readonly", width=20, height=22).pack(side="right", padx=(2, 6))
        ttk.Label(titlebar, text="Theme", style="Chrome.TLabel").pack(side="right", padx=(12, 2))
        ttk.Label(titlebar, text="Promoter Office", style="Chrome.TLabel").pack(side="right", padx=18)

        self.statusbar = ttk.Frame(shell, style="Chrome.TFrame")
        self.statusbar.pack(fill="x", padx=8, pady=(0, 4))
        self.stat_month = ttk.Label(self.statusbar, width=16, anchor="center", style="Stat.TLabel")
        self.stat_cash = ttk.Label(self.statusbar, width=18, anchor="center", style="Stat.TLabel")
        self.stat_company = ttk.Label(self.statusbar, anchor="w", style="Stat.TLabel")
        self.stat_pop = ttk.Label(self.statusbar, width=15, anchor="center", style="Stat.TLabel")
        self.stat_stability = ttk.Label(self.statusbar, width=13, anchor="center", style="Stat.TLabel")
        status_labels = (self.stat_month, self.stat_cash, self.stat_company, self.stat_pop, self.stat_stability)
        for column, label in enumerate(status_labels):
            label.grid(row=0, column=column, sticky="ew", padx=2, ipady=4)
        # The promotion name is the only flexible status field. Maximized
        # windows give it the spare width, while the business values remain
        # stable and readable when a long company name has to compress.
        self.statusbar.columnconfigure(2, weight=1, minsize=170)

        # Advancing is always visible here, even when the left navigation needs
        # scrolling on a laptop-sized display. Spectator fast-forward remains in
        # the Game Menu; this normal one-week button is hidden in observer saves.
        self.advance_activity = ttk.Frame(self.statusbar, style="Chrome.TFrame")
        self.advance_activity.grid(row=0, column=5, sticky="e", padx=(6, 2))
        self.advance_button = ttk.Button(
            self.advance_activity,
            text="Advance Week",
            style="Accent.TButton",
            command=self.request_advance_week,
        )
        self.advance_button.pack(side="right", padx=(6, 0), ipady=2)
        self.advance_progress = ttk.Progressbar(self.advance_activity, mode="determinate", maximum=100, length=105)
        self.advance_status = ttk.Label(self.advance_activity, text="", width=26, anchor="e", style="Chrome.TLabel")

        work = ttk.Frame(shell, style="Chrome.TFrame")
        work.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        nav_shell = ttk.Frame(work, style="Panel.TFrame", width=174)
        nav_shell.pack(side="left", fill="y", padx=(0, 8))
        nav_shell.pack_propagate(False)
        nav_canvas = tk.Canvas(nav_shell, width=154, bg=self.colors["panel"], highlightthickness=0, borderwidth=0)
        nav_scroll = ttk.Scrollbar(nav_shell, orient="vertical", command=nav_canvas.yview)
        nav = ttk.Frame(nav_canvas, style="Panel.TFrame")
        nav_window = nav_canvas.create_window((0, 0), window=nav, anchor="nw")
        nav.bind("<Configure>", lambda _event: nav_canvas.configure(scrollregion=nav_canvas.bbox("all")))
        nav_canvas.bind("<Configure>", lambda event: nav_canvas.itemconfigure(nav_window, width=event.width))
        nav_canvas.configure(yscrollcommand=nav_scroll.set)
        nav_canvas.pack(side="left", fill="both", expand=True)
        nav_scroll.pack(side="right", fill="y")
        groups = (
            ("TODAY", (("Dashboard", "assistant"), ("Inbox", "inbox"), ("Media Desk", "website"), ("Fight Night", "log"))),
            ("PROMOTION", (("Roster", "roster"), ("Matchmaking", "booking"), ("Contracts", "contracts"), ("Free Agents", "market"), ("Scouting", "scouting"), ("Fight Academy", "academy"), ("Staff", "staff"), ("Finance", "finance"))),
            ("WORLD", (("World", "world"), ("Regional Prospects", "regional_prospects"), ("Fighter Search", "fighter_search"), ("Combat Sports", "combat_sports"), ("Companies", "companies"), ("Rankings", "rankings"), ("Results", "results"), ("Regions", "regions"))),
            ("TOOLS", (("Game & Saves", "game_menu"), ("Rules Help", "help"), ("Company Rules", "company_editor"), ("World Editor", "editor"), ("Sim Lab", "sim_lab"))),
        )
        self.nav_buttons = {}
        for heading, entries in groups:
            ttk.Label(nav, text=heading, anchor="center", style="Section.TLabel").pack(fill="x", padx=6, pady=(5, 2), ipady=2)
            for text, tab in entries:
                button = ttk.Button(nav, text=text, style="Nav.TButton", command=lambda name=tab: self.select_tab(name))
                button.pack(fill="x", padx=8, pady=1)
                self.nav_buttons[tab] = button
        ttk.Separator(nav).pack(fill="x", padx=10, pady=10)
        ttk.Button(nav, text="Quick Save", command=self.save_game).pack(fill="x", padx=10, pady=3)
        ttk.Button(nav, text="Quick Load", command=self.load_game).pack(fill="x", padx=10, pady=3)

        main = ttk.Frame(work, style="Panel.TFrame")
        main.pack(side="left", fill="both", expand=True)
        self.tabs = ttk.Notebook(main, style="Hidden.TNotebook")
        self.tabs.pack(fill="both", expand=True, padx=6, pady=6)

        self.tab_pages = {}
        tab_specs = (
            ("game_menu", "game_menu_tab", "Game Menu"),
            ("help", "help_tab", "Rules Help"),
            ("website", "website_tab", "Website"),
            ("assistant", "assistant_tab", "Assistant"),
            ("roster", "roster_tab", "Roster"),
            ("contracts", "contracts_tab", "Contracts"),
            ("companies", "companies_tab", "Companies"),
            ("regions", "regions_tab", "Regions"),
            ("results", "results_tab", "Results"),
            ("company_editor", "company_editor_tab", "Company Editor"),
            ("inbox", "inbox_tab", "Inbox"),
            ("staff", "staff_tab", "Staff"),
            ("scouting", "scouting_tab", "Scouting"),
            ("finance", "finance_tab", "Finance"),
            ("booking", "booking_tab", "Booking"),
            ("market", "market_tab", "Free Agents"),
            ("world", "world_tab", "World"),
            ("regional_prospects", "regional_prospects_tab", "Regional Prospects"),
            ("fighter_search", "fighter_search_tab", "Fighter Search"),
            ("rankings", "rankings_tab", "Rankings"),
            ("academy", "academy_tab", "Fight Academy"),
            ("combat_sports", "combat_sports_tab", "Combat Sports"),
            ("editor", "editor_tab", "Editor"),
            ("sim_lab", "sim_lab_tab", "Sim Lab"),
            ("log", "log_tab", "Fight Night"),
        )
        for name, attr, label in tab_specs:
            page, content = self.create_main_tab()
            self.tab_pages[name] = page
            setattr(self, attr, content)
            self.tabs.add(page, text=label)

        self.screen_builders = {
            "game_menu": self.build_game_menu_tab,
            "help": self.build_help_tab,
            "website": self.build_website_tab,
            "assistant": self.build_assistant_tab,
            "roster": self.build_roster_tab,
            "contracts": self.build_contracts_tab,
            "companies": self.build_companies_tab,
            "regions": self.build_regions_tab,
            "results": self.build_results_tab,
            "company_editor": self.build_company_editor_tab,
            "inbox": self.build_inbox_tab,
            "staff": self.build_staff_tab,
            "scouting": self.build_scouting_tab,
            "finance": self.build_finance_tab,
            "booking": self.build_booking_tab,
            "market": self.build_market_tab,
            "world": self.build_world_tab,
            "regional_prospects": self.build_regional_prospects_tab,
            "fighter_search": self.build_fighter_search_tab,
            "rankings": self.build_rankings_tab,
            "academy": self.build_academy_tab,
            "combat_sports": self.build_combat_sports_tab,
            "editor": self.build_editor_tab,
            "sim_lab": self.build_sim_lab_tab,
            "log": self.build_log_tab,
        }
        self.built_screens = set()
        self._building_screens = set()
        report_startup(88, "Preparing the promoter dashboard...")
        self.ensure_screen_built("game_menu")
        report_startup(95, "Applying the presentation theme...")
        self.retheme_plain_widgets(self.root)
        self.select_tab("game_menu")

    def ensure_screen_built(self, name):
        """Construct a management screen once, when the player first opens it."""
        if name in getattr(self, "built_screens", set()) or name in getattr(self, "_building_screens", set()):
            return
        builder = getattr(self, "screen_builders", {}).get(name)
        if not builder:
            return
        self._building_screens.add(name)
        try:
            builder()
            self.built_screens.add(name)
            # Lazy screens can be opened after the last global theme pass.
            # Apply semantic Treeview accents immediately so Light Office (or
            # any alternate palette) does not inherit fixed dark-theme row
            # colours on first entry.
            self.retheme_plain_widgets(self.root)
        finally:
            self._building_screens.discard(name)

    def apply_selected_theme(self):
        previous_colors = dict(getattr(self, "colors", {}) or {})
        self.theme_name = self.theme_name_var.get()
        self.configure_style()
        self.retheme_plain_widgets(self.root, previous_colors)
        for pane in getattr(self, "vertical_resize_panes", []):
            try:
                pane.configure(bg=self.colors["panel"])
            except tk.TclError:
                pass
        for pane in getattr(self, "responsive_layout_panes", []):
            try:
                pane.configure(bg=self.colors["panel"])
            except tk.TclError:
                pass
        spacer = getattr(self, "market_resize_spacer", None)
        if spacer:
            spacer.configure(bg=self.colors["paper"])
        self.draw_logo()
        if hasattr(self, "render_event_log"):
            self.render_event_log()

    def open_tutorial_guide(self):
        tutorial_path = ASSET_DIR / "tutorial.html"
        if not tutorial_path.exists():
            messagebox.showerror("Tutorial not found", f"Could not find the tutorial guide at:\n{tutorial_path}")
            return
        webbrowser.open(tutorial_path.as_uri())

    def build_help_tab(self):
        """Build the authored, searchable rules reference as a normal page."""
        self.screen_header(
            self.help_tab,
            "RULES HELP",
            "Search the decision vocabulary without exposing hidden state",
        )
        body = ttk.Frame(self.help_tab)
        body.pack(fill="both", expand=True)

        toolbar = ttk.Frame(body, style="Panel.TFrame")
        toolbar.pack(fill="x", pady=(0, 6))
        ttk.Label(toolbar, text="Search topics", style="Panel.TLabel").pack(side="left", padx=(8, 5), pady=7)
        saved_rules = getattr(self, "rules", {})
        if not isinstance(saved_rules, dict):
            saved_rules = {}
        self.help_search_var = tk.StringVar(value=str(saved_rules.get("ui_help_search", "") or ""))
        search = ttk.Entry(toolbar, textvariable=self.help_search_var)
        search.pack(side="left", fill="x", expand=True, padx=4, pady=5)
        ttk.Button(toolbar, text="Clear", command=lambda: (self.help_search_var.set(""), self.refresh_help_topics())).pack(side="left", padx=4, pady=4)
        self.help_search_status = ttk.Label(toolbar, text="", style="Panel.TLabel")
        self.help_search_status.pack(side="right", padx=8)
        search.bind("<KeyRelease>", lambda _event: self.refresh_help_topics())

        split = tk.PanedWindow(body, orient="horizontal", bg=self.colors["line"], bd=0, sashwidth=7, sashrelief="raised")
        split.pack(fill="both", expand=True)
        topic_frame = tk.Frame(split, bg=self.colors["tree"])
        topic_frame.rowconfigure(0, weight=1)
        topic_frame.columnconfigure(0, weight=1)
        self.help_topic_list = tk.Listbox(
            topic_frame, bg=self.colors["tree"], fg=self.colors["text"],
            selectbackground=self.colors["red"], selectforeground="#ffffff",
            activestyle="none", exportselection=False, borderwidth=0,
            font=("Tahoma", 10), width=30,
        )
        help_scroll = ttk.Scrollbar(topic_frame, orient="vertical", command=self.help_topic_list.yview)
        self.help_topic_list.configure(yscrollcommand=help_scroll.set)
        self.help_topic_list.grid(row=0, column=0, sticky="nsew")
        help_scroll.grid(row=0, column=1, sticky="ns")
        split.add(topic_frame, minsize=210, width=300, stretch="never")

        detail_frame = ttk.Frame(split, style="Panel.TFrame")
        detail_frame.rowconfigure(1, weight=1)
        detail_frame.columnconfigure(0, weight=1)
        self.help_topic_title = ttk.Label(detail_frame, text="Select a topic", style="ScreenTitle.TLabel", anchor="w")
        self.help_topic_title.grid(row=0, column=0, sticky="ew", padx=12, pady=(10, 5))
        self.help_topic_detail = tk.Text(
            detail_frame, wrap="word", bg=self.colors["cream"], fg=self.colors["text"],
            insertbackground=self.colors["text"], font=("Tahoma", 10),
            padx=12, pady=10, borderwidth=0, state="disabled",
        )
        self.help_topic_detail.grid(row=1, column=0, sticky="nsew", padx=8, pady=(0, 6))
        detail_scroll = ttk.Scrollbar(detail_frame, orient="vertical", command=self.help_topic_detail.yview)
        detail_scroll.grid(row=1, column=1, sticky="ns", pady=(0, 6))
        self.help_topic_detail.configure(yscrollcommand=detail_scroll.set)
        action_row = ttk.Frame(detail_frame, style="Inset.TFrame")
        action_row.grid(row=2, column=0, columnspan=2, sticky="ew", padx=8, pady=(0, 8))
        self.help_action_button = ttk.Button(action_row, text="Open linked screen", state="disabled")
        self.help_action_button.pack(side="left", padx=4, pady=4)
        ttk.Label(
            action_row,
            text="Links open the source screen; help itself never runs a resolver.",
            style="Inset.TLabel",
        ).pack(side="left", padx=8)
        split.add(detail_frame, minsize=420, stretch="always")
        self.help_topic_list.bind("<<ListboxSelect>>", self.show_help_topic)
        self.refresh_help_topics()

    def refresh_help_topics(self):
        """Refresh only the authored help index and preserve topic identity."""
        listing = getattr(self, "help_topic_list", None)
        if listing is None:
            return
        previous_id = ""
        selected = listing.curselection()
        if selected:
            rows = getattr(self, "help_topic_rows", [])
            if selected[0] < len(rows):
                previous_id = str(rows[selected[0]].get("topic_id", ""))
        search_var = getattr(self, "help_search_var", None)
        query = str(search_var.get() if search_var is not None else "")
        # Persist only the separately allowed UI search preference. A malformed
        # rules envelope remains untouched until the normal load/migration
        # boundary; help filtering itself is still a pure catalogue read.
        if isinstance(getattr(self, "rules", None), dict):
            self.rules["ui_help_search"] = query
        rows = search_help_topics(query)
        self.help_topic_rows = rows
        listing.delete(0, "end")
        for topic in rows:
            listing.insert("end", topic.get("title", "Untitled topic"))
        if rows:
            index = next((i for i, topic in enumerate(rows) if topic.get("topic_id") == previous_id), 0)
            listing.selection_set(index)
            listing.see(index)
            self.show_help_topic()
        else:
            self.help_topic_title.configure(text="No matching topic")
            self.help_topic_detail.configure(state="normal")
            self.help_topic_detail.delete("1.0", "end")
            self.help_topic_detail.insert("end", "No authored help topic matches this search. Try a term such as rank, title, camp, staff, cost, contract, finance or weigh-in.")
            self.help_topic_detail.configure(state="disabled")
            self.help_action_button.configure(state="disabled", text="Open linked screen")
        if hasattr(self, "help_search_status"):
            self.help_search_status.configure(text=f"{len(rows)} topic(s)")

    def show_help_topic(self, _event=None):
        listing = getattr(self, "help_topic_list", None)
        rows = getattr(self, "help_topic_rows", [])
        selected = listing.curselection() if listing is not None else ()
        topic = rows[selected[0]] if selected and selected[0] < len(rows) else None
        if not topic:
            return
        self.help_topic_title.configure(text=topic.get("title", "Help topic"))
        terms = ", ".join(str(value) for value in topic.get("terms", ()) or ()) or "None listed"
        aliases = ", ".join(str(value) for value in topic.get("aliases", ()) or ()) or "None listed"
        content = (
            f"{topic.get('summary', '')}\n\n"
            f"EXPLANATION\n{topic.get('answer', '')}\n\n"
            f"WHY THIS CAN BE BLOCKED\n{topic.get('why_blocked', '')}\n\n"
            f"LINKED TERMS\n{terms}\n\n"
            f"SEARCH ALIASES\n{aliases}\n"
        )
        self.help_topic_detail.configure(state="normal")
        self.help_topic_detail.delete("1.0", "end")
        self.help_topic_detail.insert("end", content)
        self.help_topic_detail.configure(state="disabled")
        route = str(topic.get("action_route", "") or "")
        available = route in getattr(self, "tab_pages", {})
        self.help_action_button.configure(
            state="normal" if available else "disabled",
            text=topic.get("action_label", "Open linked screen") if available else "Linked screen unavailable",
            command=(lambda route=route: self.select_tab(route)) if available else (lambda: None),
        )

    def draw_logo(self):
        if not hasattr(self, "logo_canvas"):
            return
        c = self.logo_canvas
        c.delete("all")
        c.configure(bg=self.colors["chrome"])
        c.create_polygon(6, 36, 24, 6, 38, 36, fill=self.colors["red"], outline=self.colors["gold"], width=2)
        c.create_polygon(38, 36, 52, 6, 70, 36, fill=self.colors["panel_dark"], outline=self.colors["gold"], width=2)
        c.create_text(38, 24, text="MW", fill=self.colors["gold"], font=("Impact", 17))

    def retheme_plain_widgets(self, widget, previous_colors=None):
        """Retheme native widgets, including custom card frames/labels.

        Most management pages use ttk styles, but the card/detail portions use
        classic Tk widgets for exact typography and drawing.  Those widgets do
        not follow ttk when a theme changes, so remap known semantic colours
        from the previous palette before applying the new one.  Unknown colours
        are intentionally preserved for authored artwork/status accents.
        """
        color_map = {}
        old = previous_colors or {}
        for key, value in old.items():
            if value:
                color_map[str(value).lower()] = self.colors.get(key, value)
        # Legacy hand-authored card colours used before semantic palette tokens.
        color_map.update({
            "#29261e": self.colors["panel_dark"], "#625137": self.colors["line"],
            "#d5ad62": self.colors["gold"], "#e8c789": self.colors["gold"],
            "#eee4d2": self.colors["text"], "#25332e": self.colors["panel_dark"],
            "#d4eadc": self.colors["text"], "#ff766d": self.colors["red"],
            "#ffe08a": self.colors["gold"],
        })

        def remap(value):
            return color_map.get(str(value).lower(), value)

        semantic = self.semantic_status_palette(self.colors)
        tree_tag_groups = {
            # These groups cover known status tags across management, scouting,
            # finance and profile tables. Rows that deliberately carry a dark
            # authored background are handled below only when the selected
            # semantic foreground still passes contrast.
            "positive": (
                "win", "rec_win", "complete", "delivered", "active", "advice_sign",
                "tier_regional", "owned", "rising", "strong", "ready", "preserved",
            ),
            "negative": (
                "loss", "rec_loss", "risk", "failed", "negative", "expired", "medical",
                "unavailable", "shortfall", "sliding", "injured", "urgent",
            ),
            "warning": (
                "soon", "final", "stale", "attention", "nearly", "advice_monitor",
                "tier_national", "unread", "recommended", "hold", "partial", "open", "review", "normal",
            ),
            "info": (
                "offer", "shortlisted", "tier_global", "available", "assignment_pending", "booked",
            ),
            "neutral": (
                "advice_pass", "tier_local", "archived", "not_ready", "developing", "retired",
                "locked", "top_contender", "closed",
            ),
        }
        text_tag_groups = {
            "negative": ("urgent",),
            "warning": ("normal",),
            "positive": ("log_result",),
            "info": ("log_action",),
            "neutral": ("log_system", "log_body"),
        }

        for canvas in getattr(self, "scrollable_canvases", []):
            try:
                canvas.configure(bg=self.colors["paper"])
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            if isinstance(child, tk.Text):
                child.configure(bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
                for semantic_name, tags in text_tag_groups.items():
                    for tag in tags:
                        try:
                            child.tag_configure(tag, foreground=semantic[semantic_name])
                        except tk.TclError:
                            pass
            elif isinstance(child, tk.Listbox):
                child.configure(bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
            elif isinstance(child, (tk.Entry, tk.Spinbox)):
                try:
                    child.configure(bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
                except tk.TclError:
                    pass
            elif isinstance(child, ttk.Treeview):
                # Treeview tag colours are not controlled by ttk styles and
                # otherwise remain the previous theme's pale accents after a
                # live theme switch.  Update known semantic tags while leaving
                # authored row backgrounds and unknown future tags intact.
                for semantic_name, tags in tree_tag_groups.items():
                    for tag in tags:
                        try:
                            # A number of legacy rows use a fixed dark
                            # background (e.g. recommended, medical and
                            # closed-division warnings).  Do not replace a
                            # readable light foreground with a dark Light
                            # Office colour on those rows.
                            tag_background = str(child.tag_configure(tag, "background") or "")
                            candidate = semantic[semantic_name]
                            if not tag_background or self.wcag_contrast_ratio(candidate, tag_background) >= 4.5:
                                child.tag_configure(tag, foreground=candidate)
                        except tk.TclError:
                            pass
            elif isinstance(child, tk.Canvas):
                try:
                    child.configure(bg=remap(child.cget("background")))
                except tk.TclError:
                    pass
            elif isinstance(child, tk.Frame):
                try:
                    child.configure(bg=remap(child.cget("background")))
                    if child.cget("highlightbackground"):
                        child.configure(highlightbackground=remap(child.cget("highlightbackground")))
                except tk.TclError:
                    pass
            elif isinstance(child, tk.Label):
                try:
                    child.configure(bg=remap(child.cget("background")), fg=remap(child.cget("foreground")))
                    semantic_name = getattr(child, "_semantic_status_name", "")
                    if semantic_name in semantic:
                        child.configure(fg=semantic[semantic_name])
                except tk.TclError:
                    pass
            self.retheme_plain_widgets(child, previous_colors)

    def select_tab(self, name):
        # Every navigable screen is a notebook page, so the page registry is the
        # single source of truth. A hand-maintained lookup here only created a
        # second place to forget a new screen.
        page = self.tab_pages.get(name)
        if page is None:
            return
        if name != "scouting" and hasattr(self, "cancel_scouting_target_refresh"):
            self.cancel_scouting_target_refresh()
        if name != "fighter_search" and hasattr(self, "cancel_world_fighter_search"):
            self.cancel_world_fighter_search()
        if name != "editor" and hasattr(self, "cancel_database_editor_refresh"):
            self.cancel_database_editor_refresh()
        self.ensure_screen_built(name)
        self.current_tab_name = name
        self.tabs.select(page)
        if hasattr(self, "refresh_current_screen"):
            self.refresh_current_screen(name)
        # Highlight the active screen in the sidebar so the player always knows where they are.
        for tab_name, button in getattr(self, "nav_buttons", {}).items():
            button.configure(style="NavActive.TButton" if tab_name == name else "Nav.TButton")

    def update_city_options(self):
        cities = REGION_CITIES.get(self.event_region.get(), ["Las Vegas"])
        if hasattr(self, "city_box"):
            self.city_box.configure(values=cities)
        if self.event_city.get() not in cities:
            self.event_city.set(cities[0])

    def screen_header(self, parent, title, subtitle):
        frame = ttk.Frame(parent, style="Header.TFrame")
        frame.pack(fill="x", pady=(0, 6))
        ttk.Label(frame, text=title, style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=5)
        subtitle_label = ttk.Label(frame, text=subtitle, style="ScreenTitle.TLabel")
        subtitle_label.configure(font=("Tahoma", 8))
        subtitle_label.pack(side="right", padx=10)

    def section(self, parent, title):
        frame = ttk.Frame(parent, style="Panel.TFrame")
        ttk.Label(frame, text=title, anchor="center", style="Section.TLabel").pack(fill="x", ipady=3)
        inner = ttk.Frame(frame, style="Inset.TFrame")
        inner.pack(fill="both", expand=True, padx=6, pady=6)
        return frame, inner

    def disclosure_section(self, parent, title, summary_var, expanded=True, on_toggle=None):
        """Build an explicit, summary-preserving collapsible section."""
        frame = ttk.Frame(parent, style="Panel.TFrame")
        header = ttk.Frame(frame, style="Discovery.TFrame")
        header.pack(fill="x")
        ttk.Label(header, text=title, anchor="w", style="Section.TLabel").pack(side="left", fill="x", expand=True, padx=(7, 4), ipady=3)
        ttk.Label(header, textvariable=summary_var, anchor="e", style="Discovery.TLabel").pack(side="left", padx=6)
        toggle = ttk.Button(header, width=17)
        toggle.pack(side="right", padx=4, pady=3)
        inner = ttk.Frame(frame, style="Inset.TFrame")
        frame._disclosure_inner = inner
        frame._disclosure_toggle = toggle
        frame._disclosure_expanded = None
        frame._disclosure_callback = on_toggle
        toggle.configure(command=lambda target=frame: self.toggle_disclosure_section(target))
        self.set_disclosure_section_expanded(frame, expanded, notify=False)
        return frame, inner

    def set_disclosure_section_expanded(self, frame, expanded, notify=True):
        """Show or hide disclosure content while its named header remains visible."""
        expanded = bool(expanded)
        inner = frame._disclosure_inner
        if expanded:
            if not inner.winfo_manager():
                inner.pack(fill="both", expand=True, padx=6, pady=6)
            frame._disclosure_toggle.configure(text="▲ Collapse")
        else:
            inner.pack_forget()
            frame._disclosure_toggle.configure(text="▼ Expand")
        frame._disclosure_expanded = expanded
        if notify and callable(frame._disclosure_callback):
            frame._disclosure_callback(expanded)

    def toggle_disclosure_section(self, frame):
        self.set_disclosure_section_expanded(frame, not bool(frame._disclosure_expanded))

    def apply_ui_disclosure_preferences(self):
        """Apply loaded-career disclosure preferences to built screens."""
        disclosure_specs = (
            ("owner_goals_panel", "ui_owner_goals_collapsed"),
            ("show_details_panel", "ui_show_details_collapsed"),
            ("matchup_insight_panel", "ui_matchup_insight_collapsed"),
        )
        for panel_name, rule_key in disclosure_specs:
            panel = getattr(self, panel_name, None)
            desired_expanded = not self.rules.get(rule_key, False)
            if panel and bool(panel._disclosure_expanded) != bool(desired_expanded):
                self.set_disclosure_section_expanded(panel, desired_expanded, notify=False)

    def create_vertical_resizer(self, parent, initial_fraction=0.7, min_top=180, min_bottom=80):
        """Create a themed vertical split that keeps its useful default on first layout."""
        pane = tk.PanedWindow(
            parent,
            orient="vertical",
            bg=self.colors["panel"],
            bd=0,
            sashwidth=8,
            sashpad=2,
            sashrelief="raised",
            opaqueresize=True,
        )
        pane._resize_ready = False
        pane._resize_user_adjusted = False
        pane._resize_last_height = 0
        pane._resize_fraction = initial_fraction
        pane._resize_min_top = min_top
        pane._resize_min_bottom = min_bottom
        pane.bind("<Configure>", lambda _event, target=pane: self.initialize_vertical_resizer(target), add="+")
        pane.bind("<ButtonRelease-1>", lambda event, target=pane: self.mark_vertical_resizer_adjusted(target, event), add="+")
        if not hasattr(self, "vertical_resize_panes"):
            self.vertical_resize_panes = []
        self.vertical_resize_panes.append(pane)
        return pane

    def initialize_vertical_resizer(self, pane):
        """Track the intended split through startup resizing until the player drags it."""
        if getattr(pane, "_resize_user_adjusted", False) or pane.winfo_height() < 260:
            return
        if not pane.winfo_ismapped():
            if not getattr(pane, "_resize_map_bound", False):
                pane._resize_map_bound = True
                pane.bind("<Map>", lambda _event, target=pane: target.after_idle(lambda: self.initialize_vertical_resizer(target)), add="+")
            return
        if len(pane.panes()) < 2:
            pane.after_idle(lambda: self.initialize_vertical_resizer(pane))
            return
        height = pane.winfo_height()
        if getattr(pane, "_resize_ready", False) and height == getattr(pane, "_resize_last_height", 0):
            return
        min_top = getattr(pane, "_resize_min_top", 180)
        min_bottom = getattr(pane, "_resize_min_bottom", 80)
        fraction = getattr(pane, "_resize_fraction", 0.7)
        top_height = max(min_top, min(height - min_bottom, round(height * fraction)))
        try:
            pane._resize_last_height = height
            pane.sash_place(0, 0, top_height)
            pane._resize_ready = True
        except tk.TclError:
            # Both child panes may not exist until Tk completes this layout pass.
            pane.after_idle(lambda: self.initialize_vertical_resizer(pane))

    def mark_vertical_resizer_adjusted(self, pane, event):
        """Stop automatic sash placement only after a release on the sash itself."""
        if len(pane.panes()) < 2:
            return
        try:
            _x, sash_y = pane.sash_coord(0)
        except tk.TclError:
            return
        if abs(int(event.y) - int(sash_y)) <= max(10, int(pane.cget("sashwidth")) + 4):
            pane._resize_user_adjusted = True

    def configure_inbox_panel_layout(self, width):
        """Keep Inbox and Owner Goals discoverable without widening the page."""
        pane = getattr(self, "inbox_section_split", None)
        messages = getattr(self, "inbox_messages_panel", None)
        goals = getattr(self, "owner_goals_panel", None)
        if not pane or not messages or not goals:
            return
        mode = "vertical" if int(width) < 900 else "horizontal"
        if getattr(self, "_inbox_layout_mode", None) == mode:
            return
        for child in pane.panes():
            pane.forget(child)
        pane.configure(orient=mode)
        if mode == "vertical":
            pane.add(messages, minsize=190, stretch="always")
            pane.add(goals, minsize=90, stretch="always")
        else:
            pane.add(messages, minsize=430, stretch="always")
            pane.add(goals, minsize=310, stretch="always")
        self._inbox_layout_mode = mode

    def refresh_booking_scroll_region(self):
        """Let the booking page's outer canvas grow to its natural content height.

        Nested PanedWindows otherwise report only their viewport allocation to
        the canvas on the first map.  The stacked matchup layout then receives
        a short body even though the page has more content below it.  Updating
        the embedded window height after its children settle keeps every
        control reachable through the existing page scrollbar.
        """
        page = getattr(self, "booking_tab", None)
        canvas = getattr(page, "master", None) if page else None
        if not page or not canvas or not isinstance(canvas, tk.Canvas):
            return
        try:
            items = [item for item in canvas.find_all() if canvas.itemcget(item, "window") == str(page)]
            if not items:
                return
            height = max(canvas.winfo_height(), page.winfo_reqheight())
            canvas.itemconfigure(items[0], height=height)
            canvas.configure(scrollregion=canvas.bbox("all"))
            resizer = getattr(self, "booking_resize", None)
            if resizer:
                # The content expansion changes the outer split's available
                # height after its initial auto-placement pass.
                resizer._resize_last_height = 0
                self.initialize_vertical_resizer(resizer)
        except tk.TclError:
            return

    def cancel_booking_layout_callbacks(self, widget=None, attribute=None):
        """Cancel delayed booking layout work before a pane/window is destroyed.

        Tk's ``after`` scripts are owned by the interpreter, not by the widget
        that scheduled them.  Destroying a Matchmaking pane therefore used to
        leave Python callbacks pointing at dead Tcl commands, producing
        ``invalid command name`` errors during the next test or page rebuild.
        """
        targets = [widget] if widget is not None else [
            getattr(self, "booking_horizontal_split", None),
            getattr(self, "booking_resize", None),
            getattr(self, "booking_tab", None),
        ]
        for target in targets:
            if target is None:
                continue
            attributes = (attribute,) if attribute else ("_booking_sash_after_id", "_booking_scroll_after_id")
            for callback_attribute in attributes:
                token = getattr(target, callback_attribute, None)
                if not token:
                    continue
                try:
                    # Cancel through the widget that registered the callback;
                    # Tkinter then removes the Tcl command from that widget's
                    # cleanup list as well as cancelling the timer.
                    target.after_cancel(token)
                except (tk.TclError, AttributeError):
                    pass
                try:
                    setattr(target, callback_attribute, None)
                except tk.TclError:
                    pass

    def schedule_booking_layout_callback(self, widget, delay, callback, attribute):
        """Schedule one cancellable booking callback for a widget."""
        self.cancel_booking_layout_callbacks(widget, attribute)
        try:
            def run():
                try:
                    setattr(widget, attribute, None)
                    if widget.winfo_exists():
                        callback()
                except tk.TclError:
                    # A close can race the timer between Tcl dispatch and the
                    # Python callback.  The layout is already being torn down.
                    return
            token = widget.after(max(1, int(delay)), run)
            setattr(widget, attribute, token)
        except tk.TclError:
            return None
        return token

    def configure_booking_panel_layout(self, width):
        """Move the fight card above fighters when side-by-side space is unsafe."""
        pane = getattr(self, "booking_horizontal_split", None)
        available = getattr(self, "booking_available_panel", None)
        card = getattr(self, "booking_card_panel", None)
        if not pane or not available or not card:
            return
        mode = "vertical" if int(width) < 1180 else "horizontal"
        if getattr(self, "_booking_layout_mode", None) == mode:
            if mode == "vertical":
                callback = getattr(pane, "_booking_place_vertical_sash", None)
                if callback:
                    self.schedule_booking_layout_callback(pane, 120, callback, "_booking_sash_after_id")
                if hasattr(self, "refresh_booking_scroll_region"):
                    self.schedule_booking_layout_callback(pane, 140, self.refresh_booking_scroll_region, "_booking_scroll_after_id")
            return
        self.cancel_booking_layout_callbacks(pane)
        for child in pane.panes():
            pane.forget(child)
        pane.configure(orient=mode)
        if mode == "vertical":
            resize = getattr(self, "booking_resize", None)
            if resize is not None:
                # The booking page is an outer scrollable canvas. Reserve a
                # taller stacked workspace so filters, actions and four
                # readable fighter rows remain visible together.
                try:
                    resize.configure(height=720)
                except tk.TclError:
                    pass
            # Card first: new players see where booked fights will land before
            # working through the dense fighter table below it.
            pane.add(card, minsize=150, stretch="always")
            pane.add(available, minsize=520, stretch="always")
            if hasattr(self, "card_tree"):
                self.card_tree.configure(height=5)
            # The card pane already exposes the same add/remove/reorder
            # actions in its footer. Hide the duplicate left-hand action row
            # while stacked so the fighter table receives useful reading
            # height instead of being squeezed below redundant buttons.
            actions = getattr(self, "booking_actions", None)
            if actions and actions.winfo_manager():
                actions.pack_forget()
            # Tk's PanedWindow distributes a newly stacked pair almost evenly
            # and may ignore the child minsizes during the first map.  Reserve
            # the card's compact summary/header, then give the fighter pane the
            # remainder so its filters and at least four rows remain usable.
            def place_vertical_sash(target=pane):
                try:
                    height = target.winfo_height()
                    if height > 0:
                        # Keep the draft card compact in stacked mode so the
                        # fighter explorer retains at least four readable
                        # rows at the 1280x760 laptop viewport.  The card
                        # table still scrolls independently when it contains
                        # more bouts; squeezing the explorer to a 45px strip
                        # makes the primary selection task effectively
                        # unusable.
                        card_height = min(190, max(170, height - 530))
                        target.sash_place(0, 0, card_height)
                except tk.TclError:
                    pass
            pane._booking_place_vertical_sash = place_vertical_sash
            # Wait for the outer page's first geometry pass; its resizer may
            # otherwise overwrite this placement immediately after idle work.
            self.schedule_booking_layout_callback(pane, 180, place_vertical_sash, "_booking_sash_after_id")
        else:
            resize = getattr(self, "booking_resize", None)
            if resize is not None:
                try:
                    resize.configure(height=620)
                except tk.TclError:
                    pass
            pane.add(available, minsize=520, stretch="always")
            pane.add(card, minsize=430, stretch="always")
            if hasattr(self, "card_tree"):
                self.card_tree.configure(height=8)
            actions = getattr(self, "booking_actions", None)
            options = getattr(self, "booking_options", None)
            if actions and not actions.winfo_manager():
                actions.pack(fill="x", pady=(0, 5), before=options if options else None)
        self._booking_layout_mode = mode

    def configure_show_details_layout(self, width):
        """Compact Show Details into two rows when space permits, stacking safely when it does not."""
        controls = getattr(self, "show_details_controls", None)
        event_fields = getattr(self, "show_details_event_fields", None)
        location_fields = getattr(self, "show_details_location_fields", None)
        date_fields = getattr(self, "show_details_date_fields", None)
        economics_fields = getattr(self, "show_details_economics_fields", None)
        primary_actions = getattr(self, "show_details_primary_actions", None)
        secondary_actions = getattr(self, "show_details_secondary_actions", None)
        status_grid = getattr(self, "show_details_status_grid", None)
        schedule_status = getattr(self, "schedule_status", None)
        broadcaster_status = getattr(self, "event_broadcaster_status", None)
        required = (controls, event_fields, location_fields, date_fields, economics_fields, primary_actions, secondary_actions, status_grid, schedule_status, broadcaster_status)
        if not all(required):
            return
        width = int(width)
        mode = "wide" if width >= 1500 else ("medium" if width >= 1150 else "narrow")
        if getattr(self, "_show_details_layout_mode", None) == mode:
            return
        for group in (event_fields, location_fields, date_fields, economics_fields, primary_actions, secondary_actions):
            group.grid_forget()
        schedule_status.grid_forget()
        broadcaster_status.grid_forget()
        for column in range(3):
            controls.columnconfigure(column, weight=0)
            status_grid.columnconfigure(column, weight=0)
        if mode == "wide":
            event_fields.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=1)
            location_fields.grid(row=0, column=1, sticky="w", padx=(0, 8), pady=1)
            secondary_actions.grid(row=0, column=2, sticky="e", pady=1)
            date_fields.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=1)
            economics_fields.grid(row=1, column=1, sticky="w", padx=(0, 8), pady=1)
            primary_actions.grid(row=1, column=2, sticky="e", pady=1)
            controls.columnconfigure(2, weight=1)
        elif mode == "medium":
            event_fields.grid(row=0, column=0, sticky="w", padx=(0, 8), pady=1)
            location_fields.grid(row=0, column=1, columnspan=2, sticky="w", pady=1)
            date_fields.grid(row=1, column=0, sticky="w", padx=(0, 8), pady=1)
            economics_fields.grid(row=1, column=1, sticky="w", pady=1)
            primary_actions.grid(row=1, column=2, sticky="e", pady=1)
            secondary_actions.grid(row=2, column=0, columnspan=3, sticky="e", pady=1)
            controls.columnconfigure(2, weight=1)
        else:
            event_fields.grid(row=0, column=0, sticky="w", pady=1)
            location_fields.grid(row=1, column=0, sticky="w", pady=1)
            date_fields.grid(row=2, column=0, sticky="w", pady=1)
            primary_actions.grid(row=3, column=0, sticky="w", pady=1)
            secondary_actions.grid(row=4, column=0, sticky="w", pady=1)
            economics_fields.grid(row=5, column=0, sticky="w", pady=1)
            controls.columnconfigure(0, weight=1)
        if mode == "narrow":
            schedule_status.grid(row=0, column=0, sticky="ew", pady=(2, 0))
            broadcaster_status.grid(row=1, column=0, sticky="ew", pady=(1, 0))
            status_grid.columnconfigure(0, weight=1)
        else:
            schedule_status.grid(row=0, column=0, sticky="ew", padx=(0, 6), pady=(2, 0))
            broadcaster_status.grid(row=0, column=1, sticky="ew", pady=(2, 0))
            status_grid.columnconfigure(0, weight=1)
            status_grid.columnconfigure(1, weight=3)
        self._show_details_layout_mode = mode

    def configure_booking_action_layout(self, width):
        """Use one action row when the fighter pane is wide and a 3+2 grid when it is not."""
        frame = getattr(self, "booking_actions", None)
        buttons = getattr(self, "booking_action_buttons", ())
        if frame is None or len(buttons) != 5:
            return
        mode = "wide" if int(width) >= 700 else "narrow"
        if getattr(self, "_booking_action_layout_mode", None) == mode:
            return
        for button in buttons:
            button.grid_forget()
        for column in range(5):
            frame.columnconfigure(column, weight=0)
        if mode == "wide":
            for column, button in enumerate(buttons):
                button.grid(row=0, column=column, sticky="ew", padx=3, pady=2)
                frame.columnconfigure(column, weight=1)
        else:
            for column, button in enumerate(buttons[:3]):
                button.grid(row=0, column=column, sticky="ew", padx=3, pady=2)
                frame.columnconfigure(column, weight=1)
            buttons[3].grid(row=1, column=0, sticky="ew", padx=3, pady=2)
            buttons[4].grid(row=1, column=1, columnspan=2, sticky="ew", padx=3, pady=2)
        self._booking_action_layout_mode = mode

    def select_matchmaking_fighter_click(self, event):
        """Toggle Matchmaking rows without requiring keyboard modifiers.

        Ctrl/Shift keep their native extended-selection behavior, but ordinary
        clicks can build or trim matchup and tournament selections on their own.
        """
        tree = getattr(self, "available_tree", None)
        if tree is None or int(getattr(event, "state", 0) or 0) & 0x0005:
            return None
        if tree.identify_region(event.x, event.y) != "cell":
            return None
        row_id = tree.identify_row(event.y)
        if not row_id:
            return None
        if row_id in tree.selection():
            tree.selection_remove(row_id)
        else:
            tree.selection_add(row_id)
        tree.focus(row_id)
        return "break"

    def open_matchmaking_fighter_profile_click(self, event):
        """Open the double-clicked row even when several other rows are selected."""
        tree = getattr(self, "available_tree", None)
        if tree is None or tree.identify_region(event.x, event.y) != "cell":
            return None
        row_id = tree.identify_row(event.y)
        fighter = getattr(self, "available_tree_fighters", {}).get(row_id)
        if fighter is not None:
            # A double-click may follow one or two toggle callbacks depending on
            # the Tk platform. Leave the opened fighter selected either way.
            tree.selection_add(row_id)
            tree.focus(row_id)
            self.open_fighter_profile_window(fighter)
        return "break"

    def matchmaking_table_view_columns(self, view_name):
        """Return a focused display-column preset without dropping table data."""
        presets = {
            "Essentials": (
                "name", "weight", "rank", "record", "overall", "elo", "pop",
                "build", "fit", "history", "status",
            ),
            "Readiness": (
                "name", "gender", "weight", "last", "activity", "fatigue",
                "recovery", "fit", "status",
            ),
            "Form & Fitness": (
                "name", "weight", "record", "age", "overall", "elo", "pop",
                "build", "last", "form", "trend", "activity", "fatigue", "fit",
            ),
            "All 20": (
                "name", "gender", "weight", "rank", "titlepath", "record",
                "age", "overall", "elo", "pop", "build", "last", "form",
                "trend", "activity", "fatigue", "recovery", "fit", "history",
                "status",
            ),
        }
        return presets.get(str(view_name), presets["Essentials"])

    def apply_matchmaking_table_view(self, _event=None):
        """Switch the visible fighter metrics while preserving rows and selection."""
        tree = getattr(self, "available_tree", None)
        view_var = getattr(self, "available_table_view", None)
        if tree is None or view_var is None:
            return
        tree.configure(displaycolumns=self.matchmaking_table_view_columns(view_var.get()))
        tree.xview_moveto(0)

    def sync_matchmaking_alert_visibility(self, *_args):
        """Keep actionable booking alerts visible without reserving empty bands."""
        for widget_name, variable_name in (
            ("matchmaking_notice", "matchmaking_notice_var"),
            ("matchmaking_title_warning", "matchmaking_title_warning_var"),
        ):
            widget = getattr(self, widget_name, None)
            variable = getattr(self, variable_name, None)
            if widget is None or variable is None:
                continue
            if str(variable.get()).strip():
                if not widget.winfo_manager():
                    before = getattr(self, "matchup_insight_panel", None)
                    if widget_name == "matchmaking_notice":
                        warning = getattr(self, "matchmaking_title_warning", None)
                        if warning is not None and warning.winfo_manager():
                            before = warning
                    pack_options = {"fill": "x", "pady": (0, 4), "padx": 3}
                    if before is not None and before.winfo_manager():
                        pack_options["before"] = before
                    widget.pack(**pack_options)
            else:
                widget.pack_forget()

    def _show_tooltip(self, holder, text, x, y):
        """Render a small themed hover tooltip at screen coordinates (x, y)."""
        self._hide_tooltip(holder)
        popup = tk.Toplevel(self.root)
        popup.overrideredirect(True)
        popup.attributes("-topmost", True)
        popup.configure(bg=self.colors.get("gold", "#c9a13a"))
        tk.Label(
            popup, text=text, bg=self.colors.get("panel_dark", "#252525"),
            fg=self.colors.get("text", "#f0f0f0"), font=("Tahoma", 8), justify="left",
            wraplength=320, padx=8, pady=6,
        ).pack(padx=1, pady=1)
        popup.geometry(f"+{int(x)}+{int(y)}")
        holder["window"] = popup

    def _hide_tooltip(self, holder):
        popup = holder.get("window")
        holder["window"] = None
        if popup is not None:
            try:
                if popup.winfo_exists():
                    popup.destroy()
            except tk.TclError:
                pass

    def attach_tooltip(self, widget, text):
        """Attach reusable hover help to any widget."""
        holder = {"window": None}
        def show(_event=None):
            if holder.get("window") or not widget.winfo_exists():
                return
            x = widget.winfo_rootx() + 14
            y = widget.winfo_rooty() + widget.winfo_height() + 4
            self._show_tooltip(holder, text, x, y)
        def hide(_event=None):
            self._hide_tooltip(holder)
        widget.bind("<Enter>", show, add="+")
        widget.bind("<Leave>", hide, add="+")
        widget.bind("<ButtonPress>", hide, add="+")

    def attach_tree_heading_tooltips(self, tree, tips):
        """Show per-column help when the pointer hovers over a tree's header row.

        `tips` maps column ids (as declared in the tree's `columns`) to help text.
        Makes dense matchmaking tables self-explanatory without cluttering the UI.
        """
        holder = {"window": None, "column": None}
        columns = list(tree["columns"])
        def hide(_event=None):
            holder["column"] = None
            self._hide_tooltip(holder)
        def on_motion(event):
            if tree.identify_region(event.x, event.y) != "heading":
                hide()
                return
            column_ref = tree.identify_column(event.x)  # e.g. "#3"
            try:
                index = int(column_ref.replace("#", "")) - 1
            except ValueError:
                hide()
                return
            if not (0 <= index < len(columns)):
                hide()
                return
            column = columns[index]
            if column == holder.get("column"):
                return
            hide()
            text = tips.get(column)
            if text:
                holder["column"] = column
                self._show_tooltip(holder, text, tree.winfo_rootx() + event.x + 12, tree.winfo_rooty() + event.y + 18)
        tree.bind("<Motion>", on_motion, add="+")
        tree.bind("<Leave>", hide, add="+")

    def make_tree_sortable(self, tree):
        tree._sort_reverse = {}
        for col in tree["columns"]:
            label = tree.heading(col, "text")
            tree.heading(col, text=label, command=lambda c=col: self.sort_treeview(tree, c))

    def _sort_unregistered_treeview_heading(self, event):
        """Give secondary and popup tables the same sortable headings as tabs.

        The main dashboard calls ``make_tree_sortable`` explicitly. A number of
        detail windows are built later and historically missed that call, so a
        class binding supplies a safe fallback for any Treeview heading that
        has not already registered its own sorter.
        """
        tree = event.widget
        if tree.identify_region(event.x, event.y) != "heading" or hasattr(tree, "_sort_reverse"):
            return
        column_ref = tree.identify_column(event.x)
        try:
            column_index = int(column_ref.lstrip("#")) - 1
        except (TypeError, ValueError):
            return
        columns = list(tree["columns"])
        if not (0 <= column_index < len(columns)):
            return
        self.make_tree_sortable(tree)
        self.sort_treeview(tree, columns[column_index])
        return "break"

    @staticmethod
    def _parse_duration_months(text):
        """Turn a contract 'Time Left' label ('10 mo', '1y', '3y 10mo') into total months."""
        compact = text.lower().replace(" ", "")
        if not compact:
            return None
        index = 0
        total = 0
        found = False
        while index < len(compact):
            start = index
            while index < len(compact) and compact[index].isdigit():
                index += 1
            if index == start:
                return None  # expected a number before a unit
            number = int(compact[start:index])
            if compact[index:index + 2] == "mo":
                total += number
                index += 2
            elif compact[index:index + 1] == "y":
                total += number * 12
                index += 1
            else:
                return None  # unrecognised unit -> not a duration label
            found = True
        return total if found else None

    @staticmethod
    def _parse_calendar_ordinal(text):
        """Turn an expiry label ('May W1 2027') into a chronological sort key."""
        parts = text.split()
        if len(parts) != 3:
            return None
        month_abbr, week_token, year_token = parts
        if month_abbr not in CALENDAR_MONTH_ABBREVIATIONS:
            return None
        if not (week_token[:1] in ("W", "w") and week_token[1:].isdigit()):
            return None
        if not year_token.isdigit():
            return None
        month_index = CALENDAR_MONTH_ABBREVIATIONS.index(month_abbr)
        week = int(week_token[1:])
        year = int(year_token)
        return year * 48 + month_index * 4 + week

    def sort_treeview(self, tree, col):
        reverse = tree._sort_reverse.get(col, False)

        def convert(value):
            text = str(value).strip()
            if text == "C":
                return (0, -1.0)
            # Expired contracts sort ahead of any remaining term / future date.
            if text.lower() == "expired":
                return (0, -1e12)
            duration = self._parse_duration_months(text)
            if duration is not None:
                return (0, float(duration))
            calendar = self._parse_calendar_ordinal(text)
            if calendar is not None:
                return (0, float(calendar))
            cleaned = text.replace("$", "").replace(",", "").replace("%", "").replace("#", "")
            if cleaned.startswith("-") and cleaned[1:].replace(".", "", 1).isdigit():
                return (0, float(cleaned))
            if cleaned.replace(".", "", 1).isdigit():
                return (0, float(cleaned))
            record_parts = text.split("-")
            if len(record_parts) >= 2 and all(part.isdigit() for part in record_parts[:2]):
                wins, losses = int(record_parts[0]), int(record_parts[1])
                return (0, float(wins * 1000 - losses))
            # Always return a tagged tuple.  A tree column can legitimately
            # contain a numeric rank, a champion marker, and a blank/text
            # status; Python cannot sort bare floats and strings together.
            return (1, text.lower())

        rows = [(convert(tree.set(item, col)), item) for item in tree.get_children("")]
        rows.sort(key=lambda row: row[0], reverse=reverse)
        for index, (_value, item) in enumerate(rows):
            tree.move(item, "", index)
        tree._sort_reverse[col] = not reverse

    def build_game_menu_tab(self):
        self.screen_header(self.game_menu_tab, "GAME MENU", "Save game, load game, start new game, export database, and load database")
        body = ttk.Frame(self.game_menu_tab)
        body.pack(fill="both", expand=True)
        save_panel, save_inner = self.section(body, "CAREER LIBRARY")
        save_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        active_card = tk.Frame(save_inner, bg=self.colors["red"], bd=0, highlightthickness=0)
        active_card.pack(fill="x", pady=(0, 6))
        self.save_active_title = tk.StringVar(value="ACTIVE CAREER")
        self.save_active_detail = tk.StringVar(value="Loading career details...")
        tk.Label(active_card, textvariable=self.save_active_title, bg=self.colors["red"], fg="#ffffff",
                 font=("Impact", 13), anchor="w", padx=10, pady=4).pack(fill="x")
        tk.Label(active_card, textvariable=self.save_active_detail, bg=self.colors["red"], fg="#ffe9e9",
                 font=("Tahoma", 8), anchor="w", padx=10, pady=3).pack(fill="x")

        library_heading = ttk.Frame(save_inner, style="Inset.TFrame")
        library_heading.pack(fill="x", pady=(0, 4))
        ttk.Label(library_heading, text="SAVE SLOTS", style="Inset.TLabel", font=("Tahoma", 9, "bold")).pack(side="left", padx=3)
        self.save_library_status = tk.StringVar(value="Scanning saves...")
        ttk.Label(library_heading, textvariable=self.save_library_status, style="Inset.TLabel").pack(side="right", padx=3)

        folder_row = ttk.Frame(save_inner, style="Inset.TFrame")
        folder_row.pack(fill="x", pady=(0, 5))
        self.save_folder_filter = tk.StringVar(value="All Saves")
        self.save_folder_target = tk.StringVar(value=getattr(self, "active_save_group", "Main"))
        self.save_new_folder_name = tk.StringVar(value="Tests")
        ttk.Label(folder_row, text="View", style="Inset.TLabel").grid(row=0, column=0, sticky="w", padx=3)
        self.save_folder_filter_box = ttk.Combobox(folder_row, textvariable=self.save_folder_filter, values=("All Saves", "Main"), state="readonly", width=15)
        self.save_folder_filter_box.grid(row=0, column=1, sticky="ew", padx=3)
        self.save_folder_filter_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_game_menu())
        ttk.Label(folder_row, text="Save / move to", style="Inset.TLabel").grid(row=0, column=2, sticky="w", padx=(8, 3))
        self.save_folder_target_box = ttk.Combobox(folder_row, textvariable=self.save_folder_target, values=("Main",), state="readonly", width=15)
        self.save_folder_target_box.grid(row=0, column=3, sticky="ew", padx=3)
        ttk.Entry(folder_row, textvariable=self.save_new_folder_name, width=15).grid(row=1, column=0, columnspan=2, sticky="ew", padx=3, pady=(4, 0))
        ttk.Button(folder_row, text="New Folder", command=self.create_save_folder).grid(row=1, column=2, sticky="ew", padx=3, pady=(4, 0))
        self.save_move_button = ttk.Button(folder_row, text="Move Selected", command=self.move_selected_save_to_folder, state="disabled")
        self.save_move_button.grid(row=1, column=3, sticky="ew", padx=3, pady=(4, 0))
        for column in (1, 3):
            folder_row.columnconfigure(column, weight=1)
        save_browser = tk.Frame(save_inner, bg=self.colors["tree"], bd=0, highlightthickness=1,
                                highlightbackground=self.colors["tree_head"])
        save_browser.pack(fill="both", expand=True)
        save_scroll = ttk.Scrollbar(save_browser, orient="vertical")
        self.save_slot_list = tk.Listbox(
            save_browser, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"],
            selectbackground=self.colors["red"], selectforeground="#ffffff", activestyle="none",
            exportselection=False, relief="flat", highlightthickness=0, yscrollcommand=save_scroll.set,
        )
        save_scroll.configure(command=self.save_slot_list.yview)
        save_scroll.pack(side="right", fill="y")
        self.save_slot_list.pack(side="left", fill="both", expand=True)
        self.save_slot_list.bind("<<ListboxSelect>>", self.refresh_save_selection_summary)
        self.save_library_empty_hint = tk.StringVar(value="")
        ttk.Label(save_inner, textvariable=self.save_library_empty_hint, style="Inset.TLabel",
                  anchor="w", justify="left", wraplength=520).pack(fill="x", padx=5, pady=(3, 0))

        selection_card = ttk.Frame(save_inner, style="Inset.TFrame")
        selection_card.pack(fill="x", pady=(6, 2))
        self.save_selection_title = tk.StringVar(value="No save selected")
        self.save_selection_detail = tk.StringVar(value="Choose a career above to load, copy, move, back up, or delete it.")
        ttk.Label(selection_card, textvariable=self.save_selection_title, style="Inset.TLabel",
                  font=("Tahoma", 9, "bold"), anchor="w").pack(fill="x", padx=5, pady=(4, 1))
        ttk.Label(selection_card, textvariable=self.save_selection_detail, style="Inset.TLabel",
                  anchor="w", justify="left", wraplength=520).pack(fill="x", padx=5, pady=(0, 4))

        row = ttk.Frame(save_inner, style="Inset.TFrame")
        row.pack(fill="x", pady=(4, 3))
        # This is a deliberate destination field, never a reflection of the
        # active career. Keeping it blank prevents accidental overwrites.
        self.save_slot_name = tk.StringVar()
        ttk.Label(row, text="New save name", style="Inset.TLabel").grid(row=0, column=0, sticky="w", padx=4, pady=(2, 0))
        ttk.Label(row, text="Blank protects existing slots", style="Inset.TLabel").grid(row=0, column=1, columnspan=3, sticky="e", padx=4, pady=(2, 0))
        ttk.Entry(row, textvariable=self.save_slot_name, width=18).grid(row=1, column=0, columnspan=4, sticky="ew", padx=4, pady=3)
        ttk.Button(row, text="Save New / Overwrite", style="Accent.TButton", command=self.save_selected_slot).grid(row=2, column=0, columnspan=2, sticky="ew", padx=3, pady=2)
        self.save_load_button = ttk.Button(row, text="Load Selected", style="Accent.TButton", command=self.load_selected_slot, state="disabled")
        self.save_load_button.grid(row=2, column=2, columnspan=2, sticky="ew", padx=3, pady=2)
        self.save_copy_button = ttk.Button(row, text="Copy", command=self.duplicate_selected_save, state="disabled")
        self.save_copy_button.grid(row=3, column=0, sticky="ew", padx=3, pady=2)
        self.save_delete_button = ttk.Button(row, text="Delete", command=self.delete_selected_slot, state="disabled")
        self.save_delete_button.grid(row=3, column=1, sticky="ew", padx=3, pady=2)
        self.save_backup_button = ttk.Button(row, text="Back Up", command=self.backup_selected_slot, state="disabled")
        self.save_backup_button.grid(row=3, column=2, sticky="ew", padx=3, pady=2)
        ttk.Button(row, text="Restore...", command=self.open_save_backup_manager).grid(row=3, column=3, sticky="ew", padx=3, pady=2)
        self.save_migrate_archetypes_button = ttk.Button(
            row, text="Migrate Profiles", command=self.migrate_selected_save_archetypes, state="disabled",
        )
        self.save_migrate_archetypes_button.grid(row=4, column=0, columnspan=4, sticky="ew", padx=3, pady=2)
        for col in range(4):
            row.columnconfigure(col, weight=1)
        save_tools = ttk.Frame(save_inner, style="Inset.TFrame")
        save_tools.pack(fill="x", pady=(0, 6))
        ttk.Button(save_tools, text="Open Save Folder", command=self.open_saves_folder).grid(row=0, column=0, sticky="ew", padx=3, pady=2)
        ttk.Button(save_tools, text="Game Settings", command=self.open_game_settings_window).grid(row=0, column=1, sticky="ew", padx=3, pady=2)
        ttk.Button(save_tools, text="Pin Active State", command=self.pin_current_checkpoint).grid(row=1, column=0, sticky="ew", padx=3, pady=2)
        ttk.Button(save_tools, text="Checkpoints...", command=self.open_pinned_checkpoint_manager).grid(row=1, column=1, sticky="ew", padx=3, pady=2)
        for col in range(2):
            save_tools.columnconfigure(col, weight=1)
        autosave_row = ttk.Frame(save_inner, style="Inset.TFrame")
        autosave_row.pack(fill="x", pady=(0, 6))
        self.autosave_status_label = ttk.Label(autosave_row, text="Autosaves loading...", style="Inset.TLabel")
        self.autosave_status_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
        for col, (text, command) in enumerate((
            ("Toggle Autosaves", self.toggle_autosaves),
        )):
            ttk.Button(autosave_row, text=text, command=command).grid(row=1, column=col, sticky="ew", padx=2, pady=2)
            autosave_row.columnconfigure(col, weight=1)
        self.save_manager_status = ttk.Label(save_inner, text="", style="Inset.TLabel", anchor="w")
        self.save_manager_status.pack(fill="x", padx=4, pady=(0, 4))
        db_panel, db_inner = self.section(body, "DATABASE / WORLD")
        db_panel.pack(side="left", fill="both", expand=True)
        self.database_list = tk.Listbox(db_inner, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"])
        self.database_list.pack(fill="both", expand=True)
        dbrow = ttk.Frame(db_inner, style="Inset.TFrame")
        dbrow.pack(fill="x", pady=(6, 2))
        self.database_name = tk.StringVar(value="Default Database")
        ttk.Entry(dbrow, textvariable=self.database_name, width=20).pack(side="left", fill="x", expand=True, padx=4)
        db_actions = ttk.Frame(db_inner, style="Inset.TFrame")
        db_actions.pack(fill="x", pady=(0, 4))
        self.spectator_sim_buttons = []
        for col, (text, command, style) in enumerate((
            ("Export", self.export_database, None),
            ("Import Quick", self.import_quick_save_as_database, None),
            ("Career → DB", self.convert_career_to_database, "Accent.TButton"),
            ("Load DB", self.load_selected_database, None),
            ("Refresh", self.refresh_game_menu, None),
        )):
            button = ttk.Button(db_actions, text=text, command=command, style=style) if style else ttk.Button(db_actions, text=text, command=command)
            button.grid(row=col // 2, column=col % 2, sticky="ew", padx=3, pady=2)
        db_actions.columnconfigure(0, weight=1)
        db_actions.columnconfigure(1, weight=1)
        universe_row = ttk.Frame(db_inner, style="Inset.TFrame")
        universe_row.pack(fill="x", pady=(0, 6))
        for col, (text, command, style) in enumerate((
            ("Use Selected Universe", self.use_selected_universe_database, "Accent.TButton"),
            ("Clone Universe", self.clone_selected_universe_database, None),
            ("Validate Default", self.reset_default_universe_database, None),
            ("Open Folder", self.open_database_folder, None),
        )):
            button = ttk.Button(universe_row, text=text, command=command, style=style) if style else ttk.Button(universe_row, text=text, command=command)
            button.grid(row=col // 2, column=col % 2, sticky="ew", padx=3, pady=2)
        universe_row.columnconfigure(0, weight=1)
        universe_row.columnconfigure(1, weight=1)
        start_panel, start_inner = self.section(db_inner, "STARTING PROMOTION")
        start_panel.pack(fill="x", pady=(8, 0))
        self.start_company_choice = tk.StringVar(value=PLAYER_PROMOTION_NAME)
        start_choice_row = ttk.Frame(start_inner, style="Inset.TFrame")
        start_choice_row.pack(fill="x", padx=4, pady=(4, 2))
        self.start_company_combo = ttk.Combobox(start_choice_row, textvariable=self.start_company_choice, state="readonly", width=28)
        self.start_company_combo.pack(side="left", fill="x", expand=True, padx=(0, 4))
        start_button_row = ttk.Frame(start_inner, style="Inset.TFrame")
        start_button_row.pack(fill="x", padx=4, pady=(2, 4))
        ttk.Button(start_button_row, text="Start New Game With Selected Promotion", style="Accent.TButton", command=self.new_game).pack(side="left", fill="x", expand=True)
        ttk.Label(start_inner, text="Spectator Mode starts a fresh observer save with no player company.", style="Inset.TLabel", wraplength=260).pack(fill="x", padx=6, pady=(0, 4))

        self.spectator_sim_panel, spectator = self.section(db_inner, "SPECTATOR WORLD SIMULATION")
        self.spectator_sim_panel.pack(fill="x", pady=(8, 0))
        self.spectator_sim_status = ttk.Label(spectator, text="Observer controls are available in Spectator Mode.", style="Inset.TLabel", wraplength=260)
        self.spectator_sim_status.pack(fill="x", padx=6, pady=(4, 2))
        policy_panel, policy_inner = self.section(spectator, "SAFE STOP POLICY")
        policy_panel.pack(fill="x", padx=4, pady=(2, 4))
        current_policy = getattr(self, "rules", {}).get("simulation_pause_policy", {})
        self.spectator_pause_on_event_var = tk.BooleanVar(value=bool(current_policy.get("stop_on_event", False)) if isinstance(current_policy, dict) else False)
        ttk.Checkbutton(
            policy_inner,
            text="Pause after the next hosted world event",
            variable=self.spectator_pause_on_event_var,
        ).pack(fill="x", padx=5, pady=(3, 1))
        self.spectator_policy_status = ttk.Label(policy_inner, text="No saved stop policy.", style="Inset.TLabel", wraplength=260)
        self.spectator_policy_status.pack(fill="x", padx=5, pady=(1, 3))
        policy_actions = ttk.Frame(policy_inner, style="Inset.TFrame")
        policy_actions.pack(fill="x", padx=3, pady=(0, 3))
        for col, (text, command) in enumerate((
            ("Apply Policy", self.apply_spectator_pause_policy),
            ("Resume", self.resume_spectator_simulation),
            ("Clear", self.clear_spectator_pause_policy),
        )):
            button = ttk.Button(policy_actions, text=text, command=command)
            button.grid(row=0, column=col, sticky="ew", padx=2, pady=2)
            self.spectator_sim_buttons.append(button)
            policy_actions.columnconfigure(col, weight=1)
        spectator_actions = ttk.Frame(spectator, style="Inset.TFrame")
        spectator_actions.pack(fill="x", padx=4, pady=4)
        for col, (text, command, style) in enumerate((
            ("Sim Week", lambda: self.spectator_advance_weeks(1), None),
            ("Sim Month", self.spectator_sim_month, None),
            ("Sim Year", self.spectator_sim_year, None),
            ("Watch Next Event", self.spectator_watch_next_event, "Accent.TButton"),
            ("Watch Latest", self.watch_latest_world_event, None),
        )):
            button = ttk.Button(spectator_actions, text=text, command=command, style=style) if style else ttk.Button(spectator_actions, text=text, command=command)
            button.grid(row=col // 2, column=col % 2, sticky="ew", padx=3, pady=2)
            self.spectator_sim_buttons.append(button)
        spectator_actions.columnconfigure(0, weight=1)
        spectator_actions.columnconfigure(1, weight=1)
        date_row = ttk.Frame(spectator, style="Inset.TFrame")
        date_row.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Label(date_row, text="Sim to calendar date", style="Inset.TLabel").grid(row=0, column=0, columnspan=4, sticky="w", padx=4, pady=(2, 0))
        self.spectator_target_year = tk.IntVar(value=GAME_START_YEAR)
        self.spectator_target_calendar_month = tk.StringVar(value=CALENDAR_MONTHS[0])
        self.spectator_target_week = tk.IntVar(value=4)
        ttk.Label(date_row, text="Year", style="Inset.TLabel").grid(row=1, column=0, sticky="w", padx=(4, 2), pady=2)
        ttk.Spinbox(date_row, from_=GAME_START_YEAR, to=GAME_START_YEAR + 240, textvariable=self.spectator_target_year, width=6).grid(row=1, column=1, sticky="ew", padx=(0, 4), pady=2)
        ttk.Label(date_row, text="Month", style="Inset.TLabel").grid(row=2, column=0, sticky="w", padx=(4, 2), pady=2)
        ttk.Combobox(date_row, textvariable=self.spectator_target_calendar_month, values=CALENDAR_MONTHS, state="readonly", width=12).grid(row=2, column=1, sticky="ew", padx=(0, 4), pady=2)
        ttk.Label(date_row, text="Week", style="Inset.TLabel").grid(row=2, column=2, sticky="w", padx=(4, 2), pady=2)
        ttk.Spinbox(date_row, from_=1, to=4, textvariable=self.spectator_target_week, width=4).grid(row=2, column=3, sticky="ew", padx=(0, 4), pady=2)
        sim_to_date_button = ttk.Button(date_row, text="Sim To Date", command=self.spectator_sim_to_date)
        sim_to_date_button.grid(row=3, column=0, columnspan=4, sticky="ew", padx=4, pady=(2, 4))
        self.spectator_sim_buttons.append(sim_to_date_button)
        date_row.columnconfigure(1, weight=1)
        date_row.columnconfigure(3, weight=1)

    def set_advance_ui_progress(self, status, progress):
        """Update the persistent simulation status without forcing nested events."""
        if hasattr(self, "advance_status"):
            self.advance_status.config(text=str(status))
        if hasattr(self, "advance_progress"):
            self.advance_progress["value"] = max(0, min(100, float(progress)))
        if hasattr(self, "stat_month"):
            self.stat_month.config(text=self.format_game_date())
        if hasattr(self, "spectator_sim_status") and getattr(self, "spectator_mode", False):
            self.spectator_sim_status.config(text=f"{status} | {self.format_game_date()}")

    def set_advance_ui_busy(self, busy, status="", progress=0):
        """Show activity, prevent re-entry, and keep the native window responsive."""
        if not hasattr(self, "advance_activity"):
            return
        state = "disabled" if busy else "normal"
        if hasattr(self, "advance_button"):
            self.advance_button.config(state=state)
        for button in getattr(self, "spectator_sim_buttons", []):
            try:
                button.config(state=state)
            except tk.TclError:
                pass
        if busy:
            if not self.advance_status.winfo_manager():
                self.advance_status.pack(side="left", padx=(0, 5))
            if not self.advance_progress.winfo_manager():
                self.advance_progress.pack(side="left", padx=(0, 2))
            self.root.configure(cursor="watch")
            try:
                self.root.tk.call("tk", "busy", "hold", self.root)
                self._advance_busy_held = True
            except tk.TclError:
                self._advance_busy_held = False
            self.set_advance_ui_progress(status, progress)
        else:
            if getattr(self, "_advance_busy_held", False):
                try:
                    self.root.tk.call("tk", "busy", "forget", self.root)
                except tk.TclError:
                    pass
            self._advance_busy_held = False
            self.root.configure(cursor="")
            self.advance_progress.pack_forget()
            self.advance_status.pack_forget()
            self.refresh_spectator_controls()

    def build_website_tab(self):
        self.screen_header(self.website_tab, "MEDIA DESK", "Build the company brand, promote events, manage rights, and follow the fight world")

        # Media is intentionally a vertical dashboard.  Every main page already
        # lives in a scrollable canvas, so stacking these panels keeps the full
        # desk usable on a 768px laptop without forcing the player to pan past a
        # wide two-column layout just to reach a Treeview scrollbar.
        body = ttk.Frame(self.website_tab)
        body.pack(fill="both", expand=True)

        if not hasattr(self, "media_strategy_choice"):
            self.media_strategy_choice = tk.StringVar(value="Balanced")
        if not hasattr(self, "media_action_choice"):
            self.media_action_choice = tk.StringVar(value="Interview")

        strategy_panel, strategy = self.section(body, "MEDIA STRATEGY / COMPANY REACH")
        strategy_panel.pack(fill="x", pady=(0, 6))
        strategy.columnconfigure(1, weight=1)
        strategy.columnconfigure(3, weight=1)
        self.media_kpi_summary = ttk.Label(
            strategy,
            text="Media actions, brand heat, public trust, audience reach, and the next event will appear here.",
            style="Inset.TLabel",
            justify="left",
            anchor="w",
            wraplength=900,
        )
        self.media_kpi_summary.grid(row=0, column=0, columnspan=5, sticky="ew", padx=5, pady=(2, 7))
        ttk.Label(strategy, text="Company strategy", style="Inset.TLabel").grid(row=1, column=0, sticky="w", padx=(5, 4), pady=3)
        self.media_strategy_combo = ttk.Combobox(
            strategy,
            textvariable=self.media_strategy_choice,
            values=(
                "Balanced", "Sporting Credibility", "Star Builder", "Viral Growth",
                "Regional Expansion", "Sponsor Friendly", "Crisis Management",
            ),
            state="readonly",
            width=22,
        )
        self.media_strategy_combo.grid(row=1, column=1, sticky="w", padx=(0, 6), pady=3)
        ttk.Button(
            strategy,
            text="Apply Strategy",
            style="Accent.TButton",
            command=lambda: self.media_apply_strategy(),
        ).grid(row=1, column=2, sticky="w", padx=3, pady=3)
        ttk.Label(
            strategy,
            text="Strategy shapes campaign effectiveness, risk, sponsor fit, and the stories your promotion tries to create.",
            style="Inset.TLabel",
            justify="left",
            anchor="w",
            wraplength=720,
        ).grid(row=2, column=0, columnspan=5, sticky="ew", padx=5, pady=(3, 2))

        campaign_panel, campaign = self.section(body, "RUN A MEDIA CAMPAIGN")
        campaign_panel.pack(fill="x", pady=(0, 6))
        for column in (1, 3):
            campaign.columnconfigure(column, weight=1)
        ttk.Label(campaign, text="Spokesperson", style="Inset.TLabel").grid(row=0, column=0, sticky="w", padx=(5, 3), pady=4)
        self.media_fighter_combo = ttk.Combobox(campaign, textvariable=self.media_fighter_choice, state="readonly", width=22)
        self.media_fighter_combo.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
        self.media_fighter_combo.bind("<<ComboboxSelected>>", self.refresh_media_targets)
        ttk.Label(campaign, text="Optional target", style="Inset.TLabel").grid(row=0, column=2, sticky="w", padx=(3, 3), pady=4)
        self.media_target_combo = ttk.Combobox(campaign, textvariable=self.media_target_choice, state="readonly", width=22)
        self.media_target_combo.grid(row=0, column=3, sticky="ew", padx=(0, 8), pady=4)
        ttk.Label(campaign, text="Campaign", style="Inset.TLabel").grid(row=1, column=0, sticky="w", padx=(5, 3), pady=4)
        self.media_action_combo = ttk.Combobox(
            campaign,
            textvariable=self.media_action_choice,
            values=(
                "Interview", "Call Out", "Press Tour", "Open Workout",
                "Highlight Package", "Press Conference", "Regional Tour", "Crisis Response",
            ),
            state="readonly",
            width=20,
        )
        self.media_action_combo.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)
        self.media_action_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_media_dashboard())
        ttk.Button(
            campaign,
            text="Run Campaign",
            style="Accent.TButton",
            command=lambda: self.media_run_selected_campaign(),
        ).grid(row=1, column=2, columnspan=2, sticky="w", padx=3, pady=4)
        self.media_action_summary = ttk.Label(
            campaign,
            text="Select an action to see its cost, likely reach, exposure level, and whether a target is required.",
            style="Inset.TLabel",
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.media_action_summary.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=(2, 4))
        # Keep campaign outcomes on the desk.  This is deliberately separate
        # from the action preview so a committed result remains visible after
        # the dashboard refreshes its read-only projections.
        self.media_action_notice = ttk.Label(
            campaign,
            text="Campaign results and blockers will appear here.",
            style="Inset.TLabel",
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.media_action_notice.grid(row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=(0, 5))

        # M1 campaign brief: a saved, retargetable organisational plan around
        # the existing media resolver.  It is intentionally explicit about
        # what is and is not an active gameplay effect.
        plan_panel, plan = self.section(body, "CAMPAIGN PLAN / TARGET BRIEF")
        plan_panel.pack(fill="x", pady=(0, 6))
        for column in (1, 3):
            plan.columnconfigure(column, weight=1)
        if not hasattr(self, "media_plan_objective_choice"):
            self.media_plan_objective_choice = tk.StringVar(value="Event Promotion")
        if not hasattr(self, "media_plan_target_choice"):
            self.media_plan_target_choice = tk.StringVar(value="")
        if not hasattr(self, "media_plan_action_choice"):
            self.media_plan_action_choice = tk.StringVar(value="Press Tour")
        ttk.Label(plan, text="Objective", style="Inset.TLabel").grid(row=0, column=0, sticky="w", padx=(5, 3), pady=4)
        self.media_plan_objective_combo = ttk.Combobox(
            plan, textvariable=self.media_plan_objective_choice,
            values=("Event Promotion", "Prospect Exposure", "Sponsor Duty", "Regional Work", "Trust Repair"),
            state="readonly", width=20,
        )
        self.media_plan_objective_combo.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
        self.media_plan_objective_combo.bind("<<ComboboxSelected>>", self.refresh_media_plan_targets)
        ttk.Label(plan, text="Target", style="Inset.TLabel").grid(row=0, column=2, sticky="w", padx=(3, 3), pady=4)
        self.media_plan_target_combo = ttk.Combobox(plan, textvariable=self.media_plan_target_choice, state="readonly", width=28)
        self.media_plan_target_combo.grid(row=0, column=3, sticky="ew", padx=(0, 8), pady=4)
        self.media_plan_target_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_media_plan_summary())
        ttk.Label(plan, text="Allowed action", style="Inset.TLabel").grid(row=1, column=0, sticky="w", padx=(5, 3), pady=4)
        self.media_plan_action_combo = ttk.Combobox(
            plan, textvariable=self.media_plan_action_choice,
            values=("Interview", "Press Tour", "Open Workout", "Highlight Package", "Press Conference", "Regional Tour", "Crisis Response"),
            state="readonly", width=20,
        )
        self.media_plan_action_combo.grid(row=1, column=1, sticky="ew", padx=(0, 8), pady=4)
        self.media_plan_action_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_media_plan_summary())
        ttk.Label(plan, text="Spend ceiling", style="Inset.TLabel").grid(row=1, column=2, sticky="w", padx=(3, 3), pady=4)
        self.media_plan_spend_entry = ttk.Entry(plan, width=12)
        self.media_plan_spend_entry.insert(0, "0")
        self.media_plan_spend_entry.grid(row=1, column=3, sticky="w", padx=(0, 8), pady=4)
        plan_buttons = ttk.Frame(plan, style="Inset.TFrame")
        plan_buttons.grid(row=2, column=0, columnspan=4, sticky="ew", padx=3, pady=(2, 3))
        ttk.Button(plan_buttons, text="Save / Replace Brief", style="Accent.TButton", command=self.media_save_plan_from_ui).pack(side="left", padx=3)
        ttk.Button(plan_buttons, text="Retarget", command=self.media_retarget_plan_from_ui).pack(side="left", padx=3)
        ttk.Button(plan_buttons, text="Cancel Plan", command=self.media_cancel_plan_from_ui).pack(side="left", padx=3)
        self.media_plan_summary = ttk.Label(
            plan, text="No active plan. Save an optional target and action to create a reviewable campaign brief; this does not grant a hidden bonus.",
            style="Inset.TLabel", justify="left", anchor="w", wraplength=980,
        )
        self.media_plan_summary.grid(row=3, column=0, columnspan=4, sticky="ew", padx=5, pady=(2, 4))
        self.media_plan_notice = ttk.Label(
            plan,
            text="Brief changes and validation results will appear here.",
            style="Inset.TLabel", justify="left", anchor="w", wraplength=980,
        )
        self.media_plan_notice.grid(row=4, column=0, columnspan=4, sticky="ew", padx=5, pady=(0, 5))
        self.refresh_media_plan_targets()

        rights_panel, rights = self.section(body, "MEDIA RIGHTS / COMPLIANCE")
        rights_panel.pack(fill="x", pady=(0, 6))
        self.media_rights_summary = ttk.Label(
            rights,
            text="No active rights package. Available offers and delivery requirements will appear below.",
            style="Inset.TLabel",
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.media_rights_summary.pack(fill="x", padx=5, pady=(2, 6))
        self.media_rights_notice = ttk.Label(
            rights,
            text="Rights actions, renewal decisions and review blockers will appear here.",
            style="Inset.TLabel",
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.media_rights_notice.pack(fill="x", padx=5, pady=(0, 5))
        self.media_account_review = ttk.Label(
            rights,
            text="ACCOUNT REVIEW  |  No delivery history recorded yet.",
            style="Inset.TLabel",
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.media_account_review.pack(fill="x", padx=5, pady=(0, 6))
        self.media_offer_detail = tk.Frame(rights, bg=self.colors["panel_dark"], padx=10, pady=8)
        self.media_offer_detail.pack(fill="x", padx=5, pady=(0, 6))
        self.media_offer_verdict = tk.Label(self.media_offer_detail, text="SELECT AN OFFER", bg=self.colors["panel_dark"],
                                            fg=self.colors["gold"], font=("Impact", 14), anchor="w")
        self.media_offer_verdict.pack(fill="x")
        self.media_offer_numbers = tk.Label(self.media_offer_detail, text="", bg=self.colors["panel_dark"],
                                            fg=self.colors["text"], font=("Tahoma", 9, "bold"), anchor="w")
        self.media_offer_numbers.pack(fill="x", pady=(2, 0))

        offers_frame = ttk.Frame(rights, style="Panel.TFrame")
        offers_frame.pack(fill="both", expand=True)
        self.media_offers_tree = ttk.Treeview(
            offers_frame,
            columns=("partner", "type", "reach", "fee", "term", "events", "requirements"),
            show="headings",
            height=4,
        )
        for column, label, width, anchor in (
            ("partner", "Partner", 125, "w"), ("type", "Platform", 85, "w"),
            ("reach", "Reach", 45, "center"), ("fee", "Fee / Event", 75, "e"),
            ("term", "Term", 45, "center"), ("events", "Events", 45, "center"),
            ("requirements", "Requirements / Risk", 220, "w"),
        ):
            self.media_offers_tree.heading(column, text=label)
            self.media_offers_tree.column(column, width=width, minwidth=48, anchor=anchor, stretch=column in ("partner", "requirements"))
        offers_y = ttk.Scrollbar(offers_frame, orient="vertical", command=self.media_offers_tree.yview)
        offers_x = ttk.Scrollbar(offers_frame, orient="horizontal", command=self.media_offers_tree.xview)
        self.media_offers_tree.configure(yscrollcommand=offers_y.set, xscrollcommand=offers_x.set)
        offers_frame.rowconfigure(0, weight=1)
        offers_frame.columnconfigure(0, weight=1)
        self.media_offers_tree.grid(row=0, column=0, sticky="nsew")
        offers_y.grid(row=0, column=1, sticky="ns")
        offers_x.grid(row=1, column=0, sticky="ew")
        self.make_tree_sortable(self.media_offers_tree)
        self.media_offers_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_media_offer())
        offer_buttons = ttk.Frame(rights, style="Inset.TFrame")
        offer_buttons.pack(fill="x", pady=(5, 0))
        ttk.Button(offer_buttons, text="Accept Selected", style="Accent.TButton", command=lambda: self.media_accept_selected_offer()).pack(side="left", padx=3, pady=3)
        ttk.Button(offer_buttons, text="Reject Selected", command=lambda: self.media_reject_selected_offer()).pack(side="left", padx=3, pady=3)
        self.media_negotiation_stance = tk.StringVar(value="Higher Guarantee")
        ttk.Combobox(offer_buttons, textvariable=self.media_negotiation_stance,
                     values=("Higher Guarantee", "Wider Reach", "Lower Standards", "Shorter Commitment"),
                     state="readonly", width=19).pack(side="left", padx=(12, 3), pady=3)
        ttk.Button(offer_buttons, text="Counter Offer", command=lambda: self.media_counter_selected_offer()).pack(side="left", padx=3, pady=3)
        review_btn = ttk.Button(offer_buttons, text="Paid Market Review ($3,500)", command=lambda: self.media_refresh_offers())
        review_btn.pack(side="left", padx=3, pady=3)
        self.attach_tooltip(review_btn, "Commission a fresh market review for $3,500. It replaces only uncommitted offers; active media contracts remain unchanged.")
        ttk.Button(offer_buttons, text="Prepare Renewal", command=lambda: self.media_prepare_renewal()).pack(side="right", padx=3, pady=3)
        ttk.Button(offer_buttons, text="Counter Renewal", command=lambda: self.media_counter_renewal()).pack(side="right", padx=3, pady=3)
        ttk.Button(offer_buttons, text="Accept Renewal", command=lambda: self.media_accept_renewal()).pack(side="right", padx=3, pady=3)
        ttk.Button(offer_buttons, text="End Active Deal", command=lambda: self.media_terminate_contract()).pack(side="right", padx=3, pady=3)

        receipt_panel = ttk.Frame(rights, style="Inset.TFrame")
        receipt_panel.pack(fill="both", expand=True, pady=(6, 0))
        receipt_header = ttk.Frame(receipt_panel, style="Inset.TFrame")
        receipt_header.pack(fill="x", padx=5, pady=(3, 0))
        ttk.Label(receipt_header, text="SETTLEMENT RECEIPTS / READ-ONLY", style="Section.TLabel", anchor="w").pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Button(receipt_header, text="View selected", command=self.media_open_selected_receipt).pack(side="right")
        ttk.Label(
            receipt_panel,
            text="Open a receipt for separated rights, production, sponsor-duty and audience evidence. Settlement records remain immutable.",
            style="Inset.TLabel", anchor="w",
        ).pack(fill="x", padx=5, pady=(0, 3))
        receipt_table = ttk.Frame(receipt_panel, style="Panel.TFrame")
        receipt_table.pack(fill="both", expand=True, padx=5)
        self.media_receipts_tree = ttk.Treeview(
            receipt_table, columns=("date", "event", "rights", "sponsors", "delivery"), show="headings", height=4,
        )
        for column, label, width, anchor in (
            ("date", "Date", 62, "center"), ("event", "Event", 150, "w"),
            ("rights", "Rights", 78, "e"), ("sponsors", "Sponsors", 78, "e"),
            ("delivery", "Delivery", 90, "w"),
        ):
            self.media_receipts_tree.heading(column, text=label)
            self.media_receipts_tree.column(column, width=width, minwidth=48, anchor=anchor, stretch=column == "event")
        receipt_y = ttk.Scrollbar(receipt_table, orient="vertical", command=self.media_receipts_tree.yview)
        receipt_x = ttk.Scrollbar(receipt_table, orient="horizontal", command=self.media_receipts_tree.xview)
        self.media_receipts_tree.configure(yscrollcommand=receipt_y.set, xscrollcommand=receipt_x.set)
        receipt_table.rowconfigure(0, weight=1)
        receipt_table.columnconfigure(0, weight=1)
        self.media_receipts_tree.grid(row=0, column=0, sticky="nsew")
        receipt_y.grid(row=0, column=1, sticky="ns")
        receipt_x.grid(row=1, column=0, sticky="ew")
        self.media_receipts_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_media_receipt())
        self.media_receipts_tree.bind("<Double-1>", lambda _event: self.media_open_selected_receipt())
        self.media_receipt_detail = ttk.Label(
            receipt_panel, text="No settled receipts yet. A receipt is created once at event settlement and cannot be edited by reopening it.",
            style="Inset.TLabel", justify="left", anchor="w", wraplength=980,
        )
        self.media_receipt_detail.pack(fill="x", padx=5, pady=(3, 5))

        history_panel, history = self.section(body, "CAMPAIGN HISTORY")
        history_panel.pack(fill="both", expand=True, pady=(0, 6))
        history_frame = ttk.Frame(history, style="Panel.TFrame")
        history_frame.pack(fill="both", expand=True)
        self.media_campaign_history_tree = ttk.Treeview(
            history_frame,
            columns=("date", "strategy", "action", "subject", "target", "outcome", "heat", "cost"),
            show="headings",
            height=7,
        )
        for column, label, width, anchor in (
            ("date", "Date", 62, "center"), ("strategy", "Strategy", 80, "w"),
            ("action", "Campaign", 82, "w"), ("subject", "Spokesperson", 95, "w"),
            ("target", "Target", 95, "w"), ("outcome", "Outcome", 150, "w"),
            ("heat", "Heat", 42, "center"), ("cost", "Cost", 55, "e"),
        ):
            self.media_campaign_history_tree.heading(column, text=label)
            self.media_campaign_history_tree.column(column, width=width, minwidth=48, anchor=anchor, stretch=column == "outcome")
        history_y = ttk.Scrollbar(history_frame, orient="vertical", command=self.media_campaign_history_tree.yview)
        history_x = ttk.Scrollbar(history_frame, orient="horizontal", command=self.media_campaign_history_tree.xview)
        self.media_campaign_history_tree.configure(yscrollcommand=history_y.set, xscrollcommand=history_x.set)
        history_frame.rowconfigure(0, weight=1)
        history_frame.columnconfigure(0, weight=1)
        self.media_campaign_history_tree.grid(row=0, column=0, sticky="nsew")
        history_y.grid(row=0, column=1, sticky="ns")
        history_x.grid(row=1, column=0, sticky="ew")
        self.make_tree_sortable(self.media_campaign_history_tree)
        self.media_campaign_history_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_media_campaign())
        self.media_campaign_detail = ttk.Label(
            history, text="Select a campaign to inspect its retained outcome. Campaign history is read-only.",
            style="Inset.TLabel", justify="left", anchor="w", wraplength=980,
        )
        self.media_campaign_detail.pack(fill="x", pady=(4, 0))

        brief_panel, brief = self.section(body, "COMPANY MEDIA BRIEF / UPCOMING EVENTS")
        brief_panel.pack(fill="x", pady=(0, 6))
        self.website_story = tk.Text(brief, wrap="word", font=("Tahoma", 9, "bold"), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], height=5, padx=10, pady=8)
        self.website_story.pack(fill="x")
        ttk.Label(brief, text="Upcoming Events Calendar", style="Section.TLabel", anchor="center").pack(fill="x", pady=(6, 4))
        self.website_calendar = tk.Text(brief, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], height=5, padx=10, pady=8)
        self.website_calendar.pack(fill="x")

        news_panel, news = self.section(body, "WORLD NEWSROOM")
        news_panel.pack(fill="both", expand=True)
        news_table = ttk.Frame(news, style="Panel.TFrame")
        news_table.pack(fill="both", expand=True)
        self.website_news = ttk.Treeview(news_table, columns=("type", "headline", "date"), show="headings", height=11)
        for column, label, width, anchor in (
            ("type", "Type", 95, "w"), ("headline", "Headline", 430, "w"), ("date", "Date", 85, "center"),
        ):
            self.website_news.heading(column, text=label)
            self.website_news.column(column, width=width, minwidth=65, anchor=anchor, stretch=column == "headline")
        news_y = ttk.Scrollbar(news_table, orient="vertical", command=self.website_news.yview)
        news_x = ttk.Scrollbar(news_table, orient="horizontal", command=self.website_news.xview)
        self.website_news.configure(yscrollcommand=news_y.set, xscrollcommand=news_x.set)
        news_table.rowconfigure(0, weight=1)
        news_table.columnconfigure(0, weight=1)
        self.website_news.grid(row=0, column=0, sticky="nsew")
        news_y.grid(row=0, column=1, sticky="ns")
        news_x.grid(row=1, column=0, sticky="ew")
        self.website_news.bind("<<TreeviewSelect>>", self.show_selected_media_story)
        self.website_news.bind("<Double-1>", lambda _event: self.open_selected_news_story())
        self.website_news.bind("<Return>", lambda _event: self.open_selected_news_story())
        self.website_news_preview = tk.Text(news, wrap="word", height=6, font=("Tahoma", 9), bg=self.colors["panel_dark"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=10, pady=8)
        self.website_news_preview.pack(fill="x", pady=(6, 0))
        self.website_news_preview.config(state="disabled")
        news_buttons = ttk.Frame(news, style="Inset.TFrame")
        news_buttons.pack(fill="x", pady=(5, 0))
        ttk.Button(news_buttons, text="Read Selected Story", style="Accent.TButton", command=self.open_selected_news_story).pack(side="left", padx=3, pady=3)
        ttk.Button(news_buttons, text="Open Story Context", command=self.open_selected_story_context).pack(side="left", padx=3, pady=3)
        ttk.Button(news_buttons, text="World Chronicle", command=self.open_world_chronicle).pack(side="right", padx=3, pady=3)

        def resize_media_wrap(event):
            wrap = max(320, event.width - 30)
            for label in (self.media_kpi_summary, self.media_action_summary, self.media_rights_summary):
                label.configure(wraplength=wrap)

        body.bind("<Configure>", resize_media_wrap, add="+")

    def build_assistant_tab(self):
        self.assistant_tab._force_viewport_width = True
        style = ttk.Style(self.assistant_tab)
        style.configure("Dashboard.Treeview", rowheight=34, font=("Tahoma", 9))
        style.configure("Dashboard.Treeview.Heading", font=("Tahoma", 9, "bold"), padding=(8, 8))
        self.screen_header(self.assistant_tab, "PROMOTER DASHBOARD", "Your week at a glance. Resolve the risks, build the card, then advance.")
        top_panel, top = self.section(self.assistant_tab, "01 / THE PROMOTION")
        top_panel.pack(fill="x", pady=(0, 6))
        self.assistant_snapshot = ttk.Label(top, text="", justify="left", anchor="w", style="Inset.TLabel")
        self.assistant_snapshot.pack(fill="x", padx=8, pady=6)
        self.assistant_snapshot.bind("<Configure>", lambda event: self.assistant_snapshot.configure(wraplength=max(180, event.width - 18)))
        self.assistant_kpis = {}
        kpi_row = ttk.Frame(top, style="Inset.TFrame")
        kpi_row.pack(fill="x", padx=5, pady=(0, 5))
        kpi_cells = []
        for key, label, destination in (("show", "NEXT SHOW", "booking"), ("card", "CARD READINESS", "booking"), ("contracts", "CONTRACTS", "contracts"),
                                        ("divisions", "DIVISION DEPTH", "market"), ("runway", "FIXED-COST RUNWAY", "finance"), ("medical", "FIGHTER READINESS", "roster")):
            cell = tk.Frame(kpi_row, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
            kpi_cells.append(cell)
            tk.Label(cell, text=label, bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 8, "bold")).pack(anchor="w", padx=12, pady=(10, 3))
            value = tk.Label(cell, text="-", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 13, "bold"), anchor="w", justify="left")
            value.pack(fill="x", padx=12, pady=(0, 6))
            value.bind("<Configure>", lambda event, widget=value: widget.configure(wraplength=max(120, event.width - 8)))
            ttk.Button(cell, text="Open " + destination.title(), command=lambda name=destination: self.select_tab(
                "results" if getattr(self, "spectator_mode", False) else name)).pack(anchor="w", padx=12, pady=(0, 10))
            self.assistant_kpis[key] = value
        layout_state = {"columns": None}
        def fit_dashboard(event):
            columns = 3 if event.width >= 780 else 2 if event.width >= 480 else 1
            if layout_state["columns"] == columns:
                return
            layout_state["columns"] = columns
            for column in range(3):
                kpi_row.columnconfigure(column, weight=1 if column < columns else 0, uniform="dashboard")
            for index, cell in enumerate(kpi_cells):
                cell.grid(row=index // columns, column=index % columns, sticky="nsew", padx=3, pady=3)
        kpi_row.bind("<Configure>", fit_dashboard)
        for index, cell in enumerate(kpi_cells):
            cell.grid(row=index // 3, column=index % 3, sticky="nsew", padx=3, pady=3)
        quick = ttk.Frame(top, style="Inset.TFrame")
        quick.pack(fill="x", padx=5, pady=(0, 6))
        for index, (label, tab) in enumerate((("Build a Card", "booking"), ("Read Inbox", "inbox"), ("Latest Results", "results"))):
            ttk.Button(quick, text=label, command=lambda name=tab: self.select_tab(name)).grid(row=0, column=index, sticky="ew", padx=3, pady=4)
            quick.columnconfigure(index, weight=1)
        ttk.Button(quick, text="First Week Guide", command=self.open_guided_first_week).grid(row=1, column=0, sticky="w", padx=3, pady=3)

        body = ttk.Frame(self.assistant_tab, style="Panel.TFrame")
        body.pack(fill="both", expand=True)
        dashboard_tabs = ttk.Notebook(body)
        dashboard_tabs.pack(fill="both", expand=True)
        msg_panel, msg = self.section(dashboard_tabs, "02 / DECISION QUEUE")
        dashboard_tabs.add(msg_panel, text="  Decisions & Actions  ")
        self.assistant_queue_summary = ttk.Label(msg, text="", style="Inset.TLabel", anchor="w")
        self.assistant_queue_summary.pack(fill="x", pady=(0, 6))
        message_table = ttk.Frame(msg, style="Inset.TFrame")
        message_table.pack(fill="both", expand=True)
        self.assistant_messages = ttk.Treeview(message_table, style="Dashboard.Treeview", columns=("priority", "notice", "action"), show="headings", selectmode="browse", height=6)
        for column, label, width in (("priority", "!", 36), ("notice", "Decision / Risk", 510), ("action", "Open", 90)):
            self.assistant_messages.heading(column, text=label)
            self.assistant_messages.column(column, width=width, anchor="w")
        self.assistant_messages.column("priority", width=36, minwidth=30, stretch=False)
        self.assistant_messages.column("notice", width=440, minwidth=120, stretch=True)
        self.assistant_messages.column("action", width=90, minwidth=70, stretch=False)
        dashboard_semantic = self.semantic_status_palette(self.colors)
        self.assistant_messages.tag_configure("urgent", foreground=dashboard_semantic["negative"])
        self.assistant_messages.tag_configure("normal", foreground=dashboard_semantic["warning"])
        message_scroll = ttk.Scrollbar(message_table, orient="vertical", command=self.assistant_messages.yview)
        self.assistant_messages.configure(yscrollcommand=message_scroll.set)
        message_scroll.pack(side="right", fill="y")
        self.assistant_messages.pack(side="left", fill="both", expand=True)
        self.assistant_messages.bind("<Double-1>", lambda _event: self.open_selected_assistant_notice())
        self.assistant_messages.bind("<Return>", lambda _event: self.open_selected_assistant_notice())
        self.assistant_messages.bind("<<TreeviewSelect>>", self.refresh_assistant_decision_detail)
        detail = ttk.Frame(msg, style="Inset.TFrame", padding=10)
        detail.pack(fill="x", pady=(8, 0))
        ttk.Label(detail, text="ASSISTANT BRIEFING", style="Inset.TLabel", font=("Tahoma", 9, "bold")).pack(anchor="w", pady=(0, 5))
        self.assistant_decision_detail = ttk.Label(detail, text="Select a decision to read the complete advice.", style="Inset.TLabel", anchor="w", justify="left")
        self.assistant_decision_detail.pack(fill="x")
        self.assistant_decision_detail.bind("<Configure>", lambda event: self.assistant_decision_detail.configure(wraplength=max(160, event.width - 16)))
        self.assistant_decision_consequence = ttk.Label(
            detail,
            text="The selected row's consequence and next destination will appear here.",
            style="Inset.TLabel", anchor="w", justify="left",
        )
        self.assistant_decision_consequence.pack(fill="x", pady=(6, 0))
        self.assistant_decision_consequence.bind("<Configure>", lambda event: self.assistant_decision_consequence.configure(wraplength=max(160, event.width - 16)))
        self.assistant_decision_button = ttk.Button(detail, text="Open Selected Context", style="Accent.TButton", command=self.open_selected_assistant_notice, state="disabled")
        self.assistant_decision_button.pack(anchor="w", pady=(8, 0))

        change_panel, changes = self.section(dashboard_tabs, "03 / WHAT CHANGED AND WHY")
        dashboard_tabs.add(change_panel, text="  Recent Changes  ")
        change_table = ttk.Frame(changes, style="Inset.TFrame")
        change_table.pack(fill="both", expand=True)
        self.assistant_changes = ttk.Treeview(change_table, style="Dashboard.Treeview", columns=("date", "change", "why"), show="headings", height=8)
        for column, label, width in (("date", "When", 90), ("change", "Attributed Delta", 190), ("why", "Why", 390)):
            self.assistant_changes.heading(column, text=label)
            self.assistant_changes.column(column, width=width, anchor="w")
        change_y = ttk.Scrollbar(change_table, orient="vertical", command=self.assistant_changes.yview)
        change_x = ttk.Scrollbar(change_table, orient="horizontal", command=self.assistant_changes.xview)
        self.assistant_changes.configure(yscrollcommand=change_y.set, xscrollcommand=change_x.set)
        change_x.pack(side="bottom", fill="x")
        self.assistant_changes.pack(side="left", fill="both", expand=True)
        change_y.pack(side="right", fill="y")

        calendar_panel, calendar = self.section(dashboard_tabs, "04 / OWNED COMPANY CALENDAR")
        dashboard_tabs.add(calendar_panel, text="  Owned Calendar  ")
        self.assistant_calendar_summary = ttk.Label(calendar, text="", style="Inset.TLabel", anchor="w")
        self.assistant_calendar_summary.pack(fill="x", pady=(0, 6))
        calendar_filters = ttk.Frame(calendar, style="Inset.TFrame")
        calendar_filters.pack(fill="x", pady=(0, 5))
        self.assistant_calendar_owner_filter = tk.StringVar(value="All")
        self.assistant_calendar_source_filter = tk.StringVar(value="All")
        self.assistant_calendar_status_filter = tk.StringVar(value="All")
        ttk.Label(calendar_filters, text="Company", style="Inset.TLabel").pack(side="left", padx=(5, 3))
        self.assistant_calendar_owner_combo = ttk.Combobox(
            calendar_filters, textvariable=self.assistant_calendar_owner_filter,
            values=("All",), state="readonly", width=20,
        )
        self.assistant_calendar_owner_combo.pack(side="left", padx=(0, 7))
        ttk.Label(calendar_filters, text="Source", style="Inset.TLabel").pack(side="left", padx=(3, 3))
        self.assistant_calendar_source_combo = ttk.Combobox(
            calendar_filters, textvariable=self.assistant_calendar_source_filter,
            values=("All",), state="readonly", width=14,
        )
        self.assistant_calendar_source_combo.pack(side="left", padx=(0, 7))
        ttk.Label(calendar_filters, text="Status", style="Inset.TLabel").pack(side="left", padx=(3, 3))
        self.assistant_calendar_status_combo = ttk.Combobox(
            calendar_filters, textvariable=self.assistant_calendar_status_filter,
            values=("All",), state="readonly", width=13,
        )
        self.assistant_calendar_status_combo.pack(side="left", padx=(0, 7))
        for combo in (
            self.assistant_calendar_owner_combo,
            self.assistant_calendar_source_combo,
            self.assistant_calendar_status_combo,
        ):
            combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_assistant())
        ttk.Button(
            calendar_filters, text="Reset", command=self.reset_assistant_calendar_filters,
        ).pack(side="left", padx=3)
        calendar_table = ttk.Frame(calendar, style="Inset.TFrame")
        calendar_table.pack(fill="both", expand=True)
        self.assistant_calendar_tree = ttk.Treeview(
            calendar_table, style="Dashboard.Treeview",
            columns=("date", "owner", "source", "event", "status", "bouts", "venue", "identity"),
            show="headings", height=8, selectmode="browse",
        )
        for column, label, width in (
            ("date", "When", 95), ("owner", "Operating company", 170), ("source", "Source", 92),
            ("event", "Event", 210), ("status", "Status", 90), ("bouts", "Bouts", 52),
            ("venue", "Venue", 160), ("identity", "ID", 100),
        ):
            self.assistant_calendar_tree.heading(column, text=label)
            self.assistant_calendar_tree.column(column, width=width, anchor="center")
        for column in ("owner", "event", "venue"):
            self.assistant_calendar_tree.column(column, anchor="w")
        calendar_scroll_y = ttk.Scrollbar(calendar_table, orient="vertical", command=self.assistant_calendar_tree.yview)
        calendar_scroll_x = ttk.Scrollbar(calendar_table, orient="horizontal", command=self.assistant_calendar_tree.xview)
        self.assistant_calendar_tree.configure(yscrollcommand=calendar_scroll_y.set, xscrollcommand=calendar_scroll_x.set)
        calendar_scroll_y.pack(side="right", fill="y")
        calendar_scroll_x.pack(side="bottom", fill="x")
        self.assistant_calendar_tree.pack(side="left", fill="both", expand=True)
        self.assistant_calendar_tree.bind("<<TreeviewSelect>>", self.refresh_assistant_calendar_detail)
        self.assistant_calendar_tree.bind("<Double-1>", lambda _event: self.open_selected_owned_calendar_event())
        calendar_actions = ttk.Frame(calendar, style="Inset.TFrame")
        calendar_actions.pack(fill="x", pady=(7, 0))
        self.assistant_calendar_detail = ttk.Label(
            calendar_actions,
            text="Select an owned event to inspect its stored source, ownership and participants.",
            style="Inset.TLabel", anchor="w", justify="left",
        )
        self.assistant_calendar_detail.pack(side="left", fill="x", expand=True, padx=(5, 8))
        self.assistant_calendar_detail.bind(
            "<Configure>", lambda event: self.assistant_calendar_detail.configure(wraplength=max(220, event.width - 16))
        )
        ttk.Button(
            calendar_actions, text="View Event Detail", style="Accent.TButton",
            command=self.open_selected_owned_calendar_event,
        ).pack(side="right", padx=4)

    def build_companies_tab(self):
        self.screen_header(self.companies_tab, "INDUSTRY STANDINGS", "Every promotion and combat-sport circuit, ranked by power. Filter, sort, and open a profile to see why.")

        filters = ttk.Frame(self.companies_tab, style="Inset.TFrame")
        filters.pack(fill="x", pady=(0, 6))
        self.company_sport_filter = tk.StringVar(value="All Sports")
        self.company_region_filter = tk.StringVar(value="All Regions")
        self.company_sort_by = tk.StringVar(value="Power ranking")
        ttk.Label(filters, text="Sport", style="Inset.TLabel").pack(side="left", padx=(6, 2))
        self.company_sport_combo = ttk.Combobox(filters, textvariable=self.company_sport_filter, values=("All Sports",), state="readonly", width=16)
        self.company_sport_combo.pack(side="left", padx=(0, 8))
        self.company_sport_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_companies())
        ttk.Label(filters, text="Region", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        self.company_region_combo = ttk.Combobox(filters, textvariable=self.company_region_filter, values=("All Regions",), state="readonly", width=16)
        self.company_region_combo.pack(side="left", padx=(0, 8))
        self.company_region_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_companies())
        ttk.Label(filters, text="Sort by", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        self.company_sort_combo = ttk.Combobox(
            filters, textvariable=self.company_sort_by, state="readonly", width=18,
            values=("Power ranking", "Richest", "Most stable", "Best reputation", "Deepest roster", "Most champions"),
        )
        self.company_sort_combo.pack(side="left", padx=(0, 8))
        self.company_sort_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_companies())
        self.company_standings_summary = ttk.Label(filters, text="", style="Inset.TLabel")
        self.company_standings_summary.pack(side="right", padx=8)

        companies_resize = self.create_vertical_resizer(self.companies_tab, initial_fraction=0.56, min_top=200, min_bottom=190)
        companies_resize.pack(fill="both", expand=True)

        table_panel, table_inner = self.section(companies_resize, "STANDINGS")
        companies_resize.add(table_panel, minsize=200)
        columns = ("rank", "move", "name", "sport", "region", "tier", "power", "cred", "stability", "cash", "roster", "champs", "stars")
        self.company_list = ttk.Treeview(table_inner, columns=columns, show="headings", selectmode="browse")
        for col, text, width in (
            ("rank", "#", 40), ("move", "Move", 52), ("name", "Company", 190), ("sport", "Sport", 92),
            ("region", "Region", 96), ("tier", "Tier", 84), ("power", "Power", 60), ("cred", "Cred", 50),
            ("stability", "Stab", 50), ("cash", "Cash", 100), ("roster", "Roster", 56), ("champs", "Champs", 58), ("stars", "Stars", 52),
        ):
            self.company_list.heading(col, text=text)
            self.company_list.column(col, width=width, anchor="center")
        self.company_list.column("name", anchor="w")
        self.company_list.column("region", anchor="w")
        self.company_list.column("cash", anchor="e")
        self.company_list.tag_configure("player", background="#26405c", foreground="#ffffff")
        self.company_list.tag_configure("tier_global", foreground="#e6c15a")
        self.company_list.tag_configure("tier_national", foreground="#7fb0f0")
        self.company_list.tag_configure("tier_regional", foreground="#7fd694")
        self.company_list.tag_configure("tier_local", foreground="#b8bdc4")
        standings_scroll = ttk.Scrollbar(table_inner, orient="vertical", command=self.company_list.yview)
        self.company_list.configure(yscrollcommand=standings_scroll.set)
        standings_scroll.pack(side="right", fill="y")
        self.make_tree_sortable(self.company_list)
        self.company_list.pack(fill="both", expand=True)
        self.company_list.bind("<<TreeviewSelect>>", lambda _e: self.refresh_company_profile())
        self.company_list.bind("<Double-1>", lambda _e: self.open_selected_company_hub())

        lower = ttk.Frame(companies_resize, style="Inset.TFrame")
        companies_resize.add(lower, minsize=190)
        profile_panel, profile = self.section(lower, "COMPANY PROFILE")
        profile_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.company_metric_cards = {}
        company_metrics = ttk.Frame(profile, style="Inset.TFrame")
        company_metrics.pack(fill="x", padx=4, pady=(0, 5))
        for key, title, detail in (
            ("rank", "INDUSTRY RANK", "Tracked standings"),
            ("power", "POWER", "Composite strength"),
            ("roster", "ROSTER", "Contracted fighters"),
            ("stability", "STABILITY", "Operating health"),
        ):
            card = ttk.Frame(company_metrics, style="Panel.TFrame")
            card.pack(side="left", fill="both", expand=True, padx=3, pady=3)
            ttk.Label(card, text=title, style="Section.TLabel", anchor="center").pack(fill="x")
            value = ttk.Label(card, text="—", style="Panel.TLabel", anchor="center", font=("Tahoma", 11, "bold"))
            value.pack(fill="x", padx=4, pady=(5, 1))
            note = ttk.Label(card, text=detail, style="Panel.TLabel", anchor="center", wraplength=135)
            note.pack(fill="x", padx=4, pady=(0, 5))
            self.company_metric_cards[key] = (value, note)
        self.company_profile = tk.Text(profile, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=10, pady=10)
        self.company_profile.pack(fill="both", expand=True)

        next_steps = ttk.Frame(profile, style="Inset.TFrame")
        next_steps.pack(fill="x", pady=(5, 2))
        ttk.Label(next_steps, text="NEXT STEP", style="Section.TLabel").pack(side="left", padx=(5, 8), pady=5)
        self.company_next_step_summary = ttk.Label(next_steps, text="Select a company to see the most useful next action.", style="Inset.TLabel", anchor="w")
        self.company_next_step_summary.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)
        self.company_next_step_primary = ttk.Button(next_steps, text="Open", command=lambda: self.open_company_next_step("primary"), state="disabled")
        self.company_next_step_primary.pack(side="right", padx=3, pady=3)
        self.company_next_step_secondary = ttk.Button(next_steps, text="Review", command=lambda: self.open_company_next_step("secondary"), state="disabled")
        self.company_next_step_secondary.pack(side="right", padx=3, pady=3)

        detail_panel, detail = self.section(lower, "POWER BREAKDOWN & TREND")
        detail_panel.pack(side="left", fill="both", expand=True)
        detail_panel.configure(width=340)
        detail_panel.pack_propagate(False)
        self.company_breakdown = tk.Text(detail, wrap="word", font=("Consolas", 9), bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=8, height=9)
        self.company_breakdown.pack(fill="both", expand=True)
        spark_row = ttk.Frame(detail, style="Inset.TFrame")
        spark_row.pack(fill="x", pady=(4, 0))
        ttk.Label(spark_row, text="Power trend", style="Inset.TLabel").pack(side="left", padx=(2, 6))
        self.company_sparkline = tk.Canvas(spark_row, height=38, width=240, bg=self.colors["cream"], highlightthickness=1, highlightbackground="#7a7f87")
        self.company_sparkline.pack(side="left", fill="x", expand=True, padx=(0, 4))

        company_buttons = ttk.Frame(profile, style="Inset.TFrame")
        company_buttons.pack(fill="x", pady=4)
        ttk.Button(company_buttons, text="Open Company Hub", style="Accent.TButton", command=self.open_selected_company_hub).pack(side="left", padx=4)
        ttk.Button(company_buttons, text="Roster", command=lambda: self.open_selected_company_section("Roster")).pack(side="left", padx=2)
        ttk.Button(company_buttons, text="Rankings", command=lambda: self.open_selected_company_section("Rankings")).pack(side="left", padx=2)
        ttk.Button(company_buttons, text="Belts", command=lambda: self.open_selected_company_section("Belts")).pack(side="left", padx=2)
        ttk.Button(company_buttons, text="Events", command=lambda: self.open_selected_company_section("Events")).pack(side="left", padx=2)
        ttk.Button(company_buttons, text="Results", command=lambda: self.open_selected_company_section("Results")).pack(side="left", padx=2)
        company_actions = ttk.Frame(profile, style="Inset.TFrame")
        company_actions.pack(fill="x", pady=(0, 4))
        ttk.Button(company_actions, text="Finance", command=lambda: self.open_selected_company_section("Finance")).pack(side="left", padx=4)
        ttk.Button(company_actions, text="Staff", command=lambda: self.open_selected_company_section("Staff")).pack(side="left", padx=2)
        ttk.Button(company_actions, text="Read Last Card", command=self.view_selected_company_card).pack(side="left", padx=8)
        ttk.Button(company_actions, text="Watch Last Card", command=self.watch_selected_company_card).pack(side="left", padx=2)
        ttk.Button(company_actions, text="MMA Child Promotions", command=self.open_child_promotion_manager).pack(side="left", padx=8)
        self.return_to_spectator_button = ttk.Button(company_actions, text="Return to Spectator", command=self.return_to_spectator_mode)
        self.return_to_spectator_button.pack(side="right", padx=4)
        self.take_control_company_button = ttk.Button(company_actions, text="Take Control Of Selected Company", command=self.take_control_selected_company)
        self.take_control_company_button.pack(side="right", padx=4)

    def build_regions_tab(self):
        self.screen_header(self.regions_tab, "GAME WORLD", "Regions, states, economies, legal status, drug testing, teams, and local show history")
        body = ttk.Frame(self.regions_tab)
        body.pack(fill="both", expand=True)
        region_panel, region_inner = self.section(body, "REGIONS")
        region_panel.pack(side="left", fill="y", padx=(0, 6))
        region_panel.configure(width=240)
        region_panel.pack_propagate(False)
        self.region_list = tk.Listbox(
            region_inner,
            font=("Tahoma", 9),
            bg=self.colors["tree"],
            fg=self.colors["text"],
            selectbackground=self.colors["red"],
            selectforeground="#ffffff",
            activestyle="none",
            highlightbackground=self.colors["line"],
            highlightcolor=self.colors["line"],
            relief="flat",
        )
        self.region_list.pack(fill="both", expand=True)
        self.region_list.bind("<<ListboxSelect>>", lambda _e: self.refresh_region_profile())
        info_panel, info = self.section(body, "REGION PROFILE")
        info_panel.pack(side="left", fill="both", expand=True)
        self.region_metric_cards = {}
        region_metrics = ttk.Frame(info, style="Inset.TFrame")
        region_metrics.pack(fill="x", padx=4, pady=(0, 6))
        for key, title, detail in (
            ("economy", "MARKET", "Regional economy"),
            ("legality", "REGULATION", "MMA legal status"),
            ("testing", "TESTING", "Estimated drug-test accuracy"),
            ("mma_love", "LOCAL PULSE", "Regional MMA interest"),
        ):
            card = ttk.Frame(region_metrics, style="Panel.TFrame")
            card.pack(side="left", fill="both", expand=True, padx=3, pady=3)
            ttk.Label(card, text=title, style="Section.TLabel", anchor="center").pack(fill="x")
            value = ttk.Label(card, text="—", style="Panel.TLabel", anchor="center", font=("Tahoma", 11, "bold"))
            value.pack(fill="x", padx=4, pady=(5, 1))
            note = ttk.Label(card, text=detail, style="Panel.TLabel", anchor="center", wraplength=150)
            note.pack(fill="x", padx=4, pady=(0, 5))
            self.region_metric_cards[key] = (value, note)
        self.region_profile = tk.Text(info, wrap="word", font=("Tahoma", 10, "italic"), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=14, pady=14)
        self.region_profile.pack(fill="both", expand=True)
        region_next_steps = ttk.Frame(info, style="Inset.TFrame")
        region_next_steps.pack(fill="x", pady=(5, 2))
        ttk.Label(region_next_steps, text="NEXT STEP", style="Section.TLabel").pack(side="left", padx=(5, 8), pady=5)
        self.region_next_step_summary = ttk.Label(region_next_steps, text="Select a region to see the most useful next action.", style="Inset.TLabel", anchor="w")
        self.region_next_step_summary.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)
        self.region_next_step_primary = ttk.Button(region_next_steps, text="Open", command=lambda: self.open_region_next_step("primary"), state="disabled")
        self.region_next_step_primary.pack(side="right", padx=3, pady=3)
        self.region_next_step_secondary = ttk.Button(region_next_steps, text="Review", command=lambda: self.open_region_next_step("secondary"), state="disabled")
        self.region_next_step_secondary.pack(side="right", padx=3, pady=3)
        region_actions = ttk.Frame(info, style="Inset.TFrame")
        region_actions.pack(fill="x", pady=(6, 0))
        ttk.Button(region_actions, text="Open Region Hub", style="Accent.TButton", command=self.open_selected_region_hub).pack(side="left", padx=4)
        ttk.Button(region_actions, text="View Local Gyms", command=lambda: self.open_selected_region_hub("Gyms")).pack(side="left", padx=4)
        ttk.Button(region_actions, text="View Local Fighters", command=lambda: self.open_selected_region_hub("Fighters")).pack(side="left", padx=4)
        ttk.Button(region_actions, text="Feasibility Review", command=self.open_selected_region_feasibility).pack(side="left", padx=4)

    def build_results_tab(self):
        self.screen_header(self.results_tab, "RESULTS DATABASE", "Event recaps, critical ratings, commercial ratings, gates, methods, and show histories")
        controls = ttk.Frame(self.results_tab, style="Inset.TFrame")
        controls.pack(fill="x", pady=(0, 6))
        ttk.Label(controls, text="Search", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        search_entry = ttk.Entry(controls, textvariable=self.result_search, width=34)
        search_entry.pack(side="left", fill="x", expand=True, padx=4)
        search_entry.bind("<KeyRelease>", lambda _e: self.refresh_results())
        ttk.Label(controls, text="Promotion", style="Inset.TLabel").pack(side="left", padx=(8, 2))
        self.result_company_combo = ttk.Combobox(controls, textvariable=self.result_company_filter, values=("All",), state="readonly", width=24)
        self.result_company_combo.pack(side="left", padx=(0, 4))
        self.result_company_combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_results())
        result_buttons = ttk.Frame(self.results_tab, style="Inset.TFrame")
        result_buttons.pack(fill="x", pady=(0, 6))
        for col, (text, command, style) in enumerate((
            ("Open Selected", self.open_selected_result, None),
            ("Watch Card", self.watch_selected_result, "Accent.TButton"),
            ("Awards", self.open_awards_history_window, None),
            ("Hall of Fame", self.open_hall_of_fame_window, None),
            ("Achievements", self.open_achievements_window, None),
            ("Historical Records", self.open_records_ledger_window, None),
            ("Record Book", self.open_record_book_window, None),
            ("Legacy Ledger", self.open_legacy_ledger, None),
            ("Tournament History", self.open_tournament_history_window, "Accent.TButton"),
        )):
            button = ttk.Button(result_buttons, text=text, command=command, style=style) if style else ttk.Button(result_buttons, text=text, command=command)
            button.grid(row=col // 4, column=col % 4, sticky="ew", padx=3, pady=2)
        for col in range(4):
            result_buttons.columnconfigure(col, weight=1)
        results_resize = self.create_vertical_resizer(self.results_tab, initial_fraction=0.66, min_top=220, min_bottom=135)
        results_resize.pack(fill="both", expand=True)
        body = ttk.Frame(results_resize, style="Inset.TFrame")
        results_resize.add(body, minsize=220)
        panel, inner = self.section(body, "EVENT RESULTS")
        panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.results_tree = ttk.Treeview(inner, columns=("date", "company", "event", "headline", "fights", "gate", "profit"), show="headings", height=12)
        for col, text, width in (("date", "Date", 88), ("company", "Company", 130), ("event", "Event", 150), ("headline", "Main Event", 210), ("fights", "Fights", 52), ("gate", "Gate", 85), ("profit", "Profit", 85)):
            self.results_tree.heading(col, text=text)
            self.results_tree.column(col, width=width, anchor="center")
        self.results_tree.column("event", anchor="w")
        self.results_tree.column("headline", anchor="w")
        self.results_tree.bind("<<TreeviewSelect>>", lambda _e: self.show_selected_result_detail())
        self.make_tree_sortable(self.results_tree)
        self.results_tree.pack(fill="both", expand=True)
        self.results_tree.bind("<Double-1>", lambda _e: self.open_selected_result())
        retired_panel, retired = self.section(body, "RETIRED FIGHTERS")
        retired_panel.pack(side="left", fill="both", expand=True)
        retired_controls = ttk.Frame(retired, style="Inset.TFrame")
        retired_controls.pack(fill="x", pady=(0, 4))
        ttk.Label(retired_controls, text="Search", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        retired_search = ttk.Entry(retired_controls, textvariable=self.retired_search, width=20)
        retired_search.pack(side="left", fill="x", expand=True, padx=(0, 4), pady=2)
        retired_search.bind("<KeyRelease>", lambda _e: self.refresh_results())
        for label, variable, values, width in (
            ("G", self.retired_gender_filter, ("All", "Male", "Female"), 8),
            ("Division", self.retired_weight_filter, ("All", *WEIGHTS), 13),
            ("Legacy", self.retired_legacy_filter, ("All", "Former Champions", "20+ Bouts", "30+ Bouts"), 18),
        ):
            ttk.Label(retired_controls, text=label, style="Inset.TLabel").pack(side="left", padx=(4, 2))
            combo = ttk.Combobox(retired_controls, textvariable=variable, values=values, width=width, state="readonly")
            combo.pack(side="left", padx=(0, 2), pady=2)
            combo.bind("<<ComboboxSelected>>", lambda _e: self.refresh_results())
        self.retired_tree = ttk.Treeview(retired, columns=("name", "gender", "weight", "record", "age", "peak", "motivation"), show="headings", height=12)
        for col, text, width in (("name", "Fighter", 150), ("gender", "G", 38), ("weight", "Division", 95), ("record", "W-L-D", 84), ("age", "Age", 45), ("peak", "Peak OVR", 66), ("motivation", "Mot", 45)):
            self.retired_tree.heading(col, text=text)
            self.retired_tree.column(col, width=width, anchor="center")
        self.retired_tree.column("name", anchor="w")
        self.make_tree_sortable(self.retired_tree)
        retired_scroll = ttk.Scrollbar(retired, orient="vertical", command=self.retired_tree.yview)
        self.retired_tree.configure(yscrollcommand=retired_scroll.set)
        retired_scroll.pack(side="right", fill="y")
        self.retired_tree.pack(fill="both", expand=True)
        self.retired_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.retired_tree, "name"))
        ttk.Button(retired, text="Offer Comeback Deal", command=self.unretire_selected_fighter).pack(anchor="e", pady=4)
        detail_panel, detail = self.section(results_resize, "DETAIL")
        results_resize.add(detail_panel, minsize=135)
        self.result_detail_cards = {}
        result_metrics = ttk.Frame(detail, style="Inset.TFrame")
        result_metrics.pack(fill="x", padx=4, pady=(0, 5))
        for key, title, hint in (
            ("date", "DATE", "Recorded event date"),
            ("main", "MAIN EVENT", "Headline pairing"),
            ("fights", "BOUTS", "Stored card size"),
            ("profit", "RESULT", "Recorded gate outcome"),
        ):
            card = ttk.Frame(result_metrics, style="Panel.TFrame")
            card.pack(side="left", fill="both", expand=True, padx=2, pady=2)
            ttk.Label(card, text=title, style="Section.TLabel", anchor="center").pack(fill="x")
            value = ttk.Label(card, text="—", style="Panel.TLabel", anchor="center", font=("Tahoma", 9, "bold"), wraplength=150)
            value.pack(fill="x", padx=3, pady=(4, 1))
            note = ttk.Label(card, text=hint, style="Panel.TLabel", anchor="center", wraplength=150)
            note.pack(fill="x", padx=3, pady=(0, 4))
            self.result_detail_cards[key] = (value, note)
        self.results_text = tk.Text(detail, wrap="word", font=("Courier New", 9), bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=10)
        self.results_text.pack(fill="both", expand=True)
        self.results_action_notice = ttk.Label(
            detail, text="Select a recorded event to inspect or replay its retained card.",
            style="Inset.TLabel", anchor="w", justify="left", wraplength=620,
        )
        self.results_action_notice.pack(fill="x", pady=(5, 0))

    def build_company_editor_tab(self):
        self.screen_header(self.company_editor_tab, "COMPANY EDITOR", "Belts, rules, broadcasters, and weight classes")
        top = ttk.Frame(self.company_editor_tab)
        top.pack(fill="both", expand=True)
        belt_panel, belt = self.section(top, "BELTS / WEIGHT CLASSES")
        belt_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.company_belts_tree = ttk.Treeview(belt, columns=("gender", "weight", "champion", "interim", "active"), show="headings", height=12)
        for col, text, width in (("gender", "Gender", 70), ("weight", "Weight", 110), ("champion", "Champion", 165), ("interim", "Interim", 165), ("active", "Active", 60)):
            self.company_belts_tree.heading(col, text=text)
            self.company_belts_tree.column(col, width=width, anchor="center")
        self.make_tree_sortable(self.company_belts_tree)
        self.company_belts_tree.pack(fill="both", expand=True)
        self.company_belts_tree.bind("<<TreeviewSelect>>", lambda _e: self.refresh_belt_history_view())
        self.belt_history_text = tk.Text(belt, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], height=7, padx=8, pady=8)
        self.belt_history_text.pack(fill="x", pady=(6, 0))
        self.company_division_toggle_button = ttk.Button(belt, text="Open / Close Selected Division", command=self.toggle_selected_company_division)
        self.company_division_toggle_button.pack(anchor="e", pady=4)
        self.company_editor_status_var = tk.StringVar(value="Select a division to review or change its operating status.")
        self.company_editor_status_label = ttk.Label(belt, textvariable=self.company_editor_status_var, style="Inset.TLabel", anchor="w", wraplength=520)
        self.company_editor_status_label.pack(fill="x", pady=(0, 4))
        ttk.Label(belt, text="SPECIAL BELTS", style="Section.TLabel", anchor="center").pack(fill="x", pady=(5, 3))
        special_entry = ttk.Frame(belt, style="Inset.TFrame")
        special_entry.pack(fill="x", pady=(0, 3))
        self.special_belt_name_var = tk.StringVar(value="")
        ttk.Entry(special_entry, textvariable=self.special_belt_name_var).pack(side="left", fill="x", expand=True, padx=(3, 5), pady=3)
        ttk.Button(special_entry, text="Create Belt", style="Accent.TButton", command=self.create_special_belt).pack(side="left", padx=3)
        self.special_belts_tree = ttk.Treeview(belt, columns=("name", "holder", "defenses"), show="headings", height=4)
        for col, text, width in (("name", "Belt", 145), ("holder", "Holder", 175), ("defenses", "Def", 45)):
            self.special_belts_tree.heading(col, text=text)
            self.special_belts_tree.column(col, width=width, anchor="w" if col != "defenses" else "center")
        self.special_belts_tree.pack(fill="x")
        special_actions = ttk.Frame(belt, style="Inset.TFrame")
        special_actions.pack(fill="x", pady=(3, 0))
        ttk.Button(special_actions, text="Vacate", command=self.vacate_selected_special_belt).pack(side="left", padx=3)
        ttk.Button(special_actions, text="Delete", command=self.delete_selected_special_belt).pack(side="left", padx=3)
        self.special_belt_status_var = tk.StringVar(value="Create named championships such as BMF, then select them in Matchmaking.")
        ttk.Label(special_actions, textvariable=self.special_belt_status_var, style="Inset.TLabel").pack(side="left", padx=8)
        rules_panel, rules = self.section(top, "RULES / EVENT PRODUCTION PROVIDERS")
        rules_panel.pack(side="left", fill="both", expand=True)
        self.rules_text = tk.Text(rules, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], height=10)
        self.rules_text.pack(fill="both", expand=True)
        buttons = ttk.Frame(rules, style="Inset.TFrame")
        buttons.pack(fill="x", pady=4)
        for col, (text, command) in enumerate((
            ("Drug Testing", self.cycle_drug_testing),
            ("Testing Providers", self.open_drug_testing_provider_window),
            ("Testing Cases", self.open_drug_testing_cases_window),
            ("Mixed Gender", self.toggle_mixed_gender_rule),
            ("+ Round Min", lambda: self.adjust_round_length(1)),
            ("- Round Min", lambda: self.adjust_round_length(-1)),
            ("+ Reg Round", lambda: self.adjust_regular_rounds(1)),
            ("- Reg Round", lambda: self.adjust_regular_rounds(-1)),
            ("+ Title Round", lambda: self.adjust_title_rounds(1)),
            ("- Title Round", lambda: self.adjust_title_rounds(-1)),
            ("+ Fighter Target", lambda: self.adjust_active_fighter_target(50)),
            ("- Fighter Target", lambda: self.adjust_active_fighter_target(-50)),
            ("Broadcast Contracts", self.add_broadcaster),
        )):
            ttk.Button(buttons, text=text, command=command).grid(row=col // 3, column=col % 3, sticky="ew", padx=3, pady=2)
        for col in range(3):
            buttons.columnconfigure(col, weight=1)

    def build_inbox_tab(self):
        self.inbox_tab._force_viewport_width = True
        self.screen_header(self.inbox_tab, "MAIL / DECISIONS", "Owner goals, decisions, contract alerts, suspensions, and business mail")
        inbox_resize = self.create_vertical_resizer(self.inbox_tab, initial_fraction=0.72, min_top=425, min_bottom=135)
        self.inbox_resize = inbox_resize
        inbox_resize.pack(fill="both", expand=True)
        body = tk.PanedWindow(
            inbox_resize,
            orient="horizontal",
            bg=self.colors["panel"],
            bd=0,
            sashwidth=8,
            sashpad=2,
            sashrelief="raised",
            opaqueresize=True,
        )
        if not hasattr(self, "responsive_layout_panes"):
            self.responsive_layout_panes = []
        self.responsive_layout_panes.append(body)
        inbox_resize.add(body, minsize=425)
        inbox_panel, inbox = self.section(body, "INBOX")
        inbox.columnconfigure(0, weight=1)
        inbox.rowconfigure(2, weight=1)
        controls = ttk.Frame(inbox, style="Inset.TFrame")
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 6))
        self.inbox_filter = tk.StringVar(value="Open")
        self.inbox_type_filter = tk.StringVar(value="All")
        self.inbox_search = tk.StringVar(value="")
        self.inbox_sort = tk.StringVar(value="Newest")
        ttk.Label(controls, text="Search", style="Inset.TLabel").pack(side="left", padx=(5, 2))
        search = ttk.Entry(controls, textvariable=self.inbox_search, width=25)
        search.pack(side="left", fill="x", expand=True, padx=(0, 7))
        search.bind("<KeyRelease>", lambda _event: self.refresh_inbox())
        ttk.Label(controls, text="Status", style="Inset.TLabel").pack(side="left", padx=(5, 2))
        status = ttk.Combobox(controls, textvariable=self.inbox_filter, values=("Open", "Needs Action", "Unread", "Read", "Archived", "All"), state="readonly", width=13)
        status.pack(side="left", padx=(0, 7))
        ttk.Label(controls, text="Type", style="Inset.TLabel").pack(side="left", padx=(0, 2))
        self.inbox_type_box = ttk.Combobox(controls, textvariable=self.inbox_type_filter, values=("All",), state="readonly", width=16)
        self.inbox_type_box.pack(side="left", padx=(0, 7))
        ttk.Label(controls, text="Sort", style="Inset.TLabel").pack(side="left", padx=(0, 2))
        order = ttk.Combobox(controls, textvariable=self.inbox_sort, values=("Newest", "Oldest", "Priority", "Type"), state="readonly", width=9)
        order.pack(side="left")
        status.bind("<<ComboboxSelected>>", lambda _event: self.refresh_inbox())
        self.inbox_type_box.bind("<<ComboboxSelected>>", lambda _event: self.refresh_inbox())
        order.bind("<<ComboboxSelected>>", lambda _event: self.refresh_inbox())
        inbox_summary_row = ttk.Frame(inbox, style="Inset.TFrame")
        inbox_summary_row.grid(row=1, column=0, sticky="ew", padx=5, pady=(0, 4))
        self.inbox_summary = ttk.Label(inbox_summary_row, text="", style="Inset.TLabel", anchor="w")
        self.inbox_summary.pack(side="left", fill="x", expand=True)
        self.inbox_show_all_button = ttk.Button(inbox_summary_row, text="Show All Messages", command=self.show_all_inbox_messages)
        self.inbox_show_all_button.pack(side="right", padx=(6, 0))
        self.inbox_tree = ttk.Treeview(inbox, columns=("state", "date", "type", "subject"), show="headings", height=8)
        for column, text, width in (("state", "", 32), ("date", "Received", 100), ("type", "Type", 110), ("subject", "Subject", 390)):
            self.inbox_tree.heading(column, text=text)
            self.inbox_tree.column(column, width=width, anchor="w")
        self.inbox_tree.tag_configure("unread", foreground="#ffe08a")
        self.inbox_tree.tag_configure("urgent", foreground="#ff9b9b")
        self.inbox_tree.grid(row=2, column=0, sticky="nsew")
        self.inbox_tree.bind("<<TreeviewSelect>>", self.show_selected_inbox_message)
        self.inbox_tree.bind("<Double-1>", lambda _event: self.open_inbox_context())
        inbox_actions = ttk.Frame(inbox, style="Inset.TFrame")
        self.inbox_actions = inbox_actions
        inbox_actions.grid(row=3, column=0, sticky="ew", pady=(6, 0))
        for col, (text, command, style) in enumerate((
            ("Open Context", self.open_inbox_context, "Accent.TButton"),
            ("Medical Decision", self.resolve_serious_injury_inbox, None),
            ("Mark Read", self.mark_inbox_read, None),
            ("Mark Visible Read", self.mark_visible_inbox_read, None),
            ("Hide Type", self.hide_selected_inbox_type, None),
            ("Show Hidden Types", self.show_all_inbox_types, None),
            ("Resolve / Archive", self.resolve_inbox_item, None),
            ("Clear Old Mail", self.clear_old_inbox, None),
        )):
            button = ttk.Button(inbox_actions, text=text, command=command, style=style) if style else ttk.Button(inbox_actions, text=text, command=command)
            button.grid(row=col // 4, column=col % 4, sticky="ew", padx=3, pady=2)
        for col in range(4):
            inbox_actions.columnconfigure(col, weight=1)
        self.inbox_notice = ttk.Label(inbox, text="", style="Inset.TLabel", anchor="w")
        self.inbox_notice.grid(row=4, column=0, sticky="ew", padx=5, pady=(4, 0))
        self.owner_goals_summary_var = tk.StringVar(value="0 goals")
        goals_panel, goals = self.disclosure_section(
            body,
            "OWNER GOALS",
            self.owner_goals_summary_var,
            expanded=not self.rules.get("ui_owner_goals_collapsed", False),
            on_toggle=lambda expanded: self.rules.__setitem__("ui_owner_goals_collapsed", not expanded),
        )
        self.owner_goals_panel = goals_panel
        self.goals_tree = ttk.Treeview(goals, columns=("goal", "progress", "deadline", "status"), show="headings", height=8)
        for column, text, width in (("goal", "Goal", 260), ("progress", "Progress", 115), ("deadline", "Deadline", 85), ("status", "Status", 80)):
            self.goals_tree.heading(column, text=text)
            self.goals_tree.column(column, width=width, anchor="w")
        self.goals_tree.tag_configure("complete", foreground="#9de6a0")
        self.goals_tree.tag_configure("failed", foreground="#ff9b9b")
        self.goals_tree.pack(fill="both", expand=True)
        self.goals_tree.bind("<Double-1>", lambda _event: self.open_selected_owner_goal())
        self.inbox_section_split = body
        self.inbox_messages_panel = inbox_panel
        body.bind("<Configure>", lambda event: self.configure_inbox_panel_layout(event.width), add="+")
        self.configure_inbox_panel_layout(1400)
        detail_panel, detail = self.section(inbox_resize, "MESSAGE DETAIL")
        inbox_resize.add(detail_panel, minsize=135)
        self.inbox_detail_hint_var = tk.StringVar(value="Select a message above to view its full detail and available actions.")
        ttk.Label(detail, textvariable=self.inbox_detail_hint_var, style="Discovery.TLabel", anchor="w").pack(fill="x", pady=(0, 5))
        self.inbox_detail = tk.Text(detail, wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=12, pady=12)
        self.inbox_detail.pack(fill="both", expand=True)
        self.medical_decision_bar = ttk.Frame(detail, style="Inset.TFrame")
        ttk.Label(self.medical_decision_bar, text="MEDICAL DECISION", style="Inset.TLabel", font=("Tahoma", 8, "bold")).pack(side="left", padx=6)
        ttk.Button(self.medical_decision_bar, text="Surgical Repair", style="Accent.TButton", command=lambda: self.apply_inbox_medical_decision("surgery")).pack(side="left", padx=3, pady=5)
        ttk.Button(self.medical_decision_bar, text="Accelerated Rehab", command=lambda: self.apply_inbox_medical_decision("rehab")).pack(side="left", padx=3, pady=5)
        ttk.Button(self.medical_decision_bar, text="Retirement Bout", command=lambda: self.apply_inbox_medical_decision("retire")).pack(side="left", padx=3, pady=5)

    def staff_open_selected_work_receipt(self):
        """Open the selected Staff receipt as a read-only evidence brief."""
        selected = self.staff_work_tree.selection() if hasattr(self, "staff_work_tree") else ()
        if not selected:
            notice = getattr(self, "_staff_status_notice", None)
            if callable(notice):
                notice("Select a work receipt first.", warning=True)
            else:
                messagebox.showinfo("Staff receipt", "Select a work receipt first.", parent=getattr(self, "root", None))
            return None
        row = getattr(self, "staff_work_rows", {}).get(selected[0], {})
        detail_fn = getattr(self, "staff_work_details", None)
        detail = detail_fn(
            operation_id=row.get("operation_id", ""),
            work_id=row.get("work_id", ""),
        ) if callable(detail_fn) else None
        if not detail:
            notice = getattr(self, "_staff_status_notice", None)
            if callable(notice):
                notice("The selected receipt is no longer available in the current save. Refresh the evidence ledger and choose another row.", warning=True)
            else:
                messagebox.showinfo("Staff receipt", "The selected receipt is no longer available in the current save.", parent=getattr(self, "root", None))
            return None

        window = self.create_managed_window(key="staff-work-receipt", parent=getattr(self, "root", None))
        window.title("MMA Warriors - Staff Work Receipt")
        window.geometry("900x660")
        window.minsize(720, 500)
        window.configure(bg=self.colors["chrome"])
        card = detail.get("card", {}) if isinstance(detail, dict) else {}
        work = detail.get("work", {}) if isinstance(detail, dict) else {}
        brief = detail.get("brief", {}) if isinstance(detail, dict) and isinstance(detail.get("brief", {}), dict) else {}
        department = str(work.get("department", card.get("domain", "Staff")) or "Staff")
        status = str(card.get("status_label", work.get("status", "Recorded")) or "Recorded")
        if str(work.get("status", "")).lower() == "recommendation":
            status = "Advice ready"
        target = str(work.get("target_ref", card.get("target_id", "-")) or "-")
        ttk.Label(window, text=f"{department}  ·  {status}", style="Title.TLabel", anchor="w").pack(fill="x", padx=14, pady=(12, 1))
        ttk.Label(window, text=f"Target: {target}    Action: {self.STAFF_ACTION_LABELS.get(str(work.get('action_id', card.get('action', ''))), str(work.get('action_id', card.get('action', ''))))}", style="Inset.TLabel", anchor="w").pack(fill="x", padx=14, pady=(0, 8))
        body = ttk.Frame(window, style="Inset.TFrame")
        body.pack(fill="both", expand=True, padx=10, pady=(0, 8))
        scrollbar = ttk.Scrollbar(body, orient="vertical")
        text = tk.Text(body, wrap="word", yscrollcommand=scrollbar.set, font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=12, pady=10)
        scrollbar.configure(command=text.yview)
        scrollbar.pack(side="right", fill="y")
        text.pack(side="left", fill="both", expand=True)

        def value_text(value):
            if isinstance(value, (dict, list, tuple)):
                return json.dumps(value, indent=2, ensure_ascii=False, default=str)
            return str(value)

        def money_text(key, fallback_key="spend"):
            """Render receipt amounts without letting malformed legacy data crash detail."""
            raw = card.get(key, work.get(fallback_key, 0))
            if card.get(f"{key}_state") == "Unknown":
                return "Unknown"
            try:
                if isinstance(raw, bool) or raw is None or raw == "":
                    raise ValueError
                return f"${max(0, int(raw)):,}"
            except (TypeError, ValueError):
                return "Unknown"

        lines = [
            "STAFF WORK RECEIPT",
            "=" * 68,
            f"Status: {status}",
            f"Department: {department}",
            f"Action: {work.get('action_id', card.get('action', '-'))}",
            f"Target: {target}",
            f"Objective: {brief.get('objective', '-') or '-'}",
            f"Brief: {work.get('brief_id', '-')}",
            f"Boundary: {work.get('boundary', '-')}",
            f"Lead: {work.get('lead_id', '-')}",
            f"Quote / actual spend: {money_text('amount')} / {money_text('actual_spend')}",
            f"Evidence: {card.get('evidence_key', work.get('evidence_key', '-')) or '-'}",
            f"Operation: {card.get('operation_id', work.get('operation_id', '-')) or '-'}",
        ]
        if card.get("diagnostics"):
            lines.extend(("", "DATA QUALITY", "-" * 68, " • ".join(str(item) for item in card["diagnostics"])))
        if card.get("error"):
            lines.extend(("", "NEEDS ATTENTION", "-" * 68, str(card.get("error"))))

        recommendations = detail.get("recommendations", []) if isinstance(detail, dict) else []
        if recommendations:
            lines.extend(("", "RECOMMENDATION EVIDENCE", "-" * 68))
            for index, recommendation in enumerate(recommendations, 1):
                if not isinstance(recommendation, dict):
                    lines.append(f"{index}. {value_text(recommendation)}")
                    continue
                action_id = str(recommendation.get("action_id", "recommendation") or "recommendation")
                label = self.STAFF_ACTION_LABELS.get(action_id, action_id)
                lines.append(f"{index}. {label} [{recommendation.get('status', 'Recorded')}]")
                if recommendation.get("reason"):
                    lines.append(f"   Reason: {recommendation['reason']}")
                if recommendation.get("evidence_key"):
                    lines.append(f"   Evidence: {recommendation['evidence_key']}")
                result = recommendation.get("result") if isinstance(recommendation.get("result"), dict) else {}
                for key, value in result.items():
                    if key in ("alternatives", "relationship_cases"):
                        continue
                    lines.append(f"   {key.replace('_', ' ').title()}: {value_text(value)}")
                alternatives = result.get("alternatives") if isinstance(result.get("alternatives"), list) else []
                if alternatives:
                    lines.append(f"   Ranked alternatives ({len(alternatives)} shown; {result.get('eligible_alternatives', 0)} eligible):")
                    for alternative in alternatives:
                        if not isinstance(alternative, dict):
                            lines.append(f"     - {value_text(alternative)}")
                            continue
                        name = alternative.get("name", alternative.get("fighter_id", "Unknown"))
                        company_rank = alternative.get("company_rank", "-")
                        world_rank = alternative.get("world_rank", "-")
                        fit = alternative.get("fit", "-")
                        build = alternative.get("build", "-")
                        blockers = ", ".join(str(item) for item in (alternative.get("hard_blocks") or [])) or "none"
                        cautions = ", ".join(str(item) for item in (alternative.get("cautions") or [])) or "none"
                        lines.append(f"     - {name} | company {company_rank} | world {world_rank} | fit {fit} | build {build}")
                        lines.append(f"       Blockers: {blockers}; cautions: {cautions}")
                cases = result.get("relationship_cases") if isinstance(result.get("relationship_cases"), list) else []
                if cases:
                    lines.append(f"   Open relationship cases ({len(cases)}):")
                    for case in cases:
                        if isinstance(case, dict):
                            lines.append(f"     - {case.get('case_id', 'Case')} [{case.get('status', 'Open')}]: {case.get('reason', 'No reason recorded')}")
                        else:
                            lines.append(f"     - {value_text(case)}")

        lines.extend(("", "FULL STORED PAYLOAD", "-" * 68, json.dumps(detail, indent=2, ensure_ascii=False, default=str)))
        text.insert("1.0", "\n".join(lines))
        text.configure(state="disabled")
        ttk.Button(window, text="Close", command=window.destroy).pack(anchor="e", padx=14, pady=(0, 12))
        return window

    def build_staff_tab(self):
        self.screen_header(self.staff_tab, "STAFF / SCOUTING / DRUG TESTING", "Hire, fire, and negotiate staff while tracking the effect of each department")
        staff_panel, staff = self.section(self.staff_tab, "STAFF")
        staff_panel.pack(fill="both", expand=True, pady=(0, 6))
        staff_notebook = ttk.Notebook(staff)
        staff_notebook.pack(fill="both", expand=True)
        staff_roster_page = ttk.Frame(staff_notebook, style="Chrome.TFrame")
        staff_expiry_page = ttk.Frame(staff_notebook, style="Chrome.TFrame")
        staff_notebook.add(staff_roster_page, text="Roster & Market")
        staff_notebook.add(staff_expiry_page, text="Expiring Contracts")
        self.staff_contract_notebook = staff_notebook
        self.staff_tree = ttk.Treeview(staff_roster_page, columns=("name", "role", "skill", "salary", "remaining", "expiry", "morale"), show="headings", height=5)
        for col, text, width in (("name", "Name", 150), ("role", "Role", 112), ("skill", "Skill", 55), ("salary", "Salary", 84), ("remaining", "Time Left", 78), ("expiry", "Expiry", 92), ("morale", "Morale", 62)):
            self.staff_tree.heading(col, text=text)
            self.staff_tree.column(col, width=width, anchor="center")
        self.staff_tree.column("name", anchor="w")
        self.make_tree_sortable(self.staff_tree)
        self.staff_tree.pack(fill="x")
        self.staff_tree.bind("<Double-1>", lambda _event: self.open_selected_staff_profile())
        self.staff_candidate_tree = ttk.Treeview(staff_roster_page, columns=("name", "role", "skill", "salary", "term", "morale"), show="headings", height=5)
        for col, text, width in (("name", "Candidate", 150), ("role", "Role", 126), ("skill", "Skill", 55), ("salary", "Ask / mo", 84), ("term", "Term", 66), ("morale", "Morale", 62)):
            self.staff_candidate_tree.heading(col, text=text)
            self.staff_candidate_tree.column(col, width=width, anchor="center")
        self.staff_candidate_tree.column("name", anchor="w")
        self.make_tree_sortable(self.staff_candidate_tree)
        self.staff_candidate_tree.pack(fill="x", pady=(6, 0))
        self.staff_candidate_tree.bind("<Double-1>", lambda _event: self.open_selected_staff_profile(candidate=True))
        staff_buttons = ttk.Frame(staff, style="Inset.TFrame")
        staff_buttons.pack(fill="x", pady=4)
        for col, (text, command) in enumerate((
            ("Hire Candidate", self.hire_staff),
            ("Negotiate Selected", self.negotiate_selected_staff),
            ("Fire Selected", self.fire_selected_staff),
            ("Scouting Centre", lambda: self.select_tab("scouting")),
            ("Talent Relations Cases", self.open_relationship_cases_window),
            ("Run Drug Tests", self.confirm_drug_testing_commission),
            ("Testing Providers", self.open_drug_testing_provider_window),
            ("Testing Cases", self.open_drug_testing_cases_window),
            ("Hire Commentator", self.hire_commentator),
            ("View Staff Profile", self.open_selected_staff_profile),
            ("AI Staff Ledger", self.open_ai_staff_employment_window),
            ("Fighting Academy", self.open_academy_window),
        )):
            ttk.Button(staff_buttons, text=text, command=command).grid(row=col // 4, column=col % 4, sticky="ew", padx=3, pady=2)
        for col in range(4):
            staff_buttons.columnconfigure(col, weight=1)
        self.staff_action_notice = ttk.Label(
            staff, text="Staff actions, blockers and contract outcomes will appear here.",
            style="Inset.TLabel", anchor="w", justify="left", wraplength=980,
        )
        self.staff_action_notice.pack(fill="x", padx=5, pady=(0, 5))
        self.staff_expiry_tree = ttk.Treeview(staff_expiry_page, columns=("name", "role", "skill", "salary", "remaining", "expiry", "status"), show="headings", height=9)
        for col, text, width in (("name", "Staff Member", 170), ("role", "Role", 140), ("skill", "Skill", 62), ("salary", "Salary / mo", 90), ("remaining", "Time Left", 86), ("expiry", "Expiry", 100), ("status", "Status", 120)):
            self.staff_expiry_tree.heading(col, text=text)
            self.staff_expiry_tree.column(col, width=width, anchor="center")
        self.staff_expiry_tree.column("name", anchor="w")
        self.staff_expiry_tree.tag_configure("expired", background="#5c1a1a", foreground="#ffffff")
        self.staff_expiry_tree.tag_configure("final", background="#7a2f12", foreground="#ffffff")
        self.staff_expiry_tree.tag_configure("soon", background="#6b5a1e", foreground="#ffffff")
        self.make_tree_sortable(self.staff_expiry_tree)
        self.staff_expiry_tree.pack(fill="both", expand=True, padx=6, pady=6)
        self.staff_expiry_tree.bind("<Double-1>", lambda _event: self.negotiate_selected_staff(expiry=True))
        expiry_buttons = ttk.Frame(staff_expiry_page, style="Inset.TFrame")
        expiry_buttons.pack(fill="x", padx=6, pady=(0, 6))
        ttk.Button(expiry_buttons, text="Negotiate Selected", style="Accent.TButton", command=lambda: self.negotiate_selected_staff(expiry=True)).pack(side="left", padx=4)
        ttk.Button(expiry_buttons, text="Fire Selected", command=lambda: self.fire_selected_staff(expiry=True)).pack(side="left", padx=4)
        self.staff_expiry_summary = ttk.Label(expiry_buttons, text="", style="Inset.TLabel")
        self.staff_expiry_summary.pack(side="right", padx=8)

        # A compact decision surface keeps the Staff desk actionable without
        # turning the reader into an automatic workflow.  The buttons only
        # open existing review surfaces; all employment and brief mutations
        # remain behind their explicit controls below.
        staff_next_steps = ttk.Frame(staff, style="Inset.TFrame")
        staff_next_steps.pack(fill="x", pady=(0, 5))
        ttk.Label(staff_next_steps, text="NEXT STEP", style="Section.TLabel").pack(side="left", padx=(5, 8), pady=5)
        self.staff_next_step_summary = ttk.Label(
            staff_next_steps,
            text="Review contracts, evidence, or department coverage to see the most useful next action.",
            style="Inset.TLabel", anchor="w",
        )
        self.staff_next_step_summary.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)
        self.staff_next_step_primary = ttk.Button(
            staff_next_steps, text="Open", command=lambda: self.open_staff_next_step("primary"), state="disabled",
        )
        self.staff_next_step_primary.pack(side="right", padx=3, pady=3)
        self.staff_next_step_secondary = ttk.Button(
            staff_next_steps, text="Review", command=lambda: self.open_staff_next_step("secondary"), state="disabled",
        )
        self.staff_next_step_secondary.pack(side="right", padx=3, pady=3)
        self.staff_expiry_page = staff_expiry_page
        self.staff_roster_page = staff_roster_page

        # Player-owned staff policy and accountable department briefs.  This
        # is intentionally a planning surface: recommendations and draft
        # briefs never spend money or execute legacy actions by themselves.
        autonomy_panel, autonomy = self.section(self.staff_tab, "AUTONOMY & DEPARTMENT BRIEFS")
        autonomy_panel.pack(fill="x", pady=(0, 6))
        autonomy_intro = ttk.Label(
            autonomy,
            text=("Choose Manual, Recommendations, Selective Recommendations or Full Auto. "
                  "Recommendations review safe actions; Selective Recommendations uses only the actions on the brief; "
                  "Full Auto is still limited by the selected department, permissions and cash caps."),
            style="Inset.TLabel", anchor="w",
        )
        autonomy_intro.pack(fill="x", padx=8, pady=(4, 2))
        autonomy_row = ttk.Frame(autonomy, style="Inset.TFrame")
        autonomy_row.pack(fill="x", padx=6, pady=(2, 4))
        self.staff_autonomy_choice = tk.StringVar(value=self.staff_management_summary().get("mode", "Manual"))
        self.staff_department_choice = tk.StringVar(value="Company default")
        ttk.Label(autonomy_row, text="Default / department", style="Inset.TLabel").pack(side="left", padx=(2, 4))
        self.staff_department_combo = ttk.Combobox(
            autonomy_row, textvariable=self.staff_department_choice,
            values=("Company default", *self.STAFF_DEPARTMENTS), state="readonly", width=22,
        )
        self.staff_department_combo.pack(side="left", padx=(0, 5))
        self.staff_department_combo.bind("<<ComboboxSelected>>", self.staff_sync_autonomy_choice)
        ttk.Label(autonomy_row, text="Mode", style="Inset.TLabel").pack(side="left", padx=(2, 4))
        ttk.Combobox(
            autonomy_row, textvariable=self.staff_autonomy_choice,
            values=self.STAFF_AUTONOMY_MODES, state="readonly", width=24,
        ).pack(side="left", padx=(0, 5))
        ttk.Button(autonomy_row, text="Apply Policy", style="Accent.TButton", command=self.staff_apply_autonomy_from_ui).pack(side="left", padx=3)
        ttk.Button(autonomy_row, text="View Evidence Audit", command=self.open_staff_evidence_audit_window).pack(side="left", padx=3)
        ttk.Label(autonomy_row, text="Monthly cap $", style="Inset.TLabel").pack(side="left", padx=(8, 2))
        self.staff_monthly_ceiling_entry = ttk.Entry(autonomy_row, width=9)
        self.staff_monthly_ceiling_entry.insert(0, str(self.staff_management.get("monthly_ceiling", 0)))
        self.staff_monthly_ceiling_entry.pack(side="left", padx=(0, 4))
        ttk.Label(autonomy_row, text="Reserve $", style="Inset.TLabel").pack(side="left", padx=(2, 2))
        self.staff_minimum_reserve_entry = ttk.Entry(autonomy_row, width=9)
        self.staff_minimum_reserve_entry.insert(0, str(self.staff_management.get("minimum_cash_reserve", 0)))
        self.staff_minimum_reserve_entry.pack(side="left", padx=(0, 4))
        ttk.Label(autonomy_row, text="Action cap $", style="Inset.TLabel").pack(side="left", padx=(2, 2))
        self.staff_action_ceiling_entry = ttk.Entry(autonomy_row, width=9)
        self.staff_action_ceiling_entry.insert(0, str(self.staff_management.get("per_action_ceiling", {}).get("*", 0)))
        self.staff_action_ceiling_entry.pack(side="left", padx=(0, 4))
        self.staff_autonomy_status = ttk.Label(autonomy_row, text="", style="Inset.TLabel", anchor="w")
        self.staff_autonomy_status.pack(side="left", fill="x", expand=True, padx=(8, 2))
        self.staff_sync_autonomy_choice()

        brief_row = ttk.Frame(autonomy, style="Inset.TFrame")
        brief_row.pack(fill="x", padx=6, pady=(0, 4))
        self.staff_brief_department_choice = tk.StringVar(value="Marketing")
        self.staff_brief_action_choice = tk.StringVar(value="campaign_plan_review")
        self.staff_brief_objective_entry = ttk.Entry(brief_row, width=34)
        self.staff_brief_target_entry = ttk.Entry(brief_row, width=34)
        ttk.Label(brief_row, text="Department", style="Inset.TLabel").pack(side="left", padx=(2, 4))
        self.staff_brief_department_combo = ttk.Combobox(
            brief_row, textvariable=self.staff_brief_department_choice,
            values=self.STAFF_DEPARTMENTS, state="readonly", width=20,
        )
        self.staff_brief_department_combo.pack(side="left", padx=(0, 5))
        self.staff_brief_department_combo.bind("<<ComboboxSelected>>", self.staff_refresh_brief_action_choices)
        ttk.Label(brief_row, text="Objective", style="Inset.TLabel").pack(side="left", padx=(2, 4))
        self.staff_brief_objective_entry.pack(side="left", padx=(0, 5))
        ttk.Label(brief_row, text="Targets (comma separated)", style="Inset.TLabel").pack(side="left", padx=(2, 4))
        self.staff_brief_target_entry.pack(side="left", padx=(0, 5), fill="x", expand=True)
        ttk.Button(brief_row, text="Save Brief", command=self.staff_save_brief_from_ui).pack(side="left", padx=3)
        ttk.Button(brief_row, text="Commit Selected", command=self.staff_commit_selected_brief_from_ui).pack(side="left", padx=3)
        ttk.Button(brief_row, text="Requeue", command=self.staff_requeue_selected_brief_from_ui).pack(side="left", padx=3)
        ttk.Button(brief_row, text="Cancel Selected", command=self.staff_cancel_selected_brief_from_ui).pack(side="left", padx=3)

        action_row = ttk.Frame(autonomy, style="Inset.TFrame")
        action_row.pack(fill="x", padx=6, pady=(0, 4))
        ttk.Label(action_row, text="Delegated actions", style="Inset.TLabel").pack(side="left", padx=(2, 4))
        # The saved brief contract already supports an ordered allow-list. A
        # multi-select list lets the player author more than one action while
        # retaining the old StringVar as a compatibility projection for
        # callers that only inspect the first selected action.
        self.staff_brief_action_list = tk.Listbox(
            action_row, selectmode="extended", exportselection=False,
            height=3, width=32, bg=self.colors["tree"], fg=self.colors["text"],
            selectbackground=self.colors["red"], selectforeground="#ffffff",
            highlightthickness=0, relief="flat", font=("Tahoma", 9),
        )
        self.staff_brief_action_list.pack(side="left", padx=(0, 6))
        ttk.Label(
            action_row,
            text="Ctrl/Shift-select actions in order. Review is free advice; Commit may execute the selected existing actions only when that department is Full Auto.",
            style="Inset.TLabel", anchor="w",
        ).pack(side="left", fill="x", expand=True)
        self.staff_brief_target_hint = ttk.Label(
            autonomy,
            text="Targets use saved IDs; the brief never creates a new domain record.",
            style="Muted.TLabel", anchor="w",
        )
        self.staff_brief_target_hint.pack(fill="x", padx=8, pady=(0, 4))
        self.staff_refresh_brief_action_choices()

        capability_frame = ttk.Frame(autonomy, style="Inset.TFrame")
        capability_frame.pack(fill="x", padx=6, pady=(0, 4))
        self.staff_capability_tree = ttk.Treeview(
            capability_frame, columns=("department", "mode", "lead", "advice", "recommendations", "automation"),
            # Keep every registered department visible; the grid is compact
            # enough for the Staff page and must not hide Compliance/Doctor/
            # Testing rows behind an unadvertised clipped viewport.
            show="headings", height=len(self.STAFF_DEPARTMENTS),
        )
        for col, text, width in (
            ("department", "Department", 145), ("mode", "Mode", 130),
            ("lead", "Lead", 135), ("advice", "Advice", 62),
            ("recommendations", "Safe read IDs", 190), ("automation", "Auto", 55),
        ):
            self.staff_capability_tree.heading(col, text=text)
            self.staff_capability_tree.column(col, width=width, anchor="center")
        self.staff_capability_tree.column("department", anchor="w")
        self.staff_capability_tree.pack(fill="x")
        self.staff_capability_detail = ttk.Label(
            autonomy,
            text="Select a department to inspect its handler, target scope, cost/capacity boundary and stop conditions.",
            style="Inset.TLabel", anchor="w", justify="left", wraplength=1080,
        )
        self.staff_capability_detail.pack(fill="x", padx=8, pady=(2, 4))
        self.staff_capability_tree.bind("<<TreeviewSelect>>", self.staff_refresh_capability_detail)

        ttk.Label(autonomy, text="SPECIALTY READOUT (APPROVED EFFECTS + EVIDENCE)", style="Inset.TLabel", anchor="w").pack(fill="x", padx=8, pady=(2, 0))
        specialty_frame = ttk.Frame(autonomy, style="Inset.TFrame")
        specialty_frame.pack(fill="x", padx=6, pady=(0, 4))
        self.staff_specialty_tree = ttk.Treeview(
            specialty_frame, columns=("name", "role", "specialty", "strength", "classification", "effect", "progress"),
            show="headings", height=3,
        )
        for col, text, width in (
            ("name", "Staff", 150), ("role", "Role", 120), ("specialty", "Specialty", 155),
            ("strength", "Strength", 90), ("classification", "Mechanic status", 145),
            ("effect", "Approved effect", 300),
            ("progress", "Progression evidence", 180),
        ):
            self.staff_specialty_tree.heading(col, text=text)
            self.staff_specialty_tree.column(col, width=width, anchor="center")
        self.staff_specialty_tree.column("name", anchor="w")
        self.staff_specialty_tree.column("specialty", anchor="w")
        self.staff_specialty_tree.column("effect", anchor="w")
        self.staff_specialty_tree.pack(fill="x")

        ttk.Label(autonomy, text="RETENTION WATCH (OBSERVED FACTS ONLY)", style="Inset.TLabel", anchor="w").pack(fill="x", padx=8, pady=(2, 0))
        retention_frame = ttk.Frame(autonomy, style="Inset.TFrame")
        retention_frame.pack(fill="x", padx=6, pady=(0, 4))
        self.staff_retention_tree = ttk.Treeview(
            retention_frame, columns=("staff", "role", "contract", "concerns", "credits"),
            show="headings", height=3,
        )
        for col, text, width in (
            ("staff", "Staff", 150), ("role", "Role", 120), ("contract", "Months left", 86),
            ("concerns", "Observed concerns", 330), ("credits", "Credits / periods", 105),
        ):
            self.staff_retention_tree.heading(col, text=text)
            self.staff_retention_tree.column(col, width=width, anchor="center")
        self.staff_retention_tree.column("staff", anchor="w")
        self.staff_retention_tree.column("concerns", anchor="w")
        self.staff_retention_tree.pack(fill="x")

        brief_frame = ttk.Frame(autonomy, style="Inset.TFrame")
        brief_frame.pack(fill="x", padx=6, pady=(0, 4))
        self.staff_brief_tree = ttk.Treeview(
            brief_frame, columns=("department", "objective", "target", "status", "lead", "actions", "work"),
            show="headings", height=3,
        )
        for col, text, width in (
            ("department", "Department", 120), ("objective", "Objective", 270),
            ("target", "Target", 150), ("status", "Status", 84),
            ("lead", "Lead", 120), ("actions", "Actions", 72), ("work", "Work", 48),
        ):
            self.staff_brief_tree.heading(col, text=text)
            self.staff_brief_tree.column(col, width=width, anchor="center")
        self.staff_brief_tree.column("department", anchor="w")
        self.staff_brief_tree.column("objective", anchor="w")
        self.staff_brief_tree.pack(fill="x")

        ttk.Label(autonomy, text="NEEDS ATTENTION / EXCEPTIONS", style="Inset.TLabel", anchor="w").pack(fill="x", padx=8, pady=(2, 0))
        exception_frame = ttk.Frame(autonomy, style="Inset.TFrame")
        exception_frame.pack(fill="x", padx=6, pady=(0, 4))
        self.staff_exception_tree = ttk.Treeview(
            exception_frame, columns=("department", "brief", "reason", "boundary"),
            show="headings", height=2,
        )
        for col, text, width in (
            ("department", "Department", 120), ("brief", "Brief", 140),
            ("reason", "Reason", 430), ("boundary", "Boundary", 82),
        ):
            self.staff_exception_tree.heading(col, text=text)
            self.staff_exception_tree.column(col, width=width, anchor="center")
        self.staff_exception_tree.column("department", anchor="w")
        self.staff_exception_tree.column("reason", anchor="w")
        self.staff_exception_tree.pack(fill="x")

        work_header = ttk.Frame(autonomy, style="Inset.TFrame")
        work_header.pack(fill="x", padx=6, pady=(2, 0))
        ttk.Label(work_header, text="WORK RECEIPTS (READ-ONLY)", style="Inset.TLabel", anchor="w").pack(side="left", fill="x", expand=True, padx=(2, 0))
        ttk.Button(work_header, text="View selected", command=self.staff_open_selected_work_receipt).pack(side="right", padx=(4, 0))
        ttk.Label(
            autonomy,
            text="Select a receipt to inspect the full evidence, recommendation alternatives and linked cases. Nothing in this view changes the game.",
            style="Inset.TLabel", anchor="w",
        ).pack(fill="x", padx=8, pady=(0, 2))
        work_frame = ttk.Frame(autonomy, style="Inset.TFrame")
        work_frame.pack(fill="x", padx=6, pady=(0, 4))
        self.staff_work_tree = ttk.Treeview(
            work_frame, columns=("status", "action", "target", "spend", "evidence", "operation"),
            show="headings", height=3,
        )
        for col, text, width in (
            ("status", "Status", 105), ("action", "Action", 145), ("target", "Target", 135),
            ("spend", "Quote / Spend", 105), ("evidence", "Evidence", 160), ("operation", "Receipt", 145),
        ):
            self.staff_work_tree.heading(col, text=text)
            self.staff_work_tree.column(col, width=width, anchor="center")
        self.staff_work_tree.column("action", anchor="w")
        self.staff_work_tree.column("target", anchor="w")
        self.staff_work_tree.pack(fill="x")
        self.staff_work_tree.bind("<Double-1>", lambda _event: self.staff_open_selected_work_receipt())

        self.refresh_staff_management_panel()
        bonus_panel, bonus = self.section(self.staff_tab, "POST-SHOW BONUSES / STAFF EFFECTS")
        bonus_panel.pack(fill="x")
        self.staff_text = tk.Text(bonus, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
        self.staff_text.pack(fill="both", expand=True, ipady=4)

    def build_scouting_tab(self):
        self.screen_header(self.scouting_tab, "SCOUTING", "Evaluate fighters, observe upcoming bouts, search regions, and turn uncertain reports into recruitment decisions")
        self.scouting_scout_var = tk.StringVar()
        self.scouting_region_var = tk.StringVar(value=self.player_region)
        self.scouting_gender_var = tk.StringVar(value="All")
        self.scouting_weight_var = tk.StringVar(value="All")
        self.scouting_focus_var = tk.StringVar(value=self.rules.get("scouting_search_focus", "Free Agent Pool"))
        self.scouting_priority_var = tk.StringVar(value=self.rules.get("scouting_search_priority", "Balanced"))
        self.scouting_age_band_var = tk.StringVar(value="Any Age")
        self.scouting_style_var = tk.StringVar(value="All")
        self.scouting_brief_level_var = tk.StringVar(value="Standard")
        scouting_tabs = ttk.Notebook(self.scouting_tab)
        scouting_tabs.pack(fill="both", expand=True)
        target_page = ttk.Frame(scouting_tabs, style="Chrome.TFrame")
        assignment_page = ttk.Frame(scouting_tabs, style="Chrome.TFrame")
        decision_page = ttk.Frame(scouting_tabs, style="Chrome.TFrame")
        scouting_tabs.add(target_page, text="Target Board")
        scouting_tabs.add(assignment_page, text="Assignments & Searches")
        scouting_tabs.add(decision_page, text="Decision Packs")
        self.scouting_notebook = scouting_tabs
        self.scouting_target_page_ui = target_page
        self.scouting_assignment_page_ui = assignment_page
        self.scouting_decision_page_ui = decision_page

        target_panel, target = self.section(target_page, "RECRUITMENT TARGETS")
        target_panel.pack(fill="both", expand=True)
        target_filters = ttk.Frame(target, style="Inset.TFrame")
        target_filters.pack(fill="x", padx=4, pady=4)
        self.scouting_target_search = tk.StringVar()
        self.scouting_target_company = tk.StringVar(value="All")
        self.scouting_target_gender = tk.StringVar(value="All")
        self.scouting_target_weight = tk.StringVar(value="All")
        self.scouting_target_status = tk.StringVar(value="All")
        self.scouting_recommendation_mode_var = tk.StringVar(value=self.rules.get("scouting_recommendation_mode", "Balanced"))
        self.scouting_target_count_var = tk.StringVar(value="")
        self.scouting_target_page = 0
        self.scouting_target_page_size = 400
        target_search_row = ttk.Frame(target_filters, style="Inset.TFrame")
        target_search_row.pack(fill="x", pady=(0, 3))
        target_filter_row = ttk.Frame(target_filters, style="Inset.TFrame")
        target_filter_row.pack(fill="x")
        search_label = ttk.Label(target_search_row, text="Search", style="Inset.TLabel")
        search_label.pack(side="left", padx=(4, 2))
        search_entry = ttk.Entry(target_search_row, textvariable=self.scouting_target_search, width=22)
        search_entry.pack(side="left", padx=(0, 6))
        search_entry.bind("<KeyRelease>", lambda _event: self.schedule_scouting_target_refresh())
        self.attach_tooltip(search_label, "Find fighters by name or current company.")
        self.attach_tooltip(search_entry, "Type part of a fighter or company name. Results update while you type.")
        target_combos = (
            ("Company", self.scouting_target_company, (), 20),
            ("Gender", self.scouting_target_gender, ("All", "Male", "Female"), 9),
            ("Division", self.scouting_target_weight, ("All", *WEIGHTS), 14),
            ("Intel", self.scouting_target_status, ("All", "Recommended Signings", "Monitor", "Pass", "Shortlisted", "Unscouted", "In Progress", "Scouted", "Stale", "Cancelled", "Expired", "Free Agents", "Rival Rosters"), 18),
            ("Logic", self.scouting_recommendation_mode_var, SCOUTING_RECOMMENDATION_MODES, 15),
        )
        filter_help = {
            "Company": "Limit the board to free agents, independent fighters, or one promotion's roster.",
            "Gender": "Show male fighters, female fighters, or both.",
            "Division": "Limit results to one MMA weight class.",
            "Intel": "Filter by scouting state or recommendation. Monitor means the scout sees value, but price, uncertainty, or current division need makes an immediate offer hard to justify.",
            "Logic": "Adjust how scouts turn completed reports into advice.\n\n" + "\n".join(
                f"{mode}: {SCOUTING_MODE_DESCRIPTORS[mode]}" for mode in SCOUTING_RECOMMENDATION_MODES
            ),
        }
        for label, variable, values, width in target_combos:
            row = target_search_row if label == "Company" else target_filter_row
            label_widget = ttk.Label(row, text=label, style="Inset.TLabel")
            label_widget.pack(side="left", padx=(3, 2))
            combo = ttk.Combobox(row, textvariable=variable, values=values, state="readonly", width=width)
            combo.pack(side="left", padx=(0, 5))
            if label == "Logic":
                combo.bind("<<ComboboxSelected>>", lambda _event: self.update_scouting_recommendation_mode())
            else:
                combo.bind("<<ComboboxSelected>>", lambda _event: self.reset_scouting_target_page())
            self.attach_tooltip(label_widget, filter_help[label])
            self.attach_tooltip(combo, filter_help[label])
            if label == "Company":
                self.scouting_target_company_box = combo

        self.scouting_legend_var = tk.StringVar(value="")
        scouting_legend = ttk.Label(
            target, textvariable=self.scouting_legend_var,
            style="Inset.TLabel", anchor="w", justify="left", wraplength=1450,
        )
        scouting_legend.pack(fill="x", padx=8, pady=(0, 2))
        self.refresh_scouting_legend()
        self.attach_tooltip(scouting_legend, "\n\n".join(
            [f"{verdict}: {SCOUTING_VERDICT_DESCRIPTORS[verdict]}"
             for verdict in ("RECOMMEND SIGNING", "MONITOR", "PASS", "PENDING")]
            + ["Recommendations are advisory, not restrictions. They combine projected ability, potential, market pull, "
               "where the fighter would slot into your division, asking price, and available cash."]
        ))

        # Actionable summary strip: at a glance, what the board wants you to do.
        summary_row = tk.Frame(target, bg=self.colors["panel_dark"])
        summary_row.pack(fill="x", padx=8, pady=(0, 4))
        self.scouting_board_summary_var = tk.StringVar(value="")
        tk.Label(summary_row, textvariable=self.scouting_board_summary_var, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8, "bold"), anchor="w", justify="left").pack(side="left", padx=(6, 10), pady=2)
        scouting_semantic = self.semantic_status_palette(self.colors)
        self.scouting_target_legend_labels = []
        for semantic_name, swatch_text in (("positive", "recommend"), ("warning", "monitor"), ("neutral", "pass"), ("info", "shortlisted"), ("warning", "stale")):
            swatch = tk.Label(summary_row, text="■", bg=self.colors["panel_dark"], fg=scouting_semantic.get(semantic_name, self.colors["text"]), font=("Tahoma", 9))
            swatch._semantic_status_name = semantic_name
            self.scouting_target_legend_labels.append(swatch)
            swatch.pack(side="left", padx=(6, 1))
            tk.Label(summary_row, text=swatch_text, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8)).pack(side="left")

        # Selected-target cards keep the board's key decision context visible
        # without forcing the player to parse a paragraph below the table.
        # Values are populated from the selected identity and saved report;
        # they never reveal hidden ability or create a new scouting result.
        target_card_strip = tk.Frame(target, bg=self.colors["panel_dark"])
        target_card_strip.pack(fill="x", padx=8, pady=(0, 4))
        self.scouting_target_cards = {}
        for key, label in (
            ("identity", "SELECTED TARGET"),
            ("intel", "INTEL STATUS"),
            ("advice", "SCOUT ADVICE"),
            ("market", "MARKET CONTEXT"),
        ):
            cell = tk.Frame(target_card_strip, bg=self.colors["panel"], highlightthickness=1, highlightbackground=self.colors["line"])
            cell.pack(side="left", fill="both", expand=True, padx=2, pady=2)
            tk.Label(cell, text=label, bg=self.colors["panel"], fg=self.colors["muted"], font=("Tahoma", 7, "bold"), anchor="w").pack(fill="x", padx=6, pady=(4, 1))
            value = tk.Label(cell, text="—", bg=self.colors["panel"], fg=self.colors["text"], font=("Tahoma", 9, "bold"), anchor="w", justify="left", wraplength=180)
            value.pack(fill="x", padx=6, pady=(0, 4))
            self.scouting_target_cards[key] = value

        scouting_next_steps = ttk.Frame(target, style="Inset.TFrame")
        scouting_next_steps.pack(fill="x", padx=8, pady=(0, 4))
        ttk.Label(scouting_next_steps, text="NEXT STEP", style="Section.TLabel").pack(side="left", padx=(5, 8), pady=5)
        self.scouting_next_step_summary = ttk.Label(
            scouting_next_steps,
            text="The board will explain the strongest safe review action after targets load.",
            style="Inset.TLabel", anchor="w",
        )
        self.scouting_next_step_summary.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)
        self.scouting_next_step_primary = ttk.Button(
            scouting_next_steps, text="Open", command=lambda: self.open_scouting_next_step("primary"), state="disabled",
        )
        self.scouting_next_step_primary.pack(side="right", padx=3, pady=3)
        self.scouting_next_step_secondary = ttk.Button(
            scouting_next_steps, text="Review", command=lambda: self.open_scouting_next_step("secondary"), state="disabled",
        )
        self.scouting_next_step_secondary.pack(side="right", padx=3, pady=3)

        target_tree_frame = ttk.Frame(target, style="Inset.TFrame")
        target_tree_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.scouting_target_tree = ttk.Treeview(target_tree_frame, columns=("watch", "name", "company", "gender", "division", "record", "age", "intel", "advice", "ovr", "potential", "last"), show="headings", height=15, selectmode="extended")
        for col, text, width in (("watch", "Watch", 48), ("name", "Fighter", 150), ("company", "Company", 165), ("gender", "G", 34), ("division", "Division", 88), ("record", "Record", 65), ("age", "Age", 38), ("intel", "Intel", 82), ("advice", "Scout Advice", 125), ("ovr", "OVR", 58), ("potential", "Ceiling", 62), ("last", "Last Fight", 88)):
            self.scouting_target_tree.heading(col, text=text)
            self.scouting_target_tree.column(col, width=width, anchor="center")
        self.scouting_target_tree.column("name", anchor="w")
        self.scouting_target_tree.column("company", anchor="w")
        self.make_tree_sortable(self.scouting_target_tree)
        # Shortlist/stale keep priority as deliberate user/quality signals; the
        # scout's verdict colours the rest of the board so recommendations pop.
        semantic = self.semantic_status_palette(self.colors)
        self.scouting_target_tree.tag_configure("shortlisted", foreground=semantic["info"])
        self.scouting_target_tree.tag_configure("stale", foreground=semantic["warning"])
        self.scouting_target_tree.tag_configure("advice_sign", foreground=semantic["positive"])
        self.scouting_target_tree.tag_configure("advice_monitor", foreground=semantic["warning"])
        self.scouting_target_tree.tag_configure("advice_pass", foreground=semantic["neutral"])
        target_y_scroll = ttk.Scrollbar(target_tree_frame, orient="vertical", command=self.scouting_target_tree.yview)
        target_x_scroll = ttk.Scrollbar(target_tree_frame, orient="horizontal", command=self.scouting_target_tree.xview)
        self.scouting_target_tree.configure(yscrollcommand=target_y_scroll.set, xscrollcommand=target_x_scroll.set)
        target_y_scroll.pack(side="right", fill="y")
        target_x_scroll.pack(side="bottom", fill="x")
        self.scouting_target_tree.pack(side="left", fill="both", expand=True)
        self.scouting_target_tree.bind("<Double-1>", lambda _event: self.open_selected_recruitment_target())
        self.scouting_target_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_recruitment_target_summary())
        self.attach_tree_heading_tooltips(self.scouting_target_tree, {
            "watch": "WATCH marks fighters on your persistent recruitment shortlist.",
            "name": "Double-click a fighter to open their profile. Hidden attributes remain hidden while scouting mode is active.",
            "company": "The fighter's current employer. Only free agents can enter immediate contract negotiations.",
            "gender": "M = male, F = female. Rankings and divisions remain gender-specific.",
            "division": "The fighter's current MMA competition class.",
            "record": "Overall professional win-loss-draw record.",
            "age": "Current age. Age affects development room, likely career stage, and long-term value.",
            "intel": "Unscouted: no report. In Progress: assigned. Basic: broad ranges. Observed: live-fight evidence. Full: strongest report. Stale: over one year old.",
            "advice": "RECOMMEND SIGNING means pursue now. MONITOR means useful but not an immediate value fit. PASS means the projected return does not justify the commitment today.",
            "ovr": "Your scout's estimated current overall ability range. A question mark means no reliable estimate exists.",
            "potential": "Estimated career ceiling, not guaranteed future ability. Development, activity, gym quality, age, and injuries affect whether it is reached.",
            "last": "Most recent known fight date. Long inactivity can make an otherwise complete report less dependable.",
        })
        target_nav = ttk.Frame(target, style="Inset.TFrame")
        target_nav.pack(fill="x", padx=4, pady=(0, 3))
        ttk.Button(target_nav, text="Previous Page", command=lambda: self.change_scouting_target_page(-1)).pack(side="left", padx=(0, 4))
        ttk.Button(target_nav, text="Next Page", command=lambda: self.change_scouting_target_page(1)).pack(side="left")
        ttk.Label(target_nav, textvariable=self.scouting_target_count_var, style="Inset.TLabel", anchor="center").pack(side="left", fill="x", expand=True, padx=8)
        ttk.Label(target_nav, text="All matching fighters are available across pages.", style="Inset.TLabel").pack(side="right", padx=4)
        target_actions = ttk.Frame(target, style="Inset.TFrame")
        target_actions.pack(fill="x", padx=4, pady=(0, 4))
        report_action_row = ttk.Frame(target_actions, style="Inset.TFrame")
        report_action_row.pack(fill="x", pady=(0, 3))
        target_action_row = ttk.Frame(target_actions, style="Inset.TFrame")
        target_action_row.pack(fill="x")
        assign_label = ttk.Label(report_action_row, text="Assign", style="Inset.TLabel")
        assign_label.pack(side="left", padx=(4, 2))
        self.scouting_target_scout_box = ttk.Combobox(report_action_row, textvariable=self.scouting_scout_var, values=(), state="readonly", width=22)
        self.scouting_target_scout_box.pack(side="left", padx=(0, 6))
        self.attach_tooltip(assign_label, "Choose a scout for the report. Auto Assign selects a suitable scout with a free assignment slot.")
        self.attach_tooltip(self.scouting_target_scout_box, "Each scout has limited assignment capacity. Better judging and reliability produce tighter, more dependable estimates.")
        report_help = {
            "Basic Dossier": "~$2,500, ~2 weeks. A quicker, cheaper initial report revealing broad ability and potential ranges. Out-of-region +35%, independent contractor +50%.",
            "Full Evaluation": "~$7,500, ~6 weeks. Adds dated technical estimates. Repeated high-confidence work can establish exact report-date overall ability, never a live feed or certain potential. Exact cost and capacity are shown before confirmation.",
            "Observe Next Fight": "~$4,000. Keeps the slot open until the fighter competes; live evidence improves confidence, but the report expires if they stay inactive.",
        }
        for text, kind in (("Basic Dossier", "basic"), ("Full Evaluation", "full"), ("Observe Next Fight", "observation")):
            button = ttk.Button(report_action_row, text=text, command=lambda report_kind=kind: self.start_selected_recruitment_report(report_kind))
            button.pack(side="left", padx=3)
            self.attach_tooltip(button, report_help[text])
        shortlist_button = ttk.Button(target_action_row, text="Toggle Shortlist", command=self.toggle_selected_scouting_shortlist)
        shortlist_button.pack(side="left", padx=3)
        ttk.Button(target_action_row, text="Compare Two", command=self.compare_selected_scouting_targets).pack(side="left", padx=3)
        profile_button = ttk.Button(target_action_row, text="Open Profile", command=self.open_selected_recruitment_target)
        profile_button.pack(side="right", padx=3)
        negotiate_button = ttk.Button(target_action_row, text="Negotiate", style="Accent.TButton", command=self.negotiate_selected_recruitment_target)
        negotiate_button.pack(side="right", padx=3)
        self.attach_tooltip(shortlist_button, "Add or remove the selected fighter from your persistent watch list. This does not spend money or consume a scout slot.")
        self.attach_tooltip(profile_button, "Open the complete fighter profile. Information your scouts have not uncovered remains hidden.")
        self.attach_tooltip(negotiate_button, "Approach a free agent even without a scouting report. Hidden ratings stay hidden, so signing unscouted talent carries more risk.")
        watchlist_row = ttk.Frame(target, style="Inset.TFrame")
        watchlist_row.pack(fill="x", padx=4, pady=(0, 3))
        ttk.Label(watchlist_row, text="Active watchlist", style="Inset.TLabel").pack(side="left", padx=(5, 3))
        self.scouting_watchlist_var = tk.StringVar(value="Main Watchlist")
        self.scouting_watchlist_box = ttk.Combobox(
            watchlist_row, textvariable=self.scouting_watchlist_var,
            values=(), state="readonly", width=24,
        )
        self.scouting_watchlist_box.pack(side="left", padx=(0, 5))
        self.scouting_watchlist_box.bind("<<ComboboxSelected>>", lambda _event: self.switch_selected_scouting_watchlist())
        ttk.Button(watchlist_row, text="New List", command=self.create_scouting_watchlist_from_ui).pack(side="left", padx=2)
        ttk.Button(watchlist_row, text="Rename", command=self.rename_scouting_watchlist_from_ui).pack(side="left", padx=2)
        ttk.Button(watchlist_row, text="Archive", command=self.archive_scouting_watchlist_from_ui).pack(side="left", padx=2)
        ttk.Label(
            watchlist_row,
            text="Lists keep fighter IDs and alerts; archiving never deletes reports or decision packs.",
            style="Inset.TLabel", anchor="w",
        ).pack(side="left", fill="x", expand=True, padx=(8, 4))
        self.scouting_target_status_var = tk.StringVar(value="Select a fighter to evaluate, monitor, or approach.")
        ttk.Label(target, textvariable=self.scouting_target_status_var, style="Inset.TLabel", anchor="w", justify="left", wraplength=1450).pack(fill="x", padx=8, pady=(0, 5))

        panel, bonus = self.section(assignment_page, "SCOUTING CONTROL CENTRE")
        panel.pack(fill="both", expand=True)
        scout_controls = ttk.Frame(bonus, style="Inset.TFrame")
        scout_controls.pack(fill="x", padx=4, pady=4)
        scout_brief_row = ttk.Frame(scout_controls, style="Inset.TFrame")
        scout_brief_row.pack(fill="x", pady=(0, 3))
        scout_filter_row = ttk.Frame(scout_controls, style="Inset.TFrame")
        scout_filter_row.pack(fill="x", pady=(0, 3))
        scout_action_row = ttk.Frame(scout_controls, style="Inset.TFrame")
        scout_action_row.pack(fill="x")
        for label, variable, values, width in (
            ("Scout", self.scouting_scout_var, (), 22),
            ("Region", self.scouting_region_var, REGIONS, 16),
            ("Gender", self.scouting_gender_var, ("All", "Male", "Female"), 10),
            ("Division", self.scouting_weight_var, ("All", *WEIGHTS), 15),
            ("Aim", self.scouting_focus_var, SCOUTING_SEARCH_FOCUSES, 17),
            ("Priority", self.scouting_priority_var, SCOUTING_SEARCH_PRIORITIES, 16),
            ("Age", self.scouting_age_band_var, SCOUTING_AGE_BANDS, 11),
            ("Style", self.scouting_style_var, ("All", *STYLES), 16),
            ("Level", self.scouting_brief_level_var, SCOUTING_BRIEF_LEVELS, 10),
        ):
            row = scout_brief_row if label in ("Scout", "Region", "Aim", "Priority") else scout_filter_row
            label_widget = ttk.Label(row, text=label, style="Inset.TLabel")
            label_widget.pack(side="left", padx=(5, 2))
            combo = ttk.Combobox(row, textvariable=variable, values=values, state="readonly", width=width)
            combo.pack(side="left", padx=(0, 5))
            search_help = {
                "Scout": "Assign a specific scout or let Auto Assign choose an available one.",
                "Region": "The geographical market to search. Regional knowledge and scout specialties can improve the lead.",
                "Gender": "Choose which fighter market the search should prioritize.",
                "Division": "Choose a specific weight class or search across all divisions.",
                "Aim": "Tell scouts what kind of lead to find: free agents, rival-roster targets, regional prospects, young prospects, or the broad market.",
                "Priority": "Tell scouts what to optimise inside that market: present ability, upside, value, drawing power, or a thin division.",
                "Age": "Limit the brief to a career stage. Near matches may be returned when the exact pool is thin.",
                "Style": "Prefer a specific public fighting style or search across all styles.",
                "Level": "Priority costs more and returns faster. Ongoing retains the scout slot and refreshes the brief every quarter.",
            }[label]
            self.attach_tooltip(label_widget, search_help)
            self.attach_tooltip(combo, search_help)
            if label == "Scout":
                self.scouting_scout_box = combo
        start_search_button = ttk.Button(scout_action_row, text="Start Search", style="Accent.TButton", command=self.assign_scouting)
        start_search_button.pack(side="left", padx=4)
        cancel_assignment_button = ttk.Button(scout_action_row, text="Cancel Assignment", command=self.cancel_selected_scouting_assignment)
        cancel_assignment_button.pack(side="left", padx=4)
        open_fighter_button = ttk.Button(scout_action_row, text="Open Fighter", command=self.open_selected_scouting_target)
        open_fighter_button.pack(side="left", padx=4)
        self.attach_tooltip(start_search_button, "Send the selected scout to find a new lead matching this brief. Searches cost money and occupy one assignment slot until complete.")
        self.attach_tooltip(cancel_assignment_button, "End the selected active report or talent search and release its scout slot. Spent scouting costs are not refunded.")
        self.attach_tooltip(open_fighter_button, "Open the fighter attached to the selected report. Talent searches without a completed lead have no fighter to open.")

        self.scouting_status_var = tk.StringVar(value="Select a scout and a search brief. Fighter evaluations are started from fighter profiles.")
        ttk.Label(bonus, textvariable=self.scouting_status_var, style="Inset.TLabel", anchor="w").pack(fill="x", padx=8, pady=(0, 4))
        self.scouting_auto_assign_var = tk.BooleanVar(value=self.rules.get("auto_assign_idle_scouts", True))
        auto_assign = ttk.Checkbutton(
            bonus,
            text="Automatically commission one discounted Basic Dossier per week when staff capacity is idle",
            variable=self.scouting_auto_assign_var,
            command=self.set_idle_scout_auto_assignment,
        )
        auto_assign.pack(fill="x", padx=8, pady=(0, 4))
        self.attach_tooltip(auto_assign, "When enabled, the department may commission one $1,000 home-market Basic Dossier per week (travel still applies). Explicit player briefs always retain the remaining capacity.")
        assignment_tree_frame = ttk.Frame(bonus, style="Inset.TFrame")
        assignment_tree_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.scouting_assignment_tree = ttk.Treeview(assignment_tree_frame, columns=("type", "target", "scout", "status", "due", "confidence", "advice", "cost"), show="headings", height=7, selectmode="browse")
        for col, text, width in (("type", "Assignment", 120), ("target", "Target / Region", 190), ("scout", "Scout", 145), ("status", "Status", 82), ("due", "Due", 82), ("confidence", "Confidence", 78), ("advice", "Scout Advice", 135), ("cost", "Cost", 78)):
            self.scouting_assignment_tree.heading(col, text=text)
            self.scouting_assignment_tree.column(col, width=width, anchor="center")
        self.scouting_assignment_tree.column("target", anchor="w")
        self.make_tree_sortable(self.scouting_assignment_tree)
        self.scouting_assignment_tree.tag_configure("advice_sign", foreground="#7fd694")
        self.scouting_assignment_tree.tag_configure("advice_monitor", foreground="#e6c15a")
        self.scouting_assignment_tree.tag_configure("advice_pass", foreground="#8a8f97")
        self.scouting_assignment_tree.tag_configure("assignment_pending", foreground="#9db4c0")
        assignment_y_scroll = ttk.Scrollbar(assignment_tree_frame, orient="vertical", command=self.scouting_assignment_tree.yview)
        assignment_x_scroll = ttk.Scrollbar(assignment_tree_frame, orient="horizontal", command=self.scouting_assignment_tree.xview)
        self.scouting_assignment_tree.configure(yscrollcommand=assignment_y_scroll.set, xscrollcommand=assignment_x_scroll.set)
        assignment_y_scroll.pack(side="right", fill="y")
        assignment_x_scroll.pack(side="bottom", fill="x")
        self.scouting_assignment_tree.pack(side="left", fill="both", expand=True)
        self.scouting_assignment_tree.bind("<Double-1>", lambda _event: self.open_selected_scouting_target())
        self.attach_tree_heading_tooltips(self.scouting_assignment_tree, {
            "type": "Basic, full, observation, automatic, academy-network, or regional talent-search assignment.",
            "target": "The fighter being evaluated or the market covered by a talent search.",
            "scout": "The staff member using one of their available assignment slots.",
            "status": "In Progress is active work; Complete is available intelligence; Expired means an observation ended before the fighter competed.",
            "due": "Estimated weeks remaining, or Next fight for an observation assignment.",
            "confidence": "How dependable the report is. Higher confidence narrows estimated ranges; only a full evaluation reveals exact current ratings.",
            "advice": "The scout's current recruitment conclusion, based on the completed evidence and your promotion's needs.",
            "cost": "Up-front scouting expense. Cancelling an assignment does not refund this cost.",
        })

        detail_panel, detail = self.section(assignment_page, "SCOUT RECOMMENDATION")
        detail_panel.pack(fill="x", pady=(6, 0))
        self.scouting_detail_text = tk.Text(detail, height=8, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
        self.scouting_detail_text.pack(fill="x")
        self.scouting_assignment_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_scouting_assignment())

        # Saved, evidence-linked recruitment decisions.  This is intentionally
        # a separate page from the live target board: sorting or refreshing the
        # board must never rewrite the player's comparison notes or snapshots.
        pack_panel, pack_inner = self.section(decision_page, "RECRUITMENT DECISION PACKS")
        pack_panel.pack(fill="both", expand=True)
        pack_intro = ttk.Label(
            pack_inner,
            text="Capture a two-to-four-fighter decision with dated scouting evidence. A pack is a planning record: it never signs anyone or refreshes a report for free.",
            style="Inset.TLabel", anchor="w", justify="left", wraplength=1450,
        )
        pack_intro.pack(fill="x", padx=8, pady=(3, 5))
        pack_controls = ttk.Frame(pack_inner, style="Inset.TFrame")
        pack_controls.pack(fill="x", padx=4, pady=(0, 4))
        self.scouting_pack_state_var = tk.StringVar(value="Considering")
        ttk.Label(pack_controls, text="Selected state", style="Inset.TLabel").pack(side="left", padx=(5, 3))
        self.scouting_pack_state_box = ttk.Combobox(
            pack_controls, textvariable=self.scouting_pack_state_var,
            values=("Considering", "Needs report", "Ready for negotiation", "Archived"),
            state="readonly", width=22,
        )
        self.scouting_pack_state_box.pack(side="left", padx=(0, 5))
        ttk.Button(pack_controls, text="Create from Target Selection", style="Accent.TButton", command=self.create_scouting_decision_pack_from_targets).pack(side="left", padx=3)
        ttk.Button(pack_controls, text="Rename", command=self.rename_selected_scouting_decision_pack).pack(side="left", padx=3)
        ttk.Button(pack_controls, text="Apply State", command=self.update_selected_scouting_decision_pack_state).pack(side="left", padx=3)
        ttk.Button(pack_controls, text="Add / Edit Note", command=self.edit_selected_scouting_pack_note).pack(side="left", padx=3)
        ttk.Button(pack_controls, text="Open Candidate", command=self.open_selected_scouting_pack_candidate).pack(side="right", padx=3)
        self.scouting_pack_status_var = tk.StringVar(value="Select two to four candidates on Target Board, then create a decision pack.")
        ttk.Label(pack_inner, textvariable=self.scouting_pack_status_var, style="Inset.TLabel", anchor="w", wraplength=1450).pack(fill="x", padx=8, pady=(0, 4))
        pack_tree_frame = ttk.Frame(pack_inner, style="Inset.TFrame")
        pack_tree_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.scouting_decision_pack_tree = ttk.Treeview(
            pack_tree_frame, columns=("name", "purpose", "state", "candidates", "updated"),
            show="headings", height=7, selectmode="browse",
        )
        for col, label, width in (("name", "Pack", 190), ("purpose", "Purpose", 330), ("state", "Decision", 150), ("candidates", "Candidates", 110), ("updated", "Updated", 100)):
            self.scouting_decision_pack_tree.heading(col, text=label)
            self.scouting_decision_pack_tree.column(col, width=width, anchor="center")
        self.scouting_decision_pack_tree.column("name", anchor="w")
        self.scouting_decision_pack_tree.column("purpose", anchor="w")
        pack_tree_y = ttk.Scrollbar(pack_tree_frame, orient="vertical", command=self.scouting_decision_pack_tree.yview)
        self.scouting_decision_pack_tree.configure(yscrollcommand=pack_tree_y.set)
        pack_tree_y.pack(side="right", fill="y")
        self.scouting_decision_pack_tree.pack(side="left", fill="both", expand=True)
        self.scouting_decision_pack_tree.tag_configure("archived", foreground="#8a8f97")
        self.scouting_decision_pack_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_scouting_decision_pack())
        self.attach_tree_heading_tooltips(self.scouting_decision_pack_tree, {
            "name": "A saved player decision. Rename it without changing any evidence snapshots.",
            "purpose": "Your stated recruitment question, separate from the scout's opinion.",
            "state": "Considering, Needs report, Ready for negotiation, or Archived. Ready is not an automatic signing.",
            "candidates": "Two to four ID-linked candidates; unavailable names remain as historical alternatives.",
            "updated": "Last player edit, not a report refresh date.",
        })
        candidate_frame = ttk.Frame(pack_inner, style="Inset.TFrame")
        candidate_frame.pack(fill="x", padx=4, pady=(0, 4))
        self.scouting_pack_candidate_tree = ttk.Treeview(
            candidate_frame, columns=("fighter", "current", "division", "record", "intel", "captured", "note"),
            show="headings", height=4, selectmode="browse",
        )
        for col, label, width in (("fighter", "Candidate", 180), ("current", "Current status", 150), ("division", "Division", 100), ("record", "Record", 90), ("intel", "Evidence", 125), ("captured", "Captured", 100), ("note", "Player note", 300)):
            self.scouting_pack_candidate_tree.heading(col, text=label)
            self.scouting_pack_candidate_tree.column(col, width=width, anchor="center")
        self.scouting_pack_candidate_tree.column("fighter", anchor="w")
        self.scouting_pack_candidate_tree.column("note", anchor="w")
        self.scouting_pack_candidate_tree.pack(fill="x", expand=True)
        self.scouting_pack_candidate_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_scouting_decision_pack())
        pack_detail_panel, pack_detail = self.section(pack_inner, "PACK EVIDENCE")
        pack_detail_panel.pack(fill="x", pady=(2, 0))
        self.scouting_pack_detail_text = tk.Text(pack_detail, height=8, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
        self.scouting_pack_detail_text.pack(fill="x")

    def build_finance_tab(self):
        self.screen_header(self.finance_tab, "FINANCE", "Ticketing, broadcast income, sponsorship, payroll, production, medical, tax, and ledger")
        panel, inner = self.section(self.finance_tab, "CASHFLOW")
        panel.pack(fill="both", expand=True)
        actions = ttk.Frame(inner, style="Inset.TFrame")
        actions.pack(fill="x", pady=(0, 6))
        ttk.Button(actions, text="Pitch Sponsors", command=self.pitch_sponsors).pack(side="left", padx=4)
        ttk.Button(actions, text="Negotiate Media Rights", command=self.negotiate_media_rights).pack(side="left", padx=4)
        ttk.Button(actions, text="Academy Management", command=self.open_academy_window).pack(side="left", padx=4)
        ttk.Button(actions, text="Raise Ticket Price", command=lambda: self.adjust_ticket_price(5)).pack(side="right", padx=4)
        ttk.Button(actions, text="Lower Ticket Price", command=lambda: self.adjust_ticket_price(-5)).pack(side="right", padx=4)
        self.finance_summary = ttk.Label(inner, text="", style="Panel.TLabel", justify="left")
        self.finance_summary.pack(fill="x", padx=6, pady=(0, 6))
        # Keep the full summary for auditability, but promote the four values a
        # promoter needs to decide what to do next into a compact visual strip.
        # These are read-only views populated by refresh_finance; they do not
        # introduce a second balance or forecast calculation.
        self.finance_kpi_cards = {}
        finance_kpi_row = ttk.Frame(inner, style="Inset.TFrame")
        finance_kpi_row.pack(fill="x", padx=4, pady=(0, 7))
        for key, title, detail in (
            ("cash", "CASH ON HAND", "Current player wallet"),
            ("commitments", "MONTHLY COMMITMENTS", "Office, staff, academy and upkeep"),
            ("event_income", "NEXT EVENT INCOME", "Media + active sponsor estimate"),
            ("exposure", "BOOKED EXPOSURE", "Purses + event medical reserve"),
        ):
            card = ttk.Frame(finance_kpi_row, style="Panel.TFrame")
            card.pack(side="left", fill="both", expand=True, padx=3, pady=3)
            ttk.Label(card, text=title, style="Section.TLabel", anchor="center").pack(fill="x")
            value = ttk.Label(card, text="—", style="Panel.TLabel", anchor="center", font=("Tahoma", 13, "bold"))
            value.pack(fill="x", padx=4, pady=(6, 1))
            note = ttk.Label(card, text=detail, style="Panel.TLabel", anchor="center", wraplength=190)
            note.pack(fill="x", padx=4, pady=(0, 6))
            self.finance_kpi_cards[key] = (value, note)
        self.finance_notebook = ttk.Notebook(inner)
        self.finance_notebook.pack(fill="both", expand=True)
        cashflow_page = ttk.Frame(self.finance_notebook, style="Chrome.TFrame")
        history_page = ttk.Frame(self.finance_notebook, style="Chrome.TFrame")
        investment_page = ttk.Frame(self.finance_notebook, style="Chrome.TFrame")
        self.finance_notebook.add(cashflow_page, text="Cashflow & Sponsors")
        self.finance_notebook.add(history_page, text="History & Outlook")
        self.finance_notebook.add(investment_page, text="Strategic Investments")

        runway_panel, runway_inner = self.section(history_page, "12-WEEK CASH RUNWAY — PLANNING VIEW")
        runway_panel.pack(fill="x", pady=(3, 6))
        self.finance_runway_summary = ttk.Label(
            runway_inner, text="Forecast starts from current cash. Scenario closes exclude conditional rights/sponsor receipts.",
            style="Inset.TLabel", justify="left",
        )
        self.finance_runway_summary.pack(fill="x", padx=6, pady=(0, 4))
        runway_actions = ttk.Frame(runway_inner, style="Inset.TFrame")
        runway_actions.pack(fill="x", padx=4, pady=(0, 4))
        self.finance_runway_scenario_status = ttk.Label(
            runway_actions, text="Saved snapshots are planning evidence only; they never reserve cash or move a card.",
            style="Inset.TLabel", anchor="w",
        )
        self.finance_runway_scenario_status.pack(side="left", fill="x", expand=True, padx=3)
        self.finance_runway_scenario_vars = {}
        for key, label, default in (("conservative", "Low", 0.80), ("baseline", "Base", 1.00), ("strong", "High", 1.20)):
            ttk.Label(runway_actions, text=f"{label} attendance", style="Inset.TLabel").pack(side="left", padx=(6, 2))
            variable = tk.StringVar(value=f"{default:.2f}")
            self.finance_runway_scenario_vars[key] = variable
            ttk.Spinbox(
                runway_actions, from_=0.0, to=2.0, increment=0.05, width=5,
                textvariable=variable, command=self.refresh_finance_runway,
            ).pack(side="left", padx=(0, 2))
            variable.trace_add("write", lambda *_args: self.refresh_finance_runway())
        ttk.Button(
            runway_actions, text="Save Scenario Snapshot", command=self.save_cash_runway_scenario_from_ui,
        ).pack(side="right", padx=3)
        ttk.Button(
            runway_actions, text="Review Saved Scenarios", command=self.open_cash_runway_scenarios_window,
        ).pack(side="right", padx=3)
        runway_table = ttk.Frame(runway_inner, style="Inset.TFrame")
        runway_table.pack(fill="x", expand=True)
        self.finance_runway_tree = ttk.Treeview(
            runway_table,
            columns=("week", "date", "opening", "bills", "events", "conditional", "conditional_expected", "conservative", "baseline", "strong", "event_detail"),
            show="headings", height=4,
        )
        for column, text, width in (
            ("week", "Week", 48), ("date", "Date", 96), ("opening", "Opening", 100),
            ("bills", "Bills", 90), ("events", "Event Commitments", 122), ("conditional", "Conditional max", 105),
            ("conditional_expected", "Activation estimate", 125),
            ("conservative", "80% Close", 100), ("baseline", "Base Close", 100),
            ("strong", "120% Close", 100), ("event_detail", "Cards Due", 180),
        ):
            self.finance_runway_tree.heading(column, text=text)
            self.finance_runway_tree.column(column, width=width, anchor="w" if column in ("date", "event_detail") else "e")
        self.finance_runway_tree.tag_configure("positive", foreground="#9de6a0")
        self.finance_runway_tree.tag_configure("negative", foreground="#ff9b9b")
        self.finance_runway_tree.pack(side="left", fill="x", expand=True)
        runway_x = ttk.Scrollbar(runway_table, orient="horizontal", command=self.finance_runway_tree.xview)
        runway_x.pack(side="bottom", fill="x")
        self.finance_runway_tree.configure(xscrollcommand=runway_x.set)
        self.attach_tree_heading_tooltips(self.finance_runway_tree, {
            "bills": "Recurring office/payroll/project bills and weekly academy cost due in this week.",
            "events": "Committed main-promotion card costs due on the scheduled date; child/sport wallets are excluded.",
            "conditional": "Rights and sponsor receipts that may be earned if their activation conditions are met.",
            "conditional_expected": "Read-only estimate after current sponsor activation conditions; this remains conditional and is not included in cash closes.",
            "conservative": "Projected closing cash using 80% of baseline attendance; this is a sensitivity, not a probability.",
            "baseline": "Projected closing cash using baseline attendance, excluding conditional receipts.",
            "strong": "Projected closing cash using 120% of baseline attendance, bounded by venue capacity.",
        })

        sponsor_panel, sponsor_inner = self.section(cashflow_page, "SPONSOR MARKET")
        sponsor_panel.pack(fill="x", pady=(0, 6))
        sponsor_brief = ttk.Frame(sponsor_inner, style="Inset.TFrame")
        sponsor_brief.pack(fill="x", pady=(0, 5))
        ttk.Label(sponsor_brief, text="PITCH BRIEF", style="Inset.TLabel").pack(side="left", padx=(4, 3))
        self.sponsor_pitch_brief = tk.StringVar(value="Balanced Portfolio")
        ttk.Combobox(sponsor_brief, textvariable=self.sponsor_pitch_brief,
                     values=("Balanced Portfolio", "Highest Fee", "Best Brand Fit", "Long Partnership", "Accessible Brands"),
                     state="readonly", width=20).pack(side="left", padx=3)
        ttk.Button(sponsor_brief, text="Pitch Market", style="Accent.TButton", command=self.pitch_sponsors).pack(side="left", padx=4)
        self.sponsor_portfolio_summary = ttk.Label(sponsor_brief, text="", style="Inset.TLabel", anchor="e")
        self.sponsor_portfolio_summary.pack(side="right", fill="x", expand=True, padx=5)
        self.sponsor_offer_detail = tk.Frame(sponsor_inner, bg=self.colors["panel_dark"], padx=10, pady=7)
        self.sponsor_offer_detail.pack(fill="x", pady=(0, 5))
        self.sponsor_offer_verdict = tk.Label(self.sponsor_offer_detail, text="SELECT AN OFFER", bg=self.colors["panel_dark"],
                                              fg=self.colors["gold"], font=("Impact", 13), anchor="w")
        self.sponsor_offer_verdict.pack(fill="x")
        self.sponsor_offer_numbers = tk.Label(self.sponsor_offer_detail, text="", bg=self.colors["panel_dark"],
                                              fg=self.colors["text"], font=("Tahoma", 9, "bold"), anchor="w")
        self.sponsor_offer_numbers.pack(fill="x", pady=(2, 0))
        self.sponsor_offer_reason = tk.Label(
            self.sponsor_offer_detail, text="", bg=self.colors["panel_dark"],
            fg=self.colors["muted"], font=("Tahoma", 8), anchor="w", justify="left",
        )
        self.sponsor_offer_reason.pack(fill="x", pady=(2, 0))
        self.sponsor_offer_detail.bind(
            "<Configure>",
            lambda event: self.sponsor_offer_reason.configure(wraplength=max(260, event.width - 20)),
            add="+",
        )
        sponsor_table = ttk.Frame(sponsor_inner, style="Inset.TFrame")
        sponsor_table.pack(fill="x", expand=True)
        sponsor_actions = ttk.Frame(sponsor_inner, style="Inset.TFrame")
        sponsor_actions.pack(fill="x", pady=(0, 5))
        self.sponsor_accept_button = ttk.Button(sponsor_actions, text="Accept Offer", style="Accent.TButton", command=self.accept_sponsor_offer)
        self.sponsor_accept_button.pack(side="left", padx=(0, 4))
        self.sponsor_negotiate_button = ttk.Button(sponsor_actions, text="Negotiate +12%", command=self.negotiate_sponsor_offer)
        self.sponsor_negotiate_button.pack(side="left", padx=4)
        self.sponsor_reject_button = ttk.Button(sponsor_actions, text="Reject Offer", command=self.reject_sponsor_offer)
        self.sponsor_reject_button.pack(side="left", padx=4)
        ttk.Label(sponsor_actions, text="One counter per offer; a failed counter withdraws it.", style="Inset.TLabel").pack(side="left", padx=10)
        self.sponsor_market_tree = ttk.Treeview(sponsor_table, columns=("status", "brand", "category", "fee", "term", "fit", "requirement"), show="headings", height=4)
        for column, text, width in (("status", "Status", 58), ("brand", "Brand", 145), ("category", "Category", 100), ("fee", "Per Event", 90), ("term", "Term", 62), ("fit", "Fit", 42), ("requirement", "Requirement", 290)):
            self.sponsor_market_tree.heading(column, text=text)
            self.sponsor_market_tree.column(column, width=width, anchor="w" if column in ("brand", "category", "requirement") else "center")
        semantic = self.semantic_status_palette(self.colors)
        self.sponsor_market_tree.tag_configure("offer", foreground=semantic["info"])
        self.sponsor_market_tree.tag_configure("active", foreground=semantic["positive"])
        self.sponsor_market_tree.tag_configure("risk", foreground=semantic["negative"])
        self.sponsor_market_tree.pack(side="left", fill="x", expand=True)
        self.sponsor_market_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_sponsor_offer())
        self.sponsor_market_note = ttk.Label(sponsor_inner, text="", style="Inset.TLabel", justify="left")
        self.sponsor_market_note.pack(fill="x", pady=(3, 0))
        body = ttk.Frame(cashflow_page, style="Chrome.TFrame")
        body.pack(fill="both", expand=True)
        self.finance_tree = ttk.Treeview(body, columns=("period", "opening", "revenue", "costs", "net", "ending"), show="headings", height=9)
        for column, text, width in (("period", "Period", 95), ("opening", "Opening", 115), ("revenue", "Revenue", 115), ("costs", "Costs", 115), ("net", "Net", 105), ("ending", "Ending", 115)):
            self.finance_tree.heading(column, text=text)
            self.finance_tree.column(column, width=width, anchor="e" if column != "period" else "w")
        self.finance_tree.tag_configure("positive", foreground="#9de6a0")
        self.finance_tree.tag_configure("negative", foreground="#ff9b9b")
        self.make_tree_sortable(self.finance_tree)
        self.finance_tree.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.finance_tree.bind("<<TreeviewSelect>>", self.show_selected_finance_week)
        detail_panel, detail = self.section(body, "WEEK DETAIL")
        detail_panel.pack(side="left", fill="both", expand=True)
        self.finance_detail = tk.Text(detail, wrap="word", font=("Courier New", 9), bg=self.colors["panel_dark"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=10, pady=10)
        self.finance_detail.pack(fill="both", expand=True)

        outlook_top = ttk.Frame(history_page, style="Chrome.TFrame")
        outlook_top.pack(fill="both", expand=True, pady=(3, 6))
        annual_panel, annual_inner = self.section(outlook_top, "ANNUAL PROFIT HISTORY")
        annual_panel.pack(side="left", fill="both", expand=True, padx=(0, 3))
        self.finance_annual_tree = ttk.Treeview(annual_inner, columns=("year", "events", "revenue", "costs", "net", "margin", "ending"), show="headings", height=5)
        for column, text, width in (("year", "Year", 60), ("events", "Events", 55), ("revenue", "Revenue", 100), ("costs", "Costs", 100), ("net", "Profit", 100), ("margin", "Margin", 65), ("ending", "Year-end Cash", 110)):
            self.finance_annual_tree.heading(column, text=text)
            self.finance_annual_tree.column(column, width=width, anchor="e" if column not in ("year", "events") else "center")
        self.finance_annual_tree.tag_configure("positive", foreground="#9de6a0")
        self.finance_annual_tree.tag_configure("negative", foreground="#ff9b9b")
        self.finance_annual_tree.pack(fill="both", expand=True)

        mix_panel, mix_inner = self.section(outlook_top, "12-MONTH REVENUE MIX")
        mix_panel.pack(side="left", fill="both", expand=True, padx=(3, 0))
        self.finance_mix_tree = ttk.Treeview(mix_inner, columns=("stream", "amount", "share"), show="headings", height=5)
        for column, text, width in (("stream", "Revenue Stream", 150), ("amount", "Amount", 115), ("share", "Share", 70)):
            self.finance_mix_tree.heading(column, text=text)
            self.finance_mix_tree.column(column, width=width, anchor="w" if column == "stream" else "e")
        self.finance_mix_tree.pack(fill="both", expand=True)

        outlook_bottom = ttk.Frame(history_page, style="Chrome.TFrame")
        outlook_bottom.pack(fill="both", expand=True)
        roster_panel, roster_inner = self.section(outlook_bottom, "ROSTER COST TREND")
        roster_panel.pack(side="left", fill="both", expand=True, padx=(0, 3))
        self.finance_roster_cost_tree = ttk.Treeview(roster_inner, columns=("period", "roster", "pool", "top10", "booked", "fixed"), show="headings", height=6)
        for column, text, width in (("period", "Month", 80), ("roster", "Roster", 55), ("pool", "Purse Pool", 100), ("top10", "Top 10", 95), ("booked", "Booked", 95), ("fixed", "Fixed + Projects", 110)):
            self.finance_roster_cost_tree.heading(column, text=text)
            self.finance_roster_cost_tree.column(column, width=width, anchor="e" if column != "period" else "w")
        self.finance_roster_cost_tree.pack(fill="both", expand=True)

        milestone_panel, milestone_inner = self.section(outlook_bottom, "MILESTONE PROJECTIONS")
        milestone_panel.pack(side="left", fill="both", expand=True, padx=(3, 0))
        self.finance_milestone_tree = ttk.Treeview(milestone_inner, columns=("milestone", "cash_gap", "event_gap", "eta", "blockers"), show="headings", height=6)
        for column, text, width in (("milestone", "Milestone", 135), ("cash_gap", "Cash Gap", 95), ("event_gap", "Events", 55), ("eta", "ETA", 75), ("blockers", "Other Gates", 220)):
            self.finance_milestone_tree.heading(column, text=text)
            self.finance_milestone_tree.column(column, width=width, anchor="w" if column in ("milestone", "blockers") else "center")
        self.finance_milestone_tree.pack(fill="both", expand=True)
        self.finance_outlook_note = ttk.Label(history_page, text="", style="Panel.TLabel", justify="left")
        self.finance_outlook_note.pack(fill="x", padx=6, pady=(4, 0))

        investment_panel, investment_inner = self.section(investment_page, "LATE-GAME FACILITIES, OPERATIONS, DEPARTMENTS & PRESTIGE")
        investment_panel.pack(fill="both", expand=True, pady=3)
        self.finance_investment_tree = ttk.Treeview(investment_inner, columns=("category", "project", "capital", "upkeep", "status", "requirement", "effect"), show="headings", height=10)
        for column, text, width in (("category", "Category", 95), ("project", "Project", 190), ("capital", "Capital", 100), ("upkeep", "Monthly", 90), ("status", "Status", 80), ("requirement", "Requirement", 210), ("effect", "Permanent Effect", 260)):
            self.finance_investment_tree.heading(column, text=text)
            self.finance_investment_tree.column(column, width=width, anchor="w" if column in ("category", "project", "requirement", "effect") else "center")
        self.finance_investment_tree.tag_configure("owned", foreground="#9de6a0")
        self.finance_investment_tree.tag_configure("available", foreground="#9de6ff")
        self.finance_investment_tree.pack(fill="both", expand=True)
        investment_actions = ttk.Frame(investment_inner, style="Inset.TFrame")
        investment_actions.pack(fill="x", pady=(6, 0))
        ttk.Button(investment_actions, text="Approve Selected Project", style="Accent.TButton", command=self.purchase_selected_strategic_investment).pack(side="left", padx=4)
        self.finance_investment_note = ttk.Label(investment_actions, text="Select a project to review its capital and operating commitment.", style="Inset.TLabel", justify="left")
        self.finance_investment_note.pack(side="left", fill="x", expand=True, padx=8)

    def build_roster_tab(self):
        self.screen_header(self.roster_tab, "COMPANY ROSTER", "Sort fighters, check status, and build your divisions")
        body = ttk.Frame(self.roster_tab)
        body.pack(fill="both", expand=True)

        left_panel, left = self.section(body, "FIGHTERS UNDER CONTRACT")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        top = ttk.Frame(left, style="Inset.TFrame")
        top.pack(fill="x", pady=(0, 5))
        top_primary = ttk.Frame(top, style="Inset.TFrame")
        top_primary.pack(fill="x", pady=(2, 0))
        ttk.Label(top_primary, text="Search", style="Inset.TLabel").pack(side="left")
        roster_search = ttk.Entry(top_primary, textvariable=self.roster_search, width=18)
        roster_search.pack(side="left", padx=(4, 10))
        roster_search.bind("<KeyRelease>", lambda _e: self.refresh_roster())
        ttk.Label(top_primary, text="Weight", style="Inset.TLabel").pack(side="left")
        weight = ttk.Combobox(top_primary, values=["All"] + WEIGHTS, textvariable=self.weight_filter, state="readonly", width=20)
        self.roster_weight_combo = weight
        weight.pack(side="left", padx=(4, 10))
        weight.bind("<<ComboboxSelected>>", lambda _e: self.refresh_roster())
        ttk.Label(top_primary, text="Gender", style="Inset.TLabel").pack(side="left")
        roster_gender = ttk.Combobox(top_primary, values=["All", "Male", "Female"], textvariable=self.roster_gender_filter, state="readonly", width=9)
        self.roster_gender_combo = roster_gender
        roster_gender.pack(side="left", padx=(4, 10))
        roster_gender.bind("<<ComboboxSelected>>", lambda _e: (self.refresh_player_division_filter_options("roster"), self.refresh_roster()))
        ttk.Label(top_primary, text="Status", style="Inset.TLabel").pack(side="left")
        roster_status = ttk.Combobox(top_primary, values=["All", "Ready", "Champion", "Injured", "Tired", "Expiring", "Unhappy", "Closed Division"], textvariable=self.roster_status_filter, state="readonly", width=15)
        roster_status.pack(side="left", padx=(4, 0))
        roster_status.bind("<<ComboboxSelected>>", lambda _e: self.refresh_roster())
        ttk.Button(top_primary, text="Career Goals", command=self.open_career_goals_window).pack(side="right", padx=4)
        top_ranges = ttk.Frame(top, style="Inset.TFrame")
        top_ranges.pack(fill="x", pady=(3, 2))
        for label, variable, minimum, maximum, width in (
            ("Age", self.roster_age_min, 16, 60, 4), ("to", self.roster_age_max, 16, 60, 4),
            ("OVR", self.roster_ovr_min, 0, 100, 4), ("to", self.roster_ovr_max, 0, 100, 4),
            ("Min Pop", self.roster_pop_min, 0, 100, 4),
        ):
            ttk.Label(top_ranges, text=label, style="Inset.TLabel").pack(side="left", padx=(7, 2))
            spin = ttk.Spinbox(top_ranges, from_=minimum, to=maximum, textvariable=variable, width=width, command=self.refresh_roster)
            spin.pack(side="left")
            spin.bind("<KeyRelease>", lambda _e: self.refresh_roster())
            spin.bind("<FocusOut>", lambda _e: self.refresh_roster())
        ttk.Button(top_ranges, text="Reset Filters", command=self.reset_roster_filters).pack(side="left", padx=10)
        ttk.Button(top_ranges, text="Manage Divisions", style="Accent.TButton", command=self.open_division_management_window).pack(side="right", padx=4)

        # Routine roster feedback stays on the game surface so blocked actions
        # and completed division changes do not interrupt the player with a
        # transient information dialog. The view helper retains a native
        # fallback for legacy/headless callers that do not build this page.
        self.roster_action_notice = tk.Label(
            left, text="", font=("Tahoma", 9, "bold"), anchor="w", justify="left",
            bg=self.colors["chrome"], fg=self.colors["gold"],
        )
        self.roster_action_notice.pack(fill="x", padx=2, pady=(2, 4))

        columns = ("name", "gender", "weight", "record", "age", "overall", "popularity", "momentum", "morale", "contract", "status")
        self.roster_tree = ttk.Treeview(left, columns=columns, show="headings", selectmode="browse")
        headings = ["Name", "G", "Weight", "Record", "Age", "OVR", "Pop", "Mom", "Morale", "Deal", "Status"]
        widths = [180, 38, 115, 70, 55, 55, 60, 60, 70, 65, 105]
        for col, text, width in zip(columns, headings, widths):
            self.roster_tree.heading(col, text=text)
            self.roster_tree.column(col, width=width, anchor="center")
        self.roster_tree.column("name", anchor="w")
        self.roster_tree.tag_configure("champ", foreground=self.colors["gold"])
        self.roster_tree.tag_configure("injured", foreground="#9a9a9a")
        self.roster_tree.tag_configure("expiring", background="#6b5a1e", foreground="#ffffff")
        self.roster_tree.tag_configure("closed_division", background="#5a3516", foreground="#ffd27a")
        self.make_tree_sortable(self.roster_tree)
        roster_scroll = ttk.Scrollbar(left, orient="vertical", command=self.roster_tree.yview)
        self.roster_tree.configure(yscrollcommand=roster_scroll.set)
        roster_scroll.pack(side="right", fill="y")
        self.roster_tree.pack(side="left", fill="both", expand=True)
        self.roster_tree.bind("<<TreeviewSelect>>", self.update_fighter_detail)
        self.roster_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.roster_tree, "name"))

        detail_panel, detail = self.section(body, "FIGHTER PROFILE")
        detail_panel.pack(side="left", fill="y")
        detail_panel.configure(width=330)
        detail_panel.pack_propagate(False)
        self.detail_name = ttk.Label(detail, text="Select a fighter", font=("Tahoma", 11, "bold"), style="Inset.TLabel")
        self.detail_name.pack(anchor="w", padx=8, pady=(8, 6))
        self.portrait_canvas = tk.Canvas(detail, width=104, height=104, highlightthickness=1, highlightbackground="#444444", bg="#222222")
        self.portrait_canvas.pack(anchor="w", padx=8, pady=(0, 6))
        self.detail_lines = ttk.Label(detail, text="", justify="left", style="Inset.TLabel")
        self.detail_lines.pack(anchor="w", padx=8, pady=4)
        ttk.Button(detail, text="Detailed Skills", command=self.open_detailed_skills_selected).pack(fill="x", padx=8, pady=4)
        ttk.Button(detail, text="Open Fighter Profile", style="Accent.TButton",
                   command=lambda: self.open_tree_fighter_profile(self.roster_tree, "name")).pack(fill="x", padx=8, pady=4)
        ttk.Button(detail, text="Camp Plan", command=self.choose_camp_focus_selected).pack(fill="x", padx=8, pady=4)
        ttk.Button(detail, text="Media Callout", command=self.media_callout_selected).pack(fill="x", padx=8, pady=4)
        self.skill_rows = {}
        profile_stats = (
            ("Standing", "striking"),
            ("Wrestling", "wrestling"),
            ("Ground", "grappling"),
            ("Cardio", "cardio"),
            ("Chin", "chin"),
            ("Power", "power"),
            ("TD Defence", "takedown_defence"),
            ("Ground Control", "ground_control"),
            ("Submissions", "submissions"),
            ("Sub Defence", "submission_defence"),
            ("Recovery", "recovery"),
            ("Toughness", "toughness"),
            ("Fight IQ", "fight_iq"),
            ("Finishing", "finishing_instinct"),
            ("Star", "star_quality"),
            ("Charisma", "charisma"),
            ("Pro", "professionalism"),
        )
        for label, key in profile_stats:
            row = ttk.Frame(detail, style="Inset.TFrame")
            row.pack(fill="x", padx=8, pady=3)
            ttk.Label(row, text=label, width=10, style="Inset.TLabel").pack(side="left")
            bar = ttk.Progressbar(row, maximum=100, length=150)
            bar.pack(side="left", padx=5)
            value = ttk.Label(row, text="0", width=3, style="Inset.TLabel")
            value.pack(side="left")
            self.skill_rows[key] = (bar, value)

    def build_contracts_tab(self):
        self.screen_header(self.contracts_tab, "CONTRACTS", "Expiring deals, renewal talks, and roster wage pressure")
        self.contracts_alert = tk.Label(self.contracts_tab, text="", font=("Tahoma", 10, "bold"), anchor="w",
                                         bg=self.colors["chrome"], fg=self.colors["gold"])
        self.contracts_alert.pack(fill="x", padx=2, pady=(0, 4))
        filters = ttk.Frame(self.contracts_tab, style="Inset.TFrame")
        filters.pack(fill="x", pady=(0, 4))
        ttk.Label(filters, text="Show", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        self.contracts_filter = tk.StringVar(value="All")
        filter_box = ttk.Combobox(filters, textvariable=self.contracts_filter, width=18, state="readonly",
                                  values=["All", "Expiring (<=3 mo)", "Final month", "Non-Exclusive"])
        filter_box.pack(side="left", padx=4)
        filter_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_contracts())
        contracts_notebook = ttk.Notebook(self.contracts_tab)
        contracts_notebook.pack(fill="both", expand=True)
        mma_contracts_tab = ttk.Frame(contracts_notebook, style="Chrome.TFrame")
        sport_contracts_tab = ttk.Frame(contracts_notebook, style="Chrome.TFrame")
        contracts_notebook.add(mma_contracts_tab, text="MMA Roster")
        contracts_notebook.add(sport_contracts_tab, text="Combat Sports")
        self.sport_contracts_tab = sport_contracts_tab
        panel, inner = self.section(mma_contracts_tab, "CONTRACT OVERVIEW")
        panel.pack(fill="both", expand=True)
        self.contracts_tree = ttk.Treeview(inner, columns=("name", "gender", "weight", "rank", "pop", "ovr", "remaining", "expiry", "purse", "type", "morale", "status"), show="headings", selectmode="extended")
        for col, text, width in (("name", "Fighter", 160), ("gender", "G", 34), ("weight", "Division", 96), ("rank", "Rank", 52), ("pop", "Pop", 46), ("ovr", "OVR", 46), ("remaining", "Time Left", 72), ("expiry", "Expiry", 92), ("purse", "Purse", 88), ("type", "Type", 96), ("morale", "Morale", 58), ("status", "Status", 118)):
            self.contracts_tree.heading(col, text=text)
            self.contracts_tree.column(col, width=width, anchor="center")
        self.contracts_tree.column("name", anchor="w")
        self.contracts_tree.tag_configure("expired", background="#5c1a1a", foreground="#ffffff")
        self.contracts_tree.tag_configure("final", background="#7a2f12", foreground="#ffffff")
        self.contracts_tree.tag_configure("soon", background="#6b5a1e", foreground="#ffffff")
        self.make_tree_sortable(self.contracts_tree)
        self.contracts_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.contracts_tree, "name"))
        self.contracts_tree.pack(fill="both", expand=True)
        self.contract_selected_summary = ttk.Label(
            inner,
            text="Select a fighter to review the deal, obligations and renewal context.",
            style="Inset.TLabel", justify="left", anchor="w", wraplength=980,
        )
        self.contract_selected_summary.pack(fill="x", padx=6, pady=(4, 0))
        buttons = ttk.Frame(inner, style="Inset.TFrame")
        buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(buttons, text="Negotiate Renewal", style="Accent.TButton", command=self.renew_selected_contract).pack(side="left", padx=4)
        ttk.Button(buttons, text="Review Renewal Batch", command=self.open_contract_batch_workbench).pack(side="left", padx=4)
        ttk.Button(buttons, text="Auto Negotiate Selected", command=self.auto_negotiate_selected_contracts).pack(side="left", padx=4)
        ttk.Button(buttons, text="View Profile", command=self.view_contract_profile).pack(side="left", padx=4)
        self.auto_renew_button = ttk.Button(buttons, text="", command=self.toggle_auto_renew)
        self.auto_renew_button.pack(side="left", padx=4)
        ttk.Label(buttons, text="Rows: red = expired, orange = final month, yellow = expiring soon", style="Inset.TLabel").pack(side="left", padx=12)
        self.contracts_summary = ttk.Label(buttons, text="", style="Inset.TLabel")
        self.contracts_summary.pack(side="right", padx=8)
        self.contracts_tree.bind("<<TreeviewSelect>>", lambda _event: self.show_selected_contract_summary(), add="+")

        # Child-promotion athletes carry real terms now, so they get the same
        # expiry warnings and renewal flow as the MMA roster rather than sitting
        # on invisible open-ended deals.
        self.sport_contracts_alert = tk.Label(
            sport_contracts_tab, text="", font=("Tahoma", 10, "bold"), anchor="w",
            bg=self.colors["chrome"], fg=self.colors["gold"],
        )
        self.sport_contracts_alert.pack(fill="x", padx=2, pady=(4, 4))
        sport_panel, sport_inner = self.section(sport_contracts_tab, "COMBAT SPORT CONTRACTS")
        sport_panel.pack(fill="both", expand=True)
        self.sport_contracts_tree = ttk.Treeview(
            sport_inner,
            columns=("name", "sport", "division", "gender", "age", "rating", "record", "remaining", "purse", "status"),
            show="headings", selectmode="extended",
        )
        for col, text, width in (
            ("name", "Athlete", 165), ("sport", "Sport", 120), ("division", "Division", 120), ("gender", "G", 34),
            ("age", "Age", 46), ("rating", "Sport RTG", 74), ("record", "Record", 74),
            ("remaining", "Time Left", 78), ("purse", "Purse", 88), ("status", "Status", 96),
        ):
            self.sport_contracts_tree.heading(col, text=text)
            self.sport_contracts_tree.column(col, width=width, anchor="center")
        self.sport_contracts_tree.column("name", anchor="w")
        self.sport_contracts_tree.column("sport", anchor="w")
        self.sport_contracts_tree.column("division", anchor="w")
        self.sport_contracts_tree.tag_configure("expired", background="#5c1a1a", foreground="#ffffff")
        self.sport_contracts_tree.tag_configure("final", background="#7a2f12", foreground="#ffffff")
        self.sport_contracts_tree.tag_configure("soon", background="#6b5a1e", foreground="#ffffff")
        self.make_tree_sortable(self.sport_contracts_tree)
        self.sport_contracts_tree.pack(fill="both", expand=True)
        sport_buttons = ttk.Frame(sport_inner, style="Inset.TFrame")
        sport_buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(sport_buttons, text="Negotiate Renewal", style="Accent.TButton",
                   command=self.renew_selected_sport_contract).pack(side="left", padx=4)
        ttk.Button(sport_buttons, text="Release Athlete",
                   command=self.release_selected_sport_contract).pack(side="left", padx=4)
        ttk.Label(sport_buttons, text="Rows: red = expired, orange = final month, yellow = expiring soon",
                  style="Inset.TLabel").pack(side="left", padx=12)
        self.sport_contracts_summary = ttk.Label(sport_buttons, text="", style="Inset.TLabel")
        self.sport_contracts_summary.pack(side="right", padx=8)

    def build_booking_tab(self):
        self.booking_tab._force_viewport_width = True
        booking_style = ttk.Style(self.booking_tab)
        booking_style.configure("Booking.Treeview", rowheight=32, font=("Tahoma", 9),
                                background=self.colors["panel_dark"], fieldbackground=self.colors["panel_dark"],
                                foreground=self.colors["text"], borderwidth=0)
        booking_style.configure("Booking.Treeview.Heading", font=("Tahoma", 9, "bold"), padding=(8, 9))
        booking_style.map("Booking.Treeview", background=[("selected", "#574421")],
                          foreground=[("selected", "#fff1cf")])
        booking_style.configure("Booking.TButton", font=("Tahoma", 9), padding=(10, 8))
        booking_style.configure("Booking.Accent.TButton", font=("Tahoma", 9, "bold"), padding=(10, 8))
        self.screen_header(self.booking_tab, "FIGHT SCHEDULER", "Plan the show. Find the right opponents. Build the next contenders.")
        self.show_details_summary_var = tk.StringVar(value="Unscheduled")
        header_panel, header = self.disclosure_section(
            self.booking_tab,
            "01 / SHOW DETAILS",
            self.show_details_summary_var,
            expanded=not self.rules.get("ui_show_details_collapsed", False),
            on_toggle=lambda expanded: self.rules.__setitem__("ui_show_details_collapsed", not expanded),
        )
        self.show_details_panel = header_panel
        header_panel.pack(fill="x", pady=(0, 6))
        self.schedule_status_var = tk.StringVar(value="Card has not been scheduled.")
        controls = ttk.Frame(header, style="Inset.TFrame")
        controls.pack(fill="x")
        self.show_details_controls = controls
        self.show_details_event_fields = ttk.Frame(controls, style="Inset.TFrame")
        self.show_details_location_fields = ttk.Frame(controls, style="Inset.TFrame")
        self.show_details_date_fields = ttk.Frame(controls, style="Inset.TFrame")
        self.show_details_economics_fields = ttk.Frame(controls, style="Inset.TFrame")
        self.show_details_primary_actions = ttk.Frame(controls, style="Inset.TFrame")
        self.show_details_secondary_actions = ttk.Frame(controls, style="Inset.TFrame")
        line1 = self.show_details_event_fields
        line2 = self.show_details_location_fields
        line3 = self.show_details_date_fields
        line4 = self.show_details_economics_fields
        schedule_actions = self.show_details_primary_actions
        ttk.Label(line1, text="Event", style="Inset.TLabel", width=7).pack(side="left")
        self.event_name_entry = ttk.Entry(line1, textvariable=self.event_name, width=34)
        self.event_name_entry.pack(side="left", padx=(4, 12))
        ttk.Label(line1, text="Venue", style="Inset.TLabel", width=7).pack(side="left")
        venue_box = ttk.Combobox(line1, textvariable=self.venue, values=self.available_event_venues(), state="readonly", width=24)
        venue_box.pack(side="left", padx=(4, 12))
        self.event_venue_box = venue_box
        venue_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_event_economics_forecast())
        self.attach_tooltip(venue_box, "Bigger venues seat more fans and can lift the gate, but a half-empty large room hurts atmosphere and stability. Match the venue to your drawing power.")
        schedule_btn = ttk.Button(schedule_actions, text="Schedule Show", style="Booking.Accent.TButton", command=self.schedule_event)
        schedule_btn.pack(side="right", padx=(4, 0))
        self.attach_tooltip(schedule_btn, "Lock in the card for the chosen date. A viable card needs at least one complete bout, every fighter available, and any champion's title correctly flagged.")
        ttk.Button(schedule_actions, text="Earliest Valid Date", command=self.move_booking_to_earliest_card_date).pack(side="right", padx=(4, 0))
        ttk.Button(schedule_actions, text="Watch Event", command=self.watch_due_event).pack(side="right", padx=(4, 0))
        ttk.Button(schedule_actions, text="Skip Event", command=self.skip_due_event).pack(side="right", padx=(4, 0))
        ttk.Label(line2, text="Region", style="Inset.TLabel", width=7).pack(side="left")
        region_box = ttk.Combobox(line2, textvariable=self.event_region, values=REGIONS, state="readonly", width=11)
        region_box.pack(side="left", padx=(4, 12))
        self.event_region_box = region_box
        region_box.bind("<<ComboboxSelected>>", lambda _e: (self.update_city_options(), self.refresh_event_atmosphere_forecast(), self.refresh_event_economics_forecast()))
        ttk.Label(line2, text="City", style="Inset.TLabel", width=7).pack(side="left")
        self.city_box = ttk.Combobox(line2, textvariable=self.event_city, values=REGION_CITIES["USA"], state="readonly", width=13)
        self.city_box.pack(side="left", padx=(4, 12))
        ttk.Label(line3, text="Month", style="Inset.TLabel", width=7).pack(side="left")
        event_month_box = ttk.Combobox(line3, textvariable=self.event_calendar_month, values=CALENDAR_MONTH_ABBREVIATIONS, state="readonly", width=6)
        event_month_box.pack(side="left", padx=(4, 5))
        self.event_calendar_month_box = event_month_box
        event_month_box.bind("<<ComboboxSelected>>", lambda _e: (self.sync_booking_internal_date(), self.refresh_available()))
        ttk.Label(line3, text="Year", style="Inset.TLabel", width=5).pack(side="left")
        event_year_box = ttk.Spinbox(line3, from_=GAME_START_YEAR, to=GAME_START_YEAR + 50, textvariable=self.event_year, width=6)
        event_year_box.pack(side="left", padx=(4, 12))
        self.event_year_box = event_year_box
        event_year_box.bind("<FocusOut>", lambda _e: (self.sync_booking_internal_date(), self.refresh_available()))
        event_year_box.bind("<Return>", lambda _e: (self.sync_booking_internal_date(), self.refresh_available()))
        ttk.Label(line3, text="Week", style="Inset.TLabel", width=5).pack(side="left")
        event_week_box = ttk.Combobox(line3, textvariable=self.event_week, values=(1, 2, 3, 4), state="readonly", width=4)
        event_week_box.pack(side="left", padx=(4, 12))
        self.event_week_box = event_week_box
        event_week_box.bind("<<ComboboxSelected>>", lambda _e: (self.sync_booking_internal_date(), self.refresh_available()))
        ttk.Label(line3, text="Day", style="Inset.TLabel", width=4).pack(side="left")
        event_day_box = ttk.Combobox(line3, textvariable=self.event_day_choice, values=CALENDAR_DAYS, state="readonly", width=10)
        event_day_box.pack(side="left", padx=(4, 12))
        self.event_day_box = event_day_box
        event_day_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_available())
        self.attach_tooltip(event_day_box, "The day of the week the card runs. A later day in the week means a longer camp and more recovery since the last fight; an earlier one means a shorter turnaround.")
        ttk.Label(line2, text="Provider", style="Inset.TLabel", width=7).pack(side="left")
        self.event_broadcaster_box = ttk.Combobox(line2, textvariable=self.event_broadcaster, values=["No Coverage"] + [item["name"] for item in self.broadcasters], state="readonly", width=23)
        self.event_broadcaster_box.pack(side="left", padx=(4, 0))
        self.event_broadcaster_box.bind("<<ComboboxSelected>>", self.refresh_event_broadcaster_status)
        self.attach_tooltip(self.event_broadcaster_box, "A broadcast provider adds media income and exposure that grows your popularity. 'No Coverage' means sharply reduced reach and revenue.")
        ttk.Label(line4, text="Ticket $", style="Inset.TLabel", width=8).pack(side="left")
        ticket_spin = ttk.Spinbox(
            line4, from_=EVENT_TICKET_PRICE_MIN, to=EVENT_TICKET_PRICE_MAX, increment=5,
            textvariable=self.event_ticket_price, width=6, command=self.refresh_event_economics_forecast,
        )
        ticket_spin.pack(side="left", padx=(4, 12))
        ticket_spin.configure(command=self.note_manual_event_price)
        ticket_spin.bind("<KeyRelease>", lambda _e: self.note_manual_event_price())
        ticket_spin.bind("<FocusOut>", lambda _e: self.note_manual_event_price())
        self.event_ticket_price_spin = ticket_spin
        self.attach_tooltip(ticket_spin, "Price this card's tickets. Charging near what the market will bear fills the room; going well above it empties seats and costs you gate, atmosphere and merch.")
        ttk.Label(line4, text="Production", style="Inset.TLabel", width=10).pack(side="left")
        tier_box = ttk.Combobox(line4, textvariable=self.event_production_tier, values=list(EVENT_PRODUCTION_TIER_ORDER), state="readonly", width=11)
        tier_box.pack(side="left", padx=(4, 12))
        tier_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_event_economics_forecast())
        self.event_production_tier_box = tier_box
        self.attach_tooltip(tier_box, chr(10).join(
            f"{name}: {EVENT_PRODUCTION_TIERS[name]['note']}" for name in EVENT_PRODUCTION_TIER_ORDER
        ))
        ttk.Label(line4, text="Marketing $", style="Inset.TLabel", width=11).pack(side="left")
        marketing_spin = ttk.Spinbox(
            line4, from_=0, to=EVENT_MARKETING_BUDGET_MAX, increment=2500,
            textvariable=self.event_marketing_budget, width=9, command=self.refresh_event_economics_forecast,
        )
        marketing_spin.pack(side="left", padx=(4, 12))
        marketing_spin.bind("<KeyRelease>", lambda _e: self.refresh_event_economics_forecast())
        marketing_spin.bind("<FocusOut>", lambda _e: self.refresh_event_economics_forecast())
        self.event_marketing_spin = marketing_spin
        self.attach_tooltip(marketing_spin, "Spend on promoting this card. Buys turnout and awareness, and is charged as an event cost whether or not the show sells.")
        ttk.Button(line4, text="Suggest", command=self.apply_suggested_event_economics).pack(side="left", padx=(0, 4))

        status_grid = ttk.Frame(header, style="Inset.TFrame")
        status_grid.pack(fill="x")
        self.show_details_status_grid = status_grid
        self.schedule_status = tk.Label(
            status_grid,
            textvariable=self.schedule_status_var,
            anchor="w",
            justify="left",
            bg="#252525",
            fg=self.colors["text"],
            font=("Tahoma", 9, "bold"),
            padx=6,
            pady=3,
        )
        self.schedule_status.bind("<Configure>", lambda event: self.schedule_status.configure(wraplength=max(300, event.width - 20)))
        self.event_broadcaster_status = ttk.Label(status_grid, text="", style="Inset.TLabel", anchor="w", justify="left")
        self.event_broadcaster_status.bind("<Configure>", lambda event: self.event_broadcaster_status.configure(wraplength=max(260, event.width - 14)))
        atmosphere_row = ttk.Frame(header, style="Inset.TFrame")
        atmosphere_row.pack(fill="x")
        self.event_atmosphere_status = ttk.Label(atmosphere_row, text="", style="Inset.TLabel", anchor="w", justify="left")
        self.event_atmosphere_status.pack(fill="x", expand=True, padx=4, pady=2)
        self.event_atmosphere_status.bind("<Configure>", lambda event: self.event_atmosphere_status.configure(wraplength=max(300, event.width - 14)))
        self.event_economics_status = ttk.Label(atmosphere_row, text="", style="Inset.TLabel", anchor="w", justify="left")
        self.event_economics_status.pack(fill="x", expand=True, padx=4, pady=(0, 2))
        self.event_economics_status.bind("<Configure>", lambda event: self.event_economics_status.configure(wraplength=max(300, event.width - 14)))
        self.booking_priority_var = tk.StringVar(value="BOOKING PRIORITIES | Choose a date to review roster availability.")
        priority_panel = tk.Frame(self.booking_tab, bg="#29261e", highlightbackground="#625137", highlightthickness=1)
        priority_panel.pack(fill="x", pady=(2, 10))
        tk.Frame(priority_panel, bg="#d5ad62", width=4).pack(side="left", fill="y")
        priority_content = tk.Frame(priority_panel, bg="#29261e")
        priority_content.pack(side="left", fill="both", expand=True, padx=12, pady=9)
        tk.Label(priority_content, text="MATCHMAKER'S DESK", bg="#29261e", fg="#e8c789",
                 font=("Tahoma", 9, "bold"), anchor="w").pack(fill="x", pady=(0, 4))
        booking_priority = tk.Label(priority_content, textvariable=self.booking_priority_var,
                                    bg="#29261e", fg="#eee4d2", font=("Tahoma", 9), anchor="w", justify="left")
        booking_priority.pack(fill="x", expand=True)
        booking_priority.bind("<Configure>", lambda event: booking_priority.configure(wraplength=max(240, event.width - 14)))
        ttk.Button(self.show_details_secondary_actions, text="Fanbase & Atmosphere", command=self.open_fanbase_window).pack(side="right", padx=3, pady=1)
        superfight_btn = ttk.Button(self.show_details_secondary_actions, text="★ Superfight Night", style="Accent.TButton", command=self.open_superfight_night_window)
        superfight_btn.pack(side="right", padx=3, pady=1)
        self.attach_tooltip(superfight_btn, "Promote a Crossover Superfight Night: pay rival promotions to sanction champion-vs-champion superfights (non-title, no belts change) plus prelims from your roster.")
        ttk.Button(self.show_details_secondary_actions, text="Super Events", command=self.open_company_milestones_window).pack(side="right", padx=3, pady=1)
        controls.bind("<Configure>", lambda event: self.configure_show_details_layout(event.width), add="+")
        self._show_details_layout_mode = None
        self.configure_show_details_layout(1600)

        booking_resize = self.create_vertical_resizer(self.booking_tab, initial_fraction=0.8, min_top=250, min_bottom=120)
        self.booking_resize = booking_resize
        # The booking workspace contains a dense filter/action header above
        # the fighter table. Give the nested split a real content height so a
        # narrow stacked layout cannot collapse the table to a sliver; the
        # containing page remains scrollable on short screens.
        # Wide mode starts compact; configure_booking_panel_layout raises this
        # to 720px when the fighter/card panes stack so the outer booking
        # canvas can scroll instead of clipping the explorer.
        booking_resize.configure(height=620)
        booking_resize.pack_propagate(False)
        booking_resize.pack(fill="both", expand=True)
        body = tk.PanedWindow(
            booking_resize,
            orient="horizontal",
            bg=self.colors["panel"],
            bd=0,
            sashwidth=8,
            sashpad=2,
            sashrelief="raised",
            opaqueresize=True,
        )
        if not hasattr(self, "responsive_layout_panes"):
            self.responsive_layout_panes = []
        self.responsive_layout_panes.append(body)
        booking_resize.add(body, minsize=250)
        left_panel, left = self.section(body, "02 / FIND YOUR MATCHUP")
        right_panel, right = self.section(body, "03 / DRAFT FIGHT CARD")
        self.booking_horizontal_split = body
        self.booking_available_panel = left_panel
        self.booking_card_panel = right_panel
        self._booking_layout_mode = None
        body.bind("<Configure>", lambda event: self.configure_booking_panel_layout(event.width), add="+")
        body.bind("<Map>", lambda _event: self.configure_booking_panel_layout(body.winfo_width()), add="+")
        body.bind(
            "<Map>",
            lambda _event: self.schedule_booking_layout_callback(
                body, 220, self.refresh_booking_scroll_region, "_booking_scroll_after_id"
            ),
            add="+",
        )
        body.bind("<Destroy>", lambda event: self.cancel_booking_layout_callbacks(event.widget), add="+")
        booking_resize.bind("<Destroy>", lambda event: self.cancel_booking_layout_callbacks(event.widget), add="+")
        self.booking_tab.bind("<Destroy>", lambda _event: self.cancel_booking_layout_callbacks(), add="+")
        self.configure_booking_panel_layout(1400)

        available_filters = ttk.Frame(left, style="Inset.TFrame")
        available_filters.pack(fill="x", pady=(0, 5))
        ttk.Label(available_filters, text="Search", style="Inset.TLabel").pack(side="left")
        available_search = ttk.Entry(available_filters, textvariable=self.available_search, width=16)
        available_search.pack(side="left", padx=(4, 8))
        available_search.bind("<KeyRelease>", lambda _e: self.refresh_available())
        ttk.Label(available_filters, text="Weight", style="Inset.TLabel").pack(side="left")
        available_weight = ttk.Combobox(available_filters, values=["All"] + WEIGHTS, textvariable=self.available_weight_filter, state="readonly", width=14)
        self.available_weight_combo = available_weight
        available_weight.pack(side="left", padx=(4, 8))
        available_weight.bind("<<ComboboxSelected>>", lambda _e: self.refresh_available())
        ttk.Label(available_filters, text="Gender", style="Inset.TLabel").pack(side="left")
        available_gender = ttk.Combobox(available_filters, values=["All", "Male", "Female"], textvariable=self.available_gender_filter, state="readonly", width=8)
        self.available_gender_combo = available_gender
        available_gender.pack(side="left", padx=(4, 8))
        available_gender.bind("<<ComboboxSelected>>", lambda _e: (self.refresh_player_division_filter_options("matchmaking"), self.refresh_available()))
        ttk.Label(available_filters, text="Status", style="Inset.TLabel").pack(side="left")
        available_status = ttk.Combobox(available_filters, values=["All", "Ready", "Champion", "Injured", "Tired", "Expiring", "Unhappy"], textvariable=self.available_status_filter, state="readonly", width=9)
        available_status.pack(side="left", padx=(4, 0))
        available_status.bind("<<ComboboxSelected>>", lambda _e: self.refresh_available())

        # Keep the actions that turn a selected pair into a booked bout on the
        # fighter side of the screen. On laptop widths the old right-aligned
        # buttons were effectively on the other side of the horizontal page.
        booking_actions = ttk.Frame(left, style="Inset.TFrame")
        booking_actions.pack(fill="x", pady=(0, 5))
        self.booking_actions = booking_actions
        booking_options = ttk.Frame(left, style="Inset.TFrame")
        self.booking_options = booking_options
        booking_options.pack(fill="x", pady=(0, 5))
        add_matchup_btn = ttk.Button(booking_actions, text="Add Matchup", style="Booking.Accent.TButton", command=self.add_matchup)
        add_matchup_btn.grid(row=0, column=0, sticky="ew", padx=3, pady=2)
        add_tba_btn = ttk.Button(booking_actions, text="Add TBA", style="Booking.TButton", command=self.add_tba_matchup)
        add_tba_btn.grid(row=0, column=1, sticky="ew", padx=3, pady=2)
        tournament_btn = ttk.Button(booking_actions, text="Tournament", style="Booking.TButton", command=self.add_tournament_to_card)
        tournament_btn.grid(row=0, column=2, sticky="ew", padx=3, pady=2)
        assistant_btn = ttk.Button(booking_actions, text="Suggest Matchup", style="Booking.TButton", command=self.assistant_pick_matchup)
        assistant_btn.grid(row=1, column=0, sticky="ew", padx=3, pady=2)
        compare_btn = ttk.Button(booking_actions, text="Compare Selected", style="Booking.TButton", command=self.compare_selected_available_fighters)
        compare_btn.grid(row=1, column=1, columnspan=2, sticky="ew", padx=3, pady=2)
        for column in range(3):
            booking_actions.columnconfigure(column, weight=1)
        self.booking_action_buttons = (add_matchup_btn, add_tba_btn, tournament_btn, assistant_btn, compare_btn)
        booking_actions.bind("<Configure>", lambda event: self.configure_booking_action_layout(event.width), add="+")
        self._booking_action_layout_mode = None
        self.configure_booking_action_layout(900)
        title_check = ttk.Checkbutton(booking_options, text="Title", variable=self.title_fight, command=self.toggle_divisional_title_booking)
        title_check.pack(side="left", padx=(2, 3))
        main_event_check = ttk.Checkbutton(booking_options, text="Main event", variable=self.main_event)
        main_event_check.pack(side="left", padx=3)
        self.special_belt_choice = tk.StringVar(value="None")
        special_belt_label = ttk.Label(booking_options, text="Special Belt", style="Inset.TLabel")
        special_belt_label.pack(side="left", padx=(10, 2))
        self.special_belt_box = ttk.Combobox(booking_options, textvariable=self.special_belt_choice, state="readonly", width=14)
        self.special_belt_box.pack(side="left", padx=(0, 3))
        self.special_belt_box.bind("<<ComboboxSelected>>", self.select_special_belt_booking)
        tier_label = ttk.Label(booking_options, text="Tier", style="Inset.TLabel")
        tier_label.pack(side="left", padx=(10, 2))
        tier_box = ttk.Combobox(booking_options, textvariable=self.card_tier, values=CARD_TIERS, state="readonly", width=12)
        tier_box.pack(side="left", padx=(0, 3))
        ttk.Label(booking_options, text="GP Events", style="Inset.TLabel").pack(side="left", padx=(8, 2))
        grand_prix_events_box = ttk.Combobox(
            booking_options, textvariable=self.grand_prix_event_count,
            values=(1, 2, 3, 4), state="readonly", width=5,
        )
        grand_prix_events_box.pack(side="left", padx=(0, 3))
        plan_options = ttk.Frame(left, style="Inset.TFrame")
        plan_options.pack(fill="x", pady=(0, 5))
        ttk.Label(plan_options, text="Corner A plan", style="Inset.TLabel").pack(side="left", padx=(2, 3))
        red_plan_box = ttk.Combobox(
            plan_options, textvariable=self.red_fight_plan, values=FIGHT_PLANS,
            state="readonly", width=20,
        )
        red_plan_box.pack(side="left", padx=(0, 10))
        ttk.Label(plan_options, text="Corner B plan", style="Inset.TLabel").pack(side="left", padx=(2, 3))
        blue_plan_box = ttk.Combobox(
            plan_options, textvariable=self.blue_fight_plan, values=FIGHT_PLANS,
            state="readonly", width=20,
        )
        blue_plan_box.pack(side="left", padx=(0, 3))
        workbench_tools = ttk.Frame(left, style="Inset.TFrame")
        workbench_tools.pack(fill="x", pady=(0, 5))
        ttk.Label(workbench_tools, text="Booking brief", style="Inset.TLabel").pack(side="left", padx=(2, 4))
        self.booking_workbench_emphasis_var = tk.StringVar(value="Balanced")
        workbench_emphasis = ttk.Combobox(
            workbench_tools, textvariable=self.booking_workbench_emphasis_var,
            values=("Balanced", "Sporting", "Development", "Commercial"),
            state="readonly", width=15,
        )
        workbench_emphasis.pack(side="left", padx=(0, 5))
        save_brief_btn = ttk.Button(workbench_tools, text="Save Brief", command=self.save_booking_workbench_brief_from_ui)
        save_brief_btn.pack(side="left", padx=2)
        generate_workbench_btn = ttk.Button(workbench_tools, text="Generate Alternatives", style="Booking.TButton", command=self.generate_booking_workbench_from_ui)
        generate_workbench_btn.pack(side="left", padx=2)
        medical_drafts_btn = ttk.Button(workbench_tools, text="Medical Drafts", command=self.open_booking_medical_drafts_window)
        medical_drafts_btn.pack(side="left", padx=2)
        draft_review_btn = ttk.Button(workbench_tools, text="Review Draft", command=self.open_booking_draft_review_window)
        draft_review_btn.pack(side="left", padx=2)
        self.attach_tooltip(save_brief_btn, "Save the selected fighter and emphasis as a planning brief. This changes no booking, cash, capacity, or RNG.")
        self.attach_tooltip(generate_workbench_btn, "Explicitly generate a deterministic, reviewable set of eligible opponents. Refreshing Matchmaking never generates a new proposal.")
        self.attach_tooltip(medical_drafts_btn, "Review non-binding medical planning notes. They show return and camp facts but never reserve a fighter or promise clearance.")
        self.attach_tooltip(draft_review_btn, "Review the current draft card, preserved pairings, and unresolved TBA slots without changing bookings or rerunning eligibility.")
        self.attach_tooltip(add_matchup_btn, "Book the two selected available fighters into a bout. Pick same-gender fighters in the same (or a close) division for a viable, credible fight.")
        self.attach_tooltip(add_tba_btn, "Add a bout with one side left open (To Be Announced). Reserve a slot now and fill it later from Upcoming Events once you've signed or freed an opponent.")
        self.attach_tooltip(tournament_btn, "Add a full bracket of bouts in one division. A quick way to fill a card and build a division — you'll need several same-division, same-gender fighters.")
        self.attach_tooltip(grand_prix_events_box, "For a tournament, choose how many event cards carry the bracket. A 4/8/16 field supports 1–2/1–3/1–4 cards; later stages schedule after the previous card settles.")
        self.attach_tooltip(assistant_btn, "Let your matchmaker propose a competitive, fresh pairing from your available roster — a fast route to a sensible bout.")
        self.attach_tooltip(title_check, "Book the bout for the divisional belt. Needs a champion or ranked contenders. A champion booked WITHOUT this defends no title — watch for the red warning.")
        self.attach_tooltip(main_event_check, "Flag this as the headline bout. Your main event drives hype, gate, and the media rating, so put your biggest draw or title fight on top.")
        self.attach_tooltip(compare_btn, "Open the full side-by-side fighter comparison for the two selected rows without leaving Matchmaking.")
        self.attach_tooltip(self.special_belt_box, "Attach an interim, tournament, or other special title to raise the stakes and hype of a non-divisional-title bout.")
        self.attach_tooltip(tier_box, "Card position tier (Main Card, Prelims, etc.). Lower tiers pay and cost less — stack prospects on the prelims and save stars for the main card.")
        self.attach_tooltip(red_plan_box, "Pre-fight plan for the first selected fighter. Plans alter action choice, target selection and pace, then the corner may adapt between rounds.")
        self.attach_tooltip(blue_plan_box, "Pre-fight plan for the second selected fighter. Plans never directly change the official result.")

        self.matchup_insight_summary_var = tk.StringVar(value="Click to add fighters • click a selected fighter to remove")
        insight_panel, insight = self.disclosure_section(
            left,
            "MATCHUP INSIGHT",
            self.matchup_insight_summary_var,
            expanded=not self.rules.get("ui_matchup_insight_collapsed", True),
            on_toggle=lambda expanded: self.rules.__setitem__("ui_matchup_insight_collapsed", not expanded),
        )
        self.matchup_insight_panel = insight_panel
        insight_panel.pack(fill="x", pady=(0, 4), padx=3)

        legend = tk.Frame(insight, bg=self.colors["panel_dark"])
        legend.pack(fill="x", pady=(0, 4), padx=3)
        tk.Label(legend, text="Row colour:", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8)).pack(side="left", padx=(4, 6), pady=2)
        for swatch_color, swatch_text in (
            ("#7fd694", "winning record"),
            ("#e8837a", "losing record"),
            ("#9298a1", "unavailable this date"),
        ):
            tk.Label(legend, text="■", bg=self.colors["panel_dark"], fg=swatch_color, font=("Tahoma", 9)).pack(side="left", padx=(4, 1))
            tk.Label(legend, text=swatch_text, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8)).pack(side="left", padx=(0, 4))

        self.matchmaking_notice_var = tk.StringVar(value="")
        self.matchmaking_notice = tk.Label(left, textvariable=self.matchmaking_notice_var,
                                         bg="#25332e", fg="#d4eadc", font=("Tahoma", 9),
                                         anchor="w", justify="left", padx=10, pady=9)
        self.matchmaking_notice.bind("<Configure>", lambda event: self.matchmaking_notice.configure(wraplength=max(220, event.width - 24)))
        self.matchmaking_notice.pack(fill="x", pady=(0, 4), padx=3, before=insight_panel)

        self.matchmaking_title_warning_var = tk.StringVar(value="")
        self.matchmaking_title_warning = tk.Label(
            left, textvariable=self.matchmaking_title_warning_var, anchor="w", justify="left",
            bg=self.colors["panel_dark"], fg="#ff766d", font=("Tahoma", 9, "bold"), padx=7, pady=3,
        )
        self.matchmaking_title_warning.pack(fill="x", pady=(0, 4), padx=3, before=insight_panel)

        self.matchmaking_notice_var.trace_add("write", self.sync_matchmaking_alert_visibility)
        self.matchmaking_title_warning_var.trace_add("write", self.sync_matchmaking_alert_visibility)
        self.sync_matchmaking_alert_visibility()

        self.matchmaking_history_var = tk.StringVar(value="Select one fighter to compare prior meetings with every possible opponent.")
        self.matchmaking_history = ttk.Label(insight, textvariable=self.matchmaking_history_var, style="Inset.TLabel", anchor="w", justify="left")
        self.matchmaking_history.pack(fill="x", pady=(0, 4), padx=3)
        self.matchmaking_history.bind("<Configure>", lambda event: self.matchmaking_history.configure(wraplength=max(300, event.width - 18)))

        self.matchmaking_brief_var = tk.StringVar(value="Select a fighter for a divisional recommendation and detailed booking context.")
        self.matchmaking_brief = tk.Label(
            insight, textvariable=self.matchmaking_brief_var, anchor="w", justify="left",
            bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=9,
        )
        self.matchmaking_brief.pack(fill="x", pady=(0, 4), padx=3)
        self.matchmaking_brief.bind("<Configure>", lambda event: self.matchmaking_brief.configure(wraplength=max(300, event.width - 18)))

        table_tools = ttk.Frame(left, style="Inset.TFrame")
        table_tools.pack(fill="x", pady=(0, 2), padx=3)
        self.available_columns_hint = ttk.Label(
            table_tools,
            text="ROSTER EXPLORER | Switch views for readiness, form and the full metric set.",
            style="Discovery.TLabel",
            anchor="w",
            justify="left",
        )
        self.available_columns_hint.pack(side="left", fill="x", expand=True)
        self.available_columns_hint.bind("<Configure>", lambda event: self.available_columns_hint.configure(wraplength=max(300, event.width - 18)))
        self.attach_tooltip(self.available_columns_hint, "All scouting, form, fatigue, medical-return, matchup-fit, history, and event-availability metrics remain available through the table views.")
        ttk.Label(table_tools, text="Table view", style="Inset.TLabel").pack(side="left", padx=(8, 3))
        self.available_table_view = tk.StringVar(value="Essentials")
        table_view_box = ttk.Combobox(
            table_tools,
            values=("Essentials", "Readiness", "Form & Fitness", "All 20"),
            textvariable=self.available_table_view,
            state="readonly",
            width=15,
        )
        table_view_box.pack(side="right")
        table_view_box.bind("<<ComboboxSelected>>", self.apply_matchmaking_table_view)
        self.attach_tooltip(table_view_box, "Change which fighter metrics are visible without filtering rows or losing the selected matchup. All 20 restores the complete scouting table.")

        self.available_tree = ttk.Treeview(left, style="Booking.Treeview", columns=("name", "gender", "weight", "rank", "titlepath", "record", "age", "overall", "elo", "pop", "build", "last", "form", "trend", "activity", "fatigue", "recovery", "fit", "history", "status"), show="headings", selectmode="extended", height=8)
        self.available_columns_hint.configure(
            text=f"ROSTER EXPLORER | Switch views for readiness, form and all {len(self.available_tree.cget('columns'))} metrics.")
        for col, text, width in (("name", "Name", 148), ("gender", "G", 34), ("weight", "Class", 90), ("rank", "Rank", 44), ("titlepath", "Title Path", 104), ("record", "Record", 66), ("age", "Age", 40), ("overall", "OVR", 44), ("elo", "ELO", 54), ("pop", "Pop", 42), ("build", "Build", 48), ("last", "Last Fight", 84), ("form", "Last 5 (→latest)", 82), ("trend", "Form", 56), ("activity", "Active", 50), ("fatigue", "Fatigue", 88), ("recovery", "Medical Return", 104), ("fit", "Match Fit", 66), ("history", "History", 74), ("status", "Event Availability", 132)):
            self.available_tree.heading(col, text=text)
            self.available_tree.column(col, width=width, anchor="center")
        self.available_tree.column("name", anchor="w")
        self.available_tree.column("titlepath", anchor="w")
        self.available_tree.column("history", width=128, minwidth=90)
        # Unavailable fighters are greyed out; available fighters are tinted by
        # record (green winning / red losing) so the two never look alike.
        self.available_tree.tag_configure("not_ready", foreground="#9298a1")
        self.available_tree.tag_configure("recommended", background="#554515", foreground="#ffe08a")
        self.available_tree.tag_configure("rec_win", foreground="#7fd694")
        self.available_tree.tag_configure("rec_loss", foreground="#e8837a")
        self.attach_tree_heading_tooltips(self.available_tree, {
            "rank": "Divisional rank. C = champion, #n = ranked contender, - = unranked. Pairing similar ranks makes competitive, credible fights.",
            "titlepath": "Where this fighter sits on the road to a belt (champion, owed a title shot, #1 or top-five contender, or building merit) — book title-relevant fights to move contenders up.",
            "record": "Career wins-losses-draws. Row colour: green = winning record, red = losing record, grey = unavailable on this date.",
            "overall": "Overall ability (OVR). A large OVR gap usually means a lopsided mismatch that fans and the media rate poorly.",
            "elo": "Rating earned from actual results. Two fighters with close ELOs make the most competitive, unpredictable bout.",
            "pop": "Fighter popularity. Popular names high on the card lift the gate, hype, and media rating.",
            "build": "Match build — how compelling this fighter is to book right now (form, momentum, stakes, and story).",
            "last": "Date of their last fight.",
            "form": "Wins-losses over the last five bouts (the raw recent results).",
            "trend": "Momentum read from the rankings: a win streak, rising, sliding, or steady — who's hot to book right now.",
            "activity": "How recently they competed. Long layoffs risk ring rust; booking too often risks fatigue and injury.",
            "fatigue": "Current fatigue, 0-100. 0-19 Fresh; 20-39 Manageable; 40-54 Elevated; 55-64 Tired; 65+ Unfit and cannot be booked.",
            "recovery": "Earliest medical return date after the fighter's previous bout or injury. This is separate from accumulated fatigue.",
            "fit": "Match fitness: fatigue, injury, and camp readiness. Book 'Ready' fighters — tired or injured ones underperform or can't be booked.",
            "history": "Prior meetings with the other selected fighter. Rematches and settled scores add stakes and hype.",
            "status": "Whether this fighter can be booked on the chosen date (ready, injured, tired, contract issue, or already booked).",
        })
        self.make_tree_sortable(self.available_tree)
        available_scroll = ttk.Scrollbar(left, orient="vertical", command=self.available_tree.yview)
        available_scroll_x = ttk.Scrollbar(left, orient="horizontal", command=self.available_tree.xview)
        self.available_tree.configure(yscrollcommand=available_scroll.set, xscrollcommand=available_scroll_x.set)
        available_scroll_x.pack(side="bottom", fill="x")
        available_scroll.pack(side="right", fill="y")
        self.available_tree.pack(side="left", fill="both", expand=True, pady=5)
        self.available_tree.bind("<Button-1>", self.select_matchmaking_fighter_click)
        self.available_tree.bind("<Double-1>", self.open_matchmaking_fighter_profile_click)
        self.available_tree.bind("<<TreeviewSelect>>", self.refresh_matchmaking_history_indicators, add="+")
        self.apply_matchmaking_table_view()

        self.card_summary_var = tk.StringVar(value="0 fights • Select two fighters, then choose Add Matchup.")
        self.card_summary = tk.Label(right, textvariable=self.card_summary_var, bg="#29261e", fg="#e8c789",
                                     font=("Tahoma", 10, "bold"), anchor="w", justify="left", padx=12, pady=12)
        self.card_summary.pack(fill="x", pady=(0, 8))
        self.card_summary.bind("<Configure>", lambda event: self.card_summary.configure(wraplength=max(240, event.width - 14)))
        self.card_tree = ttk.Treeview(right, style="Booking.Treeview", columns=("slot", "fight", "weight", "booking"), show="headings", height=8)
        for col, text, width in (("slot", "Slot", 82), ("fight", "Fight", 205), ("weight", "Weight", 90), ("booking", "Hype • Build • Fatigue • Medical A/B", 245)):
            self.card_tree.heading(col, text=text)
            self.card_tree.column(col, width=width, anchor="center")
        self.card_tree.column("fight", anchor="w")
        self.card_tree.column("fight", stretch=True)
        self.card_tree.column("booking", anchor="w", stretch=True)
        self.card_tree.tag_configure("non_title_champion", background="#5c1a1a", foreground="#ffffff")
        self.attach_tree_heading_tooltips(self.card_tree, {
            "slot": "Position on the card. The top row is your main event — order bouts from opener up to the headliner.",
            "fight": "The booked matchup. A red row flags a champion booked without their title on the line.",
            "weight": "Division the bout is contested at.",
            "booking": "Grouped booking information: projected hype, fight build, fatigue A/B, and medical return A/B. No page-level side-scroll is required.",
        })
        self.make_tree_sortable(self.card_tree)
        self.card_tree.pack(fill="both", expand=True, pady=5)
        self.card_tree.bind("<Double-1>", lambda _event: self.compare_selected_card_matchup())
        footer = ttk.Frame(right)
        self.card_actions = footer
        footer.pack(fill="x")
        ttk.Button(footer, text="Add Selected Matchup", style="Accent.TButton", command=self.add_matchup).grid(row=0, column=0, sticky="ew", padx=2, pady=2)
        ttk.Button(footer, text="Remove Fight", command=self.remove_matchup).grid(row=0, column=1, sticky="ew", padx=2, pady=2)
        fill_tba_btn = ttk.Button(footer, text="Fill TBA", command=self.fill_selected_tba_matchup)
        fill_tba_btn.grid(row=0, column=2, sticky="ew", padx=2, pady=2)
        title_interim_btn = ttk.Button(footer, text="Title / Interim", command=self.toggle_card_title)
        title_interim_btn.grid(row=0, column=3, sticky="ew", padx=2, pady=2)
        move_up_btn = ttk.Button(footer, text="Move Up", command=self.move_fight_up)
        move_up_btn.grid(row=1, column=0, sticky="ew", padx=2, pady=2)
        ttk.Button(footer, text="Move Down", command=self.move_fight_down).grid(row=1, column=1, sticky="ew", padx=2, pady=2)
        ttk.Button(footer, text="Clear Card", command=self.clear_card).grid(row=1, column=2, columnspan=2, sticky="ew", padx=2, pady=2)
        ttk.Button(footer, text="Review Tournament Field", command=self.review_selected_tournament_field).grid(row=2, column=0, columnspan=4, sticky="ew", padx=2, pady=2)
        for column in range(4):
            footer.columnconfigure(column, weight=1)
        self.attach_tooltip(fill_tba_btn, "Assign the selected available fighter to a highlighted TBA bout, completing a reserved slot.")
        self.attach_tooltip(title_interim_btn, "Toggle the selected bout between a title fight and an interim title fight (or off).")
        self.attach_tooltip(move_up_btn, "Reorder the selected bout. The top of the card is the main event, so move your biggest fight up.")

        upcoming_panel, upcoming = self.section(booking_resize, "UPCOMING EVENTS")
        booking_resize.add(upcoming_panel, minsize=120)
        self.upcoming_tree = ttk.Treeview(upcoming, columns=("date", "event", "venue", "region", "fights", "status"), show="headings", height=4)
        for col, text, width in (("date", "Date", 90), ("event", "Event", 205), ("venue", "Venue", 120), ("region", "Region", 110), ("fights", "Fights", 60), ("status", "Status", 90)):
            self.upcoming_tree.heading(col, text=text)
            self.upcoming_tree.column(col, width=width, anchor="center")
        self.upcoming_tree.column("event", anchor="w")
        self.make_tree_sortable(self.upcoming_tree)
        self.upcoming_tree.pack(fill="x")
        upcoming_actions = ttk.Frame(upcoming)
        upcoming_actions.pack(fill="x", pady=(4, 0))
        ttk.Button(
            upcoming_actions, text="Review Title Decision",
            command=self.review_selected_title_miss_decision,
        ).pack(side="left", padx=2)
        ttk.Button(upcoming_actions, text="Edit Selected Card", style="Accent.TButton", command=self.edit_selected_scheduled_event).pack(side="left", padx=2)
        self.cancel_card_button = ttk.Button(upcoming_actions, text="Cancel Selected Card", command=self.cancel_selected_scheduled_event)
        self.cancel_card_button.pack(side="left", padx=2)
        ttk.Label(upcoming_actions, text="Select a future show to replace TBA fighters or revise the bill.", style="Panel.TLabel").pack(side="left", padx=8)
        self.upcoming_tree.bind("<Double-1>", lambda _event: self.edit_selected_scheduled_event())
        self.upcoming_tree.bind("<<TreeviewSelect>>", self.reset_cancel_card_confirmation, add="+")

    def build_market_tab(self):
        self.screen_header(self.market_tab, "FREE AGENTS", "Scout talent and negotiate new contracts")
        panel, inner = self.section(self.market_tab, "AVAILABLE WORKERS")
        panel.pack(fill="both", expand=True, pady=(0, 8))
        filters = ttk.Frame(inner, style="Inset.TFrame")
        filters.pack(fill="x", pady=(0, 6))
        filter_primary = ttk.Frame(filters, style="Inset.TFrame")
        filter_primary.pack(fill="x", pady=(2, 0))
        ttk.Label(filter_primary, text="Search", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        market_search = ttk.Entry(filter_primary, textvariable=self.market_search, width=16)
        market_search.pack(side="left", padx=(0, 10))
        market_search.bind("<KeyRelease>", lambda _e: self.refresh_market())
        ttk.Label(filter_primary, text="Weight", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        market_weight = ttk.Combobox(filter_primary, values=["All"] + WEIGHTS, textvariable=self.market_weight_filter, state="readonly", width=18)
        market_weight.pack(side="left", padx=(0, 10))
        market_weight.bind("<<ComboboxSelected>>", lambda _e: self.refresh_market())
        ttk.Label(filter_primary, text="Gender", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        market_gender = ttk.Combobox(filter_primary, values=["All", "Male", "Female"], textvariable=self.market_gender_filter, state="readonly", width=10)
        market_gender.pack(side="left", padx=(0, 10))
        market_gender.bind("<<ComboboxSelected>>", lambda _e: self.refresh_market())
        ttk.Label(filter_primary, text="Market", style="Inset.TLabel").pack(side="left", padx=(2, 2))
        market_status = ttk.Combobox(filter_primary, values=["All", "Available", "Rival Offer", "Retiring"], textvariable=self.market_status_filter, state="readonly", width=12)
        market_status.pack(side="left", padx=(0, 10))
        market_status.bind("<<ComboboxSelected>>", lambda _e: self.refresh_market())
        ttk.Checkbutton(filter_primary, text="Closed divisions", variable=self.market_show_closed_divisions,
                        command=self.refresh_market).pack(side="left", padx=(0, 10))
        ttk.Button(filter_primary, text="Basic Dossier", command=lambda: self.start_selected_scout_report("basic")).pack(side="left", padx=2)
        ttk.Button(filter_primary, text="Full Evaluation", command=lambda: self.start_selected_scout_report("full")).pack(side="left", padx=2)
        ttk.Button(filter_primary, text="Observe Next Fight", command=lambda: self.start_selected_scout_report("observation")).pack(side="left", padx=2)
        filter_ranges = ttk.Frame(filters, style="Inset.TFrame")
        filter_ranges.pack(fill="x", pady=(3, 2))
        for label, variable, minimum, maximum, width in (
            ("Age", self.market_age_min, 16, 60, 4), ("to", self.market_age_max, 16, 60, 4),
            ("OVR", self.market_ovr_min, 0, 100, 4), ("to", self.market_ovr_max, 0, 100, 4),
            ("Min Pop", self.market_pop_min, 0, 100, 4), ("Min Potential", self.market_potential_min, 0, 100, 4),
        ):
            ttk.Label(filter_ranges, text=label, style="Inset.TLabel").pack(side="left", padx=(7, 2))
            spin = ttk.Spinbox(filter_ranges, from_=minimum, to=maximum, textvariable=variable, width=width, command=self.refresh_market)
            spin.pack(side="left")
            spin.bind("<KeyRelease>", lambda _e: self.refresh_market())
            spin.bind("<FocusOut>", lambda _e: self.refresh_market())
        ttk.Button(filter_ranges, text="Reset Filters", command=self.reset_market_filters).pack(side="left", padx=10)
        # The market can contain hundreds of fighters. Reserve the lower part
        # of the screen for a draggable split so large monitors can show more
        # rows without making the filters or scouting read disappear.
        self.market_resize_pane = self.create_vertical_resizer(
            inner, initial_fraction=0.95, min_top=220, min_bottom=24
        )
        self.market_resize_pane.pack(fill="both", expand=True)
        market_body = ttk.Frame(self.market_resize_pane, style="Inset.TFrame")
        self.market_resize_pane.add(market_body, minsize=220)
        self.market_resize_spacer = tk.Frame(self.market_resize_pane, bg=self.colors["paper"], height=24)
        self.market_resize_pane.add(self.market_resize_spacer, minsize=0)
        scout_panel = tk.Frame(market_body, bg=self.colors["panel_dark"], width=300, highlightthickness=1, highlightbackground=self.colors["line"])
        scout_panel.pack(side="right", fill="y", padx=(8, 0))
        scout_panel.pack_propagate(False)
        tk.Label(scout_panel, text="SCOUTING READ", font=("Impact", 15), bg=self.colors["panel_dark"], fg=self.colors["gold"]).pack(anchor="w", padx=10, pady=(8, 2))
        self.market_scout_text = tk.Text(scout_panel, height=18, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=9, pady=8, bd=0)
        self.market_scout_text.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.market_scout_text.insert("end", "Select a free agent to see scouting confidence, risk, and action advice.")
        self.market_scout_text.config(state="disabled")
        tree_frame = ttk.Frame(market_body, style="Inset.TFrame")
        tree_frame.pack(side="left", fill="both", expand=True)
        self.market_tree = ttk.Treeview(tree_frame, columns=("name", "tag", "gender", "weight", "record", "age", "overall", "popularity", "star", "media", "pro", "style", "purse", "offer"), show="headings")
        for col, text, width in (("name", "Name", 155), ("tag", "Market Status", 120), ("gender", "G", 38), ("weight", "Weight", 100), ("record", "Record", 65), ("age", "Age", 45), ("overall", "OVR", 50), ("popularity", "Pop", 50), ("star", "Star", 50), ("media", "Media", 55), ("pro", "Pro", 45), ("style", "Style", 90), ("purse", "Asking", 80), ("offer", "Rival Offer", 145)):
            self.market_tree.heading(col, text=text)
            self.market_tree.column(col, width=width, anchor="center")
        self.market_tree.column("name", anchor="w")
        self.market_tree.tag_configure("closed_division", background="#5f421b", foreground="#ffe7a3")
        self.make_tree_sortable(self.market_tree)
        market_scroll = ttk.Scrollbar(tree_frame, orient="vertical", command=self.market_tree.yview)
        self.market_tree.configure(yscrollcommand=market_scroll.set)
        market_scroll.pack(side="right", fill="y")
        self.market_tree.pack(side="left", fill="both", expand=True)
        self.market_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.market_tree, "name"))
        self.market_tree.bind("<<TreeviewSelect>>", lambda _e: self.refresh_market_scout_panel())
        actions = ttk.Frame(self.market_tab, style="TFrame")
        actions.pack(fill="x")
        ttk.Button(actions, text="Negotiate", style="Accent.TButton", command=self.open_negotiation).pack(side="right")
        self.market_action_notice = tk.Label(
            actions, text="", font=("Tahoma", 9, "bold"), anchor="w", justify="left",
            bg=self.colors["chrome"], fg=self.colors["gold"], padx=4, pady=3,
        )
        self.market_action_notice.pack(side="left", fill="x", expand=True)
        self.market_action_notice.bind("<Configure>", lambda event: self.market_action_notice.configure(wraplength=max(260, event.width - 12)))

    def build_world_tab(self):
        self.screen_header(self.world_tab, "WORLD HUB", "Promotions, news, market churn, and the wider MMA economy")
        body = ttk.Frame(self.world_tab)
        body.pack(fill="both", expand=True)
        context_board = tk.Frame(body, bg=self.colors["chrome"])
        context_board.pack(fill="x", pady=(0, 6))
        self.world_context_vars = {}
        for key, title in (("company", "SELECTED COMPANY"), ("promotion", "PROMOTION SNAPSHOT"), ("gym", "SELECTED GYM"), ("capacity", "GYM CAPACITY")):
            cell = tk.Frame(context_board, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
            cell.pack(side="left", fill="both", expand=True, padx=(0, 6))
            tk.Label(cell, text=title, bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 7, "bold"), anchor="w").pack(fill="x", padx=8, pady=(5, 0))
            value = tk.StringVar(value="Select a company or gym")
            self.world_context_vars[key] = value
            tk.Label(cell, textvariable=value, bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Tahoma", 9, "bold"), anchor="w", justify="left", wraplength=225).pack(fill="both", expand=True, padx=8, pady=(0, 6))

        world_next_steps = ttk.Frame(body, style="Inset.TFrame")
        world_next_steps.pack(fill="x", pady=(0, 5))
        ttk.Label(world_next_steps, text="NEXT STEP", style="Section.TLabel").pack(side="left", padx=(5, 8), pady=5)
        self.world_next_step_summary = ttk.Label(
            world_next_steps,
            text="Select a promotion, story, or gym to see the most useful context review.",
            style="Inset.TLabel", anchor="w",
        )
        self.world_next_step_summary.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=5)
        self.world_next_step_primary = ttk.Button(
            world_next_steps, text="Open", command=lambda: self.open_world_next_step("primary"), state="disabled",
        )
        self.world_next_step_primary.pack(side="right", padx=3, pady=3)
        self.world_next_step_secondary = ttk.Button(
            world_next_steps, text="Review", command=lambda: self.open_world_next_step("secondary"), state="disabled",
        )
        self.world_next_step_secondary.pack(side="right", padx=3, pady=3)

        left_panel, left = self.section(body, "PROMOTIONS")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.promo_tree = ttk.Treeview(left, columns=("name", "region", "rep", "score", "size", "cash", "momentum", "last"), show="headings", height=10)
        for col, text, width in (("name", "Company", 170), ("region", "Region", 65), ("rep", "Level", 75), ("score", "Rep", 45), ("size", "Size", 45), ("cash", "Cash", 85), ("momentum", "Mom", 45), ("last", "Last Event", 160)):
            self.promo_tree.heading(col, text=text)
            self.promo_tree.column(col, width=width, anchor="center")
        self.promo_tree.column("name", anchor="w")
        self.promo_tree.column("last", anchor="w")
        self.make_tree_sortable(self.promo_tree)
        self.promo_tree.pack(fill="both", expand=True)
        self.promo_tree.bind("<<TreeviewSelect>>", self.show_selected_world_promotion)

        right_panel, right = self.section(body, "WORLD NEWS")
        right_panel.pack(side="left", fill="both", expand=True)
        self.world_news_list = tk.Listbox(right, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff", activestyle="none", height=10)
        self.world_news_list.pack(fill="both", expand=True, pady=(0, 5))
        self.world_news_list.bind("<<ListboxSelect>>", self.show_selected_world_story)
        self.world_news_list.bind("<Double-1>", lambda _event: self.open_selected_world_story_reader())
        self.world_news_detail = tk.Text(right, wrap="word", font=("Tahoma", 9), bg=self.colors["panel_dark"], fg=self.colors["text"], height=5, padx=10, pady=8)
        self.world_news_detail.pack(fill="x", pady=(0, 5))
        self.world_news_detail.config(state="disabled")
        news_actions = ttk.Frame(right, style="Inset.TFrame")
        news_actions.pack(fill="x", pady=(0, 6))
        ttk.Button(news_actions, text="Read Full Story", style="Accent.TButton", command=self.open_selected_world_story_reader).pack(side="left", padx=4, pady=3)
        ttk.Button(news_actions, text="Open Story Context", command=self.open_selected_world_story_context).pack(side="left", padx=4, pady=3)
        ttk.Button(news_actions, text="Combat Sports", command=self.open_combat_sports_window).pack(side="left", padx=4, pady=3)
        ttk.Button(news_actions, text="World Chronicle", command=self.open_world_chronicle).pack(side="right", padx=4, pady=3)
        ttk.Button(news_actions, text="Storylines", style="Accent.TButton", command=self.open_storylines_window).pack(side="right", padx=4, pady=3)
        ttk.Button(news_actions, text="Story Briefings", command=self.open_followed_story_briefing_window).pack(side="right", padx=4, pady=3)
        ttk.Label(right, text="GYM NETWORK", style="PanelTitle.TLabel").pack(anchor="w")
        self.gym_tree = ttk.Treeview(right, columns=("name", "region", "tier", "effective", "morale", "members", "trend", "specialty"), show="headings", height=7)
        for col, text, width in (("name", "Gym", 135), ("region", "Region", 66), ("tier", "Tier", 72), ("effective", "Effective", 54), ("morale", "Room", 46), ("members", "Load", 66), ("trend", "Form", 44), ("specialty", "Identity", 150)):
            self.gym_tree.heading(col, text=text)
            self.gym_tree.column(col, width=width, anchor="center")
        self.gym_tree.column("name", anchor="w")
        self.gym_tree.column("specialty", anchor="w")
        self.make_tree_sortable(self.gym_tree)
        self.gym_tree.pack(fill="x")
        self.gym_tree.bind("<Double-1>", lambda _e: self.open_selected_gym_viewer())
        self.gym_tree.bind("<<TreeviewSelect>>", self.show_selected_world_gym)
        ttk.Button(right, text="View Gym", command=self.open_selected_gym_viewer).pack(anchor="e", pady=(6, 0))

    def build_fighter_search_tab(self):
        self.screen_header(self.fighter_search_tab, "FIGHTER SEARCH", "Search the full combat-sports world and inspect recent form")
        controls = ttk.Frame(self.fighter_search_tab, style="Chrome.TFrame")
        controls.pack(fill="x", pady=(0, 6))
        self.world_fighter_search = tk.StringVar(value="")
        self.world_fighter_company_filter = tk.StringVar(value="All")
        self.world_fighter_gender_filter = tk.StringVar(value="All")
        self.world_fighter_weight_filter = tk.StringVar(value="All")
        self.world_fighter_sport_filter = tk.StringVar(value="All")
        self.world_fighter_status_filter = tk.StringVar(value="Active")

        ttk.Label(controls, text="Search").grid(row=0, column=0, sticky="w", padx=(4, 3), pady=4)
        search_entry = ttk.Entry(controls, textvariable=self.world_fighter_search, width=24)
        search_entry.grid(row=0, column=1, sticky="ew", padx=(0, 8), pady=4)
        self.world_fighter_search.trace_add("write", self.schedule_world_fighter_search)
        for column, label, variable, width in (
            (2, "Company", self.world_fighter_company_filter, 25),
            (4, "Gender", self.world_fighter_gender_filter, 10),
            (6, "Division", self.world_fighter_weight_filter, 17),
            (8, "Sport", self.world_fighter_sport_filter, 18),
            (10, "Status", self.world_fighter_status_filter, 13),
        ):
            ttk.Label(controls, text=label).grid(row=0, column=column, sticky="w", padx=(2, 3), pady=4)
            combo = ttk.Combobox(controls, textvariable=variable, state="readonly", width=width)
            combo.grid(row=0, column=column + 1, sticky="ew", padx=(0, 6), pady=4)
            combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_world_fighter_search())
            if label == "Company":
                self.world_fighter_company_combo = combo
            elif label == "Gender":
                combo.configure(values=["All", "Male", "Female"])
            elif label == "Division":
                combo.configure(values=["All"] + WEIGHTS)
            elif label == "Sport":
                self.world_fighter_sport_combo = combo
            else:
                combo.configure(values=["Active", "All", "Free Agents", "Retired"])
        ttk.Button(controls, text="Clear", command=self.clear_world_fighter_filters).grid(row=0, column=12, padx=4, pady=4)
        controls.columnconfigure(1, weight=1)

        panel, inner = self.section(self.fighter_search_tab, "WORLD FIGHTER DIRECTORY")
        panel.pack(fill="both", expand=True)
        self.world_fighter_search_count = ttk.Label(inner, text="", style="Inset.TLabel")
        self.world_fighter_search_count.pack(anchor="w", padx=4, pady=(3, 2))
        pager = ttk.Frame(inner, style="Inset.TFrame")
        pager.pack(fill="x")
        self.world_search_previous = ttk.Button(pager, text="Previous 100", command=lambda: self.change_world_fighter_page(-1))
        self.world_search_previous.pack(side="left", padx=4)
        self.world_search_next = ttk.Button(pager, text="Next 100", command=lambda: self.change_world_fighter_page(1))
        self.world_search_next.pack(side="left", padx=4)
        table = ttk.Frame(inner, style="Inset.TFrame")
        table.pack(fill="both", expand=True)
        columns = ("name", "company", "sport", "gender", "division", "age", "universe", "career", "form", "last", "overall", "elo")
        self.world_fighter_tree = ttk.Treeview(table, columns=columns, show="headings", selectmode="extended")
        for column, label, width in (
            ("name", "Fighter", 175), ("company", "Company", 175), ("sport", "Sport", 100), ("gender", "G", 38),
            ("division", "Division", 112), ("age", "Age", 46), ("universe", "Universe W-L-D", 95),
            ("career", "Career W-L-D", 90), ("form", "Last 5", 72), ("last", "Last Fight", 280), ("overall", "OVR", 58), ("elo", "ELO", 64),
        ):
            self.world_fighter_tree.heading(column, text=label)
            self.world_fighter_tree.column(column, width=width, anchor="center")
        for column in ("name", "company", "last"):
            self.world_fighter_tree.column(column, anchor="w")
        self.make_tree_sortable(self.world_fighter_tree)
        scroll = ttk.Scrollbar(table, orient="vertical", command=self.world_fighter_tree.yview)
        self.world_fighter_tree.configure(yscrollcommand=scroll.set)
        self.world_fighter_tree.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        self.world_fighter_tree.bind("<Double-1>", lambda _event: self.open_selected_world_fighter_profile())
        actions = ttk.Frame(self.fighter_search_tab, style="Chrome.TFrame")
        actions.pack(fill="x", pady=(5, 0))
        ttk.Button(actions, text="Compare Selected", command=self.compare_selected_world_fighters).pack(side="right", padx=4)
        ttk.Button(actions, text="View Fighter", style="Accent.TButton", command=self.open_selected_world_fighter_profile).pack(side="right", padx=4)
        self.world_fighter_action_notice = tk.Label(
            actions, text="", font=("Tahoma", 9, "bold"), anchor="w", justify="left",
            bg=self.colors["chrome"], fg=self.colors["gold"], padx=4, pady=3,
        )
        self.world_fighter_action_notice.pack(side="left", fill="x", expand=True)
        self.world_fighter_action_notice.bind("<Configure>", lambda event: self.world_fighter_action_notice.configure(wraplength=max(280, event.width - 12)))

    def build_regional_prospects_tab(self):
        self.screen_header(
            self.regional_prospects_tab,
            "REGIONAL PROSPECTS",
            "Browse feeder-circuit graduates, scout developing talent, and negotiate before the wider market reacts",
        )
        controls = ttk.Frame(self.regional_prospects_tab, style="Chrome.TFrame")
        controls.pack(fill="x", pady=(0, 6))
        self.regional_prospect_search = tk.StringVar(value="")
        self.regional_prospect_status_filter = tk.StringVar(value="Eligible + Nearly")
        self.regional_prospect_company_filter = tk.StringVar(value="All")
        self.regional_prospect_gender_filter = tk.StringVar(value="All")
        self.regional_prospect_weight_filter = tk.StringVar(value="All")
        self.regional_prospect_show_closed_divisions = tk.BooleanVar(value=True)
        for column, label, variable, values, width in (
            (0, "Search", self.regional_prospect_search, None, 20),
            (2, "Status", self.regional_prospect_status_filter, ["Eligible + Nearly", "Eligible Now", "Nearly Eligible", "Medical Hold", "Developing", "All Regional"], 18),
            (4, "Promotion", self.regional_prospect_company_filter, ["All"], 27),
            (6, "Gender", self.regional_prospect_gender_filter, ["All", "Male", "Female"], 10),
            (8, "Division", self.regional_prospect_weight_filter, ["All"] + WEIGHTS, 16),
        ):
            ttk.Label(controls, text=label).grid(row=0, column=column, sticky="w", padx=(4, 3), pady=4)
            if values is None:
                widget = ttk.Entry(controls, textvariable=variable, width=width)
                widget.bind("<KeyRelease>", lambda _event: self.refresh_regional_prospects())
            else:
                widget = ttk.Combobox(controls, textvariable=variable, values=values, state="readonly", width=width)
                widget.bind("<<ComboboxSelected>>", lambda _event: self.refresh_regional_prospects())
            widget.grid(row=0, column=column + 1, sticky="ew", padx=(0, 6), pady=4)
            if label == "Promotion":
                self.regional_prospect_company_combo = widget
        ttk.Checkbutton(
            controls, text="Closed divisions", variable=self.regional_prospect_show_closed_divisions,
            command=self.refresh_regional_prospects,
        ).grid(row=0, column=10, padx=(4, 2), pady=4)
        ttk.Button(controls, text="Reset", command=self.clear_regional_prospect_filters).grid(row=0, column=11, padx=4, pady=4)
        controls.columnconfigure(1, weight=1)

        panel, inner = self.section(self.regional_prospects_tab, "FEEDER-CIRCUIT TALENT")
        panel.pack(fill="both", expand=True)
        self.regional_prospect_count = ttk.Label(inner, text="", style="Inset.TLabel")
        self.regional_prospect_count.pack(anchor="w", padx=4, pady=(2, 3))
        table = ttk.Frame(inner, style="Inset.TFrame")
        table.pack(fill="both", expand=True)
        columns = (
            "name", "status", "promotion", "region", "gender", "division", "age", "record",
            "winrate", "overall", "potential", "momentum", "popularity", "last", "path",
        )
        self.regional_prospect_tree = ttk.Treeview(table, columns=columns, show="headings", selectmode="browse")
        for column, label, width in (
            ("name", "Fighter", 155), ("status", "Readiness", 105), ("promotion", "Promotion", 190),
            ("region", "Region", 76), ("gender", "G", 36), ("division", "Division", 100),
            ("age", "Age", 42), ("record", "Record", 68), ("winrate", "Win %", 54),
            ("overall", "OVR", 50), ("potential", "Potential", 62), ("momentum", "Mom", 48),
            ("popularity", "Pop", 44), ("last", "Last Fight", 86), ("path", "Qualification / Next Step", 310),
        ):
            self.regional_prospect_tree.heading(column, text=label)
            self.regional_prospect_tree.column(column, width=width, anchor="center")
        for column in ("name", "promotion", "path"):
            self.regional_prospect_tree.column(column, anchor="w")
        self.regional_prospect_tree.tag_configure("eligible", background="#173d2b", foreground="#a8f0bd")
        self.regional_prospect_tree.tag_configure("nearly", background="#4b3b12", foreground="#ffe28a")
        self.regional_prospect_tree.tag_configure("medical", background="#512020", foreground="#ffaaa2")
        self.regional_prospect_tree.tag_configure("developing", foreground="#aab0b8")
        self.regional_prospect_tree.tag_configure("closed_division", background="#5f421b", foreground="#ffe7a3")
        self.make_tree_sortable(self.regional_prospect_tree)
        scroll_y = ttk.Scrollbar(table, orient="vertical", command=self.regional_prospect_tree.yview)
        scroll_x = ttk.Scrollbar(table, orient="horizontal", command=self.regional_prospect_tree.xview)
        self.regional_prospect_tree.configure(yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set)
        scroll_x.pack(side="bottom", fill="x")
        scroll_y.pack(side="right", fill="y")
        self.regional_prospect_tree.pack(side="left", fill="both", expand=True)
        self.regional_prospect_tree.bind("<<TreeviewSelect>>", self.show_selected_regional_prospect)
        self.regional_prospect_tree.bind("<Double-1>", lambda _event: self.open_selected_regional_prospect())

        self.regional_prospect_detail_var = tk.StringVar(value="Select a prospect to see exactly why they qualify or what remains.")
        detail = tk.Label(
            inner, textvariable=self.regional_prospect_detail_var, anchor="w", justify="left",
            bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=8, pady=7,
        )
        detail.pack(fill="x", pady=(5, 0))
        detail.bind("<Configure>", lambda event: detail.configure(wraplength=max(420, event.width - 20)))
        actions = ttk.Frame(self.regional_prospects_tab, style="Chrome.TFrame")
        actions.pack(fill="x", pady=(5, 0))
        ttk.Button(actions, text="View Profile", command=self.open_selected_regional_prospect).pack(side="left", padx=4)
        ttk.Button(actions, text="Basic Scout", command=lambda: self.scout_selected_regional_prospect("basic")).pack(side="left", padx=4)
        ttk.Button(actions, text="Full Scout", command=lambda: self.scout_selected_regional_prospect("full")).pack(side="left", padx=4)
        self.regional_prospect_negotiate_button = ttk.Button(actions, text="Negotiate", style="Accent.TButton", command=self.negotiate_selected_regional_prospect)
        self.regional_prospect_negotiate_button.pack(side="right", padx=4)

    def build_rankings_tab(self):
        self.screen_header(self.rankings_tab, "RANKINGS", "Division rankings and pound-for-pound rankings")
        controls = tk.Frame(self.rankings_tab, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
        controls.pack(fill="x", pady=(0, 6))
        ttk.Label(controls, text="Ranking list", style="Section.TLabel").pack(side="left", padx=(8, 4), pady=6)
        self.ranking_filter = tk.StringVar(value="Pound-for-Pound")
        ranking_box = ttk.Combobox(controls, values=["Pound-for-Pound", "Division Rankings", "Company Rankings"], textvariable=self.ranking_filter, state="readonly", width=20)
        ranking_box.pack(side="left", padx=6, pady=6)
        ranking_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_rankings())
        ttk.Label(controls, text="Weight", style="Section.TLabel").pack(side="left", padx=(14, 4), pady=6)
        ranking_weight = ttk.Combobox(controls, values=["All"] + WEIGHTS, textvariable=self.ranking_weight_filter, state="readonly", width=15)
        ranking_weight.pack(side="left", padx=6, pady=6)
        ranking_weight.bind("<<ComboboxSelected>>", lambda _e: self.refresh_rankings())
        ttk.Label(controls, text="Scope", style="Section.TLabel").pack(side="left", padx=(14, 4), pady=6)
        self.ranking_scope = tk.StringVar(value="Worldwide")
        self.ranking_scope_box = ttk.Combobox(controls, textvariable=self.ranking_scope, state="readonly", width=30)
        self.ranking_scope_box.pack(side="left", padx=6, pady=6)
        self.ranking_scope_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_rankings())
        ttk.Label(controls, text="Gender", style="Section.TLabel").pack(side="left", padx=(14, 4), pady=6)
        ranking_gender = ttk.Combobox(controls, values=["All", "Male", "Female"], textvariable=self.ranking_gender_filter, state="readonly", width=10)
        ranking_gender.pack(side="left", padx=6, pady=6)
        ranking_gender.bind("<<ComboboxSelected>>", lambda _e: self.refresh_rankings())
        ranking_board = tk.Frame(self.rankings_tab, bg=self.colors["chrome"])
        ranking_board.pack(fill="x", pady=(0, 6))
        self.ranking_summary_vars = {}
        for key, title in (
            ("mode", "BOARD"), ("scope", "SCOPE"), ("leader", "TOP RANKED"),
            ("champions", "CHAMPIONS"), ("matching", "MATCHED"), ("shown", "SHOWN"),
        ):
            cell = tk.Frame(ranking_board, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
            cell.pack(side="left", fill="x", expand=True, padx=(0, 6))
            tk.Label(cell, text=title, bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 7, "bold"), anchor="w").pack(fill="x", padx=8, pady=(5, 0))
            var = tk.StringVar(value="-")
            self.ranking_summary_vars[key] = var
            tk.Label(cell, textvariable=var, bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Tahoma", 10, "bold"), anchor="w").pack(fill="x", padx=8, pady=(0, 6))
        panel, inner = self.section(self.rankings_tab, "TOP CONTENDERS")
        panel.pack(fill="both", expand=True)
        rankings_resize = self.create_vertical_resizer(inner, initial_fraction=0.76, min_top=250, min_bottom=118)
        rankings_resize.pack(fill="both", expand=True)
        ranking_table = ttk.Frame(rankings_resize, style="Inset.TFrame")
        rankings_resize.add(ranking_table, minsize=220)
        self.rankings_tree = ttk.Treeview(ranking_table, columns=("company_rank", "world_rank", "move", "name", "gender", "company", "weight", "record", "overall", "form", "path", "score", "last", "status"), show="headings")
        for col, text, width in (("company_rank", "Co", 54), ("world_rank", "World", 58), ("move", "Move", 58), ("name", "Fighter", 170), ("gender", "G", 34), ("company", "Company", 135), ("weight", "Division", 102), ("record", "Record", 76), ("overall", "OVR", 52), ("form", "Form", 96), ("path", "Title Path", 145), ("score", "Score", 66), ("last", "Last Fight", 155), ("status", "Status", 90)):
            self.rankings_tree.heading(col, text=text)
            self.rankings_tree.column(col, width=width, anchor="center")
        self.rankings_tree.column("name", anchor="w")
        self.rankings_tree.column("company", anchor="w")
        self.rankings_tree.column("last", anchor="w")
        self.rankings_tree.tag_configure("champion", foreground=self.colors["gold"])
        self.rankings_tree.tag_configure("top_contender", foreground=self.colors["text"])
        self.rankings_tree.tag_configure("rising", foreground="#9dffb2")
        self.rankings_tree.tag_configure("sliding", foreground="#ff9a9a")
        self.rankings_tree.tag_configure("company", foreground=self.colors["gold"])
        self.make_tree_sortable(self.rankings_tree)
        ranking_y = ttk.Scrollbar(ranking_table, orient="vertical", command=self.rankings_tree.yview)
        ranking_x = ttk.Scrollbar(ranking_table, orient="horizontal", command=self.rankings_tree.xview)
        self.rankings_tree.configure(yscrollcommand=ranking_y.set, xscrollcommand=ranking_x.set)
        self.rankings_tree.grid(row=0, column=0, sticky="nsew")
        ranking_y.grid(row=0, column=1, sticky="ns")
        ranking_x.grid(row=1, column=0, sticky="ew")
        ranking_table.rowconfigure(0, weight=1)
        ranking_table.columnconfigure(0, weight=1)
        ranking_detail_frame = ttk.Frame(rankings_resize, style="Inset.TFrame")
        rankings_resize.add(ranking_detail_frame, minsize=95)
        detail_header = tk.Frame(ranking_detail_frame, bg=self.colors["panel_dark"])
        detail_header.pack(fill="x")
        tk.Label(detail_header, text="RANKING READ", bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Impact", 11), anchor="w").pack(side="left", padx=10, pady=(7, 2))
        tk.Label(detail_header, text="Double-click a fighter to open profile", bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 8), anchor="e").pack(side="right", padx=10, pady=(7, 2))
        self.ranking_detail = tk.Text(ranking_detail_frame, height=5, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], insertbackground=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8, bd=0)
        self.ranking_detail.pack(fill="both", expand=True); self.ranking_detail.config(state="disabled")
        self.rankings_tree.bind("<<TreeviewSelect>>", self.show_ranking_detail)
        self.rankings_tree.bind("<Double-1>", self.open_selected_ranking_profile)

    def build_editor_tab(self):
        self.screen_header(self.editor_tab, "WORLD EDITOR", "Edit the current career or maintain the reusable starting universe")
        self.editor_current_dirty = False
        self.editor_career_target_var = tk.StringVar(value="Current career")
        self.editor_database_target_var = tk.StringVar(value="Starting universe")
        self.editor_edit_state_var = tk.StringVar(value="No unsaved editor changes")
        self.editor_action_notice_var = tk.StringVar(value="Select a fighter to edit, or create a new fighter.")

        scope_row = ttk.Frame(self.editor_tab, style="Chrome.TFrame")
        scope_row.pack(fill="x", pady=(0, 6))
        career_scope, career_inner = self.section(scope_row, "CURRENT CAREER")
        career_scope.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Label(career_inner, textvariable=self.editor_career_target_var, style="Inset.TLabel", font=("Tahoma", 9, "bold")).pack(side="left", padx=8, pady=6)
        ttk.Label(career_inner, textvariable=self.editor_edit_state_var, style="Inset.TLabel").pack(side="left", padx=8)
        ttk.Button(career_inner, text="Save Career Now", style="Accent.TButton", command=self.save_editor_career_now).pack(side="right", padx=6, pady=4)
        ttk.Label(career_inner, textvariable=self.editor_action_notice_var, style="Inset.TLabel", anchor="e").pack(side="right", padx=8, pady=6)

        universe_scope, universe_inner = self.section(scope_row, "STARTING UNIVERSE - NEW GAMES")
        universe_scope.pack(side="left", fill="x", expand=True, padx=(4, 0))
        self.universe_section_choice = tk.StringVar(value="fighters")
        ttk.Label(universe_inner, textvariable=self.editor_database_target_var, style="Inset.TLabel", font=("Tahoma", 9, "bold")).grid(row=0, column=0, sticky="w", padx=7)
        ttk.Combobox(universe_inner, textvariable=self.universe_section_choice, values=["fighters", "companies", "combat_sports", "media", "regions"], width=14, state="readonly").grid(row=0, column=1, sticky="ew", padx=3, pady=4)
        ttk.Button(universe_inner, text="Edit Starting Data", command=self.open_universe_section_editor).grid(row=0, column=2, sticky="ew", padx=3, pady=4)
        ttk.Button(universe_inner, text="Validate", command=self.validate_active_universe_database).grid(row=0, column=3, sticky="ew", padx=3, pady=4)
        universe_inner.columnconfigure(0, weight=1)

        controls = ttk.Frame(self.editor_tab, style="Chrome.TFrame")
        controls.pack(fill="x", pady=(0, 6))
        self.editor_search = tk.StringVar(value="")
        self.editor_company_filter = tk.StringVar(value="All")
        self.editor_weight_filter = tk.StringVar(value="All")
        self.editor_gender_filter = tk.StringVar(value="All")
        filter_row = ttk.Frame(controls, style="Chrome.TFrame")
        filter_row.pack(fill="x", pady=(0, 3))
        ttk.Label(filter_row, text="Search", style="Chrome.TLabel").grid(row=0, column=0, sticky="w", padx=(4, 2))
        search = ttk.Entry(filter_row, textvariable=self.editor_search, width=20)
        search.grid(row=0, column=1, sticky="ew", padx=(0, 8))
        ttk.Label(filter_row, text="Employer", style="Chrome.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 2))
        self.editor_company_combo = ttk.Combobox(filter_row, textvariable=self.editor_company_filter, width=20, state="readonly")
        self.editor_company_combo.grid(row=0, column=3, sticky="ew", padx=(0, 8))
        ttk.Label(filter_row, text="Division", style="Chrome.TLabel").grid(row=0, column=4, sticky="w", padx=(0, 2))
        ttk.Combobox(filter_row, textvariable=self.editor_weight_filter, values=["All"] + WEIGHTS, width=14, state="readonly").grid(row=0, column=5, sticky="ew", padx=(0, 8))
        ttk.Label(filter_row, text="Gender", style="Chrome.TLabel").grid(row=0, column=6, sticky="w", padx=(0, 2))
        ttk.Combobox(filter_row, textvariable=self.editor_gender_filter, values=["All", "Male", "Female"], width=9, state="readonly").grid(row=0, column=7, sticky="ew", padx=(0, 4))
        for col in (1, 3, 5, 7):
            filter_row.columnconfigure(col, weight=1)
        ttk.Button(filter_row, text="Refresh Career", command=self.refresh_database_editor).grid(row=0, column=8, sticky="ew", padx=(4, 0))
        for variable in (self.editor_search, self.editor_company_filter, self.editor_weight_filter, self.editor_gender_filter):
            variable.trace_add("write", lambda *_args: self.schedule_database_editor_refresh())

        body = ttk.Frame(self.editor_tab, style="Chrome.TFrame")
        body.pack(fill="both", expand=True)
        list_panel, list_inner = self.section(body, "CURRENT CAREER FIGHTERS")
        list_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        editor_tree_shell = ttk.Frame(list_inner, style="Inset.TFrame")
        editor_tree_shell.pack(fill="both", expand=True)
        self.editor_tree = ttk.Treeview(editor_tree_shell, columns=("company", "name", "gender", "weight", "age", "overall", "potential", "pop", "record", "status"), show="headings", height=22)
        for col, title, width in (("company", "Employer", 135), ("name", "Fighter", 155), ("gender", "G", 38), ("weight", "Division", 95), ("age", "Age", 42), ("overall", "OVR", 48), ("potential", "Upside", 55), ("pop", "Pop", 45), ("record", "Record", 70), ("status", "Status", 84)):
            self.editor_tree.heading(col, text=title)
            self.editor_tree.column(col, width=width, anchor="center")
        self.editor_tree.column("company", anchor="w")
        self.editor_tree.column("name", anchor="w")
        editor_tree_vertical = ttk.Scrollbar(editor_tree_shell, orient="vertical", command=self.editor_tree.yview)
        editor_tree_horizontal = ttk.Scrollbar(editor_tree_shell, orient="horizontal", command=self.editor_tree.xview)
        self.editor_tree.configure(yscrollcommand=editor_tree_vertical.set, xscrollcommand=editor_tree_horizontal.set)
        self.editor_tree.grid(row=0, column=0, sticky="nsew")
        editor_tree_vertical.grid(row=0, column=1, sticky="ns")
        editor_tree_horizontal.grid(row=1, column=0, sticky="ew")
        editor_tree_shell.rowconfigure(0, weight=1)
        editor_tree_shell.columnconfigure(0, weight=1)
        self.make_tree_sortable(self.editor_tree)
        self.editor_tree.bind("<<TreeviewSelect>>", lambda _event: self.load_selected_editor_fighter())
        self.editor_tree.bind("<Double-1>", lambda _event: self.open_editor_selected_profile())

        edit_panel, edit_inner = self.section(body, "CURRENT CAREER FIGHTER")
        edit_panel.pack(side="left", fill="both", expand=True)
        self.editor_vars = {
            "name": tk.StringVar(value="Custom Fighter"),
            "gender": tk.StringVar(value="Male"),
            "weight": tk.StringVar(value="Lightweight"),
            "region": tk.StringVar(value="USA"),
            "nationality": tk.StringVar(value="American"),
            "style": tk.StringVar(value="Well-Rounded"),
            "stance": tk.StringVar(value="Orthodox"),
            "trait": tk.StringVar(value="Gym Rat"),
            "behaviour": tk.StringVar(value="Dynamic Attacker"),
            "camp": tk.StringVar(value="Independent"),
            "age": tk.IntVar(value=24),
            "record_w": tk.IntVar(value=0), "record_l": tk.IntVar(value=0), "record_d": tk.IntVar(value=0),
            "striking": tk.IntVar(value=65), "wrestling": tk.IntVar(value=65), "grappling": tk.IntVar(value=65),
            "cardio": tk.IntVar(value=65), "chin": tk.IntVar(value=65), "power": tk.IntVar(value=65),
            "takedown_defence": tk.IntVar(value=65), "ground_control": tk.IntVar(value=65),
            "submissions": tk.IntVar(value=65), "submission_defence": tk.IntVar(value=65),
            "recovery": tk.IntVar(value=65), "toughness": tk.IntVar(value=65), "fight_iq": tk.IntVar(value=65),
            "popularity": tk.IntVar(value=15),
            "momentum": tk.IntVar(value=0), "morale": tk.IntVar(value=70), "potential": tk.IntVar(value=70),
            "purse": tk.IntVar(value=8000), "contract_months": tk.IntVar(value=0), "fatigue": tk.IntVar(value=0), "injured": tk.IntVar(value=0),
            "owner": tk.StringVar(value="Free Agent"), "contract_type": tk.StringVar(value="Non-Exclusive"), "motivation": tk.IntVar(value=65), "professionalism": tk.IntVar(value=50), "media_presence": tk.IntVar(value=50), "star_quality": tk.IntVar(value=50),
            "height": tk.StringVar(value=""), "rival": tk.StringVar(value=""), "friend": tk.StringVar(value=""), "career_archetype": tk.StringVar(value="Balanced Development"), "prime_start": tk.IntVar(value=25), "prime_end": tk.IntVar(value=33), "walk_weight": tk.IntVar(value=0), "weight_cut_penalty": tk.IntVar(value=0), "injury_proneness": tk.IntVar(value=20), "finishing_instinct": tk.IntVar(value=50), "charisma": tk.IntVar(value=50), "sponsor_appeal": tk.IntVar(value=50), "media_heat": tk.IntVar(value=0), "elo_rating": tk.IntVar(value=1500), "rank_score": tk.IntVar(value=0), "title_wins": tk.IntVar(value=0), "title_defenses": tk.IntVar(value=0), "award_count": tk.IntVar(value=0), "win_bonus": tk.IntVar(value=0), "ppv_points": tk.IntVar(value=0), "relationship_trust": tk.IntVar(value=55),
            "exclusive": tk.BooleanVar(value=False), "champion": tk.BooleanVar(value=False), "interim_champion": tk.BooleanVar(value=False), "champions_clause": tk.BooleanVar(value=False), "title_shot_clause": tk.BooleanVar(value=False), "main_event_promise": tk.BooleanVar(value=False), "top_opponent_promise": tk.BooleanVar(value=False),
        }
        self.editor_selected_fighter = None
        self.editor_selected_owner = ""
        notebook = ttk.Notebook(edit_inner)
        notebook.pack(fill="both", expand=True)
        identity = ttk.Frame(notebook, style="Inset.TFrame")
        combat = ttk.Frame(notebook, style="Inset.TFrame")
        contract = ttk.Frame(notebook, style="Inset.TFrame")
        advanced = ttk.Frame(notebook, style="Inset.TFrame")
        notebook.add(identity, text="Identity")
        notebook.add(combat, text="Combat Ratings")
        notebook.add(contract, text="Contract & Status")
        notebook.add(advanced, text="Advanced & Career")

        self.build_editor_form(identity, [
            ("Name", "name", "entry"), ("Gender", "gender", "combo:Male|Female"), ("Division", "weight", "combo:" + "|".join(WEIGHTS)),
            ("Age", "age", "spin:16:55"), ("Region", "region", "combo:" + "|".join(REGIONS)), ("Nationality", "nationality", "entry"),
            ("Style", "style", "combo:" + "|".join(STYLES)), ("Stance", "stance", "combo:Orthodox|Southpaw|Switch"),
            ("Trait", "trait", "combo:" + "|".join(TRAITS)), ("Behaviour", "behaviour", "combo:" + "|".join(BEHAVIOURS)),
            ("Camp", "camp", "combo:" + "|".join(CAMPS)), ("Record Wins", "record_w", "spin:0:999"),
            ("Record Losses", "record_l", "spin:0:500"), ("Record Draws", "record_d", "spin:0:250"),
        ])
        self.build_editor_form(combat, [
            ("Striking", "striking", "spin:1:99"), ("Wrestling", "wrestling", "spin:1:99"), ("Grappling", "grappling", "spin:1:99"),
            ("Cardio", "cardio", "spin:1:99"), ("Chin", "chin", "spin:1:99"), ("Power", "power", "spin:1:99"),
            ("TD Defence", "takedown_defence", "spin:1:99"), ("Ground Control", "ground_control", "spin:1:99"), ("Submissions", "submissions", "spin:1:99"),
            ("Sub Defence", "submission_defence", "spin:1:99"), ("Recovery", "recovery", "spin:1:99"), ("Toughness", "toughness", "spin:1:99"),
            ("Fight IQ", "fight_iq", "spin:1:99"), ("Potential", "potential", "spin:1:99"), ("Popularity", "popularity", "spin:1:100"),
            ("Momentum", "momentum", "spin:-10:10"), ("Morale", "morale", "spin:1:100"),
        ])
        self.build_editor_form(contract, [
            ("Employer", "owner", "owner"), ("Purse / fight", "purse", "spin:0:1000000"), ("Contract months", "contract_months", "spin:0:60"),
            ("Contract type", "contract_type", "combo:Exclusive|Non-Exclusive"), ("Motivation", "motivation", "spin:1:100"), ("Professionalism", "professionalism", "spin:1:100"),
            ("Media Presence", "media_presence", "spin:1:100"), ("Star Quality", "star_quality", "spin:1:100"), ("Fatigue", "fatigue", "spin:0:100"), ("Injury months", "injured", "spin:0:36"),
        ])
        checks = ttk.Frame(contract, style="Inset.TFrame")
        checks.grid(row=3, column=0, columnspan=6, sticky="w", padx=10, pady=12)
        ttk.Checkbutton(checks, text="Exclusive", variable=self.editor_vars["exclusive"]).pack(side="left", padx=5)
        ttk.Checkbutton(checks, text="Champion", variable=self.editor_vars["champion"]).pack(side="left", padx=5)
        ttk.Checkbutton(checks, text="Interim Champion", variable=self.editor_vars["interim_champion"]).pack(side="left", padx=5)
        ttk.Checkbutton(checks, text="Champion Clause", variable=self.editor_vars["champions_clause"]).pack(side="left", padx=5)
        ttk.Checkbutton(checks, text="Title Shot Clause", variable=self.editor_vars["title_shot_clause"]).pack(side="left", padx=5)
        self.build_editor_form(advanced, [
            ("Height", "height", "entry"), ("Career Profile", "career_archetype", "combo:Early Maturation|Balanced Development|Late Maturation|Durable Career"), ("Prime Start", "prime_start", "spin:18:45"),
            ("Prime End", "prime_end", "spin:20:50"), ("Walk Weight", "walk_weight", "spin:0:400"), ("Cut Penalty", "weight_cut_penalty", "spin:0:30"),
            ("Injury Proneness", "injury_proneness", "spin:0:100"), ("Finishing Instinct", "finishing_instinct", "spin:1:100"), ("Charisma", "charisma", "spin:1:100"),
            ("Sponsor Appeal", "sponsor_appeal", "spin:1:100"), ("Media Heat", "media_heat", "spin:0:100"), ("ELO", "elo_rating", "spin:800:2600"),
            ("Rank Score", "rank_score", "spin:0:9999"), ("Title Wins", "title_wins", "spin:0:99"), ("Title Defences", "title_defenses", "spin:0:999"),
            ("Awards", "award_count", "spin:0:999"), ("Win Bonus", "win_bonus", "spin:0:500000"), ("PPV Points", "ppv_points", "spin:0:25"),
            ("Relationship Trust", "relationship_trust", "spin:1:100"), ("Rival", "rival", "entry"), ("Friend", "friend", "entry"),
        ])

        actions = ttk.Frame(edit_inner, style="Inset.TFrame")
        actions.pack(fill="x", pady=(6, 0))
        ttk.Button(actions, text="New Fighter", command=self.new_database_editor_fighter).pack(side="left", padx=4, pady=4)
        ttk.Button(actions, text="Apply to Current Career", style="Accent.TButton", command=self.save_database_editor_fighter).pack(side="left", padx=4, pady=4)
        ttk.Button(actions, text="Detailed Skill Sheet", command=self.open_detailed_skill_editor).pack(side="left", padx=4, pady=4)
        ttk.Button(actions, text="View Profile", command=self.open_editor_selected_profile).pack(side="left", padx=4, pady=4)
        ttk.Button(actions, text="Retire Fighter", command=self.retire_database_editor_fighter).pack(side="right", padx=4, pady=4)

    def build_sim_lab_tab(self):
        self.screen_header(self.sim_lab_tab, "SIMULATION LAB", "Division-aware fight testing, scouting cards, bracket simulations, and engine audits")
        top = ttk.Frame(self.sim_lab_tab)
        top.pack(fill="x", pady=(0, 6))
        balance_panel, balance = self.section(top, "COMPANY BALANCE")
        balance_panel.pack(side="left", fill="y", padx=(0, 6))
        self.sim_balance_label = ttk.Label(
            balance,
            text="",
            style="Inset.TLabel",
            justify="left",
            width=31,
        )
        self.sim_balance_label.pack(fill="x", padx=4, pady=(4, 2))
        self.sim_balance_edit_button = ttk.Button(
            balance,
            text="Edit Balance",
            style="Accent.TButton",
            command=self.edit_sim_company_balance,
        )
        self.sim_balance_edit_button.pack(fill="x", padx=4, pady=(2, 4))
        self.update_sim_company_balance_display()
        settings_panel, settings = self.section(top, "ENGINE SETTINGS")
        settings_panel.pack(side="left", fill="x", expand=True, padx=(0, 6))
        self.engine_vars = {}
        ttk.Label(settings, text="Fight mechanics (changes simulated actions and outcomes)", style="Inset.TLabel").pack(anchor="w", pady=(0, 2))
        for label, key in (("KO Power", "ko_power"), ("Submission Finish", "submission_finish"), ("Decision Noise", "decision_noise"), ("Gas Cost", "gas_cost"), ("Damage", "damage")):
            row = ttk.Frame(settings, style="Inset.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=18, style="Inset.TLabel").pack(side="left")
            var = tk.DoubleVar(value=self.engine_settings.get(key, 1.0))
            self.engine_vars[key] = var
            ttk.Spinbox(row, from_=0.5, to=2.0, increment=0.05, textvariable=var, width=6).pack(side="left", padx=4)
        business_row = ttk.Frame(settings, style="Inset.TFrame")
        business_row.pack(fill="x", pady=(5, 2))
        ttk.Label(business_row, text="Gate Multiplier", width=18, style="Inset.TLabel").pack(side="left")
        self.gate_multiplier_var = tk.DoubleVar(value=self.business_settings.get("gate_multiplier", 1.0))
        ttk.Spinbox(business_row, from_=0.5, to=2.0, increment=0.05, textvariable=self.gate_multiplier_var, width=6).pack(side="left", padx=4)
        ttk.Label(business_row, text="Business only", style="Inset.TLabel").pack(side="left", padx=4)
        ttk.Button(settings, text="Apply Settings", command=self.apply_engine_settings).pack(anchor="e", pady=4)
        audit_panel, audit = self.section(top, "AUDIT")
        audit_panel.pack(side="left", fill="x", expand=True)
        row = ttk.Frame(audit, style="Inset.TFrame")
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Events", style="Inset.TLabel").pack(side="left")
        ttk.Spinbox(row, from_=10, to=1000, increment=10, textvariable=self.audit_runs, width=7).pack(side="left", padx=6)
        ttk.Button(row, text="Run Audit", style="Accent.TButton", command=self.run_simulation_audit).pack(side="left", padx=8)
        ttk.Label(row, text="Seed", style="Inset.TLabel").pack(side="left", padx=(8, 2))
        ttk.Spinbox(row, from_=1, to=2147483647, increment=1, textvariable=self.play_audit_seed, width=10).pack(side="left", padx=(0, 4))
        ttk.Label(row, text="Years", style="Inset.TLabel").pack(side="left", padx=(10, 2))
        ttk.Spinbox(row, from_=1, to=100, increment=1, textvariable=self.play_audit_years, width=4).pack(side="left", padx=(0, 4))
        ttk.Button(row, text="Run Play Audit", command=self.run_play_level_audit).pack(side="left", padx=4)
        ttk.Button(row, text="Run 100-Year Audit", command=self.run_100_year_play_audit).pack(side="left", padx=4)
        ttk.Button(row, text="Resume Play Audit", command=self.resume_play_level_audit).pack(side="left", padx=4)
        # Keep the reader reachable after a restart: completed reports are
        # persisted beside their seed/year checkpoint and the action itself
        # fails closed with guidance when the selected recipe has no report.
        self.view_play_audit_button = ttk.Button(row, text="View Audit Results", command=self.open_play_level_audit_results)
        self.view_play_audit_button.pack(side="left", padx=4)
        ttk.Button(row, text="Audit History", command=self.open_play_audit_manifest).pack(side="left", padx=4)
        ttk.Button(row, text="Defaults", command=self.reset_engine_settings).pack(side="left", padx=4)
        limit_row = ttk.Frame(audit, style="Inset.TFrame")
        limit_row.pack(fill="x", padx=4, pady=(0, 2))
        ttk.Label(limit_row, text="Play-audit limit (seconds)", style="Inset.TLabel").pack(side="left", padx=(6, 4))
        ttk.Spinbox(
            limit_row, from_=30, to=1800, increment=30,
            textvariable=self.play_audit_time_limit_seconds, width=7,
        ).pack(side="left", padx=(0, 6))
        ttk.Label(
            limit_row,
            text="Stops after a completed week; Resume Play Audit continues from the checkpoint.",
            style="Inset.TLabel",
        ).pack(side="left", padx=2)
        audit_progress = ttk.Frame(audit, style="Inset.TFrame")
        audit_progress.pack(fill="x", padx=4, pady=(2, 4))
        self.play_audit_status = ttk.Label(audit_progress, text="Play audit: ready", style="Inset.TLabel", width=36)
        self.play_audit_status.pack(side="left", padx=(6, 8))
        self.play_audit_progress = ttk.Progressbar(audit_progress, mode="determinate", maximum=100, value=0)
        self.play_audit_progress.pack(side="left", fill="x", expand=True, padx=(0, 6), pady=3)

        population_panel, population = self.section(self.sim_lab_tab, "FREE-AGENT POPULATION TOOL")
        population_panel.pack(fill="x", pady=(0, 6))
        population_row = ttk.Frame(population, style="Inset.TFrame")
        population_row.pack(fill="x", padx=4, pady=4)
        ttk.Label(population_row, text="Create", style="Inset.TLabel").pack(side="left")
        ttk.Spinbox(population_row, from_=1, to=2000, increment=1, textvariable=self.sim_generate_count, width=6).pack(side="left", padx=(4, 10))
        ttk.Label(population_row, text="Age", style="Inset.TLabel").pack(side="left")
        ttk.Combobox(population_row, textvariable=self.sim_generate_age, values=["Random"] + [str(value) for value in range(16, 61)], width=8, state="readonly").pack(side="left", padx=(4, 10))
        ttk.Label(population_row, text="Ability", style="Inset.TLabel").pack(side="left")
        ttk.Combobox(population_row, textvariable=self.sim_generate_ability, values=["Random"] + [str(value) for value in range(30, 100)], width=8, state="readonly").pack(side="left", padx=(4, 10))
        ttk.Label(population_row, text="Gender", style="Inset.TLabel").pack(side="left")
        ttk.Combobox(population_row, textvariable=self.sim_generate_gender, values=["Random", "Male", "Female"], width=9, state="readonly").pack(side="left", padx=(4, 10))
        ttk.Label(population_row, text="Division", style="Inset.TLabel").pack(side="left")
        ttk.Combobox(population_row, textvariable=self.sim_generate_weight, values=["Random"] + WEIGHTS, width=17, state="readonly").pack(side="left", padx=(4, 10))
        ttk.Button(population_row, text="Generate Free Agents", style="Accent.TButton", command=self.generate_sim_lab_free_agents).pack(side="left", padx=(4, 10))
        self.sim_generate_status = ttk.Label(population_row, text="Generated fighters are added only to this save.", style="Inset.TLabel", anchor="w")
        self.sim_generate_status.pack(side="left", fill="x", expand=True)

        sim_panel, sim = self.section(self.sim_lab_tab, "QUICK FIGHT SIMULATOR")
        sim_panel.pack(fill="x", pady=(0, 6))
        sim_row = ttk.Frame(sim, style="Inset.TFrame")
        sim_row.pack(fill="x", pady=4)
        ttk.Label(sim_row, text="Gender", style="Inset.TLabel").pack(side="left")
        self.sim_gender_combo = ttk.Combobox(sim_row, textvariable=self.sim_gender_filter, values=["All", "Male", "Female"], width=9, state="readonly")
        self.sim_gender_combo.pack(side="left", padx=(4, 8))
        ttk.Label(sim_row, text="Division", style="Inset.TLabel").pack(side="left")
        self.sim_weight_combo = ttk.Combobox(sim_row, textvariable=self.sim_weight_filter, values=["All"] + WEIGHTS, width=17, state="readonly")
        self.sim_weight_combo.pack(side="left", padx=(4, 12))
        ttk.Label(sim_row, text="Red Corner", style="Inset.TLabel").pack(side="left")
        self.sim_combo_a = ttk.Combobox(sim_row, textvariable=self.sim_fighter_a, width=25, state="readonly")
        self.sim_combo_a.pack(side="left", padx=6)
        ttk.Label(sim_row, text="Blue Corner", style="Inset.TLabel").pack(side="left")
        self.sim_combo_b = ttk.Combobox(sim_row, textvariable=self.sim_fighter_b, width=25, state="readonly")
        self.sim_combo_b.pack(side="left", padx=6)
        self.sim_gender_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_sim_fighter_choices())
        self.sim_weight_combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_sim_fighter_choices())
        self.sim_combo_a.bind("<<ComboboxSelected>>", lambda _event: self.update_sim_fighter_cards())
        self.sim_combo_b.bind("<<ComboboxSelected>>", lambda _event: self.update_sim_fighter_cards())
        action_row = ttk.Frame(sim, style="Inset.TFrame")
        action_row.pack(fill="x", pady=(0, 4))
        ttk.Checkbutton(action_row, text="Title", variable=self.sim_title_fight).pack(side="left", padx=4)
        ttk.Checkbutton(action_row, text="Main Event", variable=self.sim_main_event).pack(side="left", padx=4)
        ttk.Label(action_row, text="Red Camp", style="Inset.TLabel").pack(side="left", padx=(12, 2))
        ttk.Spinbox(action_row, from_=0, to=16, textvariable=self.sim_camp_weeks_a, width=4).pack(side="left")
        ttk.Label(action_row, text="Blue Camp", style="Inset.TLabel").pack(side="left", padx=(8, 2))
        ttk.Spinbox(action_row, from_=0, to=16, textvariable=self.sim_camp_weeks_b, width=4).pack(side="left")
        ttk.Button(action_row, text="View Red Profile", command=lambda: self.open_sim_fighter_profile("red")).pack(side="left", padx=(12, 4))
        ttk.Button(action_row, text="View Blue Profile", command=lambda: self.open_sim_fighter_profile("blue")).pack(side="left", padx=4)
        ttk.Button(action_row, text="Refresh Fighters", command=self.refresh_sim_fighter_choices).pack(side="right", padx=4)
        ttk.Button(action_row, text="Sim Result", command=lambda: self.run_quick_fight_sim(False)).pack(side="right", padx=4)
        ttk.Button(action_row, text="Watch Fight", style="Accent.TButton", command=lambda: self.run_quick_fight_sim(True)).pack(side="right", padx=4)
        scout_row = ttk.Frame(sim, style="Inset.TFrame")
        scout_row.pack(fill="x", pady=(0, 4))
        red_card = tk.Frame(scout_row, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["red"])
        red_card.pack(side="left", fill="both", expand=True, padx=(0, 4))
        tk.Label(red_card, text="RED CORNER SCOUT REPORT", bg=self.colors["panel_dark"], fg=self.colors["red"], font=("Impact", 11), anchor="w").pack(fill="x", padx=8, pady=(5, 1))
        self.sim_profile_a = tk.Label(red_card, text="Select a fighter.", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8), justify="left", anchor="nw", wraplength=520)
        self.sim_profile_a.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        blue_card = tk.Frame(scout_row, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["gold"])
        blue_card.pack(side="left", fill="both", expand=True, padx=(4, 0))
        tk.Label(blue_card, text="BLUE CORNER SCOUT REPORT", bg=self.colors["panel_dark"], fg=self.colors["gold"], font=("Impact", 11), anchor="w").pack(fill="x", padx=8, pady=(5, 1))
        self.sim_profile_b = tk.Label(blue_card, text="Select a fighter.", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8), justify="left", anchor="nw", wraplength=520)
        self.sim_profile_b.pack(fill="both", expand=True, padx=8, pady=(0, 6))
        self.sim_result = ttk.Label(
            sim, text="Pick two fighters from the database.", style="Inset.TLabel",
            anchor="w", justify="left", wraplength=1120,
        )
        self.sim_result.pack(fill="x", pady=(2, 0))

        tournament_panel, tournament = self.section(self.sim_lab_tab, "SANDBOX TOURNAMENT")
        tournament_panel.pack(fill="x", pady=(0, 6))
        tournament_controls = ttk.Frame(tournament, style="Inset.TFrame")
        tournament_controls.pack(side="left", fill="y", padx=(0, 6))
        ttk.Label(tournament_controls, text="Bracket", style="Inset.TLabel").pack(anchor="w", padx=6, pady=(6, 0))
        ttk.Combobox(tournament_controls, textvariable=self.sim_tournament_size, values=[4, 8, 16], width=8, state="readonly").pack(anchor="w", padx=6, pady=4)
        ttk.Button(tournament_controls, text="Draw & Seed Field", command=self.auto_seed_sim_tournament).pack(fill="x", padx=6, pady=2)
        ttk.Button(tournament_controls, text="Run Tournament", style="Accent.TButton", command=self.run_simulation_tournament).pack(fill="x", padx=6, pady=(2, 6))
        ttk.Button(tournament_controls, text="View Bracket", command=self.open_sim_tournament_bracket).pack(fill="x", padx=6, pady=2)
        ttk.Button(tournament_controls, text="Watch Tournament Night", command=self.watch_simulation_tournament).pack(fill="x", padx=6, pady=(2, 6))
        entrants_frame = ttk.Frame(tournament, style="Inset.TFrame")
        entrants_frame.pack(side="left", fill="both", expand=True, padx=(0, 6))
        ttk.Label(entrants_frame, text="Entrants (select exactly the bracket size)", style="Inset.TLabel").pack(anchor="w", padx=6, pady=(4, 0))
        self.sim_tournament_list = tk.Listbox(entrants_frame, selectmode="extended", height=5, exportselection=False, font=("Tahoma", 9), bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff", activestyle="none")
        self.sim_tournament_list.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        bracket_frame = ttk.Frame(tournament, style="Inset.TFrame")
        bracket_frame.pack(side="left", fill="both", expand=True)
        ttk.Label(bracket_frame, text="Bracket Report", style="Inset.TLabel").pack(anchor="w", padx=6, pady=(4, 0))
        self.sim_tournament_report = tk.Text(bracket_frame, height=7, wrap="word", font=("Consolas", 8), bg=self.colors["tree"], fg=self.colors["text"], insertbackground=self.colors["text"], relief="flat", padx=8, pady=5)
        self.sim_tournament_report.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.sim_tournament_report.insert("end", "Choose a gender and division, then draw a field or select 4, 8, or 16 fighters. Run it to create a visual bracket and a watchable tournament night. Sandbox bouts never change careers.")
        self.sim_tournament_report.config(state="disabled")

        output_panel, output = self.section(self.sim_lab_tab, "AUDIT REPORT")
        output_panel.pack(fill="both", expand=True)
        self.audit_text = tk.Text(output, wrap="word", font=("Courier New", 9), bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=10)
        self.audit_text.pack(fill="both", expand=True)

    @staticmethod
    def event_log_line_tags(line, next_line=""):
        """Classify an existing log line for presentation without rewriting it."""
        value = str(line or "")
        lowered = value.lower()
        if not value.strip():
            return ("log_blank",)
        if str(next_line or "").strip().startswith("="):
            return ("log_event_header",)
        if value.strip().startswith("="):
            return ("log_divider",)
        if value.startswith(("Month ", "Week ", "Save system:", "Calendar:")):
            return ("log_system",)
        if " def. " in value or " - draw" in lowered or " - no contest" in lowered:
            return ("log_result",)
        if any(term in lowered for term in ("stoppage", "stops the contest", "knockout", "technical submission", " has to tap", " goes unconscious")):
            return ("log_highlight",)
        if value.startswith(("Signed ", "TBA filled ", "Renewed ", "Released ")):
            return ("log_action",)
        return ("log_body",)

    def render_event_log(self):
        """Render the complete office/event log with semantic visual accents."""
        if not hasattr(self, "log_text"):
            return
        text = self.log_text
        try:
            prior_scroll = text.yview()[0]
        except tk.TclError:
            prior_scroll = 0.0
        text.configure(state="normal")
        text.delete("1.0", "end")
        header_fg = self.accessible_tab_text(self.colors["panel_dark"], self.colors["gold"])
        content_accent = self.accessible_tab_text(self.colors["cream"], self.colors["gold"])
        text.tag_configure("log_event_header", foreground=header_fg, background=self.colors["panel_dark"], font=("Tahoma", 10, "bold"), spacing1=8, spacing3=2)
        text.tag_configure("log_divider", foreground=self.accessible_tab_text(self.colors["cream"], self.colors["line"]), spacing1=0, spacing3=3)
        text.tag_configure("log_result", foreground=content_accent, font=("Tahoma", 9, "bold"), spacing1=4, spacing3=2)
        text.tag_configure("log_highlight", foreground=header_fg, font=("Tahoma", 9, "bold"), background=self.colors["panel_dark"], spacing1=4, spacing3=2)
        text.tag_configure("log_system", foreground=self.colors["muted"], font=("Tahoma", 9, "italic"), spacing1=3, spacing3=2)
        text.tag_configure("log_action", foreground=self.colors["muted"], spacing1=3, spacing3=2)
        text.tag_configure("log_body", foreground=self.colors["text"], spacing1=2, spacing3=2)
        text.tag_configure("log_blank", spacing1=2, spacing3=2)
        raw_entries = getattr(self, "event_log", [])
        if isinstance(raw_entries, (list, tuple)):
            entries = list(raw_entries)
            source_count = len(raw_entries)
        elif raw_entries:
            entries = ["Event log unavailable: the retained log collection is not a list; load/migration review is required."]
            source_count = 0
        else:
            entries = []
            source_count = 0
        if not entries:
            entries = ["No event history yet. Book a card, then run the event to build the timeline."]
        for index, line in enumerate(entries):
            next_line = entries[index + 1] if index + 1 < len(entries) else ""
            text.insert("end", str(line), self.event_log_line_tags(line, next_line))
            text.insert("end", "\n")
        text.configure(state="disabled")
        try:
            text.yview_moveto(prior_scroll)
        except tk.TclError:
            pass
        if hasattr(self, "log_summary_var"):
            self.log_summary_var.set(f"{source_count:,} recorded log line(s)  ·  Read-only archive  ·  Refreshing this page never reruns a fight")

    def fight_night_archive_rows(self, limit=120):
        """Return a compact, identity-safe index for the Fight Night landing page.

        This is deliberately a presentation projection over the permanent result
        index and the retained replay shelves.  It does not repair a save, resolve
        current fighters, refresh an offer, or alter the source records.  Detailed
        replays are preferred so the watch action can open the original card; an
        index-only row remains browseable as a results-only card.
        """
        sources = []
        # The bounded replay shelves are first so a retained package supplies the
        # richer event metadata when it shares an identity with the compact index.
        sources.extend(list(getattr(self, "player_event_archive", []) or []))
        sources.extend(list(getattr(self, "ai_event_archive", []) or []))
        sources.extend(list(getattr(self, "result_index", []) or []))
        sources.extend(list(getattr(self, "result_records", []) or []))

        def source_key(record):
            if not isinstance(record, dict):
                return ""
            for field in ("record_id", "key", "detail_key"):
                value = str(record.get(field, "") or "").strip()
                if value:
                    return value
            resolver = getattr(self, "result_archive_key", None)
            if callable(resolver):
                try:
                    value = str(resolver(record) or "").strip()
                    if value:
                        return value
                except Exception:
                    pass
            # Keep legacy, identity-less rows visible without claiming the key
            # is durable.  The fingerprint is only a display de-duplicator.
            fields = ("date", "company", "event", "event_name", "summary")
            return "legacy:" + "|".join(str(record.get(field, "") or "") for field in fields)

        try:
            max_rows = None if limit is None else max(0, int(limit))
        except (TypeError, ValueError):
            max_rows = 120
        if max_rows == 0:
            return []
        replay_keys = set()
        for record in (
            list(getattr(self, "player_event_archive", []) or [])
            + list(getattr(self, "ai_event_archive", []) or [])
            + list(getattr(self, "result_records", []) or [])
        ):
            if not isinstance(record, dict):
                continue
            if not (record.get("log") or record.get("fight_logs")):
                continue
            key = source_key(record)
            if key:
                replay_keys.add(key)
        rows = []
        seen = set()
        for record in sources:
            if not isinstance(record, dict):
                continue
            key = source_key(record)
            if not key or key in seen:
                continue
            seen.add(key)
            logs = record.get("fight_logs", [])
            compact = record.get("bout_results", [])
            replay = bool(record.get("log") or (isinstance(logs, list) and logs)) or key in replay_keys
            if isinstance(logs, list):
                bout_count = len(logs)
            elif isinstance(compact, list):
                bout_count = len(compact)
            else:
                bout_count = 0
            company = str(record.get("company", "") or "").strip() or "Promotion unavailable"
            event_name = str(record.get("event", record.get("event_name", "")) or "").strip() or "Archived event"
            date_value = str(record.get("date", "") or record.get("summary", "") or "").strip() or "Date unavailable"
            rows.append({
                "row_id": f"fight-night:{key}",
                "record_id": key,
                "date": date_value,
                "company": company,
                "event": event_name,
                "fights": bout_count,
                "replay": replay,
                "status": "Replay ready" if replay else "Results only",
                "record": record,
            })
            if max_rows is not None and len(rows) >= max_rows:
                break
        return rows

    def build_log_tab(self):
        self.screen_header(self.log_tab, "FIGHT NIGHT", "Watch the card that is due, browse recorded replays, or read the complete office log")

        access_panel, access = self.section(self.log_tab, "FIGHT NIGHT CONTROL CENTRE")
        access_panel.pack(fill="x", pady=(0, 6))
        self.fight_night_status_var = tk.StringVar(value="")
        ttk.Label(access, textvariable=self.fight_night_status_var, style="Inset.TLabel", anchor="w", wraplength=900).pack(fill="x", padx=8, pady=(5, 3))
        action_row = ttk.Frame(access, style="Inset.TFrame")
        action_row.pack(fill="x", padx=5, pady=(0, 5))
        ttk.Button(action_row, text="Watch Due Event", style="Accent.TButton", command=self.watch_due_event).pack(side="left", padx=3)
        ttk.Button(action_row, text="Browse Results", command=lambda: self.select_tab("results")).pack(side="left", padx=3)
        ttk.Button(action_row, text="Watch Latest Replay", command=lambda: watch_latest_replay()).pack(side="left", padx=3)
        ttk.Button(action_row, text="Jump to Full Log", command=lambda: jump_to_log()).pack(side="right", padx=3)
        ttk.Label(access, text="The archive is read-only. Opening a replay never reapplies its results; the full log below retains every original line.", style="Muted.TLabel", anchor="w").pack(fill="x", padx=8, pady=(0, 5))

        archive_panel, archive_inner = self.section(self.log_tab, "RECORDED EVENTS")
        archive_panel.pack(fill="x", pady=(0, 6))
        archive_toolbar = ttk.Frame(archive_inner, style="Inset.TFrame")
        archive_toolbar.pack(fill="x", padx=5, pady=(3, 4))
        self.fight_night_archive_summary_var = tk.StringVar(value="")
        ttk.Label(archive_toolbar, textvariable=self.fight_night_archive_summary_var, style="Inset.TLabel", anchor="w").pack(side="left", fill="x", expand=True, padx=6, pady=3)
        archive_tree_frame = ttk.Frame(archive_inner, style="Panel.TFrame")
        archive_tree_frame.pack(fill="x", padx=5, pady=(0, 5))
        archive_columns = ("date", "company", "event", "fights", "status")
        self.fight_night_archive_tree = ttk.Treeview(archive_tree_frame, columns=archive_columns, show="headings", selectmode="browse", height=5)
        for column, heading, width in (("date", "Date", 112), ("company", "Promotion", 150), ("event", "Event", 250), ("fights", "Bouts", 55), ("status", "Access", 105)):
            self.fight_night_archive_tree.heading(column, text=heading)
            self.fight_night_archive_tree.column(column, width=width, minwidth=48, anchor="center")
        for column in ("company", "event", "status"):
            self.fight_night_archive_tree.column(column, anchor="w")
        archive_scroll = ttk.Scrollbar(archive_tree_frame, orient="vertical", command=self.fight_night_archive_tree.yview)
        self.fight_night_archive_tree.configure(yscrollcommand=archive_scroll.set)
        self.fight_night_archive_tree.pack(side="left", fill="both", expand=True)
        archive_scroll.pack(side="right", fill="y")
        if hasattr(self, "semantic_status_palette"):
            palette = self.semantic_status_palette(getattr(self, "colors", {}) or {})
            self.fight_night_archive_tree.tag_configure("results_only", foreground=palette.get("neutral", self.colors["muted"]))
            self.fight_night_archive_tree.tag_configure("review", foreground=palette.get("warning", self.colors["gold"]))

        archive_detail = tk.StringVar(value="Select a recorded event to see its access level and preserved identity.")
        ttk.Label(archive_inner, textvariable=archive_detail, style="Muted.TLabel", anchor="w", wraplength=900).pack(fill="x", padx=8, pady=(0, 5))

        log_panel, log_inner = self.section(self.log_tab, "FULL EVENT LOG")
        log_panel.pack(fill="both", expand=True)
        toolbar = ttk.Frame(log_inner, style="Inset.TFrame")
        toolbar.pack(fill="x", padx=5, pady=(3, 5))
        self.log_summary_var = tk.StringVar(value="")
        ttk.Label(toolbar, textvariable=self.log_summary_var, style="Inset.TLabel", anchor="w").pack(side="left", fill="x", expand=True, padx=6, pady=5)
        ttk.Label(toolbar, text="Colours mark event headers, results, key moments and office actions; all original text is retained.", style="Inset.TLabel", anchor="e").pack(side="right", padx=6, pady=5)
        reader = ttk.Frame(log_inner, style="Panel.TFrame")
        reader.pack(fill="both", expand=True, padx=5, pady=(0, 5))
        reader.rowconfigure(0, weight=1)
        reader.columnconfigure(0, weight=1)
        self.log_text = tk.Text(reader, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=12, pady=10, relief="flat")
        log_scroll = ttk.Scrollbar(reader, orient="vertical", command=self.log_text.yview)
        self.log_text.configure(yscrollcommand=log_scroll.set)
        self.log_text.grid(row=0, column=0, sticky="nsew")
        log_scroll.grid(row=0, column=1, sticky="ns")

        archive_rows_by_id = {}

        def refresh_archive():
            previous = self.fight_night_archive_tree.selection()
            previous_id = previous[0] if previous else ""
            self.fight_night_archive_tree.delete(*self.fight_night_archive_tree.get_children())
            archive_rows_by_id.clear()
            rows = self.fight_night_archive_rows()
            for row in rows:
                iid = row["row_id"]
                if iid in archive_rows_by_id:
                    iid = f"{iid}#2"
                archive_rows_by_id[iid] = row
                self.fight_night_archive_tree.insert("", "end", iid=iid, tags=() if row["replay"] else ("results_only",), values=(row["date"], row["company"], row["event"], row["fights"], row["status"]))
            self.fight_night_archive_summary_var.set(f"{len(rows):,} recorded event(s) indexed  ·  {sum(1 for row in rows if row['replay']):,} replay-ready  ·  results-only cards remain browseable")
            if rows:
                iid = previous_id if previous_id in archive_rows_by_id else next(iter(archive_rows_by_id))
                self.fight_night_archive_tree.selection_set(iid)
                self.fight_night_archive_tree.focus(iid)
            show_archive_detail()

        def show_archive_detail(_event=None):
            selected = self.fight_night_archive_tree.selection()
            row = archive_rows_by_id.get(selected[0]) if selected else None
            if not row:
                archive_detail.set("Select a recorded event to see its access level and preserved identity.")
                return
            identity_note = "saved archive identity" if not row["record_id"].startswith("legacy:") else "legacy display identity (not durable)"
            archive_detail.set(f"{row['event']}  ·  {row['company']}  ·  {row['status']}  ·  {identity_note}. Double-click to open the saved card.")

        def open_selected_archive(_event=None):
            selected = self.fight_night_archive_tree.selection()
            row = archive_rows_by_id.get(selected[0]) if selected else None
            if not row:
                return
            record = row["record"]
            if row["replay"] and callable(getattr(self, "watch_result_card", None)):
                self.watch_result_card(record)
            elif callable(getattr(self, "open_result_card_window", None)):
                # Permanent index rows keep compact ``bout_results`` rather
                # than full replay logs.  Let the existing reader expand that
                # compact evidence for display without changing the saved row.
                display_record = record
                expander = getattr(self, "result_record_with_compact_bouts", None)
                if callable(expander):
                    try:
                        display_record = expander(record)
                    except Exception:
                        display_record = record
                self.open_result_card_window(display_record)

        def watch_latest_replay():
            row = next((item for item in self.fight_night_archive_rows() if item["replay"]), None)
            if not row:
                archive_detail.set("No retained Fight Night replay is available yet. Results-only cards remain available in Browse Results.")
                return
            if callable(getattr(self, "watch_result_card", None)):
                self.watch_result_card(row["record"])

        def jump_to_log():
            self.log_text.focus_set()
            self.log_text.yview_moveto(0.0)

        self.fight_night_archive_tree.bind("<<TreeviewSelect>>", show_archive_detail)
        self.fight_night_archive_tree.bind("<Double-1>", open_selected_archive)
        self._fight_night_archive_refresh = refresh_archive
        refresh_archive()
        self.refresh_fight_night_landing()
        self.render_event_log()

    def refresh_fight_night_landing(self):
        """Refresh the Fight Night landing projection without touching game state."""
        status_var = getattr(self, "fight_night_status_var", None)
        if status_var is None:
            return
        refresher = getattr(self, "_fight_night_archive_refresh", None)
        if callable(refresher):
            try:
                refresher()
            except tk.TclError:
                # The page may be tearing down during a theme/window rebuild.
                pass
        try:
            due = [event for event in self.sorted_scheduled_events() if self.is_event_due(event)]
        except Exception:
            due = []
        if due:
            status_var.set(f"{len(due)} event(s) due now  ·  Watch Due Event opens the live card without changing the archive.")
            return
        try:
            upcoming = next(iter(self.sorted_scheduled_events()), None)
        except Exception:
            upcoming = None
        if upcoming:
            try:
                when = self.event_date_label(upcoming)
            except Exception:
                when = "a future date"
            status_var.set(f"No event is due right now  ·  Next card: {upcoming.get('name', 'Scheduled event')} on {when}. Browse recorded cards or read the full office log below.")
        else:
            status_var.set("No event is due right now  ·  Browse recorded cards or read the full office log below.")
