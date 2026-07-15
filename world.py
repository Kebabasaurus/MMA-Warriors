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


class WorldMixin:
    def record_world_story(self, story_type, headline, detail="", companies=None, fighters=None, importance=1):
        entry = {
            "month": self.month, "week": self.week, "year": 2026 + (self.month - 1) // 12,
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
            # Smaller national/regional companies must be capable of surviving
            # on modest gates. Fixed production overhead still scales with
            # company size and roster depth, but no longer prices half the
            # seeded field into a repeating buyout cycle.
            monthly_cost = round((32_000 + promo.size * 1_800 + roster_size * 650) * operating_multiplier)
            promo.cash -= monthly_cost
            # Cash does not compound forever. Profit above a healthy, size-based
            # operating reserve is spent on the sport (bigger purses, facilities,
            # expansion) and distributed to ownership, so a company's bank mean-
            # reverts to a realistic band instead of growing into the billions.
            target_reserve = max(1_500_000, int(promo.size ** 2 * 3_500))
            strategy["target_reserve"] = target_reserve
            if promo.cash > target_reserve:
                promo.cash -= int((promo.cash - target_reserve) * 0.35)
            commercial_strength = strategy.get("commercial_strength", promo.reputation_score)
            stability_target = max(58, min(86, round(50 + commercial_strength * 0.38)))
            strategy["stability_target"] = stability_target
            # Healthy companies retain distinct identities rather than all
            # accumulating at the old universal 91-92 stability ceiling.
            if self.month % 3 == 0 and promo.stability > stability_target:
                promo.stability = max(stability_target, promo.stability - 1)
            reserve = max(150_000, promo.size * 8_000)
            if promo.cash < 0:
                promo.stability = max(1, promo.stability - 4)
            elif promo.cash < reserve:
                promo.stability = max(1, promo.stability - 2)
            elif promo.cash < reserve * 2:
                promo.stability = max(1, promo.stability - 1)

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

    def fighter_available_for_date(self, fighter, month=None, week=None):
        return not fighter.injured and self.calendar_week_index(month, week) >= getattr(fighter, "available_week", 0)

    def fighter_return_label(self, fighter):
        available = getattr(fighter, "available_week", 0)
        if not available or self.calendar_week_index() >= available:
            return "Available"
        return_month = (available - 1) // 4 + 1
        return_week = (available - 1) % 4 + 1
        return f"Available Month {return_month}, Week {return_week}"

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
                ordered = sorted(fighters, key=self.rank_value, reverse=True)
                for position, fighter in enumerate(ordered, 1):
                    old = getattr(fighter, "ranking_position", 0)
                    if track and old and old != position:
                        fighter.previous_ranking_position = old
                    elif not old:
                        fighter.previous_ranking_position = position
                    fighter.ranking_position = position
                    if fighter.champion:
                        reason = "Champion"
                    elif getattr(fighter, "owed_title_shot", False):
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

    def resolve_rivalry_result(self, winner, loser, fight, method):
        """A rivalry can demand a rematch or be conclusively settled by a result."""
        heat = self.rivalry_heat_between(winner, loser)
        if not heat:
            return
        marquee = bool(fight.get("main") or fight.get("title"))
        rematch = method == "Decision" and (marquee or heat >= 55) and random.random() < 0.62
        if rematch:
            next_heat = min(100, heat + random.randint(12, 24))
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
        fighter.serious_injury_pending = fighter in getattr(self, "roster", [])
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
        fighter.retirement_pending = True
        fighter.retirement_fight_completed = False
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
        fighter.retirement_fight_completed = True
        fighter.retirement_pending = False
        fighter.retired = True
        fighter.retirement_reason = f"Retired after final fight at age {fighter.age}."
        if fighter in self.roster:
            self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(
                fighter, self.roster, self.belts, self.interim_belts, self.belt_history, "Retired after final fight."
            )
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
        fighter.available_week = max(getattr(fighter, "available_week", 0), self.calendar_week_index() + max(2, base - adjustment))

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

    def spectator_sim_month(self):
        self.spectator_advance_weeks(4, "Simulating month")

    def spectator_sim_year(self):
        self.spectator_advance_weeks(48, "Simulating year")

    def spectator_sim_to_date(self):
        target_month = max(1, int(self.spectator_target_month.get()))
        target_week = max(1, min(4, int(self.spectator_target_week.get())))
        target = (target_month, target_week)
        current = (self.month, self.week)
        if target <= current:
            messagebox.showinfo("Simulation date", "Choose a future month and week.")
            return
        weeks = (target_month - self.month) * 4 + (target_week - self.week)
        self.spectator_advance_weeks(weeks, f"Simulating to Month {target_month}, Week {target_week}")

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

    def apply_result(self, winner, loser, fight, method="Decision"):
        self.complete_fight_observation(winner.name)
        self.complete_fight_observation(loser.name)
        self.update_elo(winner, loser, fight, method)
        self.commit_career_stats(winner, method, won=True)
        self.commit_career_stats(loser, method, won=False)
        winner.record_w += 1
        loser.record_l += 1
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
        winner.last_fight_month = self.month
        loser.last_fight_month = self.month
        winner.rank_score = self.rank_value(winner)
        loser.rank_score = self.rank_value(loser)
        result_line = f"Month {self.month} Week {self.week}: {winner.name} def. {loser.name} by {method}"
        winner.fight_history = winner.fight_history or []
        loser.fight_history = loser.fight_history or []
        winner.fight_history.insert(0, result_line)
        loser.fight_history.insert(0, result_line)
        if winner.rival == loser.name or loser.rival == winner.name:
            self.resolve_rivalry_result(winner, loser, fight, method)
        winner.last_fight = result_line
        loser.last_fight = result_line
        if winner.trait == "Fan Favourite":
            winner.popularity = min(100, winner.popularity + 2)
        if loser.trait == "Fan Favourite" and random.random() < 0.35:
            loser.popularity = min(100, loser.popularity + 1)
        injury_chance = 0.07 + loser.injury_proneness / 420 + max(0, loser.fatigue - 35) / 500
        if random.random() < injury_chance:
            loser.injured = random.randint(1, 3)
        serious_chance = 0.0008 + loser.injury_proneness / 80_000 + max(0, loser.age - 33) / 12_000
        if method == "Injury Stoppage":
            serious_chance += 0.012
        if random.random() < serious_chance:
            self.apply_serious_injury(loser, "fight injury")
        winner.camp_boost = 0
        loser.camp_boost = 0
        winner.camp_weeks = 0
        loser.camp_weeks = 0
        winner.weight_cut_penalty = 0
        loser.weight_cut_penalty = 0
        winner.missed_weight = False
        loser.missed_weight = False
        if fight.get("title") and fight.get("interim"):
            winner.title_shots += 1
            self.interim_belts, self.belt_history = self.set_interim_champion(self.roster, self.interim_belts, self.belt_history, winner, f"Defeated {loser.name} by {method}.")
            self.news.insert(0, f"{winner.name} won the interim {winner.gender} {winner.weight} title after beating {loser.name}.")
        elif fight["title"]:
            key = self.belt_key(winner.gender, winner.weight)
            self.belts, self.belt_history = self.set_primary_champion(self.roster, self.belts, self.belt_history, winner, f"Defeated {loser.name} by {method}.", defense=True)
            self.interim_belts, self.belt_history = self.clear_interim_belt(self.roster, self.interim_belts, self.belt_history, key, "Unified with the primary title.")
            winner.title_shots += 1
            self.news.insert(0, f"{winner.name} is now the {winner.gender} {winner.weight} champion after beating {loser.name}.")
            # Champion's clause: winning/holding the belt auto-extends the deal.
            if getattr(winner, "champions_clause", False) and winner in self.roster:
                winner.contract_months = max(winner.contract_months, 12)
                self.news.insert(0, f"{winner.name}'s champion's clause automatically extends their contract while they hold the belt.")
            winner.owed_title_shot = False
        # Title-shot clause: a win earns a guaranteed future title shot.
        if getattr(winner, "title_shot_clause", False) and not fight.get("title") and winner in self.roster and not winner.champion:
            if not getattr(winner, "owed_title_shot", False):
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
        self.commit_career_stats(a)
        self.commit_career_stats(b)
        a.record_d = getattr(a, "record_d", 0) + 1
        b.record_d = getattr(b, "record_d", 0) + 1
        a.career_win_streak = 0
        b.career_win_streak = 0
        a.last_fight_month = self.month
        b.last_fight_month = self.month
        a.momentum = max(-5, min(5, a.momentum))
        b.momentum = max(-5, min(5, b.momentum))
        a.morale = min(100, a.morale + random.randint(0, 3))
        b.morale = min(100, b.morale + random.randint(0, 3))
        a.fatigue = min(100, a.fatigue + random.randint(18, 34))
        b.fatigue = min(100, b.fatigue + random.randint(18, 34))
        self.set_post_fight_recovery(a, "Decision", lost=False)
        self.set_post_fight_recovery(b, "Decision", lost=False)
        a.rank_score = self.rank_value(a)
        b.rank_score = self.rank_value(b)
        result_line = f"Month {self.month} Week {self.week}: {a.name} and {b.name} fought to a draw"
        for fighter in (a, b):
            fighter.fight_history = fighter.fight_history or []
            fighter.fight_history.insert(0, result_line)
            fighter.last_fight = result_line
        heat = self.rivalry_heat_between(a, b)
        if heat:
            next_heat = min(100, heat + random.randint(16, 28))
            for fighter in (a, b):
                fighter.rivalry_heat = next_heat
                fighter.rivalry_rematch_due = True
                fighter.rivalry_last_month = self.month
                fighter.rivalry_history = (fighter.rivalry_history or [])[-39:] + [f"Month {self.month}: Draw with {b.name if fighter is a else a.name}; rematch demand intensifies. Heat now {next_heat}/100."]
        if fight.get("title"):
            self.news.insert(0, f"The {a.gender} {a.weight} title fight between {a.name} and {b.name} ended in a draw; title status remains unchanged.")
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

    def calculate_revenue(self, total_hype, venue=None):
        venue_factor = {
            "Local Gym": 1100,
            "Regional Arena": 1850,
            "Casino Ballroom": 2400,
            "National Sports Hall": 3300,
        }[venue or self.venue.get()]
        sponsor = 15000 + self.company_pop * 700
        return round(total_hype * venue_factor + sponsor)

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

    def calculate_event_finance(self, total_hype, fighter_pay, event, results, excitement_score=50, build_score=50, regional_pull=1.0):
        venue_capacity = {
            "Local Gym": 900,
            "Regional Arena": 4200,
            "Casino Ballroom": 7500,
            "National Sports Hall": 14500,
        }.get(event["venue"], 4200)
        media_heat = max(0.58, min(1.28, 0.64 + build_score / 165 + excitement_score / 260))
        attendance_demand = total_hype * (24 + self.company_pop * 0.82 + self.company_stability * 0.22) / 14
        atmosphere = self.event_atmosphere(event, results, excitement_score)
        attendance = min(venue_capacity, max(120, round(attendance_demand * regional_pull * media_heat * atmosphere["attendance_factor"])))
        sellout_pressure = attendance / max(1, venue_capacity)
        ticket_price = round(self.finance["ticket_price"] * (0.9 + regional_pull * 0.12 + sellout_pressure * 0.18))
        ticket_revenue = round(attendance * ticket_price * self.engine_settings.get("gate_multiplier", 1.0))
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
        rights_reach = rights.get("reach", 0) if contracted_events != 0 else 0
        media_reach = best_broadcaster["reach"] + rights_reach + championship_value // 2 + commentary_quality // 8
        if not best_broadcaster["reach"] and not rights_reach:
            media_reach = max(2, championship_value // 4)
        broadcast_income = round(total_hype * media_reach * self.finance["broadcast_cut"] * (38 + build_score * 0.68 + championship_value * 0.7) * media_heat * (1 + commentary_quality / 650))
        sponsorship = round((self.finance["sponsor_income"] + sum(deal["fee"] for deal in sponsor_deals) + round(self.company_pop * total_hype * (6 + regional_pull * 3 + build_score / 16))) * atmosphere["sponsor_factor"])
        broadcast_income += rights.get("fee", 0) if contracted_events != 0 else 0
        if contracted_events > 0:
            rights["events_remaining"] -= 1
        merchandise = round(ticket_revenue * self.finance["merch_rate"] * (1 + self.company_pop / 130) * (0.85 + excitement_score / 110) * atmosphere["merch_factor"])
        commentator_pay = sum(c["salary"] for c in commentators)
        venue_ops = round(venue_capacity * (5 + self.company_pop / 16))
        bout_count = max(len(event["fights"]), len(results))
        production = self.finance["production_base"] + bout_count * 5200 + best_broadcaster["fee"] + commentator_pay + venue_ops
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
            "bonuses": bonuses,
            "production": production,
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
            for fighter in self.roster:
                fighter.morale = max(10, fighter.morale - 2)

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
                should_stop = bool(job["stop_condition"] and job["stop_condition"]())
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
            callback = job.get("on_complete")
            self._complete_advance_cleanup()
            if not getattr(self, "spectator_mode", False):
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

    def process_world_week(self):
        for _label, task in self.world_week_steps():
            task()

    def process_pending_rebookings(self):
        pending = list(getattr(self, "pending_rebookings", []))
        for entry in pending:
            if entry.get("target_month", self.month + 1) > self.month + 2:
                continue
            names = entry.get("fighters", [])
            fighters = [self.get_fighter(name) for name in names]
            if len(fighters) != 2 or any(fighter is None or fighter.injured for fighter in fighters):
                continue
            candidates = sorted(self.scheduled_events, key=lambda event: (event.get("month", 1), event.get("week", 1)))
            target = next((event for event in candidates if event.get("month", 0) >= self.month and all(self.fighter_available_for_date(fighter, event.get("month", self.month), event.get("week", 1)) for fighter in fighters)), None)
            fight = {"fighters": names, "title": False, "interim": False, "main": entry.get("main", False), "tier": entry.get("tier", "Main Card")}
            if target:
                target["fights"].append(fight)
                note = f"Rebooked {names[0]} vs {names[1]} onto {target['name']} ({entry.get('tier', 'Main Card')})."
            else:
                month = max(self.month + 1, entry.get("target_month", self.month + 1))
                target = {"name": f"{self.player_company_name} Rebooked Bouts", "venue": "Regional Arena", "region": self.player_region, "city": REGION_CITIES.get(self.player_region, ["Las Vegas"])[0], "month": month, "week": 4, "fights": [fight]}
                self.scheduled_events.append(target)
                note = f"Created {target['name']} for {names[0]} vs {names[1]} in Month {month}, Week 4."
            self.assign_event_camps(target)
            self.pending_rebookings.remove(entry)
            self.inbox.append({"subject": "Bout Rebooked", "body": note, "type": "Roster", "resolved": False})
            self.news.insert(0, note)

    def academy_defaults(self):
        return {
            "schema_version": 2,
            "owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [],
            "weekly_cost": 0, "auto_train": True, "network_weeks": 0, "network_active": False,
            "network_region": "", "network_scout": "", "network_scout_skill": 0,
            "showcase_weeks": 2, "auto_showcases": True, "last_scout_report": "",
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
        academy["schema_version"] = 2
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
        potential_roll = max(random.randint(60, 92) for _ in range(quality_rolls))
        quality_shift = round((scout_score - 50) / 14 + (academy_reputation - 20) / 35)
        target_rating = max(30, min(60, fighter.overall + quality_shift + random.randint(-2, 2)))
        stat_shift = target_rating - fighter.overall
        potential_bonus = round((scout_score - 50) / 30 + (academy_reputation - 20) / 60)
        potential = max(target_rating + 8, min(97, potential_roll + potential_bonus))
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
        return (
            f"{prospect['name']} | {prospect['age']} | {prospect['region']} | {prospect['amateur_weight']} | "
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

    def train_academy_prospect(self, prospect, academy):
        self.repair_academy_prospect(prospect)
        prospect["weeks"] = prospect.get("weeks", 0) + 1
        if prospect.get("injured", 0):
            prospect["injured"] = max(0, prospect.get("injured", 0) - 1)
            return
        intensity = prospect.get("training_intensity", "Standard")
        recovery = {"Light": (9, 14), "Standard": (7, 12), "Intensive": (5, 9), "Recovery": (12, 18)}.get(intensity, (7, 12))
        prospect["fatigue"] = max(0, prospect.get("fatigue", 0) - random.randint(*recovery))
        if not academy.get("auto_train", True):
            return
        if intensity == "Recovery" or prospect.get("fatigue", 0) >= 65:
            prospect["confidence"] = min(99, prospect.get("confidence", 55) + (1 if random.random() < 0.28 else 0))
            return
        fields = self.academy_training_fields(prospect.get("plan", "Automatic"), prospect)
        philosophy = self.academy_philosophy_fields(academy)
        facility = academy.get("level", 1) * 5 + self.staff_skill("Trainer") * 0.25 + academy.get("reputation", 10) * 0.08
        potential_gap = max(0, prospect.get("potential", 70) - prospect.get("rating", 40))
        mentality = (prospect.get("dedication", 55) + prospect.get("coachability", 55)) / 200
        intensity_factor = {"Light": 0.72, "Standard": 1.0, "Intensive": 1.28}.get(intensity, 1.0)
        fatigue_drag = max(0, prospect.get("fatigue", 0) - 35) / 180
        growth_chance = min(0.48, (0.055 + facility / 440 + potential_gap / 380) * mentality * intensity_factor - fatigue_drag)
        if random.random() < max(0.025, growth_chance):
            weighted_fields = list(fields) + [field for field in philosophy if field in fields]
            field = random.choice(weighted_fields)
            prospect[field] = min(prospect.get("potential", 99), prospect.get(field, prospect.get("rating", 40)) + 1)
            prospect["development"] = prospect.get("development", 0) + 1
            prospect["plateau_weeks"] = 0
            prospect["training_log"] = ([f"M{self.month} W{self.week}: {field.replace('_', ' ').title()} improved under {prospect.get('plan', 'Automatic')} training."] + prospect.get("training_log", []))[:30]
        else:
            prospect["plateau_weeks"] = prospect.get("plateau_weeks", 0) + 1
        fatigue_gain = {"Light": 1, "Standard": 2, "Intensive": 4}.get(intensity, 2)
        prospect["fatigue"] = min(100, prospect.get("fatigue", 0) + fatigue_gain)
        injury_risk = max(0.002, 0.004 + (0.012 if intensity == "Intensive" else 0) + max(0, prospect["fatigue"] - 75) / 1700)
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
        fighter.fight_history = [f"Amateur: {line}" for line in prospect.get("amateur_history", [])] + ["Promoted from the Fighting Academy."]
        fighter.contract_months = 24
        fighter.feeder_origin = f"{self.player_company_name} Fighting Academy"
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
        if prospect.get("age", 0) < 18:
            return False, "A prospect must be 18 to turn professional.", None
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
            detail["result"] = line; detail["lines"] += ["", f"Result: {line}"]
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
        detail["result"] = line; detail["lines"] += ["", f"Result: {line}"]
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
                 and absolute_week - item.get("last_amateur_week", -99) >= 2]
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

    def run_academy_showcase_card(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        results, fight_logs = [], []
        for a, b, label in self.choose_academy_showcase_card(academy):
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
        academy["showcase_weeks"] = max(0, academy.get("showcase_weeks", 2) - 1)
        if academy["showcase_weeks"] > 0:
            return None
        results = self.run_academy_showcase_card(academy)
        academy["showcase_weeks"] = 2 if results else 1
        academy["last_scout_report"] = f"Bi-weekly academy showcase: {len(results)} bout(s). {results[0] if results else 'Delayed: no healthy, rested prospect is eligible this week.'}"
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

    def process_scouting_reports(self):
        for name, report in list(getattr(self, "scouting_reports", {}).items()):
            if report.get("status") != "In progress":
                continue
            report["weeks_remaining"] = max(0, report.get("weeks_remaining", 0) - 1)
            if report["weeks_remaining"] == 0:
                report["status"] = "Complete"
                report["reveal"] = 100 if report.get("kind") == "full" else report.get("reveal", 50)
                detail = "; ".join(report.get("notes", [])) or "Initial read complete; more detail requires a fuller report."
                self.inbox.append({"subject": f"Scouting Report Complete - {name}", "body": f"Your {report.get('kind', 'basic')} report by {report.get('scout', 'staff')} is complete ({report.get('reveal', 0)}% confidence). {detail}", "type": "Scouting", "resolved": False})

    def complete_fight_observation(self, name):
        report = getattr(self, "scouting_reports", {}).get(name)
        if report and report.get("status") == "In progress":
            report.update({"status": "Complete", "weeks_remaining": 0, "reveal": 100, "observed_fight": True})
            self.inbox.append({"subject": f"Fight Observation Complete - {name}", "body": f"{name} competed while under observation. The live performance completed the full scouting report.", "type": "Scouting", "resolved": False})

    def record_finance_transaction(self, label, revenue=0, costs=0):
        self.ensure_finance_defaults()
        self.finance["week_transactions"].append({
            "month": self.month, "week": self.week, "label": label,
            "revenue": max(0, round(revenue)), "costs": max(0, round(costs)),
        })
        self.finance["week_transactions"] = self.finance["week_transactions"][-240:]

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
            old_camp = fighter.camp
            fighter.camp = self.suggest_camp_for_fighter(fighter, self.player_region)
            fighter.camp_quality = self.gym_quality(fighter.camp)
            self.news.insert(0, f"Week {self.week}: {fighter.name} moved camps from {old_camp} to {fighter.camp}.")

    def suggest_camp_for_fighter(self, fighter, promotion_region):
        gyms = getattr(self, "gyms", []) or self.seed_gyms()
        def score(gym):
            local = 16 if gym.region == fighter.region else 8 if gym.region == promotion_region else 0
            style = self.gym_specialty_bonus(fighter, gym)
            crowd = max(0, gym.member_count - gym.capacity) * 0.08 if gym.capacity < 500 else 0
            affordability = -max(0, gym.monthly_fee - max(1200, fighter.purse // 8)) / 700
            return gym.quality * 0.62 + gym.reputation * 0.22 + gym.morale * 0.12 + style + local + affordability - crowd + random.uniform(-4, 4)
        return max(gyms, key=score).name if gyms else "Independent"

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
        if roll < 0.28:
            old = gym.quality
            gym.facilities = min(99, gym.facilities + random.randint(1, 4))
            gym.quality = min(99, gym.quality + random.choice([0, 1, 1, 2]))
            self.news.insert(0, f"Week {self.week}: {gym.name} upgraded its facilities; gym quality moved from {old} to {gym.quality}.")
        elif roll < 0.52:
            gym.reputation = min(99, gym.reputation + random.randint(1, 3))
            gym.scouting = min(99, gym.scouting + random.randint(1, 3))
            self.news.insert(0, f"Week {self.week}: {gym.name} drew attention at regional shows and improved its scouting network.")
        elif roll < 0.74:
            gym.morale = max(25, gym.morale - random.randint(2, 7))
            self.news.insert(0, f"Week {self.week}: Tension inside {gym.name} hurt the room's morale.")
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
        rights = self.finance["media_rights"]
        if rights.get("months", 0) > 0:
            rights["months"] -= 1
            if rights["months"] <= 0:
                self.finance["ledger"].insert(0, f"Month {self.month}: Media rights package expired: {rights['name']}.")
                self.finance["media_rights"] = {"name": "No rights package", "months": 0, "fee": 0, "reach": 0}

    def world_month_steps(self, player_ran_show):
        steps = [("Player roster development", lambda: self.age_and_develop_fighters(self.roster, player_roster=True))]
        for promo in list(self.promotions):
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
        for sport, world in list(worlds.items()):
            steps.append((
                f"{sport} circuit",
                lambda sport=sport, world=world: self.process_combat_sport_world(sport, world),
            ))
        steps.extend([
            ("Non-exclusive activity", self.simulate_nonexclusive_outside_fights),
            ("Free-agent negotiations", self.advance_free_agent_market),
            ("Monthly transfer market", self.market_churn),
            ("AI operating costs", self.apply_ai_operating_costs),
            ("Promotion survival", self.process_promotion_failures),
            ("Executive reviews", self.review_ai_executives),
            ("World replenishment", self.ensure_world_fighter_target),
            ("World balance metrics", self.update_world_metric_interactions),
            ("Contract warnings", self.check_contract_warnings),
            ("Contract promises", self.review_contract_promises),
            ("Player renewals", self.auto_renew_player_contracts),
            ("Player contracts", self.update_contracts),
            ("AI contracts", self.update_ai_contracts),
            ("Retirement reviews", self.process_retirements),
            ("Promotion rankings", self.refresh_promotion_rankings),
        ])

        def finish_month():
            if not player_ran_show and not getattr(self, "spectator_mode", False):
                self.company_pop = max(1, self.company_pop - 1)
                self.news.insert(0, f"{self.player_company_name} stayed quiet this month; fans drifted toward other shows.")
            self.news = self.news[:120]

        steps.append(("Finalising the month", finish_month))
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
        distressed = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False) and (promo.cash < 0 or promo.stability < 28)]
        healthy = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False) and promo.cash > promo.size * 16_000 and promo.stability >= 55]
        sport_activity = sum(len(world.get("event_history", [])) for world in getattr(self, "combat_sport_worlds", {}).values())
        self.world_balance_metrics = {
            "month": self.month,
            "active_fighters": len(active),
            "free_agents": len(free),
            "distressed_promotions": len(distressed),
            "healthy_promotions": len(healthy),
            "combat_sport_activity": sport_activity,
        }
        if len(free) < 70 and random.random() < 0.35:
            region = random.choice(REGIONS)
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
        crowded = max(0, (gym.member_count - gym.capacity) / max(1, gym.capacity)) if gym and gym.capacity < 500 else 0
        base_boost = round(
            weeks * (quality + specialty + focus_bonus + focus_fit * 2 + intensity_bonus) / 112
            * (0.55 + fighter.professionalism / 100 * 0.3 + fighter.motivation / 100 * 0.25)
            / (2.8 + crowded)
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
        focus = {
            "Boxing": ("striking", "power", "cardio", "fight_iq"),
            "Kickboxing": ("striking", "power", "cardio", "toughness"),
            "Muay Thai": ("striking", "power", "toughness", "cardio"),
            "Wrestling": ("wrestling", "ground_control", "cardio", "fight_iq"),
            "Brazilian Jiu-Jitsu": ("grappling", "submissions", "ground_control", "fight_iq"),
        }.get(sport, ("striking", "cardio", "fight_iq"))
        growth_chance = 0.18 + (0.10 if won else 0) + (0.06 if finished else 0) + max(0, fighter.potential - fighter.overall) / 240
        if fighter.age > fighter.prime_end:
            growth_chance *= 0.45
        if random.random() < growth_chance:
            field = random.choice(focus)
            setattr(fighter, field, max(1, min(99, getattr(fighter, field, 50) + 1)))
            if field in ("striking", "wrestling", "grappling"):
                self.adjust_detailed_skill(fighter, 1)

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
                state["title_history"][title_key] = state["title_history"][title_key][:80]
                state["champion"] = winner.name
            round_note = f" R{sim.get('round')}" if method not in ("Decision", "Majority Decision", "Points", "Referee Criteria") else ""
            result_line = f"Month {self.month}: {winner.name} def. {loser.name} by {method}{round_note} in {sport} ({sim.get('score', '-')})"
        sim.setdefault("log", []).append(f"Result: {result_line}")
        retired_after = []
        for fighter in (a, b):
            fighter.multi_sport_records = fighter.multi_sport_records or {}
            fighter.multi_sport_records[sport] = f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"
            fighter.fight_history = fighter.fight_history or []
            fighter.fight_history.insert(0, result_line)
            fighter.last_fight = result_line
            fighter.last_fight_month = self.month
            condition = sim.get("condition", {}).get(fighter.name, {})
            exertion = max(0, 100 - condition.get("stamina", 70))
            damage_load = condition.get("damage", 0) + condition.get("body", 0) * 0.6 + condition.get("leg", 0) * 0.7
            lost = bool(loser is fighter)
            fatigue_gain = 10 + round(exertion * 0.34 + damage_load * 0.22) + (4 if lost else 0) + random.randint(0, 7)
            fighter.fatigue = min(100, fighter.fatigue + fatigue_gain)
            recovery_method = "TKO" if method == "KO/TKO" else method
            self.set_post_fight_recovery(fighter, recovery_method, lost=lost)
            injury_chance = 0.018 + fighter.injury_proneness / 1700 + damage_load / 520 + condition.get("cuts", 0) / 380
            if lost and method in ("KO", "KO/TKO", "Technical Fall", "Pin", "Submission"):
                injury_chance += 0.018
            if random.random() < min(0.24, injury_chance):
                fighter.injured = max(fighter.injured, random.randint(1, 3))
            serious_chance = 0.00045 + fighter.injury_proneness / 110_000 + max(0, fighter.age - 34) / 20_000
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
        return {"a": a.name, "b": b.name, "a_record": a_record_before, "b_record": b_record_before, "winner": winner.name if winner else "Draw", "method": method, "round": sim.get("round"), "score": sim.get("score", "-"), "weight": self.combat_sport_competition_class(sport, a), "title_key": title_key if effective_title else "", "title": effective_title, "scheduled_title": title, "result": result_line, "log": sim.get("log", []), "condition": sim.get("condition", {}), "start_stamina": sim.get("start_stamina", {}), "readiness": sim.get("readiness", {})}

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
            [fighter for fighter in available if fighter.age <= 27 or fighter.potential >= fighter.overall + 7],
            sorted(available, key=lambda fighter: (self.combat_sport_inactivity_months(fighter), fighter.fatigue), reverse=True)[:max(8, len(available) // 3)],
        ]
        for band in bands:
            band = [fighter for fighter in band if fighter.name not in used]
            random.shuffle(band)
            card_pool.extend(band[:max(2, target_bouts // 2)])
        card_pool = sorted(
            dict((fighter.name, fighter) for fighter in card_pool if fighter.name not in used).values(),
            key=lambda fighter: (fighter.retirement_pending, self.combat_sport_inactivity_months(fighter) if card_strategy == "Deep Roster" else 0, fighter.age <= 27, fighter.potential - fighter.overall),
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

    def run_combat_sport_card(self, sport, world, employer, player_owned=False, target_bouts=6):
        division = getattr(self, "player_combat_divisions", {}).get(sport) if player_owned else None
        if player_owned and division:
            target_bouts = {"Prospect Builder": 6, "Star Showcase": 4, "Title Focus": 5}.get(division.get("strategy", "Balanced"), target_bouts)
        state = self.ensure_combat_sport_circuit_state(sport, world, employer, player_owned)
        bouts = self.build_combat_sport_card(sport, world, employer, player_owned=player_owned, target_bouts=target_bouts)
        if not bouts:
            return None
        event_no = world.get("events", 0) + 1
        world["events"] = event_no
        promotion = self.player_company_name if player_owned else world.get("promotion", employer)
        results = [self.apply_combat_sport_result(
            sport, world, bout["a"], bout["b"], title=bout.get("title", False),
            player_owned=player_owned, title_key=bout.get("title_key", ""), employer=employer,
        ) for bout in bouts]
        title_result = next((item for item in results if item.get("title")), None)
        finishes = sum(1 for item in results if item.get("method") not in ("Decision", "Points", "Draw"))
        headline = f"Month {self.month}: {promotion} ran a {sport} card headlined by {results[0]['result']}."
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
            "a_record": item.get("a_record", ""),
            "b_record": item.get("b_record", ""),
            "a_start_gas": item.get("start_stamina", {}).get(item["a"], 100),
            "b_start_gas": item.get("start_stamina", {}).get(item["b"], 100),
            "a_condition": item.get("condition", {}).get(item["a"], {}),
            "b_condition": item.get("condition", {}).get(item["b"], {}),
            "readiness": item.get("readiness", {}),
            "weight": item.get("weight", next((fighter.weight for fighter in world.get("roster", []) if fighter.name == item["a"]), "")),
            "method": item.get("method", ""),
            "score": item.get("score", "-"),
            "result": item.get("result", ""),
            "lines": item.get("log", []),
        } for item in results]
        card = {"month": self.month, "week": self.week, "sport": sport, "promotion": promotion, "event": event_no, "event_name": f"{promotion} {sport} Card {event_no}", "results": results, "fight_logs": fight_logs, "headline": headline, "recap": recap, "strategy": strategy, "bouts": [{"a": bout["a"].name, "b": bout["b"].name, "title": bout.get("title", False), "title_key": bout.get("title_key", ""), "reason": bout.get("booking_reason", "Sport matchmaking")} for bout in bouts]}
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
        self.result_records.insert(0, {
            "date": f"Month {self.month} Week {self.week}",
            "company": promotion,
            "event": f"{sport} Card {event_no}",
            "summary": recap,
            "fights": len(results),
            "gate": f"${card.get('finance', {}).get('revenue', 0):,}",
            "profit": f"${card.get('finance', {}).get('profit', 0):,}",
            "log": [headline, recap, ""] + [item["result"] for item in results],
            "fight_logs": fight_logs,
            "finance": card.get("finance", {"ticket_revenue": 0, "total_revenue": 0, "total_expense": 0, "profit": 0}),
        })
        self.result_records = self.result_records[:500]
        return card

    def develop_combat_sport_roster(self, sport, roster):
        focus = {
            "Boxing": ("striking", "power", "chin", "cardio"),
            "Kickboxing": ("striking", "power", "toughness", "cardio"),
            "Muay Thai": ("striking", "power", "toughness", "cardio"),
            "Wrestling": ("wrestling", "ground_control", "cardio", "fight_iq"),
            "Brazilian Jiu-Jitsu": ("grappling", "submissions", "ground_control", "fight_iq"),
        }.get(sport, ("striking", "cardio", "fight_iq"))
        year = str(2026 + (self.month - 1) // 12)
        for fighter in roster:
            if fighter.injured:
                fighter.injured -= 1
            fighter.fatigue = max(0, fighter.fatigue - random.randint(8, 18))
            if fighter.age <= fighter.prime_end and fighter.overall < fighter.potential and random.random() < 0.18:
                field = random.choice(focus)
                setattr(fighter, field, max(1, min(99, getattr(fighter, field, 50) + 1)))
                if field in ("striking", "wrestling", "grappling"):
                    self.adjust_detailed_skill(fighter, 1)
            if fighter.age > fighter.prime_end + 2 and random.random() < 0.08:
                field = random.choice(focus)
                setattr(fighter, field, max(1, min(99, getattr(fighter, field, 50) - 1)))
            fighter.annual_overalls = fighter.annual_overalls or {}
            fighter.annual_overalls[year] = max(fighter.annual_overalls.get(year, 0), fighter.overall)
            fighter.rank_score = self.rank_value(fighter)

    def review_combat_sport_retirements(self, sport, world):
        """Stage retirement reviews while guaranteeing a final booked contest."""
        marked = 0
        for fighter in self.combat_sport_roster(sport):
            if fighter.retirement_pending or fighter.age < 38:
                continue
            annual_review_month = sum(ord(char) for char in fighter.name) % 12 + 1
            calendar_month = (self.month - 1) % 12 + 1
            if fighter.age < 50 and calendar_month != annual_review_month:
                continue
            losses = fighter.record_l / max(1, fighter.record_w + fighter.record_l + fighter.record_d)
            age_pressure = max(0, fighter.age - fighter.prime_end) * 0.07
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

    def generate_combat_sport_prospect(self, sport, world):
        promotion = world.get("promotion", "")
        target_skill = {
            "Boxing": ("striking", "power"),
            "Kickboxing": ("striking", "cardio"),
            "Muay Thai": ("striking", "toughness"),
            "Wrestling": ("wrestling", "ground_control"),
            "Brazilian Jiu-Jitsu": ("grappling", "submissions"),
        }.get(sport, ("striking", "cardio"))
        fighter = self.create_generated_fighter(3, 18, 38, 62, region=random.choice(REGIONS))
        reserved = self.active_fighter_names()
        for sport_world in getattr(self, "combat_sport_worlds", {}).values():
            reserved.update(candidate.name for candidate in sport_world.get("roster", []))
        self.avoid_name_collision(fighter, reserved)
        fighter.age = random.randint(18, 23)
        fighter.record_w = random.randint(0, 5)
        fighter.record_l = random.randint(0, 2)
        fighter.record_d = 0
        fighter.primary_discipline = sport
        fighter.sport_employer = promotion
        fighter.contract_type = f"{sport} Development Deal"
        fighter.exclusive = True
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
            weights = [1.0 / (1 + counts.get(label, 0)) for label in labels]
            division = random.choices(labels, weights=weights, k=1)[0]
            self.assign_combat_sport_weight(sport, fighter, division, reset_walk_weight=True)
        for field in target_skill:
            setattr(fighter, field, min(92, max(getattr(fighter, field, 45), fighter.overall + random.randint(5, 14))))
        self.generate_detailed_skills(fighter)
        self.sync_broad_skills_from_details(fighter)
        fighter.potential = max(fighter.overall + random.randint(6, 15), fighter.potential)
        fighter.potential = min(97, fighter.potential)
        fighter.multi_sport_records = {sport: fighter.record}
        return fighter

    def replenish_combat_sport_world(self, sport, world):
        promotion = world.get("promotion", "")
        active = self.combat_sport_roster(sport, promotion)
        target = max(36, int(world.get("starting_roster_size", len(active) or 50)))
        if len(active) >= max(30, round(target * 0.88)):
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
        crossover_pressure = 0.003 + (0.002 if world.get("cash", 0) < 500_000 else 0)
        if random.random() < crossover_pressure:
            champions = set(world.get("titles", {}).values())
            candidates = [
                fighter for fighter in self.combat_sport_ranked(sport, promotion)[4:28]
                if fighter.age <= 34 and fighter.fatigue < 45 and not fighter.retirement_pending
                and fighter.name not in champions and fighter.overall >= 58
            ]
            if candidates:
                fighter = random.choices(candidates, weights=[max(1, candidate.popularity + candidate.potential - candidate.overall) for candidate in candidates], k=1)[0]
                fighter.sport_employer = ""
                fighter.crossover_history = (fighter.crossover_history or [])[-9:] + [f"Month {self.month}: Left {world['promotion']} to pursue MMA."]
                fighter.multi_sport_records = fighter.multi_sport_records or {}
                fighter.multi_sport_records[sport] = fighter.record
                fighter.multi_sport_records["MMA"] = "0-0-0"
                fighter.record_w = fighter.record_l = fighter.record_d = 0
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
        for sport, world in worlds.items():
            self.process_combat_sport_world(sport, world)
        self.combat_sport_worlds = worlds

    def open_player_combat_division(self, sport):
        divisions = getattr(self, "player_combat_divisions", {})
        if sport not in divisions:
            startup_cost = 120000
            if self.cash < startup_cost:
                return False, f"Need ${startup_cost:,} to establish a {sport} division."
            self.cash -= startup_cost
            world = getattr(self, "combat_sport_worlds", {}).get(sport, {})
            candidates = sorted(world.get("roster", []), key=lambda fighter: (fighter.overall, fighter.potential), reverse=True)
            signed = candidates[12:24]
            for fighter in signed:
                fighter.sport_employer = self.player_company_name
            divisions[sport] = {
                "sport": sport, "roster": [fighter.name for fighter in signed], "rankings": [fighter.name for fighter in signed[:10]],
                "champion": "", "titles": {}, "title_history": {}, "rankings_by_division": {}, "titles_initialized": True,
                "events": [], "records": {}, "record_book": {}, "season_stats": {}, "awards": [], "hall_of_fame": [], "finance_history": [],
                "budget": startup_cost, "active": True, "strategy": "Balanced", "revenue_total": 0, "cost_total": startup_cost,
                "profit_total": -startup_cost, "last_card_summary": "No player card yet.", "title_name": f"{self.player_company_name} {sport} Championships",
                "reputation": max(20, self.company_pop), "stability": 60,
            }
            self.player_combat_divisions = divisions
            self.news.insert(0, f"{self.player_company_name} launched a {sport} division with {len(signed)} signed athletes and a shared-brand startup investment of ${startup_cost:,}.")
        return True, divisions[sport]

    def review_contract_promises(self):
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
            months_inactive = max(0, self.month - getattr(fighter, "last_fight_month", 0))
            if months_inactive >= 10 and fighter.popularity > 18 and random.random() < min(0.55, 0.12 + months_inactive / 55):
                fighter.popularity -= 1
            before = fighter.overall
            development = self.monthly_development_score(fighter)
            resurgence = self.veteran_resurgence_chance(fighter)
            development_tail = 2 if fighter.career_archetype == "Durable Career" else 0
            normal_growth_open = fighter.age <= fighter.prime_end + development_tail
            can_improve = (fighter.overall < fighter.potential and normal_growth_open) or (resurgence > 0 and random.random() < resurgence)
            if development > random.randint(70, 135) and can_improve:
                growth = 2 if development > 150 or fighter.trait == "Gym Rat" else 1
                self.adjust_random_skill(fighter, growth)
                self.adjust_detailed_skill(fighter, growth)
            decline_risk = self.monthly_decline_score(fighter)
            if decline_risk > random.randint(65, 130):
                loss = -2 if decline_risk > 155 else -1
                self.adjust_random_skill(fighter, loss)
                self.adjust_detailed_skill(fighter, loss)
            fighter.annual_overalls = fighter.annual_overalls or {}
            fighter.annual_overalls[year] = max(fighter.annual_overalls.get(year, 0), fighter.overall)
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
                decline_chance = min(0.85, 0.32 + over * 0.12 - self.veteran_resurgence_chance(fighter) * 2)
                if random.random() < decline_chance:
                    self.adjust_random_skill(fighter, -1)
                    self.adjust_detailed_skill(fighter, -1)
            elif fighter.age < fighter.prime_start and fighter.overall < fighter.potential:
                if random.random() < 0.55:
                    self.adjust_random_skill(fighter, 1)
                    self.adjust_detailed_skill(fighter, 1)
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
                if fighter.age > fighter.prime_end + 3 and random.random() < 0.18:
                    self.adjust_random_skill(fighter, -1)
                    self.adjust_detailed_skill(fighter, -1)
                fighter.annual_overalls = fighter.annual_overalls or {}
                fighter.annual_overalls[str(self.current_year())] = max(fighter.annual_overalls.get(str(self.current_year()), 0), fighter.overall)
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
            for fighter in list(roster):
                if fighter.age < 39:
                    continue
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
                        self.mark_retirement_fight_required(fighter, "Career retirement review")
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
            if promo and getattr(promo, "is_regional_feeder", False):
                for fighter in roster:
                    fighter.champion = False
                    fighter.interim_champion = False
                belts, interim_belts, belt_history = self.blank_belts(), self.blank_belts(), self.blank_belt_history()
            else:
                belts, interim_belts, belt_history = self.ensure_company_champions(roster, belts, company_name, region, size, player_owned=player_owned, interim_belts=interim_belts, belt_history=belt_history)
            if promo:
                promo.belts, promo.interim_belts, promo.belt_history = belts, interim_belts, belt_history
            else:
                self.belts, self.interim_belts, self.belt_history = belts, interim_belts, belt_history
        self.process_overdue_retirement_fights()

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
        pending = [
            fighter for fighter in self.all_fighter_objects()
            if not getattr(fighter, "retired", False) and getattr(fighter, "retirement_pending", False)
        ]
        pending.sort(key=lambda fighter: (self.retirement_fight_wait_months(fighter), fighter.age), reverse=True)
        booked = set()
        retirement_limit = min(40, max(10, len(pending) // 20))
        for fighter in pending[:retirement_limit]:
            wait = self.retirement_fight_wait_months(fighter)
            threshold = 6 if fighter in self.free_agents else 12
            if wait < threshold or fighter.name in booked:
                continue
            if fighter.injured:
                if fighter.age >= 50 and wait >= 12:
                    fighter.injured = max(0, fighter.injured - 1)
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
            opponent = min(opponents, key=lambda candidate: abs(candidate.overall - fighter.overall) + abs(candidate.age - fighter.age) * 0.25)
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
            event_name = f"{company_name} Retirement Showcase"
            self.result_records.insert(0, {
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
            self.result_records = self.result_records[:500]
            self.news.insert(0, f"Farewell fight booked: {result} at {event_name}.")
            self.retire_after_final_fight_if_due(fighter, company_name)
            self.retire_after_final_fight_if_due(opponent, company_name)

    def process_free_agent_retirements(self):
        """Free agency must not become a permanent retirement home for aging fighters."""
        for fighter in list(self.free_agents):
            if (self.month - 1) % 12 + 1 != self.retirement_review_month(fighter):
                continue
            waiting = max(0, getattr(fighter, "free_agent_months", 0))
            aging_out = fighter.age >= 38
            journeyman_exit = (fighter.age >= 34 and waiting >= 30 and fighter.overall < 73
                               and fighter.potential < 82 and not self.is_blue_chip_prospect(fighter))
            stalled_career = (fighter.age >= 30 and waiting >= 48 and fighter.overall < 68
                              and fighter.potential < 76 and not self.is_blue_chip_prospect(fighter))
            if not (aging_out or journeyman_exit or stalled_career):
                continue
            age_pressure = max(0, fighter.age - 37) * 0.065
            market_pressure = max(0, waiting - 24) / 150
            inactivity = 0.08 + max(0, -fighter.momentum) * 0.035
            health = fighter.injury_proneness / 850 + max(0, fighter.fatigue - 45) / 420
            if fighter.age >= 46 or random.random() < min(0.88, age_pressure + market_pressure + inactivity + health):
                if not getattr(fighter, "retirement_pending", False):
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

    def monthly_development_score(self, fighter):
        gym = self.gym_by_name(fighter.camp)
        camp_quality = self.gym_quality(fighter.camp)
        facilities = gym.facilities if gym else camp_quality
        specialty = self.gym_specialty_bonus(fighter, gym)
        dedication = fighter.detailed_skills.get("dedication", fighter.professionalism) if fighter.detailed_skills else fighter.professionalism
        runway = max(0, fighter.prime_end - fighter.age) * 3
        early_development = 14 if fighter.age < fighter.prime_start else 0
        late_learning = max(0, fighter.prime_end + 3 - fighter.age) * 1.5
        form = max(0, fighter.momentum) * 7
        morale = fighter.morale * 0.35
        gym_rat = 16 if fighter.trait == "Gym Rat" else 0
        learner = 14 if fighter.trait == "Technical Learner" else 0
        adaptable = 8 if fighter.trait == "Adaptable" else 0
        momentum_trait = max(0, fighter.momentum) * 3 if fighter.trait == "Momentum Fighter" else 0
        room = max(0, fighter.potential - fighter.overall) * 2.4
        fatigue_drag = fighter.fatigue * 0.35 + fighter.injured * 10
        crowd_drag = max(0, (gym.member_count - gym.capacity) * 0.12) if gym and gym.capacity < 500 else 0
        return camp_quality * 0.42 + facilities * 0.2 + specialty + dedication * 0.45 + runway + early_development + late_learning + form + morale + gym_rat + learner + adaptable + momentum_trait + room - fatigue_drag - crowd_drag

    def monthly_decline_score(self, fighter):
        age_drag = max(0, fighter.age - fighter.prime_end) * 13
        losing = max(0, -fighter.momentum) * 12
        losses = max(0, fighter.record_l - fighter.record_w // 2) * 1.8
        morale_drag = max(0, 45 - fighter.morale) * 0.8
        injury_drag = fighter.injury_proneness * 0.25 + fighter.injured * 16 + fighter.fatigue * 0.25
        professionalism_buffer = fighter.professionalism * 0.35
        form_buffer = max(0, fighter.momentum) * 5 + max(0, fighter.morale - 65) * 0.18
        veteran_buffer = 12 if fighter.trait in ("Veteran Savvy", "Warrior Spirit") else 0
        gym = self.gym_by_name(fighter.camp)
        camp_buffer = self.gym_quality(fighter.camp) * 0.16 + (gym.facilities if gym else 45) * 0.08
        return age_drag + losing + losses + morale_drag + injury_drag - professionalism_buffer - camp_buffer - form_buffer - veteran_buffer

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
        return max(0.04, min(0.58, chance - (0.08 if mode == "Financial Recovery" else 0) + (0.035 if mode == "Star Chasing" else 0) + executive_drive + mandate_drive - pressure + roster_health))

    def ai_should_run_show(self, promo):
        strategy = self.update_ai_promotion_strategy(promo)
        if promo.cash < max(120_000, promo.size * 6500):
            return False
        ready = [f for f in promo.roster if self.fighter_available_for_date(f) and f.fatigue < self.ai_fatigue_limit(promo)]
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

    def apply_ai_camp(self, fighter, promo):
        if not self.gym_by_name(fighter.camp) or random.random() < 0.08:
            fighter.camp = self.suggest_camp_for_fighter(fighter, getattr(promo, "region", "USA"))
        gym = self.gym_by_name(fighter.camp)
        quality = self.gym_quality(fighter.camp)
        weeks = random.randint(3, 10) if getattr(promo, "show_personality", "Balanced") != "Frequent Small Cards" else random.randint(2, 6)
        professionalism = fighter.professionalism / 100
        specialty = self.gym_specialty_bonus(fighter, gym)
        fighter.camp_quality = quality
        fighter.camp_weeks = weeks
        base_boost = round(weeks * (quality + specialty) / 125 * (0.7 + professionalism * 0.35) / 3)
        fighter.camp_boost = min(12, max(0, base_boost + self.camp_form_variance(fighter, gym)))
        self.apply_gym_camp_micro_improvement(fighter, gym, weeks)

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
        divisions = [(gender, weight) for weight in WEIGHTS for gender in ("Male", "Female")]
        random.shuffle(divisions)

        def pool_for(gender, weight):
            pool = [f for f in ready if f.gender == gender and f.weight == weight and f.name not in used]
            if mode == "Star Chasing":
                pool.sort(key=lambda f: (f.popularity + f.star_quality, f.overall, getattr(f, "rank_score", 0)), reverse=True)
            elif mode == "Prospect Rebuild":
                pool.sort(key=lambda f: (f.potential - f.overall, -f.age, f.momentum, f.overall), reverse=True)
            else:
                pool.sort(key=lambda f: (0 if f.champion else 1, getattr(f, "ranking_position", 999), -getattr(f, "rank_score", 0), -f.overall))
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
            opponent = min(opponents, key=lambda other: abs(other.overall - fighter.overall) + abs((other.record_w + other.record_l) - (fighter.record_w + fighter.record_l)) * 0.2)
            used.update({fighter.name, opponent.name})
            fights.append({"a": fighter, "b": opponent, "title": False, "main": False,
                           "grudge": fighter.rival == opponent.name or opponent.rival == fighter.name,
                           "booking_reason": "Final fight before retirement"})

        # 1) Title fights: champion (if fighting) defends against the top available contender.
        max_titles = (2 if promo.size >= 60 else 1) + (1 if mode == "Title Push" and promo.size >= 75 else 0)
        titles = 0
        for gender, weight in divisions:
            if titles >= max_titles or len(fights) >= target:
                break
            champ_name = belts.get(self.belt_key(gender, weight))
            pool = pool_for(gender, weight)
            champ = next((f for f in pool if f.name == champ_name), None)
            if champ and len(pool) >= 2 and random.random() < (0.52 if mode in ("Title Push", "Contender Cycle") else 0.4):
                contenders = [fighter for fighter in pool if fighter.name != champ.name]
                contender = next((fighter for fighter in contenders if getattr(fighter, "owed_title_shot", False)), None) or (contenders[0] if contenders else None)
                if contender:
                    used.update({champ.name, contender.name})
                    fights.append({"a": champ, "b": contender, "title": True, "main": False,
                                   "grudge": champ.rival == contender.name or contender.rival == champ.name, "booking_reason": "Title defense against the highest available contender"})
                    titles += 1

        # 2) Grudge matches: booked rivalries in the same division.
        for gender, weight in divisions:
            if len(fights) >= target:
                break
            pool = pool_for(gender, weight)
            for fighter in pool:
                if len(fights) >= target or fighter.name in used:
                    continue
                if fighter.rival:
                    # A rivalry is valuable only while it remains a credible
                    # sporting contest. Extremely lopsided old rivalries stay
                    # dormant instead of displacing most of a normal card.
                    opp = next((o for o in pool if o.name == fighter.rival and o.name not in used
                                and abs(o.overall - fighter.overall) <= 10), None)
                    if opp:
                        used.update({fighter.name, opp.name})
                        fights.append({"a": fighter, "b": opp, "title": False, "main": False, "grudge": True, "booking_reason": "Active rivalry matchup"})

        # 3) Ranking-based pairings: adjacent-ranked contenders fight.
        # A signed blue-chip prospect gets a visible development opportunity,
        # even before their rank catches up with their ceiling.
        prospects = [fighter for fighter in ready if fighter.name not in used and fighter.age <= 29
                     and (fighter.potential >= 90 or (fighter.potential - fighter.overall >= 12 and fighter.potential >= 84))]
        prospects.sort(key=lambda fighter: (fighter.potential, fighter.overall, fighter.record_w - fighter.record_l), reverse=True)
        prospect_showcase_limit = 2 if promo.size >= 65 and target >= 8 else 1
        prospect_showcases = 0
        for prospect in prospects:
            if len(fights) >= target or prospect_showcases >= prospect_showcase_limit:
                break
            opponents = [fighter for fighter in ready if fighter.name not in used and fighter.name != prospect.name
                         and fighter.gender == prospect.gender and fighter.weight == prospect.weight
                         and abs(fighter.overall - prospect.overall) <= 6]
            if not opponents:
                continue
            opponent = min(opponents, key=lambda fighter: abs(fighter.overall - prospect.overall) + abs((fighter.record_w + fighter.record_l) - (prospect.record_w + prospect.record_l)) * 0.25)
            used.update({prospect.name, opponent.name})
            prospect_showcases += 1
            fights.append({"a": prospect, "b": opponent, "title": False, "main": False,
                           "grudge": prospect.rival == opponent.name or opponent.rival == prospect.name, "booking_reason": "Development opportunity for a high-upside prospect"})

        # 4) Ranking-based pairings: adjacent-ranked contenders fight.
        for gender, weight in divisions:
            if len(fights) >= target:
                break
            pool = pool_for(gender, weight)
            while len(fights) < target:
                available = [fighter for fighter in pool if fighter.name not in used]
                if len(available) < 2:
                    break
                pair_options = []
                for index, a_option in enumerate(available[:-1]):
                    for b_option in available[index + 1:]:
                        rating_gap = abs(b_option.overall - a_option.overall)
                        if rating_gap > 6:
                            continue
                        rank_gap = abs(getattr(b_option, "ranking_position", 999) - getattr(a_option, "ranking_position", 999))
                        form_gap = abs(getattr(b_option, "momentum", 0) - getattr(a_option, "momentum", 0))
                        protect_a = mode == "Prospect Rebuild" and a_option.age <= 26 and a_option.potential - a_option.overall >= 7
                        protect_b = mode == "Prospect Rebuild" and b_option.age <= 26 and b_option.potential - b_option.overall >= 7
                        protection_penalty = int(protect_a and b_option.overall > a_option.overall + 3)
                        protection_penalty += int(protect_b and a_option.overall > b_option.overall + 3)
                        pair_options.append(((protection_penalty, rating_gap * 4 + rank_gap * 0.7 + form_gap * 0.8, rating_gap), a_option, b_option))
                if not pair_options:
                    break
                _, a, b = min(pair_options, key=lambda item: item[0])
                used.update({a.name, b.name})
                reason = "Adjacent-ranked divisional matchup"
                if inactive.get(a.name, 0) >= 8 or inactive.get(b.name, 0) >= 8:
                    reason = "Activity-restoring matchup for a long-inactive fighter"
                fights.append({"a": a, "b": b, "title": False, "main": False,
                               "grudge": a.rival == b.name or b.rival == a.name, "booking_reason": reason})

        if not fights:
            return []

        # 5) Main event: a title fight if there is one, else the biggest-name bout.
        def draw(fight):
            a, b = fight["a"], fight["b"]
            return (fight["title"], a.popularity + b.popularity + a.star_power + b.star_power + (40 if fight["grudge"] else 0))
        max(fights, key=draw)["main"] = True
        for fight in fights:
            if fight.get("main"):
                fight["booking_reason"] += "; elevated to main event by title/star/grudge draw"
        validated = []
        booked_names = set()
        for fight in fights:
            a, b = fight["a"], fight["b"]
            if a.name == b.name or a.name in booked_names or b.name in booked_names:
                continue
            booked_names.update((a.name, b.name))
            validated.append(fight)
        if validated and not any(fight.get("main") for fight in validated):
            max(validated, key=draw)["main"] = True
        ordered = sorted(validated, key=draw, reverse=True)
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
        commercial_strength, market_volatility, market_momentum = self.update_ai_financial_market(promo)
        ready = [f for f in promo.roster if self.fighter_available_for_date(f) and f.fatigue < self.ai_fatigue_limit(promo)]
        if len(ready) < self.ai_min_ready_fighters(promo):
            if random.random() < 0.45:
                prospect = self.create_generated_fighter(10, min(80, promo.size), 45, min(88, 55 + promo.size // 3), region=promo.region)
                prospect.contract_months = random.randint(6, 18)
                prospect.exclusive = True
                prospect.camp = promo.name
                promo.roster.append(prospect)
            return
        fight_target = {"Super Shows": random.randint(8, 11), "Seasonal": random.randint(7, 10), "Prospect Builder": random.randint(7, 9), "Frequent Small Cards": random.randint(7, 8)}.get(getattr(promo, "show_personality", "Balanced"), random.randint(7, 9))
        mode = strategy.get("current_mode")
        if mode == "Financial Recovery":
            fight_target = max(5, fight_target - 2)
        elif mode == "Star Chasing":
            fight_target = max(6, fight_target - 1)
        elif mode == "Prospect Rebuild":
            fight_target = min(11, fight_target + 1)
        elif mode == "Contender Cycle":
            fight_target = min(12, fight_target + 1)
        fights = self.build_ai_card(promo, ready, fight_target)
        minimum_card = 5 if strategy.get("current_mode") == "Financial Recovery" else 6
        if len(fights) < minimum_card:
            return
        projected_cost = sum(f["a"].purse + f["b"].purse for f in fights) + promo.size * 9500 + len(fights) * 22000
        # Broadcasters and venues advance a portion of expected receipts. AI
        # companies therefore need meaningful working capital, not the entire
        # card cost sitting idle in cash; this lets a small promotion trade out
        # of trouble while still preventing an insolvent company from booking.
        working_capital = max(80_000, projected_cost * (0.22 if mode == "Financial Recovery" else 0.32))
        if promo.cash < working_capital:
            if random.random() < 0.35:
                promo.stability = max(1, promo.stability - 1)
                self.news.insert(0, f"Week {self.week}: {promo.name} postponed a card after budget review.")
            return
        pop_gain = 0
        event_name = f"{promo.name} {promo.event_counter}"
        event_city = random.choice(REGION_CITIES.get(promo.region, [promo.region]))
        promo.event_counter += 1
        main_result = ""
        event_hype = 0
        event_log = []
        fight_logs = []
        for entry in fights:
            a, b = entry["a"], entry["b"]
            is_title, is_main, is_grudge = entry["title"], entry["main"], entry["grudge"]
            self.apply_ai_camp(a, promo)
            self.apply_ai_camp(b, promo)
            self.perform_weigh_in(a, title_fight=is_title, persist=True)
            self.perform_weigh_in(b, title_fight=is_title, persist=True)
            bout = {"main": is_main, "title": is_title, "tier": entry.get("tier", "Main Card"), "region": promo.region, "city": event_city}
            winner, loser, method, round_no, _lines = self.simulate_fight(a, b, bout)
            hype_seed = a.popularity + b.popularity + (40 if is_title else 0) + (25 if is_grudge else 0)
            ai_excitement = self.fight_excitement(a, b, winner, loser, method, round_no, bout, hype_seed)
            self.record_season_result(winner, loser, method, round_no, bout, ai_excitement, promo.name)
            label = ("TITLE FIGHT" if is_title else ("MAIN EVENT" if is_main else entry.get("card_position", "BOUT")))
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
                winner.fight_history = winner.fight_history or []
                loser.fight_history = loser.fight_history or []
                winner.fight_history.insert(0, line)
                loser.fight_history = loser.fight_history or []
                loser.fight_history.insert(0, line)
                result_line = f"{winner.name} def. {loser.name} by {method} (R{round_no})"
                if is_main or not main_result:
                    main_result = result_line
            fight_logs.append({"heading": f"{a.name} vs {b.name}", "label": label,
                               "a": a.name, "b": b.name, "a_record": a.record, "b_record": b.record,
                               "weight": a.weight, "result": result_line,
                               "booking_reason": entry.get("booking_reason", "AI matchmaking"),
                               "lines": [f"AI booking: {entry.get('booking_reason', 'AI matchmaking')}", *list(_lines), "", result_line]})
            event_log.extend([f"[{label}] {a.name} vs {b.name} — {entry.get('booking_reason', 'AI matchmaking')}", *_lines, result_line, ""])
            if method != "Draw":
                winner.last_fight = line
                loser.last_fight = line
                winner.last_fight_month = self.month
                loser.last_fight_month = self.month
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
        # Event revenue has a lower, more realistic baseline than the old
        # universal windfall and is shaped by a company's persistent market
        # health. A weak brand can have a good year, but it also has real lean
        # stretches; established companies remain more dependable.
        # Smaller brands must sell a much larger share of the room to break
        # even. Market momentum therefore has a meaningful effect on a fragile
        # company, while an established broadcaster still gives major brands a
        # dependable commercial floor.
        commercial_factor = 0.42 + commercial_strength / 170 + market_momentum / 95
        event_noise = random.uniform(-market_volatility / 170, market_volatility / 170)
        revenue_factor = max(0.32, commercial_factor + event_noise)
        revenue = round(event_hype * promo.size * regional_pull * random.randint(70, 175) * revenue_factor)
        # Attendance, distribution and sponsor demand are not certain. Most
        # cards land near forecast, while a minority underperform or break out;
        # this creates genuine loss-making shows without predetermining them.
        commercial_roll = random.random()
        if commercial_roll < 0.18:
            revenue = round(revenue * random.uniform(0.28, 0.48))
            projected_cost = round(projected_cost * random.uniform(1.12, 1.28))
        elif commercial_roll > 0.90:
            revenue = round(revenue * random.uniform(1.15, 1.35))
        # Successful companies reinvest most gross surplus into purses,
        # distribution and production. The retained share stays meaningful but
        # no longer produces the old 50% average event margins.
        reinvestment_rate = min(0.74, 0.40 + promo.size / 300)
        strategic_reinvestment = round(max(0, revenue - projected_cost) * reinvestment_rate)
        event_profit = revenue - projected_cost - strategic_reinvestment
        promo.cash += event_profit
        margin = event_profit / max(1, projected_cost)
        stability_target = strategy.get("stability_target", max(58, min(86, round(50 + commercial_strength * 0.38))))
        if margin >= 0.35 and promo.stability < stability_target:
            stability_delta = 1
        elif margin >= 0.08:
            stability_delta = 0
        elif margin >= 0:
            stability_delta = -1
        elif margin >= -0.20:
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
            "finance": {"ticket_revenue": revenue, "total_revenue": revenue, "total_expense": projected_cost + strategic_reinvestment, "profit": event_profit},
            "log": [summary, ""] + event_log,
            "fight_logs": fight_logs,
        }
        self.ai_event_archive.insert(0, package)
        self.ai_event_archive = self.ai_event_archive[:120]
        self.result_records.insert(0, {
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
        self.result_records = self.result_records[:500]
        self.evaluate_promotion_achievements(promo.name, package)
        self.refresh_historical_records()
        self.refresh_promotion_rankings(company=promo.name, roster=promo.roster)
        if promo.region in self.regions:
            self.regions[promo.region]["last_major_show"] = summary
            region_data = self.regions[promo.region]
            region_data["mma_love"] = max(10, min(100, region_data.get("mma_love", 50) + (1 if event_hype > promo.size * 3 else 0)))
        if random.random() < 0.65:
            self.news.insert(0, f"{promo.name} ran {event_name}; {main_result}.")

    def simulate_regional_feeder_month(self, promo):
        """Low-cost developmental circuit: young fighters build records, not profits."""
        ready = [fighter for fighter in promo.roster if self.fighter_available_for_date(fighter) and fighter.fatigue < 58]
        by_division = {}
        for fighter in ready:
            by_division.setdefault((fighter.gender, fighter.weight), []).append(fighter)
        fights = []
        for division, fighters in by_division.items():
            random.shuffle(fighters)
            # Developmental cards should build believable records, not repeatedly
            # feed a 0-12 novice to a much stronger prospect.
            def match_rating(item):
                bouts = item.record_w + item.record_l + item.record_d
                retirement_priority = 120 if getattr(item, "retirement_pending", False) else 0
                return retirement_priority + item.overall + (item.record_w - item.record_l) * 0.7 + min(12, bouts) * 0.25 + random.uniform(-2, 2)

            fighters.sort(key=match_rating, reverse=True)
            while len(fighters) >= 2 and len(fights) < 7:
                a = fighters.pop(0)
                a_bouts = a.record_w + a.record_l + a.record_d
                a_rate = a.record_w / max(1, a_bouts)

                def matchup_distance(item):
                    bouts = item.record_w + item.record_l + item.record_d
                    win_rate = item.record_w / max(1, bouts)
                    return (abs(item.overall - a.overall) * 3.0
                            + abs(bouts - a_bouts) * 0.35
                            + abs(win_rate - a_rate) * 18
                            + abs(item.age - a.age) * 0.25)

                opponent_index = min(range(len(fighters)), key=lambda index: matchup_distance(fighters[index]))
                b = fighters.pop(opponent_index)
                fights.append((a, b))
        if not fights:
            self.regional_recruit_fighter(promo)
            return
        event_name = f"{promo.name} Development Night {promo.event_counter}"
        promo.event_counter += 1
        results = []
        for a, b in fights:
            self.apply_ai_camp(a, promo)
            self.apply_ai_camp(b, promo)
            self.perform_weigh_in(a, title_fight=False, persist=True)
            self.perform_weigh_in(b, title_fight=False, persist=True)
            bout = {"main": False, "title": False, "tier": "Early Prelims", "region": promo.region}
            winner, loser, method, round_no, _lines = self.simulate_fight(a, b, bout)
            if method == "Draw":
                self.apply_draw_result(a, b, bout)
                results.append(f"{a.name} vs {b.name} (Draw R{round_no})")
                continue
            self.update_elo(winner, loser, bout, method)
            self.commit_career_stats(winner, method, won=True)
            self.commit_career_stats(loser, method, won=False)
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
            line = f"Month {self.month} Week {self.week}: {winner.name} def. {loser.name} by {method} at {event_name}"
            winner.fight_history = winner.fight_history or []
            loser.fight_history = loser.fight_history or []
            winner.fight_history.insert(0, line)
            loser.fight_history.insert(0, line)
            winner.last_fight = loser.last_fight = line
            if winner.age <= 24 and winner.overall < winner.potential and random.random() < 0.34:
                self.adjust_random_skill(winner, 1)
                self.adjust_detailed_skill(winner, 1)
            elif winner.trait in ("Overlooked Talent", "Technical Learner") and winner.overall < winner.potential and random.random() < 0.12:
                self.adjust_random_skill(winner, 1)
                self.adjust_detailed_skill(winner, 1)
            results.append(f"{winner.name} def. {loser.name} ({method} R{round_no})")
            self.retire_after_final_fight_if_due(winner, promo.name)
            self.retire_after_final_fight_if_due(loser, promo.name)
        promo.show_history.insert(0, f"{event_name}: {len(fights)} developmental bouts, main result {results[0]}.")
        promo.show_history = promo.show_history[:12]
        self.regional_review_underperformers(promo)
        self.regional_graduate_fighters(promo)
        self.regional_recruit_fighter(promo)
        if random.random() < 0.45:
            self.news.insert(0, f"{promo.name} ran a development night; {results[0]}.")

    def regional_review_underperformers(self, promo):
        """End unsustainable regional careers before loss records become implausible."""
        departures = []
        for fighter in list(promo.roster):
            bouts = fighter.record_w + fighter.record_l + fighter.record_d
            win_rate = fighter.record_w / max(1, bouts)
            early_washout = bouts >= 14 and fighter.record_w <= 1 and fighter.potential < 78
            sustained_struggle = bouts >= 20 and win_rate < 0.22 and fighter.potential < 85
            terminal_record = bouts >= 28 and win_rate < 0.28
            if not (early_washout or sustained_struggle or terminal_record):
                continue
            if not getattr(fighter, "retirement_pending", False):
                self.mark_retirement_fight_required(fighter, "Regional career review")
            departures.append(fighter)
        for fighter in departures[:2]:
            headline = f"Regional career review: {fighter.name} needs one final fight before leaving professional MMA ({fighter.record})."
            self.news.insert(0, headline)
            self.record_world_story("Regional Career Review", headline, fighter.retirement_reason, [promo.name], [fighter.name], 2)
        return departures

    def regional_graduate_fighters(self, promo):
        eligible = [
            fighter for fighter in promo.roster
            if fighter.age >= 18 and not fighter.injured and (
                (fighter.record_w >= 6 and fighter.overall >= 70)
                or (fighter.record_w >= 4 and fighter.potential >= 84)
                or (fighter.age >= 25 and fighter.record_w >= 8)
                or (fighter.feeder_origin == promo.name and fighter.record_w >= 3 and fighter.momentum >= 3 and fighter.popularity >= 20)
            )
        ]
        eligible.sort(key=lambda fighter: (fighter.potential, fighter.overall, fighter.record_w, fighter.momentum), reverse=True)
        for fighter in eligible[:random.choice([0, 1, 1, 2])]:
            promo.roster.remove(fighter)
            fighter.feeder_origin = promo.name
            fighter.contract_months = 0
            fighter.exclusive = False
            fighter.contract_type = "Free Agent"
            fighter.free_agent_months = 0
            fighter.popularity = min(42, fighter.popularity + 4)
            if fighter.trait == "Overlooked Talent":
                fighter.momentum = min(5, fighter.momentum + 1)
            self.free_agents.append(fighter)
            self.news.insert(0, f"Regional breakthrough: {fighter.name} ({fighter.record}, popularity {fighter.popularity}) leaves {promo.name} and enters free agency after earning a second look.")
            self.record_world_story("Regional Breakthrough", f"{fighter.name} earns a second look after {promo.name}.", f"Record {fighter.record}, popularity {fighter.popularity}, potential {fighter.potential}.", [promo.name], [fighter.name], 2)

    def regional_recruit_fighter(self, promo):
        if len(promo.roster) >= 56 or random.random() > 0.55:
            return
        candidates = [
            fighter for fighter in self.free_agents
            if not fighter.ai_offer_company and not fighter.retirement_pending and not fighter.injured and fighter.age <= 33
            and (fighter.overall < 76 or fighter.potential >= 78)
        ]
        if candidates:
            def proving_ground_value(item):
                young_upside = item.potential - item.overall
                overlooked = 18 if item.momentum <= 0 and item.age >= 21 else 0
                return young_upside + overlooked + item.professionalism * 0.12 + random.uniform(-8, 8)
            fighter = max(candidates, key=proving_ground_value)
            self.free_agents.remove(fighter)
            fighter.contract_months = 0
            fighter.exclusive = False
            fighter.contract_type = "Developmental"
            fighter.free_agent_months = 0
            fighter.feeder_origin = promo.name
            fighter.camp = promo.name
            if fighter.age >= 21 and fighter.momentum <= 0 and random.random() < 0.6:
                fighter.trait = "Overlooked Talent"
                fighter.morale = min(100, fighter.morale + 8)
                self.news.insert(0, f"Second chance: {fighter.name} joins {promo.name} to rebuild their record and market value.")
            promo.roster.append(fighter)
            return
        fighter = self.create_regional_feeder_fighter(promo.region, self.active_fighter_names(), random.choice(["Male", "Female"]))
        fighter.weight = random.choice(WEIGHTS)
        fighter.camp = promo.name
        fighter.feeder_origin = promo.name
        promo.roster.append(fighter)

    def market_churn(self):
        self.resolve_ai_contract_offers()
        if random.random() < 0.55:
            prospect = self.create_generated_fighter(5, 32, 42, 76)
            self.avoid_name_collision(prospect, self.active_fighter_names())
            self.free_agents.append(prospect)
            self.news.insert(0, f"New free agent: {prospect.name}, a {prospect.age}-year-old {prospect.style} from {prospect.region}.")
        self.ai_create_contract_offers()
        self.ensure_free_agent_depth()

    def is_blue_chip_prospect(self, fighter):
        return fighter.age <= 30 and (
            fighter.potential >= 90
            or (fighter.potential >= 85 and fighter.record_w >= 6)
            or (fighter.overall >= 88 and fighter.record_w >= 5)
        )

    def advance_free_agent_market(self):
        for fighter in self.free_agents:
            fighter.free_agent_months = max(0, getattr(fighter, "free_agent_months", 0)) + 1
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
                    and self.month - getattr(fighter, "showcase_last_month", -99) >= 3
                    and (fighter.age <= 34 or getattr(fighter, "retirement_pending", False))]
        groups = {}
        for fighter in eligible:
            groups.setdefault((fighter.gender, fighter.weight), []).append(fighter)
        bouts = 0
        fight_logs = []
        event_log = []
        results = []
        bout_target = random.randint(6, 8)
        event_name = f"Independent Showcase {getattr(self, 'independent_showcase_counter', 1)}"
        ordered_groups = sorted(
            groups.values(),
            key=lambda fighters: (
                any(getattr(fighter, "retirement_pending", False) for fighter in fighters),
                max((fighter.age for fighter in fighters if getattr(fighter, "retirement_pending", False)), default=0),
                len(fighters),
            ),
            reverse=True,
        )
        for fighters in ordered_groups:
            if bouts >= bout_target:
                break
            fighters.sort(key=lambda fighter: (getattr(fighter, "retirement_pending", False), fighter.overall, fighter.record_w - fighter.record_l, fighter.free_agent_months), reverse=True)
            while len(fighters) >= 2 and bouts < bout_target:
                a = fighters.pop(0)
                b = min(fighters, key=lambda fighter: abs(fighter.overall - a.overall) + abs((fighter.record_w + fighter.record_l) - (a.record_w + a.record_l)) * 0.3)
                fighters.remove(b)
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
                                   "a": a.name, "b": b.name, "a_record": a.record, "b_record": b.record,
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
        self.result_records.insert(0, {
            "date": package["date"], "company": "Independent Circuit", "event": event_name,
            "summary": summary, "fights": len(results), "gate": "$0", "profit": "$0",
            "log": package["log"], "fight_logs": fight_logs, "finance": package["finance"],
        })
        self.result_records = self.result_records[:500]
        if not getattr(self, "spectator_mode", False):
            for a, b, result_line, _excitement in results:
                for fighter in (a, b):
                    if self.is_blue_chip_prospect(fighter):
                        self.inbox.append({"subject": f"Showcase Scouting Report - {fighter.name}", "body": f"{fighter.name} competed at {event_name}: {result_line}. They remain available to negotiate.", "type": "Scouting", "resolved": False})
        self.news.insert(0, summary)
        self.record_world_story("Independent Showcase", summary, "Unsigned fighters competed for contracts and visibility.", ["Independent Circuit"], [fighter.name for result in results for fighter in result[:2]], 2)

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
            for fighter in list(promo.roster):
                if fighter.contract_months > 0:
                    continue
                active_roster = [member for member in promo.roster if not member.retired]
                roster_target = self.ai_roster_target(promo)
                division_depth = sum(1 for member in active_roster if member.gender == fighter.gender and member.weight == fighter.weight)
                cornerstone = (fighter.champion or fighter.interim_champion or fighter.overall >= 82
                               or fighter.potential >= 90 or fighter.popularity >= 68)
                normal_value = fighter.overall >= 75 or fighter.potential >= 86 or fighter.popularity >= 50
                coverage_value = division_depth <= 4 or (division_depth <= 5 and (fighter.overall >= 64 or fighter.potential >= 75))
                # A promotion below its sustainable card roster protects useful
                # depth. An oversized company renews only genuine cornerstones
                # or fighters needed to keep a division bookable.
                retain = cornerstone or coverage_value or (len(active_roster) <= roster_target and normal_value)
                renewal_runway = promo.cash > max(180_000, promo.size * 9_000)
                # Renewing a champion or essential divisional coverage has no
                # signing bonus. Their purses are paid only when booked, so a
                # recovering promotion should not release and immediately
                # replace the same depth merely because cash is temporarily low.
                if retain and (renewal_runway or cornerstone or coverage_value):
                    fighter.contract_months = random.randint(10, 24)
                    fighter.purse = round(fighter.purse * random.uniform(1.04, 1.20))
                    continue
                promo.roster.remove(fighter)
                fighter.contract_months = 0
                fighter.exclusive = False
                fighter.contract_type = "Free Agent"
                fighter.free_agent_months = 0
                fighter.champion = False
                fighter.interim_champion = False
                self.free_agents.append(fighter)

    def clear_ai_contract_offer(self, fighter):
        fighter.ai_offer_company = ""
        fighter.ai_offer_purse = 0
        fighter.ai_offer_months = 0
        fighter.ai_offer_signing_bonus = 0
        fighter.ai_offer_deadline_month = 0

    def ai_division_target(self, promo):
        """Sustainable contracted depth per gender/weight bucket for an AI company."""
        if promo.size >= 80:
            return 8
        if promo.size >= 60:
            return 6
        if promo.size >= 40:
            return 5
        return 4

    def ai_roster_target(self, promo):
        """Roster capacity is tied to the divisions a company must actually book."""
        weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
        return max(40, len(weights) * 2 * self.ai_division_target(promo))

    def ai_roster_market_demand(self, promo):
        active = [member for member in promo.roster if not member.retired]
        weights = list(getattr(promo, "weight_classes", None) or WEIGHTS)
        counts = {
            (gender, weight): sum(1 for member in active if member.gender == gender and member.weight == weight)
            for gender in ("Male", "Female") for weight in weights
        }
        critical = sum(max(0, 4 - count) for count in counts.values())
        capacity = max(0, self.ai_roster_target(promo) - len(active))
        return critical, capacity

    def ai_roster_division_need(self, promo, fighter):
        count = len([member for member in promo.roster if member.gender == fighter.gender and member.weight == fighter.weight])
        target = self.ai_division_target(promo)
        return max(-24, (target - count) * 7)

    def ai_free_agent_value(self, promo, fighter, division_need=None):
        strategy = self.promotion_strategy(promo)
        division_need = self.ai_roster_division_need(promo, fighter) if division_need is None else division_need
        prospect = max(0, fighter.potential - fighter.overall) * 1.7
        ability = fighter.overall * 0.7
        marketability = fighter.popularity * 0.34 + fighter.star_quality * 0.18 + fighter.media_presence * 0.12
        form = fighter.momentum * 4 + fighter.morale * 0.08
        regional = 6 if fighter.region == promo.region else 0
        age = 5 if 20 <= fighter.age <= 30 else -max(0, fighter.age - 34) * 2.2
        cost = fighter.purse / max(1800, promo.size * 38)
        star_fit = (fighter.popularity + fighter.star_quality * 0.55) * (strategy.get("star_focus", 50) - 50) / 260
        prospect_fit = max(0, fighter.potential - fighter.overall) * (strategy.get("prospect_focus", 50) - 50) / 70
        merit_fit = (fighter.elo_rating - 1450) * (strategy.get("merit_focus", 50) - 50) / 460
        recovery_drag = 18 if strategy.get("current_mode") == "Financial Recovery" and fighter.purse > promo.size * 310 else 0
        blue_chip = 65 if self.is_blue_chip_prospect(fighter) else 0
        waiting = min(28, getattr(fighter, "free_agent_months", 0) * 2)
        return ability + prospect + marketability + form + division_need + regional + age + star_fit + prospect_fit + merit_fit + blue_chip + waiting - cost - recovery_drag + random.uniform(-7, 7)

    def ai_offer_terms(self, promo, fighter):
        leverage = 1 + fighter.popularity / 95 + max(0, fighter.momentum) * 0.08
        prospect_premium = max(0, fighter.potential - fighter.overall) * 0.018
        reputation_premium = promo.reputation_score / 250
        purse = max(fighter.purse, round(fighter.purse * (1.08 + prospect_premium + reputation_premium)))
        purse += round(fighter.overall * promo.size * 5)
        purse = max(2500, min(450000, round(purse / 500) * 500))
        months = random.randint(12, 28) if fighter.age <= 30 else random.randint(8, 18)
        signing = round(purse * random.uniform(0.8, 1.8) * leverage / 500) * 500
        return purse, months, signing

    def ai_create_contract_offers(self):
        eligible_promos = [promo for promo in self.promotions if not getattr(promo, "is_regional_feeder", False) and promo.cash > max(120_000, promo.size * 7000)]
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
            critical = sum(max(0, 4 - active_counts.get((gender, weight), 0)) for gender in ("Male", "Female") for weight in weights)
            capacity = max(0, self.ai_roster_target(promo) - len(active))
            market_cache[id(promo)] = {
                "demand": (critical, capacity),
                "active_counts": active_counts,
                "all_counts": all_counts,
            }
        eligible_promos.sort(key=lambda promo: (*market_cache[id(promo)]["demand"], random.random()), reverse=True)
        offers_created = 0
        free_pool = len([fighter for fighter in self.free_agents if not fighter.retired])
        offer_capacity = max(8, min(18, 8 + max(0, free_pool - 280) // 90))

        def can_recruit(promo, fighter, blue_chip=False):
            cached = market_cache[id(promo)]
            critical, capacity = cached["demand"]
            division_depth = cached["active_counts"].get((fighter.gender, fighter.weight), 0)
            if capacity or (critical and division_depth < 4):
                return True
            # Elite prospects remain exceptional market opportunities. A full
            # roster can still sign one and release a lower-value contract at
            # the next expiry review instead of ignoring blue-chip talent.
            return blue_chip

        def cached_free_agent_value(promo, fighter):
            count = market_cache[id(promo)]["all_counts"].get((fighter.gender, fighter.weight), 0)
            division_need = max(-24, (self.ai_division_target(promo) - count) * 7)
            return self.ai_free_agent_value(promo, fighter, division_need=division_need)

        def create_offer(promo, fighter, premium=False):
            nonlocal offers_created
            purse, months, signing = self.ai_offer_terms(promo, fighter)
            if premium:
                purse = round(purse * 1.14 / 500) * 500
                signing = round(signing * 1.2 / 500) * 500
            reserve = max(90_000, promo.size * 7200)
            runway_commitment = signing + purse
            if promo.cash < reserve + runway_commitment:
                return False
            fighter.ai_offer_company = promo.name
            fighter.ai_offer_purse = purse
            fighter.ai_offer_months = months
            fighter.ai_offer_signing_bonus = signing
            fighter.ai_offer_deadline_month = self.month + 1
            fighter.negotiation_heat = min(100, fighter.negotiation_heat + (16 if premium else 12))
            offers_created += 1
            return True

        # Blue chips do not disappear in the ordinary five-offer lottery.
        priority = sorted([fighter for fighter in self.free_agents if not fighter.retired and not fighter.retirement_pending and not fighter.injured and not fighter.ai_offer_company and self.is_blue_chip_prospect(fighter) and (getattr(self, "spectator_mode", False) or fighter.player_talent_window_until < self.month)], key=lambda fighter: (fighter.potential, fighter.overall, fighter.record_w - fighter.record_l, fighter.free_agent_months), reverse=True)
        for fighter in priority[:3]:
            options = sorted([promo for promo in eligible_promos if can_recruit(promo, fighter, blue_chip=True)], key=lambda promo: cached_free_agent_value(promo, fighter), reverse=True)
            promo = next((item for item in options if item.cash > max(90_000, item.size * 7200)), None)
            if not promo:
                continue
            create_offer(promo, fighter, premium=True)
        for promo in eligible_promos:
            if offers_created >= offer_capacity:
                break
            critical, capacity = market_cache[id(promo)]["demand"]
            if not (critical or capacity):
                continue
            attempts = 2 if critical >= 2 or capacity >= 10 else 1
            demand_chance = min(0.96, 0.46 + critical * 0.10 + capacity / 90 + free_pool / 3200)
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
                fighter = candidates[0]
                if create_offer(promo, fighter):
                    self.news.insert(0, f"Contract market: {promo.name} offered {fighter.name} ${fighter.ai_offer_purse:,}/fight for {fighter.ai_offer_months} months. The offer is live until next month.")

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
            offer_score += 7 if fighter.region == promo.region else 0
            offer_score += 6 if fighter.age <= 26 and fighter.potential - fighter.overall >= 8 else 0
            offer_score += 18 if self.is_blue_chip_prospect(fighter) else 0
            offer_score += random.uniform(-12, 12)
            runway_commitment = fighter.ai_offer_signing_bonus + fighter.ai_offer_purse
            reserve = max(90_000, promo.size * 7200)
            if offer_score >= 64 and promo.cash >= reserve + runway_commitment:
                self.free_agents.remove(fighter)
                signing_bonus = fighter.ai_offer_signing_bonus
                # Only the signing bonus is paid immediately. Fight purses are
                # already charged to event costs, so deducting two purses here
                # charged AI companies twice for the same future bouts.
                promo.cash -= signing_bonus
                fighter.purse = fighter.ai_offer_purse
                fighter.contract_months = fighter.ai_offer_months
                fighter.exclusive = True
                fighter.contract_type = "Exclusive"
                fighter.free_agent_months = 0
                fighter.champion = False
                fighter.interim_champion = False
                fighter.morale = min(100, fighter.morale + random.randint(3, 8))
                self.clear_ai_contract_offer(fighter)
                promo.roster.append(fighter)
                self.news.insert(0, f"{promo.name} completed a negotiated signing with {fighter.name}: ${fighter.purse:,}/fight, {fighter.contract_months} months, ${signing_bonus:,} signing bonus.")
                self.record_world_story("Major Signing", f"{promo.name} signs {fighter.name}.", f"${fighter.purse:,}/fight for {fighter.contract_months} months.", [promo.name], [fighter.name], 3)
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
            if months not in (3, 1):
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

    def update_contracts(self):
        if getattr(self, "spectator_mode", False):
            return
        expired = [f for f in self.roster if f.contract_months <= 0]
        for fighter in expired:
            if fighter.champion or fighter.popularity > 55 or fighter.morale > 60:
                fighter.contract_months = random.randint(8, 20)
                fighter.purse = round(fighter.purse * random.uniform(1.05, 1.28))
                self.news.insert(0, f"{fighter.name} agreed a new {fighter.contract_months}-month deal with {self.player_company_name}.")
            else:
                self.belts, self.interim_belts, self.belt_history = self.vacate_fighter_belts(fighter, self.roster, self.belts, self.interim_belts, self.belt_history, "Left the company after contract expiry.")
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

    def write_log(self):
        self.log_text.config(state="normal")
        self.log_text.delete("1.0", "end")
        self.log_text.insert("end", "\n".join(self.event_log) if self.event_log else "No news yet.")
        self.log_text.config(state="disabled")
