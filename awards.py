import json
import random
import re
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

    # Long-term company milestones intentionally reuse the achievement ledger.
    # Progress is separate because it is live and may fall; an unlock is permanent.
    def company_milestone_registry(self):
        return (
            {"id": "financially_secure", "name": "Financially Secure", "cash": 1_000_000, "months": 6,
             "stability": 45, "popularity": 0, "safety": 0, "events": 0,
             "description": "Sustain $1M while operating positively for six months.", "unlock": "Company project and special-format invitations."},
            {"id": "national_power", "name": "National Power", "cash": 5_000_000, "months": 12,
             "stability": 55, "popularity": 65, "safety": 0, "events": 15,
             "description": "Build national recognition and a durable $5M operation.", "unlock": "National Stadium record-attempt invitations."},
            {"id": "major_organisation", "name": "Major Organisation", "cash": 15_000_000, "months": 12,
             "stability": 65, "popularity": 75, "safety": 0, "events": 30,
             "description": "Prove a $15M company can consistently deliver major shows.", "unlock": "Mega Stadium and historic-venue opportunities."},
            {"id": "combat_sports_institution", "name": "Combat Sports Institution", "cash": 40_000_000, "months": 12,
             "stability": 72, "popularity": 84, "safety": 78, "events": 60,
             "description": "Combine scale with an excellent safety and standing record.", "unlock": "Ceremonial capital showcases."},
            {"id": "legacy_empire", "name": "Legacy Empire", "cash": 100_000_000, "months": 24,
             "stability": 80, "popularity": 90, "safety": 85, "events": 100,
             "description": "Reach the once-in-a-save peak of commercial and sporting credibility.", "unlock": "White House Fight Night invitation."},
        )

    def company_unlocked_milestone_ids(self):
        company = getattr(self, "player_company_name", "")
        return {
            entry.get("id") for entry in getattr(self, "achievement_log", [])
            if entry.get("scope") == "Promotion" and entry.get("target") == company
            and entry.get("id") in {row["id"] for row in self.company_milestone_registry()}
        }

    def company_event_count(self):
        return sum(1 for record in getattr(self, "result_records", []) if record.get("company") == self.player_company_name)

    def update_company_safety_and_standing(self):
        """Derived welfare/reliability score; never a hidden random punishment."""
        prior = int(getattr(self, "company_safety", 60) or 60)
        serious = sum(1 for fighter in getattr(self, "roster", []) if getattr(fighter, "serious_injury", ""))
        injured = sum(1 for fighter in getattr(self, "roster", []) if getattr(fighter, "injured", 0) >= 4)
        testing = {"None": -7, "Standard": 0, "Strict": 5}.get(getattr(self, "rules", {}).get("drug_testing", "Standard"), 0)
        failures = sum(1 for row in getattr(self, "super_event_history", [])[-12:] if row.get("outcome") in ("Cancelled", "Failed"))
        medical_base = int((getattr(self, "finance", {}) or {}).get("medical_base", 0) or 0)
        medical = 3 if medical_base >= 25_000 else 1 if medical_base >= 12_000 else -2
        target = 67 + testing + medical - serious * 5 - injured * 2 - failures * 4
        self.company_safety = max(0, min(100, round(prior * 0.72 + target * 0.28)))
        return self.company_safety

    def company_valuation(self):
        return round(self.company_power_score(self.player_company_name, self.roster, self.company_pop, self.company_stability, self.cash))

    def process_company_milestones_and_super_events(self):
        """Monthly player-side milestone, safety, offer-expiry and invitation pass."""
        if getattr(self, "spectator_mode", False):
            return
        self.ensure_season_containers()
        self.update_company_safety_and_standing()
        progress = getattr(self, "company_milestone_progress", {}) or {}
        prior_cash = int(progress.get("_last_cash", self.cash) or self.cash)
        positive_month = self.cash >= prior_cash
        progress["_last_cash"] = int(self.cash)
        events = self.company_event_count()
        for rule in self.company_milestone_registry():
            row = progress.setdefault(rule["id"], {"months": 0})
            qualifies = (
                self.cash >= rule["cash"] and positive_month and self.company_stability >= rule["stability"]
                and self.company_pop >= rule["popularity"] and self.company_safety >= rule["safety"] and events >= rule["events"]
            )
            row["months"] = min(rule["months"], int(row.get("months", 0) or 0) + 1) if qualifies else 0
            row["qualifies"] = qualifies
            if row["months"] >= rule["months"]:
                unlocked = self.unlock_achievement("Promotion", self.player_company_name, self.player_company_name, rule["id"], rule["name"], rule["description"] + " Unlock: " + rule["unlock"])
                if unlocked:
                    self.record_world_story("Company Milestone", f"{self.player_company_name} becomes {rule['name']}", rule["unlock"], [self.player_company_name], importance=4)
        self.company_milestone_progress = progress
        self.expire_super_event_offers()
        self.roll_super_event_opportunity()

    def expire_super_event_offers(self):
        active = []
        for offer in list(getattr(self, "super_event_offers", []) or []):
            if offer.get("status") == "Offered" and self.month > int(offer.get("deadline_month", self.month)):
                offer["status"] = "Expired"
                self.company_safety = max(0, self.company_safety - 2)
                self.news.insert(0, f"Super-event invitation expired: {offer.get('name', 'Opportunity')}. The industry questions the missed window.")
            if offer.get("status") in ("Offered", "Planning", "Scheduled"):
                active.append(offer)
        self.super_event_offers = active[-12:]

    def super_event_templates(self):
        return {
            "financially_secure": {"kind": "Special Format", "name": "Grand Prix Showcase", "venue": "Casino Ballroom", "region": "USA", "city": "Las Vegas", "deposit": 45_000, "setup": 35_000, "security": 15_000, "reserve": 300_000, "min_fights": 6, "min_titles": 0, "min_stars": 1, "revenue": 1.12, "reward": 3},
            "national_power": {"kind": "Record Attempt", "name": "National Stadium Record Attempt", "venue": "National Stadium", "region": "USA", "city": "Las Vegas", "deposit": 180_000, "setup": 320_000, "security": 120_000, "reserve": 1_000_000, "min_fights": 8, "min_titles": 2, "min_stars": 2, "revenue": 1.32, "reward": 5},
            "major_organisation": {"kind": "Historic Venue", "name": "Historic Amphitheatre Championship", "venue": "Historic Amphitheatre", "region": "Europe", "city": "London", "deposit": 320_000, "setup": 480_000, "security": 170_000, "reserve": 2_500_000, "min_fights": 8, "min_titles": 2, "min_stars": 3, "revenue": 1.42, "reward": 7},
            "combat_sports_institution": {"kind": "Ceremonial", "name": "Ceremonial Capital Showcase", "venue": "Ceremonial Capital Grounds", "region": "USA", "city": "Washington", "deposit": 500_000, "setup": 900_000, "security": 450_000, "reserve": 6_000_000, "min_fights": 9, "min_titles": 3, "min_stars": 3, "revenue": 1.26, "reward": 9},
            "legacy_empire": {"kind": "Once-per-save Ceremonial", "name": "White House Fight Night", "venue": "White House South Lawn", "region": "USA", "city": "Washington", "deposit": 1_000_000, "setup": 3_500_000, "security": 2_500_000, "reserve": 40_000_000, "min_fights": 10, "min_titles": 3, "min_stars": 4, "revenue": 1.12, "reward": 14, "once": True},
        }

    def roll_super_event_opportunity(self, force=False):
        if getattr(self, "super_event_project", None) or any(offer.get("status") == "Offered" for offer in getattr(self, "super_event_offers", [])):
            return None
        unlocked = self.company_unlocked_milestone_ids()
        eligible = [rule["id"] for rule in self.company_milestone_registry() if rule["id"] in unlocked]
        if not eligible or (not force and random.random() >= 0.22):
            return None
        milestone_id = eligible[-1]
        template = dict(self.super_event_templates()[milestone_id])
        if template.get("once") and any(row.get("milestone") == milestone_id for row in getattr(self, "super_event_history", [])):
            return None
        offer = {
            "id": f"SE-{self.month}-{len(getattr(self, 'super_event_history', [])) + len(getattr(self, 'super_event_offers', [])) + 1}",
            "milestone": milestone_id, "status": "Offered", "earliest_month": self.month + 2,
            "deadline_month": self.month + 8, "issued_month": self.month, **template,
        }
        self.super_event_offers.insert(0, offer)
        headline = f"Super-event invitation: {offer['name']}"
        body = f"{offer['kind']} opportunity at {offer['venue']}. Accept by {self.format_game_date(offer['deadline_month'], 1)}; projected setup ${offer['deposit'] + offer['setup'] + offer['security']:,}."
        self.inbox.append({"subject": headline, "body": body, "type": "Super Events", "fighter": "", "resolved": False, "super_event_id": offer["id"]})
        self.news.insert(0, headline)
        self.record_world_story("Super Event", headline, body, [self.player_company_name], importance=4)
        return offer

    def super_event_readiness(self, offer):
        offer = offer or {}
        fights = list(getattr(self, "booked", []) or [])
        participants = [self.get_fighter(name) for fight in fights for name in fight.get("fighters", []) if name != "TBA" and self.get_fighter(name)]
        unique = list({fighter.fighter_id: fighter for fighter in participants}.values())
        title_bouts = sum(1 for fight in fights if fight.get("title"))
        star_count = sum(1 for fighter in unique if fighter.popularity >= 55 or fighter.star_quality >= 72)
        financial = min(100, round(self.cash / max(1, int(offer.get("reserve", 1))) * 100))
        prestige = min(100, self.company_pop)
        card = min(100, round((len(fights) / max(1, offer.get("min_fights", 1)) * 45) + (title_bouts / max(1, offer.get("min_titles", 1)) * 30) + (star_count / max(1, offer.get("min_stars", 1)) * 25)))
        safety = min(100, self.company_safety)
        venue = 100 if offer.get("venue") in self.available_event_venues() else 0
        readiness = round(financial * .25 + prestige * .20 + card * .20 + min(100, star_count * 34) * .15 + safety * .10 + venue * .10)
        return {"score": readiness, "financial": financial, "prestige": prestige, "card": card, "star_power": min(100, star_count * 34), "safety": safety, "venue": venue, "title_bouts": title_bouts, "stars": star_count, "fights": len(fights)}

    def super_event_novelty(self, offer):
        """Spectacles remain useful, but repeated versions stop printing hype."""
        kind = str((offer or {}).get("kind", ""))
        recent = [row for row in getattr(self, "super_event_history", []) if row.get("kind") == kind and self.month - int(row.get("month", 0) or 0) <= 48]
        return (1.0, 0.8, 0.6, 0.4)[min(3, len(recent))]

    def validate_super_event_card(self, offer, fights=None):
        fights = list(fights if fights is not None else getattr(self, "booked", []))
        participants = [self.get_fighter(name) for fight in fights for name in fight.get("fighters", []) if name != "TBA" and self.get_fighter(name)]
        stars = len({fighter.fighter_id for fighter in participants if fighter.popularity >= 55 or fighter.star_quality >= 72})
        titles = sum(1 for fight in fights if fight.get("title"))
        missing = []
        if len(fights) < int(offer.get("min_fights", 1)): missing.append(f"{offer['min_fights']} completed fights")
        if titles < int(offer.get("min_titles", 0)): missing.append(f"{offer['min_titles']} title fights")
        if stars < int(offer.get("min_stars", 0)): missing.append(f"{offer['min_stars']} recognisable stars")
        return missing

    def accept_super_event_offer(self, offer):
        if offer.get("status") != "Offered":
            return False, "That invitation is no longer open."
        total_commitment = int(offer.get("deposit", 0)) + int(offer.get("setup", 0)) + int(offer.get("security", 0))
        if self.cash - total_commitment < int(offer.get("reserve", 0)):
            return False, f"Approval requires ${offer['reserve']:,} to remain after the projected ${total_commitment:,} commitment."
        self.cash -= int(offer.get("deposit", 0))
        self.record_finance_transaction(f"Super-event approval: {offer['name']}", costs=int(offer.get("deposit", 0)))
        offer["status"] = "Planning"
        offer["accepted_month"] = self.month
        offer["remaining_setup_cost"] = int(offer.get("setup", 0))
        offer["novelty"] = self.super_event_novelty(offer)
        self.super_event_project = offer
        self.event_name.set(f"{self.player_company_name}: {offer['name']}")
        self.venue.set(offer["venue"]); self.event_region.set(offer["region"]); self.event_city.set(offer["city"])
        earliest = int(offer.get("earliest_month", self.month + 2))
        self.set_booking_date(earliest, 2)
        if hasattr(self, "event_venue_box"):
            self.event_venue_box.configure(values=self.available_event_venues())
        self.news.insert(0, f"Approved: {offer['name']}. Build the card and clear approval before {self.format_game_date(offer['deadline_month'], 1)}.")
        return True, "Project approved. The booking screen has been prepared."

    def complete_super_event(self, event, package):
        offer = dict(event.get("super_event", {}) or {})
        if not offer:
            return
        finance = package.get("finance", {}) or {}
        attendance_ratio = finance.get("attendance", 0) / max(1, finance.get("venue_capacity", 1))
        success = package.get("profit", 0) >= 0 and attendance_ratio >= .45 and package.get("average_excitement", 0) >= 43
        outcome = "Success" if success else "Failed"
        pop_delta = int(offer.get("reward", 3)) if success else -max(2, int(offer.get("reward", 3)) // 2)
        stability_delta = max(1, int(offer.get("reward", 3)) // 2) if success else -3
        self.company_pop = max(1, min(100, self.company_pop + pop_delta))
        self.company_stability = max(1, min(100, self.company_stability + stability_delta))
        self.company_safety = max(0, min(100, self.company_safety + (2 if success else -4)))
        history = {"id": offer.get("id"), "name": offer.get("name"), "kind": offer.get("kind"), "milestone": offer.get("milestone"), "month": self.month, "outcome": outcome, "attendance": finance.get("attendance", 0), "profit": package.get("profit", 0), "event": package.get("event_name", "")}
        self.super_event_history.insert(0, history)
        self.super_event_history = self.super_event_history[:60]
        offer["status"] = outcome
        self.super_event_offers = [row for row in self.super_event_offers if row.get("id") != offer.get("id")]
        self.super_event_project = None
        headline = f"{offer.get('name', 'Super Event')} {outcome.lower()}: {package.get('event_name', '')}"
        detail = f"Attendance {finance.get('attendance', 0):,}; profit ${package.get('profit', 0):,}; popularity {pop_delta:+}; stability {stability_delta:+}."
        self.news.insert(0, headline)
        self.record_world_story("Super Event", headline, detail, [self.player_company_name], importance=5 if success else 3)

    def open_company_milestones_window(self):
        self.update_company_safety_and_standing()
        window = tk.Toplevel(self.root)
        window.title("MMA Warriors - Company Milestones & Super Events")
        window.geometry("1120x700")
        window.minsize(900, 560)
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame"); header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="COMPANY MILESTONES & SUPER EVENTS", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=7)
        stats = ttk.Label(header, style="Chrome.TLabel"); stats.pack(side="right", padx=10)
        body = ttk.Panedwindow(window, orient="horizontal"); body.pack(fill="both", expand=True, padx=8, pady=8)
        left = ttk.Frame(body, style="Inset.TFrame"); right = ttk.Frame(body, style="Inset.TFrame"); body.add(left, weight=1); body.add(right, weight=1)
        ttk.Label(left, text="MILESTONE PATH", style="Section.TLabel").pack(fill="x")
        milestone_tree = ttk.Treeview(left, columns=("status", "progress", "cash", "unlock"), show="headings", height=11)
        for col, label, width in (("status", "Status", 95), ("progress", "Sustained", 90), ("cash", "Cash Gate", 105), ("unlock", "Unlock", 300)):
            milestone_tree.heading(col, text=label); milestone_tree.column(col, width=width, anchor="w")
        milestone_tree.pack(fill="both", expand=True, padx=6, pady=6)
        ttk.Label(right, text="SUPER-EVENT OPPORTUNITIES", style="Section.TLabel").pack(fill="x")
        offer_tree = ttk.Treeview(right, columns=("kind", "venue", "deadline", "status", "ready"), show="headings", height=11)
        for col, label, width in (("kind", "Kind", 115), ("venue", "Venue", 165), ("deadline", "Decision By", 110), ("status", "Status", 85), ("ready", "Readiness", 80)):
            offer_tree.heading(col, text=label); offer_tree.column(col, width=width, anchor="w")
        offer_tree.pack(fill="both", expand=True, padx=6, pady=6)
        detail = tk.Text(window, height=8, wrap="word", bg=self.colors["panel_dark"], fg=self.colors["text"], font=("Tahoma", 9), padx=10, pady=8)
        detail.pack(fill="x", padx=8, pady=(0, 6)); detail.config(state="disabled")
        footer = ttk.Frame(window, style="Inset.TFrame"); footer.pack(fill="x", padx=8, pady=(0, 8))
        offers = []
        def render():
            stats.config(text=f"Cash ${self.cash:,.0f}  |  Valuation {self.company_valuation():,}  |  Safety & Standing {self.company_safety}/100")
            milestone_tree.delete(*milestone_tree.get_children())
            progress = getattr(self, "company_milestone_progress", {}) or {}
            unlocked = self.company_unlocked_milestone_ids()
            for rule in self.company_milestone_registry():
                state = progress.get(rule["id"], {})
                status = "UNLOCKED" if rule["id"] in unlocked else "Building"
                milestone_tree.insert("", "end", iid=rule["id"], values=(status, f"{state.get('months', 0)}/{rule['months']} mo", f"${rule['cash']:,}", rule["unlock"]))
            offers[:] = list(getattr(self, "super_event_offers", []) or [])
            offer_tree.delete(*offer_tree.get_children())
            for index, offer in enumerate(offers):
                ready = self.super_event_readiness(offer)["score"]
                offer_tree.insert("", "end", iid=str(index), values=(offer.get("kind", ""), offer.get("venue", ""), self.format_game_date(offer.get("deadline_month", self.month), 1), offer.get("status", ""), f"{ready}/100"))
        def selected_offer():
            selected = offer_tree.selection()
            return offers[int(selected[0])] if selected else None
        def show_offer(_event=None):
            offer = selected_offer()
            if not offer: return
            read = self.super_event_readiness(offer)
            missing = self.validate_super_event_card(offer)
            text = (f"{offer['name']}\n\n{offer['kind']} at {offer['venue']}\n"
                    f"Approval deposit ${offer['deposit']:,}; remaining setup/security ${offer['setup'] + offer['security']:,}; reserve ${offer['reserve']:,}.\n"
                    f"Spectacle novelty: {int(self.super_event_novelty(offer) * 100)}% commercial impact.\n"
                    f"Card approval: {offer['min_fights']} fights, {offer['min_titles']} title fights, {offer['min_stars']} recognisable stars.\n\n"
                    f"READINESS {read['score']}/100\nFinancial {read['financial']} | Prestige {read['prestige']} | Card {read['card']} | Star power {read['star_power']} | Safety {read['safety']} | Venue {read['venue']}\n"
                    + ("Current card still needs: " + ", ".join(missing) if missing else "Current card meets the project approval checklist."))
            detail.config(state="normal"); detail.delete("1.0", "end"); detail.insert("end", text); detail.config(state="disabled")
        def accept():
            offer = selected_offer()
            if not offer: return
            ok, message = self.accept_super_event_offer(offer)
            if ok:
                self.select_tab("booking"); window.destroy()
            else:
                messagebox.showwarning("Project cannot be approved", message, parent=window)
        ttk.Button(footer, text="Accept Selected Project", style="Accent.TButton", command=accept).pack(side="left", padx=4, pady=4)
        ttk.Button(footer, text="Refresh", command=render).pack(side="left", padx=4, pady=4)
        ttk.Button(footer, text="Close", command=window.destroy).pack(side="right", padx=4, pady=4)
        offer_tree.bind("<<TreeviewSelect>>", show_offer); render()

    def open_achievements_window(self):
        self.ensure_season_containers()
        window = tk.Toplevel(self.root)
        window.title("Achievements & Milestones")
        window.geometry("980x620")
        window.configure(bg=self.colors["chrome"])
        header = ttk.Frame(window, style="Header.TFrame"); header.pack(fill="x", padx=8, pady=(8, 0))
        ttk.Label(header, text="ACHIEVEMENTS & MILESTONES", style="ScreenTitle.TLabel").pack(side="left", padx=10, pady=6)
        ttk.Button(header, text="Company Milestones & Super Events", command=self.open_company_milestones_window).pack(side="right", padx=8, pady=4)
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
                detail.insert("end", f"{entry['title']}\n{entry['target']} — {entry['description']}\nUnlocked {self.format_game_date(entry.get('month', 1), entry.get('week', 1))}.")
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
            if not isinstance(bucket, dict):
                bucket = {"fighters": {}, "fights": [], "companies": {}}
                self.season_stats[self.year_label()] = bucket
            bucket["fighters"] = bucket.get("fighters") if isinstance(bucket.get("fighters"), dict) else {}
            bucket["fights"] = bucket.get("fights") if isinstance(bucket.get("fights"), list) else []
            bucket["companies"] = bucket.get("companies") if isinstance(bucket.get("companies"), dict) else {}
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
        except Exception as exc:
            # Awards must not invalidate an official result, but a visible notice
            # prevents malformed seasonal state from failing silently.
            self.inbox.append({
                "subject": "Awards Tracking Error",
                "body": f"Seasonal award tracking could not record a result: {type(exc).__name__}: {exc}",
                "type": "Awards",
                "resolved": False,
            })

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

    @staticmethod
    def _parse_belt_month(date_value):
        """Pull the save-stable month index out of a 'Month N Week N' stamp."""
        match = re.search(r"Month\s+(\d+)", str(date_value or ""))
        return int(match.group(1)) if match else None

    def belt_history_date_label(self, entry):
        """Render a title event's date, including the day once one was recorded.

        Entries written before cards carried a weekday have no day, so they
        keep their original month-and-week stamp rather than being given a
        misleading one.
        """
        text = self.format_game_date_text((entry or {}).get("date", ""))
        day = (entry or {}).get("day")
        if day is None:
            return text
        return f"{text} ({self.day_name(day, short=False)})"

    def format_month_span(self, months):
        """Render a month count as a compact 'Ny Nmo' reign length."""
        if months is None:
            return "-"
        months = max(0, int(months))
        if months < 1:
            return "<1 mo"
        years, remainder = divmod(months, 12)
        parts = []
        if years:
            parts.append(f"{years}y")
        if remainder:
            parts.append(f"{remainder}mo")
        return " ".join(parts) if parts else "0mo"

    def title_reign_history(self, entries):
        """Reconstruct ordered undisputed reigns from a division's belt history.

        Returns reigns oldest-first, each with fighter, start/end month, defense
        count, and how the reign ended. Interim events are ignored here; they
        are surfaced separately in the detail timeline so the main lineage stays
        the clean undisputed line of succession.
        """
        crown_actions = ("Champion Crowned", "Inaugural Champion", "Inaugural Champion Appointed")
        end_actions = ("Vacated", "Division Closed")
        reigns = []
        current = None
        for entry in reversed(list(entries or [])):
            action = str(entry.get("action", ""))
            month = self._parse_belt_month(entry.get("date"))
            if action in crown_actions:
                if current is not None:
                    current["end_month"] = month
                    current["end_action"] = "Dethroned"
                    reigns.append(current)
                current = {
                    "fighter": entry.get("fighter", ""), "start_month": month,
                    "start_date": entry.get("date", ""), "defenses": 0,
                    "end_month": None, "end_action": "", "note": entry.get("note", ""),
                }
            elif action == "Title Defense" and current is not None:
                current["defenses"] += 1
            elif action in end_actions and current is not None:
                current["end_month"] = month
                current["end_action"] = action
                reigns.append(current)
                current = None
        if current is not None:
            reigns.append(current)
        return reigns

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
        ttk.Label(fighter_controls, text="Sport", style="Inset.TLabel").pack(side="left", padx=(6, 3))
        record_sport = tk.StringVar(value="MMA")
        sport_values = ["All Sports"] + sorted({
            self.fighter_career_sport(fighter)
            for _company, fighter in self.all_database_fighters_with_companies()
        })
        ttk.Combobox(fighter_controls, textvariable=record_sport, values=sport_values, state="readonly", width=18).pack(side="left", padx=(0, 8))
        ttk.Label(fighter_controls, text="Leaderboard", style="Inset.TLabel").pack(side="left", padx=(6, 3))
        record_category = tk.StringVar(value="Legacy Score")
        categories = (
            "Legacy Score", "Career Wins", "Career Bouts", "Win Percentage (10+ bouts)", "ELO Rating",
            "Title Defenses", "Title Wins", "Awards Won",
            "Career Knockouts", "Career Submissions", "Career Finishes", "Finish Rate (10+ bouts)",
            "Career Significant Strikes", "Significant Strikes per Round (10+ rounds)",
            "Career Takedowns", "Takedowns per Round (10+ rounds)", "Career Knockdowns",
            "Career Submission Attempts", "Career Control Time", "Career Rounds Fought",
        )
        ttk.Combobox(fighter_controls, textvariable=record_category, values=categories, state="readonly", width=38).pack(side="left", padx=(0, 8))
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
            sig = getattr(fighter, "career_sig_strikes", 0)
            takedowns = getattr(fighter, "career_takedowns", 0)
            finishes = getattr(fighter, "career_finishes", 0)
            stat_rounds = getattr(fighter, "career_stat_rounds", 0)
            control = getattr(fighter, "career_control_secs", 0)
            # Rate stats need a minimum sample or a single dominant round tops
            # the board; -1 sorts those fighters out of the leaderboard entirely.
            rated = stat_rounds >= 10
            values = {
                "Career Wins": (fighter.record_w, str(fighter.record_w)),
                "Career Bouts": (bouts, str(bouts)),
                "Win Percentage (10+ bouts)": ((fighter.record_w / bouts * 100) if bouts >= 10 else -1, f"{fighter.record_w / bouts * 100:.1f}%" if bouts else "-"),
                "ELO Rating": (getattr(fighter, "elo_rating", 1500), str(getattr(fighter, "elo_rating", 1500))),
                "Title Defenses": (getattr(fighter, "title_defenses", 0), str(getattr(fighter, "title_defenses", 0))),
                "Title Wins": (getattr(fighter, "title_wins", 0), str(getattr(fighter, "title_wins", 0))),
                "Awards Won": (getattr(fighter, "award_count", 0), str(getattr(fighter, "award_count", 0))),
                "Career Knockouts": (getattr(fighter, "career_knockouts", 0), str(getattr(fighter, "career_knockouts", 0))),
                "Career Submissions": (getattr(fighter, "career_submissions", 0), str(getattr(fighter, "career_submissions", 0))),
                "Career Finishes": (finishes, str(finishes)),
                "Finish Rate (10+ bouts)": ((finishes / fighter.record_w * 100) if bouts >= 10 and fighter.record_w else -1,
                                            f"{finishes / fighter.record_w * 100:.1f}%" if fighter.record_w else "-"),
                "Career Significant Strikes": (sig, f"{sig:,}"),
                "Significant Strikes per Round (10+ rounds)": ((sig / stat_rounds) if rated else -1,
                                                              f"{sig / stat_rounds:.1f}" if stat_rounds else "-"),
                "Career Takedowns": (takedowns, str(takedowns)),
                "Takedowns per Round (10+ rounds)": ((takedowns / stat_rounds) if rated else -1,
                                                    f"{takedowns / stat_rounds:.2f}" if stat_rounds else "-"),
                "Career Knockdowns": (getattr(fighter, "career_knockdowns", 0), str(getattr(fighter, "career_knockdowns", 0))),
                "Career Submission Attempts": (getattr(fighter, "career_sub_attempts", 0), str(getattr(fighter, "career_sub_attempts", 0))),
                "Career Control Time": (control, f"{control // 3600}h {control % 3600 // 60}m" if control >= 3600 else f"{control // 60}m {control % 60}s"),
                "Career Rounds Fought": (stat_rounds, str(stat_rounds)),
                "Legacy Score": (self.compute_legacy_score(fighter), str(self.compute_legacy_score(fighter))),
            }
            return values[category]

        def refresh_fighter_records(*_args):
            fighter_tree.delete(*fighter_tree.get_children())
            seen = set()
            rows = []
            for company, fighter in self.all_database_fighters_with_companies():
                identity = self.fighter_identity_key(fighter)
                if identity in seen:
                    continue
                seen.add(identity)
                if record_sport.get() != "All Sports" and self.fighter_career_sport(fighter) != record_sport.get():
                    continue
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
        record_sport.trace_add("write", refresh_fighter_records)
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

        self.build_title_lineage_tab(title_tab)
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(anchor="e", padx=12, pady=(0, 10))

    def build_title_lineage_tab(self, parent):
        """A filterable, master-detail belt lineage browser with a visual reign timeline."""
        colors = self.colors
        gold = colors.get("gold", "#c9a13a")
        muted = colors.get("muted", "#a8b3bf")
        text_color = colors.get("text", "#e8edf2")
        crown_color = gold
        defense_color = "#7fd694"
        interim_color = "#5aa9e6"
        vacate_color = "#e8837a"
        reign_palette = ["#3f7bd6", "#7a4fb0", "#2f9e6f", "#c77d33", "#b0466a", "#4a8f9e", "#8a6d3b", "#5a6f8a"]
        crown_actions = ("Champion Crowned", "Inaugural Champion", "Inaugural Champion Appointed")

        # --- assemble every division lineage that has any history ----------
        histories = [(self.player_company_name, "Player", getattr(self, "belt_history", {}), getattr(self, "belts", {}))]
        histories.extend(
            (
                promo.name,
                "Regional" if getattr(promo, "is_regional_feeder", False) else "Major",
                promo.belt_history or {},
                promo.belts or {},
            )
            for promo in self.promotions
        )
        lineages = []
        for company, tier, history, belts in histories:
            divisions = set((history or {}).keys()) | {key for key, holder in (belts or {}).items() if key or holder}
            for division in divisions:
                entries = list((history or {}).get(division, []) or [])
                if not entries and not (belts or {}).get(division):
                    continue
                reigns = self.title_reign_history(entries)
                gender = division.split(" ", 1)[0] if " " in division else "Male"
                weight = division.split(" ", 1)[1] if " " in division else division
                holder = (belts or {}).get(division, "")
                ongoing = reigns[-1] if reigns and reigns[-1].get("end_month") is None else None
                current_holder = holder or (ongoing.get("fighter") if ongoing else "")
                current_since = ongoing.get("start_month") if ongoing else None
                lineages.append({
                    "company": company, "tier": tier, "division": division, "gender": gender, "weight": weight,
                    "entries": entries, "reigns": reigns, "holder": current_holder,
                    "current_since": current_since, "changes": len(reigns),
                    "defenses": sum(r["defenses"] for r in reigns),
                })
        tier_order = {"Player": 0, "Major": 1, "Regional": 2}
        lineages.sort(key=lambda item: (tier_order.get(item["tier"], 9), item["company"], item["gender"], item["weight"]))

        # --- filter bar ----------------------------------------------------
        controls = ttk.Frame(parent, style="Inset.TFrame")
        controls.pack(fill="x", padx=6, pady=6)
        title_company = tk.StringVar(value="All Promotions")
        tier_filter = tk.StringVar(value="All Levels")
        gender_filter = tk.StringVar(value="All")
        division_filter = tk.StringVar(value="All")
        current_only = tk.BooleanVar(value=False)
        search_var = tk.StringVar(value="")
        company_values = ["All Promotions"] + sorted({item["company"] for item in lineages})
        weight_values = ["All"] + [w for w in WEIGHTS if any(item["weight"] == w for item in lineages)]
        ttk.Label(controls, text="Promotion", style="Inset.TLabel").pack(side="left", padx=(6, 3))
        title_company_combo = ttk.Combobox(controls, textvariable=title_company, values=company_values, state="readonly", width=26)
        title_company_combo.pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Level", style="Inset.TLabel").pack(side="left", padx=(4, 3))
        tier_filter_combo = ttk.Combobox(controls, textvariable=tier_filter, values=["All Levels", "Player", "Major", "Regional"], state="readonly", width=10)
        tier_filter_combo.pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Gender", style="Inset.TLabel").pack(side="left", padx=(4, 3))
        ttk.Combobox(controls, textvariable=gender_filter, values=["All", "Male", "Female"], state="readonly", width=9).pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Division", style="Inset.TLabel").pack(side="left", padx=(4, 3))
        ttk.Combobox(controls, textvariable=division_filter, values=weight_values, state="readonly", width=16).pack(side="left", padx=(0, 8))
        ttk.Label(controls, text="Fighter", style="Inset.TLabel").pack(side="left", padx=(4, 3))
        ttk.Entry(controls, textvariable=search_var, width=18).pack(side="left", padx=(0, 8))
        ttk.Checkbutton(controls, text="Crowned only", variable=current_only).pack(side="left", padx=(2, 6))

        body = ttk.Panedwindow(parent, orient="horizontal")
        body.pack(fill="both", expand=True, padx=6, pady=(0, 6))

        left = ttk.Frame(body, style="Chrome.TFrame")
        right = ttk.Frame(body, style="Chrome.TFrame")
        body.add(left, weight=2)
        body.add(right, weight=3)

        lineage_tree = ttk.Treeview(left, columns=("title", "champion", "reigns", "defenses"), show="headings", selectmode="browse")
        for column, heading, width, anchor in (
            ("title", "Championship", 240, "w"), ("champion", "Current Champion", 165, "w"),
            ("reigns", "Reigns", 60, "center"), ("defenses", "Def.", 52, "center"),
        ):
            lineage_tree.heading(column, text=heading)
            lineage_tree.column(column, width=width, anchor=anchor)
        lineage_tree.tag_configure("vacant", foreground=vacate_color)
        self.make_tree_sortable(lineage_tree)
        lineage_scroll = ttk.Scrollbar(left, orient="vertical", command=lineage_tree.yview)
        lineage_tree.configure(yscrollcommand=lineage_scroll.set)
        lineage_scroll.pack(side="right", fill="y")
        lineage_tree.pack(side="left", fill="both", expand=True)

        # --- detail pane: header, timeline canvas, chronological table -----
        header_var = tk.StringVar(value="Select a championship to view its full lineage.")
        header_label = tk.Label(right, textvariable=header_var, bg=colors.get("panel_dark", "#2d3540"),
                                fg=text_color, font=("Tahoma", 11, "bold"), anchor="w", justify="left", padx=10, pady=8)
        header_label.pack(fill="x", padx=4, pady=(0, 4))
        subtitle_var = tk.StringVar(value="")
        tk.Label(right, textvariable=subtitle_var, bg=colors.get("chrome", "#0b0d10"), fg=muted,
                 font=("Tahoma", 8), anchor="w", justify="left", padx=10).pack(fill="x", padx=4)

        timeline_frame = ttk.Frame(right, style="Chrome.TFrame")
        timeline_frame.pack(fill="x", padx=4, pady=(6, 0))
        timeline_canvas = tk.Canvas(timeline_frame, height=94, bg=colors.get("tree", "#11161c"), highlightthickness=1,
                                    highlightbackground=colors.get("line", "#384553"))
        timeline_hscroll = ttk.Scrollbar(timeline_frame, orient="horizontal", command=timeline_canvas.xview)
        timeline_canvas.configure(xscrollcommand=timeline_hscroll.set)
        timeline_canvas.pack(side="top", fill="x")
        timeline_hscroll.pack(side="top", fill="x", pady=(0, 6))

        legend = tk.Frame(right, bg=colors.get("chrome", "#0b0d10"))
        legend.pack(fill="x", padx=8, pady=(0, 2))
        for swatch, label_text in ((crown_color, "Crown / reign"), (defense_color, "Defence"),
                                   (interim_color, "Interim"), (vacate_color, "Vacated")):
            tk.Label(legend, text="■", bg=colors.get("chrome", "#0b0d10"), fg=swatch, font=("Tahoma", 9)).pack(side="left", padx=(6, 1))
            tk.Label(legend, text=label_text, bg=colors.get("chrome", "#0b0d10"), fg=text_color, font=("Tahoma", 8)).pack(side="left", padx=(0, 4))

        detail_tree = ttk.Treeview(right, columns=("date", "action", "fighter", "reign", "note"), show="headings")
        for column, heading, width, anchor in (
            ("date", "Date", 110, "center"), ("action", "Event", 150, "w"), ("fighter", "Fighter", 175, "w"),
            ("reign", "Reign", 90, "center"), ("note", "Context", 320, "w"),
        ):
            detail_tree.heading(column, text=heading)
            detail_tree.column(column, width=width, anchor=anchor)
        detail_tree.tag_configure("crown", foreground=crown_color)
        detail_tree.tag_configure("defense", foreground=defense_color)
        detail_tree.tag_configure("interim", foreground=interim_color)
        detail_tree.tag_configure("vacate", foreground=vacate_color)
        detail_scroll = ttk.Scrollbar(right, orient="vertical", command=detail_tree.yview)
        detail_tree.configure(yscrollcommand=detail_scroll.set)
        detail_scroll.pack(side="right", fill="y")
        detail_tree.pack(side="left", fill="both", expand=True, padx=(4, 0), pady=(2, 4))

        state = {"lineage_by_row": {}, "selected": None}

        def action_tag(action):
            if action in crown_actions:
                return "crown"
            if "Defense" in action or "Defence" in action:
                return "defense"
            if "Interim" in action:
                return "interim"
            if action in ("Vacated", "Interim Vacated", "Division Closed", "Interim Belt Cleared"):
                return "vacate"
            return ""

        def draw_timeline(lineage):
            canvas = timeline_canvas
            canvas.delete("all")
            visible_width = int(canvas.winfo_width() or 0) or 640
            height = int(canvas.winfo_height() or 0) or 94
            if not lineage:
                canvas.create_text(visible_width // 2, height // 2, text="No reign data", fill=muted, font=("Tahoma", 9))
                canvas.configure(scrollregion=(0, 0, visible_width, height))
                return
            reigns = lineage["reigns"]
            if not reigns:
                canvas.create_text(visible_width // 2, height // 2, text="No completed reigns yet", fill=muted, font=("Tahoma", 9))
                canvas.configure(scrollregion=(0, 0, visible_width, height))
                return
            now = int(getattr(self, "month", 1) or 1)
            spans = []
            for reign in reigns:
                start = reign.get("start_month") or now
                end = reign.get("end_month")
                length = max(1, (end if end is not None else now) - start)
                spans.append(length)
            # A minimum pixel width per reign, scaled by actual length beyond
            # that floor, so a long reign of many years is visibly longer than
            # a one-month cup of coffee without either squeezing short reigns
            # down to an unlabeled sliver. Content can exceed the visible
            # frame; the horizontal scrollbar handles the rest.
            pad = 8
            min_seg = 70
            pixels_per_month = 4
            segs = [max(min_seg, min_seg + (length - 1) * pixels_per_month) for length in spans]
            content_width = pad * 2 + sum(segs)
            bar_top, bar_bottom = 30, height - 26
            x = pad
            for index, (reign, length, seg) in enumerate(zip(reigns, spans, segs)):
                ongoing = reign.get("end_month") is None
                fill = reign_palette[index % len(reign_palette)]
                canvas.create_rectangle(x, bar_top, x + seg, bar_bottom, fill=fill, width=0)
                if ongoing:
                    canvas.create_rectangle(x + 1, bar_top + 1, x + seg - 1, bar_bottom - 1, outline=gold, width=2)
                # defence tick marks
                defenses = reign.get("defenses", 0)
                for d in range(min(defenses, 12)):
                    tick_x = x + seg * (d + 1) / (min(defenses, 12) + 1)
                    canvas.create_line(tick_x, bar_bottom - 6, tick_x, bar_bottom, fill="#ffffff", width=1)
                surname = (reign.get("fighter", "") or "").split(" ")[-1]
                canvas.create_text(x + seg / 2, (bar_top + bar_bottom) / 2, text=surname[:14],
                                   fill="#ffffff", font=("Tahoma", 8, "bold"))
                canvas.create_text(x + seg / 2, bar_bottom + 10, text=self.format_month_span(length),
                                   fill=muted, font=("Tahoma", 7))
                x += seg
            span_label = f"{self.format_game_date_text(reigns[0].get('start_date', ''))}  —  present"
            canvas.create_text(pad, 12, text=f"{len(reigns)} reign(s)   |   {span_label}", anchor="w",
                               fill=text_color, font=("Tahoma", 8, "bold"))
            canvas.configure(scrollregion=(0, 0, max(content_width, visible_width), height))

        def show_lineage(lineage):
            state["selected"] = lineage
            detail_tree.delete(*detail_tree.get_children())
            if not lineage:
                header_var.set("Select a championship to view its full lineage.")
                subtitle_var.set("")
                draw_timeline(None)
                return
            holder = lineage["holder"]
            now = int(getattr(self, "month", 1) or 1)
            if holder and lineage["current_since"]:
                reign_len = self.format_month_span(now - lineage["current_since"])
                header_var.set(f"{lineage['company']} — {lineage['division']} Championship   ·   {holder}")
                subtitle_var.set(f"{lineage['tier']} level   |   Current reign: {reign_len}   |   {lineage['changes']} title change(s)   |   {lineage['defenses']} total defence(s)")
            else:
                header_var.set(f"{lineage['company']} — {lineage['division']} Championship   ·   VACANT")
                subtitle_var.set(f"{lineage['tier']} level   |   {lineage['changes']} title change(s)   |   {lineage['defenses']} total defence(s)")
            draw_timeline(lineage)
            reign_lookup = {}
            for reign in lineage["reigns"]:
                reign_lookup[(reign["fighter"], reign["start_date"])] = reign
            for entry in lineage["entries"]:
                action = str(entry.get("action", ""))
                reign_label = ""
                if action in crown_actions:
                    reign = reign_lookup.get((entry.get("fighter", ""), entry.get("date", "")))
                    if reign:
                        end = reign.get("end_month")
                        reign_label = self.format_month_span((end if end is not None else now) - (reign.get("start_month") or now))
                        if end is None:
                            reign_label += " (current)"
                detail_tree.insert("", "end", tags=(action_tag(action),), values=(
                    self.belt_history_date_label(entry), action,
                    entry.get("fighter", ""), reign_label, entry.get("note", ""),
                ))

        def refresh_lineage_list(*_args):
            lineage_tree.delete(*lineage_tree.get_children())
            state["lineage_by_row"] = {}
            query = search_var.get().strip().lower()
            for index, lineage in enumerate(lineages):
                if title_company.get() != "All Promotions" and lineage["company"] != title_company.get():
                    continue
                if tier_filter.get() != "All Levels" and lineage["tier"] != tier_filter.get():
                    continue
                if gender_filter.get() != "All" and lineage["gender"] != gender_filter.get():
                    continue
                if division_filter.get() != "All" and lineage["weight"] != division_filter.get():
                    continue
                if current_only.get() and not lineage["holder"]:
                    continue
                if query:
                    haystack = f"{lineage['company']} {lineage['division']} {lineage['holder']}".lower()
                    if query not in haystack and not any(query in (r.get("fighter", "") or "").lower() for r in lineage["reigns"]):
                        continue
                row_id = f"lineage:{index}"
                state["lineage_by_row"][row_id] = lineage
                champion = lineage["holder"] or "— vacant —"
                lineage_tree.insert("", "end", iid=row_id, tags=() if lineage["holder"] else ("vacant",), values=(
                    f"{lineage['company']} · {lineage['division']} ({lineage['tier']})", champion,
                    lineage["changes"], lineage["defenses"],
                ))
            children = lineage_tree.get_children()
            if children:
                lineage_tree.selection_set(children[0])
                lineage_tree.focus(children[0])
                show_lineage(state["lineage_by_row"].get(children[0]))
            else:
                show_lineage(None)

        def refresh_company_filter(*_args):
            selected_tier = tier_filter.get()
            values = ["All Promotions"] + sorted({
                lineage["company"] for lineage in lineages
                if selected_tier == "All Levels" or lineage["tier"] == selected_tier
            })
            title_company_combo.configure(values=values)
            if title_company.get() not in values:
                title_company.set("All Promotions")

        def on_select(_event=None):
            selected = lineage_tree.selection()
            if selected:
                show_lineage(state["lineage_by_row"].get(selected[0]))

        def open_selected_fighter(_event=None):
            selected = detail_tree.selection()
            if not selected:
                return
            name = detail_tree.item(selected[0], "values")[2]
            fighter = self.find_fighter_anywhere(name) if name else None
            if fighter:
                self.open_fighter_profile_window(fighter)

        for var in (title_company, gender_filter, division_filter, search_var):
            var.trace_add("write", refresh_lineage_list)
        tier_filter.trace_add("write", refresh_company_filter)
        tier_filter.trace_add("write", refresh_lineage_list)
        current_only.trace_add("write", refresh_lineage_list)
        lineage_tree.bind("<<TreeviewSelect>>", on_select)
        detail_tree.bind("<Double-1>", open_selected_fighter)
        timeline_canvas.bind("<Configure>", lambda _event: draw_timeline(state["selected"]))
        refresh_company_filter()
        refresh_lineage_list()

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
        # A fast-forward can complete hundreds of AI cards. Rebuilding every
        # world and promotion record after each individual card repeatedly
        # scans the whole fighter population; defer that presentation work until
        # the advance ends or the player opens the record book.
        if getattr(self, "_advance_in_progress", False):
            self.historical_records_dirty = True
            return
        self.historical_records_dirty = False
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
        # Career schedules differ radically by sport. Diminishing returns and a hard
        # ceiling stop a 300- or 800-win wrestling/Muay Thai record from overwhelming
        # championship quality while still rewarding sustained success.
        win_quality = max(0.35, min(1.35, (peak - 62) / 26))
        win_value = min(220, (fighter.record_w ** 0.68) * 8 * (0.35 + 0.65 * win_pct) * win_quality)
        score = (win_value
                 + win_pct * 45
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

    def fighter_career_sport(self, fighter):
        discipline = str(getattr(fighter, "primary_discipline", "MMA") or "MMA").strip()
        return "MMA" if discipline in ("MMA", "Mixed Martial Arts") else discipline

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
            identity = self.fighter_identity_key(fighter)
            if getattr(fighter, "hall_of_fame", False) and identity not in seen:
                seen.add(identity)
                hofers.append(fighter)
        hofers.sort(key=self.compute_legacy_score, reverse=True)
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
            body.insert("end", f"  {fighter.gender} {fighter.weight} | Record {fighter.record} | Peak overall {peak} | Legacy {self.compute_legacy_score(fighter)}\n", "detail")
            extras = []
            if awards_won:
                extras.append(f"{awards_won} year-end award(s)")
            if getattr(fighter, "career_knockdowns", 0):
                extras.append(f"{fighter.career_knockdowns} knockdowns scored")
            if extras:
                body.insert("end", f"  {' | '.join(extras)}\n", "detail")
        body.config(state="disabled")
        ttk.Button(window, text="Close", style="Accent.TButton", command=window.destroy).pack(pady=(0, 8))
