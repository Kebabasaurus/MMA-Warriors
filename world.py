import json
import math
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


class WorldMixin:
    def calendar_parts(self, month=None, week=None):
        """Translate the save-stable month index into the player-facing calendar."""
        month_index = max(1, int(self.month if month is None else month))
        week_number = max(1, min(4, int(self.week if week is None else week)))
        zero_based = month_index - 1
        return GAME_START_YEAR + zero_based // 12, zero_based % 12 + 1, week_number

    def calendar_month_index(self, year, calendar_month):
        """Return the internal month index for a selected calendar month and year."""
        return max(1, (max(GAME_START_YEAR, int(year)) - GAME_START_YEAR) * 12 + max(1, min(12, int(calendar_month))))

    @staticmethod
    def normalize_day(day=None, default=LEGACY_EVENT_DAY):
        """Clamp a weekday to 1-7 (Monday-Sunday), falling back to `default`."""
        try:
            value = int(day)
        except (TypeError, ValueError):
            return default
        return max(1, min(DAYS_PER_WEEK, value))

    def calendar_day_index(self, month=None, week=None, day=None):
        """A single running day number, the fine clock under the month/week one.

        The simulation still advances a week at a time; this exists so camp
        length and recovery can be measured in days rather than being rounded
        to the week a card happens to sit in.
        """
        week_index = self.calendar_week_index(month, week)
        return (week_index - 1) * DAYS_PER_WEEK + self.normalize_day(day)

    def current_day_index(self):
        """Today. A simulated week is entered on its first day."""
        return self.calendar_day_index(self.month, self.week, getattr(self, "day", LEGACY_EVENT_DAY))

    def event_day(self, event):
        """The weekday a card runs on.

        Cards scheduled before bookings carried a day have none recorded, and
        are treated as running on the first day of their week so their camps
        are exactly as long as they were when they were booked.
        """
        if not isinstance(event, dict):
            return LEGACY_EVENT_DAY
        return self.normalize_day(event.get("day"), LEGACY_EVENT_DAY)

    def day_name(self, day=None, short=True):
        index = self.normalize_day(day) - 1
        return (CALENDAR_DAY_ABBREVIATIONS if short else CALENDAR_DAYS)[index]

    def format_game_date(self, month=None, week=None, include_week=True, day=None):
        year, calendar_month, week_number = self.calendar_parts(month, week)
        label = CALENDAR_MONTH_ABBREVIATIONS[calendar_month - 1]
        if not include_week:
            return f"{label} {year}"
        if day is None:
            return f"{label} W{week_number} {year}"
        return f"{label} W{week_number} {self.day_name(day)} {year}"

    def format_game_date_text(self, value):
        """Render save-stable numeric dates in the player-facing calendar format."""
        text = str(value or "")

        def replace_long(match):
            month = int(match.group(1))
            week = int(match.group(2)) if match.group(2) else 1
            return self.format_game_date(month, week, include_week=bool(match.group(2)))

        text = re.sub(r"\bMonth\s+(\d+)(?:\s*,?\s*Week\s+(\d+))?", replace_long, text, flags=re.IGNORECASE)

        def replace_short(match):
            return self.format_game_date(int(match.group(1)), int(match.group(2)))

        return re.sub(r"\bM(\d+)\s+W(\d+)\b", replace_short, text, flags=re.IGNORECASE)

    def record_world_story(self, story_type, headline, detail="", companies=None, fighters=None, importance=1):
        entry = {
            "month": self.month, "week": self.week, "year": GAME_START_YEAR + (self.month - 1) // 12,
            "type": story_type, "headline": headline, "detail": detail,
            "companies": companies or [], "fighters": fighters or [], "importance": importance,
        }
        self.world_chronicle = [entry] + list(getattr(self, "world_chronicle", []))
        self.world_chronicle = self.world_chronicle[:800]
        return entry

    def staff_skill(self, role):
        members = [member for member in getattr(self, "staff", []) if member.get("role") == role]
        if not members:
            return 45
        return max(member.get("skill", 45) * (0.72 + member.get("morale", 65) / 230) for member in members)

    def staff_effect(self, role, scale=1.0):
        """Small but persistent player-staff impact; quality never becomes an auto-win."""
        return max(-2.0, min(12.0, (self.staff_skill(role) - 50) * 0.16 * scale))

    def ensure_staff_profiles(self):
        specialty_by_role = {
            "Scout": "Prospect eye", "Doctor": "Injury prevention", "Marketing": "Regional campaigns",
            "Matchmaker": "Contender logic", "Drug Testing Officer": "Compliance",
            "Broadcast Producer": "Live production", "Talent Relations": "Contract trust",
        }
        for member in getattr(self, "staff", []) + getattr(self, "staff_candidates", []):
            member.setdefault("specialty", specialty_by_role.get(member.get("role"), "Operations"))
            member.setdefault("reputation", max(35, min(95, member.get("skill", 50) + random.randint(-8, 6))))
            if member.get("role") == "Scout":
                skill = member.get("skill", 50)
                for key, offset in (("fighter_judging", 0), ("potential_judging", -2), ("efficiency", 1), ("regional_knowledge", -3), ("networking", -1), ("reliability", 2), ("negotiation", -4), ("professionalism", 1)):
                    member.setdefault(key, max(25, min(95, skill + offset + random.randint(-7, 7))))

    def promotion_strategy(self, promo):
        if not getattr(promo, "strategy", None):
            promo.strategy = self.seed_promotion_strategy(promo.name, getattr(promo, "show_personality", "Balanced"))
        promo.strategy.setdefault("growth_ceiling", self.seed_promotion_strategy(promo.name, getattr(promo, "show_personality", "Balanced")).get("growth_ceiling", 76))
        return promo.strategy

    def update_ai_promotion_strategy(self, promo):
        strategy = self.promotion_strategy(promo)
        executive = getattr(promo, "executive", None) or self.seed_promotion_executive(promo.name)
        promo.executive = executive
        reserve = max(120_000, promo.size * 8_500)
        prior = strategy.get("current_mode", "Balanced")
        if promo.cash < reserve or promo.stability < 35:
            mode = "Financial Recovery"
        elif promo.reputation_score < 38 and strategy.get("prospect_focus", 50) >= 65:
            mode = "Prospect Rebuild"
        elif promo.momentum >= 5 and strategy.get("star_focus", 50) >= 65:
            mode = "Star Chasing"
        elif strategy.get("merit_focus", 50) >= 65:
            mode = "Contender Cycle"
        else:
            mode = "Title Push" if promo.reputation_score >= 65 else "Balanced"
        strategy["current_mode"] = mode
        strategy["last_review_month"] = self.month
        roster = [fighter for fighter in promo.roster if not fighter.retired]
        ready = [fighter for fighter in roster if self.fighter_available_for_date(fighter) and fighter.fatigue < 55]
        strategy["financial_pressure"] = max(0, round((reserve - promo.cash) / max(1, reserve) * 100 + max(0, 40 - promo.stability) * 1.4))
        strategy["roster_health"] = round(len(ready) / max(1, len(roster)) * 100)
        strategy["prospect_ratio"] = round(sum(1 for fighter in roster if fighter.age <= 27 and fighter.potential >= fighter.overall + 8) / max(1, len(roster)) * 100)
        strategy["star_ratio"] = round(sum(1 for fighter in roster if fighter.popularity + fighter.star_quality >= 145) / max(1, len(roster)) * 100)
        if mode != prior and random.random() < 0.55:
            headline = f"Strategy shift: {promo.name} moves into {mode.lower()} mode."
            self.news.insert(0, headline)
            self.record_world_story("Company Strategy", headline, f"Identity: {strategy.get('identity', 'company')}. Media voice: {strategy.get('media_voice', 'reliable fights')}.", [promo.name], importance=2)
        return strategy

    def update_ai_financial_market(self, promo):
        """Advance a persistent commercial cycle for one AI promotion.

        Sporting success is not a guarantee of commercial success: weaker brands
        experience larger swings in sponsorship, ticket demand, and distribution.
        The values live in ``strategy`` so existing saves receive safe defaults
        and the same company carries its financial story from month to month.
        """
        strategy = self.promotion_strategy(promo)
        executive = getattr(promo, "executive", {}) or {}
        strength = strategy.setdefault("commercial_strength", max(38, min(92, promo.reputation_score + (8 if promo.size >= 75 else -4))))
        volatility = strategy.setdefault("market_volatility", max(8, min(30, round((100 - strength) * 0.45))))
        strategy.setdefault("market_momentum", 0.0)
        if strategy.get("market_review_month") != self.month:
            discipline = executive.get("discipline", 60)
            shock = random.uniform(-volatility, volatility)
            # Disciplined companies smooth bad quarters; aggressive companies
            # feel both the upside and downside more sharply.
            smoothing = 0.48 + discipline / 260
            strategy["market_momentum"] = max(-38.0, min(38.0, strategy["market_momentum"] * smoothing + shock))
            strategy["market_review_month"] = self.month
        return strength, volatility, strategy["market_momentum"]

    def review_ai_executives(self):
        """Quarterly board pressure can force leadership changes and new company eras."""
        if self.month % 3:
            return
        for promo in [item for item in self.promotions if not getattr(item, "is_regional_feeder", False)]:
            executive = getattr(promo, "executive", None) or self.seed_promotion_executive(promo.name)
            promo.executive = executive
            self.review_executive_mandate(promo)
            pressure = max(0, 42 - promo.stability) * 1.1 + max(0, promo.size - promo.reputation_score) * 0.45
            executive["job_security"] = max(1, min(100, executive.get("job_security", 70) + random.randint(-5, 4) - round(pressure / 11)))
            if executive["job_security"] > 18 or random.random() > 0.18:
                continue
            former = executive["name"]
            successor = self.seed_promotion_executive(promo.name)
            if successor["name"] == former:
                # Named franchises seed a fixed executive; a genuine change needs a
                # distinct successor, not the same person "replacing" themselves.
                successor["name"] = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
            promo.executive = successor
            promo.executive["job_security"] = random.randint(58, 82)
            promo.era_history = list(getattr(promo, "era_history", []))
            note = f"{promo.executive['name']} replaces {former} as executive, launching a {promo.executive['archetype'].lower()} era."
            promo.era_history.insert(0, {"year": self.current_year(), "note": note})
            promo.era_history = promo.era_history[:40]
            self.news.insert(0, f"Boardroom change: {promo.name} appoints {promo.executive['name']}.")
            self.record_world_story("Executive Change", f"{promo.name} appoints {promo.executive['name']}.", note, [promo.name], importance=4)

    def review_executive_mandate(self, promo):
        """Boards issue time-bound mandates that influence strategy and job security."""
        executive = promo.executive or self.seed_promotion_executive(promo.name)
        promo.executive = executive
        mandate = executive.setdefault("board_mandate", "Financial Stability")
        if not executive.get("mandate_target"):
            executive["mandate_target"] = {
                "Reputation Growth": min(100, promo.reputation_score + 4),
                "Financial Stability": max(250_000, promo.size * 10_000),
                "Event Cadence": max(4, promo.event_counter + 5),
                "Roster Pipeline": max(4, len([fighter for fighter in promo.roster if fighter.age <= 26 and fighter.potential - fighter.overall >= 7]) + 2),
                "Title Success": max(2, sum(getattr(fighter, "title_defenses", 0) for fighter in promo.roster) + 2),
            }.get(mandate, promo.reputation_score + 4)
        executive.setdefault("mandate_deadline", self.month + 12)
        executive.setdefault("mandate_history", [])
        target = executive["mandate_target"]
        current = {
            "Reputation Growth": promo.reputation_score,
            "Financial Stability": promo.cash,
            "Event Cadence": promo.event_counter,
            "Roster Pipeline": len([fighter for fighter in promo.roster if fighter.age <= 26 and fighter.potential - fighter.overall >= 7]),
            "Title Success": sum(getattr(fighter, "title_defenses", 0) for fighter in promo.roster),
        }.get(mandate, 0)
        progress = max(0, min(100, round(current / max(1, target) * 100)))
        executive["mandate_progress"] = progress
        if current >= target:
            executive["job_security"] = min(100, executive.get("job_security", 70) + 9)
            note = f"Board mandate achieved: {mandate} ({current:,}/{target:,})."
            executive["mandate_history"] = (executive["mandate_history"] + [{"year": self.current_year(), "note": note}])[-20:]
            executive["mandate_target"] = 0
            executive["mandate_deadline"] = self.month + 12
            self.record_world_story("Board Mandate", f"{promo.name} completes its board mandate.", note, [promo.name], importance=3)
        elif self.month >= executive["mandate_deadline"]:
            executive["job_security"] = max(1, executive.get("job_security", 70) - 14)
            promo.stability = max(1, promo.stability - 2)
            note = f"Board mandate missed: {mandate} ({current:,}/{target:,})."
            executive["mandate_history"] = (executive["mandate_history"] + [{"year": self.current_year(), "note": note}])[-20:]
            executive["mandate_deadline"] = self.month + 6
            if mandate == "Financial Stability":
                self.promotion_strategy(promo)["current_mode"] = "Financial Recovery"
            elif mandate == "Roster Pipeline":
                self.promotion_strategy(promo)["current_mode"] = "Prospect Rebuild"
            self.record_world_story("Board Pressure", f"{promo.name} misses a board mandate.", note, [promo.name], importance=4)

    def apply_ai_operating_costs(self):
        """Give AI companies the same ongoing commercial pressure as the player."""
        for promo in [item for item in self.promotions if not getattr(item, "is_regional_feeder", False)]:
            roster_size = len([fighter for fighter in promo.roster if not fighter.retired])
            executive = getattr(promo, "executive", {}) or {}
            discipline = executive.get("discipline", 60)
            strategy = self.promotion_strategy(promo)
            # Cost control matters, but cannot fully erase a large roster and
            # production footprint. This makes reckless expansion expensive.
            operating_multiplier = 0.88 + max(0, 85 - discipline) / 170
            # Fighter purses are paid per card. Office costs therefore scale with
            # roster administration, not as a second hidden salary for every
            # contracted athlete. The old rate made a profitable global company
            # lose several million between shows and hollow out its divisions.
            monthly_cost = round((18_000 + promo.size * 650 + roster_size * 325) * operating_multiplier)
            promo.cash -= monthly_cost
            # Companies retain a genuine runway for cards and contract bidding.
            # Surplus above the operating ceiling is returned to ownership and
            # long-term infrastructure monthly. This is deliberately gentler
            # than a hard cap, while preventing an AI with a hot quarter from
            # compounding into nine-figure cash that no roster can use.
            target_reserve = self.ai_financial_runway(promo)
            strategy["target_reserve"] = target_reserve
            cash_ceiling = self.ai_cash_ceiling(promo)
            strategy["cash_ceiling"] = cash_ceiling
            if promo.cash > cash_ceiling:
                surplus = promo.cash - cash_ceiling
                distribution = round(surplus * (0.16 if promo.cash <= cash_ceiling * 1.4 else 0.24))
                promo.cash -= distribution
                strategy["capital_distributions"] = int(strategy.get("capital_distributions", 0) or 0) + distribution
            commercial_strength = strategy.get("commercial_strength", promo.reputation_score)
            stability_target = max(58, min(86, round(50 + commercial_strength * 0.38)))
            strategy["stability_target"] = stability_target
            # Healthy companies retain distinct identities rather than all
            # accumulating at the old universal 91-92 stability ceiling.
            if self.month % 3 == 0 and promo.stability > stability_target:
                promo.stability = max(stability_target, promo.stability - 1)
            reserve = max(150_000, promo.size * 8_000)
            # Stability reflects whether today's business is viable, not whether
            # it already has enough cash to instantly expand to its eventual
            # 300-fighter ambition. Otherwise solvent companies get trapped in
            # Financial Recovery and never rebuild their thin divisions.
            operating_reserve = max(450_000, promo.size * 8_000 + roster_size * 8_000)
            if promo.cash < 0:
                promo.stability = max(1, promo.stability - 4)
            elif promo.cash < reserve:
                promo.stability = max(1, promo.stability - 2)
            elif promo.cash < reserve * 2:
                promo.stability = max(1, promo.stability - 1)
            elif promo.cash >= operating_reserve and promo.stability < stability_target:
                promo.stability = min(stability_target, promo.stability + 1)

    def process_promotion_failures(self):
        """Restructure genuinely failed companies instead of silently deleting the world."""
        for promo in list(self.promotions):
            if getattr(promo, "is_regional_feeder", False):
                continue
            # A single bad quarter should force a rebuild, not erase a company.
            # Closure requires a sustained failure after a meaningful attempt to
            # trade, and closed names are persisted to prevent silent reseeding.
            # A company that cannot afford a single recovery card can still
            # fail. Three years is long enough to avoid opening-month churn.
            has_runway_history = self.month >= 37
            insolvent = has_runway_history and promo.cash < -500_000
            terminal = has_runway_history and promo.stability <= 2 and promo.cash < 100_000
            if not (insolvent or terminal):
                continue
            strategy = self.promotion_strategy(promo)
            last_buyout = int(strategy.get("last_buyout_month", 0) or 0)
            # New ownership gets six years to execute its rebuild. Without a
            # protected period, one weak season could trigger another buyout,
            # repeatedly dumping most of the same roster into free agency.
            if last_buyout and self.month - last_buyout < 72:
                last_workout = int(strategy.get("last_post_buyout_workout_month", 0) or 0)
                if promo.cash < 0 and self.month - last_workout >= 12:
                    card_runway = max(750_000, promo.size * 12_000)
                    workout = max(1_000_000, promo.size * 30_000, -promo.cash + card_runway)
                    promo.cash += workout
                    promo.stability = max(22, promo.stability)
                    strategy["last_post_buyout_workout_month"] = self.month
                    strategy["post_buyout_workouts"] = strategy.get("post_buyout_workouts", 0) + 1
                    strategy["current_mode"] = "Post-Buyout Rebuild"
                    promo.show_history = list(promo.show_history or [])
                    promo.show_history.insert(0, f"Post-buyout lender workout: ${workout:,} bridge funding, no roster purge.")
                    promo.show_history = promo.show_history[:12]
                continue
            executive = promo.executive or self.seed_promotion_executive(promo.name)
            promo.executive = executive
            if not executive.get("rescue_capital_used", False):
                rescue = max(4_000_000, promo.size * 75_000)
                executive["rescue_capital_used"] = True
                promo.cash += rescue
                promo.stability = max(36, promo.stability)
                headline = f"{promo.name} secures a final ${rescue:,} investor rescue package."
                self.news.insert(0, headline)
                self.record_world_story("Investor Rescue", headline, "The board has one chance to rebuild under a financial-recovery strategy.", [promo.name], importance=4)
                continue
            self.distressed_promotion_buyout(promo)

    def distressed_promotion_buyout(self, promo):
        """A failing AI company survives via new ownership, but loses most of its roster."""
        executive = promo.executive or self.seed_promotion_executive(promo.name)
        promo.executive = executive
        roster = [fighter for fighter in list(promo.roster) if not getattr(fighter, "retired", False)]
        roster.sort(key=lambda fighter: (fighter.champion, fighter.interim_champion, fighter.popularity + fighter.overall, fighter.potential), reverse=True)
        retain_count = min(len(roster), max(4, round(len(roster) * random.uniform(0.16, 0.28))))
        retained = set(fighter.name for fighter in roster[:retain_count])
        released = []
        for fighter in list(promo.roster):
            if getattr(fighter, "retired", False) or fighter.name in retained:
                continue
            fighter.champion = False
            fighter.interim_champion = False
            fighter.contract_months = 0
            fighter.exclusive = False
            fighter.contract_type = "Free Agent"
            fighter.ai_offer_company = ""
            fighter.ai_offer_months = 0
            fighter.ai_offer_purse = 0
            fighter.ai_offer_signing_bonus = 0
            fighter.free_agent_months = 0
            fighter.morale = max(20, fighter.morale - random.randint(5, 14))
            fighter.fight_history = fighter.fight_history or []
            fighter.fight_history.insert(0, f"Month {self.month}: Released after {promo.name}'s distressed buyout.")
            promo.roster.remove(fighter)
            self.free_agents.append(fighter)
            released.append(fighter)
        for belts in (promo.belts or {}, promo.interim_belts or {}):
            for key, value in list(belts.items()):
                if isinstance(value, dict):
                    for weight, champion in list(value.items()):
                        if champion and champion not in retained:
                            value[weight] = ""
                elif value and value not in retained:
                    belts[key] = ""
        injection = max(4_000_000, promo.size * random.randint(75_000, 105_000))
        promo.cash = injection
        promo.stability = random.randint(32, 48)
        promo.momentum = max(-4, min(3, promo.momentum + random.randint(-1, 2)))
        promo.size = max(35, promo.size - random.randint(2, 5))
        promo.reputation_score = max(30, promo.reputation_score - random.randint(1, 4))
        promo.reputation = "Global" if promo.reputation_score >= 68 else ("National" if promo.reputation_score >= 45 else "Regional")
        strategy = self.promotion_strategy(promo)
        strategy["current_mode"] = "Post-Buyout Rebuild"
        strategy["market_momentum"] = max(-8, strategy.get("market_momentum", 0) + 6)
        strategy["distressed_buyouts"] = strategy.get("distressed_buyouts", 0) + 1
        strategy["last_buyout_month"] = self.month
        former = executive.get("name", "the old board")
        successor = self.seed_promotion_executive(promo.name)
        if successor.get("name") == former:
            successor["name"] = f"{random.choice(FIRST_NAMES)} {random.choice(LAST_NAMES)}"
        successor["job_security"] = random.randint(62, 86)
        # The first investor rescue is a one-time route. Future failures lead
        # to another ownership change instead of an endless rescue/buyout loop.
        successor["rescue_capital_used"] = strategy["distressed_buyouts"] >= 1
        promo.executive = successor
        promo.era_history = list(getattr(promo, "era_history", []))
        note = f"Distressed buyout injected ${injection:,}, retained {len(promo.roster)} fighters, and released {len(released)} fighters into free agency."
        promo.era_history.insert(0, {"year": self.current_year(), "note": note})
        promo.era_history = promo.era_history[:40]
        promo.show_history = list(promo.show_history or [])
        promo.show_history.insert(0, f"Distressed buyout: new ownership, {len(released)} fighters released, rebuild begins.")
        promo.show_history = promo.show_history[:12]
        headline = f"{promo.name} bought out after financial distress; most of the roster hits free agency."
        self.news.insert(0, headline)
        self.record_world_story("Promotion Buyout", headline, note, [promo.name], [fighter.name for fighter in released[:8]], importance=5)

    def calendar_week_index(self, month=None, week=None):
        return (max(1, month if month is not None else self.month) - 1) * 4 + max(1, week if week is not None else self.week)

    def fighter_available_for_date(self, fighter, month=None, week=None, day=None):
        """Is a fighter clear to compete on this date?

        available_week is the authority. Suspensions, injuries, medical holds
        and every "clear this fighter now" path write it and know nothing about
        days, so treating the finer value as the gate let a suspended fighter
        through on a stale clearance. available_day only refines the boundary
        week, deciding whether a card lands before or after their return inside
        the week they become free.
        """
        if fighter.injured:
            return False
        week_gate = int(getattr(fighter, "available_week", 0) or 0)
        target_week = self.calendar_week_index(month, week)
        if target_week != week_gate:
            return target_week > week_gate
        if day is None:
            return True
        day_gate = int(getattr(fighter, "available_day", 0) or 0)
        week_start = (week_gate - 1) * DAYS_PER_WEEK + 1
        if not week_start <= day_gate < week_start + DAYS_PER_WEEK:
            # No day-level value that belongs to this week: the coarse gate has
            # already cleared them, so do not invent a finer restriction.
            return True
        return self.calendar_day_index(month, week, day) >= day_gate

    def day_index_parts(self, day_index):
        """Turn a running day number back into (month, week, day)."""
        zero_based = max(0, int(day_index) - 1)
        week_index = zero_based // DAYS_PER_WEEK + 1
        day = zero_based % DAYS_PER_WEEK + 1
        month = (week_index - 1) // WEEKS_PER_MONTH + 1
        week = (week_index - 1) % WEEKS_PER_MONTH + 1
        return month, week, day

    def fighter_available_day_index(self, fighter):
        """The first day a fighter may compete, reconciling both gates.

        Mirrors fighter_available_for_date: the week gate decides the week, and
        the day gate only refines the position inside it when it belongs there.
        """
        week_gate = int(getattr(fighter, "available_week", 0) or 0)
        week_start = (max(1, week_gate) - 1) * DAYS_PER_WEEK + 1
        day_gate = int(getattr(fighter, "available_day", 0) or 0)
        if week_start <= day_gate < week_start + DAYS_PER_WEEK:
            return day_gate
        return week_start

    def stamp_last_fight_date(self, *fighters):
        """Record when a fighter last competed, to the day of the card."""
        day_index = self.calendar_day_index(
            self.month, self.week, getattr(self, "_active_card_day", None) or LEGACY_EVENT_DAY
        )
        for fighter in fighters:
            if fighter is None:
                continue
            fighter.last_fight_month = self.month
            fighter.last_fight_day_index = day_index

    def fighter_rest_days(self, fighter, month=None, week=None, day=None):
        """Days between a fighter's last dated bout and the card being considered.

        Returns None until they have fought on a dated card, so callers can
        keep their existing week-based behaviour for older saves.
        """
        last = int(getattr(fighter, "last_fight_day_index", 0) or 0)
        if not last:
            return None
        return max(0, self.calendar_day_index(month, week, day) - last)

    def fighter_return_label(self, fighter):
        available = getattr(fighter, "available_week", 0)
        if not available or self.calendar_week_index() >= available:
            return "Available"
        return_month = (available - 1) // 4 + 1
        return_week = (available - 1) % 4 + 1
        return f"Available {self.format_game_date(return_month, return_week)}"

    def fighter_recovery_date_label(self, fighter):
        """Compact medical-return label for matchmaking tables."""
        if fighter.injured:
            return "Injured"
        available = int(getattr(fighter, "available_week", 0) or 0)
        if not available or self.calendar_week_index() >= available:
            return "Now"
        return_month = (available - 1) // 4 + 1
        return_week = (available - 1) % 4 + 1
        return self.format_game_date(return_month, return_week)

    def fighter_fatigue_label(self, fighter):
        fatigue = max(0, min(100, int(getattr(fighter, "fatigue", 0) or 0)))
        if fatigue >= 65:
            condition = "Unfit"
        elif fatigue >= 55:
            condition = "Tired"
        elif fatigue >= 40:
            condition = "Elevated"
        elif fatigue >= 20:
            condition = "Manageable"
        else:
            condition = "Fresh"
        return f"{fatigue} {condition}"

    def fighter_booking_status(self, fighter, month=None, week=None):
        """Availability label for a specific proposed event, not merely today."""
        if fighter.injured:
            return "Injured"
        if not self.fighter_available_for_date(fighter, month, week):
            return self.fighter_return_label(fighter)
        if fighter.fatigue >= 65:
            return f"Fatigued {fighter.fatigue}"
        return "Ready"

    def serious_injury_status(self, fighter):
        injury = getattr(fighter, "serious_injury", "")
        if not injury:
            return "None"
        decision = "Decision required" if getattr(fighter, "serious_injury_pending", False) else "Recovery underway"
        return f"{injury} — {decision}"

    def establish_rivalry(self, a, b, origin, heat=35, rematch_due=False):
        """Create a mutual, persistent feud and retain the story on both profiles."""
        if not a or not b or a is b or a.gender != b.gender or a.weight != b.weight:
            return False
        a.rival, b.rival = b.name, a.name
        shared_heat = max(10, min(100, heat))
        a.rivalry_heat = max(getattr(a, "rivalry_heat", 0), shared_heat)
        b.rivalry_heat = max(getattr(b, "rivalry_heat", 0), shared_heat)
        a.rivalry_origin = b.rivalry_origin = origin
        a.rivalry_rematch_due = b.rivalry_rematch_due = rematch_due
        a.rivalry_last_month = b.rivalry_last_month = self.month
        a.rivalry_history = (a.rivalry_history or [])[-39:] + [f"Month {self.month}: Rivalry with {b.name} began — {origin}."]
        b.rivalry_history = (b.rivalry_history or [])[-39:] + [f"Month {self.month}: Rivalry with {a.name} began — {origin}."]
        return True

    def rivalry_heat_between(self, a, b):
        if a.rival == b.name or b.rival == a.name:
            return max(getattr(a, "rivalry_heat", 0), getattr(b, "rivalry_heat", 0), 20)
        return 0

    def assign_career_goal(self, fighter, previous=""):
        """Give a fighter a concrete ambition that matches their public persona."""
        persona = getattr(fighter, "negotiation_persona", "Professional")
        options = {
            "Competitive": [("Win a World Title", 1), ("Build a Win Streak", 4), ("Settle a Rivalry", 1)],
            "Star Chaser": [("Become a Star", 70), ("Win a World Title", 1), ("Build a Win Streak", 4)],
            "Hard Bargainer": [("Secure a Payday", max(fighter.purse + 3_000, round(fighter.purse * 1.35))), ("Become a Star", 65)],
            "Security First": [("Earn Contract Security", 18), ("Secure a Payday", max(fighter.purse + 2_000, round(fighter.purse * 1.2)))],
            "Loyalist": [("Build a Win Streak", 3), ("Win a World Title", 1), ("Earn Contract Security", 16)],
            "Professional": [("Build a Win Streak", 3), ("Become a Star", 60), ("Win a World Title", 1)],
        }
        candidates = [item for item in options.get(persona, options["Professional"]) if item[0] != previous]
        if fighter.rival:
            candidates.append(("Settle a Rivalry", 1))
        goal, target = random.choice(candidates)
        fighter.career_goal, fighter.career_goal_target = goal, target
        fighter.career_goal_progress = 0
        fighter.career_goal_last_review = self.month
        return goal

    def career_goal_state(self, fighter):
        goal, target = getattr(fighter, "career_goal", ""), max(1, getattr(fighter, "career_goal_target", 1))
        if goal == "Win a World Title":
            return int(bool(fighter.champion)), 100 if fighter.champion else min(85, max(0, fighter.rank_score // 12))
        if goal == "Build a Win Streak":
            return fighter.career_win_streak >= target, min(100, round(fighter.career_win_streak / target * 100))
        if goal == "Become a Star":
            return fighter.popularity >= target, min(100, round(fighter.popularity / target * 100))
        if goal == "Secure a Payday":
            return fighter.purse >= target, min(100, round(fighter.purse / target * 100))
        if goal == "Earn Contract Security":
            return fighter.contract_months >= target, min(100, round(fighter.contract_months / target * 100))
        if goal == "Settle a Rivalry":
            resolved = not fighter.rival and any("claims the rivalry result" in str(note) for note in (fighter.rivalry_history or []))
            return resolved, 100 if resolved else (65 if fighter.rival else 0)
        return False, 0

    def process_career_goals(self):
        """Review active goals monthly; fulfillment improves morale, neglect erodes trust."""
        for roster, player_owned in [(self.roster, True)] + [(promo.roster, False) for promo in self.promotions]:
            for fighter in roster:
                if fighter.retired:
                    continue
                if not getattr(fighter, "career_goal", ""):
                    self.assign_career_goal(fighter)
                complete, progress = self.career_goal_state(fighter)
                fighter.career_goal_progress = progress
                if complete:
                    goal = fighter.career_goal
                    fighter.career_goal_history = (fighter.career_goal_history or [])[-19:] + [f"Month {self.month}: Completed career goal — {goal}."]
                    fighter.morale = min(100, fighter.morale + 7)
                    fighter.motivation = min(99, fighter.motivation + 6)
                    fighter.relationship_trust = min(100, fighter.relationship_trust + 4)
                    if player_owned:
                        self.inbox.append({"subject": f"Career Goal Completed — {fighter.name}", "body": f"{fighter.name} completed their goal: {goal}. Morale and motivation improved.", "type": "Talent Relations", "fighter": fighter.name, "resolved": False})
                    self.assign_career_goal(fighter, previous=goal)
                elif player_owned and progress < 20 and self.month - getattr(fighter, "career_goal_last_review", 0) >= 6:
                    fighter.relationship_trust = max(1, fighter.relationship_trust - 2)
                    fighter.morale = max(15, fighter.morale - 1)
                    fighter.career_goal_last_review = self.month
                    self.inbox.append({"subject": f"Career Goal Stalling — {fighter.name}", "body": f"{fighter.name}'s goal ({fighter.career_goal}) is only {progress}% complete. Their camp wants a clearer path.", "type": "Talent Relations", "fighter": fighter.name, "resolved": False})

    def is_player_academy_graduate(self, fighter):
        return bool(
            getattr(fighter, "academy_graduate", False)
            or "Fighting Academy" in str(getattr(fighter, "feeder_origin", ""))
        )

    def career_arc_note(self, fighter, note):
        fighter.career_arc_history = (getattr(fighter, "career_arc_history", None) or [])[-29:] + [
            f"Month {self.month}: {note}"
        ]

    def career_arc_definition(self, arc_type):
        definitions = {
            "Homegrown Champion": {
                "title": "Homegrown Champion",
                "objective": "Build an academy graduate into the promotion's first homegrown champion.",
                "deadline": 60,
            },
            "Veteran Final Run": {
                "title": "One Last Title Run",
                "objective": "Give a proven veteran a credible route to one final championship opportunity.",
                "deadline": 9,
            },
            "Professional Reset": {
                "title": "Professional Reset",
                "objective": "Turn raw talent into reliable habits before poor discipline limits the prospect.",
                "deadline": 8,
            },
            "Weight Management": {
                "title": "Weight-Cut Turnaround",
                "objective": "Stabilise a difficult cut and make weight for two consecutive appearances.",
                "deadline": 12,
            },
            "Camp Fit": {
                "title": "Find The Right Room",
                "objective": "Move a stalled fighter into a camp that suits their development.",
                "deadline": 9,
            },
            "Champion Ambition": {
                "title": "Keep The Champion",
                "objective": "Give the champion opponents, visibility, and a contract future worth defending.",
                "deadline": 6,
            },
        }
        return definitions.get(arc_type, {"title": arc_type, "objective": "Guide this fighter through the next stage of their career.", "deadline": 8})

    def active_career_arc(self, fighter):
        arc = getattr(fighter, "career_arc", None)
        return arc if isinstance(arc, dict) and arc.get("status", "active") == "active" else None

    def start_career_arc(self, fighter, arc_type, source="Career review"):
        if not fighter or self.active_career_arc(fighter):
            return False
        definition = self.career_arc_definition(arc_type)
        arc = {
            "type": arc_type,
            "title": definition["title"],
            "objective": definition["objective"],
            "status": "active",
            "started_month": self.month,
            "deadline_month": self.month + definition["deadline"],
            "plan": "",
            "last_review_month": self.month,
            "source": source,
            "baseline_title_shots": getattr(fighter, "title_shots", 0),
            "baseline_defenses": getattr(fighter, "title_defenses", 0),
            "baseline_fit": round(self.gym_fit_score(fighter, self.gym_by_name(fighter.camp), fighter.region)) if self.gym_by_name(fighter.camp) else 0,
            "weight_successes": 0,
        }
        fighter.career_arc = arc
        fighter.career_arc_last_offer_month = self.month
        self.career_arc_note(fighter, f"{definition['title']} began. {definition['objective']}")
        gym = self.gym_by_name(getattr(fighter, "camp", ""))
        if gym:
            self.record_gym_story(gym, f"Career story: {definition['title']}", definition["objective"], fighter=fighter)
        if fighter in getattr(self, "roster", []) and not getattr(self, "spectator_mode", False):
            self.inbox.append({
                "subject": f"Career Story - {fighter.name}",
                "body": f"{definition['title']}: {definition['objective']} Open Fighter Career Goals to choose how to support the plan.",
                "type": "Talent Relations", "fighter": fighter.name, "resolved": False,
            })
        return True

    def career_arc_state(self, fighter):
        arc = self.active_career_arc(fighter)
        if not arc:
            return False, 0, "No active career story."
        arc_type = arc.get("type", "")
        elapsed = max(0, self.month - arc.get("started_month", self.month))
        plan = arc.get("plan", "")
        if arc_type == "Homegrown Champion":
            if fighter.champion:
                return True, 100, "The academy graduate reached the summit."
            rank = getattr(fighter, "ranking_position", 0)
            ranking_progress = 70 if rank and rank <= 3 else 52 if rank and rank <= 6 else 35 if rank and rank <= 10 else 12
            progress = min(92, ranking_progress + min(20, getattr(fighter, "career_win_streak", 0) * 5) + min(10, fighter.record_w * 2))
            return False, progress, "Build ranking momentum, then earn a legitimate title fight."
        if arc_type == "Veteran Final Run":
            if fighter.champion or getattr(fighter, "title_shots", 0) > arc.get("baseline_title_shots", 0):
                return True, 100, "The veteran received the promised championship opportunity."
            rank = getattr(fighter, "ranking_position", 0)
            progress = 18 + (42 if getattr(fighter, "top_opponent_promise", False) else 0) + (20 if getattr(fighter, "main_event_promise", False) else 0)
            if rank and rank <= 5:
                progress += 20
            return False, min(90, progress), "Book a ranked opponent or title fight; the result remains up to the fight engine."
        if arc_type == "Professional Reset":
            professionalism = getattr(fighter, "professionalism", 50)
            progress = min(100, max(0, (professionalism - 35) * 2) + min(24, elapsed * 4))
            return professionalism >= 65 and elapsed >= 4, progress, "Structured training needs time, reliable habits, and active competition."
        if arc_type == "Weight Management":
            successes = int(arc.get("weight_successes", 0) or 0)
            return successes >= 2, min(100, successes * 50), f"Made weight appearances: {successes}/2."
        if arc_type == "Camp Fit":
            gym = self.gym_by_name(getattr(fighter, "camp", ""))
            current_fit = round(self.gym_fit_score(fighter, gym, fighter.region)) if gym else 0
            improved = current_fit - arc.get("baseline_fit", current_fit)
            complete = bool(plan) and improved >= 8 and elapsed >= 2
            progress = min(100, max(8, 35 + improved * 5 + elapsed * 4 if plan else 8))
            return complete, progress, f"Current camp fit {current_fit:+d}; a meaningful improvement needs time in the new room."
        if arc_type == "Champion Ambition":
            defense_gain = max(0, getattr(fighter, "title_defenses", 0) - arc.get("baseline_defenses", 0))
            if not fighter.champion:
                return True, 100, "The title changed hands; the champion's current chapter is complete."
            secure_deal = fighter.contract_months >= 8
            spotlight = plan in ("Showcase campaign", "Renew the deal")
            complete = defense_gain >= 1 and secure_deal and bool(plan)
            progress = min(95, defense_gain * 45 + (25 if secure_deal else 0) + (20 if spotlight else 0) + (10 if getattr(fighter, "top_opponent_promise", False) else 0))
            return complete, progress, "Keep a real opponent path and a credible future on the champion's contract."
        return False, 0, arc.get("objective", "")

    def career_arc_options(self, fighter):
        arc = self.active_career_arc(fighter)
        if not arc:
            return []
        options = {
            "Homegrown Champion": [
                ("title_path", "Build contender path", "Promise a ranked opponent within six months; this does not guarantee a title shot."),
                ("development", "Fund structured development", "Invest $6,000 in coaching, habits, and a focused development block."),
                ("camp", "Review camp fit", "Choose a gym and camp plan suited to the fighter's long-term development."),
            ],
            "Veteran Final Run": [
                ("title_path", "Back the final run", "Commit to a ranked opponent and featured opportunity within six months."),
                ("showcase", "Build a farewell showcase", "Spend $25,000 on a media push and feature the fighter when a suitable bout is booked."),
                ("decline", "Set honest expectations", "Decline the title-run request; trust and morale will fall, but no promise is made."),
            ],
            "Professional Reset": [
                ("development", "Fund structured development", "Invest $6,000 in coaching, habits, and a focused development block."),
                ("camp", "Review camp fit", "Put the fighter in a more accountable room and set a clear workload."),
            ],
            "Weight Management": [
                ("nutrition", "Fund nutrition support", "Spend $8,000 on a targeted weight-management programme and set the next camp focus."),
                ("camp", "Review division and camp", "Choose a camp plan now; a division move remains available from the fighter profile."),
            ],
            "Camp Fit": [
                ("camp", "Find the right room", "Choose a new gym, focus, and workload; the fit must improve over time."),
                ("development", "Fund structured development", "Invest $6,000 in coaching while you decide whether a move is needed."),
            ],
            "Champion Ambition": [
                ("showcase", "Build a showcase campaign", "Spend $25,000 on visibility and commit to a meaningful featured defence."),
                ("title_path", "Promise elite opposition", "Commit to a ranked challenger within six months."),
                ("contract", "Renew the deal", "Open contract negotiations to secure the champion's long-term future."),
            ],
        }
        return options.get(arc.get("type"), [])

    def apply_career_arc_plan(self, fighter, action):
        arc = self.active_career_arc(fighter)
        if not arc:
            return False, "This fighter has no active career story.", ""
        costs = {"development": 6000, "nutrition": 8000, "showcase": 25000}
        cost = costs.get(action, 0)
        if cost and self.cash < cost:
            return False, f"${cost:,} is required for this plan, but the company cannot fund it today.", ""
        if action == "contract":
            arc["plan"] = "Renew the deal"
            self.career_arc_note(fighter, "The promotion opened contract talks to secure the next chapter.")
            return True, "Open the contract offer and agree terms that match the champion's ambition.", "contract"
        if action == "camp":
            arc["plan"] = "Camp review"
            self.career_arc_note(fighter, "The promotion ordered a camp and workload review.")
            return True, "Choose the gym, focus, and workload for the next camp.", "camp"
        if action == "decline":
            arc["plan"] = "Expectations managed"
            fighter.relationship_trust = max(1, fighter.relationship_trust - 8)
            fighter.morale = max(15, fighter.morale - 6)
            self.career_arc_note(fighter, "The promotion declined the requested title run and set honest expectations.")
            return True, "The request was declined. The veteran remains under contract, but trust and morale fell.", ""
        if cost:
            self.cash -= cost
            self.finance["other"] = self.finance.get("other", 0) - cost
        if action == "development":
            arc["plan"] = "Structured development"
            fighter.professionalism = min(99, fighter.professionalism + 4)
            fighter.motivation = min(99, fighter.motivation + 5)
            self.ensure_detailed_skills(fighter)
            fighter.detailed_skills["dedication"] = min(99, fighter.detailed_skills.get("dedication", fighter.professionalism) + 3)
            fighter.camp_focus = "Game Plan" if fighter.camp_focus == "Balanced" else fighter.camp_focus
            note = f"Invested ${cost:,} in a structured development programme."
        elif action == "nutrition":
            arc["plan"] = "Nutrition programme"
            fighter.camp_focus = "Weight Management"
            fighter.camp_intensity = "Standard"
            fighter.walk_weight = max(WEIGHT_LIMITS.get(fighter.weight, fighter.walk_weight) + 3, (fighter.walk_weight or self.default_walk_weight(fighter)) - 2)
            fighter.weight_cut_penalty = max(0, fighter.weight_cut_penalty - 3)
            self.ensure_detailed_skills(fighter)
            fighter.detailed_skills["weight_cutting"] = min(99, fighter.detailed_skills.get("weight_cutting", fighter.cardio) + 3)
            note = f"Invested ${cost:,} in nutrition and weight-cut support."
        elif action == "showcase":
            arc["plan"] = "Showcase campaign"
            fighter.popularity = min(100, fighter.popularity + 3)
            fighter.media_heat = min(100, fighter.media_heat + 8)
            fighter.main_event_promise = True
            fighter.top_opponent_promise = True
            fighter.promise_deadline_month = max(fighter.promise_deadline_month, self.month + 6)
            note = f"Invested ${cost:,} in a showcase campaign and meaningful opponent path."
        elif action == "title_path":
            arc["plan"] = "Contender path"
            fighter.top_opponent_promise = True
            if arc.get("type") in ("Veteran Final Run", "Champion Ambition"):
                fighter.main_event_promise = True
            fighter.promise_deadline_month = max(fighter.promise_deadline_month, self.month + 6)
            fighter.motivation = min(99, fighter.motivation + 4)
            note = "Committed to a ranked-opponent path within six months."
        else:
            return False, "That career-plan action is not available.", ""
        self.career_arc_note(fighter, note)
        gym = self.gym_by_name(getattr(fighter, "camp", ""))
        if gym:
            self.record_gym_story(gym, f"Career plan: {arc.get('title', arc.get('type'))}", note, fighter=fighter)
        return True, note, ""

    def complete_career_arc(self, fighter, conclusion):
        arc = self.active_career_arc(fighter)
        if not arc:
            return
        title = arc.get("title", arc.get("type", "Career Story"))
        fighter.career_achievements = (fighter.career_achievements or [])[-39:] + [f"{title}: {conclusion}"]
        self.career_arc_note(fighter, f"Completed {title}. {conclusion}")
        fighter.morale = min(100, fighter.morale + 8)
        fighter.motivation = min(99, fighter.motivation + 6)
        fighter.relationship_trust = min(100, fighter.relationship_trust + 6)
        if arc.get("type") == "Homegrown Champion":
            academy = self.repair_academy(getattr(self, "academy", {}))
            academy["reputation"] = min(100, academy.get("reputation", 10) + 8)
            academy["alumni"] = [
                {**row, "title_wins": max(1, row.get("title_wins", 0))} if row.get("name") == fighter.name else row
                for row in academy.get("alumni", [])
            ]
        gym = self.gym_by_name(getattr(fighter, "camp", ""))
        if gym:
            self.record_gym_story(gym, f"Career story completed: {title}", conclusion, fighter=fighter)
        if fighter in self.roster:
            self.inbox.append({"subject": f"Career Story Completed - {fighter.name}", "body": f"{title}: {conclusion}", "type": "Talent Relations", "fighter": fighter.name, "resolved": False})
        fighter.career_arc = None

    def fail_career_arc(self, fighter, conclusion):
        arc = self.active_career_arc(fighter)
        if not arc:
            return
        title = arc.get("title", arc.get("type", "Career Story"))
        if arc.get("type") == "Champion Ambition":
            fighter.negotiation_heat = min(100, getattr(fighter, "negotiation_heat", 0) + 12)
            conclusion += " Their camp is now actively testing the market."
        self.career_arc_note(fighter, f"{title} stalled. {conclusion}")
        fighter.relationship_trust = max(1, fighter.relationship_trust - 7)
        fighter.morale = max(15, fighter.morale - 5)
        if fighter in self.roster:
            self.inbox.append({"subject": f"Career Story Stalled - {fighter.name}", "body": f"{title}: {conclusion}", "type": "Talent Relations", "fighter": fighter.name, "resolved": False})
        fighter.career_arc = None

    def record_career_arc_result(self, fighters, fight):
        for fighter in fighters:
            arc = self.active_career_arc(fighter)
            if not arc:
                continue
            if arc.get("type") == "Weight Management":
                if not getattr(fighter, "missed_weight", False):
                    arc["weight_successes"] = min(2, int(arc.get("weight_successes", 0) or 0) + 1)
                    self.career_arc_note(fighter, f"Made weight successfully ({arc['weight_successes']}/2).")
                else:
                    arc["weight_successes"] = 0
                    self.career_arc_note(fighter, "Missed weight; the turnaround count resets.")
            complete, _progress, conclusion = self.career_arc_state(fighter)
            if complete:
                self.complete_career_arc(fighter, conclusion)

    def offer_player_career_arc(self):
        if getattr(self, "spectator_mode", False) or self.rules.get("career_arc_last_generation_month") == self.month:
            return False
        candidates = []
        for fighter in self.roster:
            if fighter.retired or self.active_career_arc(fighter):
                continue
            seen = " ".join(getattr(fighter, "career_arc_history", None) or [])
            if self.is_player_academy_graduate(fighter) and "Homegrown Champion began" not in seen:
                candidates.append((0, fighter.potential * 2 + max(0, 28 - fighter.age), fighter, "Homegrown Champion", "Academy promotion"))
            if fighter.champion and fighter.contract_months <= 10 and "Keep The Champion began" not in seen:
                candidates.append((1, fighter.popularity + fighter.title_defenses * 8, fighter, "Champion Ambition", "Champion contract review"))
            if fighter.age >= 34 and fighter.record_w + fighter.record_l >= 16 and fighter.popularity >= 28 and "One Last Title Run began" not in seen:
                candidates.append((2, fighter.popularity + fighter.record_w + max(0, 39 - fighter.age), fighter, "Veteran Final Run", "Veteran career review"))
            if fighter.age <= 27 and fighter.potential - fighter.overall >= 8 and fighter.professionalism <= 48 and "Professional Reset began" not in seen:
                candidates.append((3, fighter.potential - fighter.professionalism, fighter, "Professional Reset", "Prospect development review"))
            if (fighter.missed_weight or fighter.weight_cut_penalty >= 8) and "Weight-Cut Turnaround began" not in seen:
                candidates.append((4, fighter.weight_cut_penalty + (12 if fighter.missed_weight else 0), fighter, "Weight Management", "Medical and performance review"))
            gym = self.gym_by_name(getattr(fighter, "camp", ""))
            fit = self.gym_fit_score(fighter, gym, fighter.region) if gym else 0
            if fighter.age <= fighter.prime_end and fighter.potential - fighter.overall >= 6 and fit < 48 and "Find The Right Room began" not in seen:
                candidates.append((5, 55 - fit + fighter.potential - fighter.overall, fighter, "Camp Fit", "Camp development review"))
        if not candidates:
            return False
        _priority, _score, fighter, arc_type, source = sorted(candidates, key=lambda row: (row[0], -row[1], row[2].name, row[3]))[0]
        if self.start_career_arc(fighter, arc_type, source):
            self.rules["career_arc_last_generation_month"] = self.month
            return True
        return False

    def process_career_arcs(self):
        """Advance player-controlled long-form stories alongside ordinary career goals."""
        self.offer_player_career_arc()
        for fighter in list(self.roster):
            arc = self.active_career_arc(fighter)
            if not arc:
                continue
            complete, _progress, conclusion = self.career_arc_state(fighter)
            if complete:
                self.complete_career_arc(fighter, conclusion)
                continue
            if self.month > arc.get("deadline_month", self.month):
                if arc.get("type") == "Homegrown Champion":
                    arc["deadline_month"] = self.month + 24
                    self.career_arc_note(fighter, "The homegrown project continues; development takes the time it takes.")
                elif arc.get("type") == "Champion Ambition" and fighter.champion and fighter.contract_months > 1:
                    arc["deadline_month"] = self.month + 4
                    self.career_arc_note(fighter, "Champion review extended briefly; a concrete contract or opponent decision is still needed.")
                else:
                    self.fail_career_arc(fighter, "The promised path did not materialise before the review deadline.")

    def refresh_promotion_rankings(self, track=True, company=None, roster=None):
        """Maintain a transparent current/previous rank for the player and every AI promotion."""
        if roster is not None:
            groups = [(company or self.player_company_name, roster)]
        else:
            groups = [(self.player_company_name, self.roster)] + [(promo.name, promo.roster) for promo in self.promotions if not getattr(promo, "is_regional_feeder", False)]
        for _company, roster in groups:
            buckets = {}
            for fighter in roster:
                if not fighter.retired:
                    buckets.setdefault((fighter.gender, fighter.weight), []).append(fighter)
            for fighters in buckets.values():
                champions = [fighter for fighter in fighters if fighter.champion]
                contenders = sorted((fighter for fighter in fighters if not fighter.champion), key=self.rank_value, reverse=True)
                for fighter in champions:
                    old = getattr(fighter, "ranking_position", 0)
                    if track and old:
                        fighter.previous_ranking_position = old
                    fighter.ranking_position = 0
                    fighter.ranking_reason = "Champion"
                for position, fighter in enumerate(contenders, 1):
                    old = getattr(fighter, "ranking_position", 0)
                    if track and old and old != position:
                        fighter.previous_ranking_position = old
                    elif not old:
                        fighter.previous_ranking_position = position
                    fighter.ranking_position = position
                    if getattr(fighter, "owed_title_shot", False):
                        reason = "Guaranteed title shot"
                    elif getattr(fighter, "career_win_streak", 0) >= 3:
                        reason = f"{fighter.career_win_streak}-fight win streak"
                    elif fighter.momentum >= 3:
                        reason = "Strong recent form"
                    elif fighter.fatigue >= 55 or fighter.injured:
                        reason = "Inactive / recovering"
                    else:
                        reason = "Merit ranking"
                    fighter.ranking_reason = reason

    def result_archive_key(self, record):
        """Stable identifier shared by detailed replays and the permanent card index."""
        return "|".join(str(record.get(key, "")).strip() for key in ("date", "company", "event"))

    def result_index_row(self, record, has_replay=False):
        """Store only the information needed to browse an old card quickly."""
        fight_logs = record.get("fight_logs", []) or []
        compact_bouts = [
            {
                "label": row.get("label", "BOUT"), "a": row.get("a", ""), "b": row.get("b", ""),
                "a_id": row.get("a_id", ""), "b_id": row.get("b_id", ""), "weight": row.get("weight", ""),
                "sport": row.get("sport", ""), "result": row.get("result", ""),
                "scorecards": row.get("scorecards", "") or self.scorecard_summary_from_lines(row.get("lines", [])),
                "title": bool(row.get("title", False)),
                "divisional_title": bool(row.get("divisional_title", row.get("title") and not row.get("special_belt"))),
                "interim": bool(row.get("interim", False)),
                "special_belt": str(row.get("special_belt", "") or ""),
                "booking_reason": str(row.get("booking_reason", "") or ""),
            }
            for row in fight_logs if row.get("a") or row.get("b") or row.get("result")
        ]
        if not compact_bouts:
            compact_bouts = list(record.get("bout_results", []) or [])
        main = next((row for row in fight_logs if "MAIN" in str(row.get("label", "")).upper()), None)
        if not main and fight_logs:
            main = fight_logs[-1]
        headline = ""
        if main:
            headline = f"{main.get('a', '')} vs {main.get('b', '')}".strip(" vs")
        return {
            "key": self.result_archive_key(record),
            "detail_key": self.result_archive_key(record),
            "date": record.get("date", ""),
            "company": record.get("company", ""),
            "event": record.get("event", record.get("event_name", "")),
            "summary": record.get("summary", ""),
            "headline": headline,
            "fights": record.get("fights", record.get("fight_count", "")),
            "gate": record.get("gate", ""),
            "profit": record.get("profit", ""),
            "bout_results": compact_bouts,
            "has_replay": bool(has_replay),
        }

    def archive_result_record(self, record, retain_detail=True):
        """Add a completed card to both the short replay shelf and permanent index."""
        self.result_records.insert(0, record)
        limit = max(0, int(self.rules.get("global_result_replay_limit", GLOBAL_RESULT_REPLAY_LIMIT)))
        self.result_records = self.result_records[:limit]
        key = self.result_archive_key(record)
        index = getattr(self, "result_index", []) or []
        index = [row for row in index if row.get("key") != key]
        index.insert(0, self.result_index_row(record, has_replay=retain_detail))
        self.result_index = index[:RESULT_INDEX_LIMIT]

    def ensure_result_index(self):
        """Migrate older saves and expose their retained company history too."""
        index = list(getattr(self, "result_index", []) or [])
        known = {row.get("key") for row in index if row.get("key")}
        for record in reversed(getattr(self, "result_records", []) or []):
            row = self.result_index_row(record, has_replay=True)
            if row["key"] in known:
                # Legacy retirement showcases could share a company/week/title.
                # Preserve both cards rather than silently hiding one in search.
                base_key = row["key"]
                sequence = 2
                while f"{base_key}|{sequence}" in known:
                    sequence += 1
                row["key"] = f"{base_key}|{sequence}"
                headline = row.get("headline", "")
                if headline:
                    row["event"] = f"{row['event']} - {headline}"
            index.insert(0, row)
            known.add(row["key"])
        # Older saves only retained each promotion's small show-history shelf.
        # Make those cards searchable even though their full replay is gone.
        for promo in getattr(self, "promotions", []):
            for entry in reversed(getattr(promo, "show_history", []) or []):
                event = str(entry).split(":", 1)[0].strip()
                row = {
                    "key": f"legacy|{promo.name}|{event}", "date": "Archive date unavailable",
                    "company": promo.name, "event": event, "summary": str(entry),
                    "headline": "", "fights": "", "gate": "", "profit": "", "has_replay": False,
                }
                if row["key"] not in known:
                    index.append(row)
                    known.add(row["key"])
        self.result_index = index[:RESULT_INDEX_LIMIT]

    def all_mma_fighters_for_lineage_repair(self):
        fighters = []
        fighters.extend(getattr(self, "roster", []) or [])
        fighters.extend(getattr(self, "free_agents", []) or [])
        fighters.extend(getattr(self, "retired_fighters", []) or [])
        for promo in getattr(self, "promotions", []) or []:
            fighters.extend(getattr(promo, "roster", []) or [])
        return fighters

    def result_lineage_winner_loser(self, result, a_name, b_name):
        text = str(result or "")
        if a_name and text.startswith(f"{a_name} def."):
            return a_name, b_name
        if b_name and text.startswith(f"{b_name} def."):
            return b_name, a_name
        return "", ""

    def result_lineage_method(self, result):
        match = re.search(r"\bby\s+(.+?)(?:\s+\(R\d+\))?$", str(result or ""))
        return match.group(1).strip() if match else "Decision"

    def result_lineage_date_key(self, date_value):
        match = re.search(r"Month\s+(\d+)(?:\s+Week\s+(\d+))?", str(date_value or ""), re.IGNORECASE)
        return (int(match.group(1)), int(match.group(2) or 1)) if match else (0, 0)

    def title_history_has_non_lineal_changes(self, entries):
        current = ""
        for entry in reversed(list(entries or [])):
            action = str(entry.get("action", ""))
            fighter = str(entry.get("fighter", "") or "")
            note = str(entry.get("note", "") or "")
            opponent_match = re.search(r"Defeated\s+(.+?)\s+by\s+", note)
            opponent = opponent_match.group(1).strip() if opponent_match else ""
            if action in ("Inaugural Champion", "Inaugural Champion Appointed"):
                current = fighter
            elif action == "Champion Crowned":
                if current and current not in {fighter, opponent}:
                    return True
                current = fighter
            elif action == "Title Defense":
                if current and fighter != current:
                    return True
            elif action in ("Vacated", "Division Closed"):
                current = ""
        return False

    def rebuild_lineal_belt_histories_from_results(self):
        """Recover long belt histories without inventing parallel champions.

        Old result indexes label title bouts, but a label alone does not prove
        the winner took the lineal belt. After the first known champion, only a
        bout involving the current holder may produce a defense or crown.
        """
        fighters_by_id = {}
        fighters_by_name = {}
        for fighter in self.all_mma_fighters_for_lineage_repair():
            fid = str(getattr(fighter, "fighter_id", "") or "")
            if fid:
                fighters_by_id[fid] = fighter
            fighters_by_name.setdefault(str(getattr(fighter, "name", "") or ""), []).append(fighter)

        def gender_for_bout(bout):
            for key in ("a_id", "b_id"):
                fighter = fighters_by_id.get(str(bout.get(key, "") or ""))
                if fighter and getattr(fighter, "gender", "") in ("Male", "Female"):
                    return fighter.gender
            for key in ("a", "b"):
                genders = {
                    getattr(fighter, "gender", "")
                    for fighter in fighters_by_name.get(str(bout.get(key, "") or ""), [])
                    if getattr(fighter, "gender", "") in ("Male", "Female")
                }
                if len(genders) == 1:
                    return next(iter(genders))
            return ""

        source_events = []
        seen_source = set()
        for event_index, event in enumerate(getattr(self, "result_index", []) or []):
            company = str(event.get("company", "") or "")
            if not company:
                continue
            for bout_index, bout in enumerate(event.get("bout_results", []) or []):
                label = str(bout.get("label", "") or "").upper()
                divisional_title = bool(bout.get("divisional_title", bout.get("title") and not bout.get("special_belt")))
                legacy_title_label = label in ("TITLE FIGHT", "MAIN EVENT - TITLE FIGHT")
                if str(bout.get("sport", "") or "") or not (divisional_title or legacy_title_label):
                    continue
                weight = str(bout.get("weight", "") or "")
                if weight not in WEIGHTS:
                    continue
                gender = gender_for_bout(bout)
                if gender not in ("Male", "Female"):
                    continue
                a_name, b_name = str(bout.get("a", "") or ""), str(bout.get("b", "") or "")
                winner, loser = self.result_lineage_winner_loser(bout.get("result", ""), a_name, b_name)
                if not winner:
                    continue
                key = (
                    str(event.get("date", "") or ""), company, gender, weight,
                    winner, loser, self.result_lineage_method(bout.get("result", "")),
                )
                if key in seen_source:
                    continue
                seen_source.add(key)
                source_events.append((
                    self.result_lineage_date_key(event.get("date")),
                    event_index, bout_index, str(event.get("date", "") or ""),
                    company, self.belt_key(gender, weight), winner, loser,
                    self.result_lineage_method(bout.get("result", "")), a_name, b_name,
                ))
        source_events.sort(key=lambda row: (row[0], row[1], row[2]))

        rebuilt_by_company = {}
        current_by_company = {}
        for _month, _event_index, _bout_index, date, company, division, winner, loser, method, a_name, b_name in source_events:
            histories = rebuilt_by_company.setdefault(company, self.blank_belt_history())
            current = current_by_company.setdefault(company, {}).get(division, "")
            participants = {a_name, b_name}
            if not current:
                action = "Inaugural Champion"
                current_by_company[company][division] = winner
            elif winner == current:
                action = "Title Defense"
            elif current in participants:
                action = "Champion Crowned"
                current_by_company[company][division] = winner
            else:
                continue
            histories[division].insert(0, {
                "date": date, "action": action, "division": division,
                "fighter": winner, "note": f"Defeated {loser} by {method}.",
            })

        return rebuilt_by_company

    def migrate_lineal_belt_histories(self):
        version = int((getattr(self, "rules", {}) or {}).get("lineal_belt_history_version", 0) or 0)
        if version >= 1:
            return {"updated": 0, "rebuilt_entries": 0}
        rebuilt_by_company = self.rebuild_lineal_belt_histories_from_results()
        if not rebuilt_by_company:
            self.rules["lineal_belt_history_version"] = 1
            return {"updated": 0, "rebuilt_entries": 0}

        def primary_count(history):
            return sum(
                1 for entries in (history or {}).values() for entry in (entries or [])
                if entry.get("action") in ("Champion Crowned", "Inaugural Champion", "Inaugural Champion Appointed", "Title Defense")
            )

        def merge_history(company, existing):
            existing = self.normalize_belt_history(existing)
            rebuilt = self.normalize_belt_history(rebuilt_by_company.get(company, {}))
            if not any(rebuilt.values()):
                return existing, False
            existing_count = primary_count(existing)
            rebuilt_count = primary_count(rebuilt)
            capped = any(len(entries or []) == 80 for entries in existing.values())
            non_lineal = any(self.title_history_has_non_lineal_changes(entries) for entries in existing.values())
            if not (capped or non_lineal or rebuilt_count >= existing_count):
                return existing, False
            seen = {
                (row.get("date"), row.get("action"), row.get("division"), row.get("fighter"), row.get("note"))
                for entries in rebuilt.values() for row in entries
            }
            for division, entries in existing.items():
                for entry in entries or []:
                    if entry.get("action") in ("Champion Crowned", "Inaugural Champion", "Inaugural Champion Appointed", "Title Defense"):
                        continue
                    row = dict(entry)
                    row.setdefault("division", division)
                    key = (row.get("date"), row.get("action"), row.get("division"), row.get("fighter"), row.get("note"))
                    if key not in seen:
                        rebuilt[division].append(row)
                        seen.add(key)
                rebuilt[division].sort(key=lambda row: self.result_lineage_date_key(row.get("date")), reverse=True)
            return rebuilt, True

        updated = 0
        self.belt_history, changed = merge_history(getattr(self, "player_company_name", PLAYER_PROMOTION_NAME), getattr(self, "belt_history", {}))
        updated += int(changed)
        for promo in getattr(self, "promotions", []) or []:
            promo.belt_history, changed = merge_history(promo.name, promo.belt_history or {})
            updated += int(changed)
        self.rules["lineal_belt_history_version"] = 1
        return {"updated": updated, "rebuilt_entries": sum(primary_count(history) for history in rebuilt_by_company.values())}

    def repair_future_belt_history_dates(self):
        """Clamp impossible future title-history stamps created by older calendars."""
        current_month = max(1, int(getattr(self, "month", 1) or 1))
        current_week = max(1, min(4, int(getattr(self, "week", 1) or 1)))
        fixed_entries = 0

        def repair_history(history):
            nonlocal fixed_entries
            normalized = self.normalize_belt_history(history)
            for division, entries in normalized.items():
                for entry in entries or []:
                    month, week = self.result_lineage_date_key(entry.get("date"))
                    if month <= 0:
                        entry["date"] = f"Month {current_month} Week {current_week}"
                        entry.setdefault("division", division)
                        fixed_entries += 1
                    elif month > current_month or (month == current_month and week > current_week):
                        entry["date"] = f"Month {current_month} Week {current_week}"
                        entry.setdefault("division", division)
                        fixed_entries += 1
            return normalized

        self.belt_history = repair_history(getattr(self, "belt_history", {}))
        companies_fixed = 1 if fixed_entries else 0
        for promo in getattr(self, "promotions", []) or []:
            before = fixed_entries
            promo.belt_history = repair_history(promo.belt_history or {})
            companies_fixed += 1 if fixed_entries > before else 0
        return {"entries": fixed_entries, "companies": companies_fixed}

    def resolve_rivalry_result(self, winner, loser, fight, method):
        """A rivalry can demand a rematch or be conclusively settled by a result."""
        heat = self.rivalry_heat_between(winner, loser)
        if not heat:
            return
        marquee = bool(fight.get("main") or fight.get("title"))
        series = self.matchup_series_record(winner, loser)
        tied_series = series["meetings"] >= 2 and series["a_wins"] == series["b_wins"]
        rematch = (
            tied_series
            or method == "Decision" and (marquee or heat >= 55) and random.random() < 0.62
        )
        if rematch:
            next_heat = min(100, heat + random.randint(18, 32) if tied_series else heat + random.randint(12, 24))
            if tied_series:
                outcome = (
                    f"The rivalry series is level at {series['a_wins']}-{series['b_wins']}"
                    f"{f'-{series['draws']}' if series['draws'] else ''}; both camps want a decider after "
                    f"{winner.name} beat {loser.name} by {method}."
                )
            else:
                outcome = f"The close result fuels a demanded rematch after {winner.name} beat {loser.name} by {method}."
            winner.rivalry_rematch_due = loser.rivalry_rematch_due = True
        else:
            next_heat = max(0, heat - (random.randint(28, 48) if method != "Decision" else random.randint(12, 25)))
            outcome = f"{winner.name} claims the rivalry result over {loser.name} by {method}."
            winner.rivalry_rematch_due = loser.rivalry_rematch_due = False
            if next_heat < 20:
                winner.rival = loser.rival = ""
        winner.rivalry_heat = loser.rivalry_heat = next_heat
        for fighter in (winner, loser):
            fighter.rivalry_last_month = self.month
            fighter.rivalry_history = (fighter.rivalry_history or [])[-39:]
            fighter.rivalry_history.append(f"Month {self.month}: {outcome} Heat now {next_heat}/100.")
        winner.legacy_score = max(0, winner.legacy_score + (8 if marquee else 4))
        winner.popularity = min(100, winner.popularity + (2 if marquee else 1))

    def process_rivalry_activity(self):
        """Let active feuds breathe between events without constantly creating them."""
        for roster in [self.roster] + [promo.roster for promo in self.promotions]:
            lookup = {fighter.name: fighter for fighter in roster}
            for fighter in roster:
                rival = lookup.get(fighter.rival)
                if not rival or rival.rival != fighter.name or fighter.name > rival.name:
                    continue
                if random.random() < 0.12:
                    rise = random.randint(4, 11)
                    fighter.rivalry_heat = rival.rivalry_heat = min(100, max(fighter.rivalry_heat, rival.rivalry_heat) + rise)
                    fighter.media_heat = min(100, fighter.media_heat + rise // 2)
                    rival.media_heat = min(100, rival.media_heat + rise // 2)
                    fighter.rivalry_last_month = rival.rivalry_last_month = self.month
                    headline = f"{fighter.name} and {rival.name} trade fresh shots; their feud reaches {fighter.rivalry_heat}/100 heat."
                    self.news.insert(0, headline)
                    if fighter in self.roster or rival in self.roster:
                        self.inbox.append({"subject": "Rivalry Escalation", "body": headline, "type": "Roster", "fighter": fighter.name, "resolved": False})
                elif self.month - max(fighter.rivalry_last_month, rival.rivalry_last_month) >= 6:
                    cooled = max(0, max(fighter.rivalry_heat, rival.rivalry_heat) - 4)
                    fighter.rivalry_heat = rival.rivalry_heat = cooled
                    if cooled < 12 and not (fighter.rivalry_rematch_due or rival.rivalry_rematch_due):
                        fighter.rival = rival.rival = ""

    def apply_serious_injury(self, fighter, source="competition"):
        """Create a rare, career-relevant injury without making it a scripted result."""
        if getattr(fighter, "serious_injury", "") or fighter.retired:
            return False
        injury, months, affected = random.choice([
            ("ACL tear", random.randint(7, 11), ("cardio", "takedown_defence")),
            ("Shoulder reconstruction", random.randint(6, 10), ("wrestling", "grappling")),
            ("Broken hand", random.randint(4, 7), ("striking", "power")),
            ("Concussion symptoms", random.randint(5, 9), ("chin", "fight_iq")),
            ("Neck injury", random.randint(8, 12), ("toughness", "grappling")),
        ])
        fighter.serious_injury = injury
        fighter.serious_injury_pending = (
            fighter in getattr(self, "roster", [])
            or getattr(fighter, "sport_employer", "") == getattr(self, "player_company_name", "")
        )
        fighter.injured = max(fighter.injured, months)
        fighter.available_week = max(getattr(fighter, "available_week", 0), self.calendar_week_index() + months * 4)
        fighter.injury_proneness = min(100, fighter.injury_proneness + random.randint(2, 5))
        # There is a small lasting effect even with proper treatment; the player
        # chooses how much additional risk to take below.
        for stat in affected:
            setattr(fighter, stat, max(1, getattr(fighter, stat, 50) - 1))
        if fighter.detailed_skills:
            for key in random.sample(list(fighter.detailed_skills), k=min(2, len(fighter.detailed_skills))):
                fighter.detailed_skills[key] = max(1, fighter.detailed_skills[key] - 1)
        note = f"Month {self.month}: {injury} ({source}); expected absence {months} months."
        fighter.serious_injury_history = fighter.serious_injury_history or []
        fighter.serious_injury_history.append(note)
        fighter.serious_injury_history = fighter.serious_injury_history[-12:]
        headline = f"Medical alert: {fighter.name} suffers a {injury.lower()}."
        self.news.insert(0, headline)
        self.record_world_story("Serious Injury", headline, note, fighters=[fighter.name], importance=4)
        if fighter.serious_injury_pending:
            self.inbox.append({"subject": f"Medical Decision — {fighter.name}", "body": f"{fighter.name} has a {injury}. Expected absence: {months} months. Choose surgical repair, accelerated rehabilitation, or retirement.", "type": "Medical", "fighter": fighter.name, "action": "serious_injury", "resolved": False})
        else:
            self.resolve_serious_injury(fighter, "surgery", ai_decision=True)
        return True

    def resolve_serious_injury(self, fighter, choice="surgery", ai_decision=False):
        """Apply the medical trade-off for a serious injury and record it."""
        if not getattr(fighter, "serious_injury", ""):
            return False
        injury = fighter.serious_injury
        if choice == "retire":
            self.mark_retirement_fight_required(fighter, f"Medical retirement after {injury.lower()}")
            fighter.injured = 0
            fighter.serious_injury_pending = False
            outcome = "chose retirement after one final fight"
        elif choice == "rehab":
            fighter.injured = max(2, fighter.injured - random.randint(1, 3))
            fighter.serious_injury_recurrence += random.randint(5, 10)
            fighter.morale = max(15, fighter.morale - random.randint(3, 8))
            fighter.serious_injury_pending = False
            outcome = "chose accelerated rehabilitation (higher recurrence risk)"
        else:
            fighter.injured += random.randint(1, 3)
            fighter.injury_proneness = max(1, fighter.injury_proneness - random.randint(1, 3))
            fighter.morale = max(15, fighter.morale - random.randint(1, 5))
            fighter.serious_injury_pending = False
            outcome = "underwent surgical repair"
        fighter.serious_injury_history = fighter.serious_injury_history or []
        fighter.serious_injury_history.append(f"Month {self.month}: {injury} — {outcome}.")
        fighter.serious_injury_history = fighter.serious_injury_history[-12:]
        if not ai_decision:
            self.news.insert(0, f"Medical update: {fighter.name} {outcome} for a {injury.lower()}.")
        return True

    def retirement_review_month(self, fighter):
        """Stable pseudo-birthday month for old saves that do not store a birth date."""
        return sum(ord(char) for char in fighter.name) % 12 + 1

    def mark_retirement_fight_required(self, fighter, reason="Career review"):
        if getattr(fighter, "retired", False):
            return
        guaranteed = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0))
        completed = max(0, int(getattr(fighter, "contract_fights_completed", 0) or 0))
        if fighter in self.roster and completed < guaranteed:
            remaining = guaranteed - completed
            fighter.retirement_pending = False
            fighter.retirement_reason = f"Retirement deferred: {remaining} guaranteed comeback fight{'s' if remaining != 1 else ''} remaining."
            return
        fighter.retirement_pending = True
        fighter.retirement_fight_completed = False
        fighter.retirement_fight_due_after_month = 0
        fighter.retirement_requested_month = getattr(fighter, "retirement_requested_month", 0) or self.month
        fighter.retirement_reason = f"{reason}; final fight required."
        # A retirement fight should be bookable soon; avoid permanent limbo from
        # high accumulated fatigue while still respecting serious injuries.
        if fighter.fatigue > 58:
            fighter.fatigue = 58
        if fighter.injured and fighter.age >= 48:
            fighter.injured = max(0, fighter.injured - 1)

    def retire_after_final_fight_if_due(self, fighter, company_name=""):
        if not getattr(fighter, "retirement_pending", False) or getattr(fighter, "retired", False):
            return False
        # Completing a multi-fight comeback opens a new decision: renew or take
        # one farewell bout.  Do not consume that farewell bout in the same
        # result resolution that completed the comeback commitment.
        if getattr(fighter, "retirement_fight_due_after_month", 0) == self.month:
            return False
        if fighter in getattr(self, "roster", []) and fighter.name in self.scheduled_fighter_names(include_booked=False):
            fighter.retirement_reason = "Retirement deferred until all already-scheduled fights are completed."
            return False
        was_player_fighter = fighter in getattr(self, "roster", [])
        self.update_fighter_peak_overall(fighter)
        fighter.retirement_fight_completed = True
        fighter.retirement_pending = False
        fighter.retired = True
        fighter.retirement_reason = f"Retired after final fight at age {fighter.age}."
        if fighter in self.roster:
            self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(
                fighter, self.roster, self.belts, self.interim_belts, self.belt_history, "Retired after final fight."
            )
            self.vacate_special_belts_held_by(fighter, "Retired after final fight.")
            self.roster.remove(fighter)
            company_name = company_name or self.player_company_name
        if fighter in self.free_agents:
            self.free_agents.remove(fighter)
            company_name = company_name or "Independent Circuit"
        for promo in getattr(self, "promotions", []):
            if fighter in promo.roster:
                promo.belts, promo.interim_belts, promo.belt_history = self.vacate_fighter_belts(
                    fighter, promo.roster, promo.belts or {}, promo.interim_belts or {}, promo.belt_history or {}, "Retired after final fight."
                )
                promo.roster.remove(fighter)
                company_name = company_name or promo.name
                break
        fighter.champion = False
        fighter.interim_champion = False
        if fighter not in self.retired_fighters:
            self.retired_fighters.insert(0, fighter)
        headline = f"{fighter.name} retired after a final fight" + (f" with {company_name}" if company_name else "") + f" ({fighter.record})."
        self.news.insert(0, headline)
        if was_player_fighter:
            self.inbox.append({"subject": f"Retirement Confirmed - {fighter.name}", "body": f"{fighter.name} has completed their final scheduled fight and retired with a record of {fighter.record}. Any championships they held have been vacated.", "type": "Roster", "resolved": False, "fighter_id": getattr(fighter, "fighter_id", "")})
        self.record_world_story("Retirement", f"{fighter.name} completes final fight.", f"Final record: {fighter.record}. {fighter.retirement_reason}", [company_name] if company_name else [], [fighter.name], 3)
        self.consider_hall_of_fame(fighter)
        return True

    def set_post_fight_recovery(self, fighter, method, lost=False):
        # Realistic layoffs: fighters compete a few times a year, not monthly, so
        # careers and title reigns stay believable instead of racking up 130+ fights.
        # Layoffs centre on about a month, with variance and a longer medical
        # suspension after a knockout loss.
        base = 4 if not lost else 5
        if method in ("KO", "TKO", "Doctor Stoppage", "Corner Stoppage"):
            base += 2 if lost else 1
        elif method in ("Submission", "Technical Submission"):
            base += 1 if lost else 0
        base += random.randint(-1, 3)
        resilience = self.ds(fighter, "resilience", fighter.toughness)
        professionalism = getattr(fighter, "professionalism", 50)
        adjustment = 2 if resilience >= 78 and professionalism >= 70 else 0
        if fighter.trait == "Fast Healer":
            adjustment += 2
        elif fighter.trait == "Slow Healer":
            adjustment -= 2
        if any(member is fighter for member in getattr(self, "roster", [])):
            adjustment += 1 if self.staff_skill("Doctor") >= 74 else 0
        if fighter.injured:
            base += fighter.injured * 4
        layoff_weeks = max(2, base - adjustment)
        fighter.available_week = max(getattr(fighter, "available_week", 0), self.calendar_week_index() + layoff_weeks)
        # Count the layoff from the day they actually fought, so a Saturday
        # card returns them a day later than a Friday one rather than both
        # rounding to the same week.
        fought_on = int(getattr(fighter, "last_fight_day_index", 0) or 0) or self.current_day_index()
        fighter.available_day = max(
            int(getattr(fighter, "available_day", 0) or 0),
            fought_on + layoff_weeks * DAYS_PER_WEEK,
        )

    def spectator_advance_weeks(self, weeks=1, status_prefix="Simulating", on_complete=None, stop_condition=None):
        if not getattr(self, "spectator_mode", False):
            messagebox.showinfo("Spectator controls", "Start a new game in Spectator Mode to use world fast-forward controls.")
            return False
        return self.begin_advance_sequence(
            max(1, int(weeks)),
            status_prefix=status_prefix,
            on_complete=on_complete,
            stop_condition=stop_condition,
        )

    def request_spectator_sim_stop(self):
        """Stop an observer fast-forward safely after its current world week."""
        job = getattr(self, "_advance_job", None)
        if not getattr(self, "spectator_mode", False) or not getattr(self, "_advance_in_progress", False) or not job:
            return False
        if job.get("stop_requested"):
            return True
        job["stop_requested"] = True
        self.set_advance_ui_progress(
            "Stopping after the current simulated week",
            (job.get("completed", 0) / max(1, job.get("total", 1))) * 100,
        )
        return True

    def spectator_sim_month(self):
        self.spectator_advance_weeks(4, "Simulating month")

    def spectator_sim_year(self):
        self.spectator_advance_weeks(48, "Simulating year")

    def spectator_sim_to_date(self):
        target_year = max(GAME_START_YEAR, int(self.spectator_target_year.get()))
        target_calendar_month = CALENDAR_MONTHS.index(self.spectator_target_calendar_month.get()) + 1
        target_month = self.calendar_month_index(target_year, target_calendar_month)
        target_week = max(1, min(4, int(self.spectator_target_week.get())))
        target = (target_month, target_week)
        current = (self.month, self.week)
        if target <= current:
            messagebox.showinfo("Simulation date", "Choose a future calendar date.")
            return
        weeks = (target_month - self.month) * 4 + (target_week - self.week)
        self.spectator_advance_weeks(weeks, f"Simulating to {self.format_game_date(target_month, target_week)}")

    def watch_latest_world_event(self):
        if not self.ai_event_archive:
            messagebox.showinfo("No world event", "No AI promotion has completed an archived event yet. Sim forward to create one.")
            return
        package = self.ai_event_archive[0]
        self.open_live_fight_window({"name": package.get("event_name", "World Event")}, package, apply_results=False)

    def spectator_watch_next_event(self):
        if not getattr(self, "spectator_mode", False):
            messagebox.showinfo("Spectator controls", "Start a new game in Spectator Mode to watch the next hosted event.")
            return
        before = len(self.ai_event_archive)
        # A promotion's show cadence is deliberately variable. Two dozen weeks is
        # enough to find a card without turning this command into an endless loop.
        def completed():
            if len(self.ai_event_archive) > before:
                self.watch_latest_world_event()
            else:
                messagebox.showinfo("No event yet", "No promotion hosted a card in the next 24 weeks. The world still advanced normally.")

        self.spectator_advance_weeks(
            24,
            "Looking for the next hosted event",
            on_complete=completed,
            stop_condition=lambda: len(self.ai_event_archive) > before,
        )

    def fight_popularity_movement(self, winner, loser, fight, method):
        """Return restrained, context-sensitive popularity movement for a completed bout."""
        finish = method not in ("Decision", "Draw")
        rivalry = winner.rival == loser.name or loser.rival == winner.name
        upset = winner.overall + 5 < loser.overall or winner.popularity + 12 < loser.popularity
        winner_gain = 1 + int(bool(fight.get("main"))) + int(bool(fight.get("title")))
        winner_gain += int(finish) + int(rivalry) + int(upset)
        if winner.popularity < 25:
            winner_gain += 1
        # Established stars still benefit, but do not race to 100 on routine wins.
        if winner.popularity >= 85:
            winner_gain = max(1, winner_gain - 1)
        loser_loss = int(finish) + int(loser.popularity >= winner.popularity + 15)
        if fight.get("main") and loser.popularity < 35:
            loser_loss = max(0, loser_loss - 1)
        return min(6, winner_gain), min(3, loser_loss)

    def register_fight_popularity(self, winner, loser, fight, method):
        winner_gain, loser_loss = self.fight_popularity_movement(winner, loser, fight, method)
        winner.popularity = min(100, winner.popularity + winner_gain)
        loser.popularity = max(1, loser.popularity - loser_loss)

    def register_draw_popularity(self, a, b, fight):
        """Apply the modest shared visibility gain from a competitive draw."""
        stakes = int(bool(fight.get("main"))) + int(bool(fight.get("title")))
        rivalry = int(a.rival == b.name or b.rival == a.name)
        gain = min(2, stakes + rivalry)
        if gain:
            a.popularity = min(100, a.popularity + gain)
            b.popularity = min(100, b.popularity + gain)

    def add_fight_history_entry(self, fighter, entry):
        """Record a result once, even if a resumed world task repeats a write."""
        fighter.fight_history = fighter.fight_history or []
        if entry not in fighter.fight_history:
            fighter.fight_history.insert(0, entry)

    def scorecard_summary_from_lines(self, lines):
        """Extract official totals without retaining the commentary that led to them."""
        cards, collecting = [], False
        for raw in lines or []:
            text = str(raw).strip()
            if text == "Official scorecards:":
                collecting = True
                continue
            if collecting and text.startswith("Judges' vote:"):
                break
            if collecting:
                match = re.search(r":.*?(\d{2}).*?,.*?(\d{2})", text)
                if match:
                    cards.append(f"{match.group(1)}-{match.group(2)}")
        return " / ".join(cards)

    def bout_rating_snapshot(self, fighter):
        """Return the immutable rating state shown beside a historical result."""
        return {
            "overall": int(round(getattr(fighter, "overall", 0))),
            "elo": int(round(getattr(fighter, "elo_rating", 1500))),
            "record": str(getattr(fighter, "record", "0-0-0")),
        }

    def fighter_peak_overall(self, fighter):
        """Return the best rating retained by the live and archived career data."""
        def score_value(value):
            try:
                numeric = float(value)
            except (TypeError, ValueError):
                return 0
            return int(round(numeric)) if numeric == numeric else 0

        current = score_value(getattr(fighter, "overall", 0))
        stored_peak = score_value(getattr(fighter, "career_peak_overall", 0))
        # Once the migration has persisted a peak, normal monthly and bout
        # updates stay O(1). The more expensive archive scan is only needed to
        # repair saves made before this dedicated field existed.
        if stored_peak:
            return max(1, min(99, max(current, stored_peak)))
        scores = [current]
        scores.extend((getattr(fighter, "annual_overalls", None) or {}).values())
        for bout in getattr(fighter, "bout_rating_history", None) or []:
            if isinstance(bout, dict):
                scores.append(bout.get("self_overall", bout.get("overall", 0)))
        valid_scores = [score_value(score) for score in scores]
        return max(1, min(99, max(valid_scores, default=1)))

    def update_fighter_peak_overall(self, fighter):
        peak = self.fighter_peak_overall(fighter)
        fighter.career_peak_overall = peak
        return peak

    def record_bout_rating_history(self, a, b, a_result, b_result, fight=None):
        """Keep pre-bout ratings after card replays are trimmed from the archive."""
        self.update_fighter_peak_overall(a)
        self.update_fighter_peak_overall(b)
        date = f"Month {self.month} Week {self.week}"
        a_snapshot = self.bout_rating_snapshot(a)
        b_snapshot = self.bout_rating_snapshot(b)
        fight = fight or {}

        def append_snapshot(fighter, opponent, own, other, result):
            fighter.bout_rating_history = list(getattr(fighter, "bout_rating_history", None) or [])
            entry = {
                "date": date,
                "opponent_name": opponent.name,
                "opponent_id": str(getattr(opponent, "fighter_id", "") or ""),
                "result": result,
                "self_overall": own["overall"],
                "self_elo": own["elo"],
                "self_record": own["record"],
                "opponent_overall": other["overall"],
                "opponent_elo": other["elo"],
                "opponent_record": other["record"],
                "weight": getattr(fighter, "weight", ""),
                "title": bool(fight.get("title", False)),
                "divisional_title": bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt"))),
                "interim": bool(fight.get("interim", False)),
                "special_belt": str(fight.get("special_belt", "") or ""),
                "scorecard": str(fight.get("_scorecards", "") or "-"),
            }
            # A fighter cannot legitimately have two bouts with the same opponent
            # and pre-bout record on one card. This also keeps resumed tasks idempotent.
            key = (entry["date"], entry["opponent_id"] or entry["opponent_name"], entry["self_record"])
            existing = {
                (str(item.get("date", "")), str(item.get("opponent_id", "") or item.get("opponent_name", "")), str(item.get("self_record", "")))
                for item in fighter.bout_rating_history if isinstance(item, dict)
            }
            if key not in existing:
                fighter.bout_rating_history.insert(0, entry)
                fighter.bout_rating_history = fighter.bout_rating_history[:250]

        append_snapshot(a, b, a_snapshot, b_snapshot, a_result)
        append_snapshot(b, a, b_snapshot, a_snapshot, b_result)
        return {"a_rating": a_snapshot, "b_rating": b_snapshot}

    def extend_comeback_commitment(self, fighter, additional_fights):
        """Start a fresh, fight-counted comeback deal for a returning fighter."""
        additional = max(1, int(additional_fights or 1))
        previous_guaranteed = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0))
        previous_completed = max(0, int(getattr(fighter, "contract_fights_completed", 0) or 0))
        fighter.guaranteed_fights = additional
        fighter.contract_fights_completed = 0
        fighter.comeback_contract = True
        fighter.retirement_pending = False
        fighter.retirement_fight_completed = False
        fighter.retirement_fight_due_after_month = 0
        fighter.comeback_completion_prompted = False
        return {
            "previous_guaranteed": previous_guaranteed,
            "previous_completed": previous_completed,
            "additional": additional,
            "total": additional,
            "remaining": additional,
        }

    def record_contract_fight_completion(self, fighter):
        """Track a player comeback commitment only after an official bout."""
        if fighter not in self.roster:
            return
        guaranteed = max(0, int(getattr(fighter, "guaranteed_fights", 0) or 0))
        if not getattr(fighter, "comeback_contract", False) or guaranteed <= 0:
            return
        completed = min(guaranteed, max(0, int(getattr(fighter, "contract_fights_completed", 0) or 0)) + 1)
        fighter.contract_fights_completed = completed
        remaining = guaranteed - completed
        fighter.fight_history = fighter.fight_history or []
        fighter.fight_history.insert(0, f"Comeback commitment: {completed}/{guaranteed} guaranteed fights completed.")
        if remaining:
            self.inbox.append({"subject": "Comeback Commitment", "body": f"{fighter.name} has {remaining} guaranteed comeback fight{'s' if remaining != 1 else ''} remaining on their deal.", "type": "Contracts", "resolved": False})
        else:
            fighter.comeback_contract = False
            fighter.retirement_pending = True
            fighter.retirement_fight_completed = False
            fighter.retirement_fight_due_after_month = self.month
            fighter.retirement_requested_month = self.month
            fighter.retirement_reason = "Comeback commitment complete. Renew for another comeback or book one final retirement bout."
            fighter.comeback_completion_prompted = False
            self.inbox.append({"subject": "Comeback Commitment Complete", "body": f"{fighter.name} fulfilled all {guaranteed} guaranteed comeback fights. Renew their comeback deal from the fighter profile, or book their one final retirement bout.", "type": "Contracts", "resolved": False})
            if hasattr(self, "root") and hasattr(self, "prompt_comeback_completion"):
                self.root.after(0, lambda: self.prompt_comeback_completion(fighter))

    def apply_result(self, winner, loser, fight, method="Decision"):
        # Weigh-in state is cleared later in this method, so career arcs that
        # track weight management must see the result before preparation resets.
        self.record_career_arc_result((winner, loser), fight)
        self.record_bout_rating_history(winner, loser, "W", "L", fight)
        self.complete_fight_observation(winner)
        self.complete_fight_observation(loser)
        self.update_elo(winner, loser, fight, method)
        self.commit_career_stats(winner, method, won=True)
        self.commit_career_stats(loser, method, won=False)
        winner.record_w += 1
        loser.record_l += 1
        self.record_contract_fight_completion(winner)
        self.record_contract_fight_completion(loser)
        winner.career_win_streak = getattr(winner, "career_win_streak", 0) + 1
        loser.career_win_streak = 0
        winner.momentum = min(5, winner.momentum + 1)
        loser.momentum = max(-5, loser.momentum - 1)
        winner.morale = min(100, winner.morale + random.randint(3, 8))
        loser.morale = max(15, loser.morale - random.randint(4, 10))
        winner.motivation = min(99, winner.motivation + random.randint(1, 4))
        loser.motivation = max(1, loser.motivation - random.randint(1, 6))
        self.register_fight_popularity(winner, loser, fight, method)
        winner.fatigue = min(100, winner.fatigue + random.randint(18, 35))
        loser.fatigue = min(100, loser.fatigue + random.randint(22, 44))
        self.set_post_fight_recovery(winner, method, lost=False)
        self.set_post_fight_recovery(loser, method, lost=True)
        winner.last_fight = f"W over {loser.name}"
        loser.last_fight = f"L to {winner.name}"
        self.stamp_last_fight_date(winner, loser)
        winner.rank_score = self.rank_value(winner)
        loser.rank_score = self.rank_value(loser)
        result_line = f"Month {self.month} Week {self.week}: {winner.name} def. {loser.name} by {method}"
        self.add_fight_history_entry(winner, result_line)
        self.add_fight_history_entry(loser, result_line)
        if winner.rival == loser.name or loser.rival == winner.name:
            self.resolve_rivalry_result(winner, loser, fight, method)
        else:
            series = self.matchup_series_record(winner, loser)
            if series["meetings"] >= 2 and series["a_wins"] == series["b_wins"]:
                heat = 48 + min(24, series["meetings"] * 4) + (8 if fight.get("main") or fight.get("title") else 0)
                if self.establish_rivalry(winner, loser, f"Level series at {series['a_wins']}-{series['b_wins']}", heat=heat, rematch_due=True):
                    note = (
                        f"Month {self.month}: The head-to-head series is tied "
                        f"{series['a_wins']}-{series['b_wins']}; both fighters want the decider."
                    )
                    winner.rivalry_history = (winner.rivalry_history or [])[-39:] + [note]
                    loser.rivalry_history = (loser.rivalry_history or [])[-39:] + [note]
        winner.last_fight = result_line
        loser.last_fight = result_line
        if winner.trait == "Fan Favourite":
            winner.popularity = min(100, winner.popularity + 2)
        if loser.trait == "Fan Favourite" and random.random() < 0.35:
            loser.popularity = min(100, loser.popularity + 1)
        recurrence = getattr(loser, "serious_injury_recurrence", 0)
        injury_chance = 0.07 + loser.injury_proneness / 420 + max(0, loser.fatigue - 35) / 500 + recurrence / 1500
        if random.random() < injury_chance:
            loser.injured = random.randint(1, 3)
            loser.available_week = max(getattr(loser, "available_week", 0), self.calendar_week_index() + loser.injured * 4)
        serious_chance = 0.0008 + loser.injury_proneness / 80_000 + max(0, loser.age - 33) / 12_000 + recurrence / 30_000
        if method == "Injury Stoppage":
            serious_chance += 0.012
        if random.random() < serious_chance:
            self.apply_serious_injury(loser, "fight injury")
        self.clear_post_fight_preparation(winner, loser)
        championship_won = False
        if fight.get("special_belt"):
            belt_name = fight["special_belt"]
            if self.award_special_belt(belt_name, winner, loser, method):
                championship_won = True
                self.news.insert(0, f"{winner.name} won the {belt_name} championship after beating {loser.name}.")
        divisional_title = bool(fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")))
        if divisional_title and fight.get("interim"):
            championship_won = True
            self.interim_belts, self.belt_history = self.set_interim_champion(self.roster, self.interim_belts, self.belt_history, winner, f"Defeated {loser.name} by {method}.")
            self.news.insert(0, f"{winner.name} won the interim {winner.gender} {winner.weight} title after beating {loser.name}.")
        elif divisional_title:
            championship_won = True
            key = self.belt_key(winner.gender, winner.weight)
            self.belts, self.belt_history = self.set_primary_champion(self.roster, self.belts, self.belt_history, winner, f"Defeated {loser.name} by {method}.", defense=True)
            if self.interim_title_participates(self.interim_belts, winner, loser):
                self.interim_belts, self.belt_history = self.clear_interim_belt(self.roster, self.interim_belts, self.belt_history, key, "Unified with the primary title.")
            self.news.insert(0, f"{winner.name} is now the {winner.gender} {winner.weight} champion after beating {loser.name}.")
            # Champion's clause: winning/holding the belt auto-extends the deal.
            if getattr(winner, "champions_clause", False) and winner in self.roster and not getattr(winner, "comeback_contract", False):
                winner.contract_months = max(winner.contract_months, 12)
                self.news.insert(0, f"{winner.name}'s champion's clause automatically extends their contract while they hold the belt.")
            winner.owed_title_shot = False
        if championship_won:
            winner.title_shots += 1
        if divisional_title:
            # A divisional title fight fulfils an owed title-shot clause for BOTH
            # fighters, win or lose: the guaranteed shot has been granted, so stop
            # the alert and consume the one-time clause instead of re-triggering it.
            for participant in (winner, loser):
                if getattr(participant, "owed_title_shot", False) or getattr(participant, "title_shot_clause", False):
                    participant.owed_title_shot = False
                    participant.title_shot_clause = False
                    self.resolve_title_shot_inbox(participant)
                arc = self.active_career_arc(participant)
                if arc and arc.get("type") == "Veteran Final Run":
                    self.complete_career_arc(participant, "They received a final championship opportunity on merit.")
            winner_arc = self.active_career_arc(winner)
            if winner_arc and winner_arc.get("type") == "Homegrown Champion" and winner.champion:
                self.complete_career_arc(winner, "The academy graduate became the promotion's first homegrown champion.")
        # Title-shot clause: a win in a NON-title fight earns a guaranteed future shot.
        elif getattr(winner, "title_shot_clause", False) and winner in self.roster and not winner.champion:
            if not getattr(winner, "owed_title_shot", False) and not self.has_unresolved_title_shot_inbox(winner):
                winner.owed_title_shot = True
                self.inbox.append({
                    "subject": f"Title Shot Owed - {winner.name}",
                    "body": f"{winner.name}'s contract guarantees a title shot, and they have earned it with a win over {loser.name}. Book them in a {winner.gender} {winner.weight} title fight.",
                    "type": "Contract", "resolved": False,
                })
        self.evaluate_fight_achievements(winner, loser, fight, method, self.fighter_company_name(winner))
        if not fight.get("_defer_retirement"):
            self.retire_after_final_fight_if_due(winner, self.fighter_company_name(winner))
            self.retire_after_final_fight_if_due(loser, self.fighter_company_name(loser))

    def apply_draw_result(self, a, b, fight):
        self.record_career_arc_result((a, b), fight)
        self.record_bout_rating_history(a, b, "D", "D", fight)
        self.complete_fight_observation(a)
        self.complete_fight_observation(b)
        self.update_draw_elo(a, b, fight)
        self.commit_career_stats(a)
        self.commit_career_stats(b)
        a.record_d = getattr(a, "record_d", 0) + 1
        b.record_d = getattr(b, "record_d", 0) + 1
        self.record_contract_fight_completion(a)
        self.record_contract_fight_completion(b)
        a.career_win_streak = 0
        b.career_win_streak = 0
        self.stamp_last_fight_date(a, b)
        a.momentum = max(-5, min(5, a.momentum))
        b.momentum = max(-5, min(5, b.momentum))
        a.morale = min(100, a.morale + random.randint(0, 3))
        b.morale = min(100, b.morale + random.randint(0, 3))
        self.register_draw_popularity(a, b, fight)
        a.fatigue = min(100, a.fatigue + random.randint(18, 34))
        b.fatigue = min(100, b.fatigue + random.randint(18, 34))
        self.set_post_fight_recovery(a, "Decision", lost=False)
        self.set_post_fight_recovery(b, "Decision", lost=False)
        self.clear_post_fight_preparation(a, b)
        a.rank_score = self.rank_value(a)
        b.rank_score = self.rank_value(b)
        result_line = f"Month {self.month} Week {self.week}: {a.name} and {b.name} fought to a draw"
        for fighter in (a, b):
            self.add_fight_history_entry(fighter, result_line)
            fighter.last_fight = result_line
        heat = self.rivalry_heat_between(a, b)
        if heat:
            next_heat = min(100, heat + random.randint(22, 38))
            for fighter in (a, b):
                fighter.rivalry_heat = next_heat
                fighter.rivalry_rematch_due = True
                fighter.rivalry_last_month = self.month
                fighter.rivalry_history = (fighter.rivalry_history or [])[-39:] + [f"Month {self.month}: Draw with {b.name if fighter is a else a.name}; rematch demand intensifies. Heat now {next_heat}/100."]
        else:
            heat = 42 + (10 if fight.get("main") or fight.get("title") else 0)
            if self.establish_rivalry(a, b, "Unsettled draw", heat=heat, rematch_due=True):
                for fighter in (a, b):
                    opponent = b.name if fighter is a else a.name
                    fighter.rivalry_history = (fighter.rivalry_history or [])[-39:] + [
                        f"Month {self.month}: Draw with {opponent}; both camps want a rematch. Heat now {fighter.rivalry_heat}/100."
                    ]
        if fight.get("special_belt"):
            self.news.insert(0, f"The {fight['special_belt']} title fight between {a.name} and {b.name} ended in a draw; the holder remains unchanged.")
        if fight.get("divisional_title", fight.get("title") and not fight.get("special_belt")):
            title_kind = "interim title" if fight.get("interim") else "title"
            self.news.insert(0, f"The {a.gender} {a.weight} {title_kind} fight between {a.name} and {b.name} ended in a draw; title status remains unchanged.")
        if not fight.get("_defer_retirement"):
            self.retire_after_final_fight_if_due(a, self.fighter_company_name(a))
            self.retire_after_final_fight_if_due(b, self.fighter_company_name(b))

    def update_elo(self, winner, loser, fight, method):
        winner_elo = getattr(winner, "elo_rating", 1500)
        loser_elo = getattr(loser, "elo_rating", 1500)
        expected = 1 / (1 + 10 ** ((loser_elo - winner_elo) / 400))
        stakes = 1.25 if fight.get("title") else 1.1 if fight.get("main") else 1.0
        finish = 1.12 if method != "Decision" else 1.0
        k = round(28 * stakes * finish)
        delta = max(6, round(k * (1 - expected)))
        winner.elo_rating = max(900, min(2400, winner_elo + delta))
        loser.elo_rating = max(900, min(2400, loser_elo - delta))

    def update_draw_elo(self, a, b, fight):
        """Apply the standard 0.5 result to both fighters after an official draw."""
        a_elo = getattr(a, "elo_rating", 1500)
        b_elo = getattr(b, "elo_rating", 1500)
        expected_a = 1 / (1 + 10 ** ((b_elo - a_elo) / 400))
        stakes = 1.25 if fight.get("title") else 1.1 if fight.get("main") else 1.0
        delta = round(28 * stakes * (0.5 - expected_a))
        a.elo_rating = max(900, min(2400, a_elo + delta))
        b.elo_rating = max(900, min(2400, b_elo - delta))

    def clear_post_fight_preparation(self, *fighters):
        """Remove single-bout camp and weigh-in state once an official result exists."""
        for fighter in fighters:
            fighter.camp_boost = 0
            fighter.camp_weeks = 0
            fighter.weight_cut_penalty = 0
            fighter.missed_weight = False

    def calculate_revenue(self, total_hype, venue=None):
        venue_factor = {
            "Local Gym": 1100,
            "Regional Arena": 1850,
            "Casino Ballroom": 2400,
            "National Sports Hall": 3300,
            "National Stadium": 5600,
            "Mega Stadium": 8200,
            "Historic Amphitheatre": 3900,
            "Ceremonial Capital Grounds": 3000,
            "White House South Lawn": 2400,
        }.get(venue or self.venue.get(), 1850)
        sponsor = 15000 + self.company_pop * 700
        return round(total_hype * venue_factor + sponsor)

    def venue_capacity_for(self, venue):
        return {
            "Local Gym": 900,
            "Regional Arena": 4200,
            "Casino Ballroom": 7500,
            "National Sports Hall": 14500,
            "National Stadium": 55000,
            "Mega Stadium": 90000,
            "Historic Amphitheatre": 22000,
            "Ceremonial Capital Grounds": 12000,
            "White House South Lawn": 2800,
        }.get(venue, 4200)

    def available_event_venues(self):
        base = ["Local Gym", "Regional Arena", "Casino Ballroom", "National Sports Hall"]
        unlocked = set(self.company_unlocked_milestone_ids()) if hasattr(self, "company_unlocked_milestone_ids") else set()
        if "national_power" in unlocked:
            base.append("National Stadium")
        if "major_organisation" in unlocked:
            base.extend(["Mega Stadium", "Historic Amphitheatre"])
        if "combat_sports_institution" in unlocked:
            base.append("Ceremonial Capital Grounds")
        if "legacy_empire" in unlocked:
            base.append("White House South Lawn")
        return base

    def fight_excitement(self, a, b, winner, loser, method, round_no, fight, hype):
        finish = 12 if "KO" in method or "TKO" in method or "Submission" in method else 2
        late = round_no * (3 if fight.get("main") or fight.get("title") else 2)
        upset = 0 if method == "Draw" else 9 if loser.overall > winner.overall + 4 else 0
        danger_styles = max(0, a.power + b.power + a.submissions + b.submissions - 260) * 0.05
        close_match = max(0, 16 - abs(a.overall - b.overall))
        return max(1, min(99, round(hype * 0.36 + finish + late + upset + danger_styles + close_match)))

    def regional_market_score(self, region):
        data = self.regions.get(region, {})
        economy = data.get("economy", "stable")
        economy_factor = {
            "struggling but improving": 0.86,
            "below average but improving": 0.94,
            "stable": 1.0,
            "strong": 1.12,
            "booming": 1.24,
        }.get(economy, 1.0)
        home_bonus = 1.08 if region == self.player_region else 0.98
        love_factor = 0.72 + data.get("mma_love", 50) / 100
        benefit = data.get("promo_benefit", REGION_PROMO_BENEFITS.get(region, {"media": 1.0, "gate": 1.0}))
        local_roster = len([fighter for fighter in self.roster if fighter.region == region])
        roster_factor = min(1.18, 1 + local_roster * 0.012)
        legality = data.get("legality", "")
        legal_factor = 0.9 if "restricted" in legality else 1.0
        return max(0.62, min(1.65, economy_factor * home_bonus * roster_factor * legal_factor * love_factor * benefit.get("gate", 1.0)))

    def event_atmosphere(self, event, results=None, excitement_score=50):
        """Describe the crowd and return small, explainable event modifiers."""
        region = event.get("region", self.player_region)
        data = self.regions.get(region, {})
        fanbase = getattr(self, "fanbase", {}) or {}
        names = [name for fight in event.get("fights", []) for name in fight.get("fighters", [])]
        fighters = [self.get_fighter(name) for name in names if name != "TBA"]
        connections = [self.fighter_event_connection(fighter, region, event.get("city", "")) for fighter in fighters if fighter]
        local_fighters = sum(1 for connection in connections if connection["strength"] >= 0.52)
        hometown_fighters = sum(1 for connection in connections if connection["level"] == "Hometown")
        home_pull = sum(connection["strength"] * (0.42 + connection["market_popularity"] / 145) for connection in connections)
        finishes = sum(1 for _winner, _loser, _fight, method in (results or []) if method not in ("Decision", "Draw"))
        preference = data.get("crowd_preference", "Competitive fights")
        love = data.get("mma_love", 50)
        core = fanbase.get("core_support", 42)
        casual = fanbase.get("casual_reach", 30)
        local_lift = min(0.18, home_pull * 0.030)
        finish_lift = min(0.09, finishes * 0.018) if any(word in preference.lower() for word in ("action", "finish", "aggressive")) else min(0.04, finishes * 0.008)
        technical_lift = min(0.06, max(0, excitement_score - 55) / 400) if any(word in preference.lower() for word in ("technical", "skill", "respect")) else 0
        home_lift = (core - 42) / 700 if region == fanbase.get("home_region", self.player_region) else 0
        intensity = max(15, min(100, round(love * 0.58 + core * 0.2 + casual * 0.12 + home_pull * 7 + hometown_fighters * 4 + excitement_score * 0.12)))
        mood = "Electric" if intensity >= 78 else "Loud" if intensity >= 62 else "Engaged" if intensity >= 46 else "Reserved"
        attendance_factor = max(0.84, min(1.18, 0.93 + intensity / 1200 + local_lift + technical_lift))
        merch_factor = max(0.84, min(1.22, 0.9 + intensity / 900 + local_lift + finish_lift))
        sponsor_factor = max(0.9, min(1.13, 0.94 + casual / 1000 + intensity / 1800))
        return {"mood": mood, "intensity": intensity, "identity": data.get("fan_identity", "Local MMA community"), "preference": preference,
                "attendance_factor": attendance_factor, "merch_factor": merch_factor, "sponsor_factor": sponsor_factor,
                "local_fighters": local_fighters, "hometown_fighters": hometown_fighters, "home_pull": round(home_pull, 2),
                "description": f"{mood} {data.get('fan_identity', 'local MMA')} crowd; they respond to {preference.lower()}."}

    def update_player_fanbase(self, package):
        """Carry each player event forward as a fanbase story, not an isolated gate number."""
        fanbase = getattr(self, "fanbase", {}) or {}
        finance = package.get("finance", {}) or {}
        atmosphere = finance.get("atmosphere", {}) or {}
        attendance_ratio = finance.get("attendance", 0) / max(1, finance.get("venue_capacity", 1))
        excitement = package.get("average_excitement", 50)
        core_delta = (2 if excitement >= 62 else -1 if excitement < 42 else 0) + (1 if attendance_ratio >= 0.9 else 0)
        casual_delta = (2 if attendance_ratio >= 0.9 else 0) + (1 if package.get("profit", 0) > 0 else -1)
        fanbase["core_support"] = max(5, min(100, fanbase.get("core_support", 42) + core_delta))
        fanbase["casual_reach"] = max(5, min(100, fanbase.get("casual_reach", 30) + casual_delta))
        fanbase["event_history"] = ([{"month": self.month, "event": package.get("event_name", "Event"), "mood": atmosphere.get("mood", "Engaged"), "intensity": atmosphere.get("intensity", 50), "attendance": finance.get("attendance", 0)}] + fanbase.get("event_history", []))[:30]
        self.fanbase = fanbase

    def calculate_event_finance(self, total_hype, fighter_pay, event, results, excitement_score=50, build_score=50, regional_pull=1.0, contracted_fighter_pay=None):
        # PLAYER-ONLY: this method is used exclusively for the player's shows (AI
        # promotions have their own revenue path). A promotion pays fight-night
        # purses scaled to its commercial stature: a small, low-drawing show cannot
        # pay full headline money, so early cards stay survivable instead of bleeding
        # money every time. As popularity and stability grow the payout climbs toward
        # the fighters' full contract value. Stored contract purses are untouched.
        pay_scale = max(0.34, min(1.0, 0.12 + self.company_pop / 128 + self.company_stability / 640))
        contracted_fighter_pay = fighter_pay if contracted_fighter_pay is None else contracted_fighter_pay
        fighter_pay = round(fighter_pay * pay_scale)
        contracted_fighter_pay = round(contracted_fighter_pay * pay_scale)
        tier_purse_savings = max(0, contracted_fighter_pay - fighter_pay)
        venue_capacity = self.venue_capacity_for(event["venue"])
        super_event = event.get("super_event", {}) or {}
        novelty = float(super_event.get("novelty", 1.0) or 1.0)
        spectacle_multiplier = float(super_event.get("revenue_multiplier", 1.0) or 1.0) * novelty
        media_heat = max(0.58, min(1.28, 0.64 + build_score / 165 + excitement_score / 260))
        attendance_demand = total_hype * (24 + self.company_pop * 0.82 + self.company_stability * 0.22) / 14
        atmosphere = self.event_atmosphere(event, results, excitement_score)
        attendance = min(venue_capacity, max(120, round(attendance_demand * regional_pull * media_heat * atmosphere["attendance_factor"] * (1 + max(0, spectacle_multiplier - 1) * 0.16))))
        sellout_pressure = attendance / max(1, venue_capacity)
        ticket_price = round(self.finance["ticket_price"] * (0.9 + regional_pull * 0.12 + sellout_pressure * 0.18))
        ticket_revenue = round(attendance * ticket_price * self.engine_settings.get("gate_multiplier", 1.0) * spectacle_multiplier)
        selected_name = event.get("broadcaster", "No Coverage")
        best_broadcaster = next((b for b in self.broadcasters if b["name"] == selected_name), None)
        if best_broadcaster is None:
            best_broadcaster = {"name": "No Coverage", "reach": 0, "fee": 0, "type": "None"}
        self.ensure_finance_defaults()
        rights = self.finance["media_rights"]
        sponsor_deals = self.finance["sponsor_deals"]
        commentators = self.finance.get("commentators", [])
        commentary_quality = round(sum(c["quality"] + c["chemistry"] for c in commentators) / max(1, len(commentators)) / 2)
        championship_value = 0
        for _winner, _loser, fight, _method in results:
            if fight.get("title"):
                championship_value += 18
            for name in fight.get("fighters", []):
                fighter = self.get_fighter(name)
                if fighter.champion:
                    championship_value += 6 + fighter.star_quality // 12
        contracted_events = rights.get("events_remaining", 0)
        rights_eligible = bool(contracted_events > 0 and selected_name != "No Coverage")
        if hasattr(self, "media_contract_eligibility") and rights_eligible:
            rights_eligible = self.media_contract_eligibility(rights, event)[0]
        rights_reach = rights.get("reach", 0) if rights_eligible else 0
        media_reach = best_broadcaster["reach"] + rights_reach + championship_value // 2 + commentary_quality // 8
        if not best_broadcaster["reach"] and not rights_reach:
            media_reach = max(2, championship_value // 4)
        broadcast_income = round(total_hype * media_reach * self.finance["broadcast_cut"] * (38 + build_score * 0.68 + championship_value * 0.7) * media_heat * (1 + commentary_quality / 650) * spectacle_multiplier)
        sponsorship = round((self.finance["sponsor_income"] + sum(deal["fee"] for deal in sponsor_deals) + round(self.company_pop * total_hype * (6 + regional_pull * 3 + build_score / 16))) * atmosphere["sponsor_factor"])
        broadcast_income += rights.get("fee", rights.get("guarantee_per_event", 0)) if rights_eligible else 0
        merchandise = round(ticket_revenue * self.finance["merch_rate"] * (1 + self.company_pop / 130) * (0.85 + excitement_score / 110) * atmosphere["merch_factor"])
        commentator_pay = sum(c["salary"] for c in commentators)
        venue_ops = round(venue_capacity * (5 + self.company_pop / 16))
        bout_count = max(len(event["fights"]), len(results))
        setup_cost = int(super_event.get("remaining_setup_cost", 0) or 0)
        security_cost = int(super_event.get("security_cost", 0) or 0)
        production = self.finance["production_base"] + bout_count * 5200 + best_broadcaster["fee"] + commentator_pay + venue_ops + setup_cost + security_cost
        medical = self.finance["medical_base"] + bout_count * 1900
        marketing = self.finance["marketing_budget"] + round(max(0, build_score - 48) * 1100)
        drug_testing = 0 if self.rules["drug_testing"] == "None" else bout_count * 2 * self.finance["drug_test_cost"]
        bonuses = self.post_show_bonuses["fight"]
        for _winner, _loser, _fight, method in results:
            if "KO" in method or "TKO" in method:
                bonuses += self.post_show_bonuses["ko"]
            if "Submission" in method:
                bonuses += self.post_show_bonuses["sub"]
        total_revenue = ticket_revenue + broadcast_income + sponsorship + merchandise
        pre_tax_expense = fighter_pay + production + medical + marketing + drug_testing + bonuses
        tax = round(max(0, total_revenue - pre_tax_expense) * self.finance["tax_rate"])
        total_expense = pre_tax_expense + tax
        return {
            "attendance": attendance,
            "atmosphere": atmosphere,
            "venue_capacity": venue_capacity,
            "ticket_price": ticket_price,
            "media_reach": media_reach,
            "championship_media_value": championship_value,
            "commentary_quality": commentary_quality,
            "regional_pull": regional_pull,
            "excitement_score": round(excitement_score),
            "build_score": round(build_score),
            "ticket_revenue": ticket_revenue,
            "broadcast_income": broadcast_income,
            "sponsorship": sponsorship,
            "merchandise": merchandise,
            "total_revenue": total_revenue,
            "fighter_pay": fighter_pay,
            "contracted_fighter_pay": contracted_fighter_pay,
            "tier_purse_savings": tier_purse_savings,
            "bonuses": bonuses,
            "production": production,
            "super_event_setup": setup_cost + security_cost,
            "super_event_novelty": novelty,
            "medical": medical,
            "marketing": marketing,
            "drug_testing": drug_testing,
            "tax": tax,
            "total_expense": total_expense,
            "profit": total_revenue - total_expense,
        }

    def request_advance_week(self):
        """UI command for one responsive week of world simulation."""
        return self.begin_advance_sequence(1, status_prefix="Advancing week")

    def monthly_player_business_steps(self):
        """Return the player's month-end tasks as independently paintable work."""
        if getattr(self, "spectator_mode", False):
            return []

        def update_morale():
            changed = 0
            total_delta = 0
            for fighter in self.roster:
                old = fighter.morale
                fighter.morale = max(10, fighter.morale - 2)
                changed += fighter.morale != old
                total_delta += fighter.morale - old
            if changed:
                self.record_change("Morale", f"Roster total ({changed} fighters)", total_delta, "Routine month-end morale drift; bouts, promises and bonuses can offset it")

        def pay_overhead():
            payroll = sum(s["salary"] for s in self.staff)
            overhead = self.finance["monthly_office"] + payroll
            self.cash -= overhead
            self.record_finance_transaction("Monthly office and payroll", costs=overhead)
            self.finance["ledger"].insert(0, f"Month {self.month}: Monthly overhead ${overhead:,} (office ${self.finance['monthly_office']:,}, payroll ${payroll:,})")
            self.event_log.insert(0, f"Month {self.month}: overhead paid. Injured fighters recovered one month.")

        return [
            ("Player roster morale", update_morale),
            ("Office and payroll", pay_overhead),
            ("Business agreements", self.tick_business_deals),
        ]

    def calendar_week_steps(self, include_autosave=True):
        """Build one calendar week's ordered work without touching Tk widgets."""
        month_changed = self.week >= 4
        completed_month = self.month
        old_year = 2026 + (self.month - 1) // 12
        steps = list(self.world_week_steps())

        if not month_changed:
            steps.append(("Updating the calendar", lambda: setattr(self, "week", self.week + 1)))
        else:
            def roll_month():
                self.week = 1
                self.month += 1

            steps.append(("Starting the next month", roll_month))
            steps.extend(self.world_month_steps(self.player_ran_show_in_month(completed_month)))
            new_year = 2026 + completed_month // 12
            if new_year != old_year:
                steps.append((f"{old_year} awards", lambda old_year=old_year: self.run_end_of_year_awards(old_year)))
                steps.append(("Aging the world", self.age_world_one_year))
                steps.append(("Year-end regional call-ups", self.promote_year_end_regional_candidates))
            steps.extend(self.monthly_player_business_steps())

        interval = max(1, int(self.rules.get("autosave_interval_months", 2)))
        autosave_due = (
            month_changed
            and completed_month % interval == 0
            and self.rules.get("autosave_enabled", True)
            and not getattr(self, "suppress_autosaves", False)
        )
        if include_autosave and autosave_due and hasattr(self, "run_automatic_save_cycle"):
            steps.append((
                "Creating autosave",
                lambda month_changed=month_changed: self.run_automatic_save_cycle(month_changed=month_changed),
            ))
        if month_changed and getattr(self, "spectator_mode", False) and hasattr(self, "write_spectator_decade_snapshot"):
            steps.append(("Archiving spectator decade", self.write_spectator_decade_snapshot))
        return steps, month_changed

    def advance_month(self):
        """Synchronously advance one week for tests, audits, and non-UI callers."""
        if any(self.is_event_due(event) for event in self.scheduled_events):
            self.prompt_due_event()
            return
        steps, _month_changed = self.calendar_week_steps(include_autosave=True)
        for _label, task in steps:
            task()
        self.refresh_all()
        self.write_log()
        self.prompt_due_event()

    def begin_advance_sequence(self, weeks=1, status_prefix="Advancing", on_complete=None, stop_condition=None):
        """Advance cooperatively through Tk's event queue so the app stays responsive."""
        if getattr(self, "_advance_in_progress", False):
            return False
        if any(self.is_event_due(event) for event in self.scheduled_events):
            self.prompt_due_event()
            return False
        weeks = max(1, int(weeks))
        self._advance_in_progress = True
        self._advance_job = {
            "total": weeks,
            "completed": 0,
            "steps": [],
            "step_index": 0,
            "prefix": status_prefix,
            "on_complete": on_complete,
            "stop_condition": stop_condition,
            "previous_award_suppression": getattr(self, "suppress_award_popups", False),
        }
        if getattr(self, "spectator_mode", False):
            self.suppress_award_popups = True
        self.set_advance_ui_busy(True, f"{status_prefix}: preparing world", 0)
        self.root.after(20, self._begin_queued_week)
        return True

    def _begin_queued_week(self):
        job = getattr(self, "_advance_job", None)
        if not job:
            return
        try:
            next_week = job["completed"] + 1
            month_changed = self.week >= 4
            # Automatic saves are considered only at month boundaries. The save
            # cycle itself enforces the configured two-month cadence.
            include_autosave = month_changed
            job["steps"], _ = self.calendar_week_steps(include_autosave=include_autosave)
            job["step_index"] = 0
            self._run_next_advance_step()
        except Exception:
            self._fail_advance_sequence(*sys.exc_info())

    def _run_next_advance_step(self):
        job = getattr(self, "_advance_job", None)
        if not job:
            return
        try:
            if job["step_index"] >= len(job["steps"]):
                job["completed"] += 1
                should_stop = bool(job.get("stop_requested")) or bool(job["stop_condition"] and job["stop_condition"]())
                if should_stop or job["completed"] >= job["total"]:
                    self.root.after(1, self._finish_advance_sequence)
                else:
                    self.root.after(1, self._begin_queued_week)
                return

            label, task = job["steps"][job["step_index"]]
            fraction = (job["completed"] + job["step_index"] / max(1, len(job["steps"]))) / job["total"]
            status = f"{job['prefix']} {job['completed'] + 1}/{job['total']}: {label}"
            self.set_advance_ui_progress(status, fraction * 100)
            task()
            job["step_index"] += 1
            self.root.after(1, self._run_next_advance_step)
        except Exception:
            self._fail_advance_sequence(*sys.exc_info())

    def _finish_advance_sequence(self):
        job = getattr(self, "_advance_job", None)
        if not job:
            return
        try:
            self.set_advance_ui_progress("Refreshing screens", 99)
            self.refresh_all()
            self.write_log()
            callback = None if job.get("stop_requested") else job.get("on_complete")
            self._complete_advance_cleanup()
            if not getattr(self, "spectator_mode", False):
                self.show_final_month_contract_alerts()
                self.prompt_due_event()
            if callback:
                callback()
        except Exception:
            self._fail_advance_sequence(*sys.exc_info())

    def _complete_advance_cleanup(self):
        job = getattr(self, "_advance_job", None) or {}
        self.suppress_award_popups = job.get("previous_award_suppression", getattr(self, "suppress_award_popups", False))
        self._advance_job = None
        self._advance_in_progress = False
        self.set_advance_ui_busy(False, "Ready", 100)

    def _fail_advance_sequence(self, exc_type, exc_value, exc_tb):
        self._complete_advance_cleanup()
        if hasattr(self, "handle_uncaught_exception"):
            self.handle_uncaught_exception(exc_type, exc_value, exc_tb)
        else:
            raise exc_value.with_traceback(exc_tb)

    def player_ran_show_in_month(self, month):
        """Return whether the player completed a recorded event in a month.

        Deriving this from result records keeps old saves compatible and avoids a
        transient flag being lost when a game is saved between the show and the
        end-of-month rollover.
        """
        marker = f"Month {int(month)} "
        return any(
            record.get("company") == self.player_company_name
            and marker in str(record.get("date", ""))
            for record in getattr(self, "result_records", [])
        )
    def world_week_steps(self):
        """Small, ordered world tasks usable by sync and responsive UI advances."""
        steps = [
            ("Scouting reports", self.process_scouting_reports),
            ("Academy training", self.process_academy_week),
            ("Rebooking cancelled bouts", self.process_pending_rebookings),
            ("Regional interest", self.fluctuate_region_interest),
            ("Fighter stories", self.random_fighter_events),
            ("World activity", self.generate_weekly_world_activity),
            ("Rivalries and media", self.process_rivalry_activity),
            ("AI staff market", self.simulate_ai_staff_market),
        ]
        if self.month == 1 and self.week == 1 and not self.rules.get("opening_division_depth_seeded", False):
            steps.append(("Opening division depth", self.seed_opening_ai_division_depth))
        for promo in list(self.promotions):
            steps.append((
                f"{promo.name} booking",
                lambda promo=promo: self.simulate_ai_promotion_month(promo) if self.ai_should_run_show(promo) else None,
            ))
        for index in range(self.independent_showcases_due()):
            steps.append((f"Independent showcase {index + 1}", self.simulate_free_agent_showcases))
        steps.extend([
            ("Transfer market", lambda: self.market_churn() if random.random() < 0.22 else None),
            ("Outside fights", lambda: self.simulate_nonexclusive_outside_fights() if random.random() < 0.18 else None),
        ])
        if not getattr(self, "spectator_mode", False):
            steps.append(("Weekly finances", self.close_finance_week))
        steps.append(("Finalising world news", lambda: setattr(self, "news", self.news[:160])))
        return steps

    def seed_opening_ai_division_depth(self):
        """One-time opening-week depth contracts for imported or thin databases."""
        if self.rules.get("opening_division_depth_seeded", False):
            return 0
        self.rules["opening_division_depth_seeded"] = True
        additions = []
        for promo in [item for item in self.promotions if not getattr(item, "is_regional_feeder", False)]:
            weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
            for gender in ("Male", "Female"):
                for weight in weights:
                    if not self.promotion_division_open(promo, gender, weight):
                        continue
                    division = [fighter for fighter in promo.roster if not fighter.retired and fighter.gender == gender and fighter.weight == weight]
                    while len(division) < 6:
                        candidates = [
                            fighter for fighter in self.free_agents
                            if not fighter.retired and not fighter.injured and fighter.gender == gender and fighter.weight == weight
                            and fighter.overall <= 66
                        ]
                        if not candidates:
                            candidates = [
                                fighter for fighter in self.free_agents
                                if not fighter.retired and not fighter.injured and fighter.gender == gender and fighter.weight == weight
                                and fighter.overall <= 72
                            ]
                        if candidates:
                            desired = max(50, min(64, promo.size - 18))
                            candidates.sort(key=lambda fighter: (abs(fighter.overall - desired), fighter.potential, fighter.age))
                            fighter = random.choice(candidates[:min(12, len(candidates))])
                            self.free_agents.remove(fighter)
                        else:
                            fighter = self.create_generated_fighter(2, 14, 42, 58, weight=weight, gender=gender, region=promo.region)
                            self.avoid_name_collision(fighter, self.active_fighter_names())
                            fighter.potential = min(76, max(fighter.overall + 3, fighter.potential))
                        fighter.purse = max(1_500, min(8_000, round(max(1_500, fighter.purse) / 500) * 500))
                        fighter.contract_months = random.randint(6, 10)
                        fighter.contract_type = "Depth Contract"
                        fighter.exclusive = True
                        fighter.ai_offer_company = ""
                        fighter.ai_offer_purse = 0
                        fighter.ai_offer_months = 0
                        fighter.ai_offer_signing_bonus = 0
                        fighter.ai_offer_deadline_month = 0
                        fighter.free_agent_months = 0
                        fighter.camp = self.suggest_camp_for_fighter(fighter, promo.region)
                        promo.roster.append(fighter)
                        division.append(fighter)
                        additions.append((promo.name, fighter.name))
        if additions:
            summary = ", ".join(f"{name} ({sum(1 for company, _fighter in additions if company == name)})" for name in dict.fromkeys(company for company, _fighter in additions))
            headline = f"Opening roster stabilization: short-term depth contracts completed for {summary}."
            self.news.insert(0, headline)
            self.record_world_story("Opening Roster Depth", headline, "Each affected gender and weight class was brought to a six-fighter booking floor. These low-cost depth contracts expire quickly.", list(dict.fromkeys(company for company, _fighter in additions)), [fighter for _company, fighter in additions[:12]], 3)
        return len(additions)

    def process_world_week(self):
        for _label, task in self.world_week_steps():
            task()

    def process_pending_rebookings(self):
        """Move a cancelled bout to an existing future card or let it fall away."""
        pending = list(getattr(self, "pending_rebookings", []))
        outcomes = []
        for entry in pending:
            names = entry.get("fighters", [])
            fighters = [self.get_fighter(name) for name in names]
            future_cards = sorted(
                (event for event in self.scheduled_events
                 if (event.get("month", 1), event.get("week", 1)) > (self.month, self.week)
                 and len(event.get("fights", [])) < 16),
                key=lambda event: (event.get("month", 1), event.get("week", 1)),
            )
            target = None
            if len(fighters) == 2 and all(fighter is not None and not fighter.injured for fighter in fighters):
                for candidate in future_cards:
                    already_booked = {
                        name for fight in candidate.get("fights", [])
                        for name in self.event_fight_participants(fight) if name != "TBA"
                    }
                    if (not (set(names) & already_booked)
                            and all(self.fighter_available_for_date(fighter, candidate.get("month", self.month), candidate.get("week", 1)) for fighter in fighters)):
                        target = candidate
                        break
            if target:
                fight = {"fighters": list(names), "title": False, "interim": False, "main": False, "tier": entry.get("tier", "Main Card")}
                target["fights"].append(fight)
                self.normalize_card_order(target["fights"])
                self.assign_event_camps({"month": target["month"], "week": target.get("week", 1), "fights": [fight]})
                note = f"{names[0]} vs {names[1]} moved to {target['name']} after its weigh-in cancellation."
                subject = "Cancelled Bout Moved"
            else:
                note = f"{' vs '.join(names)} was not rebooked because no suitable future player card was available."
                subject = "Cancelled Bout Dropped"
            self.pending_rebookings.remove(entry)
            self.inbox.append({"subject": subject, "body": note, "type": "Roster", "resolved": False})
            self.news.insert(0, note)
            outcomes.append(note)
        return outcomes

    def academy_defaults(self):
        return {
            "schema_version": 4,
            "owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [],
            "weekly_cost": 0, "auto_train": True, "network_weeks": 0, "network_active": False,
            "network_region": "", "network_scout": "", "network_scout_skill": 0,
            "showcase_weeks": 0, "auto_showcases": True, "auto_card_min_bouts": 2, "last_scout_report": "",
            "philosophy": "Balanced MMA", "reputation": 10, "card_history": [], "alumni": [],
            "total_cards": 0, "total_bouts": 0, "total_graduates": 0, "build_spend": 0, "operating_spend": 0,
            "signing_spend": 0, "upgrade_spend": 0, "network_spend": 0,
            "lost_leads": [], "last_alumni_review_month": 0,
            "network_potential_skill": 0, "network_networking": 0, "network_reliability": 0,
            "network_leads_found": 0, "last_showcase_week": -99, "last_showcase_recap": "",
            "development_events": [],
        }

    def repair_academy(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        previous_schema = int(academy.get("schema_version", 1) or 1)
        for key, value in self.academy_defaults().items():
            academy.setdefault(key, value if not isinstance(value, list) else [])
        if academy.get("owned"):
            academy["capacity"] = max(8, academy.get("capacity", 8))
            academy["weekly_cost"] = max(4500, academy.get("weekly_cost", 4500))
            academy["reputation"] = max(1, min(100, int(academy.get("reputation", 10))))
        academy["card_history"] = list(academy.get("card_history", []))[:24]
        academy["alumni"] = list(academy.get("alumni", []))[:100]
        academy["lost_leads"] = list(academy.get("lost_leads", []))[:30]
        academy["total_cards"] = max(int(academy.get("total_cards", 0)), len(academy["card_history"]))
        if academy["card_history"] and not academy.get("total_bouts"):
            academy["total_bouts"] = sum(len(card.get("results", [])) for card in academy["card_history"])
        for prospect in academy.get("prospects", []) + academy.get("talent_pool", []):
            self.repair_academy_prospect(prospect)
        if previous_schema < 3 and academy.get("owned"):
            # Older saves ran the entire squad every other week. Move the next
            # automatic card onto the balanced youth schedule without deleting
            # any existing records or development.
            academy["showcase_weeks"] = max(6, int(academy.get("showcase_weeks", 8) or 8))
        academy["auto_card_min_bouts"] = max(1, min(12, int(academy.get("auto_card_min_bouts", 2) or 2)))
        academy["schema_version"] = 4
        return academy

    def academy_philosophy_fields(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        return {
            "Balanced MMA": ("striking", "wrestling", "grappling", "cardio", "fight_iq"),
            "Striking Academy": ("striking", "power", "cardio", "chin"),
            "Wrestling Pipeline": ("wrestling", "cardio", "fight_iq", "toughness"),
            "Submission School": ("grappling", "fight_iq", "wrestling", "toughness"),
            "Athletic Development": ("cardio", "power", "toughness", "chin"),
            "Multi-Sport Pathway": ("striking", "wrestling", "grappling", "fight_iq"),
        }.get(academy.get("philosophy", "Balanced MMA"), ("striking", "wrestling", "grappling"))

    def academy_weight_band(self, weight):
        if weight in ("Strawweight", "Flyweight", "Bantamweight"):
            return "Youth Flyweight"
        if weight in ("Featherweight", "Lightweight"):
            return "Youth Lightweight"
        if weight in ("Welterweight", "Middleweight"):
            return "Youth Welterweight"
        return "Youth Heavyweight"

    def academy_region_distance(self, region):
        if region == self.player_region:
            return 0
        visited = {self.player_region}
        frontier = [(self.player_region, 0)]
        while frontier:
            current, distance = frontier.pop(0)
            for linked in REGIONAL_MIGRATION_LINKS.get(current, []):
                if linked == region:
                    return distance + 1
                if linked in REGIONS and linked not in visited:
                    visited.add(linked)
                    frontier.append((linked, distance + 1))
        return 3

    def academy_scouting_network_cost(self, region):
        distance = self.academy_region_distance(region)
        return round((12_000 + self.academy.get("level", 1) * 2_500) * (1 + distance * 0.55))

    def academy_signing_cost(self, prospect):
        distance = self.academy_region_distance(prospect.get("region", self.player_region))
        potential = prospect.get("potential", 70)
        rating = prospect.get("rating", 40)
        upside = max(0, potential - rating)
        high_potential = max(0, potential - 78)
        elite_potential = max(0, potential - 88)
        current = max(0, rating - 35)
        confidence_tax = max(0, prospect.get("scout_confidence", 50) - 55) * 55
        base = 5_500 + current * 135 + upside * 210 + high_potential * 720 + elite_potential * 1_250 + confidence_tax
        reputation_discount = max(0.88, 1 - max(0, self.academy.get("reputation", 10) - 30) / 500)
        return round(base * (1 + distance * 0.42) * reputation_discount)

    def academy_scout_range(self, value, confidence, minimum=1, maximum=99):
        spread = max(2, round((100 - confidence) / 7))
        low = max(minimum, value - random.randint(max(1, spread // 2), spread))
        high = min(maximum, value + random.randint(max(1, spread // 2), spread + 2))
        return low, high

    def academy_skill_defaults(self, prospect):
        rating = prospect.get("rating", 42)
        fields = ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq")
        for index, key in enumerate(fields):
            if key not in prospect:
                # Legacy-save migration must never consume the live simulation RNG.
                noise = self.academy_stable_number(prospect, f"skill-{index}", -8, 8)
                prospect[key] = max(20, min(95, rating + noise))
        return prospect

    def academy_stable_number(self, prospect, salt, minimum, maximum):
        """Return a process-stable value for deterministic old-save repair."""
        text = f"{prospect.get('name', 'Unknown')}|{prospect.get('region', self.player_region)}|{salt}"
        value = sum((index + 1) * ord(char) for index, char in enumerate(text))
        return minimum + value % max(1, maximum - minimum + 1)

    def academy_prospect_id(self, prospect):
        text = f"{prospect.get('name', 'Unknown')}|{prospect.get('region', self.player_region)}|{prospect.get('age', 0)}"
        value = sum((index + 11) * ord(char) for index, char in enumerate(text))
        return f"academy-{value:08x}"

    def repair_academy_prospect(self, prospect):
        # Avoid random-valued setdefault calls here: this repair method is also
        # used by UI refreshes, and merely opening the academy must not advance
        # the global simulation RNG or alter future fight outcomes.
        static_defaults = {
            "name": "Unknown Prospect", "region": self.player_region, "gender": "Male",
            "plan": "Automatic", "amateur_w": 0, "amateur_l": 0, "amateur_d": 0,
            "amateur_history": [], "amateur_bout_records": [], "weeks": 0, "development": 0,
            "fatigue": 0, "injured": 0, "scout_confidence": 45,
            "training_intensity": "Standard", "preferred_sport": "MMA", "rating_history": [],
            "training_log": [], "milestones": [], "last_amateur_bout": {}, "opponent_counts": {},
            "last_amateur_week": -99, "plateau_weeks": 0, "academy_member": False,
            "bout_experience": 0, "last_development": "No recorded gain yet",
            "medical_history": [], "scouting_observations": 0, "signed_cost": 0,
        }
        for key, value in static_defaults.items():
            if key not in prospect:
                prospect[key] = list(value) if isinstance(value, list) else dict(value) if isinstance(value, dict) else value
        if "age" not in prospect:
            prospect["age"] = self.academy_stable_number(prospect, "age", 12, 15)
        if "rating" not in prospect:
            prospect["rating"] = self.academy_stable_number(prospect, "rating", 38, 54)
        if "potential" not in prospect:
            prospect["potential"] = max(prospect["rating"] + 8, self.academy_stable_number(prospect, "potential", 62, 92))
        if "weight" not in prospect:
            prospect["weight"] = WEIGHTS[self.academy_stable_number(prospect, "weight", 0, len(WEIGHTS) - 1)]
        if "weeks_to_sign" not in prospect:
            prospect["weeks_to_sign"] = self.academy_stable_number(prospect, "window", 2, 3)
        if "dedication" not in prospect:
            prospect["dedication"] = self.academy_stable_number(prospect, "dedication", 40, 92)
        if "coachability" not in prospect:
            prospect["coachability"] = self.academy_stable_number(prospect, "coachability", 38, 94)
        if "confidence" not in prospect:
            prospect["confidence"] = self.academy_stable_number(prospect, "confidence", 45, 72)
        prospect.setdefault("prospect_id", self.academy_prospect_id(prospect))
        prospect.setdefault("amateur_weight", self.academy_weight_band(prospect.get("weight", "Lightweight")))
        prospect.setdefault("joined_month", self.month if hasattr(self, "month") else 1)
        prospect.setdefault("baseline_rating", prospect.get("rating", 42))
        self.academy_skill_defaults(prospect)
        if "current_range" not in prospect:
            spread = max(2, round((100 - prospect["scout_confidence"]) / 7))
            prospect["current_range"] = (max(20, prospect["rating"] - spread), min(99, prospect["rating"] + spread))
        if "potential_range" not in prospect:
            spread = max(2, round((100 - prospect["scout_confidence"]) / 7))
            prospect["potential_range"] = (max(45, prospect["potential"] - spread - 1), min(99, prospect["potential"] + spread + 1))
        prospect["signing_cost"] = prospect.get("signing_cost") or self.academy_signing_cost(prospect)
        return prospect

    def create_academy_scout_prospect(self, scout_score=45, region=None):
        region = region or self.player_region
        fighter = self.create_generated_fighter(0, 4, 32, 53, region=region)
        existing = self.active_fighter_names()
        existing.update(item.get("name", "") for item in getattr(self, "academy", {}).get("prospects", []))
        existing.update(item.get("name", "") for item in getattr(self, "academy", {}).get("talent_pool", []))
        self.avoid_name_collision(fighter, existing)
        fighter.age = random.randint(12, 15)
        academy_reputation = getattr(self, "academy", {}).get("reputation", 10)
        confidence = max(30, min(94, round(scout_score + academy_reputation * 0.08 + random.randint(-12, 10))))
        quality_rolls = 1 + int(scout_score >= 70)
        potential_roll = max(random.randint(60, 94) for _ in range(quality_rolls))
        # Scout quality should affect immediate readiness as well as ceiling and
        # report confidence; the tighter scale makes elite networks visibly
        # better at identifying athletes who can contribute sooner.
        quality_shift = round((scout_score - 50) / 10 + (academy_reputation - 20) / 35)
        target_rating = max(30, min(60, fighter.overall + quality_shift + random.randint(-2, 2)))
        stat_shift = target_rating - fighter.overall
        potential_bonus = round((scout_score - 50) / 25 + (academy_reputation - 20) / 55)
        potential = max(target_rating + 8, min(98, potential_roll + potential_bonus))
        # Exceptional academies can occasionally uncover a genuine generational
        # teenager.  This needs both a strong scout and some academy credibility,
        # so 99-100 potential stays a memorable find rather than normal output.
        elite_chance = 0.0
        if scout_score >= 78 and academy_reputation >= 35:
            elite_chance = min(0.055, 0.006 + (scout_score - 78) / 380 + (academy_reputation - 35) / 900)
        if random.random() < elite_chance:
            potential = random.choices((96, 97, 98, 99, 100), weights=(45, 33, 18, 3, 1), k=1)[0]
        prospect = {
            "name": fighter.name, "age": fighter.age, "potential": potential,
            "region": region, "gender": fighter.gender, "weight": fighter.weight,
            "amateur_weight": self.academy_weight_band(fighter.weight), "rating": target_rating,
            "style": fighter.style, "stance": fighter.stance, "trait": fighter.trait,
            "nationality": fighter.nationality, "birth_country": fighter.birth_country,
            "birth_region": fighter.birth_region, "hometown": fighter.hometown, "residence": fighter.residence,
            "training_location": fighter.training_location, "fighting_base": fighter.fighting_base,
            "cultural_connections": fighter.cultural_connections, "regional_popularity": fighter.regional_popularity,
            "scout_confidence": confidence, "weeks_to_sign": random.randint(2, 3),
            "striking": max(20, min(95, fighter.striking + stat_shift)),
            "wrestling": max(20, min(95, fighter.wrestling + stat_shift)),
            "grappling": max(20, min(95, fighter.grappling + stat_shift)),
            "cardio": max(20, min(95, fighter.cardio + stat_shift)),
            "chin": max(20, min(95, fighter.chin + stat_shift)),
            "power": max(20, min(95, fighter.power + stat_shift)),
            "toughness": max(20, min(95, fighter.toughness + stat_shift)),
            "fight_iq": max(20, min(95, fighter.fight_iq + stat_shift)),
            "dedication": random.randint(35, 96), "coachability": random.randint(35, 96),
            "confidence": random.randint(42, 70), "source_network": region,
            "source_scout_quality": round(scout_score),
        }
        prospect["current_range"] = self.academy_scout_range(target_rating, confidence, 20, 99)
        prospect["potential_range"] = self.academy_scout_range(potential, confidence, 45, 99)
        return self.repair_academy_prospect(prospect)

    def refine_academy_lead(self, prospect, academy):
        """Improve report accuracy while a lead remains on the live shortlist."""
        self.repair_academy_prospect(prospect)
        skill = academy.get("network_scout_skill", 45)
        potential_skill = academy.get("network_potential_skill", skill)
        reliability = academy.get("network_reliability", skill)
        distance = self.academy_region_distance(prospect.get("region", self.player_region))
        gain = max(1, round((skill + potential_skill + reliability) / 96 + academy.get("reputation", 10) / 45 - distance * 0.35))
        prospect["scout_confidence"] = min(97, prospect.get("scout_confidence", 45) + gain)
        prospect["scouting_observations"] = prospect.get("scouting_observations", 0) + 1
        spread = max(1, round((101 - prospect["scout_confidence"]) / 8))
        prospect["current_range"] = (max(20, prospect["rating"] - spread), min(99, prospect["rating"] + spread))
        prospect["potential_range"] = (max(45, prospect["potential"] - spread - 1), min(99, prospect["potential"] + spread + 1))
        return prospect

    def academy_lead_report(self, prospect):
        self.repair_academy_prospect(prospect)
        current = prospect.get("current_range", (prospect["rating"], prospect["rating"]))
        potential = prospect.get("potential_range", (prospect["potential"], prospect["potential"]))
        strongest = sorted(("striking", "wrestling", "grappling", "cardio", "power", "fight_iq"), key=lambda key: prospect.get(key, 40), reverse=True)[:3]
        personality_accuracy = prospect.get("scout_confidence", 45)
        personality = (
            f"Dedication approximately {max(20, prospect['dedication'] - (100-personality_accuracy)//8)}-"
            f"{min(99, prospect['dedication'] + (100-personality_accuracy)//8)}; coachability approximately "
            f"{max(20, prospect['coachability'] - (100-personality_accuracy)//8)}-{min(99, prospect['coachability'] + (100-personality_accuracy)//8)}."
        )
        return (
            f"{prospect['name']} — {prospect['gender']} age {prospect['age']} from {prospect['region']}\n\n"
            f"Projected current ability: {current[0]}-{current[1]}\nProjected potential: {potential[0]}-{potential[1]}\n"
            f"Report confidence: {personality_accuracy}% | Signing cost: ${prospect.get('signing_cost', 0):,} | Decision window: {prospect.get('weeks_to_sign', 0)} week(s)\n\n"
            f"Observed strengths: {', '.join(key.replace('_', ' ').title() for key in strongest)}.\n{personality}\n\n"
            f"Likely pathway: {self.academy_preferred_sport(prospect)}. Reports narrow each week while the lead remains available."
        )

    def academy_recruitment_label(self, prospect):
        self.repair_academy_prospect(prospect)
        current = prospect.get("current_range", (prospect.get("rating", 40), prospect.get("rating", 40)))
        potential = prospect.get("potential_range", (prospect.get("potential", 70), prospect.get("potential", 70)))
        gender = str(prospect.get("gender", "")).strip()[:1].upper() or "?"
        return (
            f"{prospect['name']} | {gender} | {prospect['age']} | {prospect['region']} | {prospect['amateur_weight']} | "
            f"Cur {current[0]}-{current[1]} | Pot {potential[0]}-{potential[1]} | "
            f"Conf {prospect.get('scout_confidence', 0)}% | ${prospect.get('signing_cost', 0):,} | {prospect.get('weeks_to_sign', 0)}w"
        )

    def start_academy_network(self, region, scout_name):
        academy = self.repair_academy(getattr(self, "academy", {}))
        if not academy.get("owned"):
            return False, "Build the academy first."
        if academy.get("network_weeks", 0) > 0 or academy.get("network_active"):
            return False, "Cancel the current youth network before setting up a new one."
        scout = next((member for member in self.staff if member.get("role") == "Scout" and member.get("name") == scout_name), None)
        if not scout:
            return False, "Hire a Scout from the Staff screen before establishing a youth network."
        if self.scout_workload(scout_name) >= self.scout_capacity(scout):
            return False, f"{scout_name} has no free assignment slot for an academy network. Finish or cancel another scouting assignment first."
        cost = self.academy_scouting_network_cost(region)
        if self.cash < cost:
            return False, f"Need ${cost:,} to establish a {region} youth scouting network."
        scout_skill = scout.get("fighter_judging", scout.get("skill", 45))
        potential_skill = scout.get("potential_judging", scout.get("skill", 45))
        networking = scout.get("networking", scout.get("skill", 45))
        reliability = round((scout.get("reliability", scout.get("skill", 45)) + scout.get("professionalism", scout.get("skill", 45))) / 2)
        self.cash -= cost
        self.record_finance_transaction(f"Academy scouting network: {region}", costs=cost)
        academy.update({"network_weeks": 8, "network_active": False, "network_region": region, "network_scout": scout_name,
                        "network_scout_skill": round(scout_skill), "network_potential_skill": round(potential_skill),
                        "network_networking": round(networking), "network_reliability": reliability, "talent_pool": []})
        academy["network_spend"] = academy.get("network_spend", 0) + cost
        academy["last_scout_report"] = f"{academy['network_scout']} is setting up a {region} youth network. Setup takes 8 weeks."
        return True, academy["last_scout_report"]

    def cancel_academy_network(self):
        academy = self.repair_academy(getattr(self, "academy", {}))
        if not academy.get("network_active") and academy.get("network_weeks", 0) <= 0:
            return False, "There is no youth scouting network to cancel."
        region = academy.get("network_region") or "regional"
        lead_count = len(academy.get("talent_pool", []))
        academy.update({"network_weeks": 0, "network_active": False, "network_region": "", "network_scout": "", "network_scout_skill": 0,
                        "network_potential_skill": 0, "network_networking": 0, "network_reliability": 0, "talent_pool": []})
        academy["last_scout_report"] = f"Cancelled the {region} youth network. {lead_count} open lead(s) were removed."
        return True, academy["last_scout_report"]

    def academy_training_fields(self, plan, prospect=None):
        if plan == "Automatic" and prospect:
            weak = sorted(("striking", "wrestling", "grappling", "cardio", "fight_iq"), key=lambda key: prospect.get(key, 45))[:2]
            recommendation = self.recommended_academy_focus(prospect)
            recommended_fields = () if recommendation in ("Automatic", "Balanced") else self.academy_training_fields(recommendation, prospect)
            return tuple(dict.fromkeys(weak + list(recommended_fields) + list(self.academy_philosophy_fields())))
        return {
            "Balanced": ("striking", "wrestling", "grappling", "cardio", "fight_iq"),
            "Boxing": ("striking", "power", "chin"), "Muay Thai": ("striking", "power", "toughness"),
            "Wrestling": ("wrestling", "cardio", "fight_iq"), "BJJ": ("grappling", "fight_iq", "toughness"),
            "Judo": ("wrestling", "grappling", "fight_iq"), "Sambo": ("wrestling", "grappling", "power"),
            "Clinch": ("wrestling", "striking", "toughness"), "Cardio": ("cardio", "toughness"),
            "Strength": ("power", "toughness", "chin"), "Fight IQ": ("fight_iq", "cardio"),
        }.get(plan, ("striking", "wrestling", "grappling"))

    def academy_preferred_sport(self, prospect):
        self.repair_academy_prospect(prospect)
        scores = {
            "Boxing": prospect.get("striking", 40) + prospect.get("power", 40) * 0.35,
            "Kickboxing": prospect.get("striking", 40) + prospect.get("cardio", 40) * 0.22,
            "Muay Thai": prospect.get("striking", 40) + prospect.get("toughness", 40) * 0.28,
            "Wrestling": prospect.get("wrestling", 40) * 1.25 + prospect.get("cardio", 40) * 0.18,
            "Brazilian Jiu-Jitsu": prospect.get("grappling", 40) * 1.25 + prospect.get("fight_iq", 40) * 0.18,
            "MMA": min(prospect.get("striking", 40), prospect.get("wrestling", 40), prospect.get("grappling", 40)) * 0.8 + prospect.get("fight_iq", 40) * 0.4,
        }
        preferred = max(scores, key=scores.get)
        prospect["preferred_sport"] = preferred
        return preferred

    def academy_graduation_readiness(self, prospect):
        self.repair_academy_prospect(prospect)
        bouts = self.academy_amateur_fight_count(prospect)
        age_score = max(0, min(28, (prospect.get("age", 15) - 15) * 9))
        ability = max(0, min(30, (prospect.get("rating", 40) - 42) * 1.2))
        experience = min(24, bouts * 3)
        mentality = (prospect.get("confidence", 55) + prospect.get("dedication", 55)) / 12
        injury_drag = prospect.get("injured", 0) * 3 + max(0, prospect.get("fatigue", 0) - 55) / 4
        return max(0, min(100, round(age_score + ability + experience + mentality - injury_drag)))

    def academy_graduation_recommendation(self, prospect):
        """A scout-style call on whether a prospect should turn professional now.

        Returns (label, reason). Labels: TOO YOUNG, NEEDS BOUTS, KEEP DEVELOPING,
        ALMOST READY, GRADUATE NOW."""
        self.repair_academy_prospect(prospect)
        age = int(prospect.get("age", 15) or 15)
        if age < 16:
            return "TOO YOUNG", "Must be at least 16 to turn professional."
        readiness = self.academy_graduation_readiness(prospect)
        rating = int(prospect.get("rating", 40) or 40)
        potential = int(prospect.get("potential", 70) or 70)
        gap = max(0, potential - rating)
        bouts = self.academy_amateur_fight_count(prospect)
        if bouts < 3 and age < 20:
            return "NEEDS BOUTS", f"Only {bouts} amateur bout(s); showcase experience will sharpen them before they turn pro."
        if readiness >= 78 and (gap <= 6 or age >= 21):
            return "GRADUATE NOW", f"Near their ceiling ({rating}/{potential}) with {readiness}% readiness — ready to turn professional."
        if readiness >= 62 and gap <= 12:
            return "ALMOST READY", f"{readiness}% ready; a little more polish or a bout or two completes the development."
        return "KEEP DEVELOPING", f"Still {gap} points from a {potential} ceiling; keep training and building the amateur record."

    def process_academy_graduations(self, academy):
        """Fire a one-time 'ready to turn pro' alert and, if the player opts in,
        auto-graduate clearly-ready adult prospects into the MMA roster."""
        auto = bool(academy.get("auto_graduate", False))
        spectator = getattr(self, "spectator_mode", False)
        auto_graduated = 0
        for prospect in list(academy.get("prospects", [])):
            label, reason = self.academy_graduation_recommendation(prospect)
            ready = label == "GRADUATE NOW"
            if ready and not prospect.get("graduation_alerted"):
                prospect["graduation_alerted"] = True
                if not spectator:
                    self.inbox.append({
                        "subject": f"Academy Prospect Ready - {prospect['name']}",
                        "body": f"{prospect['name']} ({prospect.get('age')}) is ready to turn professional. {reason} "
                                f"Promote them from the Fight Academy, or turn on Auto Graduate to have staff handle it.",
                        "type": "Academy", "fighter": prospect["name"], "resolved": False,
                    })
            elif not ready:
                # Reset so a later return to readiness re-alerts once.
                prospect["graduation_alerted"] = False
            # Auto-graduation is deliberately limited per week so a backlog does
            # not dump a whole intake onto the roster at once.
            if auto and ready and int(prospect.get("age", 0) or 0) >= 18 and auto_graduated < 2:
                ok, note, _fighter = self.promote_academy_prospect_to_sport(prospect, "MMA")
                if ok:
                    if prospect in academy.get("prospects", []):
                        academy["prospects"].remove(prospect)
                    auto_graduated += 1
                    self.news.insert(0, f"Auto-graduation: {note}")

    def academy_prospect_trend(self, prospect):
        history = prospect.get("rating_history", [])
        if len(history) < 2:
            return prospect.get("rating", 40) - prospect.get("baseline_rating", prospect.get("rating", 40))
        return history[-1].get("rating", prospect.get("rating", 40)) - history[-2].get("rating", prospect.get("rating", 40))

    def recommended_academy_focus(self, prospect):
        self.repair_academy_prospect(prospect)
        if prospect.get("grappling", 0) >= max(prospect.get("striking", 0), prospect.get("wrestling", 0)) + 5:
            return "BJJ"
        if prospect.get("wrestling", 0) >= max(prospect.get("striking", 0), prospect.get("grappling", 0)) + 5:
            return "Wrestling"
        if prospect.get("striking", 0) >= max(prospect.get("wrestling", 0), prospect.get("grappling", 0)) + 5:
            return "Boxing"
        if prospect.get("cardio", 0) < prospect.get("rating", 40) - 3:
            return "Cardio"
        if prospect.get("fight_iq", 0) < prospect.get("rating", 40) - 3:
            return "Fight IQ"
        return "Automatic" if prospect.get("potential", 70) - prospect.get("rating", 40) >= 12 else "Balanced"

    def academy_focus_recommendation(self, prospect):
        focus = self.recommended_academy_focus(prospect)
        fields = self.academy_training_fields(focus if focus != "Automatic" else "Balanced", prospect)
        weakest = min(("striking", "wrestling", "grappling", "cardio", "fight_iq"), key=lambda key: prospect.get(key, 45))
        if focus in ("Boxing", "Wrestling", "BJJ"):
            reason = f"Build around the athlete's strongest base while improving {weakest.replace('_', ' ')}."
        elif focus in ("Cardio", "Fight IQ"):
            reason = f"{focus} is limiting the prospect's current readiness and consistency."
        else:
            reason = f"Balanced work is appropriate; {weakest.replace('_', ' ')} is the main weakness."
        return focus, reason, fields

    def record_academy_progress(self, prospect, reason="Monthly development review"):
        snapshot = {"month": self.month, "week": self.week, "rating": prospect.get("rating", 40),
                    "readiness": self.academy_graduation_readiness(prospect), "reason": reason}
        for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq"):
            snapshot[key] = prospect.get(key, 40)
        history = prospect.setdefault("rating_history", [])
        if history and (history[-1].get("month"), history[-1].get("week")) == (self.month, self.week):
            history[-1] = snapshot
        else:
            history.append(snapshot)
        prospect["rating_history"] = history[-60:]
        return snapshot

    # Original academy prices, kept for saves started before the rise. A career
    # already part-way through its facility build-out should not have the
    # remaining purchases repriced underneath it.
    ACADEMY_UPGRADE_LEGACY_COSTS = {
        "elite_coaches": 90_000, "conditioning_centre": 60_000, "analysis_lab": 50_000,
        "medical_suite": 75_000, "recovery_nutrition": 45_000,
    }

    def academy_upgrade_pricing_version(self):
        """Saves without the marker predate the price rise and keep the old costs."""
        return int((getattr(self, "rules", None) or {}).get("academy_upgrade_pricing_version", 1) or 1)

    def academy_upgrade_catalog(self):
        """Purchasable academy facilities. Each is a one-off spend with a permanent
        effect on how fast and safely prospects develop.

        Priced as a long-term ambition rather than an early purchase: a permanent
        promotion-wide development bonus was reachable in the opening months at
        the original cost, so the academy stopped being a real decision.
        """
        catalog = [
            {"id": "elite_coaches", "name": "Elite Coaching Team", "cost": 1_800_000,
             "effect": "Faster skill development in every session (+9% growth).", "growth": 0.09},
            {"id": "conditioning_centre", "name": "Strength & Conditioning Centre", "cost": 1_200_000,
             "effect": "+5% growth and biases training toward cardio, power, and toughness.", "growth": 0.05, "emphasis": "physical"},
            {"id": "analysis_lab", "name": "Video & Analysis Lab", "cost": 1_050_000,
             "effect": "+3% growth and sharper Fight IQ development.", "growth": 0.03, "emphasis": "mental"},
            {"id": "medical_suite", "name": "Sports Medicine Suite", "cost": 1_500_000,
             "effect": "Halves training-injury risk and heals injuries a week sooner.", "injury_mult": 0.5, "heal": 1},
            {"id": "recovery_nutrition", "name": "Recovery & Nutrition Programme", "cost": 1_000_000,
             "effect": "+4 weekly fatigue recovery so prospects train harder without burning out.", "recovery": 4},
        ]
        if self.academy_upgrade_pricing_version() < 2:
            for upgrade in catalog:
                upgrade["cost"] = self.ACADEMY_UPGRADE_LEGACY_COSTS.get(upgrade["id"], upgrade["cost"])
        return catalog

    def academy_facility_profile(self, academy=None):
        """Aggregate the effects of every installed academy facility upgrade."""
        academy = academy if academy is not None else getattr(self, "academy", {}) or {}
        owned = set(academy.get("upgrades", []) or [])
        profile = {"growth": 0.0, "injury_mult": 1.0, "recovery": 0, "heal": 0, "emphasis": []}
        for upgrade in self.academy_upgrade_catalog():
            if upgrade["id"] in owned:
                profile["growth"] += upgrade.get("growth", 0.0)
                profile["injury_mult"] *= upgrade.get("injury_mult", 1.0)
                profile["recovery"] += upgrade.get("recovery", 0)
                profile["heal"] += upgrade.get("heal", 0)
                if upgrade.get("emphasis"):
                    profile["emphasis"].append(upgrade["emphasis"])
        return profile

    def purchase_academy_upgrade(self, academy, upgrade_id):
        """Buy a facility upgrade if affordable and not already installed."""
        academy = academy if academy is not None else getattr(self, "academy", {}) or {}
        catalog = {upgrade["id"]: upgrade for upgrade in self.academy_upgrade_catalog()}
        upgrade = catalog.get(upgrade_id)
        if not upgrade:
            return False, "Unknown upgrade."
        owned = list(academy.get("upgrades", []) or [])
        if upgrade_id in owned:
            return False, f"{upgrade['name']} is already installed."
        if self.cash < upgrade["cost"]:
            return False, f"{upgrade['name']} costs ${upgrade['cost']:,}."
        self.cash -= upgrade["cost"]
        owned.append(upgrade_id)
        academy["upgrades"] = owned
        academy["upgrade_spend"] = academy.get("upgrade_spend", 0) + upgrade["cost"]
        academy["reputation"] = min(100, academy.get("reputation", 10) + 2)
        self.record_finance_transaction(f"Academy facility: {upgrade['name']}", costs=upgrade["cost"])
        academy["last_scout_report"] = f"Installed {upgrade['name']} at the academy (${upgrade['cost']:,})."
        return True, academy["last_scout_report"]

    def train_academy_prospect(self, prospect, academy):
        self.repair_academy_prospect(prospect)
        profile = self.academy_facility_profile(academy)
        prospect["weeks"] = prospect.get("weeks", 0) + 1
        if prospect.get("injured", 0):
            prospect["injured"] = max(0, prospect.get("injured", 0) - 1 - profile["heal"])
            return
        intensity = prospect.get("training_intensity", "Standard")
        recovery = {"Light": (9, 14), "Standard": (7, 12), "Intensive": (5, 9), "Recovery": (12, 18)}.get(intensity, (7, 12))
        prospect["fatigue"] = max(0, prospect.get("fatigue", 0) - random.randint(*recovery) - profile["recovery"])
        if not academy.get("auto_train", True):
            return
        if intensity == "Recovery" or prospect.get("fatigue", 0) >= 65:
            prospect["confidence"] = min(99, prospect.get("confidence", 55) + (1 if random.random() < 0.28 else 0))
            return
        fields = self.academy_training_fields(prospect.get("plan", "Automatic"), prospect)
        philosophy = self.academy_philosophy_fields(academy)
        level = max(1, academy.get("level", 1))
        facility = level * 7 + self.staff_skill("Trainer") * 0.25 + academy.get("reputation", 10) * 0.10
        potential_gap = max(0, prospect.get("potential", 70) - prospect.get("rating", 40))
        mentality = (prospect.get("dedication", 55) + prospect.get("coachability", 55)) / 200
        intensity_factor = {"Light": 0.72, "Standard": 1.0, "Intensive": 1.35}.get(intensity, 1.0)
        fatigue_drag = max(0, prospect.get("fatigue", 0) - 35) / 180
        facility_bonus = max(0, level - 1) * 0.012
        growth_chance = min(0.58, (0.05 + facility / 400 + potential_gap / 360) * mentality * intensity_factor + facility_bonus + profile["growth"] - fatigue_drag)
        if random.random() < max(0.025, growth_chance):
            emphasis_fields = []
            if "physical" in profile["emphasis"]:
                emphasis_fields += [field for field in ("cardio", "power", "toughness") if field in fields]
            if "mental" in profile["emphasis"]:
                emphasis_fields += [field for field in ("fight_iq",) if field in fields]
            weighted_fields = list(fields) + [field for field in philosophy if field in fields] + emphasis_fields
            field = random.choice(weighted_fields)
            prospect[field] = min(prospect.get("potential", 99), prospect.get(field, prospect.get("rating", 40)) + 1)
            prospect["development"] = prospect.get("development", 0) + 1
            prospect["plateau_weeks"] = 0
            prospect["training_log"] = ([f"M{self.month} W{self.week}: {field.replace('_', ' ').title()} improved under {prospect.get('plan', 'Automatic')} training."] + prospect.get("training_log", []))[:30]
        else:
            prospect["plateau_weeks"] = prospect.get("plateau_weeks", 0) + 1
        fatigue_gain = {"Light": 1, "Standard": 2, "Intensive": 4}.get(intensity, 2)
        prospect["fatigue"] = min(100, prospect.get("fatigue", 0) + fatigue_gain)
        injury_risk = ({
            "Light": 0.0015, "Standard": 0.0035, "Intensive": 0.010, "Recovery": 0.0008,
        }.get(intensity, 0.0035) + max(0, prospect["fatigue"] - 75) / 1700) * profile["injury_mult"]
        if random.random() < injury_risk:
            prospect["injured"] = random.randint(1, 4)
            injury_note = f"M{self.month} W{self.week}: Training injury; out {prospect['injured']} week(s)."
            prospect["training_log"] = ([injury_note] + prospect.get("training_log", []))[:30]
            prospect["medical_history"] = ([injury_note] + prospect.get("medical_history", []))[:20]
        if prospect.get("weeks", 0) % 5 == 0 and prospect.get("rating", 40) < prospect.get("potential", 70):
            self.recalculate_academy_rating(prospect)
        if prospect.get("weeks", 0) % 4 == 0:
            self.record_academy_progress(prospect)

    def recalculate_academy_rating(self, prospect):
        rating = round((prospect.get("striking", 40) + prospect.get("wrestling", 40) + prospect.get("grappling", 40) + prospect.get("cardio", 40) + prospect.get("chin", 40) + prospect.get("fight_iq", 40)) / 6)
        prospect["rating"] = max(prospect.get("rating", 40), min(prospect.get("potential", 70), rating))
        return prospect["rating"]

    def apply_academy_bout_development(self, prospect, method, won=False):
        self.repair_academy_prospect(prospect)
        fields = ["cardio", "fight_iq", "toughness"]
        if method in ("KO", "TKO"):
            fields += ["striking", "power", "chin"]
        elif "Submission" in method:
            fields += ["grappling", "fight_iq"]
        else:
            fields += ["wrestling", "grappling", "striking"]
        prospect["bout_experience"] = prospect.get("bout_experience", 0) + 1
        gap = max(0, prospect.get("potential", 70) - prospect.get("rating", 40))
        mentality = (prospect.get("dedication", 55) + prospect.get("coachability", 55)) / 200
        gain_chance = min(0.72, (0.26 + gap / 120 + (0.12 if won else 0)) * mentality)
        gains = int(random.random() < gain_chance) + int(won and gap >= 15 and random.random() < 0.12)
        improved = []
        for _ in range(gains):
            field = random.choice(fields)
            prospect[field] = min(prospect.get("potential", 99), prospect.get(field, 45) + 1)
            prospect["development"] = prospect.get("development", 0) + 1
            improved.append(field.replace("_", " ").title())
        prospect["fatigue"] = min(100, prospect.get("fatigue", 0) + random.randint(8, 16))
        prospect["confidence"] = max(20, min(99, prospect.get("confidence", 55) + (random.randint(2, 5) if won else random.randint(-3, 1))))
        if random.random() < 0.025:
            prospect["injured"] = max(prospect.get("injured", 0), random.randint(1, 3))
            note = f"M{self.month} W{self.week}: Bout injury; out {prospect['injured']} week(s)."
            prospect["medical_history"] = ([note] + prospect.get("medical_history", []))[:20]
        self.recalculate_academy_rating(prospect)
        prospect["last_development"] = ", ".join(improved) if improved else "Experience gained; no immediate skill increase"
        self.record_academy_progress(prospect, "Amateur bout")

    def academy_prospect_to_fighter(self, prospect):
        self.repair_academy_prospect(prospect)
        fighter = self.create_generated_fighter(2, 14, max(35, prospect["rating"] - 6), min(86, prospect["rating"] + 6), weight=prospect["weight"], gender=prospect["gender"], region=prospect["region"])
        fighter.name = prospect["name"]; fighter.age = prospect["age"]; fighter.potential = prospect["potential"]
        fighter.style = prospect.get("style", fighter.style)
        fighter.stance = prospect.get("stance", fighter.stance)
        fighter.trait = prospect.get("trait", fighter.trait)
        fighter.record_w = fighter.record_l = fighter.record_d = 0
        for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq"):
            setattr(fighter, key, max(1, min(99, prospect.get(key, getattr(fighter, key, 50)))))
        group_targets = {
            "Standing": prospect.get("striking", 45), "Ground": prospect.get("grappling", 45),
            "Wrestling": prospect.get("wrestling", 45),
            "Muay Thai Clinch": round((prospect.get("striking", 45) + prospect.get("wrestling", 45)) / 2),
            "Mental": prospect.get("fight_iq", 45),
            "Physical": round((prospect.get("cardio", 45) + prospect.get("chin", 45) + prospect.get("power", 45) + prospect.get("toughness", 45)) / 4),
        }
        fighter.detailed_skills = {
            key: max(1, min(99, group_targets.get(group, prospect.get("rating", 45))))
            for group, keys in DETAILED_SKILL_GROUPS.items() for key in keys
        }
        fighter.detailed_skills.update({
            "conditioning": prospect.get("cardio", 45), "resilience": prospect.get("toughness", 45),
            "chin_strength": prospect.get("chin", 45), "stun_recovery": prospect.get("chin", 45),
            "strength": prospect.get("power", 45), "dedication": prospect.get("dedication", 55),
            "confidence": prospect.get("confidence", 55),
        })
        for key in ("nationality", "birth_country", "birth_region", "hometown", "residence", "training_location", "fighting_base", "cultural_connections", "regional_popularity"):
            if key in prospect:
                setattr(fighter, key, prospect[key])
        # Academy bouts are background, not professional fights. Keep their
        # structured ledger for the profile and begin the pro ledger cleanly.
        fighter.amateur_w = int(prospect.get("amateur_w", 0) or 0)
        fighter.amateur_l = int(prospect.get("amateur_l", 0) or 0)
        fighter.amateur_d = int(prospect.get("amateur_d", 0) or 0)
        fighter.amateur_bout_history = [dict(record) for record in prospect.get("amateur_bout_records", []) if isinstance(record, dict)]
        fighter.amateur_history_migration_version = 1
        fighter.fight_history = ["Promoted from the Fighting Academy."]
        fighter.record_history_baseline_w = 0
        fighter.record_history_baseline_l = 0
        fighter.record_history_baseline_d = 0
        fighter.contract_months = 24
        fighter.feeder_origin = f"{self.player_company_name} Fighting Academy"
        fighter.academy_graduate = True
        fighter.academy_graduated_month = self.month
        fighter.motivation = max(35, min(99, prospect.get("dedication", fighter.motivation)))
        fighter.professionalism = max(30, min(99, round((prospect.get("dedication", 55) + prospect.get("coachability", 55)) / 2)))
        fighter.career_achievements = list(fighter.career_achievements or []) + [
            f"Graduated from {self.player_company_name}'s academy with a {prospect.get('amateur_w', 0)}-{prospect.get('amateur_l', 0)}-{prospect.get('amateur_d', 0)} amateur record."
        ]
        fighter.rank_score = self.rank_value(fighter)
        return fighter

    def record_academy_graduate(self, prospect, fighter, destination):
        academy = self.repair_academy(getattr(self, "academy", {}))
        entry = {
            "name": fighter.name, "destination": destination, "graduated_month": self.month,
            "amateur_record": f"{prospect.get('amateur_w', 0)}-{prospect.get('amateur_l', 0)}-{prospect.get('amateur_d', 0)}",
            "graduation_rating": prospect.get("rating", fighter.overall), "potential": prospect.get("potential", fighter.potential),
            "current_rating": fighter.overall, "professional_record": fighter.record, "title_wins": 0,
            "last_wins": fighter.record_w, "active": True,
        }
        academy["alumni"] = ([entry] + [row for row in academy.get("alumni", []) if row.get("name") != fighter.name])[:100]
        academy["total_graduates"] = academy.get("total_graduates", 0) + 1
        academy["reputation"] = min(100, academy.get("reputation", 10) + 1 + int(prospect.get("rating", 40) >= 65))
        prospect["milestones"] = ([f"M{self.month}: Graduated to {destination} at rating {prospect.get('rating', fighter.overall)}."] + prospect.get("milestones", []))[:20]
        self.record_world_story("Academy Graduate", f"{fighter.name} graduates from {self.player_company_name}'s academy.", f"Destination {destination}; amateur record {entry['amateur_record']}; potential {fighter.potential}.", [self.player_company_name], [fighter.name], 2)
        if destination == "MMA" and fighter in self.roster:
            self.start_career_arc(fighter, "Homegrown Champion", "Academy graduation")

    def academy_alumnus_fighter(self, name):
        fighter = self.find_fighter_anywhere(name) if hasattr(self, "find_fighter_anywhere") else None
        if fighter:
            return fighter
        for world in getattr(self, "combat_sport_worlds", {}).values():
            for candidate in world.get("roster", []):
                if candidate.name == name:
                    return candidate
        return None

    def update_academy_alumni(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        if not academy.get("owned") or academy.get("last_alumni_review_month") == self.month:
            return
        academy["last_alumni_review_month"] = self.month
        # Build the world lookup once. Previously every alumnus independently
        # sorted the entire fighter database, which became costly in long saves.
        fighter_index = {fighter.name: fighter for fighter in self.all_database_fighters(include_retired=True)}
        for entry in academy.get("alumni", []):
            fighter = fighter_index.get(entry.get("name", ""))
            if not fighter:
                entry["active"] = False
                continue
            prior_wins = entry.get("last_wins", 0)
            prior_titles = entry.get("title_wins", 0)
            entry.update({"current_rating": fighter.overall, "professional_record": fighter.record,
                          "title_wins": getattr(fighter, "title_wins", 0), "last_wins": fighter.record_w,
                          "active": not getattr(fighter, "retired", False)})
            gained_wins = max(0, fighter.record_w - prior_wins)
            gained_titles = max(0, getattr(fighter, "title_wins", 0) - prior_titles)
            if gained_wins or gained_titles:
                academy["reputation"] = min(100, academy.get("reputation", 10) + min(2, gained_wins) + gained_titles * 3)
                if gained_titles:
                    note = f"Academy alumnus {fighter.name} won a professional title; academy reputation rose to {academy['reputation']}."
                    academy["last_scout_report"] = note
                    self.news.insert(0, note)

    def promote_academy_prospect_to_sport(self, prospect, sport):
        self.repair_academy_prospect(prospect)
        if prospect.get("age", 0) < 16:
            return False, "A prospect must be at least 16 to turn professional.", None
        fighter = self.academy_prospect_to_fighter(prospect)
        if sport == "MMA":
            self.roster.append(fighter)
            self.record_academy_graduate(prospect, fighter, sport)
            return True, f"Academy graduate: {fighter.name} joined {self.player_company_name}.", fighter
        ok, division = self.open_player_combat_division(sport)
        if not ok:
            return False, division, None
        world = self.combat_sport_worlds.get(sport)
        fighter.primary_discipline = sport if sport != "Brazilian Jiu-Jitsu" else "Brazilian Jiu-Jitsu"
        fighter.sport_employer = self.player_company_name
        fighter.contract_type = f"{sport} Developmental"
        self.assign_combat_sport_weight(sport, fighter, reset_walk_weight=True)
        fighter.multi_sport_records = fighter.multi_sport_records or {}
        fighter.multi_sport_records[sport] = "0-0-0"
        fighter.crossover_history = fighter.crossover_history or []
        fighter.crossover_history.append(f"Month {self.month}: Graduated from {self.player_company_name}'s academy into {sport}.")
        world["roster"].append(fighter)
        division["roster"] = list(dict.fromkeys(division.get("roster", []) + [fighter.name]))
        self.record_academy_graduate(prospect, fighter, sport)
        return True, f"Academy graduate: {fighter.name} joined {self.player_company_name}'s {sport} division.", fighter

    def academy_bout_fighter(self, prospect):
        """Build a disposable fighter so amateur bouts use the complete MMA engine."""
        fighter = self.academy_prospect_to_fighter(prospect)
        fighter.age = max(16, fighter.age)
        fighter.camp = f"{self.player_company_name} Fighting Academy"
        fighter.camp_quality = min(96, 48 + getattr(self, "academy", {}).get("level", 1) * 7)
        fighter.camp_weeks = 4
        fighter.camp_boost = max(0, min(8, getattr(self, "academy", {}).get("level", 1) + prospect.get("coachability", 50) // 25))
        fighter.morale = prospect.get("confidence", 55)
        fighter.motivation = prospect.get("dedication", 55)
        fighter.fatigue = prospect.get("fatigue", 0)
        fighter.walk_weight = self.default_walk_weight(fighter)
        fighter.scale_weight = float(WEIGHT_LIMITS.get(fighter.weight, fighter.walk_weight))
        return fighter

    def simulate_academy_amateur_bout(self, a, b, label):
        self.repair_academy_prospect(a); self.repair_academy_prospect(b)
        a_fighter, b_fighter = self.academy_bout_fighter(a), self.academy_bout_fighter(b)
        fight = {"main": False, "title": False, "tier": "Academy Showcase", "region": a.get("region", self.player_region)}
        winner_fighter, loser_fighter, method, round_no, lines = self.simulate_fight(a_fighter, b_fighter, fight)
        detail = {"heading": f"{a['name']} vs {b['name']}", "label": f"{label} AMATEUR",
                  "a": a["name"], "b": b["name"], "weight": label, "lines": list(lines)}
        absolute_week = self.calendar_week_index()
        for prospect, opponent in ((a, b), (b, a)):
            prospect["last_amateur_week"] = absolute_week
            counts = prospect.setdefault("opponent_counts", {})
            counts[opponent["name"]] = counts.get(opponent["name"], 0) + 1
            if len(counts) > 20:
                prospect["opponent_counts"] = dict(list(counts.items())[-20:])
        if method == "Draw":
            a["amateur_d"] += 1; b["amateur_d"] += 1
            line = f"Month {self.month}: Amateur draw - {a['name']} vs {b['name']} ({label}, R{round_no})."
            a["amateur_history"].insert(0, line); b["amateur_history"].insert(0, line)
            for prospect, opponent in ((a, b), (b, a)):
                prospect["amateur_bout_records"] = ([{
                    "month": self.month, "week": self.week, "event": "Academy Showcase", "opponent": opponent["name"],
                    "result": "D", "method": "Draw", "round": round_no, "weight": label,
                }] + prospect.get("amateur_bout_records", []))[:100]
            self.apply_academy_bout_development(a, method, False); self.apply_academy_bout_development(b, method, False)
            detail.update({"result": line, "winner": "Draw", "method": "Draw", "round": round_no, "draw": True})
            detail["lines"] += ["", f"Result: {line}"]
            a["last_amateur_bout"] = b["last_amateur_bout"] = detail
            return line
        winner, loser = (a, b) if winner_fighter.name == a["name"] else (b, a)
        winner["amateur_w"] += 1; loser["amateur_l"] += 1
        line = f"Month {self.month}: Amateur - {winner['name']} def. {loser['name']} by {method} (R{round_no}, {label} Academy Showcase)."
        winner["amateur_history"].insert(0, line); loser["amateur_history"].insert(0, line)
        for prospect, opponent, result in ((winner, loser, "W"), (loser, winner, "L")):
            prospect["amateur_bout_records"] = ([{
                "month": self.month, "week": self.week, "event": "Academy Showcase", "opponent": opponent["name"],
                "result": result, "method": method, "round": round_no, "weight": label,
            }] + prospect.get("amateur_bout_records", []))[:100]
        self.apply_academy_bout_development(winner, method, True); self.apply_academy_bout_development(loser, method, False)
        detail.update({"result": line, "winner": winner["name"], "method": method, "round": round_no, "draw": False})
        detail["lines"] += ["", f"Result: {line}"]
        a["last_amateur_bout"] = b["last_amateur_bout"] = detail
        if winner.get("academy_member") and (winner["amateur_w"] in (1, 5, 10) or (winner["amateur_w"] >= 6 and winner["amateur_l"] == 0)):
            milestone = f"M{self.month}: Reached {winner['amateur_w']} amateur wins ({winner['amateur_w']}-{winner['amateur_l']}-{winner.get('amateur_d', 0)})."
            winner["milestones"] = ([milestone] + winner.get("milestones", []))[:20]
        return line

    def academy_amateur_fight_count(self, prospect):
        return prospect.get("amateur_w", 0) + prospect.get("amateur_l", 0) + prospect.get("amateur_d", 0)

    def create_academy_guest_opponent(self, prospect, reserved_names=None):
        """Create a same-gender regional amateur for an isolated prospect.

        Academy capacity is intentionally small, so requiring an internal match
        can strand a lone woman or weight-band outlier for years.  Guest amateurs
        give every healthy prospect real simulated experience without signing a
        permanent ninth academy member.
        """
        reserved = set(reserved_names or ()) | {item.get("name", "") for item in self.academy.get("prospects", [])}
        rating = max(30, min(78, prospect.get("rating", 40) + random.randint(-5, 5)))
        fighter = self.create_generated_fighter(
            2, 12, max(28, rating - 6), min(82, rating + 6),
            weight=prospect.get("weight", "Lightweight"),
            gender=prospect.get("gender", "Male"),
            region=prospect.get("region", self.player_region),
        )
        self.avoid_name_collision(fighter, self.active_fighter_names() | reserved)
        guest = {
            "name": fighter.name,
            "age": max(15, min(20, prospect.get("age", 17) + random.choice([-1, 0, 0, 1]))),
            "potential": max(rating, min(88, rating + random.randint(5, 16))),
            "region": prospect.get("region", self.player_region),
            "gender": prospect.get("gender", "Male"),
            "weight": prospect.get("weight", "Lightweight"),
            "amateur_weight": prospect.get("amateur_weight", "Youth Openweight"),
            "rating": rating,
            "style": fighter.style,
            "nationality": fighter.nationality,
            "striking": max(25, min(85, rating + random.randint(-7, 7))),
            "wrestling": max(25, min(85, rating + random.randint(-7, 7))),
            "grappling": max(25, min(85, rating + random.randint(-7, 7))),
            "cardio": max(30, min(88, rating + random.randint(-5, 8))),
            "chin": max(30, min(88, rating + random.randint(-6, 7))),
            "power": max(25, min(86, rating + random.randint(-7, 7))),
            "toughness": max(30, min(88, rating + random.randint(-5, 8))),
            "fight_iq": max(25, min(86, rating + random.randint(-7, 7))),
            "plan": "Regional Club",
            "amateur_w": random.randint(0, 4), "amateur_l": random.randint(0, 3), "amateur_d": 0,
            "amateur_history": [], "weeks": 0, "development": 0, "fatigue": 0, "injured": 0,
        }
        return self.repair_academy_prospect(guest)

    def choose_academy_showcase_card(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        absolute_week = self.calendar_week_index()
        ready = [item for item in academy.get("prospects", [])
                 if not item.get("injured", 0) and item.get("fatigue", 0) < 70
                 and absolute_week - item.get("last_amateur_week", -99) >= 6]
        ready.sort(key=lambda item: (self.academy_amateur_fight_count(item), item.get("fatigue", 0), random.random()))
        # Every healthy, rested academy member receives a bout on a due card.
        # Guest amateurs fill isolated gender/weight slots rather than forcing
        # unsafe youth open-weight pairings.
        target_bouts = max(1, len(ready))
        bouts, used = [], set()
        for a in ready:
            if len(bouts) >= target_bouts:
                break
            if a["name"] in used:
                continue
            candidates = [b for b in ready if b["name"] not in used and b["name"] != a["name"]
                          and b.get("gender") == a.get("gender") and b.get("amateur_weight") == a.get("amateur_weight")]
            same_weight = [b for b in candidates if b.get("amateur_weight") == a.get("amateur_weight")]
            pool = same_weight
            if not pool:
                continue
            b = min(pool, key=lambda item: abs(item.get("rating", 40) - a.get("rating", 40)) + abs(self.academy_amateur_fight_count(item) - self.academy_amateur_fight_count(a)) + a.get("opponent_counts", {}).get(item.get("name"), 0) * 14)
            if a.get("opponent_counts", {}).get(b.get("name"), 0) >= 3:
                continue
            label = a.get("amateur_weight", "Youth Openweight") if b in same_weight else "Open Youth"
            bouts.append((a, b, label)); used.update([a["name"], b["name"]])
        # Fill any odd or isolated slots with regional guest amateurs.  The guest
        # is simulated normally but is not retained in the owned academy roster.
        reserved = {item.get("name", "") for item in ready}
        for prospect in ready:
            if len(bouts) >= target_bouts:
                break
            if prospect["name"] in used:
                continue
            guest = self.create_academy_guest_opponent(prospect, reserved)
            reserved.add(guest["name"])
            bouts.append((prospect, guest, prospect.get("amateur_weight", "Youth Openweight")))
            used.add(prospect["name"])
        return bouts

    def run_academy_showcase_card(self, academy=None, bouts=None):
        academy = academy or getattr(self, "academy", {})
        results, fight_logs = [], []
        for a, b, label in (bouts if bouts is not None else self.choose_academy_showcase_card(academy)):
            results.append(self.simulate_academy_amateur_bout(a, b, label))
            fight_logs.append(dict(a.get("last_amateur_bout", {})))
        if results:
            academy["total_cards"] = academy.get("total_cards", 0) + 1
            card_number = academy["total_cards"]
            card = {"event_name": f"{self.player_company_name} Academy Showcase {card_number}",
                    "date": f"Month {self.month} Week {self.week}", "results": list(results),
                    "fight_logs": fight_logs, "recap": f"{len(results)} amateur bout(s) completed."}
            academy["card_history"] = ([card] + academy.get("card_history", []))[:24]
            academy["last_showcase_week"] = self.calendar_week_index()
            academy["last_showcase_recap"] = "\n".join(results)
            academy["total_bouts"] = academy.get("total_bouts", 0) + len(results)
            academy["reputation"] = min(100, academy.get("reputation", 10) + (1 if academy["total_bouts"] % 12 < len(results) else 0))
        return results

    def run_academy_showcase_if_due(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        if not academy.get("owned") or not academy.get("auto_showcases", True):
            return None
        absolute_week = self.calendar_week_index()
        if absolute_week - int(academy.get("last_showcase_week", -99)) < 4:
            return None
        bouts = self.choose_academy_showcase_card(academy)
        required = max(1, min(12, int(academy.get("auto_card_min_bouts", 2) or 2)))
        if len(bouts) < required:
            academy["showcase_weeks"] = 1
            return None
        results = self.run_academy_showcase_card(academy, bouts=bouts)
        academy["showcase_weeks"] = 4
        academy["last_scout_report"] = f"Academy auto-card: {len(results)} bout(s) completed after reaching the {required}-fight requirement."
        if results:
            self.news.insert(0, academy["last_scout_report"])
        return academy["last_scout_report"]

    def process_academy_week(self):
        academy = self.repair_academy(getattr(self, "academy", {}))
        if not academy.get("owned") or getattr(self, "spectator_mode", False):
            return
        self.cash -= academy.get("weekly_cost", 0)
        academy["operating_spend"] = academy.get("operating_spend", 0) + academy.get("weekly_cost", 0)
        self.record_finance_transaction("Academy operating costs", costs=academy.get("weekly_cost", 0))
        for prospect in academy.get("prospects", []):
            self.train_academy_prospect(prospect, academy)
        self.process_academy_graduations(academy)
        for prospect in list(academy.get("talent_pool", [])):
            self.refine_academy_lead(prospect, academy)
            prospect["weeks_to_sign"] = prospect.get("weeks_to_sign", 2) - 1
            if prospect["weeks_to_sign"] < 0:
                academy["talent_pool"].remove(prospect)
                academy["lost_leads"] = ([{"name": prospect.get("name", "Unknown"), "region": prospect.get("region", ""),
                                                    "potential_range": list(prospect.get("potential_range", (0, 0))), "lost_month": self.month}]
                                                 + academy.get("lost_leads", []))[:30]
                academy["last_scout_report"] = f"The signing window closed for {prospect.get('name', 'a youth prospect')}; the lead has left your network."
        if academy.get("network_weeks", 0) > 0:
            academy["network_weeks"] -= 1
            if academy["network_weeks"] <= 0:
                academy["network_active"] = True
                academy["last_scout_report"] = f"{academy.get('network_scout', 'Scout')} established a youth scouting network in {academy.get('network_region', self.player_region)}."
                self.inbox.append({"subject": "Academy Network Ready", "body": academy["last_scout_report"], "type": "Scouting", "resolved": False})
        if academy.get("network_active") and len(academy.get("talent_pool", [])) < 8:
            open_slots = max(0, 8 - len(academy.get("talent_pool", [])))
            judging = (academy.get("network_scout_skill", 45) + academy.get("network_potential_skill", 45)) / 2
            networking = academy.get("network_networking", 45)
            reliability = academy.get("network_reliability", 45)
            lead_chance = max(0.20, min(0.80, 0.20 + networking / 210 + reliability / 500))
            added = 0
            for _ in range(open_slots):
                if random.random() < lead_chance:
                    academy["talent_pool"].append(self.create_academy_scout_prospect(judging, region=academy.get("network_region", self.player_region)))
                    added += 1
            if added:
                academy["network_leads_found"] = academy.get("network_leads_found", 0) + added
                academy["last_scout_report"] = f"{academy.get('network_region', self.player_region)} network produced {added} youth lead(s). Leads expire after 2-3 weeks."
        self.run_academy_showcase_if_due(academy)
        self.update_academy_alumni(academy)

    def all_scoutable_fighters(self):
        """Return one live object per permanent fighter identity."""
        rows = list(getattr(self, "roster", [])) + list(getattr(self, "free_agents", []))
        rows += list(getattr(self, "retired_fighters", []))
        for promo in getattr(self, "promotions", []):
            rows.extend(promo.roster)
        unique = {}
        for fighter in rows:
            unique.setdefault(str(getattr(fighter, "fighter_id", "") or fighter.name), fighter)
        return list(unique.values())

    def scouting_report_key(self, fighter):
        return str(getattr(fighter, "fighter_id", "") or fighter.name)

    def scouting_report_for(self, fighter):
        reports = getattr(self, "scouting_reports", {})
        key = self.scouting_report_key(fighter)
        report = reports.get(key)
        if report is None:
            # Read-through support for a legacy save before its first migration.
            report = reports.get(fighter.name, {})
        return report or {}

    def migrate_scouting_state(self):
        """Upgrade name-keyed reports without guessing between duplicate names."""
        if getattr(self, "_scouting_state_migrated", False):
            self.scouting_reports = dict(getattr(self, "scouting_reports", {}) or {})
            self.scouting_searches = list(getattr(self, "scouting_searches", []) or [])
            return
        self.scouting_reports = dict(getattr(self, "scouting_reports", {}) or {})
        self.scouting_searches = list(getattr(self, "scouting_searches", []) or [])
        by_name = {}
        fighters = self.all_scoutable_fighters()
        by_id = {self.scouting_report_key(fighter): fighter for fighter in fighters}
        for fighter in fighters:
            by_name.setdefault(fighter.name, []).append(fighter)
        migrated = {}
        for old_key, raw in self.scouting_reports.items():
            report = dict(raw or {})
            fighter = None
            if str(old_key).startswith("FTR-"):
                fighter = by_id.get(str(old_key))
            elif len(by_name.get(str(old_key), [])) == 1:
                fighter = by_name[str(old_key)][0]
            report.setdefault("fighter_name", getattr(fighter, "name", str(old_key)))
            report.setdefault("fighter_id", self.scouting_report_key(fighter) if fighter else str(old_key))
            report.setdefault("started_week", self.calendar_week_index())
            report.setdefault("confidence", int(report.get("reveal", 0) or 0))
            report.setdefault("schema_version", 2)
            if fighter and report.get("status") == "Complete" and not report.get("estimates"):
                scout = next((member for member in getattr(self, "staff", []) if member.get("name") == report.get("scout")), {"skill": 42, "fighter_judging": 42, "potential_judging": 38, "reliability": 40})
                report["estimates"] = self.build_scouting_estimates(fighter, scout, report.get("kind", "basic"), report.get("confidence", 50))
                report.setdefault("completed_week", self.calendar_week_index())
            migrated[report["fighter_id"]] = report
        self.scouting_reports = migrated
        self._scouting_state_migrated = True

    def scout_capacity(self, scout):
        if not scout:
            return 0
        efficiency = int(scout.get("efficiency", scout.get("skill", 45)) or 45)
        return 1 + int(efficiency >= 68) + int(efficiency >= 88)

    def scout_workload(self, scout_name):
        reports = sum(
            report.get("status") == "In progress" and report.get("scout") == scout_name
            for report in getattr(self, "scouting_reports", {}).values()
        )
        searches = sum(
            search.get("status") == "In progress" and search.get("scout") == scout_name
            for search in getattr(self, "scouting_searches", [])
        )
        academy = getattr(self, "academy", {}) or {}
        academy_slot = int(
            academy.get("network_scout") == scout_name
            and (academy.get("network_active") or academy.get("network_weeks", 0) > 0)
        )
        return reports + searches + academy_slot

    def scouting_effective_confidence(self, report):
        confidence = int(report.get("confidence", report.get("reveal", 0)) or 0)
        if report.get("status") != "Complete":
            return confidence
        completed = int(report.get("completed_week", self.calendar_week_index()) or self.calendar_week_index())
        age_weeks = max(0, self.calendar_week_index() - completed)
        return max(20, confidence - max(0, age_weeks - 26) // 13 * 4)

    def scouting_report_is_current_full(self, report):
        if report.get("status") != "Complete" or report.get("kind") != "full" or report.get("reveal", 0) < 100:
            return False
        completed = int(report.get("completed_week", self.calendar_week_index()) or self.calendar_week_index())
        return self.calendar_week_index() - completed <= 52

    def scouting_estimate(self, fighter, field, default=None):
        report = self.scouting_report_for(fighter)
        if report.get("status") != "Complete":
            return default
        estimates = report.get("estimates", {}) or {}
        if field in estimates:
            estimate = dict(estimates[field])
            if report.get("kind") == "full" and not self.scouting_report_is_current_full(report):
                completed = int(report.get("completed_week", self.calendar_week_index()) or self.calendar_week_index())
                stale_years = max(1, (self.calendar_week_index() - completed) // 48)
                spread = min(12, 2 + stale_years * 2)
                centre = int(estimate.get("mid", (estimate.get("low", 50) + estimate.get("high", 50)) / 2))
                estimate.update({"low": max(1, centre - spread), "high": min(99, centre + spread)})
            return estimate
        return default

    def build_scouting_estimates(self, fighter, scout, kind, confidence):
        """Create a report snapshot once; UI refreshes must never reroll it."""
        reliability = int(scout.get("reliability", scout.get("skill", 45)) or 45)
        judging = int(scout.get("fighter_judging", scout.get("skill", 45)) or 45)
        potential_judging = int(scout.get("potential_judging", scout.get("skill", 45)) or 45)
        current_spread = max(2, round((108 - (confidence + judging) / 2) / 7))
        potential_spread = max(3, round((118 - (confidence + potential_judging) / 2) / 6))
        specialty = str(scout.get("specialty", ""))
        if specialty == "Prospect eye" and fighter.age <= 27:
            potential_spread = max(2, potential_spread - 2)
        if specialty == "Women’s divisions" and fighter.gender == "Female":
            current_spread = max(1, current_spread - 2)
        if specialty == "International network" and fighter.region != self.player_region:
            current_spread = max(1, current_spread - 1)
        current_error = max(1, round((118 - reliability - judging * 0.35) / 18))
        potential_error = max(1, round((124 - reliability - potential_judging * 0.35) / 17))
        current_bias = random.randint(-current_error, current_error)
        potential_bias = random.randint(-potential_error, potential_error)

        def estimate(value, spread=current_spread, bias=current_bias):
            centre = max(1, min(99, int(value) + bias))
            return {"low": max(1, centre - spread), "high": min(99, centre + spread), "mid": centre}

        exact_current = kind == "full"
        fields = {
            "overall": estimate(fighter.overall),
            "popularity": estimate(fighter.popularity, max(2, current_spread + 1)),
            "star_quality": estimate(fighter.star_quality, max(3, current_spread + 2)),
            "media_presence": estimate(fighter.media_presence, max(3, current_spread + 2)),
            "professionalism": estimate(fighter.professionalism, max(3, current_spread + 1)),
            "potential": estimate(fighter.potential, potential_spread, potential_bias),
        }
        if exact_current:
            for key in ("overall", "popularity", "star_quality", "media_presence", "professionalism"):
                value = int(getattr(fighter, key))
                fields[key] = {"low": value, "high": value, "mid": value}
        return fields

    def process_scouting_reports(self):
        self.migrate_scouting_state()
        fighters = {self.scouting_report_key(fighter): fighter for fighter in self.all_scoutable_fighters()}
        for fighter_id, report in list(self.scouting_reports.items()):
            if report.get("status") != "In progress":
                continue
            if report.get("kind") == "observation":
                report["weeks_remaining"] = max(0, int(report.get("weeks_remaining", 26)) - 1)
                if report["weeks_remaining"] == 0:
                    report["status"] = "Expired"
                    name = report.get("fighter_name", fighter_id)
                    self.inbox.append({"subject": f"Observation Expired - {name}", "body": f"{name} did not compete during the observation window. The scout assignment has been released.", "type": "Scouting", "resolved": False, "fighter_id": fighter_id})
                continue
            report["weeks_remaining"] = max(0, int(report.get("weeks_remaining", 0)) - 1)
            if report["weeks_remaining"] == 0:
                report["status"] = "Complete"
                report["completed_week"] = self.calendar_week_index()
                report["reveal"] = 100 if report.get("kind") == "full" else report.get("confidence", 50)
                fighter = fighters.get(fighter_id)
                scout = next((member for member in self.staff if member.get("name") == report.get("scout")), {"skill": 42, "fighter_judging": 42, "potential_judging": 38, "reliability": 40})
                if fighter:
                    report["estimates"] = self.build_scouting_estimates(fighter, scout, report.get("kind", "basic"), report.get("confidence", 50))
                detail = "; ".join(report.get("notes", [])) or "Initial read complete; a full evaluation can narrow the uncertainty."
                name = report.get("fighter_name", fighter_id)
                recommendation, reason = ("REPORT COMPLETE", "Open Scouting to review the recruitment case.")
                if fighter and hasattr(self, "scout_signing_recommendation"):
                    recommendation, reason = self.scout_signing_recommendation(fighter, report)
                report["recommendation"] = recommendation
                report["recommendation_reason"] = reason
                self.inbox.append({"subject": f"Scouting Report Complete - {name}", "body": f"{report.get('kind', 'basic').title()} evaluation by {report.get('scout', 'staff')} is complete ({report.get('confidence', 0)}% confidence). {detail}\n\n{recommendation}: {reason}", "type": "Scouting", "resolved": False, "fighter_id": fighter_id})
        self.process_talent_searches()
        self.auto_assign_idle_scouts()

    def auto_assign_idle_scouts(self):
        """Keep a fully idle hired scout working without overriding player briefs."""
        scouts = [member for member in getattr(self, "staff", []) if member.get("role") == "Scout"]
        idle_scouts = [member for member in scouts if self.scout_workload(member.get("name")) == 0]
        if not idle_scouts or not hasattr(self, "start_scout_report_for_fighter"):
            return
        player_ids = {self.scouting_report_key(fighter) for fighter in getattr(self, "roster", [])}
        shortlist = set(str(key) for key in getattr(self, "scouting_shortlist", []))
        employers = {}
        candidates = []
        for fighter in getattr(self, "free_agents", []):
            employers[self.scouting_report_key(fighter)] = "Free Agent"
            candidates.append(fighter)
        for promo in getattr(self, "promotions", []):
            for fighter in promo.roster:
                employers[self.scouting_report_key(fighter)] = promo.name
                candidates.append(fighter)
        eligible = []
        seen = set()
        for fighter in candidates:
            key = self.scouting_report_key(fighter)
            if key in seen or key in player_ids or getattr(fighter, "retired", False):
                continue
            seen.add(key)
            report = self.scouting_report_for(fighter)
            if report.get("status") == "In progress" or (report.get("status") == "Complete" and self.calendar_week_index() - int(report.get("completed_week", self.calendar_week_index())) <= 52):
                continue
            division_depth = sum(member.gender == fighter.gender and member.weight == fighter.weight for member in getattr(self, "roster", []))
            public_form = fighter.record_w * 1.6 - fighter.record_l * 0.8 + fighter.record_d * 0.2
            youth_interest = max(0, 30 - fighter.age) * 0.8
            market_interest = min(15, fighter.popularity * 0.18)
            need = max(0, 10 - division_depth) * 2.5
            availability = 10 if employers.get(key) == "Free Agent" else 0
            watch = 30 if key in shortlist else 0
            regional = 6 if fighter.region == self.player_region else 0
            eligible.append((watch + need + availability + regional + youth_interest + market_interest + public_form + random.uniform(-8, 8), fighter))
        if not eligible:
            return
        eligible.sort(key=lambda row: row[0], reverse=True)
        used = set()
        for scout in idle_scouts:
            specialty = scout.get("specialty", "")
            ranked = []
            for base_score, fighter in eligible:
                key = self.scouting_report_key(fighter)
                if key in used:
                    continue
                fit = 0
                if specialty == "Prospect eye" and fighter.age <= 27:
                    fit += 10
                elif specialty == "Women’s divisions" and fighter.gender == "Female":
                    fit += 10
                elif specialty == "International network" and fighter.region != self.player_region:
                    fit += 8
                ranked.append((base_score + fit, fighter))
            if not ranked:
                break
            target = max(ranked, key=lambda row: row[0])[1]
            if self.start_scout_report_for_fighter(target, "basic", scout_name=scout.get("name"), automatic=True):
                used.add(self.scouting_report_key(target))

    def complete_fight_observation(self, fighter):
        report = self.scouting_report_for(fighter)
        if not report or report.get("status") != "In progress" or report.get("kind") != "observation":
            return
        scout = next((member for member in self.staff if member.get("name") == report.get("scout")), {})
        confidence = min(88, max(int(report.get("prior_confidence", 0)), max(48, int(report.get("confidence", 45)) + 18 + int(scout.get("fighter_judging", 45)) // 8)))
        report.update({"status": "Complete", "weeks_remaining": 0, "confidence": confidence, "reveal": confidence, "observed_fight": True, "completed_week": self.calendar_week_index()})
        report["estimates"] = self.build_scouting_estimates(fighter, scout, "observation", confidence)
        report["notes"] = list(dict.fromkeys(list(report.get("prior_notes", [])) + list(report.get("notes", [])) + ["Assessment updated from live fight observation."]))
        if hasattr(self, "scout_signing_recommendation"):
            report["recommendation"], report["recommendation_reason"] = self.scout_signing_recommendation(fighter, report)
        name = fighter.name
        advice = f"\n\n{report.get('recommendation')}: {report.get('recommendation_reason')}" if report.get("recommendation") else ""
        self.inbox.append({"subject": f"Fight Observation Complete - {name}", "body": f"{report.get('scout', 'Your scout')} observed {name}'s latest fight. The live evidence produced a {confidence}% confidence report; a full evaluation is still required for exact current ratings.{advice}", "type": "Scouting", "resolved": False, "fighter_id": self.scouting_report_key(fighter)})

    def normalize_scouting_focus(self, focus):
        return focus if focus in SCOUTING_SEARCH_FOCUSES else "Free Agent Pool"

    def scouting_search_candidate_rows(self, focus):
        focus = self.normalize_scouting_focus(focus)
        player_ids = {self.scouting_report_key(fighter) for fighter in getattr(self, "roster", [])}
        rows, seen = [], set()

        def add(source, roster):
            for fighter in roster:
                key = self.scouting_report_key(fighter)
                if key in seen or key in player_ids or getattr(fighter, "retired", False):
                    continue
                if getattr(fighter, "sport_employer", "") and getattr(fighter, "primary_discipline", "MMA") != "MMA":
                    continue
                seen.add(key)
                rows.append((fighter, source))

        if focus in ("Free Agent Pool", "Any Market", "Regional Prospects", "Young Prospects"):
            add("Free Agent", getattr(self, "free_agents", []))
        if focus in ("Rival Rosters", "Any Market", "Young Prospects"):
            for promo in getattr(self, "promotions", []):
                if focus == "Rival Rosters" and getattr(promo, "is_regional_feeder", False):
                    continue
                add(promo.name, promo.roster)
        if focus == "Regional Prospects":
            for promo in getattr(self, "promotions", []):
                if getattr(promo, "is_regional_feeder", False):
                    add(promo.name, promo.roster)
            rows = [(fighter, source) for fighter, source in rows if fighter.age <= 27 or fighter.potential >= fighter.overall + 10]
        elif focus == "Young Prospects":
            rows = [(fighter, source) for fighter, source in rows if fighter.age <= 25 or fighter.potential >= fighter.overall + 14]
        return rows

    def scouting_search_score(self, fighter, scout, focus, source):
        focus = self.normalize_scouting_focus(focus)
        skill = int(scout.get("skill", 45) or 45)
        fighter_judging = int(scout.get("fighter_judging", skill) or skill)
        potential_judging = int(scout.get("potential_judging", skill) or skill)
        networking = int(scout.get("networking", skill) or skill)
        regional = int(scout.get("regional_knowledge", skill) or skill)
        reliability = int(scout.get("reliability", skill) or skill)
        noise = random.uniform(-18, 18) * max(0.35, (112 - reliability) / 70)
        scout_lift = (networking - 50) * 0.12 + (regional - 50) * 0.08
        overall_read = fighter.overall * (0.25 + fighter_judging / 260)
        upside_read = fighter.potential * (0.20 + potential_judging / 240)
        youth = max(0, 29 - fighter.age) * 1.1
        market = fighter.popularity * 0.12 + fighter.star_quality * 0.10
        affordability = max(-6, min(8, (60_000 / max(1, fighter.purse)) - 3))
        source_bonus = 5 if source == "Free Agent" else 0
        if focus == "Free Agent Pool":
            source_bonus += 12 if source == "Free Agent" else -8
            affordability *= 1.25
        elif focus == "Rival Rosters":
            source_bonus += 10 if source != "Free Agent" else -10
            market += getattr(fighter, "record_w", 0) * 0.6
        elif focus == "Regional Prospects":
            upside_read *= 1.18
            youth *= 1.3
            market *= 0.7
        elif focus == "Young Prospects":
            upside_read *= 1.25
            youth *= 1.45
        if scout.get("specialty") == "Prospect eye" and (fighter.age <= 27 or fighter.potential >= fighter.overall + 10):
            scout_lift += 8
        if scout.get("specialty") == "Women’s divisions" and fighter.gender == "Female":
            scout_lift += 8
        if scout.get("specialty") == "International network" and fighter.region != self.player_region:
            scout_lift += 7
        return overall_read + upside_read + youth + market + affordability + source_bonus + scout_lift + noise

    def talent_search_cost(self, region, scout=None, focus="Free Agent Pool"):
        distance = 0 if region == self.player_region else 1
        efficiency = int((scout or {}).get("efficiency", 45) or 45)
        focus = self.normalize_scouting_focus(focus)
        multiplier = {"Free Agent Pool": 1.0, "Rival Rosters": 1.22, "Regional Prospects": 0.95, "Young Prospects": 1.05, "Any Market": 1.08}.get(focus, 1.0)
        return max(3500, round((6500 + distance * 4500) * multiplier * (1.12 - efficiency / 500)))

    def start_talent_search(self, scout_name, region, gender="All", weight="All", focus="Free Agent Pool"):
        scout = next((member for member in self.staff if member.get("role") == "Scout" and member.get("name") == scout_name), None)
        if not scout:
            return False, "Select a hired scout."
        if self.scout_workload(scout_name) >= self.scout_capacity(scout):
            return False, f"{scout_name} has no free assignment slots."
        focus = self.normalize_scouting_focus(focus)
        cost = self.talent_search_cost(region, scout, focus)
        if self.cash < cost:
            return False, f"This search needs ${cost:,}."
        efficiency = int(scout.get("efficiency", scout.get("skill", 45)) or 45)
        weeks = max(2, 5 - int(efficiency >= 65) - int(efficiency >= 88))
        if scout.get("specialty") == "International network" and region != self.player_region:
            weeks = max(2, weeks - 1)
        assignment = {"assignment_id": f"SEARCH-{self.calendar_week_index()}-{len(getattr(self, 'scouting_searches', [])) + 1}", "type": "Talent Search", "scout": scout_name, "region": region, "gender": gender, "weight": weight, "focus": focus, "status": "In progress", "weeks_remaining": weeks, "started_week": self.calendar_week_index(), "cost": cost}
        self.scouting_searches = list(getattr(self, "scouting_searches", []))
        self.scouting_searches.append(assignment)
        self.cash -= cost
        self.record_finance_transaction(f"Talent search: {focus} ({region})", costs=cost)
        self.scouting.append(f"{scout_name} began a {focus} search in {region} ({gender}, {weight}); due in {weeks} week(s).")
        return True, f"{scout_name} started the {focus} search in {region}. Report due in {weeks} week(s)."

    def process_talent_searches(self):
        for search in getattr(self, "scouting_searches", []):
            if search.get("status") != "In progress":
                continue
            search["weeks_remaining"] = max(0, int(search.get("weeks_remaining", 0)) - 1)
            if search["weeks_remaining"] > 0:
                continue
            scout = next((member for member in self.staff if member.get("name") == search.get("scout")), {"skill": 45, "fighter_judging": 45, "potential_judging": 45, "networking": 45, "regional_knowledge": 45, "reliability": 45})
            focus = self.normalize_scouting_focus(search.get("focus", "Free Agent Pool"))
            candidate_rows = self.scouting_search_candidate_rows(focus)
            candidate_rows = [(fighter, source) for fighter, source in candidate_rows if (search.get("region") in ("All", "Worldwide") or fighter.region == search.get("region")) and (search.get("gender") == "All" or fighter.gender == search.get("gender")) and (search.get("weight") == "All" or fighter.weight == search.get("weight"))]
            unseen = [(fighter, source) for fighter, source in candidate_rows if not self.scouting_report_for(fighter)]
            if not unseen and sum(not fighter.retired for fighter in self.free_agents) < 160:
                region = search.get("region") if search.get("region") not in ("All", "Worldwide") else random.choice(REGIONS)
                gender = search.get("gender") if search.get("gender") != "All" else random.choices(("Male", "Female"), weights=(72, 28), k=1)[0]
                weight = search.get("weight") if search.get("weight") != "All" else random.choice(WEIGHTS)
                if focus != "Rival Rosters":
                    emergency_lead = self.create_generated_fighter(4, 28, 48, 75, weight=weight, gender=gender, region=region, age_override=random.randint(17, 24), pre_universe=False)
                    self.free_agents.append(emergency_lead)
                    unseen = [(emergency_lead, "Free Agent")]
            if unseen:
                networking = int(scout.get("networking", scout.get("skill", 45)) or 45)
                sample_size = min(len(unseen), max(2, 1 + networking // 22))
                sampled = random.sample(unseen, k=sample_size)
                target, source = max(sampled, key=lambda row: self.scouting_search_score(row[0], scout, focus, row[1]))
                confidence_base = (
                    scout.get("fighter_judging", 45) * 0.34
                    + scout.get("potential_judging", 45) * 0.27
                    + scout.get("reliability", 45) * 0.24
                    + scout.get("regional_knowledge", 45) * 0.08
                    + scout.get("networking", 45) * 0.07
                )
                confidence = max(45, min(88, round(confidence_base + random.randint(-max(2, (100 - int(scout.get("reliability", 45))) // 18), 5))))
                key = self.scouting_report_key(target)
                self.scouting_reports[key] = {"schema_version": 2, "fighter_id": key, "fighter_name": target.name, "kind": "basic", "status": "Complete", "started_week": search.get("started_week", self.calendar_week_index()), "completed_week": self.calendar_week_index(), "weeks_remaining": 0, "confidence": confidence, "reveal": confidence, "scout": search.get("scout"), "region": target.region, "notes": [f"Identified through a {focus.lower()} scouting brief.", f"Current market: {source}."], "estimates": self.build_scouting_estimates(target, scout, "basic", confidence)}
                search.update({"status": "Complete", "result_fighter_id": key, "result_name": target.name})
                body = f"{search.get('scout')} identified {target.name}, a {target.gender} {target.weight} from {target.region} ({source}). A {confidence}% basic dossier is now available from the {focus} brief."
            else:
                search.update({"status": "Complete", "result_name": "No suitable lead"})
                body = f"{search.get('scout')} completed the {focus} search in {search.get('region')} but found no suitable unscouted lead matching the brief."
            self.inbox.append({"subject": f"Talent Search Complete - {focus}", "body": body, "type": "Scouting", "resolved": False, "fighter_id": search.get("result_fighter_id", "")})

    def record_finance_transaction(self, label, revenue=0, costs=0):
        self.ensure_finance_defaults()
        self.finance["week_transactions"].append({
            "month": self.month, "week": self.week, "label": label,
            "revenue": max(0, round(revenue)), "costs": max(0, round(costs)),
        })
        self.finance["week_transactions"] = self.finance["week_transactions"][-240:]
        net = round(revenue) - round(costs)
        if net:
            parts = []
            if revenue:
                parts.append(f"${round(revenue):,} income")
            if costs:
                parts.append(f"${round(costs):,} costs")
            self.record_change("Finance", label, net, " and ".join(parts))

    # ---- Crossover superfights (player-only) -------------------------------

    def crossover_promotion_of(self, fighter):
        for promo in getattr(self, "promotions", []):
            if fighter in promo.roster:
                return promo
        return None

    def crossover_weight_gap(self, weight_a, weight_b):
        """Number of divisions between two weight classes (None if unrecognised)."""
        if weight_a not in WEIGHTS or weight_b not in WEIGHTS:
            return None
        return abs(WEIGHTS.index(weight_a) - WEIGHTS.index(weight_b))

    def eligible_crossover_champions(self, gender=None, weight=None, max_class_gap=1):
        """Rival AI champions available for a non-title superfight.

        A superfight is same-division by default; a one-class gap is allowed as a
        catchweight. A Lightweight can never be matched with a Heavyweight."""
        champions = []
        for promo in getattr(self, "promotions", []):
            if getattr(promo, "is_regional_feeder", False):
                continue
            for fighter in promo.roster:
                if getattr(fighter, "champion", False) and not getattr(fighter, "retired", False) and not getattr(fighter, "injured", 0):
                    if gender and fighter.gender != gender:
                        continue
                    if weight is not None:
                        gap = self.crossover_weight_gap(weight, fighter.weight)
                        if gap is None or gap > max_class_gap:
                            continue
                    champions.append((fighter, promo))
        champions.sort(key=lambda item: -(item[0].overall + item[0].popularity))
        return champions

    def crossover_sanctioning_fee(self, rival):
        """The extra fee a rival promotion charges to sanction a superfight."""
        promo = self.crossover_promotion_of(rival)
        prestige = getattr(promo, "reputation_score", 50) if promo else 50
        return int(25000 + getattr(rival, "popularity", 40) * 1500 + prestige * 700)

    def crossover_acceptance_chance(self, rival, offer, fee=None):
        """Chance the rival promotion agrees, given your standing and the offer."""
        fee = self.crossover_sanctioning_fee(rival) if fee is None else fee
        promo = self.crossover_promotion_of(rival)
        prestige = getattr(promo, "reputation_score", 50) if promo else 50
        generosity = (offer / max(1, fee)) - 1.0
        base = 0.32 + (self.company_pop - prestige) / 130 + generosity * 0.6
        return max(0.08, min(0.95, base))

    def run_superfight_night(self, event_name, venue, region, bouts):
        """Simulate a superfight-night card in isolation.

        `bouts` is an ordered list of {"a": player_fighter, "b": opponent,
        "crossover": bool}. Every bout is non-title, so no belt ever changes
        hands; guest champions keep their belts and stay in their promotion.
        Results are real (records update). Returns a watchable package."""
        fight_logs, results, event_log = [], [], [f"{event_name} - {venue}", "=" * 60, ""]
        total_purse = 0
        star_power = 0
        crossover_count = sum(1 for bout in bouts if bout.get("crossover"))
        for index, bout in enumerate(bouts):
            a, b = bout["a"], bout["b"]
            crossover = bool(bout.get("crossover"))
            main = index == 0
            fight = {"main": main, "title": False, "tier": "Superfight" if crossover else "Prelim", "region": region, "crossover": crossover}
            a_record, b_record = a.record, b.record
            a_rating, b_rating = self.bout_rating_snapshot(a), self.bout_rating_snapshot(b)
            winner, loser, method, round_no, lines = self.simulate_fight(a, b, fight)
            excitement = self.fight_excitement(a, b, winner, loser, method, round_no, fight, a.popularity + b.popularity)
            if method == "Draw":
                self.apply_draw_result(a, b, fight)
                result_line = f"{a.name} vs {b.name} - Draw (R{round_no})"
            else:
                self.apply_result(winner, loser, fight, method)
                result_line = f"{winner.name} def. {loser.name} by {method} (R{round_no})"
            label = ("CROSSOVER SUPERFIGHT" if crossover else "PRELIM") + (" - MAIN EVENT" if main else "")
            if crossover and method != "Draw":
                if winner in self.roster:
                    gain = 2 + min(5, getattr(loser, "popularity", 40) // 20)
                    self.company_pop = min(100, self.company_pop + gain)
                    winner.star_quality = min(100, getattr(winner, "star_quality", 40) + 3)
                    winner.popularity = min(100, winner.popularity + 4)
                    winner.fight_history = ([f"Crossover superfight win over {loser.name} ({self.fighter_company_name(loser)})."] + (winner.fight_history or []))[:60]
                    self.record_world_story("Superfight", f"{winner.name} beats {loser.name} in a crossover superfight.",
                                            f"{self.player_company_name} lands a marquee cross-promotional win at {event_name}.",
                                            [self.player_company_name], [winner.name, loser.name], 3)
                elif loser in self.roster:
                    self.company_pop = max(1, self.company_pop - 1)
            fight_logs.append({
                "heading": f"{a.name} vs {b.name}", "label": label,
                "a": a.name, "b": b.name, "a_id": getattr(a, "fighter_id", ""), "b_id": getattr(b, "fighter_id", ""),
                "a_record": a_record, "b_record": b_record, "a_rating": a_rating, "b_rating": b_rating,
                "weight": a.weight, "result": result_line, "lines": list(lines) + ["", result_line],
            })
            event_log.extend([f"{label}: {a.name} vs {b.name}", result_line, ""])
            results.append((a, b, result_line, excitement))
            guest_premium = getattr(b, "popularity", 40) * 2500 if crossover else 0
            total_purse += getattr(a, "purse", 0) + getattr(b, "purse", 0) + guest_premium
            star_power += a.popularity + b.popularity
        gate = int((star_power * 4200 + self.company_pop * 9000) * (1 + 0.28 * crossover_count))
        profit = gate - total_purse
        self.cash += profit
        self.record_finance_transaction(f"Superfight Night: {event_name}", revenue=gate, costs=total_purse)
        self.company_stability = min(100, self.company_stability + 1)
        summary = f"{event_name}: {len(results)} bout(s), {crossover_count} crossover superfight(s). Gate ${gate:,}, profit ${profit:,}."
        package = {
            "date": f"Month {self.month} Week {self.week}", "company": self.player_company_name,
            "event_name": event_name, "summary": summary, "fight_count": len(results), "profit": profit,
            "finance": {"ticket_revenue": gate, "total_revenue": gate, "total_expense": total_purse, "profit": profit, "attendance": 0, "venue_capacity": 1},
            "log": [summary, ""] + event_log, "fight_logs": fight_logs,
        }
        self.archive_result_record({
            "date": package["date"], "company": self.player_company_name, "event": event_name,
            "summary": summary, "fights": len(results), "gate": f"${gate:,}", "profit": f"${profit:,}",
            "log": package["log"], "fight_logs": fight_logs, "finance": package["finance"],
        })
        self.news.insert(0, summary)
        return package

    def record_change(self, category, subject, delta, reason, importance=1):
        """Record a compact, attributed state change for weekly player reporting."""
        if getattr(self, "spectator_mode", False) and category not in {"World", "Event"}:
            return
        journal = getattr(self, "change_journal", None)
        if journal is None:
            self.change_journal = journal = []
        entry = {
            "month": int(self.month), "week": int(self.week),
            "date": self.format_game_date(), "category": str(category),
            "subject": str(subject), "delta": delta, "reason": str(reason),
            "importance": max(1, min(3, int(importance))),
        }
        journal.append(entry)
        self.change_journal = journal[-400:]

    def capture_player_change_snapshot(self):
        return {
            "cash": self.cash,
            "popularity": self.company_pop,
            "stability": self.company_stability,
            "fighters": {
                getattr(fighter, "fighter_id", "") or fighter.name: {
                    "name": fighter.name, "overall": fighter.overall,
                    "popularity": fighter.popularity, "morale": fighter.morale,
                }
                for fighter in self.roster
            },
        }

    def record_snapshot_changes(self, before, context, include_finance=True):
        """Compare two real states and retain only changes the player can act on."""
        if not before or getattr(self, "spectator_mode", False):
            return
        if include_finance and self.cash != before["cash"]:
            self.record_change("Finance", self.player_company_name, self.cash - before["cash"], context, 2)
        if self.company_pop != before["popularity"]:
            self.record_change("Popularity", self.player_company_name, self.company_pop - before["popularity"], context, 2)
        if self.company_stability != before["stability"]:
            self.record_change("Stability", self.player_company_name, self.company_stability - before["stability"], context, 2)
        changes = []
        for fighter in self.roster:
            key = getattr(fighter, "fighter_id", "") or fighter.name
            old = before["fighters"].get(key)
            if not old:
                continue
            for field, label in (("overall", "Development"), ("popularity", "Popularity"), ("morale", "Morale")):
                delta = getattr(fighter, field) - old[field]
                if delta:
                    changes.append((abs(delta), fighter.name, label, delta))
        for _magnitude, name, category, delta in sorted(changes, reverse=True)[:10]:
            reason = context
            if category == "Development":
                reason = "Monthly training, gym quality, age curve, potential and recent form"
            self.record_change(category, name, delta, reason)

    def close_finance_week(self):
        """Persist a compact, truthful weekly cashflow row for the finance dashboard."""
        self.ensure_finance_defaults()
        history = self.finance["weekly_history"]
        period = (self.month, self.week)
        transactions = [item for item in self.finance["week_transactions"] if (item["month"], item["week"]) == period]
        revenue = sum(item["revenue"] for item in transactions)
        costs = sum(item["costs"] for item in transactions)
        previous = history[-1]["ending"] if history else self.cash - revenue + costs
        row = {
            "month": self.month, "week": self.week, "opening": previous,
            "revenue": revenue, "costs": costs, "net": self.cash - previous,
            "ending": self.cash, "transactions": transactions,
        }
        if history and (history[-1]["month"], history[-1]["week"]) == period:
            history[-1] = row
        else:
            history.append(row)
        self.finance["weekly_history"] = history[-192:]

    def fluctuate_region_interest(self):
        if random.random() > 0.28:
            return
        region = random.choice(list(self.regions.keys()))
        data = self.regions[region]
        old = data.get("mma_love", 50)
        delta = random.choice([-6, -4, -2, 2, 4, 6])
        data["mma_love"] = max(15, min(100, old + delta))
        direction = "rising" if delta > 0 else "cooling"
        self.news.insert(0, f"Week {self.week}: MMA interest in {region} is {direction}; regional love is now {data['mma_love']}%.")

    def random_fighter_events(self):
        pool = [f for f in self.roster if not f.retired]
        if not pool or random.random() > 0.45:
            return
        fighter = random.choice(pool)
        event = random.choice(["viral", "badcamp", "charity", "weight", "gym"])
        if event == "viral":
            fighter.media_heat = min(100, fighter.media_heat + random.randint(6, 14))
            fighter.popularity = min(100, fighter.popularity + random.randint(1, 3))
            self.news.insert(0, f"Week {self.week}: {fighter.name} went viral after a media clip; popularity and media heat rose.")
        elif event == "badcamp":
            fighter.camp_boost = max(0, fighter.camp_boost - random.randint(1, 3))
            fighter.morale = max(1, fighter.morale - random.randint(3, 8))
            self.news.insert(0, f"Week {self.week}: {fighter.name}'s camp hit problems; morale dipped.")
        elif event == "charity":
            fighter.sponsor_appeal = min(99, fighter.sponsor_appeal + random.randint(3, 8))
            fighter.morale = min(100, fighter.morale + random.randint(2, 6))
            self.news.insert(0, f"Week {self.week}: {fighter.name} helped a local charity; sponsors took notice.")
        elif event == "weight":
            fighter.fatigue = min(100, fighter.fatigue + random.randint(4, 12))
            fighter.morale = max(1, fighter.morale - random.randint(1, 5))
            self.news.insert(0, f"Week {self.week}: {fighter.name} had a rough weight-management week.")
        else:
            gym = self.gym_by_name(fighter.camp)
            swing = random.choice([-5, -3, 3, 5])
            fighter.morale = max(1, min(100, fighter.morale + swing))
            if gym:
                gym.morale = max(25, min(95, gym.morale + (1 if swing > 0 else -1)))
            direction = "clicked with the room" if swing > 0 else "had a difficult week with the room"
            self.news.insert(0, f"Week {self.week}: {fighter.name} {direction} at {fighter.camp}; morale {'rose' if swing > 0 else 'fell'}.")

    def gym_fit_base_score(self, fighter, gym, promotion_region=""):
        local = 18 if gym.region == fighter.region else 9 if gym.region == promotion_region else 0
        style = self.gym_specialty_bonus(fighter, gym)
        attention = self.gym_attention_multiplier(gym)
        overfull = max(0.0, gym.member_count / max(1, gym.capacity) - 1.0) if gym.capacity < 500 else 0
        prospect = 5 if fighter.age < fighter.prime_start and "Prospect Development" in gym.specialties else 0
        return self.gym_effective_training(gym, fighter) * 0.70 + gym.reputation * 0.12 + style + local + prospect - overfull * 24 + attention * 4

    def gym_fit_score(self, fighter, gym, promotion_region="", randomize=False):
        affordability = -max(0, gym.monthly_fee - max(1200, fighter.purse // 8)) / 650
        noise = random.uniform(-4, 4) if randomize else 0
        return self.gym_fit_base_score(fighter, gym, promotion_region) + affordability + noise

    def move_fighter_to_gym(self, fighter, gym, reason="Career move"):
        if not gym or fighter.camp == gym.name:
            return False
        old = fighter.camp or "Independent"
        history = getattr(fighter, "camp_history", None) or []
        fit = round(self.gym_fit_score(fighter, gym, getattr(fighter, "region", "")))
        history.append({"month": self.month, "from": old, "to": gym.name, "reason": reason, "fit": fit})
        fighter.camp_history = history[-20:]
        fighter.camp = gym.name
        fighter.camp_joined_month = self.month
        fighter.camp_quality = gym.quality
        fighter.training_location = gym.region
        self.record_gym_story(gym, f"{fighter.name} joined the room", reason, fighter=fighter)
        return True

    def record_gym_story(self, gym, event, detail="", fighter=None):
        """Keep gym history as a career chronicle, not just quarterly telemetry."""
        if not gym:
            return
        entry = {
            "month": self.month, "event": event, "detail": detail,
            "members": getattr(gym, "member_count", 0), "capacity": getattr(gym, "capacity", 0),
            "effective": self.gym_effective_training(gym), "morale": getattr(gym, "morale", 0),
            "momentum": getattr(gym, "momentum", 0),
        }
        if fighter:
            entry["fighter"] = fighter.name
            entry["overall"] = fighter.overall
        gym.history = ([entry] + list(getattr(gym, "history", []) or []))[:60]

    def normalize_gym_assignments(self):
        """Place legacy promotion-camp labels into persistent world gyms once."""
        if not getattr(self, "gyms", None):
            return 0
        self.sync_gym_membership()
        gym_pool = getattr(self, "gyms", [])
        gym_lookup = {gym.name: gym for gym in gym_pool}
        viable_gyms = [gym for gym in gym_pool if gym.capacity >= 500 or gym.member_count < gym.capacity * 1.18]
        viable_gyms = viable_gyms or gym_pool
        gym_score_cache = {}
        rows = [(fighter, self.player_region) for fighter in self.roster + self.free_agents]
        for promo in self.promotions:
            rows.extend((fighter, promo.region) for fighter in promo.roster)
        for sport_world in getattr(self, "combat_sport_worlds", {}).values():
            rows.extend((fighter, getattr(fighter, "region", "")) for fighter in sport_world.get("roster", []))
        seen, moved = set(), 0
        for fighter, owner_region in rows:
            if id(fighter) in seen or fighter.retired or gym_lookup.get(fighter.camp):
                continue
            seen.add(id(fighter))
            target = gym_lookup.get(self.suggest_camp_for_fighter(fighter, owner_region, gym_pool=viable_gyms, gym_score_cache=gym_score_cache))
            if not target:
                continue
            old = fighter.camp or "Independent"
            fighter.camp = target.name
            fighter.camp_quality = target.quality
            fighter.camp_joined_month = self.month
            fighter.training_location = target.region
            if self.month > 1:
                fighter.camp_history = ((getattr(fighter, "camp_history", None) or []) + [{"month": self.month, "from": old, "to": target.name, "reason": "Joined the recognised world gym network"}])[-20:]
            moved += 1
        self.sync_gym_membership()
        return moved

    def suggest_camp_for_fighter(self, fighter, promotion_region, gym_pool=None, gym_score_cache=None):
        gyms = gym_pool if gym_pool is not None else (getattr(self, "gyms", []) or self.seed_gyms())
        pool = gyms or getattr(self, "gyms", []) or self.seed_gyms()
        if gym_score_cache is not None:
            cache_key = (
                getattr(fighter, "region", ""),
                promotion_region,
                getattr(fighter, "style", ""),
                bool(getattr(fighter, "age", 0) < getattr(fighter, "prime_start", 27)),
            )
            scored = gym_score_cache.get(cache_key)
            if scored is None:
                scored = [(gym, self.gym_fit_base_score(fighter, gym, promotion_region)) for gym in pool]
                gym_score_cache[cache_key] = scored
            affordability_floor = max(1200, int(getattr(fighter, "purse", 0) or 0) // 8)
            ranked = [
                gym for gym, _score in sorted(
                    scored,
                    key=lambda item: item[1] - max(0, item[0].monthly_fee - affordability_floor) / 650 + random.uniform(-4, 4),
                    reverse=True,
                )[:4]
            ]
        else:
            ranked = sorted(pool, key=lambda gym: self.gym_fit_score(fighter, gym, promotion_region, True), reverse=True)[:4]
        if not ranked:
            return "Independent"
        weights = [8, 5, 3, 1][:len(ranked)]
        return random.choices(ranked, weights=weights, k=1)[0].name

    def generate_weekly_world_activity(self):
        active = [f for f in self.roster if not f.injured]
        roster_by_name = {fighter.name: fighter for fighter in self.roster}
        for fighter in self.roster:
            rival = roster_by_name.get(fighter.rival)
            if rival and (rival.gender != fighter.gender or rival.weight != fighter.weight):
                fighter.rival = ""
        if active and random.random() < 0.55:
            fighter = random.choice(active)
            if fighter.media_presence + fighter.charisma + random.randint(-30, 30) > 115:
                rivals = [f for f in self.roster if f.gender == fighter.gender and f.weight == fighter.weight and f.name != fighter.name]
                if rivals:
                    target = random.choice(rivals)
                    fighter.media_heat = min(100, fighter.media_heat + random.randint(4, 10))
                    target.media_heat = min(100, target.media_heat + random.randint(2, 7))
                    self.establish_rivalry(fighter, target, "Public callout", heat=random.randint(30, 52))
                    self.news.insert(0, f"Week {self.week}: {fighter.name} called out {target.name}; media heat is rising in the {fighter.weight} division.")
        if active and random.random() < 0.18:
            fighter = random.choice(active)
            if random.random() < fighter.injury_proneness / 180:
                fighter.injured = random.randint(1, 2)
                self.inbox.append({"subject": "Training Injury", "body": f"{fighter.name} suffered a minor training injury and is out {fighter.injured} month(s).", "type": "Medical", "resolved": False})
                self.news.insert(0, f"Week {self.week}: {fighter.name} picked up an injury in camp.")
        if self.promotions and random.random() < 0.35:
            promo = random.choice(self.promotions)
            note = random.choice([
                f"{promo.name} is rumored to be chasing a new broadcast package.",
                f"{promo.name} teased a title eliminator for its next card.",
                f"{promo.name} scouts were seen at a regional show.",
                f"Executives at {promo.name} are reviewing roster cuts and contract renewals.",
            ])
            self.news.insert(0, f"Week {self.week}: {note}")
        if random.random() < 0.32:
            self.simulate_gym_world_activity()
        if random.random() < 0.2:
            scout = self.create_generated_fighter(4, 30, 35, 72)
            self.free_agents.append(scout)
            self.news.insert(0, f"Week {self.week}: {scout.name} entered the market after a strong local performance.")
        if random.random() < 0.4:
            self.surface_division_storylines()

    def surface_division_storylines(self):
        """Let the title picture move on its own: hot streaks become contenders."""
        pools = [(self.roster, self.player_company_name, self.belts)]
        for promo in self.promotions:
            pools.append((promo.roster, promo.name, promo.belts or {}))
        random.shuffle(pools)
        for roster, company, belts in pools:
            surging = [f for f in roster if not f.retired and not f.champion and f.momentum >= 3 and f.record_w >= 5]
            if not surging:
                continue
            contender = max(surging, key=lambda f: (f.momentum, f.rank_score))
            key = self.belt_key(contender.gender, contender.weight)
            champ_name = belts.get(key) if isinstance(belts, dict) else None
            contender.media_heat = min(100, contender.media_heat + random.randint(6, 12))
            contender.popularity = min(100, contender.popularity + random.randint(1, 3))
            if champ_name and champ_name != contender.name:
                champion = next((fighter for fighter in roster if fighter.name == champ_name), None)
                if champion:
                    self.establish_rivalry(contender, champion, "Title-shot campaign", heat=random.randint(35, 56))
                else:
                    contender.rival = champ_name
                self.news.insert(0, f"Week {self.week}: {contender.name} is on a tear at {company} and is calling for a shot at {contender.gender} {contender.weight} champion {champ_name}.")
            else:
                self.news.insert(0, f"Week {self.week}: {contender.name} has surged into title contention in the {company} {contender.weight} division.")
            return

    def simulate_gym_world_activity(self):
        if not getattr(self, "gyms", None):
            self.gyms = self.seed_gyms()
        self.sync_gym_membership()
        gym = random.choice(self.gyms)
        roll = random.random()
        if roll < 0.24:
            old = gym.facilities
            gym.facilities = min(99, gym.facilities + random.randint(1, 2))
            self.news.insert(0, f"Week {self.week}: {gym.name} upgraded its facilities from {old} to {gym.facilities}.")
            self.record_gym_story(gym, "Facility upgrade", f"Facilities improved from {old} to {gym.facilities}.")
        elif roll < 0.46:
            gym.scouting = min(99, gym.scouting + random.randint(1, 2))
            self.news.insert(0, f"Week {self.week}: {gym.name} expanded its regional scouting network.")
            self.record_gym_story(gym, "Scouting expansion", "The gym widened its regional talent network.")
        elif roll < 0.66:
            change = random.choice([-2, -1, 1, 2])
            gym.morale = max(25, min(95, gym.morale + change))
            self.news.insert(0, f"Week {self.week}: The room atmosphere at {gym.name} {'improved' if change > 0 else 'became strained'}.")
            self.record_gym_story(gym, "Room atmosphere", f"Morale {'improved' if change > 0 else 'dipped'} to {gym.morale}.")
        else:
            region = self.regions.get(gym.region)
            if region:
                change = random.choice([-3, -2, 2, 3, 4])
                region["mma_love"] = max(10, min(99, region.get("mma_love", 50) + change))
                direction = "rose" if change > 0 else "cooled"
                self.news.insert(0, f"Week {self.week}: Grassroots interest around {gym.city} {direction}; {gym.region} MMA love is now {region['mma_love']}%.")
        candidates = [
            f for f in self.roster + self.free_agents
            if f.camp == gym.name and not f.injured and f.fatigue < 65
        ]
        for promo in self.promotions:
            candidates.extend([f for f in promo.roster if f.camp == gym.name and not f.injured and f.fatigue < 65])
        if candidates and random.random() < 0.45:
            fighter = random.choice(candidates)
            self.apply_gym_camp_micro_improvement(fighter, gym, random.randint(2, 5))

    def process_gym_network_month(self):
        """Review room health, growth and AI camp movement once per month."""
        if not getattr(self, "gyms", None):
            self.gyms = self.seed_gyms()
        self.sync_gym_membership()
        player_ids = {id(fighter) for fighter in self.roster}
        rows = [(fighter, self.player_region) for fighter in self.free_agents]
        for promo in self.promotions:
            rows.extend((fighter, promo.region) for fighter in promo.roster)
        for sport_world in getattr(self, "combat_sport_worlds", {}).values():
            rows.extend((fighter, getattr(fighter, "region", "")) for fighter in sport_world.get("roster", []))
        by_gym = {gym.name: [] for gym in self.gyms}
        for fighter, owner_region in rows:
            if not fighter.retired:
                by_gym.setdefault(fighter.camp, []).append((fighter, owner_region))

        for gym in self.gyms:
            members = by_gym.get(gym.name, [])
            active = [fighter for fighter, _region in members]
            avg_form = sum(f.momentum for f in active) / max(1, len(active))
            elite = sum(f.overall >= 82 for f in active)
            champions = sum(f.champion or f.interim_champion for f in active)
            load = gym.member_count / max(1, gym.capacity)
            target_morale = 64 + min(10, champions * 2 + elite / max(4, len(active)) * 12) + max(-8, min(8, avg_form * 1.5))
            if gym.capacity < 500 and load > 1:
                target_morale -= min(24, (load - 1) * 28)
            gym.morale = max(25, min(95, round(gym.morale * 0.78 + target_morale * 0.22 + random.uniform(-1, 1))))
            target_momentum = max(-10, min(10, round(avg_form + champions * 1.5)))
            gym.momentum += 1 if target_momentum > gym.momentum else -1 if target_momentum < gym.momentum else 0
            if champions and random.random() < 0.12:
                gym.reputation = min(99, gym.reputation + 1)
            elif not active and gym.reputation > 35 and random.random() < 0.10:
                gym.reputation -= 1
            gym.development_reputation = max(30, min(99, round(gym.development_reputation * 0.85 + (gym.quality * 0.45 + gym.scouting * 0.25 + min(100, elite * 5) * 0.30) * 0.15)))
            if gym.capacity < 500 and load >= 0.92 and gym.facilities >= 65 and self.month - gym.last_review_month >= 6:
                growth = random.randint(5, 12)
                gym.capacity += growth
                gym.capacity_growth += growth
                gym.last_review_month = self.month
                self.record_gym_story(gym, f"Expanded capacity by {growth}", "Demand and facilities supported a larger coaching room.")
            elif not gym.last_review_month:
                gym.last_review_month = self.month
            if self.month % 3 == 0:
                self.record_gym_story(gym, "Quarterly room review", "Coaches reviewed room health, development output, and capacity.")

        moves = 0
        for gym in sorted(self.gyms, key=lambda item: item.member_count / max(1, item.capacity), reverse=True):
            if gym.capacity >= 500 or gym.member_count <= gym.capacity * 1.08:
                continue
            candidates = [(fighter, region) for fighter, region in by_gym.get(gym.name, []) if id(fighter) not in player_ids and self.month - getattr(fighter, "camp_joined_month", 0) >= 6]
            random.shuffle(candidates)
            candidates.sort(key=lambda row: self.gym_fit_score(row[0], gym, row[1]))
            for fighter, owner_region in candidates[:14]:
                old_score = self.gym_fit_score(fighter, gym, owner_region)
                target = self.gym_by_name(self.suggest_camp_for_fighter(fighter, owner_region))
                if target and target.name != gym.name and self.gym_fit_score(fighter, target, owner_region) >= old_score + 5:
                    if self.move_fighter_to_gym(fighter, target, "Sought a better training fit and more coaching attention"):
                        gym.member_count = max(0, gym.member_count - 1)
                        target.member_count += 1
                        moves += 1
                if moves >= 200:
                    break
            if moves >= 200:
                break
        self.sync_gym_membership()

    def tick_business_deals(self):
        self.ensure_finance_defaults()
        expired = []
        for deal in self.finance["sponsor_deals"]:
            deal["months"] -= 1
            if deal["months"] <= 0:
                expired.append(deal)
        self.finance["sponsor_deals"] = [deal for deal in self.finance["sponsor_deals"] if deal["months"] > 0]
        for deal in expired:
            self.finance["ledger"].insert(0, f"Month {self.month}: Sponsor deal expired: {deal['name']}.")
        if self.finance.get("media_contracts"):
            # The developed media market owns contract expiry and keeps this
            # legacy alias synchronized. Do not decrement the same deal twice.
            self.sync_legacy_media_rights()
            return
        rights = self.finance["media_rights"]
        if rights.get("months", 0) > 0:
            rights["months"] -= 1
            if rights["months"] <= 0:
                self.finance["ledger"].insert(0, f"Month {self.month}: Media rights package expired: {rights['name']}.")
                self.finance["media_rights"] = {"name": "No rights package", "months": 0, "fee": 0, "reach": 0}

    def normalize_inbox_messages(self):
        """Add durable ordering metadata to current and legacy inbox messages."""
        messages = list(getattr(self, "inbox", []) or [])
        current_month = max(1, int(getattr(self, "month", 1) or 1))
        current_week = max(1, min(4, int(getattr(self, "week", 1) or 1)))
        undated = [item for item in messages if not item.get("created_month")]
        legacy_total = len(messages)
        # Old saves did not timestamp mail. Inbox entries were appended in
        # chronological order, so spread large legacy queues conservatively at
        # roughly twenty messages per simulated month instead of declaring all
        # 600+ notices brand new forever.
        legacy_span = min(max(0, current_month - 1), max(0, (legacy_total - 1) // 20))
        for index, item in enumerate(messages):
            if not isinstance(item, dict):
                continue
            if not item.get("created_month"):
                distance = legacy_total - 1 - index
                offset = min(legacy_span, distance // 20) if legacy_total > 1 else 0
                item["created_month"] = max(1, current_month - offset)
                item["created_week"] = 1 if offset else current_week
            else:
                item["created_month"] = max(1, int(item.get("created_month", current_month) or current_month))
                item["created_week"] = max(1, min(4, int(item.get("created_week", 1) or 1)))
            item.setdefault("seen", False)
            item.setdefault("resolved", False)
        return messages

    def inbox_item_needs_action(self, item):
        """Return whether a still-live game decision depends on this message."""
        if not item or item.get("resolved", False):
            return False
        subject = str(item.get("subject", "") or "")
        subject_lower = subject.lower()
        fighter = None
        if any(token in subject_lower for token in ("contract expiring", "title shot owed", "retirement fight needed")) or item.get("action") == "serious_injury":
            fighter_id = str(item.get("fighter_id", "") or "")
            fighter_name = str(item.get("fighter", "") or subject.rsplit(" - ", 1)[-1]).strip()
            candidates = list(getattr(self, "roster", []) or []) + list(getattr(self, "free_agents", []) or []) + list(getattr(self, "retired_fighters", []) or [])
            fighter = next((candidate for candidate in candidates if (fighter_id and getattr(candidate, "fighter_id", "") == fighter_id) or candidate.name == fighter_name), None)
        action = str(item.get("action", "") or "")
        if action == "serious_injury":
            return bool(fighter and getattr(fighter, "serious_injury_pending", False))
        if action == "booking" and subject.startswith("Vacant Championship - "):
            key = subject.removeprefix("Vacant Championship - ")
            depth = sum(not candidate.retired and self.belt_key(candidate.gender, candidate.weight) == key for candidate in getattr(self, "roster", []))
            return key not in getattr(self, "closed_divisions", set()) and depth >= 2 and not self.normalize_belts(getattr(self, "belts", {})).get(key)
        if action:
            return True
        if "contract expiring" in subject_lower:
            return bool(fighter in getattr(self, "roster", []) and 0 < int(getattr(fighter, "contract_months", 0) or 0) <= 3)
        if "title shot owed" in subject_lower:
            return bool(fighter and getattr(fighter, "owed_title_shot", False))
        if "retirement fight needed" in subject_lower:
            return bool(fighter and getattr(fighter, "retirement_pending", False) and not getattr(fighter, "retired", False))
        if "academy prospect ready" in subject_lower or "academy graduation review" in subject_lower:
            name = subject.split(" - ", 1)[-1].strip()
            academy = getattr(self, "academy", {}) or {}
            return any(row.get("name") == name for row in academy.get("prospects", []) + academy.get("talent_pool", []))
        offer_id = item.get("super_event_id")
        if offer_id:
            return any(offer.get("id") == offer_id and offer.get("status", "Offered") == "Offered" for offer in getattr(self, "super_event_offers", []) or [])
        return subject_lower.startswith("urgent:")

    def maintain_inbox(self, manual=False):
        """Expire stale routine mail while preserving decisions and recent notices."""
        self.normalize_inbox_messages()
        current_month = max(1, int(getattr(self, "month", 1) or 1))
        resolved_limit = 1 if manual else 3
        read_limit = 3 if manual else 6
        unread_limit = 9 if manual else 12
        kept = []
        removed = 0
        for item in self.inbox:
            if not isinstance(item, dict):
                removed += 1
                continue
            if self.inbox_item_needs_action(item):
                kept.append(item)
                continue
            age = max(0, current_month - int(item.get("created_month", current_month) or current_month))
            subject = str(item.get("subject", "") or "").lower()
            stale_state_notice = (
                "contract expiring" in subject
                or "title shot owed" in subject
                or "observation expired" in subject
            )
            should_remove = (
                stale_state_notice
                or (item.get("resolved", False) and age >= resolved_limit)
                or (item.get("seen", False) and age >= read_limit)
                or (not item.get("seen", False) and age >= unread_limit)
            )
            if should_remove:
                removed += 1
            else:
                kept.append(item)

        # Keep the recent working set bounded even in scouting-heavy careers.
        # Actionable items never count against this limit.
        routine_positions = [index for index, item in enumerate(kept) if not self.inbox_item_needs_action(item)]
        excess = max(0, len(routine_positions) - 400)
        if excess:
            discard = set(routine_positions[:excess])
            kept = [item for index, item in enumerate(kept) if index not in discard]
            removed += excess
        self.inbox = kept
        return {"removed": removed, "remaining": len(kept)}

    def world_month_steps(self, player_ran_show):
        change_state = {}

        def capture_month_start():
            change_state["before"] = self.capture_player_change_snapshot()

        steps = [
            ("Capturing monthly changes", capture_month_start),
            ("Gym network review", self.process_gym_network_month),
            ("Player roster development", lambda: self.age_and_develop_fighters(self.roster, player_roster=True)),
            # Unsigned fighters still train, heal, lose fatigue, and age. Leaving
            # them outside this monthly pass made a minor injury permanent and
            # eventually froze both the retirement queue and transfer market.
            ("Free-agent recovery and development", lambda: self.age_and_develop_fighters(self.free_agents)),
            ("Annual regional wonderkid intake", self.spawn_annual_regional_wonderkid),
        ]
        # Feeders used to always process in the same fixed list order (Japan
        # Fight Circuit first among them), so whichever circuit ran first each
        # month systematically won the once-per-month-global regional
        # graduation overflow slots (emergency thin-division and exceptional
        # aging-out call-ups). Randomize only the execution order here; the
        # underlying self.promotions list order stays stable for company
        # listings elsewhere.
        monthly_promotion_order = list(self.promotions)
        random.shuffle(monthly_promotion_order)
        for promo in monthly_promotion_order:
            def process_promotion_month(promo=promo):
                self.age_and_develop_fighters(promo.roster)
                if getattr(promo, "is_regional_feeder", False):
                    self.simulate_regional_feeder_month(promo)
                elif random.random() < self.ai_show_chance(promo) * 0.65:
                    self.simulate_ai_promotion_month(promo, develop=False)
            steps.append((f"{promo.name} monthly review", process_promotion_month))
        worlds = getattr(self, "combat_sport_worlds", {}) or self.seed_combat_sport_worlds()
        self.combat_sport_worlds = worlds
        steps.append(("Career goals", self.process_career_goals))
        steps.append(("Career stories", self.process_career_arcs))
        for sport, world in list(worlds.items()):
            steps.append((
                f"{sport} circuit",
                lambda sport=sport, world=world: self.process_combat_sport_world(sport, world),
            ))
        steps.extend([
            ("Non-exclusive activity", self.simulate_nonexclusive_outside_fights),
            ("Free-agent negotiations", self.advance_free_agent_market),
            ("AI roster reviews", self.review_ai_roster_cuts),
            ("AI upgrade reviews", self.review_ai_upgrade_replacements),
            ("Monthly transfer market", self.market_churn),
            ("AI operating costs", self.apply_ai_operating_costs),
            ("Promotion survival", self.process_promotion_failures),
            ("Executive reviews", self.review_ai_executives),
            ("World replenishment", self.ensure_world_fighter_target),
            ("World balance metrics", self.update_world_metric_interactions),
            ("Media market and contracts", self.process_media_month),
            ("Contract warnings", self.check_contract_warnings),
            ("Contract promises", self.review_contract_promises),
            ("Player renewals", self.auto_renew_player_contracts),
            ("Player contracts", self.update_contracts),
            ("AI contracts", self.update_ai_contracts),
            ("Retirement reviews", self.process_retirements),
            ("Promotion rankings", self.refresh_promotion_rankings),
            ("Company milestones and invitations", self.process_company_milestones_and_super_events),
            ("Inbox housekeeping", self.maintain_inbox),
        ])

        def finish_month():
            if not player_ran_show and not getattr(self, "spectator_mode", False):
                self.company_pop = max(1, self.company_pop - 1)
                self.news.insert(0, f"{self.player_company_name} stayed quiet this month; fans drifted toward other shows.")
            reason = "Monthly operations, contracts, training and market activity"
            if not player_ran_show and not getattr(self, "spectator_mode", False):
                reason += "; no event was promoted, causing audience drift"
            self.record_snapshot_changes(change_state.get("before"), reason, include_finance=False)
            self.news = self.news[:120]

        steps.append(("Finalising the month", finish_month))
        steps.append(("Industry standings snapshot", self.snapshot_industry_standings))
        return steps

    def process_world_month(self, player_ran_show):
        for _label, task in self.world_month_steps(player_ran_show):
            task()

    def update_world_metric_interactions(self):
        """Let the big world metrics talk to each other once per month.

        This gives long saves a pulse: company finance affects risk appetite,
        thin divisions create scouting pressure, strong regions become more
        attractive, and combat-sport activity feeds the wider fight economy.
        """
        active = [fighter for fighter in self.all_fighter_objects() if not fighter.retired]
        free = [fighter for fighter in self.free_agents if not fighter.retired]
        contracted = [fighter for fighter in self.roster if not fighter.retired]
        contracted.extend(
            fighter for promo in self.promotions
            if not getattr(promo, "is_regional_feeder", False)
            for fighter in promo.roster if not fighter.retired
        )
        contracted_80 = sum(fighter.overall >= 80 for fighter in contracted)
        contracted_90 = sum(fighter.overall >= 90 for fighter in contracted)
        contracted_95 = sum(fighter.overall >= 95 for fighter in contracted)
        share_80 = contracted_80 / max(1, len(contracted))
        share_90 = contracted_90 / max(1, len(contracted))
        distressed = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False) and (promo.cash < 0 or promo.stability < 28)]
        healthy = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False) and promo.cash > promo.size * 16_000 and promo.stability >= 55]
        sport_activity = sum(len(world.get("event_history", [])) for world in getattr(self, "combat_sport_worlds", {}).values())
        self.world_balance_metrics = {
            "month": self.month,
            "active_fighters": len(active),
            "free_agents": len(free),
            "contracted_fighters": len(contracted),
            "contracted_80_plus": contracted_80,
            "contracted_90_plus": contracted_90,
            "contracted_95_plus": contracted_95,
            "contracted_80_share": round(share_80, 4),
            "contracted_90_share": round(share_90, 4),
            "distressed_promotions": len(distressed),
            "healthy_promotions": len(healthy),
            "combat_sport_activity": sport_activity,
        }
        current_year = self.current_year()
        if ((self.month - 1) % 12 == 0
                and int(self.rules.get("talent_health_report_year", 0) or 0) < current_year):
            self.rules["talent_health_report_year"] = current_year
            detail = (
                f"Contracted MMA talent: {len(contracted)} fighters; {contracted_80} rated 80+ "
                f"({share_80:.1%}), {contracted_90} rated 90+ ({share_90:.1%}), and "
                f"{contracted_95} rated 95+. Free-agent reserve: {len(free)}."
            )
            self.record_world_story(
                "World Talent Report", f"{current_year} world talent report published.",
                detail, importance=2,
            )
            if not getattr(self, "spectator_mode", False) and (share_80 < 0.13 or share_90 < 0.015):
                self.inbox.append({
                    "subject": f"World Talent Pipeline Warning - {current_year}",
                    "body": detail + " The global elite pipeline is below its sustainable range; regional scouting and academy development may carry extra value.",
                    "type": "Scouting", "resolved": False,
                })
        if len(free) < 70 and random.random() < 0.35:
            region = random.choice(REGION_GENERATION_POOL)
            prospect = self.create_generated_fighter(6, 34, 42, 80, region=region)
            self.avoid_name_collision(prospect, self.active_fighter_names())
            self.free_agents.append(prospect)
            self.news.insert(0, f"World scouting response: {prospect.name} emerged from {region} as the market tightened.")
        for promo in healthy[:4]:
            strategy = self.promotion_strategy(promo)
            strategy["market_momentum"] = min(38, strategy.get("market_momentum", 0) + random.uniform(0.4, 1.2))
            if strategy.get("current_mode") == "Financial Recovery":
                strategy["current_mode"] = "Balanced"
        for promo in distressed:
            strategy = self.promotion_strategy(promo)
            strategy["current_mode"] = "Financial Recovery"
            strategy["market_momentum"] = max(-38, strategy.get("market_momentum", 0) - random.uniform(0.6, 1.8))
        if sport_activity and self.month % 6 == 0:
            for region, data in self.regions.items():
                combat_lift = sum(1 for world in getattr(self, "combat_sport_worlds", {}).values() for fighter in world.get("roster", []) if fighter.region == region) // 20
                if combat_lift:
                    data["mma_love"] = max(1, min(100, data.get("mma_love", 50) + min(2, combat_lift)))

    def combat_sport_roster(self, sport, employer=None):
        world = getattr(self, "combat_sport_worlds", {}).get(sport, {})
        roster = [fighter for fighter in world.get("roster", []) if not getattr(fighter, "retired", False)]
        if employer:
            roster = [fighter for fighter in roster if fighter.sport_employer == employer]
        return roster

    def combat_sport_for_fighter(self, fighter):
        for sport, world in getattr(self, "combat_sport_worlds", {}).items():
            if fighter in world.get("roster", []):
                return sport
        native = getattr(fighter, "primary_discipline", "")
        if native == "Lethwei":
            return "Muay Thai"
        return native if native in ("Boxing", "Kickboxing", "Muay Thai", "Wrestling", "Brazilian Jiu-Jitsu") else ""

    def combat_sport_rating(self, fighter, sport):
        if getattr(fighter, "primary_discipline", "") == "Lethwei":
            # Keep Lethwei's toughness/power identity without giving its shared
            # Muay Thai rankings a larger total weighting than native athletes.
            return fighter.striking * 1.08 + fighter.power * 0.40 + fighter.toughness * 0.34 + fighter.cardio * 0.22 + fighter.fight_iq * 0.16
        if sport == "Boxing":
            return fighter.striking * 1.25 + fighter.power * 0.42 + fighter.chin * 0.28 + fighter.cardio * 0.24 + fighter.fight_iq * 0.22
        if sport in ("Kickboxing", "Muay Thai"):
            return fighter.striking * 1.12 + fighter.power * 0.36 + fighter.toughness * 0.28 + fighter.cardio * 0.24 + fighter.fight_iq * 0.20
        if sport == "Wrestling":
            return fighter.wrestling * 1.35 + fighter.ground_control * 0.42 + fighter.cardio * 0.30 + fighter.toughness * 0.20 + fighter.fight_iq * 0.22
        if sport == "Brazilian Jiu-Jitsu":
            return fighter.grappling * 1.30 + fighter.submissions * 0.46 + fighter.ground_control * 0.30 + fighter.cardio * 0.20 + fighter.fight_iq * 0.24
        return fighter.overall * 2.0 + fighter.popularity * 0.25

    def combat_sport_rating_scale(self, sport, fighter=None):
        """Convert each raw ranking formula to the same readable 1-99 scale."""
        if fighter is not None and getattr(fighter, "primary_discipline", "") == "Lethwei":
            return 2.20
        return {
            "Boxing": 2.41,
            "Kickboxing": 2.20,
            "Muay Thai": 2.20,
            "Wrestling": 2.49,
            "Brazilian Jiu-Jitsu": 2.50,
        }.get(sport, 2.0)

    def combat_sport_display_rating(self, fighter, sport):
        return round(self.combat_sport_rating(fighter, sport) / self.combat_sport_rating_scale(sport, fighter), 1)

    def combat_sport_development_profile(self, sport):
        """Detailed-skill source of truth for training and age decline by sport."""
        profiles = {
            "Boxing": {
                "growth": ("punch_technique", "hand_speed", "footwork", "head_movement", "guard_defence", "punch_power", "feints", "conditioning", "composure", "adaptability"),
                "decline": ("hand_speed", "footwork", "head_movement", "reflexes", "conditioning", "stun_recovery", "punch_power"),
                "preferred_focus": "Striking", "growth_mult": 1.03, "decline_base": 0.020, "decline_slope": 0.032,
            },
            "Kickboxing": {
                "growth": ("punch_technique", "hand_speed", "footwork", "high_kick_technique", "high_kick_speed", "low_kick_technique", "low_kick_speed", "kick_defence", "conditioning", "mobility", "composure"),
                "decline": ("hand_speed", "footwork", "high_kick_speed", "low_kick_speed", "reflexes", "conditioning", "mobility", "stun_recovery"),
                "preferred_focus": "Striking", "growth_mult": 1.00, "decline_base": 0.022, "decline_slope": 0.034,
            },
            "Muay Thai": {
                "growth": ("low_kick_technique", "high_kick_technique", "knees", "elbows", "thai_plum", "clinch_control", "kick_defence", "mobility", "conditioning", "resilience", "composure"),
                "decline": ("high_kick_speed", "low_kick_speed", "mobility", "reflexes", "conditioning", "footwork", "stun_recovery", "resilience"),
                "preferred_focus": "Striking", "growth_mult": 1.04, "decline_base": 0.026, "decline_slope": 0.034,
            },
            "Wrestling": {
                "growth": ("takedowns", "takedown_setup", "takedown_speed", "chain_wrestling", "sprawl", "takedown_defence_detail", "throws", "ride_control", "top_control", "scrambles", "strength", "conditioning", "discipline"),
                "decline": ("takedown_speed", "chain_wrestling", "scrambles", "mobility", "strength", "conditioning", "get_ups", "resilience"),
                "preferred_focus": "Wrestling", "growth_mult": 1.00, "decline_base": 0.030, "decline_slope": 0.030,
            },
            "Brazilian Jiu-Jitsu": {
                "growth": ("guard_work", "transitions", "positional_ability", "submission_attack", "submission_defence_detail", "back_control", "mount_control", "leg_locks", "scrambles", "bottom_control", "top_control", "flexibility", "composure", "adaptability"),
                "decline": ("scrambles", "mobility", "conditioning", "strength", "flexibility", "get_ups", "resilience"),
                "preferred_focus": "Grappling", "growth_mult": 0.97, "decline_base": 0.032, "decline_slope": 0.025,
            },
        }
        return profiles.get(sport, profiles["Boxing"])

    def combat_sport_effective_prime_end(self, fighter, sport):
        tail = 1 if getattr(fighter, "career_archetype", "") == "Durable Career" else 0
        if sport == "Brazilian Jiu-Jitsu":
            tail += 1
        return fighter.prime_end + tail

    def combat_sport_development_stage(self, fighter, sport):
        if fighter.age < fighter.prime_start:
            return "Pre-prime"
        end = self.combat_sport_effective_prime_end(fighter, sport)
        if fighter.age <= end:
            return "Prime"
        years = fighter.age - end
        return "Early decline" if years <= 2 else "Decline" if years <= 6 else "Deep decline"

    def combat_sport_focus_keys(self, focus):
        return {
            "Striking": tuple(STANDING_SKILLS),
            "Wrestling": tuple(WRESTLING_SKILLS),
            "Grappling": tuple(GROUND_SKILLS),
            "Conditioning": ("conditioning", "resilience", "stun_recovery", "mobility"),
            "Game Plan": ("composure", "adaptability", "discipline", "confidence", "consistency"),
            "Weight Management": ("weight_cutting", "conditioning", "discipline"),
        }.get(focus, ())

    def combat_sport_growth_allowed(self, fighter, sport):
        if getattr(fighter, "retired", False) or fighter.injured:
            return False
        current = self.combat_sport_display_rating(fighter, sport)
        return current < min(99, fighter.potential)

    def combat_sport_weighted_skill_sample(self, pool, count):
        chosen = []
        candidates = list(pool)
        while candidates and len(chosen) < count:
            key = random.choice(candidates)
            chosen.append(key)
            candidates = [candidate for candidate in candidates if candidate != key]
        return chosen

    def apply_combat_sport_broad_delta(self, fighter, sport, amount, keys):
        """Keep the readable native rating moving with its detailed source skills."""
        primary = "striking" if sport in ("Boxing", "Kickboxing", "Muay Thai") else "wrestling" if sport == "Wrestling" else "grappling"
        setattr(fighter, primary, max(1, min(99, getattr(fighter, primary) + amount)))
        key_set = set(keys)
        secondary = []
        if key_set & {"punch_power", "high_kick_power", "low_kick_power", "strength"}:
            secondary.append("power")
        if key_set & {"conditioning", "resilience", "stun_recovery"}:
            secondary.append("cardio")
        if key_set & {"composure", "adaptability", "discipline", "confidence", "consistency"}:
            secondary.append("fight_iq")
        if key_set & {"chin_strength", "stun_recovery", "resilience"}:
            secondary.append("chin")
        if sport == "Wrestling" and key_set & {"ride_control", "top_control", "scrambles"}:
            secondary.append("ground_control")
        if sport == "Brazilian Jiu-Jitsu":
            if key_set & {"submission_attack", "leg_locks", "back_control"}:
                secondary.append("submissions")
            if key_set & {"top_control", "positional_ability", "mount_control"}:
                secondary.append("ground_control")
            if key_set & {"submission_defence_detail", "guard_work"}:
                secondary.append("submission_defence")
        if secondary:
            field = random.choice(list(dict.fromkeys(secondary)))
            setattr(fighter, field, max(1, min(99, getattr(fighter, field) + amount)))

    def adjust_combat_sport_training_key(self, fighter, sport, key, amount, reason):
        """Apply one camp improvement without invoking the MMA-wide detail resync."""
        if amount > 0 and not self.combat_sport_growth_allowed(fighter, sport):
            return False
        self.ensure_detailed_skills(fighter)
        before_rating = self.combat_sport_display_rating(fighter, sport)
        before_detail = fighter.detailed_skills.get(key, 50)
        broad_fields = ("striking", "wrestling", "grappling", "cardio", "chin", "power", "ground_control", "submissions", "submission_defence", "fight_iq")
        broad_before = {field: getattr(fighter, field) for field in broad_fields}
        next_detail = max(1, min(99, before_detail + amount))
        if next_detail == before_detail:
            return False
        fighter.detailed_skills[key] = next_detail
        self.apply_combat_sport_broad_delta(fighter, sport, amount, [key])
        after_rating = self.combat_sport_display_rating(fighter, sport)
        if amount > 0 and after_rating > min(99, fighter.potential) + 0.01:
            fighter.detailed_skills[key] = before_detail
            for field, value in broad_before.items():
                setattr(fighter, field, value)
            return False
        if fighter.detailed_skills[key] != before_detail:
            self.record_combat_sport_development(fighter, sport, before_rating, after_rating, [key], reason)
            return True
        return False

    def adjust_combat_sport_skill_bundle(self, fighter, sport, amount, reason="Training", decline=False, key_count=None):
        """Mutate native detailed skills first, then synchronize broad ratings once."""
        if amount > 0 and not self.combat_sport_growth_allowed(fighter, sport):
            return []
        self.ensure_detailed_skills(fighter)
        profile = self.combat_sport_development_profile(sport)
        base_pool = list(profile["decline" if decline else "growth"])
        if not decline:
            focus = getattr(fighter, "camp_focus", "Balanced")
            focus_pool = list(self.combat_sport_focus_keys(focus))
            compatible = [key for key in focus_pool if key in base_pool]
            if compatible:
                base_pool = compatible * 2 + base_pool
            # An incompatible focus does not convert child-sport development
            # into hidden MMA cross-training. Native skills remain the source
            # of truth until the athlete actually crosses into MMA.
        stage = self.combat_sport_development_stage(fighter, sport)
        if key_count is None:
            key_count = 5 if stage == "Pre-prime" and not decline else 3 if not decline else 5
        keys = self.combat_sport_weighted_skill_sample(base_pool, key_count)
        if not keys:
            return []
        before_values = {key: fighter.detailed_skills.get(key, 50) for key in keys}
        broad_fields = ("striking", "wrestling", "grappling", "cardio", "chin", "power", "ground_control", "submissions", "submission_defence", "fight_iq")
        broad_before = {field: getattr(fighter, field) for field in broad_fields}
        before_rating = self.combat_sport_display_rating(fighter, sport)
        for key in keys:
            fighter.detailed_skills[key] = max(1, min(99, fighter.detailed_skills.get(key, 50) + amount))
        changed = [key for key in keys if fighter.detailed_skills.get(key, 50) != before_values[key]]
        if not changed:
            return []
        self.apply_combat_sport_broad_delta(fighter, sport, amount, changed)
        after_rating = self.combat_sport_display_rating(fighter, sport)
        if not decline and after_rating > min(99, fighter.potential) + 0.01:
            for key, value in before_values.items():
                fighter.detailed_skills[key] = value
            for field, value in broad_before.items():
                setattr(fighter, field, value)
            return []
        if changed:
            self.record_combat_sport_development(fighter, sport, before_rating, self.combat_sport_display_rating(fighter, sport), changed, reason)
        return changed

    def record_combat_sport_development(self, fighter, sport, before, after, keys, reason):
        fighter.sport_development_log = list(getattr(fighter, "sport_development_log", None) or [])
        fighter.sport_development_log.insert(0, {
            "month": self.month, "year": self.current_year(), "sport": sport,
            "before": round(before, 1), "after": round(after, 1),
            "change": round(after - before, 1), "skills": list(keys), "reason": reason,
        })
        fighter.sport_development_log = fighter.sport_development_log[:60]

    def record_combat_sport_rating_snapshot(self, fighter, sport):
        history = dict(getattr(fighter, "sport_rating_history", None) or {})
        sport_history = dict(history.get(sport, {}) or {})
        sport_history[str(self.month)] = self.combat_sport_display_rating(fighter, sport)
        if len(sport_history) > 180:
            for key in sorted(sport_history, key=lambda value: int(value))[:-180]:
                sport_history.pop(key, None)
        history[sport] = sport_history
        fighter.sport_rating_history = history

    def combat_sport_rating_trend(self, fighter, sport, months=12):
        history = (getattr(fighter, "sport_rating_history", None) or {}).get(sport, {})
        if not history:
            return 0.0
        current = self.combat_sport_display_rating(fighter, sport)
        target = self.month - months
        eligible = [(int(key), value) for key, value in history.items() if int(key) <= target]
        if not eligible:
            eligible = [(int(key), value) for key, value in history.items()]
        _month, previous = min(eligible, key=lambda item: abs(item[0] - target))
        return round(current - previous, 1)

    def combat_sport_monthly_growth_chance(self, fighter, sport):
        if not self.combat_sport_growth_allowed(fighter, sport):
            return 0.0
        stage = self.combat_sport_development_stage(fighter, sport)
        current = self.combat_sport_display_rating(fighter, sport)
        gap = max(0, min(99, fighter.potential) - current)
        gym = self.gym_by_name(fighter.camp)
        quality = self.gym_quality(fighter.camp)
        facilities = gym.facilities if gym else quality
        dedication = self.ds(fighter, "dedication", fighter.professionalism)
        human = (dedication + fighter.professionalism + fighter.motivation + fighter.morale) / 4
        specialty = self.gym_specialty_bonus(fighter, gym)
        crowd = max(0, (gym.member_count - gym.capacity) / max(1, gym.capacity)) if gym and gym.capacity < 500 else 0
        inactivity = self.combat_sport_inactivity_months(fighter)
        if inactivity >= 20:
            activity = -0.075
        elif inactivity >= 12:
            activity = -0.035
        elif 1 <= inactivity <= 6:
            activity = 0.025
        else:
            activity = 0.0
        if stage == "Pre-prime":
            base = 0.10
            gap_bonus = min(0.12, gap * 0.006)
        elif stage == "Prime":
            base = 0.025
            gap_bonus = min(0.055, gap * 0.0035)
        else:
            base = min(0.012, self.veteran_resurgence_chance(fighter) * 0.30)
            gap_bonus = 0.0
        chance = (
            base + gap_bonus
            + (quality + facilities - 100) / 900
            + (human - 55) / 650
            + specialty / 360
            + activity
            + max(0, fighter.momentum) * 0.006
            - fighter.fatigue * 0.0015
            - crowd * 0.11
        ) * self.combat_sport_development_profile(sport)["growth_mult"]
        ceiling = 0.40 if stage == "Pre-prime" else 0.16 if stage == "Prime" else 0.015
        return max(0.0, min(ceiling, chance))

    def combat_sport_monthly_decline_chance(self, fighter, sport):
        years_over = fighter.age - self.combat_sport_effective_prime_end(fighter, sport)
        if years_over <= 0:
            return 0.0
        profile = self.combat_sport_development_profile(sport)
        resilience = self.ds(fighter, "resilience", fighter.toughness)
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        professional_buffer = (fighter.professionalism + resilience + conditioning - 165) / 1800
        health = fighter.injured * 0.012 + max(0, fighter.fatigue - 45) / 850 + fighter.injury_proneness / 3000
        form = max(0, -fighter.momentum) * 0.012 + max(0, 45 - fighter.morale) / 950
        chance = profile["decline_base"] + years_over * profile["decline_slope"] + health + form - professional_buffer
        if years_over <= 2:
            chance *= 0.62
        if getattr(fighter, "career_archetype", "") == "Durable Career":
            chance *= 0.80
        return max(0.0, min(0.34, chance))

    def apply_combat_sport_annual_age_curve(self, fighter, sport):
        stage = self.combat_sport_development_stage(fighter, sport)
        if stage == "Pre-prime" and self.combat_sport_growth_allowed(fighter, sport):
            gap = max(0, min(99, fighter.potential) - self.combat_sport_display_rating(fighter, sport))
            chance = min(0.62, 0.22 + gap * 0.016 + max(0, fighter.professionalism - 55) / 500)
            if random.random() < chance:
                self.adjust_combat_sport_skill_bundle(fighter, sport, 1, "Annual athletic and technical maturation", key_count=5)
        elif stage in ("Early decline", "Decline", "Deep decline"):
            years_over = fighter.age - self.combat_sport_effective_prime_end(fighter, sport)
            profile = self.combat_sport_development_profile(sport)
            chance = min(0.88, 0.10 + years_over * 0.10 + profile["decline_slope"] * 2)
            if getattr(fighter, "career_archetype", "") == "Durable Career":
                chance *= 0.78
            if random.random() < chance:
                amount = -2 if years_over >= 5 and random.random() < min(0.75, 0.25 + years_over * 0.07) else -1
                self.adjust_combat_sport_skill_bundle(fighter, sport, amount, "Annual age-curve review", decline=True, key_count=6)
        self.record_combat_sport_rating_snapshot(fighter, sport)

    def combat_sport_ranked(self, sport, employer=None):
        return sorted(
            self.combat_sport_roster(sport, employer),
            key=lambda fighter: (
                self.combat_sport_rating(fighter, sport),
                fighter.record_w - fighter.record_l,
                fighter.popularity,
                -fighter.age,
            ),
            reverse=True,
        )

    def combat_sport_division_key(self, fighter, sport=None):
        """Stable save key for a non-MMA championship division."""
        sport = sport or ("Muay Thai" if getattr(fighter, "primary_discipline", "") == "Lethwei" else getattr(fighter, "primary_discipline", ""))
        division = self.combat_sport_competition_class(sport, fighter) if sport else (getattr(fighter, "sport_weight_class", "") or fighter.weight)
        return f"{fighter.gender}|{division}"

    def combat_sport_division_label(self, key):
        gender, _, weight = str(key).partition("|")
        return f"{gender} {weight}" if weight else gender

    def combat_sport_state(self, sport, world, player_owned=False):
        if player_owned:
            return getattr(self, "player_combat_divisions", {}).get(sport, world)
        return world

    def combat_sport_roster_target(self, sport, world):
        """Return the persistent circuit depth target, including migrated saves."""
        current = len(self.combat_sport_roster(sport, world.get("promotion", "")))
        baseline = max(36, int(world.get("starting_roster_size", current or 36)))
        target = max(int(world.get("roster_target", 0) or 0), baseline * COMBAT_SPORT_ROSTER_TARGET_MULTIPLIER)
        world["starting_roster_size"] = baseline
        world["roster_target"] = target
        return target

    def ensure_combat_sport_circuit_state(self, sport, world, employer=None, player_owned=False):
        """Migrate the old one-champion circuit into divisional, persistent state."""
        state = self.combat_sport_state(sport, world, player_owned)
        if not player_owned:
            employer = world.get("promotion", employer)
        state.setdefault("titles", {})
        state.setdefault("title_history", {})
        state.setdefault("rankings_by_division", {})
        state.setdefault("records", {})
        state.setdefault("record_book", {})
        state.setdefault("season_stats", {})
        state.setdefault("awards", [])
        state.setdefault("hall_of_fame", [])
        state.setdefault("finance_history", [])
        state.setdefault("reputation", 50 if player_owned else 62)
        state.setdefault("stability", 60 if player_owned else 72)
        if not player_owned:
            starting_cash = {
                "Boxing": 8_000_000,
                "Kickboxing": 4_500_000,
                "Muay Thai": 3_800_000,
                "Wrestling": 3_000_000,
                "Brazilian Jiu-Jitsu": 2_800_000,
            }.get(sport, 3_000_000)
            state.setdefault("cash", starting_cash)
            state.setdefault("starting_roster_size", len(self.combat_sport_roster(sport, employer)))
            self.combat_sport_roster_target(sport, world)
        roster = self.combat_sport_roster(sport, employer)
        for fighter in roster:
            native_sport = getattr(fighter, "primary_discipline", sport)
            if native_sport not in COMBAT_SPORT_WEIGHT_CLASSES:
                native_sport = sport
            expected = (getattr(self, "combat_sport_seed_divisions", {}) or {}).get(native_sport, {}).get(fighter.name, "")
            if not expected:
                expected = COMBAT_SPORT_REAL_DIVISIONS.get(native_sport, {}).get(fighter.name, "")
            ladder_labels = {label for label, _limit in self.combat_sport_weight_ladder(native_sport, fighter.gender)}
            current = getattr(fighter, "sport_weight_class", "")
            if current not in ladder_labels or (expected and current != expected):
                self.assign_combat_sport_weight(native_sport, fighter, expected, reset_walk_weight=True)
            else:
                fighter.weight = self.combat_sport_mma_equivalent(native_sport, current, fighter.gender)
        valid_names = {fighter.name for fighter in roster}
        groups = {}
        for fighter in roster:
            groups.setdefault(self.combat_sport_division_key(fighter, sport), []).append(fighter)
        ranked_groups = {
            key: sorted(
                fighters,
                key=lambda fighter: (self.combat_sport_rating(fighter, sport), fighter.record_w - fighter.record_l, fighter.popularity),
                reverse=True,
            )
            for key, fighters in groups.items()
        }
        state["rankings_by_division"] = {key: [fighter.name for fighter in fighters[:10]] for key, fighters in ranked_groups.items()}
        # Old saves keyed titles by a randomly assigned MMA division.  Move
        # every champion and lineage onto the athlete's corrected sport class.
        roster_by_name = {fighter.name: fighter for fighter in roster}
        migrated_titles = {}
        for old_key, champion in list(state.get("titles", {}).items()):
            champion_fighter = roster_by_name.get(champion)
            key = self.combat_sport_division_key(champion_fighter, sport) if champion_fighter else old_key
            if key in groups and (champion or key not in migrated_titles):
                migrated_titles.setdefault(key, champion)
        state["titles"] = migrated_titles
        migrated_history = {}
        for old_key, entries in list(state.get("title_history", {}).items()):
            sample_name = next((entry.get("winner") or entry.get("previous_champion") or entry.get("loser") for entry in entries if isinstance(entry, dict)), "")
            sample = roster_by_name.get(sample_name)
            key = self.combat_sport_division_key(sample, sport) if sample else old_key
            if key in groups:
                migrated_history.setdefault(key, []).extend(entries)
        state["title_history"] = migrated_history
        # Retirements, crossovers and signings vacate belts rather than silently
        # transferring them to the next athlete in a table.
        for key, champion in list(state["titles"].items()):
            if champion not in valid_names or champion not in state["rankings_by_division"].get(key, []):
                state["titles"][key] = ""
        if not state.get("titles_initialized"):
            legacy_champion = state.get("champion", "")
            legacy_fighter = next((fighter for fighter in roster if fighter.name == legacy_champion), None)
            if legacy_fighter:
                state["titles"][self.combat_sport_division_key(legacy_fighter, sport)] = legacy_fighter.name
            # A fresh AI universe begins with established divisional champions;
            # player child divisions crown theirs through booked title bouts.
            if not player_owned:
                for key, fighters in ranked_groups.items():
                    if len(fighters) >= 2:
                        state["titles"].setdefault(key, fighters[0].name)
            state["titles_initialized"] = True
        champions = [name for name in state["titles"].values() if name]
        state["champion"] = champions[0] if champions else ""
        for fighter in roster:
            fighter.champion = fighter.name in champions
        return state

    def combat_sport_record_book(self, sport, world, employer=None, player_owned=False):
        state = self.ensure_combat_sport_circuit_state(sport, world, employer, player_owned)
        roster = self.combat_sport_roster(sport, employer)
        if not roster:
            state["record_book"] = {}
            return state["record_book"]
        eligible_pct = [fighter for fighter in roster if fighter.record_w + fighter.record_l + fighter.record_d >= 5]
        title_counts = {}
        for history in state.get("title_history", {}).values():
            for entry in history:
                winner = entry.get("winner", "")
                title_counts[winner] = title_counts.get(winner, 0) + 1
        finish_methods = ("KO", "KO/TKO", "TKO", "Submission", "Technical Fall", "Pin")
        finish_counts = {}
        for fighter in roster:
            finish_counts[fighter.name] = sum(1 for line in fighter.fight_history if sport in line and any(f"by {method}" in line for method in finish_methods))
        most_wins = max(roster, key=lambda fighter: fighter.record_w)
        best_pct = max(eligible_pct, key=lambda fighter: fighter.record_w / max(1, fighter.record_w + fighter.record_l + fighter.record_d)) if eligible_pct else most_wins
        most_titles = max(title_counts, key=title_counts.get) if title_counts else "No title history yet"
        most_finishes = max(finish_counts, key=finish_counts.get) if finish_counts else most_wins.name
        state["record_book"] = {
            "Most wins": f"{most_wins.name} ({most_wins.record_w})",
            "Best win rate (5+ bouts)": f"{best_pct.name} ({best_pct.record_w / max(1, best_pct.record_w + best_pct.record_l + best_pct.record_d):.1%})",
            "Most championship wins": f"{most_titles} ({title_counts.get(most_titles, 0)})",
            "Most recorded finishes": f"{most_finishes} ({finish_counts.get(most_finishes, 0)})",
            "Oldest active athlete": f"{max(roster, key=lambda fighter: fighter.age).name} ({max(fighter.age for fighter in roster)})",
        }
        return state["record_book"]

    def refresh_combat_sport_rankings(self, sport, world, employer=None, division=None):
        ranked = self.combat_sport_ranked(sport, employer)
        names = [fighter.name for fighter in ranked[:15]]
        if division is not None:
            division["rankings"] = names[:10]
            self.ensure_combat_sport_circuit_state(sport, world, employer, player_owned=True)
        else:
            if not employer or employer == world.get("promotion", employer):
                world["rankings"] = names
            self.ensure_combat_sport_circuit_state(sport, world, employer, player_owned=False)
        return ranked

    def combat_sport_inactivity_months(self, fighter):
        return max(0, self.month - getattr(fighter, "last_fight_month", 0))

    def combat_sport_card_strategy(self, sport, world, employer, player_owned=False):
        if player_owned:
            return getattr(self, "player_combat_divisions", {}).get(sport, {}).get("strategy", "Balanced")
        world.setdefault("strategy", random.choice(["Champion Showcase", "Prospect Rotation", "Deep Roster", "Merit Ladder"]))
        roster = self.combat_sport_roster(sport, employer)
        inactive = sum(1 for fighter in roster if self.combat_sport_inactivity_months(fighter) >= 5)
        if inactive >= max(8, len(roster) // 4):
            world["strategy"] = "Deep Roster"
        elif any(world.get("titles", {}).values()) and random.random() < 0.18:
            world["strategy"] = "Champion Showcase"
        return world["strategy"]

    def combat_sport_method(self, sport, winner, loser, rating_gap):
        finish_pressure = max(0, rating_gap) / 46 + max(0, winner.finishing_instinct - loser.toughness) / 120
        if sport == "Boxing":
            return "KO" if random.random() < 0.18 + finish_pressure else "Decision"
        if sport in ("Kickboxing", "Muay Thai"):
            return "KO/TKO" if random.random() < 0.22 + finish_pressure else "Decision"
        if getattr(winner, "primary_discipline", "") == "Lethwei":
            return "KO" if random.random() < 0.32 + finish_pressure else "Draw" if random.random() < 0.18 else "Decision"
        if sport == "Wrestling":
            return random.choices(["Points", "Technical Fall", "Pin"], weights=[58, 24, 18], k=1)[0]
        if sport == "Brazilian Jiu-Jitsu":
            return "Submission" if random.random() < 0.38 + max(0, winner.submissions - loser.submission_defence) / 140 else "Points"
        return "Decision"

    def combat_sport_skill_set(self, sport, fighter):
        """Sport-specific skill lens used by non-MMA combat cards.

        This deliberately shares fighter attributes with MMA, but each sport
        weights them differently so a world-class wrestler, boxer, or grappler
        does not feel like a generic overall roll.
        """
        ds = self.ds
        if sport == "Boxing":
            attack = ds(fighter, "punch_technique", fighter.striking) * 0.34 + ds(fighter, "hand_speed", fighter.striking) * 0.22 + ds(fighter, "footwork", fighter.striking) * 0.14 + fighter.power * 0.20 + fighter.fight_iq * 0.10
            defense = ds(fighter, "head_movement", fighter.striking) * 0.26 + ds(fighter, "guard_defence", fighter.striking) * 0.24 + ds(fighter, "footwork", fighter.striking) * 0.18 + fighter.chin * 0.18 + fighter.fight_iq * 0.14
            finishing = fighter.power * 0.42 + ds(fighter, "punch_power", fighter.power) * 0.32 + fighter.finishing_instinct * 0.20 + ds(fighter, "killer_instinct", fighter.finishing_instinct) * 0.06
            return attack, defense, finishing
        if sport in ("Kickboxing", "Muay Thai"):
            clinch_bonus = 0.16 if sport == "Muay Thai" or getattr(fighter, "primary_discipline", "") == "Lethwei" else 0.05
            attack = ds(fighter, "punch_technique", fighter.striking) * 0.18 + ds(fighter, "high_kick_technique", fighter.striking) * 0.12 + ds(fighter, "low_kick_technique", fighter.striking) * 0.15 + ds(fighter, "high_kick_speed", fighter.striking) * 0.10 + ds(fighter, "knees", fighter.striking) * clinch_bonus + fighter.power * 0.20 + fighter.fight_iq * 0.10
            defense = ds(fighter, "guard_defence", fighter.striking) * 0.18 + ds(fighter, "kick_defence", fighter.striking) * 0.22 + ds(fighter, "footwork", fighter.striking) * 0.16 + fighter.chin * 0.18 + fighter.toughness * 0.14 + fighter.fight_iq * 0.12
            finishing = fighter.power * 0.34 + ds(fighter, "high_kick_power", fighter.power) * 0.14 + ds(fighter, "low_kick_power", fighter.power) * 0.10 + ds(fighter, "knees", fighter.striking) * 0.14 + fighter.finishing_instinct * 0.20 + fighter.toughness * 0.08
            return attack, defense, finishing
        if sport == "Wrestling":
            attack = ds(fighter, "takedowns", fighter.wrestling) * 0.30 + ds(fighter, "takedown_setup", fighter.wrestling) * 0.18 + ds(fighter, "chain_wrestling", fighter.wrestling) * 0.22 + ds(fighter, "ride_control", fighter.ground_control) * 0.14 + fighter.cardio * 0.10 + fighter.fight_iq * 0.06
            defense = ds(fighter, "sprawl", fighter.wrestling) * 0.24 + ds(fighter, "takedown_defence_detail", fighter.takedown_defence) * 0.22 + ds(fighter, "get_ups", fighter.wrestling) * 0.16 + ds(fighter, "mobility", fighter.wrestling) * 0.12 + fighter.cardio * 0.14 + fighter.toughness * 0.12
            finishing = ds(fighter, "slams", fighter.wrestling) * 0.16 + ds(fighter, "ride_control", fighter.ground_control) * 0.24 + ds(fighter, "top_control", fighter.ground_control) * 0.22 + ds(fighter, "strength", fighter.wrestling) * 0.18 + fighter.fight_iq * 0.20
            return attack, defense, finishing
        if sport == "Brazilian Jiu-Jitsu":
            attack = ds(fighter, "transitions", fighter.grappling) * 0.20 + ds(fighter, "guard_work", fighter.grappling) * 0.18 + ds(fighter, "positional_ability", fighter.grappling) * 0.18 + fighter.submissions * 0.24 + fighter.fight_iq * 0.12 + fighter.cardio * 0.08
            defense = ds(fighter, "submission_defence_detail", fighter.submission_defence) * 0.26 + ds(fighter, "guard_work", fighter.grappling) * 0.16 + ds(fighter, "scrambles", fighter.grappling) * 0.18 + fighter.ground_control * 0.16 + fighter.cardio * 0.12 + fighter.fight_iq * 0.12
            finishing = fighter.submissions * 0.42 + ds(fighter, "back_control", fighter.grappling) * 0.18 + ds(fighter, "mount_control", fighter.grappling) * 0.14 + ds(fighter, "flexibility", fighter.grappling) * 0.10 + fighter.fight_iq * 0.16
            return attack, defense, finishing
        rating = self.combat_sport_rating(fighter, sport) / 2
        return rating, rating, rating

    def combat_sport_bout_rules(self, sport, title=False, a=None, b=None):
        lethwei = getattr(a, "primary_discipline", "") == "Lethwei" or getattr(b, "primary_discipline", "") == "Lethwei"
        if sport == "Boxing":
            return {"rounds": 10 if title else 6, "finish": "KO/TKO", "decision": "Decision", "draws": True, "fatigue": 3.0, "finish_divisor": 335, "finish_cap": 0.19, "draw_chance": 0.22}
        if sport == "Kickboxing":
            return {"rounds": 5 if title else 3, "finish": "KO/TKO", "decision": "Decision", "draws": True, "fatigue": 4.0, "finish_divisor": 230, "finish_cap": 0.33, "draw_chance": 0.22}
        if sport == "Muay Thai":
            return {"rounds": 5, "finish": "KO" if lethwei else "KO/TKO", "decision": "Decision", "draws": True, "fatigue": 4.2, "finish_divisor": 292 if not lethwei else 260, "finish_cap": 0.31 if not lethwei else 0.36, "draw_chance": 0.08 if not lethwei else 0.48, "lethwei": lethwei}
        if sport == "Wrestling":
            return {"rounds": 3, "finish": "Pin", "decision": "Points", "draws": False, "fatigue": 3.4, "tech_gap": 10}
        if sport == "Brazilian Jiu-Jitsu":
            return {"rounds": 1, "finish": "Submission", "decision": "Points", "draws": False, "fatigue": 3.2}
        return {"rounds": 3, "finish": "Finish", "decision": "Decision", "draws": True, "fatigue": 3.5}

    def combat_sport_commentary_bank(self):
        """Reusable sport-specific phrase library.

        The categories are intentionally generic enough that the MMA engine can
        reuse them later for pure boxing, kickboxing, Thai clinch, wrestling, or
        BJJ moments inside an MMA fight.
        """
        cached = getattr(self, "_combat_sport_commentary_cache", None)
        if cached is not None:
            return cached
        bank = {
            "Boxing": {
                "opening": [
                    "{stakes}: {A} vs {B}. The key battle is jab, counters and pocket discipline.",
                    "{stakes}: {A} meets {B}. Watch the lead hand, the first counter, and who owns the center line.",
                    "{stakes}: {A} and {B} touch gloves. This should be decided by range, timing and body work.",
                    "{stakes}: {A} vs {B}. The corner talk is all about feints, exits and not giving away the pocket.",
                    "{stakes}: {A} faces {B}. The fight starts as a battle for the jab lane.",
                    "{stakes}: {A} and {B} square up. The question is who can draw first and answer last.",
                    "{stakes}: {A} vs {B}. Both teams expect a chess match until someone finds the counter.",
                    "{stakes}: {A} meets {B}. Early footwork will decide who punches downhill.",
                ],
                "close": [
                    "R{round_no}: {A} shades a tight boxing round with the jab and a cleaner final exchange. {score_text}",
                    "R{round_no}: {A} lands the more memorable single shots, but {B} keeps the round uncomfortable. {score_text}",
                    "R{round_no}: {A} steals the optics late, stepping out after a short right hand. {score_text}",
                    "R{round_no}: {A} does just enough with feints and check hooks to edge a cagey round. {score_text}",
                    "R{round_no}: {A} controls the rhythm for small stretches; {B} answers, but not quite enough. {score_text}",
                    "R{round_no}: {A} keeps the lead hand busy and makes {B} reset before the counters arrive. {score_text}",
                    "R{round_no}: A narrow round. {A}'s body jab and late pivot are the clearest scoring moments. {score_text}",
                    "R{round_no}: {A} wins the round on cleaner exits, avoiding the return fire after landing. {score_text}",
                    "R{round_no}: {A} puts a right hand behind the jab twice and that may be enough. {score_text}",
                    "R{round_no}: {A} walks {B} onto the cleaner counters in a low-volume round. {score_text}",
                    "R{round_no}: {A} makes the judges choose accuracy over volume. {score_text}",
                    "R{round_no}: {A} edges the exchanges by punching in twos while {B} mostly lands singles. {score_text}",
                ],
                "dominant": [
                    "R{round_no}: {A} takes over behind a stiff jab, then rips the body when {B} shells up. {score_text}",
                    "R{round_no}: {A} owns the center and keeps {B} turning into the right hand. {score_text}",
                    "R{round_no}: {A} strings together jab, cross, hook and leaves {B} stuck behind the guard. {score_text}",
                    "R{round_no}: {A} hurts {B} with a body-head sequence and controls the rest of the round. {score_text}",
                    "R{round_no}: {A} is reading every entry now, slipping outside and countering clean. {score_text}",
                    "R{round_no}: {A} doubles the jab, splits the guard and backs {B} to the ropes. {score_text}",
                    "R{round_no}: {A} wins the pocket exchanges and makes {B} pay for every reset. {score_text}",
                    "R{round_no}: {A} breaks the rhythm with feints, then lands the heavier combinations. {score_text}",
                    "R{round_no}: {A} turns defence into offence, rolling under and answering upstairs. {score_text}",
                    "R{round_no}: {A} piles up scoring punches while {B} struggles to get their feet set. {score_text}",
                    "R{round_no}: {A} catches {B} between stances and runs away with the round. {score_text}",
                    "R{round_no}: {A} makes it a fundamentals round: jab, angle, counter, repeat. {score_text}",
                ],
                "finish": [
                    "R{round_no}: {A} has read the timing now - a jab freezes {B}, the follow-up lands clean, and the referee waves it off.",
                    "R{round_no}: {A} pours on a measured finishing burst. {B} is defending but not answering enough. {method}.",
                    "R{round_no}: A clean counter changes the fight. {A} stays composed and closes the show with accurate follow-up shots.",
                    "R{round_no}: {A} digs to the body, brings the guard down, then lands the fight-ending shot upstairs.",
                    "R{round_no}: {B} backs straight out and {A} punishes the mistake with a perfect right hand.",
                    "R{round_no}: {A} traps {B} on the ropes and the unanswered combinations force the stoppage.",
                    "R{round_no}: {A} lands the same counter twice; the second one ends the argument.",
                    "R{round_no}: {B}'s legs betray them after a clean hook and {A} swarms with discipline.",
                    "R{round_no}: {A} feints low, fires high, and the referee has no choice but to step in.",
                    "R{round_no}: {A} turns a defensive slip into a finishing counter. {B} cannot recover.",
                ],
                "decision": [
                    "The scorecards reward {A}'s cleaner boxing and round management over {B}. ({score_text})",
                    "{A} takes it on the cards after banking the clearer work in the scoring rounds. ({score_text})",
                    "The judges side with {A}: sharper entries, fewer wasted exchanges, better control of the fight. ({score_text})",
                    "{A}'s jab and exits carry the decision. {B} had moments, but not enough rounds. ({score_text})",
                    "The cards favor {A}'s cleaner counters and steadier ring generalship. ({score_text})",
                    "{A} wins the tactical battle: first touch, last punch, better geography. ({score_text})",
                ],
                "draw": [
                    "The cards cannot split them. The booth points to the swing rounds and the rematch talk starts immediately. ({score_text})",
                    "The judges are divided by the close rounds; this boxing match ends level. ({score_text})",
                    "Neither fighter separates clearly enough on the cards. It is a draw. ({score_text})",
                ],
            },
            "Kickboxing": {
                "opening": [
                    "{stakes}: {A} vs {B}. The key battle is range, low kicks and layered kick-punch exits.",
                    "{stakes}: {A} meets {B}. Watch the lead leg, the body kick and who exits after punching.",
                    "{stakes}: {A} and {B} square off. This starts with stance reads and calf-kick threats.",
                    "{stakes}: {A} vs {B}. The first fighter to blend hands into kicks may control the tempo.",
                    "{stakes}: {A} faces {B}. Range weapons, teeps and counter knees are the story.",
                    "{stakes}: {A} meets {B}. Expect feints upstairs and punishment to the base.",
                    "{stakes}: {A} vs {B}. The corners want clean resets after every combination.",
                    "{stakes}: {A} and {B} touch gloves. The leg-kick battle starts immediately.",
                ],
                "close": [
                    "R{round_no}: {A} edges it with cleaner kick-punch exits. {score_text}",
                    "R{round_no}: {A}'s body kick and final flurry stand out in a close kickboxing round. {score_text}",
                    "R{round_no}: {A} lands the better single shots while {B} answers in spots. {score_text}",
                    "R{round_no}: Neither fighter takes over; {A} shades it on accuracy. {score_text}",
                    "R{round_no}: {A} checks a kick, returns low, and steals a narrow round. {score_text}",
                    "R{round_no}: {A} finishes combinations with kicks while {B} mostly boxes back. {score_text}",
                    "R{round_no}: {A} wins the small moments: a teep, a low kick, a clean exit. {score_text}",
                    "R{round_no}: {A} keeps {B} at the edge of kicking range and nicks the round. {score_text}",
                    "R{round_no}: {A} lands the cleaner counter kick after most punching exchanges. {score_text}",
                    "R{round_no}: {A} scores just enough with low kicks to tilt a tight frame. {score_text}",
                ],
                "dominant": [
                    "R{round_no}: {A} mixes low kicks into the boxing and visibly slows {B}'s stance. {score_text}",
                    "R{round_no}: {A} controls range with teeps and punctuates the round with hard right hands. {score_text}",
                    "R{round_no}: {A} wins the kicking battle, forcing {B} to reset after every exchange. {score_text}",
                    "R{round_no}: {A} batters the lead leg, then goes high when {B} starts bracing. {score_text}",
                    "R{round_no}: {A} turns the round into a range clinic with body kicks and exit hooks. {score_text}",
                    "R{round_no}: {A} catches {B} marching in and keeps meeting them with knees and counters. {score_text}",
                    "R{round_no}: {A} overwhelms {B} with layered attacks: jab, low kick, cross, body kick. {score_text}",
                    "R{round_no}: {B} cannot plant safely; {A} keeps chopping and angling away. {score_text}",
                    "R{round_no}: {A} makes {B} miss at kicking range and answers with the heavier work. {score_text}",
                    "R{round_no}: {A} turns every reset into a scoring opportunity. {score_text}",
                ],
                "finish": [
                    "R{round_no}: {A} chops the base, goes upstairs, and the final combination forces the stoppage.",
                    "R{round_no}: {B} is trapped between the ropes and the low kick. {A} opens up and gets the {method}.",
                    "R{round_no}: A kick-punch sequence lands flush for {A}; the referee has seen enough.",
                    "R{round_no}: {A} hammers the calf, draws the guard down and lands clean upstairs.",
                    "R{round_no}: {A} times the entry with a knee, then follows with hands until the stoppage.",
                    "R{round_no}: {B}'s stance collapses after repeated low kicks and {A} closes the show.",
                    "R{round_no}: {A} hides the high kick behind the cross and finishes with follow-up punches.",
                    "R{round_no}: {A} corners {B}, rips the body, and the unanswered shots bring the referee in.",
                    "R{round_no}: {A} lands a spinning attack that breaks the rhythm and leads straight to the finish.",
                    "R{round_no}: {A} keeps the pressure measured, picking the final shot rather than rushing it.",
                ],
                "decision": [
                    "{A} wins the decision through cleaner kick-punch layers and better range discipline. ({score_text})",
                    "The cards go to {A}; the low kicks and exits told the story. ({score_text})",
                    "{A}'s range control and body kicks carry the decision. ({score_text})",
                    "The judges reward {A}'s more complete kickboxing: hands to set kicks, kicks to reset hands. ({score_text})",
                    "{A} wins on accuracy, stance damage and cleaner exits. ({score_text})",
                    "{A} takes it by controlling the safest kicking lanes. ({score_text})",
                ],
                "draw": [
                    "The judges see the momentum shifts as too close to separate. ({score_text})",
                    "The kickboxing rounds split thinly enough that the cards come back level. ({score_text})",
                    "Neither fighter owns enough clean rounds; this ends as a draw. ({score_text})",
                ],
            },
            "Muay Thai": {
                "opening": [
                    "{stakes}: {A} vs {B}. The key battle is balance, body kicks and clinch scoring{lethwei_note}.",
                    "{stakes}: {A} meets {B}. Watch the checks, the teeps and who controls posture in the clinch{lethwei_note}.",
                    "{stakes}: {A} and {B} take the center. Thai scoring will reward balance, effect and clean body kicks{lethwei_note}.",
                    "{stakes}: {A} vs {B}. The early read is whether elbows or kicks force the first reaction{lethwei_note}.",
                    "{stakes}: {A} faces {B}. The clinch battle may decide the whole fight{lethwei_note}.",
                    "{stakes}: {A} meets {B}. Every checked kick and every off-balancing knee matters{lethwei_note}.",
                    "{stakes}: {A} vs {B}. Expect body kicks, long guard frames and sudden elbows{lethwei_note}.",
                    "{stakes}: {A} and {B} touch gloves. This one starts with balance and ends in the clinch{lethwei_note}.",
                ],
                "close": [
                    "R{round_no}: Tight Thai round; both score, but {A}'s body kick is the clearest moment. {score_text}",
                    "R{round_no}: A measured round with checks, feints and clinch pummeling. {A} just shades it. {score_text}",
                    "R{round_no}: {A} edges the Muay Thai scoring with balance, kicks, and clinch control. {score_text}",
                    "R{round_no}: {A} lands the cleaner knees inside and exits before {B} can answer. {score_text}",
                    "R{round_no}: {A} keeps posture in the clinch and scores the cleaner knees. {score_text}",
                    "R{round_no}: {A}'s teep disrupts the rhythm just enough to win a close round. {score_text}",
                    "R{round_no}: {A} checks well, returns to the body, and steals the optics. {score_text}",
                    "R{round_no}: {A} lands one heavy kick across the ribs that may swing the frame. {score_text}",
                    "R{round_no}: {A} balances better after contact and that matters on the Thai cards. {score_text}",
                    "R{round_no}: {A} wins a narrow round by turning {B} in the clinch. {score_text}",
                ],
                "dominant": [
                    "R{round_no}: {A} takes command in the clinch, landing knees and turning {B} into the ropes. {score_text}",
                    "R{round_no}: {A} scores with heavy body kicks and checks the returns. {score_text}",
                    "R{round_no}: {A} breaks posture with elbows and knees, making the round feel one-way. {score_text}",
                    "R{round_no}: {A} dumps {B} from the clinch and follows with a heavy kick on the reset. {score_text}",
                    "R{round_no}: {A} repeatedly wins inside position and drives knees through the middle. {score_text}",
                    "R{round_no}: {A} uses the long guard to frame, elbow and exit before {B} can settle. {score_text}",
                    "R{round_no}: {A} dominates the scoring weapons: kick, knee, turn, kick again. {score_text}",
                    "R{round_no}: {B} is losing balance after nearly every exchange; {A} is in control. {score_text}",
                    "R{round_no}: {A}'s body kicks are moving {B} across the ring. {score_text}",
                    "R{round_no}: {A} makes the clinch a trap and wins the round clearly. {score_text}",
                ],
                "finish": [
                    "R{round_no}: {A} breaks posture in the clinch and piles on knees until the stoppage comes.",
                    "R{round_no}: Heavy body kicks set the trap, then {A} crashes in with fight-ending knees and elbows.",
                    "R{round_no}: {B} cannot get out of the clinch storm. {A} forces the {method}.",
                    "R{round_no}: {A} folds {B} with a body kick and follows with the finishing barrage.",
                    "R{round_no}: {A} cuts the angle, lands the elbow, and {B} never truly recovers.",
                    "R{round_no}: {A} times the knee as {B} steps in and the fight turns instantly.",
                    "R{round_no}: {A} off-balances {B}, then lands clean before the guard returns.",
                    "R{round_no}: {B} is trapped on the ropes eating knees; the referee steps in.",
                    "R{round_no}: {A}'s small gloves find the gap in the long guard and the finish follows.",
                    "R{round_no}: {A} lands the kind of elbow that changes the whole room's sound.",
                ],
                "decision": [
                    "{A} gets the nod on Thai scoring: balance, body kicks and clinch control carried the fight. ({score_text})",
                    "The judges reward {A}'s stronger scoring weapons in the championship rounds. ({score_text})",
                    "{A} wins through cleaner body kicks, better posture and stronger clinch turns. ({score_text})",
                    "Thai scoring favors {A}: more effect, cleaner balance, better late-round authority. ({score_text})",
                    "{A} takes it by making the meaningful scoring moments clearer. ({score_text})",
                    "{A}'s knees and kicks did more visible damage across the fight. ({score_text})",
                ],
                "draw": [
                    "The scoring moments balance out; neither fighter gets enough separation on the cards. ({score_text})",
                    "The Thai rounds are too tight to split cleanly. This one is ruled a draw. ({score_text})",
                    "Both fighters had scoring weapons, but neither owned the fight. Draw. ({score_text})",
                ],
            },
            "Wrestling": {
                "opening": [
                    "{stakes}: {A} vs {B}. The key battle is hand-fighting, chain attacks and ride control.",
                    "{stakes}: {A} meets {B}. First contact will tell us who owns inside ties.",
                    "{stakes}: {A} and {B} step in low. Watch the first re-shot and the mat returns.",
                    "{stakes}: {A} vs {B}. This could swing on underhooks, head position and edge control.",
                    "{stakes}: {A} faces {B}. Whoever wins the hand fight probably wins the periods.",
                    "{stakes}: {A} meets {B}. The danger is not the first shot; it is the second and third.",
                    "{stakes}: {A} vs {B}. Ride time and exposure threats matter as much as takedowns.",
                    "{stakes}: {A} and {B} start low, forehead pressure already building.",
                ],
                "close": [
                    "R{round_no}: {points_text} - {A} wins the hand-fight and converts the key scramble.",
                    "R{round_no}: {points_text} - {A} scores off the re-attack after {B}'s first shot stalls.",
                    "R{round_no}: {points_text} - {A} controls the tie long enough to edge the period.",
                    "R{round_no}: {points_text} - {A} gets the important go-behind in a cagey period.",
                    "R{round_no}: {points_text} - {A} finishes one clean attack and defends the rest.",
                    "R{round_no}: {points_text} - {A} wins the edge exchanges and denies the late answer.",
                    "R{round_no}: {points_text} - {A} uses head position to make the decisive attack.",
                    "R{round_no}: {points_text} - {A} scrambles through danger and comes out with the points.",
                    "R{round_no}: {points_text} - {A} turns defence into a short score at the boundary.",
                    "R{round_no}: {points_text} - {A} rides just long enough to separate the period.",
                ],
                "dominant": [
                    "R{round_no}: {points_text} - {A} chains attempts, finishes cleanly, and rides out the period on top.",
                    "R{round_no}: {points_text} - {A} breaks {B}'s stance with snaps and scores repeatedly.",
                    "R{round_no}: {points_text} - {A} controls wrists, hips and tempo for a one-way period.",
                    "R{round_no}: {points_text} - {A} gets to the legs whenever the opening is there and keeps returning {B}.",
                    "R{round_no}: {points_text} - {A} stacks attacks until {B}'s defence finally opens.",
                    "R{round_no}: {points_text} - {A} dominates the mat with turns, rides and pressure.",
                    "R{round_no}: {points_text} - {B} cannot clear the ties and {A} keeps scoring.",
                    "R{round_no}: {points_text} - {A} wins the period with chain wrestling and heavy hips.",
                    "R{round_no}: {points_text} - {A} turns every scramble into their own points.",
                    "R{round_no}: {points_text} - {A} runs the score up with relentless second efforts.",
                ],
                "finish": [
                    "R{round_no}: {A} catches the turn, settles chest pressure and secures the {method}.",
                    "R{round_no}: {A} converts the scramble into full control. The official calls it: {method}.",
                    "R{round_no}: {A} stacks the hips, kills the bridge and finishes the {method}.",
                    "R{round_no}: {A} chains one attack into another until the technical fall is inevitable.",
                    "R{round_no}: {A} exposes {B} again and the scoreboard ends it.",
                    "R{round_no}: {A} rides heavy, traps the shoulders and gets the pin.",
                    "R{round_no}: {A} turns a single-leg scramble into full control and the finish.",
                    "R{round_no}: {A} keeps building points until the official steps between them.",
                    "R{round_no}: {B} cannot escape the ride and {A} completes the finish.",
                    "R{round_no}: {A} wins the scramble, the position and finally the match.",
                ],
                "decision": [
                    "{A} wins on the mat through activity, chain attacks and control. ({score_text})",
                    "The final whistle confirms {A}'s edge in takedowns and ride time. ({score_text})",
                    "{A} takes it through cleaner attacks, heavier hips and better period management. ({score_text})",
                    "{A}'s hand-fighting and mat returns decide the match. ({score_text})",
                    "{A} wins because the second and third attacks kept coming. ({score_text})",
                    "{A} controls enough ties and scrambles to earn the points win. ({score_text})",
                ],
                "criteria": [
                    "Referee criteria goes to {A}: better initiative, cleaner attacks and stronger control positions. ({score_text})",
                    "{A} gets the criteria nod after creating the more meaningful attacks in a tied match. ({score_text})",
                    "The official criteria favors {A}'s hand-fighting, pressure and late activity. ({score_text})",
                    "{A} wins the criteria call by forcing more defensive reactions from {B}. ({score_text})",
                ],
                "draw": [],
            },
            "Brazilian Jiu-Jitsu": {
                "opening": [
                    "{stakes}: {A} vs {B}. The key battle is guard battles, positional pressure and submission threats.",
                    "{stakes}: {A} meets {B}. Watch the grips, the first guard choice and who concedes top position.",
                    "{stakes}: {A} and {B} begin hand-fighting. The first pass attempt may reveal everything.",
                    "{stakes}: {A} vs {B}. The danger is positional: pass, back take, submission chain.",
                    "{stakes}: {A} faces {B}. This could be decided by advantage threats as much as points.",
                    "{stakes}: {A} meets {B}. Expect patient grips until one scramble opens the match.",
                    "{stakes}: {A} vs {B}. Guard retention and back exposure are the key tells.",
                    "{stakes}: {A} and {B} start measured, both hunting the first meaningful grip.",
                    "{stakes}: {A} vs {B}. Watch whether the first takedown becomes passing pressure or an active guard.",
                    "{stakes}: {A} meets {B}. The hand fight will decide who builds the first real positional chain.",
                    "{stakes}: {A} and {B} square up. Neither wants to concede the underhook or the first hip angle.",
                    "{stakes}: {A} vs {B}. One clean sweep could change the score and expose the back immediately.",
                    "{stakes}: {A} faces {B}. The key is not reaching position; it is holding it long enough to score.",
                    "{stakes}: {A} meets {B}. Expect guard retention to be tested against sustained passing pressure.",
                    "{stakes}: {A} vs {B}. Submission threats may create the positional points rather than end the match.",
                    "{stakes}: {A} and {B} begin cautiously, each hiding their preferred guard and passing direction.",
                ],
                "close": [
                    "Match: {points_text} - {A} wins the positional battle through sweeps, pressure and advantage threats.",
                    "Match: {points_text} - {A} creates the better submission reactions in a tight grappling exchange.",
                    "Match: {points_text} - {A} keeps the grips they want and edges the positional flow.",
                    "Match: {points_text} - {A} threatens the pass just enough to tilt the match.",
                    "Match: {points_text} - {A} uses a sweep threat to force the key scoring moment.",
                    "Match: {points_text} - {A} wins the scramble by coming up to top position.",
                    "Match: {points_text} - {A} keeps {B} defending the neck while chasing points.",
                    "Match: {points_text} - {A} pressures through half guard and makes {B} react first.",
                    "Match: {points_text} - {A} uses grip fighting to keep the match on their terms.",
                    "Match: {points_text} - {A} edges a technical exchange with better positional intent.",
                ],
                "dominant": [
                    "Match: {points_text} - {A} passes, settles position, and forces repeated submission reactions.",
                    "Match: {points_text} - {A} smashes through guard and makes {B} defend layer after layer.",
                    "Match: {points_text} - {A} controls the hips, clears the frames and dominates from top.",
                    "Match: {points_text} - {A} turns a sweep into pressure and never lets {B} rebuild guard.",
                    "Match: {points_text} - {A} keeps advancing: pass threat, mount threat, back threat.",
                    "Match: {points_text} - {A} pins the shoulders and opens submission routes repeatedly.",
                    "Match: {points_text} - {A} breaks the guard structure and stacks pressure from every angle.",
                    "Match: {points_text} - {A} turns grip dominance into positional dominance.",
                    "Match: {points_text} - {A} forces {B} to defend instead of attack for almost the whole match.",
                    "Match: {points_text} - {A} is ahead in every phase: grips, passing and submission danger.",
                ],
                "finish": [
                    "Match: {A} links the pass to back control and tightens the submission before {B} can peel the grip.",
                    "Match: {A} forces the defensive reaction, switches grips, and gets the tap.",
                    "Match: {A} stays patient through the scramble and finishes the submission chain.",
                    "Match: {A} traps the far arm, climbs to a stronger angle and finishes before {B} can turn.",
                    "Match: {A} uses the pass threat to expose the neck and locks the submission.",
                    "Match: {A} catches {B} during the guard recovery and the tap comes quickly.",
                    "Match: {A} chains from sweep to back take to submission in one clean sequence.",
                    "Match: {A} isolates the limb, adjusts the hips and forces the tap.",
                    "Match: {A} stays calm through the roll and tightens the choke on the far side.",
                    "Match: {A} converts pressure into panic and panic into a submission.",
                ],
                "decision": [
                    "{A} takes the grappling match through positional pressure and higher-value threats. ({score_text})",
                    "The result goes to {A}; the passes, sweeps and submission danger mattered most. ({score_text})",
                    "{A} wins because the match spent longer in their preferred positions. ({score_text})",
                    "{A}'s passing pressure and submission threats carry the points result. ({score_text})",
                    "{A} controlled the grip sequences and won the important scrambles. ({score_text})",
                    "{A} earns it through positional intent and cleaner scoring moments. ({score_text})",
                ],
                "criteria": [
                    "Referee criteria decides it for {A}: more initiative, stronger positional intent, and the better late threats. ({score_text})",
                    "{A} gets the criteria nod after creating the more credible submission danger in a dead-even score. ({score_text})",
                    "The criteria call goes to {A}, who pushed the action and forced the more urgent defence. ({score_text})",
                    "{A} wins the criteria debate by attacking first and making {B} respond. ({score_text})",
                ],
                "draw": [],
            },
        }
        self.expand_combat_sport_commentary_bank(bank)
        self._combat_sport_commentary_cache = bank
        return bank

    def expand_combat_sport_commentary_bank(self, bank):
        """Add generated sport-native templates without making the file unreadable.

        These templates are still sport-specific; generation just combines
        authentic tactical nouns with authentic scoring/finish consequences.
        That gives each sport hundreds of usable lines while keeping one source
        of truth that MMA can also reuse.
        """
        generators = {
            "Boxing": {
                "close_tools": ["the double jab", "the body jab", "a check hook", "a short right hand", "a slip-counter", "a late one-two", "a shoulder roll counter", "a pivot off the ropes"],
                "dominant_tools": ["body-head combinations", "a punishing jab", "rope-side pressure", "counter right hands", "uppercuts through the guard", "angle changes", "inside hooks", "lead-hand control"],
                "finish_tools": ["a counter right hand", "a body shot that drops the elbow", "a left hook on the exit", "a jab-cross through the guard", "an uppercut in the pocket", "a rope-trap combination"],
                "scoring": ["cleaner punching", "ring generalship", "body work", "counter timing", "defensive responsibility", "late-round accuracy"],
                "dominant_results": ["sustained pressure", "body work", "clean counters"],
            },
            "Kickboxing": {
                "close_tools": ["a checked kick and return", "a calf kick", "a body kick", "a teep to reset range", "a kick-punch exit", "a counter knee", "a low kick after the jab", "a right hand into a left kick"],
                "dominant_tools": ["low-kick damage", "body kicks", "teeps and exits", "kick-punch layers", "stance switches", "counter knees", "high-kick feints", "pressure against the ropes"],
                "finish_tools": ["a low kick that buckles the stance", "a head kick hidden behind the cross", "a knee on entry", "a body kick that freezes the guard", "a spinning kick", "a kick-punch flurry"],
                "scoring": ["range control", "leg damage", "body-kick effect", "clean exits", "kick volume", "counter accuracy"],
                "dominant_results": ["range control", "leg damage", "body-kick effect"],
            },
            "Muay Thai": {
                "close_tools": ["a body kick", "a clinch turn", "a knee inside", "a checked kick and return", "a long-guard elbow", "a teep to the hip", "a dump from the clinch", "a late scoring kick"],
                "dominant_tools": ["clinch knees", "body kicks", "elbows through the guard", "off-balancing turns", "long-guard pressure", "rib-cracking kicks", "sweeps and dumps", "posture-breaking knees"],
                "finish_tools": ["a small-glove counter", "a slicing elbow", "a knee up the middle", "a body kick that folds the stance", "a clinch storm", "a rope-side elbow exchange"],
                "scoring": ["balance", "visible effect", "body-kick impact", "clinch control", "posture breaks", "late-round authority"],
                "dominant_results": ["balance", "visible effect", "clinch control"],
            },
            "Wrestling": {
                "close_tools": ["inside ties", "a re-shot", "edge control", "a go-behind", "a short ride", "head position", "wrist control", "a late mat return"],
                "dominant_tools": ["chain attacks", "heavy rides", "exposure turns", "snap-down pressure", "leg attacks", "mat returns", "wrist rides", "relentless second efforts"],
                "finish_tools": ["a trapped turn", "a stack and pin", "repeated exposure", "a technical-fall sequence", "a scramble to chest pressure", "a ride that kills the bridge"],
                "scoring": ["takedowns", "ride time", "exposure threats", "hand-fighting", "mat returns", "scramble control"],
                "dominant_results": ["takedowns", "exposure threats", "ride control"],
            },
            "Brazilian Jiu-Jitsu": {
                "close_tools": ["grip fighting", "a sweep threat", "a knee-cut attempt", "a guard recovery", "a back-take threat", "an advantage attack", "half-guard pressure", "a collar grip"],
                "dominant_tools": ["passing pressure", "back exposure", "mount pressure", "guard-smashing", "submission chains", "hip control", "grip dominance", "positional pressure"],
                "finish_tools": ["a back-take to choke", "an arm isolation", "a leg entanglement", "a pass-to-mount chain", "a neck attack during the scramble", "a sweep into submission control"],
                "scoring": ["passes", "sweeps", "submission danger", "positional intent", "grip control", "advantage threats"],
                "dominant_results": ["submission danger", "positional control", "back exposure"],
            },
        }
        for sport, data in generators.items():
            close_frames = [
                "R{round_no}: {A} edges the frame with {tool} and {score}. {score_text}",
                "R{round_no}: Very little separates them, but {tool} gives {A} the cleaner {score}. {score_text}",
                "R{round_no}: {B} has moments, yet {A}'s {tool} is the clearest example of {score}. {score_text}",
                "R{round_no}: The margins are thin; {A} steals it late through {tool} and {score}. {score_text}",
            ]
            close_templates = [
                frame.format(tool=tool, score=score, A="{A}", B="{B}", round_no="{round_no}", score_text="{score_text}")
                for frame in close_frames for tool in data["close_tools"] for score in data["scoring"][:3]
            ]
            if sport == "Wrestling":
                close_templates = [
                    "R{round_no}: {points_text} - {A} edges the period with " + tool + " and " + score + "."
                    for tool in data["close_tools"] for score in data["scoring"][:3]
                ]
            elif sport == "Brazilian Jiu-Jitsu":
                bjj_close_frames = [
                    "Match: {points_text} - {A} edges the exchange with {tool} and {score}.",
                    "Match: {points_text} - A narrow positional phase; {A}'s {tool} creates the better {score}.",
                    "Match: {points_text} - {B} defends well, but {A} turns {tool} into the clearest {score}.",
                    "Match: {points_text} - The grips are finely balanced until {A} finds {tool} and meaningful {score}.",
                ]
                close_templates = [
                    frame.format(tool=tool, score=score, A="{A}", B="{B}", points_text="{points_text}")
                    for frame in bjj_close_frames for tool in data["close_tools"] for score in data["scoring"][:3]
                ]
            dominant_frames = [
                "R{round_no}: {A} takes over through {tool}, forcing {B} to deal with {score}. {score_text}",
                "R{round_no}: This is becoming one-way: {A}'s {tool} keeps turning into {score}. {score_text}",
                "R{round_no}: {B} cannot find a safe reset while {A} builds everything from {tool} and {score}. {score_text}",
                "R{round_no}: A commanding frame for {A}, whose {tool} creates sustained {score}. {score_text}",
            ]
            dominant_templates = [
                frame.format(tool=tool, score=score, A="{A}", B="{B}", round_no="{round_no}", score_text="{score_text}")
                for frame in dominant_frames for tool in data["dominant_tools"] for score in data.get("dominant_results", data["scoring"][:3])
            ]
            if sport == "Wrestling":
                dominant_templates = [
                    "R{round_no}: {points_text} - {A} takes over with " + tool + ", turning it into " + score + "."
                    for tool in data["dominant_tools"] for score in data.get("dominant_results", data["scoring"][:3])
                ]
            elif sport == "Brazilian Jiu-Jitsu":
                bjj_dominant_frames = [
                    "Match: {points_text} - {A} takes over with {tool}, turning it into {score}.",
                    "Match: {points_text} - {B} is stuck defending layers as {A}'s {tool} builds sustained {score}.",
                    "Match: {points_text} - A commanding phase for {A}: {tool}, positional consolidation, then {score}.",
                    "Match: {points_text} - {A} denies every reset and uses {tool} to maintain {score}.",
                ]
                dominant_templates = [
                    frame.format(tool=tool, score=score, A="{A}", B="{B}", points_text="{points_text}")
                    for frame in bjj_dominant_frames for tool in data["dominant_tools"] for score in data.get("dominant_results", data["scoring"][:3])
                ]
            finish_frames = [
                "R{round_no}: {A} finds {tool}; {B} cannot recover and the result is {method}.",
                "R{round_no}: The opening appears for {tool}. {A} commits and forces the {method}.",
                "R{round_no}: {B} is hurt by {tool}; {A} stays composed and closes the show by {method}.",
                "R{round_no}: One decisive sequence—{tool}—ends with {A} winning by {method}.",
            ]
            finish_templates = [
                frame.format(tool=tool, A="{A}", B="{B}", round_no="{round_no}", method="{method}")
                for frame in finish_frames for tool in data["finish_tools"]
            ]
            if sport == "Brazilian Jiu-Jitsu":
                bjj_finish_frames = [
                    "Match: {A} finds {tool}; {B} has to tap.",
                    "Match: {A} uses {tool} to force the defensive turn, follows the reaction and gets the submission.",
                    "Match: The finish grows from {tool}. {A} adjusts the angle until {B} can no longer defend.",
                    "Match: {B} survives the first threat, but {A} reconnects through {tool} and forces the tap.",
                ]
                finish_templates = [
                    frame.format(tool=tool, A="{A}", B="{B}")
                    for frame in bjj_finish_frames for tool in data["finish_tools"]
                ]
            elif sport == "Wrestling":
                finish_templates = ["R{round_no}: {A} finishes through " + tool + ". The official records it as {method}." for tool in data["finish_tools"]]
            bank[sport]["close"].extend(close_templates)
            bank[sport]["dominant"].extend(dominant_templates)
            bank[sport]["finish"].extend(finish_templates)
            decision_frames = [
                "{A} wins because {score} decided the fight. ({score_text})",
                "The cards reward {A}'s {score} across the full contest. ({score_text})",
                "{B} had competitive spells, but {A} owned the more meaningful {score}. ({score_text})",
                "The official decision goes to {A}; the lasting difference was {score}. ({score_text})",
            ]
            bank[sport]["decision"].extend([
                frame.format(score=score, A="{A}", B="{B}", score_text="{score_text}")
                for frame in decision_frames for score in data["scoring"]
            ])

    def combat_sport_phrase(self, sport, category, actor=None, opponent=None, **context):
        bank = self.combat_sport_commentary_bank()
        templates = bank.get(sport, {}).get(category) or bank.get(sport, {}).get("close") or ["{A} has the cleaner moment."]
        actor_name = getattr(actor, "name", actor) or context.get("actor", "The fighter")
        opponent_name = getattr(opponent, "name", opponent) or context.get("opponent", "the opponent")
        values = {
            "A": actor_name,
            "B": opponent_name,
            "round_no": context.get("round_no", ""),
            "score_text": context.get("score_text", ""),
            "points_text": context.get("points_text", ""),
            "method": context.get("method", ""),
            "stakes": context.get("stakes", "Scheduled bout"),
            "lethwei_note": context.get("lethwei_note", ""),
        }
        return random.choice(templates).format(**values)

    def combat_sport_round_commentary(self, sport, round_no, leader, trailer, margin, score_text="", points_text=""):
        """Richer, sport-specific lines for combat-sport cards.

        These are intentionally lighter than the live MMA engine, but they use
        the same idea: the text should explain why the round moved the fight.
        """
        edge = abs(margin)
        category = "dominant" if edge > 24 or (sport in ("Wrestling", "Brazilian Jiu-Jitsu") and margin > 3) else "close"
        return self.combat_sport_phrase(sport, category, leader, trailer, round_no=round_no, score_text=score_text, points_text=points_text)

    def combat_sport_finish_commentary(self, sport, round_no, winner, loser, method):
        return self.combat_sport_phrase(sport, "finish", winner, loser, round_no=round_no, method=method)

    def combat_sport_opening_commentary(self, sport, a, b, title=False):
        stakes = "Title bout" if title else "Scheduled bout"
        lethwei_note = ""
        if sport == "Muay Thai" and (getattr(a, "primary_discipline", "") == "Lethwei" or getattr(b, "primary_discipline", "") == "Lethwei"):
            lethwei_note = " with Lethwei knockout urgency"
        return self.combat_sport_phrase(sport, "opening", a, b, stakes=stakes, lethwei_note=lethwei_note)

    def combat_sport_decision_commentary(self, sport, winner, loser, method, score_text):
        if method == "Draw" or not winner:
            return self.combat_sport_phrase(sport, "draw", winner, loser, score_text=score_text)
        category = "criteria" if sport in ("Brazilian Jiu-Jitsu", "Wrestling") and method == "Referee Criteria" else "decision"
        return self.combat_sport_phrase(sport, category, winner, loser, score_text=score_text, method=method)

    def combat_sport_live_actions(self, sport):
        """Return action definitions used by the detailed non-MMA fight viewer.

        Each action names the detailed skills that create and stop it. This makes
        the commentary a description of the simulation rather than decorative
        text added after a round has already been decided.
        """
        actions = {
            "Boxing": [
                ("jab", "punch_technique", "head_movement", 1.5, 0.7),
                ("double jab", "hand_speed", "guard", 1.8, 0.9),
                ("body shot", "punch_power", "guard", 2.4, 1.7),
                ("right hand", "punch_technique", "head_movement", 2.7, 2.2),
                ("check hook", "counter_striking", "footwork", 2.2, 1.8),
                ("combination", "hand_speed", "guard", 3.3, 2.6),
                ("uppercut", "punch_power", "head_movement", 3.0, 2.8),
                ("rope attack", "killer_instinct", "guard", 3.6, 3.0),
            ],
            "Kickboxing": [
                ("jab-cross", "punch_technique", "head_movement", 2.0, 1.2),
                ("low kick", "low_kick_technique", "kick_defence", 2.6, 1.8),
                ("body kick", "kick_technique", "kick_defence", 3.0, 2.1),
                ("head kick", "kick_speed", "guard", 4.0, 3.5),
                ("counter cross", "counter_striking", "head_movement", 2.4, 2.0),
                ("kick-punch combination", "kick_technique", "footwork", 3.6, 2.7),
                ("spinning attack", "creativity", "footwork", 4.5, 3.8),
                ("clinch knee", "knees", "clinch_control", 3.5, 2.8),
            ],
            "Muay Thai": [
                ("teep", "kick_technique", "balance", 1.8, 0.9),
                ("body kick", "kick_technique", "kick_defence", 3.0, 2.2),
                ("low kick", "low_kick_technique", "kick_defence", 2.7, 1.9),
                ("elbow", "elbows", "guard", 3.1, 3.2),
                ("straight knee", "knees", "clinch_control", 3.3, 2.8),
                ("clinch turn", "clinch_control", "balance", 3.5, 1.5),
                ("dump", "trips", "balance", 3.8, 2.0),
                ("high kick", "kick_power", "guard", 4.2, 3.8),
            ],
            "Wrestling": [
                ("single leg", "takedowns", "sprawl", 3.0, 1.3),
                ("double leg", "takedown_setup", "takedown_defence_detail", 3.7, 1.7),
                ("re-shot", "chain_wrestling", "balance", 3.8, 1.5),
                ("body lock", "clinch_control", "balance", 3.2, 1.2),
                ("mat return", "slams", "get_ups", 4.0, 2.1),
                ("ride", "ride_control", "scrambles", 2.5, 0.8),
                ("turn", "top_control", "get_ups", 3.6, 1.8),
                ("pinning attack", "ride_control", "toughness", 4.2, 2.2),
            ],
            "Brazilian Jiu-Jitsu": [
                ("grip exchange", "transitions", "composure", 1.2, 0.1),
                ("takedown", "takedowns", "sprawl", 3.2, 0.8),
                ("guard pull", "guard_work", "balance", 1.8, 0.3),
                ("off-balance attempt", "guard_work", "top_control", 1.8, 0.2),
                ("sweep", "transitions", "base", 3.0, 0.8),
                ("guard pass", "positional_ability", "guard_work", 3.2, 0.9),
                ("pressure adjustment", "top_control", "scrambles", 1.7, 0.2),
                ("defensive framing", "guard_work", "top_control", 1.6, 0.1),
                ("guard recovery", "guard_work", "ride_control", 2.8, 0.5),
                ("positional escape", "scrambles", "top_control", 3.0, 0.5),
                ("back take", "back_control", "scrambles", 3.5, 1.0),
                ("mount advance", "mount_control", "get_ups", 3.3, 0.9),
                ("arm attack", "submissions", "submission_defence_detail", 3.6, 1.3),
                ("choke attack", "back_control", "submission_defence_detail", 3.8, 1.4),
                ("leg entanglement", "leg_locks", "submission_defence_detail", 3.9, 1.2),
                ("front headlock", "submission_attack", "submission_defence_detail", 3.5, 1.1),
            ],
        }
        return actions.get(sport, actions["Kickboxing"])

    def combat_sport_striking_situation_bank(self):
        """Build large action-specific broadcast pools for the striking sports.

        The combinations are assembled once and cached.  Each finished line is
        still a coherent sport/action situation, while the simulator continues
        to make exactly the same mechanical action and success decisions.
        """
        cached = getattr(self, "_combat_sport_striking_situation_cache", None)
        if cached is not None:
            return cached
        success_cores = {
            "Boxing": {
                "jab": ["threads a jab between {B}'s gloves", "stabs the lead hand into {B}'s chest", "touches low and snaps the jab upstairs"],
                "double jab": ["steps behind a double jab that moves {B}'s guard", "jabs to the body before doubling upstairs", "uses the second jab to catch {B} on the exit"],
                "body shot": ["digs a left hook underneath {B}'s elbow", "drives a straight shot into {B}'s solar plexus", "shifts close enough to bury a shovel hook in the ribs"],
                "right hand": ["drives the rear hand straight through the centre", "pulls just outside the jab and fires the right hand back", "pins {B}'s lead glove and lands the cross"],
                "check hook": ["takes a half-step back and turns {B} with the check hook", "meets the rush with a compact lead hook", "pivots around {B}'s front foot while landing the hook"],
                "combination": ["layers a body-head combination before changing angle", "puts a straight-hook-straight sequence through the guard", "touches with the jab and finishes the combination downstairs"],
                "uppercut": ["splits {B}'s elbows with a short uppercut", "catches {B} dipping with the rear uppercut", "rolls under the hook and answers up the middle"],
                "rope attack": ["cuts off the rope-side exit and works in combination", "keeps {B} in the corner with hooks to both levels", "steps across the escape route and unloads without smothering the work"],
            },
            "Kickboxing": {
                "jab-cross": ["steps through a sharp jab-cross", "paws with the lead hand before spearing the cross", "changes rhythm and lands both straight punches"],
                "low kick": ["finishes the punches with an outside low kick", "chops the inside thigh as {B} plants", "waits for the weight transfer and kicks through the lead leg"],
                "body kick": ["wraps the rear kick around {B}'s elbow", "switches and drives the shin across the open ribs", "draws the guard high before turning over the body kick"],
                "head kick": ["hides the head kick behind the straight punches", "changes levels with the eyes and whips the kick upstairs", "steps outside the lead foot and sends the shin around the guard"],
                "counter cross": ["checks the kick and shoots the cross down the middle", "leans away from the entry and fires the rear hand back", "catches {B} resetting with a straight counter"],
                "kick-punch combination": ["goes low-high with the kick before punching through the reaction", "kicks the body and follows the retreat with straight punches", "uses the hands to hide a final kick on the exit"],
                "spinning attack": ["turns off the centre line with a spinning back kick", "draws the pressure and whips a spinning strike into the opening", "uses the missed lead hand to disguise the spin"],
                "clinch knee": ["catches the head and drives a knee through the middle", "frames on the collarbone before landing the knee", "meets {B}'s forward step with a compact clinch knee"],
            },
            "Muay Thai": {
                "teep": ["spears the teep into {B}'s body", "lifts the lead leg and pushes {B} off balance", "times the forward step with a stabbing teep to the hip"],
                "body kick": ["turns the shin over across {B}'s ribs", "catches the arm and body together with a heavy round kick", "steps outside and lands the open-side body kick"],
                "low kick": ["chops through {B}'s supporting leg", "waits for the punch and cracks the exposed thigh", "steps deep before driving the shin into the inside leg"],
                "elbow": ["frames across {B}'s guard and slices the elbow through", "steps into the pocket with a horizontal elbow", "turns out of the clinch while landing the elbow on the break"],
                "straight knee": ["wins inside position and drives the knee through the body", "breaks {B}'s posture before lifting the straight knee", "pulls the head into a knee up the centre"],
                "clinch turn": ["swims to inside control and turns {B} sharply", "uses head position to off-balance {B} in the clinch", "pins an arm and rotates {B} into the ropes"],
                "dump": ["catches the kick and runs {B} across the supporting leg", "steps behind the base and dumps {B} from the clinch", "times the turn as {B} knees and sends them to the canvas"],
                "high kick": ["wraps the high kick over {B}'s long guard", "shows the body kick before sending the shin upstairs", "arches the kick around the glove and onto the head"],
            },
        }
        defence_cores = {
            "Boxing": {
                "jab": ["parries the jab outside", "pulls the head beyond the lead hand", "catches the jab on the rear glove"],
                "double jab": ["blocks the first jab and slips the second", "gives ground before either jab can settle", "meets the double jab with a tight high guard"],
                "body shot": ["drops the elbow onto the body shot", "turns the hip away from the hook", "frames off before the punch reaches the ribs"],
                "right hand": ["slips outside the right hand", "rolls the cross across the shoulder", "steps off line and lets the rear hand miss"],
                "check hook": ["stays balanced through the hook and squares up", "keeps the rear glove home to block the counter", "halts the entry before the check hook can turn them"],
                "combination": ["shells through the combination", "uses small slips to take the force off each punch", "ties up before the final shot can land"],
                "uppercut": ["keeps the elbows connected and smothers the uppercut", "leans away before the punch splits the guard", "crowds the shot so it cannot extend"],
                "rope attack": ["slides along the ropes and escapes the corner", "clinches before the rope-side flurry develops", "blocks the first wave and pivots back to open space"],
            },
            "Kickboxing": {
                "jab-cross": ["parries the jab and slips outside the cross", "catches both straight shots on the gloves", "exits before the one-two reaches full range"],
                "low kick": ["turns the shin out and checks the low kick", "withdraws the lead leg before impact", "sits down on the stance and absorbs the kick safely"],
                "body kick": ["braces the forearm and ribs behind a tight block", "slides beyond the arc of the body kick", "catches the kick before it can score cleanly"],
                "head kick": ["sees the high kick and gets both gloves to it", "leans outside the kick's arc", "steps inside before the shin can gather force"],
                "counter cross": ["recovers the guard before the counter arrives", "rolls under the returning cross", "uses the kick to exit beyond the counter"],
                "kick-punch combination": ["blocks low and moves before the punches follow", "breaks the combination with a stiff frame", "changes angle and makes the layered attack fall short"],
                "spinning attack": ["reads the turn and steps safely off line", "crowds the spin before it can extend", "retreats beyond the spinning strike"],
                "clinch knee": ["wins the frame and prevents the knee lane", "turns the hips away from the clinch knee", "pummels inside and forces a clean break"],
            },
            "Muay Thai": {
                "teep": ["scoops the teep aside", "steps off line before the push kick lands", "parries the foot and keeps advancing"],
                "body kick": ["checks the body kick across the forearms", "leans away from the shin", "catches the kick and denies the score"],
                "low kick": ["checks shin against shin", "takes the weight off the targeted leg", "steps inside the low kick before it turns over"],
                "elbow": ["frames across the biceps and stops the elbow", "leans outside the slicing elbow", "ties up the arms before the elbow can clear the guard"],
                "straight knee": ["turns the hips and takes the knee off line", "locks the posture down before the knee rises", "wins inside position and blocks the knee lane"],
                "clinch turn": ["widens the base and refuses the turn", "recovers head position before being off-balanced", "pummels back inside and squares the clinch"],
                "dump": ["hops free and recovers the trapped leg", "posts on the shoulder to stay upright", "reads the reap and keeps the base underneath them"],
                "high kick": ["raises the long guard and blocks the high kick", "leans back beyond the shin", "steps under the kick and forces a clinch"],
            },
        }
        situations = {
            "Boxing": {
                "setups": ["{A} feints low, then", "As {B} steps into range, {A}", "After taking the centre, {A}", "{A} changes rhythm and", "With {B} near the ropes, {A}"],
                "endings": ["The angle takes {A} away from the return.", "{A} resets behind a disciplined guard.", "{B} is left reacting rather than leading.", "{A} slides back to the centre line."],
                "defence_starts": ["{A} shows the lead hand, but {B}", "As {A} commits, {B}", "{B} reads the boxing entry and", "{A} tries to trap the exit; {B}", "The crowd reacts as {A} steps in, but {B}"],
                "defence_endings": ["{B} circles back to centre.", "{B} resets without taking a clean scoring shot.", "A short counter discourages the follow-up.", "{A} has to build the attack again."],
            },
            "Kickboxing": {
                "setups": ["{A} uses a stance feint and", "As {B} plants to answer, {A}", "After touching with the lead hand, {A}", "{A} changes levels and", "With {B} backed toward the ropes, {A}"],
                "endings": ["{A} exits outside the lead leg.", "{A} returns to a balanced kicking stance.", "{B} has to defend hands and feet together.", "{A} takes the centre on the reset."],
                "defence_starts": ["{A} starts the combination, but {B}", "As {A} enters kicking range, {B}", "{B} recognizes the setup and", "{A} tries to layer the attack; {B}", "The exchange opens for {A}, yet {B}"],
                "defence_endings": ["{B} angles safely out of range.", "{B} is ready for the next layer.", "The stance remains intact on the reset.", "There is no clean scoring impact."],
            },
            "Muay Thai": {
                "setups": ["{A} posts with the long guard and", "As {B} steps square, {A}", "After a measured feint, {A}", "{A} claims the centre and", "With the clinch threat drawing the guard, {A}"],
                "endings": ["{A} finishes the exchange in balance.", "{A} reclaims the centre with the long guard.", "The judges get a clear view of the effect.", "{A} resets without giving {B} a free return."],
                "defence_starts": ["{A} looks for the scoring weapon, but {B}", "As {A} closes behind the long guard, {B}", "{B} reads the Thai entry and", "{A} tries to break the posture; {B}", "The opening appears for {A}, yet {B}"],
                "defence_endings": ["{B} takes the centre back.", "{B} remains balanced through the exchange.", "Posture and position win out over chasing a return.", "The action has to start again."],
            },
            "Lethwei": {
                "setups": ["{A} presses forward behind the bare-knuckle guard and", "As {B} braces for the rough entry, {A}", "{A} gives ground for a beat, then", "With knockout urgency building, {A}", "{A} crowds the pocket and"],
                "endings": ["{A} stays close enough to continue the exchange.", "{A} immediately retakes the centre.", "{B} cannot settle into a comfortable Thai rhythm.", "{A} squares up for another bare-knuckle exchange."],
                "defence_starts": ["{A} charges into the exchange, but {B}", "As {A} loads the bare-knuckle attack, {B}", "{B} reads the aggressive entry and", "{A} tries to turn it into a brawl; {B}", "The knockout opening seems available to {A}, yet {B}"],
                "defence_endings": ["{B} returns to the centre.", "The clean knockout impact is denied.", "{B} braces for the next close-range exchange.", "{A} has to reset the attack."],
            },
        }
        bank = {}
        for sport, action_map in success_cores.items():
            sport_bank = {}
            context = situations[sport]
            for action, cores in action_map.items():
                land = [f"{setup} {core}. {ending}" for setup in context["setups"] for core in cores for ending in context["endings"]]
                defended = [f"{start} {core}. {ending}" for start in context["defence_starts"] for core in defence_cores[sport][action] for ending in context["defence_endings"]]
                sport_bank[action] = {"land": land, "defended": defended}
            bank[sport] = sport_bank
        lethwei_bank = {}
        for action, cores in success_cores["Muay Thai"].items():
            context = situations["Lethwei"]
            land = [f"{setup} {core}. {ending}" for setup in context["setups"] for core in cores for ending in context["endings"]]
            defended = [f"{start} {core}. {ending}" for start in context["defence_starts"] for core in defence_cores["Muay Thai"][action] for ending in context["defence_endings"]]
            lethwei_bank[action] = {"land": land, "defended": defended}
        bank["Lethwei"] = lethwei_bank
        self._combat_sport_striking_situation_cache = bank
        return bank

    def combat_sport_bjj_situation_bank(self):
        """Create action-specific BJJ calls for attacks, transitions and defences."""
        cached = getattr(self, "_combat_sport_bjj_situation_cache", None)
        if cached is not None:
            return cached
        success_cores = {
            "grip exchange": ["peels the controlling grip and replaces it with a strong two-on-one", "wins inside wrist position before reconnecting to the hips", "clears the collar-and-elbow control and establishes preferred grips"],
            "takedown": ["changes level and finishes a clean takedown into top position", "wins the hand fight before running the hips to the mat", "connects the upper body and trips {B} into guard"],
            "guard pull": ["secures two useful grips and pulls into an active guard", "sits underneath {B} with immediate off-balancing control", "uses the entry to establish guard without conceding posture"],
            "off-balance attempt": ["loads {B}'s weight over the hands and forces a wide recovery step", "uses the hooks to break {B}'s posture and threaten the base", "changes the angle underneath and makes {B} post to stay on top"],
            "sweep": ["loads {B}'s weight onto the wrong post and comes up on top", "uses the hook and far-side grip to complete the sweep", "redirects the passing pressure and reverses the position"],
            "guard pass": ["clears the knee line and settles chest-to-chest beyond the legs", "wins the inside position before circling into side control", "staples the hips and completes a measured guard pass"],
            "pressure adjustment": ["switches the hip pressure and closes the space around {B}'s frames", "repositions the cross-face and settles the weight before attacking", "walks the knees closer and makes {B} carry the pressure"],
            "defensive framing": ["connects an elbow-to-knee frame and prevents the next advance", "builds a strong inside frame that creates a pocket of breathing room", "keeps the forearms inside and redirects {B}'s chest pressure"],
            "guard recovery": ["creates a frame, hip-escapes and brings both knees back inside", "uses the near-side elbow frame to rebuild guard", "threads a shin back into the space and recovers the defensive structure"],
            "positional escape": ["wins the inside frame and escapes the pinning pressure", "turns onto the side, clears the cross-face and creates separation", "times the weight shift and scrambles out of the bad position"],
            "back take": ["follows the exposed hip and secures both hooks on the back", "uses the scramble to climb behind {B} and establish back control", "wins the seat-belt grip before settling onto the back"],
            "mount advance": ["isolates the near arm and slides the knee through into mount", "walks the trapped leg free and settles into a stable mount", "uses shoulder pressure to climb from side control into mount"],
            "arm attack": ["separates the elbow and extends into a dangerous armbar", "switches from the shoulder lock threat into an armbar angle", "traps the wrist and builds a tight triangle-armbar dilemma"],
            "choke attack": ["wins the head-and-arm position and builds a tight choke threat", "connects the control grips before closing space around the neck", "forces an urgent hand fight as the choke begins to tighten"],
            "leg entanglement": ["controls the knee line and isolates the foot inside the entanglement", "sits beneath the base and connects to the far hip", "uses a controlled entry to expose a clean leg-lock angle"],
            "front headlock": ["snaps the posture and wraps a dangerous front headlock", "uses the sprawl to connect hands beneath the chin", "circles from the head-and-arm control into a guillotine threat"],
        }
        defence_cores = {
            "grip exchange": ["keeps the stronger grip and circles the wrist away from danger", "re-pummels inside before the two-on-one can settle", "breaks the grip sequence and returns both hands to safe position"],
            "takedown": ["sprawls the hips back and squares to the shot", "wins the underhook before the takedown can turn the corner", "posts on the shoulder and remains standing"],
            "guard pull": ["keeps posture, clears the dangerous grips and refuses the preferred guard", "steps around the pulling leg before the guard can settle", "controls the ankles and prevents an immediate attacking structure"],
            "off-balance attempt": ["shifts the base before the hooks can load the hips", "keeps the posture aligned and refuses to post a hand", "floats over the angle change and remains balanced on top"],
            "sweep": ["widens the base and removes the lifting hook", "posts beyond the sweep line and stays on top", "floats with the off-balance attempt before settling the hips again"],
            "guard pass": ["recovers the knee shield before the hips can be pinned", "frames across the shoulder and keeps the legs between them", "wins the near-side underhook and blocks the passing angle"],
            "pressure adjustment": ["keeps the frame in place and prevents the weight from settling", "turns onto the side before the cross-face can control the shoulders", "uses the knee shield to hold the pressure at a safe distance"],
            "defensive framing": ["swims inside the frame and reconnects chest-to-chest", "pins the near elbow before the defensive structure can settle", "changes the angle of pressure and collapses the frame"],
            "guard recovery": ["controls the hips and keeps the knees outside the frame", "switches the cross-face before the guard can rebuild", "follows the hip escape and denies the returning leg"],
            "positional escape": ["adjusts the weight and closes the escape route", "follows the turn with chest pressure and keeps the pin", "controls the far hip before the scramble can develop"],
            "back take": ["keeps the shoulders to the mat and denies the back exposure", "wins the hand fight before either hook can settle", "turns safely into the attack and clears the seat-belt grip"],
            "mount advance": ["blocks the advancing knee and traps a leg in half guard", "frames at the hip and stops the climb into mount", "turns onto the side before the top pressure can settle"],
            "arm attack": ["connects the hands and pulls the elbow back to safety", "stacks the hips before the arm can be extended", "reads the grip switch and clears the threatened limb"],
            "choke attack": ["wins the two-on-one hand fight and protects the neck", "tucks the chin while peeling the control hand", "turns toward the choking side and creates breathing room"],
            "leg entanglement": ["clears the knee line before the foot can be isolated", "turns the toes safely and removes the controlling hook", "keeps the heel hidden while extracting the trapped leg"],
            "front headlock": ["rebuilds posture and hand-fights out of the front headlock", "peels the choking grip before circling free", "keeps the neck safe and drives back to a neutral position"],
        }
        attack_setups = [
            "After winning a grip exchange, {A}",
            "As {B} shifts their base, {A}",
            "{A} chains the previous reaction into the next attack and",
            "With patient hip and head position, {A}",
            "{A} changes direction at exactly the right moment and",
        ]
        attack_reads = [
            "{A} consolidates the position before hunting the next layer.",
            "{B} is forced to defend position before thinking about offence.",
            "The mat-side team marks that as a meaningful attacking sequence.",
            "{A} stays connected and denies an easy reset.",
        ]
        defence_setups = [
            "{A} begins the transition, but {B}",
            "As {A} tries to advance, {B}",
            "{B} recognizes the grip sequence early and",
            "{A} appears to have the angle; {B}",
            "The attack develops for {A}, yet {B}",
        ]
        defence_reads = [
            "The position remains competitive.",
            "{A} has to rebuild the attack from the grips.",
            "{B} earns a valuable defensive reset.",
            "Neither athlete receives a clean positional score from the exchange.",
        ]
        recovery_setups = [
            "Under sustained pressure from {B}, {A}",
            "Before {B} can stabilize the position, {A}",
            "Working patiently from underneath, {A}",
            "As {B} shifts their weight to advance, {A}",
            "With the immediate attack contained, {A}",
        ]
        recovery_reads = [
            "{A} has bought enough room to rebuild safely.",
            "{B} must establish control again before attacking.",
            "That is composed defensive work from a difficult position.",
            "The immediate danger is gone, but the positional battle continues.",
        ]
        recovery_denied_setups = [
            "{A} tries to create an escape, but {B}",
            "As {A} frames to recover, {B}",
            "{A} begins to turn toward safety; {B}",
            "The defensive opening appears for {A}, yet {B}",
            "{A} tries to make space underneath, but {B}",
        ]
        recovery_denied_reads = [
            "{B} keeps the controlling position.",
            "{A} remains pinned beneath disciplined pressure.",
            "The escape route closes before {A} can use it.",
            "{B} denies the reset and stays attached.",
        ]
        bank = {}
        for action, cores in success_cores.items():
            if action in ("guard recovery", "positional escape", "defensive framing"):
                land = [f"{setup} {core}. {read}" for setup in recovery_setups for core in cores for read in recovery_reads]
                defended = [f"{setup} {core}. {read}" for setup in recovery_denied_setups for core in defence_cores[action] for read in recovery_denied_reads]
            else:
                land = [f"{setup} {core}. {read}" for setup in attack_setups for core in cores for read in attack_reads]
                defended = [f"{setup} {core}. {read}" for setup in defence_setups for core in defence_cores[action] for read in defence_reads]
            bank[action] = {"land": land, "defended": defended}
        self._combat_sport_bjj_situation_cache = bank
        return bank

    def combat_sport_live_line(self, sport, action, actor, defender, success, momentum=False):
        """Create one sport-native live call for a simulated exchange."""
        success_lines = {
            "Boxing": {
                "jab": ["{A} spears the jab through the center and steps off before {B} can answer.", "{A} touches the body, brings the jab upstairs and makes {B} reset."],
                "double jab": ["{A} doubles the jab and the second one snaps {B}'s head back.", "Two quick jabs from {A}; {B}'s guard is being moved out of position."],
                "body shot": ["{A} dips outside the lead hand and digs a hook into {B}'s ribs.", "A hard body shot lands for {A}; {B} gives ground and takes a deeper breath."],
                "right hand": ["{A} freezes {B} with the lead hand and drives the right hand down the pipe.", "{A}'s straight right gets there first and forces {B} into a hurried clinch."],
                "check hook": ["{A} gives a half-step, catches {B} with the check hook and pivots away.", "{B} reaches on the entry and {A} makes them pay with a compact counter hook."],
                "combination": ["{A} puts three punches together, finishes to the body and leaves on an angle.", "Sharp combination from {A}: jab, cross, hook before {B} can close the guard."],
                "uppercut": ["{A} splits the guard with an uppercut as {B} leans over the front knee.", "The uppercut lands clean for {A}; {B}'s legs stiffen for a moment."],
                "rope attack": ["{A} traps {B} near the ropes and works head-body-head without smothering the shots.", "{A} cuts off the exit and unloads while {B} shells up on the ropes."],
            },
            "Kickboxing": {
                "jab-cross": ["{A} steps through a crisp jab-cross and exits outside {B}'s lead leg.", "The straight punches land clean for {A} before {B} can set the kick."],
                "low kick": ["{A} punches into a chopping low kick; {B}'s stance jolts on impact.", "A clean outside low kick from {A} reddens {B}'s lead thigh."],
                "body kick": ["{A} whips the shin into {B}'s open side and turns the hip all the way through.", "{A}'s body kick lands flush beneath the elbow; {B} exhales sharply."],
                "head kick": ["{A} hides the high kick behind the hands and clips {B} around the guard.", "The head kick gets through for {A}; {B} stumbles away and regains the stance."],
                "counter cross": ["{A} checks the kick and fires the right hand straight back at {B}.", "{B} is caught admiring the kick as {A}'s counter cross lands clean."],
                "kick-punch combination": ["{A} goes low kick, cross, left hook and keeps {B} defending on two levels.", "{A} layers the attack beautifully, kicking into punches before angling out."],
                "spinning attack": ["{A} reads the pressure and lands a spinning back kick to {B}'s body.", "A spinning strike from {A} finds the target and brings the crowd to its feet."],
                "clinch knee": ["{A} catches the posture and drives a knee through the middle before the break.", "In the brief clinch, {A} lands the clean knee and turns {B} off balance."],
            },
            "Muay Thai": {
                "teep": ["{A} plants a teep in {B}'s chest and takes the center back.", "The lead teep from {A} breaks {B}'s rhythm and sends them back a step."],
                "body kick": ["{A} scores with a heavy body kick, shin slapping across {B}'s ribs.", "A balanced, fully turned-over body kick lands for {A}; the judges see it clearly."],
                "low kick": ["{A} chops the supporting leg as {B} begins to punch.", "{A}'s low kick lands with a thud and makes {B} square the stance."],
                "elbow": ["{A} frames in the pocket and slices an elbow across {B}'s brow.", "A short elbow lands for {A} as {B} tries to close into the clinch."],
                "straight knee": ["{A} wins inside position and drives a straight knee into {B}'s body.", "The clinch tightens and {A} scores with a clean knee up the middle."],
                "clinch turn": ["{A} controls the biceps, turns {B} sharply and finishes the exchange in command.", "Excellent clinch balance from {A}, who off-balances {B} and lands on the turn."],
                "dump": ["{A} times the kick, catches it and dumps {B} hard to the canvas.", "{A} steps across in the clinch and sends {B} down with a clean dump."],
                "high kick": ["{A} raises the tempo and wraps a high kick around {B}'s guard.", "The shin reaches the head for {A}; {B} absorbs it but looks shaken."],
            },
            "Wrestling": {
                "single leg": ["{A} gets to the single, runs the pipe and puts {B} on the mat.", "{A} catches the lead leg and finishes the single before {B} can square up."],
                "double leg": ["{A} changes levels under the hands and drives through a clean double-leg finish.", "Deep penetration step from {A}; {B} is carried to the boundary and taken down."],
                "re-shot": ["{A} stuffs the first contact, immediately re-shoots and wins the scramble.", "The first attack stalls, but {A} chains into the re-shot and finishes."],
                "body lock": ["{A} locks around the waist, steps behind and returns {B} to the mat.", "{A} wins the underhook battle and converts the body lock into control."],
                "mat return": ["{B} gets one foot under them, but {A} lifts and returns them hard to the mat.", "Another mat return from {A}; {B} cannot clear the hands around the waist."],
                "ride": ["{A} stays heavy on the hips, follows every turn and keeps {B} underneath.", "{A}'s wrist ride kills the escape and keeps the control clock moving."],
                "turn": ["{A} breaks {B} flat and exposes the back for scoring points.", "{A} drives across the shoulders and earns the turn as {B} fights off the back."],
                "pinning attack": ["{A} tightens the pressure across the chest; {B} bridges desperately away from the fall.", "{A} settles the pinning combination and {B} has to fight every inch off the back."],
            },
            "Brazilian Jiu-Jitsu": {
                "guard pull": ["{A} secures the preferred grips and pulls directly into an active guard.", "{A} sits to guard on their terms and immediately threatens {B}'s posture."],
                "sweep": ["{A} disrupts the base, comes up on top and completes the sweep.", "Beautiful timing from {A}, who redirects {B}'s pressure into a clean sweep."],
                "guard pass": ["{A} clears the knee line, settles the hips and completes the guard pass.", "{A} wins the grip fight and circles around {B}'s legs into side control."],
                "back take": ["{A} follows the turn, inserts both hooks and secures the back.", "{B} exposes the back during the scramble and {A} attaches immediately."],
                "mount advance": ["{A} isolates the near arm and slides through into mount.", "Heavy positional pressure from {A}, who advances from side control to mount."],
                "arm attack": ["{A} separates the elbow and extends the arm; {B} is forced into a hurried defensive roll.", "The arm is in danger as {A} transitions cleanly between the armbar and triangle."],
                "choke attack": ["{A} gets under the chin and tightens the choke; {B} fights the hands with urgency.", "A dangerous choke sequence from {A} forces {B} to turn and surrender position."],
                "leg entanglement": ["{A} enters the legs, controls the knee line and begins isolating the foot.", "{A} sits beneath the base and turns the exchange into a dangerous leg entanglement."],
            },
        }
        defended_lines = {
            "Boxing": ["{B} reads the attack, catches it on the gloves and answers before {A} can settle.", "{A} commits, but {B} slips outside and the counter just misses."],
            "Kickboxing": ["{B} checks the first attack and forces {A} to reset at kicking range.", "{A}'s attack is read early; {B} blocks and returns a quick low kick."],
            "Muay Thai": ["{B} checks the kick and answers immediately, refusing to concede the scoring exchange.", "{B} frames, turns out of the clinch and leaves {A} reaching."],
            "Wrestling": ["{B} gets the hips back, squares to the shot and forces a neutral reset.", "{A} attacks, but {B} wins the scramble and clears the danger."],
            "Brazilian Jiu-Jitsu": ["{B} recognizes the transition, rebuilds the frames and denies {A}'s advance.", "{A} threatens, but {B} stays calm and pummels back to a safe position."],
        }
        presentation_sport = "Lethwei" if sport == "Muay Thai" and getattr(actor, "primary_discipline", "") == "Lethwei" else sport
        generated = (
            self.combat_sport_bjj_situation_bank().get(action, {})
            if sport == "Brazilian Jiu-Jitsu"
            else self.combat_sport_striking_situation_bank().get(presentation_sport, {}).get(action, {})
        )
        if success:
            pool = list(success_lines.get(sport, {}).get(action, [])) + list(generated.get("land", []))
        else:
            pool = list(generated.get("defended", [])) or defended_lines.get(sport, [])
        if not pool:
            pool = ["{A} creates an opening, but {B} closes it before the attack develops."]
        line = random.choice(pool).format(A=actor.name, B=defender.name)
        if momentum and success:
            if sport == "Brazilian Jiu-Jitsu":
                if action in ("arm attack", "choke attack", "leg entanglement", "front headlock"):
                    line += random.choice([" The submission pressure is building now.", " That is the most dangerous threat of the match so far."])
                elif action in ("guard recovery", "positional escape", "defensive framing"):
                    line += random.choice([" That recovery could change the shape of the match.", " Composed defence keeps the match competitive."])
                else:
                    line += random.choice([" The positional initiative is beginning to shift.", " That is the clearest positional sequence of the match so far."])
            else:
                line += random.choice([" The momentum is beginning to shift.", " That is the clearest sequence of the round so far.", " The pressure is building now."])
        return line

    def combat_sport_bjj_legal_actions(self, actions, actor, state):
        """Limit BJJ narration to actions that make sense from the current position."""
        position = state.get("position", "standing")
        actor_name = actor.name
        if position == "standing":
            legal = {"grip exchange", "takedown", "guard pull", "front headlock"}
        elif actor_name == state.get("top"):
            legal = {
                "guard": {"grip exchange", "pressure adjustment", "guard pass", "arm attack", "leg entanglement"},
                "half guard": {"grip exchange", "pressure adjustment", "guard pass", "back take", "mount advance", "arm attack", "front headlock"},
                "side control": {"grip exchange", "pressure adjustment", "mount advance", "back take", "arm attack", "choke attack"},
                "mount": {"grip exchange", "pressure adjustment", "arm attack", "choke attack", "back take"},
                "back control": {"grip exchange", "pressure adjustment", "choke attack", "arm attack"},
            }.get(position, {"arm attack", "choke attack", "front headlock"})
        else:
            legal = {
                "guard": {"grip exchange", "off-balance attempt", "sweep", "arm attack", "choke attack", "leg entanglement"},
                "half guard": {"grip exchange", "off-balance attempt", "sweep", "guard recovery", "positional escape", "leg entanglement", "front headlock"},
                "side control": {"grip exchange", "defensive framing", "guard recovery", "positional escape"},
                "mount": {"grip exchange", "defensive framing", "guard recovery", "positional escape"},
                "back control": {"grip exchange", "defensive framing", "guard recovery", "positional escape"},
            }.get(position, {"guard recovery", "positional escape"})
        filtered = [action for action in actions if action[0] in legal]
        return filtered or actions

    def combat_sport_bjj_apply_transition(self, state, action, actor, defender, success):
        """Apply a successful, commentary-only BJJ position transition."""
        if not success:
            return ""
        actor_name, defender_name = actor.name, defender.name
        previous = (state.get("position"), state.get("top"), state.get("bottom"))
        position = state.get("position", "standing")
        if action == "takedown":
            state.update(position="guard", top=actor_name, bottom=defender_name)
        elif action == "guard pull":
            state.update(position="guard", top=defender_name, bottom=actor_name)
        elif action == "sweep" and actor_name == state.get("bottom"):
            state.update(position="guard", top=actor_name, bottom=defender_name)
        elif action == "guard pass" and actor_name == state.get("top"):
            state["position"] = "side control"
        elif action == "guard recovery" and actor_name == state.get("bottom"):
            state["position"] = "guard"
        elif action == "positional escape" and actor_name == state.get("bottom"):
            state.update(position="standing", top=None, bottom=None)
        elif action == "back take":
            state.update(position="back control", top=actor_name, bottom=defender_name)
        elif action == "mount advance" and actor_name == state.get("top"):
            state["position"] = "mount"
        current = (state.get("position"), state.get("top"), state.get("bottom"))
        if current == previous:
            return ""
        if state["position"] == "standing":
            return "They separate and return to standing after the escape."
        labels = {
            "guard": "guard",
            "half guard": "half guard",
            "side control": "side control",
            "mount": "mount",
            "back control": "back control",
        }
        return f"Position settles: {state['top']} controls from {labels.get(state['position'], state['position'])}, with {state['bottom']} working underneath."

    def combat_sport_bjj_position_update(self, state):
        """Return a concise mat-side position read without consuming simulation RNG."""
        if state.get("position") == "standing":
            return "Mat-side update: both athletes are standing and hand-fighting for the next clean entry."
        if state.get("position") == "guard":
            return (
                f"Mat-side update: {state.get('top')} is working to open and pass the guard; "
                f"{state.get('bottom')} remains active underneath with sweeps and submissions available."
            )
        return (
            f"Mat-side update: {state.get('top')} is controlling {state.get('position')}; "
            f"{state.get('bottom')} must recover position before opening up safely."
        )

    def combat_sport_bjj_terminal_line(self, winner, loser, state):
        """Make a BJJ submission result the final visible action of the match."""
        position = state.get("position", "standing")
        if state.get("top") == winner.name and position == "back control":
            return f"{winner.name} wins the final hand fight from the back, slides the forearm under the chin and locks the choke. {loser.name} taps."
        if state.get("top") == winner.name and position == "mount":
            return f"{winner.name} isolates an arm from mount, steps over the head and extends the armbar. {loser.name} taps."
        if state.get("bottom") == winner.name and position in ("guard", "half guard"):
            return f"{winner.name} breaks the posture from underneath, closes the triangle and adjusts the angle. {loser.name} taps."
        if state.get("top") == winner.name and position in ("guard", "side control"):
            return f"{winner.name} traps the far arm during the final transition and tightens the shoulder lock. {loser.name} taps."
        return f"{winner.name} wins the last scramble, wraps the front headlock and finishes the guillotine. {loser.name} taps."

    def combat_sport_round_seconds(self, sport):
        """Return the broadcast clock used by a standard round/match."""
        return {
            "Boxing": 180,
            "Kickboxing": 180,
            "Muay Thai": 180,
            "Wrestling": 120,
            "Brazilian Jiu-Jitsu": 600,
        }.get(sport, 180)

    def combat_sport_clock(self, sport, beat_no, beat_count):
        """Space narrated exchanges across the live clock without changing simulation RNG."""
        duration = self.combat_sport_round_seconds(sport)
        remaining = max(1, round(duration * (beat_count + 1 - beat_no) / (beat_count + 1)))
        return f"{remaining // 60}:{remaining % 60:02d}"

    def simulate_combat_sport_live_beats(self, sport, a, b, round_no, margin, stamina, damage, body=None, leg=None, cuts=None):
        """Simulate and narrate the exchanges inside one non-MMA round."""
        body = body if body is not None else {a.name: 0.0, b.name: 0.0}
        leg = leg if leg is not None else {a.name: 0.0, b.name: 0.0}
        cuts = cuts if cuts is not None else {a.name: 0.0, b.name: 0.0}
        actions = self.combat_sport_live_actions(sport)
        beat_count = random.randint(7, 11) if sport != "Brazilian Jiu-Jitsu" else random.randint(20, 28)
        lines = []
        successful = {a.name: 0, b.name: 0}
        previous_actor = None
        recent_lines = []
        bjj_state = {"position": "standing", "top": None, "bottom": None}
        for beat_no in range(1, beat_count + 1):
            a_share = max(0.22, min(0.78, 0.50 + margin / 115))
            actor, defender = (a, b) if random.random() < a_share else (b, a)
            actor_overall = actor.overall
            available_actions = self.combat_sport_bjj_legal_actions(actions, actor, bjj_state) if sport == "Brazilian Jiu-Jitsu" else actions
            action_weights = [
                max(8, self.ds(actor, item[1], actor_overall)) * self.combat_sport_action_multiplier(sport, actor, item[0], stamina[actor.name])
                for item in available_actions
            ]
            action = random.choices(available_actions, weights=action_weights, k=1)[0]
            action_name, attack_key, defense_key, cost, base_damage = action
            attack_fallback = actor.wrestling if sport == "Wrestling" else actor.grappling if sport == "Brazilian Jiu-Jitsu" else actor.striking
            defense_fallback = defender.takedown_defence if sport == "Wrestling" else defender.submission_defence if sport == "Brazilian Jiu-Jitsu" else defender.striking
            attack = self.ds(actor, attack_key, attack_fallback) + actor.fight_iq * 0.11 + stamina[actor.name] * 0.10 + actor.momentum * 1.4
            defense = self.ds(defender, defense_key, defense_fallback) + defender.fight_iq * 0.09 + stamina[defender.name] * 0.08
            exchange_margin = attack - defense + random.gauss(0, 15)
            success = exchange_margin >= -1.5
            stamina[actor.name] = max(3, stamina[actor.name] - cost * random.uniform(0.20, 0.34))
            stamina[defender.name] = max(3, stamina[defender.name] - cost * random.uniform(0.06, 0.13))
            if success:
                successful[actor.name] += 1
                impact = base_damage * 0.28 + max(0, exchange_margin) / 65 + actor.power / 500
                damage[defender.name] += impact
                if action_name in ("body shot", "body kick", "straight knee", "clinch knee"):
                    body[defender.name] += impact
                    stamina[defender.name] = max(3, stamina[defender.name] - 0.5 - impact * 0.18)
                if action_name == "low kick":
                    leg[defender.name] += impact
                if action_name in ("elbow", "right hand", "uppercut", "head kick", "high kick"):
                    cut_skill = self.ds(actor, "cut_creation", actor.power)
                    cuts[defender.name] += max(0, impact * (0.18 + cut_skill / 500) - 0.15)
            momentum = previous_actor is not actor and success and successful[actor.name] >= 2
            line = self.combat_sport_live_line(sport, action_name, actor, defender, success, momentum=momentum)
            for _ in range(8):
                if line not in recent_lines:
                    break
                line = self.combat_sport_live_line(sport, action_name, actor, defender, success, momentum=momentum)
            if line in recent_lines:
                line += " The position changes before they engage again."
            if sport == "Brazilian Jiu-Jitsu":
                transition = self.combat_sport_bjj_apply_transition(bjj_state, action_name, actor, defender, success)
                if transition:
                    line += f" {transition}"
            # Other-sport cards use the same genuine playback rhythm as MMA:
            # every exchange is placed on a visible round or match clock.
            lines.append(f"  [{self.combat_sport_clock(sport, beat_no, beat_count)}] {line}")
            if sport == "Brazilian Jiu-Jitsu" and beat_no in (beat_count // 3, (beat_count * 2) // 3):
                lines.append(f"  [{self.combat_sport_clock(sport, beat_no, beat_count)}] {self.combat_sport_bjj_position_update(bjj_state)}")
            recent_lines.append(line)
            del recent_lines[:-16]
            previous_actor = actor if success else previous_actor
        return lines, successful, bjj_state

    def combat_sport_round_status(self, sport, a, b, stamina, damage, body=None, leg=None, cuts=None):
        if sport == "Brazilian Jiu-Jitsu":
            a_gas, b_gas = round(stamina[a.name]), round(stamina[b.name])
            if min(a_gas, b_gas) < 35:
                tired = a if a_gas < b_gas else b
                read = f"{tired.name}'s grip endurance is fading, making every frame and hand fight more expensive."
            elif abs(a_gas - b_gas) >= 12:
                fresher = a if a_gas > b_gas else b
                read = f"{fresher.name} looks fresher in the scrambles and is reaching each second effort first."
            elif min(a_gas, b_gas) >= 70:
                read = "Both athletes have managed the ten-minute pace well; the technical decisions remain sharp."
            else:
                read = "The accumulated grip fighting is slowing the transitions, so efficient frames and pressure matter more now."
            return f"Mat-side condition: {a.name} stamina {a_gas}, {b.name} stamina {b_gas}. {read}"
        if sport == "Wrestling":
            return f"Mat-side read: {a.name} stamina {round(stamina[a.name])}, {b.name} stamina {round(stamina[b.name])}; the hand-fighting pace is beginning to matter."
        a_state = "marked up" if damage[a.name] >= 7 else "under pressure" if damage[a.name] >= 3.5 else "composed"
        b_state = "marked up" if damage[b.name] >= 7 else "under pressure" if damage[b.name] >= 3.5 else "composed"
        body = body or {a.name: 0, b.name: 0}
        leg = leg or {a.name: 0, b.name: 0}
        cuts = cuts or {a.name: 0, b.name: 0}
        details = []
        for fighter in (a, b):
            concerns = []
            if body[fighter.name] >= 3:
                concerns.append("body wear")
            if leg[fighter.name] >= 3:
                concerns.append("lead-leg damage")
            if cuts[fighter.name] >= 1.2:
                concerns.append("facial cut")
            if concerns:
                details.append(f"{fighter.name}: {', '.join(concerns)}")
        condition_note = f" Damage: {'; '.join(details)}." if details else ""
        return f"Corner read: {a.name} stamina {round(stamina[a.name])} ({a_state}); {b.name} stamina {round(stamina[b.name])} ({b_state}).{condition_note}"

    def combat_sport_focus_fit(self, sport, fighter):
        preferred = {
            "Boxing": "Striking", "Kickboxing": "Striking", "Muay Thai": "Striking",
            "Wrestling": "Wrestling", "Brazilian Jiu-Jitsu": "Grappling",
        }.get(sport, "Balanced")
        focus = getattr(fighter, "camp_focus", "Balanced")
        if focus == preferred:
            return 3.0
        if focus in ("Conditioning", "Game Plan", "Weight Management"):
            return 1.5
        return 0.0 if focus == "Balanced" else -0.8

    def perform_combat_sport_weigh_in(self, sport, fighter, title_fight=False, camp_weeks=None, persist=True):
        """Resolve a weigh-in against the athlete's real sport-class limit."""
        native_sport = getattr(fighter, "primary_discipline", sport)
        if native_sport not in COMBAT_SPORT_WEIGHT_CLASSES:
            native_sport = sport
        division = getattr(fighter, "sport_weight_class", "") or self.assign_combat_sport_weight(native_sport, fighter)
        class_limit = self.combat_sport_weight_limit(native_sport, division, fighter.gender)
        walk = fighter.walk_weight or self.default_walk_weight(fighter)
        if class_limit is None:
            result = {"limit": "Open", "walk": walk, "cut_amount": 0, "miss_by": 0.0,
                      "scale_weight": round(float(walk), 1), "penalty": 0, "made": True}
            if persist:
                fighter.scale_weight = result["scale_weight"]
                fighter.missed_weight = False
                fighter.weight_cut_penalty = 0
            return result
        limit = class_limit + (0 if title_fight else 1)
        cut_amount = max(0, walk - limit)
        cut_skill = self.ds(fighter, "weight_cutting", fighter.cardio)
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        natural_size = self.ds(fighter, "natural_size", 50)
        weeks = fighter.camp_weeks if camp_weeks is None else max(0, int(camp_weeks))
        camp_quality = fighter.camp_quality or self.gym_quality(fighter.camp)
        focus_bonus = 3.0 if getattr(fighter, "camp_focus", "") == "Weight Management" else 0.0
        preparation = min(9.0, weeks * 0.82) + fighter.camp_boost * 0.7 + camp_quality * 0.025 + focus_bonus
        sustainable_cut = 8 + cut_skill * 0.15 + conditioning * 0.045 + preparation - max(0, natural_size - 55) * 0.1
        variance = random.uniform(-3.0, 2.2)
        miss_by = max(0, round((cut_amount - sustainable_cut + variance) * 0.75, 1))
        scale_weight = round(limit + miss_by if miss_by else limit - random.uniform(0.1, 1.0), 1)
        penalty = max(0, min(22, round(max(0, cut_amount - sustainable_cut + 5) * 0.7 + miss_by * 3 + max(0, 3 - weeks) * 0.8)))
        result = {"limit": limit, "walk": walk, "cut_amount": cut_amount, "miss_by": miss_by,
                  "scale_weight": scale_weight, "penalty": penalty, "made": miss_by <= 0}
        if persist:
            fighter.scale_weight = scale_weight
            fighter.missed_weight = miss_by > 0
            fighter.weight_cut_penalty = penalty
        return result

    def prepare_combat_sport_fighter(self, sport, fighter, title=False):
        """Run a real camp and weigh-in before a combat-sport card.

        Combat-sport cards are generated and resolved together, so this models
        the camp retrospectively from activity, professionalism and motivation.
        It uses the same gym/camp/weigh-in functions as MMA and stores the same
        fighter fields for profiles and save compatibility.
        """
        inactivity = self.combat_sport_inactivity_months(fighter)
        reliability = (fighter.professionalism + fighter.motivation) / 2
        weeks = round(5 + min(4, inactivity * 0.55) + (reliability - 55) / 28 + random.uniform(-1.8, 1.8))
        weeks = max(2, min(12, weeks))
        gym = self.gym_by_name(fighter.camp)
        quality = self.gym_quality(fighter.camp)
        specialty = self.gym_specialty_bonus(fighter, gym)
        focus_fit = self.combat_sport_focus_fit(sport, fighter)
        focus_bonus = self.camp_focus_bonus(fighter, gym)
        intensity = getattr(fighter, "camp_intensity", "Standard")
        intensity_bonus = {"Light": -1.5, "Standard": 0, "Hard": 3.5}.get(intensity, 0)
        attention = self.gym_attention_multiplier(gym)
        base_boost = round(
            weeks * (quality + specialty + focus_bonus + focus_fit * 2 + intensity_bonus) / 112
            * (0.55 + fighter.professionalism / 100 * 0.3 + fighter.motivation / 100 * 0.25)
            / 2.8 * attention
        )
        fighter.camp_quality = quality
        fighter.camp_weeks = weeks
        fighter.camp_boost = min(12, max(0, base_boost + self.camp_form_variance(fighter, gym)))
        fighter.morale = min(100, fighter.morale + max(0, fighter.camp_boost // 3))
        self.apply_gym_camp_micro_improvement(fighter, gym, weeks)
        self.apply_camp_focus_improvement(fighter, gym, weeks)
        self.evolve_trait_from_camp(fighter, quality, weeks)
        setback = False
        if intensity == "Hard" and random.random() < max(0.012, fighter.injury_proneness / 1900):
            setback = True
            fighter.camp_boost = max(0, fighter.camp_boost - 3)
            fighter.fatigue = min(100, fighter.fatigue + random.randint(3, 8))
        weigh_in = self.perform_combat_sport_weigh_in(sport, fighter, title_fight=title, camp_weeks=weeks, persist=True)
        focus_text = getattr(fighter, "camp_focus", "Balanced")
        note = f"Camp: {fighter.name} completed {weeks} weeks at {fighter.camp} ({focus_text}, {intensity}); readiness +{fighter.camp_boost}."
        if setback:
            note += " A hard-camp knock reduced the final preparation score."
        weight_outcome = "made weight" if weigh_in["made"] else f"missed by {weigh_in['miss_by']:.1f} lb"
        weight_note = f"Weigh-in: {fighter.name} {weight_outcome} at {weigh_in['scale_weight']} lb; cut penalty {weigh_in['penalty']}."
        return {"weeks": weeks, "setback": setback, "weigh_in": weigh_in, "notes": [note, weight_note]}

    def prepare_combat_sport_bout(self, sport, a, b, title=False):
        a_prep = self.prepare_combat_sport_fighter(sport, a, title=title)
        b_prep = self.prepare_combat_sport_fighter(sport, b, title=title)
        title_valid = title and a_prep["weigh_in"]["made"] and b_prep["weigh_in"]["made"]
        notes = a_prep["notes"] + b_prep["notes"]
        if title and not title_valid:
            notes.append("Commission ruling: a missed weight removes championship status from this bout.")
        return {"a": a_prep, "b": b_prep, "title_valid": title_valid, "notes": notes}

    def combat_sport_readiness_modifier(self, sport, fighter, opponent=None, title=False):
        mental = (fighter.morale - 55) * 0.065 + (fighter.motivation - 55) * 0.055
        preparation = fighter.camp_boost * 0.85 + min(2.4, fighter.camp_weeks * 0.20)
        gym = min(2.2, (fighter.camp_quality or self.gym_quality(fighter.camp)) / 48)
        focus = self.combat_sport_focus_fit(sport, fighter)
        cut = fighter.weight_cut_penalty * 1.15
        trait = 0.0
        if fighter.trait in ("Clutch", "Title Mentality") and title:
            trait += 2.0
        if fighter.trait in ("Gym Rat", "Coach Favourite"):
            trait += 1.0
        if fighter.trait == "Momentum Fighter":
            trait += fighter.momentum * 0.55
        if fighter.trait in ("Erratic", "Slow Starter"):
            trait -= random.uniform(0.5, 2.0)
        pressure = 0.0
        if opponent and opponent.popularity > fighter.popularity + 18:
            composure = self.ds(fighter, "composure", fighter.fight_iq)
            pressure = (composure - 55) / 25
        return max(-12, min(16, mental + preparation + gym + focus + trait + pressure - cut))

    def combat_sport_action_multiplier(self, sport, fighter, action_name, stamina):
        multiplier = 1.0
        trait = fighter.trait
        behaviour = fighter.behaviour
        if trait == "Body Hunter" and action_name in ("body shot", "body kick", "straight knee", "clinch knee"):
            multiplier *= 1.8
        if trait == "Leg Kicker" and action_name == "low kick":
            multiplier *= 1.8
        if trait == "Elbow Specialist" and action_name == "elbow":
            multiplier *= 1.9
        if trait in ("Counter Specialist", "Comeback Artist") and action_name in ("check hook", "counter cross", "re-shot", "sweep"):
            multiplier *= 1.55
        if trait in ("Knockout Artist", "Big Finisher", "Fight Finisher") and action_name in ("right hand", "uppercut", "head kick", "high kick", "elbow", "pinning attack", "choke attack"):
            multiplier *= 1.45
        if behaviour in ("Pressure Fighter", "Dynamic Attacker") and action_name in ("combination", "rope attack", "kick-punch combination", "clinch knee", "straight knee", "double leg", "guard pass"):
            multiplier *= 1.30
        elif behaviour in ("Counter Specialist", "Cautious Counter") and action_name in ("check hook", "counter cross", "re-shot", "sweep"):
            multiplier *= 1.35
        if stamina < 28 and action_name in ("combination", "rope attack", "head kick", "spinning attack", "high kick", "double leg", "mat return", "pinning attack", "choke attack", "leg entanglement"):
            multiplier *= 0.48
        return multiplier

    def clear_combat_sport_preparation(self, fighter):
        fighter.camp_boost = 0
        fighter.camp_weeks = 0
        fighter.weight_cut_penalty = 0
        fighter.missed_weight = False

    def simulate_combat_sport_bout(self, sport, a, b, title=False):
        rules = self.combat_sport_bout_rules(sport, title=title, a=a, b=b)
        a_attack, a_defense, a_finish = self.combat_sport_skill_set(sport, a)
        b_attack, b_defense, b_finish = self.combat_sport_skill_set(sport, b)
        a_points = b_points = 0
        a_rounds = b_rounds = 0
        a_damage = b_damage = 0
        # Other sports now begin from the same physical-readiness calculation
        # as MMA: conditioning, resilience, fatigue, traits and weight-cut state.
        # The sport-specific exchanges below then spend that gas differently.
        a_stamina = self.starting_fight_gas(a)
        b_stamina = self.starting_fight_gas(b)
        stamina = {a.name: float(a_stamina), b.name: float(b_stamina)}
        damage = {a.name: 0.0, b.name: 0.0}
        body_damage = {a.name: 0.0, b.name: 0.0}
        leg_damage = {a.name: 0.0, b.name: 0.0}
        cuts = {a.name: 0.0, b.name: 0.0}
        a_readiness = self.combat_sport_readiness_modifier(sport, a, b, title=title)
        b_readiness = self.combat_sport_readiness_modifier(sport, b, a, title=title)
        log = []
        round_scores = []
        fight_edge = 0
        winner = loser = None
        method = rules["decision"]
        end_round = rules["rounds"]
        log.append(self.combat_sport_opening_commentary(sport, a, b, title=title))

        for round_no in range(1, rules["rounds"] + 1):
            if round_no > 1:
                a_recovery = 1.0 + self.ds(a, "conditioning", a.cardio) / 45 + a.recovery / 120 + a.camp_quality / 100 + a.camp_weeks * 0.04 + a.camp_boost * 0.08 - body_damage[a.name] * 0.10
                b_recovery = 1.0 + self.ds(b, "conditioning", b.cardio) / 45 + b.recovery / 120 + b.camp_quality / 100 + b.camp_weeks * 0.04 + b.camp_boost * 0.08 - body_damage[b.name] * 0.10
                if a.trait == "Cardio Machine":
                    a_recovery += 1.4
                if b.trait == "Cardio Machine":
                    b_recovery += 1.4
                stamina[a.name] = min(a_stamina, stamina[a.name] + a_recovery)
                stamina[b.name] = min(b_stamina, stamina[b.name] + b_recovery)
            a_energy = stamina[a.name] + random.uniform(-4, 4) - leg_damage[a.name] * (0.20 if sport in ("Kickboxing", "Muay Thai") else 0.05)
            b_energy = stamina[b.name] + random.uniform(-4, 4) - leg_damage[b.name] * (0.20 if sport in ("Kickboxing", "Muay Thai") else 0.05)
            a_perf = a_attack + a.momentum * 2.6 + a_energy * 0.20 + a_readiness - b_defense * 0.42 + random.gauss(0, 10)
            b_perf = b_attack + b.momentum * 2.6 + b_energy * 0.20 + b_readiness - a_defense * 0.42 + random.gauss(0, 10)

            round_seconds = self.combat_sport_round_seconds(sport)
            round_clock = f"{round_seconds // 60}:{round_seconds % 60:02d}"
            if sport == "Brazilian Jiu-Jitsu":
                log.append(f"MATCH CLOCK — {round_clock} | The referee starts the contest.")
            elif sport == "Wrestling":
                log.append(f"PERIOD {round_no} — {round_clock} | The whistle sounds and both wrestlers take the centre.")
            else:
                log.append(f"ROUND {round_no} — {round_clock} | The bell sounds.")

            if sport == "Wrestling":
                a_rp = max(0, round((a_perf - b_perf) / 9 + random.choice([0, 1, 2, 3])))
                b_rp = max(0, round((b_perf - a_perf) / 9 + random.choice([0, 1, 2, 3])))
                if a_rp == b_rp:
                    a_rp += 1 if a_perf >= b_perf else 0
                    b_rp += 1 if b_perf > a_perf else 0
                a_points += a_rp
                b_points += b_rp
                margin = a_rp - b_rp
                leader, trailer = (a, b) if margin >= 0 else (b, a)
                live_lines, _successful, _position_state = self.simulate_combat_sport_live_beats(sport, a, b, round_no, a_perf - b_perf, stamina, damage, body_damage, leg_damage, cuts)
                log.extend(live_lines)
                if abs(a_points - b_points) >= rules.get("tech_gap", 10) and round_no >= 2:
                    winner, loser = (a, b) if a_points > b_points else (b, a)
                    method = "Technical Fall"
                    end_round = round_no
                    log.append(self.combat_sport_finish_commentary(sport, round_no, winner, loser, method))
                    break
                # Generate the recap before the pin roll to retain the established
                # RNG/order and balance, but only display it if the period survives.
                period_commentary = self.combat_sport_round_commentary(sport, round_no, leader, trailer, abs(margin), points_text=f"{a.name} {a_rp}, {b.name} {b_rp}")
                pin_chance = max(0.006, min(0.14, (max(a_finish - b_defense, b_finish - a_defense) - 16) / 230))
                if random.random() < pin_chance:
                    winner, loser = (a, b) if a_perf + a_finish >= b_perf + b_finish else (b, a)
                    method = "Pin"
                    end_round = round_no
                    log.append(self.combat_sport_finish_commentary(sport, round_no, winner, loser, method))
                    break
                log.append(period_commentary)
                log.append(
                    f"Period {round_no} summary: {a.name} {a_rp}-{b_rp} {b.name}. "
                    f"Live score {a.name} {a_points}-{b_points} {b.name}. "
                    f"Stamina: {a.name} {round(stamina[a.name])}, {b.name} {round(stamina[b.name])}."
                )
                log.append(self.combat_sport_round_status(sport, a, b, stamina, damage, body_damage, leg_damage, cuts))
            elif sport == "Brazilian Jiu-Jitsu":
                a_rp = max(0, round((a_perf - b_perf) / 10 + random.choice([0, 2, 2, 3])))
                b_rp = max(0, round((b_perf - a_perf) / 10 + random.choice([0, 2, 2, 3])))
                a_points += a_rp
                b_points += b_rp
                margin = a_rp - b_rp
                leader, trailer = (a, b) if margin >= 0 else (b, a)
                sub_a = max(0.015, min(0.62, ((a_finish - b_defense) * 1.05 + (a_perf - b_perf) * 1.35 + 16) / 165))
                sub_b = max(0.015, min(0.62, ((b_finish - a_defense) * 1.05 + (b_perf - a_perf) * 1.35 + 16) / 165))
                live_lines, _successful, position_state = self.simulate_combat_sport_live_beats(sport, a, b, round_no, a_perf - b_perf, stamina, damage, body_damage, leg_damage, cuts)
                log.extend(live_lines)
                if random.random() < max(sub_a, sub_b):
                    winner, loser = (a, b) if sub_a >= sub_b else (b, a)
                    method = "Submission"
                    end_round = round_no
                    log.append(f"  [0:05] {self.combat_sport_bjj_terminal_line(winner, loser, position_state)}")
                    log.append(f"Submission confirmed: {winner.name} forces the tap from {loser.name} before time expires.")
                    break
                log.append("  [0:00] Time expires. Both athletes release their grips and await the official score.")
                log.append(self.combat_sport_round_commentary(sport, round_no, leader, trailer, abs(margin), points_text=f"{a.name} {a_rp}, {b.name} {b_rp}"))
                log.append(
                    f"Match summary: {a.name} {a_rp}-{b_rp} {b.name}. "
                    f"Live score {a.name} {a_points}-{b_points} {b.name}. "
                    f"Stamina: {a.name} {round(stamina[a.name])}, {b.name} {round(stamina[b.name])}."
                )
                log.append(self.combat_sport_round_status(sport, a, b, stamina, damage, body_damage, leg_damage, cuts))
            else:
                margin = a_perf - b_perf
                fight_edge += margin
                live_lines, _successful, _position_state = self.simulate_combat_sport_live_beats(sport, a, b, round_no, margin, stamina, damage, body_damage, leg_damage, cuts)
                log.extend(live_lines)
                round_winner = a if margin >= 0 else b
                if round_winner is a:
                    a_rounds += 1
                    a_score, b_score = (10, 8) if margin > 31 and random.random() < 0.18 else (10, 9)
                else:
                    b_rounds += 1
                    a_score, b_score = (8, 10) if margin < -31 and random.random() < 0.18 else (9, 10)
                round_scores.append((a_score, b_score))
                # Live exchanges accumulate enough detail for the viewer to
                # describe condition, but only a calibrated fraction feeds the
                # established finish model. Otherwise a ten-round boxing bout
                # receives ten rounds of full-exchange damage on top of its
                # existing stoppage pressure and becomes unrealistically wild.
                a_damage = damage[a.name] * 0.15
                b_damage = damage[b.name] * 0.15
                score_text = f"Scores {a.name} {a_score}-{b_score} {b.name}."
                trailer = b if round_winner is a else a
                finish_divisor = rules.get("finish_divisor", 300)
                finish_cap = rules.get("finish_cap", 0.30)
                if sport == "Boxing":
                    finish_a = (a_finish - b.chin + b_damage * 3.3 + body_damage[b.name] * 0.45 + cuts[b.name] * 0.55 + max(0, margin) * 0.62 - max(0, b_energy - 55) * 0.10) / finish_divisor
                    finish_b = (b_finish - a.chin + a_damage * 3.3 + body_damage[a.name] * 0.45 + cuts[a.name] * 0.55 + max(0, -margin) * 0.62 - max(0, a_energy - 55) * 0.10) / finish_divisor
                else:
                    finish_a = (a_finish - b.chin + b_damage * 4.2 + body_damage[b.name] * 0.40 + leg_damage[b.name] * 0.28 + cuts[b.name] * 0.65 + max(0, margin) * 0.82) / finish_divisor
                    finish_b = (b_finish - a.chin + a_damage * 4.2 + body_damage[a.name] * 0.40 + leg_damage[a.name] * 0.28 + cuts[a.name] * 0.65 + max(0, -margin) * 0.82) / finish_divisor
                    if sport == "Muay Thai":
                        # Small gloves and clinch/elbow exchanges make Thai rules
                        # more volatile than kickboxing score-fighting. A clearly
                        # weaker fighter should still have a live counter/inside
                        # finish path without turning every close fight into chaos.
                        a_rating = self.combat_sport_rating(a, sport)
                        b_rating = self.combat_sport_rating(b, sport)
                        small_glove_volatility = 0.010
                        lethwei_bonus = 0.010 if rules.get("lethwei") else 0
                        if a_rating + 12 < b_rating:
                            finish_a += min(0.060, (b_rating - a_rating) / 520) + small_glove_volatility + lethwei_bonus
                        else:
                            finish_a += small_glove_volatility * 0.45 + lethwei_bonus * 0.50
                        if b_rating + 12 < a_rating:
                            finish_b += min(0.060, (a_rating - b_rating) / 520) + small_glove_volatility + lethwei_bonus
                        else:
                            finish_b += small_glove_volatility * 0.45 + lethwei_bonus * 0.50
                finish_a = max(0.003, min(finish_cap, finish_a))
                finish_b = max(0.003, min(finish_cap, finish_b))
                a_finish_lands = random.random() < finish_a
                b_finish_lands = random.random() < finish_b
                if a_finish_lands or b_finish_lands:
                    if a_finish_lands and b_finish_lands:
                        a_claim = finish_a + max(0, margin) / 360 + random.uniform(0, 0.04)
                        b_claim = finish_b + max(0, -margin) / 360 + random.uniform(0, 0.04)
                        winner, loser = (a, b) if a_claim >= b_claim else (b, a)
                    else:
                        winner, loser = (a, b) if a_finish_lands else (b, a)
                    method = rules["finish"]
                    loser_condition = loser.name
                    if cuts[loser_condition] >= 4.5 and random.random() < min(0.55, cuts[loser_condition] / 12):
                        method = "Doctor Stoppage"
                    elif stamina[loser_condition] <= 9 and damage[loser_condition] >= 8 and random.random() < 0.45:
                        method = "Corner Stoppage"
                    end_round = round_no
                    log.append(self.combat_sport_finish_commentary(sport, round_no, winner, loser, method))
                    break
                log.append(self.combat_sport_round_commentary(sport, round_no, round_winner, trailer, margin, score_text=score_text))
                a_total_live = sum(score[0] for score in round_scores)
                b_total_live = sum(score[1] for score in round_scores)
                log.append(
                    f"Round {round_no} summary: {a.name} {a_score}-{b_score} {b.name}. "
                    f"Live score {a.name} {a_total_live}-{b_total_live} {b.name}. "
                    f"Stamina: {a.name} {round(stamina[a.name])}, {b.name} {round(stamina[b.name])}."
                )
                log.append(self.combat_sport_round_status(sport, a, b, stamina, damage, body_damage, leg_damage, cuts))

        if not winner and method != "Draw":
            if sport in ("Wrestling", "Brazilian Jiu-Jitsu"):
                if a_points == b_points:
                    winner, loser = (a, b) if (a_attack + a_defense + random.random()) >= (b_attack + b_defense + random.random()) else (b, a)
                    method = "Referee Criteria"
                else:
                    winner, loser = (a, b) if a_points > b_points else (b, a)
                    method = rules["decision"]
            else:
                a_total = sum(score[0] for score in round_scores)
                b_total = sum(score[1] for score in round_scores)
                close = abs(a_total - b_total) <= 1
                draw_chance = rules.get("draw_chance", 0.06)
                if a_total == b_total and rules["draws"] and random.random() < draw_chance:
                    method = "Draw"
                else:
                    if a_total == b_total:
                        winner, loser = (a, b) if fight_edge >= 0 else (b, a)
                        method = "Majority Decision" if rules["draws"] else rules["decision"]
                    else:
                        winner, loser = (a, b) if a_total > b_total else (b, a)
                        method = rules["decision"]
        if sport in ("Wrestling", "Brazilian Jiu-Jitsu"):
            score_text = f"{a.name} {a_points}-{b_points} {b.name}"
        else:
            a_total = sum(score[0] for score in round_scores)
            b_total = sum(score[1] for score in round_scores)
            card_text = ", ".join(f"{x}-{y}" for x, y in round_scores) or "-"
            score_text = f"{a.name} {a_total}-{b_total} {b.name} ({card_text})"
        if not any("stoppage" in line.lower() or "submission" in line.lower() and "gets the tap" in line.lower() or "technical fall" in line.lower() or "secures the pin" in line.lower() for line in log[-2:]):
            if method in ("Decision", "Majority Decision", "Points", "Referee Criteria", "Draw"):
                log.append(self.combat_sport_decision_commentary(sport, winner, loser, method, score_text))
        condition = {
            a.name: {"stamina": round(stamina[a.name], 1), "damage": round(damage[a.name], 1), "body": round(body_damage[a.name], 1), "leg": round(leg_damage[a.name], 1), "cuts": round(cuts[a.name], 1)},
            b.name: {"stamina": round(stamina[b.name], 1), "damage": round(damage[b.name], 1), "body": round(body_damage[b.name], 1), "leg": round(leg_damage[b.name], 1), "cuts": round(cuts[b.name], 1)},
        }
        return {"winner": winner, "loser": loser, "method": method, "round": end_round, "score": score_text, "log": log, "condition": condition, "start_stamina": {a.name: round(a_stamina, 1), b.name: round(b_stamina, 1)}, "readiness": {a.name: round(a_readiness, 1), b.name: round(b_readiness, 1)}}

    def develop_after_combat_sport_bout(self, sport, fighter, won=False, finished=False):
        if not self.combat_sport_growth_allowed(fighter, sport):
            self.record_combat_sport_rating_snapshot(fighter, sport)
            return
        stage = self.combat_sport_development_stage(fighter, sport)
        gap = max(0, min(99, fighter.potential) - self.combat_sport_display_rating(fighter, sport))
        base = 0.070 if stage == "Pre-prime" else 0.020 if stage == "Prime" else min(0.008, self.veteran_resurgence_chance(fighter) * 0.20)
        gap_bonus = min(0.075, gap * 0.0045) if stage == "Pre-prime" else min(0.035, gap * 0.0025) if stage == "Prime" else 0
        chance = base + gap_bonus + (0.018 if won else 0.006) + (0.010 if finished else 0)
        chance += max(0, fighter.professionalism - 55) / 900
        chance -= fighter.fatigue * 0.0011 + fighter.injured * 0.05
        ceiling = 0.20 if stage == "Pre-prime" else 0.08 if stage == "Prime" else 0.010
        if random.random() < max(0, min(ceiling, chance)):
            reason = "Post-bout experience"
            if won and finished:
                reason = "Post-bout experience from a winning finish"
            elif won:
                reason = "Post-bout experience from a win"
            self.adjust_combat_sport_skill_bundle(fighter, sport, 1, reason, key_count=3 if stage == "Pre-prime" else 2)
        self.record_combat_sport_rating_snapshot(fighter, sport)

    def record_combat_sport_season_result(self, state, a, b, winner, method, title_key="", previous_champion=""):
        stats = state.setdefault("season_stats", {})
        for fighter in (a, b):
            row = stats.setdefault(fighter.name, {"bouts": 0, "wins": 0, "losses": 0, "draws": 0, "finishes": 0, "title_wins": 0, "title_defenses": 0, "score": 0})
            row["bouts"] += 1
            if not winner:
                row["draws"] += 1
                row["score"] += 2
            elif fighter is winner:
                row["wins"] += 1
                row["score"] += 8 + min(5, fighter.popularity // 20)
                if method not in ("Decision", "Majority Decision", "Points", "Referee Criteria"):
                    row["finishes"] += 1
                    row["score"] += 3
                if title_key:
                    if previous_champion == fighter.name:
                        row["title_defenses"] += 1
                        row["score"] += 6
                    else:
                        row["title_wins"] += 1
                        row["score"] += 10
            else:
                row["losses"] += 1
        state["records"] = state.get("records", {})
        state["records"][a.name] = a.record
        state["records"][b.name] = b.record

    def consider_combat_sport_hall_of_fame(self, sport, world, fighter, state):
        if any(entry.get("name") == fighter.name for entry in state.get("hall_of_fame", []) if isinstance(entry, dict)):
            return False
        title_entries = sum(1 for history in state.get("title_history", {}).values() for entry in history if entry.get("winner") == fighter.name)
        score = fighter.record_w * 2 + title_entries * 9 + fighter.popularity + max(0, self.combat_sport_rating(fighter, sport) - 140) / 2
        if fighter.record_w < 10 or score < 105:
            return False
        induction = {
            "name": fighter.name, "year": self.current_year(), "record": fighter.record,
            "titles": title_entries, "popularity": fighter.popularity,
            "summary": f"{fighter.name} inducted after a {fighter.record} {sport} career with {title_entries} championship result(s).",
        }
        state.setdefault("hall_of_fame", []).insert(0, induction)
        state["hall_of_fame"] = state["hall_of_fame"][:100]
        world.setdefault("media", []).insert(0, f"HALL OF FAME: {induction['summary']}")
        return True

    def retire_combat_sport_after_final_fight(self, sport, world, fighter, state):
        if not fighter.retirement_pending or fighter.retired:
            return False
        self.update_fighter_peak_overall(fighter)
        fighter.retirement_fight_completed = True
        fighter.retirement_pending = False
        fighter.retired = True
        fighter.retirement_reason = f"Retired from {sport} after a final fight at age {fighter.age}."
        fighter.champion = False
        for key, champion in list(state.get("titles", {}).items()):
            if champion == fighter.name:
                state["titles"][key] = ""
                state.setdefault("title_history", {}).setdefault(key, []).insert(0, {
                    "month": self.month, "year": self.current_year(), "winner": "VACANT",
                    "loser": "", "method": "Retirement", "previous_champion": fighter.name,
                })
        headline = f"{fighter.name} retired from {sport} after completing a required farewell fight ({fighter.record})."
        world.setdefault("media", []).insert(0, headline)
        self.news.insert(0, headline)
        self.record_world_story("Combat Sports Retirement", headline, fighter.retirement_reason, [world.get("promotion", "")], [fighter.name], 3)
        return True

    def apply_combat_sport_result(self, sport, world, a, b, title=False, player_owned=False, title_key="", employer=""):
        a_record_before, b_record_before = a.record, b.record
        a_rating_before, b_rating_before = self.bout_rating_snapshot(a), self.bout_rating_snapshot(b)
        state = self.ensure_combat_sport_circuit_state(sport, world, employer or a.sport_employer, player_owned)
        preparation = self.prepare_combat_sport_bout(sport, a, b, title=title)
        effective_title = bool(title and preparation["title_valid"])
        title_key = title_key or (self.combat_sport_division_key(a, sport) if effective_title else "")
        previous_champion = state.get("titles", {}).get(title_key, "") if title_key else ""
        sim = self.simulate_combat_sport_bout(sport, a, b, title=effective_title)
        readiness = sim.get("readiness", {})
        readiness_note = f"Fight-night readiness: {a.name} {readiness.get(a.name, 0):+} | {b.name} {readiness.get(b.name, 0):+}. Camp, morale, motivation, gym, traits and weight cut are active."
        sim["log"] = preparation["notes"] + [readiness_note] + sim.get("log", [])
        winner, loser, method = sim.get("winner"), sim.get("loser"), sim.get("method", "Decision")
        if method == "Draw" or not winner:
            self.record_bout_rating_history(a, b, "D", "D", {"title": effective_title})
        else:
            self.record_bout_rating_history(a, b, "W" if winner is a else "L", "L" if winner is a else "W", {"title": effective_title})
        if method == "Draw" or not winner:
            a.record_d += 1
            b.record_d += 1
            a.career_win_streak = b.career_win_streak = 0
            a.morale = min(100, a.morale + random.randint(0, 2))
            b.morale = min(100, b.morale + random.randint(0, 2))
            result_line = f"Month {self.month}: {a.name} and {b.name} fought to a draw in {sport} ({sim.get('score', '-')})"
        else:
            winner.record_w += 1
            loser.record_l += 1
            winner.career_win_streak = getattr(winner, "career_win_streak", 0) + 1
            loser.career_win_streak = 0
            winner.momentum = min(5, winner.momentum + 1)
            loser.momentum = max(-5, loser.momentum - 1)
            winner.morale = min(100, winner.morale + random.randint(3, 7))
            loser.morale = max(15, loser.morale - random.randint(3, 9))
            winner.motivation = min(99, winner.motivation + random.randint(1, 3))
            loser.motivation = max(1, loser.motivation - random.randint(1, 5))
            finished = method not in ("Decision", "Majority Decision", "Points", "Referee Criteria")
            winner.popularity = min(100, winner.popularity + (2 if effective_title else 1) + int(finished))
            loser.popularity = max(1, loser.popularity - (1 if loser.popularity > winner.popularity + 12 else 0))
            if effective_title:
                state.setdefault("titles", {})[title_key] = winner.name
                if previous_champion == winner.name:
                    winner.title_defenses += 1
                else:
                    winner.title_wins += 1
                state.setdefault("title_history", {}).setdefault(title_key, []).insert(0, {
                    "month": self.month, "year": self.current_year(), "winner": winner.name,
                    "loser": loser.name, "method": method, "previous_champion": previous_champion,
                })
                state["champion"] = winner.name
            round_note = f" R{sim.get('round')}" if method not in ("Decision", "Majority Decision", "Points", "Referee Criteria") else ""
            result_line = f"Month {self.month}: {winner.name} def. {loser.name} by {method}{round_note} in {sport} ({sim.get('score', '-')})"
        sim.setdefault("log", []).append(f"Result: {result_line}")
        retired_after = []
        for fighter in (a, b):
            fighter.multi_sport_records = fighter.multi_sport_records or {}
            fighter.multi_sport_records[sport] = f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"
            self.add_fight_history_entry(fighter, result_line)
            fighter.last_fight = result_line
            self.stamp_last_fight_date(fighter)
            condition = sim.get("condition", {}).get(fighter.name, {})
            exertion = max(0, 100 - condition.get("stamina", 70))
            damage_load = condition.get("damage", 0) + condition.get("body", 0) * 0.6 + condition.get("leg", 0) * 0.7
            lost = bool(loser is fighter)
            fatigue_gain = 10 + round(exertion * 0.34 + damage_load * 0.22) + (4 if lost else 0) + random.randint(0, 7)
            fighter.fatigue = min(100, fighter.fatigue + fatigue_gain)
            recovery_method = "TKO" if method == "KO/TKO" else method
            self.set_post_fight_recovery(fighter, recovery_method, lost=lost)
            recurrence = getattr(fighter, "serious_injury_recurrence", 0)
            injury_chance = 0.018 + fighter.injury_proneness / 1700 + damage_load / 520 + condition.get("cuts", 0) / 380 + recurrence / 1500
            if lost and method in ("KO", "KO/TKO", "Technical Fall", "Pin", "Submission"):
                injury_chance += 0.018
            if random.random() < min(0.24, injury_chance):
                fighter.injured = max(fighter.injured, random.randint(1, 3))
                fighter.available_week = max(getattr(fighter, "available_week", 0), self.calendar_week_index() + fighter.injured * 4)
            serious_chance = 0.00045 + fighter.injury_proneness / 110_000 + max(0, fighter.age - 34) / 20_000 + recurrence / 30_000
            if lost and method in ("KO", "KO/TKO", "Technical Fall"):
                serious_chance += 0.0012
            if random.random() < serious_chance:
                self.apply_serious_injury(fighter, f"{sport} bout")
            self.develop_after_combat_sport_bout(sport, fighter, won=(winner is fighter), finished=method not in ("Decision", "Majority Decision", "Points", "Draw", "Referee Criteria"))
            self.clear_combat_sport_preparation(fighter)
            if self.retire_combat_sport_after_final_fight(sport, world, fighter, state):
                retired_after.append(fighter)
        self.record_combat_sport_season_result(state, a, b, winner, method, title_key if effective_title else "", previous_champion)
        for fighter in retired_after:
            self.consider_combat_sport_hall_of_fame(sport, world, fighter, state)
        return {"a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id, "a_record": a_record_before, "b_record": b_record_before, "a_rating": a_rating_before, "b_rating": b_rating_before, "winner": winner.name if winner else "Draw", "method": method, "round": sim.get("round"), "score": sim.get("score", "-"), "weight": self.combat_sport_competition_class(sport, a), "title_key": title_key if effective_title else "", "title": effective_title, "scheduled_title": title, "result": result_line, "log": sim.get("log", []), "condition": sim.get("condition", {}), "start_stamina": sim.get("start_stamina", {}), "readiness": sim.get("readiness", {})}

    def create_combat_sport_guest_opponent(self, sport, fighter, employer, reserved_names=None):
        """Supply a credible independent opponent for an isolated sport athlete."""
        guest = self.create_generated_fighter(
            5, max(12, fighter.popularity), max(34, fighter.overall - 6), min(94, fighter.overall + 6),
            weight=fighter.weight, gender=fighter.gender, region=fighter.region,
        )
        reserved = set(reserved_names or ()) | self.active_fighter_names()
        self.avoid_name_collision(guest, reserved)
        guest.primary_discipline = sport
        guest.sport_employer = f"Independent {sport} Circuit"
        guest.contract_type = "One-Fight Independent"
        guest.popularity = max(5, min(fighter.popularity, guest.popularity))
        target_rating = max(30, min(96, fighter.overall + random.randint(-5, 4)))
        for field in ("striking", "wrestling", "grappling", "cardio", "chin"):
            setattr(guest, field, max(25, min(99, target_rating + random.randint(-4, 4))))
        guest.potential = max(guest.overall, min(98, guest.overall + random.randint(0, 8)))
        guest.fatigue = random.randint(0, 16)
        guest.injured = 0
        guest.available_week = 0
        guest.sport_weight_class = self.combat_sport_competition_class(sport, fighter)
        self.assign_combat_sport_weight(sport, guest, guest.sport_weight_class, reset_walk_weight=True)
        return guest

    def build_combat_sport_card(self, sport, world, employer, player_owned=False, target_bouts=6, champion_name=None):
        ranked = self.refresh_combat_sport_rankings(sport, world, employer=employer)
        state = self.ensure_combat_sport_circuit_state(sport, world, employer, player_owned)
        current_week = self.calendar_week_index()
        available = [
            fighter for fighter in ranked
            if (fighter.fatigue < 55 or (fighter.retirement_pending and fighter.fatigue < 66))
            and not fighter.injured and getattr(fighter, "available_week", 0) <= current_week
        ]
        if not available:
            return []
        card_strategy = self.combat_sport_card_strategy(sport, world, employer, player_owned)
        if not player_owned and len(available) > target_bouts * 2:
            target_bouts = min(14, max(target_bouts, len(available) // 4))
        if card_strategy == "Deep Roster":
            target_bouts = min(14, max(target_bouts, 10))
        elif card_strategy == "Champion Showcase":
            target_bouts = min(target_bouts, 8)
        used = set()
        bouts = []
        available_by_division = {}
        for fighter in available:
            available_by_division.setdefault(self.combat_sport_division_key(fighter, sport), []).append(fighter)
        title_opportunities = []
        for key, names in state.get("rankings_by_division", {}).items():
            eligible = [fighter for fighter in available_by_division.get(key, []) if fighter.name in names]
            if len(eligible) < 2:
                continue
            champion = next((fighter for fighter in eligible if fighter.name == state.get("titles", {}).get(key, "")), None)
            if champion and card_strategy == "Prospect Rotation":
                continue
            inactivity = self.combat_sport_inactivity_months(champion) if champion else 99
            title_opportunities.append((0 if not champion else 1, -inactivity, key, champion, eligible))
        title_opportunities.sort(key=lambda item: (item[0], item[1], item[2]))
        max_title_bouts = 2 if card_strategy == "Title Focus" else 1
        for _vacancy, _inactivity, key, champion, eligible in title_opportunities[:max_title_bouts]:
            if champion:
                challengers = [fighter for fighter in eligible if fighter is not champion and fighter.name not in used]
                challenger = min(challengers[:8], key=lambda fighter: abs(self.combat_sport_rating(fighter, sport) - self.combat_sport_rating(champion, sport))) if challengers else None
                if not challenger:
                    continue
                a, b = champion, challenger
                reason = f"{card_strategy}: {self.combat_sport_division_label(key)} champion vs closest ranked contender"
            else:
                eligible = [fighter for fighter in eligible if fighter.name not in used]
                if len(eligible) < 2:
                    continue
                a, b = eligible[0], eligible[1]
                reason = f"Vacant {self.combat_sport_division_label(key)} championship: top two available contenders"
            bouts.append({"a": a, "b": b, "title": True, "title_key": key, "main": not bouts, "booking_reason": reason})
            used.update([a.name, b.name])

        band_size = max(6, len(available) // 4)
        card_pool = []
        bands = [
            available[:band_size],
            available[band_size:band_size * 2],
            available[band_size * 2:band_size * 3],
            available[band_size * 3:],
            [fighter for fighter in available if fighter.age <= 27 or fighter.potential >= self.combat_sport_display_rating(fighter, sport) + 7],
            sorted(available, key=lambda fighter: (self.combat_sport_inactivity_months(fighter), fighter.fatigue), reverse=True)[:max(8, len(available) // 3)],
        ]
        for band in bands:
            band = [fighter for fighter in band if fighter.name not in used]
            random.shuffle(band)
            card_pool.extend(band[:max(2, target_bouts // 2)])
        card_pool = sorted(
            dict((fighter.name, fighter) for fighter in card_pool if fighter.name not in used).values(),
            key=lambda fighter: (fighter.retirement_pending, self.combat_sport_inactivity_months(fighter) if card_strategy == "Deep Roster" else 0, fighter.age <= 27, fighter.potential - self.combat_sport_display_rating(fighter, sport)),
            reverse=True,
        )
        fallback_pool = sorted(
            [fighter for fighter in available if fighter.name not in used],
            key=lambda fighter: (fighter.retirement_pending, self.combat_sport_inactivity_months(fighter), random.random()),
            reverse=True,
        )
        for fighter in card_pool + fallback_pool:
            if len(bouts) >= target_bouts or fighter.name in used:
                continue
            fighter_division = self.combat_sport_competition_class(sport, fighter)
            opponent_pool = [
                other for other in available
                if other.name not in used and other is not fighter
                and other.gender == fighter.gender
                and self.combat_sport_competition_class(sport, other) == fighter_division
                and abs(self.combat_sport_rating(other, sport) - self.combat_sport_rating(fighter, sport)) <= (30 if fighter.age <= 25 else 44)
            ]
            if not opponent_pool:
                ladder = [label for label, _limit in self.combat_sport_weight_ladder(sport, fighter.gender)]
                try:
                    fighter_weight_index = ladder.index(fighter_division)
                except ValueError:
                    fighter_weight_index = -99
                opponent_pool = [
                    other for other in available
                    if other.name not in used and other is not fighter
                    and other.gender == fighter.gender
                    and self.combat_sport_competition_class(sport, other) in ladder
                    and abs(ladder.index(self.combat_sport_competition_class(sport, other)) - fighter_weight_index) == 1
                    and abs(self.combat_sport_rating(other, sport) - self.combat_sport_rating(fighter, sport)) <= (30 if fighter.age <= 25 else 44)
                ]
            if not opponent_pool and self.combat_sport_inactivity_months(fighter) >= 8:
                opponent_pool = [
                    other for other in available
                    if other.name not in used and other is not fighter
                    and other.gender == fighter.gender
                    and self.combat_sport_competition_class(sport, other) == fighter_division
                    and abs(self.combat_sport_rating(other, sport) - self.combat_sport_rating(fighter, sport)) <= 60
                ]
            if not opponent_pool:
                opponent = self.create_combat_sport_guest_opponent(sport, fighter, employer, used)
                bouts.append({"a": fighter, "b": opponent, "title": False, "title_key": "", "main": not bouts, "booking_reason": "Independent opponent for an isolated division"})
                used.update([fighter.name, opponent.name])
                continue
            opponent = min(opponent_pool, key=lambda other: (
                abs(self.combat_sport_rating(other, sport) - self.combat_sport_rating(fighter, sport)),
                -self.combat_sport_inactivity_months(other),
                abs(other.record_w + other.record_l - fighter.record_w - fighter.record_l),
            ))
            reason = "Activity rotation" if self.combat_sport_inactivity_months(fighter) >= 5 or self.combat_sport_inactivity_months(opponent) >= 5 else "Style/ranking matchup"
            opponent_division = self.combat_sport_competition_class(sport, opponent)
            if fighter_division != opponent_division:
                reason = f"Adjacent-division catchweight: {fighter_division}/{opponent_division}"
            if card_strategy == "Prospect Rotation" and (fighter.age <= 27 or opponent.age <= 27):
                reason = "Prospect rotation"
            bouts.append({"a": fighter, "b": opponent, "title": False, "title_key": "", "main": not bouts, "booking_reason": reason})
            used.update([fighter.name, opponent.name])
        return bouts

    def combat_sport_card_day(self, sport, world, employer):
        """The weekday a boxing, kickboxing, Muay Thai, wrestling or BJJ card runs.

        Same intent as ai_card_day: a settled weekend slot per circuit rather
        than a value that wanders across the week from card to card.
        """
        label = f"{sport}{(world or {}).get('promotion', '')}{employer or ''}"
        seed = sum(ord(char) for char in str(label)) + self.month
        return (6, 6, 5, 7, 6, 5, 6, 4)[seed % 8]

    def run_combat_sport_card(self, sport, world, employer, player_owned=False, target_bouts=6, bouts=None, event_name=""):
        division = getattr(self, "player_combat_divisions", {}).get(sport) if player_owned else None
        if player_owned and division and bouts is None:
            target_bouts = {"Prospect Builder": 6, "Star Showcase": 4, "Title Focus": 5}.get(division.get("strategy", "Balanced"), target_bouts)
        state = self.ensure_combat_sport_circuit_state(sport, world, employer, player_owned)
        # Other-sport cards run on a weekday too, so their bouts are dated the
        # same way MMA ones are instead of all landing on a Monday.
        self._active_card_day = self.combat_sport_card_day(sport, world, employer)
        bouts = bouts if bouts is not None else self.build_combat_sport_card(sport, world, employer, player_owned=player_owned, target_bouts=target_bouts)
        if not bouts:
            self._active_card_day = None
            return None
        event_no = world.get("events", 0) + 1
        world["events"] = event_no
        promotion = (division or {}).get("promotion_name", f"{self.player_company_name} {sport}") if player_owned else world.get("promotion", employer)
        results = [self.apply_combat_sport_result(
            sport, world, bout["a"], bout["b"], title=bout.get("title", False),
            player_owned=player_owned, title_key=bout.get("title_key", ""), employer=employer,
        ) for bout in bouts]
        title_result = next((item for item in results if item.get("title")), None)
        finishes = sum(1 for item in results if item.get("method") not in ("Decision", "Points", "Draw"))
        event_label = event_name.strip() or f"{promotion} {sport} Card {event_no}"
        headline = f"Month {self.month}: {event_label} was headlined by {results[0]['result']}."
        strategy = self.combat_sport_card_strategy(sport, world, employer, player_owned)
        recap = f"{len(results)} bouts | {finishes} finish(es) | Strategy: {strategy}"
        if title_result:
            recap += f" | Title: {title_result['result']}"
        fight_logs = [{
            "heading": f"{'TITLE' if item.get('title') else 'BOUT'}: {item['a']} vs {item['b']}",
            "fight": f"{item['a']} vs {item['b']}",
            "label": f"{sport} {self.combat_sport_division_label(item.get('title_key')) + ' Title Bout' if item.get('title') else 'Bout'}",
            "sport": sport,
            "a": item["a"],
            "b": item["b"],
            "a_id": item.get("a_id", ""),
            "b_id": item.get("b_id", ""),
            "a_record": item.get("a_record", ""),
            "b_record": item.get("b_record", ""),
            "a_rating": item.get("a_rating", {}),
            "b_rating": item.get("b_rating", {}),
            "a_start_gas": item.get("start_stamina", {}).get(item["a"], 100),
            "b_start_gas": item.get("start_stamina", {}).get(item["b"], 100),
            "a_condition": item.get("condition", {}).get(item["a"], {}),
            "b_condition": item.get("condition", {}).get(item["b"], {}),
            "readiness": item.get("readiness", {}),
            "weight": item.get("weight", next((fighter.weight for fighter in world.get("roster", []) if fighter.name == item["a"]), "")),
            "method": item.get("method", ""),
            "winner": item.get("winner", ""),
            "draw": item.get("winner") == "Draw" or item.get("method") == "Draw",
            "round": item.get("round"),
            "score": item.get("score", "-"),
            "result": item.get("result", ""),
            "lines": item.get("log", []),
        } for item in results]
        card = {"month": self.month, "week": self.week, "sport": sport, "promotion": promotion, "event": event_no, "event_name": event_label, "results": results, "fight_logs": fight_logs, "headline": headline, "recap": recap, "strategy": strategy, "bouts": [{"a": bout["a"].name, "b": bout["b"].name, "title": bout.get("title", False), "title_key": bout.get("title_key", ""), "reason": bout.get("booking_reason", "Sport matchmaking")} for bout in bouts]}
        world["event_history"] = ([headline] + world.get("event_history", []))[:80]
        world["media"] = ([headline] + world.get("media", []))[:24]
        self.refresh_combat_sport_rankings(sport, world, employer=employer)
        if player_owned:
            divisions = getattr(self, "player_combat_divisions", {})
            division = divisions.get(sport)
            if division:
                revenue = sum(max(1200, fighter.popularity * 150 + fighter.overall * 60) for bout in bouts for fighter in (bout["a"], bout["b"]))
                cost = 18000 + len(bouts) * 2200 + sum(max(900, fighter.popularity * 95) for bout in bouts for fighter in (bout["a"], bout["b"]))
                # Growing a child division requires production, promotion and
                # athlete-development reinvestment rather than converting the
                # whole card surplus directly into parent-company cash.
                cost += round(max(0, revenue - cost) * 0.45)
                profit = revenue - cost
                card["finance"] = {"revenue": revenue, "cost": cost, "profit": profit}
                division["events"] = ([card] + division.get("events", []))[:50]
                division["last_card_month"] = self.month
                division["last_card_summary"] = f"{recap} | Revenue ${revenue:,} | Cost ${cost:,} | Profit ${profit:,}"
                division["revenue_total"] = division.get("revenue_total", 0) + revenue
                division["cost_total"] = division.get("cost_total", 0) + cost
                division["profit_total"] = division.get("profit_total", 0) + profit
                division["reputation"] = max(10, min(99, division.get("reputation", self.company_pop) + (1 if title_result or finishes >= 3 else 0)))
                stability_target = max(58, min(90, round(50 + division.get("reputation", self.company_pop) * 0.4)))
                division["stability"] = max(5, min(99, division.get("stability", 60) + (1 if profit >= 0 and division.get("stability", 60) < stability_target else (-2 if profit < 0 else 0))))
                division.setdefault("finance_history", []).insert(0, {"month": self.month, "revenue": revenue, "cost": cost, "profit": profit, "cash": self.cash + profit})
                division["finance_history"] = division["finance_history"][:120]
                self.refresh_combat_sport_rankings(sport, world, employer=employer, division=division)
                self.cash = max(0, self.cash + profit)
                self.record_finance_transaction(f"{sport} child division card", revenue=revenue, costs=cost)
                self.news.insert(0, headline)
        else:
            reputation = state.get("reputation", 62)
            star_value = sum(max(1200, fighter.popularity * 210 + fighter.overall * 75) for bout in bouts for fighter in (bout["a"], bout["b"]))
            revenue = round((32_000 + star_value + reputation * 1_450) * random.uniform(0.82, 1.18))
            cost = 42_000 + len(bouts) * 4_500 + sum(max(1_200, fighter.popularity * 105 + fighter.overall * 42) for bout in bouts for fighter in (bout["a"], bout["b"]))
            cost += round(max(0, revenue - cost) * 0.62)
            profit = revenue - cost
            state["cash"] = state.get("cash", 0) + profit
            state["reputation"] = max(10, min(99, reputation + (1 if title_result or finishes >= 3 else 0) - (1 if finishes == 0 and random.random() < 0.3 else 0)))
            stability_target = max(58, min(88, round(50 + state["reputation"] * 0.38)))
            state["stability"] = max(5, min(99, state.get("stability", 70) + (1 if profit >= 0 and state.get("stability", 70) < stability_target else (-2 if profit < 0 else 0))))
            card["finance"] = {"revenue": revenue, "cost": cost, "profit": profit, "cash_after": state["cash"]}
            state.setdefault("finance_history", []).insert(0, {"month": self.month, "revenue": revenue, "cost": cost, "profit": profit, "cash": state["cash"]})
            state["finance_history"] = state["finance_history"][:120]
            if random.random() < 0.35:
                self.record_world_story("Combat Sports", headline, "\n".join(item["result"] for item in results[:6]), [promotion], [results[0]["a"], results[0]["b"]], importance=2)
        self.archive_result_record({
            "date": f"Month {self.month} Week {self.week}",
            "company": promotion,
            "event": event_label,
            "summary": recap,
            "fights": len(results),
            "gate": f"${card.get('finance', {}).get('revenue', 0):,}",
            "profit": f"${card.get('finance', {}).get('profit', 0):,}",
            "log": [headline, recap, ""] + [item["result"] for item in results],
            "fight_logs": fight_logs,
            "finance": card.get("finance", {"ticket_revenue": 0, "total_revenue": 0, "total_expense": 0, "profit": 0}),
        })
        self._active_card_day = None
        return card

    def process_player_combat_auto_card(self, sport, world):
        """Run an opt-in player child-promotion card when its minimum is viable."""
        division = getattr(self, "player_combat_divisions", {}).get(sport)
        if not division:
            return None
        division.setdefault("auto_cards", False)
        division["auto_card_min_bouts"] = max(1, min(14, int(division.get("auto_card_min_bouts", 5) or 5)))
        if "last_card_month" not in division:
            division["last_card_month"] = max((int(card.get("month", 0) or 0) for card in division.get("events", [])), default=0)
        if not division.get("auto_cards", False):
            division["auto_card_status"] = "Off - manual cards only."
            return None
        if int(division.get("last_card_month", 0) or 0) >= self.month:
            division["auto_card_status"] = f"Already held a card in {self.format_game_date(self.month, self.week, include_week=False)}."
            return None
        if division.get("booked_bouts"):
            division["auto_card_status"] = "Waiting - a manually booked card is in progress."
            return None

        required = division["auto_card_min_bouts"]
        strategy_target = {"Prospect Builder": 6, "Star Showcase": 4, "Title Focus": 5}.get(division.get("strategy", "Balanced"), 6)
        target = max(required, strategy_target)
        bouts = self.build_combat_sport_card(
            sport, world, self.player_company_name, player_owned=True, target_bouts=target,
        )
        if len(bouts) < required:
            ready = len({bout["a"].fighter_id for bout in bouts} | {bout["b"].fighter_id for bout in bouts if bout["b"] in world.get("roster", [])})
            division["auto_card_status"] = f"Waiting - only {len(bouts)} of {required} required bouts can be built ({ready} roster athletes ready)."
            return None
        card = self.run_combat_sport_card(
            sport, world, self.player_company_name, player_owned=True, bouts=bouts,
        )
        if card:
            division["auto_card_status"] = f"Ran {len(card.get('results', []))} bouts in {self.format_game_date(self.month, self.week, include_week=False)}."
        return card

    def develop_combat_sport_roster(self, sport, roster):
        year = str(2026 + (self.month - 1) // 12)
        for fighter in roster:
            if fighter.retired:
                continue
            rehabbing = fighter.injured > 0
            if fighter.injured:
                fighter.injured -= 1
            fighter.fatigue = max(0, fighter.fatigue - random.randint(8, 18))
            if not rehabbing and random.random() < self.combat_sport_monthly_growth_chance(fighter, sport):
                stage = self.combat_sport_development_stage(fighter, sport)
                gap = max(0, min(99, fighter.potential) - self.combat_sport_display_rating(fighter, sport))
                dedication = self.ds(fighter, "dedication", fighter.professionalism)
                prodigy_chance = 0.04 + max(0, gap - 14) / 150 + max(0, dedication - 78) / 300
                amount = 2 if stage == "Pre-prime" and random.random() < min(0.24, prodigy_chance) else 1
                self.adjust_combat_sport_skill_bundle(fighter, sport, amount, f"{stage} monthly {sport} training")
            decline_chance = self.combat_sport_monthly_decline_chance(fighter, sport)
            if random.random() < decline_chance:
                years_over = fighter.age - self.combat_sport_effective_prime_end(fighter, sport)
                amount = -2 if years_over >= 5 and random.random() < min(0.62, 0.18 + years_over * 0.06) else -1
                self.adjust_combat_sport_skill_bundle(fighter, sport, amount, "Age, mileage and recovery decline", decline=True)
            fighter.annual_overalls = fighter.annual_overalls or {}
            fighter.annual_overalls[year] = max(fighter.annual_overalls.get(year, 0), fighter.overall)
            self.update_fighter_peak_overall(fighter)
            self.record_combat_sport_rating_snapshot(fighter, sport)
            fighter.rank_score = self.rank_value(fighter)

    def review_combat_sport_retirements(self, sport, world):
        """Stage retirement reviews while guaranteeing a final booked contest."""
        marked = 0
        review_age = {
            "Boxing": 38,
            "Kickboxing": 36,
            "Muay Thai": 35,
            "Wrestling": 35,
            "Brazilian Jiu-Jitsu": 39,
        }.get(sport, 38)
        for fighter in self.combat_sport_roster(sport):
            if fighter.retirement_pending or fighter.age < review_age:
                continue
            annual_review_month = sum(ord(char) for char in fighter.name) % 12 + 1
            calendar_month = (self.month - 1) % 12 + 1
            if fighter.age < 50 and calendar_month != annual_review_month:
                continue
            losses = fighter.record_l / max(1, fighter.record_w + fighter.record_l + fighter.record_d)
            age_pressure = max(0, fighter.age - self.combat_sport_effective_prime_end(fighter, sport)) * 0.07
            chance = 1.0 if fighter.age >= 50 else min(0.82, 0.08 + age_pressure + losses * 0.12)
            if random.random() < chance:
                self.mark_retirement_fight_required(fighter, f"{sport} career review at age {fighter.age}")
                fighter.available_week = min(getattr(fighter, "available_week", 0), self.calendar_week_index())
                marked += 1
                if fighter.sport_employer == self.player_company_name:
                    self.inbox.append({
                        "subject": f"{sport} Farewell Fight Required",
                        "body": f"{fighter.name} plans to retire. Book them on your next {sport} card to complete their career.",
                        "type": "Combat Sports", "fighter": fighter.name, "resolved": False,
                    })
        return marked

    def generate_combat_sport_prospect(self, sport, world, age_range=None, gender=None, division_label=None):
        promotion = world.get("promotion", "")
        target_skill = {
            "Boxing": ("striking", "power"),
            "Kickboxing": ("striking", "cardio"),
            "Muay Thai": ("striking", "toughness"),
            "Wrestling": ("wrestling", "ground_control"),
            "Brazilian Jiu-Jitsu": ("grappling", "submissions"),
        }.get(sport, ("striking", "cardio"))
        fighter = self.create_generated_fighter(3, 18, 38, 62, region=random.choice(REGION_GENERATION_POOL), gender=gender)
        reserved = self.active_fighter_names()
        for sport_world in getattr(self, "combat_sport_worlds", {}).values():
            reserved.update(candidate.name for candidate in sport_world.get("roster", []))
        for player_division in getattr(self, "player_combat_divisions", {}).values():
            for entry in player_division.get("signable_youth", []):
                data = entry.get("fighter", entry) if isinstance(entry, dict) else {}
                if isinstance(data, dict) and data.get("name"):
                    reserved.add(data["name"])
        self.avoid_name_collision(fighter, reserved)
        fighter.age = random.randint(*(age_range or (18, 23)))
        fighter.record_w = random.randint(0, 2 if age_range else 5)
        fighter.record_l = random.randint(0, 1 if age_range else 2)
        fighter.record_d = 0
        fighter.primary_discipline = sport
        fighter.sport_employer = promotion
        fighter.contract_type = f"{sport} Development Deal"
        fighter.exclusive = True
        self.stamp_last_fight_date(fighter)
        ladder = self.combat_sport_weight_ladder(sport, fighter.gender)
        counts = {
            label: sum(
                1 for candidate in world.get("roster", [])
                if not candidate.retired and candidate.gender == fighter.gender
                and self.combat_sport_competition_class(sport, candidate) == label
            )
            for label, _limit in ladder
        }
        if ladder:
            labels = [label for label, _limit in ladder]
            if division_label in labels:
                division = division_label
            else:
                weights = [1.0 / (1 + counts.get(label, 0)) for label in labels]
                division = random.choices(labels, weights=weights, k=1)[0]
            self.assign_combat_sport_weight(sport, fighter, division, reset_walk_weight=True)
        # The original worlds are deliberately packed with all-time names, but
        # their successors must still enter as credible national prospects. A
        # steady diet of 40-rated replacements made every circuit collapse by
        # roughly forty percent once the legends retired.
        if random.random() < 0.08:
            native_rating = random.randint(76, 86)
        elif random.random() < 0.30:
            native_rating = random.randint(66, 77)
        else:
            native_rating = random.randint(56, 69)
        self.ensure_detailed_skills(fighter)
        profile = self.combat_sport_development_profile(sport)
        for key in profile["growth"]:
            fighter.detailed_skills[key] = max(35, min(94, native_rating + random.randint(-7, 7)))
        primary = "striking" if sport in ("Boxing", "Kickboxing", "Muay Thai") else "wrestling" if sport == "Wrestling" else "grappling"
        setattr(fighter, primary, native_rating)
        if sport in ("Boxing", "Kickboxing", "Muay Thai"):
            fighter.power = max(35, min(94, native_rating + random.randint(-6, 7)))
            fighter.chin = max(35, min(94, native_rating + random.randint(-7, 6)))
        elif sport == "Wrestling":
            fighter.ground_control = max(35, min(94, native_rating + random.randint(-5, 7)))
            fighter.toughness = max(35, min(94, native_rating + random.randint(-5, 6)))
        else:
            fighter.submissions = max(35, min(96, native_rating + random.randint(-4, 8)))
            fighter.submission_defence = max(35, min(95, native_rating + random.randint(-5, 7)))
            fighter.ground_control = max(35, min(94, native_rating + random.randint(-6, 6)))
        fighter.cardio = max(35, min(94, native_rating + random.randint(-6, 6)))
        fighter.fight_iq = max(35, min(96, native_rating + random.randint(-5, 8)))
        for field in target_skill:
            setattr(fighter, field, min(96, max(getattr(fighter, field, 45), native_rating + random.randint(-3, 6))))
        prime_ranges = {
            "Boxing": ((26, 28), (34, 37)),
            "Kickboxing": ((24, 27), (32, 35)),
            "Muay Thai": ((23, 26), (31, 34)),
            "Wrestling": ((23, 26), (30, 34)),
            "Brazilian Jiu-Jitsu": ((25, 28), (35, 39)),
        }
        start_range, end_range = prime_ranges.get(sport, ((24, 27), (33, 36)))
        fighter.prime_start = random.randint(*start_range)
        fighter.prime_end = max(fighter.prime_start + 5, random.randint(*end_range))
        if sport == "Brazilian Jiu-Jitsu" or random.random() < 0.18:
            fighter.career_archetype = "Durable Career"
        fighter.potential = min(98, max(fighter.overall, native_rating + random.randint(8, 20)))
        fighter.multi_sport_records = {sport: fighter.record}
        fighter.sport_rating_history = {sport: {str(self.month): self.combat_sport_display_rating(fighter, sport)}}
        fighter.sport_development_log = []
        return fighter

    def player_combat_signable_youth(self, sport):
        """Return player-only youth recruits without exposing them to the sport ladder."""
        division = getattr(self, "player_combat_divisions", {}).get(sport)
        if not division:
            return []
        recruits = []
        retained = []
        for entry in division.get("signable_youth", []):
            if isinstance(entry, Fighter):
                entry = {"fighter": asdict(entry), "created_month": self.month}
            elif isinstance(entry, dict) and "fighter" not in entry:
                entry = {"fighter": dict(entry), "created_month": self.month}
            if not isinstance(entry, dict) or not isinstance(entry.get("fighter"), dict):
                continue
            created_month = max(1, int(entry.get("created_month", self.month) or self.month))
            data = dict(entry["fighter"])
            starting_age = max(16, int(entry.get("starting_age", data.get("age", 18)) or 18))
            data["age"] = starting_age + max(0, self.month - created_month) // 12
            # Unsigned recruits eventually leave this private market rather than
            # accumulating forever. They never join the simulated sport ladder.
            if data["age"] > 22 or self.month - created_month > 48:
                continue
            try:
                fighter = Fighter(**data)
            except (TypeError, ValueError):
                continue
            entry = {"fighter": asdict(fighter), "created_month": created_month, "starting_age": starting_age}
            retained.append(entry)
            recruits.append(fighter)
        division["signable_youth"] = retained
        return recruits

    def ensure_player_combat_signable_depth(self, sport, world, force=False):
        """Build a paced player-only youth market outside the simulated ladder."""
        division = getattr(self, "player_combat_divisions", {}).get(sport)
        if not division:
            return 0
        last_intake = int(division.get("last_youth_market_month", -99) or -99)
        if not force and self.month - last_intake < 2:
            return 0
        recruits = self.player_combat_signable_youth(sport)
        deficits = []
        for gender in ("Male", "Female"):
            for label, _limit in self.combat_sport_weight_ladder(sport, gender):
                count = sum(
                    1 for fighter in recruits
                    if not fighter.retired and fighter.age < 20
                    and fighter.gender == gender
                    and self.combat_sport_competition_class(sport, fighter) == label
                )
                deficits.extend((count, random.random(), gender, label) for _ in range(max(0, 4 - count)))
        deficits.sort(key=lambda item: (item[0], item[1]))
        additions = 0
        for _count, _tie, gender, label in deficits[:12]:
            prospect = self.generate_combat_sport_prospect(
                sport, world, age_range=(18, 19), gender=gender, division_label=label,
            )
            prospect.sport_employer = ""
            prospect.contract_type = f"Unsigned {sport} Prospect"
            prospect.exclusive = False
            division.setdefault("signable_youth", []).append({
                "fighter": asdict(prospect),
                "created_month": self.month,
                "starting_age": prospect.age,
            })
            additions += 1
        division["last_youth_market_month"] = self.month
        if additions:
            note = (f"Your {sport} recruitment network found {additions} under-20 athletes "
                    f"for thin weight divisions. They remain outside the competitive ladder until signed.")
            division["last_card_summary"] = note
        return additions

    def sign_player_combat_youth(self, sport, fighter_id):
        """Move one private-market recruit into the player's active sport roster."""
        division = getattr(self, "player_combat_divisions", {}).get(sport)
        world = getattr(self, "combat_sport_worlds", {}).get(sport)
        if not division or not world:
            return False, "That sport division is not open.", None
        recruits = {fighter.fighter_id: fighter for fighter in self.player_combat_signable_youth(sport)}
        fighter = recruits.get(fighter_id)
        if not fighter:
            return False, "That recruit is no longer available.", None
        cost = max(8000, fighter.popularity * 450 + round(self.combat_sport_display_rating(fighter, sport)) * 260)
        if self.cash < cost:
            return False, f"Need ${cost:,} to sign {fighter.name}.", None
        self.cash -= cost
        self.record_finance_transaction(f"Combat-sport youth signing: {fighter.name}", costs=cost)
        division["signable_youth"] = [
            entry for entry in division.get("signable_youth", [])
            if str((entry.get("fighter", entry) if isinstance(entry, dict) else {}).get("fighter_id", "")) != fighter_id
        ]
        fighter.sport_employer = self.player_company_name
        fighter.contract_type = f"{sport} Player Deal"
        fighter.exclusive = True
        fighter.fight_history = fighter.fight_history or []
        fighter.fight_history.insert(0, f"Month {self.month}: Signed with {self.player_company_name}'s {sport} division.")
        world.setdefault("roster", []).append(fighter)
        division["roster"] = list(dict.fromkeys(division.get("roster", []) + [fighter.name]))
        note = f"{self.player_company_name} signed {fighter.name} to its {sport} division for ${cost:,}."
        self.news.insert(0, note)
        return True, note, fighter

    def replenish_combat_sport_world(self, sport, world):
        promotion = world.get("promotion", "")
        active = self.combat_sport_roster(sport, promotion)
        target = self.combat_sport_roster_target(sport, world)
        if len(active) >= target:
            return 0
        additions = min(3, max(1, target - len(active)))
        for _ in range(additions):
            prospect = self.generate_combat_sport_prospect(sport, world)
            world.setdefault("roster", []).append(prospect)
            world.setdefault("prospects", []).insert(0, prospect.name)
        world["prospects"] = world.get("prospects", [])[:80]
        world.setdefault("media", []).insert(0, f"{world.get('promotion', sport)} signed {additions} new {sport} prospect(s) to replenish its development ranks.")
        return additions

    def run_combat_sport_year_awards(self, sport, world, year, player_owned=False):
        employer = self.player_company_name if player_owned else world.get("promotion", "")
        state = self.ensure_combat_sport_circuit_state(sport, world, employer, player_owned)
        if state.get("last_awards_year", 0) >= year:
            return None
        stats = state.get("season_stats", {})
        roster_by_name = {fighter.name: fighter for fighter in world.get("roster", [])}
        eligible = [(name, row) for name, row in stats.items() if row.get("bouts", 0)]
        if not eligible:
            state["last_awards_year"] = year
            return None
        athlete = max(eligible, key=lambda item: (item[1].get("score", 0), item[1].get("wins", 0)))[0]
        prospects = [(name, row) for name, row in eligible if roster_by_name.get(name) and roster_by_name[name].age <= 25]
        veteran = [(name, row) for name, row in eligible if roster_by_name.get(name) and roster_by_name[name].age >= 34]
        finisher = max(eligible, key=lambda item: (item[1].get("finishes", 0), item[1].get("wins", 0)))[0]
        award = {
            "year": year,
            "athlete": athlete,
            "prospect": max(prospects, key=lambda item: item[1].get("score", 0))[0] if prospects else "No eligible prospect",
            "veteran": max(veteran, key=lambda item: item[1].get("score", 0))[0] if veteran else "No eligible veteran",
            "finisher": finisher,
            "summary": f"{year} {sport} Awards — Athlete: {athlete}; Prospect: {max(prospects, key=lambda item: item[1].get('score', 0))[0] if prospects else 'None'}; Finisher: {finisher}.",
        }
        state.setdefault("awards", []).insert(0, award)
        state["awards"] = state["awards"][:60]
        state["last_awards_year"] = year
        state["season_stats"] = {}
        world.setdefault("media", []).insert(0, award["summary"])
        company = self.player_company_name if player_owned else world.get("promotion", "")
        self.record_world_story("Combat Sports Awards", award["summary"], f"Veteran award: {award['veteran']}.", [company], [athlete, finisher], 2)
        return award

    def update_combat_sport_business_strategy(self, sport, world):
        cash = world.get("cash", 0)
        stability = world.get("stability", 70)
        if cash < -1_000_000:
            injection = 2_250_000
            world["cash"] = cash + injection
            world["stability"] = max(18, stability - 14)
            world["reputation"] = max(15, world.get("reputation", 60) - 7)
            world["strategy"] = "Prospect Rotation"
            story = f"{world.get('promotion', sport)} received a ${injection:,} federation survival injection and shifted toward lower-cost prospects."
            world.setdefault("media", []).insert(0, story)
            self.record_world_story("Combat Sports Finance", story, "The circuit survives, but its reputation and stability have fallen.", [world.get("promotion", "")], [], 3)
        elif cash < 500_000 or stability < 35:
            world["strategy"] = "Prospect Rotation"
        elif cash > 8_000_000 and random.random() < 0.25:
            world["strategy"] = "Champion Showcase"
        return world.get("strategy", "Merit Ladder")

    def process_combat_sport_world(self, sport, world):
        """Process one complete circuit while allowing the UI to yield between sports."""
        promotion = world.get("promotion", "")
        roster = self.combat_sport_roster(sport)
        self.ensure_combat_sport_circuit_state(sport, world, promotion, False)
        self.develop_combat_sport_roster(sport, roster)
        self.review_combat_sport_retirements(sport, world)
        self.update_combat_sport_business_strategy(sport, world)
        self.refresh_combat_sport_rankings(sport, world, employer=promotion)
        show_chance = max(0.55, min(0.92, 0.68 + world.get("stability", 70) / 500 + world.get("reputation", 60) / 1000))
        if random.random() < show_chance:
            target = min(max(8, len(self.combat_sport_roster(sport, promotion)) // 5), 12)
            self.run_combat_sport_card(sport, world, promotion, player_owned=False, target_bouts=random.randint(max(6, target - 2), target))
        if (self.month - 1) % 12 == 0:
            self.run_combat_sport_year_awards(sport, world, self.current_year() - 1)
            if sport in getattr(self, "player_combat_divisions", {}):
                self.run_combat_sport_year_awards(sport, world, self.current_year() - 1, player_owned=True)
        self.replenish_combat_sport_world(sport, world)
        if sport in getattr(self, "player_combat_divisions", {}):
            self.ensure_player_combat_signable_depth(sport, world)
            self.process_player_combat_auto_card(sport, world)
        crossover_pressure = 0.003 + (0.002 if world.get("cash", 0) < 500_000 else 0)
        if random.random() < crossover_pressure:
            champions = set(world.get("titles", {}).values())
            candidates = [
                fighter for fighter in self.combat_sport_ranked(sport, promotion)[4:28]
                if fighter.age <= 34 and fighter.fatigue < 45 and not fighter.retirement_pending
                and fighter.name not in champions and self.combat_sport_display_rating(fighter, sport) >= 68
            ]
            if candidates:
                fighter = random.choices(candidates, weights=[max(1, candidate.popularity + candidate.potential - self.combat_sport_display_rating(candidate, sport)) for candidate in candidates], k=1)[0]
                fighter.sport_employer = ""
                fighter.crossover_history = (fighter.crossover_history or [])[-9:] + [f"Month {self.month}: Left {world['promotion']} to pursue MMA."]
                fighter.multi_sport_records = fighter.multi_sport_records or {}
                fighter.multi_sport_records[sport] = fighter.record
                fighter.multi_sport_records["MMA"] = "0-0-0"
                fighter.record_w = fighter.record_l = fighter.record_d = 0
                fighter.combat_background = sport
                fighter.primary_discipline = "MMA"
                fighter.contract_type = "Free Agent"
                fighter.contract_months = 0
                fighter.exclusive = False
                fighter.camp_focus = "Balanced"
                self.stamp_last_fight_date(fighter)
                world["roster"].remove(fighter)
                self.free_agents.append(fighter)
                headline = f"CROSSOVER: Former {sport} standout {fighter.name} has entered the MMA free-agent market."
                self.news.insert(0, headline)
                self.record_world_story("Crossover", headline, fighter.crossover_history[-1], [world["promotion"]], [fighter.name], importance=4)
        self.refresh_combat_sport_rankings(sport, world, employer=promotion)
        self.combat_sport_record_book(sport, world, promotion, False)

    def process_combat_sport_worlds(self):
        """Synchronous consumer retained for audits and non-UI callers."""
        worlds = getattr(self, "combat_sport_worlds", {}) or self.seed_combat_sport_worlds()
        self.combat_sport_worlds = worlds
        self.sync_gym_membership()
        for sport, world in worlds.items():
            self.process_combat_sport_world(sport, world)
        self.combat_sport_worlds = worlds

    def move_player_combat_athlete_to_mma(self, sport, fighter):
        """Transfer one player-owned child-sport athlete into the MMA roster."""
        world = getattr(self, "combat_sport_worlds", {}).get(sport)
        division = getattr(self, "player_combat_divisions", {}).get(sport)
        if not world or not division:
            return False, "That player-owned sport division is not available."
        if fighter not in world.get("roster", []) or fighter.sport_employer != self.player_company_name:
            return False, f"{fighter.name} is not contracted to your {sport} division."
        if fighter.retired or fighter.retirement_pending:
            return False, f"{fighter.name} cannot cross over while retired or awaiting a farewell fight."
        if any(candidate.fighter_id == fighter.fighter_id for candidate in self.roster):
            return False, f"{fighter.name} is already on your MMA roster."

        state = self.ensure_combat_sport_circuit_state(
            sport, world, self.player_company_name, player_owned=True,
        )
        for key, champion in list(state.get("titles", {}).items()):
            if champion != fighter.name:
                continue
            state["titles"][key] = ""
            state.setdefault("title_history", {}).setdefault(key, []).insert(0, {
                "month": self.month, "year": self.current_year(), "winner": "VACANT",
                "loser": "", "method": "Crossover to MMA", "previous_champion": fighter.name,
            })
        state["champion"] = next((name for name in state.get("titles", {}).values() if name), "")

        records = dict(fighter.multi_sport_records or {})
        records[sport] = f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"
        had_mma_record = "MMA" in records
        mma_record = str(records.get("MMA", "0-0-0") or "0-0-0")
        try:
            wins, losses, draws = [max(0, int(value)) for value in mma_record.split("-")[:3]]
        except (TypeError, ValueError):
            wins = losses = draws = 0
            mma_record = "0-0-0"
        records["MMA"] = f"{wins}-{losses}-{draws}"

        division["roster"] = [name for name in division.get("roster", []) if name != fighter.name]
        division["booked_bouts"] = [
            bout for bout in division.get("booked_bouts", [])
            if fighter.name not in (bout.get("a"), bout.get("b"))
        ]
        world["roster"].remove(fighter)
        world["prospects"] = [name for name in world.get("prospects", []) if name != fighter.name]

        fighter.multi_sport_records = records
        fighter.crossover_history = list(fighter.crossover_history or [])
        fighter.crossover_history.append(
            f"Month {self.month}: Moved from {self.player_company_name}'s {sport} division to its MMA roster."
        )
        fighter.record_w, fighter.record_l, fighter.record_d = wins, losses, draws
        if not had_mma_record:
            fighter.record_history_baseline_w = 0
            fighter.record_history_baseline_l = 0
            fighter.record_history_baseline_d = 0
        fighter.combat_background = sport
        fighter.primary_discipline = "MMA"
        fighter.sport_employer = ""
        fighter.contract_type = "Exclusive"
        fighter.contract_months = max(12, fighter.contract_months)
        fighter.exclusive = True
        fighter.free_agent_months = 0
        fighter.champion = False
        fighter.interim_champion = False
        fighter.purse = max(
            fighter.purse,
            round(max(5_000, fighter.overall * 300 + fighter.popularity * 500) / 500) * 500,
        )
        fighter.morale = min(100, fighter.morale + 3)
        fighter.rank_score = self.rank_value(fighter)
        self.roster.append(fighter)

        note = (f"{fighter.name} crossed over from {self.player_company_name}'s {sport} division "
                f"to the MMA roster with a {records[sport]} {sport} record.")
        fighter.fight_history = list(fighter.fight_history or [])
        fighter.fight_history.insert(0, f"Month {self.month}: {note}")
        division["last_card_summary"] = note
        self.news.insert(0, note)
        self.record_world_story(
            "Player Crossover", note,
            f"MMA record on arrival: {fighter.record}. Child-sport history and identity were retained.",
            [self.player_company_name], [fighter.name], importance=3,
        )
        self.refresh_combat_sport_rankings(sport, world, employer=self.player_company_name, division=division)
        self.refresh_promotion_rankings()
        return True, note

    def release_player_combat_athlete(self, sport, fighter):
        """Release a child-promotion athlete back into the sport's main circuit."""
        world = getattr(self, "combat_sport_worlds", {}).get(sport)
        division = getattr(self, "player_combat_divisions", {}).get(sport)
        if not world or not division:
            return False, "That player-owned sport division is not available."
        if fighter not in world.get("roster", []) or fighter.sport_employer != self.player_company_name:
            return False, f"{fighter.name} is not contracted to your {sport} division."

        state = self.ensure_combat_sport_circuit_state(
            sport, world, self.player_company_name, player_owned=True,
        )
        vacated = []
        for key, champion in list(state.get("titles", {}).items()):
            if champion != fighter.name:
                continue
            state["titles"][key] = ""
            vacated.append(self.combat_sport_division_label(key))
            state.setdefault("title_history", {}).setdefault(key, []).insert(0, {
                "month": self.month, "week": self.week, "year": self.current_year(),
                "winner": "VACANT", "loser": "", "method": "Champion released",
                "previous_champion": fighter.name,
            })
        state["champion"] = next((name for name in state.get("titles", {}).values() if name), "")

        division["roster"] = [name for name in division.get("roster", []) if name != fighter.name]
        division["booked_bouts"] = [
            bout for bout in division.get("booked_bouts", [])
            if fighter.name not in (bout.get("a"), bout.get("b"))
        ]
        fighter.sport_employer = world.get("promotion", "")
        fighter.contract_months = 0
        fighter.champion = False
        fighter.interim_champion = False
        fighter.fight_history = list(fighter.fight_history or [])
        fighter.fight_history.insert(
            0,
            f"{self.format_game_date()}: Released by {self.player_company_name}'s {sport} division.",
        )
        self.refresh_combat_sport_rankings(sport, world, employer=self.player_company_name, division=division)
        self.refresh_combat_sport_rankings(sport, world, employer=world.get("promotion", ""))
        title_note = f" The {', '.join(vacated)} title was vacated." if vacated else ""
        note = f"{fighter.name} was released from your {sport} division and returned to the {world.get('promotion', sport)} circuit.{title_note}"
        self.news.insert(0, note)
        return True, note

    def open_player_combat_division(self, sport):
        divisions = getattr(self, "player_combat_divisions", {})
        world = getattr(self, "combat_sport_worlds", {}).get(sport, {})
        if sport not in divisions:
            startup_cost = 120000
            if self.cash < startup_cost:
                return False, f"Need ${startup_cost:,} to establish a {sport} division."
            self.cash -= startup_cost
            self.record_finance_transaction(f"Launch {sport} division", costs=startup_cost)
            # A child promotion begins as a genuine expansion: the player signs
            # its roster deliberately instead of receiving an invisible starter team.
            signed = []
            sport_brand = {"Brazilian Jiu-Jitsu": "BJJ"}.get(sport, sport)
            promotion_name = f"{self.player_company_name} {sport_brand}"
            divisions[sport] = {
                "sport": sport, "roster": [fighter.name for fighter in signed], "rankings": [fighter.name for fighter in signed[:10]],
                "champion": "", "titles": {}, "title_history": {}, "rankings_by_division": {}, "titles_initialized": True,
                "events": [], "booked_bouts": [], "promotion_name": promotion_name, "records": {}, "record_book": {}, "season_stats": {}, "awards": [], "hall_of_fame": [], "finance_history": [],
                "budget": startup_cost, "active": True, "strategy": "Balanced", "revenue_total": 0, "cost_total": startup_cost,
                "profit_total": -startup_cost, "last_card_summary": "No player card yet.", "title_name": f"{promotion_name} Championships",
                "reputation": max(20, self.company_pop), "stability": 60,
                "auto_cards": False, "auto_card_min_bouts": 5, "auto_card_status": "Off - manual cards only.", "last_card_month": 0,
            }
            self.player_combat_divisions = divisions
            self.ensure_player_combat_signable_depth(sport, world, force=True)
            self.news.insert(0, f"{promotion_name} launched as a child promotion. Sign specialists, book matchups and run its first card after the ${startup_cost:,} startup investment.")
        elif "last_youth_market_month" not in divisions[sport]:
            # Existing saves receive one controlled intake when first opened;
            # subsequent additions obey the normal two-month cadence.
            self.ensure_player_combat_signable_depth(sport, world, force=True)
        return True, divisions[sport]

    def has_unresolved_title_shot_inbox(self, fighter):
        subject = f"Title Shot Owed - {fighter.name}"
        return any(m.get("subject") == subject and not m.get("resolved", False) for m in getattr(self, "inbox", []) or [])

    def resolve_title_shot_inbox(self, fighter):
        """Mark any outstanding 'Title Shot Owed' inbox alerts for this fighter as resolved."""
        subject = f"Title Shot Owed - {fighter.name}"
        for message in getattr(self, "inbox", []) or []:
            if message.get("subject") == subject and not message.get("resolved", False):
                message["resolved"] = True

    def reconcile_title_shot_alerts(self):
        """Self-heal stale title-shot state left by older saves.

        A current champion, or a fighter who has already won a title, has been
        given their guaranteed shot, so the one-time clause is consumed and the
        owed flag cleared. Any fighter no longer owed a shot has their leftover
        inbox alert resolved. Fighters genuinely still owed a shot (never titled)
        are untouched. Runs on load and in the monthly contract review, so it
        corrects in-memory state without ever editing the save file directly."""
        for fighter in getattr(self, "roster", []) or []:
            fulfilled = getattr(fighter, "champion", False) or getattr(fighter, "title_shots", 0) >= 1
            if fulfilled:
                fighter.owed_title_shot = False
                fighter.title_shot_clause = False
            if not getattr(fighter, "owed_title_shot", False):
                self.resolve_title_shot_inbox(fighter)

    def review_contract_promises(self):
        self.reconcile_title_shot_alerts()
        for fighter in self.roster:
            if not getattr(fighter, "promise_deadline_month", 0) or fighter.promise_deadline_month >= self.month:
                continue
            broken = []
            if fighter.main_event_promise:
                broken.append("main-event")
            if fighter.top_opponent_promise:
                broken.append("top-opponent")
            if not broken:
                fighter.promise_deadline_month = 0
                continue
            fighter.main_event_promise = False
            fighter.top_opponent_promise = False
            fighter.promise_deadline_month = 0
            fighter.relationship_trust = max(1, fighter.relationship_trust - 20)
            fighter.morale = max(15, fighter.morale - 12)
            fighter.negotiation_heat = min(100, fighter.negotiation_heat + 14)
            self.inbox.append({"subject": f"Broken Promise - {fighter.name}", "body": f"The promised {' and '.join(broken)} opportunity never materialised. Trust and morale have fallen.", "type": "Talent Relations", "resolved": False})
            self.news.insert(0, f"Broken promise: {fighter.name} is unhappy after a missed {' and '.join(broken)} commitment.")

    def simulate_nonexclusive_outside_fights(self):
        outside = [f for f in self.roster if not f.exclusive and not f.injured and f.fatigue < 45]
        for fighter in outside:
            if random.random() > 0.22:
                continue
            opponent = self.create_generated_fighter(5, max(18, fighter.popularity + 8), max(35, fighter.overall - 10), min(88, fighter.overall + 8))
            winner, loser, method, round_no, _lines = self.simulate_fight(fighter, opponent, {"main": False, "title": False})
            self.update_elo(winner, loser, {"main": False, "title": False}, method)
            self.commit_career_stats(fighter)
            if winner is fighter:
                fighter.record_w += 1
                fighter.popularity = min(100, fighter.popularity + random.randint(1, 4))
                fighter.momentum = min(5, fighter.momentum + 1)
                result = f"won an outside fight by {method} in round {round_no}"
            else:
                fighter.record_l += 1
                fighter.popularity = max(1, fighter.popularity - random.randint(1, 5))
                fighter.momentum = max(-5, fighter.momentum - 1)
                result = f"lost an outside fight by {method} in round {round_no}"
            fighter.fatigue = min(100, fighter.fatigue + random.randint(20, 45))
            fighter.fight_history = fighter.fight_history or []
            fighter.fight_history.insert(0, f"Month {self.month} Week {self.week}: {fighter.name} {result}.")
            if random.random() < 0.12:
                fighter.injured = random.randint(1, 4)
                result += " and came back injured"
            self.news.insert(0, f"{fighter.name} {result} because their contract is non-exclusive.")

    def age_and_develop_fighters(self, fighters, player_roster=False):
        year = str(2026 + (self.month - 1) // 12)
        for fighter in fighters:
            fighter.elo_rating = getattr(fighter, "elo_rating", 1500) or 1500
            if fighter.injured:
                fighter.injured -= 1
                if fighter.injured <= 0 and getattr(fighter, "serious_injury", "") and not getattr(fighter, "serious_injury_pending", False):
                    completed = fighter.serious_injury
                    fighter.serious_injury = ""
                    fighter.serious_injury_history = (fighter.serious_injury_history or [])[-11:] + [f"Month {self.month}: Cleared to return after {completed.lower()}."]
                    if fighter in getattr(self, "roster", []):
                        self.inbox.append({"subject": f"Medical Clearance — {fighter.name}", "body": f"{fighter.name} has been medically cleared following {completed.lower()}.", "type": "Medical", "fighter": fighter.name, "resolved": False})
            fighter.fatigue = max(0, fighter.fatigue - random.randint(10, 22))
            fighter.media_heat = max(0, fighter.media_heat - random.randint(1, 4))
            self.acclimatize_division_fit(fighter)
            months_inactive = max(0, self.month - getattr(fighter, "last_fight_month", 0))
            if months_inactive >= 10 and fighter.popularity > 18 and random.random() < min(0.55, 0.12 + months_inactive / 55):
                fighter.popularity -= 1
            before = fighter.overall
            development = self.monthly_development_score(fighter)
            resurgence = self.veteran_resurgence_chance(fighter)
            development_tail = 2 if fighter.career_archetype == "Durable Career" else 0
            normal_growth_open = fighter.age <= fighter.prime_end + development_tail
            can_improve = (fighter.overall < fighter.potential and normal_growth_open) or (resurgence > 0 and random.random() < resurgence)
            # Entry-level and regional fighters were passing the same hard roll
            # as established professionals. That left too many 20-28 year olds
            # frozen well below their potential for an entire save. Give genuine
            # low-rated prospects a better training opportunity, not extra ceiling.
            runway_gap = max(0, fighter.potential - fighter.overall)
            grassroots_developer = fighter.age <= 31 and fighter.overall < 75 and runway_gap >= 5
            development_roll_floor = 70
            development_roll_ceiling = 135
            if grassroots_developer:
                opportunity = min(30, 10 + max(0, 73 - fighter.overall) * 0.45 + runway_gap * 0.35)
                development_roll_floor = max(52, round(development_roll_floor - opportunity * 0.70))
                development_roll_ceiling = max(development_roll_floor + 18, round(development_roll_ceiling - opportunity))
            growth_roll = random.randint(development_roll_floor, development_roll_ceiling)
            if development > growth_roll and can_improve:
                # Lumpier, more individual development. How far the score clears the
                # roll decides the size of the step: a standout month can be a real
                # leap, a routine pass is a steady tick, and even eligible fighters
                # sometimes plateau for a stretch. This widens career trajectories
                # (breakout prospects vs slow burners) instead of everyone tracking
                # the same smooth line.
                margin = development - growth_roll
                grassroots_leap = grassroots_developer and fighter.overall < 58 and runway_gap >= 12 and random.random() < 0.32
                if (margin > 72 or development > 185) and fighter.age <= fighter.prime_end and random.random() < 0.20:
                    growth = 3
                elif (margin > 42 or development > 165 or fighter.trait == "Gym Rat" or grassroots_leap) and random.random() < 0.45:
                    growth = 2
                elif random.random() < 0.22:
                    growth = 0  # plateau month
                else:
                    growth = 1
                if growth:
                    self.apply_development_growth(fighter, growth)
            decline_risk = self.monthly_decline_score(fighter)
            decline_roll = random.randint(65, 130)
            if decline_risk > decline_roll:
                # Once a fighter has been past their prime for several years,
                # erosion should be visible rather than being fully hidden by a
                # strong camp or a good run of form.  Durable veterans can still
                # resist it, but they no longer stay near their peak indefinitely.
                years_past_prime = max(0, fighter.age - fighter.prime_end)
                loss = -2 if (decline_risk > 155 or (years_past_prime >= 4 and decline_risk > 145) or fighter.age >= 40) else -1
                self.adjust_random_skill(fighter, loss)
                self.adjust_detailed_skill(fighter, loss)
                # A late-30s body erodes across the board, not just one attribute,
                # so the drop is actually visible in the overall rating.
                if fighter.age >= 38:
                    self.adjust_random_skill(fighter, -1)
            if fighter.overall != before:
                explanation = self.fighter_development_explanation(fighter)
                direction = "Development" if fighter.overall > before else "Decline"
                key_factors = explanation["positive"][:3] if fighter.overall > before else explanation["negative"][:3]
                if not key_factors and fighter.overall < before:
                    key_factors = [("Age, career wear and form", -decline_risk)]
                fighter.development_log = fighter.development_log or []
                fighter.development_log.insert(0, {
                    "date": self.format_game_date(), "before": before, "after": fighter.overall,
                    "type": direction, "score": round(development, 1),
                    "roll": growth_roll if fighter.overall > before else decline_roll,
                    "reason": "; ".join(f"{label} {value:+.1f}" for label, value in key_factors),
                })
                fighter.development_log = fighter.development_log[:10]
                gym = self.gym_by_name(getattr(fighter, "camp", ""))
                if gym and abs(fighter.overall - before) >= 2:
                    direction_word = "breakthrough" if fighter.overall > before else "career-wear setback"
                    self.record_gym_story(
                        gym, f"{fighter.name}: {direction_word}",
                        f"OVR {before} -> {fighter.overall}. {fighter.development_log[0]['reason']}", fighter=fighter,
                    )
            elif player_roster:
                arc = self.active_career_arc(fighter)
                tracked_types = {"Homegrown Champion", "Professional Reset", "Camp Fit"}
                if arc and arc.get("type") in tracked_types and self.month - arc.get("last_gym_story_month", 0) >= 3:
                    explanation = self.fighter_development_explanation(fighter)
                    brakes = explanation["negative"][:2]
                    reason = "; ".join(f"{label} {value:+.1f}" for label, value in brakes)
                    if not reason:
                        reason = f"Development score {explanation['score']:.1f} did not clear this month's growth opportunity."
                    gym = self.gym_by_name(getattr(fighter, "camp", ""))
                    if gym:
                        self.record_gym_story(
                            gym, f"{fighter.name}: development plateau", reason, fighter=fighter,
                        )
                    fighter.development_log = (fighter.development_log or [])[:9]
                    fighter.development_log.insert(0, {
                        "date": self.format_game_date(), "before": before, "after": fighter.overall,
                        "type": "Plateau", "score": round(explanation["score"], 1), "reason": reason,
                    })
                    arc["last_gym_story_month"] = self.month
            fighter.annual_overalls = fighter.annual_overalls or {}
            fighter.annual_overalls[year] = max(fighter.annual_overalls.get(year, 0), fighter.overall)
            self.update_fighter_peak_overall(fighter)
            fighter.rank_score = self.rank_value(fighter)
            if fighter.contract_months > 0:
                fighter.contract_months -= 1
            # Surface notable development so prospects don't improve invisibly.
            if player_roster and fighter.overall > before and (fighter.age <= 26 or fighter.age > fighter.prime_end) and random.random() < 0.3:
                fighter.popularity = min(100, fighter.popularity + 1)
                label = "Veteran resurgence" if fighter.age > fighter.prime_end else "Development watch"
                self.news.insert(0, f"{label}: {fighter.name} ({fighter.age}) is improving at {fighter.camp}; now rated overall {fighter.overall}.")

    def age_world_one_year(self):
        """Deterministic yearly career arc: everyone ages once, primes matter."""
        aged = self.all_fighter_objects() if hasattr(self, "all_fighter_objects") else list(self.roster)
        for prospect in getattr(self, "academy", {}).get("prospects", []):
            prospect["age"] += 1
            if prospect["age"] >= 18 and not prospect.get("adult_weight_reviewed"):
                prospect["adult_weight_reviewed"] = True
                old_weight = prospect.get("weight", "Lightweight")
                if old_weight in WEIGHTS and self.academy_stable_number(prospect, "adult-growth", 0, 99) < 42:
                    prospect["weight"] = WEIGHTS[min(len(WEIGHTS) - 1, WEIGHTS.index(old_weight) + 1)]
                prospect["amateur_weight"] = self.academy_weight_band(prospect["weight"])
                note = (f"{prospect['name']} is now 18 and eligible to turn professional. "
                        f"Adult weight review: {old_weight} -> {prospect['weight']}; readiness {self.academy_graduation_readiness(prospect)}%.")
                prospect["milestones"] = ([f"M{self.month}: {note}"] + prospect.get("milestones", []))[:20]
                if not getattr(self, "spectator_mode", False):
                    self.inbox.append({"subject": f"Academy Graduation Review - {prospect['name']}", "body": note,
                                       "type": "Academy", "fighter": prospect["name"], "resolved": False})
        broke_out = []
        for fighter in aged:
            if getattr(fighter, "retired", False):
                continue
            fighter.age += 1
            if fighter.age > fighter.prime_end:
                over = fighter.age - fighter.prime_end
                decline_chance = min(0.90, 0.38 + over * 0.13 - self.veteran_resurgence_chance(fighter) * 2)
                if random.random() < decline_chance:
                    self.adjust_random_skill(fighter, -1)
                    self.adjust_detailed_skill(fighter, -1)
            elif fighter.age < fighter.prime_start and fighter.overall < fighter.potential:
                if random.random() < 0.55:
                    self.apply_development_growth(fighter, 1)
                    if fighter.overall >= 80 and fighter.age <= 24:
                        broke_out.append(fighter)
            fighter.rank_score = self.rank_value(fighter)
        self.process_annual_weight_class_movements()
        combat_aged = set()
        for world in getattr(self, "combat_sport_worlds", {}).values():
            for fighter in world.get("roster", []):
                if id(fighter) in combat_aged or getattr(fighter, "retired", False):
                    continue
                combat_aged.add(id(fighter))
                fighter.age += 1
                sport = self.combat_sport_for_fighter(fighter)
                if sport:
                    self.apply_combat_sport_annual_age_curve(fighter, sport)
                fighter.annual_overalls = fighter.annual_overalls or {}
                fighter.annual_overalls[str(self.current_year())] = max(fighter.annual_overalls.get(str(self.current_year()), 0), fighter.overall)
                self.update_fighter_peak_overall(fighter)
        self.news.insert(0, f"A new year begins across the MMA world; every fighter is now a year older.")
        for fighter in broke_out[:3]:
            self.news.insert(0, f"Breakout prospect: {fighter.name} ({fighter.age}) has developed into a genuine talent at overall {fighter.overall}.")

    def career_weight_move_target(self, fighter, roster):
        """Choose a credible adjacent division from body fit, career stage, and opportunity."""
        if fighter.champion or fighter.interim_champion or fighter.injured or fighter.retired:
            return None, ""
        if self.month - getattr(fighter, "weight_move_last_month", -99) < 12:
            return None, ""
        try:
            index = WEIGHTS.index(fighter.weight)
        except ValueError:
            return None, ""
        current_limit = WEIGHT_LIMITS[fighter.weight]
        walk = fighter.walk_weight or self.default_walk_weight(fighter)
        natural_size = self.ds(fighter, "natural_size", 50)
        cut_skill = self.ds(fighter, "weight_cutting", fighter.cardio)
        current_depth = len([candidate for candidate in roster if candidate.gender == fighter.gender and candidate.weight == fighter.weight and not candidate.retired])
        options = []
        for step, label in ((-1, "move down"), (1, "move up")):
            target_index = index + step
            if target_index < 0 or target_index >= len(WEIGHTS):
                continue
            target = WEIGHTS[target_index]
            allowed, _assessment = self.weight_class_move_assessment(fighter, target)
            if not allowed:
                continue
            target_depth = len([candidate for candidate in roster if candidate.gender == fighter.gender and candidate.weight == target and not candidate.retired])
            opportunity = max(-5, min(12, (current_depth - target_depth) * 2))
            if step > 0:
                pressure = max(0, walk - current_limit - 12) * 1.4 + max(0, fighter.age - 30) * 2.2
                pressure += max(0, fighter.weight_cut_penalty - 2) * 3 + (8 if fighter.missed_weight else 0) + max(0, natural_size - 58) * 0.45
                # A thin division next door and a lucky roll could clear the
                # threshold between them with no bodily reason at all, which
                # moved fighters who fit their class perfectly well: a
                # lightweight walking eight pounds over the limit -- a smaller
                # cut than his division's median -- was relocated to
                # welterweight for "natural frame growth" and ended up seven
                # pounds under his new limit. Opportunity may tip a decision
                # that the body already supports; it cannot make one on its own.
                if pressure < 6:
                    continue
                score = pressure + opportunity + random.uniform(-7, 7)
                reason = "a healthier fit at a higher weight after difficult cuts" if fighter.missed_weight or fighter.weight_cut_penalty >= 4 else "natural frame growth and a clearer divisional opportunity"
            else:
                pressure = max(0, current_limit + 11 - walk) * 1.5 + max(0, cut_skill - 70) * 0.18 + (4 if fighter.age <= 29 else 0)
                score = pressure + opportunity + random.uniform(-7, 7)
                reason = "a sustainable cut and an opportunity in a thinner division"
            options.append((score, target, reason))
        if not options:
            return None, ""
        score, target, reason = max(options, key=lambda row: row[0])
        return (target, reason) if score >= 13 else (None, "")

    def process_annual_weight_class_movements(self):
        """Annual career reviews create a small number of believable division moves."""
        groups = [(self.roster, True, self.player_company_name)]
        groups.extend((promo.roster, False, promo.name) for promo in self.promotions if not getattr(promo, "is_regional_feeder", False))
        for roster, player_owned, company in groups:
            candidates = list(roster)
            random.shuffle(candidates)
            moves = 0
            for fighter in candidates:
                if moves >= (1 if player_owned else 2):
                    break
                target, reason = self.career_weight_move_target(fighter, roster)
                if not target:
                    continue
                if player_owned:
                    self.inbox.append({"subject": f"Division Review — {fighter.name}", "body": f"Your staff recommend that {fighter.name} consider moving from {fighter.weight} to {target}: {reason}. Open their profile to review the body-fit assessment and decide.", "type": "Roster", "fighter": fighter.name, "action": "weight_move_recommendation", "resolved": False})
                    fighter.weight_move_last_month = self.month
                else:
                    self.complete_weight_class_move(fighter, target, reason)
                moves += 1

    def process_retirements(self):
        self.process_free_agent_retirements()
        retirement_groups = [] if getattr(self, "spectator_mode", False) else [(self.roster, self.belts, self.interim_belts, self.belt_history, self.player_company_name, self.player_region, self.company_pop, True, None)]
        retirement_groups.extend((promo.roster, promo.belts or {}, promo.interim_belts or {}, promo.belt_history or {}, promo.name, promo.region, promo.reputation_score, False, promo) for promo in self.promotions)
        for roster, belts, interim_belts, belt_history, company_name, region, size, player_owned, promo in retirement_groups:
            in_regional_feeder = promo is not None and getattr(promo, "is_regional_feeder", False)
            for fighter in list(roster):
                # A fighter still sitting in a feeder roster around 35 was
                # never picked up by the wider market. Regional development is
                # a young talent's pathway, not a decades-long holding
                # pattern, so this is a hard cutoff rather than the general
                # population's probabilistic age-39+ review. The exact age is
                # stable per fighter (33-37) so an entire circuit doesn't
                # retire in lockstep on the same birthday.
                if in_regional_feeder:
                    variable_retirement_age = 33 + (sum(ord(char) for char in fighter.name) % 5)
                    if fighter.age < variable_retirement_age:
                        continue
                    should_retire = True
                elif fighter.age < 39:
                    continue
                else:
                    should_retire = getattr(fighter, "retirement_pending", False)
                if not should_retire:
                    # Most fighters receive one meaningful career review per year, not
                    # a fresh retirement coin-flip every month after turning 40.
                    if fighter.age < 49 and (self.month - 1) % 12 + 1 != self.retirement_review_month(fighter):
                        continue
                    age_pressure = max(0, fighter.age - 39) * 0.055
                    motivation_pressure = max(0, 55 - fighter.motivation) / 240
                    form_pressure = max(0, -fighter.momentum) * 0.025 + max(0, fighter.record_l - fighter.record_w * 0.65) / 180
                    health_pressure = fighter.injury_proneness / 900 + max(0, fighter.fatigue - 55) / 500
                    legacy_buffer = 0.10 if fighter.champion or fighter.popularity >= 75 or fighter.motivation >= 82 else 0
                    retirement_chance = max(0.01, min(0.82, age_pressure + motivation_pressure + form_pressure + health_pressure - legacy_buffer))
                    should_retire = fighter.age >= 46 or random.random() < retirement_chance
                if should_retire:
                    player_booked = player_owned and fighter.name in self.scheduled_fighter_names(include_booked=True)
                    if not getattr(fighter, "retirement_pending", False):
                        reason = "Regional career review: never picked up by a major promotion" if in_regional_feeder else "Career retirement review"
                        self.mark_retirement_fight_required(fighter, reason)
                        if player_owned:
                            body = f"{fighter.name} intends to retire, but must take one final fight first. Book them soon; they will retire immediately after that bout."
                            if player_booked:
                                body = f"{fighter.name} intends to retire after their currently booked bout. They will remain available until that commitment is complete."
                            self.inbox.append({"subject": f"Retirement Fight Needed - {fighter.name}", "body": body, "type": "Roster", "resolved": False})
                        self.news.insert(0, f"Retirement watch: {fighter.name} wants one final fight before retiring.")
                    if not player_owned:
                        fighter.available_week = min(getattr(fighter, "available_week", 0), self.week)
                        fighter.fatigue = min(fighter.fatigue, 45)
                        continue
                    continue
            belts, interim_belts, belt_history = self.ensure_company_champions(
                roster, belts, company_name, region, size, player_owned=player_owned,
                interim_belts=interim_belts, belt_history=belt_history,
                closed_divisions=self.company_closed_divisions(promo) if promo else None,
                allow_appointed=not (promo is not None and getattr(promo, "is_regional_feeder", False)),
            )
            if promo:
                promo.belts, promo.interim_belts, promo.belt_history = belts, interim_belts, belt_history
            else:
                self.belts, self.interim_belts, self.belt_history = belts, interim_belts, belt_history
        self.process_overdue_retirement_fights()
        self.simulate_due_free_agent_retirement_cards()

    def retirement_fight_wait_months(self, fighter):
        requested = getattr(fighter, "retirement_requested_month", 0) or self.month
        return max(0, self.month - requested)

    def retirement_fight_roster_for(self, fighter):
        if fighter in self.roster:
            return self.roster, self.player_company_name, self.player_region
        if fighter in self.free_agents:
            return self.free_agents, "Independent Circuit", fighter.region
        for promo in getattr(self, "promotions", []):
            if fighter in promo.roster:
                return promo.roster, promo.name, promo.region
        return [], "", fighter.region

    def process_overdue_retirement_fights(self):
        # Company retirees can be resolved through a one-off farewell showcase.
        # Unsigned retirees use the dedicated Independent Retirement Card flow
        # below, where several careers conclude together on a proper event.
        free_agent_ids = {id(fighter) for fighter in self.free_agents}
        scheduled = self.scheduled_fighter_names(include_booked=True)
        pending = [
            fighter for fighter in self.all_fighter_objects()
            if not getattr(fighter, "retired", False) and getattr(fighter, "retirement_pending", False)
            and id(fighter) not in free_agent_ids
            and fighter.name not in scheduled
        ]
        pending.sort(key=lambda fighter: (self.retirement_fight_wait_months(fighter), fighter.age), reverse=True)
        booked = set()
        retirement_limit = min(40, max(10, len(pending) // 20))
        for fighter in pending[:retirement_limit]:
            wait = self.retirement_fight_wait_months(fighter)
            threshold = 12
            if wait < threshold or fighter.name in booked:
                continue
            if fighter.injured:
                if wait >= threshold:
                    fighter.injured = 0
                if fighter.injured:
                    continue
            roster, company_name, region = self.retirement_fight_roster_for(fighter)
            if not roster:
                continue
            opponents = [
                candidate for candidate in roster
                if candidate is not fighter and not getattr(candidate, "retired", False) and not getattr(candidate, "retirement_pending", False)
                and not candidate.injured and candidate.fatigue < 70 and candidate.gender == fighter.gender
            ]
            if not opponents:
                opponents = [
                    candidate for candidate in roster
                    if candidate is not fighter and not getattr(candidate, "retired", False)
                    and candidate.name not in booked and not candidate.injured and candidate.fatigue < 70
                    and candidate.gender == fighter.gender
                ]
            same_weight = [candidate for candidate in opponents if candidate.weight == fighter.weight]
            opponents = same_weight or opponents
            if not opponents:
                continue
            opponent = min(opponents, key=lambda candidate: (
                abs(candidate.overall - fighter.overall)
                + abs(candidate.age - fighter.age) * 0.25
                + self.matchup_history_penalty(fighter, candidate)
            ))
            booked.update({fighter.name, opponent.name})
            fighter.fatigue = min(fighter.fatigue, 35)
            opponent.fatigue = min(opponent.fatigue, 45)
            bout = {"main": False, "title": False, "tier": "Retirement Showcase", "region": region}
            winner, loser, method, round_no, lines = self.simulate_fight(fighter, opponent, bout)
            if method == "Draw":
                self.apply_draw_result(fighter, opponent, bout)
                result = f"{fighter.name} vs {opponent.name} - Draw (R{round_no})"
            else:
                self.apply_result(winner, loser, bout, method)
                result = f"{winner.name} def. {loser.name} by {method} (R{round_no})"
            event_name = f"{company_name} Retirement Showcase: {self.matchup_display_name(fighter, opponent)}"
            self.archive_result_record({
                "date": f"Month {self.month} Week {self.week}",
                "company": company_name,
                "event": event_name,
                "summary": f"Farewell fight: {result}",
                "fights": 1,
                "gate": "$0",
                "profit": "$0",
                "log": [f"{event_name}: {result}", *lines],
                "fight_logs": [{"heading": f"{fighter.name} vs {opponent.name}", "label": "RETIREMENT SHOWCASE", "a": fighter.name, "b": opponent.name, "result": result, "lines": list(lines) + ["", result]}],
                "finance": {"ticket_revenue": 0, "total_revenue": 0, "total_expense": 0, "profit": 0},
            })
            self.news.insert(0, f"Farewell fight booked: {result} at {event_name}.")
            self.retire_after_final_fight_if_due(fighter, company_name)
            self.retire_after_final_fight_if_due(opponent, company_name)

    def in_universe_loss_streak(self, fighter):
        """Return the current loss streak from simulated-universe bout records.

        Imported pre-universe records are intentionally ignored: a veteran can
        arrive with an old losing run, but only results played in this save can
        trigger the free-agent career-end rule.
        """
        streak = 0
        for entry in list(getattr(fighter, "bout_rating_history", None) or []):
            if not isinstance(entry, dict):
                continue
            result = str(entry.get("result", "")).upper()
            if result == "L":
                streak += 1
            elif result in ("W", "D"):
                break
        return streak

    def recent_real_win_rate(self, fighter, n=5):
        """Win rate over the fighter's last n simulated-universe bouts, or None if unfought."""
        history = [
            entry for entry in list(getattr(fighter, "bout_rating_history", None) or [])
            if isinstance(entry, dict)
        ][:n]
        if not history:
            return None
        wins = sum(1 for entry in history if str(entry.get("result", "")).upper() == "W")
        return wins / len(history)

    def process_free_agent_retirements(self):
        """Free agency must not become a permanent retirement home for aging fighters."""
        # Low-overall fighters stuck on a losing skid rarely accumulate the long
        # unsigned "waiting" months the veteran checks below need, so they can
        # clutter free agency indefinitely without ever qualifying for review.
        # Checked twice a year rather than every month so a single rough patch
        # doesn't end a career the moment a third loss lands.
        stagnation_review_due = self.month % 6 == 0
        for fighter in list(self.free_agents):
            losing_streak = self.in_universe_loss_streak(fighter)
            losing_streak_exit = fighter.age > 30 and fighter.overall < 80 and losing_streak >= 7
            recent_win_rate = self.recent_real_win_rate(fighter, 5)
            low_overall_stagnation = (
                stagnation_review_due and fighter.age >= 30 and fighter.overall < 55
                and losing_streak >= 3 and recent_win_rate is not None and recent_win_rate <= 0.30
                and not self.is_blue_chip_prospect(fighter)
            )
            waiting = max(0, getattr(fighter, "free_agent_months", 0))
            accelerated_market_review = (
                (fighter.age >= 43 and waiting >= 3)
                or (fighter.age >= 40 and waiting >= 6)
            )
            if (not losing_streak_exit and not accelerated_market_review and not low_overall_stagnation
                    and (self.month - 1) % 12 + 1 != self.retirement_review_month(fighter)):
                continue
            aging_out = fighter.age >= 38
            journeyman_exit = (fighter.age >= 34 and waiting >= 30 and fighter.overall < 73
                               and fighter.potential < 82 and not self.is_blue_chip_prospect(fighter))
            stalled_career = (fighter.age >= 30 and waiting >= 48 and fighter.overall < 68
                              and fighter.potential < 76 and not self.is_blue_chip_prospect(fighter))
            if not (losing_streak_exit or aging_out or journeyman_exit or stalled_career or low_overall_stagnation):
                continue
            age_pressure = max(0, fighter.age - 37) * 0.065
            market_pressure = max(0, waiting - 24) / 150
            inactivity = 0.08 + max(0, -fighter.momentum) * 0.035
            health = fighter.injury_proneness / 850 + max(0, fighter.fatigue - 45) / 420
            unsigned_veteran_pressure = 0.12 if fighter.age >= 43 and waiting >= 3 else 0.07 if fighter.age >= 40 and waiting >= 6 else 0
            if (losing_streak_exit or low_overall_stagnation or fighter.age >= 46
                    or random.random() < min(0.88, age_pressure + market_pressure + inactivity + health + unsigned_veteran_pressure)):
                if not getattr(fighter, "retirement_pending", False):
                    if losing_streak_exit:
                        reason = f"Independent career review after a {losing_streak}-fight in-universe losing streak"
                    elif low_overall_stagnation:
                        reason = f"Independent career review after {losing_streak} straight losses with no real progress ({fighter.overall} OVR)"
                    else:
                        reason = "Free-agent retirement review" if aging_out else "Independent-career review"
                    self.mark_retirement_fight_required(fighter, reason)
                    fighter.free_agent_months = max(getattr(fighter, "free_agent_months", 0), 2)
                    self.news.insert(0, f"Independent retirement watch: {fighter.name} is seeking one final showcase fight.")

    def adjust_random_skill(self, fighter, amount):
        key = random.choice(["striking", "wrestling", "grappling", "cardio", "chin"])
        setattr(fighter, key, max(20, min(99, getattr(fighter, key) + amount)))

    def adjust_detailed_skill(self, fighter, amount):
        self.ensure_detailed_skills(fighter)
        group = random.choice(list(DETAILED_SKILL_GROUPS.values()))
        for key in random.sample(group, k=min(3, len(group))):
            fighter.detailed_skills[key] = max(1, min(99, fighter.detailed_skills.get(key, 50) + amount))
        self.sync_broad_skills_from_details(fighter)

    def detailed_skill_growth_chance(self, fighter, key, signature_keys=None):
        """Soft-cap one detailed skill without imposing an artificial hard ceiling."""
        value = fighter.detailed_skills.get(key, 50)
        if key in {"reach", "natural_size"} or value >= 99:
            return 0.0
        if value < 80:
            chance = 0.98
        elif value < 90:
            chance = 0.72
        elif value < 95:
            chance = 0.38
        elif value < 98:
            chance = 0.14
        else:
            chance = 0.03
        if signature_keys is None:
            signature_keys = self.fighter_signature_detailed_skills(fighter)
        if key in signature_keys:
            chance *= 1.25
        if fighter.trait in ("Technical Learner", "Gym Rat"):
            chance *= 1.08
        return min(0.99, chance)

    def improve_detailed_skill(self, fighter, key, amount=1):
        """Apply bounded, potential-aware training to one trainable attribute."""
        self.ensure_detailed_skills(fighter)
        if key not in fighter.detailed_skills:
            return 0
        improved = 0
        for _ in range(max(1, int(amount))):
            if random.random() > self.detailed_skill_growth_chance(fighter, key):
                continue
            before_value = fighter.detailed_skills[key]
            before_overall = fighter.overall
            fighter.detailed_skills[key] = min(99, before_value + 1)
            self.sync_broad_skills_from_details(fighter)
            if fighter.overall > min(99, fighter.potential):
                fighter.detailed_skills[key] = before_value
                self.sync_broad_skills_from_details(fighter)
                break
            if fighter.detailed_skills[key] > before_value:
                improved += 1
            elif fighter.overall != before_overall:
                break
        return improved

    def apply_development_growth(self, fighter, amount=1):
        """Spend a successful training month on a handful of relevant skills."""
        self.ensure_detailed_skills(fighter)
        style_group = {
            "Boxer": "Standing", "Kickboxer": "Standing", "Dutch Kickboxer": "Standing",
            "Karate": "Standing", "Taekwondo": "Standing", "Sanda": "Standing",
            "Muay Thai": "Muay Thai Clinch", "Wrestler": "Wrestling",
            "Freestyle Wrestler": "Wrestling", "Catch Wrestler": "Wrestling",
            "Judo": "Wrestling", "BJJ": "Ground", "Luta Livre": "Ground",
            "Submission Grappler": "Ground", "Grappler": "Ground", "Sambo": "Ground",
        }.get(fighter.style)
        available = list(DETAILED_SKILL_GROUPS)
        primary = style_group if style_group in available and random.random() < 0.68 else random.choice(available)
        gap = max(0, fighter.potential - fighter.overall)
        groups = [primary]
        if fighter.age <= 30 and fighter.potential >= 70 and gap >= 4:
            secondary_pool = [name for name in ("Mental", "Physical", "Standing", "Wrestling", "Ground") if name != primary]
            groups.append(random.choice(secondary_pool))
        before = fighter.overall
        signature = self.fighter_signature_detailed_skills(fighter)
        pool = []
        for group_name in groups:
            for key in DETAILED_SKILL_GROUPS[group_name]:
                if key not in {"reach", "natural_size"}:
                    pool.extend([key] * (3 if key in signature else 1))
        unique = list(dict.fromkeys(pool))
        # Broad OVR is rebuilt from a large detailed-skill profile. Six isolated
        # one-point gains usually disappeared into rounding, so a prospect could
        # pass dozens of monthly development checks without visibly progressing.
        # Spend a wider training block while retaining potential and per-skill
        # soft caps; this improves realization, not the fighter's ceiling.
        point_budget = {1: 15, 2: 25, 3: 34}.get(max(1, min(3, int(amount))), 15)
        improved_keys = set()
        attempts = 0
        growth_chances = {
            key: self.detailed_skill_growth_chance(fighter, key, signature)
            for key in unique
        }
        while unique and len(improved_keys) < point_budget and attempts < point_budget * 5:
            weights = [max(0.01, growth_chances[key]) * (2.2 if key in signature else 1.0) for key in unique]
            key = random.choices(unique, weights=weights, k=1)[0]
            if random.random() <= growth_chances[key]:
                fighter.detailed_skills[key] = min(99, fighter.detailed_skills.get(key, 50) + 1)
                improved_keys.add(key)
            unique.remove(key)
            attempts += 1
        self.sync_broad_skills_from_details(fighter)
        ceiling = min(99, fighter.potential)
        if fighter.overall > ceiling:
            # A rounded broad rating can cross the ceiling after a batch. Undo
            # the least style-defining gains first until potential is respected.
            rollback = sorted(improved_keys, key=lambda key: (key in signature, fighter.detailed_skills.get(key, 50)))
            for key in rollback:
                fighter.detailed_skills[key] = max(1, fighter.detailed_skills.get(key, 50) - 1)
                self.sync_broad_skills_from_details(fighter)
                if fighter.overall <= ceiling:
                    break
        return max(0, fighter.overall - before)

    def development_realization_bonus(self, fighter):
        """Help rare high ceilings translate into rare elite adult fighters."""
        if fighter.age < 17 or fighter.age > 30 or fighter.potential < 70:
            return 0
        gap = max(0, fighter.potential - fighter.overall)
        if gap <= 4:
            return 0
        if fighter.potential >= 80:
            upside = max(0, fighter.potential - 84) * 1.15
            unrealized = max(0, gap - 5) * 0.75
            youth_runway = 4 if fighter.age <= 25 else 0
            return min(28, upside + unrealized + youth_runway)
        # The 70-79 band supplies credible major-promotion depth. These fighters
        # should usually mature beyond regional level, while their lower ceiling
        # still prevents this support rule from manufacturing elite talent.
        upside = max(0, fighter.potential - 70) * 0.45
        unrealized = max(0, gap - 5) * 0.55
        youth_runway = 3 if fighter.age <= 25 else 0
        return min(16, upside + unrealized + youth_runway)

    def regional_record_development_bonus(self, fighter):
        """Turn an excellent regional run into development momentum, not free ability."""
        if fighter.contract_type == "Developmental":
            wins, losses, draws = fighter.record_w, fighter.record_l, fighter.record_d
            months_since = 0
        else:
            wins = getattr(fighter, "regional_record_w", 0)
            losses = getattr(fighter, "regional_record_l", 0)
            draws = getattr(fighter, "regional_record_d", 0)
            recorded_month = getattr(fighter, "regional_record_month", 0)
            if not recorded_month:
                return 0
            months_since = max(0, self.month - recorded_month)
            if months_since > 24:
                return 0
        bouts = wins + losses + draws
        if bouts < 5:
            return 0
        win_rate = (wins + draws * 0.5) / bouts
        if losses == 0 and wins >= 7:
            bonus = 12
        elif bouts >= 10 and win_rate >= 0.80:
            bonus = 10
        elif bouts >= 8 and win_rate >= 0.75:
            bonus = 7
        elif win_rate >= 0.70:
            bonus = 4
        else:
            return 0
        if months_since > 12:
            bonus *= 0.5
        return bonus

    def monthly_development_score(self, fighter):
        return sum(value for _label, value in self.fighter_development_factors(fighter))

    def fighter_development_factors(self, fighter):
        """Return the exact additive inputs used by the monthly growth roll."""
        gym = self.gym_by_name(fighter.camp)
        camp_quality = self.gym_quality(fighter.camp)
        facilities = gym.facilities if gym else camp_quality
        specialty = self.gym_specialty_bonus(fighter, gym)
        dedication = fighter.detailed_skills.get("dedication", fighter.professionalism) if fighter.detailed_skills else fighter.professionalism
        # Development is a monthly opportunity, not a monthly guarantee. The
        # old weights made even an ordinary 25-year-old improve virtually every
        # month, which gradually filled a long save with 95-99 overall fighters.
        runway = max(0, fighter.prime_end - fighter.age) * 0.9
        early_development = 7 if fighter.age < fighter.prime_start else 0
        late_learning = max(0, fighter.prime_end + 2 - fighter.age) * 0.5
        form = max(0, fighter.momentum) * 2.5
        # Winning drives growth: real competition and confidence accelerate a
        # developing fighter far more than gym time alone. A win streak matters
        # most for the young and tapers off once a fighter is past their prime.
        win_streak = getattr(fighter, "career_win_streak", 0)
        if fighter.age <= fighter.prime_end:
            win_growth = min(9, win_streak * 1.7)
        elif fighter.age <= fighter.prime_end + 3:
            win_growth = min(5, win_streak * 0.9)
        else:
            win_growth = min(2, win_streak * 0.4)
        morale = fighter.morale * 0.10
        gym_rat = 9 if fighter.trait == "Gym Rat" else 0
        learner = 8 if fighter.trait == "Technical Learner" else 0
        adaptable = 4 if fighter.trait == "Adaptable" else 0
        momentum_trait = max(0, fighter.momentum) * 1.5 if fighter.trait == "Momentum Fighter" else 0
        room = max(0, fighter.potential - fighter.overall) * 0.65
        fatigue_drag = fighter.fatigue * 0.30 + fighter.injured * 10
        # A busy elite camp should lose some individual attention, but global
        # world growth must not turn a 95-quality gym into a development trap.
        crowd_drag = max(0, (1.0 - self.gym_attention_multiplier(gym)) * 16) if gym else 0
        realization = self.development_realization_bonus(fighter)
        structured_pathway = fighter.contract_type == "Developmental"
        pathway_bonus = 14 if structured_pathway and fighter.age <= 25 else 8 if structured_pathway and fighter.age <= 29 else 0
        recent_activity = 5 if fighter.age <= 29 and 0 < self.month - getattr(fighter, "last_fight_month", 0) <= 4 else 0
        development_age = 5 if fighter.age <= 23 else 3 if fighter.age <= 26 else 1 if fighter.age <= 29 else 0
        regional_form = self.regional_record_development_bonus(fighter)
        return [
            (f"Gym quality ({fighter.camp})", camp_quality * 0.25),
            ("Gym facilities", facilities * 0.08),
            ("Coaching and style fit", specialty * 0.55),
            ("Dedication / professionalism", dedication * 0.23),
            ("Age and remaining prime", runway + early_development + late_learning + development_age),
            (f"Potential room ({max(0, fighter.potential - fighter.overall)} OVR)", room + realization),
            ("Recent victories and momentum", form + momentum_trait + regional_form + win_growth),
            ("Motivation and morale", morale),
            ("Active competition", recent_activity + pathway_bonus),
            ("Learning traits", gym_rat + learner + adaptable),
            ("Fatigue and injuries", -fatigue_drag),
            ("Gym crowding", -crowd_drag),
        ]

    def fighter_development_explanation(self, fighter):
        """Player-facing, calculation-backed explanation of current development."""
        factors = self.fighter_development_factors(fighter)
        total = sum(value for _label, value in factors)
        positives = sorted(((label, value) for label, value in factors if value > 0.05), key=lambda row: row[1], reverse=True)
        negatives = sorted(((label, value) for label, value in factors if value < -0.05), key=lambda row: row[1])
        runway = max(0, fighter.potential - fighter.overall)
        if fighter.age > fighter.prime_end:
            outlook = "DECLINE PHASE"
        elif runway <= 0:
            outlook = "AT PROJECTED CEILING"
        elif total >= 115:
            outlook = "STRONG GROWTH ENVIRONMENT"
        elif total >= 85:
            outlook = "POSITIVE DEVELOPMENT ENVIRONMENT"
        else:
            outlook = "LIMITED DEVELOPMENT ENVIRONMENT"
        return {"score": round(total, 1), "outlook": outlook, "positive": positives, "negative": negatives}

    def monthly_decline_score(self, fighter):
        years_past_prime = max(0, fighter.age - fighter.prime_end)
        # A good camp can delay decline, never erase the calendar indefinitely.
        age_drag = years_past_prime * 23 + max(0, years_past_prime - 3) * 14
        # Absolute-age erosion: regardless of when an individual prime ended, the
        # late 30s bring real physical decline that a late prime cannot fully hide.
        hard_age = max(0, fighter.age - 37) ** 1.7 * 8
        losing = max(0, -fighter.momentum) * 12
        losses = max(0, fighter.record_l - fighter.record_w * 0.55) * 2.4
        morale_drag = max(0, 45 - fighter.morale) * 0.8
        injury_drag = fighter.injury_proneness * 0.25 + fighter.injured * 16 + fighter.fatigue * 0.25
        professionalism_buffer = fighter.professionalism * 0.35
        form_buffer = max(0, fighter.momentum) * 5 + max(0, fighter.morale - 65) * 0.18
        veteran_buffer = 12 if fighter.trait in ("Veteran Savvy", "Warrior Spirit") else 0
        gym = self.gym_by_name(fighter.camp)
        camp_buffer = self.gym_quality(fighter.camp) * 0.16 + (gym.facilities if gym else 45) * 0.08
        elite_drag = max(0, fighter.overall - 92) * max(0, years_past_prime - 1) * 1.4
        # Buffers slow decline but cannot cancel hard age; only a fraction of the
        # late-30s erosion can be resisted by professionalism, camp and form.
        resistible = professionalism_buffer + camp_buffer + form_buffer + veteran_buffer
        if fighter.age >= 38:
            resistible = min(resistible, hard_age * 0.4)
        return age_drag + hard_age + losing + losses + morale_drag + injury_drag + elite_drag - resistible

    def veteran_resurgence_chance(self, fighter):
        """Rare late-career growth: form and durability can beat the calendar for a while."""
        if fighter.age <= fighter.prime_end or fighter.age >= 45 or fighter.momentum < 3:
            return 0.0
        resilience = self.ds(fighter, "resilience", fighter.toughness)
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        quality = (resilience + conditioning + fighter.professionalism + fighter.motivation) / 400
        trait = 0.012 if fighter.trait in ("Veteran Savvy", "Warrior Spirit") else 0
        streak = min(0.016, fighter.momentum * 0.003)
        age_drag = max(0, fighter.age - fighter.prime_end - 1) * 0.004
        return max(0.0, min(0.045, 0.004 + quality * 0.012 + trait + streak - age_drag))

    def ai_show_chance(self, promo):
        personality = getattr(promo, "show_personality", "Balanced")
        chance = {
            "Super Shows": 0.12,
            "Seasonal": 0.10,
            "Star Builder": 0.17,
            "Prospect Builder": 0.22,
            "Frequent Small Cards": 0.30,
            "Regional Development": 0.42,
            "Balanced": 0.16,
        }.get(personality, 0.16)
        strategy = self.promotion_strategy(promo)
        mode = strategy.get("current_mode", "Balanced")
        executive = getattr(promo, "executive", {}) or {}
        executive_drive = (executive.get("aggression", 55) - executive.get("discipline", 55)) / 700
        mandate = executive.get("board_mandate", "")
        mandate_drive = 0.035 if mandate == "Event Cadence" and executive.get("mandate_progress", 0) < 100 else (-0.035 if mandate == "Financial Stability" and executive.get("mandate_progress", 0) < 100 else 0)
        pressure = strategy.get("financial_pressure", 0) / 900
        roster_health = (strategy.get("roster_health", 70) - 70) / 900
        # Deep, healthy rosters can support a more regular schedule. This used
        # to cap out at a 208-fighter roster, giving a 373-fighter global
        # flagship like the UFC no more credit than a mid-sized promotion less
        # than half its size. Availability, finance and recovery checks still
        # decide whether any particular card can actually take place; the
        # overall chance stays bounded by the final clamp below regardless.
        depth_drive = max(0, len(getattr(promo, "roster", [])) - 100) / 1200
        show_chance = chance - (0.08 if mode == "Financial Recovery" else 0) + (0.035 if mode == "Star Chasing" else 0) + executive_drive + mandate_drive - pressure + roster_health + depth_drive
        # A 320+ fighter major needs regular full cards to sustain 2-3 annual
        # appearances per athlete. Personality-only schedules left several
        # major rosters below two fights and created a permanent backlog.
        if len(getattr(promo, "roster", [])) >= 280 and mode != "Financial Recovery":
            show_chance = max(show_chance, 0.72)
        # That floor was a cliff, so a company carrying fewer than 280 fighters
        # dropped back to its personality rate however many people it had signed.
        # A seasonal, cost-controlled promotion with 230 fighters ran seven cards
        # a year -- around half a fight each -- and left 65 of them idle for
        # years, several for over eight. The requirement scales with the roster
        # actually carried: the divisor reproduces the 280-fighter floor above
        # and extends the same standard downward instead of falling off a step.
        active_roster = sum(1 for member in getattr(promo, "roster", []) if not getattr(member, "retired", False))
        if active_roster >= 120 and mode != "Financial Recovery":
            show_chance = max(show_chance, min(0.72, active_roster / 446))
        # The 400-fighter flagship needs roughly 36 full cards per year to
        # maintain the same activity target at its larger roster scale.
        if promo.name == "Ultimate Fighting Championship" and mode != "Financial Recovery":
            show_chance = max(show_chance, 0.76)
        # BAMMA opens with roughly 190 athletes. At 12-13 bouts per card it
        # needs about 23 shows to sustain three appearances per active fighter.
        if promo.name == PLAYER_PROMOTION_NAME and mode != "Financial Recovery":
            show_chance = max(show_chance, 0.44)
        return max(0.04, min(0.78, show_chance))

    def ai_should_run_show(self, promo):
        strategy = self.update_ai_promotion_strategy(promo)
        if promo.cash < max(120_000, promo.size * 6500):
            return False
        ready = [f for f in promo.roster if self.fighter_available_for_date(f, day=self.ai_card_day(promo)) and f.fatigue < self.ai_fatigue_limit(promo)]
        if len(ready) < self.ai_min_ready_fighters(promo):
            return False
        if strategy.get("current_mode") == "Financial Recovery" and promo.cash < max(350_000, promo.size * 12_000):
            return random.random() < 0.18
        return random.random() < self.ai_show_chance(promo)

    def ai_fatigue_limit(self, promo):
        base = {"Super Shows": 32, "Seasonal": 36, "Prospect Builder": 48, "Frequent Small Cards": 52}.get(getattr(promo, "show_personality", "Balanced"), 42)
        return base - (6 if self.promotion_strategy(promo).get("current_mode") == "Title Push" else 0)

    def ai_min_ready_fighters(self, promo):
        return {"Super Shows": 14, "Seasonal": 12, "Prospect Builder": 11, "Frequent Small Cards": 11}.get(getattr(promo, "show_personality", "Balanced"), 11)

    def ai_card_day(self, promo):
        """The weekday an AI promotion runs its card on.

        Real promotions run at the weekend, and the AI should book the same way
        so its camps and turnarounds behave like the player's. Kept stable per
        promotion and month rather than re-rolled, so a company has a settled
        slot instead of drifting across the week at random.
        """
        seed = sum(ord(char) for char in str(getattr(promo, "name", ""))) + self.month
        preferred = (6, 6, 6, 5, 7, 6, 5, 3)[seed % 8]
        # Late-week cards buy marginally more recovery, but only when that
        # changes who can credibly appear. Each promotion still has a stable
        # default broadcast rhythm instead of drifting randomly.
        candidates = (preferred,) if preferred not in (5, 6, 7) else tuple(dict.fromkeys((preferred, 5, 6, 7)))
        limit = self.ai_fatigue_limit(promo)
        def readiness(day):
            ready = [fighter for fighter in promo.roster if not fighter.retired and self.fighter_available_for_date(fighter, day=day) and fighter.fatigue < limit]
            priority = sum(1 for fighter in ready if fighter.champion or getattr(fighter, "owed_title_shot", False) or getattr(fighter, "ranking_position", 99) <= 2)
            return len(ready) + priority * 2
        return max(candidates, key=lambda day: (readiness(day), -abs(day - preferred)))

    def ai_contender_booking_note(self, promo, fighter, day=None):
        """Explain the real scheduling constraint behind a title-picture athlete."""
        day = self.normalize_day(day if day is not None else self.ai_card_day(promo), LEGACY_EVENT_DAY)
        if not fighter or fighter.injured:
            return "medical recovery"
        if not self.fighter_available_for_date(fighter, day=day):
            return f"available {self.fighter_return_label(fighter)}"
        rest_days = self.fighter_rest_days(fighter, day=day)
        if fighter.fatigue >= self.ai_fatigue_limit(promo):
            return f"recovery priority ({self.fighter_fatigue_label(fighter)})"
        if rest_days is not None and rest_days < 42:
            return f"short turnaround ({rest_days} days since last fight)"
        return "ready for booking"

    def update_ai_title_roadmap(self, promo, day=None):
        """Persist a compact contender queue so title inactivity is visible and managed."""
        strategy = self.promotion_strategy(promo)
        roadmap = []
        for weight in WEIGHTS:
            for gender in ("Male", "Female"):
                if not self.promotion_division_open(promo, gender, weight):
                    continue
                holder_name = self.ai_primary_title_holder_name(promo, gender, weight)
                contenders = sorted(
                    (fighter for fighter in promo.roster if not fighter.retired and fighter.gender == gender and fighter.weight == weight and fighter.name != holder_name),
                    key=lambda fighter: (not getattr(fighter, "owed_title_shot", False), getattr(fighter, "ranking_position", 999), -fighter.rank_score),
                )
                if not contenders:
                    continue
                leader = contenders[0]
                urgency = self.ai_title_contender_pressure(promo, gender, weight)
                if urgency >= 2 or getattr(leader, "owed_title_shot", False):
                    champion = next((fighter for fighter in promo.roster if fighter.name == holder_name), None)
                    roadmap.append({
                        "division": f"{gender} {weight}", "champion": holder_name or "Vacant", "contender": leader.name,
                        "status": self.ai_contender_booking_note(promo, champion, day) if champion else "vacant title resolution",
                        "urgency": urgency, "month": self.month,
                    })
        strategy["title_roadmap"] = sorted(roadmap, key=lambda row: (-row["urgency"], row["division"]))[:16]
        return strategy["title_roadmap"]

    def apply_ai_camp(self, fighter, promo):
        if not self.gym_by_name(fighter.camp):
            target = self.gym_by_name(self.suggest_camp_for_fighter(fighter, getattr(promo, "region", "USA")))
            self.move_fighter_to_gym(fighter, target, "Joined a recognised training room")
        gym = self.gym_by_name(fighter.camp)
        quality = self.gym_quality(fighter.camp)
        weeks = random.randint(3, 10) if getattr(promo, "show_personality", "Balanced") != "Frequent Small Cards" else random.randint(2, 6)
        # An AI card runs on a weekday too, so its camp is measured to that day
        # rather than to the start of the week. Booking later in the week buys
        # the same extra preparation it does for the player.
        card_day = self.normalize_day(getattr(self, "_active_card_day", None), LEGACY_EVENT_DAY)
        camp_length_weeks = weeks + (card_day - LEGACY_EVENT_DAY) / DAYS_PER_WEEK
        professionalism = fighter.professionalism / 100
        specialty = self.gym_specialty_bonus(fighter, gym)
        fighter.camp_quality = quality
        fighter.camp_weeks = weeks
        attention = self.gym_attention_multiplier(gym)
        base_boost = round(camp_length_weeks * (quality + specialty) / 125 * (0.7 + professionalism * 0.35) / 3 * attention)
        fighter.camp_boost = min(12, max(0, base_boost + self.camp_form_variance(fighter, gym)))
        self.apply_gym_camp_micro_improvement(fighter, gym, weeks)

    def matchup_history_penalty(self, a, b):
        """Softly discourage stale repeat pairings without forbidding rematches."""
        if not a or not b or a is b:
            return 0.0
        meetings, latest_month = self.matchup_history_summary(a, b)
        if not meetings:
            return 0.0
        gap = max(0, self.month - latest_month) if latest_month else 18
        recency = 0.0
        if gap <= 2:
            recency = 105.0
        elif gap <= 4:
            recency = 72.0
        elif gap <= 8:
            recency = 38.0
        elif gap <= 14:
            recency = 16.0
        else:
            recency = 4.0
        penalty = recency + max(0, meetings - 1) * 13.0
        mutual_rivalry = a.rival == b.name and b.rival == a.name
        heat = max(getattr(a, "rivalry_heat", 0), getattr(b, "rivalry_heat", 0))
        if mutual_rivalry:
            penalty *= max(0.28, 1.0 - heat / 120)
        if getattr(a, "rivalry_rematch_due", False) or getattr(b, "rivalry_rematch_due", False):
            penalty *= 0.45
        return round(penalty, 2)

    def matchup_history_summary(self, a, b):
        """Return confirmed previous meetings and the newest recorded month."""
        cache = getattr(self, "_matchup_history_cache", None)
        if cache is None:
            cache = self._matchup_history_cache = {}
        # Fight-history parsing is expensive when the AI considers hundreds of
        # pairs. Lengths make the entry self-invalidating after a new result.
        key = tuple(sorted((getattr(a, "fighter_id", a.name), getattr(b, "fighter_id", b.name)))) + (len(getattr(a, "fight_history", []) or []), len(getattr(b, "fight_history", []) or []))
        cached = cache.get(key)
        if cached is not None:
            return cached
        meetings, latest_month = 0, None
        opponent_name = b.name.casefold()
        for entry in (getattr(a, "fight_history", None) or [])[:80]:
            text = str(entry)
            if opponent_name not in text.casefold() or (" def. " not in text and "fought to a draw" not in text):
                continue
            meetings += 1
            if "Month " in text:
                try:
                    month = int(text.split("Month ", 1)[1].split(" ", 1)[0])
                    latest_month = max(latest_month or 0, month)
                except (TypeError, ValueError):
                    pass
        result = (meetings, latest_month)
        if len(cache) > 50000:
            cache.clear()
        cache[key] = result
        return result

    def matchup_series_record(self, a, b):
        """Return head-to-head wins from a's perspective, including draws."""
        record = {"meetings": 0, "a_wins": 0, "b_wins": 0, "draws": 0}
        if not a or not b:
            return record
        a_name = a.name.casefold()
        b_name = b.name.casefold()
        for entry in (getattr(a, "fight_history", None) or [])[:120]:
            text = str(entry)
            lowered = text.casefold()
            if b_name not in lowered:
                continue
            if "fought to a draw" in lowered:
                record["meetings"] += 1
                record["draws"] += 1
                continue
            match = re.search(r":\s*(.+?)\s+def\.\s+(.+?)\s+by\s+", text, re.IGNORECASE)
            if not match:
                continue
            winner_name = match.group(1).strip().casefold()
            loser_name = match.group(2).strip().casefold()
            if {winner_name, loser_name} != {a_name, b_name}:
                continue
            record["meetings"] += 1
            if winner_name == a_name:
                record["a_wins"] += 1
            elif winner_name == b_name:
                record["b_wins"] += 1
        return record

    def matchup_display_name(self, a, b):
        """Return the promotional matchup title, including a confirmed rematch number."""
        if not a or not b:
            return "Main Event"
        meetings, _latest_month = self.matchup_history_summary(a, b)
        ordinal = meetings + 1
        numerals = (
            (1000, "M"), (900, "CM"), (500, "D"), (400, "CD"),
            (100, "C"), (90, "XC"), (50, "L"), (40, "XL"),
            (10, "X"), (9, "IX"), (5, "V"), (4, "IV"), (1, "I"),
        )
        remaining, roman = ordinal, ""
        for value, symbol in numerals:
            while remaining >= value:
                roman += symbol
                remaining -= value
        suffix = f" {roman}" if meetings else ""
        return f"{a.name} vs {b.name}{suffix}"

    def fighter_needs_matchmaking_rebuild(self, fighter):
        """Flag a poor run for gentler opposition, not fabricated results."""
        bouts = fighter.record_w + fighter.record_l + fighter.record_d
        win_rate = fighter.record_w / max(1, bouts)
        return bouts >= 10 and fighter.record_l >= fighter.record_w + 6 and win_rate < 0.30 and fighter.momentum <= -3

    def ai_matchup_is_stale(self, a, b, title=False):
        """Decline a repeatedly lopsided, non-story rematch while alternatives develop."""
        meetings, latest_month = self.matchup_history_summary(a, b)
        if meetings < 5:
            return False
        gap = max(0, self.month - latest_month) if latest_month else 18
        rivalry = a.rival == b.name and b.rival == a.name and max(a.rivalry_heat, b.rivalry_heat) >= 55
        rematch_due = getattr(a, "rivalry_rematch_due", False) or getattr(b, "rivalry_rematch_due", False)
        if rivalry or rematch_due:
            return meetings >= 9 and gap <= 5 and not title
        a_bouts = a.record_w + a.record_l + a.record_d
        b_bouts = b.record_w + b.record_l + b.record_d
        record_gap = abs(a.record_w / max(1, a_bouts) - b.record_w / max(1, b_bouts))
        struggling_a = self.fighter_needs_matchmaking_rebuild(a)
        struggling_b = self.fighter_needs_matchmaking_rebuild(b)
        # A series can become commercially exhausted even after a long break.
        # This is intentionally narrower than a hard rematch limit: it applies
        # only when one fighter is still in a severe slide and the historical
        # result gap makes another non-title bout implausible. A comeback, a
        # genuine rivalry, or a title context can reopen the matchup.
        exhausted_series = meetings >= 10 and record_gap >= 0.45 and (struggling_a or struggling_b)
        if exhausted_series and gap <= 48:
            return True
        # A recent fifth non-rival meeting with a visibly divergent career is no
        # longer a credible booking. The division waits for a fresh contender.
        return gap <= 14 and (meetings >= 7 or (meetings >= 5 and record_gap >= 0.28))

    def ai_primary_title_holder_name(self, promo, gender, weight):
        """Return a legitimate current holder, independent of this week's readiness.

        AI matchmaking receives a reduced ``ready`` pool. Looking for a champion
        only inside that pool made a fatigued or injured holder indistinguishable
        from a genuinely vacant belt and allowed contenders to steal the title
        without ever fighting the champion.
        """
        key = self.belt_key(gender, weight)
        holder_name = str((getattr(promo, "belts", {}) or {}).get(key, "") or "")
        if not holder_name:
            return ""
        holder = next((fighter for fighter in promo.roster if fighter.name == holder_name), None)
        if not holder or holder.retired or holder.gender != gender or holder.weight != weight:
            return ""
        return holder_name

    def ai_divisional_title_bout_is_valid(self, promo, a, b):
        """A non-vacant AI belt can only be contested by its recognised holder."""
        if a.gender != b.gender or a.weight != b.weight:
            return False
        holder_name = self.ai_primary_title_holder_name(promo, a.gender, a.weight)
        return not holder_name or holder_name in {a.name, b.name}

    def ai_title_contender_pressure(self, promo, gender, weight):
        """Return urgency for an AI division's leading contender getting a shot."""
        contenders = sorted(
            (
                fighter for fighter in promo.roster
                if not fighter.retired and fighter.gender == gender and fighter.weight == weight
                and not fighter.champion
            ),
            key=lambda fighter: (
                getattr(fighter, "ranking_position", 999),
                -getattr(fighter, "rank_score", 0),
            ),
        )
        if not contenders:
            return 0
        leader = contenders[0]
        rank = getattr(leader, "ranking_position", 999)
        streak = max(0, int(getattr(leader, "career_win_streak", 0) or 0))
        if getattr(leader, "owed_title_shot", False):
            return 4
        if rank == 1 and streak >= 8:
            return 3
        if rank == 1 and streak >= 5:
            return 2
        return 1 if rank == 1 else 0

    def ai_matchmaking_rank_gap_limit(self, a, b):
        """Keep routine AI matchmaking on a credible divisional ladder."""
        ranks = [
            rank for rank in (getattr(a, "ranking_position", 0), getattr(b, "ranking_position", 0))
            if rank > 0
        ]
        best_rank = min(ranks, default=99)
        if best_rank <= 5:
            return 6
        if best_rank <= 10:
            return 8
        if best_rank <= 20:
            return 12
        return 16

    def build_ai_card(self, promo, ready, target):
        """Matchmake a believable AI card: title fights for champions vs top contenders,
        grudge matches for rivalries, ranking-based pairings for the rest, and a
        star-driven main event. Returns a list of fight dicts."""
        # Old saves or editor imports can contain duplicate references. Treat the
        # first instance as canonical before matchmaking, then validate again
        # before returning the card.
        unique_ready = {}
        for fighter in ready:
            unique_ready.setdefault(fighter.name, fighter)
        ready = list(unique_ready.values())
        belts = promo.belts or {}
        strategy = self.promotion_strategy(promo)
        mode = strategy.get("current_mode", "Balanced")
        used = set()
        fights = []
        inactive = {fighter.name: max(0, self.month - getattr(fighter, "last_fight_month", 0)) for fighter in ready}
        divisions = [(gender, weight) for weight in WEIGHTS for gender in ("Male", "Female") if self.promotion_division_open(promo, gender, weight)]
        random.shuffle(divisions)
        # Vacant championships need a sporting resolution before routine
        # defenses consume the card's limited title-fight slots.
        divisions.sort(key=lambda division: (
            bool(belts.get(self.belt_key(*division))),
            -self.ai_title_contender_pressure(promo, *division),
        ))

        def overdue_tier(fighter):
            """How badly a fighter is owed a booking, in six-month steps.

            Every booking mode orders by quality of one kind or another, so a
            fighter who sits just below the cut is never reached again: real
            saves had ranked, healthy, unfatigued fighters idle for six years
            while the same names were rebooked. The inactivity figure was
            already being measured here and then ignored. Capped so a long
            wait moves someone up the queue without letting seniority override
            merit permanently.
            """
            return min(3, inactive.get(fighter.name, 0) // 6)

        def pool_for(gender, weight):
            pool = [f for f in ready if f.gender == gender and f.weight == weight and f.name not in used]
            if mode == "Star Chasing":
                pool.sort(key=lambda f: (overdue_tier(f), f.popularity + f.star_quality, f.overall, getattr(f, "rank_score", 0)), reverse=True)
            elif mode == "Prospect Rebuild":
                pool.sort(key=lambda f: (overdue_tier(f), f.potential - f.overall, -f.age, f.momentum, f.overall), reverse=True)
            else:
                pool.sort(key=lambda f: (0 if f.champion else 1, -overdue_tier(f), getattr(f, "ranking_position", 999), -getattr(f, "rank_score", 0), -f.overall))
            return pool

        # 0) Retirement fights: aging fighters who have declared retirement get
        # a final bout before they can leave the active roster.
        pending_retirees = sorted(
            [fighter for fighter in ready if getattr(fighter, "retirement_pending", False)],
            key=lambda fighter: (self.month - getattr(fighter, "retirement_requested_month", self.month), fighter.age, fighter.popularity),
            reverse=True,
        )
        for fighter in pending_retirees:
            if len(fights) >= target or fighter.name in used:
                continue
            opponents = [
                other for other in ready
                if other.name not in used and other is not fighter
                and other.gender == fighter.gender and other.weight == fighter.weight
                and not getattr(other, "retirement_pending", False)
            ]
            if not opponents:
                opponents = [
                    other for other in ready
                    if other.name not in used and other is not fighter
                    and other.gender == fighter.gender and other.weight == fighter.weight
                ]
            if not opponents:
                continue
            opponent = min(opponents, key=lambda other: (
                abs(other.overall - fighter.overall)
                + abs((other.record_w + other.record_l) - (fighter.record_w + fighter.record_l)) * 0.2
                + self.matchup_history_penalty(fighter, other)
            ))
            used.update({fighter.name, opponent.name})
            fights.append({"a": fighter, "b": opponent, "title": False, "main": False,
                           "grudge": fighter.rival == opponent.name or opponent.rival == fighter.name,
                           "booking_reason": "Final fight before retirement"})

        # 1) Title fights: champions defend against leading contenders, while
        # established vacant championships are contested by the two strongest
        # credible available contenders. Only initial world seeding appoints
        # title holders; an active universe decides later vacancies in fights.
        max_titles = (2 if promo.size >= 60 else 1) + (1 if mode == "Title Push" and promo.size >= 75 else 0)
        titles = 0
        for gender, weight in divisions:
            if titles >= max_titles or len(fights) >= target:
                break
            # The holder is resolved from the full promotion roster, not the
            # currently-ready pool. An unavailable champion keeps their belt.
            champ_name = self.ai_primary_title_holder_name(promo, gender, weight)
            pool = pool_for(gender, weight)
            champ = next((f for f in pool if f.name == champ_name), None)
            key = self.belt_key(gender, weight)
            if not champ_name and (promo.belt_history or {}).get(key) and len(pool) >= 2:
                pair = next(
                    (
                        (a, b)
                        for index, a in enumerate(pool[:8])
                        for b in pool[index + 1:8]
                        if not self.ai_matchup_is_stale(a, b, title=True)
                    ),
                    None,
                )
                if pair:
                    a, b = pair
                    used.update({a.name, b.name})
                    fights.append({"a": a, "b": b, "title": True, "main": False,
                                   "grudge": a.rival == b.name or b.rival == a.name,
                                   "booking_reason": "Vacant championship between the two leading available contenders"})
                    titles += 1
                    continue
            contender_pressure = self.ai_title_contender_pressure(promo, gender, weight)
            defense_chance = 0.52 if mode in ("Title Push", "Contender Cycle") else 0.4
            if contender_pressure >= 3:
                defense_chance = max(defense_chance, 0.9)
            elif contender_pressure >= 2:
                defense_chance = max(defense_chance, 0.7)
            if champ and len(pool) >= 2 and random.random() < defense_chance:
                contenders = [fighter for fighter in pool if fighter.name != champ.name
                              and not self.ai_matchup_is_stale(champ, fighter, title=True)]
                contender = min(
                    contenders,
                    key=lambda fighter: (
                        0 if getattr(fighter, "owed_title_shot", False) else 1,
                        getattr(fighter, "ranking_position", 999),
                        -getattr(fighter, "career_win_streak", 0),
                        self.matchup_history_penalty(champ, fighter),
                    ),
                    default=None,
                )
                if contender:
                    used.update({champ.name, contender.name})
                    fights.append({"a": champ, "b": contender, "title": True, "main": False,
                                   "grudge": champ.rival == contender.name or contender.rival == champ.name, "booking_reason": "Title defense against the highest available contender"})
                    titles += 1

        # A reigning champion who was not selected for a defense sits out this
        # card. Do not let later rivalry, prospect, or depth matchmaking turn
        # their appearance into a non-title bout in their own division.
        protected_champions = {name for name in belts.values() if name} - used

        # 2) Grudge matches: booked rivalries in the same division.
        for gender, weight in divisions:
            if len(fights) >= target:
                break
            pool = [fighter for fighter in pool_for(gender, weight) if fighter.name not in protected_champions]
            for fighter in pool:
                if len(fights) >= target or fighter.name in used:
                    continue
                if fighter.rival:
                    # A rivalry is valuable only while it remains a credible
                    # sporting contest. Extremely lopsided old rivalries stay
                    # dormant instead of displacing most of a normal card.
                    rivals = [o for o in pool if o.name == fighter.rival and o.name not in used
                              and abs(o.overall - fighter.overall) <= 10]
                    opp = min(
                        rivals,
                        key=lambda other: abs(other.overall - fighter.overall) * 2 + self.matchup_history_penalty(fighter, other),
                        default=None,
                    )
                    if opp:
                        used.update({fighter.name, opp.name})
                        fights.append({"a": fighter, "b": opp, "title": False, "main": False, "grudge": True, "booking_reason": "Active rivalry matchup"})

        # 3) Ranking-based pairings: adjacent-ranked contenders fight.
        # A signed blue-chip prospect gets a visible development opportunity,
        # even before their rank catches up with their ceiling.
        prospects = [fighter for fighter in ready if fighter.name not in used and fighter.name not in protected_champions and fighter.age <= 29
                     and (fighter.potential >= 90 or (fighter.potential - fighter.overall >= 12 and fighter.potential >= 84))]
        prospects.sort(key=lambda fighter: (fighter.potential, fighter.overall, fighter.record_w - fighter.record_l), reverse=True)
        prospect_showcase_limit = 2 if promo.size >= 65 and target >= 8 else 1
        prospect_showcases = 0
        for prospect in prospects:
            if len(fights) >= target or prospect_showcases >= prospect_showcase_limit:
                break
            opponents = [fighter for fighter in ready if fighter.name not in used and fighter.name not in protected_champions and fighter.name != prospect.name
                          and fighter.gender == prospect.gender and fighter.weight == prospect.weight
                         and abs(fighter.overall - prospect.overall) <= 6
                         and abs(getattr(fighter, "ranking_position", 999) - getattr(prospect, "ranking_position", 999)) <= self.ai_matchmaking_rank_gap_limit(prospect, fighter)
                         and not self.ai_matchup_is_stale(prospect, fighter)]
            if not opponents:
                continue
            opponent = min(opponents, key=lambda fighter: (
                abs(fighter.overall - prospect.overall)
                + abs(getattr(fighter, "ranking_position", 999) - getattr(prospect, "ranking_position", 999)) * 1.8
                + abs((fighter.record_w + fighter.record_l) - (prospect.record_w + prospect.record_l)) * 0.25
                + self.matchup_history_penalty(prospect, fighter)
            ))
            used.update({prospect.name, opponent.name})
            prospect_showcases += 1
            fights.append({"a": prospect, "b": opponent, "title": False, "main": False,
                           "grudge": prospect.rival == opponent.name or opponent.rival == prospect.name, "booking_reason": "Development opportunity for a high-upside prospect"})

        # 4) Ranking-based pairings: adjacent-ranked contenders fight. Rotate
        # divisions instead of draining one pool into an entire card; two bouts
        # is enough room for a title fight plus a supporting divisional contest.
        division_bouts = {}
        for fight in fights:
            key = (fight["a"].gender, fight["a"].weight)
            division_bouts[key] = division_bouts.get(key, 0) + 1
        max_bouts_per_division = 2
        for gender, weight in divisions:
            if len(fights) >= target:
                break
            pool = [fighter for fighter in pool_for(gender, weight) if fighter.name not in protected_champions]
            division_key = (gender, weight)
            while len(fights) < target and division_bouts.get(division_key, 0) < max_bouts_per_division:
                available = [fighter for fighter in pool if fighter.name not in used]
                if len(available) < 2:
                    break
                pair_options = []
                for index, a_option in enumerate(available[:-1]):
                    for b_option in available[index + 1:]:
                        rating_gap = abs(b_option.overall - a_option.overall)
                        rebuild_a = self.fighter_needs_matchmaking_rebuild(a_option)
                        rebuild_b = self.fighter_needs_matchmaking_rebuild(b_option)
                        if self.ai_matchup_is_stale(a_option, b_option):
                            continue
                        # A fighter can end up with nobody inside the normal
                        # gaps at all: the only opponent within range is the
                        # champion, who is held back for title fights, and the
                        # rest of the division sits too far below. Nothing
                        # relaxed, so they simply never fought again -- real
                        # saves stranded a top-ranked contender for five years
                        # this way. Widen both gaps as the layoff grows, so a
                        # stranded fighter takes a step down in opposition
                        # rather than waiting for a bout that cannot exist.
                        # Untouched for anyone fighting at a normal cadence.
                        stranded = min(12, max(0, max(inactive.get(a_option.name, 0), inactive.get(b_option.name, 0)) - 6) // 2)
                        # A struggling fighter gets a fresh, sensible reset
                        # matchup rather than another punitive rematch. The
                        # allowance is deliberately small: it may avoid an
                        # exact top-contender draw, but it cannot manufacture a
                        # "get-well" mismatch or a presumed win.
                        if rating_gap > (9 if rebuild_a or rebuild_b else 6) + stranded:
                            continue
                        rank_gap = abs(getattr(b_option, "ranking_position", 999) - getattr(a_option, "ranking_position", 999))
                        if rank_gap > self.ai_matchmaking_rank_gap_limit(a_option, b_option) + stranded:
                            continue
                        form_gap = abs(getattr(b_option, "momentum", 0) - getattr(a_option, "momentum", 0))
                        protect_a = mode == "Prospect Rebuild" and a_option.age <= 26 and a_option.potential - a_option.overall >= 7
                        protect_b = mode == "Prospect Rebuild" and b_option.age <= 26 and b_option.potential - b_option.overall >= 7
                        protection_penalty = int(protect_a and b_option.overall > a_option.overall + 3)
                        protection_penalty += int(protect_b and a_option.overall > b_option.overall + 3)
                        variety_penalty = self.matchup_history_penalty(a_option, b_option)
                        a_bouts = a_option.record_w + a_option.record_l + a_option.record_d
                        b_bouts = b_option.record_w + b_option.record_l + b_option.record_d
                        record_gap = abs(a_option.record_w / max(1, a_bouts) - b_option.record_w / max(1, b_bouts))
                        rebuild_target = 0
                        if rebuild_a ^ rebuild_b:
                            rebuild_fighter = a_option if rebuild_a else b_option
                            opponent = b_option if rebuild_a else a_option
                            # Prefer a close, fresh contest with a slight
                            # practical step back in opposition. The target is
                            # only three OVR below, so stylistic matchup,
                            # readiness, and the exchange engine still govern
                            # the outcome.
                            rebuild_target = abs((opponent.overall - rebuild_fighter.overall) + 3) * 1.4
                        inactivity_priority = min(28, (inactive.get(a_option.name, 0) + inactive.get(b_option.name, 0)) * 1.8)
                        pair_options.append(((protection_penalty, rating_gap * 2.2 + rank_gap * 2.8 + form_gap * 0.8 + record_gap * 26 + variety_penalty + rebuild_target - inactivity_priority, rating_gap), a_option, b_option))
                if not pair_options:
                    break
                _, a, b = min(pair_options, key=lambda item: item[0])
                used.update({a.name, b.name})
                reason = "Adjacent-ranked divisional matchup"
                if inactive.get(a.name, 0) >= 8 or inactive.get(b.name, 0) >= 8:
                    reason = "Activity-restoring matchup for a long-inactive fighter"
                fights.append({"a": a, "b": b, "title": False, "main": False,
                               "grudge": a.rival == b.name or b.rival == a.name, "booking_reason": reason})
                division_bouts[division_key] = division_bouts.get(division_key, 0) + 1

        if not fights:
            return []

        # Retirement commitments and migrated cards can enter the builder
        # before normal title selection. As a final invariant, any bout in the
        # recognized champion's own division is a championship fight.
        for fight in fights:
            a, b = fight["a"], fight["b"]
            holder = self.ai_primary_title_holder_name(promo, a.gender, a.weight)
            if a.gender == b.gender and a.weight == b.weight and holder in {a.name, b.name}:
                if not fight.get("title"):
                    fight["title"] = True
                    fight["booking_reason"] += "; reigning champion's divisional appearance requires a title defense"

        # 5) Main event: choose the strongest *headline*, not merely the first
        # title fight found. Belts matter, but a huge rivalry or two established
        # stars can legitimately headline over a thin divisional title bout.
        def headline_score(fight):
            a, b = fight["a"], fight["b"]
            star_draw = (
                a.popularity + b.popularity
                + (a.star_quality + b.star_quality) * 0.55
                + (a.media_presence + b.media_presence) * 0.24
                + (a.media_heat + b.media_heat) * 0.42
                + (a.charisma + b.charisma) * 0.14
            )
            sporting_weight = (a.overall + b.overall) * 0.16
            champion_weight = 14 * sum(1 for fighter in (a, b) if fighter.champion)
            title_weight = 34 if fight.get("title") else 0
            rivalry_weight = 30 + self.rivalry_heat_between(a, b) * 0.35 if fight.get("grudge") else 0
            momentum_weight = max(0, a.momentum + b.momentum) * 1.4
            return star_draw + sporting_weight + champion_weight + title_weight + rivalry_weight + momentum_weight

        main_fight = max(fights, key=headline_score)
        main_fight["main"] = True
        for fight in fights:
            if fight.get("main"):
                fight["booking_reason"] += "; elevated to main event by headline value (stars, title stakes, rivalry and current heat)"
        validated = []
        booked_names = set()
        for fight in fights:
            a, b = fight["a"], fight["b"]
            if a.name == b.name or a.name in booked_names or b.name in booked_names:
                continue
            booked_names.update((a.name, b.name))
            validated.append(fight)
        if validated and not any(fight.get("main") for fight in validated):
            max(validated, key=headline_score)["main"] = True
        ordered = sorted(validated, key=headline_score, reverse=True)
        for index, fight in enumerate(ordered):
            if fight.get("main"):
                fight["tier"] = "Main Card"
                fight["card_position"] = "Main Event"
            elif index == 1:
                fight["tier"] = "Main Card"
                fight["card_position"] = "Co-Main Event"
                fight["booking_reason"] += "; selected as co-main by event value"
            elif index < max(4, len(ordered) // 2):
                fight["tier"] = "Main Card"
                fight["card_position"] = "Main Card"
            elif index < max(6, len(ordered) - 2):
                fight["tier"] = "Prelims"
                fight["card_position"] = "Prelims"
            else:
                fight["tier"] = "Early Prelims"
                fight["card_position"] = "Early Prelims"
        return ordered

    def simulate_ai_promotion_month(self, promo, develop=True):
        if promo.show_history is None:
            promo.show_history = []
        if develop:
            self.age_and_develop_fighters(promo.roster)
        strategy = self.update_ai_promotion_strategy(promo)
        self.ensure_ai_media_state(promo)
        self.review_ai_media_deals(promo)
        commercial_strength, market_volatility, market_momentum = self.update_ai_financial_market(promo)
        card_day = self.ai_card_day(promo)
        self.update_ai_title_roadmap(promo, card_day)
        ready = [f for f in promo.roster if self.fighter_available_for_date(f, day=card_day) and f.fatigue < self.ai_fatigue_limit(promo)]
        if len(ready) < self.ai_min_ready_fighters(promo):
            if random.random() < 0.45:
                open_divisions = [
                    (gender, weight)
                    for gender in ("Male", "Female")
                    for weight in (getattr(promo, "weight_classes", None) or WEIGHTS)
                    if self.promotion_division_open(promo, gender, weight)
                ]
                if not open_divisions:
                    return
                division_counts = {
                    key: sum(1 for fighter in promo.roster if not fighter.retired and (fighter.gender, fighter.weight) == key)
                    for key in open_divisions
                }
                gender, weight = min(open_divisions, key=lambda key: (division_counts[key], random.random()))
                prospect = self.create_generated_fighter(
                    10, min(80, promo.size), 45, min(88, 55 + promo.size // 3),
                    gender=gender, weight=weight, region=promo.region,
                )
                prospect.contract_months = random.randint(6, 18)
                prospect.exclusive = True
                prospect.camp = promo.name
                promo.roster.append(prospect)
            return
        fight_target = {"Super Shows": random.randint(10, 14), "Seasonal": random.randint(9, 13), "Star Builder": random.randint(9, 13), "Prospect Builder": random.randint(9, 12), "Frequent Small Cards": random.randint(8, 10)}.get(getattr(promo, "show_personality", "Balanced"), random.randint(9, 12))
        # Deep rosters can support a longer broadcast card, up to 16 bouts.
        # Readiness is the gate: a promotion cannot pad its bill with athletes
        # who are injured, exhausted, or already in a recovery window.
        if len(ready) >= 56:
            fight_target += 1
        if len(ready) >= 84:
            fight_target += 1
        if len(ready) >= 112 and getattr(promo, "show_personality", "Balanced") in ("Super Shows", "Seasonal", "Star Builder"):
            fight_target += 1
        if len(getattr(promo, "roster", [])) >= 280:
            fight_target = max(14, fight_target)
        if promo.name == "Ultimate Fighting Championship":
            fight_target = max(14, fight_target)
        mode = strategy.get("current_mode")
        if mode == "Financial Recovery":
            fight_target = max(5, fight_target - 2)
        elif mode == "Star Chasing":
            fight_target = max(6, fight_target - 1)
        elif mode == "Prospect Rebuild":
            fight_target = min(16, fight_target + 1)
        elif mode == "Contender Cycle":
            fight_target = min(16, fight_target + 1)
        fight_target = min(16, fight_target)
        # Pick the card's day before matchmaking, so camps and the fighters'
        # availability for it are both measured against the same date.
        self._active_card_day = card_day
        fights = self.build_ai_card(promo, ready, fight_target)
        minimum_card = 5 if strategy.get("current_mode") == "Financial Recovery" else 6
        if len(fights) < minimum_card:
            self._active_card_day = None
            return
        projected_cost = sum(f["a"].purse + f["b"].purse for f in fights) + promo.size * 9500 + len(fights) * 22000
        # Broadcasters and venues advance a portion of expected receipts. AI
        # companies therefore need meaningful working capital, not the entire
        # card cost sitting idle in cash; this lets a small promotion trade out
        # of trouble while still preventing an insolvent company from booking.
        working_capital = max(80_000, projected_cost * (0.22 if mode == "Financial Recovery" else 0.32))
        recovery_until = max(0, int(strategy.get("recovery_support_until_month", 0) or 0))
        recovery_active = self.month <= recovery_until
        if promo.cash < working_capital:
            # A negative balance or a documented run of bad cards earns a
            # short operating bridge. It is not a permanent subsidy and never
            # applies to the player company.
            if promo.cash < 0:
                recovery_until = max(recovery_until, self.month + 12)
                recovery_active = True
            if promo.cash < 0 or recovery_active:
                promo.cash = working_capital
            elif random.random() < 0.35:
                promo.stability = max(1, promo.stability - 1)
                self.news.insert(0, f"Week {self.week}: {promo.name} postponed a card after budget review.")
                return
        pop_gain = 0
        main_fight = next((fight for fight in fights if fight.get("main")), fights[0])
        event_name = f"{promo.name} {promo.event_counter}: {self.matchup_display_name(main_fight['a'], main_fight['b'])}"
        event_city = random.choice(REGION_CITIES.get(promo.region, [promo.region]))
        promo.event_counter += 1
        main_result = ""
        event_hype = 0
        event_log = []
        fight_logs = []
        # AI matchmaking stores the card headline-first for management views;
        # the actual show runs upward from the undercard to the main event.
        for entry in reversed(fights):
            a, b = entry["a"], entry["b"]
            is_title, is_main, is_grudge = entry["title"], entry["main"], entry["grudge"]
            # Defensive validation for migrated cards or future matchmaker
            # changes: a living champion cannot lose their belt from ringside.
            if is_title and not self.ai_divisional_title_bout_is_valid(promo, a, b):
                is_title = False
                entry["title"] = False
                entry["booking_reason"] = (
                    f"{entry.get('booking_reason', 'AI matchmaking')}; "
                    "title status removed because the reigning champion was not booked"
                )
            self.apply_ai_camp(a, promo)
            self.apply_ai_camp(b, promo)
            self.perform_weigh_in(a, title_fight=is_title, persist=True)
            self.perform_weigh_in(b, title_fight=is_title, persist=True)
            a_record, b_record = a.record, b.record
            a_rating, b_rating = self.bout_rating_snapshot(a), self.bout_rating_snapshot(b)
            bout = {"main": is_main, "title": is_title, "tier": entry.get("tier", "Main Card"), "region": promo.region, "city": event_city}
            winner, loser, method, round_no, _lines = self.simulate_fight(a, b, bout)
            bout["_scorecards"] = self.scorecard_summary_from_lines(_lines)
            hype_seed = a.popularity + b.popularity + (40 if is_title else 0) + (25 if is_grudge else 0)
            ai_excitement = self.fight_excitement(a, b, winner, loser, method, round_no, bout, hype_seed)
            self.record_season_result(winner, loser, method, round_no, bout, ai_excitement, promo.name)
            if is_main and is_title:
                label = "MAIN EVENT - TITLE FIGHT"
            elif is_main:
                label = "MAIN EVENT"
            elif is_title:
                label = "TITLE FIGHT"
            else:
                label = entry.get("card_position", "BOUT")
            if method != "Draw":
                self.record_bout_rating_history(a, b, "W" if winner is a else "L", "L" if winner is a else "W", bout)
            if method == "Draw":
                self.apply_draw_result(a, b, bout)
                line = f"Month {self.month} Week {self.week}: {a.name} and {b.name} fought to a draw at {event_name}"
                result_line = f"{a.name} vs {b.name} - Draw (R{round_no})"
                if is_main or not main_result:
                    main_result = result_line
            else:
                self.update_elo(winner, loser, bout, method)
                self.commit_career_stats(winner, method, won=True)
                self.commit_career_stats(loser, method, won=False)
                winner.record_w += 1
                loser.record_l += 1
                winner.career_win_streak = getattr(winner, "career_win_streak", 0) + 1
                loser.career_win_streak = 0
                line = f"Month {self.month} Week {self.week}: {winner.name} def. {loser.name} by {method} at {event_name}"
                self.add_fight_history_entry(winner, line)
                self.add_fight_history_entry(loser, line)
                result_line = f"{winner.name} def. {loser.name} by {method} (R{round_no})"
                if is_main or not main_result:
                    main_result = result_line
            fight_logs.append({"heading": f"{a.name} vs {b.name}", "label": label,
                                "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id, "a_record": a_record, "b_record": b_record, "a_rating": a_rating, "b_rating": b_rating,
                                "weight": a.weight, "title": is_title, "interim": False, "result": result_line, "scorecards": bout.get("_scorecards", ""),
                               "booking_reason": entry.get("booking_reason", "AI matchmaking"),
                               "lines": [f"AI booking: {entry.get('booking_reason', 'AI matchmaking')}", *list(_lines), "", result_line]})
            event_log.extend([f"[{label}] {a.name} vs {b.name} — {entry.get('booking_reason', 'AI matchmaking')}", *_lines, result_line, ""])
            if method != "Draw":
                winner.last_fight = line
                loser.last_fight = line
                self.stamp_last_fight_date(winner, loser)
                winner.momentum = min(5, winner.momentum + 1)
                loser.momentum = max(-5, loser.momentum - 1)
                self.register_fight_popularity(winner, loser, bout, method)
                for fighter, won in ((winner, True), (loser, False)):
                    connection = self.fighter_event_connection(fighter, promo.region, event_city)
                    if connection["strength"]:
                        local_delta = (3 if won else 1) + (2 if connection["level"] == "Hometown" and won else 0)
                        self.update_regional_popularity(fighter, promo.region, local_delta, f"{connection['level']} appearance for {promo.name}")
                        fighter.morale = min(100, fighter.morale + max(1, round(connection["strength"] * (3 if won else 1))))
                winner.fatigue = min(100, winner.fatigue + random.randint(16, 30))
                loser.fatigue = min(100, loser.fatigue + random.randint(20, 38))
                self.set_post_fight_recovery(winner, method, lost=False)
                self.set_post_fight_recovery(loser, method, lost=True)
                self.clear_post_fight_preparation(a, b)
            if is_title and method != "Draw":
                promo.belts = promo.belts or {}
                promo.belt_history = promo.belt_history or {}
                promo.belts, promo.belt_history = self.set_primary_champion(promo.roster, promo.belts, promo.belt_history, winner, f"Defeated {loser.name} by {method}.", defense=True)
                self.news.insert(0, f"{promo.name}: {winner.name} is the {winner.gender} {winner.weight} champion after beating {loser.name} by {method}.")
                self.record_world_story("Title Change", f"{winner.name} wins the {promo.name} {winner.gender} {winner.weight} title.", f"Defeated {loser.name} by {method} in round {round_no}.", [promo.name], [winner.name, loser.name], 4)
            if is_grudge and method != "Draw":
                self.resolve_rivalry_result(winner, loser, bout, method)
            if method != "Draw":
                self.evaluate_fight_achievements(winner, loser, bout, method, promo.name)
            self.retire_after_final_fight_if_due(a, promo.name)
            self.retire_after_final_fight_if_due(b, promo.name)
            pop_gain += max(1, (winner.popularity + loser.popularity) // 35) + (2 if is_title else 0)
            event_hype += max(1, (winner.popularity + loser.popularity + winner.overall + loser.overall) // 4) + (12 if is_title else 0) + (6 if is_grudge else 0)
            if random.random() < 0.1:
                loser.injured = random.randint(1, 4)
        ceiling = self.promotion_strategy(promo).get("growth_ceiling", 76)
        event_profit = 0
        quality = event_hype / max(1, promo.size * 5)
        growth_roll = pop_gain / 15 + max(0, quality - 1) * 0.6 + random.uniform(-0.8, 0.65)
        rep_delta = 1 if growth_roll > 1.0 and promo.reputation_score < ceiling else (-1 if growth_roll < -0.45 or promo.stability < 32 else 0)
        promo.size = max(5, min(ceiling, promo.size + rep_delta))
        promo.reputation_score = max(1, min(ceiling, promo.reputation_score + rep_delta))
        promo.reputation = "Global" if promo.reputation_score >= 68 else ("National" if promo.reputation_score >= 45 else "Regional")
        promo.momentum = max(-10, min(10, promo.momentum + random.choice([-1, 0, 1])))
        regional_pull = self.regional_market_score(promo.region)
        # Card income is anchored to the actual card cost. The earlier formula
        # multiplied hype, promotion size, regional pull, a large random value,
        # distribution and a second gate multiplier, so one normal show could
        # create tens of millions in cash. Brand strength and card quality now
        # determine a realistic operating margin around the cost of staging the
        # show; a weak company can lose money while a healthy major makes a
        # modest surplus that supports its deep roster.
        card_quality = max(0.0, min(1.0, event_hype / max(1, len(fights) * 180)))
        quality_margin = (card_quality - 0.48) * 0.16
        commercial_margin = -0.17 + commercial_strength / 285
        momentum_margin = market_momentum / 320
        regional_margin = (regional_pull - 1.0) * 0.12
        event_noise = random.uniform(-market_volatility / 360, market_volatility / 360)
        revenue_factor = max(0.70, min(1.28, 1 + commercial_margin + quality_margin + momentum_margin + regional_margin + event_noise))
        # Attendance, distribution and sponsor demand are not certain. Most
        # cards land near forecast, while a minority underperform or break out.
        commercial_roll = random.random()
        downside_chance = max(0.08, min(0.18, 0.23 - commercial_strength / 850))
        if commercial_roll < downside_chance:
            revenue_factor *= random.uniform(0.72, 0.88)
            projected_cost = round(projected_cost * random.uniform(1.04, 1.16))
        elif commercial_roll > 0.93:
            revenue_factor *= random.uniform(1.08, 1.18)
        ai_event = {
            "name": event_name, "event_name": event_name, "region": promo.region, "city": event_city,
            "broadcaster": (promo.broadcasters or [{"name": "Local Production"}])[0].get("name", "Local Production"),
            "fights": [{"fighters": [entry["a"].name, entry["b"].name], "main": entry.get("main", False), "title": entry.get("title", False)} for entry in fights],
        }
        media_build = max(35, min(92, event_hype / max(1, len(fights) * 2.5)))
        ai_media = self.calculate_event_media_outcome(ai_event, {
            "fight_count": len(fights), "average_excitement": max(35, min(90, quality * 48)),
            "average_build": media_build, "finance": {"build_score": media_build},
        }, promotion=promo)
        # Distribution changes the margin within a narrow band; media income
        # itself is then added once, through the actual rights deal.
        distribution_factor = max(0.90, min(1.16, 0.90 + ai_media.get("reach", 0) / 350))
        revenue_factor = max(0.68, min(1.34, revenue_factor + (distribution_factor - 1) * 0.28))
        revenue = round(projected_cost * revenue_factor) + int(ai_media.get("rights_income", 0))
        provisional_profit = revenue - projected_cost
        negative_streak = max(0, int(strategy.get("negative_event_streak", 0) or 0))
        if provisional_profit < 0:
            negative_streak += 1
        else:
            negative_streak = max(0, negative_streak - 1)
        if negative_streak >= 2:
            recovery_until = max(recovery_until, self.month + 12)
            recovery_active = True
        if recovery_active:
            # The recovery bridge lasts one in-game year. It gives the AI time
            # to retain a roster and renegotiate naturally, then expires.
            minimum_commercial_return = round(projected_cost * (1.06 + commercial_strength / 1_500))
            revenue = max(revenue, minimum_commercial_return)
        strategy["negative_event_streak"] = negative_streak
        strategy["recovery_support_until_month"] = recovery_until
        # Production, purses, distribution, and marketing are already explicit
        # card costs. Reinvestment is a smaller discretionary spend, not an
        # opaque sink that removes most successful-event profit from the ledger.
        reinvestment_rate = min(0.28, 0.12 + promo.size / 1_200)
        strategic_reinvestment = round(max(0, revenue - projected_cost) * reinvestment_rate)
        event_profit = revenue - projected_cost - strategic_reinvestment
        promo.cash += event_profit
        strategy["last_event_finance"] = {
            "month": self.month, "revenue": revenue, "cost": projected_cost,
            "profit": event_profit, "margin": round(event_profit / max(1, projected_cost), 3),
        }
        margin = event_profit / max(1, projected_cost)
        stability_target = strategy.get("stability_target", max(58, min(86, round(50 + commercial_strength * 0.38))))
        if margin >= 0.18 and promo.stability < stability_target:
            stability_delta = 1
        elif margin >= -0.03:
            stability_delta = 0
        elif margin >= -0.14:
            stability_delta = -1
        elif margin >= -0.28:
            stability_delta = -2
        else:
            stability_delta = -3
        promo.stability = max(1, min(100, promo.stability + round(rep_delta / 2 + stability_delta)))
        summary = f"{event_name}: {len(fights)} fights, main event {main_result}, rep {'+' if rep_delta >= 0 else ''}{rep_delta} [{strategy.get('current_mode', 'Balanced')}]"
        promo.show_history.insert(0, summary)
        promo.show_history = promo.show_history[:12]
        package = {
            "date": f"Month {self.month} Week {self.week}",
            "company": promo.name,
            "event_name": event_name,
            "summary": summary,
            "fight_count": len(fights),
            "profit": event_profit,
                "finance": {"ticket_revenue": max(0, revenue - ai_media.get("rights_income", 0)), "broadcast_income": ai_media.get("rights_income", 0), "media_reach": ai_media.get("reach", 0), "total_revenue": revenue, "total_expense": projected_cost + strategic_reinvestment, "profit": event_profit, "media_outcome": ai_media},
            "log": [summary, ""] + event_log,
            "fight_logs": fight_logs,
            "media_outcome": ai_media,
        }
        featured_media_fighters = [entry[side] for entry in fights for side in ("a", "b") if entry.get("main") or entry.get("title")]
        self.record_media_event_outcome(ai_event, ai_media, promotion=promo, featured_fighters=featured_media_fighters)
        self.ai_event_archive.insert(0, package)
        self.ai_event_archive = self.ai_event_archive[:120]
        self.archive_result_record({
            "date": package["date"],
            "company": promo.name,
            "event": event_name,
            "summary": summary,
            "fights": len(fights),
            "gate": f"${revenue:,}",
            "profit": f"${revenue - projected_cost:,}",
            "log": package["log"],
            "fight_logs": fight_logs,
            "finance": package["finance"],
        })
        self.evaluate_promotion_achievements(promo.name, package)
        self.refresh_historical_records()
        self.refresh_promotion_rankings(company=promo.name, roster=promo.roster)
        if promo.region in self.regions:
            self.regions[promo.region]["last_major_show"] = summary
            region_data = self.regions[promo.region]
            region_data["mma_love"] = max(10, min(100, region_data.get("mma_love", 50) + (1 if event_hype > promo.size * 3 else 0)))
        if random.random() < 0.65:
            self.news.insert(0, f"{promo.name} ran {event_name}; {main_result}.")
        self._active_card_day = None

    def major_roster_population_status(self):
        """Return live major-promotion demand without treating capacity as free agents."""
        promotions = [
            item for item in self.promotions
            if not getattr(item, "is_regional_feeder", False)
        ]
        target = sum(self.ai_roster_target(item) for item in promotions)
        active = sum(
            1 for item in promotions for fighter in item.roster
            if not getattr(fighter, "retired", False)
        )
        deficit = max(0, target - active)
        return {
            "active": active,
            "target": target,
            "deficit": deficit,
            "fill_ratio": active / max(1, target),
        }

    def regional_roster_vacancies(self, promo, target=100):
        active = sum(1 for fighter in promo.roster if not getattr(fighter, "retired", False))
        return max(0, target - active)

    def regional_eligible_backlog_count(self):
        """Count regional fighters who already meet Eligible Now, cached once per month.

        Readiness has no ceiling: during a stretch where the majors are fully
        staffed and the free-agent reserve is comfortable, graduation_slots
        can sit at 0 for many consecutive months while the round-robin feeder
        cards keep seasoning the whole population. Real observed saves showed
        this pile up to over 75% of the entire regional pool simultaneously
        eligible before anything drained it. This is called from the UI's
        Regional Prospects refresh as well as the monthly graduation pass, so
        the full scan is cached per month rather than recomputed on every
        call.
        """
        if self.rules.get("regional_eligible_backlog_month") == self.month:
            return self.rules.get("regional_eligible_backlog_count", 0)
        count = 0
        for promo in self.promotions:
            if not getattr(promo, "is_regional_feeder", False):
                continue
            for fighter in promo.roster:
                if fighter.retired:
                    continue
                if self.regional_candidate_assessment(fighter, promo)["eligible"]:
                    count += 1
        self.rules["regional_eligible_backlog_month"] = self.month
        self.rules["regional_eligible_backlog_count"] = count
        return count

    def regional_market_throughput(self):
        """Scale feeder output to major-roster demand while keeping a usable market reserve."""
        status = self.major_roster_population_status()
        free_agents = [fighter for fighter in self.free_agents if not getattr(fighter, "retired", False)]
        available = [
            fighter for fighter in free_agents
            if not getattr(fighter, "retirement_pending", False)
            and not getattr(fighter, "injured", 0)
            and not getattr(fighter, "ai_offer_company", "")
        ]
        deficit = status["deficit"]

        if len(available) < 170:
            reserve_slots = 6
        elif len(available) < 230:
            reserve_slots = 3
        elif len(available) < 300:
            reserve_slots = 2
        elif len(available) < 340:
            reserve_slots = 1
        else:
            reserve_slots = 0

        if deficit >= 2_000:
            demand_slots = 4
        elif deficit >= 1_200:
            demand_slots = 3
        elif deficit >= 500:
            demand_slots = 2
        elif deficit >= 200:
            demand_slots = 1
        else:
            demand_slots = 0

        # Pending offers are already leaving the market next month. They should
        # not make the regional pathway shut down as though they were idle stock.
        graduation_slots = max(reserve_slots, demand_slots)
        if len(available) >= 420 or (len(free_agents) >= 560 and len(available) >= 330):
            graduation_slots = min(graduation_slots, 1)
        # A comfortable free-agent market and fully-staffed majors both push
        # slots toward 0, but regional readiness keeps accumulating regardless.
        # A large backlog of already-eligible fighters is its own pressure and
        # overrides the crowding cap above: leaving them stuck isn't healthier
        # than a slightly busier free-agent market.
        backlog = self.regional_eligible_backlog_count()
        if backlog >= 700:
            backlog_slots = 6
        elif backlog >= 400:
            backlog_slots = 4
        elif backlog >= 200:
            backlog_slots = 2
        elif backlog >= 80:
            backlog_slots = 1
        else:
            backlog_slots = 0
        graduation_slots = max(graduation_slots, backlog_slots)
        return {
            **status,
            "free_agents": len(free_agents),
            "available_free_agents": len(available),
            "graduation_slots": max(0, min(6, graduation_slots)),
        }

    def regional_candidate_assessment(self, fighter, promo):
        """Use one sporting-readiness model for the feeder sim and player browser."""
        origin_matches = getattr(fighter, "feeder_origin", "") == promo.name
        baseline_w, baseline_l, baseline_d = self.ensure_fighter_history_baseline(fighter)
        # A fabricated pre-universe backstory record must not do the work of
        # actual regional experience. Every readiness threshold below is
        # measured against bouts and wins fought for real, in this circuit,
        # not the flavour record a fighter was generated with.
        real_w = max(0, fighter.record_w - baseline_w)
        real_l = max(0, fighter.record_l - baseline_l)
        real_d = max(0, fighter.record_d - baseline_d)
        bouts = real_w + real_l + real_d
        win_rate = real_w / max(1, bouts)
        criteria = []

        def add(label, met, missing):
            criteria.append({"label": label, "met": bool(met), "missing": [item for item in missing if item]})

        early_missing = [
            f"{23 - fighter.age} more year(s)" if fighter.age < 23 else "",
            f"{11 - bouts} more bout(s)" if bouts < 11 else "",
            f"potential {fighter.potential}/86" if fighter.potential < 86 else "",
            "7 wins or +4 momentum" if real_w < 7 and fighter.momentum < 4 else "",
        ]
        add(
            "Early breakthrough",
            fighter.age >= 23 and bouts >= 11 and fighter.potential >= 86
            and (real_w >= 7 or fighter.momentum >= 4),
            early_missing,
        )
        proven_missing = [
            f"{25 - fighter.age} more year(s)" if fighter.age < 25 else "",
            f"{12 - bouts} more bout(s)" if bouts < 12 else "",
            f"{7 - real_w} more win(s)" if real_w < 7 else "",
            f"win rate {win_rate:.0%}/53%" if win_rate < 0.53 else "",
        ]
        add(
            "Proven regional",
            fighter.age >= 25 and bouts >= 12 and real_w >= 7 and win_rate >= 0.53,
            proven_missing,
        )
        established_missing = [
            f"{27 - fighter.age} more year(s)" if fighter.age < 27 else "",
            f"{15 - bouts} more bout(s)" if bouts < 15 else "",
            f"win rate {win_rate:.0%}/51%" if win_rate < 0.51 else "",
        ]
        add(
            "Established exit",
            fighter.age >= 27 and bouts >= 15 and win_rate >= 0.51,
            established_missing,
        )
        hot_missing = [
            "regional origin not linked" if not origin_matches else "",
            f"{7 - real_w} more win(s)" if real_w < 7 else "",
            f"momentum {fighter.momentum:+d}/+5" if fighter.momentum < 5 else "",
            f"popularity {fighter.popularity}/26" if fighter.popularity < 26 else "",
        ]
        add(
            "Hot regional run",
            origin_matches and real_w >= 7 and fighter.momentum >= 5 and fighter.popularity >= 26,
            hot_missing,
        )
        circuit_path_a = max(0, 24 - fighter.age) + max(0, 22 - bouts)
        circuit_path_b = max(0, 30 - bouts)
        circuit_missing = (
            [f"{max(0, 24 - fighter.age)} year(s) and {max(0, 22 - bouts)} bout(s) from a full run"]
            if circuit_path_a <= circuit_path_b else [f"{max(0, 30 - bouts)} more bout(s)"]
        )
        add(
            "Circuit complete",
            (fighter.age >= 24 and bouts >= 22) or bouts >= 30,
            [] if (fighter.age >= 24 and bouts >= 22) or bouts >= 30 else circuit_missing,
        )
        veteran_missing = [
            f"{28 - fighter.age} more year(s)" if fighter.age < 28 else "",
            f"{15 - bouts} more bout(s)" if bouts < 15 else "",
        ]
        add("Veteran exit", fighter.age >= 28 and bouts >= 15, veteran_missing)
        high_results = (
            win_rate >= 0.60
            or real_w >= 10
            or fighter.potential >= 88
            or (fighter.momentum >= 4 and fighter.popularity >= 26)
        )
        add(
            "Aging out",
            fighter.age >= 29 and bouts >= 7 and not high_results,
            [
                f"{29 - fighter.age} more year(s)" if fighter.age < 29 else "",
                f"{7 - bouts} more bout(s)" if bouts < 7 else "",
                "results remain above the age-out threshold" if high_results else "",
            ],
        )

        sporting_reasons = [item["label"] for item in criteria if item["met"]]
        blocked = []
        if fighter.age < 18:
            blocked.append("under 18")
        if fighter.injured:
            blocked.append("injured")
        if fighter.retirement_pending:
            blocked.append("retirement pending")
        if fighter.retired:
            blocked.append("retired")
        eligible = bool(sporting_reasons) and not blocked

        unmet = [item for item in criteria if not item["met"]]
        nearest = min(unmet, key=lambda item: len(item["missing"]), default=None)
        missing = nearest["missing"] if nearest else []
        # "Nearly" is intentionally broad enough to expose useful developing
        # fighters without labelling every new 17-year-old as one decision away.
        nearly = not sporting_reasons and fighter.age >= 18 and (
            bouts >= 8 or fighter.potential >= 86 or fighter.momentum >= 4
        ) and len(missing) <= 2
        if eligible:
            status = "Eligible Now"
            explanation = ", ".join(sporting_reasons)
        elif sporting_reasons:
            status = "Medical Hold" if fighter.injured else "Blocked"
            explanation = f"{', '.join(sporting_reasons)}; blocked by {', '.join(blocked)}"
        elif nearly:
            status = "Nearly Eligible"
            explanation = f"{nearest['label']}: {', '.join(missing) or 'one final threshold'}"
        else:
            status = "Developing"
            explanation = f"{nearest['label']}: {', '.join(missing)}" if nearest else "Building a regional record"
        # A backstory record (pre-universe flavour) is not the same as having
        # actually competed here. A fighter must have at least one real,
        # in-engine bout before the pathway can call them ready for the wider
        # market, no matter how their fabricated record reads.
        if bouts <= 0 and (eligible or status == "Nearly Eligible"):
            eligible = False
            status = "Developing"
            explanation = "Has not yet fought in this circuit; awaiting a debut bout before regional readiness can be confirmed"
        return {
            "eligible": eligible,
            "status": status,
            "explanation": explanation,
            "reasons": sporting_reasons,
            "blocked": blocked,
            "bouts": bouts,
            "win_rate": win_rate,
        }

    def repair_regional_fighter_tracking(self):
        """Repair feeder origin and activity fields in older sealed saves."""
        repaired_origin = 0
        repaired_activity = 0
        seeded_divisions = 0
        evicted_wrong_gender = 0
        for promo in self.promotions:
            if not getattr(promo, "is_regional_feeder", False):
                continue
            # A single-gender circuit can strand a fighter it has no division
            # for: they can never be matched, so they can never graduate, and a
            # pending retirement can never resolve. Release them to free agency
            # where the normal pathways can pick them up again.
            if self.promotion_male_only(promo):
                for fighter in [item for item in promo.roster if item.gender != "Male"]:
                    if self.move_regional_fighter_to_free_agency(
                        promo, fighter,
                        "Released: no division on a male-only circuit.",
                        "Regional reset", popularity_bonus=0,
                    ):
                        evicted_wrong_gender += 1
            promo.regional_division_activity = getattr(promo, "regional_division_activity", None) or {}
            for fighter in promo.roster:
                if getattr(fighter, "feeder_origin", "") != promo.name:
                    fighter.feeder_origin = promo.name
                    repaired_origin += 1
                latest_month = 0
                for entry in getattr(fighter, "bout_rating_history", None) or []:
                    if not isinstance(entry, dict):
                        continue
                    match = re.search(r"Month\s+(\d+)", str(entry.get("date", "")))
                    if match:
                        latest_month = max(latest_month, int(match.group(1)))
                if latest_month > int(getattr(fighter, "last_fight_month", 0) or 0):
                    fighter.last_fight_month = latest_month
                    repaired_activity += 1
                key = f"{fighter.gender}|{fighter.weight}"
                if key not in promo.regional_division_activity:
                    promo.regional_division_activity[key] = int(getattr(fighter, "last_fight_month", 0) or 0)
                    seeded_divisions += 1
                else:
                    promo.regional_division_activity[key] = max(
                        int(promo.regional_division_activity.get(key, 0) or 0),
                        int(getattr(fighter, "last_fight_month", 0) or 0),
                    )
        return {"origin": repaired_origin, "activity": repaired_activity, "division_activity": seeded_divisions}

    def repair_regional_title_state(self):
        """Remove legacy feeder belts that were invented by company-state repair."""
        repaired_divisions = 0
        repaired_fighters = 0
        for promo in self.promotions:
            if not getattr(promo, "is_regional_feeder", False):
                continue
            promo.belts = self.normalize_belts(getattr(promo, "belts", None) or {})
            promo.interim_belts = self.normalize_belts(getattr(promo, "interim_belts", None) or {})
            promo.belt_history = self.normalize_belt_history(getattr(promo, "belt_history", None) or {})
            for key, entries in list(promo.belt_history.items()):
                entries = list(entries or [])
                invented = bool(entries) and all(
                    entry.get("action") == "Inaugural Champion Appointed"
                    and str(entry.get("note", "")).endswith("title status normalized.")
                    for entry in entries
                )
                if not invented:
                    continue
                gender, weight = key.split(" ", 1)
                for fighter in promo.roster:
                    if fighter.gender != gender or fighter.weight != weight:
                        continue
                    if fighter.champion or fighter.interim_champion:
                        repaired_fighters += 1
                    fighter.champion = False
                    fighter.interim_champion = False
                    fighter.title_wins = 0
                    fighter.title_defenses = 0
                    for bout in getattr(fighter, "bout_rating_history", None) or []:
                        if isinstance(bout, dict) and (bout.get("title") or bout.get("divisional_title")):
                            bout["title"] = False
                            bout["divisional_title"] = False
                            bout["interim"] = False
                promo.belts[key] = ""
                promo.interim_belts[key] = ""
                promo.belt_history[key] = []
                repaired_divisions += 1
        return {"divisions": repaired_divisions, "fighters": repaired_fighters}

    def simulate_regional_feeder_month(self, promo):
        """Low-cost developmental circuit: young fighters build records, not profits."""
        ready = [fighter for fighter in promo.roster if self.fighter_available_for_date(fighter, day=self.ai_card_day(promo)) and fighter.fatigue < 58]
        by_division = {}
        for fighter in ready:
            by_division.setdefault((fighter.gender, fighter.weight), []).append(fighter)

        # Developmental cards should build believable records, not repeatedly
        # feed a 0-12 novice to a much stronger prospect.
        def match_rating(item):
            bouts = item.record_w + item.record_l + item.record_d
            retirement_priority = 120 if getattr(item, "retirement_pending", False) else 0
            return retirement_priority + item.overall + (item.record_w - item.record_l) * 0.7 + min(12, bouts) * 0.25 + random.uniform(-2, 2)

        def pick_opponent_index(a, fighters):
            a_bouts = a.record_w + a.record_l + a.record_d
            a_rate = a.record_w / max(1, a_bouts)

            def rematch_count(item):
                """Keep developmental cards from becoming a two-person loop."""
                opponent_id = str(getattr(item, "fighter_id", "") or "")
                return sum(
                    1 for entry in (getattr(a, "bout_rating_history", None) or [])
                    if isinstance(entry, dict)
                    and (str(entry.get("opponent_id", "") or "") == opponent_id
                         or (not opponent_id and entry.get("opponent_name") == item.name))
                )

            def matchup_distance(item):
                bouts = item.record_w + item.record_l + item.record_d
                win_rate = item.record_w / max(1, bouts)
                prior_meetings = rematch_count(item)
                return (abs(item.overall - a.overall) * 3.0
                        + abs(bouts - a_bouts) * 0.35
                        + abs(win_rate - a_rate) * 18
                        + abs(item.age - a.age) * 0.25
                        # A third meeting should lose to a slightly less tidy
                        # matchup. This still permits rematches in a thin division.
                        + prior_meetings * 22)

            fresh_indices = [index for index, item in enumerate(fighters) if rematch_count(item) < 2]
            candidate_indices = fresh_indices or list(range(len(fighters)))
            return min(candidate_indices, key=lambda index: matchup_distance(fighters[index]))

        for fighters in by_division.values():
            random.shuffle(fighters)
            fighters.sort(key=match_rating, reverse=True)
        # Regional champions follow the same rule as a major-promotion title
        # holder: they only appear when the belt is on the line. Previously we
        # moved the champion to the front of their division's generic queue,
        # then marked that bout as a title fight only every four months. That
        # quietly produced a stream of ordinary wins between defenses.
        #
        # Reserve a due defense before building the development slate. If there
        # is no ready challenger, the champion sits out; a promotion cannot use
        # its titleholder as a development opponent just to fill a card.
        reserved_title_fights = []
        reserved_title_keys = set()
        for (gender, weight), fighters in by_division.items():
            key = self.belt_key(gender, weight)
            champion_name = self.ai_primary_title_holder_name(promo, gender, weight)
            if not champion_name:
                continue
            holder_index = next((index for index, fighter in enumerate(fighters) if fighter.name == champion_name), None)
            if holder_index is None:
                # The holder is injured, fatigued, or otherwise unavailable.
                # They were not present in ``ready``, so generic booking cannot
                # accidentally use them in this card.
                continue
            champion = fighters.pop(holder_index)
            history = (promo.belt_history or {}).get(key) or []
            last_title_month = max(
                (self.result_lineage_date_key(entry.get("date", ""))[0] for entry in history),
                default=0,
            )
            title_due = not last_title_month or self.month - last_title_month >= 4
            if not title_due or not fighters:
                continue
            opponent_index = pick_opponent_index(champion, fighters)
            challenger = fighters.pop(opponent_index)
            reserved_title_fights.append((champion, challenger))
            reserved_title_keys.add(key)

        # A shared bout budget used to drain itself on whichever divisions
        # happened to appear first in roster order, starving every division
        # further down the list for months or years at a time. The first fix
        # rotated a fresh random division order each month; this keeps that
        # one-bout-per-pass fairness but remembers which divisions have been
        # served least recently, so a division that misses a capped card moves
        # to the front of the next one instead of rolling unlucky again.
        max_card_bouts = 15
        promo.regional_division_activity = getattr(promo, "regional_division_activity", None) or {}

        def division_activity_key(division):
            return f"{division[0]}|{division[1]}"

        for division, fighters in by_division.items():
            key = division_activity_key(division)
            if key not in promo.regional_division_activity:
                promo.regional_division_activity[key] = max(
                    (int(getattr(fighter, "last_fight_month", 0) or 0) for fighter in fighters),
                    default=0,
                )
        division_order = sorted(
            by_division,
            key=lambda division: (
                int(promo.regional_division_activity.get(division_activity_key(division), 0) or 0),
                -len(by_division[division]),
                random.random(),
            ),
        )
        fights = list(reserved_title_fights)
        divisions_booked = {(fighter.gender, fighter.weight) for fighter, _challenger in reserved_title_fights}
        progress = True
        while progress and len(fights) < max_card_bouts:
            progress = False
            for division in division_order:
                if len(fights) >= max_card_bouts:
                    break
                fighters = by_division[division]
                if len(fighters) < 2:
                    continue
                a = fighters.pop(0)
                opponent_index = pick_opponent_index(a, fighters)
                b = fighters.pop(opponent_index)
                fights.append((a, b))
                divisions_booked.add(division)
                progress = True
        for division in divisions_booked:
            promo.regional_division_activity[division_activity_key(division)] = self.month
        if not fights:
            self.regional_recruit_fighter(promo, slots=max(1, self.regional_roster_vacancies(promo)))
            return

        # A regional title starts only when two fighters have built enough of a
        # record to contest it. Existing champions defend at a measured cadence;
        # state repair must never create an appointed feeder champion.
        title_flags = [self.belt_key(a.gender, a.weight) in reserved_title_keys for a, _b in fights]
        title_keys_used = set(reserved_title_keys)
        for index, (a, b) in enumerate(fights):
            key = self.belt_key(a.gender, a.weight)
            if key in title_keys_used:
                continue
            champ_name = (promo.belts or {}).get(key)
            history = (promo.belt_history or {}).get(key) or []
            last_title_month = max((self.result_lineage_date_key(entry.get("date", ""))[0] for entry in history), default=0)
            title_due = not last_title_month or self.month - last_title_month >= 4
            bouts_a = a.record_w + a.record_l + a.record_d
            bouts_b = b.record_w + b.record_l + b.record_d
            inaugural_contested = not champ_name and not history and min(bouts_a, bouts_b) >= 4
            vacant_contested = not champ_name and bool(history)
            # A vacancy is resolved on the next suitable pairing. The measured
            # cadence applies to defenses and inaugural crowns, not an empty belt.
            if vacant_contested or (title_due and (champ_name in (a.name, b.name) or inaugural_contested)):
                title_flags[index] = True
                title_keys_used.add(key)

        # Development cards run on a weekday like any other, so their bouts are
        # dated and count toward a prospect's turnaround the same way.
        self._active_card_day = self.ai_card_day(promo)
        event_name = f"{promo.name} Development Night {promo.event_counter}"
        promo.event_counter += 1
        results = []
        fight_logs = []
        for fight_number, (a, b) in enumerate(fights, 1):
            is_title = title_flags[fight_number - 1]
            self.apply_ai_camp(a, promo)
            self.apply_ai_camp(b, promo)
            self.perform_weigh_in(a, title_fight=is_title, persist=True)
            self.perform_weigh_in(b, title_fight=is_title, persist=True)
            a_rating, b_rating = self.bout_rating_snapshot(a), self.bout_rating_snapshot(b)
            bout = {"main": False, "title": is_title, "tier": "Regional Title Bout" if is_title else "Early Prelims", "region": promo.region}
            winner, loser, method, round_no, _lines = self.simulate_fight(a, b, bout)
            bout["_scorecards"] = self.scorecard_summary_from_lines(_lines)
            label = "TITLE FIGHT" if is_title else ("MAIN EVENT" if fight_number == 1 else "DEVELOPMENT BOUT")
            if method == "Draw":
                self.apply_draw_result(a, b, bout)
                result_line = f"{a.name} vs {b.name} - Draw (R{round_no})"
                results.append(result_line)
                fight_logs.append({"heading": f"{a.name} vs {b.name}", "label": label,
                                   "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id,
                                   "a_record": a_rating["record"], "b_record": b_rating["record"], "a_rating": a_rating, "b_rating": b_rating,
                                   "weight": a.weight, "result": result_line, "scorecards": bout["_scorecards"], "lines": [result_line]})
                continue
            self.record_bout_rating_history(a, b, "W" if winner is a else "L", "L" if winner is a else "W", bout)
            self.update_elo(winner, loser, bout, method)
            self.commit_career_stats(winner, method, won=True)
            self.commit_career_stats(loser, method, won=False)
            if is_title:
                promo.belts = promo.belts or {}
                promo.belt_history = promo.belt_history or {}
                promo.belts, promo.belt_history = self.set_primary_champion(promo.roster, promo.belts, promo.belt_history, winner, f"Defeated {loser.name} by {method}.", defense=True)
            winner.record_w += 1
            loser.record_l += 1
            winner.career_win_streak = getattr(winner, "career_win_streak", 0) + 1
            loser.career_win_streak = 0
            winner.momentum = min(5, winner.momentum + 1)
            loser.momentum = max(-5, loser.momentum - 1)
            proving_ground_bonus = 2 if winner.trait in ("Regional Star", "Overlooked Talent") else 0
            if winner.feeder_origin == promo.name and winner.age >= 22:
                proving_ground_bonus += 1
            winner.popularity = min(36, winner.popularity + random.randint(1, 3) + proving_ground_bonus)
            loser.popularity = max(1, loser.popularity - random.randint(0, 1))
            winner.morale = min(100, winner.morale + random.randint(2, 5))
            loser.morale = max(25, loser.morale - random.randint(1, 4))
            winner.fatigue = min(100, winner.fatigue + random.randint(16, 28))
            loser.fatigue = min(100, loser.fatigue + random.randint(18, 32))
            self.set_post_fight_recovery(winner, method, lost=False)
            self.set_post_fight_recovery(loser, method, lost=True)
            self.clear_post_fight_preparation(a, b)
            line = f"Month {self.month} Week {self.week}: {winner.name} def. {loser.name} by {method} at {event_name}"
            self.add_fight_history_entry(winner, line)
            self.add_fight_history_entry(loser, line)
            winner.last_fight = loser.last_fight = line
            self.stamp_last_fight_date(winner, loser)
            if winner.age <= 24 and winner.overall < winner.potential and random.random() < 0.34:
                self.adjust_random_skill(winner, 1)
                self.adjust_detailed_skill(winner, 1)
            elif winner.trait in ("Overlooked Talent", "Technical Learner") and winner.overall < winner.potential and random.random() < 0.12:
                self.adjust_random_skill(winner, 1)
                self.adjust_detailed_skill(winner, 1)
            result_line = f"{winner.name} def. {loser.name} by {method} (R{round_no})"
            results.append(result_line)
            fight_logs.append({"heading": f"{a.name} vs {b.name}", "label": label,
                               "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id,
                               "a_record": a_rating["record"], "b_record": b_rating["record"], "a_rating": a_rating, "b_rating": b_rating,
                               "weight": a.weight, "result": result_line, "scorecards": bout["_scorecards"], "lines": [result_line]})
            self.retire_after_final_fight_if_due(winner, promo.name)
            self.retire_after_final_fight_if_due(loser, promo.name)
        promo.show_history.insert(0, f"{event_name}: {len(fights)} developmental bouts, main result {results[0]}.")
        promo.show_history = promo.show_history[:12]
        # Feeder cards used to exist only in a promotion's twelve-line recent
        # history. Preserve a compact result entry just like every other card,
        # without retaining commentary for a replay that was never produced.
        self.archive_result_record({
            "date": f"Month {self.month} Week {self.week}", "company": promo.name,
            "event": event_name,
            "summary": f"{event_name}: {len(fights)} developmental bouts, main result {results[0]}.",
            "fights": len(fights), "gate": "—", "profit": "—", "log": [*results], "fight_logs": fight_logs,
            "replay_available": False,
        }, retain_detail=False)
        self._active_card_day = None
        self.regional_review_underperformers(promo)
        self.regional_graduate_fighters(promo)
        # A busy regional card can graduate several people. Refill promptly so
        # the next card has fresh divisions instead of recycling two veterans.
        self.regional_recruit_fighter(promo, slots=min(10, max(1, self.regional_roster_vacancies(promo))))
        if random.random() < 0.45:
            self.news.insert(0, f"{promo.name} ran a development night; {results[0]}.")

    def regional_review_underperformers(self, promo):
        """Move struggling young regional talent back to the market before retirement."""
        departures = []
        for fighter in list(promo.roster):
            bouts = fighter.record_w + fighter.record_l + fighter.record_d
            win_rate = fighter.record_w / max(1, bouts)
            early_washout = bouts >= 14 and fighter.record_w <= 1 and fighter.potential < 78
            sustained_struggle = bouts >= 20 and win_rate < 0.22 and fighter.potential < 85
            terminal_record = bouts >= 28 and win_rate < 0.28
            if not (early_washout or sustained_struggle or terminal_record):
                continue
            # A bad early record means the regional matchmaker has run out of
            # useful pairings, not that an 18-29 year old has ended a career.
            # Keep the record and let a different gym or circuit offer a reset.
            if fighter.age < 30:
                if not self.move_regional_fighter_to_free_agency(
                    promo,
                    fighter,
                    "Released after a regional career review.",
                    "Regional reset",
                    popularity_bonus=0,
                ):
                    continue
                fighter.retirement_pending = False
                fighter.retirement_reason = "Released after a regional career review; available for a fresh start."
                fighter.available_week = max(getattr(fighter, "available_week", 0), self.calendar_week_index() + 4)
                self.news.insert(0, f"Regional reset: {fighter.name} leaves {promo.name} for free agency at {fighter.record}.")
                continue
            if not getattr(fighter, "retirement_pending", False):
                self.mark_retirement_fight_required(fighter, "Regional career review")
            departures.append(fighter)
        for fighter in departures[:2]:
            headline = f"Regional career review: {fighter.name} needs one final fight before leaving professional MMA ({fighter.record})."
            self.news.insert(0, headline)
            self.record_world_story("Regional Career Review", headline, fighter.retirement_reason, [promo.name], [fighter.name], 2)
        return departures

    def capture_regional_record(self, fighter):
        """Persist the results earned during the fighter's latest feeder run."""
        fighter.regional_record_w = max(0, fighter.record_w - getattr(fighter, "regional_entry_w", 0))
        fighter.regional_record_l = max(0, fighter.record_l - getattr(fighter, "regional_entry_l", 0))
        fighter.regional_record_d = max(0, fighter.record_d - getattr(fighter, "regional_entry_d", 0))
        fighter.regional_record_month = self.month

    def move_regional_fighter_to_free_agency(self, promo, fighter, reason, market_origin, popularity_bonus=3):
        """Centralize feeder exits so champions always vacate before moving up."""
        if fighter not in promo.roster:
            return False
        self.capture_regional_record(fighter)
        promo.belts, promo.interim_belts, promo.belt_history = self.vacate_fighter_belts(
            fighter,
            promo.roster,
            promo.belts or {},
            promo.interim_belts or {},
            promo.belt_history or {},
            reason,
        )
        promo.roster.remove(fighter)
        fighter.champion = False
        fighter.interim_champion = False
        fighter.feeder_origin = promo.name
        fighter.last_regional_promotion = promo.name
        fighter.regional_departure_month = self.month
        fighter.market_origin = market_origin
        fighter.contract_months = 0
        fighter.exclusive = False
        fighter.contract_type = "Free Agent"
        fighter.free_agent_months = 0
        fighter.popularity = min(45, fighter.popularity + max(0, int(popularity_bonus)))
        if fighter not in self.free_agents:
            self.free_agents.append(fighter)
        return True

    def regional_graduate_fighters(self, promo):
        eligible = []
        for fighter in promo.roster:
            if self.regional_candidate_assessment(fighter, promo)["eligible"]:
                eligible.append(fighter)
        market_counts = {}
        for fighter in self.free_agents:
            if (fighter.retired or fighter.retirement_pending or fighter.injured
                    or getattr(fighter, "ai_offer_company", "")):
                continue
            key = (fighter.gender, fighter.weight)
            market_counts[key] = market_counts.get(key, 0) + 1
        thin_female_divisions = {
            ("Female", weight) for weight in WEIGHTS
            if market_counts.get(("Female", weight), 0) < 8
        }
        # Bout count used to fully dominate this ranking below the boolean
        # tiers -- potential/overall/wins/momentum only ever broke an exact
        # tie, which real bout counts almost never produce. Blending them into
        # one score lets a genuinely better prospect edge out a slightly more
        # active one, without letting quality override activity outright: the
        # bonus tops out well under a single bout's worth of ranking weight.
        eligible.sort(
            key=lambda fighter: (
                (fighter.gender, fighter.weight) in thin_female_divisions,
                (fighter.record_w + fighter.record_l + fighter.record_d >= 24),
                fighter.age >= 26,
                (fighter.record_w + fighter.record_l + fighter.record_d)
                + fighter.potential * 0.15
                + fighter.overall * 0.10
                + fighter.record_w * 0.2
                + fighter.momentum * 0.4,
            ),
            reverse=True,
        )
        if not eligible:
            return 0
        # Output follows both available market stock and the number of unfilled
        # major-roster jobs. Counting pending offers as idle free agents was the
        # main long-save choke point: ten full feeders could not replace retirees.
        throughput = self.regional_market_throughput()
        # `graduation_slots` is a WORLD allowance, not a per-promotion one.
        # Applying it independently to every feeder pushed more than 130
        # fighters into free agency in a single year. Rotate the allowance
        # across circuits so the pathway stays global and geographically fair.
        if int(self.rules.get("regional_graduation_budget_month", -1) or -1) != self.month:
            feeder_names = [
                item.name for item in self.promotions
                if getattr(item, "is_regional_feeder", False)
            ]
            random.shuffle(feeder_names)
            budget = max(0, int(throughput["graduation_slots"]))
            self.rules["regional_graduation_budget_month"] = self.month
            self.rules["regional_graduation_promotions"] = feeder_names[:budget]
        selected_promotions = set(self.rules.get("regional_graduation_promotions", []) or [])
        graduation_slots = 1 if promo.name in selected_promotions else 0
        overflow_kind = ""
        thin_market_candidates = [
            fighter for fighter in eligible
            if (fighter.gender, fighter.weight) in thin_female_divisions
        ]
        if graduation_slots <= 0:
            if (thin_market_candidates
                    and int(self.rules.get("regional_emergency_graduation_month", -1) or -1) != self.month):
                # A full global market must not hide an empty female division.
                # Permit only one global emergency call-up in a month.
                eligible = thin_market_candidates + [fighter for fighter in eligible if fighter not in thin_market_candidates]
                graduation_slots = 1
                overflow_kind = "emergency"
            elif (throughput["graduation_slots"] <= 0
                    and int(self.rules.get("regional_exceptional_graduation_month", -1) or -1) != self.month):
                # A healthy, full market still permits unavoidable aging-out
                # exits and exceptional breakouts, capped globally at one.
                priority = [fighter for fighter in eligible if fighter.age >= 28 and fighter.potential < 84]
                priority += [fighter for fighter in eligible if fighter.potential >= 88 or fighter.momentum >= 4]
                seen = set()
                eligible = [fighter for fighter in priority if not (id(fighter) in seen or seen.add(id(fighter)))]
                graduation_slots = min(1, len(eligible))
                overflow_kind = "exceptional" if graduation_slots else ""
            else:
                graduation_slots = 0
        graduation_slots = min(len(eligible), graduation_slots)
        graduated = 0
        for fighter in eligible[:graduation_slots]:
            if fighter not in promo.roster:
                continue
            if not self.move_regional_fighter_to_free_agency(
                promo,
                fighter,
                "Promoted from the regional circuit into the wider free-agent market.",
                "Regional graduate" if fighter.age < 28 else "Regional veteran exit",
                popularity_bonus=4,
            ):
                continue
            if fighter.trait == "Overlooked Talent":
                fighter.momentum = min(5, fighter.momentum + 1)
            bouts = fighter.record_w + fighter.record_l + fighter.record_d
            story_type = "Regional Breakthrough" if fighter.potential >= 80 or fighter.record_w >= fighter.record_l else "Regional Circuit Move"
            reason = "earning a second look" if story_type == "Regional Breakthrough" else "completing a regional run"
            self.news.insert(0, f"{story_type}: {fighter.name} ({fighter.record}, {bouts} bouts) leaves {promo.name} and enters free agency after {reason}.")
            self.record_world_story(story_type, f"{fighter.name} leaves {promo.name} after a regional run.", f"Record {fighter.record}, {bouts} bouts, popularity {fighter.popularity}, potential {fighter.potential}.", [promo.name], [fighter.name], 2)
            graduated += 1
        if graduated and overflow_kind == "emergency":
            self.rules["regional_emergency_graduation_month"] = self.month
        elif graduated and overflow_kind == "exceptional":
            self.rules["regional_exceptional_graduation_month"] = self.month
        return graduated

    def promote_regional_emergency_talent(self, slots):
        """Use experienced feeder talent before inventing an emergency free agent.

        A real market crash can need far more than a couple of graduates per
        circuit, and there's no need to protect it here: any vacancy this
        leaves behind is refilled with a fresh generated prospect on the very
        next monthly feeder pass regardless. So just pull evenly across every
        circuit in turn, with no per-circuit ceiling, instead of letting one
        circuit's best candidates supply the whole emergency.

        Within each circuit's turn the call-up is chosen by what the market is
        actually short of rather than by raw quality alone. Filling a headcount
        floor blindly let the biggest, most male-heavy circuits crowd out the
        divisions in genuine trouble -- a single-gender circuit could drain a
        whole emergency into divisions that were already comfortable while the
        women's divisions it cannot serve stayed empty.
        """
        slots = max(0, int(slots))
        if not slots:
            return 0
        division_stock = {}
        for fighter in self.free_agents:
            if (fighter.retired or fighter.retirement_pending or fighter.injured
                    or getattr(fighter, "ai_offer_company", "")):
                continue
            key = (fighter.gender, fighter.weight)
            division_stock[key] = division_stock.get(key, 0) + 1

        def scarcity_bonus(fighter):
            """Weight a call-up by how starved their division currently is."""
            stock = division_stock.get((fighter.gender, fighter.weight), 0)
            return max(0, 12 - stock) * 9

        promo_candidates = {}
        for promo in self.promotions:
            if not getattr(promo, "is_regional_feeder", False):
                continue
            ranked = []
            for fighter in promo.roster:
                bouts = fighter.record_w + fighter.record_l + fighter.record_d
                if (fighter.retired or fighter.injured or fighter.retirement_pending
                        or fighter.age < 20 or bouts < 5 or fighter.fatigue >= 65):
                    continue
                value = (
                    bouts * 4 + fighter.record_w * 3 + fighter.overall * 0.7
                    + fighter.potential * 0.25 + fighter.popularity * 0.2
                    + max(0, fighter.momentum) * 3 + random.uniform(-3, 3)
                )
                ranked.append((value, fighter))
            ranked.sort(key=lambda item: item[0], reverse=True)
            promo_candidates[promo.name] = ranked
        promo_by_name = {
            promo.name: promo for promo in self.promotions
            if getattr(promo, "is_regional_feeder", False)
        }
        moved = 0
        progress = True
        while progress and moved < slots:
            progress = False
            for name, ranked in promo_candidates.items():
                if moved >= slots or not ranked:
                    continue
                promo = promo_by_name[name]
                # Re-score against live stock each turn: every call-up changes
                # which divisions are still short, so a static quality order
                # would keep feeding divisions that have already recovered.
                pick = max(range(len(ranked)), key=lambda index: ranked[index][0] + scarcity_bonus(ranked[index][1]))
                _value, fighter = ranked.pop(pick)
                if fighter not in promo.roster:
                    continue
                division_stock[(fighter.gender, fighter.weight)] = division_stock.get((fighter.gender, fighter.weight), 0) + 1
                if not self.move_regional_fighter_to_free_agency(
                    promo,
                    fighter,
                    "Emergency call-up to the wider free-agent market.",
                    "Regional emergency call-up",
                    popularity_bonus=3,
                ):
                    continue
                moved += 1
                progress = True
        if moved:
            self.news.insert(0, f"Regional call-ups: {moved} experienced fighters entered free agency to meet market demand.")
        return moved

    def promote_year_end_regional_candidates(self, threshold=180, limit=5):
        """Top up a thin free-agent market with the most promotion-ready regional fighters.

        This is deliberately a small, once-per-year reserve mechanism. It is not
        a replacement for normal feeder graduation: age leads the decision, then
        regional wins, ability, current form, and public profile separate fighters
        who are otherwise ready for the wider market.
        """
        threshold = max(0, int(threshold))
        limit = max(0, int(limit))
        active_free_agents = [
            fighter for fighter in self.free_agents
            if not getattr(fighter, "retired", False)
        ]
        vacancies = max(0, threshold - len(active_free_agents))
        slots = min(limit, vacancies)
        if not slots:
            return 0

        candidates = []
        for promo in self.promotions:
            if not getattr(promo, "is_regional_feeder", False):
                continue
            division_counts = {}
            for member in promo.roster:
                if not getattr(member, "retired", False):
                    key = (member.gender, member.weight)
                    division_counts[key] = division_counts.get(key, 0) + 1
            for fighter in promo.roster:
                assessment = self.regional_candidate_assessment(fighter, promo)
                key = (fighter.gender, fighter.weight)
                if (
                    not (assessment["eligible"] or assessment["status"] == "Nearly Eligible")
                    or fighter.retired
                    or fighter.injured
                    or fighter.retirement_pending
                    or fighter.fatigue >= 65
                    or division_counts.get(key, 0) <= 3
                ):
                    continue
                bouts = assessment["bouts"]
                # Age is the strongest factor: the annual market release is mainly
                # for fighters who have had time to prove themselves in the feeder.
                age_value = min(56, max(0, fighter.age - 18) * 7)
                value = (
                    age_value
                    + fighter.record_w * 3.5
                    + fighter.overall * 0.30
                    + max(0, fighter.momentum) * 5
                    + fighter.popularity * 0.20
                    + min(12, bouts * 0.5)
                    + random.uniform(-2, 2)
                )
                candidates.append((value, promo, fighter))

        if not candidates:
            return 0
        candidates.sort(key=lambda item: item[0], reverse=True)
        moved = 0
        used_promotions = set()
        for _value, promo, fighter in candidates:
            if moved >= slots:
                break
            # Spread the annual intake across the feeder system where possible.
            if promo.name in used_promotions or fighter not in promo.roster:
                continue
            if not self.move_regional_fighter_to_free_agency(
                promo,
                fighter,
                "Year-end promotion from the regional circuit into the wider free-agent market.",
                "Year-end regional graduate",
                popularity_bonus=3,
            ):
                continue
            used_promotions.add(promo.name)
            moved += 1

        if moved:
            headline = f"Year-end regional class: {moved} promotion-ready fighters entered free agency as the market fell below {threshold}."
            self.news.insert(0, headline)
            self.record_world_story(
                "Regional Year-End Call-Ups", headline,
                "Older, winning, in-form regional fighters were prioritised to restore free-agent depth.",
                list(used_promotions), [], importance=2,
            )
        return moved

    def spawn_annual_regional_wonderkid(self):
        """Place one exceptional 17-year-old into the global regional pathway each year."""
        current_year = 2026 + (self.month - 1) // 12
        if (self.month - 1) % 12 != 0:
            return None
        if int(self.rules.get("regional_wonderkid_last_year", 2025) or 2025) >= current_year:
            return None
        feeders = [promo for promo in self.promotions if getattr(promo, "is_regional_feeder", False)]
        if not feeders:
            return None

        promo = random.choice(feeders)
        gender = "Female" if random.random() < 0.20 else "Male"
        # A single-gender circuit has no division to place them in.
        if not self.promotion_division_open(promo, gender, WEIGHTS[0]):
            gender = "Male" if gender == "Female" else "Female"
            if not self.promotion_division_open(promo, gender, WEIGHTS[0]):
                return None
        target_rating = random.randint(80, 84)
        potential = random.randint(max(87, target_rating + 3), 95)
        fighter = self.create_generated_fighter(
            12, 30, target_rating - 4, target_rating + 3,
            gender=gender, region=promo.region, apply_entry_balance=False,
            age_override=18, pre_universe=False,
        )
        self.avoid_name_collision(fighter, self.active_fighter_names())
        fighter.age = 17
        fighter.record_w = fighter.record_l = fighter.record_d = 0
        fighter.record_history_baseline_w = fighter.record_history_baseline_l = fighter.record_history_baseline_d = 0
        fighter.multi_sport_records = {"MMA": "0-0-0"}
        fighter.potential = potential
        fighter.contract_months = 0
        fighter.exclusive = False
        fighter.contract_type = "Developmental"
        fighter.feeder_origin = promo.name
        fighter.camp = self.suggest_camp_for_fighter(fighter, promo.region)
        fighter.camp_quality = self.gym_quality(fighter.camp)
        fighter.trait = random.choice(("Gym Rat", "Technical Learner", "Adaptable", "Prospect Mindset"))
        self.ensure_detailed_skills(fighter)
        # Shift the complete profile together so its style strengths survive
        # while the displayed overall lands in the promised 80-84 band.
        for _ in range(4):
            adjustment = target_rating - fighter.overall
            if adjustment == 0:
                break
            for key in fighter.detailed_skills:
                fighter.detailed_skills[key] = max(1, min(99, fighter.detailed_skills[key] + adjustment))
            self.sync_broad_skills_from_details(fighter)
        fighter.potential = max(fighter.overall + 3, potential)
        fighter.annual_overalls = {str(current_year): fighter.overall}
        fighter.rank_score = self.rank_value(fighter)
        promo.roster.append(fighter)
        self.rules["regional_wonderkid_last_year"] = current_year
        note = (f"Regional wonderkid: {fighter.name}, a 17-year-old {fighter.gender.lower()} "
                f"{fighter.weight} prospect rated {fighter.overall} with {fighter.potential} potential, "
                f"has joined {promo.name}.")
        self.news.insert(0, note)
        self.record_world_story(
            "Regional Wonderkid", note,
            "One exceptional teenager has emerged through the regional system and is now available to scout.",
            [promo.name], [fighter.name], importance=4,
        )
        return fighter

    def regional_recruit_fighter(self, promo, slots=1):
        """Keep development circuits deep enough to offer varied, fair matchups."""
        target = 100
        slots = min(max(0, int(slots)), self.regional_roster_vacancies(promo, target))
        for _ in range(slots):
            throughput = self.regional_market_throughput()
            deficit_ratio = throughput["deficit"] / max(1, throughput["target"])
            if deficit_ratio >= 0.40:
                fresh_intake_chance = 1.0
            elif deficit_ratio >= 0.25:
                fresh_intake_chance = 0.96
            elif deficit_ratio >= 0.12:
                fresh_intake_chance = 0.90
            else:
                fresh_intake_chance = 0.84
            if throughput["available_free_agents"] < 260:
                fresh_intake_chance = 1.0
            elif throughput["available_free_agents"] < 320:
                fresh_intake_chance = min(fresh_intake_chance, 0.75)
            elif throughput["available_free_agents"] < 420:
                fresh_intake_chance = min(fresh_intake_chance, 0.45)
            else:
                # Once the reserve is crowded, regional vacancies become the
                # proving ground for long-waiting young free agents. This is a
                # real roster transfer, not deletion, and fresh debuts resume
                # automatically as the market returns toward 200-300 fighters.
                fresh_intake_chance = min(fresh_intake_chance, 0.20)

            counts = {}
            for member in promo.roster:
                if not getattr(member, "retired", False):
                    key = (member.gender, member.weight)
                    counts[key] = counts.get(key, 0) + 1
            male_only = promo.name == EURASIAN_FIGHT_CIRCUIT_NAME
            if male_only:
                division_targets = {
                    ("Male", weight): (11 if weight in ("Light Heavyweight", "Heavyweight") else 13)
                    for weight in WEIGHTS
                }
            else:
                division_targets = {
                    (gender, weight): (
                        3 if gender == "Female" and weight in ("Light Heavyweight", "Heavyweight")
                        else 4 if gender == "Female"
                        else 8 if weight in ("Light Heavyweight", "Heavyweight")
                        else 9
                    )
                    for gender in ("Male", "Female") for weight in WEIGHTS
                }
            thinnest = sorted(
                division_targets,
                key=lambda key: (counts.get(key, 0) - division_targets[key], counts.get(key, 0), random.random()),
            )
            intake_gender, intake_weight = thinnest[0]
            candidates = [
                fighter for fighter in self.free_agents
                if not fighter.ai_offer_company and not fighter.retirement_pending and not fighter.injured and fighter.age <= 27
                and not self.is_blue_chip_prospect(fighter)
                and getattr(fighter, "free_agent_months", 0) >= 12
                # A regional graduate needs time in another market before they
                # can return. This is long enough to prevent carousel booking.
                and not (getattr(fighter, "last_regional_promotion", "") == promo.name and self.month - getattr(fighter, "regional_departure_month", 0) < 36)
                and (fighter.overall < 76 or fighter.potential >= 78)
                and not (male_only and fighter.gender != "Male")
            ]
            matching_candidates = [
                fighter for fighter in candidates
                if fighter.gender == intake_gender and fighter.weight == intake_weight
            ]
            if candidates and random.random() >= fresh_intake_chance:
                def proving_ground_value(item):
                    young_upside = item.potential - item.overall
                    overlooked = 18 if item.momentum <= 0 and item.age >= 21 else 0
                    division_fit = 18 if item.gender == intake_gender and item.weight == intake_weight else 0
                    return young_upside + overlooked + division_fit + item.professionalism * 0.12 + random.uniform(-8, 8)
                fighter = max(matching_candidates or candidates, key=proving_ground_value)
                self.free_agents.remove(fighter)
                fighter.contract_months = 0
                fighter.exclusive = False
                fighter.contract_type = "Developmental"
                fighter.free_agent_months = 0
                fighter.feeder_origin = promo.name
                fighter.regional_entry_w = fighter.record_w
                fighter.regional_entry_l = fighter.record_l
                fighter.regional_entry_d = fighter.record_d
                fighter.camp = promo.name
                if fighter.age >= 21 and fighter.momentum <= 0 and random.random() < 0.6:
                    fighter.trait = "Overlooked Talent"
                    fighter.morale = min(100, fighter.morale + 8)
                    self.news.insert(0, f"Second chance: {fighter.name} joins {promo.name} to rebuild their record and market value.")
                promo.roster.append(fighter)
                continue
            fighter = self.create_regional_feeder_fighter(promo.region, self.active_fighter_names(), intake_gender)
            fighter.weight = intake_weight
            fighter.camp = promo.name
            fighter.feeder_origin = promo.name
            fighter.market_origin = "Regional youth intake"
            if male_only:
                self.apply_eurasian_origin(fighter, used_names=self.active_fighter_names())
            fighter.regional_entry_w = fighter.record_w
            fighter.regional_entry_l = fighter.record_l
            fighter.regional_entry_d = fighter.record_d
            promo.roster.append(fighter)

    def market_churn(self):
        self.resolve_ai_contract_offers()
        self.ai_create_contract_offers()
        self.ensure_free_agent_depth(emergency=True)

    def is_blue_chip_prospect(self, fighter):
        return fighter.age <= 30 and (
            fighter.potential >= 90
            or (fighter.age <= 27 and fighter.potential >= 88 and fighter.overall >= 65)
            or (fighter.potential >= 85 and fighter.record_w >= 6)
            or (fighter.overall >= 88 and fighter.record_w >= 5)
        )

    def advance_free_agent_market(self):
        for fighter in self.free_agents:
            previous_months = max(0, getattr(fighter, "free_agent_months", 0))
            fighter.free_agent_months = previous_months + 1
            # Every newly available fighter gets one full market pass where the
            # player can scout or negotiate before AI boards can bid. This
            # applies to releases, graduates, and generated entrants alike;
            # blue-chip prospects still receive their longer dedicated window.
            if (not getattr(self, "spectator_mode", False)
                    and previous_months == 0
                    and getattr(fighter, "player_talent_window_until", 0) < self.month):
                fighter.player_talent_window_until = self.month
            if (not getattr(self, "spectator_mode", False) and self.is_blue_chip_prospect(fighter)
                    and not fighter.player_talent_alerted):
                fighter.player_talent_alerted = True
                fighter.player_talent_window_until = self.month + 2
                self.inbox.append({
                    "subject": f"Blue-Chip Talent Alert - {fighter.name}",
                    "body": (f"Scouting has flagged {fighter.name} ({fighter.gender} {fighter.weight}, {fighter.record}) as an elite-upside free agent. "
                             "You have a two-month exclusive scouting window before rival promotions enter the bidding."),
                    "type": "Scouting", "resolved": False,
                })
                self.news.insert(0, f"Blue-chip alert: {fighter.name} is available. Rival bidding opens in two months.")

    def simulate_free_agent_showcases(self):
        """Run small, watchable independent cards for unsigned talent."""
        eligible = [fighter for fighter in self.free_agents if not fighter.retired and not fighter.injured
                    and not fighter.ai_offer_company and fighter.fatigue < 42 and fighter.free_agent_months >= 2
                    and self.month - getattr(fighter, "showcase_last_month", -99) >= 3]
        groups = {}
        for fighter in eligible:
            groups.setdefault((fighter.gender, fighter.weight), []).append(fighter)
        # Do not create a token independent event. A card may span any number
        # of divisions, but the available pool must yield five legal bouts.
        if sum(len(fighters) // 2 for fighters in groups.values()) < 5:
            return
        bouts = 0
        fight_logs = []
        event_log = []
        results = []
        # Independent cards should feel like full fight nights when the unsigned
        # pool supports them, while the five-bout eligibility minimum above
        # prevents thin, token events.
        bout_target = random.randint(6, 16)
        event_name = f"Independent Showcase {getattr(self, 'independent_showcase_counter', 1)}"
        ordered_groups = sorted(
            groups.values(),
            key=lambda fighters: (
                any(getattr(fighter, "retirement_pending", False) for fighter in fighters),
                max((fighter.age for fighter in fighters if getattr(fighter, "retirement_pending", False)), default=0),
                sum(1 for fighter in fighters if fighter.age < 36),
                len(fighters),
            ),
            reverse=True,
        )
        for fighters in ordered_groups:
            if bouts >= bout_target:
                break
            # Veterans remain eligible, but ordinary independent cards should
            # naturally lean toward the younger active market. Retirement bouts
            # still take precedence regardless of age.
            fighters.sort(key=lambda fighter: (
                getattr(fighter, "retirement_pending", False),
                fighter.age < 36,
                fighter.overall,
                fighter.record_w - fighter.record_l,
                fighter.free_agent_months,
            ), reverse=True)
            while len(fighters) >= 2 and bouts < bout_target:
                a = fighters.pop(0)
                b = min(fighters, key=lambda fighter: (
                    abs(fighter.overall - a.overall)
                    + abs((fighter.record_w + fighter.record_l) - (a.record_w + a.record_l)) * 0.3
                    + self.matchup_history_penalty(a, fighter)
                    + random.uniform(0, 2.5)
                ))
                fighters.remove(b)
                a_record, b_record = a.record, b.record
                a_rating, b_rating = self.bout_rating_snapshot(a), self.bout_rating_snapshot(b)
                fight = {"main": False, "title": False, "tier": "Independent Showcase", "region": a.region}
                winner, loser, method, round_no, lines = self.simulate_fight(a, b, fight)
                excitement = self.fight_excitement(a, b, winner, loser, method, round_no, fight, a.popularity + b.popularity)
                if method == "Draw":
                    self.apply_draw_result(a, b, fight)
                    result_line = f"{a.name} vs {b.name} - Draw (R{round_no})"
                else:
                    self.apply_result(winner, loser, fight, method)
                    result_line = f"{winner.name} def. {loser.name} by {method} (R{round_no})"
                self.record_season_result(winner, loser, method, round_no, fight, excitement, "Independent Circuit")
                for fighter in (a, b):
                    fighter.popularity = min(55, fighter.popularity + (2 if fighter is winner and method != "Draw" else 1))
                    fighter.showcase_last_month = self.month
                fight_logs.append({"heading": f"{a.name} vs {b.name}", "label": "INDEPENDENT SHOWCASE",
                                   "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id, "a_record": a_record, "b_record": b_record, "a_rating": a_rating, "b_rating": b_rating,
                                   "weight": a.weight, "result": result_line,
                                   "lines": list(lines) + ["", result_line]})
                event_log.extend([f"[SHOWCASE] {a.name} vs {b.name}", *lines, result_line, ""])
                results.append((a, b, result_line, excitement))
                bouts += 1
                self.retire_after_final_fight_if_due(a, "Independent Circuit")
                self.retire_after_final_fight_if_due(b, "Independent Circuit")
        if not results:
            return
        self.independent_showcase_counter = getattr(self, "independent_showcase_counter", 1) + 1
        headline = max(results, key=lambda item: item[3])[2]
        summary = f"{event_name}: {len(results)} bouts; showcase highlight {headline}."
        package = {
            "date": f"Month {self.month} Week {self.week}", "company": "Independent Circuit",
            "event_name": event_name, "summary": summary, "fight_count": len(results), "profit": 0,
            "finance": {"ticket_revenue": 0, "total_revenue": 0, "total_expense": 0, "profit": 0},
            "log": [summary, ""] + event_log, "fight_logs": fight_logs,
        }
        self.ai_event_archive.insert(0, package)
        self.ai_event_archive = self.ai_event_archive[:120]
        self.archive_result_record({
            "date": package["date"], "company": "Independent Circuit", "event": event_name,
            "summary": summary, "fights": len(results), "gate": "$0", "profit": "$0",
            "log": package["log"], "fight_logs": fight_logs, "finance": package["finance"],
        })
        if not getattr(self, "spectator_mode", False):
            for a, b, result_line, _excitement in results:
                for fighter in (a, b):
                    if self.is_blue_chip_prospect(fighter):
                        self.inbox.append({"subject": f"Showcase Scouting Report - {fighter.name}", "body": f"{fighter.name} competed at {event_name}: {result_line}. They remain available to negotiate.", "type": "Scouting", "resolved": False})
        self.news.insert(0, summary)
        self.record_world_story("Independent Showcase", summary, "Unsigned fighters competed for contracts and visibility.", ["Independent Circuit"], [fighter.name for result in results for fighter in result[:2]], 2)

    def eligible_free_agent_retirement_card_fighters(self):
        """Return healthy, genuinely long-waiting retirees who can fight this week."""
        current_week = self.calendar_week_index()
        return [
            fighter for fighter in self.free_agents
            if not fighter.retired and fighter.retirement_pending
            and fighter.free_agent_months >= (3 if fighter.age >= 43 else 6 if fighter.age >= 40 else 12)
            and not fighter.injured
            and not fighter.ai_offer_company and fighter.fatigue < 70
            and current_week >= getattr(fighter, "available_week", 0)
            and self.month - getattr(fighter, "showcase_last_month", -99) >= 3
        ]

    def retirement_cards_already_run_this_week(self):
        date = f"Month {self.month} Week {self.week}"
        return sum(
            1 for record in self.result_records
            if record.get("date") == date
            and str(record.get("event", "")).startswith("Independent Retirement Card")
        )

    def retirement_card_weekly_limit(self, waiting_count):
        """Keep farewell events special: one normally, two only for a severe queue."""
        if waiting_count < 10:
            return 0
        return 2 if waiting_count >= 48 else 1

    def simulate_due_free_agent_retirement_cards(self):
        # Long-waiting free agents receive a controlled medical clearance for
        # their farewell event. They still need a real, simulated final bout;
        # this only prevents a minor old injury from trapping the whole card
        # queue forever in a legacy or long-running save.
        for fighter in self.free_agents:
            if (getattr(fighter, "retirement_pending", False)
                    and self.retirement_fight_wait_months(fighter) >= 12):
                fighter.injured = 0
                fighter.fatigue = min(fighter.fatigue, 45)
        waiting = self.eligible_free_agent_retirement_card_fighters()
        limit = self.retirement_card_weekly_limit(len(waiting))
        remaining = max(0, limit - self.retirement_cards_already_run_this_week())
        packages = []
        for _ in range(remaining):
            package = self.simulate_free_agent_retirement_card()
            if not package:
                break
            packages.append(package)
        return packages

    def simulate_free_agent_retirement_card(self):
        """Run a dedicated farewell card when the unsigned retirement queue is large.

        Ordinary independent showcases remain the quickest route to a final bout.
        This card is the queue safety net: it exists only when at least ten
        healthy retirement-pending free agents have reached their age-based
        market limit (three months at 43+, six at 40+, twelve when younger).
        Every matchup remains within gender and weight class, and the most popular
        available farewells headline a card of no more than twelve bouts.
        """
        waiting = self.eligible_free_agent_retirement_card_fighters()
        if len(waiting) < 10:
            return None

        waiting.sort(
            key=lambda fighter: (
                fighter.popularity,
                self.retirement_fight_wait_months(fighter),
                fighter.age,
                fighter.overall,
            ),
            reverse=True,
        )
        groups = {}
        for fighter in waiting:
            groups.setdefault((fighter.gender, fighter.weight), []).append(fighter)
        pairings = []
        for fighters in groups.values():
            fighters.sort(
                key=lambda fighter: (
                    fighter.popularity,
                    self.retirement_fight_wait_months(fighter),
                    fighter.age,
                    fighter.overall,
                ),
                reverse=True,
            )
            while len(fighters) >= 2:
                fighter = fighters.pop(0)
                opponent = min(
                    fighters,
                    key=lambda other: (
                        self.matchup_history_penalty(fighter, other),
                        abs(other.overall - fighter.overall),
                        abs((other.record_w + other.record_l) - (fighter.record_w + fighter.record_l)),
                        -other.popularity,
                    ),
                )
                fighters.remove(opponent)
                pairings.append((fighter, opponent))

        # Ten waiting fighters should create a genuine card, not one or two bouts
        # assembled from otherwise unpairable divisions.
        if len(pairings) < 5:
            return None

        pairings.sort(
            key=lambda pairing: (
                max(pairing[0].popularity, pairing[1].popularity),
                pairing[0].popularity + pairing[1].popularity,
            ),
            reverse=True,
        )
        card_number = self.retirement_cards_already_run_this_week() + 1
        suffix = f" #{card_number}" if card_number > 1 else ""
        event_name = f"Independent Retirement Card{suffix} - {self.current_year()} M{(self.month - 1) % 12 + 1}"
        fight_logs = []
        event_log = []
        results = []
        retired_names = []

        for index, (a, b) in enumerate(pairings[:12]):
            a.fatigue = min(a.fatigue, 35)
            b.fatigue = min(b.fatigue, 45)
            a_record, b_record = a.record, b.record
            a_rating, b_rating = self.bout_rating_snapshot(a), self.bout_rating_snapshot(b)
            fight = {
                "main": index == 0,
                "title": False,
                "tier": "Retirement Card Main Event" if index == 0 else "Retirement Card",
                "region": a.region,
            }
            winner, loser, method, round_no, lines = self.simulate_fight(a, b, fight)
            excitement = self.fight_excitement(a, b, winner, loser, method, round_no, fight, a.popularity + b.popularity)
            retiring_before = [fighter.name for fighter in (a, b) if fighter.retirement_pending]
            if method == "Draw":
                self.apply_draw_result(a, b, fight)
                result_line = f"{a.name} vs {b.name} - Draw (R{round_no})"
            else:
                self.apply_result(winner, loser, fight, method)
                result_line = f"{winner.name} def. {loser.name} by {method} (R{round_no})"
            self.record_season_result(winner, loser, method, round_no, fight, excitement, "Independent Circuit")
            for fighter in (a, b):
                fighter.showcase_last_month = self.month
                self.retire_after_final_fight_if_due(fighter, "Independent Circuit")
            retired_names.extend(retiring_before)
            label = "RETIREMENT CARD MAIN EVENT" if index == 0 else "RETIREMENT CARD"
            fight_logs.append({
                "heading": f"{a.name} vs {b.name}", "label": label,
                "a": a.name, "b": b.name, "a_id": a.fighter_id, "b_id": b.fighter_id, "a_record": a_record, "b_record": b_record, "a_rating": a_rating, "b_rating": b_rating,
                "weight": a.weight, "result": result_line,
                "lines": list(lines) + ["", result_line],
            })
            event_log.extend([f"[{label}] {a.name} vs {b.name}", *lines, result_line, ""])
            results.append((a, b, result_line, excitement))

        headline = results[0][2]
        summary = f"{event_name}: {len(results)} farewell bouts; main event {headline}."
        package = {
            "date": f"Month {self.month} Week {self.week}", "company": "Independent Circuit",
            "event_name": event_name, "summary": summary, "fight_count": len(results), "profit": 0,
            "finance": {"ticket_revenue": 0, "total_revenue": 0, "total_expense": 0, "profit": 0},
            "log": [summary, ""] + event_log, "fight_logs": fight_logs,
            "retired_names": list(dict.fromkeys(retired_names)),
        }
        self.ai_event_archive.insert(0, package)
        self.ai_event_archive = self.ai_event_archive[:120]
        self.archive_result_record({
            "date": package["date"], "company": "Independent Circuit", "event": event_name,
            "summary": summary, "fights": len(results), "gate": "$0", "profit": "$0",
            "log": package["log"], "fight_logs": fight_logs, "finance": package["finance"],
        })
        self.news.insert(0, summary)
        self.record_world_story(
            "Retirement Card", summary,
            f"The independent circuit gave {len(package['retired_names'])} long-waiting veterans their final contests.",
            ["Independent Circuit"], package["retired_names"], 4,
        )
        return package

    def independent_showcases_due(self):
        """Scale independent-card supply to the actual unsigned talent pool."""
        pool_size = len([fighter for fighter in self.free_agents if not fighter.retired])
        if pool_size < 90:
            return 1 if self.week == 1 else 0
        if pool_size < 180:
            return 1 if self.week in (1, 3) else 0
        if pool_size < 350:
            return 1
        if pool_size < 500:
            return 2 if self.week in (1, 3) else 1
        if pool_size < 900:
            return 2
        if pool_size < 1800:
            return 3
        return 4

    def update_ai_contracts(self):
        for promo in [item for item in self.promotions if not getattr(item, "is_regional_feeder", False)]:
            belt_holders = self.promotion_belt_holders(promo)
            for fighter in list(promo.roster):
                if fighter.contract_months > 0:
                    continue
                # A declared retiree may finish an already-booked farewell bout,
                # but an expired contract must not be renewed simply because the
                # fighter is popular, a champion, or useful divisional coverage.
                if fighter.retirement_pending:
                    promo.roster.remove(fighter)
                    fighter.contract_months = 0
                    fighter.exclusive = False
                    fighter.contract_type = "Free Agent"
                    fighter.free_agent_months = 0
                    fighter.champion = False
                    fighter.interim_champion = False
                    self.clear_ai_contract_offer(fighter)
                    self.free_agents.append(fighter)
                    continue
                active_roster = [member for member in promo.roster if not member.retired]
                # Expiring contracts are the least disruptive place for a
                # struggling promotion to retrench. A solvent company keeps
                # its full long-term plan; a cash-poor one only renews depth it
                # can responsibly carry today.
                roster_target = self.ai_financial_roster_target(promo)
                division_depth = sum(1 for member in active_roster if member.gender == fighter.gender and member.weight == fighter.weight)
                cornerstone = (fighter.champion or fighter.interim_champion or fighter.name in belt_holders or fighter.overall >= 82
                               or fighter.potential >= 90 or fighter.popularity >= 68)
                normal_value = fighter.overall >= 75 or fighter.potential >= 86 or fighter.popularity >= 50
                coverage_value = division_depth <= 4 or (division_depth <= 5 and (fighter.overall >= 64 or fighter.potential >= 75))
                division_target = self.ai_division_target(promo, fighter.gender)
                usable_depth = (fighter.overall >= 50 or fighter.potential >= 68 or fighter.popularity >= 22
                                or (fighter.age <= 27 and fighter.potential >= 64))
                regional_core = self.promotion_regional_affinity(promo, fighter) >= 14 and usable_depth
                # A promotion below its sustainable card roster protects useful
                # depth while that fighter's division is also within plan. The
                # upgrade review provides gradual churn later; expiring every
                # opening depth deal at six fighters flooded the market before
                # promotions had built their intended long-term rosters.
                planned_depth = len(active_roster) <= roster_target and usable_depth
                retain = cornerstone or coverage_value or planned_depth or regional_core or (len(active_roster) <= roster_target and normal_value)
                renewal_runway = promo.cash > max(180_000, promo.size * 9_000)
                # Renewing a champion or essential divisional coverage has no
                # signing bonus. Their purses are paid only when booked, so a
                # recovering promotion should not release and immediately
                # replace the same depth merely because cash is temporarily low.
                if retain and (renewal_runway or cornerstone or coverage_value):
                    fighter.contract_months = random.randint(10, 24)
                    market_purse = self.ai_market_purse(promo, fighter)
                    renewal_floor = min(self.ai_contract_purse_cap(promo, fighter), round(fighter.purse * 0.94))
                    fighter.purse = round(max(renewal_floor, market_purse * random.uniform(0.98, 1.10)) / 500) * 500
                    continue
                promo.roster.remove(fighter)
                fighter.contract_months = 0
                fighter.exclusive = False
                fighter.contract_type = "Free Agent"
                fighter.free_agent_months = 0
                fighter.champion = False
                fighter.interim_champion = False
                self.free_agents.append(fighter)

    def review_ai_roster_cuts(self):
        """Let AI companies make selective, explainable roster cuts.

        Expired contracts alone keep a roster artificially static. This review
        gives each promotion a modest chance to release a redundant, expensive,
        inactive, or clearly struggling fighter before expiry. It deliberately
        does not manufacture a market: champions, booked fighters, blue-chip
        prospects, and shallow divisions are protected, and released fighters
        become real free agents who can rebuild on independent cards.
        """
        scheduled = set(self.scheduled_fighter_names(include_booked=True)) if hasattr(self, "scheduled_fighter_names") else set()
        for promo in [item for item in self.promotions if not getattr(item, "is_regional_feeder", False)]:
            active = [fighter for fighter in promo.roster if not fighter.retired]
            if len(active) < 12:
                continue
            strategy = self.update_ai_promotion_strategy(promo)
            ideal_roster_target = self.ai_roster_target(promo)
            roster_target = self.ai_financial_roster_target(promo)
            financial_retrenchment = roster_target < ideal_roster_target
            # A distressed company can trim surplus, but it must retain enough
            # opponents for a division to remain meaningfully bookable.
            counts = {}
            for fighter in active:
                key = (fighter.gender, fighter.weight)
                counts[key] = counts.get(key, 0) + 1
            belt_holders = self.promotion_belt_holders(promo)

            candidates = []
            for fighter in active:
                if (fighter.champion or fighter.interim_champion or fighter.name in belt_holders or fighter.retirement_pending
                        or fighter.name in scheduled or fighter.age <= 24 and fighter.potential >= fighter.overall + 8):
                    continue
                depth = counts.get((fighter.gender, fighter.weight), 0)
                division_target = self.ai_division_target(promo, fighter.gender)
                division_floor = 4 if financial_retrenchment else max(4, division_target - 1)
                # Never solve one company's payroll by hollowing out the only
                # bookable part of a division.
                if depth <= division_floor:
                    continue
                bouts = fighter.record_w + fighter.record_l + fighter.record_d
                win_rate = fighter.record_w / max(1, bouts)
                months_idle = max(0, self.month - getattr(fighter, "last_fight_month", 0))
                poor_form = bouts >= 7 and win_rate < 0.34 and fighter.momentum <= -2
                expensive = fighter.purse > max(18_000, promo.size * 260)
                redundant = depth > (division_floor if financial_retrenchment else division_target)
                near_expiry = fighter.contract_months <= 6
                declining = fighter.age >= max(33, fighter.prime_end + 2) and fighter.overall < 76
                if not (poor_form or expensive or redundant or near_expiry or (months_idle >= 10 and declining)):
                    continue
                # Higher score means less central to the current company plan.
                cut_score = 0.0
                cut_score += max(0, depth - (division_floor if financial_retrenchment else division_target)) * 20
                cut_score += max(0, 0.48 - win_rate) * 42 if bouts >= 5 else 0
                cut_score += max(0, -fighter.momentum) * 3
                cut_score += min(18, months_idle * 1.5)
                cut_score += max(0, fighter.purse / max(1, promo.size * 220) - 1) * 16
                cut_score += max(0, fighter.age - fighter.prime_end) * 2
                cut_score -= max(0, fighter.potential - fighter.overall) * 1.4
                cut_score -= fighter.popularity * 0.18
                cut_score -= self.promotion_regional_affinity(promo, fighter) * 0.9
                candidates.append((cut_score, fighter, poor_form, expensive, redundant))

            if not candidates:
                continue
            oversized = max(0, len(active) - roster_target)
            financial_pressure = strategy.get("financial_pressure", 0)
            max_cuts = 0
            if oversized >= 20:
                max_cuts = 3
            elif oversized >= 12:
                max_cuts = 2
            elif oversized >= 4 or (financial_pressure >= 125 and any(item[3] for item in candidates)):
                max_cuts = 1
            elif len(active) >= roster_target and any(item[4] for item in candidates) and random.random() < 0.36:
                max_cuts = 1
            elif financial_pressure >= 190 and random.random() < 0.24:
                max_cuts = 1
            if not max_cuts:
                continue

            released = []
            for _score, fighter, poor_form, expensive, redundant in sorted(candidates, key=lambda item: item[0], reverse=True):
                if len(released) >= max_cuts or fighter not in promo.roster:
                    break
                key = (fighter.gender, fighter.weight)
                fighter_target = self.ai_division_target(promo, fighter.gender)
                fighter_floor = 4 if financial_retrenchment else max(4, fighter_target - 1)
                if counts.get(key, 0) <= fighter_floor:
                    continue
                # A one-fight cut is possible only for a genuinely poor or
                # costly fit. This avoids cutting solid contracted depth merely
                # because the monthly random review happened to fire.
                if fighter.contract_months > 6 and not (poor_form or expensive or redundant):
                    continue
                promo.roster.remove(fighter)
                counts[key] -= 1
                fighter.contract_months = 0
                fighter.exclusive = False
                fighter.contract_type = "Free Agent"
                fighter.free_agent_months = 0
                self.clear_ai_contract_offer(fighter)
                fighter.morale = max(20, fighter.morale - random.randint(4, 10))
                fighter.fight_history = list(fighter.fight_history or [])
                fighter.fight_history.insert(0, f"Month {self.month}: Released by {promo.name} after roster review.")
                self.free_agents.append(fighter)
                released.append(fighter)
            if released:
                names = ", ".join(fighter.name for fighter in released)
                note = f"Roster review: {promo.name} released {names} to free agency."
                promo.show_history = list(promo.show_history or [])
                promo.show_history.insert(0, note)
                promo.show_history = promo.show_history[:12]
                self.news.insert(0, note)
                self.record_world_story("Roster Review", note, "The promotion rebalanced its roster around division depth, form, contract cost, and future upside.", [promo.name], [fighter.name for fighter in released], importance=2)

    def review_ai_upgrade_replacements(self):
        """Make occasional, explainable same-division quality upgrades.

        The normal market builds depth. This review exists for the obvious case
        where a solvent company keeps an aging or weak non-core fighter while a
        substantially stronger free agent is available in that exact division.
        It is deliberately capped at one completed move per company every two
        months, and respects the player's newly-available-fighter grace period.
        """
        scheduled = set(self.scheduled_fighter_names(include_booked=True)) if hasattr(self, "scheduled_fighter_names") else set()
        free_agents = [
            fighter for fighter in self.free_agents
            if not fighter.retired and not fighter.retirement_pending and not fighter.injured
            and not fighter.ai_offer_company and fighter.fatigue < 55 and fighter.age >= 18
            and (getattr(self, "spectator_mode", False) or getattr(fighter, "player_talent_window_until", 0) < self.month)
        ]
        if not free_agents:
            return

        promos = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False)]
        promos.sort(key=lambda promo: (
            self.ai_financial_roster_target(promo) - len([fighter for fighter in promo.roster if not fighter.retired]),
            promo.cash,
            random.random(),
        ), reverse=True)
        for promo in promos:
            strategy = self.promotion_strategy(promo)
            if self.month - int(strategy.get("last_upgrade_review_month", -99) or -99) < 2:
                continue
            completed = 0
            # Three moves is the hard ceiling for a two-month review cycle. It
            # lets a board correct obvious mistakes without emptying the market.
            while completed < 3:
                active = [fighter for fighter in promo.roster if not fighter.retired]
                if len(active) < 12 or promo.cash <= self.ai_contract_reserve(promo):
                    break
                belt_holders = self.promotion_belt_holders(promo)
                by_division = {}
                for fighter in active:
                    by_division.setdefault((fighter.gender, fighter.weight), []).append(fighter)
                best = None
                quality_benchmark = max(62, min(70, 62 + max(0, promo.reputation_score - 70) * 0.24))
                incoming_floor = max(65, min(74, round(quality_benchmark + 3)))
                for incoming in list(free_agents):
                    if incoming not in self.free_agents:
                        continue
                    development_signing = (
                        incoming.age <= 27
                        and incoming.potential >= incoming_floor + 9
                        and incoming.overall >= incoming_floor - 4
                    )
                    if incoming.overall < incoming_floor and not development_signing:
                        continue
                    incumbents = by_division.get((incoming.gender, incoming.weight), [])
                    if len(incumbents) <= 4:
                        continue
                    replaceable = [fighter for fighter in incumbents
                                   if not fighter.champion and not fighter.interim_champion and fighter.name not in belt_holders
                                   and fighter.name not in scheduled and not fighter.retirement_pending
                                   and not (fighter.age <= 24 and fighter.potential >= fighter.overall + 8)]
                    if not replaceable:
                        continue
                    incumbent = min(replaceable, key=lambda fighter: (
                        fighter.overall + max(0, fighter.potential - fighter.overall) * 0.35
                        + min(8, fighter.popularity * 0.08) - max(0, fighter.age - 32) * 0.55
                    ))
                    gap = incoming.overall - incumbent.overall
                    quality_deficit = max(0, quality_benchmark - incumbent.overall)
                    required_gap = 9
                    required_gap -= 2 if quality_deficit >= 8 else 0
                    required_gap -= 1 if incumbent.age >= 35 else 0
                    required_gap += 3 if incoming.age >= 38 else 0
                    required_gap = max(5, required_gap)
                    if gap < required_gap:
                        continue
                    purse, months, signing = self.ai_offer_terms(promo, incoming)
                    purse = min(self.ai_contract_purse_cap(promo, incoming), max(incoming.purse, round(purse * 1.08 / 500) * 500))
                    signing = round(signing * 1.10 / 500) * 500
                    expected = max(incoming.purse * 1.15, incoming.overall * 260 + incoming.popularity * 430)
                    acceptance = purse / max(1, expected) * 58 + promo.reputation_score * 0.34 + promo.stability * 0.16
                    acceptance += min(12, self.promotion_regional_affinity(promo, incoming) * 0.55)
                    if promo.cash < self.ai_contract_reserve(promo) + purse + signing or acceptance < 64:
                        continue
                    score = gap * 11 + self.ai_free_agent_value(promo, incoming) + max(0, incumbent.age - incoming.age) * 1.5
                    if best is None or score > best[0]:
                        best = (score, incoming, incumbent, purse, months, signing)
                if best is None:
                    break
                _score, incoming, incumbent, purse, months, signing = best
                if incoming not in self.free_agents or incumbent not in promo.roster:
                    break
                promo.roster.remove(incumbent)
                incumbent.contract_months = 0
                incumbent.exclusive = False
                incumbent.contract_type = "Free Agent"
                incumbent.free_agent_months = 0
                self.clear_ai_contract_offer(incumbent)
                incumbent.morale = max(20, incumbent.morale - random.randint(3, 7))
                incumbent.fight_history = list(incumbent.fight_history or [])
                incumbent.fight_history.insert(0, f"Month {self.month}: Released by {promo.name} after an upgrade review.")
                self.free_agents.append(incumbent)
                signed, _message = self.complete_ai_free_agent_signing(incoming, promo, purse, months, signing, source="AI upgrade replacement review")
                if not signed:
                    if incumbent in self.free_agents:
                        self.free_agents.remove(incumbent)
                    promo.roster.append(incumbent)
                    break
                free_agents.remove(incoming)
                completed += 1
                note = f"Upgrade review: {promo.name} released {incumbent.name} and signed {incoming.name} for a clear {incoming.gender} {incoming.weight} upgrade."
                promo.show_history = list(promo.show_history or [])
                promo.show_history.insert(0, note)
                promo.show_history = promo.show_history[:12]
                self.news.insert(0, note)
                self.record_world_story("Roster Upgrade", note, f"{incumbent.overall} OVR replaced by {incoming.overall} OVR; deal ${purse:,}/fight for {months} months.", [promo.name], [incoming.name, incumbent.name], importance=3)
            if completed:
                strategy["last_upgrade_review_month"] = self.month

    def promotion_belt_holders(self, promo):
        """Return every primary/interim holder recorded by a promotion.

        Fighter flags are the normal path, but belt tables are authoritative for
        older saves and editor imports. Roster cuts must never accidentally
        release a titleholder because only one representation was updated.
        """
        holders = set()

        def collect(value):
            if isinstance(value, dict):
                for nested in value.values():
                    collect(nested)
            elif isinstance(value, str) and value.strip() and value != "Vacant":
                holders.add(value.strip())

        collect(getattr(promo, "belts", {}) or {})
        collect(getattr(promo, "interim_belts", {}) or {})
        return holders

    def clear_ai_contract_offer(self, fighter):
        fighter.ai_offer_company = ""
        fighter.ai_offer_purse = 0
        fighter.ai_offer_months = 0
        fighter.ai_offer_signing_bonus = 0
        fighter.ai_offer_deadline_month = 0

    def ai_division_target(self, promo, gender=None):
        """Sustainable contracted depth per gender/weight bucket for an AI company."""
        # Regional circuits are deliberately smaller, but still need enough
        # bodies across all sixteen buckets to rotate opponents and run varied
        # development cards.
        if getattr(promo, "is_regional_feeder", False):
            return 5
        named_targets = {
            # These values are per gender/weight bucket. They must support the
            # stated company roster targets across all sixteen MMA divisions.
            "Ultimate Fighting Championship": 25,
            "Professional Fighters League": 20,
            "ONE Championship": 20,
            "RIZIN Fighting Federation": 20,
            "KSW": 20,
            "Cage Warriors": 20,
            "Oktagon MMA": 20,
            "Legacy Fighting Alliance": 20,
            "BRAVE Combat Federation": 20,
            "Absolute Championship Akhmat": 20,
            "BAMMA": 20,
            "PRIDE Fighting Championships": 20,
            "Strikeforce": 20,
            "World Extreme Cagefighting": 20,
        }
        if promo.name in named_targets:
            base_target = named_targets[promo.name]
        elif promo.size >= 80:
            base_target = 8
        elif promo.size >= 60:
            base_target = 6
        elif promo.size >= 40:
            base_target = 5
        else:
            base_target = 4
        if gender not in ("Male", "Female"):
            return base_target
        # The old flat target allocated half the roster to each gender, so a
        # healthy 32-man division at a 320-fighter company was treated as
        # twelve contracts over plan and dumped into free agency. Preserve the
        # same total capacity while giving each gender its actual roster share.
        # This must track the real regional-intake ratio (46 male / 24 female
        # per circuit, ~66/34) rather than an assumed 80/20 split -- a
        # mismatched assumption here starved the free-agent market of men and
        # flooded it with women over long saves, since majors were budgeting
        # demand against a gender split the world doesn't actually produce.
        share = 1.31 if gender == "Male" else 0.69
        return max(4, round(base_target * share))

    def ai_roster_target(self, promo):
        """Roster capacity is tied to the divisions a company must actually book."""
        if getattr(promo, "is_regional_feeder", False):
            return 70
        weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
        open_divisions = sum(1 for gender in ("Male", "Female") for weight in weights if self.promotion_division_open(promo, gender, weight))
        named_targets = {
            "Ultimate Fighting Championship": 400,
            "Professional Fighters League": 320,
            "ONE Championship": 320,
            "RIZIN Fighting Federation": 320,
            "KSW": 320,
            "Cage Warriors": 320,
            "Oktagon MMA": 320,
            "Legacy Fighting Alliance": 320,
            "BRAVE Combat Federation": 320,
            "Absolute Championship Akhmat": 320,
            "BAMMA": 320,
            "PRIDE Fighting Championships": 320,
            "Strikeforce": 320,
            "World Extreme Cagefighting": 320,
        }
        return max(named_targets.get(promo.name, 40), open_divisions * self.ai_division_target(promo))

    def ai_roster_cap(self, promo):
        """Hard ceiling that prevents a wealthy AI company hoarding the market."""
        weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
        # A modest buffer permits one opportunistic signing and normal contract
        # overlap, but does not let a major promotion absorb the free-agent pool.
        return self.ai_roster_target(promo) + max(16, len(weights) * 3)

    def ai_financial_runway(self, promo):
        """Cash reserve needed to run cards and retain a deep roster without panic cuts."""
        target = self.ai_roster_target(promo)
        return max(650_000, target * 24_000, promo.size * 35_000)

    def ai_cash_ceiling(self, promo):
        """Maximum useful liquidity before capital is put back into the business.

        It is a soft operating ceiling, not a bankruptcy threshold: promotions
        retain several complete card-and-roster runways, then pay out the excess
        gradually through the normal monthly finance pass.
        """
        runway = self.ai_financial_runway(promo)
        return max(2_500_000, round(runway * 3.5), promo.size * 140_000)

    def ai_contract_reserve(self, promo):
        """Liquidity that remains protected when an AI company makes an offer."""
        # Signings spend cash immediately while fighter purses arrive only when a
        # show happens. Keeping most of the runway intact prevents a needy
        # company from accepting six deals in one month and then cancelling its
        # next card because the signing bonuses consumed all operating cash.
        return max(200_000, round(self.ai_financial_runway(promo) * 0.70))

    def rebalance_ai_finance_model(self):
        """One-time refinancing for saves created before the sustainable AI model."""
        refinanced = []
        for promo in [item for item in self.promotions if not getattr(item, "is_regional_feeder", False)]:
            strategy = self.promotion_strategy(promo)
            runway = self.ai_financial_runway(promo)
            if int(strategy.get("finance_model_version", 0) or 0) < 2:
                minimum_cash = max(650_000, runway)
                if promo.cash < minimum_cash:
                    refinancing = minimum_cash - promo.cash
                    promo.cash = minimum_cash
                    promo.stability = max(28, promo.stability)
                    refinanced.append((promo.name, refinancing))
                strategy["finance_model_version"] = 2
                strategy["target_reserve"] = runway
            # Version 3 corrects the old multiplicative card-revenue model.
            # Existing careers keep a healthy liquidity buffer rather than
            # losing all accumulated cash in one migration.
            if int(strategy.get("finance_model_version", 0) or 0) < 3:
                cash_ceiling = self.ai_cash_ceiling(promo)
                if promo.cash > cash_ceiling:
                    retained_buffer = max(runway * 0.30, 1_000_000)
                    correction = max(0, promo.cash - (cash_ceiling + retained_buffer))
                    if correction:
                        promo.cash -= correction
                        strategy["finance_correction_total"] = int(strategy.get("finance_correction_total", 0) or 0) + correction
                        promo.show_history = list(promo.show_history or [])
                        promo.show_history.insert(0, f"Finance normalization: ${correction:,} redirected from excess retained cash into owner distributions and infrastructure.")
                        promo.show_history = promo.show_history[:12]
                strategy["finance_model_version"] = 3
                strategy["cash_ceiling"] = cash_ceiling
            # Versioned repair for saves where viable companies were pushed to
            # single-digit stability by the old per-card margin penalties.
            if int(strategy.get("stability_model_version", 0) or 0) < 2:
                roster_size = len([fighter for fighter in promo.roster if not fighter.retired])
                operating_reserve = max(450_000, promo.size * 8_000 + roster_size * 8_000)
                commercial_strength = strategy.get("commercial_strength", promo.reputation_score)
                stability_target = max(58, min(86, round(50 + commercial_strength * 0.38)))
                if promo.cash >= operating_reserve * 0.75:
                    repair_floor = 48 if promo.cash >= operating_reserve else 42
                    promo.stability = max(promo.stability, min(stability_target - 8, repair_floor))
                strategy["stability_model_version"] = 2
        if refinanced:
            total = sum(amount for _name, amount in refinanced)
            names = ", ".join(name for name, _amount in refinanced)
            headline = f"World finance correction: {len(refinanced)} promotions refinanced under the sustainable operating model."
            self.news.insert(0, headline)
            self.record_world_story("Finance Reform", headline, f"${total:,} in board refinancing protected existing rosters at {names}.", [name for name, _amount in refinanced], importance=4)
        return refinanced

    def ai_financial_roster_target(self, promo):
        """Return the roster depth an AI company can responsibly carry today."""
        ideal = self.ai_roster_target(promo)
        weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
        open_divisions = sum(1 for gender in ("Male", "Female") for weight in weights if self.promotion_division_open(promo, gender, weight))
        survival_floor = max(20, open_divisions * 5)
        reserve = self.ai_financial_runway(promo)
        # This is deliberately a *financial* roster plan. Stability can affect
        # booking and executive confidence elsewhere, but a company sitting on
        # real cash should still build full divisions instead of behaving like
        # it is bankrupt because of one poor recent stretch.
        severe = promo.cash < 0
        pressured = promo.cash < reserve * 0.35
        caution = promo.cash < reserve * 0.70
        if severe:
            return max(survival_floor, round(ideal * 0.82))
        if pressured:
            return max(survival_floor, round(ideal * 0.90))
        if caution:
            return max(survival_floor, round(ideal * 0.96))
        return ideal

    def ai_roster_market_demand(self, promo):
        active = [member for member in promo.roster if not member.retired]
        weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
        counts = {
            (gender, weight): sum(1 for member in active if member.gender == gender and member.weight == weight)
            for gender in ("Male", "Female") for weight in weights if self.promotion_division_open(promo, gender, weight)
        }
        critical = sum(max(0, 4 - count) for count in counts.values())
        capacity = max(0, self.ai_financial_roster_target(promo) - len(active))
        return critical, capacity

    def ai_division_market_need(self, promo, fighter, count=None):
        """Value a division shortage without making every signing deterministic.

        Wealthy promotions aim to fill every configured gender/weight division.
        The first four fighters make a division bookable; the remaining gap
        creates depth, contender variety, and injury cover. The score is large
        enough to steer recruitment toward thin divisions, while a finite cap
        still lets a company take an exceptional star or prospect elsewhere.
        """
        if count is None:
            count = sum(
                1 for member in promo.roster
                if not member.retired and member.gender == fighter.gender and member.weight == fighter.weight
            )
        target = self.ai_division_target(promo, fighter.gender)
        shortage = target - count
        bookability = max(0, 4 - count)
        # The floor gets an urgent boost; normal depth is rewarded more softly.
        return max(-30, min(82, shortage * 10 + bookability * 11))

    def ai_roster_division_need(self, promo, fighter):
        count = len([member for member in promo.roster if member.gender == fighter.gender and member.weight == fighter.weight])
        return self.ai_division_market_need(promo, fighter, count=count)

    def promotion_regional_affinity(self, promo, fighter):
        """Score cultural and market fit without making recruitment exclusive."""
        identity = {
            str(getattr(fighter, "region", "")), str(getattr(fighter, "birth_region", "")),
            str(getattr(fighter, "birth_country", "")), str(getattr(fighter, "nationality", "")),
            str(getattr(fighter, "residence", "")), str(getattr(fighter, "fighting_base", "")),
            *(str(value) for value in (getattr(fighter, "cultural_connections", None) or [])),
        }
        normalized = {value.strip().lower() for value in identity if value}
        local = str(getattr(promo, "region", "")).strip().lower()
        affinity = 6 if local and any(local == value or local in value for value in normalized) else 0
        if promo.name == "Absolute Championship Akhmat":
            russian_identity = any(value in ("russia", "russian") or "russian" in value for value in normalized)
            if russian_identity:
                affinity = max(20, affinity)
        return affinity

    def ai_free_agent_value(self, promo, fighter, division_need=None):
        strategy = self.promotion_strategy(promo)
        division_need = self.ai_roster_division_need(promo, fighter) if division_need is None else division_need
        prospect = max(0, fighter.potential - fighter.overall) * 1.7
        ability = fighter.overall * 0.7
        marketability = fighter.popularity * 0.34 + fighter.star_quality * 0.18 + fighter.media_presence * 0.12
        form = fighter.momentum * 4 + fighter.morale * 0.08
        regional = self.promotion_regional_affinity(promo, fighter)
        age = 5 if 20 <= fighter.age <= 30 else -max(0, fighter.age - 34) * 2.2
        cost = fighter.purse / max(1800, promo.size * 38)
        star_fit = (fighter.popularity + fighter.star_quality * 0.55) * (strategy.get("star_focus", 50) - 50) / 260
        prospect_fit = max(0, fighter.potential - fighter.overall) * (strategy.get("prospect_focus", 50) - 50) / 70
        merit_fit = (fighter.elo_rating - 1450) * (strategy.get("merit_focus", 50) - 50) / 460
        recovery_drag = 18 if strategy.get("current_mode") == "Financial Recovery" and fighter.purse > promo.size * 310 else 0
        blue_chip = 65 if self.is_blue_chip_prospect(fighter) else 0
        waiting = min(28, getattr(fighter, "free_agent_months", 0) * 2)
        return ability + prospect + marketability + form + division_need + regional + age + star_fit + prospect_fit + merit_fit + blue_chip + waiting - cost - recovery_drag + random.uniform(-7, 7)

    def ai_contract_purse_cap(self, promo, fighter):
        """AI-only ceiling for a per-fight purse in a promotion's economy."""
        cap = 38_000 + promo.size * 2_450
        cap += fighter.popularity * 720 + fighter.star_quality * 210
        if fighter.champion or fighter.interim_champion:
            cap += 42_000
        if promo.name == "Ultimate Fighting Championship":
            cap += 52_000
        return max(28_000, round(cap / 500) * 500)

    def ai_market_purse(self, promo, fighter):
        """Current AI market value; avoids compounding every contract renewal."""
        skill_value = max(0, fighter.overall - 42) * 950
        drawing_value = fighter.popularity * 520 + fighter.star_quality * 115 + fighter.media_presence * 50
        form_value = max(0, fighter.momentum) * 1_750
        title_value = 38_000 if fighter.champion else (18_000 if fighter.interim_champion else 0)
        prospect_value = max(0, fighter.potential - fighter.overall) * 350 if fighter.age <= 28 else 0
        company_multiplier = 0.58 + promo.size / 165
        if promo.name == "Ultimate Fighting Championship":
            company_multiplier *= 1.32
        elif promo.reputation_score >= 80:
            company_multiplier *= 1.12
        value = (4_500 + skill_value + drawing_value + form_value + title_value + prospect_value) * company_multiplier
        return max(2_500, min(self.ai_contract_purse_cap(promo, fighter), round(value / 500) * 500))

    def ai_offer_terms(self, promo, fighter):
        leverage = 1 + fighter.popularity / 380 + max(0, fighter.momentum) * 0.018
        prospect_premium = max(0, fighter.potential - fighter.overall) * 0.006
        reputation_premium = promo.reputation_score / 900
        purse = self.ai_market_purse(promo, fighter) * (leverage + prospect_premium + reputation_premium)
        purse = max(2_500, min(self.ai_contract_purse_cap(promo, fighter), round(purse / 500) * 500))
        months = random.randint(12, 28) if fighter.age <= 30 else random.randint(8, 18)
        signing = round(purse * random.uniform(0.45, 1.10) * leverage / 500) * 500
        return purse, months, signing

    def ai_create_contract_offers(self):
        eligible_promos = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False) and promo.cash > self.ai_contract_reserve(promo)]
        market_cache = {}
        for promo in eligible_promos:
            active = [member for member in promo.roster if not member.retired]
            weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
            active_counts = {}
            all_counts = {}
            for member in promo.roster:
                key = (member.gender, member.weight)
                all_counts[key] = all_counts.get(key, 0) + 1
                if not member.retired:
                    active_counts[key] = active_counts.get(key, 0) + 1
            pending_offers = [fighter for fighter in self.free_agents
                              if fighter.ai_offer_company == promo.name and fighter.ai_offer_deadline_month >= self.month]
            for fighter in pending_offers:
                key = (fighter.gender, fighter.weight)
                active_counts[key] = active_counts.get(key, 0) + 1
                all_counts[key] = all_counts.get(key, 0) + 1
            critical = sum(max(0, 4 - active_counts.get((gender, weight), 0)) for gender in ("Male", "Female") for weight in weights if self.promotion_division_open(promo, gender, weight))
            capacity = max(0, self.ai_financial_roster_target(promo) - len(active) - len(pending_offers))
            market_cache[id(promo)] = {
                "demand": (critical, capacity),
                "active_counts": active_counts,
                "all_counts": all_counts,
                "roster_count": len(active) + len(pending_offers),
                "roster_cap": self.ai_roster_cap(promo),
            }
        eligible_promos.sort(key=lambda promo: (*market_cache[id(promo)]["demand"], random.random()), reverse=True)
        offers_created = 0
        free_pool = len([fighter for fighter in self.free_agents if not fighter.retired])
        # The market must be able to repair a mature world's roster shortage.
        # A fixed 18-offer ceiling left hundreds of viable free agents idle
        # while major companies stayed 30-60 fighters below their own depth
        # plans. The pulse means busy and quiet months emerge naturally rather
        # than every month producing the same number of negotiations. These are
        # only offers: cash, reserve, and fighter acceptance still decide every
        # signing.
        world_shortage = sum(market_cache[id(promo)]["demand"][1] for promo in eligible_promos)
        # A materially depleted world needs a fast, competitive correction.
        # The saved target lets a player tune the liveliness of the AI market.
        # It controls offer capacity only; recruitment eligibility, division
        # caps, cash reserves, and fighter acceptance still decide real deals.
        market_target = max(20, min(180, int(self.rules.get("ai_offer_market_target", 100))))
        flush_shortage = sum(
            market_cache[id(promo)]["demand"][1]
            for promo in eligible_promos
            if promo.cash >= self.ai_financial_runway(promo) * 1.5
        )
        # Empty, cash-rich companies should become visibly aggressive buyers.
        # The saved setting remains the normal cadence; roster shortage adds a
        # temporary catch-up pulse that disappears as the world reaches depth.
        shortage_boost = min(140, world_shortage // 18)
        liquidity_boost = min(50, flush_shortage // 45)
        market_base = market_target + shortage_boost + liquidity_boost + max(0, free_pool - 300) // 30
        market_pulse = random.triangular(0.58, 1.58, 1.08)
        offer_capacity = max(12, min(340, round(market_base * market_pulse)))

        def can_recruit(promo, fighter, blue_chip=False):
            if not self.promotion_division_open(promo, fighter.gender, fighter.weight):
                return False
            cached = market_cache[id(promo)]
            critical, capacity = cached["demand"]
            division_depth = cached["active_counts"].get((fighter.gender, fighter.weight), 0)
            division_cap = self.ai_division_target(promo, fighter.gender) + 2
            if cached["roster_count"] >= cached["roster_cap"] or division_depth >= division_cap:
                return False
            if capacity or (critical and division_depth < 4):
                return True
            # A full company pursues blue-chip talent through the atomic
            # upgrade-replacement review. Signing above plan here and waiting
            # for a later expiry created hundreds of avoidable free agents.
            return False

        value_cache = {}

        def cached_free_agent_value(promo, fighter):
            count = market_cache[id(promo)]["all_counts"].get((fighter.gender, fighter.weight), 0)
            cache_key = (id(promo), id(fighter), count)
            if cache_key in value_cache:
                return value_cache[cache_key]
            division_need = self.ai_division_market_need(promo, fighter, count=count)
            value = self.ai_free_agent_value(promo, fighter, division_need=division_need)
            value_cache[cache_key] = value
            return value

        def create_offer(promo, fighter, premium=False):
            nonlocal offers_created
            purse, months, signing = self.ai_offer_terms(promo, fighter)
            executive = getattr(promo, "executive", {}) or {}
            aggression = executive.get("aggression", 55)
            discipline = executive.get("discipline", 55)
            # Offers should feel negotiated rather than generated from one
            # identical formula. Disciplined executives cluster near value;
            # aggressive or pressured boards are willing to swing farther in
            # either direction. The fighter still sees the actual terms and
            # can decline a lowball in resolve_ai_contract_offers.
            volatility = 0.055 + max(0, aggression - discipline) / 700
            offer_swing = random.uniform(-volatility, volatility * 1.35)
            if self.promotion_strategy(promo).get("current_mode") == "Financial Recovery":
                offer_swing -= random.uniform(0.01, 0.055)
            if premium:
                offer_swing += random.uniform(0.035, 0.09)
            purse = max(fighter.purse, round(purse * (1 + offer_swing) / 500) * 500)
            months = max(6, min(32, months + random.choice((-2, -1, 0, 0, 1, 2))))
            signing = max(0, round(signing * (1 + offer_swing * 1.5 + random.uniform(-0.10, 0.16)) / 500) * 500)
            if premium:
                purse = round(purse * 1.08 / 500) * 500
                signing = round(signing * 1.12 / 500) * 500
            reserve = self.ai_contract_reserve(promo)
            runway_commitment = signing + purse
            if promo.cash < reserve + runway_commitment:
                return False
            fighter.ai_offer_company = promo.name
            fighter.ai_offer_purse = purse
            fighter.ai_offer_months = months
            fighter.ai_offer_signing_bonus = signing
            fighter.ai_offer_deadline_month = self.month + 1
            fighter.negotiation_heat = min(100, fighter.negotiation_heat + (16 if premium else 12))
            # Reserve the slot for this live offer. Without this, three offers
            # created in one pass all read the same old roster count and can
            # collectively overfill a division when accepted next month.
            cached = market_cache[id(promo)]
            key = (fighter.gender, fighter.weight)
            cached["roster_count"] += 1
            cached["active_counts"][key] = cached["active_counts"].get(key, 0) + 1
            cached["all_counts"][key] = cached["all_counts"].get(key, 0) + 1
            cached["demand"] = (
                max(0, cached["demand"][0] - (1 if cached["active_counts"][key] <= 4 else 0)),
                max(0, self.ai_financial_roster_target(promo) - cached["roster_count"]),
            )
            offers_created += 1
            return True

        # Blue chips do not disappear in the ordinary five-offer lottery.
        priority = sorted([fighter for fighter in self.free_agents if not fighter.retired and not fighter.retirement_pending and not fighter.injured and not fighter.ai_offer_company and self.is_blue_chip_prospect(fighter) and (getattr(self, "spectator_mode", False) or fighter.player_talent_window_until < self.month)], key=lambda fighter: (fighter.potential, fighter.overall, fighter.record_w - fighter.record_l, fighter.free_agent_months), reverse=True)
        for fighter in priority[:3]:
            if offers_created >= offer_capacity:
                break
            options = sorted([promo for promo in eligible_promos if can_recruit(promo, fighter, blue_chip=True)], key=lambda promo: cached_free_agent_value(promo, fighter), reverse=True)
            promo = next((item for item in options if item.cash > self.ai_contract_reserve(item)), None)
            if not promo:
                continue
            create_offer(promo, fighter, premium=True)
        for promo in eligible_promos:
            if offers_created >= offer_capacity:
                break
            critical, capacity = market_cache[id(promo)]["demand"]
            if not (critical or capacity):
                continue
            executive = getattr(promo, "executive", {}) or {}
            aggression = executive.get("aggression", 55)
            attempts = 12 if critical >= 4 or capacity >= 28 else (7 if critical >= 2 or capacity >= 10 else 3)
            reserve = self.ai_financial_runway(promo)
            cash_flush = promo.cash >= reserve * 1.5
            if cash_flush and capacity >= 20:
                attempts += min(10, max(2, capacity // 20))
            # Every board has a different appetite each month. This is a
            # market-volume decision, not a disguised ability modifier: a
            # quiet month simply means fewer negotiations begin, while a busy
            # month lets a cash-ready promotion pursue several needs at once.
            hiring_pulse = random.triangular(0.32, 2.20, 1.14)
            attempts = max(1, min(24, round(attempts * hiring_pulse)))
            if aggression >= 72 and random.random() < 0.38:
                attempts += 1
            if aggression <= 36 and random.random() < 0.30:
                attempts = max(1, attempts - 1)
            attempts = min(24, attempts)
            normal_demand_chance = 0.39 + critical * 0.10 + capacity / 90 + free_pool / 3300 + (aggression - 50) / 260
            demand_chance = max(0.16, min(0.98, normal_demand_chance * (0.74 + hiring_pulse * 0.48)))
            if random.random() > demand_chance:
                continue
            for _ in range(attempts):
                if offers_created >= offer_capacity:
                    break
                candidates = [
                    fighter for fighter in self.free_agents
                    if not fighter.retired and not fighter.retirement_pending and not fighter.injured and not fighter.ai_offer_company
                    and fighter.fatigue < 55 and fighter.age >= 18
                    and (getattr(self, "spectator_mode", False) or fighter.player_talent_window_until < self.month)
                    and can_recruit(promo, fighter)
                ]
                if not candidates:
                    break
                candidates.sort(key=lambda fighter: cached_free_agent_value(promo, fighter), reverse=True)
                # Mostly choose the best available fit. Occasionally a board
                # pursues another elite option in its short list, so a weak
                # division is prioritised rather than made exclusive.
                shortlist = candidates[:min(6, len(candidates))]
                fighter = shortlist[0] if random.random() < 0.74 else random.choice(shortlist[1:] or shortlist)
                if create_offer(promo, fighter):
                    self.news.insert(0, f"Contract market: {promo.name} offered {fighter.name} ${fighter.ai_offer_purse:,}/fight for {fighter.ai_offer_months} months. The offer is live until next month.")

    def complete_ai_free_agent_signing(self, fighter, promo, purse=None, months=None, signing_bonus=None, source="AI contract market"):
        """Move a free agent to an AI roster as one atomic, auditable action.

        Both the monthly market and a player negotiation loss use this method.
        Keeping the transfer here prevents a headline from claiming a signing
        while the same fighter object remains selectable in Free Agents.
        """
        if fighter not in self.free_agents or promo not in self.promotions or getattr(promo, "is_regional_feeder", False):
            return False, "The fighter or promotion is no longer available."
        if not self.promotion_division_open(promo, fighter.gender, fighter.weight):
            return False, f"{promo.name} does not operate a {fighter.gender} {fighter.weight} division."
        active = [member for member in promo.roster if not member.retired]
        division_depth = sum(1 for member in active if member.gender == fighter.gender and member.weight == fighter.weight)
        # Eight overlap slots cover a handful of urgent thin-division offers;
        # quality upgrades normally remove the incumbent before reaching here.
        operating_cap = min(self.ai_roster_cap(promo), self.ai_financial_roster_target(promo) + 8)
        if len(active) >= operating_cap:
            return False, f"{promo.name} has reached its roster cap."
        if division_depth >= self.ai_division_target(promo, fighter.gender) + 2:
            return False, f"{promo.name} already has its permitted depth at {fighter.gender} {fighter.weight}."
        purse = max(1_000, int(purse if purse is not None else getattr(fighter, "ai_offer_purse", 0) or fighter.purse))
        months = max(1, int(months if months is not None else getattr(fighter, "ai_offer_months", 0) or 12))
        signing_bonus = max(0, int(signing_bonus if signing_bonus is not None else getattr(fighter, "ai_offer_signing_bonus", 0) or purse))
        reserve = self.ai_contract_reserve(promo)
        if promo.cash < reserve + signing_bonus + purse:
            return False, f"{promo.name} could not fund the agreed deal."
        self.free_agents.remove(fighter)
        promo.cash -= signing_bonus
        fighter.purse = purse
        fighter.contract_months = months
        fighter.exclusive = True
        fighter.contract_type = "Exclusive"
        fighter.free_agent_months = 0
        fighter.champion = False
        fighter.interim_champion = False
        fighter.morale = min(100, fighter.morale + random.randint(3, 8))
        self.clear_ai_contract_offer(fighter)
        if fighter not in promo.roster:
            promo.roster.append(fighter)
        headline = f"{promo.name} completed a negotiated signing with {fighter.name}: ${fighter.purse:,}/fight, {fighter.contract_months} months, ${signing_bonus:,} signing bonus."
        self.news.insert(0, headline)
        self.record_world_story("Major Signing", f"{promo.name} signs {fighter.name}.", f"{source}. ${fighter.purse:,}/fight for {fighter.contract_months} months.", [promo.name], [fighter.name], 3)
        return True, headline

    def resolve_ai_contract_offers(self):
        for fighter in list(self.free_agents):
            if not fighter.ai_offer_company or fighter.ai_offer_deadline_month > self.month:
                continue
            if fighter.retired or fighter.retirement_pending:
                self.clear_ai_contract_offer(fighter)
                continue
            promo = next((item for item in self.promotions if item.name == fighter.ai_offer_company and not getattr(item, "is_regional_feeder", False)), None)
            if not promo:
                self.clear_ai_contract_offer(fighter)
                continue
            expected = max(fighter.purse * 1.15, fighter.overall * 260 + fighter.popularity * 430)
            offer_score = fighter.ai_offer_purse / max(1, expected) * 58
            offer_score += promo.reputation_score * 0.34 + promo.stability * 0.16
            offer_score += min(12, self.promotion_regional_affinity(promo, fighter) * 0.55)
            offer_score += 6 if fighter.age <= 26 and fighter.potential - fighter.overall >= 8 else 0
            offer_score += 18 if self.is_blue_chip_prospect(fighter) else 0
            offer_score += random.uniform(-12, 12)
            runway_commitment = fighter.ai_offer_signing_bonus + fighter.ai_offer_purse
            reserve = self.ai_contract_reserve(promo)
            if offer_score >= 64 and promo.cash >= reserve + runway_commitment:
                self.complete_ai_free_agent_signing(
                    fighter, promo, fighter.ai_offer_purse, fighter.ai_offer_months,
                    fighter.ai_offer_signing_bonus, source="Accepted AI contract-market offer",
                )
            else:
                rejected_company = fighter.ai_offer_company
                self.clear_ai_contract_offer(fighter)
                fighter.negotiation_heat = max(0, fighter.negotiation_heat - 5)
                fighter.morale = max(30, fighter.morale - random.randint(0, 3))
                self.news.insert(0, f"{fighter.name} rejected {rejected_company}'s terms and remains on the market.")

    def check_contract_warnings(self):
        """Warn the player before a deal lapses so renewals can be proactive.
        Fires once as each fighter ticks through the 3-month and final-month marks."""
        for fighter in self.roster:
            months = fighter.contract_months
            if fighter.retirement_pending or getattr(fighter, "comeback_contract", False) or months not in (3, 1):
                continue
            crown = " champion" if fighter.champion else ""
            when = "just 1 month" if months == 1 else "3 months"
            urgency = "URGENT" if months == 1 else "Notice"
            self.inbox.append({
                "subject": f"Contract Expiring - {fighter.name}",
                "body": (f"Your {fighter.gender} {fighter.weight}{crown} {fighter.name} has {when} left on their deal "
                         f"(${fighter.purse:,}/fight). Open Contracts to renew before they can talk to rival promotions."),
                "type": "Contract", "resolved": False,
            })
            self.news.insert(0, f"{urgency}: {fighter.name}'s contract expires in {when}.")
            if months == 1 and not getattr(self, "spectator_mode", False):
                pending = getattr(self, "pending_final_month_contract_alerts", [])
                pending.append({
                    "name": fighter.name, "weight": fighter.weight, "gender": fighter.gender,
                    "champion": bool(fighter.champion or fighter.interim_champion), "purse": fighter.purse,
                })
                self.pending_final_month_contract_alerts = pending

    def show_final_month_contract_alerts(self):
        """Show one compact, post-advance warning instead of interrupting the monthly sim loop."""
        alerts = list(getattr(self, "pending_final_month_contract_alerts", []) or [])
        self.pending_final_month_contract_alerts = []
        if not alerts:
            return
        lines = []
        for row in alerts[:12]:
            crown = " - CHAMPION" if row.get("champion") else ""
            lines.append(f"{row['name']} ({row['gender']} {row['weight']})${crown} - ${row['purse']:,}/fight")
        remainder = f"\n+ {len(alerts) - 12} more final-month deal(s)." if len(alerts) > 12 else ""
        messagebox.showwarning(
            "Final-month contracts",
            "These fighters now have one month left. Renew, release, or accept that they may leave.\n\n"
            + "\n".join(lines) + remainder + "\n\nOpen Contracts to act.",
        )

    def update_contracts(self):
        if getattr(self, "spectator_mode", False):
            return
        expired = [
            fighter for fighter in self.roster
            if fighter.contract_months <= 0
            and not getattr(fighter, "comeback_contract", False)
            and not getattr(fighter, "retirement_pending", False)
        ]
        for fighter in expired:
            if not fighter.retirement_pending and (fighter.champion or fighter.popularity > 55 or fighter.morale > 60):
                fighter.contract_months = random.randint(8, 20)
                fighter.purse = round(fighter.purse * random.uniform(1.05, 1.28))
                self.news.insert(0, f"{fighter.name} agreed a new {fighter.contract_months}-month deal with {self.player_company_name}.")
            else:
                self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(fighter, self.roster, self.belts, self.interim_belts, self.belt_history, "Left the company after contract expiry.")
                self.vacate_special_belts_held_by(fighter, "Left the company after contract expiry.")
                self.roster.remove(fighter)
                self.free_agents.append(fighter)
                self.news.insert(0, f"{fighter.name} left {self.player_company_name} after their contract expired.")
        self.belts, self.interim_belts, self.belt_history = self.ensure_company_champions(self.roster, self.belts, self.player_company_name, self.player_region, self.company_pop, player_owned=True, interim_belts=self.interim_belts, belt_history=self.belt_history)

    def auto_renew_player_contracts(self):
        """Conservatively retain core fighters before their final contract month."""
        if getattr(self, "spectator_mode", False) or not self.rules.get("auto_renew_enabled", False):
            return
        payroll = sum(fighter.purse for fighter in self.roster)
        reserve = self.finance.get("monthly_office", 12_000) * 3 + payroll
        for fighter in self.roster:
            if fighter.contract_months != 1 or fighter.retirement_pending or fighter.morale < 45:
                continue
            retain = fighter.champion or (fighter.overall >= 75 and fighter.popularity >= 35) or (fighter.age <= 29 and fighter.potential >= 88)
            if not retain:
                continue
            new_purse = round(fighter.purse * (1.05 + min(0.10, fighter.popularity / 1000)) / 500) * 500
            signing_cost = round(new_purse * 0.75)
            if self.cash - signing_cost < reserve:
                continue
            self.cash -= signing_cost
            self.record_finance_transaction(f"Auto-renewal: {fighter.name}", costs=signing_cost)
            fighter.purse = new_purse
            fighter.contract_months = 12 if fighter.age >= 36 else 18
            fighter.morale = min(100, fighter.morale + 4)
            self.news.insert(0, f"Auto-renewed {fighter.name}: {fighter.contract_months} months at ${fighter.purse:,}/fight.")

    def auto_negotiate_player_contracts(self, fighters):
        """Have talent relations negotiate independent renewal packages in one batch."""
        self.ensure_finance_defaults()
        unique = {fighter.fighter_id: fighter for fighter in fighters if fighter in self.roster}
        ordered = sorted(unique.values(), key=lambda fighter: (not fighter.champion, fighter.contract_months, -fighter.popularity))
        payroll = sum(fighter.purse for fighter in self.roster)
        reserve = self.finance.get("monthly_office", 12_000) * 3 + payroll
        talent_skill = self.staff_skill("Talent Relations")
        report = {"renewed": 0, "failed": 0, "unaffordable": 0, "cost": 0, "results": []}
        for fighter in ordered:
            if fighter.retired or fighter.retirement_pending:
                report["failed"] += 1
                report["results"].append({"name": fighter.name, "status": "failed", "reason": "retiring or already retired"})
                continue
            leverage = 1 + fighter.popularity / 140 + (0.35 if fighter.champion else 0) + max(0, fighter.momentum) * 0.05
            loyalty = max(0.76, min(0.94, 0.88 + (fighter.relationship_trust - 55) / 500 + (fighter.morale - 60) / 700))
            demand = max(fighter.purse * 1.03, fighter.purse * leverage * loyalty, 4000)
            persona = getattr(fighter, "negotiation_persona", "Professional")
            persona_premium = {
                "Hard Bargainer": 1.10, "Star Chaser": 1.08, "Security First": 0.98,
                "Loyalist": 0.96, "Competitive": 1.02,
            }.get(persona, 1.0)
            offer_purse = max(4000, round(demand * persona_premium * random.uniform(1.00, 1.10) / 500) * 500)
            months = random.randint(16, 24) if fighter.age <= 32 else random.randint(10, 18)
            if persona == "Security First":
                months = min(30, months + 6)
            signing_bonus = round(offer_purse * 0.5 / 500) * 500
            upfront = offer_purse * 2 + signing_bonus
            if self.cash - upfront < reserve:
                report["unaffordable"] += 1
                report["results"].append({"name": fighter.name, "status": "cash", "reason": f"${upfront:,} package would breach operating reserve"})
                continue
            acceptance = 0.72 + (talent_skill - 50) / 220 + (fighter.relationship_trust - 50) / 300
            acceptance += 0.08 if fighter.contract_months > 0 else -0.05
            acceptance += 0.05 if persona == "Loyalist" else -0.08 if persona == "Hard Bargainer" else 0
            acceptance -= max(0, 50 - fighter.morale) / 180
            acceptance = max(0.42, min(0.96, acceptance))
            if random.random() > acceptance:
                fighter.negotiation_heat = min(100, fighter.negotiation_heat + 8)
                report["failed"] += 1
                report["results"].append({"name": fighter.name, "status": "failed", "reason": "camp rejected the agent's best package"})
                continue
            self.cash -= upfront
            self.record_finance_transaction(f"Batch renewal: {fighter.name}", costs=upfront)
            fighter.purse = offer_purse
            fighter.contract_months = months
            fighter.exclusive = True
            fighter.contract_type = "Exclusive"
            fighter.champions_clause = bool(fighter.champion or fighter.champions_clause)
            fighter.morale = min(100, fighter.morale + 5)
            fighter.relationship_trust = min(100, fighter.relationship_trust + 3)
            fighter.negotiation_heat = max(0, fighter.negotiation_heat - 8)
            fighter.fight_history = fighter.fight_history or []
            fighter.fight_history.insert(0, f"{self.format_game_date()}: Auto-negotiated renewal - {months} months at ${offer_purse:,}/fight.")
            self.news.insert(0, f"{fighter.name} agreed a {months}-month renewal with {self.player_company_name} at ${offer_purse:,}/fight.")
            report["renewed"] += 1
            report["cost"] += upfront
            report["results"].append({"name": fighter.name, "status": "renewed", "months": months, "purse": offer_purse, "cost": upfront})
        return report

    def write_log(self):
        # The Log screen is lazy-built. Startup, spectator mode and world
        # simulation can all create an event log before its text widget exists.
        # Keep the data in self.event_log and render it when the screen opens.
        if not hasattr(self, "log_text"):
            return
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self.event_log) if self.event_log else "No news yet.")
        self.log_text.config(state="disabled")
