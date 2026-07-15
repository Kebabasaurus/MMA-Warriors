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


class AwardsMixin:
    """End-of-year awards: a season tracker fed by every fight (player and AI),
    resolved into award winners when the calendar rolls into a new year."""

    def current_year(self):
        return 2026 + (self.month - 1) // 12

    def year_label(self, year=None):
        return str(year if year is not None else self.current_year())

    def ensure_season_containers(self):
        if not hasattr(self, "season_stats") or self.season_stats is None:
            self.season_stats = {}
        if not hasattr(self, "awards_history") or self.awards_history is None:
            self.awards_history = []
        if not hasattr(self, "achievement_log") or self.achievement_log is None:
            self.achievement_log = []

    def unlock_achievement(self, scope, target, company, achievement_id, title, description):
        """Record an unlock once; achievement entries are a permanent world ledger."""
        self.ensure_season_containers()
        if any(entry.get("id") == achievement_id and entry.get("target") == target for entry in self.achievement_log):
            return False
        entry = {
            "id": achievement_id, "scope": scope, "target": target, "company": company,
            "title": title, "description": description, "month": self.month,
            "year": self.current_year(),
        }
        self.achievement_log.insert(0, entry)
        self.achievement_log = self.achievement_log[:1000]
        fighter = self.find_fighter_anywhere(target) if scope == "Fighter" and hasattr(self, "find_fighter_anywhere") else None
        if fighter:
            fighter.career_achievements = (getattr(fighter, "career_achievements", None) or [])
            fighter.career_achievements.append(title)
            fighter.career_achievements = fighter.career_achievements[-30:]
        if company == getattr(self, "player_company_name", "") or (fighter and any(member is fighter for member in getattr(self, "roster", []))):
            headline = f"Achievement unlocked: {title} — {target}"
            self.news.insert(0, headline)
            self.inbox.append({"subject": f"Achievement — {title}", "body": f"{target}: {description}", "type": "Awards", "fighter": target if fighter else "", "resolved": False})
        return True

    def fighter_company_name(self, fighter):
        if any(member is fighter for member in getattr(self, "roster", [])):
            return self.player_company_name
        for promo in getattr(self, "promotions", []):
            if any(member is fighter for member in promo.roster):
                return promo.name
        return "Independent"

    def evaluate_fight_achievements(self, winner, loser, fight, method, company=None):
        """Evaluate objective career and fight milestones after a decisive result."""
        company = company or self.fighter_company_name(winner)
        if winner.record_w == 1:
            self.unlock_achievement("Fighter", winner.name, company, "first_pro_win", "First Professional Win", "Earned their first recorded professional victory.")
        if winner.record_w == 10:
            self.unlock_achievement("Fighter", winner.name, company, "ten_career_wins", "Ten-Win Club", "Reached ten professional wins.")
        if winner.record_w == 20:
            self.unlock_achievement("Fighter", winner.name, company, "twenty_career_wins", "Twenty-Win Veteran", "Reached twenty professional wins.")
        if winner.overall + 8 <= loser.overall:
            self.unlock_achievement("Fighter", winner.name, company, "giant_slayer", "Giant Slayer", f"Defeated the higher-rated {loser.name} by {method}.")
        if fight.get("title") and winner.champion:
            self.unlock_achievement("Fighter", winner.name, company, "world_title", "World Champion", f"Captured the {winner.gender} {winner.weight} title.")
        if getattr(winner, "title_defenses", 0) == 5:
            self.unlock_achievement("Fighter", winner.name, company, "five_title_defenses", "Dynasty Builder", "Reached five successful title defenses.")
        if method not in ("Decision", "Draw") and winner.record_w >= 10:
            finishes = sum(1 for item in (winner.fight_history or []) if " by KO" in str(item) or " by TKO" in str(item) or " by Submission" in str(item))
            if finishes >= 10:
                self.unlock_achievement("Fighter", winner.name, company, "ten_finishes", "Finishing Machine", "Recorded ten documented professional finishes.")

    def evaluate_promotion_achievements(self, company, package):
        """Promotion milestones are checked after an event is committed to results."""
        total_events = sum(1 for row in getattr(self, "result_records", []) if row.get("company") == company)
        finance = package.get("finance", {}) or {}
        if total_events == 1:
            self.unlock_achievement("Promotion", company, company, "first_promoted_event", "Opening Bell", "Promoted its first recorded event.")
        if total_events == 10:
            self.unlock_achievement("Promotion", company, company, "ten_promoted_events", "Established Promotion", "Successfully promoted ten recorded events.")
        attendance, capacity = finance.get("attendance", 0), finance.get("venue_capacity", 0)
        if capacity and attendance >= capacity * 0.95:
            self.unlock_achievement("Promotion", company, company, "sellout", "Sold Out", f"Filled {attendance:,} of {capacity:,} available seats.")
        if package.get("profit", 0) >= 250_000:
            self.unlock_achievement("Promotion", company, company, "major_profit", "Big Night", f"Generated ${package['profit']:,} in event profit.")

    def open_achievements_window(self):
        self.ensure_season_containers()
        window = tk.Toplevel(self.root)
        window.title("Achievements & Milestones")
        window.geometry("980x620")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame"); header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="ACHIEVEMENTS & MILESTONES", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Label(header, text="Career landmarks and promotion accomplishments", style="Chrome.TLabel").pack(side="right", padx=10)
        controls = ttk.Frame(window, style="Inset.TFrame"); controls.pack(fill="x", padx=8, pady=8)
        ttk.Label(controls, text="Show", style="Inset.TLabel").pack(side="left", padx=(6, 4))
        scope = tk.StringVar(value="All")
        ttk.Combobox(controls, textvariable=scope, values=("All", "Fighter", "Promotion"), state="readonly", width=14).pack(side="left", padx=4)
        summary = ttk.Label(controls, style="Inset.TLabel"); summary.pack(side="right", padx=8)
        tree = ttk.Treeview(window, columns=("year", "scope", "target", "company", "achievement", "description"), show="headings")
        for column, label, width in (("year", "Year", 60), ("scope", "Type", 90), ("target", "Recipient", 180), ("company", "Promotion", 165), ("achievement", "Achievement", 175), ("description", "Description", 295)):
            tree.heading(column, text=label); tree.column(column, width=width, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=(0, 8))
        detail = tk.Text(window, height=4, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        detail.pack(fill="x", padx=8, pady=(0, 8)); detail.config(state="disabled")
        visible = []
        def render(*_args):
            visible[:] = [entry for entry in self.achievement_log if scope.get() == "All" or entry.get("scope") == scope.get()]
            tree.delete(*tree.get_children())
            for index, entry in enumerate(visible):
                tree.insert("", "end", iid=str(index), values=(entry.get("year", ""), entry.get("scope", ""), entry.get("target", ""), entry.get("company", ""), entry.get("title", ""), entry.get("description", "")))
            summary.config(text=f"{len(visible)} unlocked")
        def select(_event=None):
            chosen = tree.selection()
            detail.config(state="normal"); detail.delete("1.0", "end")
            if chosen:
                entry = visible[int(chosen[0])]
                detail.insert("end", f"{entry['title']}\n{entry['target']} — {entry['description']}\nUnlocked Month {entry.get('month', '?')}, {entry.get('year', '?')}.")
            detail.config(state="disabled")
        def open_profile(_event=None):
            chosen = tree.selection()
            if chosen and visible[int(chosen[0])].get("scope") == "Fighter":
                fighter = self.find_fighter_anywhere(visible[int(chosen[0])]["target"])
                if fighter:
                    self.open_fighter_profile_window(fighter)
        scope.trace_add("write", render); tree.bind("<<TreeviewSelect>>", select); tree.bind("<Double-1>", open_profile); render()

    def season_bucket(self, year=None):
        self.ensure_season_containers()
        key = self.year_label(year)
        return self.season_stats.setdefault(key, {"fighters": {}, "fights": [], "companies": {}})

    def record_season_result(self, winner, loser, method, round_no, fight, excitement, company):
        """Log a result for later award scoring, including draws without false W/L credit."""
        try:
            bucket = self.season_bucket()
            fighters = bucket["fighters"]
            is_finish = method not in ("Decision", "Draw")
            is_ko = method in ("KO", "TKO")
            is_sub = method in ("Submission", "Technical Submission")
            is_title = bool(fight.get("title"))

            wrec = fighters.setdefault(winner.name, self.blank_season_fighter(winner))
            wrec.update({"gender": winner.gender, "weight": winner.weight, "age": winner.age,
                         "popularity": winner.popularity, "company": company})

            lrec = fighters.setdefault(loser.name, self.blank_season_fighter(loser))
            lrec.update({"gender": loser.gender, "weight": loser.weight, "age": loser.age})
            if method == "Draw":
                wrec["draws"] = wrec.get("draws", 0) + 1
                lrec["draws"] = lrec.get("draws", 0) + 1
            else:
                wrec["wins"] += 1
                wrec["finishes"] += 1 if is_finish else 0
                wrec["kos"] += 1 if is_ko else 0
                wrec["subs"] += 1 if is_sub else 0
                wrec["title_wins"] += 1 if is_title else 0
                wrec["best_excitement"] = max(wrec["best_excitement"], excitement)
                if excitement >= wrec["best_excitement"]:
                    wrec["signature_win"] = f"def. {loser.name} by {method}"
                lrec["losses"] += 1

            comp = bucket["companies"]
            comp[company] = comp.get(company, 0) + 1

            bucket["fights"].append({
                "winner": winner.name, "loser": loser.name, "method": method, "round": round_no,
                "excitement": int(excitement), "weight": winner.weight, "gender": winner.gender,
                "title": is_title, "main": bool(fight.get("main")), "company": company,
                "date": f"Month {self.month} Week {self.week}",
            })
            # keep the most exciting bouts to bound memory
            if len(bucket["fights"]) > 220:
                bucket["fights"].sort(key=lambda r: r["excitement"], reverse=True)
                del bucket["fights"][180:]
        except Exception:
            # awards tracking must never break a fight from being applied
            pass

    def blank_season_fighter(self, fighter):
        return {"name": fighter.name, "wins": 0, "losses": 0, "draws": 0, "finishes": 0, "kos": 0, "subs": 0,
                "title_wins": 0, "best_excitement": 0, "signature_win": "", "company": "",
                "gender": fighter.gender, "weight": fighter.weight, "age": fighter.age,
                "popularity": fighter.popularity}

    # ---- award computation -------------------------------------------------

    def compute_year_awards(self, year):
        self.ensure_season_containers()
        bucket = self.season_stats.get(self.year_label(year))
        if not bucket:
            return []
        fighters = bucket["fighters"]
        fights = bucket["fights"]
        if not fights:
            return []
        awards = []

        def add(category, winner, detail, company=""):
            if winner:
                awards.append({"category": category, "winner": winner, "detail": detail, "company": company})

        # Fighter of the Year
        contenders = [f for f in fighters.values() if f["wins"] >= 2]
        if contenders:
            def foty_score(f):
                return (f["wins"] * 2 + f["finishes"] * 1.5 + f["title_wins"] * 6
                        + f["kos"] * 0.5 + f["subs"] * 0.5 + f["popularity"] * 0.02
                        - f["losses"] * 1.5)
            best = max(contenders, key=foty_score)
            record = f"{best['wins']}-{best['losses']}"
            extras = []
            if best["title_wins"]:
                extras.append(f"{best['title_wins']} title win{'s' if best['title_wins'] > 1 else ''}")
            if best["finishes"]:
                extras.append(f"{best['finishes']} finish{'es' if best['finishes'] > 1 else ''}")
            tail = f" ({', '.join(extras)})" if extras else ""
            add("Fighter of the Year", best["name"], f"Went {record}{tail}.", best["company"])

        # Fight of the Year
        foty_fight = max(fights, key=lambda r: r["excitement"])
        add("Fight of the Year", f"{foty_fight['winner']} vs {foty_fight['loser']}",
            f"{foty_fight['winner']} def. {foty_fight['loser']} by {foty_fight['method']} "
            f"(R{foty_fight['round']}) - excitement {foty_fight['excitement']}.", foty_fight["company"])

        # Knockout of the Year
        kos = [r for r in fights if r["method"] in ("KO", "TKO")]
        if kos:
            best_ko = max(kos, key=lambda r: r["excitement"])
            add("Knockout of the Year", best_ko["winner"],
                f"{best_ko['method']} over {best_ko['loser']} (R{best_ko['round']}).", best_ko["company"])

        # Submission of the Year
        subs = [r for r in fights if r["method"] in ("Submission", "Technical Submission")]
        if subs:
            best_sub = max(subs, key=lambda r: r["excitement"])
            add("Submission of the Year", best_sub["winner"],
                f"{best_sub['method']} over {best_sub['loser']} (R{best_sub['round']}).", best_sub["company"])

        # Prospect of the Year (young, winning)
        prospects = [f for f in fighters.values() if f["age"] <= 24 and f["wins"] >= 2]
        if prospects:
            best_p = max(prospects, key=lambda f: (f["wins"] * 2 + f["finishes"] - f["losses"]))
            add("Prospect of the Year", best_p["name"],
                f"Age {best_p['age']}, went {best_p['wins']}-{best_p['losses']} with {best_p['finishes']} finishes.",
                best_p["company"])

        # Veteran of the Year (older, still winning)
        vets = [f for f in fighters.values() if f["age"] >= 34 and f["wins"] >= 2]
        if vets:
            best_v = max(vets, key=lambda f: (f["wins"] * 2 + f["finishes"] - f["losses"]))
            add("Veteran of the Year", best_v["name"],
                f"Age {best_v['age']}, went {best_v['wins']}-{best_v['losses']}.", best_v["company"])

        # Promotion of the Year (busiest + most decisive scene)
        companies = bucket.get("companies", {})
        if companies:
            top_company = max(companies, key=lambda c: companies[c])
            add("Promotion of the Year", top_company, f"Ran the most competitive season with {companies[top_company]} decisive bouts.", top_company)

        return awards

    # ---- resolution & presentation ----------------------------------------

    def run_end_of_year_awards(self, year):
        awards = self.compute_year_awards(year)
        if not awards:
            return
        self.ensure_season_containers()
        self.awards_history.insert(0, {"year": self.year_label(year), "awards": awards})
        self.awards_history = self.awards_history[:12]

        headline = next((a for a in awards if a["category"] == "Fighter of the Year"), awards[0])
        self.news.insert(0, f"{self.year_label(year)} Awards: {headline['winner']} named {headline['category']}.")
        self.inbox.append({
            "subject": f"{self.year_label(year)} End-of-Year Awards",
            "body": "The results are in:\n" + "\n".join(f"- {a['category']}: {a['winner']} ({a['detail']})" for a in awards),
            "type": "Awards", "resolved": False,
        })
        self.apply_award_effects(awards)
        self.record_legacy_year(year, awards)
        self.prune_season_stats(year)
        try:
            if not getattr(self, "suppress_award_popups", False) and hasattr(self, "root") and self.root.winfo_exists():
                self.open_awards_window(self.year_label(year), awards)
        except Exception:
            pass

    def apply_award_effects(self, awards):
        """Winning an award is a career milestone: a small, lasting bump."""
        for award in awards:
            fighter = self.find_fighter_anywhere(award["winner"]) if hasattr(self, "find_fighter_anywhere") else None
            if not fighter:
                continue
            fighter.popularity = min(100, fighter.popularity + 4)
            fighter.morale = min(100, fighter.morale + 6)
            fighter.star_quality = min(99, fighter.star_quality + 3)
            fighter.media_heat = min(100, fighter.media_heat + 5)
            fighter.award_count = getattr(fighter, "award_count", 0) + 1
            history = fighter.fight_history or []
            history.insert(0, f"Won {award['category']}.")
            fighter.fight_history = history

    def record_legacy_year(self, year, awards):
        """Archive eras and company achievement alongside individual awards."""
        for promo in self.promotions:
            promo.era_history = list(getattr(promo, "era_history", []) or [])
            won = [award["category"] for award in awards if award.get("company") == promo.name]
            if won:
                executive = getattr(promo, "executive", {}) or {}
                promo.era_history.insert(0, {"year": self.year_label(year), "note": f"{executive.get('name', 'Executive')} led an award-winning year: {', '.join(won)}."})
            promo.legacy_score = round(promo.reputation_score * 1.2 + promo.size * 0.6 + len(promo.show_history or []) * 2 + len(promo.era_history) * 3)
            promo.era_history = promo.era_history[:40]
        self.record_world_story("Year In Review", f"{self.year_label(year)} MMA awards are recorded.", f"{len(awards)} major awards entered the historical record.", importance=4)

    def prune_season_stats(self, year):
        """Keep the awarded year (for history) but drop older seasons."""
        self.ensure_season_containers()
        keep = {self.year_label(year), self.year_label(int(year) + 1)}
        self.season_stats = {k: v for k, v in self.season_stats.items() if k in keep}

    def open_awards_window(self, year, awards):
        window = tk.Toplevel(self.root)
        window.title(f"{year} End-of-Year Awards")
        window.geometry("620x560")
        window.configure(bg=self.colors["chrome"])

        header = ttk.Frame(window, style="Header.TFrame")
        header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text=f"\U0001F3C6  {year} MMA WARRIORS AWARDS", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)

        body = tk.Text(window, wrap="word", font=("Georgia", 12), bg=self.colors["cream"], fg=self.colors["text"],
                       padx=18, pady=16, spacing1=4, spacing2=2, spacing3=12, relief="flat")
        body.pack(fill="both", expand=True, padx=8, pady=8)
        body.tag_configure("cat", font=("Georgia", 11, "bold"), foreground=self.colors["gold"])
        body.tag_configure("win", font=("Georgia", 14, "bold"), foreground=self.colors["red"])
        body.tag_configure("detail", font=("Georgia", 10), foreground=self.colors["text"])
        for award in awards:
            body.insert("end", f"{award['category'].upper()}\n", "cat")
            body.insert("end", f"{award['winner']}\n", "win")
            company = f"   [{award['company']}]" if award.get("company") else ""
            body.insert("end", f"{award['detail']}{company}\n\n", "detail")
        body.config(state="disabled")

        footer = ttk.Frame(window, style="Chrome.TFrame")
        footer.pack(fill="x", padx=8, pady=(0, 8))
        ttk.Button(footer, text="View Past Years", command=self.open_awards_history_window).pack(side="left", padx=4)
        ttk.Button(footer, text="Close", style="Accent.TButton", command=window.destroy).pack(side="right", padx=4)

    def open_awards_history_window(self):
        self.ensure_season_containers()
        window = tk.Toplevel(self.root)
        window.title("Awards History")
        window.geometry("640x560")
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="\U0001F3C6  AWARDS HISTORY", style="ScreenTitle.TLabel").pack(anchor="w", padx=14, pady=(10, 4))
        body = tk.Text(window, wrap="word", font=("Georgia", 11), bg=self.colors["cream"], fg=self.colors["text"], padx=16, pady=12)
        body.pack(fill="both", expand=True, padx=8, pady=8)
        body.tag_configure("year", font=("Georgia", 13, "bold"), foreground=self.colors["gold"])
        body.tag_configure("cat", font=("Georgia", 10, "bold"))
        if not self.awards_history:
            body.insert("end", "No awards have been handed out yet. Play through a full season (12 months) to crown the first winners.")
        for entry in self.awards_history:
            body.insert("end", f"\n{entry['year']}\n", "year")
            for award in entry["awards"]:
                body.insert("end", f"  {award['category']}: ", "cat")
                body.insert("end", f"{award['winner']} - {award['detail']}\n")
        body.config(state="disabled")
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(pady=(0, 8))

    # ---- Historical records ------------------------------------------------

    def open_records_ledger_window(self):
        """Browsable all-time records, built from the persistent world roster."""
        window = tk.Toplevel(self.root)
        window.title("MMA Warriors - Historical Records")
        window.geometry("1120x690")
        window.minsize(940, 560)
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="HISTORICAL RECORDS", style="ScreenTitle.TLabel").pack(anchor="w", padx=14, pady=(10, 0))
        ttk.Label(
            window,
            text="All active, free-agent, and retired careers in this save. Double-click a fighter to open their profile.",
            style="Inset.TLabel",
        ).pack(anchor="w", padx=14, pady=(0, 8))

        notebook = ttk.Notebook(window)
        notebook.pack(fill="both", expand=True, padx=10, pady=(0, 8))

        fighter_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        company_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        title_tab = ttk.Frame(notebook, style="Chrome.TFrame")
        notebook.add(fighter_tab, text="Fighter Records")
        notebook.add(company_tab, text="Promotion Records")
        notebook.add(title_tab, text="Title Lineage")

        fighter_controls = ttk.Frame(fighter_tab, style="Inset.TFrame")
        fighter_controls.pack(fill="x", padx=6, pady=6)
        ttk.Label(fighter_controls, text="Leaderboard", style="Inset.TLabel").pack(side="left", padx=(6, 3))
        record_category = tk.StringVar(value="Career Wins")
        categories = (
            "Career Wins", "Career Bouts", "Win Percentage (10+ bouts)", "ELO Rating",
            "Title Defenses", "Title Wins", "Career Significant Strikes", "Career Takedowns",
            "Career Knockdowns", "Career Submissions", "Awards Won", "Legacy Score",
        )
        ttk.Combobox(fighter_controls, textvariable=record_category, values=categories, state="readonly", width=30).pack(side="left", padx=(0, 8))
        ttk.Label(fighter_controls, text="Career totals include the stats tracked since the save began.", style="Inset.TLabel").pack(side="left", padx=4)
        fighter_tree = ttk.Treeview(
            fighter_tab,
            columns=("rank", "fighter", "company", "division", "record", "value", "status"),
            show="headings",
        )
        for column, heading, width, anchor in (
            ("rank", "#", 44, "center"), ("fighter", "Fighter", 205, "w"), ("company", "Current Home", 180, "w"),
            ("division", "Division", 120, "center"), ("record", "Record", 95, "center"), ("value", "Record Value", 150, "center"),
            ("status", "Status", 95, "center"),
        ):
            fighter_tree.heading(column, text=heading)
            fighter_tree.column(column, width=width, anchor=anchor)
        self.make_tree_sortable(fighter_tree)
        fighter_tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        def fighter_value(fighter, category):
            bouts = fighter.record_w + fighter.record_l + getattr(fighter, "record_d", 0)
            values = {
                "Career Wins": (fighter.record_w, str(fighter.record_w)),
                "Career Bouts": (bouts, str(bouts)),
                "Win Percentage (10+ bouts)": ((fighter.record_w / bouts * 100) if bouts >= 10 else -1, f"{fighter.record_w / bouts * 100:.1f}%" if bouts else "-"),
                "ELO Rating": (getattr(fighter, "elo_rating", 1500), str(getattr(fighter, "elo_rating", 1500))),
                "Title Defenses": (getattr(fighter, "title_defenses", 0), str(getattr(fighter, "title_defenses", 0))),
                "Title Wins": (getattr(fighter, "title_wins", 0), str(getattr(fighter, "title_wins", 0))),
                "Career Significant Strikes": (getattr(fighter, "career_sig_strikes", 0), f"{getattr(fighter, 'career_sig_strikes', 0):,}"),
                "Career Takedowns": (getattr(fighter, "career_takedowns", 0), str(getattr(fighter, "career_takedowns", 0))),
                "Career Knockdowns": (getattr(fighter, "career_knockdowns", 0), str(getattr(fighter, "career_knockdowns", 0))),
                "Career Submissions": (getattr(fighter, "career_submissions", 0), str(getattr(fighter, "career_submissions", 0))),
                "Awards Won": (getattr(fighter, "award_count", 0), str(getattr(fighter, "award_count", 0))),
                "Legacy Score": (self.compute_legacy_score(fighter), str(self.compute_legacy_score(fighter))),
            }
            return values[category]

        def refresh_fighter_records(*_args):
            fighter_tree.delete(*fighter_tree.get_children())
            seen = set()
            rows = []
            for company, fighter in self.all_database_fighters_with_companies():
                if fighter.name in seen:
                    continue
                seen.add(fighter.name)
                value, display = fighter_value(fighter, record_category.get())
                if value >= 0:
                    rows.append((value, fighter.name, company, fighter, display))
            for position, (_value, name, company, fighter, display) in enumerate(sorted(rows, key=lambda row: (row[0], row[3].record_w, row[3].elo_rating), reverse=True)[:100], 1):
                status = "Hall of Fame" if getattr(fighter, "hall_of_fame", False) else ("Retired" if getattr(fighter, "retired", False) else "Active")
                fighter_tree.insert("", "end", values=(position, name, company, f"{fighter.gender} {fighter.weight}", fighter.record, display, status))

        def open_selected_record(_event=None):
            selected = fighter_tree.selection()
            if not selected:
                return
            fighter = self.find_fighter_anywhere(fighter_tree.item(selected[0], "values")[1])
            if fighter:
                self.open_fighter_profile_window(fighter)

        record_category.trace_add("write", refresh_fighter_records)
        fighter_tree.bind("<Double-1>", open_selected_record)
        refresh_fighter_records()

        company_tree = ttk.Treeview(company_tab, columns=("rank", "promotion", "region", "events", "reputation", "legacy", "champions", "cash"), show="headings")
        for column, heading, width, anchor in (
            ("rank", "#", 44, "center"), ("promotion", "Promotion", 245, "w"), ("region", "Region", 110, "center"),
            ("events", "Events", 80, "center"), ("reputation", "Reputation", 95, "center"), ("legacy", "Legacy", 80, "center"),
            ("champions", "Champions", 90, "center"), ("cash", "Cash", 130, "e"),
        ):
            company_tree.heading(column, text=heading)
            company_tree.column(column, width=width, anchor=anchor)
        self.make_tree_sortable(company_tree)
        company_tree.pack(fill="both", expand=True, padx=6, pady=6)

        player_events = len([record for record in getattr(self, "result_records", []) if record.get("company") == self.player_company_name])
        company_rows = [(self.player_company_name, self.player_region, player_events, self.company_pop, getattr(self, "company_legacy_score", 0), self.belts, getattr(self, "cash", 0))]
        company_rows.extend((promo.name, promo.region, max(0, getattr(promo, "event_counter", 1) - 1), promo.reputation_score, getattr(promo, "legacy_score", 0), promo.belts or {}, promo.cash) for promo in self.promotions)
        for position, (name, region, events, reputation, legacy, belts, cash) in enumerate(sorted(company_rows, key=lambda row: (row[4], row[3], row[2]), reverse=True), 1):
            champion_count = len([holder for holder in (belts or {}).values() if holder])
            company_tree.insert("", "end", values=(position, name, region, events, f"{reputation}%", legacy, champion_count, f"${cash:,.0f}"))

        title_controls = ttk.Frame(title_tab, style="Inset.TFrame")
        title_controls.pack(fill="x", padx=6, pady=6)
        ttk.Label(title_controls, text="Promotion", style="Inset.TLabel").pack(side="left", padx=(6, 3))
        title_company = tk.StringVar(value="All Promotions")
        title_companies = ["All Promotions", self.player_company_name] + [promo.name for promo in self.promotions]
        ttk.Combobox(title_controls, textvariable=title_company, values=title_companies, state="readonly", width=30).pack(side="left", padx=(0, 8))
        ttk.Label(title_controls, text="Championship crowns, defences, interim reigns, and vacancies.", style="Inset.TLabel").pack(side="left", padx=4)
        title_tree = ttk.Treeview(title_tab, columns=("promotion", "division", "date", "action", "fighter", "note"), show="headings")
        for column, heading, width, anchor in (
            ("promotion", "Promotion", 185, "w"), ("division", "Division", 130, "center"), ("date", "Date", 120, "center"),
            ("action", "Record", 150, "w"), ("fighter", "Fighter", 190, "w"), ("note", "Context", 360, "w"),
        ):
            title_tree.heading(column, text=heading)
            title_tree.column(column, width=width, anchor=anchor)
        self.make_tree_sortable(title_tree)
        title_tree.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        def refresh_title_lineage(*_args):
            title_tree.delete(*title_tree.get_children())
            histories = [(self.player_company_name, getattr(self, "belt_history", {}))]
            histories.extend((promo.name, promo.belt_history or {}) for promo in self.promotions)
            for company, history in histories:
                if title_company.get() != "All Promotions" and company != title_company.get():
                    continue
                for division, entries in (history or {}).items():
                    for entry in entries or []:
                        title_tree.insert("", "end", values=(company, division, entry.get("date", ""), entry.get("action", ""), entry.get("fighter", ""), entry.get("note", "")))

        title_company.trace_add("write", refresh_title_lineage)
        title_tree.bind("<Double-1>", lambda _event: self.open_fighter_profile_window(fighter) if (selected := title_tree.selection()) and (fighter := self.find_fighter_anywhere(title_tree.item(selected[0], "values")[4])) else None)
        refresh_title_lineage()
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(anchor="e", padx=12, pady=(0, 10))

    def ensure_historical_records(self):
        records = getattr(self, "historical_records", None) or {}
        records.setdefault("world", {})
        records.setdefault("promotion", {})
        records.setdefault("event", {})
        records.setdefault("initialized", False)
        # Older in-memory record updates could retain the current history list
        # inside a prior entry, creating an unsaveable circular reference.  Keep
        # history deliberately flat: previous marks never need their own nested
        # copy of the entire record book.
        for group in ("world", "promotion", "event"):
            for entry in records[group].values():
                cleaned = []
                for prior in list(entry.get("history", []) or []):
                    if isinstance(prior, dict) and prior is not entry:
                        cleaned.append({key: value for key, value in prior.items() if key != "history"})
                entry["history"] = cleaned[:30]
        self.historical_records = records
        return records

    def update_historical_record(self, group, key, value, holders, context):
        """Keep the active holder plus a permanent list of superseded records."""
        records = self.ensure_historical_records()
        bucket = records[group]
        old = bucket.get(key)
        if not old or value > old.get("value", -1):
            history = list((old or {}).get("history", []) or [])
            if old:
                prior = {field: detail for field, detail in old.items() if field != "history"}
                prior["still_stands"] = False
                prior["ended_month"] = self.month
                history.insert(0, prior)
            entry = {"value": value, "holders": list(holders), "date": context.get("date", f"Month {self.month} Week {self.week}"), "event": context.get("event", ""), "promotion": context.get("promotion", ""), "opponent": context.get("opponent", ""), "still_stands": True, "history": history[:30]}
            bucket[key] = entry
            if records["initialized"]:
                verb = "holds" if len(holders) == 1 else "hold"
                headline = f"RECORD BROKEN: {', '.join(holders)} now {verb} {key} ({value})."
                self.news.insert(0, headline)
                self.record_world_story("Record", headline, f"{context.get('promotion', 'World')} — {context.get('event', 'career record')}", [context.get("promotion", "")], holders, importance=3)
        elif value == old.get("value"):
            added = [holder for holder in holders if holder not in old.get("holders", [])]
            if added:
                old["holders"] = old.get("holders", []) + added
                old["date"] = context.get("date", old.get("date", ""))
                old["event"] = context.get("event", old.get("event", ""))

    def refresh_historical_records(self):
        """Refresh official world, promotion, and event records after completed cards."""
        records = self.ensure_historical_records()
        seen, fighters = set(), []
        for company, fighter in self.all_database_fighters_with_companies():
            if fighter.name not in seen:
                seen.add(fighter.name); fighters.append((company, fighter))
        if not fighters:
            return
        metrics = (
            ("Most Career Wins", lambda fighter: fighter.record_w),
            ("Most Career Finishes", lambda fighter: getattr(fighter, "career_finishes", 0)),
            ("Most Career Knockouts", lambda fighter: getattr(fighter, "career_knockouts", 0)),
            ("Most Career Submissions", lambda fighter: getattr(fighter, "career_submissions", 0)),
            ("Most Title Defenses", lambda fighter: getattr(fighter, "title_defenses", 0)),
            ("Most Championship Wins", lambda fighter: getattr(fighter, "title_wins", 0)),
            ("Longest Win Streak", lambda fighter: getattr(fighter, "career_win_streak", 0)),
        )
        for key, metric in metrics:
            top = max(metric(fighter) for _company, fighter in fighters)
            holders = [fighter.name for _company, fighter in fighters if metric(fighter) == top]
            self.update_historical_record("world", key, top, holders, {"promotion": "World"})
        for promo_name in [self.player_company_name] + [promo.name for promo in self.promotions]:
            roster = self.roster if promo_name == self.player_company_name else next((promo.roster for promo in self.promotions if promo.name == promo_name), [])
            if not roster:
                continue
            defenses = max(getattr(fighter, "title_defenses", 0) for fighter in roster)
            wins = max(fighter.record_w for fighter in roster)
            self.update_historical_record("promotion", f"{promo_name}: Most Title Defenses", defenses, [fighter.name for fighter in roster if getattr(fighter, "title_defenses", 0) == defenses], {"promotion": promo_name})
            self.update_historical_record("promotion", f"{promo_name}: Most Wins", wins, [fighter.name for fighter in roster if fighter.record_w == wins], {"promotion": promo_name})
        for record in getattr(self, "result_records", []):
            finance = record.get("finance", {}) or {}
            context = {"date": record.get("date", ""), "event": record.get("event", ""), "promotion": record.get("company", "")}
            gate = int(finance.get("ticket_revenue", 0) or 0)
            fights = int(record.get("fights", 0) or 0)
            logs = record.get("fight_logs", []) or []
            finishes = sum(1 for row in logs if any(token in str(row.get("result", "")) for token in ("KO", "TKO", "Submission")))
            knockouts = sum(1 for row in logs if "KO" in str(row.get("result", "")) or "TKO" in str(row.get("result", "")))
            title_fights = sum(1 for row in logs if "TITLE" in str(row.get("label", "")).upper())
            for key, value in (("Highest Gate", gate), ("Most Bouts", fights), ("Most Finishes", finishes), ("Most Knockouts", knockouts), ("Most Title Fights", title_fights)):
                self.update_historical_record("event", key, value, [record.get("event", "Event")], context)
        records["initialized"] = True

    def open_record_book_window(self):
        self.refresh_historical_records()
        window = tk.Toplevel(self.root)
        window.title("MMA Warriors - Official Record Book")
        window.geometry("980x630")
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="OFFICIAL RECORD BOOK", style="ScreenTitle.TLabel").pack(anchor="w", padx=12, pady=(10, 2))
        ttk.Label(window, text="Current record holders and every superseded mark saved in this world.", style="Inset.TLabel").pack(anchor="w", padx=12, pady=(0, 8))
        tree = ttk.Treeview(window, columns=("scope", "record", "value", "holders", "date", "event", "promotion"), show="headings")
        for column, label, width in (("scope", "Scope", 100), ("record", "Record", 230), ("value", "Mark", 80), ("holders", "Current Holder(s)", 215), ("date", "Set", 110), ("event", "Event", 155), ("promotion", "Promotion", 160)):
            tree.heading(column, text=label); tree.column(column, width=width, anchor="w")
        tree.pack(fill="both", expand=True, padx=8, pady=8)
        detail = tk.Text(window, height=7, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        detail.pack(fill="x", padx=8, pady=(0, 8)); detail.config(state="disabled")
        rows = []
        for scope in ("world", "promotion", "event"):
            for key, entry in self.historical_records.get(scope, {}).items():
                rows.append((scope.title(), key, entry))
        for index, (scope, key, entry) in enumerate(sorted(rows, key=lambda row: (row[0], row[1]))):
            tree.insert("", "end", iid=str(index), values=(scope, key, entry.get("value", 0), ", ".join(entry.get("holders", [])), entry.get("date", ""), entry.get("event", ""), entry.get("promotion", "")))
        def show_history(_event=None):
            selected = tree.selection(); detail.config(state="normal"); detail.delete("1.0", "end")
            if selected:
                scope, key, entry = rows[int(selected[0])]
                history = entry.get("history", [])
                detail.insert("end", f"{scope.upper()} — {key}\nCurrent: {entry.get('value', 0)} — {', '.join(entry.get('holders', []))}\nSet: {entry.get('date', '')} | {entry.get('event', '')}\n\nPrevious holders:\n")
                detail.insert("end", "\n".join(f"{old.get('value', 0)} — {', '.join(old.get('holders', []))} ({old.get('date', '')}; {old.get('event', '') or old.get('promotion', '')})" for old in history) or "No previous holder recorded.")
            detail.config(state="disabled")
        tree.bind("<<TreeviewSelect>>", show_history)
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(anchor="e", padx=10, pady=(0, 10))

    # ---- Hall of Fame ------------------------------------------------------

    def compute_legacy_score(self, fighter):
        """Career legacy score used to decide Hall-of-Fame induction."""
        bouts = fighter.record_w + fighter.record_l + getattr(fighter, "record_d", 0)
        win_pct = fighter.record_w / max(1, bouts)
        peak = max(fighter.annual_overalls.values()) if fighter.annual_overalls else fighter.overall
        awards_won = sum(1 for entry in (fighter.fight_history or []) if "of the Year" in str(entry))
        score = (fighter.record_w * 6
                 + win_pct * 60
                 + getattr(fighter, "title_shots", 0) * 42
                 + getattr(fighter, "title_wins", 0) * 68
                 + getattr(fighter, "title_defenses", 0) * 34
                 + peak * 1.6
                 + fighter.popularity * 0.8
                 + getattr(fighter, "career_knockdowns", 0) * 2
                 + awards_won * 55
                 + getattr(fighter, "award_count", 0) * 35
                 + len(getattr(fighter, "rivalry_history", []) or []) * 4)
        return round(score)

    def consider_hall_of_fame(self, fighter):
        """Called on retirement: score the career and enshrine the greats."""
        fighter.legacy_score = self.compute_legacy_score(fighter)
        # A Hall of Fame should be selective over a century of generated careers.
        # Title shots are a useful legacy signal, but being a perennial contender
        # alone is not a sufficient reason to be inducted.
        bouts = fighter.record_w + fighter.record_l + getattr(fighter, "record_d", 0)
        peak = max(fighter.annual_overalls.values()) if fighter.annual_overalls else fighter.overall
        inducted = bouts >= 25 and (
            getattr(fighter, "title_defenses", 0) >= 8
            or getattr(fighter, "title_wins", 0) >= 4
            or getattr(fighter, "award_count", 0) >= 4
            or (fighter.legacy_score >= 1050 and peak >= 90 and fighter.record_w / max(1, bouts) >= 0.7)
        )
        if inducted and not getattr(fighter, "hall_of_fame", False):
            fighter.hall_of_fame = True
            self.news.insert(0, f"HALL OF FAME: {fighter.name} retires and is enshrined (legacy {fighter.legacy_score}, {fighter.record}).")
            self.inbox.append({
                "subject": f"Hall of Fame Induction - {fighter.name}",
                "body": f"{fighter.name} has retired with a {fighter.record} record and a legacy score of {fighter.legacy_score}, earning enshrinement in the MMA Warriors Hall of Fame.",
                "type": "Awards", "resolved": False,
            })
        return inducted

    def hall_of_famers(self):
        everyone = list(getattr(self, "retired_fighters", []))
        for source in (getattr(self, "roster", []), getattr(self, "free_agents", [])):
            everyone.extend(source)
        for promo in getattr(self, "promotions", []):
            everyone.extend(promo.roster)
        seen = set()
        hofers = []
        for fighter in everyone:
            if getattr(fighter, "hall_of_fame", False) and fighter.name not in seen:
                seen.add(fighter.name)
                hofers.append(fighter)
        hofers.sort(key=lambda f: getattr(f, "legacy_score", 0), reverse=True)
        return hofers

    def open_hall_of_fame_window(self):
        window = tk.Toplevel(self.root)
        window.title("Hall of Fame")
        window.geometry("680x580")
        window.configure(bg=self.colors["chrome"])
        ttk.Label(window, text="\U0001F396  MMA WARRIORS HALL OF FAME", style="ScreenTitle.TLabel").pack(anchor="w", padx=14, pady=(10, 4))
        body = tk.Text(window, wrap="word", font=("Georgia", 11), bg=self.colors["cream"], fg=self.colors["text"], padx=16, pady=12)
        body.pack(fill="both", expand=True, padx=8, pady=8)
        body.tag_configure("name", font=("Georgia", 14, "bold"), foreground=self.colors["gold"])
        body.tag_configure("detail", font=("Georgia", 10), foreground=self.colors["text"])
        hofers = self.hall_of_famers()
        if not hofers:
            body.insert("end", "The Hall of Fame is empty. Legendary fighters are enshrined when they retire with a great career.")
        for fighter in hofers:
            peak = max(fighter.annual_overalls.values()) if fighter.annual_overalls else fighter.overall
            awards_won = sum(1 for entry in (fighter.fight_history or []) if "of the Year" in str(entry))
            body.insert("end", f"\n{fighter.name}\n", "name")
            body.insert("end", f"  {fighter.gender} {fighter.weight} | Record {fighter.record} | Peak overall {peak} | Legacy {getattr(fighter, 'legacy_score', 0)}\n", "detail")
            extras = []
            if awards_won:
                extras.append(f"{awards_won} year-end award(s)")
            if getattr(fighter, "career_knockdowns", 0):
                extras.append(f"{fighter.career_knockdowns} knockdowns scored")
            if extras:
                body.insert("end", f"  {' | '.join(extras)}\n", "detail")
        body.config(state="disabled")
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(pady=(0, 8))
