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
        inner = ttk.Frame(canvas, style=style)
        window_id = canvas.create_window((0, 0), window=inner, anchor="nw")

        def update_scrollregion(_event=None):
            canvas.configure(scrollregion=canvas.bbox("all"))

        def fit_width(event):
            canvas.itemconfigure(window_id, width=event.width)
            update_scrollregion()

        def wheel(event):
            delta = -1 if event.delta > 0 else 1
            if sys.platform == "darwin":
                delta = -event.delta
            canvas.yview_scroll(delta, "units")

        def bind_wheel(_event=None):
            canvas.bind_all("<MouseWheel>", wheel)
            canvas.bind_all("<Button-4>", lambda _e: canvas.yview_scroll(-1, "units"))
            canvas.bind_all("<Button-5>", lambda _e: canvas.yview_scroll(1, "units"))

        def unbind_wheel(_event=None):
            canvas.unbind_all("<MouseWheel>")
            canvas.unbind_all("<Button-4>")
            canvas.unbind_all("<Button-5>")

        inner.bind("<Configure>", update_scrollregion)
        canvas.bind("<Configure>", fit_width)
        shell.bind("<Enter>", bind_wheel)
        shell.bind("<Leave>", unbind_wheel)
        canvas.configure(yscrollcommand=scroll.set)
        canvas.pack(side="left", fill="both", expand=True)
        scroll.pack(side="right", fill="y")
        if not hasattr(self, "scrollable_canvases"):
            self.scrollable_canvases = []
        self.scrollable_canvases.append(canvas)
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
        ttk.Combobox(titlebar, values=list(self.themes.keys()), textvariable=self.theme_name_var, state="readonly", width=16).pack(side="right", padx=10)
        ttk.Button(titlebar, text="Apply Theme", command=self.apply_selected_theme).pack(side="right")
        ttk.Label(titlebar, text="Promoter Office", style="Chrome.TLabel").pack(side="right", padx=18)

        self.statusbar = ttk.Frame(shell, style="Chrome.TFrame")
        self.statusbar.pack(fill="x", padx=8, pady=(0, 4))
        self.stat_month = ttk.Label(self.statusbar, width=18, anchor="center", style="Stat.TLabel")
        self.stat_cash = ttk.Label(self.statusbar, width=24, anchor="center", style="Stat.TLabel")
        self.stat_pop = ttk.Label(self.statusbar, width=24, anchor="center", style="Stat.TLabel")
        self.stat_stability = ttk.Label(self.statusbar, width=18, anchor="center", style="Stat.TLabel")
        for label in (self.stat_month, self.stat_cash, self.stat_pop, self.stat_stability):
            label.pack(side="left", padx=2, ipady=4)

        work = ttk.Frame(shell, style="Chrome.TFrame")
        work.pack(fill="both", expand=True, padx=8, pady=(0, 8))

        nav = ttk.Frame(work, style="Panel.TFrame", width=154)
        nav.pack(side="left", fill="y", padx=(0, 8))
        nav.pack_propagate(False)
        groups = (
            ("TODAY", (("Assistant", "assistant"), ("Inbox", "inbox"), ("Media Desk", "website"), ("Fight Night", "log"))),
            ("PROMOTION", (("Roster", "roster"), ("Matchmaking", "booking"), ("Contracts", "contracts"), ("Free Agents", "market"), ("Staff", "staff"), ("Finance", "finance"))),
            ("WORLD", (("World", "world"), ("Combat Sports", "combat_sports"), ("Companies", "companies"), ("Rankings", "rankings"), ("Results", "results"), ("Regions", "regions"))),
            ("TOOLS", (("Game & Saves", "game_menu"), ("Company Rules", "company_editor"), ("Database Editor", "editor"), ("Sim Lab", "sim_lab"))),
        )
        self.nav_buttons = {}
        for heading, entries in groups:
            ttk.Label(nav, text=heading, anchor="center", style="Section.TLabel").pack(fill="x", padx=6, pady=(5, 2), ipady=2)
            for text, tab in entries:
                command = self.open_combat_sports_window if tab == "combat_sports" else (lambda name=tab: self.select_tab(name))
                button = ttk.Button(nav, text=text, style="Nav.TButton", command=command)
                button.pack(fill="x", padx=8, pady=1)
                self.nav_buttons[tab] = button
        ttk.Separator(nav).pack(fill="x", padx=10, pady=10)
        ttk.Button(nav, text="Quick Save", command=self.save_game).pack(fill="x", padx=10, pady=3)
        ttk.Button(nav, text="Quick Load", command=self.load_game).pack(fill="x", padx=10, pady=3)
        ttk.Button(nav, text="Advance Week", command=self.advance_month).pack(fill="x", padx=10, pady=3)

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
            ("finance", "finance_tab", "Finance"),
            ("booking", "booking_tab", "Booking"),
            ("market", "market_tab", "Free Agents"),
            ("world", "world_tab", "World"),
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
        self.build_finance_tab()
        self.build_booking_tab()
        self.build_market_tab()
        self.build_world_tab()
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
            "finance": self.tab_pages["finance"],
            "booking": self.tab_pages["booking"],
            "market": self.tab_pages["market"],
            "world": self.tab_pages["world"],
            "rankings": self.tab_pages["rankings"],
            "editor": self.tab_pages["editor"],
            "sim_lab": self.tab_pages["sim_lab"],
            "log": self.tab_pages["log"],
        }
        self.tabs.select(lookup[name])
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

    def make_tree_sortable(self, tree):
        tree._sort_reverse = {}
        for col in tree["columns"]:
            label = tree.heading(col, "text")
            tree.heading(col, text=label, command=lambda c=col: self.sort_treeview(tree, c))

    def sort_treeview(self, tree, col):
        reverse = tree._sort_reverse.get(col, False)

        def convert(value):
            text = str(value).strip()
            if text == "C":
                return -1
            cleaned = text.replace("$", "").replace(",", "").replace("%", "")
            if cleaned.startswith("-") and cleaned[1:].replace(".", "", 1).isdigit():
                return float(cleaned)
            if cleaned.replace(".", "", 1).isdigit():
                return float(cleaned)
            record_parts = text.split("-")
            if len(record_parts) >= 2 and all(part.isdigit() for part in record_parts[:2]):
                wins, losses = int(record_parts[0]), int(record_parts[1])
                return wins * 1000 - losses
            return text.lower()

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
        self.save_slot_list = tk.Listbox(save_inner, font=("Tahoma", 9), bg="#c9c9c9")
        self.save_slot_list.pack(fill="both", expand=True)
        row = ttk.Frame(save_inner, style="Inset.TFrame")
        row.pack(fill="x", pady=6)
        self.save_slot_name = tk.StringVar(value="Game 1")
        ttk.Entry(row, textvariable=self.save_slot_name, width=24).pack(side="left", padx=4)
        ttk.Button(row, text="Save Slot", command=self.save_selected_slot).pack(side="left", padx=4)
        ttk.Button(row, text="Load Slot", command=self.load_selected_slot).pack(side="left", padx=4)
        ttk.Button(row, text="Delete Slot", command=self.delete_selected_slot).pack(side="left", padx=4)
        save_tools = ttk.Frame(save_inner, style="Inset.TFrame")
        save_tools.pack(fill="x", pady=(0, 6))
        ttk.Button(save_tools, text="Backup Slot", command=self.backup_selected_slot).pack(side="left", padx=4)
        ttk.Button(save_tools, text="Restore Backup", command=self.open_save_backup_manager).pack(side="left", padx=4)
        ttk.Button(save_tools, text="Open Saves Folder", command=self.open_saves_folder).pack(side="left", padx=4)
        db_panel, db_inner = self.section(body, "DATABASE / WORLD")
        db_panel.pack(side="left", fill="both", expand=True)
        self.database_list = tk.Listbox(db_inner, font=("Tahoma", 9), bg="#c9c9c9")
        self.database_list.pack(fill="both", expand=True)
        dbrow = ttk.Frame(db_inner, style="Inset.TFrame")
        dbrow.pack(fill="x", pady=6)
        self.database_name = tk.StringVar(value="Default Database")
        ttk.Entry(dbrow, textvariable=self.database_name, width=24).pack(side="left", padx=4)
        ttk.Button(dbrow, text="Export Database", command=self.export_database).pack(side="left", padx=4)
        ttk.Button(dbrow, text="Import Quick Save", command=self.import_quick_save_as_database).pack(side="left", padx=4)
        ttk.Button(dbrow, text="Load Database", command=self.load_selected_database).pack(side="left", padx=4)
        ttk.Button(dbrow, text="New Game", style="Accent.TButton", command=self.new_game).pack(side="left", padx=4)
        ttk.Button(dbrow, text="Refresh", command=self.refresh_game_menu).pack(side="left", padx=4)
        universe_row = ttk.Frame(db_inner, style="Inset.TFrame")
        universe_row.pack(fill="x", pady=(0, 6))
        ttk.Button(universe_row, text="Use Selected Universe", style="Accent.TButton", command=self.use_selected_universe_database).pack(side="left", padx=4, pady=3)
        ttk.Button(universe_row, text="Clone Universe", command=self.clone_selected_universe_database).pack(side="left", padx=4, pady=3)
        ttk.Button(universe_row, text="Reset Default Universe", command=self.reset_default_universe_database).pack(side="left", padx=4, pady=3)
        ttk.Button(universe_row, text="Open Database Folder", command=self.open_database_folder).pack(side="right", padx=4, pady=3)
        start_panel, start_inner = self.section(db_inner, "STARTING PROMOTION")
        start_panel.pack(fill="x", pady=(8, 0))
        self.start_company_choice = tk.StringVar(value=PLAYER_PROMOTION_NAME)
        self.start_company_combo = ttk.Combobox(start_inner, textvariable=self.start_company_choice, state="readonly", width=34)
        self.start_company_combo.pack(side="left", padx=4, pady=4)
        ttk.Label(start_inner, text="Choose Spectator Mode to run the whole MMA world without controlling a company.", style="Inset.TLabel").pack(side="left", padx=8)

        self.spectator_sim_panel, spectator = self.section(db_inner, "SPECTATOR WORLD SIMULATION")
        self.spectator_sim_panel.pack(fill="x", pady=(8, 0))
        self.spectator_sim_status = ttk.Label(spectator, text="Observer controls are available in Spectator Mode.", style="Inset.TLabel")
        self.spectator_sim_status.pack(anchor="w", padx=6, pady=(4, 2))
        spectator_actions = ttk.Frame(spectator, style="Inset.TFrame")
        spectator_actions.pack(fill="x", padx=4, pady=4)
        ttk.Button(spectator_actions, text="Sim Week", command=lambda: self.spectator_advance_weeks(1)).pack(side="left", padx=3)
        ttk.Button(spectator_actions, text="Sim Month", command=self.spectator_sim_month).pack(side="left", padx=3)
        ttk.Button(spectator_actions, text="Sim Year", command=self.spectator_sim_year).pack(side="left", padx=3)
        ttk.Button(spectator_actions, text="Watch Next Hosted Event", style="Accent.TButton", command=self.spectator_watch_next_event).pack(side="left", padx=8)
        ttk.Button(spectator_actions, text="Watch Latest Event", command=self.watch_latest_world_event).pack(side="left", padx=3)
        date_row = ttk.Frame(spectator, style="Inset.TFrame")
        date_row.pack(fill="x", padx=4, pady=(0, 4))
        ttk.Label(date_row, text="Sim to", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        self.spectator_target_month = tk.IntVar(value=12)
        self.spectator_target_week = tk.IntVar(value=4)
        ttk.Label(date_row, text="Month", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        ttk.Spinbox(date_row, from_=1, to=240, textvariable=self.spectator_target_month, width=5).pack(side="left")
        ttk.Label(date_row, text="Week", style="Inset.TLabel").pack(side="left", padx=(8, 2))
        ttk.Spinbox(date_row, from_=1, to=4, textvariable=self.spectator_target_week, width=4).pack(side="left")
        ttk.Button(date_row, text="Sim To Date", command=self.spectator_sim_to_date).pack(side="left", padx=6)

    def build_website_tab(self):
        self.screen_header(self.website_tab, "MEDIA DESK", "Manage narrative, press activity, rivalries, and public interest")
        body = ttk.Frame(self.website_tab)
        body.pack(fill="both", expand=True)
        actions = ttk.Frame(body, style="Inset.TFrame")
        actions.pack(fill="x", pady=(0, 6))
        ttk.Label(actions, text="Spokesperson", style="Inset.TLabel").pack(side="left", padx=(6, 2))
        self.media_fighter_combo = ttk.Combobox(actions, textvariable=self.media_fighter_choice, state="readonly", width=22)
        self.media_fighter_combo.pack(side="left", padx=(0, 6))
        self.media_fighter_combo.bind("<<ComboboxSelected>>", self.refresh_media_targets)
        ttk.Label(actions, text="Target", style="Inset.TLabel").pack(side="left", padx=(2, 2))
        self.media_target_combo = ttk.Combobox(actions, textvariable=self.media_target_choice, state="readonly", width=22)
        self.media_target_combo.pack(side="left", padx=(0, 6))
        ttk.Button(actions, text="Call Out", command=self.media_desk_callout).pack(side="left", padx=3)
        ttk.Button(actions, text="Interview", command=self.media_desk_interview).pack(side="left", padx=3)
        ttk.Button(actions, text="Press Tour", style="Accent.TButton", command=self.media_desk_press_tour).pack(side="left", padx=3)
        ttk.Button(actions, text="Open Story Context", command=self.open_selected_story_context).pack(side="right", padx=3)
        left_panel, left = self.section(body, "FEATURED STORY / UPCOMING EVENTS")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.website_story = tk.Text(left, wrap="word", font=("Tahoma", 9, "bold"), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], height=9, padx=10, pady=10)
        self.website_story.pack(fill="x")
        ttk.Label(left, text="Upcoming Events Calendar", style="Section.TLabel", anchor="center").pack(fill="x", pady=(8, 4))
        self.website_calendar = tk.Text(left, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], height=12, padx=10, pady=8)
        self.website_calendar.pack(fill="both", expand=True)
        right_panel, right = self.section(body, "TODAY'S MAJOR STORIES")
        right_panel.pack(side="left", fill="both", expand=True)
        self.website_news = tk.Listbox(right, font=("Tahoma", 9), bg="#c9c9c9")
        self.website_news.pack(fill="both", expand=True)
        self.website_news.bind("<Double-1>", lambda _event: self.open_selected_story_context())

    def build_assistant_tab(self):
        self.screen_header(self.assistant_tab, "PERSONAL ASSISTANT", "Warnings, upcoming shows, quick roster, finance, birthdays, and recommendations")
        top_panel, top = self.section(self.assistant_tab, "COMPANY SNAPSHOT")
        top_panel.pack(fill="x", pady=(0, 6))
        self.assistant_snapshot = ttk.Label(top, text="", justify="left", style="Inset.TLabel")
        self.assistant_snapshot.pack(anchor="w", padx=8, pady=6)
        ttk.Button(top, text="Guided First Week", command=self.open_guided_first_week).pack(anchor="e", padx=8, pady=(0, 6))
        msg_panel, msg = self.section(self.assistant_tab, "MESSAGES FROM PERSONAL ASSISTANT")
        msg_panel.pack(fill="both", expand=True)
        self.assistant_messages = ttk.Treeview(msg, columns=("priority", "notice", "action"), show="headings", height=14)
        for column, label, width in (("priority", "!", 42), ("notice", "Notice", 570), ("action", "Open", 110)):
            self.assistant_messages.heading(column, text=label)
            self.assistant_messages.column(column, width=width, anchor="w")
        self.assistant_messages.tag_configure("urgent", foreground="#ff9b9b")
        self.assistant_messages.tag_configure("normal", foreground="#ffe08a")
        self.assistant_messages.pack(fill="both", expand=True)
        self.assistant_messages.bind("<Double-1>", lambda _event: self.open_selected_assistant_notice())
        ttk.Button(msg, text="Open Selected Context", style="Accent.TButton", command=self.open_selected_assistant_notice).pack(anchor="e", pady=(6, 0))

    def build_companies_tab(self):
        self.screen_header(self.companies_tab, "COMPANY BROWSER", "Company profiles, rosters, upcoming events, recent events, credibility, stability, and size")
        body = ttk.Frame(self.companies_tab)
        body.pack(fill="both", expand=True)
        list_panel, list_inner = self.section(body, "COMPANIES")
        list_panel.pack(side="left", fill="y", padx=(0, 6))
        list_panel.configure(width=220)
        list_panel.pack_propagate(False)
        self.company_list = tk.Listbox(list_inner, font=("Tahoma", 9), bg="#c9c9c9")
        self.company_list.pack(fill="both", expand=True)
        self.company_list.bind("<<ListboxSelect>>", lambda _e: self.refresh_company_profile())
        profile_panel, profile = self.section(body, "COMPANY PROFILE")
        profile_panel.pack(side="left", fill="both", expand=True)
        self.company_profile = tk.Text(profile, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=10, pady=10)
        self.company_profile.pack(fill="both", expand=True)
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
        ttk.Button(company_actions, text="Take Control Of Selected Company", command=self.take_control_selected_company).pack(side="right", padx=4)

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
        search_entry.pack(side="left", padx=4)
        search_entry.bind("<KeyRelease>", lambda _e: self.refresh_results())
        ttk.Button(controls, text="Open Selected", command=self.open_selected_result).pack(side="left", padx=6)
        ttk.Button(controls, text="\U0001F3C6 Awards History", command=self.open_awards_history_window).pack(side="left", padx=6)
        ttk.Button(controls, text="\U0001F396 Hall of Fame", command=self.open_hall_of_fame_window).pack(side="left", padx=6)
        ttk.Button(controls, text="Achievements", style="Accent.TButton", command=self.open_achievements_window).pack(side="left", padx=6)
        ttk.Button(controls, text="Historical Records", command=self.open_records_ledger_window).pack(side="left", padx=6)
        ttk.Button(controls, text="Record Book", command=self.open_record_book_window).pack(side="left", padx=6)
        ttk.Button(controls, text="Legacy Ledger", command=self.open_legacy_ledger).pack(side="left", padx=6)
        body = ttk.Frame(self.results_tab)
        body.pack(fill="both", expand=True)
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
        self.retired_tree = ttk.Treeview(retired, columns=("name", "gender", "weight", "record", "age", "motivation"), show="headings", height=12)
        for col, text, width in (("name", "Fighter", 150), ("gender", "G", 38), ("weight", "Division", 95), ("record", "W-L-D", 84), ("age", "Age", 45), ("motivation", "Mot", 45)):
            self.retired_tree.heading(col, text=text)
            self.retired_tree.column(col, width=width, anchor="center")
        self.retired_tree.column("name", anchor="w")
        self.make_tree_sortable(self.retired_tree)
        self.retired_tree.pack(fill="both", expand=True)
        self.retired_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.retired_tree, "name"))
        ttk.Button(retired, text="Offer Comeback Deal", command=self.unretire_selected_fighter).pack(anchor="e", pady=4)
        detail_panel, detail = self.section(self.results_tab, "DETAIL")
        detail_panel.pack(fill="both", expand=True, pady=(6, 0))
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
        ttk.Button(belt, text="Toggle Selected Weight Class", command=self.toggle_weight_class).pack(anchor="e", pady=4)
        rules_panel, rules = self.section(top, "RULES / BROADCASTERS")
        rules_panel.pack(side="left", fill="both", expand=True)
        self.rules_text = tk.Text(rules, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"], height=10)
        self.rules_text.pack(fill="both", expand=True)
        buttons = ttk.Frame(rules, style="Inset.TFrame")
        buttons.pack(fill="x", pady=4)
        ttk.Button(buttons, text="Cycle Drug Testing", command=self.cycle_drug_testing).pack(side="left", padx=4)
        ttk.Button(buttons, text="Toggle Mixed-Gender Rule", command=self.toggle_mixed_gender_rule).pack(side="left", padx=4)
        ttk.Button(buttons, text="+ Round Minute", command=lambda: self.adjust_round_length(1)).pack(side="left", padx=4)
        ttk.Button(buttons, text="- Round Minute", command=lambda: self.adjust_round_length(-1)).pack(side="left", padx=4)
        ttk.Button(buttons, text="+ Reg Round", command=lambda: self.adjust_regular_rounds(1)).pack(side="left", padx=4)
        ttk.Button(buttons, text="- Reg Round", command=lambda: self.adjust_regular_rounds(-1)).pack(side="left", padx=4)
        ttk.Button(buttons, text="+ Title Round", command=lambda: self.adjust_title_rounds(1)).pack(side="left", padx=4)
        ttk.Button(buttons, text="- Title Round", command=lambda: self.adjust_title_rounds(-1)).pack(side="left", padx=4)
        ttk.Button(buttons, text="+ Fighter Target", command=lambda: self.adjust_active_fighter_target(50)).pack(side="left", padx=4)
        ttk.Button(buttons, text="- Fighter Target", command=lambda: self.adjust_active_fighter_target(-50)).pack(side="left", padx=4)
        ttk.Button(buttons, text="Add Broadcaster", command=self.add_broadcaster).pack(side="left", padx=4)

    def build_inbox_tab(self):
        self.screen_header(self.inbox_tab, "MAIL / DECISIONS", "Owner goals, decisions, contract alerts, suspensions, and business mail")
        body = ttk.Frame(self.inbox_tab)
        body.pack(fill="both", expand=True)
        inbox_panel, inbox = self.section(body, "INBOX")
        inbox_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        controls = ttk.Frame(inbox, style="Inset.TFrame")
        controls.pack(fill="x", pady=(0, 6))
        self.inbox_filter = tk.StringVar(value="Open")
        self.inbox_type_filter = tk.StringVar(value="All")
        ttk.Label(controls, text="Status", style="Inset.TLabel").pack(side="left", padx=(5, 2))
        status = ttk.Combobox(controls, textvariable=self.inbox_filter, values=("Open", "All", "Read"), state="readonly", width=8)
        status.pack(side="left", padx=(0, 7))
        ttk.Label(controls, text="Type", style="Inset.TLabel").pack(side="left", padx=(0, 2))
        kind = ttk.Combobox(controls, textvariable=self.inbox_type_filter, values=("All", "Contract", "Scouting", "Medical", "Roster", "Business", "Staff", "Media", "Rules", "Talent Relations"), state="readonly", width=16)
        kind.pack(side="left")
        status.bind("<<ComboboxSelected>>", lambda _event: self.refresh_inbox())
        kind.bind("<<ComboboxSelected>>", lambda _event: self.refresh_inbox())
        self.inbox_tree = ttk.Treeview(inbox, columns=("state", "type", "subject"), show="headings", height=14)
        for column, text, width in (("state", "", 32), ("type", "Type", 110), ("subject", "Subject", 390)):
            self.inbox_tree.heading(column, text=text)
            self.inbox_tree.column(column, width=width, anchor="w")
        self.inbox_tree.tag_configure("unread", foreground="#ffe08a")
        self.inbox_tree.tag_configure("urgent", foreground="#ff9b9b")
        self.inbox_tree.pack(fill="both", expand=True)
        self.inbox_tree.bind("<<TreeviewSelect>>", self.show_selected_inbox_message)
        self.inbox_tree.bind("<Double-1>", lambda _event: self.open_inbox_context())
        inbox_actions = ttk.Frame(inbox, style="Inset.TFrame")
        inbox_actions.pack(fill="x", pady=(6, 0))
        ttk.Button(inbox_actions, text="Open Context", style="Accent.TButton", command=self.open_inbox_context).pack(side="left", padx=4, pady=4)
        ttk.Button(inbox_actions, text="Medical Decision", command=self.resolve_serious_injury_inbox).pack(side="left", padx=4, pady=4)
        ttk.Button(inbox_actions, text="Mark Read", command=self.mark_inbox_read).pack(side="left", padx=4, pady=4)
        ttk.Button(inbox_actions, text="Hide This Type", command=self.hide_selected_inbox_type).pack(side="left", padx=4, pady=4)
        ttk.Button(inbox_actions, text="Show Hidden Types", command=self.show_all_inbox_types).pack(side="left", padx=4, pady=4)
        ttk.Button(inbox_actions, text="Resolve / Archive", command=self.resolve_inbox_item).pack(side="right", padx=4, pady=4)
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
        detail_panel, detail = self.section(self.inbox_tab, "MESSAGE DETAIL")
        detail_panel.pack(fill="both", expand=True, pady=(6, 0))
        self.inbox_detail = tk.Text(detail, wrap="word", font=("Tahoma", 10), bg=self.colors["panel_dark"], fg=self.colors["text"], insertbackground=self.colors["text"], padx=12, pady=12)
        self.inbox_detail.pack(fill="both", expand=True)

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
        ttk.Button(staff_buttons, text="Hire Selected Candidate", command=self.hire_staff).pack(side="left", padx=4)
        ttk.Button(staff_buttons, text="Assign Scout", command=self.assign_scouting).pack(side="left", padx=4)
        ttk.Button(staff_buttons, text="Run Drug Tests", command=self.run_drug_tests).pack(side="left", padx=4)
        ttk.Button(staff_buttons, text="Hire Commentator", command=self.hire_commentator).pack(side="left", padx=4)
        ttk.Button(staff_buttons, text="View Staff Profile", command=self.open_selected_staff_profile).pack(side="right", padx=4)
        ttk.Button(staff_buttons, text="Fighting Academy", command=self.open_academy_window).pack(side="right", padx=4)
        bonus_panel, bonus = self.section(self.staff_tab, "POST-SHOW BONUSES / SCOUTING")
        bonus_panel.pack(fill="both", expand=True)
        self.staff_text = tk.Text(bonus, wrap="word", font=("Tahoma", 9), bg=self.colors["cream"], fg=self.colors["text"], insertbackground=self.colors["text"])
        self.staff_text.pack(fill="both", expand=True)

    def build_finance_tab(self):
        self.screen_header(self.finance_tab, "FINANCE", "Ticketing, broadcast income, sponsorship, payroll, production, medical, tax, and ledger")
        panel, inner = self.section(self.finance_tab, "CASHFLOW")
        panel.pack(fill="both", expand=True)
        actions = ttk.Frame(inner, style="Inset.TFrame")
        actions.pack(fill="x", pady=(0, 6))
        ttk.Button(actions, text="Pitch Sponsors", command=self.pitch_sponsors).pack(side="left", padx=4)
        ttk.Button(actions, text="Negotiate Media Rights", command=self.negotiate_media_rights).pack(side="left", padx=4)
        ttk.Button(actions, text="Raise Ticket Price", command=lambda: self.adjust_ticket_price(5)).pack(side="right", padx=4)
        ttk.Button(actions, text="Lower Ticket Price", command=lambda: self.adjust_ticket_price(-5)).pack(side="right", padx=4)
        self.finance_summary = ttk.Label(inner, text="", style="Panel.TLabel", justify="left")
        self.finance_summary.pack(fill="x", padx=6, pady=(0, 6))
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
        ttk.Label(top, text="Search", style="Inset.TLabel").pack(side="left")
        roster_search = ttk.Entry(top, textvariable=self.roster_search, width=18)
        roster_search.pack(side="left", padx=(4, 10))
        roster_search.bind("<KeyRelease>", lambda _e: self.refresh_roster())
        ttk.Label(top, text="Weight", style="Inset.TLabel").pack(side="left")
        weight = ttk.Combobox(top, values=["All"] + WEIGHTS, textvariable=self.weight_filter, state="readonly", width=20)
        weight.pack(side="left", padx=(4, 10))
        weight.bind("<<ComboboxSelected>>", lambda _e: self.refresh_roster())
        ttk.Label(top, text="Gender", style="Inset.TLabel").pack(side="left")
        roster_gender = ttk.Combobox(top, values=["All", "Male", "Female"], textvariable=self.roster_gender_filter, state="readonly", width=9)
        roster_gender.pack(side="left", padx=(4, 10))
        roster_gender.bind("<<ComboboxSelected>>", lambda _e: self.refresh_roster())
        ttk.Label(top, text="Status", style="Inset.TLabel").pack(side="left")
        roster_status = ttk.Combobox(top, values=["All", "Ready", "Champion", "Injured", "Tired", "Expiring", "Unhappy"], textvariable=self.roster_status_filter, state="readonly", width=10)
        roster_status.pack(side="left", padx=(4, 0))
        roster_status.bind("<<ComboboxSelected>>", lambda _e: self.refresh_roster())
        ttk.Button(top, text="Career Goals", command=self.open_career_goals_window).pack(side="right", padx=4)

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
        ttk.Button(detail, text="Detailed Skills", command=self.open_detailed_skills_selected).pack(anchor="w", padx=8, pady=4)
        ttk.Button(detail, text="Camp Plan", command=self.choose_camp_focus_selected).pack(anchor="w", padx=8, pady=4)
        ttk.Button(detail, text="Media Callout", command=self.media_callout_selected).pack(anchor="w", padx=8, pady=4)
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
        self.contracts_tree = ttk.Treeview(inner, columns=("name", "gender", "weight", "rank", "pop", "ovr", "months", "purse", "type", "morale", "status"), show="headings")
        for col, text, width in (("name", "Fighter", 160), ("gender", "G", 34), ("weight", "Division", 96), ("rank", "Rank", 52), ("pop", "Pop", 46), ("ovr", "OVR", 46), ("months", "Months", 58), ("purse", "Purse", 88), ("type", "Type", 96), ("morale", "Morale", 58), ("status", "Status", 118)):
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
        line1 = ttk.Frame(header, style="Inset.TFrame")
        line1.pack(fill="x", pady=2)
        line2 = ttk.Frame(header, style="Inset.TFrame")
        line2.pack(fill="x", pady=2)
        ttk.Label(line1, text="Event", style="Inset.TLabel", width=7).pack(side="left")
        ttk.Entry(line1, textvariable=self.event_name, width=34).pack(side="left", padx=(4, 12))
        ttk.Label(line1, text="Venue", style="Inset.TLabel", width=7).pack(side="left")
        ttk.Combobox(line1, textvariable=self.venue, values=["Local Gym", "Regional Arena", "Casino Ballroom", "National Sports Hall"], state="readonly", width=24).pack(side="left", padx=(4, 12))
        ttk.Button(line1, text="Schedule Show", command=self.schedule_event).pack(side="right", padx=(4, 0))
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
        ttk.Spinbox(line2, from_=1, to=240, textvariable=self.event_month, width=5).pack(side="left", padx=(4, 12))
        ttk.Label(line2, text="Week", style="Inset.TLabel", width=5).pack(side="left")
        ttk.Spinbox(line2, from_=1, to=4, textvariable=self.event_week, width=4).pack(side="left", padx=(4, 12))
        ttk.Label(line2, text="Provider", style="Inset.TLabel", width=7).pack(side="left")
        self.event_broadcaster_box = ttk.Combobox(line2, textvariable=self.event_broadcaster, values=["No Coverage"] + [item["name"] for item in self.broadcasters], state="readonly", width=23)
        self.event_broadcaster_box.pack(side="left", padx=(4, 0))
        self.event_broadcaster_box.bind("<<ComboboxSelected>>", self.refresh_event_broadcaster_status)
        self.event_broadcaster_status = ttk.Label(header, text="", style="Inset.TLabel", justify="left")
        self.event_broadcaster_status.pack(fill="x", pady=(4, 0))
        atmosphere_row = ttk.Frame(header, style="Inset.TFrame"); atmosphere_row.pack(fill="x", pady=(4, 0))
        self.event_atmosphere_status = ttk.Label(atmosphere_row, text="", style="Inset.TLabel", justify="left")
        self.event_atmosphere_status.pack(side="left", fill="x", expand=True, padx=4, pady=3)
        ttk.Button(atmosphere_row, text="Fanbase & Atmosphere", command=self.open_fanbase_window).pack(side="right", padx=4, pady=3)

        body = ttk.Frame(self.booking_tab)
        body.pack(fill="both", expand=True)
        left_panel, left = self.section(body, "AVAILABLE FIGHTERS")
        left_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        right_panel, right = self.section(body, "CURRENT FIGHT CARD")
        right_panel.pack(side="left", fill="both", expand=True)

        available_filters = ttk.Frame(left, style="Inset.TFrame")
        available_filters.pack(fill="x", pady=(0, 5))
        ttk.Label(available_filters, text="Search", style="Inset.TLabel").pack(side="left")
        available_search = ttk.Entry(available_filters, textvariable=self.available_search, width=16)
        available_search.pack(side="left", padx=(4, 8))
        available_search.bind("<KeyRelease>", lambda _e: self.refresh_available())
        ttk.Label(available_filters, text="Weight", style="Inset.TLabel").pack(side="left")
        available_weight = ttk.Combobox(available_filters, values=["All"] + WEIGHTS, textvariable=self.available_weight_filter, state="readonly", width=14)
        available_weight.pack(side="left", padx=(4, 8))
        available_weight.bind("<<ComboboxSelected>>", lambda _e: self.refresh_available())
        ttk.Label(available_filters, text="Gender", style="Inset.TLabel").pack(side="left")
        available_gender = ttk.Combobox(available_filters, values=["All", "Male", "Female"], textvariable=self.available_gender_filter, state="readonly", width=8)
        available_gender.pack(side="left", padx=(4, 8))
        available_gender.bind("<<ComboboxSelected>>", lambda _e: self.refresh_available())
        ttk.Label(available_filters, text="Status", style="Inset.TLabel").pack(side="left")
        available_status = ttk.Combobox(available_filters, values=["All", "Ready", "Champion", "Injured", "Tired", "Expiring", "Unhappy"], textvariable=self.available_status_filter, state="readonly", width=9)
        available_status.pack(side="left", padx=(4, 0))
        available_status.bind("<<ComboboxSelected>>", lambda _e: self.refresh_available())

        self.available_tree = ttk.Treeview(left, columns=("name", "gender", "weight", "rank", "record", "overall", "pop", "build", "status"), show="headings", selectmode="extended", height=14)
        for col, text, width in (("name", "Name", 150), ("gender", "G", 42), ("weight", "Class", 96), ("rank", "Rank", 48), ("record", "Record", 66), ("overall", "OVR", 48), ("pop", "Pop", 48), ("build", "Build", 54), ("status", "Status", 90)):
            self.available_tree.heading(col, text=text)
            self.available_tree.column(col, width=width, anchor="center")
        self.available_tree.column("name", anchor="w")
        self.make_tree_sortable(self.available_tree)
        available_scroll = ttk.Scrollbar(left, orient="vertical", command=self.available_tree.yview)
        self.available_tree.configure(yscrollcommand=available_scroll.set)
        available_scroll.pack(side="right", fill="y")
        self.available_tree.pack(side="left", fill="both", expand=True, pady=5)
        self.available_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.available_tree, "name"))

        controls = ttk.Frame(left)
        controls.pack(fill="x")
        ttk.Checkbutton(controls, text="Title fight", variable=self.title_fight).pack(side="left")
        ttk.Checkbutton(controls, text="Main event", variable=self.main_event).pack(side="left", padx=12)
        ttk.Label(controls, text="Tier", style="Inset.TLabel").pack(side="left")
        ttk.Combobox(controls, textvariable=self.card_tier, values=CARD_TIERS, state="readonly", width=14).pack(side="left", padx=6)
        ttk.Button(controls, text="Add Matchup", command=self.add_matchup).pack(side="right")
        ttk.Button(controls, text="Add TBA Opponent", command=self.add_tba_matchup).pack(side="right", padx=4)
        ttk.Button(controls, text="Assistant Pick", command=self.assistant_pick_matchup).pack(side="right", padx=4)

        self.card_tree = ttk.Treeview(right, columns=("slot", "fight", "weight", "hype", "media"), show="headings", height=14)
        for col, text, width in (("slot", "Slot", 90), ("fight", "Fight", 250), ("weight", "Weight", 105), ("hype", "Hype", 60), ("media", "Build", 60)):
            self.card_tree.heading(col, text=text)
            self.card_tree.column(col, width=width, anchor="center")
        self.card_tree.column("fight", anchor="w")
        self.make_tree_sortable(self.card_tree)
        self.card_tree.pack(fill="both", expand=True, pady=5)
        footer = ttk.Frame(right)
        footer.pack(fill="x")
        ttk.Button(footer, text="Remove Fight", command=self.remove_matchup).pack(side="left")
        ttk.Button(footer, text="Fill TBA", command=self.fill_selected_tba_matchup).pack(side="left", padx=4)
        ttk.Button(footer, text="Title / Interim", command=self.toggle_card_title).pack(side="left", padx=4)
        ttk.Button(footer, text="Move Up", command=self.move_fight_up).pack(side="left", padx=4)
        ttk.Button(footer, text="Move Down", command=self.move_fight_down).pack(side="left", padx=4)
        ttk.Button(footer, text="Clear Card", command=self.clear_card).pack(side="right")

        upcoming_panel, upcoming = self.section(self.booking_tab, "UPCOMING EVENTS")
        upcoming_panel.pack(fill="x", pady=(6, 0))
        self.upcoming_tree = ttk.Treeview(upcoming, columns=("date", "event", "venue", "region", "fights", "status"), show="headings", height=4)
        for col, text, width in (("date", "Date", 90), ("event", "Event", 205), ("venue", "Venue", 120), ("region", "Region", 110), ("fights", "Fights", 60), ("status", "Status", 90)):
            self.upcoming_tree.heading(col, text=text)
            self.upcoming_tree.column(col, width=width, anchor="center")
        self.upcoming_tree.column("event", anchor="w")
        self.make_tree_sortable(self.upcoming_tree)
        self.upcoming_tree.pack(fill="x")

    def build_market_tab(self):
        self.screen_header(self.market_tab, "FREE AGENTS", "Scout talent and negotiate new contracts")
        panel, inner = self.section(self.market_tab, "AVAILABLE WORKERS")
        panel.pack(fill="both", expand=True, pady=(0, 8))
        filters = ttk.Frame(inner, style="Inset.TFrame")
        filters.pack(fill="x", pady=(0, 6))
        ttk.Label(filters, text="Weight", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        market_weight = ttk.Combobox(filters, values=["All"] + WEIGHTS, textvariable=self.market_weight_filter, state="readonly", width=18)
        market_weight.pack(side="left", padx=(0, 10))
        market_weight.bind("<<ComboboxSelected>>", lambda _e: self.refresh_market())
        ttk.Label(filters, text="Gender", style="Inset.TLabel").pack(side="left", padx=(4, 2))
        market_gender = ttk.Combobox(filters, values=["All", "Male", "Female"], textvariable=self.market_gender_filter, state="readonly", width=10)
        market_gender.pack(side="left", padx=(0, 10))
        market_gender.bind("<<ComboboxSelected>>", lambda _e: self.refresh_market())
        self.scouting_mode_var = tk.BooleanVar(value=self.rules.get("scouting_mode", False))
        ttk.Checkbutton(filters, text="Scouting Mode", variable=self.scouting_mode_var, command=self.toggle_scouting_mode).pack(side="left", padx=(0, 8))
        ttk.Button(filters, text="Basic Scout (2 wk)", command=lambda: self.start_selected_scout_report("basic")).pack(side="left", padx=2)
        ttk.Button(filters, text="Full Scout (6 wk)", command=lambda: self.start_selected_scout_report("full")).pack(side="left", padx=2)
        self.market_tree = ttk.Treeview(inner, columns=("name", "tag", "gender", "weight", "record", "age", "overall", "popularity", "star", "media", "pro", "style", "purse", "offer"), show="headings")
        for col, text, width in (("name", "Name", 155), ("tag", "Scout", 88), ("gender", "G", 38), ("weight", "Weight", 100), ("record", "Record", 65), ("age", "Age", 45), ("overall", "OVR", 50), ("popularity", "Pop", 50), ("star", "Star", 50), ("media", "Media", 55), ("pro", "Pro", 45), ("style", "Style", 90), ("purse", "Asking", 80), ("offer", "Rival Offer", 145)):
            self.market_tree.heading(col, text=text)
            self.market_tree.column(col, width=width, anchor="center")
        self.market_tree.column("name", anchor="w")
        self.make_tree_sortable(self.market_tree)
        market_scroll = ttk.Scrollbar(inner, orient="vertical", command=self.market_tree.yview)
        self.market_tree.configure(yscrollcommand=market_scroll.set)
        market_scroll.pack(side="right", fill="y")
        self.market_tree.pack(side="left", fill="both", expand=True)
        self.market_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.market_tree, "name"))
        self.market_tree.bind("<<TreeviewSelect>>", lambda _e: self.refresh_market_scout_panel())
        scout_panel = tk.Frame(inner, bg=self.colors["panel_dark"], width=300, highlightthickness=1, highlightbackground=self.colors["line"])
        scout_panel.pack(side="right", fill="y", padx=(8, 0))
        scout_panel.pack_propagate(False)
        tk.Label(scout_panel, text="SCOUTING READ", font=("Impact", 15), bg=self.colors["panel_dark"], fg=self.colors["gold"]).pack(anchor="w", padx=10, pady=(8, 2))
        self.market_scout_text = tk.Text(scout_panel, height=18, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=9, pady=8, bd=0)
        self.market_scout_text.pack(fill="both", expand=True, padx=6, pady=(0, 6))
        self.market_scout_text.insert("end", "Select a free agent to see scouting confidence, risk, and action advice.")
        self.market_scout_text.config(state="disabled")
        ttk.Button(self.market_tab, text="Negotiate", command=self.open_negotiation).pack(anchor="e")

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
        self.world_news_detail = tk.Text(right, wrap="word", font=("Tahoma", 9), bg=self.colors["panel_dark"], fg=self.colors["text"], height=5, padx=10, pady=8)
        self.world_news_detail.pack(fill="x", pady=(0, 5))
        self.world_news_detail.config(state="disabled")
        news_actions = ttk.Frame(right, style="Inset.TFrame")
        news_actions.pack(fill="x", pady=(0, 6))
        ttk.Button(news_actions, text="Open Story Context", command=self.open_selected_world_story_context).pack(side="left", padx=4, pady=3)
        ttk.Button(news_actions, text="Combat Sports", command=self.open_combat_sports_window).pack(side="left", padx=4, pady=3)
        ttk.Button(news_actions, text="World Chronicle", command=self.open_world_chronicle).pack(side="right", padx=4, pady=3)
        ttk.Label(right, text="GYM NETWORK", style="PanelTitle.TLabel").pack(anchor="w")
        self.gym_tree = ttk.Treeview(right, columns=("name", "region", "quality", "rep", "morale", "members", "specialty"), show="headings", height=6)
        for col, text, width in (("name", "Gym", 145), ("region", "Region", 70), ("quality", "Q", 42), ("rep", "Rep", 45), ("morale", "Room", 52), ("members", "Fighters", 64), ("specialty", "Specialties", 185)):
            self.gym_tree.heading(col, text=text)
            self.gym_tree.column(col, width=width, anchor="center")
        self.gym_tree.column("name", anchor="w")
        self.gym_tree.column("specialty", anchor="w")
        self.make_tree_sortable(self.gym_tree)
        self.gym_tree.pack(fill="x")
        self.gym_tree.bind("<Double-1>", lambda _e: self.open_selected_gym_viewer())
        ttk.Button(right, text="View Gym", command=self.open_selected_gym_viewer).pack(anchor="e", pady=(6, 0))

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
        self.rankings_tree = ttk.Treeview(inner, columns=("company_rank", "world_rank", "move", "name", "gender", "company", "weight", "record", "overall", "form", "path", "score", "last", "status"), show="headings")
        for col, text, width in (("company_rank", "Co Rank", 62), ("world_rank", "World", 58), ("move", "Move", 60), ("name", "Fighter", 150), ("gender", "G", 38), ("company", "Company", 135), ("weight", "Division", 100), ("record", "Record", 70), ("overall", "OVR", 55), ("form", "Form", 90), ("path", "Title Path", 135), ("score", "Score", 65), ("last", "Last Fight", 120), ("status", "Status", 85)):
            self.rankings_tree.heading(col, text=text)
            self.rankings_tree.column(col, width=width, anchor="center")
        self.rankings_tree.column("name", anchor="w")
        self.rankings_tree.column("company", anchor="w")
        self.rankings_tree.column("last", anchor="w")
        self.make_tree_sortable(self.rankings_tree)
        self.rankings_tree.bind("<Double-1>", lambda _e: self.open_tree_fighter_profile(self.rankings_tree, "name"))
        self.rankings_tree.pack(fill="both", expand=True)
        self.ranking_detail = tk.Text(inner, height=4, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        self.ranking_detail.pack(fill="x", pady=(6, 0)); self.ranking_detail.config(state="disabled")
        self.rankings_tree.bind("<<TreeviewSelect>>", self.show_ranking_detail)

    def build_editor_tab(self):
        self.screen_header(self.editor_tab, "DATABASE EDITOR", "Edit every active fighter, their ratings, contracts, ownership, and detailed fight attributes")
        controls = ttk.Frame(self.editor_tab, style="Chrome.TFrame")
        controls.pack(fill="x", pady=(0, 6))
        self.editor_search = tk.StringVar(value="")
        self.editor_company_filter = tk.StringVar(value="All")
        self.editor_weight_filter = tk.StringVar(value="All")
        self.editor_gender_filter = tk.StringVar(value="All")
        ttk.Label(controls, text="Search", style="Chrome.TLabel").pack(side="left", padx=(4, 2))
        search = ttk.Entry(controls, textvariable=self.editor_search, width=24)
        search.pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Employer", style="Chrome.TLabel").pack(side="left", padx=(0, 2))
        self.editor_company_combo = ttk.Combobox(controls, textvariable=self.editor_company_filter, width=26, state="readonly")
        self.editor_company_combo.pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Division", style="Chrome.TLabel").pack(side="left", padx=(0, 2))
        ttk.Combobox(controls, textvariable=self.editor_weight_filter, values=["All"] + WEIGHTS, width=16, state="readonly").pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Gender", style="Chrome.TLabel").pack(side="left", padx=(0, 2))
        ttk.Combobox(controls, textvariable=self.editor_gender_filter, values=["All", "Male", "Female"], width=9, state="readonly").pack(side="left", padx=(0, 8))
        self.universe_section_choice = tk.StringVar(value="fighters")
        ttk.Label(controls, text="Universe Section", style="Chrome.TLabel").pack(side="left", padx=(0, 2))
        ttk.Combobox(controls, textvariable=self.universe_section_choice, values=["fighters", "companies", "combat_sports", "media", "regions"], width=14, state="readonly").pack(side="left", padx=(0, 4))
        ttk.Button(controls, text="Edit Section JSON", command=self.open_universe_section_editor).pack(side="left", padx=2)
        ttk.Button(controls, text="Validate Universe", command=self.validate_active_universe_database).pack(side="left", padx=2)
        ttk.Button(controls, text="Refresh", command=self.refresh_database_editor).pack(side="right", padx=4)
        for variable in (self.editor_search, self.editor_company_filter, self.editor_weight_filter, self.editor_gender_filter):
            variable.trace_add("write", lambda *_args: self.refresh_database_editor())

        body = ttk.Frame(self.editor_tab, style="Chrome.TFrame")
        body.pack(fill="both", expand=True)
        list_panel, list_inner = self.section(body, "FIGHTER DATABASE")
        list_panel.pack(side="left", fill="both", expand=True, padx=(0, 6))
        self.editor_tree = ttk.Treeview(list_inner, columns=("company", "name", "gender", "weight", "age", "overall", "potential", "pop", "record", "status"), show="headings", height=22)
        for col, title, width in (("company", "Employer", 135), ("name", "Fighter", 155), ("gender", "G", 38), ("weight", "Division", 95), ("age", "Age", 42), ("overall", "OVR", 48), ("potential", "Upside", 55), ("pop", "Pop", 45), ("record", "Record", 70), ("status", "Status", 84)):
            self.editor_tree.heading(col, text=title)
            self.editor_tree.column(col, width=width, anchor="center")
        self.editor_tree.column("company", anchor="w")
        self.editor_tree.column("name", anchor="w")
        self.editor_tree.pack(fill="both", expand=True)
        self.make_tree_sortable(self.editor_tree)
        self.editor_tree.bind("<<TreeviewSelect>>", lambda _event: self.load_selected_editor_fighter())
        self.editor_tree.bind("<Double-1>", lambda _event: self.open_editor_selected_profile())

        edit_panel, edit_inner = self.section(body, "FIGHTER WORKBENCH")
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
            ("Camp", "camp", "combo:" + "|".join(CAMPS)), ("Record Wins", "record_w", "spin:0:120"),
            ("Record Losses", "record_l", "spin:0:120"), ("Record Draws", "record_d", "spin:0:30"),
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
        ttk.Button(actions, text="Save Changes", style="Accent.TButton", command=self.save_database_editor_fighter).pack(side="left", padx=4, pady=4)
        ttk.Button(actions, text="Detailed Skill Sheet", command=self.open_detailed_skill_editor).pack(side="left", padx=4, pady=4)
        ttk.Button(actions, text="View Profile", command=self.open_editor_selected_profile).pack(side="left", padx=4, pady=4)
        ttk.Button(actions, text="Retire Fighter", command=self.retire_database_editor_fighter).pack(side="right", padx=4, pady=4)

    def build_sim_lab_tab(self):
        self.screen_header(self.sim_lab_tab, "SIMULATION LAB", "Division-aware fight testing, scouting cards, bracket simulations, and engine audits")
        top = ttk.Frame(self.sim_lab_tab)
        top.pack(fill="x", pady=(0, 6))
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
