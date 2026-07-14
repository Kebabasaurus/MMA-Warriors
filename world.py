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
            # Cost control matters, but cannot fully erase a large roster and
            # production footprint. This makes reckless expansion expensive.
            operating_multiplier = 0.88 + max(0, 85 - discipline) / 170
            monthly_cost = round((32_000 + promo.size * 1_850 + roster_size * 520) * operating_multiplier)
            promo.cash -= monthly_cost
            # Cash does not compound forever. Profit above a healthy, size-based
            # operating reserve is spent on the sport (bigger purses, facilities,
            # expansion) and distributed to ownership, so a company's bank mean-
            # reverts to a realistic band instead of growing into the billions.
            target_reserve = max(2_000_000, int(promo.size ** 2 * 9_000))
            if promo.cash > target_reserve:
                promo.cash -= int((promo.cash - target_reserve) * 0.28)
            reserve = max(150_000, promo.size * 8_000)
            if promo.cash < 0:
                promo.stability = max(1, promo.stability - 7)
            elif promo.cash < reserve:
                promo.stability = max(1, promo.stability - 3)
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
            executive = promo.executive or self.seed_promotion_executive(promo.name)
            promo.executive = executive
            if not executive.get("rescue_capital_used", False):
                rescue = max(8_000_000, promo.size * 120_000)
                executive["rescue_capital_used"] = True
                promo.cash = rescue
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
        injection = max(2_500_000, promo.size * random.randint(55_000, 85_000))
        promo.cash = injection
        promo.stability = random.randint(32, 48)
        promo.momentum = max(-4, min(3, promo.momentum + random.randint(-1, 2)))
        promo.size = max(22, promo.size - random.randint(3, 9))
        promo.reputation_score = max(18, promo.reputation_score - random.randint(2, 6))
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
        successor["rescue_capital_used"] = False
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

    def refresh_promotion_rankings(self, track=True):
        """Maintain a transparent current/previous rank for the player and every AI promotion."""
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
        if fighter in getattr(self, "roster", []):
            adjustment += 1 if self.staff_skill("Doctor") >= 74 else 0
        if fighter.injured:
            base += fighter.injured * 4
        fighter.available_week = max(getattr(fighter, "available_week", 0), self.calendar_week_index() + max(2, base - adjustment))

    def spectator_advance_weeks(self, weeks=1, status_prefix="Simulating"):
        if not getattr(self, "spectator_mode", False):
            messagebox.showinfo("Spectator controls", "Start a new game in Spectator Mode to use world fast-forward controls.")
            return False
        weeks = max(1, int(weeks))
        for index in range(weeks):
            if hasattr(self, "spectator_sim_status"):
                self.spectator_sim_status.config(text=f"{status_prefix}: {index + 1}/{weeks} weeks | Month {self.month}, Week {self.week}")
            self.root.update_idletasks()
            self.advance_month()
        self.refresh_all()
        self.write_log()
        return True

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
        for _ in range(24):
            self.spectator_advance_weeks(1, "Looking for the next hosted event")
            if len(self.ai_event_archive) > before:
                self.watch_latest_world_event()
                return
        messagebox.showinfo("No event yet", "No promotion hosted a card in the next 24 weeks. The world still advanced normally.")

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
        production = self.finance["production_base"] + len(event["fights"]) * 5200 + best_broadcaster["fee"] + commentator_pay + venue_ops
        medical = self.finance["medical_base"] + len(event["fights"]) * 1900
        marketing = self.finance["marketing_budget"] + round(max(0, build_score - 48) * 1100)
        drug_testing = 0 if self.rules["drug_testing"] == "None" else len(event["fights"]) * 2 * self.finance["drug_test_cost"]
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

    def advance_month(self):
        if any(self.is_event_due(event) for event in self.scheduled_events):
            self.prompt_due_event()
            return
        month_changed = False
        self.process_world_week()
        self.week += 1
        if self.week <= 4:
            if hasattr(self, "run_automatic_save_cycle"):
                self.run_automatic_save_cycle(month_changed=False)
            self.refresh_all()
            self.write_log()
            self.prompt_due_event()
            return
        self.week = 1
        old_year = 2026 + (self.month - 1) // 12
        self.month += 1
        month_changed = True
        new_year = 2026 + (self.month - 1) // 12
        self.process_world_month(player_ran_show=False)
        if new_year != old_year:
            self.run_end_of_year_awards(old_year)
            self.age_world_one_year()
        if not getattr(self, "spectator_mode", False):
            for fighter in self.roster:
                fighter.morale = max(10, fighter.morale - 2)
            payroll = sum(s["salary"] for s in self.staff)
            overhead = self.finance["monthly_office"] + payroll
            self.cash -= overhead
            self.record_finance_transaction("Monthly office and payroll", costs=overhead)
            self.tick_business_deals()
            self.finance["ledger"].insert(0, f"Month {self.month}: Monthly overhead ${overhead:,} (office ${self.finance['monthly_office']:,}, payroll ${payroll:,})")
            self.event_log.insert(0, f"Month {self.month}: overhead paid. Injured fighters recovered one month.")
        if hasattr(self, "run_automatic_save_cycle"):
            self.run_automatic_save_cycle(month_changed=month_changed)
        self.refresh_all()
        self.write_log()
        self.prompt_due_event()

    def process_world_week(self):
        self.process_scouting_reports()
        self.process_academy_week()
        self.process_pending_rebookings()
        self.fluctuate_region_interest()
        self.random_fighter_events()
        self.generate_weekly_world_activity()
        self.process_rivalry_activity()
        self.simulate_ai_staff_market()
        for promo in self.promotions:
            if self.ai_should_run_show(promo):
                self.simulate_ai_promotion_month(promo)
        for _ in range(self.independent_showcases_due()):
            self.simulate_free_agent_showcases()
        if random.random() < 0.22:
            self.market_churn()
        if random.random() < 0.18:
            self.simulate_nonexclusive_outside_fights()
        if not getattr(self, "spectator_mode", False):
            self.close_finance_week()
        self.news = self.news[:160]

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
            "owned": False, "level": 0, "capacity": 0, "prospects": [], "talent_pool": [],
            "weekly_cost": 0, "auto_train": True, "network_weeks": 0, "network_active": False,
            "network_region": "", "network_scout": "", "network_scout_skill": 0,
            "showcase_weeks": 2, "auto_showcases": True, "last_scout_report": "",
        }

    def repair_academy(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        for key, value in self.academy_defaults().items():
            academy.setdefault(key, value if not isinstance(value, list) else [])
        if academy.get("owned"):
            academy["capacity"] = max(8, academy.get("capacity", 8))
            academy["weekly_cost"] = max(4500, academy.get("weekly_cost", 4500))
        for prospect in academy.get("prospects", []) + academy.get("talent_pool", []):
            self.repair_academy_prospect(prospect)
        return academy

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
        return round(base * (1 + distance * 0.42))

    def academy_scout_range(self, value, confidence, minimum=1, maximum=99):
        spread = max(2, round((100 - confidence) / 7))
        low = max(minimum, value - random.randint(max(1, spread // 2), spread))
        high = min(maximum, value + random.randint(max(1, spread // 2), spread + 2))
        return low, high

    def academy_skill_defaults(self, prospect):
        rating = prospect.get("rating", 42)
        for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq"):
            prospect.setdefault(key, max(20, min(95, rating + random.randint(-8, 8))))
        return prospect

    def repair_academy_prospect(self, prospect):
        prospect.setdefault("name", "Unknown Prospect")
        prospect.setdefault("age", random.randint(12, 15))
        prospect.setdefault("potential", random.randint(62, 92))
        prospect.setdefault("rating", random.randint(38, 54))
        prospect.setdefault("region", self.player_region)
        prospect.setdefault("gender", "Male")
        prospect.setdefault("weight", random.choice(WEIGHTS))
        prospect.setdefault("amateur_weight", self.academy_weight_band(prospect.get("weight", "Lightweight")))
        prospect.setdefault("plan", "Automatic")
        prospect.setdefault("amateur_w", 0); prospect.setdefault("amateur_l", 0); prospect.setdefault("amateur_d", 0)
        prospect.setdefault("amateur_history", [])
        prospect.setdefault("weeks", 0); prospect.setdefault("development", 0)
        prospect.setdefault("fatigue", 0); prospect.setdefault("injured", 0)
        prospect.setdefault("weeks_to_sign", random.randint(2, 3))
        prospect.setdefault("scout_confidence", 45)
        self.academy_skill_defaults(prospect)
        prospect.setdefault("current_range", self.academy_scout_range(prospect["rating"], prospect["scout_confidence"], 20, 99))
        prospect.setdefault("potential_range", self.academy_scout_range(prospect["potential"], prospect["scout_confidence"], 45, 99))
        prospect["signing_cost"] = prospect.get("signing_cost") or self.academy_signing_cost(prospect)
        return prospect

    def create_academy_scout_prospect(self, scout_score=45, region=None):
        region = region or self.player_region
        fighter = self.create_generated_fighter(0, 4, 32, 53, region=region)
        fighter.age = random.randint(12, 15)
        confidence = max(30, min(94, round(scout_score + random.randint(-12, 10))))
        prospect = {
            "name": fighter.name, "age": fighter.age, "potential": random.randint(max(62, fighter.overall + 12), 96),
            "region": region, "gender": fighter.gender, "weight": fighter.weight,
            "amateur_weight": self.academy_weight_band(fighter.weight), "rating": fighter.overall,
            "style": fighter.style, "nationality": fighter.nationality, "birth_country": fighter.birth_country,
            "birth_region": fighter.birth_region, "hometown": fighter.hometown, "residence": fighter.residence,
            "training_location": fighter.training_location, "fighting_base": fighter.fighting_base,
            "cultural_connections": fighter.cultural_connections, "regional_popularity": fighter.regional_popularity,
            "scout_confidence": confidence, "weeks_to_sign": random.randint(2, 3),
            "striking": fighter.striking, "wrestling": fighter.wrestling, "grappling": fighter.grappling,
            "cardio": fighter.cardio, "chin": fighter.chin, "power": fighter.power,
            "toughness": fighter.toughness, "fight_iq": fighter.fight_iq,
        }
        return self.repair_academy_prospect(prospect)

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
        cost = self.academy_scouting_network_cost(region)
        if self.cash < cost:
            return False, f"Need ${cost:,} to establish a {region} youth scouting network."
        scout = next((member for member in self.staff if member.get("name") == scout_name), None)
        scout_skill = scout.get("fighter_judging", scout.get("skill", 45)) if scout else self.staff_skill("Scout")
        self.cash -= cost
        self.record_finance_transaction(f"Academy scouting network: {region}", costs=cost)
        academy.update({"network_weeks": 8, "network_active": False, "network_region": region, "network_scout": scout_name or "Scout", "network_scout_skill": round(scout_skill), "talent_pool": []})
        academy["last_scout_report"] = f"{academy['network_scout']} is setting up a {region} youth network. Setup takes 8 weeks."
        return True, academy["last_scout_report"]

    def cancel_academy_network(self):
        academy = self.repair_academy(getattr(self, "academy", {}))
        if not academy.get("network_active") and academy.get("network_weeks", 0) <= 0:
            return False, "There is no youth scouting network to cancel."
        region = academy.get("network_region") or "regional"
        lead_count = len(academy.get("talent_pool", []))
        academy.update({"network_weeks": 0, "network_active": False, "network_region": "", "network_scout": "", "network_scout_skill": 0, "talent_pool": []})
        academy["last_scout_report"] = f"Cancelled the {region} youth network. {lead_count} open lead(s) were removed."
        return True, academy["last_scout_report"]

    def academy_training_fields(self, plan, prospect=None):
        if plan == "Automatic" and prospect:
            weak = sorted(("striking", "wrestling", "grappling", "cardio", "fight_iq"), key=lambda key: prospect.get(key, 45))[:2]
            return tuple(dict.fromkeys(weak + ["cardio", "striking"]))
        return {
            "Balanced": ("striking", "wrestling", "grappling", "cardio", "fight_iq"),
            "Boxing": ("striking", "power", "chin"), "Muay Thai": ("striking", "power", "toughness"),
            "Wrestling": ("wrestling", "cardio", "fight_iq"), "BJJ": ("grappling", "fight_iq", "toughness"),
            "Judo": ("wrestling", "grappling", "fight_iq"), "Sambo": ("wrestling", "grappling", "power"),
            "Clinch": ("wrestling", "striking", "toughness"), "Cardio": ("cardio", "toughness"),
            "Strength": ("power", "toughness", "chin"), "Fight IQ": ("fight_iq", "cardio"),
        }.get(plan, ("striking", "wrestling", "grappling"))

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

    def train_academy_prospect(self, prospect, academy):
        self.repair_academy_prospect(prospect)
        prospect["weeks"] = prospect.get("weeks", 0) + 1
        if prospect.get("injured", 0):
            prospect["injured"] = max(0, prospect.get("injured", 0) - 1)
            return
        prospect["fatigue"] = max(0, prospect.get("fatigue", 0) - random.randint(4, 9))
        if not academy.get("auto_train", True):
            return
        fields = self.academy_training_fields(prospect.get("plan", "Automatic"), prospect)
        facility = academy.get("level", 1) * 5 + self.staff_skill("Trainer") * 0.25 + self.staff_skill("Scout") * 0.12
        if random.random() < min(0.42, 0.09 + facility / 360):
            field = random.choice(fields)
            prospect[field] = min(99, prospect.get(field, prospect.get("rating", 40)) + 1)
            prospect["development"] = prospect.get("development", 0) + 1
        if prospect.get("weeks", 0) % 5 == 0 and prospect.get("rating", 40) < prospect.get("potential", 70):
            self.recalculate_academy_rating(prospect)

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
        gains = 2 if won else 1
        for _ in range(gains):
            field = random.choice(fields)
            prospect[field] = min(99, prospect.get(field, 45) + 1)
            prospect["development"] = prospect.get("development", 0) + 1
        prospect["fatigue"] = min(100, prospect.get("fatigue", 0) + random.randint(10, 22))
        if random.random() < 0.025:
            prospect["injured"] = max(prospect.get("injured", 0), random.randint(1, 3))
        self.recalculate_academy_rating(prospect)

    def academy_prospect_to_fighter(self, prospect):
        self.repair_academy_prospect(prospect)
        fighter = self.create_generated_fighter(2, 14, max(35, prospect["rating"] - 6), min(86, prospect["rating"] + 6), weight=prospect["weight"], gender=prospect["gender"], region=prospect["region"])
        fighter.name = prospect["name"]; fighter.age = prospect["age"]; fighter.potential = prospect["potential"]
        fighter.record_w = fighter.record_l = fighter.record_d = 0
        for key in ("striking", "wrestling", "grappling", "cardio", "chin", "power", "toughness", "fight_iq"):
            setattr(fighter, key, max(1, min(99, prospect.get(key, getattr(fighter, key, 50)))))
        for key in ("nationality", "birth_country", "birth_region", "hometown", "residence", "training_location", "fighting_base", "cultural_connections", "regional_popularity"):
            if key in prospect:
                setattr(fighter, key, prospect[key])
        fighter.fight_history = list(prospect.get("amateur_history", [])) + ["Promoted from the Fighting Academy."]
        fighter.contract_months = 24
        fighter.rank_score = self.rank_value(fighter)
        return fighter

    def promote_academy_prospect_to_sport(self, prospect, sport):
        fighter = self.academy_prospect_to_fighter(prospect)
        if sport == "MMA":
            self.roster.append(fighter)
            return True, f"Academy graduate: {fighter.name} joined {self.player_company_name}.", fighter
        ok, division = self.open_player_combat_division(sport)
        if not ok:
            return False, division, None
        world = self.combat_sport_worlds.get(sport)
        fighter.primary_discipline = sport if sport != "Brazilian Jiu-Jitsu" else "Brazilian Jiu-Jitsu"
        fighter.sport_employer = self.player_company_name
        fighter.contract_type = f"{sport} Developmental"
        fighter.multi_sport_records = fighter.multi_sport_records or {}
        fighter.multi_sport_records[sport] = "0-0-0"
        fighter.crossover_history = fighter.crossover_history or []
        fighter.crossover_history.append(f"Month {self.month}: Graduated from {self.player_company_name}'s academy into {sport}.")
        world["roster"].append(fighter)
        division["roster"] = list(dict.fromkeys(division.get("roster", []) + [fighter.name]))
        return True, f"Academy graduate: {fighter.name} joined {self.player_company_name}'s {sport} division.", fighter

    def simulate_academy_amateur_bout(self, a, b, label):
        a_score = a.get("rating", 40) + a.get("fight_iq", 40) * 0.12 + random.randint(-14, 14)
        b_score = b.get("rating", 40) + b.get("fight_iq", 40) * 0.12 + random.randint(-14, 14)
        if abs(a_score - b_score) <= 2 and random.random() < 0.16:
            a["amateur_d"] += 1; b["amateur_d"] += 1
            method = "Draw"
            line = f"{a['name']} vs {b['name']} ended in a draw ({label})."
            a["amateur_history"].insert(0, line); b["amateur_history"].insert(0, line)
            self.apply_academy_bout_development(a, method, False); self.apply_academy_bout_development(b, method, False)
            return line
        winner, loser = (a, b) if a_score >= b_score else (b, a)
        method = random.choices(["Decision", "TKO", "Submission"], weights=[52, 28, 20], k=1)[0]
        winner["amateur_w"] += 1; loser["amateur_l"] += 1
        line = f"{winner['name']} def. {loser['name']} by {method} ({label} Academy Showcase)."
        winner["amateur_history"].insert(0, line); loser["amateur_history"].insert(0, line)
        self.apply_academy_bout_development(winner, method, True); self.apply_academy_bout_development(loser, method, False)
        return line

    def academy_amateur_fight_count(self, prospect):
        return prospect.get("amateur_w", 0) + prospect.get("amateur_l", 0) + prospect.get("amateur_d", 0)

    def choose_academy_showcase_card(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        ready = [item for item in academy.get("prospects", []) if not item.get("injured", 0) and item.get("fatigue", 0) < 70]
        ready.sort(key=lambda item: (self.academy_amateur_fight_count(item), item.get("fatigue", 0), random.random()))
        bouts, used = [], set()
        for a in ready:
            if a["name"] in used:
                continue
            candidates = [b for b in ready if b["name"] not in used and b["name"] != a["name"] and b.get("gender") == a.get("gender")]
            same_weight = [b for b in candidates if b.get("amateur_weight") == a.get("amateur_weight")]
            pool = same_weight or candidates
            if not pool:
                continue
            b = min(pool, key=lambda item: abs(item.get("rating", 40) - a.get("rating", 40)) + abs(self.academy_amateur_fight_count(item) - self.academy_amateur_fight_count(a)))
            label = a.get("amateur_weight", "Youth Openweight") if b in same_weight else "Open Youth"
            bouts.append((a, b, label)); used.update([a["name"], b["name"]])
        return bouts

    def run_academy_showcase_card(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        return [self.simulate_academy_amateur_bout(a, b, label) for a, b, label in self.choose_academy_showcase_card(academy)]

    def run_academy_showcase_if_due(self, academy=None):
        academy = academy or getattr(self, "academy", {})
        if not academy.get("owned") or not academy.get("auto_showcases", True):
            return None
        academy["showcase_weeks"] = max(0, academy.get("showcase_weeks", 2) - 1)
        if academy["showcase_weeks"] > 0:
            return None
        results = self.run_academy_showcase_card(academy)
        academy["showcase_weeks"] = 2 if results else 1
        academy["last_scout_report"] = f"Bi-weekly academy showcase: {len(results)} bout(s). {results[0] if results else 'Delayed: two eligible same-gender prospects are needed.'}"
        if results:
            self.news.insert(0, academy["last_scout_report"])
        return academy["last_scout_report"]

    def process_academy_week(self):
        academy = self.repair_academy(getattr(self, "academy", {}))
        if not academy.get("owned"):
            return
        self.cash -= academy.get("weekly_cost", 0)
        self.record_finance_transaction("Academy operating costs", costs=academy.get("weekly_cost", 0))
        for prospect in academy.get("prospects", []):
            self.train_academy_prospect(prospect, academy)
        for prospect in list(academy.get("talent_pool", [])):
            prospect["weeks_to_sign"] = prospect.get("weeks_to_sign", 2) - 1
            if prospect["weeks_to_sign"] < 0:
                academy["talent_pool"].remove(prospect)
        if academy.get("network_weeks", 0) > 0:
            academy["network_weeks"] -= 1
            if academy["network_weeks"] <= 0:
                academy["network_active"] = True
                academy["last_scout_report"] = f"{academy.get('network_scout', 'Scout')} established a youth scouting network in {academy.get('network_region', self.player_region)}."
                self.inbox.append({"subject": "Academy Network Ready", "body": academy["last_scout_report"], "type": "Scouting", "resolved": False})
        if academy.get("network_active") and len(academy.get("talent_pool", [])) < 8:
            open_slots = max(0, 8 - len(academy.get("talent_pool", [])))
            lead_chance = 0.32 + academy.get("network_scout_skill", self.staff_skill("Scout")) / 220
            added = 0
            for _ in range(open_slots):
                if random.random() < lead_chance:
                    academy["talent_pool"].append(self.create_academy_scout_prospect(academy.get("network_scout_skill", 45), region=academy.get("network_region", self.player_region)))
                    added += 1
            if added:
                academy["last_scout_report"] = f"{academy.get('network_region', self.player_region)} network produced {added} youth lead(s). Leads expire after 2-3 weeks."
        self.run_academy_showcase_if_due(academy)

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

    def process_world_month(self, player_ran_show):
        self.age_and_develop_fighters(self.roster, player_roster=True)
        for promo in self.promotions:
            self.age_and_develop_fighters(promo.roster)
            if getattr(promo, "is_regional_feeder", False):
                self.simulate_regional_feeder_month(promo)
            elif random.random() < self.ai_show_chance(promo) * 0.65:
                self.simulate_ai_promotion_month(promo, develop=False)
        self.process_career_goals()
        self.process_combat_sport_worlds()
        self.simulate_nonexclusive_outside_fights()
        self.advance_free_agent_market()
        self.market_churn()
        self.apply_ai_operating_costs()
        self.process_promotion_failures()
        self.review_ai_executives()
        self.ensure_world_fighter_target()
        self.update_world_metric_interactions()
        self.check_contract_warnings()
        self.review_contract_promises()
        self.auto_renew_player_contracts()
        self.update_contracts()
        self.update_ai_contracts()
        self.process_retirements()
        self.refresh_promotion_rankings()
        if not player_ran_show and not getattr(self, "spectator_mode", False):
            self.company_pop = max(1, self.company_pop - 1)
            self.news.insert(0, f"{self.player_company_name} stayed quiet this month; fans drifted toward other shows.")
        self.news = self.news[:120]

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
        if sport == "Boxing":
            return fighter.striking * 1.25 + fighter.power * 0.42 + fighter.chin * 0.28 + fighter.cardio * 0.24 + fighter.fight_iq * 0.22
        if sport in ("Kickboxing", "Muay Thai"):
            return fighter.striking * 1.12 + fighter.power * 0.36 + fighter.toughness * 0.28 + fighter.cardio * 0.24 + fighter.fight_iq * 0.20
        if sport == "Wrestling":
            return fighter.wrestling * 1.35 + fighter.ground_control * 0.42 + fighter.cardio * 0.30 + fighter.toughness * 0.20 + fighter.fight_iq * 0.22
        if sport == "Brazilian Jiu-Jitsu":
            return fighter.grappling * 1.30 + fighter.submissions * 0.46 + fighter.ground_control * 0.30 + fighter.cardio * 0.20 + fighter.fight_iq * 0.24
        if getattr(fighter, "primary_discipline", "") == "Lethwei":
            return fighter.striking * 1.12 + fighter.power * 0.44 + fighter.toughness * 0.40 + fighter.cardio * 0.20 + fighter.fight_iq * 0.16
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

    def refresh_combat_sport_rankings(self, sport, world, employer=None, division=None):
        ranked = self.combat_sport_ranked(sport, employer)
        names = [fighter.name for fighter in ranked[:15]]
        if division is not None:
            division["rankings"] = names[:10]
            if division.get("champion") not in names:
                division["champion"] = names[0] if names else ""
        else:
            world["rankings"] = names
            if world.get("champion") not in names:
                world["champion"] = names[0] if names else ""
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
        elif world.get("champion") and random.random() < 0.18:
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
            defense = ds(fighter, "head_movement", fighter.striking) * 0.26 + ds(fighter, "guard", fighter.striking) * 0.24 + ds(fighter, "footwork", fighter.striking) * 0.18 + fighter.chin * 0.18 + fighter.fight_iq * 0.14
            finishing = fighter.power * 0.42 + ds(fighter, "punch_power", fighter.power) * 0.32 + fighter.finishing_instinct * 0.20 + ds(fighter, "killer_instinct", fighter.finishing_instinct) * 0.06
            return attack, defense, finishing
        if sport in ("Kickboxing", "Muay Thai"):
            clinch_bonus = 0.16 if sport == "Muay Thai" or getattr(fighter, "primary_discipline", "") == "Lethwei" else 0.05
            attack = ds(fighter, "punch_technique", fighter.striking) * 0.18 + ds(fighter, "kick_technique", fighter.striking) * 0.22 + ds(fighter, "low_kick_technique", fighter.striking) * 0.15 + ds(fighter, "knees", fighter.striking) * clinch_bonus + fighter.power * 0.20 + fighter.fight_iq * 0.10
            defense = ds(fighter, "guard", fighter.striking) * 0.18 + ds(fighter, "kick_defence", fighter.striking) * 0.22 + ds(fighter, "footwork", fighter.striking) * 0.16 + fighter.chin * 0.18 + fighter.toughness * 0.14 + fighter.fight_iq * 0.12
            finishing = fighter.power * 0.34 + ds(fighter, "kick_power", fighter.power) * 0.24 + ds(fighter, "knees", fighter.striking) * 0.14 + fighter.finishing_instinct * 0.20 + fighter.toughness * 0.08
            return attack, defense, finishing
        if sport == "Wrestling":
            attack = ds(fighter, "takedowns", fighter.wrestling) * 0.30 + ds(fighter, "takedown_setup", fighter.wrestling) * 0.18 + ds(fighter, "chain_wrestling", fighter.wrestling) * 0.22 + ds(fighter, "ride_control", fighter.ground_control) * 0.14 + fighter.cardio * 0.10 + fighter.fight_iq * 0.06
            defense = ds(fighter, "sprawl", fighter.wrestling) * 0.24 + ds(fighter, "takedown_defence_detail", fighter.takedown_defence) * 0.22 + ds(fighter, "get_ups", fighter.wrestling) * 0.16 + ds(fighter, "balance", fighter.wrestling) * 0.12 + fighter.cardio * 0.14 + fighter.toughness * 0.12
            finishing = ds(fighter, "slams", fighter.wrestling) * 0.16 + ds(fighter, "ride_control", fighter.ground_control) * 0.24 + ds(fighter, "top_control", fighter.ground_control) * 0.22 + fighter.strength * 0.18 + fighter.fight_iq * 0.20 if hasattr(fighter, "strength") else fighter.wrestling
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
            return {"rounds": 10 if title else 6, "finish": "KO/TKO", "decision": "Decision", "draws": True, "fatigue": 3.0}
        if sport == "Kickboxing":
            return {"rounds": 5 if title else 3, "finish": "KO/TKO", "decision": "Decision", "draws": True, "fatigue": 4.0}
        if sport == "Muay Thai":
            return {"rounds": 5, "finish": "KO" if lethwei else "KO/TKO", "decision": "Draw" if lethwei else "Decision", "draws": True, "fatigue": 4.2}
        if sport == "Wrestling":
            return {"rounds": 3, "finish": "Pin", "decision": "Points", "draws": False, "fatigue": 3.4}
        if sport == "Brazilian Jiu-Jitsu":
            return {"rounds": 1, "finish": "Submission", "decision": "Points", "draws": False, "fatigue": 3.2}
        return {"rounds": 3, "finish": "Finish", "decision": "Decision", "draws": True, "fatigue": 3.5}

    def simulate_combat_sport_bout(self, sport, a, b, title=False):
        rules = self.combat_sport_bout_rules(sport, title=title, a=a, b=b)
        a_attack, a_defense, a_finish = self.combat_sport_skill_set(sport, a)
        b_attack, b_defense, b_finish = self.combat_sport_skill_set(sport, b)
        a_points = b_points = 0
        a_rounds = b_rounds = 0
        a_damage = b_damage = 0
        a_stamina = max(18, a.cardio - a.fatigue * 0.35)
        b_stamina = max(18, b.cardio - b.fatigue * 0.35)
        log = []
        round_scores = []
        winner = loser = None
        method = rules["decision"]
        end_round = rules["rounds"]

        for round_no in range(1, rules["rounds"] + 1):
            a_energy = a_stamina - (round_no - 1) * rules["fatigue"] + random.uniform(-5, 5)
            b_energy = b_stamina - (round_no - 1) * rules["fatigue"] + random.uniform(-5, 5)
            a_perf = a_attack + a.momentum * 2.6 + a_energy * 0.20 - b_defense * 0.42 + random.gauss(0, 10)
            b_perf = b_attack + b.momentum * 2.6 + b_energy * 0.20 - a_defense * 0.42 + random.gauss(0, 10)

            if sport == "Wrestling":
                a_rp = max(0, round((a_perf - b_perf) / 12 + random.choice([0, 1, 2])))
                b_rp = max(0, round((b_perf - a_perf) / 12 + random.choice([0, 1, 2])))
                if a_rp == b_rp:
                    a_rp += 1 if a_perf >= b_perf else 0
                    b_rp += 1 if b_perf > a_perf else 0
                a_points += a_rp
                b_points += b_rp
                margin = a_rp - b_rp
                log.append(f"R{round_no}: {a.name} {a_rp}, {b.name} {b_rp} - {'chain attacks and top control' if margin > 0 else 'scrambles and counters' if margin < 0 else 'even hand-fighting'}.")
                if abs(a_points - b_points) >= 15 and round_no >= 2:
                    winner, loser = (a, b) if a_points > b_points else (b, a)
                    method = "Technical Fall"
                    end_round = round_no
                    break
                pin_chance = max(0.01, min(0.22, (max(a_finish - b_defense, b_finish - a_defense) - 10) / 190))
                if random.random() < pin_chance:
                    winner, loser = (a, b) if a_perf + a_finish >= b_perf + b_finish else (b, a)
                    method = "Pin"
                    end_round = round_no
                    break
            elif sport == "Brazilian Jiu-Jitsu":
                a_rp = max(0, round((a_perf - b_perf) / 10 + random.choice([0, 2, 2, 3])))
                b_rp = max(0, round((b_perf - a_perf) / 10 + random.choice([0, 2, 2, 3])))
                a_points += a_rp
                b_points += b_rp
                sub_a = max(0.02, min(0.58, (a_finish - b_defense + a_perf - b_perf + 20) / 175))
                sub_b = max(0.02, min(0.58, (b_finish - a_defense + b_perf - a_perf + 20) / 175))
                log.append(f"R{round_no}: {a.name} {a_rp}, {b.name} {b_rp} - guard passes, sweeps and submission threats decide the grappling exchanges.")
                if random.random() < max(sub_a, sub_b):
                    winner, loser = (a, b) if sub_a >= sub_b else (b, a)
                    method = "Submission"
                    end_round = round_no
                    break
            else:
                margin = a_perf - b_perf
                round_winner = a if margin >= 0 else b
                if round_winner is a:
                    a_rounds += 1
                    a_score, b_score = (10, 8) if margin > 26 and random.random() < 0.28 else (10, 9)
                else:
                    b_rounds += 1
                    a_score, b_score = (8, 10) if margin < -26 and random.random() < 0.28 else (9, 10)
                round_scores.append((a_score, b_score))
                damage_a = max(0, (b_perf + b_finish * 0.34 - a_defense) / 28)
                damage_b = max(0, (a_perf + a_finish * 0.34 - b_defense) / 28)
                a_damage += damage_a
                b_damage += damage_b
                action = "boxing combinations" if sport == "Boxing" else "kicks, knees and clinch exchanges" if sport == "Muay Thai" else "kicks and punch combinations"
                log.append(f"R{round_no}: {round_winner.name} edges the round with cleaner {action}. Scores {a.name} {a_score}-{b_score} {b.name}.")
                finish_a = max(0.005, min(0.44, (a_finish - b.chin + b_damage * 5 + max(0, margin)) / 230))
                finish_b = max(0.005, min(0.44, (b_finish - a.chin + a_damage * 5 + max(0, -margin)) / 230))
                if random.random() < max(finish_a, finish_b):
                    winner, loser = (a, b) if finish_a >= finish_b else (b, a)
                    method = rules["finish"]
                    end_round = round_no
                    log.append(f"R{round_no}: {winner.name} forces the stoppage after cumulative damage and a clean finishing sequence.")
                    break

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
                if a_total == b_total or (close and rules["draws"] and random.random() < (0.18 if sport == "Muay Thai" else 0.07)):
                    method = "Draw"
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
        return {"winner": winner, "loser": loser, "method": method, "round": end_round, "score": score_text, "log": log}

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

    def apply_combat_sport_result(self, sport, world, a, b, title=False, player_owned=False):
        sim = self.simulate_combat_sport_bout(sport, a, b, title=title)
        winner, loser, method = sim.get("winner"), sim.get("loser"), sim.get("method", "Decision")
        if method == "Draw" or not winner:
            a.record_d += 1
            b.record_d += 1
            result_line = f"Month {self.month}: {a.name} and {b.name} fought to a draw in {sport} ({sim.get('score', '-')})"
        else:
            winner.record_w += 1
            loser.record_l += 1
            winner.momentum = min(5, winner.momentum + 1)
            loser.momentum = max(-5, loser.momentum - 1)
            finished = method not in ("Decision", "Points", "Referee Criteria")
            winner.popularity = min(100, winner.popularity + (2 if title else 1) + int(finished))
            loser.popularity = max(1, loser.popularity - (1 if loser.popularity > winner.popularity + 12 else 0))
            if title:
                world["champion"] = winner.name
                winner.title_wins += 1 if not getattr(winner, "champion", False) else 0
                winner.title_defenses += 1 if getattr(winner, "champion", False) else 0
                for fighter in world.get("roster", []):
                    if fighter.sport_employer == winner.sport_employer:
                        fighter.champion = fighter is winner
            round_note = f" R{sim.get('round')}" if method not in ("Decision", "Points", "Referee Criteria") else ""
            result_line = f"Month {self.month}: {winner.name} def. {loser.name} by {method}{round_note} in {sport} ({sim.get('score', '-')})"
        for fighter in (a, b):
            fighter.multi_sport_records = fighter.multi_sport_records or {}
            fighter.multi_sport_records[getattr(fighter, "primary_discipline", sport)] = f"{fighter.record_w}-{fighter.record_l}-{fighter.record_d}"
            fighter.fight_history = fighter.fight_history or []
            fighter.fight_history.insert(0, result_line)
            fighter.last_fight = result_line
            fighter.last_fight_month = self.month
            fighter.fatigue = min(100, fighter.fatigue + random.randint(12, 32))
            if random.random() < 0.025 + fighter.injury_proneness / 1400:
                fighter.injured = max(fighter.injured, random.randint(1, 3))
            self.develop_after_combat_sport_bout(sport, fighter, won=(winner is fighter), finished=method not in ("Decision", "Points", "Draw", "Referee Criteria"))
        return {"a": a.name, "b": b.name, "winner": winner.name if winner else "Draw", "method": method, "round": sim.get("round"), "score": sim.get("score", "-"), "title": title, "result": result_line, "log": sim.get("log", [])}

    def build_combat_sport_card(self, sport, world, employer, player_owned=False, target_bouts=6, champion_name=None):
        ranked = self.refresh_combat_sport_rankings(sport, world, employer=employer)
        available = [fighter for fighter in ranked if fighter.fatigue < 55 and not fighter.injured]
        if len(available) < 2:
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
        champion_name = champion_name if champion_name is not None else world.get("champion", "")
        champion = next((fighter for fighter in available if fighter.name == champion_name), None)
        if champion and champion.name not in used and card_strategy != "Prospect Rotation":
            challengers = [fighter for fighter in available if fighter is not champion and fighter.name not in used]
            if challengers:
                challenger = min(challengers[:8], key=lambda fighter: abs(self.combat_sport_rating(fighter, sport) - self.combat_sport_rating(champion, sport)))
                bouts.append({"a": champion, "b": challenger, "title": True, "main": True, "booking_reason": f"{card_strategy}: champion vs closest top contender"})
                used.update([champion.name, challenger.name])

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
            key=lambda fighter: (self.combat_sport_inactivity_months(fighter) if card_strategy == "Deep Roster" else 0, fighter.age <= 27, fighter.potential - fighter.overall),
            reverse=True,
        )
        fallback_pool = sorted(
            [fighter for fighter in available if fighter.name not in used],
            key=lambda fighter: (self.combat_sport_inactivity_months(fighter), random.random()),
            reverse=True,
        )
        for fighter in card_pool + fallback_pool:
            if len(bouts) >= target_bouts or fighter.name in used:
                continue
            opponent_pool = [
                other for other in available
                if other.name not in used and other is not fighter
                and other.gender == fighter.gender
                and abs(self.combat_sport_rating(other, sport) - self.combat_sport_rating(fighter, sport)) <= (30 if fighter.age <= 25 else 44)
            ]
            if not opponent_pool and self.combat_sport_inactivity_months(fighter) >= 8:
                opponent_pool = [
                    other for other in available
                    if other.name not in used and other is not fighter
                    and other.gender == fighter.gender
                    and abs(self.combat_sport_rating(other, sport) - self.combat_sport_rating(fighter, sport)) <= 60
                ]
            if not opponent_pool:
                continue
            opponent = min(opponent_pool, key=lambda other: (
                abs(self.combat_sport_rating(other, sport) - self.combat_sport_rating(fighter, sport)),
                -self.combat_sport_inactivity_months(other),
                abs(other.record_w + other.record_l - fighter.record_w - fighter.record_l),
            ))
            reason = "Activity rotation" if self.combat_sport_inactivity_months(fighter) >= 5 or self.combat_sport_inactivity_months(opponent) >= 5 else "Style/ranking matchup"
            if card_strategy == "Prospect Rotation" and (fighter.age <= 27 or opponent.age <= 27):
                reason = "Prospect rotation"
            bouts.append({"a": fighter, "b": opponent, "title": False, "main": not bouts, "booking_reason": reason})
            used.update([fighter.name, opponent.name])
        return bouts

    def run_combat_sport_card(self, sport, world, employer, player_owned=False, target_bouts=6):
        division = getattr(self, "player_combat_divisions", {}).get(sport) if player_owned else None
        champion_name = division.get("champion", "") if division else None
        if player_owned and division:
            target_bouts = {"Prospect Builder": 6, "Star Showcase": 4, "Title Focus": 5}.get(division.get("strategy", "Balanced"), target_bouts)
        bouts = self.build_combat_sport_card(sport, world, employer, player_owned=player_owned, target_bouts=target_bouts, champion_name=champion_name)
        if not bouts:
            return None
        event_no = world.get("events", 0) + 1
        world["events"] = event_no
        promotion = self.player_company_name if player_owned else world.get("promotion", employer)
        original_champion = world.get("champion", "")
        if player_owned and division:
            world["champion"] = division.get("champion", "")
        results = [self.apply_combat_sport_result(sport, world, bout["a"], bout["b"], title=bout.get("title", False), player_owned=player_owned) for bout in bouts]
        title_result = next((item for item in results if item.get("title")), None)
        finishes = sum(1 for item in results if item.get("method") not in ("Decision", "Points", "Draw"))
        headline = f"Month {self.month}: {promotion} ran a {sport} card headlined by {results[0]['result']}."
        strategy = self.combat_sport_card_strategy(sport, world, employer, player_owned)
        recap = f"{len(results)} bouts | {finishes} finish(es) | Strategy: {strategy}"
        if title_result:
            recap += f" | Title: {title_result['result']}"
        card = {"month": self.month, "week": self.week, "sport": sport, "promotion": promotion, "event": event_no, "results": results, "headline": headline, "recap": recap, "strategy": strategy, "bouts": [{"a": bout["a"].name, "b": bout["b"].name, "title": bout.get("title", False), "reason": bout.get("booking_reason", "Sport matchmaking")} for bout in bouts]}
        world["event_history"] = ([headline] + world.get("event_history", []))[:80]
        world["media"] = ([headline] + world.get("media", []))[:24]
        self.refresh_combat_sport_rankings(sport, world, employer=employer)
        if player_owned:
            divisions = getattr(self, "player_combat_divisions", {})
            division = divisions.get(sport)
            if division:
                revenue = sum(max(1200, fighter.popularity * 150 + fighter.overall * 60) for bout in bouts for fighter in (bout["a"], bout["b"]))
                cost = 18000 + len(bouts) * 2200 + sum(max(900, fighter.popularity * 95) for bout in bouts for fighter in (bout["a"], bout["b"]))
                profit = revenue - cost
                card["finance"] = {"revenue": revenue, "cost": cost, "profit": profit}
                division["events"] = ([card] + division.get("events", []))[:50]
                division["last_card_summary"] = f"{recap} | Revenue ${revenue:,} | Cost ${cost:,} | Profit ${profit:,}"
                division["revenue_total"] = division.get("revenue_total", 0) + revenue
                division["cost_total"] = division.get("cost_total", 0) + cost
                division["profit_total"] = division.get("profit_total", 0) + profit
                if results and results[0].get("title") and results[0].get("winner") != "Draw":
                    division["champion"] = results[0].get("winner", division.get("champion", ""))
                self.refresh_combat_sport_rankings(sport, world, employer=employer, division=division)
                self.cash = max(0, self.cash + profit)
                self.record_finance_transaction(f"{sport} child division card", revenue=revenue, costs=cost)
                self.news.insert(0, headline)
            world["champion"] = original_champion
        elif random.random() < 0.35:
            self.record_world_story("Combat Sports", headline, "\n".join(item["result"] for item in results[:6]), [promotion], [results[0]["a"], results[0]["b"]], importance=2)
        self.result_records.insert(0, {
            "date": f"Month {self.month} Week {self.week}",
            "company": promotion,
            "event": f"{sport} Card {event_no}",
            "summary": recap,
            "fights": len(results),
            "gate": "$0" if not player_owned else f"${card.get('finance', {}).get('revenue', 0):,}",
            "profit": "$0" if not player_owned else f"${card.get('finance', {}).get('profit', 0):,}",
            "log": [headline, recap, ""] + [item["result"] for item in results],
            "fight_logs": [{"fight": f"{item['a']} vs {item['b']}", "method": item.get("method", ""), "score": item.get("score", "-"), "lines": item.get("log", [])} for item in results],
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

    def process_combat_sport_worlds(self):
        """Run independent combat sports as real circuits with smart cards, records, and rare MMA crossovers."""
        worlds = getattr(self, "combat_sport_worlds", {}) or self.seed_combat_sport_worlds()
        for sport, world in worlds.items():
            promotion = world.get("promotion", "")
            roster = self.combat_sport_roster(sport)
            self.develop_combat_sport_roster(sport, roster)
            self.refresh_combat_sport_rankings(sport, world, employer=promotion)
            if random.random() < 0.82:
                target = min(max(8, len(self.combat_sport_roster(sport, promotion)) // 5), 12)
                self.run_combat_sport_card(sport, world, promotion, player_owned=False, target_bouts=random.randint(max(6, target - 2), target))
            if random.random() < 0.006:
                candidates = [fighter for fighter in self.combat_sport_ranked(sport, promotion)[4:24] if fighter.age <= 34 and fighter.fatigue < 45]
                if candidates:
                    fighter = random.choice(candidates)
                    fighter.sport_employer = ""
                    fighter.crossover_history = (fighter.crossover_history or [])[-9:] + [f"Month {self.month}: Left {world['promotion']} to pursue MMA."]
                    fighter.multi_sport_records = fighter.multi_sport_records or {}
                    fighter.multi_sport_records["MMA"] = "0-0-0"
                    fighter.record_w = fighter.record_l = fighter.record_d = 0
                    world["roster"].remove(fighter)
                    self.free_agents.append(fighter)
                    headline = f"CROSSOVER: Former {sport} standout {fighter.name} has entered the MMA free-agent market."
                    self.news.insert(0, headline)
                    self.record_world_story("Crossover", headline, fighter.crossover_history[-1], [world["promotion"]], [fighter.name], importance=4)
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
                "champion": signed[0].name if signed else "", "events": [], "records": {}, "awards": [], "hall_of_fame": [],
                "budget": startup_cost, "active": True, "strategy": "Balanced", "revenue_total": 0, "cost_total": startup_cost,
                "profit_total": -startup_cost, "last_card_summary": "No player card yet.", "title_name": f"{self.player_company_name} {sport} Championship",
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
                    should_retire = fighter.age >= 49 or random.random() < retirement_chance
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
        for fighter in pending[:10]:
            wait = self.retirement_fight_wait_months(fighter)
            threshold = 6 if fighter in self.free_agents else 12
            if wait < threshold or fighter.name in booked or fighter.injured:
                continue
            roster, company_name, region = self.retirement_fight_roster_for(fighter)
            if not roster:
                continue
            opponents = [
                candidate for candidate in roster
                if candidate is not fighter and not getattr(candidate, "retired", False) and not getattr(candidate, "retirement_pending", False)
                and not candidate.injured and candidate.fatigue < 70 and candidate.gender == fighter.gender
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

    def process_free_agent_retirements(self):
        """Free agency must not become a permanent retirement home for aging fighters."""
        for fighter in list(self.free_agents):
            if fighter.age < 38 or (self.month - 1) % 12 + 1 != self.retirement_review_month(fighter):
                continue
            age_pressure = max(0, fighter.age - 38) * 0.075
            inactivity = 0.12 + max(0, -fighter.momentum) * 0.035
            health = fighter.injury_proneness / 850 + max(0, fighter.fatigue - 45) / 420
            if fighter.age >= 47 or random.random() < min(0.88, age_pressure + inactivity + health):
                if not getattr(fighter, "retirement_pending", False):
                    self.mark_retirement_fight_required(fighter, "Free-agent retirement review")
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
                    opp = next((o for o in pool if o.name == fighter.rival and o.name not in used), None)
                    if opp:
                        used.update({fighter.name, opp.name})
                        fights.append({"a": fighter, "b": opp, "title": False, "main": False, "grudge": True, "booking_reason": "Active rivalry matchup"})

        # 3) Ranking-based pairings: adjacent-ranked contenders fight.
        # A signed blue-chip prospect gets a visible development opportunity,
        # even before their rank catches up with their ceiling.
        prospects = [fighter for fighter in ready if fighter.name not in used and fighter.age <= 29
                     and (fighter.potential >= 90 or (fighter.potential - fighter.overall >= 12 and fighter.potential >= 84))]
        prospects.sort(key=lambda fighter: (fighter.potential, fighter.overall, fighter.record_w - fighter.record_l), reverse=True)
        for prospect in prospects:
            if len(fights) >= target:
                break
            opponents = [fighter for fighter in ready if fighter.name not in used and fighter.name != prospect.name
                         and fighter.gender == prospect.gender and fighter.weight == prospect.weight]
            if not opponents:
                continue
            opponent = min(opponents, key=lambda fighter: abs(fighter.overall - prospect.overall) + abs((fighter.record_w + fighter.record_l) - (prospect.record_w + prospect.record_l)) * 0.25)
            used.update({prospect.name, opponent.name})
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
                a, b = available[0], available[1]
                if mode == "Prospect Rebuild" and a.age <= 26 and a.potential - a.overall >= 7:
                    protected = next((candidate for candidate in available[1:] if candidate.overall <= a.overall + 3), None)
                    if protected:
                        b = protected
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
        if promo.cash < projected_cost * 1.25:
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
        revenue = round(event_hype * promo.size * regional_pull * random.randint(85, 210) * revenue_factor)
        strategic_reinvestment = round(max(0, revenue - projected_cost) * (0.3 + promo.size / 320))
        event_profit = revenue - projected_cost - strategic_reinvestment
        promo.cash += event_profit
        margin = event_profit / max(1, projected_cost)
        stability_delta = 1 if margin >= 0.25 and promo.stability < 92 else (-1 if margin >= 0 else -3)
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
        self.refresh_promotion_rankings()
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
            if not fighter.ai_offer_company and not fighter.injured and fighter.age <= 33
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
        for fighters in groups.values():
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
        return 2

    def update_ai_contracts(self):
        for promo in [item for item in self.promotions if not getattr(item, "is_regional_feeder", False)]:
            for fighter in list(promo.roster):
                if fighter.contract_months > 0:
                    continue
                retain = fighter.champion or fighter.overall >= 75 or fighter.potential >= 86 or fighter.popularity >= 50
                if retain and promo.cash > max(180_000, promo.size * 9_000):
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

    def ai_roster_division_need(self, promo, fighter):
        count = len([member for member in promo.roster if member.gender == fighter.gender and member.weight == fighter.weight])
        target = 7 if promo.size >= 70 else 5
        return max(-8, (target - count) * 7)

    def ai_free_agent_value(self, promo, fighter):
        strategy = self.promotion_strategy(promo)
        division_need = self.ai_roster_division_need(promo, fighter)
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
        random.shuffle(eligible_promos)
        offers_created = 0
        # Blue chips do not disappear in the ordinary five-offer lottery.
        priority = sorted([fighter for fighter in self.free_agents if not fighter.retired and not fighter.injured and not fighter.ai_offer_company and self.is_blue_chip_prospect(fighter) and (getattr(self, "spectator_mode", False) or fighter.player_talent_window_until < self.month)], key=lambda fighter: (fighter.potential, fighter.overall, fighter.record_w - fighter.record_l, fighter.free_agent_months), reverse=True)
        for fighter in priority[:3]:
            options = sorted(eligible_promos, key=lambda promo: self.ai_free_agent_value(promo, fighter), reverse=True)
            promo = next((item for item in options if item.cash > max(90_000, item.size * 7200)), None)
            if not promo:
                continue
            purse, months, signing = self.ai_offer_terms(promo, fighter)
            purse = round(purse * 1.14 / 500) * 500
            signing = round(signing * 1.2 / 500) * 500
            if promo.cash < max(90_000, promo.size * 7200) + signing + purse * 2:
                continue
            fighter.ai_offer_company = promo.name
            fighter.ai_offer_purse = purse
            fighter.ai_offer_months = months
            fighter.ai_offer_signing_bonus = signing
            fighter.ai_offer_deadline_month = self.month + 1
            fighter.negotiation_heat = min(100, fighter.negotiation_heat + 16)
            offers_created += 1
        for promo in eligible_promos:
            if offers_created >= 8 or random.random() > (0.24 + promo.reputation_score / 420):
                continue
            candidates = [
                fighter for fighter in self.free_agents
                if not fighter.retired and not fighter.injured and not fighter.ai_offer_company
                and fighter.fatigue < 55 and fighter.age >= 18
                and (getattr(self, "spectator_mode", False) or fighter.player_talent_window_until < self.month)
            ]
            if not candidates:
                break
            candidates.sort(key=lambda fighter: self.ai_free_agent_value(promo, fighter), reverse=True)
            fighter = candidates[0]
            purse, months, signing = self.ai_offer_terms(promo, fighter)
            reserve = max(90_000, promo.size * 7200)
            commitment = signing + purse * 2
            if promo.cash < reserve + commitment:
                continue
            fighter.ai_offer_company = promo.name
            fighter.ai_offer_purse = purse
            fighter.ai_offer_months = months
            fighter.ai_offer_signing_bonus = signing
            fighter.ai_offer_deadline_month = self.month + 1
            fighter.negotiation_heat = min(100, fighter.negotiation_heat + 12)
            offers_created += 1
            self.news.insert(0, f"Contract market: {promo.name} offered {fighter.name} ${purse:,}/fight for {months} months. The offer is live until next month.")

    def resolve_ai_contract_offers(self):
        for fighter in list(self.free_agents):
            if not fighter.ai_offer_company or fighter.ai_offer_deadline_month > self.month:
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
            commitment = fighter.ai_offer_signing_bonus + fighter.ai_offer_purse * 2
            reserve = max(90_000, promo.size * 7200)
            if offer_score >= 64 and promo.cash >= reserve + commitment:
                self.free_agents.remove(fighter)
                promo.cash -= commitment
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
                self.news.insert(0, f"{promo.name} completed a negotiated signing with {fighter.name}: ${fighter.purse:,}/fight, {fighter.contract_months} months, ${commitment:,} committed up front.")
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
