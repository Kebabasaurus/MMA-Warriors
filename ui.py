import json
import random
import sys
import traceback
from datetime import datetime
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from models import Fighter, Gym, Promotion


class UIMixin:
    def configure_style(self):
        style = ttk.Style()
        style.theme_use("clam")
        self.themes = {
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
        style.configure("Panel.TLabel", background=self.colors["panel"], foreground=self.colors["text"])
        style.configure("Inset.TLabel", background=self.colors["cream"], foreground=self.colors["text"])
        style.configure("Stat.TLabel", font=("Tahoma", 8, "bold"), background=self.colors["chrome2"], foreground=self.colors["text"])
        style.configure("TButton", font=("Tahoma", 8, "bold"), padding=(8, 4), background=self.colors["button"], foreground=self.colors["button_text"], borderwidth=1)
        style.map("TButton", background=[("active", self.colors["panel_dark"])])
        style.configure("Accent.TButton", font=("Tahoma", 8, "bold"), background=self.colors["red"], foreground="#ffffff")
        style.map("Accent.TButton", background=[("active", self.colors["gold"])], foreground=[("active", "#111111")])
        # Sidebar navigation buttons: default look, plus a highlighted "active screen" look.
        style.configure("Nav.TButton", font=("Tahoma", 8, "bold"), padding=(8, 4), anchor="w", background=self.colors["button"], foreground=self.colors["button_text"], borderwidth=1)
        style.map("Nav.TButton", background=[("active", self.colors["panel_dark"])])
        style.configure("NavActive.TButton", font=("Tahoma", 8, "bold"), padding=(8, 4), anchor="w", background=self.colors["gold"], foreground="#111111", borderwidth=1)
        style.map("NavActive.TButton", background=[("active", self.colors["gold"])], foreground=[("active", "#111111")])
        input_bg = self.colors["cream"]
        input_fg = self.colors["text"]
        selected_bg = self.colors["red"]
        style.configure("TEntry", fieldbackground=input_bg, background=input_bg, foreground=input_fg, insertcolor=input_fg, bordercolor=self.colors["line"], lightcolor=self.colors["line"], darkcolor=self.colors["line"])
        style.map("TEntry", fieldbackground=[("disabled", self.colors["panel"]), ("readonly", input_bg), ("focus", input_bg)], foreground=[("disabled", self.colors["muted"]), ("readonly", input_fg), ("focus", input_fg)])
        style.configure("TSpinbox", fieldbackground=input_bg, background=input_bg, foreground=input_fg, insertcolor=input_fg, arrowcolor=input_fg, bordercolor=self.colors["line"], lightcolor=self.colors["line"], darkcolor=self.colors["line"])
        style.map("TSpinbox", fieldbackground=[("disabled", self.colors["panel"]), ("readonly", input_bg), ("focus", input_bg)], foreground=[("disabled", self.colors["muted"]), ("readonly", input_fg), ("focus", input_fg)])
        style.configure("TCombobox", fieldbackground=input_bg, background=input_bg, foreground=input_fg, arrowcolor=input_fg, selectbackground=selected_bg, selectforeground="#ffffff", bordercolor=self.colors["line"], lightcolor=self.colors["line"], darkcolor=self.colors["line"])
        style.map("TCombobox", fieldbackground=[("disabled", self.colors["panel"]), ("readonly", input_bg), ("focus", input_bg)], background=[("readonly", input_bg), ("active", self.colors["panel_dark"])], foreground=[("disabled", self.colors["muted"]), ("readonly", input_fg), ("focus", input_fg)], selectbackground=[("readonly", selected_bg), ("focus", selected_bg)], selectforeground=[("readonly", "#ffffff"), ("focus", "#ffffff")])
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
        style.configure("TNotebook", background=self.colors["chrome"], borderwidth=0)
        style.configure("TNotebook.Tab", font=("Tahoma", 8, "bold"), padding=(18, 5), background="#777268", foreground="#111111")
        style.map("TNotebook.Tab", background=[("selected", self.colors["paper"])])
        style.configure("Hidden.TNotebook", background=self.colors["chrome"], borderwidth=0)
        style.layout("Hidden.TNotebook.Tab", [])
        style.configure("Treeview", font=("Tahoma", 8), background=self.colors["tree"], fieldbackground=self.colors["tree"], foreground=self.colors["text"], rowheight=22, borderwidth=0)
        style.configure("Treeview.Heading", font=("Tahoma", 8, "bold"), background=self.colors["tree_head"], foreground="#ffffff", relief="flat")

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
            width = max(1, canvas.winfo_width(), inner.winfo_reqwidth())
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

        def bind_wheel(_event=None):
            canvas.bind_all("<MouseWheel>", wheel)
            canvas.bind_all("<Button-4>", lambda event: linux_wheel(event, -1))
            canvas.bind_all("<Button-5>", lambda event: linux_wheel(event, 1))

        def unbind_wheel(_event=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        inner.bind("<Configure>", schedule_fit)
        canvas.bind("<Configure>", schedule_fit)
        shell.bind("<Enter>", bind_wheel)
        shell.bind("<Leave>", unbind_wheel)
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
        shell = ttk.Frame(self.root, style="Chrome.TFrame")
        shell.pack(fill="both", expand=True)

        titlebar = ttk.Frame(shell, style="Chrome.TFrame")
        titlebar.pack(fill="x")
        self.logo_canvas = tk.Canvas(titlebar, width=76, height=42, bg=self.colors["chrome"], highlightthickness=0)
        self.logo_canvas.pack(side="left", padx=(12, 4), pady=5)
        self.draw_logo()
        ttk.Label(titlebar, text=GAME_NAME.upper(), style="Title.TLabel").pack(side="left", padx=8, pady=8)
        self.theme_name_var = tk.StringVar(value=getattr(self, "theme_name", "Fight Night"))
        ttk.Button(titlebar, text="Apply Theme", command=self.apply_selected_theme).pack(side="right", padx=(2, 10))
        ttk.Combobox(titlebar, values=list(self.themes.keys()), textvariable=self.theme_name_var, state="readonly", width=20, height=22).pack(side="right", padx=(2, 6))
        ttk.Label(titlebar, text="Theme", style="Chrome.TLabel").pack(side="right", padx=(12, 2))
        ttk.Label(titlebar, text="Promoter Office", style="Chrome.TLabel").pack(side="right", padx=18)

        self.statusbar = ttk.Frame(shell, style="Chrome.TFrame")
        self.statusbar.pack(fill="x", padx=8, pady=(0, 4))
        self.stat_month = ttk.Label(self.statusbar, width=16, anchor="center", style="Stat.TLabel")
        self.stat_cash = ttk.Label(self.statusbar, width=18, anchor="center", style="Stat.TLabel")
        self.stat_pop = ttk.Label(self.statusbar, width=20, anchor="center", style="Stat.TLabel")
        self.stat_stability = ttk.Label(self.statusbar, width=13, anchor="center", style="Stat.TLabel")
        for label in (self.stat_month, self.stat_cash, self.stat_pop, self.stat_stability):
            label.pack(side="left", padx=2, ipady=4)

        # Advancing is always visible here, even when the left navigation needs
        # scrolling on a laptop-sized display. Spectator fast-forward remains in
        # the Game Menu; this normal one-week button is hidden in observer saves.
        self.advance_activity = ttk.Frame(self.statusbar, style="Chrome.TFrame")
        self.advance_activity.pack(side="right", padx=(6, 2))
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
            ("TODAY", (("Assistant", "assistant"), ("Inbox", "inbox"), ("Media Desk", "website"), ("Fight Night", "log"))),
            ("PROMOTION", (("Roster", "roster"), ("Matchmaking", "booking"), ("Contracts", "contracts"), ("Free Agents", "market"), ("Scouting", "scouting"), ("Fight Academy", "academy"), ("Staff", "staff"), ("Finance", "finance"))),
            ("WORLD", (("World", "world"), ("Regional Prospects", "regional_prospects"), ("Fighter Search", "fighter_search"), ("Combat Sports", "combat_sports"), ("Companies", "companies"), ("Rankings", "rankings"), ("Results", "results"), ("Regions", "regions"))),
            ("TOOLS", (("Game & Saves", "game_menu"), ("Company Rules", "company_editor"), ("World Editor", "editor"), ("Sim Lab", "sim_lab"))),
        )
        self.nav_buttons = {}
        for heading, entries in groups:
            ttk.Label(nav, text=heading, anchor="center", style="Section.TLabel").pack(fill="x", padx=6, pady=(5, 2), ipady=2)
            for text, tab in entries:
                command = self.open_combat_sports_window if tab == "combat_sports" else (self.open_academy_window if tab == "academy" else (lambda name=tab: self.select_tab(name)))
                button = ttk.Button(nav, text=text, style="Nav.TButton", command=command)
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
            ("editor", "editor_tab", "Editor"),
            ("sim_lab", "sim_lab_tab", "Sim Lab"),
            ("log", "log_tab", "Fight Night"),
        )
        for name, attr, label in tab_specs:
            page, content = self.create_main_tab()
            self.tab_pages[name] = page
            setattr(self, attr, content)
            self.tabs.add(page, text=label)

        self.build_game_menu_tab()
        self.build_website_tab()
        self.build_assistant_tab()
        self.build_roster_tab()
        self.build_contracts_tab()
        self.build_companies_tab()
        self.build_regions_tab()
        self.build_results_tab()
        self.build_company_editor_tab()
        self.build_inbox_tab()
        self.build_staff_tab()
        self.build_scouting_tab()
        self.build_finance_tab()
        self.build_booking_tab()
        self.build_market_tab()
        self.build_world_tab()
        self.build_regional_prospects_tab()
        self.build_fighter_search_tab()
        self.build_rankings_tab()
        self.build_editor_tab()
        self.build_sim_lab_tab()
        self.build_log_tab()
        self.retheme_plain_widgets(self.root)
        self.select_tab("game_menu")

    def apply_selected_theme(self):
        self.theme_name = self.theme_name_var.get()
        self.configure_style()
        self.retheme_plain_widgets(self.root)
        for pane in getattr(self, "vertical_resize_panes", []):
            try:
                pane.configure(bg=self.colors["panel"])
            except tk.TclError:
                pass
        spacer = getattr(self, "market_resize_spacer", None)
        if spacer:
            spacer.configure(bg=self.colors["paper"])
        self.draw_logo()

    def draw_logo(self):
        if not hasattr(self, "logo_canvas"):
            return
        c = self.logo_canvas
        c.delete("all")
        c.configure(bg=self.colors["chrome"])
        c.create_polygon(6, 36, 24, 6, 38, 36, fill=self.colors["red"], outline=self.colors["gold"], width=2)
        c.create_polygon(38, 36, 52, 6, 70, 36, fill=self.colors["panel_dark"], outline=self.colors["gold"], width=2)
        c.create_text(38, 24, text="MW", fill=self.colors["gold"], font=("Impact", 17))

    def retheme_plain_widgets(self, widget):
        for canvas in getattr(self, "scrollable_canvases", []):
            try:
                canvas.configure(bg=self.colors["paper"])
            except tk.TclError:
                pass
        for child in widget.winfo_children():
            if isinstance(child, tk.Text):
                child.configure(bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
            elif isinstance(child, tk.Listbox):
                child.configure(bg=self.colors["tree"], fg=self.colors["text"], selectbackground=self.colors["red"], selectforeground="#ffffff")
            elif isinstance(child, (tk.Entry, tk.Spinbox)):
                try:
                    child.configure(bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
                except tk.TclError:
                    pass
            self.retheme_plain_widgets(child)

    def select_tab(self, name):
        lookup = {
            "game_menu": self.tab_pages["game_menu"],
            "website": self.tab_pages["website"],
            "assistant": self.tab_pages["assistant"],
            "roster": self.tab_pages["roster"],
            "contracts": self.tab_pages["contracts"],
            "companies": self.tab_pages["companies"],
            "regions": self.tab_pages["regions"],
            "results": self.tab_pages["results"],
            "company_editor": self.tab_pages["company_editor"],
            "inbox": self.tab_pages["inbox"],
            "staff": self.tab_pages["staff"],
            "scouting": self.tab_pages["scouting"],
            "finance": self.tab_pages["finance"],
            "booking": self.tab_pages["booking"],
            "market": self.tab_pages["market"],
            "world": self.tab_pages["world"],
            "regional_prospects": self.tab_pages["regional_prospects"],
            "fighter_search": self.tab_pages["fighter_search"],
            "rankings": self.tab_pages["rankings"],
            "editor": self.tab_pages["editor"],
            "sim_lab": self.tab_pages["sim_lab"],
            "log": self.tab_pages["log"],
        }
        self.current_tab_name = name
        self.tabs.select(lookup[name])
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
        pane._resize_fraction = initial_fraction
        pane._resize_min_top = min_top
        pane._resize_min_bottom = min_bottom
        pane.bind("<Configure>", lambda _event, target=pane: self.initialize_vertical_resizer(target), add="+")
        if not hasattr(self, "vertical_resize_panes"):
            self.vertical_resize_panes = []
        self.vertical_resize_panes.append(pane)
        return pane

    def initialize_vertical_resizer(self, pane):
        """Position a new split once; subsequent drags belong entirely to the player."""
        if getattr(pane, "_resize_ready", False) or pane.winfo_height() < 260:
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
        min_top = getattr(pane, "_resize_min_top", 180)
        min_bottom = getattr(pane, "_resize_min_bottom", 80)
        fraction = getattr(pane, "_resize_fraction", 0.7)
        top_height = max(min_top, min(height - min_bottom, round(height * fraction)))
        try:
            pane.sash_place(0, 0, top_height)
            pane._resize_ready = True
        except tk.TclError:
            # Both child panes may not exist until Tk completes this layout pass.
            pane.after_idle(lambda: self.initialize_vertical_resizer(pane))

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
        save_panel, save_inner = self.section(body, "SAVE GAMES")
        save_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
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
        ttk.Button(folder_row, text="Create Folder", command=self.create_save_folder).grid(row=1, column=2, sticky="ew", padx=3, pady=(4, 0))
        ttk.Button(folder_row, text="Move Selected", command=self.move_selected_save_to_folder).grid(row=1, column=3, sticky="ew", padx=3, pady=(4, 0))
        for column in (1, 3):
            folder_row.columnconfigure(column, weight=1)
        self.save_slot_list = tk.Listbox(save_inner, font=("Tahoma", 9), bg="#c9c9c9")
        self.save_slot_list.pack(fill="both", expand=True)
        row = ttk.Frame(save_inner, style="Inset.TFrame")
        row.pack(fill="x", pady=6)
        self.save_slot_name = tk.StringVar(value="Game 1")
        ttk.Entry(row, textvariable=self.save_slot_name, width=18).grid(row=0, column=0, columnspan=4, sticky="ew", padx=4, pady=2)
        ttk.Button(row, text="Save Slot", command=self.save_selected_slot).grid(row=1, column=0, sticky="ew", padx=3, pady=2)
        ttk.Button(row, text="Load Slot", command=self.load_selected_slot).grid(row=1, column=1, sticky="ew", padx=3, pady=2)
        ttk.Button(row, text="Copy Slot", command=self.duplicate_selected_save).grid(row=1, column=2, sticky="ew", padx=3, pady=2)
        ttk.Button(row, text="Delete Slot", command=self.delete_selected_slot).grid(row=1, column=3, sticky="ew", padx=3, pady=2)
        for col in range(4):
            row.columnconfigure(col, weight=1)
        save_tools = ttk.Frame(save_inner, style="Inset.TFrame")
        save_tools.pack(fill="x", pady=(0, 6))
        ttk.Button(save_tools, text="Backup Slot", command=self.backup_selected_slot).grid(row=0, column=0, sticky="ew", padx=3, pady=2)
        ttk.Button(save_tools, text="Restore Backup", command=self.open_save_backup_manager).grid(row=0, column=1, sticky="ew", padx=3, pady=2)
        ttk.Button(save_tools, text="Open Saves Folder", command=self.open_saves_folder).grid(row=0, column=2, sticky="ew", padx=3, pady=2)
        ttk.Button(save_tools, text="Game Settings", command=self.open_game_settings_window).grid(row=1, column=0, columnspan=3, sticky="ew", padx=3, pady=2)
        for col in range(3):
            save_tools.columnconfigure(col, weight=1)
        autosave_row = ttk.Frame(save_inner, style="Inset.TFrame")
        autosave_row.pack(fill="x", pady=(0, 6))
        self.autosave_status_label = ttk.Label(autosave_row, text="Autosaves loading...", style="Inset.TLabel")
        self.autosave_status_label.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=2)
        for col, (text, command) in enumerate((
            ("Auto", self.toggle_autosaves),
        )):
            ttk.Button(autosave_row, text=text, command=command).grid(row=1, column=col, sticky="ew", padx=2, pady=2)
            autosave_row.columnconfigure(col, weight=1)
        self.save_manager_status = ttk.Label(save_inner, text="", style="Inset.TLabel", anchor="w")
        self.save_manager_status.pack(fill="x", padx=4, pady=(0, 4))
        db_panel, db_inner = self.section(body, "DATABASE / WORLD")
        db_panel.pack(side="left", fill="both", expand=True)
        self.database_list = tk.Listbox(db_inner, font=("Tahoma", 9), bg="#c9c9c9")
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
            ("Reset Default", self.reset_default_universe_database, None),
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
        ttk.Button(start_button_row, text="Create Your Own Promotion", command=self.open_create_promotion_mode).pack(side="left", fill="x", expand=True, padx=(4, 0))
        ttk.Label(start_inner, text="Spectator Mode starts a fresh observer save with no player company.", style="Inset.TLabel", wraplength=260).pack(fill="x", padx=6, pady=(0, 4))

        self.spectator_sim_panel, spectator = self.section(db_inner, "SPECTATOR WORLD SIMULATION")
        self.spectator_sim_panel.pack(fill="x", pady=(8, 0))
        self.spectator_sim_status = ttk.Label(spectator, text="Observer controls are available in Spectator Mode.", style="Inset.TLabel", wraplength=260)
        self.spectator_sim_status.pack(fill="x", padx=6, pady=(4, 2))
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
            text="Select an action to see its cost, likely reach, risk, and whether a target is required.",
            style="Inset.TLabel",
            justify="left",
            anchor="w",
            wraplength=980,
        )
        self.media_action_summary.grid(row=2, column=0, columnspan=4, sticky="ew", padx=5, pady=(2, 4))

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

        offers_frame = ttk.Frame(rights, style="Panel.TFrame")
        offers_frame.pack(fill="both", expand=True)
        self.media_offers_tree = ttk.Treeview(
            offers_frame,
            columns=("partner", "type", "reach", "fee", "term", "events", "requirements"),
            show="headings",
            height=6,
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
        offer_buttons = ttk.Frame(rights, style="Inset.TFrame")
        offer_buttons.pack(fill="x", pady=(5, 0))
        ttk.Button(offer_buttons, text="Accept Selected", style="Accent.TButton", command=lambda: self.media_accept_selected_offer()).pack(side="left", padx=3, pady=3)
        ttk.Button(offer_buttons, text="Reject Selected", command=lambda: self.media_reject_selected_offer()).pack(side="left", padx=3, pady=3)
        ttk.Button(offer_buttons, text="Refresh Offers", command=lambda: self.media_refresh_offers()).pack(side="left", padx=3, pady=3)
        ttk.Button(offer_buttons, text="End Active Deal", command=lambda: self.media_terminate_contract()).pack(side="right", padx=3, pady=3)

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
        self.screen_header(self.assistant_tab, "WEEKLY COMMAND CENTRE", "The next decisions, show readiness, runway, division health, and attributed changes")
        top_panel, top = self.section(self.assistant_tab, "THIS WEEK")
        top_panel.pack(fill="x", pady=(0, 6))
        self.assistant_snapshot = ttk.Label(top, text="", justify="left", anchor="w", style="Inset.TLabel")
        self.assistant_snapshot.pack(fill="x", padx=8, pady=6)
        self.assistant_kpis = {}
        kpi_row = ttk.Frame(top, style="Inset.TFrame")
        kpi_row.pack(fill="x", padx=5, pady=(0, 5))
        for key, label in (("show", "NEXT SHOW"), ("card", "CARD"), ("contracts", "CONTRACTS"),
                           ("divisions", "DIVISION HEALTH"), ("runway", "RUNWAY"), ("medical", "MEDICAL")):
            cell = tk.Frame(kpi_row, bg=self.colors["panel_dark"], highlightthickness=1, highlightbackground=self.colors["line"])
            cell.pack(side="left", fill="x", expand=True, padx=2)
            tk.Label(cell, text=label, bg=self.colors["panel_dark"], fg=self.colors["muted"], font=("Tahoma", 7, "bold")).pack(anchor="w", padx=7, pady=(4, 0))
            value = tk.Label(cell, text="-", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 10, "bold"), anchor="w")
            value.pack(fill="x", padx=7, pady=(0, 5))
            self.assistant_kpis[key] = value
        quick = ttk.Frame(top, style="Inset.TFrame")
        quick.pack(fill="x", padx=5, pady=(0, 6))
        for label, tab in (("Matchmaking", "booking"), ("Inbox", "inbox"), ("Contracts", "contracts"), ("Finance", "finance"), ("Results", "results")):
            ttk.Button(quick, text=label, command=lambda name=tab: self.select_tab(name)).pack(side="left", padx=3)
        ttk.Button(quick, text="Guided First Week", command=self.open_guided_first_week).pack(side="right", padx=3)

        body = ttk.Frame(self.assistant_tab, style="Panel.TFrame")
        body.pack(fill="both", expand=True)
        msg_panel, msg = self.section(body, "PRIORITY DECISIONS")
        msg_panel.pack(side="left", fill="both", expand=True, padx=(0, 3))
        self.assistant_messages = ttk.Treeview(msg, columns=("priority", "notice", "action"), show="headings", height=14)
        for column, label, width in (("priority", "!", 36), ("notice", "Decision / Risk", 510), ("action", "Open", 90)):
            self.assistant_messages.heading(column, text=label)
            self.assistant_messages.column(column, width=width, anchor="w")
        self.assistant_messages.tag_configure("urgent", foreground="#ff9b9b")
        self.assistant_messages.tag_configure("normal", foreground="#ffe08a")
        self.assistant_messages.pack(fill="both", expand=True)
        self.assistant_messages.bind("<Double-1>", lambda _event: self.open_selected_assistant_notice())
        ttk.Button(msg, text="Open Selected Context", style="Accent.TButton", command=self.open_selected_assistant_notice).pack(anchor="e", pady=(6, 0))

        change_panel, changes = self.section(body, "WHAT CHANGED")
        change_panel.pack(side="left", fill="both", expand=True, padx=(3, 0))
        change_table = ttk.Frame(changes, style="Inset.TFrame")
        change_table.pack(fill="both", expand=True)
        self.assistant_changes = ttk.Treeview(change_table, columns=("date", "change", "why"), show="headings", height=14)
        for column, label, width in (("date", "When", 90), ("change", "Attributed Delta", 190), ("why", "Why", 390)):
            self.assistant_changes.heading(column, text=label)
            self.assistant_changes.column(column, width=width, anchor="w")
        change_y = ttk.Scrollbar(change_table, orient="vertical", command=self.assistant_changes.yview)
        self.assistant_changes.configure(yscrollcommand=change_y.set)
        self.assistant_changes.pack(side="left", fill="both", expand=True)
        change_y.pack(side="right", fill="y")

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
        self.company_profile = tk.Text(profile, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=10, pady=10)
        self.company_profile.pack(fill="both", expand=True)

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
        self.region_list = tk.Listbox(region_inner, font=("Tahoma", 9), bg="#c9c9c9")
        self.region_list.pack(fill="both", expand=True)
        self.region_list.bind("<<ListboxSelect>>", lambda _e: self.refresh_region_profile())
        info_panel, info = self.section(body, "REGION PROFILE")
        info_panel.pack(side="left", fill="both", expand=True)
        self.region_profile = tk.Text(info, wrap="word", font=("Tahoma", 10, "italic"), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=14, pady=14)
        self.region_profile.pack(fill="both", expand=True)
        region_actions = ttk.Frame(info, style="Inset.TFrame")
        region_actions.pack(fill="x", pady=(6, 0))
        ttk.Button(region_actions, text="Open Region Hub", style="Accent.TButton", command=self.open_selected_region_hub).pack(side="left", padx=4)
        ttk.Button(region_actions, text="View Local Gyms", command=lambda: self.open_selected_region_hub("Gyms")).pack(side="left", padx=4)
        ttk.Button(region_actions, text="View Local Fighters", command=lambda: self.open_selected_region_hub("Fighters")).pack(side="left", padx=4)

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
        self.results_text = tk.Text(detail, wrap="word", font=("Courier New", 9), bg=self.colors["cream"], fg=self.colors["text"], padx=10, pady=10)
        self.results_text.pack(fill="both", expand=True)

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
            ("Mixed Gender", self.toggle_mixed_gender_rule),
            ("+ Round Min", lambda: self.adjust_round_length(1)),
            ("- Round Min", lambda: self.adjust_round_length(-1)),
            ("+ Reg Round", lambda: self.adjust_regular_rounds(1)),
            ("- Reg Round", lambda: self.adjust_regular_rounds(-1)),
            ("+ Title Round", lambda: self.adjust_title_rounds(1)),
            ("- Title Round", lambda: self.adjust_title_rounds(-1)),
            ("+ Fighter Target", lambda: self.adjust_active_fighter_target(50)),
            ("- Fighter Target", lambda: self.adjust_active_fighter_target(-50)),
            ("Add Production Provider", self.add_broadcaster),
        )):
            ttk.Button(buttons, text=text, command=command).grid(row=col // 3, column=col % 3, sticky="ew", padx=3, pady=2)
        for col in range(3):
            buttons.columnconfigure(col, weight=1)

    def build_inbox_tab(self):
        self.screen_header(self.inbox_tab, "MAIL / DECISIONS", "Owner goals, decisions, contract alerts, suspensions, and business mail")
        inbox_resize = self.create_vertical_resizer(self.inbox_tab, initial_fraction=0.66, min_top=220, min_bottom=135)
        inbox_resize.pack(fill="both", expand=True)
        body = ttk.Frame(inbox_resize, style="Inset.TFrame")
        inbox_resize.add(body, minsize=220)
        inbox_panel, inbox = self.section(body, "INBOX")
        inbox_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        controls = ttk.Frame(inbox, style="Inset.TFrame")
        controls.pack(fill="x", pady=(0, 6))
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
        self.inbox_summary = ttk.Label(inbox, text="", style="Inset.TLabel", anchor="w")
        self.inbox_summary.pack(fill="x", padx=5, pady=(0, 4))
        self.inbox_tree = ttk.Treeview(inbox, columns=("state", "date", "type", "subject"), show="headings", height=14)
        for column, text, width in (("state", "", 32), ("date", "Received", 100), ("type", "Type", 110), ("subject", "Subject", 390)):
            self.inbox_tree.heading(column, text=text)
            self.inbox_tree.column(column, width=width, anchor="w")
        self.inbox_tree.tag_configure("unread", foreground="#ffe08a")
        self.inbox_tree.tag_configure("urgent", foreground="#ff9b9b")
        self.inbox_tree.pack(fill="both", expand=True)
        self.inbox_tree.bind("<<TreeviewSelect>>", self.show_selected_inbox_message)
        self.inbox_tree.bind("<Double-1>", lambda _event: self.open_inbox_context())
        inbox_actions = ttk.Frame(inbox, style="Inset.TFrame")
        inbox_actions.pack(fill="x", pady=(6, 0))
        for col, (text, command, style) in enumerate((
            ("Open Context", self.open_inbox_context, "Accent.TButton"),
            ("Medical Decision", self.resolve_serious_injury_inbox, None),
            ("Mark Read", self.mark_inbox_read, None),
            ("Mark Visible Read", self.mark_visible_inbox_read, None),
            ("Hide Type", self.hide_selected_inbox_type, None),
            ("Show Hidden", self.show_all_inbox_types, None),
            ("Resolve / Archive", self.resolve_inbox_item, None),
            ("Clear Old Mail", self.clear_old_inbox, None),
        )):
            button = ttk.Button(inbox_actions, text=text, command=command, style=style) if style else ttk.Button(inbox_actions, text=text, command=command)
            button.grid(row=col // 4, column=col % 4, sticky="ew", padx=3, pady=2)
        for col in range(4):
            inbox_actions.columnconfigure(col, weight=1)
        self.inbox_notice = ttk.Label(inbox, text="", style="Inset.TLabel", anchor="w")
        self.inbox_notice.pack(fill="x", padx=5, pady=(4, 0))
        goals_panel, goals = self.section(body, "OWNER GOALS")
        goals_panel.pack(side="left", fill="both", expand=True)
        self.goals_tree = ttk.Treeview(goals, columns=("goal", "progress", "deadline", "status"), show="headings", height=14)
        for column, text, width in (("goal", "Goal", 260), ("progress", "Progress", 115), ("deadline", "Deadline", 85), ("status", "Status", 80)):
            self.goals_tree.heading(column, text=text)
            self.goals_tree.column(column, width=width, anchor="w")
        self.goals_tree.tag_configure("complete", foreground="#9de6a0")
        self.goals_tree.tag_configure("failed", foreground="#ff9b9b")
        self.goals_tree.pack(fill="both", expand=True)
        self.goals_tree.bind("<Double-1>", lambda _event: self.open_selected_owner_goal())
        detail_panel, detail = self.section(inbox_resize, "MESSAGE DETAIL")
        inbox_resize.add(detail_panel, minsize=135)
        self.inbox_detail = tk.Text(detail, wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=12, pady=12)
        self.inbox_detail.pack(fill="both", expand=True)
        self.medical_decision_bar = ttk.Frame(detail, style="Inset.TFrame")
        ttk.Label(self.medical_decision_bar, text="MEDICAL DECISION", style="Inset.TLabel", font=("Tahoma", 8, "bold")).pack(side="left", padx=6)
        ttk.Button(self.medical_decision_bar, text="Surgical Repair", style="Accent.TButton", command=lambda: self.apply_inbox_medical_decision("surgery")).pack(side="left", padx=3, pady=5)
        ttk.Button(self.medical_decision_bar, text="Accelerated Rehab", command=lambda: self.apply_inbox_medical_decision("rehab")).pack(side="left", padx=3, pady=5)
        ttk.Button(self.medical_decision_bar, text="Retirement Bout", command=lambda: self.apply_inbox_medical_decision("retire")).pack(side="left", padx=3, pady=5)

    def build_staff_tab(self):
        self.screen_header(self.staff_tab, "STAFF / SCOUTING / DRUG TESTING", "Hire staff, assign scouting, manage testing, and post-show bonuses")
        staff_panel, staff = self.section(self.staff_tab, "STAFF")
        staff_panel.pack(fill="x", pady=(0, 6))
        self.staff_tree = ttk.Treeview(staff, columns=("name", "role", "skill", "salary", "morale"), show="headings", height=5)
        for col, text, width in (("name", "Name", 160), ("role", "Role", 110), ("skill", "Skill", 60), ("salary", "Salary", 90), ("morale", "Morale", 70)):
            self.staff_tree.heading(col, text=text)
            self.staff_tree.column(col, width=width, anchor="center")
        self.make_tree_sortable(self.staff_tree)
        self.staff_tree.pack(fill="x")
        self.staff_tree.bind("<Double-1>", lambda _event: self.open_selected_staff_profile())
        self.staff_candidate_tree = ttk.Treeview(staff, columns=("name", "role", "skill", "salary", "morale"), show="headings", height=5)
        for col, text, width in (("name", "Candidate", 160), ("role", "Role", 130), ("skill", "Skill", 60), ("salary", "Salary", 90), ("morale", "Morale", 70)):
            self.staff_candidate_tree.heading(col, text=text)
            self.staff_candidate_tree.column(col, width=width, anchor="center")
        self.make_tree_sortable(self.staff_candidate_tree)
        self.staff_candidate_tree.pack(fill="x", pady=(6, 0))
        self.staff_candidate_tree.bind("<Double-1>", lambda _event: self.open_selected_staff_profile(candidate=True))
        staff_buttons = ttk.Frame(staff, style="Inset.TFrame")
        staff_buttons.pack(fill="x", pady=4)
        for col, (text, command) in enumerate((
            ("Hire Candidate", self.hire_staff),
            ("Scouting Centre", lambda: self.select_tab("scouting")),
            ("Run Drug Tests", self.run_drug_tests),
            ("Hire Commentator", self.hire_commentator),
            ("View Staff Profile", self.open_selected_staff_profile),
            ("Fighting Academy", self.open_academy_window),
        )):
            ttk.Button(staff_buttons, text=text, command=command).grid(row=col // 3, column=col % 3, sticky="ew", padx=3, pady=2)
        for col in range(3):
            staff_buttons.columnconfigure(col, weight=1)
        bonus_panel, bonus = self.section(self.staff_tab, "POST-SHOW BONUSES / STAFF EFFECTS")
        bonus_panel.pack(fill="both", expand=True)
        self.staff_text = tk.Text(bonus, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
        self.staff_text.pack(fill="both", expand=True)

    def build_scouting_tab(self):
        self.screen_header(self.scouting_tab, "SCOUTING", "Evaluate fighters, observe upcoming bouts, search regions, and turn uncertain reports into recruitment decisions")
        self.scouting_scout_var = tk.StringVar()
        self.scouting_region_var = tk.StringVar(value=self.player_region)
        self.scouting_gender_var = tk.StringVar(value="All")
        self.scouting_weight_var = tk.StringVar(value="All")
        scouting_tabs = ttk.Notebook(self.scouting_tab)
        scouting_tabs.pack(fill="both", expand=True)
        target_page = ttk.Frame(scouting_tabs, style="Chrome.TFrame")
        assignment_page = ttk.Frame(scouting_tabs, style="Chrome.TFrame")
        scouting_tabs.add(target_page, text="Target Board")
        scouting_tabs.add(assignment_page, text="Assignments & Searches")

        target_panel, target = self.section(target_page, "RECRUITMENT TARGETS")
        target_panel.pack(fill="both", expand=True)
        target_filters = ttk.Frame(target, style="Inset.TFrame")
        target_filters.pack(fill="x", padx=4, pady=4)
        self.scouting_target_search = tk.StringVar()
        self.scouting_target_company = tk.StringVar(value="All")
        self.scouting_target_gender = tk.StringVar(value="All")
        self.scouting_target_weight = tk.StringVar(value="All")
        self.scouting_target_status = tk.StringVar(value="All")
        self.scouting_target_count_var = tk.StringVar(value="")
        self.scouting_target_page = 0
        self.scouting_target_page_size = 400
        search_label = ttk.Label(target_filters, text="Search", style="Inset.TLabel")
        search_label.pack(side="left", padx=(4, 2))
        search_entry = ttk.Entry(target_filters, textvariable=self.scouting_target_search, width=22)
        search_entry.pack(side="left", padx=(0, 6))
        search_entry.bind("<KeyRelease>", lambda _event: self.reset_scouting_target_page())
        self.attach_tooltip(search_label, "Find fighters by name or current company.")
        self.attach_tooltip(search_entry, "Type part of a fighter or company name. Results update while you type.")
        target_combos = (
            ("Company", self.scouting_target_company, (), 20),
            ("Gender", self.scouting_target_gender, ("All", "Male", "Female"), 9),
            ("Division", self.scouting_target_weight, ("All", *WEIGHTS), 14),
            ("Intel", self.scouting_target_status, ("All", "Recommended Signings", "Monitor", "Pass", "Shortlisted", "Unscouted", "In Progress", "Scouted", "Stale", "Free Agents", "Rival Rosters"), 18),
        )
        filter_help = {
            "Company": "Limit the board to free agents, independent fighters, or one promotion's roster.",
            "Gender": "Show male fighters, female fighters, or both.",
            "Division": "Limit results to one MMA weight class.",
            "Intel": "Filter by scouting state or recommendation. Monitor means the scout sees value, but price, uncertainty, or current division need makes an immediate offer hard to justify.",
        }
        for label, variable, values, width in target_combos:
            label_widget = ttk.Label(target_filters, text=label, style="Inset.TLabel")
            label_widget.pack(side="left", padx=(3, 2))
            combo = ttk.Combobox(target_filters, textvariable=variable, values=values, state="readonly", width=width)
            combo.pack(side="left", padx=(0, 5))
            combo.bind("<<ComboboxSelected>>", lambda _event: self.reset_scouting_target_page())
            self.attach_tooltip(label_widget, filter_help[label])
            self.attach_tooltip(combo, filter_help[label])
            if label == "Company":
                self.scouting_target_company_box = combo

        scouting_legend = ttk.Label(
            target,
            text="Scout advice: RECOMMEND SIGNING = pursue now  |  MONITOR = promising, but wait for a better fit, price, or clearer report  |  PASS = no current roster-value case",
            style="Inset.TLabel", anchor="w", justify="left", wraplength=1450,
        )
        scouting_legend.pack(fill="x", padx=8, pady=(0, 2))
        self.attach_tooltip(scouting_legend, "Recommendations are advisory, not restrictions. They combine projected ability, potential, market pull, your divisional depth, asking price, and available cash.")

        # Actionable summary strip: at a glance, what the board wants you to do.
        summary_row = tk.Frame(target, bg=self.colors["panel_dark"])
        summary_row.pack(fill="x", padx=8, pady=(0, 4))
        self.scouting_board_summary_var = tk.StringVar(value="")
        tk.Label(summary_row, textvariable=self.scouting_board_summary_var, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8, "bold"), anchor="w", justify="left").pack(side="left", padx=(6, 10), pady=2)
        for swatch_color, swatch_text in (("#7fd694", "recommend"), ("#e6c15a", "monitor"), ("#8a8f97", "pass"), ("#9de6ff", "shortlisted"), ("#e7bd72", "stale")):
            tk.Label(summary_row, text="■", bg=self.colors["panel_dark"], fg=swatch_color, font=("Tahoma", 9)).pack(side="left", padx=(6, 1))
            tk.Label(summary_row, text=swatch_text, bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8)).pack(side="left")

        target_tree_frame = ttk.Frame(target, style="Inset.TFrame")
        target_tree_frame.pack(fill="both", expand=True, padx=4, pady=(0, 4))
        self.scouting_target_tree = ttk.Treeview(target_tree_frame, columns=("watch", "name", "company", "gender", "division", "record", "age", "intel", "advice", "ovr", "potential", "last"), show="headings", height=15, selectmode="browse")
        for col, text, width in (("watch", "Watch", 48), ("name", "Fighter", 150), ("company", "Company", 165), ("gender", "G", 34), ("division", "Division", 88), ("record", "Record", 65), ("age", "Age", 38), ("intel", "Intel", 82), ("advice", "Scout Advice", 125), ("ovr", "OVR", 58), ("potential", "Ceiling", 62), ("last", "Last Fight", 88)):
            self.scouting_target_tree.heading(col, text=text)
            self.scouting_target_tree.column(col, width=width, anchor="center")
        self.scouting_target_tree.column("name", anchor="w")
        self.scouting_target_tree.column("company", anchor="w")
        self.make_tree_sortable(self.scouting_target_tree)
        # Shortlist/stale keep priority as deliberate user/quality signals; the
        # scout's verdict colours the rest of the board so recommendations pop.
        self.scouting_target_tree.tag_configure("shortlisted", foreground="#9de6ff")
        self.scouting_target_tree.tag_configure("stale", foreground="#e7bd72")
        self.scouting_target_tree.tag_configure("advice_sign", foreground="#7fd694")
        self.scouting_target_tree.tag_configure("advice_monitor", foreground="#e6c15a")
        self.scouting_target_tree.tag_configure("advice_pass", foreground="#8a8f97")
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
        assign_label = ttk.Label(target_actions, text="Assign", style="Inset.TLabel")
        assign_label.pack(side="left", padx=(4, 2))
        self.scouting_target_scout_box = ttk.Combobox(target_actions, textvariable=self.scouting_scout_var, values=(), state="readonly", width=22)
        self.scouting_target_scout_box.pack(side="left", padx=(0, 6))
        self.attach_tooltip(assign_label, "Choose a scout for the report. Auto Assign selects a suitable scout with a free assignment slot.")
        self.attach_tooltip(self.scouting_target_scout_box, "Each scout has limited assignment capacity. Better judging and reliability produce tighter, more dependable estimates.")
        report_help = {
            "Basic Dossier": "~$2,500, ~2 weeks. A quicker, cheaper initial report revealing broad ability and potential ranges. Out-of-region +35%, independent contractor +50%.",
            "Full Evaluation": "~$7,500, ~6 weeks. Reveals exact current ratings and the most reliable view of potential. Out-of-region +35%, independent contractor +50%.",
            "Observe Next Fight": "~$4,000. Keeps the slot open until the fighter competes; live evidence improves confidence, but the report expires if they stay inactive.",
        }
        for text, kind in (("Basic Dossier", "basic"), ("Full Evaluation", "full"), ("Observe Next Fight", "observation")):
            button = ttk.Button(target_actions, text=text, command=lambda report_kind=kind: self.start_selected_recruitment_report(report_kind))
            button.pack(side="left", padx=3)
            self.attach_tooltip(button, report_help[text])
        shortlist_button = ttk.Button(target_actions, text="Toggle Shortlist", command=self.toggle_selected_scouting_shortlist)
        shortlist_button.pack(side="left", padx=3)
        profile_button = ttk.Button(target_actions, text="Open Profile", command=self.open_selected_recruitment_target)
        profile_button.pack(side="right", padx=3)
        negotiate_button = ttk.Button(target_actions, text="Negotiate", style="Accent.TButton", command=self.negotiate_selected_recruitment_target)
        negotiate_button.pack(side="right", padx=3)
        self.attach_tooltip(shortlist_button, "Add or remove the selected fighter from your persistent watch list. This does not spend money or consume a scout slot.")
        self.attach_tooltip(profile_button, "Open the complete fighter profile. Information your scouts have not uncovered remains hidden.")
        self.attach_tooltip(negotiate_button, "Approach a free agent even without a scouting report. Hidden ratings stay hidden, so signing unscouted talent carries more risk.")
        self.scouting_target_status_var = tk.StringVar(value="Select a fighter to evaluate, monitor, or approach.")
        ttk.Label(target, textvariable=self.scouting_target_status_var, style="Inset.TLabel", anchor="w", justify="left", wraplength=1450).pack(fill="x", padx=8, pady=(0, 5))

        panel, bonus = self.section(assignment_page, "SCOUTING CONTROL CENTRE")
        panel.pack(fill="both", expand=True)
        scout_controls = ttk.Frame(bonus, style="Inset.TFrame")
        scout_controls.pack(fill="x", padx=4, pady=4)
        for label, variable, values, width in (
            ("Scout", self.scouting_scout_var, (), 22),
            ("Region", self.scouting_region_var, REGIONS, 16),
            ("Gender", self.scouting_gender_var, ("All", "Male", "Female"), 10),
            ("Division", self.scouting_weight_var, ("All", *WEIGHTS), 15),
        ):
            label_widget = ttk.Label(scout_controls, text=label, style="Inset.TLabel")
            label_widget.pack(side="left", padx=(5, 2))
            combo = ttk.Combobox(scout_controls, textvariable=variable, values=values, state="readonly", width=width)
            combo.pack(side="left", padx=(0, 5))
            search_help = {
                "Scout": "Assign a specific scout or let Auto Assign choose an available one.",
                "Region": "The geographical market to search. Regional knowledge and scout specialties can improve the lead.",
                "Gender": "Choose which fighter market the search should prioritize.",
                "Division": "Choose a specific weight class or search across all divisions.",
            }[label]
            self.attach_tooltip(label_widget, search_help)
            self.attach_tooltip(combo, search_help)
            if label == "Scout":
                self.scouting_scout_box = combo
        start_search_button = ttk.Button(scout_controls, text="Start Search", style="Accent.TButton", command=self.assign_scouting)
        start_search_button.pack(side="left", padx=4)
        cancel_assignment_button = ttk.Button(scout_controls, text="Cancel Assignment", command=self.cancel_selected_scouting_assignment)
        cancel_assignment_button.pack(side="left", padx=4)
        open_fighter_button = ttk.Button(scout_controls, text="Open Fighter", command=self.open_selected_scouting_target)
        open_fighter_button.pack(side="left", padx=4)
        self.attach_tooltip(start_search_button, "Send the selected scout to find a new lead matching this brief. Searches cost money and occupy one assignment slot until complete.")
        self.attach_tooltip(cancel_assignment_button, "End the selected active report or talent search and release its scout slot. Spent scouting costs are not refunded.")
        self.attach_tooltip(open_fighter_button, "Open the fighter attached to the selected report. Talent searches without a completed lead have no fighter to open.")

        self.scouting_status_var = tk.StringVar(value="Select a scout and a search brief. Fighter evaluations are started from fighter profiles.")
        ttk.Label(bonus, textvariable=self.scouting_status_var, style="Inset.TLabel", anchor="w").pack(fill="x", padx=8, pady=(0, 4))
        self.scouting_assignment_tree = ttk.Treeview(bonus, columns=("type", "target", "scout", "status", "due", "confidence", "advice", "cost"), show="headings", height=7, selectmode="browse")
        for col, text, width in (("type", "Assignment", 120), ("target", "Target / Region", 190), ("scout", "Scout", 145), ("status", "Status", 82), ("due", "Due", 82), ("confidence", "Confidence", 78), ("advice", "Scout Advice", 135), ("cost", "Cost", 78)):
            self.scouting_assignment_tree.heading(col, text=text)
            self.scouting_assignment_tree.column(col, width=width, anchor="center")
        self.scouting_assignment_tree.column("target", anchor="w")
        self.make_tree_sortable(self.scouting_assignment_tree)
        self.scouting_assignment_tree.tag_configure("advice_sign", foreground="#7fd694")
        self.scouting_assignment_tree.tag_configure("advice_monitor", foreground="#e6c15a")
        self.scouting_assignment_tree.tag_configure("advice_pass", foreground="#8a8f97")
        self.scouting_assignment_tree.tag_configure("assignment_pending", foreground="#9db4c0")
        self.scouting_assignment_tree.pack(fill="both", expand=True, padx=4, pady=(0, 4))
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
        sponsor_panel, sponsor_inner = self.section(inner, "SPONSOR MARKET")
        sponsor_panel.pack(fill="x", pady=(0, 6))
        sponsor_actions = ttk.Frame(sponsor_inner, style="Inset.TFrame")
        sponsor_actions.pack(side="right", fill="y", padx=(6, 0))
        ttk.Button(sponsor_actions, text="Accept Offer", style="Accent.TButton", command=self.accept_sponsor_offer).pack(fill="x", pady=(0, 3))
        ttk.Button(sponsor_actions, text="Reject Offer", command=self.reject_sponsor_offer).pack(fill="x")
        self.sponsor_market_tree = ttk.Treeview(sponsor_inner, columns=("status", "brand", "category", "fee", "term", "fit", "requirement"), show="headings", height=4)
        for column, text, width in (("status", "Status", 58), ("brand", "Brand", 145), ("category", "Category", 100), ("fee", "Per Event", 90), ("term", "Term", 62), ("fit", "Fit", 42), ("requirement", "Requirement", 290)):
            self.sponsor_market_tree.heading(column, text=text)
            self.sponsor_market_tree.column(column, width=width, anchor="w" if column in ("brand", "category", "requirement") else "center")
        self.sponsor_market_tree.tag_configure("offer", foreground="#9de6ff")
        self.sponsor_market_tree.tag_configure("active", foreground="#9de6a0")
        self.sponsor_market_tree.pack(fill="x", expand=True)
        self.sponsor_market_note = ttk.Label(sponsor_inner, text="", style="Inset.TLabel", justify="left")
        self.sponsor_market_note.pack(fill="x", pady=(3, 0))
        body = ttk.Frame(inner, style="Chrome.TFrame")
        body.pack(fill="both", expand=True)
        self.finance_tree = ttk.Treeview(body, columns=("period", "opening", "revenue", "costs", "net", "ending"), show="headings", height=14)
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
        panel, inner = self.section(self.contracts_tab, "CONTRACT OVERVIEW")
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
        buttons = ttk.Frame(inner, style="Inset.TFrame")
        buttons.pack(fill="x", pady=(6, 0))
        ttk.Button(buttons, text="Negotiate Renewal", style="Accent.TButton", command=self.renew_selected_contract).pack(side="left", padx=4)
        ttk.Button(buttons, text="Auto Negotiate Selected", command=self.auto_negotiate_selected_contracts).pack(side="left", padx=4)
        ttk.Button(buttons, text="View Profile", command=self.view_contract_profile).pack(side="left", padx=4)
        self.auto_renew_button = ttk.Button(buttons, text="", command=self.toggle_auto_renew)
        self.auto_renew_button.pack(side="left", padx=4)
        ttk.Label(buttons, text="Rows: red = expired, orange = final month, yellow = expiring soon", style="Inset.TLabel").pack(side="left", padx=12)
        self.contracts_summary = ttk.Label(buttons, text="", style="Inset.TLabel")
        self.contracts_summary.pack(side="right", padx=8)

    def build_booking_tab(self):
        self.screen_header(self.booking_tab, "ADD SHOW / MATCHMAKING", "Build the card from opener to main event")
        header_panel, header = self.section(self.booking_tab, "SHOW DETAILS")
        header_panel.pack(fill="x", pady=(0, 6))
        self.schedule_status_var = tk.StringVar(value="Card has not been scheduled.")
        line1 = ttk.Frame(header, style="Inset.TFrame")
        line1.pack(fill="x", pady=2)
        line2 = ttk.Frame(header, style="Inset.TFrame")
        line2.pack(fill="x", pady=2)
        ttk.Label(line1, text="Event", style="Inset.TLabel", width=7).pack(side="left")
        ttk.Entry(line1, textvariable=self.event_name, width=34).pack(side="left", padx=(4, 12))
        ttk.Label(line1, text="Venue", style="Inset.TLabel", width=7).pack(side="left")
        venue_box = ttk.Combobox(line1, textvariable=self.venue, values=self.available_event_venues(), state="readonly", width=24)
        venue_box.pack(side="left", padx=(4, 12))
        self.event_venue_box = venue_box
        self.attach_tooltip(venue_box, "Bigger venues seat more fans and can lift the gate, but a half-empty large room hurts atmosphere and stability. Match the venue to your drawing power.")
        schedule_btn = ttk.Button(line1, text="Schedule Show", command=self.schedule_event)
        schedule_btn.pack(side="right", padx=(4, 0))
        self.attach_tooltip(schedule_btn, "Lock in the card for the chosen date. A viable card needs at least one complete bout, every fighter available, and any champion's title correctly flagged.")
        ttk.Button(line1, text="Earliest Valid Date", command=self.move_booking_to_earliest_card_date).pack(side="right", padx=(4, 0))
        ttk.Button(line1, text="Watch Event", command=self.watch_due_event).pack(side="right", padx=(4, 0))
        ttk.Button(line1, text="Skip Event", style="Accent.TButton", command=self.skip_due_event).pack(side="right", padx=(4, 0))
        ttk.Label(line2, text="Region", style="Inset.TLabel", width=7).pack(side="left")
        region_box = ttk.Combobox(line2, textvariable=self.event_region, values=REGIONS, state="readonly", width=11)
        region_box.pack(side="left", padx=(4, 12))
        region_box.bind("<<ComboboxSelected>>", lambda _e: (self.update_city_options(), self.refresh_event_atmosphere_forecast()))
        ttk.Label(line2, text="City", style="Inset.TLabel", width=7).pack(side="left")
        self.city_box = ttk.Combobox(line2, textvariable=self.event_city, values=REGION_CITIES["USA"], state="readonly", width=13)
        self.city_box.pack(side="left", padx=(4, 12))
        ttk.Label(line2, text="Month", style="Inset.TLabel", width=7).pack(side="left")
        event_month_box = ttk.Combobox(line2, textvariable=self.event_calendar_month, values=CALENDAR_MONTH_ABBREVIATIONS, state="readonly", width=6)
        event_month_box.pack(side="left", padx=(4, 5))
        event_month_box.bind("<<ComboboxSelected>>", lambda _e: (self.sync_booking_internal_date(), self.refresh_available()))
        ttk.Label(line2, text="Year", style="Inset.TLabel", width=5).pack(side="left")
        event_year_box = ttk.Spinbox(line2, from_=GAME_START_YEAR, to=GAME_START_YEAR + 50, textvariable=self.event_year, width=6)
        event_year_box.pack(side="left", padx=(4, 12))
        event_year_box.bind("<FocusOut>", lambda _e: (self.sync_booking_internal_date(), self.refresh_available()))
        event_year_box.bind("<Return>", lambda _e: (self.sync_booking_internal_date(), self.refresh_available()))
        ttk.Label(line2, text="Week", style="Inset.TLabel", width=5).pack(side="left")
        event_week_box = ttk.Combobox(line2, textvariable=self.event_week, values=(1, 2, 3, 4), state="readonly", width=4)
        event_week_box.pack(side="left", padx=(4, 12))
        event_week_box.bind("<<ComboboxSelected>>", lambda _e: (self.sync_booking_internal_date(), self.refresh_available()))
        ttk.Label(line2, text="Provider", style="Inset.TLabel", width=7).pack(side="left")
        self.event_broadcaster_box = ttk.Combobox(line2, textvariable=self.event_broadcaster, values=["No Coverage"] + [item["name"] for item in self.broadcasters], state="readonly", width=23)
        self.event_broadcaster_box.pack(side="left", padx=(4, 0))
        self.event_broadcaster_box.bind("<<ComboboxSelected>>", self.refresh_event_broadcaster_status)
        self.attach_tooltip(self.event_broadcaster_box, "A broadcast provider adds media income and exposure that grows your popularity. 'No Coverage' means sharply reduced reach and revenue.")
        self.schedule_status = tk.Label(
            header,
            textvariable=self.schedule_status_var,
            anchor="w",
            justify="left",
            bg="#252525",
            fg=self.colors["text"],
            font=("Tahoma", 9, "bold"),
            padx=8,
            pady=5,
        )
        self.schedule_status.pack(fill="x", pady=(4, 2))
        self.schedule_status.bind("<Configure>", lambda event: self.schedule_status.configure(wraplength=max(300, event.width - 20)))
        self.event_broadcaster_status = ttk.Label(header, text="", style="Inset.TLabel", justify="left")
        self.event_broadcaster_status.pack(fill="x", pady=(4, 0))
        atmosphere_row = ttk.Frame(header, style="Inset.TFrame"); atmosphere_row.pack(fill="x", pady=(4, 0))
        self.event_atmosphere_status = ttk.Label(atmosphere_row, text="", style="Inset.TLabel", justify="left")
        self.event_atmosphere_status.pack(side="left", fill="x", expand=True, padx=4, pady=3)
        ttk.Button(atmosphere_row, text="Fanbase & Atmosphere", command=self.open_fanbase_window).pack(side="right", padx=4, pady=3)
        superfight_btn = ttk.Button(atmosphere_row, text="★ Superfight Night", style="Accent.TButton", command=self.open_superfight_night_window)
        superfight_btn.pack(side="right", padx=4, pady=3)
        self.attach_tooltip(superfight_btn, "Promote a Crossover Superfight Night: pay rival promotions to sanction champion-vs-champion superfights (non-title, no belts change) plus prelims from your roster.")
        ttk.Button(atmosphere_row, text="Super Events", command=self.open_company_milestones_window).pack(side="right", padx=4, pady=3)

        booking_resize = self.create_vertical_resizer(self.booking_tab, initial_fraction=0.8, min_top=250, min_bottom=120)
        booking_resize.pack(fill="both", expand=True)
        body = ttk.Panedwindow(booking_resize, orient="horizontal")
        booking_resize.add(body, minsize=250)
        left_panel, left = self.section(body, "AVAILABLE FIGHTERS")
        right_panel, right = self.section(body, "CURRENT FIGHT CARD")
        body.add(left_panel, weight=3)
        body.add(right_panel, weight=2)
        self.booking_horizontal_split = body
        self._booking_split_initialized = False

        def initialize_booking_split(event):
            if self._booking_split_initialized or event.width < 700:
                return
            self._booking_split_initialized = True
            body.sashpos(0, int(event.width * 0.62))

        body.bind("<Configure>", initialize_booking_split, add="+")

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
        add_matchup_btn = ttk.Button(booking_actions, text="Add Matchup", style="Accent.TButton", command=self.add_matchup)
        add_matchup_btn.pack(side="left", padx=(2, 4), pady=3)
        add_tba_btn = ttk.Button(booking_actions, text="Add TBA", command=self.add_tba_matchup)
        add_tba_btn.pack(side="left", padx=3, pady=3)
        tournament_btn = ttk.Button(booking_actions, text="Tournament", command=self.add_tournament_to_card)
        tournament_btn.pack(side="left", padx=3, pady=3)
        assistant_btn = ttk.Button(booking_actions, text="Assistant Recommend", command=self.assistant_pick_matchup)
        assistant_btn.pack(side="left", padx=3, pady=3)
        title_check = ttk.Checkbutton(booking_actions, text="Title", variable=self.title_fight, command=self.toggle_divisional_title_booking)
        title_check.pack(side="left", padx=(12, 3))
        main_event_check = ttk.Checkbutton(booking_actions, text="Main event", variable=self.main_event)
        main_event_check.pack(side="left", padx=3)
        self.special_belt_choice = tk.StringVar(value="None")
        special_belt_label = ttk.Label(booking_actions, text="Special Belt", style="Inset.TLabel")
        special_belt_label.pack(side="left", padx=(10, 2))
        self.special_belt_box = ttk.Combobox(booking_actions, textvariable=self.special_belt_choice, state="readonly", width=14)
        self.special_belt_box.pack(side="left", padx=(0, 3))
        self.special_belt_box.bind("<<ComboboxSelected>>", self.select_special_belt_booking)
        tier_label = ttk.Label(booking_actions, text="Tier", style="Inset.TLabel")
        tier_label.pack(side="left", padx=(10, 2))
        tier_box = ttk.Combobox(booking_actions, textvariable=self.card_tier, values=CARD_TIERS, state="readonly", width=12)
        tier_box.pack(side="left", padx=(0, 3))
        self.attach_tooltip(add_matchup_btn, "Book the two selected available fighters into a bout. Pick same-gender fighters in the same (or a close) division for a viable, credible fight.")
        self.attach_tooltip(add_tba_btn, "Add a bout with one side left open (To Be Announced). Reserve a slot now and fill it later from Upcoming Events once you've signed or freed an opponent.")
        self.attach_tooltip(tournament_btn, "Add a full bracket of bouts in one division. A quick way to fill a card and build a division — you'll need several same-division, same-gender fighters.")
        self.attach_tooltip(assistant_btn, "Let your matchmaker propose a competitive, fresh pairing from your available roster — a fast route to a sensible bout.")
        self.attach_tooltip(title_check, "Book the bout for the divisional belt. Needs a champion or ranked contenders. A champion booked WITHOUT this defends no title — watch for the red warning.")
        self.attach_tooltip(main_event_check, "Flag this as the headline bout. Your main event drives hype, gate, and the media rating, so put your biggest draw or title fight on top.")
        self.attach_tooltip(self.special_belt_box, "Attach an interim, tournament, or other special title to raise the stakes and hype of a non-divisional-title bout.")
        self.attach_tooltip(tier_box, "Card position tier (Main Card, Prelims, etc.). Lower tiers pay and cost less — stack prospects on the prelims and save stars for the main card.")

        legend = tk.Frame(left, bg=self.colors["panel_dark"])
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
        self.matchmaking_notice = ttk.Label(left, textvariable=self.matchmaking_notice_var, style="Inset.TLabel", anchor="w")
        self.matchmaking_notice.pack(fill="x", pady=(0, 4), padx=3)

        self.matchmaking_title_warning_var = tk.StringVar(value="")
        self.matchmaking_title_warning = tk.Label(
            left, textvariable=self.matchmaking_title_warning_var, anchor="w", justify="left",
            bg=self.colors["panel_dark"], fg="#ff766d", font=("Tahoma", 9, "bold"), padx=7, pady=3,
        )
        self.matchmaking_title_warning.pack(fill="x", pady=(0, 4), padx=3)

        self.matchmaking_history_var = tk.StringVar(value="Select one fighter to compare prior meetings with every possible opponent.")
        self.matchmaking_history = ttk.Label(left, textvariable=self.matchmaking_history_var, style="Inset.TLabel", anchor="w")
        self.matchmaking_history.pack(fill="x", pady=(0, 4), padx=3)

        self.matchmaking_brief_var = tk.StringVar(value="Select a fighter for a divisional recommendation and detailed booking context.")
        self.matchmaking_brief = tk.Label(
            left, textvariable=self.matchmaking_brief_var, anchor="w", justify="left",
            bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 8), padx=7, pady=5,
        )
        self.matchmaking_brief.pack(fill="x", pady=(0, 4), padx=3)
        self.matchmaking_brief.bind("<Configure>", lambda event: self.matchmaking_brief.configure(wraplength=max(300, event.width - 18)))

        self.available_tree = ttk.Treeview(left, columns=("name", "gender", "weight", "rank", "titlepath", "record", "age", "overall", "elo", "pop", "build", "last", "form", "trend", "activity", "fatigue", "recovery", "fit", "history", "status"), show="headings", selectmode="extended", height=14)
        for col, text, width in (("name", "Name", 148), ("gender", "G", 34), ("weight", "Class", 90), ("rank", "Rank", 44), ("titlepath", "Title Path", 104), ("record", "Record", 66), ("age", "Age", 40), ("overall", "OVR", 44), ("elo", "ELO", 54), ("pop", "Pop", 42), ("build", "Build", 48), ("last", "Last Fight", 84), ("form", "Last 5 (→latest)", 82), ("trend", "Form", 56), ("activity", "Active", 50), ("fatigue", "Fatigue", 88), ("recovery", "Medical Return", 104), ("fit", "Match Fit", 66), ("history", "History", 74), ("status", "Event Availability", 132)):
            self.available_tree.heading(col, text=text)
            self.available_tree.column(col, width=width, anchor="center")
        self.available_tree.column("name", anchor="w")
        self.available_tree.column("titlepath", anchor="w")
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
        self.available_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.available_tree, "name"))
        self.available_tree.bind("<<TreeviewSelect>>", self.refresh_matchmaking_history_indicators, add="+")

        self.card_tree = ttk.Treeview(right, columns=("slot", "fight", "weight", "hype", "media", "fatigue", "recovery"), show="headings", height=14)
        for col, text, width in (("slot", "Slot", 90), ("fight", "Fight", 250), ("weight", "Weight", 105), ("hype", "Hype", 60), ("media", "Build", 60), ("fatigue", "Fatigue A/B", 92), ("recovery", "Medical Return A/B", 150)):
            self.card_tree.heading(col, text=text)
            self.card_tree.column(col, width=width, anchor="center")
        self.card_tree.column("fight", anchor="w")
        self.card_tree.tag_configure("non_title_champion", background="#5c1a1a", foreground="#ffffff")
        self.attach_tree_heading_tooltips(self.card_tree, {
            "slot": "Position on the card. The top row is your main event — order bouts from opener up to the headliner.",
            "fight": "The booked matchup. A red row flags a champion booked without their title on the line.",
            "weight": "Division the bout is contested at.",
            "hype": "Projected fan interest in this bout — drives gate and media rating. Ranked names, titles, and rivalries raise it.",
            "media": "Fight build score — how competitive and story-rich the matchup is. Even, high-stakes fights score highest.",
            "fatigue": "Current fatigue for each fighter in the same order as the matchup. 65 or higher is unfit.",
            "recovery": "Earliest medical return for each fighter in matchup order. Now means medically cleared today.",
        })
        self.make_tree_sortable(self.card_tree)
        self.card_tree.pack(fill="both", expand=True, pady=5)
        footer = ttk.Frame(right)
        footer.pack(fill="x")
        ttk.Button(footer, text="Remove Fight", command=self.remove_matchup).pack(side="left")
        fill_tba_btn = ttk.Button(footer, text="Fill TBA", command=self.fill_selected_tba_matchup)
        fill_tba_btn.pack(side="left", padx=4)
        title_interim_btn = ttk.Button(footer, text="Title / Interim", command=self.toggle_card_title)
        title_interim_btn.pack(side="left", padx=4)
        move_up_btn = ttk.Button(footer, text="Move Up", command=self.move_fight_up)
        move_up_btn.pack(side="left", padx=4)
        ttk.Button(footer, text="Move Down", command=self.move_fight_down).pack(side="left", padx=4)
        ttk.Button(footer, text="Clear Card", command=self.clear_card).pack(side="right")
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

    def build_world_tab(self):
        self.screen_header(self.world_tab, "WORLD HUB", "Promotions, news, market churn, and the wider MMA economy")
        body = ttk.Frame(self.world_tab)
        body.pack(fill="both", expand=True)

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
        search_entry.bind("<KeyRelease>", lambda _event: self.refresh_world_fighter_search())
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
        table = ttk.Frame(inner, style="Inset.TFrame")
        table.pack(fill="both", expand=True)
        columns = ("name", "company", "sport", "gender", "division", "age", "universe", "career", "form", "last", "overall", "elo")
        self.world_fighter_tree = ttk.Treeview(table, columns=columns, show="headings")
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
        ttk.Button(actions, text="View Fighter", style="Accent.TButton", command=self.open_selected_world_fighter_profile).pack(side="right", padx=4)

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
        ttk.Button(controls, text="Reset", command=self.clear_regional_prospect_filters).grid(row=0, column=10, padx=4, pady=4)
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
        ttk.Button(actions, text="Negotiate", style="Accent.TButton", command=self.negotiate_selected_regional_prospect).pack(side="right", padx=4)

    def build_rankings_tab(self):
        self.screen_header(self.rankings_tab, "RANKINGS", "Division rankings and pound-for-pound rankings")
        controls = ttk.Frame(self.rankings_tab)
        controls.pack(fill="x", pady=(0, 6))
        ttk.Label(controls, text="Ranking list").pack(side="left")
        self.ranking_filter = tk.StringVar(value="Pound-for-Pound")
        ranking_box = ttk.Combobox(controls, values=["Pound-for-Pound", "Division Rankings", "Company Rankings"], textvariable=self.ranking_filter, state="readonly", width=20)
        ranking_box.pack(side="left", padx=8)
        ranking_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_rankings())
        ttk.Label(controls, text="Weight").pack(side="left", padx=(16, 0))
        ranking_weight = ttk.Combobox(controls, values=["All"] + WEIGHTS, textvariable=self.ranking_weight_filter, state="readonly", width=15)
        ranking_weight.pack(side="left", padx=8)
        ranking_weight.bind("<<ComboboxSelected>>", lambda _e: self.refresh_rankings())
        ttk.Label(controls, text="Scope").pack(side="left", padx=(16, 0))
        self.ranking_scope = tk.StringVar(value="Worldwide")
        self.ranking_scope_box = ttk.Combobox(controls, textvariable=self.ranking_scope, state="readonly", width=30)
        self.ranking_scope_box.pack(side="left", padx=8)
        self.ranking_scope_box.bind("<<ComboboxSelected>>", lambda _e: self.refresh_rankings())
        ttk.Label(controls, text="Gender").pack(side="left", padx=(16, 0))
        ranking_gender = ttk.Combobox(controls, values=["All", "Male", "Female"], textvariable=self.ranking_gender_filter, state="readonly", width=10)
        ranking_gender.pack(side="left", padx=8)
        ranking_gender.bind("<<ComboboxSelected>>", lambda _e: self.refresh_rankings())
        panel, inner = self.section(self.rankings_tab, "TOP CONTENDERS")
        panel.pack(fill="both", expand=True)
        rankings_resize = self.create_vertical_resizer(inner, initial_fraction=0.78, min_top=220, min_bottom=95)
        rankings_resize.pack(fill="both", expand=True)
        ranking_table = ttk.Frame(rankings_resize, style="Inset.TFrame")
        rankings_resize.add(ranking_table, minsize=220)
        self.rankings_tree = ttk.Treeview(ranking_table, columns=("company_rank", "world_rank", "move", "name", "gender", "company", "weight", "record", "overall", "form", "path", "score", "last", "status"), show="headings")
        for col, text, width in (("company_rank", "Co Rank", 62), ("world_rank", "World", 58), ("move", "Move", 60), ("name", "Fighter", 150), ("gender", "G", 38), ("company", "Company", 135), ("weight", "Division", 100), ("record", "Record", 70), ("overall", "OVR", 55), ("form", "Form", 90), ("path", "Title Path", 135), ("score", "Score", 65), ("last", "Last Fight", 120), ("status", "Status", 85)):
            self.rankings_tree.heading(col, text=text)
            self.rankings_tree.column(col, width=width, anchor="center")
        self.rankings_tree.column("name", anchor="w")
        self.rankings_tree.column("company", anchor="w")
        self.rankings_tree.column("last", anchor="w")
        self.make_tree_sortable(self.rankings_tree)
        self.rankings_tree.pack(fill="both", expand=True)
        ranking_detail_frame = ttk.Frame(rankings_resize, style="Inset.TFrame")
        rankings_resize.add(ranking_detail_frame, minsize=95)
        self.ranking_detail = tk.Text(ranking_detail_frame, height=4, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        self.ranking_detail.pack(fill="both", expand=True); self.ranking_detail.config(state="disabled")
        self.rankings_tree.bind("<<TreeviewSelect>>", self.show_ranking_detail)
        self.rankings_tree.bind("<Double-1>", self.open_selected_ranking_profile)

    def build_editor_tab(self):
        self.screen_header(self.editor_tab, "WORLD EDITOR", "Edit the current career or maintain the reusable starting universe")
        self.editor_current_dirty = False
        self.editor_career_target_var = tk.StringVar(value="Current career")
        self.editor_database_target_var = tk.StringVar(value="Starting universe")
        self.editor_edit_state_var = tk.StringVar(value="No unsaved editor changes")

        scope_row = ttk.Frame(self.editor_tab, style="Chrome.TFrame")
        scope_row.pack(fill="x", pady=(0, 6))
        career_scope, career_inner = self.section(scope_row, "CURRENT CAREER")
        career_scope.pack(side="left", fill="x", expand=True, padx=(0, 4))
        ttk.Label(career_inner, textvariable=self.editor_career_target_var, style="Inset.TLabel", font=("Tahoma", 9, "bold")).pack(side="left", padx=8, pady=6)
        ttk.Label(career_inner, textvariable=self.editor_edit_state_var, style="Inset.TLabel").pack(side="left", padx=8)
        ttk.Button(career_inner, text="Save Career Now", style="Accent.TButton", command=self.save_editor_career_now).pack(side="right", padx=6, pady=4)

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
        for label, key in (("KO Power", "ko_power"), ("Submission Finish", "submission_finish"), ("Decision Noise", "decision_noise"), ("Gas Cost", "gas_cost"), ("Damage", "damage"), ("Gate Multiplier", "gate_multiplier")):
            row = ttk.Frame(settings, style="Inset.TFrame")
            row.pack(fill="x", pady=2)
            ttk.Label(row, text=label, width=18, style="Inset.TLabel").pack(side="left")
            var = tk.DoubleVar(value=self.engine_settings.get(key, 1.0))
            self.engine_vars[key] = var
            ttk.Spinbox(row, from_=0.5, to=2.0, increment=0.05, textvariable=var, width=6).pack(side="left", padx=4)
        ttk.Button(settings, text="Apply Engine Settings", command=self.apply_engine_settings).pack(anchor="e", pady=4)
        audit_panel, audit = self.section(top, "AUDIT")
        audit_panel.pack(side="left", fill="x", expand=True)
        row = ttk.Frame(audit, style="Inset.TFrame")
        row.pack(fill="x", pady=4)
        ttk.Label(row, text="Events", style="Inset.TLabel").pack(side="left")
        ttk.Spinbox(row, from_=10, to=1000, increment=10, textvariable=self.audit_runs, width=7).pack(side="left", padx=6)
        ttk.Button(row, text="Run Audit", style="Accent.TButton", command=self.run_simulation_audit).pack(side="left", padx=8)
        ttk.Label(row, text="Years", style="Inset.TLabel").pack(side="left", padx=(10, 2))
        ttk.Spinbox(row, from_=1, to=100, increment=1, textvariable=self.play_audit_years, width=4).pack(side="left", padx=(0, 4))
        ttk.Button(row, text="Run Play Audit", command=self.run_play_level_audit).pack(side="left", padx=4)
        self.view_play_audit_button = ttk.Button(row, text="View 30-Year Results", command=self.open_play_level_audit_results, state="disabled")
        self.view_play_audit_button.pack(side="left", padx=4)
        ttk.Button(row, text="Defaults", command=self.reset_engine_settings).pack(side="left", padx=4)
        audit_progress = ttk.Frame(audit, style="Inset.TFrame")
        audit_progress.pack(fill="x", padx=4, pady=(2, 4))
        self.play_audit_status = ttk.Label(audit_progress, text="30-year play audit: ready", style="Inset.TLabel", width=36)
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
        self.sim_result = ttk.Label(sim, text="Pick two fighters from the database.", style="Inset.TLabel", anchor="w")
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

    def build_log_tab(self):
        self.screen_header(self.log_tab, "LIVE FIGHT NIGHT", "Blow-by-blow report and office news")
        panel, inner = self.section(self.log_tab, "EVENT REPORT")
        panel.pack(fill="both", expand=True)
        self.log_text = tk.Text(inner, wrap="word", font=("Courier New", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=10, pady=10, relief="flat")
        self.log_text.pack(fill="both", expand=True)
        self.log_text.insert("end", "Book a card, then run the event to see blow-by-blow results here.\n")
        self.log_text.config(state="disabled")
