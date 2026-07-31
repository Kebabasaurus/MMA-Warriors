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
    ASSET_DIR, BEHAVIOURS, CAMPS, COUNTRY_TO_REGION, DATABASE_DIR, DETAILED_SKILL_GROUPS, PLAYER_PROMOTION_NAME,
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
UNSET_CHOICE_LABEL = "Not set"
FIGHTER_NUMERIC_AUTHOR_FIELDS = {
    "rating", "profile_rating", "prime_age", "prime_start", "prime_end", "record_w", "record_l", "record_d", "popularity",
    "potential", "star_quality", "charisma", "professionalism", "injury_proneness", "finishing_instinct",
    "media_presence", "sponsor_appeal",
}

FIELD_HELP = {
    "rating": "Base database rating. Opening OVR uses Profile Rating when it is supplied.",
    "profile_rating": "Opening OVR used when a new game creates this curated fighter.",
    "potential": "Long-term ceiling for development. It is not the fighter's current ability.",
    "age": "Age at the start of a new game.",
    "prime_age": "Optional historic-age override for a legend. Leave this blank for normal fighters; their actual development window is Prime Start through Prime End.",
    "prime_start": "The age at which this fighter's normal prime development phase begins in a new game.",
    "prime_end": "The age after which normal physical decline begins. Rare veteran resurgences can still occur.",
    "weight": "Natural MMA competition division. Fighters can later move, with appropriate size penalties.",
    "owner": "Promotion that owns this fighter at the start of a new game.",
    "placement": "Starting market placement: promotion roster, player roster, or free agency.",
    "detailed_skills": "Advanced full detailed-skill data. Use Skill Ratings (1-99) for normal editing.",
    "signature_skills": "Direct individual-skill overrides. Use Skill Ratings (1-99) for normal editing.",
    "striking": "Broad striking rating. It affects the suggested OVR and the standing fight engine.",
    "wrestling": "Broad wrestling rating. It affects takedown and control exchanges.",
    "grappling": "Broad grappling rating. It affects positional and submission exchanges.",
    "cardio": "Broad endurance rating. It affects stamina, recovery between rounds, and late-fight form.",
    "chin": "Broad durability rating. It affects knockdown, stoppage, and damage resistance.",
}


class Tooltip:
    """Small hover tooltip used for editor controls that need context."""

    def __init__(self, widget, text):
        self.widget = widget
        self.text = text
        self.window = None
        widget.bind("<Enter>", self.show, add="+")
        widget.bind("<Leave>", self.hide, add="+")
        widget.bind("<ButtonPress>", self.hide, add="+")

    def show(self, _event=None):
        if self.window or not self.text:
            return
        x = self.widget.winfo_rootx() + 14
        y = self.widget.winfo_rooty() + self.widget.winfo_height() + 6
        self.window = window = tk.Toplevel(self.widget)
        window.wm_overrideredirect(True)
        window.wm_geometry(f"+{x}+{y}")
        tk.Label(window, text=self.text, justify="left", wraplength=360, bg="#102236", fg="#e6f2f2", padx=8, pady=6, relief="solid", borderwidth=1).pack()

    def hide(self, _event=None):
        if self.window is not None:
            self.window.destroy()
            self.window = None


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
        self.root.title("MMA Warriors Database Editor")
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
        style.configure("TNotebook", background=colors["bg"], borderwidth=0, tabmargins=(0, 2, 0, 0))
        style.configure(
            "TNotebook.Tab", background=colors["panel"], foreground=colors["text"],
            font=("Tahoma", 9, "bold"), padding=(12, 7), borderwidth=2,
            bordercolor=colors["line"], lightcolor=colors["line"], darkcolor=colors["bg"], relief="flat",
        )
        style.map(
            "TNotebook.Tab",
            background=[("selected", colors["accent"]), ("active", "#193956")],
            foreground=[("selected", "#062116"), ("active", "#ffffff")],
            bordercolor=[("selected", "#062116"), ("focus", "#a5f3ce"), ("active", colors["accent"])],
            lightcolor=[("selected", "#062116")], darkcolor=[("selected", "#062116")],
            relief=[("selected", "raised"), ("active", "raised")],
            expand=[("selected", (1, 1, 1, 0))],
        )

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
        profile_button = ttk.Button(toolbar, text="Lock Opening Profiles", command=self.materialize_all_opening_profiles)
        profile_button.pack(side="left", padx=3)
        Tooltip(profile_button, "Writes a complete core and detailed 1-99 skill sheet for every fighter. Future new games then use the exact database values, not seed-time rolls.")
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
        self.build_range_filter(metrics, "Opening OVR", self.fighter_min_rating, self.fighter_max_rating, 1, 99)
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
        self.fighter_tree = self.build_tree(left, columns, ("Fighter", "Company", "Weight", "Gender", "Opening OVR", "Potential", "Pop.", "Age", "Style", "Region"), (210, 185, 115, 70, 92, 72, 58, 55, 125, 100), "fighter")
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
        notebook.add(fields_tab, text="Advanced Fields")
        notebook.add(raw_tab, text="Record JSON")
        ratings_tab = None
        skills_tab = None
        if kind == "fighter":
            profile_tab = ttk.Frame(notebook)
            business_tab = ttk.Frame(notebook)
            ratings_tab = ttk.Frame(notebook)
            skills_tab = ttk.Frame(notebook)
            notebook.insert(0, profile_tab, text="Profile")
            notebook.insert(1, ratings_tab, text="Core Ratings")
            notebook.add(skills_tab, text="Skills (1-99)")
            notebook.insert(3, business_tab, text="Business & Contract")
        columns = ("field", "value", "source")
        tree = self.build_tree(fields_tab, columns, ("Field", "Value", "Source"), (195, 390, 80))
        tree.bind("<<TreeviewSelect>>", lambda _event, item_kind=kind: self.select_field(item_kind))
        editor = ttk.Frame(fields_tab, style="Panel.TFrame")
        editor.pack(fill="x", pady=(7, 0))
        field_var = tk.StringVar()
        choice_var = tk.StringVar()
        number_var = tk.StringVar()
        field_help_var = tk.StringVar(value="Choose a field to see its editing guidance.")
        value = tk.Text(editor, height=3, wrap="word", bg=self.colors["inset"], fg=self.colors["text"], insertbackground=self.colors["text"], relief="flat")
        ttk.Label(editor, text="Field", style="Panel.TLabel").grid(row=0, column=0, sticky="w", padx=(8, 4), pady=(6, 2))
        field_box = ttk.Combobox(editor, textvariable=field_var, state="readonly", width=25)
        field_box.grid(row=0, column=1, sticky="ew", padx=(0, 6), pady=(6, 2))
        Tooltip(field_box, "Choose a database field. The value control below changes automatically to the correct type.")
        field_box.bind("<<ComboboxSelected>>", lambda _event, item_kind=kind: self.field_choice_changed(item_kind))
        ttk.Label(editor, text="Value", style="Panel.TLabel").grid(row=1, column=0, sticky="nw", padx=(8, 4), pady=4)
        value.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)
        choice_box = ttk.Combobox(editor, textvariable=choice_var, state="readonly")
        number_box = ttk.Spinbox(editor, textvariable=number_var, width=18)
        apply_button = ttk.Button(editor, text="Apply Field", style="Accent.TButton", command=lambda item_kind=kind: self.apply_field(item_kind))
        apply_button.grid(row=2, column=1, sticky="w", padx=(0, 6), pady=(0, 3))
        Tooltip(apply_button, "Writes the selected field value to the starting database.")
        remove_button = ttk.Button(editor, text="Remove Field", command=lambda item_kind=kind: self.remove_field(item_kind))
        remove_button.grid(row=2, column=1, sticky="e", padx=(0, 6), pady=(0, 3))
        Tooltip(remove_button, "Removes an optional authored field. Required identity fields cannot be removed.")
        ttk.Label(editor, textvariable=field_help_var, style="Muted.TLabel", wraplength=520).grid(row=3, column=0, columnspan=2, sticky="w", padx=8, pady=(0, 7))
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
            self.fighter_field_tree, self.fighter_field_var, self.fighter_value_text, self.fighter_value_choice, self.fighter_value_combo, self.fighter_value_number, self.fighter_value_spinbox, self.fighter_field_box, self.fighter_raw_text, self.fighter_field_help = tree, field_var, value, choice_var, choice_box, number_var, number_box, field_box, raw, field_help_var
            self.build_quick_fighter_editor(profile_tab, self.FIGHTER_PROFILE_SECTIONS, "Profile")
            self.build_quick_fighter_editor(business_tab, self.FIGHTER_BUSINESS_SECTIONS, "Business & Contract")
            self.build_core_rating_editor(ratings_tab)
            self.build_detailed_skill_editor(skills_tab)
        else:
            self.company_field_tree, self.company_field_var, self.company_value_text, self.company_value_choice, self.company_value_combo, self.company_value_number, self.company_value_spinbox, self.company_field_box, self.company_raw_text, self.company_field_help = tree, field_var, value, choice_var, choice_box, number_var, number_box, field_box, raw, field_help_var

    def build_detailed_skill_editor(self, parent):
        """Build the direct, all-skills editor used for authored fighter sheets."""
        overview = ttk.Frame(parent, style="Panel.TFrame")
        overview.pack(fill="x", padx=8, pady=(8, 6))
        ttk.Label(overview, text="SKILL SHEET", style="Title.TLabel").grid(row=0, column=0, sticky="w", padx=10, pady=(8, 1))
        ttk.Label(
            overview,
            text="Every skill below is an exact opening value from 1 to 99. Edit the number or drag its slider, then apply the full sheet.",
            style="Muted.TLabel",
        ).grid(row=1, column=0, sticky="w", padx=10, pady=(0, 8))
        self.fighter_skill_current_overall = tk.StringVar(value="Current OVR: -")
        self.fighter_skill_suggested_overall = tk.StringVar(value="Suggested from skills: -")
        self.fighter_skill_difference = tk.StringVar(value="Difference: -")
        for row, variable in enumerate((self.fighter_skill_current_overall, self.fighter_skill_suggested_overall, self.fighter_skill_difference)):
            ttk.Label(overview, textvariable=variable, style="Panel.TLabel" if row else "Title.TLabel").grid(
                row=row, column=1, sticky="e", padx=12, pady=(8, 1) if row == 0 else 1,
            )
        overview.columnconfigure(0, weight=1)

        sheet_frame = ttk.Frame(parent, style="Inset.TFrame")
        sheet_frame.pack(fill="both", expand=True, padx=8, pady=(0, 7))
        self.fighter_skill_canvas = tk.Canvas(sheet_frame, bg=self.colors["inset"], highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(sheet_frame, orient="vertical", command=self.fighter_skill_canvas.yview)
        self.fighter_skill_canvas.configure(yscrollcommand=scrollbar.set)
        self.fighter_skill_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        self.fighter_skill_sheet = ttk.Frame(self.fighter_skill_canvas, style="Inset.TFrame")
        self.fighter_skill_sheet_window = self.fighter_skill_canvas.create_window((0, 0), window=self.fighter_skill_sheet, anchor="nw")
        self.fighter_skill_sheet.bind("<Configure>", self.refresh_skill_sheet_scrollregion)
        self.fighter_skill_canvas.bind("<Configure>", self.fit_skill_sheet_to_canvas)
        self.fighter_skill_canvas.bind_all("<MouseWheel>", self.scroll_skill_sheet, add="+")

        self.fighter_skill_vars = {}
        self.fighter_skill_scales = {}
        self.fighter_skill_sources = {}
        self._refreshing_skill_editor = False
        for index, (group, skills) in enumerate(DETAILED_SKILL_GROUPS.items()):
            row, column = divmod(index, 2)
            group_frame = ttk.LabelFrame(self.fighter_skill_sheet, text=group, padding=(9, 7))
            group_frame.grid(row=row, column=column, sticky="new", padx=6, pady=6)
            group_frame.columnconfigure(1, weight=1)
            for skill_row, skill in enumerate(skills):
                label = ttk.Label(group_frame, text=self.detailed_skill_label(skill), style="Panel.TLabel")
                label.grid(row=skill_row, column=0, sticky="w", padx=(0, 7), pady=3)
                Tooltip(label, f"{self.detailed_skill_label(skill)}: exact opening ability from 1 to 99.")
                variable = tk.StringVar(value="1")
                self.fighter_skill_vars[skill] = variable
                scale = ttk.Scale(
                    group_frame, from_=1, to=99, orient="horizontal", length=145,
                    command=lambda value, target=variable: self.set_skill_sheet_from_scale(target, value),
                )
                scale.grid(row=skill_row, column=1, sticky="ew", pady=3)
                Tooltip(scale, f"Drag to set {self.detailed_skill_label(skill)} from 1 to 99.")
                self.fighter_skill_scales[skill] = scale
                spinbox = ttk.Spinbox(group_frame, textvariable=variable, from_=1, to=99, increment=1, width=5)
                spinbox.grid(row=skill_row, column=2, sticky="e", padx=(7, 0), pady=3)
                Tooltip(spinbox, f"Enter {self.detailed_skill_label(skill)} as a whole number from 1 to 99.")
                spinbox.bind("<KeyRelease>", lambda _event: self.refresh_skill_sheet_overview())
                spinbox.bind("<FocusOut>", lambda _event: self.normalize_skill_sheet_inputs())
            self.fighter_skill_sheet.columnconfigure(column, weight=1, uniform="skill_groups")

        actions = ttk.Frame(parent, style="Panel.TFrame")
        actions.pack(fill="x", padx=8, pady=(0, 8))
        apply_button = ttk.Button(actions, text="Apply Full Skill Sheet", style="Accent.TButton", command=self.apply_skill_sheet)
        apply_button.pack(side="left", padx=8, pady=7)
        Tooltip(apply_button, "Writes all 67 displayed 1-99 skills to the selected fighter's opening profile.")
        sync_button = ttk.Button(actions, text="Sync Core Ratings From Skills", command=self.sync_core_ratings_from_skill_sheet)
        sync_button.pack(side="left", padx=2, pady=7)
        Tooltip(sync_button, "Recalculates the broad Core Ratings from this exact skill sheet, without changing the listed skill values.")
        suggested_button = ttk.Button(actions, text="Use Suggested OVR", command=self.use_skill_sheet_suggested_overall)
        suggested_button.pack(side="left", padx=2, pady=7)
        Tooltip(suggested_button, "Applies the skill sheet and sets both opening OVR fields to the suggested rating calculated from it.")
        revert_button = ttk.Button(actions, text="Revert Unapplied Changes", command=self.revert_skill_sheet)
        revert_button.pack(side="left", padx=2, pady=7)
        Tooltip(revert_button, "Restores the displayed values from the selected fighter's stored opening profile.")
        lock_button = ttk.Button(actions, text="Lock Full Opening Profile", command=self.materialize_opening_profile)
        lock_button.pack(side="right", padx=8, pady=7)
        Tooltip(lock_button, "Fills any missing opening values so future new games use this exact authored profile.")

    CORE_RATING_FIELDS = (
        ("striking", "Striking"), ("wrestling", "Wrestling"), ("grappling", "Grappling"),
        ("cardio", "Cardio"), ("chin", "Chin"), ("power", "Power"),
        ("takedown_defence", "Takedown Defence"), ("ground_control", "Ground Control"),
        ("submissions", "Submissions"), ("submission_defence", "Submission Defence"),
        ("recovery", "Recovery"), ("toughness", "Toughness"), ("fight_iq", "Fight IQ"),
        ("finishing_instinct", "Finishing"),
    )
    FIGHTER_PROFILE_SECTIONS = (
        ("Identity", ("name", "owner", "placement", "seed_org", "gender", "weight", "age", "region", "nationality", "birth_country", "hometown")),
        ("Career", ("record_w", "record_l", "record_d", "rating", "profile_rating", "potential", "prime_start", "prime_end", "style", "profile_style", "stance", "trait", "behaviour", "camp")),
    )
    FIGHTER_BUSINESS_SECTIONS = (
        ("Market", ("popularity", "star_quality", "charisma", "media_presence", "sponsor_appeal", "professionalism", "injury_proneness")),
        ("Contract", ("contract_type", "contract_months", "purse", "win_bonus", "exclusive", "negotiation_persona")),
    )

    def build_quick_fighter_editor(self, parent, sections, title):
        ttk.Label(parent, text=f"{title} fields are direct starting-database values. Use Advanced Fields for every optional or technical value.", style="Muted.TLabel").pack(anchor="w", padx=8, pady=(8, 4))
        body = ttk.Frame(parent, style="Panel.TFrame")
        body.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        self.fighter_quick_vars = getattr(self, "fighter_quick_vars", {})
        self.fighter_quick_controls = getattr(self, "fighter_quick_controls", {})
        for section_index, (section_name, fields) in enumerate(sections):
            frame = ttk.LabelFrame(body, text=section_name, padding=8)
            frame.grid(row=0, column=section_index, sticky="nsew", padx=(0, 8) if section_index == 0 else 0, pady=8)
            frame.columnconfigure(1, weight=1)
            for row, field in enumerate(fields):
                label = ttk.Label(frame, text=self.detailed_skill_label(field), style="Panel.TLabel")
                label.grid(row=row, column=0, sticky="w", padx=(0, 7), pady=3)
                Tooltip(label, self.field_help_text("fighter", field))
                variable = tk.StringVar()
                is_choice = field in FIGHTER_VALUE_CHOICES or field in ("owner", "seed_org")
                if is_choice:
                    control = ttk.Combobox(frame, textvariable=variable, state="readonly", width=24)
                elif field in FIGHTER_NUMERIC_AUTHOR_FIELDS or field in {"age", "record_w", "record_l", "record_d", "contract_months", "purse", "win_bonus"}:
                    control = ttk.Spinbox(frame, textvariable=variable, width=14)
                else:
                    control = ttk.Entry(frame, textvariable=variable, width=25)
                control.grid(row=row, column=1, sticky="ew", pady=3)
                Tooltip(control, self.field_help_text("fighter", field))
                self.fighter_quick_vars[field] = variable
                self.fighter_quick_controls[field] = control
            body.columnconfigure(section_index, weight=1)
        actions = ttk.Frame(parent, style="Panel.TFrame")
        actions.pack(fill="x", padx=8, pady=(0, 8))
        fields = tuple(field for _name, section_fields in sections for field in section_fields)
        button = ttk.Button(actions, text=f"Apply {title}", style="Accent.TButton", command=lambda selected=fields: self.apply_quick_fighter_fields(selected))
        button.pack(side="left", padx=8, pady=7)
        Tooltip(button, f"Apply every edited field in this {title.lower()} section to the selected fighter.")

    def refresh_quick_fighter_editor(self, record):
        if not hasattr(self, "fighter_quick_vars"):
            return
        for field, variable in self.fighter_quick_vars.items():
            value = record.get(field, self.fighter_defaults.get(field, "")) if isinstance(record, dict) else ""
            control = self.fighter_quick_controls[field]
            choices = self.value_choices_for("fighter", field)
            if isinstance(control, ttk.Combobox):
                values = tuple(str(choice) for choice in choices)
                if value in (None, ""):
                    values = (UNSET_CHOICE_LABEL, *values)
                    variable.set(UNSET_CHOICE_LABEL)
                else:
                    shown = str(value)
                    if shown not in values:
                        values = (shown, *values)
                    variable.set(shown)
                control["values"] = values
            else:
                numeric = self.numeric_spec_for("fighter", field, compact_json(value))
                if numeric and isinstance(control, ttk.Spinbox):
                    lower, upper, increment = numeric
                    control.configure(from_=lower, to=upper, increment=increment)
                variable.set("" if value is None else str(value))

    def apply_quick_fighter_fields(self, fields):
        record = self.selected_fighter()
        if not isinstance(record, dict):
            messagebox.showinfo("No fighter selected", "Select a fighter first.")
            return
        updates = {}
        for field in fields:
            value = self.fighter_quick_vars[field].get()
            if self.value_choices_for("fighter", field) and value == UNSET_CHOICE_LABEL:
                value = ""
            else:
                value = json_value(value)
            if field == "prime_age" and value in ("", None):
                # This is a legacy legend reset override, not the normal
                # prime window. Keeping it blank must be a valid profile save.
                updates[field] = None
                continue
            numeric = self.numeric_spec_for("fighter", field, compact_json(record.get(field, self.fighter_defaults.get(field, ""))))
            if numeric:
                lower, upper, increment = numeric
                if isinstance(value, bool) or not isinstance(value, (int, float)) or not lower <= value <= upper:
                    messagebox.showerror("Invalid value", f"{self.detailed_skill_label(field)} must be between {lower:g} and {upper:g}.")
                    return
                value = int(value) if increment == 1 else float(value)
            updates[field] = value
        record.update(updates)
        self.refresh_all()

    def build_core_rating_editor(self, parent):
        ttk.Label(parent, text="Core ratings are direct 1-99 values. Suggested OVR updates from these ratings and individual skill values.", style="Muted.TLabel").pack(anchor="w", padx=8, pady=(8, 4))
        self.fighter_suggested_overall = tk.StringVar(value="Suggested OVR: -")
        ttk.Label(parent, textvariable=self.fighter_suggested_overall, style="Title.TLabel").pack(anchor="w", padx=8, pady=(0, 7))
        grid = ttk.Frame(parent, style="Panel.TFrame")
        grid.pack(fill="x", padx=8, pady=(0, 8))
        self.fighter_core_rating_vars = {}
        self.fighter_core_rating_scales = {}
        for index, (field, label) in enumerate(self.CORE_RATING_FIELDS):
            row, column = divmod(index, 2)
            offset = column * 3
            rating_label = ttk.Label(grid, text=label, style="Panel.TLabel")
            rating_label.grid(row=row, column=offset, sticky="w", padx=(8, 4), pady=4)
            Tooltip(rating_label, FIELD_HELP.get(field, "Direct 1-99 fighter core rating."))
            variable = tk.StringVar()
            self.fighter_core_rating_vars[field] = variable
            spinbox = ttk.Spinbox(grid, textvariable=variable, from_=1, to=99, increment=1, width=7)
            spinbox.grid(row=row, column=offset + 1, sticky="w", padx=(0, 18), pady=4)
            Tooltip(spinbox, f"{label}: enter a whole number from 1 to 99.")
            spinbox.bind("<KeyRelease>", lambda _event: self.refresh_suggested_overall())
            spinbox.bind("<FocusOut>", lambda _event: self.refresh_suggested_overall())
            scale = ttk.Scale(
                grid, from_=1, to=99, orient="horizontal", length=108,
                command=lambda value, target=variable: self.set_core_rating_from_scale(target, value),
            )
            scale.grid(row=row, column=offset + 2, sticky="w", padx=(0, 10), pady=4)
            self.fighter_core_rating_scales[field] = scale
            Tooltip(scale, f"Drag to adjust {label}. The spinbox keeps the exact whole-number value.")
        actions = ttk.Frame(parent, style="Panel.TFrame")
        actions.pack(fill="x", padx=8, pady=(0, 8))
        apply_button = ttk.Button(actions, text="Apply Core Ratings", style="Accent.TButton", command=self.apply_core_ratings)
        apply_button.pack(side="left", padx=8, pady=7)
        Tooltip(apply_button, "Writes all displayed 1-99 core ratings to this fighter's database record.")
        suggested_button = ttk.Button(actions, text="Use Suggested OVR", command=self.use_suggested_overall)
        suggested_button.pack(side="left", padx=2, pady=7)
        Tooltip(suggested_button, "Sets Profile Rating to the suggested OVR calculated from the fighter's current ratings and skills.")

    def core_rating_value(self, record, field, overrides=None):
        values = overrides if isinstance(overrides, dict) and field in overrides else record if isinstance(record, dict) else {}
        raw = values.get(field) if isinstance(values, dict) else None
        if raw not in (None, ""):
            try:
                return max(1, min(99, int(raw)))
            except (TypeError, ValueError):
                pass
        return self.fighter_opening_rating(record if isinstance(record, dict) else {})

    def detailed_skill_value(self, record, skill, core_overrides=None, skill_overrides=None):
        record = record if isinstance(record, dict) else {}
        overrides = skill_overrides if isinstance(skill_overrides, dict) else self.fighter_skill_overrides(record)
        if skill in overrides:
            try:
                return max(1, min(99, int(overrides[skill])))
            except (TypeError, ValueError):
                pass
        rating = self.fighter_opening_rating(record)
        style = record.get("profile_style") or record.get("style") or "Well-Rounded"
        group_bias = {
            "Boxer": (8, -6, -7, 2, 2, 1), "Kickboxer": (8, -5, -6, 3, 1, 1),
            "Karate": (7, -6, -7, 2, 1, 2), "Muay Thai": (8, -3, -4, 5, 1, 1),
            "Wrestler": (-7, 9, 4, 2, 3, 2), "BJJ": (-8, -1, 10, -1, 2, 2),
            "Sambo": (-1, 7, 8, 2, 3, 3), "Judo": (-5, 8, 5, 4, 2, 2),
            "Grappler": (-7, 3, 9, 0, 2, 2), "Well-Rounded": (2, 2, 2, 2, 2, 2),
        }
        standing, wrestling, ground, clinch, mental, physical = group_bias.get(style, group_bias["Well-Rounded"])
        group_bases = {
            "Standing": rating + standing,
            "Ground": rating + ground,
            "Wrestling": rating + wrestling,
            "Muay Thai Clinch": rating + clinch,
            "Mental": rating + mental,
            "Physical": rating + physical,
        }
        if isinstance(core_overrides, dict):
            group_bases.update({
                "Standing": core_overrides.get("striking", group_bases["Standing"]),
                "Ground": core_overrides.get("grappling", group_bases["Ground"]),
                "Wrestling": core_overrides.get("wrestling", group_bases["Wrestling"]),
                "Mental": core_overrides.get("fight_iq", group_bases["Mental"]),
                "Physical": round((core_overrides.get("cardio", group_bases["Physical"]) + core_overrides.get("chin", group_bases["Physical"])) / 2),
            })
        style_focus = {
            "Boxer": ("punch_power", "punch_technique", "hand_speed", "head_movement"),
            "Kickboxer": ("high_kick_power", "high_kick_technique", "low_kick_technique", "kick_defence"),
            "Karate": ("footwork", "high_kick_speed", "creative_kicks", "head_movement"),
            "Muay Thai": ("knees", "elbows", "thai_plum", "low_kick_power"),
            "Wrestler": ("takedowns", "takedown_setup", "chain_wrestling", "sprawl"),
            "BJJ": ("submission_attack", "submission_defence_detail", "guard_work", "back_control"),
            "Sambo": ("takedowns", "throws", "submission_attack", "leg_locks"),
            "Judo": ("throws", "clinch_takedowns", "top_control", "positional_ability"),
            "Grappler": ("top_control", "submission_attack", "transitions", "scrambles"),
        }
        name_seed = sum((index + 1) * ord(char) for index, char in enumerate(str(record.get("name", ""))))
        skill_mods = record.get("skill_mods") if isinstance(record.get("skill_mods"), dict) else {}
        for group, skills in DETAILED_SKILL_GROUPS.items():
            if skill in skills:
                variation = ((name_seed + skills.index(skill) * 17 + len(group) * 7) % 7) - 3
                focus_bonus = 5 if skill in style_focus.get(style, ("adaptability", "conditioning")) else 0
                return max(1, min(99, group_bases[group] + variation + focus_bonus + int(skill_mods.get(skill, 0) or 0)))
        return self.fighter_opening_rating(record)

    def suggested_overall_for_record(self, record, core_overrides=None, skill_overrides=None):
        """Suggest an OVR from the actual authored broad and individual skill sheet."""
        values = core_overrides if isinstance(core_overrides, dict) else {}
        core = {field: self.core_rating_value(record, field, values) for field, _label in self.CORE_RATING_FIELDS}
        group_values = {
            group: round(sum(
                self.detailed_skill_value(record, skill, values, skill_overrides)
                for skill in skills
            ) / max(1, len(skills)))
            for group, skills in DETAILED_SKILL_GROUPS.items()
        }
        # Broad ratings describe a fighter at a glance, while individual skills are
        # the actual exchange-level data. Blend both so neither can mask the other.
        components = (
            (0.22, (core["striking"] + group_values["Standing"]) / 2),
            (0.15, (core["wrestling"] + group_values["Wrestling"]) / 2),
            (0.15, (core["grappling"] + group_values["Ground"]) / 2),
            (0.10, (core["takedown_defence"] + core["ground_control"] + group_values["Muay Thai Clinch"]) / 3),
            (0.14, (core["cardio"] + core["recovery"] + group_values["Physical"]) / 3),
            (0.10, (core["chin"] + core["toughness"] + group_values["Physical"]) / 3),
            (0.09, (core["fight_iq"] + group_values["Mental"]) / 2),
            (0.05, (core["power"] + core["finishing_instinct"] + group_values["Standing"] + group_values["Ground"]) / 4),
        )
        return max(1, min(99, round(sum(weight * value for weight, value in components))))

    def refresh_suggested_overall(self):
        record = self.selected_fighter()
        if not isinstance(record, dict) or not hasattr(self, "fighter_core_rating_vars"):
            if hasattr(self, "fighter_suggested_overall"):
                self.fighter_suggested_overall.set("Suggested OVR: -")
            return
        overrides = {}
        for field, variable in self.fighter_core_rating_vars.items():
            try:
                overrides[field] = int(variable.get())
            except (TypeError, ValueError):
                continue
        self.fighter_suggested_overall.set(f"Suggested OVR: {self.suggested_overall_for_record(record, overrides)}")

    def refresh_core_rating_editor(self, record):
        if not hasattr(self, "fighter_core_rating_vars"):
            return
        for field, variable in self.fighter_core_rating_vars.items():
            value = self.core_rating_value(record, field)
            variable.set(str(value))
            scale = getattr(self, "fighter_core_rating_scales", {}).get(field)
            if scale:
                scale.set(value)
        self.refresh_suggested_overall()

    def set_core_rating_from_scale(self, variable, value):
        variable.set(str(max(1, min(99, round(float(value))))))
        self.refresh_suggested_overall()

    def apply_core_ratings(self):
        record = self.selected_fighter()
        if not isinstance(record, dict):
            messagebox.showinfo("No fighter selected", "Select a fighter first.")
            return
        values = {}
        for field, variable in self.fighter_core_rating_vars.items():
            try:
                value = int(variable.get())
            except (TypeError, ValueError):
                messagebox.showerror("Invalid rating", f"{field} must be a whole number from 1 to 99.")
                return
            if not 1 <= value <= 99:
                messagebox.showerror("Rating out of range", f"{field} must be between 1 and 99.")
                return
            values[field] = value
        record.update(values)
        self.refresh_fighter_editor()

    def use_suggested_overall(self):
        record = self.selected_fighter()
        if not isinstance(record, dict):
            messagebox.showinfo("No fighter selected", "Select a fighter first.")
            return
        overrides = {}
        for field, _label in self.CORE_RATING_FIELDS:
            try:
                value = int(self.fighter_core_rating_vars[field].get())
            except (TypeError, ValueError):
                value = self.core_rating_value(record, field)
            overrides[field] = max(1, min(99, value))
        suggested = self.suggested_overall_for_record(record, overrides)
        record["rating"] = suggested
        record["profile_rating"] = suggested
        self.refresh_fighter_editor()

    @staticmethod
    def _average_skill_values(values, keys, fallback=50):
        return round(sum(values.get(key, fallback) for key in keys) / max(1, len(keys)))

    def apply_core_ratings_from_skill_values(self, record, details):
        """Keep the broad card ratings coherent with a directly authored skill sheet."""
        groups = DETAILED_SKILL_GROUPS
        record["striking"] = self._average_skill_values(details, groups["Standing"])
        record["wrestling"] = self._average_skill_values(details, groups["Wrestling"])
        record["grappling"] = self._average_skill_values(details, groups["Ground"])
        record["cardio"] = self._average_skill_values(details, ("conditioning", "resilience", "dedication"))
        record["chin"] = self._average_skill_values(details, ("chin_strength", "stun_recovery", "resilience"))
        record["power"] = self._average_skill_values(details, ("punch_power", "high_kick_power", "strength"))
        record["takedown_defence"] = self._average_skill_values(details, ("takedown_defence_detail", "sprawl", "get_ups"))
        record["ground_control"] = self._average_skill_values(details, ("top_control", "positional_ability", "ride_control"))
        record["submissions"] = self._average_skill_values(details, ("submission_attack", "leg_locks", "back_control"))
        record["submission_defence"] = self._average_skill_values(details, ("submission_defence_detail", "guard_work"))
        record["recovery"] = self._average_skill_values(details, ("stun_recovery", "composure"))
        record["toughness"] = self._average_skill_values(details, ("resilience", "chin_strength"))
        record["fight_iq"] = self._average_skill_values(details, ("adaptability", "composure", "discipline"))
        record["finishing_instinct"] = self._average_skill_values(details, ("killer_instinct", "punch_power", "submission_attack"))

    def materialize_record_opening_profile(self, record):
        """Write a complete opening profile directly into one database record."""
        if not isinstance(record, dict):
            return False
        details = dict(self.fighter_skill_overrides(record))
        for skills in DETAILED_SKILL_GROUPS.values():
            for skill in skills:
                details[skill] = self.detailed_skill_value(record, skill)
        special = record.get("special_profile") if isinstance(record.get("special_profile"), dict) else {}
        for key, value in (special.get("skill_minimums") or {}).items():
            if key in details:
                details[key] = max(details[key], int(value))
        for key, value in (special.get("skill_values") or {}).items():
            if key in details:
                details[key] = max(1, min(99, int(value)))
        for group, value in (special.get("group_minimums") or {}).items():
            for key in DETAILED_SKILL_GROUPS.get(group, ()):
                details[key] = max(details[key], int(value))
        for key, bounds in (special.get("skill_random_minimums") or {}).items():
            if key in details and isinstance(bounds, (tuple, list)) and len(bounds) == 2:
                details[key] = max(details[key], round((int(bounds[0]) + int(bounds[1])) / 2))
        for key, bounds in (special.get("skill_random_maximums") or {}).items():
            if key in details and isinstance(bounds, (tuple, list)) and len(bounds) == 2:
                details[key] = min(details[key], round((int(bounds[0]) + int(bounds[1])) / 2))
        record["signature_skills"] = details

        self.apply_core_ratings_from_skill_values(record, details)
        for field, value in (special.get("broad_values") or {}).items():
            if field in {key for key, _label in self.CORE_RATING_FIELDS}:
                record[field] = max(1, min(99, int(value)))
        for field, value in (special.get("broad_minimums") or {}).items():
            if field in {key for key, _label in self.CORE_RATING_FIELDS}:
                record[field] = max(record[field], int(value))
        for field, value in (special.get("broad_maximums") or {}).items():
            if field in {key for key, _label in self.CORE_RATING_FIELDS}:
                record[field] = min(record[field], int(value))
        if special.get("potential") not in (None, ""):
            record["potential"] = max(record.get("potential") or 0, int(special["potential"]))
        overall = self.suggested_overall_for_record(record)
        record["rating"] = overall
        record["profile_rating"] = overall
        if record.get("potential") in (None, ""):
            record["potential"] = min(98, overall + 6)
        return True

    def materialize_opening_profile(self):
        """Persist a complete, deterministic opening sheet for the selected fighter."""
        record = self.selected_fighter()
        if not isinstance(record, dict):
            messagebox.showinfo("No fighter selected", "Select a fighter first.")
            return
        self.materialize_record_opening_profile(record)
        self.refresh_fighter_editor()

    def materialize_all_opening_profiles(self):
        if not self.ensure_database_loaded():
            return
        count = len(self.fighter_records())
        if not messagebox.askyesno(
            "Lock opening profiles",
            f"Write full core and detailed 1-99 opening profiles for all {count:,} fighters?\n\n"
            "This makes the editor and all future new games use the same seeded values. Save the database afterwards.",
        ):
            return
        for record in self.fighter_records():
            self.materialize_record_opening_profile(record)
        self.refresh_all()
        self.status_var.set(f"Locked exact opening profiles for {count:,} fighters. Save to write the database.")

    @staticmethod
    def detailed_skill_label(skill):
        return str(skill).replace("_", " ").title()

    @staticmethod
    def fighter_skill_overrides(record):
        if not isinstance(record, dict):
            return {}
        values = record.get("signature_skills") or record.get("detailed_skills") or {}
        return values if isinstance(values, dict) else {}

    def refresh_skill_sheet_scrollregion(self, _event=None):
        if hasattr(self, "fighter_skill_canvas"):
            self.fighter_skill_canvas.configure(scrollregion=self.fighter_skill_canvas.bbox("all"))

    def fit_skill_sheet_to_canvas(self, event):
        if hasattr(self, "fighter_skill_canvas") and hasattr(self, "fighter_skill_sheet_window"):
            self.fighter_skill_canvas.itemconfigure(self.fighter_skill_sheet_window, width=event.width)

    def scroll_skill_sheet(self, event):
        if not hasattr(self, "fighter_skill_canvas") or not self.fighter_skill_canvas.winfo_ismapped():
            return
        canvas = self.fighter_skill_canvas
        within_canvas = (
            canvas.winfo_rootx() <= event.x_root <= canvas.winfo_rootx() + canvas.winfo_width()
            and canvas.winfo_rooty() <= event.y_root <= canvas.winfo_rooty() + canvas.winfo_height()
        )
        if not within_canvas:
            return
        steps = -1 if event.delta > 0 else 1
        canvas.yview_scroll(steps * 3, "units")

    def skill_sheet_values(self, show_errors=False):
        values = {}
        for skill, variable in getattr(self, "fighter_skill_vars", {}).items():
            try:
                value = int(variable.get())
            except (TypeError, ValueError):
                if show_errors:
                    messagebox.showerror("Invalid skill value", f"{self.detailed_skill_label(skill)} must be a whole number from 1 to 99.")
                return None
            if not 1 <= value <= 99:
                if show_errors:
                    messagebox.showerror("Skill value out of range", f"{self.detailed_skill_label(skill)} must be between 1 and 99.")
                return None
            values[skill] = value
        return values

    def refresh_skill_sheet_overview(self):
        if getattr(self, "_refreshing_skill_editor", False):
            return
        record = self.selected_fighter()
        values = self.skill_sheet_values()
        if not isinstance(record, dict) or values is None:
            return
        current = self.fighter_opening_rating(record)
        suggested = self.suggested_overall_for_record(record, skill_overrides=values)
        difference = suggested - current
        self.fighter_skill_current_overall.set(f"Current OVR: {current}")
        self.fighter_skill_suggested_overall.set(f"Suggested OVR: {suggested}")
        self.fighter_skill_difference.set(f"Difference: {difference:+d} from current OVR")

    def normalize_skill_sheet_inputs(self):
        if getattr(self, "_refreshing_skill_editor", False):
            return
        for skill, variable in getattr(self, "fighter_skill_vars", {}).items():
            try:
                value = int(variable.get())
            except (TypeError, ValueError):
                continue
            value = max(1, min(99, value))
            variable.set(str(value))
            scale = self.fighter_skill_scales.get(skill)
            if scale:
                scale.set(value)
        self.refresh_skill_sheet_overview()

    def set_skill_sheet_from_scale(self, variable, value):
        if getattr(self, "_refreshing_skill_editor", False):
            return
        variable.set(str(max(1, min(99, round(float(value))))))
        self.refresh_skill_sheet_overview()

    def refresh_detailed_skill_editor(self, record):
        if not hasattr(self, "fighter_skill_vars"):
            return
        self._refreshing_skill_editor = True
        try:
            overrides = self.fighter_skill_overrides(record)
            for skill, variable in self.fighter_skill_vars.items():
                value = overrides.get(skill)
                if value in (None, ""):
                    value = self.detailed_skill_value(record, skill)
                value = max(1, min(99, int(value)))
                variable.set(str(value))
                scale = self.fighter_skill_scales.get(skill)
                if scale:
                    scale.set(value)
        finally:
            self._refreshing_skill_editor = False
        self.refresh_skill_sheet_overview()

    def save_skill_sheet_values(self, record, values):
        record["signature_skills"] = dict(values)
        record.pop("detailed_skills", None)

    def apply_skill_sheet(self):
        record = self.selected_fighter()
        if not isinstance(record, dict):
            messagebox.showinfo("No fighter selected", "Select a fighter first.")
            return False
        values = self.skill_sheet_values(show_errors=True)
        if values is None:
            return False
        self.save_skill_sheet_values(record, values)
        self.refresh_fighter_editor()
        self.status_var.set(f"Applied all {len(values)} individual skill values for {record.get('name', 'fighter')}.")
        return True

    def sync_core_ratings_from_skill_sheet(self):
        record = self.selected_fighter()
        values = self.skill_sheet_values(show_errors=True)
        if not isinstance(record, dict) or values is None:
            return
        self.save_skill_sheet_values(record, values)
        self.apply_core_ratings_from_skill_values(record, values)
        self.refresh_fighter_editor()
        self.status_var.set(f"Synced Core Ratings from the skill sheet for {record.get('name', 'fighter')}.")

    def use_skill_sheet_suggested_overall(self):
        record = self.selected_fighter()
        values = self.skill_sheet_values(show_errors=True)
        if not isinstance(record, dict) or values is None:
            return
        self.save_skill_sheet_values(record, values)
        self.apply_core_ratings_from_skill_values(record, values)
        suggested = self.suggested_overall_for_record(record, skill_overrides=values)
        record["rating"] = suggested
        record["profile_rating"] = suggested
        self.refresh_fighter_editor()
        self.status_var.set(f"Set {record.get('name', 'fighter')} to suggested OVR {suggested} from the current skill sheet.")

    def revert_skill_sheet(self):
        record = self.selected_fighter()
        self.refresh_detailed_skill_editor(record)

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
            if not self.matches_number_range(self.fighter_opening_rating(record), min_rating, max_rating):
                continue
            if not self.matches_number_range(record.get("age"), min_age, max_age):
                continue
            if min_popularity is not None and not self.matches_number_range(record.get("popularity", record.get("pop")), min_popularity, None):
                continue
            rows.append((index, record))
        return rows

    @staticmethod
    def fighter_opening_rating(record):
        """Return the OVR a new game will use for an authored fighter."""
        value = record.get("profile_rating", record.get("rating", record.get("skill", record.get("overall", 65))))
        try:
            return int(value)
        except (TypeError, ValueError):
            return int(record.get("rating", 65) or 65)

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
            value = (
                self.company_kind_for_key(key) if table_kind == "company" and column == "kind"
                else self.fighter_opening_rating(record) if table_kind == "fighter" and column == "rating"
                else record.get(column)
            )
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
            self.fighter_tree.insert("", "end", iid=str(index), values=(record.get("name", ""), record.get("owner", ""), record.get("weight", ""), record.get("gender", ""), self.fighter_opening_rating(record), record.get("potential", ""), record.get("popularity", record.get("pop", "")), record.get("age", ""), record.get("style", ""), record.get("region", "")))
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
            tree, raw, field_var, field_box = self.fighter_field_tree, self.fighter_raw_text, self.fighter_field_var, self.fighter_field_box
            fields, defaults = self.fighter_field_names(), self.fighter_defaults
        else:
            tree, raw, field_var, field_box = self.company_field_tree, self.company_raw_text, self.company_field_var, self.company_field_box
            fields, defaults = self.company_field_names(), self.company_defaults
        for item in tree.get_children():
            tree.delete(item)
        raw.delete("1.0", "end")
        if not isinstance(record, dict):
            field_var.set("")
            field_box["values"] = ()
            self.clear_value_control(kind)
            if kind == "fighter":
                self.refresh_quick_fighter_editor(None)
                self.refresh_core_rating_editor(None)
                self.refresh_detailed_skill_editor(None)
            return
        for field in fields:
            authored = field in record
            value = record[field] if authored else defaults.get(field, "")
            source = "Authored" if authored else "Default"
            tree.insert("", "end", iid=field, values=(field, compact_json(value), source))
        field_box["values"] = fields
        raw.insert("1.0", json.dumps(record, indent=2, ensure_ascii=True))
        current_field = field_var.get()
        if current_field in fields:
            self.configure_value_control(kind, current_field, compact_json(record.get(current_field, defaults.get(current_field, ""))))
        else:
            field_var.set("")
            self.clear_value_control(kind)
        if kind == "fighter":
            self.refresh_quick_fighter_editor(record)
            self.refresh_core_rating_editor(record)
            self.refresh_detailed_skill_editor(record)

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
        if not field:
            self.clear_value_control(kind)
            return
        record = self.record_for_kind(kind)
        defaults = self.fighter_defaults if kind == "fighter" else self.company_defaults
        value = record.get(field, defaults.get(field, "")) if isinstance(record, dict) else defaults.get(field, "")
        self.configure_value_control(kind, field, compact_json(value))

    def clear_value_control(self, kind):
        """Return an editor value area to a neutral state between records/fields."""
        if kind == "fighter":
            value_text, choice_var, choice_box, number_var, number_box = self.fighter_value_text, self.fighter_value_choice, self.fighter_value_combo, self.fighter_value_number, self.fighter_value_spinbox
        else:
            value_text, choice_var, choice_box, number_var, number_box = self.company_value_text, self.company_value_choice, self.company_value_combo, self.company_value_number, self.company_value_spinbox
        choice_var.set("")
        choice_box["values"] = ()
        number_var.set("")
        choice_box.grid_remove()
        number_box.grid_remove()
        value_text.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)
        value_text.delete("1.0", "end")
        help_var = self.fighter_field_help if kind == "fighter" else self.company_field_help
        help_var.set("Choose a field to see its editing guidance.")

    def field_help_text(self, kind, field):
        if field in FIELD_HELP:
            return FIELD_HELP[field]
        if self.value_choices_for(kind, field):
            return "Choose a valid option. Existing custom values are retained so they can be corrected safely."
        if self.numeric_spec_for(kind, field, "0"):
            return "Numeric field. The editor enforces the valid range shown by its spinner."
        return "Free-form database value. Use valid JSON for lists or objects; plain text is stored as text."

    def value_choices_for(self, kind, field):
        values = dict(FIGHTER_VALUE_CHOICES if kind == "fighter" else COMPANY_VALUE_CHOICES).get(field)
        if values is not None:
            if field == "nationality":
                return tuple(sorted({str(record.get("nationality", "")) for record in self.fighter_records() if record.get("nationality")}, key=str.casefold))
            return values
        if kind == "fighter" and field in ("owner", "seed_org"):
            companies = [PLAYER_PROMOTION_NAME, "Free Agent", "Legend"]
            companies.extend(
                str(record.get("name"))
                for record in (*self.company_records(), *self.regional_company_records())
                if record.get("name")
            )
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
        help_var = self.fighter_field_help if kind == "fighter" else self.company_field_help
        help_var.set(self.field_help_text(kind, field))
        if choices:
            value_text.grid_remove()
            number_box.grid_remove()
            number_var.set("")
            raw_value = json_value(rendered_value)
            selected = str(raw_value).lower() if isinstance(raw_value, bool) else str(raw_value)
            # Old/custom databases can contain a value outside today's normal
            # list. Keep it visible instead of blanking the field or making it
            # impossible to repair through the dropdown.
            choice_values = tuple(str(choice) for choice in choices)
            if not selected:
                choice_values = (UNSET_CHOICE_LABEL, *choice_values)
                selected = UNSET_CHOICE_LABEL
            elif selected not in choice_values:
                choice_values = (selected, *choice_values)
            choice_box["values"] = choice_values
            choice_var.set(selected)
            choice_box.grid(row=1, column=1, sticky="ew", padx=(0, 6), pady=4)
        elif numeric:
            value_text.grid_remove()
            choice_box.grid_remove()
            choice_var.set("")
            choice_box["values"] = ()
            lower, upper, increment = numeric
            number_box.configure(from_=lower, to=upper, increment=increment)
            number_var.set(str(json_value(rendered_value)))
            number_box.grid(row=1, column=1, sticky="w", padx=(0, 6), pady=4)
        else:
            choice_box.grid_remove()
            number_box.grid_remove()
            choice_var.set("")
            choice_box["values"] = ()
            number_var.set("")
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
        if self.value_choices_for(kind, field) and selected_value == UNSET_CHOICE_LABEL:
            value = ""
        if kind == "fighter" and field == "prime_age" and value in ("", None):
            record[field] = None
            self.refresh_all()
            return
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
