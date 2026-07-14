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


class FightEngineMixin:
    def simulate_fight(self, a, b, fight):
        self.ensure_rule_defaults()
        max_rounds = self.rules["title_rounds"] if fight["main"] or fight["title"] else self.rules["rounds"]
        round_length_factor = self.rules["round_length"] / 5
        ticks_per_round = max(10, round(18 * round_length_factor))
        state = {
            "position": "range",
            "top": None,
            "bottom": None,
            "clinch_controller": None,
            "clinch_ticks": 0,
            "gas": {a.name: self.starting_fight_gas(a), b.name: self.starting_fight_gas(b)},
            "gas_cap": {a.name: self.starting_fight_gas(a), b.name: self.starting_fight_gas(b)},
            "damage": {a.name: 0, b.name: 0},
            "body": {a.name: 0, b.name: 0},
            "leg": {a.name: 0, b.name: 0},
            "cuts": {a.name: 0, b.name: 0},
            "control": {a.name: 0, b.name: 0},
            "impact": {a.name: 0, b.name: 0},
            "danger": {a.name: 0, b.name: 0},
            "scores": {a.name: [], b.name: []},
            "judge_scores": self.make_judge_cards(a, b),
            "knockdowns": {a.name: 0, b.name: 0},
            "unanswered": {a.name: 0, b.name: 0},
            "referee": random.choice(["cautious", "standard", "permissive", "late"]),
            "finish_detail": "",
            "finish_category": "",
            "official_time": "",
            "context": self.fight_context(a, b, fight),
            "championship_pacing": bool(fight.get("main") or fight.get("title")),
            "low_level_chaos": max(0, 68 - ((a.overall + b.overall) / 2)) / 68,
            "last_actor": None,
            "actor_streak": 0,
            "ticks_per_round": ticks_per_round,
            "ground_inactivity": 0,
            "ground_warning": False,
            "head_to_head": self.commentary_head_to_head(a, b),
            "round_leaders": [],
            "stats": {
                a.name: {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0, "control_ticks": 0},
                b.name: {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0, "control_ticks": 0},
            },
        }
        a_scale = f"{a.scale_weight} lb" if a.scale_weight else "not recorded"
        b_scale = f"{b.scale_weight} lb" if b.scale_weight else "not recorded"
        lines = [f"Tale of the tape: {a.style} / {a.stance} / {a.behaviour} / {a.trait} vs {b.style} / {b.stance} / {b.behaviour} / {b.trait}. Rules: {max_rounds}x{self.rules['round_length']}. Scale: {a_scale} vs {b_scale}."]
        lines.extend(self.commentary_opening_context(a, b, fight, state))

        recent_commentary = []

        def add_fight_line(line):
            clean = line.strip()
            if not clean:
                return
            # A long watched fight should not echo the same event line every few ticks.
            if clean in recent_commentary or (lines and lines[-1].strip() == clean):
                return
            lines.append(line)
            recent_commentary.append(clean)
            del recent_commentary[:-12]

        for round_no in range(1, max_rounds + 1):
            round_stats = {a.name: {"impact": 0, "control": 0, "danger": 0}, b.name: {"impact": 0, "control": 0, "danger": 0}}
            # Every scored round begins standing. Ground and clinch control cannot
            # leak through the horn into the next round.
            state["position"] = "range"
            if state["position"] in ("range", "pocket", "clinch", "cage"):
                state["top"] = None
                state["bottom"] = None
            if state["position"] in ("range", "pocket"):
                state["clinch_controller"] = None
            if round_no > 1:
                transition = self.commentary_round_transition(a, b, state)
                if transition:
                    lines.append(f"Between rounds: {transition}")
            lines.append(f"Round {round_no}: {self.fight_phrase('round_start', a, b, state=state)}")

            for tick in range(1, ticks_per_round + 1):
                state["round"] = round_no
                state["tick"] = tick
                state["official_time"] = self.elapsed_round_time(tick, ticks_per_round)
                state["early_round"] = tick <= max(3, ticks_per_round // 3)
                a_init = self.initiative(a, b, state)
                b_init = self.initiative(b, a, state)
                actor, defender = (a, b) if a_init >= b_init else (b, a)
                if state["last_actor"] == actor.name and state["actor_streak"] >= 2:
                    other = defender
                    other_init = b_init if other is b else a_init
                    actor_init = a_init if actor is a else b_init
                    comeback_chance = 0.24 + min(0.28, state["actor_streak"] * 0.06) + max(0, other.fight_iq - 55) / 220
                    if other_init + random.randint(-8, 18) > actor_init - 22 and random.random() < comeback_chance:
                        actor, defender = defender, actor
                if state["last_actor"] == actor.name:
                    state["actor_streak"] += 1
                else:
                    state["last_actor"] = actor.name
                    state["actor_streak"] = 1
                action = self.choose_action(actor, defender, state, round_no, tick)
                result = self.resolve_exchange(actor, defender, action, state, round_stats)
                self.apply_exchange_fatigue(actor, defender, action, state)
                control_fighter = state["top"] if state["position"] in ("guard", "half guard", "side control", "mount", "back control") else state["clinch_controller"]
                if control_fighter:
                    state["stats"][control_fighter]["control_ticks"] += 1
                ground_note = self.update_ground_inactivity(state, action)
                clock = self.round_clock(tick, ticks_per_round)
                if result:
                    add_fight_line(f"  [{clock}] {result}")
                    presence = self.fighter_presence_line(actor, defender, state)
                    if presence:
                        add_fight_line(f"  [{clock}] {presence}")
                if ground_note:
                    add_fight_line(f"  [{clock}] {ground_note}")
                else:
                    flavor = self.dynamic_flavor_line(actor, defender, state, round_no)
                    if flavor:
                        add_fight_line(f"  [{clock}] {flavor}")
                stoppage = self.check_fight_stoppage(actor, defender, state)
                if stoppage:
                    winner, loser, method, detail = stoppage
                    add_fight_line(f"  [{clock}] {detail}")
                    lines.extend(self.commentary_closing_context(a, b, winner, method, state))
                    self.attach_fight_stats(a, b, state, round_no, lines)
                    return winner, loser, method, round_no, lines
                if len(lines) > 95:
                    lines = lines[:92] + ["  ...later exchanges are summarized by the judges and fight report."]

            judge_rounds = []
            for judge in state["judge_scores"]:
                winner, loser, score = self.score_round(a, b, round_stats, state, judge=judge)
                a_score, b_score = (10, score) if winner is a else (score, 10)
                judge[a.name].append(a_score)
                judge[b.name].append(b_score)
                judge_rounds.append((a_score, b_score))
            # This is only a running broadcast estimate; the three official cards
            # remain independent until the decision is announced after the fight.
            a_average = round(sum(score[0] for score in judge_rounds) / len(judge_rounds))
            b_average = round(sum(score[1] for score in judge_rounds) / len(judge_rounds))
            state["scores"][a.name].append(a_average)
            state["scores"][b.name].append(b_average)
            total_a = sum(state["scores"][a.name])
            total_b = sum(state["scores"][b.name])
            momentum_name = a.name if round_stats[a.name]["impact"] + round_stats[a.name]["danger"] >= round_stats[b.name]["impact"] + round_stats[b.name]["danger"] else b.name
            judge_display = " | ".join(f"{a_score}-{b_score}" for a_score, b_score in judge_rounds)
            lines.append(
                f"Round {round_no} summary: judge cards {judge_display}. "
                f"Metrics - {a.name}: impact {round_stats[a.name]['impact']}, control {round_stats[a.name]['control']}, danger {round_stats[a.name]['danger']}; "
                f"{b.name}: impact {round_stats[b.name]['impact']}, control {round_stats[b.name]['control']}, danger {round_stats[b.name]['danger']}. "
                f"Live score {a.name} {total_a}, {b.name} {total_b}. "
                f"Gas: {a.name} {round(state['gas'][a.name])}, {b.name} {round(state['gas'][b.name])}. Momentum: {momentum_name}."
            )
            state["commentary_memory"] = {
                "leader": momentum_name, "a_damage": state["damage"][a.name], "b_damage": state["damage"][b.name],
                "a_gas": round(state["gas"][a.name]), "b_gas": round(state["gas"][b.name]), "round": round_no,
            }
            callback = self.commentary_round_callback(a, b, state, momentum_name, round_no)
            if callback:
                lines.append(f"Broadcast read: {callback}")
            if round_no < max_rounds:
                corner = self.check_corner_stoppage(a, b, state, round_no)
                if corner:
                    winner, loser, method, detail = corner
                    lines.append(detail)
                    lines.extend(self.commentary_closing_context(a, b, winner, method, state))
                    self.attach_fight_stats(a, b, state, round_no, lines)
                    return winner, loser, method, round_no, lines
                self.recover_between_rounds(a, b, state)

        lines.extend(self.final_scorecard_lines(a, b, state))
        decision = self.decision_from_judges(a, b, state)
        if decision["winner"] is None:
            lines.append(self.fight_phrase("draw", a, b, score=decision["summary"]))
            lines.extend(self.commentary_closing_context(a, b, None, "Draw", state))
            self.attach_fight_stats(a, b, state, max_rounds, lines)
            return a, b, "Draw", max_rounds, lines
        winner = decision["winner"]
        loser = b if winner is a else a
        method = "Decision"
        lines.append(self.fight_phrase("decision", winner, loser, score=decision["summary"]))
        lines.extend(self.commentary_closing_context(a, b, winner, method, state))
        self.attach_fight_stats(a, b, state, max_rounds, lines)
        return winner, loser, method, max_rounds, lines

    def commentary_head_to_head(self, a, b):
        """Read a compact, best-effort prior-meeting record from persistent career history."""
        meetings = a_wins = b_wins = 0
        last_result = ""
        for entry in (a.fight_history or []):
            text = str(entry)
            if b.name.lower() not in text.lower() or "def." not in text:
                continue
            meetings += 1
            if f"{a.name} def." in text:
                a_wins += 1
            elif f"{b.name} def." in text:
                b_wins += 1
            last_result = text
        return {"meetings": meetings, "a_wins": a_wins, "b_wins": b_wins, "last_result": last_result}

    def commentary_opening_context(self, a, b, fight, state=None):
        lines = []
        head_to_head = (state or {}).get("head_to_head", self.commentary_head_to_head(a, b))
        prior_meetings = head_to_head["meetings"]
        if fight.get("title"):
            lines.append("Broadcast context: championship stakes raise the pressure; composure and late-round reserves could decide this one.")
        if a.rival == b.name or b.rival == a.name:
            heat = self.rivalry_heat_between(a, b) if hasattr(self, "rivalry_heat_between") else max(getattr(a, "rivalry_heat", 0), getattr(b, "rivalry_heat", 0))
            lines.append(f"Broadcast context: this rivalry is running at {heat}/100 heat — every exchange carries extra meaning.")
        if prior_meetings:
            lines.append(f"Broadcast context: head-to-head is {a.name} {head_to_head['a_wins']}-{head_to_head['b_wins']} {b.name} across {prior_meetings} prior meeting{'s' if prior_meetings != 1 else ''}; adjustments will matter early.")
        if fight.get("region") and hasattr(self, "fighter_event_connection"):
            a_home = self.fighter_event_connection(a, fight["region"], fight.get("city", ""))
            b_home = self.fighter_event_connection(b, fight["region"], fight.get("city", ""))
            if a_home["strength"] >= 0.52 and a_home["strength"] > b_home["strength"] + 0.15:
                lines.append(f"Broadcast context: {a.name} is fighting in a {a_home['level'].lower()} market and has the crowd behind them tonight.")
            elif b_home["strength"] >= 0.52 and b_home["strength"] > a_home["strength"] + 0.15:
                lines.append(f"Broadcast context: {b.name} is fighting in a {b_home['level'].lower()} market and has the crowd behind them tonight.")
            elif a_home["strength"] >= 0.52 and b_home["strength"] >= 0.52:
                lines.append("Broadcast context: both fighters carry a meaningful local connection tonight, making this a split-room atmosphere.")
        return lines

    def commentary_round_callback(self, a, b, state, leader_name, round_no):
        leaders = state.setdefault("round_leaders", [])
        prior = leaders[-1] if leaders else ""
        leaders.append(leader_name)
        leader = a if leader_name == a.name else b
        trailing = b if leader is a else a
        head_to_head = state.get("head_to_head", {})
        if prior and prior != leader_name:
            return f"Momentum has swung from {prior} to {leader.name}; {trailing.name}'s corner must answer the adjustment."
        if state["cuts"].get(trailing.name, 0) >= 2:
            return f"{trailing.name}'s face is showing the accumulated work, and the referee will be watching it closely."
        if state["body"].get(trailing.name, 0) >= 16:
            return f"The body work is slowing {trailing.name}; that investment could change the later rounds."
        if round_no >= 2 and head_to_head.get("meetings", 0):
            previous_edge = head_to_head.get("a_wins", 0) - head_to_head.get("b_wins", 0)
            if (previous_edge > 0 and leader is b) or (previous_edge < 0 and leader is a):
                return f"This rematch is taking a different shape: {leader.name} is outperforming the historical series so far."
        return ""

    def commentary_round_transition(self, a, b, state):
        memory = state.get("commentary_memory", {})
        if not memory:
            return "Both corners are making their first adjustments."
        leader = memory.get("leader")
        trailing = b if leader == a.name else a
        leader_fighter = a if leader == a.name else b
        leader_damage = memory.get("a_damage", 0) if leader is a else memory.get("b_damage", 0)
        trailing_damage = memory.get("b_damage", 0) if leader is a else memory.get("a_damage", 0)
        if trailing_damage - leader_damage >= 10:
            return f"{trailing.name}'s corner needs urgency after absorbing the heavier damage in round {memory.get('round', 1)}."
        leader_gas = memory.get("a_gas", 0) if leader is a else memory.get("b_gas", 0)
        trailing_gas = memory.get("b_gas", 0) if leader is a else memory.get("a_gas", 0)
        if leader_gas - trailing_gas >= 12:
            return f"{leader_fighter.name} carries the fresher gas tank; {trailing.name} needs to change the pace."
        return f"{leader_fighter.name} edged the last round, but the fight remains close enough for a tactical swing."

    def commentary_closing_context(self, a, b, winner, method, state):
        if winner is None:
            return ["Broadcast recap: neither fighter created enough separation; the unresolved story is likely to invite more debate."]
        loser = b if winner is a else a
        if winner.rival == loser.name or loser.rival == winner.name:
            return [f"Broadcast recap: {winner.name} wins a meaningful rivalry chapter by {method}; the feud may not be finished."]
        head_to_head = state.get("head_to_head", {})
        if head_to_head.get("meetings", 0):
            a_wins = head_to_head.get("a_wins", 0) + int(winner is a)
            b_wins = head_to_head.get("b_wins", 0) + int(winner is b)
            return [f"Broadcast recap: the head-to-head now stands {a.name} {a_wins}-{b_wins} {b.name}; this rivalry has real history."]
        memory = state.get("commentary_memory", {})
        leader = memory.get("leader")
        if leader and leader != winner.name:
            return [f"Broadcast recap: {winner.name} turned the fight after {leader} had the earlier momentum."]
        return [f"Broadcast recap: {winner.name}'s game plan held up across the fight and earned the {method} victory."]

    def attach_fight_stats(self, a, b, state, ending_round, lines):
        """Build a readable box score from the same events that produced commentary."""
        seconds_per_tick = (self.rules.get("round_length", 5) * 60) / max(1, state.get("ticks_per_round", 18))
        for fighter in (a, b):
            s = state["stats"][fighter.name]
            s["control_secs"] = round(s["control_ticks"] * seconds_per_tick)
            s["knockdowns"] = state["knockdowns"].get(fighter.name, 0)
            fighter.last_fight_stats = {
                "sig": s["sig"], "sig_att": s["sig_att"], "td": s["td"], "td_att": s["td_att"],
                "sub_att": s["sub_att"], "control_secs": s["control_secs"], "knockdowns": s["knockdowns"], "rounds": ending_round,
                "damage_taken": state["damage"][fighter.name], "body_damage": state["body"][fighter.name], "leg_damage": state["leg"][fighter.name], "cuts": state["cuts"][fighter.name],
            }

        def line_for(fighter):
            s = fighter.last_fight_stats
            mm, ss = divmod(s["control_secs"], 60)
            return f"{s['sig']:>3}/{s['sig_att']:<3}  {s['td']:>2}/{s['td_att']:<2}  {s['sub_att']:>2}    {mm}:{ss:02d}    {s['knockdowns']:>2}"
        name_width = max(16, min(26, max(len(a.name), len(b.name))))
        lines.extend([
            "FIGHT METRICS",
            f"{'Fighter':<{name_width}}  Sig. Str.   TD     Subs  Control   KD   Damage (Head/Body/Leg/Cuts)",
            "-" * (name_width + 67),
            f"{a.name:<{name_width}}  {line_for(a)}  {a.last_fight_stats['damage_taken']:>3}/{a.last_fight_stats['body_damage']:>2}/{a.last_fight_stats['leg_damage']:>2}/{a.last_fight_stats['cuts']}",
            f"{b.name:<{name_width}}  {line_for(b)}  {b.last_fight_stats['damage_taken']:>3}/{b.last_fight_stats['body_damage']:>2}/{b.last_fight_stats['leg_damage']:>2}/{b.last_fight_stats['cuts']}",
        ])

    def commit_career_stats(self, fighter, result_method=None, won=False):
        """Fold the most recent fight's stats into a fighter's career totals."""
        stats = getattr(fighter, "last_fight_stats", None)
        if not stats:
            return
        fighter.career_sig_strikes = getattr(fighter, "career_sig_strikes", 0) + stats.get("sig", 0)
        fighter.career_takedowns = getattr(fighter, "career_takedowns", 0) + stats.get("td", 0)
        fighter.career_control_secs = getattr(fighter, "career_control_secs", 0) + stats.get("control_secs", 0)
        fighter.career_knockdowns = getattr(fighter, "career_knockdowns", 0) + stats.get("knockdowns", 0)
        fighter.career_sub_attempts = getattr(fighter, "career_sub_attempts", 0) + stats.get("sub_att", 0)
        fighter.career_stat_rounds = getattr(fighter, "career_stat_rounds", 0) + stats.get("rounds", 0)
        fighter.career_stat_fights = getattr(fighter, "career_stat_fights", 0) + 1
        if won and result_method not in (None, "Decision", "Draw"):
            fighter.career_finishes = getattr(fighter, "career_finishes", 0) + 1
        if won and result_method in ("KO", "TKO"):
            fighter.career_knockouts = getattr(fighter, "career_knockouts", 0) + 1
        if won and result_method in ("Submission", "Technical Submission"):
            fighter.career_submissions = getattr(fighter, "career_submissions", 0) + 1
        fighter.last_fight_stats = None

    def starting_fight_gas(self, fighter):
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        resilience = self.ds(fighter, "resilience", fighter.toughness)
        cap = 92 + (conditioning - 50) * 0.18 + (fighter.cardio - 50) * 0.09 + (resilience - 50) * 0.04
        trait = 4 if fighter.trait == "Cardio Machine" else -5 if fighter.trait == "Bad Weight Cut" else 0
        penalty = fighter.fatigue * 0.48 + fighter.weight_cut_penalty * 1.35
        return max(18, min(100, round(cap + trait - penalty)))

    def update_ground_inactivity(self, state, action):
        ground_positions = ("guard", "half guard", "side control", "mount", "back control")
        if state["position"] not in ground_positions:
            state["ground_inactivity"] = 0
            state["ground_warning"] = False
            return ""
        active = {"ground_strikes", "advance_position", "recover_guard", "submission", "bottom_submission", "sweep", "stand_up"}
        if action in active:
            state["ground_inactivity"] = 0
            state["ground_warning"] = False
            return ""
        state["ground_inactivity"] += 1
        # One tick is roughly 15-17 seconds. A warning follows about 45 seconds of
        # inactivity, then a stand-up only after it continues for another beat.
        if state["ground_inactivity"] >= 3 and not state["ground_warning"]:
            state["ground_warning"] = True
            return random.choice([
                "The referee calls for more activity from the grounded fighters.",
                "The referee circles the action and warns both fighters to work.",
                "\"Let's go, work!\" - the referee wants more from the ground exchange.",
                "The crowd murmurs as the referee urges the fighters to improve position or stand.",
                "The referee crouches in close and tells them to be busy on the mat.",
            ])
        threshold = {"cautious": 4, "standard": 5, "permissive": 6, "late": 7}.get(state.get("referee"), 5)
        if state["ground_warning"] and state["ground_inactivity"] >= threshold:
            state["position"] = "range"
            state["top"] = None
            state["bottom"] = None
            state["clinch_controller"] = None
            state["ground_inactivity"] = 0
            state["ground_warning"] = False
            return random.choice([
                "After a prolonged stalemate on the mat, the referee stands them up.",
                "The referee has seen enough of the lull and brings them back to the feet.",
                "Stalemate on the ground - the referee resets the fighters at range.",
                "The referee waves it up; the ground position had gone stagnant.",
            ])
        return ""

    def fight_context(self, a, b, fight):
        region = fight.get("region", fight.get("event_region", ""))
        context = {a.name: {}, b.name: {}}
        for fighter, opponent in ((a, b), (b, a)):
            stance_edge = self.stance_matchup_edge(fighter, opponent)
            home_edge = 2.2 if region and fighter.region == region else 0
            prime_edge = self.prime_fight_edge(fighter)
            experience_edge = self.experience_fight_edge(fighter)
            pressure_edge = self.pressure_fight_edge(fighter, opponent, fight)
            rivalry_edge = (1.6 + min(4.2, getattr(fighter, "rivalry_heat", 0) / 24)
                            if fighter.rival == opponent.name else (-1.5 if fighter.friend == opponent.name else 0))
            reach_edge = (self.ds(fighter, "reach", 50) - self.ds(opponent, "reach", 50)) * 0.035
            size_edge = (self.ds(fighter, "natural_size", 50) - self.ds(opponent, "natural_size", 50)) * 0.04
            style_edge = self.style_matchup_bonus(fighter, opponent) * 0.55
            context[fighter.name] = {
                "stance": stance_edge,
                "home": home_edge,
                "prime": prime_edge,
                "experience": experience_edge,
                "pressure": pressure_edge,
                "rivalry": rivalry_edge,
                "reach": reach_edge,
                "size": size_edge,
                "style": style_edge,
            }
        return context

    def stance_matchup_edge(self, fighter, opponent):
        if fighter.stance == "Switch":
            return 1.8 + (self.ds(fighter, "adaptability", 50) - 50) * 0.03
        if fighter.stance != opponent.stance:
            familiarity = self.ds(fighter, "adaptability", 50) + self.ds(fighter, "footwork", 50)
            return -1.8 + max(0, familiarity - 105) * 0.035
        return 0.4

    def prime_fight_edge(self, fighter):
        if fighter.prime_start <= fighter.age <= fighter.prime_end:
            return 2.0
        if fighter.age < fighter.prime_start:
            return max(-2.5, -0.6 * (fighter.prime_start - fighter.age))
        return max(-7.0, -1.1 * (fighter.age - fighter.prime_end))

    def experience_fight_edge(self, fighter):
        bouts = fighter.record_w + fighter.record_l + fighter.record_d
        quality = fighter.record_w - fighter.record_l * 0.5
        return max(-2.0, min(5.0, bouts * 0.08 + quality * 0.05))

    def pressure_fight_edge(self, fighter, opponent, fight):
        stakes = (4 if fight.get("title") else 0) + (2 if fight.get("main") else 0)
        if not stakes:
            return 0
        composure = self.ds(fighter, "composure", fighter.fight_iq)
        title_bonus = 2 if fighter.trait == "Title Mentality" else 0
        prospect_drag = -1.5 if fighter.trait == "Prospect Mindset" and opponent.popularity > fighter.popularity + 12 else 0
        return (composure - 55) * 0.06 + title_bonus + prospect_drag - stakes * 0.18

    def context_edge(self, fighter, state, *keys):
        values = state.get("context", {}).get(fighter.name, {})
        return sum(values.get(key, 0) for key in keys) * 0.45

    def recover_between_rounds(self, a, b, state):
        for fighter in (a, b):
            conditioning = self.ds(fighter, "conditioning", fighter.cardio)
            resilience = self.ds(fighter, "resilience", fighter.toughness)
            camp_quality = fighter.camp_quality or self.gym_quality(fighter.camp)
            camp_recovery = min(2.4, camp_quality / 70 + fighter.camp_weeks * 0.08 + fighter.camp_boost * 0.12)
            recovery = 2 + conditioning / 30 + fighter.cardio / 36 + resilience / 55 + camp_recovery
            recovery -= state["damage"][fighter.name] / 28 + state["body"][fighter.name] / 9 + state["leg"][fighter.name] / 24
            if fighter.trait == "Cardio Machine":
                recovery += 2.2
            if fighter.trait == "Bad Weight Cut":
                recovery -= 3
            recovery += self.context_edge(fighter, state, "prime", "experience", "pressure") * 0.18
            elite_control = max(0, fighter.overall - 78) / 14
            recovery += elite_control * 1.6
            if state.get("championship_pacing") and state.get("round", 1) >= 3:
                state["damage"][fighter.name] = max(0, state["damage"][fighter.name] - (1.4 + elite_control * 1.2))
                state["body"][fighter.name] = max(0, state["body"][fighter.name] - 0.8)
                state["leg"][fighter.name] = max(0, state["leg"][fighter.name] - 0.8)
            # Corners restore a little, never a fresh tank. The original fight cap
            # already includes the fighter's camp and weight-cut condition.
            state["gas"][fighter.name] = max(3, min(state["gas_cap"][fighter.name], state["gas"][fighter.name] + max(1, recovery)))

    def check_corner_stoppage(self, a, b, state, round_no):
        state["round"] = round_no
        state["official_time"] = f"{self.rules.get('round_length', 5)}:00"
        for fighter, opponent in ((a, b), (b, a)):
            damage = state["damage"][fighter.name]
            body = state["body"][fighter.name]
            leg = state["leg"][fighter.name]
            gas = state["gas"][fighter.name]
            danger = state["danger"][opponent.name]
            if damage > fighter.toughness * 1.05 or body > 30 or leg > 28 or (gas < 10 and danger > 18):
                chance = 0.08 + max(0, damage - fighter.toughness) / 190 + max(0, body - 24) / 80 + max(0, leg - 23) / 95 + max(0, 12 - gas) / 75
                if random.random() < min(0.55, chance):
                    method = "Corner Stoppage"
                    return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, self.fight_phrase("corner_stoppage", opponent, fighter), state)
        return None

    def make_judge_cards(self, a, b):
        profiles = ["Damage-first", "Balanced", "Control-sensitive"]
        random.shuffle(profiles)
        return [
            {"name": f"Judge {index + 1}", "profile": profile, a.name: [], b.name: []}
            for index, profile in enumerate(profiles)
        ]

    def decision_from_judges(self, a, b, state):
        cards = []
        votes = {a.name: 0, b.name: 0}
        for judge in state["judge_scores"]:
            a_total = sum(judge[a.name])
            b_total = sum(judge[b.name])
            cards.append((judge["name"], a_total, b_total))
            if a_total > b_total:
                votes[a.name] += 1
            elif b_total > a_total:
                votes[b.name] += 1
        winner = a if votes[a.name] > votes[b.name] else b if votes[b.name] > votes[a.name] else None
        summary = ", ".join(f"{a_total}-{b_total}" for _name, a_total, b_total in cards)
        return {"winner": winner, "cards": cards, "votes": votes, "summary": summary}

    def final_scorecard_lines(self, a, b, state):
        decision = self.decision_from_judges(a, b, state)
        lines = ["Official scorecards:"]
        for card, (judge, a_total, b_total) in zip(state["judge_scores"], decision["cards"]):
            leader = a.name if a_total > b_total else b.name if b_total > a_total else "Even"
            lines.append(f"  {judge} [{card['profile']}]: {a.name} {a_total}, {b.name} {b_total} ({leader})")
        lines.append(f"  Judges' vote: {a.name} {decision['votes'][a.name]}, {b.name} {decision['votes'][b.name]}")
        return lines

    def round_clock(self, tick, ticks_per_round):
        total_seconds = self.rules.get("round_length", 5) * 60
        seconds_left = max(0, round(total_seconds * (ticks_per_round - tick) / max(1, ticks_per_round)))
        return f"{seconds_left // 60}:{seconds_left % 60:02d}"

    def elapsed_round_time(self, tick, ticks_per_round):
        total_seconds = self.rules.get("round_length", 5) * 60
        elapsed = min(total_seconds, max(0, round(total_seconds * tick / max(1, ticks_per_round))))
        return f"{elapsed // 60}:{elapsed % 60:02d}"

    def fighter_presence_line(self, actor, defender, state):
        if state.get("actor_streak", 0) < 3 or random.random() > 0.32:
            return ""
        if state["damage"][defender.name] > defender.toughness * 0.55:
            return random.choice([
                f"{defender.name} shells up, takes a breath, and tries to reset the range.",
                f"{defender.name} is hurt but keeps framing and looking for a way off the fence.",
                f"{defender.name} fires a short warning shot to stop {actor.name} from rushing in.",
            ])
        if state["gas"][defender.name] < 24:
            return random.choice([
                f"{defender.name} is visibly tired and takes an extra second before resetting.",
                f"{defender.name}'s guard is sagging as the pace starts to bite.",
                f"{defender.name} circles away with heavy legs and tries to slow the fight down.",
            ])
        if state["position"] in ("guard", "half guard", "side control", "mount", "back control"):
            return random.choice([
                f"{defender.name} controls a wrist and slows the ground attack for a moment.",
                f"{defender.name} hip-escapes just enough to make {actor.name} reset position.",
                f"{defender.name} stays defensively responsible and keeps talking to the referee.",
            ])
        return random.choice([
            f"{defender.name} answers with movement and makes {actor.name} start again.",
            f"{defender.name} shows a counter and keeps {actor.name} honest.",
            f"{defender.name} circles off the center line before the next exchange.",
        ])

    def dynamic_flavor_line(self, actor, defender, state, round_no):
        """Occasional atmospheric beat - crowd, corner, taunts, blood, tactics, fouls -
        so the play-by-play breathes beyond the mechanical exchanges."""
        if random.random() > 0.12:
            return ""
        cap = state.get("gas_cap", {}).get(defender.name, 100)
        dmg_def = state["damage"][defender.name]
        gas_act = state["gas"][actor.name]
        gas_def = state["gas"][defender.name]
        cut_def = state["cuts"][defender.name]
        body_def = state["body"][defender.name]
        streak = state.get("actor_streak", 0)
        pos = state["position"]

        # Rare fouls interrupt the action with a brief recovery pause.
        if random.random() < 0.06 and pos in ("range", "pocket", "clinch", "cage"):
            foul = random.choice(["eye poke", "eye poke", "low blow", "fence grab", "grounded knee"])
            if foul == "eye poke":
                state["gas"][defender.name] = min(cap, gas_def + 4)
                return random.choice([
                    f"Action stops - {actor.name} catches {defender.name} with a stray eye poke and the referee gives time to recover.",
                    f"{defender.name} turns away blinking after a finger to the eye; the referee calls a brief timeout.",
                ])
            if foul == "low blow":
                state["gas"][defender.name] = min(cap, gas_def + 3)
                return f"{defender.name} drops to a knee after a low blow and takes the full recovery time from the referee."
            if foul == "grounded knee":
                return f"The referee sternly warns {actor.name} about a knee to a grounded opponent."
            return f"The referee warns {actor.name} for grabbing the fence."

        pool = []
        if cut_def >= 1:
            pool += [
                f"Blood is streaming down {defender.name}'s face now and the crowd senses a finish.",
                f"The ringside doctor leans in for a look at {defender.name}'s cut during the lull.",
                f"{defender.name} keeps wiping at the blood, trying to keep it out of their eye.",
            ]
        if body_def >= 12:
            pool += [
                f"{defender.name}'s hand keeps drifting to the ribs - the body work is adding up.",
                f"You can see {defender.name} wince whenever the body is threatened.",
            ]
        if gas_def < 24:
            pool += [
                f"{defender.name} is sucking wind between exchanges, mouth wide open.",
                f"{defender.name}'s corner screams at them to breathe and reset.",
            ]
        if gas_act < 24 and gas_def < 24:
            pool += ["Both fighters are running on fumes now - this has become a test of will.",
                     "The pace has cratered; whoever finds a second wind takes over.",
                     "Two exhausted fighters lean on each other, chests heaving.",
                     "The output has dropped to a trickle as the tank runs dry for both.",
                     "This is grit over technique now - both are utterly spent."]
        if streak >= 3 and dmg_def > defender.toughness * 0.3:
            pool += [
                f"The arena is on its feet as {actor.name} takes over.",
                f"A wall of noise builds behind {actor.name}'s surge.",
                f"{actor.name} has found a rhythm and the momentum has clearly swung.",
            ]
            if defender.trait == "Comeback Artist":
                pool += [f"But {defender.name} is at their most dangerous when hurt - the corner stays calm."]
        if actor.trait in ("Showman", "Trash Talker") and state["damage"][actor.name] < actor.toughness * 0.4:
            pool += [
                f"{actor.name} drops the hands and beckons {defender.name} forward, playing to the crowd.",
                f"{actor.name} flashes a grin and taps their own chin at {defender.name}.",
                f"{actor.name} showboats for a beat, soaking up the reaction.",
            ]
        if actor.trait in ("Fan Favourite", "Marketable") and round_no >= 2:
            pool += [f"The crowd breaks into a \"{actor.name.split()[-1]}!\" chant."]
        if actor.professionalism > 68 or self.ds(actor, "discipline", 50) > 66:
            pool += [
                f"You can hear {actor.name}'s corner between beats: \"Hands up, back behind the jab!\"",
                f"{actor.name}'s coach is barking for the body-head combination.",
                f"\"Circle out, don't sit on the fence!\" comes the shout from {actor.name}'s corner.",
                f"{actor.name}'s cornerman calls for more feints before committing.",
                f"\"Double the jab, then move!\" - {actor.name}'s coach is dialed in.",
                f"{actor.name}'s corner wants the leg kick set up behind the hands.",
            ]
        if pos in ("range", "pocket"):
            pool += [
                f"{actor.name} switches stance, hunting a fresh angle.",
                f"A tense feeling-out spell as both reset the range.",
                f"{actor.name} pumps a couple of feints, fishing for a reaction.",
                f"{actor.name} rolls the shoulders and resets, measuring the distance.",
                f"{actor.name} steps in and out of range, baiting a counter.",
                f"{actor.name} paws with the lead hand, hunting an opening.",
                f"A brief lull as {actor.name} circles and studies {defender.name}.",
                f"{actor.name} feints the level change, testing {defender.name}'s reactions.",
                f"{actor.name} bounces on the balls of the feet, changing rhythm.",
            ]
        elif pos in ("clinch", "cage"):
            pool += [
                f"They grind against the fence, each looking for an underhook.",
                f"The referee watches the clinch closely, ready to break it if it stalls.",
                f"{actor.name} digs for double underhooks and turns {defender.name} along the cage.",
                f"Heads pressed together, they fight for wrist control in the tie-up.",
                f"{actor.name} thuds a knee up the middle of the clinch to stay busy.",
                f"A grinding clinch battle - neither wants to give up the position.",
            ]
        return random.choice(pool) if pool else ""

    def initiative(self, fighter, opponent, state):
        aggression = (self.ds(fighter, "aggression", 50) - 50) * 0.09
        pressure = 8 if fighter.behaviour in ("Pressure", "Volume", "Dynamic Attacker") else 0
        caution = -7 if fighter.behaviour == "Cautious" else 0
        freshness = state["gas"][fighter.name] * 0.17 - state["damage"][fighter.name] * 0.18
        mental = self.skill_bundle(fighter, "mental") * 0.13 + self.ds(fighter, "confidence", 50) * 0.07
        mobility = (self.ds(fighter, "mobility", 50) + self.ds(fighter, "reflexes", 50)) * 0.04
        context = self.context_edge(fighter, state, "home", "prime", "experience", "pressure", "rivalry", "stance", "style")
        return freshness + mental + mobility + aggression + fighter.momentum * 2 + fighter.camp_boost * 1.3 - fighter.weight_cut_penalty * 0.9 + pressure + caution + context + random.randint(-10, 10)

    STYLE_BIAS = {
        "range": {
            "Boxer": {"jab": 1.22, "power_punch": 1.2, "kick": 0.5, "shoot": 0.82},
            "Kickboxer": {"kick": 1.4, "power_punch": 1.12, "jab": 1.05, "shoot": 0.82},
            "Dutch Kickboxer": {"kick": 1.46, "power_punch": 1.2, "jab": 1.08, "shoot": 0.72},
            "Karate": {"kick": 1.32, "jab": 1.16, "power_punch": 1.12, "clinch": 0.55, "shoot": 0.7},
            "Taekwondo": {"kick": 1.58, "jab": 0.88, "power_punch": 0.82, "clinch": 0.48, "shoot": 0.62},
            "Sanda": {"kick": 1.24, "shoot": 1.12, "clinch": 1.18, "power_punch": 1.04},
            "Muay Thai": {"kick": 1.2, "clinch": 1.4, "power_punch": 1.06, "shoot": 0.85},
            "Wrestler": {"shoot": 1.55, "clinch": 1.2, "kick": 0.5, "power_punch": 0.95},
            "Freestyle Wrestler": {"shoot": 1.68, "clinch": 1.25, "kick": 0.48, "power_punch": 0.92},
            "Catch Wrestler": {"shoot": 1.36, "clinch": 1.25, "power_punch": 1.04},
            "Judo": {"clinch": 1.5, "shoot": 1.12, "kick": 0.72},
            "BJJ": {"shoot": 1.35, "clinch": 1.1, "kick": 0.82, "power_punch": 0.85},
            "Luta Livre": {"shoot": 1.28, "clinch": 1.14, "power_punch": 0.96},
            "Sambo": {"shoot": 1.3, "power_punch": 1.1, "clinch": 1.12},
            "Grappler": {"shoot": 1.4, "clinch": 1.1, "kick": 0.82},
            "Submission Grappler": {"shoot": 1.44, "clinch": 1.12, "power_punch": 0.82},
            "MMA Generalist": {"jab": 1.08, "kick": 1.08, "shoot": 1.08, "clinch": 1.08},
        },
        "clinch": {
            "Muay Thai": {"dirty_boxing": 1.5},
            "Boxer": {"dirty_boxing": 1.25, "break_clinch": 1.1},
            "Kickboxer": {"dirty_boxing": 1.15, "break_clinch": 1.05},
            "Dutch Kickboxer": {"dirty_boxing": 1.28, "break_clinch": 1.02},
            "Karate": {"break_clinch": 1.5, "dirty_boxing": 0.8},
            "Taekwondo": {"break_clinch": 1.62, "dirty_boxing": 0.68},
            "Sanda": {"takedown": 1.22, "dirty_boxing": 1.12, "break_clinch": 1.1},
            "Wrestler": {"takedown": 1.4, "cage_control": 1.2},
            "Freestyle Wrestler": {"takedown": 1.52, "cage_control": 1.25},
            "Catch Wrestler": {"takedown": 1.3, "dirty_boxing": 1.12},
            "Judo": {"takedown": 1.5, "cage_control": 1.1},
            "BJJ": {"takedown": 1.3},
            "Sambo": {"takedown": 1.3, "dirty_boxing": 1.1},
            "Grappler": {"takedown": 1.3},
            "Luta Livre": {"takedown": 1.28, "dirty_boxing": 1.12},
            "Submission Grappler": {"takedown": 1.3},
        },
        "top": {
            "BJJ": {"submission": 1.5, "advance_position": 1.2},
            "Sambo": {"submission": 1.35, "advance_position": 1.1},
            "Wrestler": {"ground_control": 1.3, "ground_strikes": 1.4},
            "Judo": {"ground_control": 1.2, "ground_strikes": 1.1},
            "Grappler": {"submission": 1.3, "advance_position": 1.15},
            "Luta Livre": {"submission": 1.42, "ground_strikes": 1.12},
            "Catch Wrestler": {"submission": 1.28, "ground_control": 1.18},
            "Submission Grappler": {"submission": 1.52, "advance_position": 1.18},
            "Freestyle Wrestler": {"ground_control": 1.38, "ground_strikes": 1.25},
        },
        "bottom": {
            "BJJ": {"bottom_submission": 1.5, "sweep": 1.2},
            "Sambo": {"bottom_submission": 1.3, "sweep": 1.1},
            "Grappler": {"bottom_submission": 1.3, "sweep": 1.15},
            "Judo": {"sweep": 1.25, "stand_up": 1.1},
            "Wrestler": {"stand_up": 1.35, "recover_guard": 1.1},
            "Boxer": {"stand_up": 1.4},
            "Kickboxer": {"stand_up": 1.4},
            "Karate": {"stand_up": 1.45},
            "Muay Thai": {"stand_up": 1.35},
            "Dutch Kickboxer": {"stand_up": 1.42},
            "Taekwondo": {"stand_up": 1.52},
            "Sanda": {"stand_up": 1.3, "sweep": 1.08},
            "Luta Livre": {"bottom_submission": 1.42, "sweep": 1.14},
            "Catch Wrestler": {"bottom_submission": 1.28, "sweep": 1.18},
            "Submission Grappler": {"bottom_submission": 1.52, "sweep": 1.16},
        },
    }

    def apply_style_bias(self, fighter, weights, phase):
        """Give each fighting style a real identity in how it chooses actions."""
        profile = self.STYLE_BIAS.get(phase, {}).get(fighter.style)
        if profile:
            for action, mult in profile.items():
                if action in weights:
                    weights[action] *= mult
        return weights

    def choose_action(self, fighter, opponent, state, round_no, tick):
        position = state["position"]
        gas = state["gas"][fighter.name]
        tired = gas < 42
        exhausted = gas < 22
        hurt = state["damage"][fighter.name] > fighter.toughness * 0.65
        mental = self.skill_bundle(fighter, "mental")
        aggression = self.ds(fighter, "aggression", 50)
        if gas < 8 and random.random() < 0.62:
            return "survive"
        if exhausted and random.random() < 0.22 + max(0, 35 - gas) / 90:
            return "survive"
        if hurt and fighter.recovery + mental + self.ds(fighter, "stun_recovery", fighter.recovery) + random.randint(-35, 25) > 185:
            return "survive"
        if position in ("range", "pocket"):
            weights = {
                "jab": self.skill_bundle(fighter, "boxing") + mental * 0.35 + self.ds(fighter, "reach", 50) * 0.18,
                "power_punch": self.skill_bundle(fighter, "power_boxing") + fighter.power * 0.35 + (14 if fighter.trait in ("Big Finisher", "Knockout Artist", "Glass Cannon") else 0),
                "kick": self.skill_bundle(fighter, "kick_game") + self.ds(fighter, "mobility", 50) * 0.22,
                "shoot": self.skill_bundle(fighter, "shot") + (18 if fighter.behaviour in ("Control", "Dynamic Attacker") else 0),
                "clinch": self.skill_bundle(fighter, "clinch_attack") + self.ds(fighter, "strength", 50) * 0.25,
            }
            if fighter.trait in ("Pressure Fighter", "Fast Starter"):
                weights["power_punch"] *= 1.16
                weights["clinch"] *= 1.1
            if fighter.trait == "Counter Specialist":
                weights["jab"] *= 1.18
                weights["power_punch"] *= 0.92
            if fighter.trait == "Submission Ace":
                weights["shoot"] *= 1.2
            if fighter.trait in ("Leg Kicker", "Body Hunter"):
                weights["kick"] *= 1.22
            if fighter.trait == "Cage Specialist":
                weights["clinch"] *= 1.18
            if fighter.trait == "Cardio Machine" and state["round"] >= 2:
                weights["jab"] *= 1.14
                weights["shoot"] *= 1.1
            if aggression > 65:
                weights["power_punch"] *= 1.12
                weights["shoot"] *= 1.08
            if self.ds(fighter, "discipline", 50) > 68:
                weights["jab"] *= 1.12
            if fighter.behaviour == "Sprawl And Brawl":
                weights["shoot"] *= 0.25
                weights["jab"] *= 1.2
            if fighter.behaviour == "Submission Hunter":
                weights["shoot"] *= 1.58
                weights["power_punch"] *= 0.9
            if fighter.grappling > fighter.striking + 6:
                weights["shoot"] *= 1.18
                weights["clinch"] *= 1.05
                weights["kick"] *= 0.92
            self.apply_style_bias(fighter, weights, "range")
            if tired:
                weights["jab"] *= 1.12
                weights["power_punch"] *= 0.42
                weights["kick"] *= 0.48
                weights["shoot"] *= 0.62
                weights["clinch"] *= 1.12
            if exhausted:
                weights["power_punch"] *= 0.55
                weights["kick"] *= 0.45
                weights["shoot"] *= 0.45
                weights["clinch"] *= 1.25
            if opponent.wrestling > fighter.takedown_defence + 8 and fighter.fight_iq > 58:
                weights["kick"] *= 0.45
            return self.weighted_choice(weights)
        if position in ("clinch", "cage"):
            weights = {
                "dirty_boxing": self.skill_bundle(fighter, "clinch_attack") + self.ds(fighter, "dirty_boxing", fighter.striking) * 0.45,
                "takedown": self.ds_avg(fighter, ("clinch_takedowns", "throws", "chain_wrestling", "strength"), fighter.wrestling),
                "cage_control": self.ds_avg(fighter, ("cage_pressure", "clinch_control", "cage_wrestling", "strength"), fighter.wrestling),
                "break_clinch": self.skill_bundle(fighter, "clinch_defence") + mental * 0.25,
            }
            if state.get("clinch_controller") == fighter.name:
                weights["dirty_boxing"] *= 1.22
                weights["takedown"] *= 1.16
                weights["cage_control"] *= 1.12
                weights["break_clinch"] *= 0.42
            elif state.get("clinch_controller"):
                # The trapped fighter is more likely to frame, escape, or win an
                # underhook battle than to magically continue the same control.
                weights["break_clinch"] *= 1.58
                weights["cage_control"] *= 0.68
                weights["takedown"] *= 0.84
            if fighter.behaviour == "Control":
                weights["cage_control"] *= 1.45
            if fighter.behaviour == "Submission Hunter":
                weights["takedown"] *= 1.35
            self.apply_style_bias(fighter, weights, "clinch")
            return self.weighted_choice(weights)
        if state["top"] == fighter.name:
            sub_multiplier = 1.52 if fighter.behaviour == "Submission Hunter" else 0.94
            # From a dominant, finish-friendly position a good grappler hunts the tap.
            if position in ("mount", "back control"):
                sub_multiplier *= 1.24
            elif position == "side control":
                sub_multiplier *= 1.1
            weights = {
                "ground_control": self.ds_avg(fighter, ("top_control", "ride_control", "discipline", "positional_ability"), fighter.ground_control) * 0.68,
                "ground_strikes": self.ds_avg(fighter, ("ground_striking", "top_control", "elbows", "punch_power"), fighter.ground_control) * 0.48,
                "advance_position": self.ds_avg(fighter, ("transitions", "positional_ability", "scrambles", "mount_control"), fighter.grappling),
                "submission": self.skill_bundle(fighter, "submission_game") * sub_multiplier,
            }
            if tired:
                weights["advance_position"] *= 0.6
                weights["submission"] *= 0.7
            self.apply_style_bias(fighter, weights, "top")
            return self.weighted_choice(weights)
        weights = {
            "recover_guard": self.ds_avg(fighter, ("guard_work", "bottom_control", "flexibility", "submission_defence_detail"), fighter.grappling),
            "sweep": self.ds_avg(fighter, ("scrambles", "bottom_control", "transitions", "strength"), fighter.grappling),
            "bottom_submission": self.ds_avg(fighter, ("submission_attack", "guard_work", "leg_locks", "confidence"), fighter.submissions) * (1.28 if fighter.behaviour == "Submission Hunter" else 0.78),
            "cling": mental + self.ds(fighter, "resilience", fighter.toughness) + (20 if tired else 0),
            "stand_up": self.ds_avg(fighter, ("get_ups", "scrambles", "sprawl", "conditioning"), fighter.takedown_defence),
        }
        self.apply_style_bias(fighter, weights, "bottom")
        return self.weighted_choice(weights)

    def weighted_choice(self, weights):
        cleaned = {key: max(1, int(value)) for key, value in weights.items()}
        total = sum(cleaned.values())
        pick = random.randint(1, total)
        running = 0
        for key, value in cleaned.items():
            running += value
            if pick <= running:
                return key
        return next(iter(cleaned))

    def fight_phrase(self, category, actor, defender, **context):
        templates = {
            "round_start": [
                "both fighters take the centre and begin reading range.",
                "{A} circles at long range while {B} looks for the first opening.",
                "{A} inches forward behind a high guard as {B} gives ground.",
                "the fighters exchange feints without fully committing.",
                "{A} switches stance while {B} hovers at boxing range.",
            ],
            "jab_land": [
                "{A} snaps {B}'s head back with a stiff jab.",
                "{A} lands a clean one-two and exits before {B} can answer.",
                "{A} splits the guard with a straight punch.",
                "{A} doubles the jab and disrupts {B}'s stance.",
                "{A} lands a long straight at maximum range.",
            ],
            "jab_miss": [
                "{A}'s jab falls short as {B} shifts backward.",
                "{B} parries the jab and keeps the range.",
                "{A} reaches with the jab and is left out of position.",
                "{B} slips outside the straight punch.",
            ],
            "power_land": [
                "{A} lands a heavy hook that turns {B}'s head.",
                "{A} catches {B} with a loaded overhand.",
                "{A} steps in with a powerful straight right.",
                "{A} lands an uppercut through the middle.",
                "{A} catches {B} cleanly with a compact hook.",
            ],
            "power_miss": [
                "{A} loads up and misses wide.",
                "{B} rolls beneath the return punch.",
                "{A}'s overhand sails over {B}'s shoulder.",
                "{B} blocks the power shot on the forearms.",
            ],
            "dirty_boxing_land": [
                "{A} lands short punches in the tie-up.",
                "{A} sneaks an uppercut through the clinch.",
                "{A} scores with shoulder-pressure boxing.",
                "{A} digs inside punches while leaning on {B}.",
            ],
            "ground_strikes_land": [
                "{A} lands short punches from top control.",
                "{A} postures and drops elbows from the top.",
                "{A} chips away with ground-and-pound.",
                "{A} traps a wrist and lands heavy shots on the mat.",
            ],
            "low_kick_land": [
                "{A} chops the lead leg with a low kick.",
                "{A} lands a calf kick that changes {B}'s stance.",
                "{A} slams a hard kick into the body and leg.",
                "{A} feints high and attacks the lead leg.",
            ],
            "high_kick_land": [
                "{A} whips a high kick around the guard.",
                "{A} fires a fast head kick that clips {B}.",
                "{A} disguises the high kick behind a feint.",
                "{A} sends a high round kick crashing into the guard and head.",
            ],
            "kick_miss": [
                "{A}'s kick whistles past the target.",
                "{B} slides out of range before the kick lands.",
                "{A} over-rotates on the kick and has to reset.",
                "{B} reads the kick and checks it cleanly.",
            ],
            "kick_caught": [
                "{B} catches the kick and dumps {A} to the mat.",
                "{B} times the kick, scoops the leg, and turns it into a takedown.",
                "{B} catches the body kick and runs {A} down to the canvas.",
            ],
            "knockdown": [
                "{A} lands {technique} and drops {B}!",
                "{A} catches {B} clean with {technique}; {B} hits the mat!",
                "{B} stumbles badly after {A} lands {technique}.",
            ],
            "cut": [
                "{A} opens visible damage on {B}.",
                "{B} is cut after {A}'s clean strike gets through.",
                "swelling starts to show around {B}'s eye after {A}'s shot lands.",
            ],
            "clinch_entry": [
                "{A} uses a jab feint to enter the clinch.",
                "{A} closes distance and locks {B} into the tie-up.",
                "{A} crowds {B} and denies striking space.",
                "{A} gets chest-to-chest before {B} can circle away.",
            ],
            "clinch_denied": [
                "{B} circles out before {A} can establish the clinch.",
                "{B} frames against {A}'s shoulder and escapes.",
                "{A} reaches for the clinch, but {B} pivots away.",
            ],
            "cage_control": [
                "{A} pins {B} to the fence and drains the clock.",
                "{A} turns {B} toward the cage and leans heavy.",
                "{A} controls the wrists against the fence.",
            ],
            "cage_escape": [
                "{B} refuses to be wall-stalled and escapes to open space.",
                "{B} pummels inside and circles off the fence.",
                "{B} creates a frame and slips away from the cage.",
            ],
            "break_clinch": [
                "{A} breaks free and resets at range.",
                "{A} peels the hands away and exits the clinch.",
                "{A} circles off before {B} can keep the tie-up.",
            ],
            "takedown_complete": [
                "{A} changes levels and completes the takedown into {position}.",
                "{A} drives through the hips and lands on top in {position}.",
                "{A} chains the shot beautifully and settles in {position}.",
            ],
            "slam_takedown": [
                "{A} blasts through with a slam takedown into {position}.",
                "{A} lifts, turns the corner, and dumps {B} into {position}.",
            ],
            "takedown_cage": [
                "{A} cannot finish the shot but drives {B} to the cage.",
                "{A} runs {B} to the fence and keeps working for the legs.",
                "{B} stays upright, but {A} has them pinned on the cage.",
            ],
            "takedown_denied": [
                "{B} sprawls hard and denies the takedown.",
                "{B} stuffs the shot and circles back to space.",
                "{B} gets the hips back before {A} can connect the hands.",
            ],
            "pass": [
                "{A} advances to {position}.",
                "{A} clears the knee shield and moves to {position}.",
                "{A} wins the transition and settles in {position}.",
            ],
            "pass_denied": [
                "{B} blocks the pass and keeps {A} from improving.",
                "{B} frames hard and recovers enough space to stop the pass.",
                "{B} traps a leg and denies the advance.",
            ],
            "recover_guard": [
                "{A} recovers guard and reduces the danger.",
                "{A} shrimps back to guard before {B} can settle.",
                "{A} gets the legs back in play and slows the attack.",
            ],
            "hold_position": [
                "{B} keeps the dominant position.",
                "{B} stays heavy and denies the guard recovery.",
                "{B} rides the hips and keeps {A} pinned.",
            ],
            "top_control": [
                "{A} keeps heavy top pressure and limits {B}'s options.",
                "{A} controls the wrists and smothers {B}'s hips.",
                "{A} stays patient from top and makes {B} carry the weight.",
            ],
            "ref_standup": [
                "{A} stalls from top and the referee stands them up.",
                "the action slows on the mat and the referee orders a stand-up.",
            ],
            "sweep": [
                "{A} times a sweep and reverses to top position.",
                "{A} elevates the hips and comes up on top.",
                "{A} uses the scramble to reverse the position.",
            ],
            "sweep_denied": [
                "{A} tries to sweep, but {B} stays heavy.",
                "{B} posts out and kills the sweep attempt.",
                "{B} keeps balance and shuts down the reversal.",
            ],
            "stand_up": [
                "{A} builds up and gets back to the feet.",
                "{A} wall-walks back to standing.",
                "{A} posts on the mat and escapes to open space.",
            ],
            "mat_return": [
                "{B} mat-returns {A} before the escape is complete.",
                "{B} drags {A} back down and keeps top control.",
            ],
            "cling": [
                "{A} ties up wrists from bottom and slows the damage.",
                "{A} clamps down from guard and forces a slower pace.",
                "{A} holds on and buys recovery time.",
            ],
            "submission_finish": [
                "{A} traps {B} in a tight submission and forces the tap.",
                "{A} connects the submission chain and {B} has to tap.",
                "{A} cinches the finish before {B} can escape.",
            ],
            "submission_danger": [
                "{A} locks on a dangerous submission, but {B} survives.",
                "{B} stays composed through a deep submission threat.",
                "{A} attacks the neck and forces {B} into emergency defence.",
            ],
            "submission_threat": [
                "{A} threatens a submission and makes {B} defend carefully.",
                "{A} isolates a limb and forces {B} to react.",
                "{A} starts a submission chain from the position.",
            ],
            "submission_defended": [
                "{A} looks for a submission, but the defence is ready.",
                "{B} reads the setup and keeps the submission from locking in.",
                "{A} attacks, but {B} stays calm and clears the danger.",
            ],
            "survive": [
                "{A} shells up, breathes, and tries to recover.",
                "{A} covers up and focuses on surviving the moment.",
                "{A} clinches defensively to buy time.",
            ],
            "ko_finish": [
                "{A} lands a perfect right hand and {B} collapses instantly.",
                "{A} catches {B} clean and switches the lights off.",
                "{A} threads a straight punch through the guard and ends the fight.",
                "{A} lands flush on the chin and {B} falls backward without resistance.",
                "{A} detonates a shot that leaves {B} limp before the referee arrives.",
            ],
            "walkoff_ko": [
                "{A} lands cleanly and walks away before {B} hits the canvas.",
                "{A} knows the fight is over and turns away after the punch lands.",
                "{A} drops {B} with a single shot and refuses to throw an unnecessary follow-up.",
            ],
            "head_kick_ko": [
                "{A} lands a clean head kick and {B} collapses instantly.",
                "{A}'s shin wraps around the guard and knocks {B} unconscious.",
                "{A} lands a question-mark kick that completely surprises {B}.",
            ],
            "signature_ko": [
                "{A} uncorks {technique} out of nowhere and {B} is unconscious before hitting the mat!",
                "{A} lands {technique} flush on the button - {B} goes stiff and drops!",
                "{A} catches {B} with {technique} and the fight is over the instant it lands!",
                "Highlight reel! {A} detonates {technique} and {B} is out cold!",
                "{A} throws {technique} on a hunch and it lands perfectly - {B} is done!",
            ],
            "standing_tko": [
                "{A} traps {B} against the fence and unloads with both hands.",
                "{B} shells up and absorbs a long unanswered combination.",
                "{A} overwhelms {B} against the fence and forces the stoppage.",
            ],
            "ground_tko": [
                "{A} postures up and lands repeated clean punches.",
                "{A} traps one wrist and strikes until {B} stops improving position.",
                "{A} secures dominant control and rains down unanswered shots.",
            ],
            "doctor": [
                "the doctor checks {B}'s facial damage and waves the fight off.",
                "{B}'s cut is too severe and the doctor stops the fight.",
                "the swelling prevents {B} from seeing clearly and the doctor calls it.",
            ],
            "corner_stoppage": [
                "{B}'s corner refuses to send them out for the next round.",
                "{B}'s corner waves off the fight after the accumulated damage.",
                "the corner has seen enough and tells the referee {B} cannot continue.",
            ],
            "injury_stoppage": [
                "{B} cannot place weight on the damaged leg and the fight is stopped.",
                "{B} signals that they cannot continue after the leg damage.",
                "{B}'s body gives out under the accumulated punishment.",
            ],
            "fatigue_tko": [
                "{B} is exhausted and no longer defending intelligently.",
                "{B} fades badly under the pressure and the referee steps in.",
            ],
            "ref_intervention": [
                "The referee steps between them and waves it off.",
                "The referee dives in to protect {B}.",
                "The referee pulls {A} away after the final strike.",
                "The referee has seen enough and stops the contest.",
            ],
            "late_ref": [
                "The referee is slow to intervene and {B} absorbs unnecessary follow-up shots.",
                "The stoppage comes late after prolonged punishment.",
                "The commentary team will question how long that was allowed to continue.",
            ],
            "early_ref": [
                "{B} immediately protests the stoppage.",
                "The stoppage appears cautious, but the referee prioritises safety.",
                "The crowd is split as {B} tries to return to their feet.",
            ],
            "aftermath": [
                "The crowd erupts as the fight ends.",
                "{A} checks on {B} before celebrating.",
                "Medical staff enter quickly as the official announcement is prepared.",
                "The replay is shown and the arena reacts all over again.",
            ],
            "official_finish": [
                "Official result: {A} wins by {method} at {time} of round {round_no}.",
                "The official time is {time} of round {round_no}; {A} wins by {method}.",
            ],
            "decision": [
                "Judges score it {score}. {A} wins by decision.",
                "After the scorecards are read, {A} takes the decision over {B} ({score}).",
                "The judges prefer {A}'s work. Official score before variance: {score}.",
            ],
            "draw": [
                "Judges score it {score}. The bout is declared a draw.",
                "After the scorecards are read, {A} and {B} fight to a draw ({score}).",
                "The cards are level at {score}; this one is officially a draw.",
            ],
        }
        template = random.choice(templates.get(category, ["{A} continues to work against {B}."]))
        return template.format(A=actor.name, B=defender.name, **context)

    def ds(self, fighter, key, fallback=50):
        skills = fighter.detailed_skills or {}
        return skills.get(key, fallback)

    def ds_avg(self, fighter, keys, fallback=50):
        return round(sum(self.ds(fighter, key, fallback) for key in keys) / max(1, len(keys)))

    def skill_bundle(self, fighter, bundle):
        bundles = {
            "boxing": ("punch_technique", "hand_speed", "footwork", "feints", "creative_punches"),
            "power_boxing": ("punch_power", "punch_technique", "hand_speed", "killer_instinct"),
            "kick_game": ("low_kick_technique", "low_kick_speed", "high_kick_technique", "high_kick_speed", "creative_kicks"),
            "strike_defence": ("head_movement", "guard_defence", "footwork", "reflexes"),
            "kick_defence": ("kick_defence", "mobility", "reflexes", "takedown_defence_detail"),
            "shot": ("takedowns", "takedown_setup", "takedown_speed", "chain_wrestling"),
            "anti_wrestling": ("takedown_defence_detail", "sprawl", "get_ups", "clinch_defence"),
            "clinch_attack": ("clinch_control", "dirty_boxing", "elbows", "knees", "thai_plum", "cage_pressure"),
            "clinch_defence": ("clinch_defence", "cage_wrestling", "strength", "balance"),
            "top_game": ("top_control", "positional_ability", "ride_control", "transitions", "ground_striking"),
            "bottom_game": ("guard_work", "bottom_control", "scrambles", "get_ups", "submission_defence_detail"),
            "submission_game": ("submission_attack", "back_control", "leg_locks", "positional_ability", "killer_instinct"),
            "submission_defence": ("submission_defence_detail", "guard_work", "composure", "flexibility"),
            "athleticism": ("conditioning", "strength", "mobility", "flexibility", "reflexes"),
            "durability": ("chin_strength", "resilience", "stun_recovery", "cut_immunity"),
            "mental": ("composure", "consistency", "adaptability", "discipline", "confidence"),
        }
        keys = bundles.get(bundle, ())
        return self.ds_avg(fighter, keys, fighter.overall)

    def resolve_exchange(self, actor, defender, action, state, round_stats):
        position = state["position"]
        attack = self.action_attack_value(actor, action, state)
        defence = self.action_defence_value(defender, action, state)
        margin = attack - defence + random.randint(-18, 18)

        if action in ("jab", "power_punch", "kick", "dirty_boxing", "ground_strikes"):
            state["unanswered"][defender.name] = state["unanswered"].get(defender.name, 0) + 1
            state["unanswered"][actor.name] = 0
            return self.resolve_strike(actor, defender, action, margin, state, round_stats)
        if action in ("shoot", "takedown"):
            return self.resolve_takedown(actor, defender, margin, state, round_stats)
        if action == "clinch":
            controller = state.get("clinch_controller")
            if controller and controller != actor.name:
                if margin > 7:
                    state["clinch_controller"] = actor.name
                    state["clinch_ticks"] = 0
                    state["position"] = "cage" if state["position"] == "cage" else "clinch"
                    round_stats[actor.name]["control"] += 2
                    return f"{actor.name} pummels inside, wins the underhook battle, and reverses {defender.name}."
                return f"{defender.name} keeps the stronger clinch position and denies the reversal."
            if margin > -5:
                state["position"] = "clinch"
                state["clinch_controller"] = actor.name
                state["clinch_ticks"] = 0
                round_stats[actor.name]["control"] += 1
                return self.fight_phrase("clinch_entry", actor, defender)
            return self.fight_phrase("clinch_denied", actor, defender)
        if action == "cage_control":
            controller = state.get("clinch_controller")
            if controller and controller != actor.name:
                if margin > 7:
                    state["clinch_controller"] = actor.name
                    state["position"] = "cage"
                    state["clinch_ticks"] = 0
                    round_stats[actor.name]["control"] += 3
                    return f"{actor.name} digs for double underhooks and turns {defender.name} onto the fence."
                return f"{defender.name} keeps {actor.name} pinned and wins the hand fight."
            if margin > -3:
                was_cage = state["position"] == "cage"
                state["position"] = "cage"
                state["clinch_controller"] = actor.name
                round_stats[actor.name]["control"] += 3
                state["clinch_ticks"] = state.get("clinch_ticks", 0) + 1
                if not was_cage:
                    return f"{actor.name} walks {defender.name} to the fence, settles head position, and locks the hands."
                return random.choice([
                    f"{actor.name} keeps {defender.name} on the fence with shoulder pressure and inside control.",
                    f"{actor.name} pins one wrist and uses the cage to keep {defender.name} from circling out.",
                    f"{actor.name} changes levels against the fence, forcing {defender.name} to defend the hips.",
                ])
            state["position"] = "range"
            state["clinch_controller"] = None
            state["clinch_ticks"] = 0
            return self.fight_phrase("cage_escape", defender, actor)
        if action == "break_clinch":
            if margin > -6:
                state["position"] = "range"
                state["clinch_controller"] = None
                state["clinch_ticks"] = 0
                return self.fight_phrase("break_clinch", actor, defender)
            round_stats[defender.name]["control"] += 1
            return f"{defender.name} keeps the tie-up and makes {actor.name} work."
        if action in ("advance_position", "recover_guard"):
            return self.resolve_position_move(actor, defender, action, margin, state, round_stats)
        if action in ("submission", "bottom_submission"):
            return self.resolve_submission(actor, defender, action, margin, state, round_stats)
        if action == "ground_control":
            round_stats[actor.name]["control"] += 3
            return self.fight_phrase("top_control", actor, defender)
        if action == "sweep":
            if margin > 10:
                state["top"] = actor.name
                state["bottom"] = defender.name
                state["position"] = "guard"
                round_stats[actor.name]["control"] += 4
                return self.fight_phrase("sweep", actor, defender)
            round_stats[defender.name]["control"] += 1
            return self.fight_phrase("sweep_denied", actor, defender)
        if action == "stand_up":
            if margin > 5:
                state["position"] = "range"
                state["top"] = None
                state["bottom"] = None
                return self.fight_phrase("stand_up", actor, defender)
            round_stats[defender.name]["control"] += 2
            return self.fight_phrase("mat_return", actor, defender)
        if action == "cling":
            round_stats[actor.name]["control"] += 1
            return self.fight_phrase("cling", actor, defender)
        if action == "survive":
            survive_recovery = 0.18 + self.ds(actor, "conditioning", actor.cardio) / 210 + actor.recovery / 420 + actor.camp_boost / 45
            state["gas"][actor.name] = min(state["gas_cap"][actor.name], state["gas"][actor.name] + survive_recovery)
            state["damage"][actor.name] = max(0, state["damage"][actor.name] - 1)
            if state["position"] in ("guard", "half guard", "side control", "mount", "back control"):
                if state.get("top") == actor.name:
                    return random.choice([
                        f"{actor.name} settles their weight and takes a breath without giving up top position.",
                        f"{actor.name} stays heavy on top and steadies the pace for a moment.",
                        f"{actor.name} rides the position, catching a breather while staying busy enough to hold it.",
                        f"{actor.name} postures just enough to keep control while recovering.",
                    ])
                return random.choice([
                    f"{actor.name} closes space from bottom, controls the wrists, and waits for a chance to improve.",
                    f"{actor.name} ties up the hands from underneath and slows the exchange down.",
                    f"{actor.name} frames and hip-escapes just enough to stay in the fight.",
                    f"{actor.name} keeps a tight guard from the bottom and rides out the pressure.",
                ])
            if state["position"] in ("clinch", "cage"):
                return random.choice([
                    f"{actor.name} leans into the clinch and uses the tie-up to recover.",
                    f"{actor.name} buries their head on the chest in the clinch and catches a breath.",
                    f"{actor.name} pins the tie-up against the fence to steal a moment of rest.",
                    f"{actor.name} clings on in the clinch, slowing everything down to recover.",
                ])
            return self.fight_phrase("survive", actor, defender)
        return None

    def action_attack_value(self, fighter, action, state):
        gas = state["gas"][fighter.name]
        damage = state["damage"][fighter.name]
        leg_damage = state.get("leg", {}).get(fighter.name, 0)
        fatigue = (gas - 50) * 0.32
        low_gas_penalty = max(0, 32 - gas) * 0.45 + max(0, 12 - gas) * 0.9
        burst_actions = {"power_punch", "kick", "shoot", "takedown", "submission", "bottom_submission", "sweep", "stand_up"}
        base = {
            "jab": self.skill_bundle(fighter, "boxing") * 0.85 + self.ds(fighter, "reach", 50) * 0.18 + fighter.fight_iq * 0.18,
            "power_punch": self.skill_bundle(fighter, "power_boxing") * 0.65 + fighter.power * 0.55 + self.ds(fighter, "killer_instinct", 50) * 0.16,
            "kick": self.skill_bundle(fighter, "kick_game") * 0.85 + self.ds(fighter, "mobility", 50) * 0.22,
            "dirty_boxing": self.skill_bundle(fighter, "clinch_attack") * 0.75 + fighter.toughness * 0.2 + self.ds(fighter, "strength", 50) * 0.18,
            "ground_strikes": self.ds_avg(fighter, ("ground_striking", "top_control", "elbows", "punch_power"), fighter.ground_control) * 0.75 + fighter.power * 0.25,
            "shoot": self.skill_bundle(fighter, "shot") * 0.82 + self.ds(fighter, "conditioning", fighter.cardio) * 0.18,
            "takedown": self.ds_avg(fighter, ("clinch_takedowns", "throws", "chain_wrestling", "strength"), fighter.wrestling) * 0.78 + fighter.ground_control * 0.2,
            "cage_control": self.ds_avg(fighter, ("cage_pressure", "cage_wrestling", "clinch_control", "strength"), fighter.wrestling) * 0.78 + fighter.fight_iq * 0.22,
            "break_clinch": self.skill_bundle(fighter, "clinch_defence") * 0.75 + fighter.fight_iq * 0.22,
            "advance_position": self.ds_avg(fighter, ("transitions", "positional_ability", "scrambles", "mount_control"), fighter.grappling) * 0.72 + fighter.ground_control * 0.25,
            "recover_guard": self.skill_bundle(fighter, "bottom_game") * 0.8 + fighter.submission_defence * 0.2,
            "submission": self.skill_bundle(fighter, "submission_game") * 0.68 + fighter.grappling * 0.14,
            "bottom_submission": self.ds_avg(fighter, ("submission_attack", "guard_work", "leg_locks", "confidence"), fighter.submissions) * 0.66 + fighter.fight_iq * 0.14,
            "sweep": self.ds_avg(fighter, ("scrambles", "bottom_control", "transitions", "strength"), fighter.grappling) * 0.78 + fighter.wrestling * 0.18,
            "stand_up": self.ds_avg(fighter, ("get_ups", "scrambles", "sprawl", "conditioning"), fighter.takedown_defence) * 0.82 + fighter.cardio * 0.15,
        }.get(action, fighter.overall)
        trait = 6 if fighter.trait == "Clutch" and gas < 45 else 0
        if fighter.trait == "Comeback Artist" and damage > fighter.toughness * 0.45:
            trait += 7
        if fighter.trait == "Fast Starter" and state["round"] == 1 and state.get("early_round", False):
            trait += 6
        if fighter.trait == "Cardio Machine" and state["round"] >= 2 and gas > 38:
            trait += 5
        if fighter.trait == "Title Mentality" and state["round"] >= 4:
            trait += 6
        if fighter.trait == "Warrior Spirit" and (gas < 42 or damage > fighter.toughness * 0.42):
            trait += 4
        if fighter.trait == "Momentum Fighter":
            trait += max(0, fighter.momentum) * 1.5
        if fighter.trait == "Cage Specialist" and action in ("cage_control", "takedown", "dirty_boxing"):
            trait += 5
        if fighter.trait == "Elbow Specialist" and action == "dirty_boxing":
            trait += 4
        if fighter.trait == "Scramble Artist" and action in ("sweep", "recover_guard", "stand_up"):
            trait += 5
        if fighter.trait == "Fight Finisher" and action in ("power_punch", "kick", "ground_strikes", "submission", "bottom_submission") and damage > fighter.toughness * 0.3:
            trait += 4
        if fighter.trait == "Front Runner" and damage > fighter.toughness * 0.35:
            trait -= 6
        if fighter.trait == "Bad Weight Cut":
            trait -= max(2, fighter.weight_cut_penalty // 2)
        erratic = random.randint(-7, 7) if fighter.trait == "Erratic" else 0
        consistency = (self.ds(fighter, "consistency", 50) - 50) * 0.07
        action_drag = low_gas_penalty * (1.35 if action in burst_actions else 0.65)
        context = self.context_edge(fighter, state, "prime", "experience", "pressure", "rivalry")
        if action in ("jab", "power_punch", "kick", "dirty_boxing"):
            context += self.context_edge(fighter, state, "stance", "reach")
        if action in ("shoot", "takedown", "cage_control", "ground_control"):
            context += self.context_edge(fighter, state, "size")
        if action in ("submission", "bottom_submission"):
            context += self.context_edge(fighter, state, "experience")
        leg_drag = leg_damage * (0.26 if action in ("kick", "shoot", "takedown", "stand_up") else 0.08)
        return base + fatigue + fighter.momentum * 1.5 + fighter.camp_boost * 1.6 + trait + erratic + consistency + context - action_drag - leg_drag

    def action_defence_value(self, fighter, action, state):
        gas = state["gas"][fighter.name]
        damage = state["damage"][fighter.name]
        leg_damage = state.get("leg", {}).get(fighter.name, 0)
        gas_drag = max(0, 34 - gas) * 0.38 + max(0, 12 - gas) * 0.72
        base = self.skill_bundle(fighter, "mental") * 0.1 + fighter.recovery * 0.08
        if action in ("jab", "power_punch", "kick", "dirty_boxing", "ground_strikes"):
            if action == "kick":
                base += self.skill_bundle(fighter, "kick_defence") * 0.48 + fighter.chin * 0.2 + fighter.toughness * 0.24
            elif action == "ground_strikes":
                base += self.skill_bundle(fighter, "bottom_game") * 0.45 + self.ds(fighter, "stun_recovery", fighter.recovery) * 0.2 + fighter.toughness * 0.26
            else:
                base += self.skill_bundle(fighter, "strike_defence") * 0.48 + fighter.chin * 0.22 + fighter.toughness * 0.24
        elif action in ("shoot", "takedown", "cage_control"):
            base += self.skill_bundle(fighter, "anti_wrestling") * 0.58 + fighter.wrestling * 0.2
        elif action in ("submission", "bottom_submission"):
            base += self.skill_bundle(fighter, "submission_defence") * 0.82 + fighter.grappling * 0.2
        else:
            base += self.skill_bundle(fighter, "bottom_game") * 0.45 + fighter.wrestling * 0.2
        context = self.context_edge(fighter, state, "prime", "experience", "pressure")
        if action in ("jab", "power_punch", "kick", "dirty_boxing"):
            context += self.context_edge(fighter, state, "stance", "reach")
        if action in ("shoot", "takedown", "cage_control"):
            context += self.context_edge(fighter, state, "size")
        mobility_drag = leg_damage * (0.18 if action in ("kick", "shoot", "takedown", "cage_control") else 0.07)
        return base + fighter.camp_boost * 1.2 + (gas - 50) * 0.24 - damage * 0.22 - gas_drag - mobility_drag + (self.ds(fighter, "reflexes", 50) - 50) * 0.05 + context

    def apply_exchange_fatigue(self, actor, defender, action, state):
        costs = {
            "jab": 1,
            "power_punch": 4,
            "kick": 4,
            "shoot": 6,
            "clinch": 3,
            "dirty_boxing": 3,
            "takedown": 6,
            "cage_control": 4,
            "break_clinch": 3,
            "ground_control": 2,
            "ground_strikes": 4,
            "advance_position": 5,
            "submission": 6,
            "recover_guard": 4,
            "sweep": 5,
            "bottom_submission": 5,
            "cling": 1,
            "stand_up": 5,
            "survive": 0,
        }
        conditioning = self.ds(actor, "conditioning", actor.cardio)
        defender_conditioning = self.ds(defender, "conditioning", defender.cardio)
        efficiency = 1 - max(-0.16, min(0.26, (conditioning - 55) / 240 + (self.ds(actor, "discipline", 50) - 50) / 470))
        actor_cost = costs.get(action, 2) * self.engine_settings.get("gas_cost", 1.0) * efficiency
        if state["gas"][actor.name] < 30 and action in ("power_punch", "kick", "shoot", "takedown", "submission", "sweep", "stand_up"):
            actor_cost *= 1.22
        if actor.trait == "Cardio Machine":
            actor_cost *= 0.9
        if actor.trait == "Warrior Spirit" and state["gas"][actor.name] < 35:
            actor_cost *= 0.94
        if actor.trait == "Bad Weight Cut":
            actor_cost *= 1.14
        defender_efficiency = 1 - max(-0.12, min(0.20, (defender_conditioning - 55) / 280))
        defender_cost = max(0.7, actor_cost * 0.5 * defender_efficiency)
        if state["body"][actor.name] > 12:
            actor_cost += 1 + state["body"][actor.name] / 28
        if state["body"][defender.name] > 12:
            defender_cost += 1 + state["body"][defender.name] / 32
        state["gas"][actor.name] = max(3, min(state["gas_cap"][actor.name], state["gas"][actor.name] - actor_cost))
        state["gas"][defender.name] = max(3, min(state["gas_cap"][defender.name], state["gas"][defender.name] - defender_cost))

    def flush_knockout_chance(self, actor, defender, power, margin, creativity=50):
        """Puncher's chance: probability that a strike lands so flush it ends the fight
        cold, independent of round or accumulated damage. Driven by how clean the connect
        is (margin), the striker's power, killer instinct and creativity (spectacular,
        technical strikers land more highlight-reel finishes), with a small floor so even
        an underdog can land the perfect shot at any moment."""
        cleanliness = max(0, margin)
        chin = defender.chin
        recovery = self.ds(defender, "stun_recovery", defender.recovery)
        killer = self.ds(actor, "killer_instinct", 50)
        average_level = (actor.overall + defender.overall) / 2
        low_level_chaos = max(0, 68 - average_level) / 68
        elite_control = max(0, average_level - 78) / 14
        chance = (0.0025
                  + cleanliness / 1200
                  + max(0, power - chin) / 2000
                  + (power - 55) / 4200
                  + max(0, killer - 55) / 4500
                  + max(0, creativity - 55) / 4000
                  - recovery / 4200
                  + low_level_chaos * 0.0045
                  - elite_control * 0.004)
        return max(0.0016, min(0.12, chance)) * self.engine_settings.get("ko_power", 1.0)

    def signature_technique(self, actor, action):
        """Pick a highlight-reel technique name; creative fighters unlock spinning /
        flying / exotic strikes."""
        if action == "power_punch":
            options = ["a flush overhand", "a perfectly timed counter right", "a short left hook on the button"]
            if self.ds(actor, "creative_punches", 50) > 60:
                options += ["a spinning backfist", "a superman punch", "a leaping left hook"]
        elif action == "high_kick":
            options = ["a head kick", "a question-mark kick"]
            if self.ds(actor, "creative_kicks", 50) > 60:
                options += ["a spinning back kick", "a flying knee", "a wheel kick", "a jumping switch kick"]
        elif action == "dirty_boxing":
            options = ["a short elbow", "a knee up the middle"]
            if self.ds(actor, "elbows", 50) > 58 or self.ds(actor, "knees", 50) > 58:
                options += ["a flying knee", "a spinning elbow", "an upward elbow on the break"]
        else:
            options = ["a clean shot"]
        return random.choice(options)

    def deliver_flush_knockout(self, actor, defender, action, state, round_stats):
        """Apply a sudden flush KO and register the instant finish with named technique."""
        state["danger"][actor.name] += 12
        round_stats[actor.name]["danger"] += 12
        state["damage"][defender.name] += 14
        state["knockdowns"][defender.name] += 1
        state["finish_category"] = "walkoff_ko" if random.random() < 0.45 else "ko_finish"
        technique = self.signature_technique(actor, action)
        detail = self.fight_phrase("signature_ko", actor, defender, technique=technique)
        state["instant_finish"] = (actor.name, defender.name, "KO", self.finish_sequence(actor, defender, "KO", detail, state))
        return self.fight_phrase("knockdown", actor, defender, technique=technique)

    def strike_volume(self, action, margin, landed=True, attempts=None):
        """Each commentary beat represents a small, explicit strike sequence, not one invisible strike.

        Pass a pre-drawn ``attempts`` when computing landed strikes for the same
        sequence, so the number that land can never exceed the number thrown."""
        if attempts is None:
            attempts = {
                "jab": random.randint(2, 5),
                "power_punch": random.randint(2, 4),
                "kick": random.randint(1, 3),
                "dirty_boxing": random.randint(2, 5),
                "ground_strikes": random.randint(3, 8),
            }.get(action, 1)
        if not landed:
            return attempts, 0
        accuracy = 0.46 + min(0.38, max(-0.1, margin) / 52)
        if action == "jab":
            accuracy += 0.12
        elif action == "ground_strikes":
            accuracy += 0.08
        return attempts, max(1, min(attempts, round(attempts * accuracy)))

    def resolve_strike(self, actor, defender, action, margin, state, round_stats):
        attempts, _ = self.strike_volume(action, margin, landed=False)
        state["stats"][actor.name]["sig_att"] += attempts
        if action == "kick":
            roll = random.random()
            high_chance = 0.26 + (self.ds(actor, "creative_kicks", 50) - 50) / 300
            body_share = 0.30 + (0.18 if actor.trait == "Body Hunter" else 0)
            leg_share = 1 - high_chance - body_share
            if actor.trait == "Leg Kicker":
                high_chance = max(0.15, high_chance - 0.08)
                body_share = max(0.18, body_share - 0.06)
                leg_share = 1 - high_chance - body_share
            kick_type = "high" if roll < high_chance else "body" if roll < high_chance + body_share else "leg"
            if kick_type == "high":
                kick_power = self.ds(actor, "high_kick_power", actor.power)
                kick_speed = self.ds(actor, "high_kick_speed", actor.striking)
                kick_tech = self.ds(actor, "high_kick_technique", actor.striking)
                defence = self.ds_avg(defender, ("kick_defence", "head_movement", "reflexes", "mobility"), defender.striking)
                label = random.choice(["a high kick", "a fast head kick", "a question-mark kick", "a high round kick"])
                body_gain, leg_gain = 0, 0
            else:
                kick_power = self.ds(actor, "low_kick_power", actor.power)
                kick_speed = self.ds(actor, "low_kick_speed", actor.striking)
                kick_tech = self.ds(actor, "low_kick_technique", actor.striking)
                defence = self.ds_avg(defender, ("kick_defence", "mobility", "reflexes", "takedown_defence_detail"), defender.striking)
                if kick_type == "body":
                    label = random.choice(["a hard body kick", "a digging round kick to the ribs", "a thudding kick to the midsection"])
                    body_gain, leg_gain = random.randint(2, 5), 0
                else:
                    label = random.choice(["a chopping low kick", "a calf kick", "an inside leg kick", "a hard kick to the thigh"])
                    body_gain, leg_gain = 0, random.randint(2, 5)
            kick_margin = margin + (kick_tech - defence) * 0.28 + (kick_speed - self.ds(defender, "reflexes", 50)) * 0.22
            catch_risk = max(0.03, 0.18 + (defender.wrestling - actor.takedown_defence) / 210 + (self.ds(defender, "takedowns", defender.wrestling) - kick_speed) / 280)
            if kick_margin < -13:
                if random.random() < catch_risk:
                    state["position"] = "guard"
                    state["top"] = defender.name
                    state["bottom"] = actor.name
                    round_stats[defender.name]["control"] += 4
                    return self.fight_phrase("kick_caught", actor, defender)
                return self.fight_phrase("kick_miss", actor, defender)
            if kick_margin < 4 and random.random() < catch_risk * 0.35:
                state["position"] = "guard"
                state["top"] = defender.name
                state["bottom"] = actor.name
                round_stats[defender.name]["control"] += 4
                return self.fight_phrase("kick_caught", actor, defender)
            _attempts, landed = self.strike_volume(action, kick_margin, landed=True, attempts=attempts)
            state["stats"][actor.name]["sig"] += landed
            impact = max(1, round((kick_margin + kick_power * 0.25 + kick_speed * 0.09) / 10 * self.engine_settings.get("damage", 1.0)))
            if kick_type == "body":
                state["body"][defender.name] += body_gain
                state["gas"][defender.name] = max(3, state["gas"][defender.name] - max(1, body_gain))
            elif kick_type == "leg":
                state["leg"][defender.name] += leg_gain
                state["gas"][defender.name] = max(3, state["gas"][defender.name] - max(1, leg_gain // 2))
            else:
                impact += 1
            state["damage"][defender.name] += impact
            round_stats[actor.name]["impact"] += impact
            if kick_type == "high" and random.random() < self.flush_knockout_chance(actor, defender, kick_power, kick_margin, self.ds(actor, "creative_kicks", 50)):
                return self.deliver_flush_knockout(actor, defender, "high_kick", state, round_stats)
            if random.random() < max(0.028, (impact + kick_power * 0.9 + kick_speed * 0.24 - defender.chin - self.ds(defender, "stun_recovery", defender.recovery) * 0.22) / 125):
                state["danger"][actor.name] += 9
                round_stats[actor.name]["danger"] += 9
                state["damage"][defender.name] += 8
                state["knockdowns"][defender.name] += 1
                state["finish_category"] = "head_kick_ko" if kick_type == "high" else "injury_stoppage"
                clean_ko_chance = max(0.08, min(0.8, (kick_power + kick_speed + impact * 7.4 - defender.chin - self.ds(defender, "stun_recovery", defender.recovery) * 0.42) / 122))
                if kick_type == "high" and random.random() < clean_ko_chance:
                    detail = self.fight_phrase("head_kick_ko", actor, defender)
                    state["instant_finish"] = (actor.name, defender.name, "KO", self.finish_sequence(actor, defender, "KO", detail, state))
                return self.fight_phrase("knockdown", actor, defender, technique=label)
            if kick_type == "high":
                return self.fight_phrase("high_kick_land", actor, defender)
            if kick_type == "body":
                return f"{actor.name} lands {label} and forces {defender.name} to protect the body."
            return f"{actor.name} lands {label}; {defender.name}'s movement is starting to slow."
        if margin < -12:
            return self.fight_phrase("jab_miss" if action == "jab" else "power_miss", actor, defender)
        impact = max(1, round((margin + actor.power * 0.34 + 2.3) / 8.5 * self.engine_settings.get("damage", 1.0)))
        if action == "jab":
            impact = max(1, impact - 2)
        if action == "ground_strikes":
            impact = max(1, impact - 1)
            round_stats[actor.name]["control"] += 1
        clinch_detail = ""
        if action == "dirty_boxing":
            elbow = self.ds(actor, "elbows", 50)
            knee = self.ds(actor, "knees", 50)
            dirty = self.ds(actor, "dirty_boxing", actor.striking)
            weapon = self.weighted_choice({"elbow": elbow, "knee": knee, "punch": dirty})
            if weapon == "elbow":
                impact += 1
                cut_chance = max(0.04, (elbow + impact * 3 - self.ds(defender, "cut_immunity", 50)) / 180)
                if random.random() < cut_chance:
                    state["cuts"][defender.name] += 1
                    clinch_detail = f"{actor.name} slices {defender.name} with a short elbow in the clinch; a cut opens."
                else:
                    clinch_detail = f"{actor.name} lands a compact elbow over the top in the clinch."
            elif weapon == "knee":
                body_gain = max(2, round((knee + max(0, margin)) / 34))
                state["body"][defender.name] += body_gain
                state["gas"][defender.name] = max(3, state["gas"][defender.name] - body_gain)
                clinch_detail = f"{actor.name} drives a knee into {defender.name}'s body and makes them fold their elbows in."
            else:
                clinch_detail = f"{actor.name} lands short punches while controlling the inside position."
        if action == "kick":
            state["body"][defender.name] += random.randint(1, 4)
        state["damage"][defender.name] += impact
        _attempts, landed = self.strike_volume(action, margin, landed=True, attempts=attempts)
        state["stats"][actor.name]["sig"] += landed
        round_stats[actor.name]["impact"] += impact
        if action == "power_punch" and random.random() < self.flush_knockout_chance(actor, defender, self.ds(actor, "punch_power", actor.power), margin, self.ds(actor, "creative_punches", 50)):
            return self.deliver_flush_knockout(actor, defender, action, state, round_stats)
        if action == "dirty_boxing":
            clinch_power = self.ds_avg(actor, ("knees", "elbows"), actor.power)
            clinch_creativity = self.ds_avg(actor, ("knees", "elbows"), 50)
            if random.random() < self.flush_knockout_chance(actor, defender, clinch_power, margin, clinch_creativity) * 0.7:
                return self.deliver_flush_knockout(actor, defender, "dirty_boxing", state, round_stats)
        if random.random() < max(0.022, (impact + actor.power * 0.95 - defender.chin - self.ds(defender, "stun_recovery", defender.recovery) * 0.18) / 120):
            state["danger"][actor.name] += 8
            round_stats[actor.name]["danger"] += 8
            state["damage"][defender.name] += 8
            state["knockdowns"][defender.name] += 1
            state["finish_category"] = "walkoff_ko" if action == "power_punch" and impact > 9 and random.random() < 0.25 else "ko_finish"
            if action in ("power_punch", "dirty_boxing") and random.random() < max(0.04, min(0.58, (impact * 7.4 + actor.power - defender.chin - self.ds(defender, "stun_recovery", defender.recovery) * 0.25) / 112)):
                detail = self.fight_phrase(state["finish_category"], actor, defender)
                state["instant_finish"] = (actor.name, defender.name, "KO", self.finish_sequence(actor, defender, "KO", detail, state))
            return self.fight_phrase("knockdown", actor, defender, technique=self.action_label(action))
        cut_resistance = self.ds(defender, "cut_immunity", 50)
        if random.random() < max(0.008, (impact - defender.toughness / 24 - cut_resistance / 55) / 46):
            state["cuts"][defender.name] += 1
            return self.fight_phrase("cut", actor, defender)
        category = {
            "jab": "jab_land",
            "power_punch": "power_land",
            "dirty_boxing": "dirty_boxing_land",
            "ground_strikes": "ground_strikes_land",
        }.get(action, "power_land")
        if clinch_detail:
            return clinch_detail
        return self.fight_phrase(category, actor, defender)

    def resolve_takedown(self, actor, defender, margin, state, round_stats):
        state["stats"][actor.name]["td_att"] += 1
        shot_speed = self.ds(actor, "takedown_speed", actor.wrestling)
        setup = self.ds(actor, "takedown_setup", actor.wrestling)
        sprawl = self.ds(defender, "sprawl", defender.takedown_defence)
        size_edge = (self.ds(actor, "natural_size", 50) - self.ds(defender, "natural_size", 50)) * 0.08
        margin += (shot_speed + setup - sprawl - self.ds(defender, "takedown_defence_detail", defender.takedown_defence)) * 0.12 + size_edge
        if margin > 8:
            state["stats"][actor.name]["td"] += 1
            state["position"] = "half guard" if self.ds(actor, "chain_wrestling", actor.wrestling) > self.ds(defender, "scrambles", defender.grappling) + random.randint(-8, 12) else "guard"
            state["top"] = actor.name
            state["bottom"] = defender.name
            state["clinch_controller"] = None
            round_stats[actor.name]["control"] += 5
            if self.ds(actor, "slams", actor.wrestling) > 68 and random.random() < 0.22:
                state["damage"][defender.name] += 3
                round_stats[actor.name]["impact"] += 3
                return self.fight_phrase("slam_takedown", actor, defender, position=self.position_label(state["position"]))
            return self.fight_phrase("takedown_complete", actor, defender, position=self.position_label(state["position"]))
        if margin > -8:
            state["position"] = "cage"
            state["clinch_controller"] = actor.name
            round_stats[actor.name]["control"] += 2
            return self.fight_phrase("takedown_cage", actor, defender)
        state["position"] = "range"
        state["clinch_controller"] = None
        round_stats[defender.name]["control"] += 2
        return self.fight_phrase("takedown_denied", actor, defender)

    def resolve_position_move(self, actor, defender, action, margin, state, round_stats):
        if action == "advance_position" and state["top"] == actor.name:
            margin += (self.ds(actor, "transitions", actor.grappling) + self.ds(actor, "positional_ability", actor.grappling) - self.ds(defender, "guard_work", defender.grappling) - self.ds(defender, "scrambles", defender.grappling)) * 0.13
            if margin > 6:
                next_pos = {"guard": "half guard", "half guard": "side control", "side control": "mount", "mount": "back control"}.get(state["position"], "side control")
                if next_pos == "mount" and self.ds(actor, "back_control", actor.grappling) > self.ds(actor, "mount_control", actor.grappling) + 8 and random.random() < 0.35:
                    next_pos = "back control"
                state["position"] = next_pos
                round_stats[actor.name]["control"] += 4
                round_stats[actor.name]["danger"] += 2
                return self.fight_phrase("pass", actor, defender, position=self.position_label(next_pos))
            round_stats[actor.name]["control"] += 1
            return self.fight_phrase("pass_denied", actor, defender)
        if action == "recover_guard":
            margin += (self.ds(actor, "guard_work", actor.grappling) + self.ds(actor, "flexibility", 50) - self.ds(defender, "ride_control", defender.ground_control) - self.ds(defender, "top_control", defender.ground_control)) * 0.1
            if margin > 8:
                state["position"] = "guard"
                round_stats[actor.name]["control"] += 2
                return self.fight_phrase("recover_guard", actor, defender)
            round_stats[defender.name]["control"] += 2
            return self.fight_phrase("hold_position", actor, defender)
        return None

    def resolve_submission(self, actor, defender, action, margin, state, round_stats):
        state["stats"][actor.name]["sub_att"] += 1
        sub_attack = self.skill_bundle(actor, "submission_game")
        sub_def = self.skill_bundle(defender, "submission_defence")
        technique = self.submission_technique(actor, action, state)
        danger_bonus = 9 if state["position"] in ("mount", "back control", "side control") else 0
        if state["position"] == "back control":
            danger_bonus += max(0, self.ds(actor, "back_control", actor.grappling) - 55) * 0.26
        if state["position"] == "mount":
            danger_bonus += max(0, self.ds(actor, "mount_control", actor.grappling) - 55) * 0.2
        if state["position"] in ("guard", "half guard"):
            # Elite submission artists threaten from guard/half guard (triangles, armbars, guillotines).
            danger_bonus += 5 + max(0, sub_attack - 55) * 0.24
        if action == "bottom_submission":
            danger_bonus += max(0, self.ds(actor, "guard_work", actor.grappling) - 55) * 0.17
        margin += (sub_attack - sub_def) * 0.12 + (self.ds(actor, "killer_instinct", 50) - self.ds(defender, "composure", 50)) * 0.07
        if margin + danger_bonus > 8:
            round_stats[actor.name]["danger"] += 14
            state["danger"][actor.name] += 14
            finish_boost = 1 + (self.ds(actor, "leg_locks", 50) - 50) / 750 if action == "bottom_submission" else 1
            hunter_boost = 1.12 if actor.behaviour == "Submission Hunter" else 1.0
            position_finish = 1.2 if state["position"] in ("mount", "back control") else 1.08 if state["position"] == "side control" else 0.92
            exhaustion_finish = 1 + max(0, 18 - state["gas"][defender.name]) / 100
            finish_chance = (0.085 + max(0, margin + danger_bonus) / 240) * finish_boost * hunter_boost * position_finish * exhaustion_finish * self.engine_settings.get("submission_finish", 1.0)
            if random.random() < min(0.56, finish_chance):
                technical = technique["choke"] and random.random() < max(0.08, (self.ds(defender, "toughness", defender.toughness) - self.ds(defender, "composure", defender.fight_iq)) / 360)
                state["submission_finish"] = (actor.name, defender.name, self.submission_finish_text(actor, defender, technique, technical), "Technical Submission" if technical else "Submission")
                return None
            state["gas"][defender.name] = max(5, state["gas"][defender.name] - 10)
            return self.fight_phrase("submission_danger", actor, defender)
        if margin > 0:
            round_stats[actor.name]["danger"] += 5
            return self.fight_phrase("submission_threat", actor, defender)
        if action == "bottom_submission" and margin < -10:
            state["top"] = defender.name
            state["bottom"] = actor.name
            round_stats[defender.name]["control"] += 2
            return f"{defender.name} shrugs off the submission attempt and settles back on top."
        return self.fight_phrase("submission_defended", actor, defender)

    def submission_technique(self, actor, action, state):
        position = state["position"]
        options = []
        if position == "back control":
            options.extend([("rear-naked choke", True, 6), ("armbar", False, 2)])
        if position in ("mount", "side control"):
            options.extend([("arm-triangle choke", True, 4), ("Americana", False, 2), ("armbar", False, 3)])
        if position in ("guard", "half guard") or action == "bottom_submission":
            options.extend([("guillotine choke", True, 3), ("triangle choke", True, 3), ("armbar", False, 3)])
            if self.ds(actor, "leg_locks", 50) > 62:
                options.extend([("heel hook", False, 2), ("kneebar", False, 1)])
        if not options:
            options = [("D'Arce choke", True, 2), ("kimura", False, 2), ("guillotine choke", True, 2)]
        expanded = []
        for technique, choke, weight in options:
            expanded.extend([(technique, choke)] * weight)
        technique, choke = random.choice(expanded)
        return {"name": technique, "choke": choke}

    def submission_finish_text(self, actor, defender, technique, technical=False):
        name = technique["name"]
        if technical:
            lines = [
                f"{actor.name} locks the {name} and {defender.name} refuses to tap.",
                f"The referee checks {defender.name}'s arm and receives no response.",
                f"{actor.name} releases immediately as the referee stops it. Technical submission.",
            ]
        else:
            lines = [
                f"{actor.name} creates the opening for the {name} and starts the attack.",
                f"{actor.name} secures the {name} and improves the angle.",
                f"{defender.name} fights the hands and tries to change the position.",
                f"{actor.name} tightens the finish as {defender.name}'s defence breaks down.",
                f"{defender.name} taps to the {name}.",
            ]
        return " ".join(lines)

    def check_fight_stoppage(self, actor, defender, state):
        if "instant_finish" in state:
            winner_name, loser_name, method, detail = state.pop("instant_finish")
            winner = actor if actor.name == winner_name else defender
            loser = actor if actor.name == loser_name else defender
            return winner, loser, method, detail
        if "submission_finish" in state:
            winner_name, loser_name, detail, method = state["submission_finish"]
            winner = actor if actor.name == winner_name else defender
            loser = actor if actor.name == loser_name else defender
            return winner, loser, method, self.finish_sequence(winner, loser, method, detail, state)
        for fighter, opponent in ((actor, defender), (defender, actor)):
            damage = state["damage"][fighter.name]
            gas = state["gas"][fighter.name]
            body = state["body"][fighter.name]
            leg = state.get("leg", {}).get(fighter.name, 0)
            cuts = state["cuts"][fighter.name]
            finisher_bonus = max(0, opponent.finishing_instinct - 55) / 260
            exhaustion_bonus = max(0, 28 - gas) / 180
            durability = self.skill_bundle(fighter, "durability")
            composure = self.ds(fighter, "composure", fighter.fight_iq)
            ko_threshold = fighter.chin * 0.52 + fighter.toughness * 0.31 + durability * 0.24 + composure * 0.09
            low_level_chaos = state.get("low_level_chaos", 0)
            elite_control = max(0, ((actor.overall + defender.overall) / 2) - 78) / 14
            championship_late = state.get("championship_pacing") and state.get("round", 1) >= 4
            ko_threshold -= low_level_chaos * 7.0
            ko_threshold += elite_control * 30.0
            if state.get("championship_pacing"):
                ko_threshold += 10.0 + composure / 30
            if championship_late:
                ko_threshold += 18.0 + composure / 16
            knockdowns = state["knockdowns"].get(fighter.name, 0)
            unanswered = state["unanswered"].get(fighter.name, 0)
            ref_mod = {"cautious": 0.04, "standard": 0.0, "permissive": -0.03, "late": -0.06}.get(state.get("referee"), 0)
            pacing_mod = (-0.08 if state.get("championship_pacing") else 0) + (-0.145 if championship_late else 0)
            low_mod = low_level_chaos * 0.065
            elite_mod = -elite_control * 0.16
            ko_chance = (0.108 + low_mod + pacing_mod + elite_mod + (damage - ko_threshold) / 240 + finisher_bonus * 1.08 + exhaustion_bonus + knockdowns * 0.085 + ref_mod) * self.engine_settings.get("ko_power", 1.0)
            if damage > ko_threshold and random.random() < ko_chance:
                clean = knockdowns >= 1 and unanswered < 5 and random.random() < 0.88
                method = "KO" if clean else "TKO"
                detail = self.finish_strike_text(opponent, fighter, state, clean=clean)
                return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, detail, state)
            unanswered_trigger = 5 if low_level_chaos >= 0.08 else 6
            unanswered_chance = 0.07 + ref_mod + unanswered * 0.014 + low_level_chaos * 0.035 - elite_control * 0.105 + (-0.06 if state.get("championship_pacing") else 0) + (-0.115 if championship_late else 0)
            if unanswered >= unanswered_trigger and (damage > fighter.toughness * (0.58 if low_level_chaos >= 0.08 else 0.62) or gas < 20) and random.random() < unanswered_chance:
                method = "TKO"
                category = "ground_tko" if state["position"] in ("guard", "half guard", "side control", "mount", "back control") else "standing_tko"
                detail = self.fight_phrase(category, opponent, fighter)
                return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, detail, state)
            if cuts >= 2 and random.random() < max(0.025, 0.18 + cuts * 0.06 - self.ds(fighter, "cut_immunity", 50) / 430):
                return opponent, fighter, "Doctor Stoppage", self.finish_sequence(opponent, fighter, "Doctor Stoppage", self.fight_phrase("doctor", opponent, fighter), state)
            if body > 24 and random.random() < max(0.05, (body - 18) / 130 + ref_mod):
                method = "Injury Stoppage"
                return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, self.fight_phrase("injury_stoppage", opponent, fighter), state)
            if leg > 29 and random.random() < max(0.02, (leg - 24) / 150 + ref_mod):
                method = "Injury Stoppage"
                detail = f"{fighter.name} can no longer put weight on the damaged leg and the referee stops the fight."
                return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, detail, state)
            if gas < 10 and damage > fighter.toughness * 0.78 and random.random() < max(0.025, 0.12 - self.ds(fighter, "resilience", fighter.toughness) / 760 + max(0, 8 - gas) / 150):
                return opponent, fighter, "TKO", self.finish_sequence(opponent, fighter, "TKO", self.fight_phrase("fatigue_tko", opponent, fighter), state)
        return None

    def finish_strike_text(self, winner, loser, state, clean=False):
        if clean:
            category = state.get("finish_category") or "ko_finish"
            if category == "injury_stoppage":
                category = "ko_finish"
            return self.fight_phrase(category, winner, loser)
        category = "ground_tko" if state["position"] in ("guard", "half guard", "side control", "mount", "back control") else "standing_tko"
        return self.fight_phrase(category, winner, loser)

    def finish_sequence(self, winner, loser, method, detail, state):
        parts = [detail]
        if method in ("KO", "TKO", "Technical Submission"):
            parts.append(self.fight_phrase("ref_intervention", winner, loser))
            if state.get("referee") == "late" and method == "TKO":
                parts.append(self.fight_phrase("late_ref", winner, loser))
            elif state.get("referee") == "cautious" and method == "TKO" and random.random() < 0.35:
                parts.append(self.fight_phrase("early_ref", winner, loser))
        parts.append(self.fight_phrase("official_finish", winner, loser, method=method, time=state.get("official_time", "0:00"), round_no=state.get("round", 1)))
        if random.random() < 0.55:
            parts.append(self.fight_phrase("aftermath", winner, loser))
        return " ".join(parts)

    def score_round(self, a, b, round_stats, state, judge=None):
        profile = (judge or {}).get("profile", "Balanced")
        def value(f):
            stats = round_stats[f.name]
            noise = max(1, round(4 * self.engine_settings.get("decision_noise", 1.0)))
            consistency = self.ds(f, "consistency", 50)
            judging_noise = random.randint(-noise, noise) * (1.15 - min(0.35, consistency / 260))
            discipline_bonus = max(0, self.ds(f, "discipline", 50) - 60) * 0.03
            gas_bonus = max(-3, min(4, (state["gas"][f.name] - 45) / 12))
            poise_bonus = self.context_edge(f, state, "home", "experience", "pressure") * 0.25
            # Effective striking and genuine danger lead under modern MMA scoring;
            # control matters most when it creates damage or threatening positions.
            if profile == "Damage-first":
                impact_weight, danger_weight, control_weight = 1.72, 2.16, 0.30
            elif profile == "Control-sensitive":
                impact_weight, danger_weight, control_weight = 1.32, 1.72, 0.68
            else:
                impact_weight, danger_weight, control_weight = 1.52, 1.95, 0.42
            control_weight += discipline_bonus + (0.12 if stats["impact"] + stats["danger"] >= 10 else 0)
            return stats["impact"] * impact_weight + stats["danger"] * danger_weight + stats["control"] * control_weight + gas_bonus + poise_bonus + judging_noise
        a_value = value(a)
        b_value = value(b)
        if abs(a_value - b_value) < 3:
            winner = a if random.random() < 0.5 else b
            loser = b if winner is a else a
            return winner, loser, 9
        winner = a if a_value > b_value else b
        loser = b if winner is a else a
        winner_stats = round_stats[winner.name]
        loser_stats = round_stats[loser.name]
        dominant_damage = winner_stats["impact"] >= loser_stats["impact"] + 20 or winner_stats["danger"] >= loser_stats["danger"] + 26
        dominant_control = winner_stats["control"] >= loser_stats["control"] + 18
        score = 8 if abs(a_value - b_value) > 72 and dominant_damage and (winner_stats["danger"] >= 20 or dominant_control) else 9
        return winner, loser, score

    def action_label(self, action):
        variants = {
            "jab": ["clean straight shots", "a sharp one-two", "a crisp jab-cross", "fast straight punches"],
            "power_punch": ["a heavy power punch", "a looping right hand", "a hard counter", "a loaded hook"],
            "kick": ["a kick to the body and leg", "a thudding body kick", "a chopping low kick", "a quick high-low kick sequence"],
            "dirty_boxing": ["short clinch punches", "inside uppercuts", "shoulder-pressure boxing", "short punches in the tie-up"],
            "ground_strikes": ["ground-and-pound", "short punches from top", "elbows from top control", "heavy shots on the mat"],
        }
        return random.choice(variants.get(action, [action.replace("_", " ")]))

    def position_label(self, position):
        return position.replace("_", " ")

    def style_matchup_bonus(self, fighter, opponent):
        # Rock-paper-scissors edges: grappling beats pure striking, striking beats
        # takedown-reliant grapplers who can't finish, awkward strikers trouble pressure.
        table = {
            ("Wrestler", "Boxer"): 5,
            ("Wrestler", "Kickboxer"): 5,
            ("Wrestler", "Muay Thai"): 4,
            ("Wrestler", "Karate"): 5,
            ("Freestyle Wrestler", "Boxer"): 5,
            ("Freestyle Wrestler", "Kickboxer"): 5,
            ("Freestyle Wrestler", "Taekwondo"): 5,
            ("Catch Wrestler", "Boxer"): 4,
            ("BJJ", "Wrestler"): 5,
            ("BJJ", "Freestyle Wrestler"): 4,
            ("Luta Livre", "Wrestler"): 4,
            ("Submission Grappler", "Wrestler"): 4,
            ("BJJ", "Judo"): 3,
            ("Sambo", "BJJ"): 4,
            ("Sambo", "Wrestler"): 3,
            ("Judo", "Boxer"): 4,
            ("Judo", "Kickboxer"): 3,
            ("Grappler", "Boxer"): 4,
            ("Grappler", "Kickboxer"): 4,
            ("Kickboxer", "BJJ"): 5,
            ("Kickboxer", "Wrestler"): 3,
            ("Dutch Kickboxer", "BJJ"): 5,
            ("Dutch Kickboxer", "Wrestler"): 3,
            ("Sanda", "Karate"): 3,
            ("Sanda", "Boxer"): 3,
            ("Boxer", "Karate"): 4,
            ("Boxer", "Taekwondo"): 4,
            ("Boxer", "BJJ"): 4,
            ("Muay Thai", "Boxer"): 4,
            ("Muay Thai", "Karate"): 3,
            ("Karate", "Muay Thai"): 3,
            ("Karate", "Wrestler"): 2,
            ("Well-Rounded", "Erratic"): 2,
        }
        return table.get((fighter.style, opponent.style), 0) - table.get((opponent.style, fighter.style), 0) / 2

    def finish_chance(self, leader, trailer, damage, gas, round_gap):
        finishing = 0.05 + max(0, round_gap - 10) / 170 + max(0, damage - trailer.chin / 2) / 260 + max(0, 45 - gas) / 300 + max(0, leader.finishing_instinct - 55) / 360
        if leader.trait == "Big Finisher":
            finishing += 0.06
        if leader.trait == "Fight Finisher":
            finishing += 0.035
        if trailer.trait == "Fragile":
            finishing += 0.05
        if leader.style in ("BJJ", "Sambo") and leader.grappling > trailer.grappling + 8:
            finishing += 0.04
        if leader.striking > trailer.chin + 8:
            finishing += 0.04
        return min(0.42, max(0.02, finishing))

    def finish_method(self, leader, trailer):
        sub_score = leader.grappling + (8 if leader.style in ("BJJ", "Sambo", "Wrestler") else 0)
        ko_score = leader.striking + (8 if leader.style in ("Boxer", "Kickboxer", "Muay Thai", "Karate") else 0)
        return "Submission" if sub_score + random.randint(-12, 12) > ko_score + random.randint(-12, 12) else "KO/TKO"
