"""Standalone universe database editor shipped with MMA Warriors.

The game reads universe packs directly, so this tool deliberately edits the
same JSON files. It never opens or rewrites career saves.
"""

import json
import os
import shutil
import sys
from copy import deepcopy
from dataclasses import asdict
from datetime import datetime
from pathlib import Path
import tkinter as tk
from tkinter import filedialog, messagebox, simpledialog, ttk

from constants import (
    ASSET_DIR, BEHAVIOURS, CAMPS, COUNTRY_TO_REGION, DATABASE_DIR, PLAYER_PROMOTION_NAME,
    REGIONS, STYLES, TRAITS, WEIGHTS,
)
from models import Fighter, Promotion


DEFAULT_UNIVERSE_NAME = "Default Universe.universe.json"
DATABASE_EDITOR_ICON = ASSET_DIR / "database_editor_icon.ico"
FIGHTER_REQUIRED_FIELDS = ("name", "placement", "owner", "weight", "gender", "rating", "age", "region", "nationality")
COMPANY_REQUIRED_FIELDS = ("name", "region", "size", "cash", "roster_key")
FIGHTER_AUTHOR_FIELDS = {
    "database_type": "mma", "generated": False, "placement": "promotion", "owner": "Free Agent",
    "seed_org": "Free Agent", "rating": 65, "profile_rating": 65, "profile_style": "Well-Rounded",
    "skill_mods": {}, "signature_skills": {}, "special_profile": "", "prime_age": None,
    "nexgen_prospect": False, "regional_feeder_headliner": False, "record_note": "", "record_as_of": "",
}
COMPANY_AUTHOR_FIELDS = {
    "roster_key": "", "target_roster_size": 120, "personality": "Balanced", "player_company": False,
}
COUNTRIES = tuple(sorted(COUNTRY_TO_REGION, key=str.casefold))
FIGHTER_VALUE_CHOICES = {
    "database_type": ("mma",),
    "placement": ("promotion", "player_roster", "free_agents"),
    "weight": tuple(WEIGHTS),
    "gender": ("Male", "Female"),
    "region": tuple(REGIONS),
    "birth_region": tuple(REGIONS),
    "residence": tuple(REGIONS),
    "training_location": tuple(REGIONS),
    "birth_country": COUNTRIES,
    "nationality": (),
    "style": tuple(STYLES),
    "profile_style": tuple(STYLES),
    "stance": ("Orthodox", "Southpaw", "Switch"),
    "trait": tuple(TRAITS),
    "behaviour": tuple(BEHAVIOURS),
    "camp": tuple(CAMPS),
    "career_archetype": ("Early Maturation", "Balanced Development", "Late Maturation", "Durable Career"),
    "contract_type": ("Exclusive", "Non-Exclusive", "Developmental"),
    "negotiation_persona": ("Professional", "Hard Bargainer", "Loyalist", "Star Chaser", "Security First", "Competitive"),
    "camp_focus": ("Balanced", "Striking", "Wrestling", "Grappling", "Conditioning"),
    "camp_intensity": ("Light", "Standard", "Hard"),
}
COMPANY_VALUE_CHOICES = {
    "region": tuple(REGIONS),
    "reputation": ("Local", "Regional", "National", "International", "Global", "Regional Player Company", "Regional Feeder"),
    "personality": ("Balanced", "Star Builder", "Prospect Builder", "Seasonal", "Super Shows", "Regional Development"),
    "show_personality": ("Balanced", "Star Builder", "Prospect Builder", "Seasonal", "Super Shows", "Regional Development"),
}
BOOLEAN_VALUES = ("true", "false")
FIGHTER_NUMERIC_AUTHOR_FIELDS = {
    "rating", "profile_rating", "prime_age", "record_w", "record_l", "record_d", "popularity",
    "potential", "star_quality", "charisma", "professionalism", "injury_proneness", "finishing_instinct",
    "media_presence", "sponsor_appeal",
}


def json_value(text):
    """Read a JSON value, with bare text treated as a string for speed."""
    text = text.strip()
    if not text:
        return ""
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def compact_json(value):
    return json.dumps(value, ensure_ascii=True, separators=(",", ": "))


def atomic_write_json(path, payload):
    path = Path(path)
    temporary = path.with_suffix(path.suffix + ".writing")
    temporary.write_text(json.dumps(payload, indent=2, ensure_ascii=True) + "\n", encoding="utf-8")
    os.replace(temporary, path)


def fighter_row_from_record(record):
    """Keep the legacy grouped fighter views synchronized with all_fighters."""
    owner = record.get("owner") or record.get("company") or record.get("promotion") or "Free Agent"
    row = [
        record.get("name", "Unnamed Fighter"),
        record.get("weight", "Lightweight"),
        record.get("seed_org") or owner,
        int(record.get("popularity", record.get("pop", 35)) or 35),
        int(record.get("rating", record.get("skill", record.get("overall", 65))) or 65),
        int(record.get("age", 28) or 28),
        int(record.get("record_w", record.get("wins", 0)) or 0),
        int(record.get("record_l", record.get("losses", 0)) or 0),
        record.get("region", "USA"),
        record.get("style", "Well-Rounded"),
    ]
    extras = (
        record.get("source_url", ""), record.get("gender", ""), record.get("potential", ""),
        record.get("nationality", ""), record.get("birth_country", ""), record.get("hometown", ""),
    )
    appended = []
    if any(value not in ("", None) for value in extras):
        appended.append(extras[0])
    if any(value not in ("", None) for value in extras[1:]):
        appended.append(extras[1])
    for value in extras[2:]:
        if appended or value not in ("", None):
            appended.append(value)
    return row + appended


def sync_fighter_groups(section):
    records = [dict(record) for record in section.get("all_fighters", []) if isinstance(record, dict)]
    player_roster, free_agents, promotions = [], [], {}
    seen = set()
    for record in records:
        name = str(record.get("name", "")).strip()
        owner = str(record.get("owner", "")).strip() or "Free Agent"
        key = (name.casefold(), owner.casefold())
        if not name or key in seen:
            continue
        seen.add(key)
        row = fighter_row_from_record(record)
        placement = str(record.get("placement", "promotion")).lower()
        if placement in ("player", "player_roster") or owner == PLAYER_PROMOTION_NAME:
            player_roster.append(row)
        elif placement in ("free_agent", "free_agents") or owner in ("Free Agent", "Legend"):
            free_agents.append(row)
        else:
            promotions.setdefault(owner, []).append(row)
    section["all_fighters"] = records
    section["player_roster"] = player_roster
    section["free_agents"] = free_agents
    section["promotions"] = promotions
    section["schema"] = max(4, int(section.get("schema", 1) or 1))


def validate_universe_pack(pack):
    issues = []
    if not isinstance(pack, dict) or pack.get("type") != "universe_database":
        return ["This is not a universe database pack."]
    sections = pack.get("sections")
    if not isinstance(sections, dict):
        return ["Universe pack has no sections object."]
    fighters = sections.get("fighters", {})
    records = fighters.get("all_fighters", []) if isinstance(fighters, dict) else []
    if not isinstance(records, list) or not records:
        issues.append("fighters.all_fighters must contain fighter records.")
    seen_fighters = set()
    for record in records:
        if not isinstance(record, dict):
            issues.append("A fighter record is not an object.")
            continue
        missing = [key for key in FIGHTER_REQUIRED_FIELDS if record.get(key) in (None, "")]
        if missing:
            issues.append(f"Fighter {record.get('name', '<unnamed>')}: missing {', '.join(missing)}")
        key = (str(record.get("name", "")).casefold(), str(record.get("owner", "")).casefold())
        if key in seen_fighters:
            issues.append(f"Duplicate fighter/owner pair: {record.get('name', '<unnamed>')}")
        seen_fighters.add(key)
        for field in ("rating", "age", "record_w", "record_l", "record_d"):
            value = record.get(field, 0)
            if not isinstance(value, int):
                issues.append(f"Fighter {record.get('name', '<unnamed>')}: {field} must be an integer.")
        if isinstance(record.get("rating"), int) and not 1 <= record["rating"] <= 99:
            issues.append(f"Fighter {record.get('name', '<unnamed>')}: rating must be 1-99.")
        if isinstance(record.get("age"), int) and not 14 <= record["age"] <= 70:
            issues.append(f"Fighter {record.get('name', '<unnamed>')}: age must be 14-70.")
    companies = sections.get("companies", {})
    promotions = companies.get("promotions", []) if isinstance(companies, dict) else []
    if not isinstance(promotions, list):
        issues.append("companies.promotions must be a list.")
    seen_companies = set()
    for company in promotions if isinstance(promotions, list) else []:
        if not isinstance(company, dict):
            issues.append("A promotion record is not an object.")
            continue
        missing = [key for key in COMPANY_REQUIRED_FIELDS if company.get(key) in (None, "")]
        if missing:
            issues.append(f"Company {company.get('name', '<unnamed>')}: missing {', '.join(missing)}")
        name = str(company.get("name", "")).casefold()
        if name in seen_companies:
            issues.append(f"Duplicate company: {company.get('name', '<unnamed>')}")
        seen_companies.add(name)
    feeders = companies.get("regional_feeders", []) if isinstance(companies, dict) else []
    if not isinstance(feeders, list):
        issues.append("companies.regional_feeders must be a list.")
    for feeder in feeders if isinstance(feeders, list) else []:
        if not isinstance(feeder, dict) or not feeder.get("name") or not feeder.get("region"):
            issues.append("Every regional feeder needs a name and region.")
    return issues


class UniverseDatabaseEditor:
    def __init__(self, root):
        self.root = root
        self.root.title(f"{GAME_TITLE} Database Editor")
        self.root.geometry("1480x900")
        self.root.minsize(1120, 700)
        self.database_dir = DATABASE_DIR
        self.database_dir.mkdir(parents=True, exist_ok=True)
        self.path = None
        self.pack = None
        self.fighter_defaults = self.build_fighter_defaults()
        self.company_defaults = self.build_company_defaults()
        self.fighter_selection = None
        self.company_selection = None
        self.table_sort = {"fighter": ("name", False), "company": ("name", False)}
        self.table_specs = {}
        self.configure_style()
        self.build_ui()
        self.refresh_database_selector(select_name=DEFAULT_UNIVERSE_NAME)
        default = self.database_dir / DEFAULT_UNIVERSE_NAME
        if default.exists():
            self.load_database(default)

    def configure_style(self):
        colors = {"bg": "#09131f", "panel": "#102236", "inset": "#0b1a2b", "text": "#e6f2f2", "muted": "#9db7c7", "accent": "#32d583", "line": "#244760"}
        self.colors = colors
        self.root.configure(bg=colors["bg"])
        style = ttk.Style(self.root)
        style.theme_use("clam")
        style.configure("TFrame", background=colors["bg"])
        style.configure("Panel.TFrame", background=colors["panel"])
        style.configure("Inset.TFrame", background=colors["inset"])
        style.configure("TLabel", background=colors["bg"], foreground=colors["text"], font=("Tahoma", 9))
        style.configure("Panel.TLabel", background=colors["panel"], foreground=colors["text"], font=("Tahoma", 9))
        style.configure("Title.TLabel", background=colors["bg"], foreground=colors["text"], font=("Tahoma", 16, "bold"))
        style.configure("Muted.TLabel", background=colors["bg"], foreground=colors["muted"], font=("Tahoma", 9))
        style.configure("TButton", padding=(8, 5), background=colors["panel"], foreground=colors["text"])
        style.map("TButton", background=[("active", "#193956")])
        style.configure("Accent.TButton", background=colors["accent"], foreground="#062116", font=("Tahoma", 9, "bold"))
        style.map("Accent.TButton", background=[("active", "#60e9ab")])
        style.configure("TEntry", fieldbackground=colors["inset"], background=colors["inset"], foreground=colors["text"], insertcolor=colors["text"], bordercolor=colors["line"], lightcolor=colors["line"], darkcolor=colors["line"])
        style.map("TEntry", fieldbackground=[("readonly", colors["inset"]), ("disabled", colors["panel"])], foreground=[("readonly", colors["text"]), ("disabled", colors["muted"])])
        style.configure("TCombobox", fieldbackground=colors["inset"], background=colors["panel"], foreground=colors["text"], arrowcolor=colors["text"], bordercolor=colors["line"], lightcolor=colors["line"], darkcolor=colors["line"])
        style.map("TCombobox", fieldbackground=[("readonly", colors["inset"]), ("disabled", colors["panel"])], background=[("readonly", colors["panel"]), ("disabled", colors["panel"])], foreground=[("readonly", colors["text"]), ("disabled", colors["muted"])], selectbackground=[("readonly", colors["inset"])], selectforeground=[("readonly", colors["text"])])
        style.configure("TSpinbox", fieldbackground=colors["inset"], background=colors["panel"], foreground=colors["text"], arrowcolor=colors["text"], insertcolor=colors["text"], bordercolor=colors["line"], lightcolor=colors["line"], darkcolor=colors["line"])
        style.map("TSpinbox", fieldbackground=[("readonly", colors["inset"]), ("disabled", colors["panel"])], background=[("readonly", colors["panel"]), ("disabled", colors["panel"])], foreground=[("readonly", colors["text"]), ("disabled", colors["muted"])])
        style.configure("Treeview", background=colors["inset"], fieldbackground=colors["inset"], foreground=colors["text"], rowheight=25, bordercolor=colors["line"])
        style.map("Treeview", background=[("selected", "#1c5a70")], foreground=[("selected", "#ffffff")])
        style.configure("Treeview.Heading", background=colors["panel"], foreground=colors["text"], font=("Tahoma", 9, "bold"), relief="flat")
        style.configure("TNotebook", background=colors["bg"], borderwidth=0)
        style.configure("TNotebook.Tab", background=colors["panel"], foreground=colors["muted"], padding=(10, 6))
        style.map("TNotebook.Tab", background=[("selected", "#1c405a")], foreground=[("selected", "#ffffff")])

    def build_ui(self):
        header = ttk.Frame(self.root)
        header.pack(fill="x", padx=12, pady=(10, 6))
        ttk.Label(header, text="DATABASE EDITOR", style="Title.TLabel").pack(side="left")
        self.status_var = tk.StringVar(value="Choose a universe database to begin.")
        ttk.Label(header, textvariable=self.status_var, style="Muted.TLabel").pack(side="right")

        toolbar = ttk.Frame(self.root, style="Panel.TFrame")
        toolbar.pack(fill="x", padx=12, pady=(0, 8))
        ttk.Label(toolbar, text="Database", style="Panel.TLabel").pack(side="left", padx=(8, 4), pady=7)
        self.database_choice = tk.StringVar()
        self.database_selector = ttk.Combobox(toolbar, textvariable=self.database_choice, state="readonly", width=38)
        self.database_selector.pack(side="left", padx=(0, 4), pady=7)
        self.database_selector.bind("<<ComboboxSelected>>", lambda _event: self.load_selected_database())
        ttk.Button(toolbar, text="Browse", command=self.browse_database).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Copy Current", command=self.copy_current_database).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Save", style="Accent.TButton", command=self.save_database).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Save As", command=self.save_database_as).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Validate", command=self.validate_database).pack(side="left", padx=3)
        ttk.Button(toolbar, text="Open Folder", command=self.open_database_folder).pack(side="right", padx=8)

        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill="both", expand=True, padx=12, pady=(0, 12))
        self.fighters_tab = ttk.Frame(self.notebook)
        self.companies_tab = ttk.Frame(self.notebook)
        self.notebook.add(self.fighters_tab, text="Fighters")
        self.notebook.add(self.companies_tab, text="Companies")
        self.build_fighters_tab()
        self.build_companies_tab()

    def build_fighters_tab(self):
        filters = ttk.Frame(self.fighters_tab, style="Panel.TFrame")
        filters.pack(fill="x", pady=(0, 8))
        self.fighter_search = tk.StringVar()
        self.fighter_owner_filter = tk.StringVar(value="All companies")
        self.fighter_weight_filter = tk.StringVar(value="All weights")
        self.fighter_gender_filter = tk.StringVar(value="All genders")
        for label, variable, width in (("Search", self.fighter_search, 24), ("Company", self.fighter_owner_filter, 26), ("Weight", self.fighter_weight_filter, 18), ("Gender", self.fighter_gender_filter, 14)):
            ttk.Label(filters, text=label, style="Panel.TLabel").pack(side="left", padx=(8, 3), pady=7)
            if label == "Company":
                combo = ttk.Combobox(filters, textvariable=variable, state="readonly", width=width)
                self.fighter_owner_combo = combo
            elif label == "Weight":
                combo = ttk.Combobox(filters, textvariable=variable, state="readonly", width=width)
                self.fighter_weight_combo = combo
            elif label == "Gender":
                combo = ttk.Combobox(filters, textvariable=variable, state="readonly", width=width)
                self.fighter_gender_combo = combo
            else:
                combo = ttk.Entry(filters, textvariable=variable, width=width)
            combo.pack(side="left", padx=(0, 4), pady=7)
            if label == "Search":
                combo.bind("<KeyRelease>", lambda _event: self.refresh_fighters())
            else:
                combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_fighters())
        ttk.Button(filters, text="Clear", command=self.clear_fighter_filters).pack(side="left", padx=4)
        ttk.Button(filters, text="Add Fighter", command=self.add_fighter).pack(side="right", padx=(3, 8))
        ttk.Button(filters, text="Duplicate", command=self.duplicate_fighter).pack(side="right", padx=3)
        ttk.Button(filters, text="Delete", command=self.delete_fighter).pack(side="right", padx=3)

        metrics = ttk.Frame(self.fighters_tab, style="Panel.TFrame")
        metrics.pack(fill="x", pady=(0, 8))
        self.fighter_style_filter = tk.StringVar(value="All styles")
        self.fighter_region_filter = tk.StringVar(value="All regions")
        self.fighter_min_rating = tk.StringVar()
        self.fighter_max_rating = tk.StringVar()
        self.fighter_min_age = tk.StringVar()
        self.fighter_max_age = tk.StringVar()
        self.fighter_min_popularity = tk.StringVar()
        self.fighter_style_combo = self.build_filter_combo(metrics, "Style", self.fighter_style_filter, 18)
        self.fighter_region_combo = self.build_filter_combo(metrics, "Region", self.fighter_region_filter, 14)
        self.build_range_filter(metrics, "Rating", self.fighter_min_rating, self.fighter_max_rating, 1, 99)
        self.build_range_filter(metrics, "Age", self.fighter_min_age, self.fighter_max_age, 14, 70)
        self.build_single_number_filter(metrics, "Min pop.", self.fighter_min_popularity, 0, 100)

        bulk = ttk.Frame(self.fighters_tab, style="Inset.TFrame")
        bulk.pack(fill="x", pady=(0, 8))
        ttk.Label(bulk, text="Bulk edit filtered fighters", style="Panel.TLabel").pack(side="left", padx=(8, 8), pady=7)
        self.fighter_bulk_field = tk.StringVar()
        self.fighter_bulk_operation = tk.StringVar(value="Set")
        self.fighter_bulk_value = tk.StringVar()
        self.fighter_bulk_field_box = ttk.Combobox(bulk, textvariable=self.fighter_bulk_field, state="readonly", width=25)
        self.fighter_bulk_field_box.pack(side="left", padx=3, pady=7)
        ttk.Combobox(bulk, textvariable=self.fighter_bulk_operation, values=("Set", "Add", "Multiply", "Clear"), state="readonly", width=10).pack(side="left", padx=3, pady=7)
        ttk.Entry(bulk, textvariable=self.fighter_bulk_value, width=25).pack(side="left", padx=3, pady=7)
        ttk.Button(bulk, text="Apply", style="Accent.TButton", command=lambda: self.apply_bulk("fighter")).pack(side="left", padx=5, pady=7)

        pane = ttk.Panedwindow(self.fighters_tab, orient="horizontal")
        pane.pack(fill="both", expand=True)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=4)
        pane.add(right, weight=5)
        columns = ("name", "owner", "weight", "gender", "rating", "potential", "popularity", "age", "style", "region")
        self.fighter_tree = self.build_tree(left, columns, ("Fighter", "Company", "Weight", "Gender", "Rating", "Potential", "Pop.", "Age", "Style", "Region"), (210, 185, 115, 70, 65, 72, 58, 55, 125, 100), "fighter")
        self.fighter_tree.bind("<<TreeviewSelect>>", lambda _event: self.select_fighter())
        self.build_record_editor(right, "fighter")

    def build_companies_tab(self):
        filters = ttk.Frame(self.companies_tab, style="Panel.TFrame")
        filters.pack(fill="x", pady=(0, 8))
        self.company_search = tk.StringVar()
        ttk.Label(filters, text="Search", style="Panel.TLabel").pack(side="left", padx=(8, 3), pady=7)
        company_search = ttk.Entry(filters, textvariable=self.company_search, width=32)
        company_search.pack(side="left", padx=(0, 4), pady=7)
        company_search.bind("<KeyRelease>", lambda _event: self.refresh_companies())
        self.company_region_filter = tk.StringVar(value="All regions")
        self.company_reputation_filter = tk.StringVar(value="All reputations")
        self.company_kind_filter = tk.StringVar(value="All types")
        self.company_region_combo = self.build_filter_combo(filters, "Region", self.company_region_filter, 14)
        self.company_reputation_combo = self.build_filter_combo(filters, "Reputation", self.company_reputation_filter, 16)
        self.company_kind_combo = self.build_filter_combo(filters, "Type", self.company_kind_filter, 11)
        ttk.Button(filters, text="Clear", command=self.clear_company_filters).pack(side="left", padx=4)
        ttk.Button(filters, text="Add Company", command=self.add_company).pack(side="right", padx=(3, 8))
        ttk.Button(filters, text="Duplicate", command=self.duplicate_company).pack(side="right", padx=3)
        ttk.Button(filters, text="Delete", command=self.delete_company).pack(side="right", padx=3)

        metrics = ttk.Frame(self.companies_tab, style="Panel.TFrame")
        metrics.pack(fill="x", pady=(0, 8))
        self.company_min_cash = tk.StringVar()
        self.company_max_cash = tk.StringVar()
        self.company_min_size = tk.StringVar()
        self.company_max_size = tk.StringVar()
        self.company_min_stability = tk.StringVar()
        self.build_range_filter(metrics, "Cash", self.company_min_cash, self.company_max_cash, 0, 100000000, 1000)
        self.build_range_filter(metrics, "Size", self.company_min_size, self.company_max_size, 0, 10000)
        self.build_single_number_filter(metrics, "Min stability", self.company_min_stability, 0, 10000)

        bulk = ttk.Frame(self.companies_tab, style="Inset.TFrame")
        bulk.pack(fill="x", pady=(0, 8))
        ttk.Label(bulk, text="Bulk edit filtered companies", style="Panel.TLabel").pack(side="left", padx=(8, 8), pady=7)
        self.company_bulk_field = tk.StringVar()
        self.company_bulk_operation = tk.StringVar(value="Set")
        self.company_bulk_value = tk.StringVar()
        self.company_bulk_field_box = ttk.Combobox(bulk, textvariable=self.company_bulk_field, state="readonly", width=25)
        self.company_bulk_field_box.pack(side="left", padx=3, pady=7)
        ttk.Combobox(bulk, textvariable=self.company_bulk_operation, values=("Set", "Add", "Multiply", "Clear"), state="readonly", width=10).pack(side="left", padx=3, pady=7)
        ttk.Entry(bulk, textvariable=self.company_bulk_value, width=25).pack(side="left", padx=3, pady=7)
        ttk.Button(bulk, text="Apply", style="Accent.TButton", command=lambda: self.apply_bulk("company")).pack(side="left", padx=5, pady=7)

        pane = ttk.Panedwindow(self.companies_tab, orient="horizontal")
        pane.pack(fill="both", expand=True)
        left = ttk.Frame(pane)
        right = ttk.Frame(pane)
        pane.add(left, weight=4)
        pane.add(right, weight=5)
        columns = ("name", "region", "reputation", "size", "cash", "stability", "roster_key", "kind")
        self.company_tree = self.build_tree(left, columns, ("Company", "Region", "Reputation", "Size", "Cash", "Stability", "Roster Key", "Type"), (250, 105, 125, 65, 105, 75, 170, 70), "company")
        self.company_tree.bind("<<TreeviewSelect>>", lambda _event: self.select_company())
        self.build_record_editor(right, "company")

    def build_filter_combo(self, parent, label, variable, width):
        ttk.Label(parent, text=label, style="Panel.TLabel").pack(side="left", padx=(8, 3), pady=7)
        combo = ttk.Combobox(parent, textvariable=variable, state="readonly", width=width)
        combo.pack(side="left", padx=(0, 4), pady=7)
        combo.bind("<<ComboboxSelected>>", lambda _event: self.refresh_all())
        return combo

    def build_range_filter(self, parent, label, minimum_var, maximum_var, lower, upper, increment=1):
        ttk.Label(parent, text=label, style="Panel.TLabel").pack(side="left", padx=(8, 3), pady=7)
        minimum = ttk.Spinbox(parent, textvariable=minimum_var, from_=lower, to=upper, increment=increment, width=7)
        minimum.pack(side="left", pady=7)
        ttk.Label(parent, text="to", style="Panel.TLabel").pack(side="left", padx=3, pady=7)
        maximum = ttk.Spinbox(parent, textvariable=maximum_var, from_=lower, to=upper, increment=increment, width=7)
        maximum.pack(side="left", padx=(0, 3), pady=7)
        for widget in (minimum, maximum):
            widget.bind("<KeyRelease>", lambda _event: self.refresh_all())
            widget.bind("<FocusOut>", lambda _event: self.refresh_all())

    def build_single_number_filter(self, parent, label, variable, lower, upper, increment=1):
        ttk.Label(parent, text=label, style="Panel.TLabel").pack(side="left", padx=(8, 3), pady=7)
        control = ttk.Spinbox(parent, textvariable=variable, from_=lower, to=upper, increment=increment, width=7)
        control.pack(side="left", padx=(0, 3), pady=7)
        control.bind("<KeyRelease>", lambda _event: self.refresh_all())
        control.bind("<FocusOut>", lambda _event: self.refresh_all())

    def build_tree(self, parent, columns, headings, widths, table_kind=None):
        frame = ttk.Frame(parent, style="Inset.TFrame")
        frame.pack(fill="both", expand=True)
        tree = ttk.Treeview(frame, columns=columns, show="headings", selectmode="browse")
        for column, heading, width in zip(columns, headings, widths):
            heading_options = {"text": heading}
            if table_kind:
                heading_options["command"] = lambda selected=column, kind=table_kind: self.toggle_table_sort(kind, selected)
            tree.heading(column, **heading_options)
            tree.column(column, width=width, minwidth=50, stretch=column in ("name", "owner", "roster_key"))
        vertical = ttk.Scrollbar(frame, orient="vertical", command=tree.yview)
        horizontal = ttk.Scrollbar(frame, orient="horizontal", command=tree.xview)
        tree.configure(yscrollcommand=vertical.set, xscrollcommand=horizontal.set)
        tree.grid(row=0, column=0, sticky="nsew")
        vertical.grid(row=0, column=1, sticky="ns")
        horizontal.grid(row=1, column=0, sticky="ew")
        frame.rowconfigure(0, weight=1)
        frame.columnconfigure(0, weight=1)
        if table_kind:
            self.table_specs[table_kind] = (tree, columns, headings)
            self.update_table_sort_headings(table_kind)
        return tree

    def build_record_editor(self, parent, kind):
        notebook = ttk.Notebook(parent)
        notebook.pack(fill="both", expand=True)
        fields_tab = ttk.Frame(notebook)
        raw_tab = ttk.Frame(notebook)
        notebook.add(fields_tab, text="All Fields")
        notebook.add(raw_tab, text="Record JSON")
        columns = ("field", "value", "source")
        tree = self.build_tree(fields_tab, columns, ("Field", "Value", "Source"), (195, 390, 80))
        tree.bind("<<TreeviewSelect>>", lambda _event, item_kind=kind: self.select_field(item_kind))
        editor = ttk.Frame(fields_tab, style="Panel.TFrame")
        editor.pack(fill="x", pady=(7, 0))
        field_var = tk.StringVar()
        choice_var = tk.StringVar()
        number_var = tk.StringVar()
        value = tk.Text(editor, height=3, wrap="word", bg=self.colors["inset"], fg=self.colors["text"], insertbackground=self.colors["text"], relief="flat")
        ttk.Label(editor, text="Field", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(8, 4), pady=(6, 2))
        field_box = ttk.Combobox(editor, textvariable=field_var, state="readonly", width=25)
        field_box.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=(6, 2))
        field_box.bind("<<ComboboxSelected>>", lambda _event, item_kind=kind: self.field_choice_changed(item_kind))
        ttk.Label(editor, text="Value", style="Panel.TLabel").grid(row=1, column=0, sticky="nw", padx=(8, 4), pady=4)
        value.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)
        choice_box = ttk.Combobox(editor, textvariable=choice_var, state="readonly")
        number_box = ttk.Spinbox(editor, textvariable=number_var, width=18)
        ttk.Button(editor, text="Apply Field", style="Accent.TButton", command=lambda item_kind=kind: self.apply_field(item_kind)).grid(row=2, column=1, sticky="w", padx=(0, 6), pady=(0, 7))
        ttk.Button(editor, text="Remove Field", command=lambda item_kind=kind: self.remove_field(item_kind)).grid(row=2, column=1, sticky="e", padx=(0, 6), pady=(0, 7))
        editor.columnconfigure(1, weight=1)
        raw = tk.Text(raw_tab, wrap="none", font=("Consolas", 9), bg=self.colors["inset"], fg=self.colors["text"], insertbackground=self.colors["text"])
        raw_scroll = ttk.Scrollbar(raw_tab, orient="vertical", command=raw.yview)
        raw.configure(yscrollcommand=raw_scroll.set)
        raw.pack(side="left", fill="both", expand=True)
        raw_scroll.pack(side="right", fill="y")
        actions = ttk.Frame(raw_tab, style="Panel.TFrame")
        actions.pack(fill="x", side="bottom")
        ttk.Button(actions, text="Apply Record JSON", style="Accent.TButton", command=lambda item_kind=kind: self.apply_raw_record(item_kind)).pack(side="left", padx=7, pady=6)
        if kind == "fighter":
            self.fighter_field_tree, self.fighter_field_var, self.fighter_value_text, self.fighter_value_choice, self.fighter_value_combo, self.fighter_value_number, self.fighter_value_spinbox, self.fighter_field_box, self.fighter_raw_text = tree, field_var, value, choice_var, choice_box, number_var, number_box, field_box, raw
        else:
            self.company_field_tree, self.company_field_var, self.company_value_text, self.company_value_choice, self.company_value_combo, self.company_value_number, self.company_value_spinbox, self.company_field_box, self.company_raw_text = tree, field_var, value, choice_var, choice_box, number_var, number_box, field_box, raw

    def build_fighter_defaults(self):
        example = Fighter("", "Lightweight", 28, 0, 0, 65, 65, 65, 65, 65, 20, 0, 70, 8000)
        defaults = asdict(example)
        defaults.update(FIGHTER_AUTHOR_FIELDS)
        return defaults

    def build_company_defaults(self):
        example = Promotion("", "USA", 50, 250000, [])
        defaults = asdict(example)
        defaults.update(COMPANY_AUTHOR_FIELDS)
        return defaults

    def current_sections(self):
        return self.pack.setdefault("sections", {}) if isinstance(self.pack, dict) else {}

    def fighter_records(self):
        section = self.current_sections().setdefault("fighters", {})
        return section.setdefault("all_fighters", [])

    def company_records(self):
        section = self.current_sections().setdefault("companies", {})
        section.setdefault("player_company", {"name": PLAYER_PROMOTION_NAME, "region": "UK", "reputation": "Regional Player Company", "popularity": 38, "stability": 52, "cash": 275000})
        return section.setdefault("promotions", [])

    def regional_company_records(self):
        return self.current_sections().setdefault("companies", {}).setdefault("regional_feeders", [])

    def database_paths(self):
        return sorted(self.database_dir.glob("*.universe.json"), key=lambda path: path.name.casefold())

    def refresh_database_selector(self, select_name=None):
        paths = self.database_paths()
        self.database_choice_paths = {path.name: path for path in paths}
        if self.path and self.path.resolve() not in {path.resolve() for path in paths}:
            self.database_choice_paths[f"{self.path.name} (external)"] = self.path
        labels = list(self.database_choice_paths)
        self.database_selector["values"] = labels
        target = select_name or (self.path.name if self.path else "")
        matching = next((label for label, path in self.database_choice_paths.items() if label == target or path.name == target), "")
        if matching:
            self.database_choice.set(matching)
        elif paths:
            self.database_choice.set(paths[0].name)
        else:
            self.database_choice.set("")

    def load_selected_database(self):
        selected = self.database_choice.get().strip()
        if selected:
            self.load_database(getattr(self, "database_choice_paths", {}).get(selected, self.database_dir / selected))

    def load_database(self, path):
        path = Path(path)
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            issues = validate_universe_pack(data)
            if not isinstance(data, dict) or data.get("type") != "universe_database":
                raise ValueError("not a universe database pack")
        except Exception as exc:
            messagebox.showerror("Could not load database", f"{path}\n\n{type(exc).__name__}: {exc}")
            return
        self.path = path
        self.pack = data
        self.refresh_database_selector(select_name=path.name)
        self.refresh_all()
        self.status_var.set(f"Loaded {path.name}. {len(issues)} validation issue(s).")

    def browse_database(self):
        path = filedialog.askopenfilename(title="Open universe database", initialdir=self.database_dir, filetypes=(("Universe databases", "*.universe.json"), ("JSON files", "*.json")))
        if path:
            self.load_database(path)

    def copy_current_database(self):
        if not self.ensure_database_loaded():
            return
        default_name = f"{self.path.stem} Copy.universe.json"
        target = filedialog.asksaveasfilename(title="Copy current universe database", initialdir=self.database_dir, initialfile=default_name, defaultextension=".universe.json", filetypes=(("Universe databases", "*.universe.json"),))
        if not target:
            return
        target_path = Path(target)
        if target_path.exists() and not messagebox.askyesno("Replace database", f"Replace existing copy?\n\n{target_path.name}"):
            return
        try:
            shutil.copy2(self.path, target_path)
        except OSError as exc:
            messagebox.showerror("Copy failed", f"{type(exc).__name__}: {exc}")
            return
        self.load_database(target_path)
        self.status_var.set(f"Created editable copy: {target_path.name}")

    def save_database_as(self):
        if not self.ensure_database_loaded():
            return
        target = filedialog.asksaveasfilename(title="Save universe database as", initialdir=self.database_dir, initialfile=self.path.name, defaultextension=".universe.json", filetypes=(("Universe databases", "*.universe.json"),))
        if not target:
            return
        self.path = Path(target)
        self.save_database()
        self.refresh_database_selector(select_name=self.path.name)

    def save_database(self):
        if not self.ensure_database_loaded():
            return
        if self.path.name == DEFAULT_UNIVERSE_NAME and not messagebox.askyesno("Edit shipped default", "This is the shipped base universe. Copy it first if you want a separate custom database.\n\nSave changes to the base file anyway?"):
            self.copy_current_database()
            return
        self.sync_for_save()
        issues = validate_universe_pack(self.pack)
        if issues:
            messagebox.showwarning("Database not saved", "Fix the validation issues before saving:\n\n" + "\n".join(issues[:24]))
            return
        if self.path.exists():
            backup = self.path.with_suffix(f".backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
            try:
                shutil.copy2(self.path, backup)
            except OSError as exc:
                messagebox.showerror("Backup failed", f"The database was not saved.\n\n{type(exc).__name__}: {exc}")
                return
        try:
            atomic_write_json(self.path, self.pack)
        except OSError as exc:
            messagebox.showerror("Save failed", f"{type(exc).__name__}: {exc}")
            return
        self.status_var.set(f"Saved {self.path.name}. A timestamped backup was created.")
        self.refresh_all()

    def sync_for_save(self):
        sections = self.current_sections()
        fighters = sections.setdefault("fighters", {})
        sync_fighter_groups(fighters)
        self.pack["last_edited_at"] = datetime.now().isoformat(timespec="seconds")
        self.pack["last_edited_by"] = "MMA Warriors Database Editor"

    def validate_database(self):
        if not self.ensure_database_loaded():
            return
        self.sync_for_save()
        issues = validate_universe_pack(self.pack)
        if issues:
            messagebox.showwarning("Validation issues", "\n".join(issues[:60]))
        else:
            messagebox.showinfo("Database valid", f"{self.path.name} is valid and ready for a new game.")
        self.status_var.set(f"Validation complete: {len(issues)} issue(s).")

    def open_database_folder(self):
        try:
            os.startfile(self.database_dir)
        except OSError:
            messagebox.showinfo("Database folder", str(self.database_dir))

    def ensure_database_loaded(self):
        if self.pack is None or self.path is None:
            messagebox.showinfo("No database selected", "Choose a universe database first.")
            return False
        return True

    def fighter_field_names(self):
        names = set(self.fighter_defaults)
        for record in self.fighter_records():
            if isinstance(record, dict):
                names.update(record)
        priority = ["name", "placement", "owner", "seed_org", "weight", "gender", "rating", "age", "record_w", "record_l", "record_d", "region", "nationality", "style", "profile_rating", "potential"]
        return priority + sorted(names - set(priority))

    def company_field_names(self):
        names = set(self.company_defaults)
        player = self.current_sections().get("companies", {}).get("player_company", {})
        if isinstance(player, dict):
            names.update(player)
        for record in self.company_records():
            if isinstance(record, dict):
                names.update(record)
        for record in self.regional_company_records():
            if isinstance(record, dict):
                names.update(record)
        priority = ["name", "region", "size", "cash", "roster_key", "target_roster_size", "reputation", "reputation_score", "stability", "show_personality", "is_regional_feeder"]
        return priority + sorted(names - set(priority))

    def filtered_fighters(self):
        search = self.fighter_search.get().strip().casefold()
        owner = self.fighter_owner_filter.get()
        weight = self.fighter_weight_filter.get()
        gender = self.fighter_gender_filter.get()
        style = self.fighter_style_filter.get()
        region = self.fighter_region_filter.get()
        min_rating, max_rating = self.range_filter_values(self.fighter_min_rating, self.fighter_max_rating)
        min_age, max_age = self.range_filter_values(self.fighter_min_age, self.fighter_max_age)
        min_popularity = self.number_filter_value(self.fighter_min_popularity)
        rows = []
        for index, record in enumerate(self.fighter_records()):
            if not isinstance(record, dict):
                continue
            haystack = " ".join(str(record.get(key, "")) for key in ("name", "owner", "region", "nationality", "style")).casefold()
            if search and search not in haystack:
                continue
            if owner != "All companies" and record.get("owner") != owner:
                continue
            if weight != "All weights" and record.get("weight") != weight:
                continue
            if gender != "All genders" and record.get("gender") != gender:
                continue
            if style != "All styles" and record.get("style") != style:
                continue
            if region != "All regions" and record.get("region") != region:
                continue
            if not self.matches_number_range(record.get("rating"), min_rating, max_rating):
                continue
            if not self.matches_number_range(record.get("age"), min_age, max_age):
                continue
            if min_popularity is not None and not self.matches_number_range(record.get("popularity", record.get("pop")), min_popularity, None):
                continue
            rows.append((index, record))
        return rows

    def filtered_companies(self):
        search = self.company_search.get().strip().casefold()
        region = self.company_region_filter.get()
        reputation = self.company_reputation_filter.get()
        company_kind = self.company_kind_filter.get()
        min_cash, max_cash = self.range_filter_values(self.company_min_cash, self.company_max_cash)
        min_size, max_size = self.range_filter_values(self.company_min_size, self.company_max_size)
        min_stability = self.number_filter_value(self.company_min_stability)
        rows = []
        player = self.current_sections().get("companies", {}).get("player_company", {})
        if isinstance(player, dict):
            rows.append(("player", player))
        for index, record in enumerate(self.company_records()):
            if isinstance(record, dict):
                rows.append((index, record))
        for index, record in enumerate(self.regional_company_records()):
            if isinstance(record, dict):
                rows.append((f"regional:{index}", record))
        filtered = []
        for key, record in rows:
            haystack = " ".join(str(record.get(field, "")) for field in ("name", "region", "reputation", "roster_key")).casefold()
            if search and search not in haystack:
                continue
            if region != "All regions" and record.get("region") != region:
                continue
            if reputation != "All reputations" and record.get("reputation") != reputation:
                continue
            if company_kind != "All types" and self.company_kind_for_key(key) != company_kind:
                continue
            if not self.matches_number_range(record.get("cash"), min_cash, max_cash):
                continue
            if not self.matches_number_range(record.get("size"), min_size, max_size):
                continue
            if min_stability is not None and not self.matches_number_range(record.get("stability"), min_stability, None):
                continue
            filtered.append((key, record))
        return filtered

    @staticmethod
    def number_filter_value(variable):
        try:
            value = variable.get().strip()
            return float(value) if value else None
        except (tk.TclError, TypeError, ValueError):
            return None

    def range_filter_values(self, minimum_var, maximum_var):
        return self.number_filter_value(minimum_var), self.number_filter_value(maximum_var)

    @staticmethod
    def matches_number_range(value, minimum, maximum):
        if minimum is None and maximum is None:
            return True
        try:
            number = float(value)
        except (TypeError, ValueError):
            return False
        return (minimum is None or number >= minimum) and (maximum is None or number <= maximum)

    @staticmethod
    def company_kind_for_key(key):
        return "Player" if key == "player" else "Regional" if str(key).startswith("regional:") else "AI"

    def sort_rows(self, table_kind, rows):
        column, descending = self.table_sort[table_kind]
        numeric_columns = {
            "fighter": {"rating", "potential", "popularity", "age"},
            "company": {"size", "cash", "stability"},
        }
        populated, missing = [], []
        for key, record in rows:
            value = self.company_kind_for_key(key) if table_kind == "company" and column == "kind" else record.get(column)
            if value in (None, ""):
                missing.append((key, record))
                continue
            if column in numeric_columns[table_kind]:
                try:
                    sort_value = float(value)
                except (TypeError, ValueError):
                    missing.append((key, record))
                    continue
            else:
                sort_value = str(value).casefold()
            populated.append((sort_value, key, record))
        populated.sort(key=lambda row: row[0], reverse=descending)
        return [(key, record) for _value, key, record in populated] + missing

    def toggle_table_sort(self, table_kind, column):
        current_column, descending = self.table_sort[table_kind]
        self.table_sort[table_kind] = (column, not descending if current_column == column else False)
        self.update_table_sort_headings(table_kind)
        if table_kind == "fighter":
            self.refresh_fighters()
        else:
            self.refresh_companies()

    def update_table_sort_headings(self, table_kind):
        tree, columns, headings = self.table_specs.get(table_kind, (None, (), ()))
        if tree is None:
            return
        sorted_column, descending = self.table_sort[table_kind]
        for column, heading in zip(columns, headings):
            marker = " v" if column == sorted_column and descending else " ^" if column == sorted_column else ""
            tree.heading(column, text=heading + marker, command=lambda selected=column, kind=table_kind: self.toggle_table_sort(kind, selected))

    def refresh_all(self):
        self.refresh_fighters()
        self.refresh_companies()

    def refresh_fighters(self):
        if not self.ensure_database_loaded():
            return
        owners = sorted({str(record.get("owner", "Free Agent")) for record in self.fighter_records() if isinstance(record, dict)})
        styles = sorted({str(record.get("style")) for record in self.fighter_records() if record.get("style")})
        regions = sorted({str(record.get("region")) for record in self.fighter_records() if record.get("region")})
        self.refresh_filter_choice(self.fighter_owner_filter, self.fighter_owner_combo, owners, "All companies")
        self.refresh_filter_choice(self.fighter_weight_filter, self.fighter_weight_combo, WEIGHTS, "All weights")
        self.refresh_filter_choice(self.fighter_gender_filter, self.fighter_gender_combo, ("Male", "Female"), "All genders")
        self.refresh_filter_choice(self.fighter_style_filter, self.fighter_style_combo, styles, "All styles")
        self.refresh_filter_choice(self.fighter_region_filter, self.fighter_region_combo, regions, "All regions")
        for item in self.fighter_tree.get_children():
            self.fighter_tree.delete(item)
        for index, record in self.sort_rows("fighter", self.filtered_fighters()):
            self.fighter_tree.insert("", "end", iid=str(index), values=(record.get("name", ""), record.get("owner", ""), record.get("weight", ""), record.get("gender", ""), record.get("rating", ""), record.get("potential", ""), record.get("popularity", record.get("pop", "")), record.get("age", ""), record.get("style", ""), record.get("region", "")))
        values = self.fighter_field_names()
        self.fighter_bulk_field_box["values"] = values
        if not self.fighter_bulk_field.get() and values:
            self.fighter_bulk_field.set("rating")
        self.refresh_fighter_editor()

    def refresh_filter_choice(self, variable, combo, values, all_label):
        current = variable.get()
        combo["values"] = (all_label, *values)
        if current not in (all_label, *values):
            variable.set(all_label)

    def clear_fighter_filters(self):
        self.fighter_search.set("")
        self.fighter_owner_filter.set("All companies")
        self.fighter_weight_filter.set("All weights")
        self.fighter_gender_filter.set("All genders")
        self.fighter_style_filter.set("All styles")
        self.fighter_region_filter.set("All regions")
        self.fighter_min_rating.set("")
        self.fighter_max_rating.set("")
        self.fighter_min_age.set("")
        self.fighter_max_age.set("")
        self.fighter_min_popularity.set("")
        self.refresh_fighters()

    def select_fighter(self):
        selection = self.fighter_tree.selection()
        self.fighter_selection = int(selection[0]) if selection else None
        self.refresh_fighter_editor()

    def selected_fighter(self):
        if self.fighter_selection is None:
            return None
        records = self.fighter_records()
        return records[self.fighter_selection] if 0 <= self.fighter_selection < len(records) else None

    def refresh_fighter_editor(self):
        self.refresh_record_editor("fighter", self.selected_fighter())

    def refresh_companies(self):
        if not self.ensure_database_loaded():
            return
        company_rows = self.filtered_companies()
        regions = sorted({str(record.get("region")) for _key, record in company_rows if record.get("region")})
        reputations = sorted({str(record.get("reputation")) for _key, record in company_rows if record.get("reputation")})
        self.refresh_filter_choice(self.company_region_filter, self.company_region_combo, regions, "All regions")
        self.refresh_filter_choice(self.company_reputation_filter, self.company_reputation_combo, reputations, "All reputations")
        self.refresh_filter_choice(self.company_kind_filter, self.company_kind_combo, ("Player", "AI", "Regional"), "All types")
        for item in self.company_tree.get_children():
            self.company_tree.delete(item)
        for key, record in self.sort_rows("company", self.filtered_companies()):
            kind = self.company_kind_for_key(key)
            self.company_tree.insert("", "end", iid=str(key), values=(record.get("name", ""), record.get("region", ""), record.get("reputation", ""), record.get("size", ""), record.get("cash", ""), record.get("stability", ""), record.get("roster_key", ""), kind))
        values = self.company_field_names()
        self.company_bulk_field_box["values"] = values
        if not self.company_bulk_field.get() and values:
            self.company_bulk_field.set("cash")
        self.refresh_company_editor()

    def clear_company_filters(self):
        self.company_search.set("")
        self.company_region_filter.set("All regions")
        self.company_reputation_filter.set("All reputations")
        self.company_kind_filter.set("All types")
        self.company_min_cash.set("")
        self.company_max_cash.set("")
        self.company_min_size.set("")
        self.company_max_size.set("")
        self.company_min_stability.set("")
        self.refresh_companies()

    def select_company(self):
        selection = self.company_tree.selection()
        self.company_selection = selection[0] if selection else None
        self.refresh_company_editor()

    def selected_company(self):
        if self.company_selection is None:
            return None
        if self.company_selection == "player":
            return self.current_sections().get("companies", {}).get("player_company")
        if str(self.company_selection).startswith("regional:"):
            try:
                return self.regional_company_records()[int(str(self.company_selection).split(":", 1)[1])]
            except (IndexError, TypeError, ValueError):
                return None
        try:
            return self.company_records()[int(self.company_selection)]
        except (IndexError, TypeError, ValueError):
            return None

    def refresh_company_editor(self):
        self.refresh_record_editor("company", self.selected_company())

    def refresh_record_editor(self, kind, record):
        if kind == "fighter":
            tree, raw = self.fighter_field_tree, self.fighter_raw_text
            fields, defaults = self.fighter_field_names(), self.fighter_defaults
        else:
            tree, raw = self.company_field_tree, self.company_raw_text
            fields, defaults = self.company_field_names(), self.company_defaults
        for item in tree.get_children():
            tree.delete(item)
        raw.delete("1.0", "end")
        if not isinstance(record, dict):
            return
        for field in fields:
            authored = field in record
            value = record[field] if authored else defaults.get(field, "")
            source = "Authored" if authored else "Default"
            tree.insert("", "end", iid=field, values=(field, compact_json(value), source))
        field_box = self.fighter_field_box if kind == "fighter" else self.company_field_box
        field_box["values"] = fields
        raw.insert("1.0", json.dumps(record, indent=2, ensure_ascii=True))

    def select_field(self, kind):
        if kind == "fighter":
            tree, field_var, value_text = self.fighter_field_tree, self.fighter_field_var, self.fighter_value_text
        else:
            tree, field_var, value_text = self.company_field_tree, self.company_field_var, self.company_value_text
        selection = tree.selection()
        if not selection:
            return
        field = selection[0]
        field_var.set(field)
        item = tree.item(field)
        self.configure_value_control(kind, field, item["values"][1])

    def field_choice_changed(self, kind):
        field = self.fighter_field_var.get() if kind == "fighter" else self.company_field_var.get()
        record = self.record_for_kind(kind)
        if not isinstance(record, dict) or not field:
            return
        value = record.get(field, self.fighter_defaults.get(field, "") if kind == "fighter" else self.company_defaults.get(field, ""))
        self.configure_value_control(kind, field, compact_json(value))

    def value_choices_for(self, kind, field):
        values = dict(FIGHTER_VALUE_CHOICES if kind == "fighter" else COMPANY_VALUE_CHOICES).get(field)
        if values is not None:
            if field == "nationality":
                return tuple(sorted({str(record.get("nationality", "")) for record in self.fighter_records() if record.get("nationality")}, key=str.casefold))
            return values
        if kind == "fighter" and field in ("owner", "seed_org"):
            companies = [PLAYER_PROMOTION_NAME, "Free Agent", "Legend"]
            companies.extend(str(record.get("name")) for _key, record in self.filtered_companies() if record.get("name"))
            return tuple(dict.fromkeys(companies))
        if kind == "company" and field == "roster_key":
            return tuple(dict.fromkeys(str(record.get("owner")) for record in self.fighter_records() if record.get("owner")))
        record = self.record_for_kind(kind)
        if isinstance(record, dict) and isinstance(record.get(field), bool):
            return BOOLEAN_VALUES
        defaults = self.fighter_defaults if kind == "fighter" else self.company_defaults
        if isinstance(defaults.get(field), bool):
            return BOOLEAN_VALUES
        return ()

    def configure_value_control(self, kind, field, rendered_value):
        if kind == "fighter":
            value_text, choice_var, choice_box, number_var, number_box = self.fighter_value_text, self.fighter_value_choice, self.fighter_value_combo, self.fighter_value_number, self.fighter_value_spinbox
        else:
            value_text, choice_var, choice_box, number_var, number_box = self.company_value_text, self.company_value_choice, self.company_value_combo, self.company_value_number, self.company_value_spinbox
        choices = self.value_choices_for(kind, field)
        numeric = self.numeric_spec_for(kind, field, rendered_value)
        if choices:
            value_text.grid_remove()
            number_box.grid_remove()
            choice_box["values"] = choices
            raw_value = json_value(rendered_value)
            selected = str(raw_value).lower() if isinstance(raw_value, bool) else str(raw_value)
            choice_var.set(selected if selected in choices else "")
            choice_box.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)
        elif numeric:
            value_text.grid_remove()
            choice_box.grid_remove()
            lower, upper, increment = numeric
            number_box.configure(from_=lower, to=upper, increment=increment)
            number_var.set(str(json_value(rendered_value)))
            number_box.grid(row=1, column=1, sticky="w", padx=(0, 6), pady=4)
        else:
            choice_box.grid_remove()
            number_box.grid_remove()
            value_text.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)
            value_text.delete("1.0", "end")
            value_text.insert("1.0", rendered_value)

    def numeric_spec_for(self, kind, field, rendered_value):
        defaults = self.fighter_defaults if kind == "fighter" else self.company_defaults
        parsed = json_value(rendered_value)
        numeric = isinstance(parsed, (int, float)) and not isinstance(parsed, bool)
        numeric = numeric or isinstance(defaults.get(field), (int, float)) and not isinstance(defaults.get(field), bool)
        numeric = numeric or kind == "fighter" and field in FIGHTER_NUMERIC_AUTHOR_FIELDS
        if not numeric:
            return None
        skill_fields = {
            "rating", "profile_rating", "potential", "striking", "wrestling", "grappling", "cardio", "chin",
            "power", "takedown_defence", "ground_control", "submissions", "submission_defence", "recovery",
            "toughness", "fight_iq", "star_quality", "charisma", "professionalism", "injury_proneness",
            "finishing_instinct", "media_presence", "sponsor_appeal", "motivation", "morale", "fatigue",
            "camp_quality", "camp_boost", "relationship_trust", "rivalry_heat",
        }
        if field in skill_fields:
            return 1, 99, 1
        if field in ("age", "prime_age", "prime_start", "prime_end"):
            return 14, 70, 1
        if field.startswith(("record_", "amateur_", "career_", "title_", "award_", "regional_", "rank_", "available_", "last_fight_", "universe_entry_", "contract_", "guaranteed_", "free_agent_", "showcase_", "ai_offer_", "promise_", "retirement_", "camp_weeks", "weight_cut_", "division_size_")):
            lower = -99 if field in ("showcase_last_month", "weight_move_last_month") else 0
            return lower, 10000, 1
        if field in ("cash", "purse", "win_bonus", "ppv_points", "ai_offer_purse", "ai_offer_signing_bonus"):
            upper = max(10000000, int(parsed or 0) * 2)
            return 0, upper, 1000
        if field in ("size", "target_roster_size", "event_counter", "legacy_score", "reputation_score", "stability"):
            return 0, 10000, 1
        if isinstance(parsed, float) or isinstance(defaults.get(field), float):
            return -100000.0, max(100000.0, abs(float(parsed or 0)) * 2), 0.1
        return -1000000, max(1000000, abs(int(parsed or 0)) * 2), 1

    def record_for_kind(self, kind):
        return self.selected_fighter() if kind == "fighter" else self.selected_company()

    def apply_field(self, kind):
        record = self.record_for_kind(kind)
        if not isinstance(record, dict):
            messagebox.showinfo("No record selected", "Select a record first.")
            return
        if kind == "fighter":
            field, value_text = self.fighter_field_var.get().strip(), self.fighter_value_text
            selected_value = self.fighter_value_choice.get() if self.value_choices_for(kind, field) else self.fighter_value_number.get() if self.numeric_spec_for(kind, field, compact_json(self.selected_fighter().get(field, self.fighter_defaults.get(field, "")))) else value_text.get("1.0", "end")
        else:
            field, value_text = self.company_field_var.get().strip(), self.company_value_text
            selected_value = self.company_value_choice.get() if self.value_choices_for(kind, field) else self.company_value_number.get() if self.numeric_spec_for(kind, field, compact_json(self.selected_company().get(field, self.company_defaults.get(field, "")))) else value_text.get("1.0", "end")
        if not field:
            return
        numeric = self.numeric_spec_for(kind, field, compact_json(record.get(field, self.fighter_defaults.get(field, "") if kind == "fighter" else self.company_defaults.get(field, ""))))
        value = json_value(selected_value)
        if numeric:
            lower, upper, increment = numeric
            if isinstance(value, bool) or not isinstance(value, (int, float)):
                messagebox.showerror("Invalid number", f"{field} must be a number between {lower:g} and {upper:g}.")
                return
            if not lower <= value <= upper:
                messagebox.showerror("Number out of range", f"{field} must be between {lower:g} and {upper:g}.")
                return
            if increment == 1 and isinstance(value, float) and not value.is_integer():
                messagebox.showerror("Whole number required", f"{field} uses whole numbers.")
                return
            value = int(value) if increment == 1 else float(value)
        old_name = record.get("name")
        record[field] = value
        if kind == "company" and field == "name" and old_name and old_name != record["name"]:
            self.rename_company_references(old_name, record["name"])
        self.refresh_all()

    def remove_field(self, kind):
        record = self.record_for_kind(kind)
        field = self.fighter_field_var.get().strip() if kind == "fighter" else self.company_field_var.get().strip()
        if not isinstance(record, dict) or not field:
            return
        if field in FIGHTER_REQUIRED_FIELDS if kind == "fighter" else field in COMPANY_REQUIRED_FIELDS:
            messagebox.showwarning("Required field", f"{field} is required and cannot be removed.")
            return
        record.pop(field, None)
        self.refresh_all()

    def apply_raw_record(self, kind):
        record = self.record_for_kind(kind)
        raw = self.fighter_raw_text if kind == "fighter" else self.company_raw_text
        if not isinstance(record, dict):
            messagebox.showinfo("No record selected", "Select a record first.")
            return
        try:
            edited = json.loads(raw.get("1.0", "end").strip() or "{}")
            if not isinstance(edited, dict):
                raise ValueError("record JSON must be an object")
        except Exception as exc:
            messagebox.showerror("Invalid JSON", f"{type(exc).__name__}: {exc}")
            return
        old_name = record.get("name")
        record.clear()
        record.update(edited)
        if kind == "company" and old_name and old_name != record.get("name"):
            self.rename_company_references(old_name, record.get("name", ""))
        self.refresh_all()

    def apply_bulk(self, kind):
        if kind == "fighter":
            rows, field, operation, raw_value = self.filtered_fighters(), self.fighter_bulk_field.get().strip(), self.fighter_bulk_operation.get(), self.fighter_bulk_value.get()
        else:
            rows, field, operation, raw_value = self.filtered_companies(), self.company_bulk_field.get().strip(), self.company_bulk_operation.get(), self.company_bulk_value.get()
        if not rows or not field:
            messagebox.showinfo("Nothing to edit", "Choose a field and leave at least one record in the current filter.")
            return
        value = json_value(raw_value)
        if not messagebox.askyesno("Apply bulk edit", f"{operation} {field} on {len(rows)} filtered {kind}s?"):
            return
        for _key, record in rows:
            if operation == "Clear":
                record.pop(field, None)
            elif operation == "Set":
                record[field] = deepcopy(value)
            else:
                try:
                    current = record.get(field, 0)
                    record[field] = current + value if operation == "Add" else current * value
                except TypeError:
                    messagebox.showerror("Bulk edit failed", f"{field} must be numeric for {operation}.")
                    return
        self.status_var.set(f"Bulk edit applied to {len(rows)} {kind} record(s).")
        self.refresh_all()

    def add_fighter(self):
        if not self.ensure_database_loaded():
            return
        name = simpledialog.askstring("Add fighter", "Fighter name:", parent=self.root)
        if not name:
            return
        record = {
            "database_type": "mma", "generated": False, "placement": "free_agents", "owner": "Free Agent", "seed_org": "Free Agent",
            "name": name.strip(), "weight": "Lightweight", "gender": "Male", "popularity": 20, "rating": 65, "age": 25,
            "record_w": 0, "record_l": 0, "record_d": 0, "region": "USA", "nationality": "American", "style": "Well-Rounded",
        }
        self.fighter_records().append(record)
        self.fighter_selection = len(self.fighter_records()) - 1
        self.refresh_fighters()

    def duplicate_fighter(self):
        record = self.selected_fighter()
        if not isinstance(record, dict):
            messagebox.showinfo("No fighter selected", "Select a fighter to duplicate.")
            return
        copied = deepcopy(record)
        copied["name"] = f"{record.get('name', 'Fighter')} Copy"
        self.fighter_records().append(copied)
        self.fighter_selection = len(self.fighter_records()) - 1
        self.refresh_fighters()

    def delete_fighter(self):
        record = self.selected_fighter()
        if not isinstance(record, dict):
            return
        if not messagebox.askyesno("Delete fighter", f"Delete {record.get('name', 'this fighter')} from this database?"):
            return
        self.fighter_records().pop(self.fighter_selection)
        self.fighter_selection = None
        self.refresh_fighters()

    def add_company(self):
        if not self.ensure_database_loaded():
            return
        name = simpledialog.askstring("Add company", "Company name:", parent=self.root)
        if not name:
            return
        record = {"name": name.strip(), "region": "USA", "size": 50, "cash": 1000000, "reputation": "National", "roster_key": name.strip(), "target_roster_size": 120, "personality": "Balanced"}
        self.company_records().append(record)
        self.company_selection = str(len(self.company_records()) - 1)
        self.refresh_companies()

    def duplicate_company(self):
        record = self.selected_company()
        if not isinstance(record, dict):
            messagebox.showinfo("No company selected", "Select a company to duplicate.")
            return
        copied = deepcopy(record)
        copied["name"] = f"{record.get('name', 'Company')} Copy"
        copied["roster_key"] = copied["name"]
        if str(self.company_selection).startswith("regional:"):
            self.regional_company_records().append(copied)
            self.company_selection = f"regional:{len(self.regional_company_records()) - 1}"
        else:
            self.company_records().append(copied)
            self.company_selection = str(len(self.company_records()) - 1)
        self.refresh_companies()

    def delete_company(self):
        if self.company_selection == "player":
            messagebox.showwarning("Player company", "The player company cannot be deleted from a universe pack.")
            return
        record = self.selected_company()
        if not isinstance(record, dict):
            return
        if not messagebox.askyesno("Delete company", f"Delete {record.get('name', 'this company')}? Fighters stay in the database and should be reassigned with a bulk owner edit."):
            return
        if str(self.company_selection).startswith("regional:"):
            self.regional_company_records().pop(int(str(self.company_selection).split(":", 1)[1]))
        else:
            self.company_records().pop(int(self.company_selection))
        self.company_selection = None
        self.refresh_companies()

    def rename_company_references(self, old_name, new_name):
        for record in self.fighter_records():
            if record.get("owner") == old_name:
                record["owner"] = new_name
            if record.get("seed_org") == old_name:
                record["seed_org"] = new_name


def main():
    if len(sys.argv) == 3 and sys.argv[1] == "--validate":
        path = Path(sys.argv[2])
        try:
            pack = json.loads(path.read_text(encoding="utf-8"))
        except Exception as exc:
            print(f"Could not read {path}: {type(exc).__name__}: {exc}")
            return 1
        issues = validate_universe_pack(pack)
        if issues:
            print("DATABASE VALIDATION FAILED")
            print("\n".join(issues))
            return 1
        print(f"DATABASE VALID: {path.name}")
        return 0
    root = tk.Tk()
    try:
        if DATABASE_EDITOR_ICON.exists():
            root.iconbitmap(default=str(DATABASE_EDITOR_ICON))
    except tk.TclError:
        pass
    UniverseDatabaseEditor(root)
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
