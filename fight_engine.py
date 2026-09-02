import json
import random
import sys
import traceback
import zlib
from copy import deepcopy
from datetime import datetime
import tkinter as tk
from dataclasses import asdict, dataclass
from pathlib import Path
from tkinter import messagebox, ttk

from constants import *
from fight_moves import DEFENSE_REGISTRY, MOVE_REGISTRY, legal_defenses, legal_moves
from models import Fighter, Gym, Promotion


FIGHT_SKILL_BUNDLES = {
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

REPRESENTATIVE_SPECIALIST_MOVES = frozenset({
    "anaconda_choke", "body_jab", "chained_reshot", "darce_choke", "front_headlock_go_behind",
    "guillotine_choke", "heel_hook", "kneebar", "lift_mat_return", "limp_leg_escape",
    "rear_waist_ride", "sit_out_reversal", "snapdown_front_headlock", "straight_ankle_lock",
    "toe_hold", "turtle_breakdown", "whizzer_recovery",
})

TRAIT_COMMENTARY_INTROS = {
    "Fan Favourite": "The crowd response makes it clear that {name} is the fan favourite tonight.",
    "Fragile": "Durability has been the recurring question around {name} entering this fight.",
    "Clutch": "{name} has built a reputation for finding the right response when the pressure peaks.",
    "Slow Starter": "{name} often needs time to read the fight before settling into full output.",
    "Big Finisher": "When {name} creates a decisive opening, the fight can end in a hurry.",
    "Marketable": "{name} arrives with the attention and expectation that follow a marketable fighter.",
    "Gym Rat": "The reputation around {name} is built on steady, disciplined work in the gym.",
    "Erratic": "The challenge with {name} is the unpredictability from one exchange to the next.",
    "Weight Bully": "{name} is known for making physical size count once the cage door closes.",
    "Cardio Machine": "A sustained pace usually suits {name}, whose conditioning is a recognised strength.",
    "Fast Starter": "{name} is known for attacking the opening minutes before opponents can settle.",
    "Comeback Artist": "Even when a fight turns against {name}, a comeback remains part of the threat.",
    "Iron Chin": "Opponents have learned that clean contact does not easily discourage {name}.",
    "Glass Cannon": "{name} brings genuine danger, with durability adding tension to every exchange.",
    "Submission Ace": "Any extended grappling exchange gives {name} a chance to build a serious submission.",
    "Knockout Artist": "Every standing exchange carries knockout danger when {name} plants the feet.",
    "Pressure Fighter": "{name} does the best work while taking space and forcing a sustained pace.",
    "Counter Specialist": "{name} is most dangerous when an opponent commits first and leaves an opening.",
    "Showman": "{name} is comfortable making the crowd part of the performance.",
    "Trash Talker": "The words have already raised the temperature; now {name} has to back them up.",
    "Quiet Professional": "{name} has approached this assignment with the usual quiet professionalism.",
    "Coach Favourite": "The trust between {name} and the corner has been a consistent part of preparation.",
    "Bad Weight Cut": "The weight cut is the question hanging over {name}'s ability to sustain the pace.",
    "Injury Magnet": "Staying physically intact has been a recurring challenge in {name}'s career.",
    "Media Natural": "{name} carries the ease and attention of a fighter comfortable in the spotlight.",
    "Gym Leader": "{name} enters with the responsibility and composure expected of a gym leader.",
    "Front Runner": "{name} is particularly dangerous while dictating terms from the front.",
    "Late Bloomer": "{name}'s best work arrived later than expected, built through accumulated experience.",
    "Veteran Savvy": "Experience gives {name} a deep reserve of small adjustments and positional judgement.",
    "Prospect Mindset": "{name} still approaches each assignment as another step in a developing career.",
    "Short Notice Hero": "{name} has earned respect for being willing to answer difficult calls at short notice.",
    "Title Mentality": "The bigger the stakes, the more comfortable {name} has historically looked.",
    "Technical Learner": "{name} has a reputation for absorbing technical lessons and applying them quickly.",
    "Warrior Spirit": "Hard moments rarely persuade {name} to stop competing.",
    "Fast Healer": "{name} has generally recovered well from the physical demands between fights.",
    "Slow Healer": "Managing accumulated wear has often required patience in {name}'s preparation.",
    "Adaptable": "{name}'s strongest tactical quality is the ability to change the answer as the fight develops.",
    "Momentum Fighter": "Confidence and rhythm can make {name} increasingly difficult to slow once the run begins.",
    "Regional Star": "{name} brings the recognition and support earned as a regional star.",
    "Overlooked Talent": "Those close to the sport believe {name}'s ability has exceeded the wider recognition.",
    "Body Hunter": "{name} habitually invests in the body and looks for the effects to accumulate.",
    "Leg Kicker": "Damage to the opponent's base is a central part of {name}'s striking identity.",
    "Cage Specialist": "Fence position is rarely neutral against {name}, a recognised cage specialist.",
    "Elbow Specialist": "Small pockets of space are dangerous against {name}'s specialised elbow game.",
    "Scramble Artist": "Loose transitions tend to favour {name}'s instinctive scrambling ability.",
    "Fight Finisher": "Once an opponent is compromised, {name} is known for recognising the finishing window.",
}

@dataclass(frozen=True)
class FightResult:
    """Structured evidence from one completed MMA simulation.

    Existing callers continue to receive the legacy five-item tuple. New audit,
    replay, judging, and commentary work can consume this immutable result from
    ``simulate_fight_result()`` or ``_last_fight_result``.
    """

    winner_id: str
    loser_id: str
    method: str
    verdict: str
    round_no: int
    commentary: tuple
    trace: tuple
    scorecards: tuple
    metrics: dict
    rules: dict

    def legacy_tuple(self, fighter_a, fighter_b):
        if self.method in ("Draw", "No Contest"):
            return fighter_a, fighter_b, self.method, self.round_no, list(self.commentary)
        winner = fighter_a if getattr(fighter_a, "fighter_id", "") == self.winner_id else fighter_b
        loser = fighter_b if winner is fighter_a else fighter_a
        return winner, loser, self.method, self.round_no, list(self.commentary)


class FightEngineMixin:
    # These profiles describe officiating process only. They deliberately keep
    # the pre-profile stoppage and stand-up values, so naming the tendencies
    # does not silently recalibrate KO/TKO/finish rates.
    REFEREE_PROFILES = {
        "cautious": {"stoppage_modifier": 0.04, "standup_threshold": 4, "warning_style": "strict"},
        "standard": {"stoppage_modifier": 0.0, "standup_threshold": 5, "warning_style": "measured"},
        "permissive": {"stoppage_modifier": -0.03, "standup_threshold": 6, "warning_style": "patient"},
        "late": {"stoppage_modifier": -0.06, "standup_threshold": 7, "warning_style": "hands-off"},
    }
    GROUND_POSITIONS = frozenset({
        "guard", "half guard", "side control", "mount", "back control",
        "turtle", "front headlock", "leg entanglement",
    })
    STANDING_CONTROL_POSITIONS = frozenset({
        "clinch", "cage", "failed shot", "standing back control",
    })
    # These are presentation milestones over the existing calibrated head,
    # body, and leg trauma channels. Crossing one records visible evidence and
    # commentary, but never adds damage, consumes RNG, or creates a stoppage
    # roll. Only the highest newly crossed tier is emitted for one channel on
    # one exchange, preventing a single heavy strike from dumping four lines.
    VISIBLE_DAMAGE_MILESTONES = {
        "head": (
            (6, "face_reddening", "reddening across the face", "reddening"),
            (14, "facial_bruising", "facial bruising", "bruis"),
            (24, "general_swelling", "visible facial swelling", "swelling"),
            (38, "heavily_marked_face", "heavy facial damage", "damage"),
        ),
        "body": (
            (4, "torso_reddening", "reddening across the torso", "reddening"),
            (9, "body_bruising", "bruising across the body", "bruis"),
            (16, "guarded_midsection", "a guarded midsection", "midsection"),
            (24, "laboured_breathing", "laboured breathing", "breathing"),
        ),
        "leg": (
            (3, "leg_reddening", "reddening across the leg", "reddening"),
            (7, "leg_welt", "a welt on the damaged leg", "welt"),
            (12, "weight_shift", "weight shifting off the damaged leg", "weight"),
            (24, "visible_limp", "a visible limp", "limp"),
        ),
    }
    ALLOWED_FIGHT_TRANSITIONS = {
        "range": frozenset({"range", "pocket", "clinch", "cage", "failed shot", "guard", "half guard"}),
        "pocket": frozenset({"pocket", "range", "clinch", "cage", "failed shot", "guard", "half guard"}),
        "clinch": frozenset({"clinch", "cage", "range", "standing back control", "failed shot", "guard", "half guard"}),
        "cage": frozenset({"cage", "clinch", "range", "standing back control", "failed shot", "guard", "half guard"}),
        "failed shot": frozenset({"failed shot", "range", "cage", "front headlock", "guard"}),
        "standing back control": frozenset({"standing back control", "range", "cage", "back control", "guard"}),
        "guard": frozenset({"guard", "half guard", "range", "turtle", "leg entanglement"}),
        "half guard": frozenset({"half guard", "guard", "side control", "range", "turtle", "leg entanglement"}),
        "side control": frozenset({"side control", "mount", "back control", "guard", "range", "turtle"}),
        "mount": frozenset({"mount", "back control", "guard", "range", "turtle"}),
        "back control": frozenset({"back control", "side control", "guard", "range", "turtle"}),
        "turtle": frozenset({"turtle", "front headlock", "back control", "guard", "range"}),
        "front headlock": frozenset({"front headlock", "turtle", "back control", "guard", "range"}),
        "leg entanglement": frozenset({"leg entanglement", "guard", "half guard", "range"}),
    }

    @staticmethod
    def fight_state_key(fighter, state):
        """Return the private, collision-safe key for one live bout.

        Display names are intentionally non-unique in a career.  Live fight
        state must therefore never use ``fighter.name`` as a dictionary key.
        The slots are local to one simulation and are not serialized.
        """
        keys = state.get("fighter_keys", {})
        # Focused engine tests and older tooling can still construct a tiny
        # hand-written state dictionary.  Preserve that non-live compatibility
        # path; every real simulation installs collision-safe slots above.
        return keys.get(id(fighter), fighter.name)

    def validate_fight_transition(self, previous, current, state):
        """Reject illegal position changes and impossible ownership immediately."""
        allowed = self.ALLOWED_FIGHT_TRANSITIONS.get(previous, frozenset({previous}))
        if current not in allowed:
            raise AssertionError(f"Illegal fight position transition: {previous} -> {current}")
        top, bottom = state.get("top"), state.get("bottom")
        controller = state.get("clinch_controller")
        valid_keys = {"a", "b"}
        if current in self.GROUND_POSITIONS:
            if top not in valid_keys or bottom not in valid_keys or top == bottom or controller is not None:
                raise AssertionError(
                    f"Illegal ground ownership in {current}: top={top}, bottom={bottom}, controller={controller}"
                )
        elif top is not None or bottom is not None:
            raise AssertionError(f"Standing position {current} retained ground ownership")
        if current in ("failed shot", "standing back control") and controller not in valid_keys:
            raise AssertionError(f"Controlled standing position {current} has no legal controller")
        if current in ("range", "pocket") and controller is not None:
            raise AssertionError(f"Open-space position {current} retained a clinch controller")
        return True

    def set_fight_position(self, state, position, *, top=None, bottom=None, controller=None):
        """Apply one positional transition through the shared ownership boundary."""
        previous = state.get("position", "range")
        state["position"] = position
        state["top"] = top
        state["bottom"] = bottom
        state["clinch_controller"] = controller
        self.validate_fight_transition(previous, position, state)

    def record_intermediate_position(self, state, position, *, top=None, bottom=None, controller=None):
        """Record a legal within-exchange scramble state without changing its settled endpoint."""
        path = state.setdefault("intermediate_positions", [])
        previous = path[-1]["position"] if path else state.get("position", "range")
        probe = {"position": position, "top": top, "bottom": bottom, "clinch_controller": controller}
        self.validate_fight_transition(previous, position, probe)
        path.append(probe)

    def simulate_fight(self, a, b, fight):
        if a is b:
            raise ValueError("A fight requires two distinct fighters.")
        fight = dict(fight or {})
        cache_missing = object()
        previous_bundle_cache = getattr(self, "_fight_skill_bundle_cache", cache_missing)
        previous_conversion_cache = getattr(self, "_fight_finish_conversion_cache", cache_missing)
        previous_mechanics_rng = getattr(self, "_fight_mechanics_rng", cache_missing)
        previous_officiating_rng = getattr(self, "_fight_officiating_rng", cache_missing)
        previous_judging_rng = getattr(self, "_fight_judging_rng", cache_missing)
        previous_presentation_rng = getattr(self, "_fight_presentation_rng", cache_missing)
        self._fight_skill_bundle_cache = {}
        self._fight_finish_conversion_cache = {}
        source_rng_state = random.getstate()
        presentation_material = (
            repr(source_rng_state)
            + str(getattr(a, "fighter_id", "")) + str(getattr(b, "fighter_id", ""))
            + json.dumps(dict(fight or {}), sort_keys=True, default=str)
        )
        self._fight_mechanics_rng = random.Random()
        self._fight_mechanics_rng.setstate(source_rng_state)
        self._fight_officiating_rng = random.Random(
            zlib.crc32(("officiating:" + presentation_material).encode("utf-8"))
        )
        self._fight_judging_rng = random.Random(
            zlib.crc32(("judging:" + presentation_material).encode("utf-8"))
        )
        self._fight_presentation_rng = random.Random(zlib.crc32(presentation_material.encode("utf-8")))

        try:
            return self._simulate_fight_with_caches(a, b, fight)
        finally:
            # Preserve the public stream's historical progression semantics for
            # callers that run several bouts without explicitly reseeding.
            random.setstate(self._fight_mechanics_rng.getstate())
            if previous_bundle_cache is cache_missing:
                self.__dict__.pop("_fight_skill_bundle_cache", None)
            else:
                self._fight_skill_bundle_cache = previous_bundle_cache
            if previous_conversion_cache is cache_missing:
                self.__dict__.pop("_fight_finish_conversion_cache", None)
            else:
                self._fight_finish_conversion_cache = previous_conversion_cache
            if previous_mechanics_rng is cache_missing:
                self.__dict__.pop("_fight_mechanics_rng", None)
            else:
                self._fight_mechanics_rng = previous_mechanics_rng
            if previous_officiating_rng is cache_missing:
                self.__dict__.pop("_fight_officiating_rng", None)
            else:
                self._fight_officiating_rng = previous_officiating_rng
            if previous_judging_rng is cache_missing:
                self.__dict__.pop("_fight_judging_rng", None)
            else:
                self._fight_judging_rng = previous_judging_rng
            if previous_presentation_rng is cache_missing:
                self.__dict__.pop("_fight_presentation_rng", None)
            else:
                self._fight_presentation_rng = previous_presentation_rng

    def fight_presentation_rng(self):
        """Return the bout-local presentation stream, with a legacy fallback for focused helpers."""
        return getattr(self, "_fight_presentation_rng", random)

    def fight_mechanics_rng(self):
        """Return the bout-local combat stream, with focused-helper fallback."""
        return getattr(self, "_fight_mechanics_rng", random)

    def fight_officiating_rng(self):
        """Return the bout-local referee and judging stream."""
        return getattr(self, "_fight_officiating_rng", self.fight_mechanics_rng())

    def fight_judging_rng(self):
        """Return the judging substream so scorecard variance cannot alter stoppages."""
        return getattr(self, "_fight_judging_rng", self.fight_officiating_rng())

    def fight_presentation_choice(self, values):
        return self.fight_presentation_rng().choice(values)

    def fight_presentation_random(self):
        return self.fight_presentation_rng().random()

    def simulate_fight_result(self, a, b, fight):
        """Run a fight and return its structured result without changing legacy callers."""
        self.simulate_fight(a, b, fight)
        return self._last_fight_result

    @staticmethod
    def normalize_fight_plan(plan):
        candidate = str(plan or "Balanced").strip()
        return candidate if candidate in FIGHT_PLANS else "Balanced"

    @staticmethod
    def fighter_styles(fighter):
        primary = normalize_mma_style(getattr(fighter, "style", ""))
        secondary = normalize_secondary_style(getattr(fighter, "secondary_style", ""), primary)
        return (primary, secondary) if secondary else (primary,)

    def ai_fight_plan(self, fighter, opponent, fight):
        """Choose an AI plan from style, matchup, preparation and stakes."""
        if fighter.grappling >= fighter.striking + 7:
            return "Submission hunt" if fighter.submissions >= fighter.wrestling else "Wrestle early"
        if fighter.wrestling >= opponent.takedown_defence + 6:
            return "Wrestle early"
        styles = self.fighter_styles(fighter)
        if any(style in ("Wrestler", "Freestyle Wrestler", "Judo") for style in styles):
            return "Cage grind"
        if fighter.trait == "Body Hunter":
            return "Attack the body"
        if fighter.trait == "Leg Kicker" or any(
                style in ("Muay Thai", "Kickboxer", "Dutch Kickboxer") for style in styles):
            return "Damage the lead leg"
        if fighter.behaviour == "Counter" or fighter.trait == "Counter Specialist":
            return "Counter striking"
        if fighter.behaviour in ("Pressure", "Volume"):
            return "Pressure and volume"
        if fighter.cardio < 55 or fighter.weight_cut_penalty >= 10:
            return "Conserve energy"
        if fight.get("title") and fighter.fight_iq >= 72:
            return "Balanced"
        return "Balanced"

    def fight_plan_state(self, a, b, fight):
        supplied = fight.get("fight_plans", {}) if isinstance(fight.get("fight_plans", {}), dict) else {}
        result = {}
        for key, fighter, opponent in (("a", a, b), ("b", b, a)):
            fighter_id = str(getattr(fighter, "fighter_id", "") or "")
            requested = supplied.get(fighter_id, supplied.get(key))
            plan_enabled = requested is not None or bool(fight.get("ai_controlled"))
            if requested is None and fight.get("ai_controlled"):
                requested = self.ai_fight_plan(fighter, opponent, fight)
            plan = self.normalize_fight_plan(requested)
            coaching = max(0, min(100, (fighter.camp_quality or self.gym_quality(fighter.camp)) + fighter.camp_boost * 4))
            execution = max(0.45, min(1.1, (
                self.ds(fighter, "adaptability", fighter.fight_iq) * 0.28
                + self.ds(fighter, "discipline", 50) * 0.24
                + fighter.fight_iq * 0.28 + coaching * 0.20
            ) / 70))
            result[key] = {
                "initial": plan, "current": plan, "execution": round(execution, 3),
                "enabled": plan_enabled,
                "history": [{"round": 0, "plan": plan, "reason": "Pre-fight plan"}],
                "effective_actions": 0, "attempts": 0,
                "adjustments": 0, "last_adjustment_round": 0, "confidence": 0.5,
            }
        return result

    def fight_plan_for(self, fighter, state):
        return state.get("plans", {}).get(self.fight_state_key(fighter, state), {
            "initial": "Balanced", "current": "Balanced", "execution": 1.0,
            "history": [], "effective_actions": 0, "attempts": 0,
            "adjustments": 0, "last_adjustment_round": 0, "confidence": 0.5,
        })

    def apply_fight_plan_weights(self, fighter, opponent, state, phase, weights, round_no):
        """Apply a plan through action preference, never a result modifier."""
        row = self.fight_plan_for(fighter, state)
        plan, execution = row["current"], row["execution"]
        profiles = {
            "range": {
                "Pressure and volume": {"jab": 1.28, "power_punch": 1.18, "clinch": 1.14},
                "Counter striking": {"jab": 1.08, "power_punch": 1.06, "kick": 1.05, "clinch": 0.78},
                "Wrestle early": {"shoot": 1.52 if round_no <= 2 else 1.18, "clinch": 1.18, "kick": 0.82},
                "Cage grind": {"clinch": 1.58, "shoot": 1.16, "power_punch": 0.86},
                "Attack the body": {"jab": 1.12, "kick": 1.35, "power_punch": 1.08},
                "Damage the lead leg": {"kick": 1.58, "jab": 1.05, "shoot": 0.84},
                "Submission hunt": {"shoot": 1.52, "clinch": 1.12, "power_punch": 0.82},
                "Conserve energy": {"jab": 1.30, "power_punch": 0.62, "kick": 0.72, "shoot": 0.72, "clinch": 1.08},
                "Protect a lead": {"jab": 1.34, "power_punch": 0.68, "kick": 0.74, "shoot": 0.72, "clinch": 1.12},
                "Chase a finish": {"power_punch": 1.48, "kick": 1.24, "clinch": 1.12, "jab": 0.86},
            },
            "clinch": {
                "Pressure and volume": {"dirty_boxing": 1.28, "takedown": 1.08},
                "Counter striking": {"break_clinch": 1.42, "dirty_boxing": 0.84},
                "Wrestle early": {"takedown": 1.52, "cage_control": 1.18},
                "Cage grind": {"cage_control": 1.62, "takedown": 1.22, "break_clinch": 0.58},
                "Attack the body": {"dirty_boxing": 1.38},
                "Submission hunt": {"takedown": 1.45, "dirty_boxing": 0.78},
                "Conserve energy": {"cage_control": 1.28, "dirty_boxing": 0.72},
                "Protect a lead": {"cage_control": 1.34, "break_clinch": 1.16, "dirty_boxing": 0.74},
                "Chase a finish": {"dirty_boxing": 1.44, "takedown": 1.18},
            },
            "top": {
                "Pressure and volume": {"ground_strikes": 1.35, "ground_control": 0.88},
                "Submission hunt": {"submission": 1.62, "advance_position": 1.28, "ground_strikes": 0.78},
                "Conserve energy": {"ground_control": 1.42, "submission": 0.68, "ground_strikes": 0.72},
                "Protect a lead": {"ground_control": 1.52, "advance_position": 0.78, "submission": 0.70},
                "Chase a finish": {"ground_strikes": 1.45, "submission": 1.38, "ground_control": 0.68},
            },
            "bottom": {
                "Counter striking": {"stand_up": 1.30, "cling": 0.72},
                "Submission hunt": {"bottom_submission": 1.58, "sweep": 1.18},
                "Conserve energy": {"cling": 1.48, "stand_up": 0.72, "bottom_submission": 0.72},
                "Protect a lead": {"cling": 1.34, "recover_guard": 1.22, "bottom_submission": 0.68},
                "Chase a finish": {"bottom_submission": 1.42, "sweep": 1.24, "cling": 0.62},
            },
        }
        profile = profiles.get(phase, {}).get(plan, {})
        for action, multiplier in profile.items():
            if action in weights:
                weights[action] *= 1 + (multiplier - 1) * execution
        window = state.get("counter_window") or {}
        if plan == "Counter striking" and window.get("fighter") == self.fight_state_key(fighter, state):
            for action in ("jab", "power_punch", "kick", "dirty_boxing", "takedown", "submission", "bottom_submission"):
                if action in weights:
                    weights[action] *= 1 + 0.42 * execution
        return weights

    def plan_energy_multiplier(self, fighter, state):
        row = self.fight_plan_for(fighter, state)
        multiplier = {
            "Pressure and volume": 1.14, "Counter striking": 0.96,
            "Wrestle early": 1.08, "Cage grind": 0.94,
            "Conserve energy": 0.80, "Protect a lead": 0.86,
            "Chase a finish": 1.18,
        }.get(row["current"], 1.0)
        return 1 + (multiplier - 1) * row["execution"]

    @staticmethod
    def commentary_move_id_label(move_id):
        """Translate a trace move ID without exposing internal placeholders."""
        normalized = str(move_id or "").strip()
        if normalized.casefold() == "composed_survival":
            return "defensive survival"
        definition = MOVE_REGISTRY.get(normalized)
        if definition is not None:
            return str(definition.name or normalized.replace("_", " ")).strip()
        return normalized.replace("_", " ").strip() or "last exchange"

    def commentary_corner_speaker(self, fighter, opponent=None):
        """Name a verified coach/camp without assigning one coach to both stablemates."""
        identity = self.commentary_corner_identity(fighter)
        opponent_identity = self.commentary_corner_identity(opponent) if opponent is not None else {}
        shared_room = bool(
            identity.get("verified_gym") and opponent_identity.get("verified_gym")
            and identity.get("camp", "").casefold() == opponent_identity.get("camp", "").casefold()
        )
        if shared_room:
            return f"{fighter.name}'s {identity['camp']} corner"
        if identity.get("coach") and identity.get("camp"):
            return f"{identity['coach']} ({identity['camp']})"
        if identity.get("coach"):
            return identity["coach"]
        if identity.get("verified_gym") and identity.get("camp"):
            return f"the {identity['camp']} corner"
        return f"{fighter.name}'s corner"

    @staticmethod
    def commentary_corner_round_read(fighter, opponent, own, other, gas, deficit,
                                      repeated_label="", repeated_count=0,
                                      effective_family=""):
        """Summarise only completed, public evidence for a between-round read."""
        if other.get("knockdowns", 0) > own.get("knockdowns", 0):
            return f"{opponent.name} found the knockdown, so the defensive reset has to come first"
        if gas < 28:
            return "the pace is showing in your breathing"
        if deficit >= 8:
            return f"{opponent.name} produced the more damaging offense in that round"
        if repeated_count >= 3 and repeated_label:
            return f"{opponent.name} has shown the {repeated_label} {repeated_count} times"
        if effective_family:
            return f"your {effective_family.lower()} work produced the clearest success"
        if own.get("control_ticks", 0) >= 3:
            return "you earned useful control but need to turn more of it into offense"
        if deficit <= -8:
            return "your effective offense gave you the stronger round"
        return "the round was competitive and the next clean exchange can change its shape"

    def render_corner_feedback(self, fighter, opponent, round_no, review, instruction):
        """Render deterministic coach feedback in the selected broadcast personality."""
        speaker = self.commentary_corner_speaker(fighter, opponent)
        command = str(instruction or "stay composed and make the next exchange cleaner").strip()
        command = command[:1].upper() + command[1:]
        command = command.rstrip(".!?")
        review = str(review or "the round was competitive").strip().rstrip(".!?")
        voice = self.commentary_personality()
        if voice == "Technical":
            return (
                f"Technical corner - {speaker} to {fighter.name}: Read: {review}. "
                f"Adjustment: {command}."
            )
        if voice == "Excitable":
            return f"Corner urgency - {speaker} to {fighter.name}: {review}! {command}!"
        if voice == "Concise":
            return f"Corner - {speaker} to {fighter.name}: {command}."
        return f"Corner advice - {speaker} to {fighter.name}: {review}. {command}."

    def adapt_fight_plans(self, a, b, state, round_no, max_rounds):
        """Make corner adjustments from completed, observable trace evidence."""
        evidence = self.round_evidence_from_trace(state, round_no)
        advice = []
        advice_memory = state.setdefault("corner_advice_memory", {})
        for fighter, opponent in ((a, b), (b, a)):
            key, opponent_key = self.fight_state_key(fighter, state), self.fight_state_key(opponent, state)
            row = self.fight_plan_for(fighter, state)
            own, other = evidence[key], evidence[opponent_key]
            own_effect = own["impact"] + own["danger"] * 2 + own["effective_actions"]
            other_effect = other["impact"] + other["danger"] * 2 + other["effective_actions"]
            deficit = other_effect - own_effect
            adaptability = self.ds(fighter, "adaptability", fighter.fight_iq)
            discipline = self.ds(fighter, "discipline", 50)
            adaptive_ready = (adaptability + discipline + fighter.fight_iq) / 3 >= 58
            should_adjust = deficit >= 8 and adaptive_ready
            new_plan, reason = row["current"], "The corner keeps the current approach"
            gas = state["gas"][key]
            opponent_patterns = (state.get("move_reads") or {}).get(opponent_key, {}).get("moves", {})
            repeated_opponent_move = max(opponent_patterns, key=opponent_patterns.get, default="")
            repeated_count = opponent_patterns.get(repeated_opponent_move, 0)
            repeated_opponent_label = self.commentary_move_id_label(repeated_opponent_move)
            own_effective_family = max(
                own.get("effective_families", {}),
                key=own.get("effective_families", {}).get,
                default="",
            )
            round_read = self.commentary_corner_round_read(
                fighter, opponent, own, other, gas, deficit,
                repeated_opponent_label, repeated_count, own_effective_family,
            )
            if not row.get("enabled", False):
                if gas < 28:
                    observation = "slow the pace, recover behind position, and choose the next burst carefully"
                elif deficit >= 8:
                    observation = "raise the activity after conceding the cleaner offense"
                elif repeated_count >= 3:
                    observation = f"prepare for the repeated {repeated_opponent_label} and answer off the first read"
                elif own_effective_family:
                    observation = f"keep building behind the successful {own_effective_family.lower()} work"
                elif own.get("control_ticks", 0) >= 3:
                    observation = "keep the useful control, but turn it into clearer offense"
                else:
                    observation = "stay balanced and make the next exchange cleaner"
                if advice_memory.get(key) == observation:
                    observation = {
                        "slow the pace, recover behind position, and choose the next burst carefully":
                            "protect the remaining gas, then work in shorter bursts",
                        "raise the activity after conceding the cleaner offense":
                            "contest the center and make the next exchange count",
                        "stay balanced and make the next exchange cleaner":
                            "keep the shape, add a feint, and demand a clearer opening",
                    }.get(observation, "show a different look before returning to the best work")
                line = self.render_corner_feedback(
                    fighter, opponent, round_no, round_read, observation,
                )
                advice_memory[key] = observation
                advice.append(line)
                continue
            adjustment_ready = round_no > int(row.get("last_adjustment_round", 0))
            if gas < 25 and adaptive_ready and row["current"] != "Conserve energy":
                new_plan, reason = "Conserve energy", "the pace is draining the gas tank"
            elif round_no >= max_rounds - 1 and deficit >= 8 and adaptive_ready:
                new_plan, reason = "Chase a finish", "the damaging exchanges and remaining rounds demand urgency"
            elif round_no >= max_rounds - 1 and deficit <= -14 and adaptive_ready:
                new_plan, reason = "Protect a lead", "the effective offense has built a clear lead"
            elif (should_adjust and adjustment_ready and repeated_count >= 4
                  and self.ds(fighter, "counter_timing", fighter.fight_iq) >= 62):
                new_plan = "Counter striking"
                reason = f"the opponent has repeated {repeated_opponent_label}"
            elif should_adjust and adjustment_ready and own_effective_family:
                family_plan = {
                    "Submissions": "Submission hunt",
                    "Wrestling": "Wrestle early",
                    "Clinch": "Cage grind",
                    "Boxing": "Pressure and volume",
                    "Ground Striking": "Chase a finish",
                    "Transitions & Control": "Cage grind",
                }.get(own_effective_family)
                if family_plan:
                    new_plan = family_plan
                    reason = f"the {own_effective_family.lower()} family produced the clearest success"
            elif should_adjust and adjustment_ready:
                if own["submission_attempts"] or own["takedowns"] >= 2:
                    new_plan, reason = "Submission hunt", "the grappling entries created the best threats"
                elif own["control_ticks"] >= 3:
                    new_plan, reason = "Cage grind", "control has been the most reliable success"
                elif state["body"][opponent_key] >= state["head"][opponent_key] * 0.55:
                    new_plan, reason = "Attack the body", "the body work is visibly accumulating"
                elif state["leg"][opponent_key] >= 8:
                    new_plan, reason = "Damage the lead leg", "the opponent's movement is being compromised"
                else:
                    new_plan, reason = "Pressure and volume", "the current plan is conceding effective offense"
            if new_plan != row["current"]:
                row["current"] = new_plan
                row["adjustments"] = int(row.get("adjustments", 0)) + 1
                row["last_adjustment_round"] = round_no
                evidence_strength = max(0, min(1, (abs(deficit) + repeated_count * 2) / 32))
                row["confidence"] = round(0.5 + evidence_strength * 0.45, 3)
                row["history"].append({
                    "round": round_no, "plan": new_plan, "reason": reason,
                    "confidence": row["confidence"],
                    "evidence": {
                        "deficit": round(deficit, 2), "repeated_move": repeated_opponent_move,
                        "repeated_count": repeated_count, "best_effective_family": own_effective_family,
                    },
                })
                line = self.render_corner_feedback(
                    fighter, opponent, round_no, round_read,
                    f"Switch to {new_plan}; {reason}",
                )
                advice_memory[key] = line
                advice.append(line)
            else:
                if row["current"] == "Conserve energy" and gas < 35:
                    reason = "the gas tank still needs protection before the next sustained attack"
                elif own_effective_family:
                    reason = f"the {own_effective_family.lower()} work remains the clearest success"
                elif repeated_count >= 3:
                    reason = f"the corner has identified the repeated {repeated_opponent_label} and wants the prepared response"
                elif deficit <= -8:
                    reason = "the cleaner offense has built a useful edge"
                elif deficit >= 5:
                    reason = "the round was close enough to adjust the execution before abandoning the plan"
                else:
                    reason = "the observable exchanges do not justify a wholesale change"
                line = self.render_corner_feedback(
                    fighter, opponent, round_no, round_read,
                    f"Stay with {row['current']}; {reason}",
                )
                if advice_memory.get(key) == line:
                    line = self.render_corner_feedback(
                        fighter, opponent, round_no, round_read,
                        f"Keep {row['current']} for round {round_no + 1}; {reason}",
                    )
                advice_memory[key] = line
                advice.append(line)
        return advice

    def fight_trace_snapshot(self, a, b, state):
        a_key = self.fight_state_key(a, state)
        b_key = self.fight_state_key(b, state)
        return {
            "position": state.get("position", "range"),
            "top": state.get("top"), "bottom": state.get("bottom"),
            "clinch_controller": state.get("clinch_controller"),
            "gas": {a_key: state["gas"][a_key], b_key: state["gas"][b_key]},
            "damage": {a_key: state["damage"][a_key], b_key: state["damage"][b_key]},
            "hurt": {a_key: state["hurt"][a_key], b_key: state["hurt"][b_key]},
            "head": {
                a_key: state.get("head_trauma", state["head"])[a_key],
                b_key: state.get("head_trauma", state["head"])[b_key],
            },
            "body": {a_key: state["body"][a_key], b_key: state["body"][b_key]},
            "leg": {a_key: state["leg"][a_key], b_key: state["leg"][b_key]},
            "cuts": {a_key: state["cuts"][a_key], b_key: state["cuts"][b_key]},
            "cut_state": {a_key: deepcopy(state["cut_state"][a_key]), b_key: deepcopy(state["cut_state"][b_key])},
            "knockdowns": {a_key: state["knockdowns"][a_key], b_key: state["knockdowns"][b_key]},
            "stats": {a_key: dict(state["stats"][a_key]), b_key: dict(state["stats"][b_key])},
        }

    def record_visible_damage_events(self, actor, defender, before, state):
        """Record newly visible trauma milestones without changing mechanics.

        The existing location channels already tax reactions, output and
        movement. This layer only turns a newly crossed threshold into a
        structured, replayable fact. It deliberately reads settled state and
        uses no random stream.
        """
        actor_key = self.fight_state_key(actor, state)
        defender_key = self.fight_state_key(defender, state)
        milestones = state.setdefault("visible_damage_milestones", {}).setdefault(
            defender_key, {channel: 0 for channel in self.VISIBLE_DAMAGE_MILESTONES}
        )
        history = state.setdefault("visible_damage", {}).setdefault(defender_key, [])
        head_state = state.get("head_trauma", state.get("head", {}))
        current = {
            "head": float(head_state.get(defender_key, 0) or 0),
            "body": float(state.get("body", {}).get(defender_key, 0) or 0),
            "leg": float(state.get("leg", {}).get(defender_key, 0) or 0),
        }
        events = []
        for channel, thresholds in self.VISIBLE_DAMAGE_MILESTONES.items():
            previous_total = float((before.get(channel, {}) or {}).get(defender_key, 0) or 0)
            total = current[channel]
            if total <= previous_total:
                continue
            crossed = [
                (tier, threshold, damage_id, label, keyword)
                for tier, (threshold, damage_id, label, keyword) in enumerate(thresholds, 1)
                if total >= threshold
            ]
            if not crossed:
                continue
            tier, threshold, damage_id, label, keyword = crossed[-1]
            if tier <= int(milestones.get(channel, 0) or 0):
                continue
            milestones[channel] = tier
            row = {
                "damage_id": damage_id,
                "channel": channel,
                "severity": tier,
                "threshold": threshold,
                "total": int(round(total)),
                "label": label,
                "narrative_keyword": keyword,
                "actor": actor_key,
                "defender": defender_key,
                "move_id": str((state.get("last_move_payload") or {}).get("move_id") or ""),
                "round": int(state.get("round", 1) or 1),
                "tick": int(state.get("tick", 1) or 1),
            }
            history.append(row)
            events.append(deepcopy(row))
        return events

    def render_visible_damage_narratives(self, event):
        """Render structured damage and cut facts through isolated presentation logic."""
        actor = str(event.get("actor_name") or "The attacker")
        defender = str(event.get("defender_name") or "the opponent")
        move = self.exchange_display_move(event)
        pools = {
            "face_reddening": (
                "Reddening starts to show across {defender}'s face after the latest offense from {actor}.",
                "The latest exchange from {actor} leaves visible reddening across {defender}'s face.",
                "The head strikes are beginning to mark {defender}; that offense from {actor} adds more reddening.",
            ),
            "facial_bruising": (
                "The latest offense from {actor} leaves bruising across {defender}'s face.",
                "Bruising starts to show on {defender} after {actor}'s latest attack gets through.",
                "That exchange from {actor} adds visible bruising to {defender}'s face.",
            ),
            "general_swelling": (
                "Visible swelling is building across {defender}'s face after the latest offense from {actor}.",
                "The latest exchange from {actor} adds to the general swelling on {defender}'s face.",
                "The accumulated head strikes on {defender} show as facial swelling after that attack from {actor}.",
            ),
            "heavily_marked_face": (
                "The facial damage is heavy now as the latest offense from {actor} finds {defender} again.",
                "Accumulated head damage is written across {defender}'s face; that exchange from {actor} adds to it.",
                "The facial damage across {defender}'s face is obvious after another attack from {actor}.",
            ),
            "torso_reddening": (
                "Reddening spreads across {defender}'s torso after the latest offense from {actor}.",
                "The latest exchange from {actor} leaves visible reddening on {defender}'s body.",
                "The body work is showing as reddening across {defender}'s torso after that attack from {actor}.",
            ),
            "body_bruising": (
                "Bruising is forming across {defender}'s body after the latest offense from {actor}.",
                "That exchange from {actor} deepens the bruising on {defender}'s midsection.",
                "The accumulated body work shows as bruising on {defender} when the latest attack from {actor} lands.",
            ),
            "guarded_midsection": (
                "{defender} starts guarding the midsection after the latest offense from {actor} gets through.",
                "That exchange from {actor} leaves {defender} protecting the midsection.",
                "{defender}'s elbows pinch toward the damaged midsection after the latest attack from {actor}.",
            ),
            "laboured_breathing": (
                "{defender}'s breathing is laboured after the latest offense from {actor} adds to the body damage.",
                "The body damage is affecting {defender}'s breathing as that exchange from {actor} lands.",
                "The latest attack from {actor} leaves {defender} breathing heavily through the accumulated body damage.",
            ),
            "leg_reddening": (
                "Reddening spreads across {defender}'s leg after the latest offense from {actor}.",
                "That exchange from {actor} leaves visible reddening on {defender}'s damaged leg.",
                "The leg work on {defender} is starting to show as reddening after the latest attack from {actor}.",
            ),
            "leg_welt": (
                "A welt starts to rise on {defender}'s damaged leg after the latest offense from {actor}.",
                "That exchange from {actor} leaves a visible welt across {defender}'s leg.",
                "The accumulated leg work on {defender} shows as a welt after the latest attack from {actor}.",
            ),
            "weight_shift": (
                "{defender} shifts weight off the damaged leg after the latest offense from {actor}.",
                "That exchange from {actor} forces {defender} to shift weight away from the damaged leg.",
                "{defender}'s weight shifts noticeably after the latest leg attack from {actor}.",
            ),
            "visible_limp": (
                "A limp is visible as {defender} resets after the latest offense from {actor}.",
                "The latest exchange from {actor} leaves {defender} moving with a pronounced limp.",
                "The accumulated leg damage shows in {defender}'s limp after that attack from {actor}.",
            ),
        }
        lines = []
        for damage in event.get("visible_damage_events", ()) or ():
            damage_id = str(damage.get("damage_id") or "")
            pool = pools.get(damage_id, ())
            if not pool:
                continue
            line = self.stable_commentary_choice(
                event, f"visible-damage:{damage_id}:{damage.get('severity', 0)}", pool,
            )
            lines.append(line.format(actor=actor, defender=defender, move=move))

        defender_key = event.get("defender")
        for cut in ((event.get("cut_events") or {}).get(defender_key, ()) or ()):
            location = str(cut.get("location") or "face")
            bleeding = int(cut.get("bleeding", 0) or 0)
            if cut.get("vision_risk"):
                cut_pool = (
                    "The cut at {defender}'s {location} is swelling into the line of sight after {actor}'s latest offense.",
                    "Blood and swelling gather around the cut at {defender}'s {location}; the latest offense from {actor} worsens it.",
                )
            elif bleeding >= 4:
                cut_pool = (
                    "Blood is flowing from the cut on {defender}'s {location} after the latest offense from {actor}.",
                    "The cut at {defender}'s {location} is bleeding heavily as {actor} keeps the pressure on.",
                )
            else:
                cut_pool = (
                    "A fresh cut is visible on {defender}'s {location} after the latest offense from {actor}.",
                    "The latest attack from {actor} leaves a small cut at {defender}'s {location}.",
                )
            line = self.stable_commentary_choice(
                event,
                f"cut-detail:{location}:{cut.get('severity', 0)}:{bleeding}",
                cut_pool,
            )
            lines.append(line.format(actor=actor, defender=defender, move=move, location=location))
        return lines

    def select_exchange_move(self, actor, defender, action, position, target, state):
        """Choose a legal named technique without consuming any RNG stream."""
        target = {"high": "head", "teep": "body"}.get(target, target or "")
        candidates = list(legal_moves(action, position, target))
        styles = self.fighter_styles(actor)
        candidates = [
            definition for definition in candidates
            if not set(definition.tags).intersection({"style-combination", "style-finisher"})
            or set(styles).intersection(definition.preferred_styles)
        ]
        identity = str(getattr(actor, "fighter_id", "") or actor.name)
        actor_key = self.fight_state_key(actor, state)
        active_counter = bool(
            state.get("last_exchange_counter")
            or (state.get("counter_window") or {}).get("fighter") == actor_key
        )
        candidates = [
            definition for definition in candidates
            if ("counter" in definition.tags) == active_counter
            or (active_counter and "counter" not in definition.tags)
        ]
        if active_counter:
            candidates = [
                definition for definition in candidates
                if "style-combination" not in definition.tags or "counter" in definition.tags
            ]
        boxing_specialists = {
            "combination_punching": self.ds(actor, "combination_punching", actor.striking),
            "body_punching": self.ds(actor, "body_punching", actor.striking),
            "counter_timing": self.ds(actor, "counter_timing", actor.fight_iq),
        }
        signature_moves = set(getattr(actor, "signature_moves", []) or [])
        signature_finisher_ids = {
            definition.move_id for definition in candidates
            if definition.move_id in signature_moves
            and set(definition.tags).intersection({"finisher", "style-finisher"})
        }
        active_chain = (state.get("move_chains") or {}).get(actor_key, {}) or {}
        chain_live = (
            active_chain.get("round") == int(state.get("round", 1))
            and 0 < int(state.get("tick", 1)) - int(active_chain.get("tick", 0)) <= 2
        )

        def contextual_score(definition):
            actor_reads = (state.get("move_reads") or {}).get(actor_key, {})
            defender_key = self.fight_state_key(defender, state)
            defender_reads = (state.get("move_reads") or {}).get(defender_key, {})
            plan = self.fight_plan_for(actor, state)
            tags = set(definition.tags)
            bonus = 0.0
            reasons = []
            if chain_live and definition.move_id == active_chain.get("next_move_id"):
                bonus += 10
                reasons.append(f"sequence-follow-up:{active_chain.get('source_move_id', '')}")
            strain = float((state.get("move_exertion") or {}).get(actor_key, 0.0) or 0.0)
            if definition.energy > 1.0 and strain > 0:
                bonus -= min(6.0, (definition.energy - 1.0) * strain * 2.2)
                reasons.append("move-exertion-management")
            recent_misses = float((state.get("move_miss_pressure") or {}).get(actor_key, 0.0) or 0.0)
            if definition.miss_risk > 1.0 and recent_misses > 0:
                bonus -= min(5.0, (definition.miss_risk - 1.0) * recent_misses * 2.5)
                reasons.append("miss-risk-management")
            defender_vulnerability = float(
                (state.get("move_counter_vulnerability") or {}).get(defender_key, 0.0) or 0.0
            )
            if active_counter and "counter" in tags and defender_vulnerability > 0:
                bonus += min(6.0, defender_vulnerability * self.ds(actor, "counter_timing", actor.fight_iq) / 100)
                reasons.append("technique-counter-risk")
            actor_stance = str((state.get("current_stance") or {}).get(actor_key, getattr(actor, "stance", "Orthodox")) or "Orthodox")
            defender_key = self.fight_state_key(defender, state)
            defender_stance = str((state.get("current_stance") or {}).get(defender_key, getattr(defender, "stance", "Orthodox")) or "Orthodox")
            if "Switch" in (actor_stance, defender_stance):
                stance_matchup = "switch"
            elif {actor_stance, defender_stance} == {"Orthodox", "Southpaw"}:
                stance_matchup = "open"
            else:
                stance_matchup = "closed"
            if stance_matchup == "open" and (definition.side == "rear" or tags.intersection({"body", "counter"})):
                bonus += 3
                reasons.append("open-stance-rear-lane")
            elif stance_matchup == "closed" and (definition.side == "lead" or tags.intersection({"setup", "low-kick"})):
                bonus += 2
                reasons.append("closed-stance-lead-lane")
            elif stance_matchup == "switch" and tags.intersection({"creative", "spinning", "high-risk"}):
                bonus += 2.5
                reasons.append("switch-stance-angle")
            grappling_styles = {
                "Wrestler", "Freestyle Wrestler", "Catch Wrestler", "BJJ", "Luta Livre",
                "Sambo", "Judo", "Grappler", "Submission Grappler",
            }
            actor_grappler = bool(set(styles).intersection(grappling_styles))
            defender_grappler = bool(set(self.fighter_styles(defender)).intersection(grappling_styles))
            if actor_grappler and not defender_grappler and tags.intersection({"entry", "takedown", "clinch"}):
                bonus += 2.5
                reasons.append("grappler-vs-striker-entry")
            elif not actor_grappler and defender_grappler and tags.intersection({"setup", "counter", "kick"}):
                bonus += 2
                reasons.append("striker-vs-grappler-range")
            elif actor_grappler and defender_grappler and tags.intersection({"scramble", "transition", "submission"}):
                bonus += 1.5
                reasons.append("grappling-matchup-chain")
            plan_preferences = {
                "Pressure and volume": ("combination",),
                "Counter striking": ("counter",),
                "Wrestle early": ("wrestling", "entry"),
                "Cage grind": ("cage", "control"),
                "Attack the body": ("body",),
                "Damage the lead leg": ("leg",),
                "Submission hunt": ("submission",),
                "Chase a finish": ("power", "submission", "high-risk"),
            }
            preferred = plan_preferences.get(plan["current"], ())
            if tags.intersection(preferred):
                bonus += 5 * plan["execution"]
                reasons.append(f"plan:{plan['current']}")
            targets_seen = actor_reads.get("targets", {})
            if targets_seen.get("body", 0) >= 2 and ("head" in tags or definition.parent_action == "power_punch"):
                bonus += min(4.5, targets_seen["body"] * 0.7)
                reasons.append("body-work-opened-head")
            if targets_seen.get("leg", 0) >= 2 and tags.intersection({"head", "entry", "takedown"}):
                bonus += min(4.0, targets_seen["leg"] * 0.6)
                reasons.append("low-kick-read")
            if actor_reads.get("setups", {}).get("feint", 0) >= 2 and "entry" in tags:
                bonus += min(3.5, actor_reads["setups"]["feint"] * 0.5)
                reasons.append("feint-established-entry")
            repeats = actor_reads.get("moves", {}).get(definition.move_id, 0)
            if repeats >= 2:
                adaptability = self.ds(actor, "adaptability", actor.fight_iq)
                penalty = min(7.0, (repeats - 1) * (1.5 + max(0, 65 - adaptability) / 80))
                bonus -= penalty
                reasons.append("pattern-repetition-penalty")
            opponent_repeats = max(defender_reads.get("moves", {}).values(), default=0)
            if active_counter and "counter" in tags and opponent_repeats >= 3:
                bonus += min(5.0, opponent_repeats * self.ds(actor, "adaptability", actor.fight_iq) / 150)
                reasons.append("opponent-pattern-counter")
            return bonus, tuple(reasons)

        def score(definition):
            attack = [boxing_specialists.get(key, self.ds(actor, key, 50)) for key in definition.attack_skills]
            proficiency = sum(attack) / max(1, len(attack))
            if definition.minimum_skill and proficiency < definition.minimum_skill:
                return -10_000
            style_bonus = 8 if styles[0] in definition.preferred_styles else 0
            if len(styles) > 1 and styles[1] in definition.preferred_styles:
                style_bonus += 3
            if definition.move_id in REPRESENTATIVE_SPECIALIST_MOVES and styles[0] in definition.preferred_styles:
                style_bonus += 24
            style_tag_preferences = {
                "Boxer": {"punch", "combination", "counter"},
                "Kickboxer": {"kick", "mixed-combination", "counter"},
                "Dutch Kickboxer": {"combination", "low-kick", "mixed-combination"},
                "Muay Thai": {"knee", "elbow", "clinch"},
                "Karate": {"kick", "counter", "high-risk"},
                "Taekwondo": {"kick", "spinning", "high-risk"},
                "Sanda": {"kick", "takedown", "trip"},
                "Wrestler": {"wrestling", "takedown", "control"},
                "Freestyle Wrestler": {"entry", "takedown", "scramble"},
                "Catch Wrestler": {"ride", "front-headlock", "submission"},
                "BJJ": {"submission", "guard", "transition"},
                "Luta Livre": {"leg-lock", "submission", "scramble"},
                "Sambo": {"takedown", "leg-lock", "trip"},
                "Judo": {"throw", "trip", "clinch"},
                "Grappler": {"transition", "control", "ground"},
                "Submission Grappler": {"submission", "back-take", "choke"},
                "Well-Rounded": {"mixed-combination", "transition", "counter"},
                "MMA Generalist": {"mixed-combination", "entry", "control"},
            }
            definition_tags = set(definition.tags)
            if ("style-finisher" in definition_tags
                    and signature_finisher_ids
                    and definition.move_id not in signature_finisher_ids):
                return -10_000
            if "style-combination" in definition_tags:
                style_bonus += 2 if styles[0] in definition.preferred_styles else 1
            if "style-finisher" in definition_tags:
                style_bonus += 5 if styles[0] in definition.preferred_styles else 2
            if definition_tags.intersection(style_tag_preferences.get(styles[0], set())):
                style_bonus += 4
            if len(styles) > 1 and definition_tags.intersection(style_tag_preferences.get(styles[1], set())):
                style_bonus += 1.5
            signature_bonus = 6 if definition.move_id in signature_moves else 0
            mastery_bonus = float((getattr(actor, "move_mastery", {}) or {}).get(definition.move_id, 0) or 0) * 0.12
            context_bonus, _reasons = contextual_score(definition)
            material = (
                f"{identity}|{state.get('round', 1)}|{state.get('tick', 1)}|"
                f"{action}|{position}|{target}|{definition.move_id}"
            )
            fingerprint = zlib.crc32(material.encode("utf-8"))
            if "high-risk" in definition.tags and fingerprint % 100 >= 14:
                return -10_000
            if definition_tags.intersection({"finisher", "style-finisher"}):
                finisher_material = (
                    f"{identity}|{state.get('round', 1)}|{state.get('tick', 1)}|"
                    f"{action}|{position}|{target}|authored-finisher"
                )
                authored_frequency = 18 if "style-finisher" in definition_tags else 12
                if zlib.crc32(finisher_material.encode("utf-8")) % 100 >= authored_frequency:
                    return -10_000
            variety = fingerprint % 901 / 100
            return proficiency + style_bonus + signature_bonus + mastery_bonus + context_bonus + variety

        scored = [(score(definition), definition) for definition in candidates]
        eligible = [row for row in scored if row[0] > -10_000]
        if not eligible:
            return {
                "move_id": f"generic_{action}", "name": action.replace("_", " "),
                "parent_action": action, "target": target or "", "attack_skills": (),
                "defense_skills": (), "energy": 1.0, "miss_risk": 1.0,
                "counter_risk": 1.0, "follow_up_id": "", "tags": ("generic",),
                "follow_up_ids": (),
                "side": "", "range_band": "", "defense_families": (),
                "entry_family": "", "finish_positions": (),
                "attack_path": "", "failure_outcomes": (), "components": (),
                "signature": False, "selection_reasons": (),
                "sequence_source_id": "", "sequence_step": 0,
                "generic": True,
            }
        definition = max(eligible, key=lambda row: (row[0], row[1].move_id))[1]
        _context_bonus, selection_reasons = contextual_score(definition)
        return {
            "move_id": definition.move_id, "name": definition.name,
            "parent_action": definition.parent_action, "target": target or "",
            "attack_skills": definition.attack_skills,
            "defense_skills": definition.defense_skills,
            "energy": definition.energy, "miss_risk": definition.miss_risk,
            "counter_risk": definition.counter_risk,
            "follow_up_id": definition.follow_ups[0] if definition.follow_ups else "",
            "follow_up_ids": definition.follow_ups,
            "tags": definition.tags, "side": definition.side,
            "range_band": definition.range_band,
            "defense_families": definition.defense_families,
            "entry_family": definition.entry_family,
            "finish_positions": definition.finish_positions,
            "attack_path": definition.attack_path,
            "failure_outcomes": definition.failure_outcomes,
            "components": definition.components,
            "signature": definition.move_id in signature_moves,
            "selection_reasons": selection_reasons,
            "sequence_source_id": (
                str(active_chain.get("source_move_id", ""))
                if chain_live and definition.move_id == active_chain.get("next_move_id") else ""
            ),
            "sequence_step": (
                int(active_chain.get("step", 1)) + 1
                if chain_live and definition.move_id == active_chain.get("next_move_id") else 0
            ),
            "stance_matchup": (
                "switch" if "Switch" in (
                    str((state.get("current_stance") or {}).get(actor_key, getattr(actor, "stance", ""))),
                    str((state.get("current_stance") or {}).get(self.fight_state_key(defender, state), getattr(defender, "stance", ""))),
                )
                else "open" if {
                    str((state.get("current_stance") or {}).get(actor_key, getattr(actor, "stance", ""))),
                    str((state.get("current_stance") or {}).get(self.fight_state_key(defender, state), getattr(defender, "stance", ""))),
                }
                == {"Orthodox", "Southpaw"} else "closed"
            ),
            "active_stance": str((state.get("current_stance") or {}).get(actor_key, getattr(actor, "stance", "Orthodox"))),
            "generic": False,
        }

    def update_dynamic_stance(self, fighter, opponent, state):
        """Make a deliberate, traceable stance choice without another RNG draw."""
        key = self.fight_state_key(fighter, state)
        current = state.setdefault("current_stance", {}).setdefault(key, getattr(fighter, "stance", "Orthodox"))
        last_tick = int(state.setdefault("stance_switch_tick", {}).get(key, -99))
        tick = int(state.get("tick", 1))
        if tick - last_tick < 4:
            return current
        switching = self.ds(fighter, "footwork", 50) + self.ds(fighter, "adaptability", fighter.fight_iq)
        natural_switch = getattr(fighter, "stance", "Orthodox") == "Switch"
        plan = self.fight_plan_for(fighter, state).get("current", "Balanced")
        trigger = (tick + int(state.get("round", 1)) + (1 if key == "b" else 0)) % (5 if natural_switch else 9) == 0
        if not trigger or (not natural_switch and switching < 145):
            return current
        opponent_key = self.fight_state_key(opponent, state)
        opponent_stance = state.get("current_stance", {}).get(opponent_key, getattr(opponent, "stance", "Orthodox"))
        if plan in ("Counter striking", "Attack the body"):
            target = "Southpaw" if opponent_stance == "Orthodox" else "Orthodox"
        elif natural_switch:
            target = "Southpaw" if current == "Orthodox" else "Orthodox"
        else:
            target = getattr(fighter, "stance", "Orthodox") if current != getattr(fighter, "stance", "Orthodox") else (
                "Southpaw" if current == "Orthodox" else "Orthodox"
            )
        if target != current:
            state["current_stance"][key] = target
            state["stance_switch_tick"][key] = tick
            state.setdefault("stance_switches", {"a": [], "b": []})[key].append({
                "round": int(state.get("round", 1)), "tick": tick, "from": current, "to": target, "plan": plan,
            })
        return state["current_stance"][key]

    def select_exchange_defense(self, defender, move_payload, position, state):
        """Name the legal defense attempted against a selected technique."""
        families = move_payload.get("defense_families", ()) or self.default_defense_families(move_payload)
        candidates = legal_defenses(families, position)
        if not candidates:
            fallback = DEFENSE_REGISTRY["technical_scramble"]
            return {
                "defense_id": fallback.defense_id, "name": fallback.name,
                "families": fallback.families, "skills": fallback.skills,
                "tags": fallback.tags, "generic": False,
            }
        identity = str(getattr(defender, "fighter_id", "") or defender.name)
        mastery = getattr(defender, "move_mastery", {}) or {}
        def score(definition):
            skill = sum(self.ds(defender, key, 50) for key in definition.skills) / max(1, len(definition.skills))
            learned = float(mastery.get(f"defense:{definition.defense_id}", 0) or 0) * 0.12
            fingerprint = zlib.crc32(
                f"{identity}|{state.get('round', 1)}|{state.get('tick', 1)}|{definition.defense_id}".encode("utf-8")
            ) % 401 / 100
            return skill + learned + fingerprint
        definition = max(candidates, key=lambda row: (score(row), row.defense_id))
        return {
            "defense_id": definition.defense_id, "name": definition.name,
            "families": definition.families, "skills": definition.skills,
            "tags": definition.tags, "generic": False,
        }

    @staticmethod
    def default_defense_families(move_payload):
        tags = set(move_payload.get("tags", ()))
        if "submission" in tags:
            return ("submission defense", "stack", "leg escape")
        if "takedown" in tags or "wrestling" in tags:
            return ("sprawl", "whizzer", "underhook")
        if "kick" in tags:
            return ("check", "block", "evade")
        return ("block", "parry", "evade")

    @staticmethod
    def fighter_signature_move_labels(fighter):
        return [
            MOVE_REGISTRY[move_id].name
            for move_id in (getattr(fighter, "signature_moves", []) or [])
            if move_id in MOVE_REGISTRY
        ]

    @staticmethod
    def update_move_reads(state, event):
        """Retain bounded, bout-local evidence for later deterministic move choices."""
        actor = event.get("actor")
        if actor not in ("a", "b"):
            return
        reads = state.setdefault("move_reads", {}).setdefault(
            actor, {"moves": {}, "targets": {}, "tags": {}, "setups": {}},
        )
        move_id = event.get("move_id")
        if move_id:
            reads["moves"][move_id] = min(12, reads["moves"].get(move_id, 0) + 1)
        target = event.get("move", {}).get("target")
        if target:
            reads["targets"][target] = min(12, reads["targets"].get(target, 0) + 1)
        for tag in event.get("move", {}).get("tags", ()):
            reads["tags"][tag] = min(12, reads["tags"].get(tag, 0) + 1)
        setup = event.get("exchange", {}).get("setup")
        if setup:
            reads["setups"][setup] = min(12, reads["setups"].get(setup, 0) + 1)

    @staticmethod
    def update_move_mechanics(state, event):
        """Apply bounded technique-layer energy/miss/counter consequences.

        These values shape later legal move choices only. Broad action damage,
        gas, landing and finish resolution remain the calibrated authority.
        """
        actor = event.get("actor")
        defender = event.get("defender")
        if actor not in ("a", "b") or defender not in ("a", "b"):
            return
        move = event.get("move", {}) or {}
        energy = max(0.75, min(1.75, float(move.get("energy", 1.0) or 1.0)))
        miss_risk = max(0.75, min(1.75, float(move.get("miss_risk", 1.0) or 1.0)))
        counter_risk = max(0.75, min(1.75, float(move.get("counter_risk", 1.0) or 1.0)))
        exertion = state.setdefault("move_exertion", {"a": 0.0, "b": 0.0})
        misses = state.setdefault("move_miss_pressure", {"a": 0.0, "b": 0.0})
        vulnerability = state.setdefault("move_counter_vulnerability", {"a": 0.0, "b": 0.0})
        for key in ("a", "b"):
            exertion[key] = round(max(0.0, float(exertion.get(key, 0.0)) * 0.72), 3)
            misses[key] = round(max(0.0, float(misses.get(key, 0.0)) * 0.65), 3)
            vulnerability[key] = round(max(0.0, float(vulnerability.get(key, 0.0)) * 0.55), 3)
        exertion[actor] = round(min(12.0, exertion[actor] + max(0.0, energy - 1.0) * 5), 3)
        if event.get("outcome") in ("defended", "control"):
            misses[actor] = round(min(12.0, misses[actor] + max(0.0, miss_risk - 1.0) * 6), 3)
            vulnerability[actor] = round(
                min(12.0, vulnerability[actor] + max(0.0, counter_risk - 1.0) * 7), 3,
            )
        event["move_mechanics"] = {
            "energy": energy, "miss_risk": miss_risk, "counter_risk": counter_risk,
            "actor_exertion": exertion[actor],
            "actor_miss_pressure": misses[actor],
            "actor_counter_vulnerability": vulnerability[actor],
        }

    @staticmethod
    def update_move_sequence(state, event):
        """Carry a successful registry follow-up across at most two ticks."""
        actor = event.get("actor")
        if actor not in ("a", "b"):
            return
        chains = state.setdefault("move_chains", {"a": {}, "b": {}})
        move = event.get("move", {}) or {}
        selected_source = str(move.get("sequence_source_id", "") or "")
        selected_step = int(move.get("sequence_step", 0) or 0)
        prior_chain = dict(chains.get(actor, {}) or {})
        event["move_sequence"] = {
            "source_move_id": selected_source,
            "step": selected_step,
            "completed_follow_up": bool(selected_source),
            "branch_options": list(prior_chain.get("branch_options", [])),
            "branch_reason": str(prior_chain.get("branch_reason", "") or ""),
        }
        effective = event.get("outcome") in {
            "landed", "knockdown", "takedown", "submission_attempt", "position_change",
        } or (event.get("outcome") == "control" and "control" in set(move.get("tags", ())))
        raw_follow_ups = move.get("follow_up_ids", ()) or ((move.get("follow_up_id"),) if move.get("follow_up_id") else ())
        follow_up_ids = [str(value) for value in raw_follow_ups if value in MOVE_REGISTRY]
        position_after = str(event.get("position_after", "") or "")
        legal_branches = [
            move_id for move_id in follow_up_ids
            if not position_after or position_after in MOVE_REGISTRY[move_id].positions
        ]
        defense_tags = set((event.get("defense") or {}).get("tags", ()))
        branch_index = 1 if len(legal_branches) > 1 and defense_tags.intersection({"evasion", "escape", "frame"}) else 0
        follow_up_id = legal_branches[branch_index] if legal_branches else ""
        if effective and follow_up_id:
            chains[actor] = {
                "source_move_id": selected_source or str(event.get("move_id", "") or ""),
                "previous_move_id": str(event.get("move_id", "") or ""),
                "next_move_id": follow_up_id,
                "branch_options": legal_branches,
                "branch_reason": "defensive-reaction" if branch_index else "primary-continuation",
                "step": selected_step or 1,
                "round": int(event.get("round", 1)),
                "tick": int(event.get("tick", 1)),
            }
        else:
            chains[actor] = {}

    @staticmethod
    def move_family(move):
        tags = set((move or {}).get("tags", ()))
        if "submission" in tags:
            return "Submissions"
        if tags.intersection({"takedown", "wrestling"}):
            return "Wrestling"
        if "ground" in tags and "strike" in tags:
            return "Ground Striking"
        if "kick" in tags:
            return "Kicks"
        if tags.intersection({"knee", "elbow"}):
            return "Knees & Elbows"
        if tags.intersection({"punch", "combination", "power"}):
            return "Boxing"
        if "clinch" in tags:
            return "Clinch"
        if tags.intersection({"transition", "sweep", "escape", "control"}):
            return "Transitions & Control"
        return "Other"

    def round_move_family_summary(self, state, fighter_key, round_no):
        counts = {}
        for event in state.get("trace", []):
            if event.get("type") != "exchange" or event.get("round") != round_no or event.get("actor") != fighter_key:
                continue
            family = event.get("move_family") or self.move_family(event.get("move", {}))
            row = counts.setdefault(family, {"attempts": 0, "effective": 0})
            row["attempts"] += 1
            row["effective"] += event.get("outcome") in ("landed", "knockdown", "takedown", "submission_attempt", "position_change")
        leaders = sorted(counts.items(), key=lambda item: (-item[1]["attempts"], item[0]))[:2]
        return ", ".join(f"{family} {row['effective']}/{row['attempts']}" for family, row in leaders) or "No established family"

    def exchange_setup(self, actor, action, position):
        """Describe the mechanical entry already represented by the action ratings."""
        if action in ("shoot", "takedown"):
            if self.ds(actor, "takedown_setup", actor.wrestling) >= self.ds(actor, "chain_wrestling", actor.wrestling):
                return "level change"
            return "re-shot"
        if action in ("clinch", "cage_control"):
            return "pressure to fence" if position in ("range", "pocket", "cage") else "inside pummel"
        if action == "jab":
            return "jab entry"
        if action in ("power_punch", "kick"):
            return "feint" if self.ds(actor, "feints", 50) >= self.ds(actor, "footwork", 50) else "stance trap"
        if action in ("dirty_boxing", "break_clinch"):
            return "inside hand fight"
        if action in ("submission", "bottom_submission"):
            return "grip sequence"
        if action in ("advance_position", "recover_guard", "sweep", "stand_up"):
            return "positional transition"
        return "direct attack"

    def exchange_defensive_response(self, defender, action, outcome, position_before, position_after, target):
        """Classify the defense evidenced by the resolved exchange without another draw."""
        if outcome not in ("defended", "control"):
            return "defense breached" if outcome in ("landed", "knockdown", "takedown") else "transition contested"
        if action in ("shoot", "takedown"):
            return "sprawl to fence" if position_after == "cage" else "sprawl"
        if action in ("clinch", "cage_control", "dirty_boxing", "break_clinch"):
            return "pummel" if position_before in ("clinch", "cage") else "frame"
        if action == "kick":
            return "check" if target == "leg" else "block"
        if action in ("jab", "power_punch"):
            options = {
                "block": self.ds(defender, "guard_defence", defender.striking),
                "evade": self.ds_avg(defender, ("head_movement", "footwork"), defender.striking),
                "parry": self.ds_avg(defender, ("reflexes", "punch_defence"), defender.striking),
            }
            return max(options, key=options.get)
        if action in ("submission", "bottom_submission", "advance_position", "recover_guard", "sweep", "stand_up"):
            return "scramble"
        return "block"

    @staticmethod
    def exchange_combination_components(action, attempts, landed, target, move_id=""):
        """Expand aggregate strike volume into bounded, internally consistent evidence."""
        if attempts <= 0:
            return []
        authored_components = (
            tuple(MOVE_REGISTRY[move_id].components)
            if move_id in MOVE_REGISTRY and MOVE_REGISTRY[move_id].components else ()
        )
        move_templates = {
            "single_jab": ("jab",),
            "double_jab": ("jab", "jab"),
            "body_jab": ("body jab",),
            "one_two": ("jab", "cross"),
            "lead_hook_cross": ("lead hook", "cross"),
            "double_jab_cross": ("jab", "jab", "cross"),
            "cross_hook_cross": ("cross", "lead hook", "cross"),
            "body_head_change": ("shovel hook to body", "cross to head"),
            "jab_cross_lead_hook": ("jab", "cross", "lead hook"),
            "jab_uppercut_lead_hook": ("jab", "rear uppercut", "lead hook"),
            "double_jab_body_cross": ("body jab", "body jab", "cross to head"),
            "cross_body_hook_lead_hook": ("cross", "body hook", "lead hook to head"),
            "stance_shift_cross_hook": ("stance-shift cross", "lead hook"),
            "boxing_pressure_flurry": ("jab", "cross", "lead hook", "rear cross", "lead hook"),
            "rear_uppercut": ("rear uppercut",),
            "corkscrew_cross": ("corkscrew cross",),
            "spinning_backfist": ("spinning backfist",),
            "check_hook": ("check hook",),
            "pull_counter": ("pull counter",),
            "slip_cross": ("slip-cross",),
            "calf_kick": ("rear calf kick",),
            "low_kick_counter": ("check", "return low kick"),
            "lead_teep": ("lead teep",),
            "side_kick": ("lead side kick",),
            "question_mark_kick": ("question-mark kick",),
            "wheel_kick": ("wheel kick",),
            "spinning_back_kick": ("spinning back kick",),
            "switch_body_kick": ("switch kick",),
            "jab_low_kick": ("jab", "outside low kick"),
            "cross_body_kick": ("cross", "body kick"),
            "hook_low_kick": ("lead hook", "low kick"),
            "punch_head_kick": ("jab", "cross", "head kick"),
            "double_jab_low_kick": ("jab", "jab", "outside low kick"),
            "cross_hook_body_kick": ("cross", "lead hook", "body kick"),
            "axe_kick": ("axe kick",),
            "jumping_front_kick": ("jumping front kick",),
            "intercepting_knee": ("intercepting knee",),
            "jab_cross_rear_knee": ("jab", "cross", "rear knee to head"),
            "hook_elbow_knee": ("lead hook", "rear elbow", "lead knee"),
            "flying_knee": ("flying knee",),
            "switch_flying_knee": ("switch flying knee",),
            "step_in_elbow": ("step-in elbow",),
            "spinning_elbow": ("spinning elbow",),
            "posture_punches": ("postured punch", "straight punch"),
            "short_ground_elbows": ("short elbow",),
            "ride_wrist_punches": ("wrist-ride punch", "short elbow"),
            "guard_posture_elbows": ("postured punch", "short elbow"),
            "half_guard_crossface_strikes": ("crossface punch", "short elbow"),
            "crucifix_elbows": ("short crucifix elbow",),
            "mounted_hammerfist_flurry": ("hammerfist", "straight punch", "hammerfist"),
            "back_control_short_punches": ("short punch", "punch around the guard"),
            "turtle_wrist_ride_strikes": ("wrist-ride punch", "hammerfist", "short elbow"),
        }
        templates = {
            "jab": ("jab",),
            "power_punch": ("cross", "lead hook", "rear uppercut", "body hook"),
            "kick": (f"{target or 'general'} kick",),
            "dirty_boxing": ("short punch", "elbow", "knee"),
            "ground_strikes": ("short punch", "elbow", "hammerfist"),
        }
        weapons = authored_components or move_templates.get(move_id) or templates.get(action)
        if not weapons:
            return []
        attempts = max(0, min(30, int(attempts)))
        landed = max(0, min(attempts, int(landed)))
        return [
            {"sequence": index + 1, "weapon": weapons[index % len(weapons)], "landed": index < landed}
            for index in range(attempts)
        ]

    def record_fight_trace_exchange(self, a, b, actor, defender, action, result, before, round_before, state, round_stats):
        actor_key = self.fight_state_key(actor, state)
        defender_key = self.fight_state_key(defender, state)
        after = self.fight_trace_snapshot(a, b, state)
        intermediate_positions = deepcopy(state.get("intermediate_positions", []))
        previous_position = before["position"]
        for intermediate in intermediate_positions:
            self.validate_fight_transition(previous_position, intermediate["position"], intermediate)
            previous_position = intermediate["position"]
        self.validate_fight_transition(previous_position, after["position"], state)
        sig_delta = after["stats"][actor_key]["sig"] - before["stats"][actor_key]["sig"]
        sig_att_delta = after["stats"][actor_key]["sig_att"] - before["stats"][actor_key]["sig_att"]
        td_delta = after["stats"][actor_key]["td"] - before["stats"][actor_key]["td"]
        td_att_delta = after["stats"][actor_key]["td_att"] - before["stats"][actor_key]["td_att"]
        sub_att_delta = after["stats"][actor_key]["sub_att"] - before["stats"][actor_key]["sub_att"]
        knockdown_delta = {key: after["knockdowns"][key] - before["knockdowns"][key] for key in ("a", "b")}
        if knockdown_delta[actor_key] > 0:
            outcome = "knockdown"
        elif sub_att_delta > 0:
            outcome = "submission_attempt"
        elif td_delta > 0:
            outcome = "takedown"
        elif sig_delta > 0:
            outcome = "landed"
        elif sig_att_delta > 0 or td_att_delta > 0:
            outcome = "defended"
        elif before["position"] != after["position"]:
            outcome = "position_change"
        else:
            outcome = "control"
        flags = {
            "hurt": after["damage"][defender_key] > before["damage"][defender_key],
            "knockdown": knockdown_delta[actor_key] > 0,
            "cut": after["cuts"][defender_key] > before["cuts"][defender_key],
            "position_changed": before["position"] != after["position"],
        }
        round_metric_delta = {
            key: {
                metric: round_stats[key][metric] - round_before[key][metric]
                for metric in ("impact", "danger", "control")
            }
            for key in ("a", "b")
        }
        move_payload = state.get("last_move_payload") or self.select_exchange_move(
            actor, defender, action, before["position"], state.get("last_strike_target"), state,
        )
        defense_move_payload = move_payload
        submission_technique = state.get("last_submission_technique") or {}
        if submission_technique:
            technique_name = str(submission_technique.get("name") or "").casefold()
            leg_attack = any(term in technique_name for term in (
                "heel", "knee", "ankle", "toe hold", "slicer", "cloverleaf",
            ))
            defense_move_payload = dict(move_payload)
            defense_move_payload["defense_families"] = (
                ("leg escape", "stack") if leg_attack else ("submission defense", "stack")
            )
        defense_payload = self.select_exchange_defense(
            defender, defense_move_payload, before["position"], state,
        )
        plan_row = self.fight_plan_for(actor, state)
        plan_change = {}
        history = list(plan_row.get("history", []) or [])
        if int(state.get("tick", 1)) == 1 and history:
            latest = history[-1]
            if (int(latest.get("round", 0) or 0) > 0
                    and int(latest.get("round", 0) or 0) == int(state.get("round", 1)) - 1
                    and str(latest.get("plan", "") or "") == str(plan_row.get("current", "") or "")):
                plan_change = deepcopy(latest)
        mastery = getattr(actor, "move_mastery", {}) or {}
        try:
            move_mastery = int(round(float(mastery.get(move_payload["move_id"], 0) or 0)))
        except (TypeError, ValueError):
            move_mastery = 0
        corner_identity = self.commentary_corner_identity(actor)
        event = {
            "type": "exchange", "round": state.get("round", 1),
            "tick": state.get("tick", 1), "clock": state.get("official_time", "0:00"),
            "actor": actor_key, "defender": defender_key, "action": action,
            "actor_name": actor.name, "defender_name": defender.name,
            "commentary_salt": int(state.get("commentary_salt", 0) or 0),
            "actor_commentary_profile": deepcopy(
                (state.get("commentary_profiles") or {}).get(actor_key, {})
            ),
            "defender_commentary_profile": deepcopy(
                (state.get("commentary_profiles") or {}).get(defender_key, {})
            ),
            "move_id": move_payload["move_id"], "move": move_payload,
            "defense_id": defense_payload["defense_id"], "defense": defense_payload,
            "signature": bool(move_payload.get("signature", False)),
            "sequence_source_id": str(move_payload.get("sequence_source_id", "") or ""),
            "sequence_step": int(move_payload.get("sequence_step", 0) or 0),
            "move_family": self.move_family(move_payload),
            "plan": plan_row["current"], "plan_change": plan_change,
            "counter": bool(state.get("last_exchange_counter", False)),
            "actor_style": str(getattr(actor, "style_label", getattr(actor, "style", "")) or ""),
            "defender_style": str(getattr(defender, "style_label", getattr(defender, "style", "")) or ""),
            "actor_stance": str((state.get("current_stance") or {}).get(actor_key, getattr(actor, "stance", "")) or ""),
            "defender_stance": str((state.get("current_stance") or {}).get(defender_key, getattr(defender, "stance", "")) or ""),
            "stance_matchup": str(move_payload.get("stance_matchup", "") or ""),
            "actor_camp": corner_identity["camp"], "actor_coach": corner_identity["coach"],
            "actor_camp_specialties": corner_identity["specialties"],
            "actor_camp_city": corner_identity["city"],
            "actor_camp_region": corner_identity["region"],
            "move_mastery": move_mastery,
            "actor_streak": max(0, int(state.get("actor_streak", 0) or 0)),
            "actor_damage_after": after["damage"][actor_key],
            "defender_damage_after": after["damage"][defender_key],
            "actor_gas_after": round(after["gas"][actor_key], 3),
            "defender_gas_after": round(after["gas"][defender_key], 3),
            "championship": bool(state.get("is_title_fight", False)),
            "rivalry_heat": max(0, int(state.get("rivalry_heat", 0) or 0)),
            "position_before": before["position"], "position_after": after["position"],
            "position_path": [before["position"]]
                             + [row["position"] for row in intermediate_positions]
                             + [after["position"]],
            "top_before": before["top"], "top_after": after["top"],
            "bottom_before": before["bottom"], "bottom_after": after["bottom"],
            "clinch_before": before["clinch_controller"], "clinch_after": after["clinch_controller"],
            "outcome": outcome, "flags": flags, "result": result or "", "commentary": [],
            "visible_damage_events": deepcopy(state.get("last_visible_damage_events", [])),
            "damage_narrative": [],
            "foul": deepcopy(state.get("last_foul")),
            "submission_escape": deepcopy(state.get("last_submission_escape")),
            "submission_technique": deepcopy(state.get("last_submission_technique")),
            "referee_ground_action": deepcopy(state.get("last_referee_ground_action")),
            "point_deductions": deepcopy(state.get("point_deductions", {})),
            "gas_delta": {key: round(after["gas"][key] - before["gas"][key], 3) for key in ("a", "b")},
            "damage_delta": {key: after["damage"][key] - before["damage"][key] for key in ("a", "b")},
            "hurt_delta": {key: round(after["hurt"][key] - before["hurt"][key], 3) for key in ("a", "b")},
            "head_delta": {key: after["head"][key] - before["head"][key] for key in ("a", "b")},
            "body_delta": {key: after["body"][key] - before["body"][key] for key in ("a", "b")},
            "leg_delta": {key: after["leg"][key] - before["leg"][key] for key in ("a", "b")},
            "cut_delta": {key: after["cuts"][key] - before["cuts"][key] for key in ("a", "b")},
            "cut_events": {
                key: deepcopy(after["cut_state"][key][len(before["cut_state"][key]):])
                for key in ("a", "b")
            },
            "knockdown_delta": knockdown_delta,
            "sig_delta": sig_delta, "sig_att_delta": sig_att_delta,
            "td_delta": td_delta, "td_att_delta": td_att_delta,
            "sub_att_delta": sub_att_delta,
            "exchange": {
                "setup": self.exchange_setup(actor, action, before["position"]),
                "defensive_response": (
                    defense_payload["name"] + " — " + self.exchange_defensive_response(
                        defender, action, outcome, before["position"], after["position"],
                        state.get("last_strike_target"),
                    )
                ),
                "counter_opportunity": bool(
                    (state.get("counter_window") or {}).get("fighter") == defender_key
                    and (state.get("counter_window") or {}).get("created_tick") == int(state.get("tick", 1))
                ),
                "counter_consumed": bool(state.get("last_exchange_counter", False)),
                "counter_success": bool(
                    state.get("last_exchange_counter", False)
                    and outcome in ("landed", "knockdown", "takedown", "submission_attempt", "position_change")
                ),
                "follow_up": (
                    "transition" if before["position"] != after["position"]
                    else "counter available" if (state.get("counter_window") or {}).get("fighter") == defender_key
                    else "follow-up pressure" if outcome in ("landed", "knockdown")
                    else "disengagement"
                ),
                "combination": self.exchange_combination_components(
                    action, sig_att_delta, sig_delta, state.get("last_strike_target"), move_payload["move_id"],
                ),
            },
            "round_metric_delta": round_metric_delta,
            "control_delta": {
                key: after["stats"][key]["control_ticks"] - before["stats"][key]["control_ticks"]
                for key in ("a", "b")
            },
            "stoppage": None,
        }
        exchange = event["exchange"]
        exchange["beats"] = [
            {"phase": "setup", "detail": exchange["setup"]},
            {"phase": "attack", "detail": action},
            {"phase": "defense", "detail": exchange["defensive_response"]},
        ]
        if exchange["counter_opportunity"] or exchange["counter_consumed"]:
            exchange["beats"].append({
                "phase": "counter",
                "detail": "landed" if exchange["counter_success"] else "available",
            })
        exchange["beats"].append({"phase": "follow_up", "detail": exchange["follow_up"]})
        event["trait_commentary"] = ""
        trait_line = self.trait_exchange_commentary(event, self.exchange_commentary_kind(event))
        trait_seen = state.setdefault("trait_commentary_seen", {}).setdefault(
            actor_key, {"rounds": set(), "count": 0},
        )
        trait_round = int(event.get("round", 1) or 1)
        if (trait_line and int(trait_seen.get("count", 0) or 0) < 2
                and trait_round not in trait_seen.get("rounds", set())):
            event["trait_commentary"] = trait_line
            trait_seen.setdefault("rounds", set()).add(trait_round)
            trait_seen["count"] = int(trait_seen.get("count", 0) or 0) + 1
        event["camp_commentary"] = ""
        camp_line = self.camp_exchange_commentary(event, self.exchange_commentary_kind(event))
        camp_seen = state.setdefault("camp_commentary_seen", {}).setdefault(
            actor_key, {"rounds": set(), "count": 0},
        )
        camp_round = int(event.get("round", 1) or 1)
        if (camp_line and int(camp_seen.get("count", 0) or 0) < 2
                and camp_round not in camp_seen.get("rounds", set())):
            event["camp_commentary"] = camp_line
            camp_seen.setdefault("rounds", set()).add(camp_round)
            camp_seen["count"] = int(camp_seen.get("count", 0) or 0) + 1
        plan_row["attempts"] += max(1, sig_att_delta + td_att_delta + sub_att_delta)
        if outcome in ("landed", "knockdown", "takedown", "submission_attempt", "position_change"):
            plan_row["effective_actions"] += 1
        state["trace"].append(event)
        self.update_move_reads(state, event)
        self.update_move_mechanics(state, event)
        self.update_move_sequence(state, event)
        return event

    def commentary_personality(self, value=None):
        """Return a safe presentation voice without touching combat state."""
        candidate = str(
            value if value is not None else getattr(self, "rules", {}).get(
                "fight_commentary_personality", "Balanced"
            )
        ).strip().title()
        return candidate if candidate in FIGHT_COMMENTARY_PERSONALITIES else "Balanced"

    def commentary_corner_identity(self, fighter):
        """Return saved camp and coach identity without inventing either fact."""
        camp = str(getattr(fighter, "camp", "") or "").strip()
        coach = ""
        specialties = ()
        city = ""
        region = ""
        verified_gym = False
        for gym in getattr(self, "gyms", ()) or ():
            if str(getattr(gym, "name", "") or "").strip().casefold() != camp.casefold():
                continue
            coach = str(getattr(gym, "head_coach", "") or "").strip()
            specialties = tuple(
                str(value).strip() for value in (getattr(gym, "specialties", ()) or ())
                if str(value).strip()
            )
            city = str(getattr(gym, "city", "") or "").strip()
            region = str(getattr(gym, "region", "") or "").strip()
            verified_gym = True
            break
        return {
            "camp": camp, "coach": coach, "specialties": specialties,
            "city": city, "region": region, "verified_gym": verified_gym,
        }

    def commentary_camp_intro(self, fighter):
        """Introduce exact saved corner facts and degrade safely for legacy camps."""
        identity = self.commentary_corner_identity(fighter)
        camp = identity["camp"]
        if not camp or camp.casefold() == "independent":
            return ""
        name = str(getattr(fighter, "name", "") or "The fighter")
        coach = identity["coach"]
        specialties = identity["specialties"]
        location = identity["city"] or identity["region"]
        if specialties:
            specialty_copy = ", ".join(specialties[:-1]) + (
                f" and {specialties[-1]}" if len(specialties) > 1 else specialties[-1]
            )
            coach_copy = f", led by {coach}," if coach else ""
            location_copy = f" from {location}" if location else ""
            return (
                f"{name}'s {camp} corner{location_copy}{coach_copy} brings recognised work in "
                f"{specialty_copy}."
            )
        if coach:
            return f"{name} is guided tonight by {coach} in the {camp} corner."
        return f"{name} is listed out of {camp} tonight."

    def camp_exchange_commentary(self, event, kind):
        """Connect recorded camp specialties to completed exchange evidence."""
        actor = str(event.get("actor_name") or "The attacker")
        camp = str(event.get("actor_camp") or "").strip()
        coach = str(event.get("actor_coach") or "").strip()
        specialties = {
            str(value).strip().casefold()
            for value in (event.get("actor_camp_specialties", ()) or ())
            if str(value).strip()
        }
        if not camp or camp.casefold() == "independent" or not specialties:
            return ""
        move = event.get("move", {}) or {}
        tags = {str(tag).casefold() for tag in (move.get("tags", ()) or ())}
        action = str(event.get("action") or "")
        outcome = str(event.get("outcome") or "")
        effective = outcome in {
            "landed", "knockdown", "takedown", "submission_attempt", "position_change",
        }
        round_no = max(1, int(event.get("round", 1) or 1))
        actor_gas = max(0, float(event.get("actor_gas_after", 0) or 0))
        position_before = str(event.get("position_before") or "")
        position_after = str(event.get("position_after") or "")
        specialty = ""
        evidence = ""
        if "boxing" in specialties and effective and (
                tags.intersection({"punch", "boxing", "hand-strike"})
                or action in {"jab", "combination", "power_punch", "body_punch"}):
            specialty, evidence = "Boxing", "The camp's boxing work is visible in that exchange"
        elif "kickboxing" in specialties and effective and tags.intersection({"kick", "knee", "mixed-combination"}):
            specialty, evidence = "Kickboxing", "That kicking sequence reflects the camp's striking identity"
        elif "wrestling" in specialties and effective and (
                outcome == "takedown" or tags.intersection({"wrestling", "takedown", "ride"})):
            specialty, evidence = "Wrestling", "The camp's wrestling detail shows in the completed action"
        elif "bjj" in specialties and (
                outcome == "submission_attempt" or (
                    effective and position_after in self.GROUND_POSITIONS and tags.intersection({"submission", "transition", "guard"})
                )):
            specialty, evidence = "BJJ", "That ground sequence carries the camp's jiu-jitsu identity"
        elif "sambo" in specialties and effective and tags.intersection({"trip", "throw", "leg-lock", "submission"}):
            specialty, evidence = "Sambo", "The camp's sambo influence is clear in that sequence"
        elif "clinch" in specialties and effective and (
                position_before in {"clinch", "cage"} or position_after in {"clinch", "cage"}
                or tags.intersection({"clinch", "elbow", "knee", "cage"})):
            specialty, evidence = "Clinch", "The camp's clinch work is shaping the exchange"
        elif "gameplanning" in specialties and effective and (
                bool(event.get("plan_change")) or kind == "countered"):
            specialty, evidence = "Gameplanning", "The prepared tactical read is paying off for the corner"
        elif "conditioning" in specialties and round_no >= 2 and actor_gas >= 35 and effective:
            specialty, evidence = "Conditioning", "The camp's conditioning base is keeping the work available"
        if not specialty:
            return ""
        if not self.stable_commentary_due(event, f"camp-context:{camp}:{specialty}", 5):
            return ""
        corner = f"{coach} and {camp}" if coach else camp
        pool = (
            f"{evidence} from {actor}; {corner} will recognise that work.",
            f"{actor} shows the {specialty.lower()} emphasis associated with {corner}.",
        )
        return self.stable_commentary_choice(event, f"camp-context:{camp}:{specialty}:{kind}", pool)

    def commentary_fighter_profile(self, fighter):
        """Derive natural broadcast identities from saved fighter attributes.

        The labels are presentation evidence, not new ratings or mechanics.
        Recording them in the completed trace lets replays explain why two
        fighters using the same move still look and sound different.
        """
        standing = {
            "power": self.ds_avg(fighter, ("punch_power", "killer_instinct", "strength"), fighter.power),
            "speed": self.ds_avg(fighter, ("hand_speed", "reflexes", "footwork"), fighter.striking),
            "volume": self.ds_avg(fighter, ("combination_punching", "aggression", "conditioning"), fighter.striking),
            "precision": self.ds_avg(fighter, ("punch_technique", "counter_timing", "feints"), fighter.striking),
            "kicking": self.ds_avg(fighter, ("low_kick_technique", "high_kick_technique", "creative_kicks"), fighter.striking),
            "inside": self.ds_avg(fighter, ("dirty_boxing", "elbows", "knees", "clinch_control"), fighter.striking),
        }
        ground = {
            "ground striking": self.ds_avg(fighter, ("ground_striking", "elbows", "top_control"), fighter.ground_control),
            "control": self.ds_avg(fighter, ("top_control", "ride_control", "positional_ability"), fighter.ground_control),
            "submission": self.ds_avg(fighter, ("submission_attack", "leg_locks", "back_control"), fighter.submissions),
            "scramble": self.ds_avg(fighter, ("scrambles", "guard_work", "get_ups"), fighter.grappling),
            "wrestling": self.ds_avg(fighter, ("chain_wrestling", "takedowns", "cage_wrestling"), fighter.wrestling),
        }
        defense = {
            "movement": self.ds_avg(fighter, ("head_movement", "footwork", "reflexes"), fighter.striking),
            "guard": self.ds_avg(fighter, ("guard_defence", "punch_defence", "composure"), fighter.striking),
            "kick defense": self.ds_avg(fighter, ("kick_defence", "mobility", "balance"), fighter.takedown_defence),
            "anti-wrestling": self.ds_avg(fighter, ("sprawl", "takedown_defence_detail", "clinch_defence"), fighter.takedown_defence),
            "submission defense": self.ds_avg(fighter, ("submission_defence_detail", "guard_work", "flexibility"), fighter.submission_defence),
        }
        behaviour = str(getattr(fighter, "behaviour", "") or "")
        if behaviour == "Volume":
            standing["volume"] += 8
        elif behaviour == "Pressure":
            standing["power"] += 4
            standing["volume"] += 4
        elif behaviour == "Counter":
            standing["precision"] += 8
        elif behaviour == "Submission Hunter":
            ground["submission"] += 8
        elif behaviour == "Control":
            ground["control"] += 8
        elif behaviour == "Sprawl And Brawl":
            defense["anti-wrestling"] += 6
            standing["precision"] += 3
        return {
            "standing": max(standing, key=standing.get),
            "ground": max(ground, key=ground.get),
            "defense": max(defense, key=defense.get),
            "standing_scores": {key: int(round(value)) for key, value in standing.items()},
            "ground_scores": {key: int(round(value)) for key, value in ground.items()},
            "defense_scores": {key: int(round(value)) for key, value in defense.items()},
            "behaviour": behaviour,
            "trait": str(getattr(fighter, "trait", "") or ""),
            "weight_cut_penalty": max(0, int(getattr(fighter, "weight_cut_penalty", 0) or 0)),
        }

    def commentary_trait_intro(self, fighter):
        """Return one natural, saved-trait introduction without consuming RNG."""
        trait = str(getattr(fighter, "trait", "") or "").strip()
        template = TRAIT_COMMENTARY_INTROS.get(trait)
        if not template:
            return ""
        return template.format(name=str(getattr(fighter, "name", "") or "The fighter"))

    def trait_exchange_commentary(self, event, kind):
        """Describe a trait only when completed trace facts make it relevant.

        This is presentation over recorded facts. It cannot add an action,
        damage, score, position change, or finish opportunity.
        """
        actor = str(event.get("actor_name") or "The attacker")
        actor_profile = event.get("actor_commentary_profile", {}) or {}
        trait = str(actor_profile.get("trait") or "").strip()
        move = event.get("move", {}) or {}
        tags = {str(tag).casefold() for tag in (move.get("tags", ()) or ())}
        target = str(move.get("target") or "").casefold()
        action = str(event.get("action") or "")
        outcome = str(event.get("outcome") or "")
        round_no = max(1, int(event.get("round", 1) or 1))
        tick = max(1, int(event.get("tick", 1) or 1))
        actor_streak = max(0, int(event.get("actor_streak", 0) or 0))
        actor_damage = max(0, float(event.get("actor_damage_after", 0) or 0))
        actor_gas = max(0, float(event.get("actor_gas_after", 0) or 0))
        defender_key = event.get("defender")
        defender_hurt_gain = max(
            0.0, float((event.get("hurt_delta") or {}).get(defender_key, 0) or 0),
        )
        weight_cut_penalty = max(0, int(actor_profile.get("weight_cut_penalty", 0) or 0))
        effective = outcome in {
            "landed", "knockdown", "takedown", "submission_attempt", "position_change",
        }
        pool = ()
        critical = kind == "knockdown"

        if trait == "Fast Starter" and round_no == 1 and tick <= 6 and effective:
            pool = (
                f"That is the fast start {actor} is known for.",
                f"{actor} is imposing that familiar early urgency.",
            )
        elif trait == "Slow Starter" and round_no == 1 and tick <= 6 and not effective:
            pool = (
                f"{actor} is still taking the customary time to read the fight.",
                f"The opening read matters for {actor}, who often builds into the contest.",
            )
        elif trait in {"Big Finisher", "Fight Finisher"} and (
                kind == "knockdown" or defender_hurt_gain >= 6):
            pool = (
                f"{actor}'s finishing instinct is engaged now.",
                f"This is the kind of opening {actor} is known for converting.",
            )
            critical = True
        elif trait == "Knockout Artist" and kind == "knockdown":
            pool = (
                f"That is the knockout threat attached to every exchange with {actor}.",
                f"{actor}'s reputation as a knockout artist is fully justified there.",
            )
            critical = True
        elif trait == "Submission Ace" and outcome == "submission_attempt":
            pool = (
                f"This is where {actor}'s submission expertise becomes dangerous.",
                f"{actor} has reached the kind of submission lane opponents fear.",
            )
            critical = True
        elif trait == "Pressure Fighter" and actor_streak >= 3 and effective:
            pool = (
                f"The sustained pressure is becoming {actor}'s fight.",
                f"{actor} keeps taking space and stacking successful exchanges.",
            )
        elif trait == "Counter Specialist" and kind == "countered":
            pool = (
                f"That counter is exactly where {actor}'s specialist timing shows.",
                f"{actor} turns the first commitment into a clean countering opportunity.",
            )
        elif trait == "Cardio Machine" and round_no >= 2 and actor_gas >= 35 and effective:
            pool = (
                f"{actor}'s conditioning is keeping the work rate available.",
                f"The pace remains comfortable for the well-conditioned {actor}.",
            )
        elif trait == "Comeback Artist" and actor_damage >= 20 and effective:
            pool = (
                f"{actor} is beginning another response after absorbing damage.",
                f"The comeback reputation follows {actor} into this rally.",
            )
        elif trait == "Iron Chin" and actor_damage >= 20 and effective:
            pool = (
                f"After absorbing damage, {actor} is still producing an effective response.",
                f"{actor}'s durability matters here, with offense still coming back after the punishment.",
            )
        elif trait == "Clutch" and (round_no >= 3 or bool(event.get("championship"))) and effective:
            pool = (
                f"The pressure is rising, and {actor} has found a timely answer.",
                f"{actor}'s reputation for delivering in pivotal moments shows there.",
            )
        elif trait == "Title Mentality" and bool(event.get("championship")) and round_no >= 4 and effective:
            pool = (
                f"{actor} looks increasingly comfortable in the championship rounds.",
                f"The title-fight composure is showing for {actor}.",
            )
        elif trait == "Warrior Spirit" and (actor_damage >= 24 or actor_gas < 32) and effective:
            pool = (
                f"{actor} is still competing through the difficult physical stretch.",
                f"That response says plenty about {actor}'s resolve.",
            )
        elif trait == "Momentum Fighter" and actor_streak >= 3 and effective:
            pool = (
                f"Momentum is amplifying everything {actor} is doing now.",
                f"{actor} has the rhythm, and the exchanges are beginning to compound.",
            )
        elif trait == "Bad Weight Cut" and weight_cut_penalty > 0 and actor_gas < 32:
            pool = (
                f"The difficult cut is becoming part of the conditioning question for {actor}.",
                f"{actor}'s energy is bringing the weight cut back into focus.",
            )
        elif trait == "Adaptable" and bool(event.get("plan_change")) and effective:
            pool = (
                f"That exchange supports the adjustment from the adaptable {actor}.",
                f"{actor} is turning the revised plan into visible results.",
            )
        elif trait == "Body Hunter" and target == "body" and effective:
            pool = (
                f"{actor} returns to the body-hunting identity.",
                f"That investment downstairs is characteristic work from {actor}.",
            )
        elif trait == "Leg Kicker" and target == "leg" and effective:
            pool = (
                f"Attacking the base remains central to {actor}'s game.",
                f"That is the specialised leg work expected from {actor}.",
            )
        elif trait == "Cage Specialist" and (
                event.get("position_before") == "cage" or event.get("position_after") == "cage") and effective:
            pool = (
                f"The fence is becoming a specialised working area for {actor}.",
                f"{actor}'s cage craft is visible in that exchange.",
            )
        elif trait == "Elbow Specialist" and "elbow" in tags and effective:
            pool = (
                f"The elbow specialist finds the small opening for {actor}.",
                f"That compact elbow is a recognised part of {actor}'s identity.",
            )
        elif trait == "Scramble Artist" and action in {"sweep", "recover_guard", "stand_up"} \
                and kind in {"escaped", "transitioned", "countered"}:
            pool = (
                f"The loose transition plays directly into {actor}'s scrambling strength.",
                f"{actor}'s scramble instinct turns disorder into position.",
            )

        if not pool:
            return ""
        if not critical and not self.stable_commentary_due(event, f"trait-context:{trait}", 4):
            return ""
        return self.stable_commentary_choice(event, f"trait-context:{trait}:{kind}", pool)

    @staticmethod
    def commentary_style_family(style):
        """Collapse a displayed mixed style to a prose family, primary first."""
        primary = str(style or "MMA Generalist").split("/")[0].strip().casefold()
        if "muay thai" in primary:
            return "muay thai"
        if "dutch" in primary:
            return "dutch kickboxing"
        if "kickbox" in primary:
            return "kickboxing"
        if "taekwondo" in primary:
            return "taekwondo"
        if "karate" in primary:
            return "karate"
        if "sanda" in primary:
            return "sanda"
        if "box" in primary:
            return "boxing"
        if "judo" in primary:
            return "judo"
        if "sambo" in primary:
            return "sambo"
        if "wrest" in primary:
            return "wrestling"
        if any(term in primary for term in ("bjj", "luta livre", "grappl")):
            return "jiu-jitsu"
        return "mma"

    def commentary_style_language(self, event, domain):
        """Return deterministic style-shaped setup and continuation language."""
        family = self.commentary_style_family(event.get("actor_style"))
        standing = {
            "boxing": (
                ("Behind a compact boxing rhythm", "keeping the shoulders compact"),
                ("Working behind the lead hand", "building the exchange in punching range"),
                ("From a balanced boxing stance", "staying ready to punch on the reset"),
            ),
            "muay thai": (
                ("From a square Muay Thai base", "remaining balanced for the return"),
                ("Behind a patient Thai rhythm", "holding position in the pocket"),
                ("With the hips set under a high guard", "staying planted through contact"),
            ),
            "dutch kickboxing": (
                ("Behind a Dutch combination rhythm", "linking the hands and feet together"),
                ("With a tight high guard advancing", "keeping combination range"),
                ("From a pressure-kickboxing stance", "finishing the exchange in balance"),
            ),
            "kickboxing": (
                ("At long kickboxing range", "resetting outside the pocket"),
                ("Behind a mixed hands-and-feet rhythm", "keeping both striking lanes available"),
                ("From a mobile kickboxing stance", "leaving on an angle"),
            ),
            "taekwondo": (
                ("From a long bladed stance", "using distance before the reset"),
                ("With the lead leg active", "keeping the kicking lane open"),
                ("Bouncing at the edge of range", "leaving before the pocket settles"),
            ),
            "karate": (
                ("From a wide in-and-out stance", "exiting on the same line"),
                ("With a sharp burst across distance", "returning to long range"),
                ("Behind a stop-start karate rhythm", "denying a stationary target"),
            ),
            "sanda": (
                ("From a mixed striking-and-shot stance", "keeping the level change available"),
                ("Behind a quick Sanda entry", "leaving the hips ready to wrestle"),
                ("With the stance square enough to change levels", "mixing the threat of the takedown"),
            ),
            "wrestling": (
                ("Behind the threat of the level change", "keeping the hips ready underneath"),
                ("From a pressure-wrestling stance", "making every strike hide a possible shot"),
                ("With the hands drawing a defensive reaction", "staying close enough to wrestle"),
            ),
            "judo": (
                ("From an upright grip-fighting stance", "staying close enough to connect a tie"),
                ("With the clinch threat holding the centre", "keeping balance for the next contact"),
                ("Behind a measured upright entry", "watching for the body lock"),
            ),
            "sambo": (
                ("From a compact combat-sambo stance", "keeping strike and takedown threats together"),
                ("Behind a direct mixed-attack rhythm", "staying ready to connect to the hips"),
                ("With a square stance built for contact", "remaining ready for the next tie-up"),
            ),
            "jiu-jitsu": (
                ("Behind a cautious entry built around the clinch", "staying ready to connect to grappling"),
                ("With the hands searching for contact", "keeping the grappling route available"),
                ("From a measured MMA stance", "avoiding unnecessary time in the pocket"),
            ),
            "mma": (
                ("From a balanced MMA stance", "keeping every phase available"),
                ("Behind a layered mixed-rules rhythm", "resetting without giving up the centre"),
                ("With no single phase overcommitted", "remaining ready for the next transition"),
            ),
        }
        ground = {
            "boxing": (("Keeping the mat work direct", "looking to create striking room"),),
            "muay thai": (("Using a compact clinch-to-ground approach", "staying heavy enough to strike"),),
            "dutch kickboxing": (("Keeping the ground exchange direct", "looking to return to striking room"),),
            "kickboxing": (("Working carefully on the mat", "looking for space or a route back up"),),
            "taekwondo": (("Treating the ground exchange as an escape problem", "building toward open space"),),
            "karate": (("Staying patient away from the preferred long range", "looking to rebuild distance"),),
            "sanda": (("Linking the scramble to a Sanda-style ride", "staying ready to return upright"),),
            "wrestling": (
                ("With a tight wrestling ride", "following every turn of the hips"),
                ("Behind patient mat pressure", "keeping the scramble connected"),
                ("From a stable wrestling base", "making the next movement carry weight"),
            ),
            "judo": (
                ("Behind close upper-body control", "staying connected through the turn"),
                ("From a compact judo-style ride", "controlling the shoulders through movement"),
            ),
            "sambo": (
                ("From a pressure-heavy Sambo ride", "keeping both control and submission lanes close"),
                ("Using a compact combat-sambo base", "following the hips through the scramble"),
            ),
            "jiu-jitsu": (
                ("Through a patient jiu-jitsu sequence", "connecting the next grip to the position"),
                ("With the guard-and-position battle in focus", "keeping the submission route available"),
                ("Through layered positional pressure", "making each frame lead to the next grip"),
            ),
            "mma": (
                ("Through a balanced MMA ground sequence", "mixing control, damage and escape awareness"),
                ("With the position still developing", "staying ready for the next scramble"),
            ),
        }
        pool = (ground if domain == "ground" else standing).get(family)
        if not pool:
            pool = (ground if domain == "ground" else standing)["mma"]
        return self.stable_commentary_choice(event, f"style-language:{domain}:{family}", pool)

    def commentary_position_detail(self, event):
        """Describe the live positional battle from recorded ownership only."""
        actor_key = event.get("actor")
        before = str(event.get("position_before") or "range")
        after = str(event.get("position_after") or before)
        # When an escape or stand-up reaches the feet, old-position colour
        # appended after the reset contradicts the completed transition.
        if after not in self.GROUND_POSITIONS:
            return ""
        position = after
        if position not in self.GROUND_POSITIONS:
            return ""
        top_key = event.get("top_after") if after in self.GROUND_POSITIONS else event.get("top_before")
        actor_on_top = top_key == actor_key
        top = {
            "guard": ("The hips stay heavy inside the guard.", "Top pressure keeps the guard player carrying weight."),
            "half guard": ("The near leg remains tied up in half guard.", "The crossface-and-underhook battle stays central."),
            "side control": ("Chest pressure keeps the shoulders pinned in side control.", "The near hip remains blocked under side-control pressure."),
            "mount": ("The knees stay tight around the hips in mount.", "Every bridge is being followed from mount."),
            "back control": ("The hooks keep the back-control battle connected.", "The hand fight continues with the back still controlled."),
            "turtle": ("The ride stays connected over the turtle.", "Hip pressure prevents an easy turn out of turtle."),
            "front headlock": ("Head-and-arm control remains the centre of the position.", "The front-headlock grip keeps the scramble compressed."),
            "leg entanglement": ("The knee line remains trapped in the leg entanglement.", "Both fighters keep hand-fighting around the trapped leg."),
        }
        bottom = {
            "guard": ("The guard stays active around the hips.", "Frames and hip movement keep the bottom position alive."),
            "half guard": ("The bottom knee shield still creates a line of defence.", "The underhook battle keeps half guard from settling completely."),
            "side control": ("The bottom fighter keeps searching for a frame and a hip escape.", "The near-side frame is the first route out of side control."),
            "mount": ("The bottom fighter keeps bridging for a path back to guard.", "Elbows stay tight while the hips search for space under mount."),
            "back control": ("The defensive hand fight remains urgent from back control.", "The chin and choking hand remain the immediate priorities."),
            "turtle": ("The turtle stays active, with hands protecting the neck and hips.", "The base remains underneath the defender despite the ride."),
            "front headlock": ("The trapped fighter keeps fighting the hands and turning the corner.", "Posture and hand position remain the route out of the front headlock."),
            "leg entanglement": ("The defender keeps working to clear the knee line.", "Hand fighting and hip rotation decide the leg-lock exchange."),
        }
        pool = (top if actor_on_top else bottom).get(position, (f"The battle remains in {position}.",))
        return self.stable_commentary_choice(
            event, f"position-detail:{position}:{'top' if actor_on_top else 'bottom'}", pool,
        )

    @staticmethod
    def stable_commentary_choice(event, channel, values):
        """Choose presentation copy from trace identity without consuming RNG.

        The exchange has already happened. Commentary variety therefore belongs
        to a reproducible hash of immutable presentation facts, not any combat,
        officiating, judging, presentation, or process-global random stream.
        """
        choices = tuple(values or ())
        if not choices:
            return ""
        material = "|".join(str(value or "") for value in (
            channel, event.get("commentary_salt"), event.get("round"), event.get("tick"), event.get("actor"),
            event.get("defender"), event.get("move_id"), event.get("outcome"),
            event.get("defense_id"), event.get("position_before"), event.get("position_after"),
        ))
        return choices[zlib.crc32(material.encode("utf-8")) % len(choices)]

    @staticmethod
    def stable_commentary_due(event, channel, every=4):
        """Rate-limit optional analysis deterministically, without mutable memory."""
        material = "|".join(str(value or "") for value in (
            channel, event.get("commentary_salt"), event.get("round"), event.get("tick"), event.get("actor"),
            event.get("move_id"), event.get("defense_id"), event.get("position_after"),
        ))
        return zlib.crc32(material.encode("utf-8")) % max(1, int(every)) == 0

    @staticmethod
    def exchange_commentary_kind(event):
        """Classify an exchange from recorded outcome and defense facts only."""
        if (event.get("referee_ground_action") or {}).get("type") == "standup":
            return "referee_standup"
        outcome = str(event.get("outcome") or "control")
        exchange = event.get("exchange", {}) or {}
        move = event.get("move", {}) or {}
        move_id = str(event.get("move_id") or move.get("move_id") or "").casefold()
        move_name = str(move.get("name") or "").strip().casefold()
        if move_id == "composed_survival" or move_name == "composed survival":
            return "survived"
        if bool(event.get("counter") or exchange.get("counter_consumed")) and outcome in {
                "landed", "knockdown", "takedown", "submission_attempt", "position_change"}:
            return "countered"
        defense = event.get("defense", {}) or {}
        defense_text = " ".join((
            str(defense.get("name") or ""),
            " ".join(str(tag) for tag in (defense.get("tags", ()) or ())),
        )).casefold()
        if outcome == "defended":
            if any(term in defense_text for term in ("slip", "evad", "angle", "pivot", "roll", "pull", "duck")):
                return "slipped"
            return "blocked"
        before = str(event.get("position_before") or "range")
        after = str(event.get("position_after") or before)
        position_path = [str(value) for value in (event.get("position_path", ()) or ())]
        ownership_changed = any(
            event.get(before_key) != event.get(after_key)
            for before_key, after_key in (
                ("top_before", "top_after"),
                ("bottom_before", "bottom_after"),
                ("clinch_before", "clinch_after"),
            )
            if event.get(before_key) is not None or event.get(after_key) is not None
        )
        transition_proven = (
            before != after
            or any(value != before for value in position_path[1:])
            or ownership_changed
        )
        action = str(event.get("action") or "").casefold()
        if action in {"survive", "cling"} and not transition_proven:
            return "survived"
        move_id = str(event.get("move_id") or "").casefold()
        transition_attempt = action in {
            "sweep", "stand_up", "pass", "advance_position", "recover_guard",
            "transition", "break_clinch", "cage_escape", "clinch", "shoot", "takedown",
        } or any(term in move_id for term in (
            "sweep", "stand_up", "wall_walk", "pass", "escape", "transition", "reversal",
        ))
        if transition_attempt and not transition_proven:
            return "denied_transition"
        controlled = before in FightEngineMixin.GROUND_POSITIONS | FightEngineMixin.STANDING_CONTROL_POSITIONS
        standing = after in {"range", "pocket", "clinch", "cage"}
        if outcome == "position_change" and controlled and standing:
            return "escaped"
        if outcome in ("takedown", "position_change"):
            return "transitioned"
        if outcome == "knockdown":
            return "knockdown"
        if outcome == "submission_attempt":
            return "submission"
        return "landed" if outcome == "landed" else "control"

    @staticmethod
    def exchange_display_move(event):
        """Return a player-facing technique label without leaking engine placeholders."""
        submission_technique = event.get("submission_technique") or {}
        submission_name = str(submission_technique.get("name") or "").strip()
        if submission_name:
            return submission_name
        move = event.get("move", {}) or {}
        move_id = str(event.get("move_id") or move.get("move_id") or "").casefold()
        move_name = str(move.get("name") or event.get("action") or "attack").replace("_", " ").strip()
        action = str(event.get("action") or "").casefold()
        before = str(event.get("position_before") or "")
        after = str(event.get("position_after") or before)
        tags = {str(tag).casefold() for tag in (move.get("tags", ()) or ())}
        if action == "advance_position" and before != after:
            explicit_target = (
                ("back control" if "back-take" in tags or "back take" in move_name.casefold() else "")
                or ("mount" if "mount" in tags or "mount" in move_name.casefold() else "")
            )
            pass_bypasses_target = "pass" in tags and after in {"mount", "back control"}
            if (explicit_target and explicit_target != after) or pass_bypasses_target:
                move_name = {
                    "back control": "back-take transition",
                    "mount": "transition to mount",
                    "side control": "pass to side control",
                    "half guard": "pass to half guard",
                    "turtle": "turn into a turtle ride",
                    "front headlock": "front-headlock transition",
                }.get(after, f"transition to {after}")
        if move_id == "composed_survival" or move_name.casefold() == "composed survival":
            position = str(event.get("position_after") or event.get("position_before") or "range")
            outcome = str(event.get("outcome") or "control")
            if position in FightEngineMixin.GROUND_POSITIONS:
                return "defensive ground work" if outcome == "control" else "ground escape"
            if position in FightEngineMixin.STANDING_CONTROL_POSITIONS:
                return "defensive framing" if outcome == "control" else "cage escape"
            return "guarded reset"
        return move_name or "attack"

    @classmethod
    def exchange_commentary_domain(cls, event):
        """Separate standing exchanges from the positional ground broadcast."""
        if (event.get("referee_ground_action") or {}).get("type") in {"warning", "standup"}:
            return "ground"
        action = str(event.get("action") or "")
        before = str(event.get("position_before") or "range")
        after = str(event.get("position_after") or before)
        ground_actions = {
            "ground_control", "ground_strikes", "advance_position", "recover_guard",
            "submission", "bottom_submission", "sweep", "stand_up", "cling",
            "front_headlock_submission", "leg_attack", "leg_escape", "counter_leg_lock",
            "take_back", "turtle_ride", "turtle_escape", "front_headlock_escape",
        }
        return "ground" if action in ground_actions or before in cls.GROUND_POSITIONS or after in cls.GROUND_POSITIONS else "standing"

    @staticmethod
    def commentary_identity_label(profile, domain):
        key = str((profile or {}).get("ground" if domain == "ground" else "standing") or "balanced")
        labels = {
            "power": "power game",
            "speed": "hand speed",
            "volume": "pace",
            "precision": "timing",
            "kicking": "kicking craft",
            "inside": "inside work",
            "ground striking": "ground striking",
            "control": "control game",
            "submission": "submission game",
            "scramble": "scrambling",
            "wrestling": "wrestling base",
            "balanced": "all-round game",
        }
        return labels.get(key, key.replace("_", " "))

    def commentary_exchange_identity(self, event, domain, kind):
        """Choose the fighter strength relevant to the recorded technique."""
        profile = event.get("actor_commentary_profile") or {}
        move = event.get("move", {}) or {}
        tags = {str(tag).casefold() for tag in (move.get("tags", ()) or ())}
        action = str(event.get("action") or "").casefold()
        family = str(event.get("move_family") or "").casefold()
        if domain == "standing":
            if kind == "countered" or "counter" in tags:
                candidates = ("precision",)
            elif "kick" in tags or "kick" in family:
                candidates = ("kicking",)
            elif tags.intersection({"knee", "elbow", "clinch"}) or action in {
                    "dirty_boxing", "clinch", "cage_control"}:
                candidates = ("inside",)
            elif "combination" in tags:
                candidates = ("volume", "precision", "power", "speed")
            else:
                candidates = ("power", "speed", "volume", "precision")
            scores = profile.get("standing_scores") or {}
            fallback = str(profile.get("standing") or "balanced")
        else:
            if kind == "submission" or action in {
                    "submission", "bottom_submission", "front_headlock_submission", "leg_attack"}:
                candidates = ("submission",)
            elif kind == "escaped" or action in {
                    "sweep", "stand_up", "recover_guard", "turtle_escape", "leg_escape"}:
                candidates = ("scramble", "wrestling", "control")
            elif action == "ground_strikes" or tags.intersection({"ground-strike", "ground striking"}):
                candidates = ("ground striking",)
            elif kind in {"transitioned", "denied_transition"} or tags.intersection({"takedown", "wrestling", "transition"}):
                candidates = ("wrestling", "scramble", "control")
            else:
                candidates = ("control", "wrestling", "ground striking", "scramble")
            scores = profile.get("ground_scores") or {}
            fallback = str(profile.get("ground") or "balanced")
        key = max(candidates, key=lambda candidate: float(scores.get(candidate, -1))) if scores else fallback
        return self.commentary_identity_label(
            {"ground" if domain == "ground" else "standing": key}, domain,
        )

    @staticmethod
    def commentary_defense_clause(event, defender, defense):
        defense_row = event.get("defense") or {}
        defense_text = " ".join((
            str(defense_row.get("defense_id") or ""), str(defense_row.get("name") or defense),
            " ".join(str(tag) for tag in (defense_row.get("tags", ()) or ())),
        )).casefold()
        if any(term in defense_text for term in ("submission", "stack", "knee-line", "knee_line")):
            identity = "submission defense"
        elif any(term in defense_text for term in ("sprawl", "whizzer", "underhook", "fence post", "hip frame")):
            identity = "anti-wrestling"
        elif any(term in defense_text for term in ("shin check", "kick catch", "kick defense")):
            identity = "kick defense"
        elif any(term in defense_text for term in ("slip", "angle", "pivot", "evad")):
            identity = "movement"
        else:
            identity = str((event.get("defender_commentary_profile") or {}).get("defense") or "guard")
        clauses = {
            "movement": f"{defender}'s movement and {defense} take the target away",
            "guard": f"{defender}'s disciplined {defense} closes the lane",
            "kick defense": f"{defender}'s kick awareness and {defense} shut it down",
            "anti-wrestling": f"{defender}'s anti-wrestling base and {defense} hold up",
            "submission defense": f"{defender}'s submission awareness and {defense} solve the first attack",
        }
        return clauses.get(identity, f"{defender}'s {defense} stops it")

    def evidence_driven_exchange_pool(self, event, kind, facts):
        """Build style/stat/position-specific calls from completed trace facts."""
        domain = self.exchange_commentary_domain(event)
        style_setup, style_follow = self.commentary_style_language(event, domain)
        identity = self.commentary_exchange_identity(event, domain, kind)
        defense_clause = self.commentary_defense_clause(event, facts["defender"], facts["defense"])
        position_detail = self.commentary_position_detail(event)
        position_tail = f" {position_detail}" if position_detail else ""
        escape = event.get("submission_escape") or {}
        consequence = str(escape.get("consequence") or "").strip().rstrip(".")
        escape_position = str(escape.get("position") or facts["after"] or facts["before"])
        consequence_copy = {
            "knee line retained; leg entanglement established": (
                f"the first grip is gone, but the knee line remains trapped in {escape_position}"
            ),
            "late defense; position retained": (
                f"the immediate danger passes, though the position remains {escape_position}"
            ),
            "safe defense; position retained": (
                f"the attack is made safe without changing {escape_position}"
            ),
            "top control consolidated": (
                f"the escape ends with top control consolidated in {escape_position}"
            ),
            "reversal to top guard": "the escape becomes a reversal into top guard",
            "guard recovered": "the submission danger clears as guard is recovered",
            "grips cleared; position retained": (
                f"the grips are cleared, but the fight remains in {escape_position}"
            ),
            "safe escape to existing position": (
                f"the threat is removed and the existing {escape_position} position holds"
            ),
        }.get(consequence, consequence)
        escape_tail = (
            f" {facts['defender']} uses the {facts['defense']}; {consequence_copy}."
            if consequence else ""
        )
        expanded = {
            **facts,
            "style_setup": style_setup,
            "style_follow": style_follow,
            "identity": identity,
            "defense_clause": defense_clause,
            "defense_clause_cap": defense_clause[:1].upper() + defense_clause[1:],
            "position_tail": position_tail,
            "escape_tail": escape_tail,
        }
        if domain == "standing":
            pools = {
                "landed": (
                    "{style_setup}, {actor}'s {identity} shows as the {move} lands{landing_copy}.",
                    "{actor} finds the line for the {move}{landing_copy}, {style_follow}.",
                    "The {move} gets through for {actor}{landing_copy}; the {identity} is shaping the exchange.",
                    "{style_setup}, {actor} places the {move}{landing_copy} and resets cleanly.",
                    "{actor}'s {move} reaches {defender}{target_copy}, with the {identity} setting the tempo.",
                ),
                "blocked": (
                    "{style_setup}, {actor} sets up the {move}{target_copy}, but {defense_clause}.",
                    "{actor}'s {identity} brings the {move} into range; {defense_clause}.",
                    "The {move} from {actor} is read early as {defense_clause}.",
                    "{actor} tries the {move}{target_copy} while {style_follow}, but {defense_clause}.",
                ),
                "slipped": (
                    "{style_setup}, {actor} sends the {move}{target_copy}, but {defense_clause}.",
                    "{actor} looks for the {move}; {defense_clause} before it arrives.",
                    "The {move} misses for {actor} as {defense_clause}.",
                    "{actor} creates the {move} attempt with {identity}, yet {defense_clause}.",
                ),
                "countered": (
                    "On the counter, {actor}'s {identity} shows as the {move} lands{landing_copy}.",
                    "{style_setup}, {actor} reads the opening and answers with the {move}{target_copy}.",
                    "{actor} times the return {move}{landing_copy}, {style_follow}.",
                    "The counter window opens and {actor}'s {move} finds {defender}{target_copy}.",
                ),
                "knockdown": (
                    "{style_setup}, {actor} drives the {move}{landing_copy} and drops {defender}.",
                    "{actor}'s {identity} turns the {move} into a knockdown on {defender}.",
                    "The {move} from {actor} puts {defender} down, {style_follow}.",
                    "{actor} finds the decisive line with the {move}{target_copy}; {defender} hits the canvas.",
                ),
                "transitioned": (
                    "{style_setup}, {actor}'s {move} changes the exchange from {before} to {after}.",
                    "{actor} uses the {move} to carry the fight from {before} into {after}, {style_follow}.",
                    "The {move} gives {actor} the positional turn from {before} to {after}.",
                    "{actor}'s {identity} shows as the {move} reaches {after}.",
                ),
                "escaped": (
                    "{actor} uses the {move} to clear {before} and reset at {after}.",
                    "{style_setup}, {actor}'s {move} breaks the control and reaches {after}.",
                    "The {move} gets {actor} out of {before}; the fight opens again at {after}.",
                    "{actor}'s {identity} helps the {move} clear {before}.",
                ),
                "denied_transition": (
                    "{actor} tries the {move} from {before}, but {defender} keeps the exchange there.",
                    "{style_setup}, {actor}'s {move} cannot move beyond {before}; {defense_clause}.",
                    "The {move} stalls for {actor} as {defense_clause}.",
                    "{defender} reads {actor}'s {move} and denies the change from {before}.",
                ),
                "control": (
                    "{style_setup}, {actor} uses the {move} to hold the exchange at {after}.",
                    "{actor}'s {move} keeps {defender} occupied in {after}, {style_follow}.",
                    "The {move} lets {actor}'s {identity} dictate the beat at {after}.",
                    "{actor} settles the {move} in {after} without overcommitting.",
                ),
                "survived": (
                    "{actor} stays composed behind the {move}, then resets with {identity}.",
                    "{style_setup}, {actor}'s {move} takes the sting out of the exchange.",
                    "The {move} gives {actor} a quiet defensive beat before the next attack.",
                    "{actor} trusts the {move}, keeps the shape and makes {defender} start again.",
                    "{actor}'s {identity} shows in the disciplined {move} at {after}.",
                    "The pressure pauses as {actor} uses the {move} and reclaims the distance.",
                    "{actor} reads the moment, uses the {move} and refuses to be drawn out of position.",
                    "Behind the {move}, {actor} slows {defender}'s momentum and resets at {after}.",
                ),
            }
        else:
            pools = {
                "landed": (
                    "{style_setup}, {actor}'s {identity} shows as the {move} lands{landing_copy} from {after}.{position_tail}",
                    "{actor} makes room for the {move}{landing_copy} in {after}, {style_follow}.{position_tail}",
                    "The {move} scores for {actor} from {after}; the {identity} is visible here.{position_tail}",
                    "{actor} keeps the ground exchange active with the {move}{landing_copy}.{position_tail}",
                ),
                "blocked": (
                    "{style_setup}, {actor} works the {move} from {before}, but {defense_clause}.{position_tail}",
                    "{actor}'s {move} is denied in {before} as {defense_clause}.{position_tail}",
                    "{actor} tries to create room for the {move}; {defense_clause}.{position_tail}",
                    "The {identity} behind {actor}'s {move} is clear, but {defense_clause}.{position_tail}",
                ),
                "slipped": (
                    "{actor} looks for the {move} in {before}, but {defense_clause}.{position_tail}",
                    "{style_setup}, the {move} misses for {actor} as {defense_clause}.{position_tail}",
                    "{defense_clause_cap} before {actor}'s {move} can settle.{position_tail}",
                ),
                "transitioned": (
                    "{style_setup}, {actor}'s {identity} carries the {move} from {before} to {after}.{position_tail}",
                    "{actor} completes the {move}, changing the position from {before} to {after}.{position_tail}",
                    "The {move} moves {actor} through {before} and into {after}, {style_follow}.{position_tail}",
                    "{actor} wins the positional beat with the {move} and settles in {after}.{position_tail}",
                ),
                "escaped": (
                    "{style_setup}, {actor} uses the {move} to escape from {before} to {after}.{position_tail}",
                    "{actor}'s {identity} shows in the {move}, clearing {before} and reaching {after}.{position_tail}",
                    "The {move} gets {actor} free of {before}; the fight returns to {after}.{position_tail}",
                    "{actor} completes the {move} and breaks the positional control to {after}.{position_tail}",
                ),
                "denied_transition": (
                    "{style_setup}, {actor} attempts the {move} from {before}, but {defender} keeps the position there.{position_tail}",
                    "{actor}'s {move} cannot clear {before}; {defense_clause}.{position_tail}",
                    "The {identity} shapes {actor}'s {move}, but {defender} denies the positional change in {before}.{position_tail}",
                    "{defender} follows the hips and stops {actor}'s {move} from advancing beyond {before}.{position_tail}",
                ),
                "submission": (
                    "{style_setup}, {actor}'s {identity} connects the {move} from {before}; {defender} must defend.{position_tail}{escape_tail}",
                    "{actor} builds the {move} in {before}, {style_follow}; {defender} is forced into the hand fight.{position_tail}{escape_tail}",
                    "The {move} becomes a real threat for {actor} from {before}.{position_tail}{escape_tail}",
                    "{actor} attacks the {move} without giving up the positional connection in {before}.{position_tail}{escape_tail}",
                ),
                "control": (
                    "{style_setup}, {actor}'s {identity} shows as the {move} maintains control in {after}.{position_tail}",
                    "{actor} uses the {move} to keep the position settled at {after}, {style_follow}.{position_tail}",
                    "The {move} keeps {actor} connected in {after}; no easy reset is available.{position_tail}",
                    "{actor} makes the next positional beat count with the {move} from {after}.{position_tail}",
                ),
                "survived": (
                    "{actor}'s {identity} shows in the {move} from {after}.{position_tail}",
                    "{style_setup}, {actor} uses the {move} to stay safe in {after}.{position_tail}",
                    "The {move} buys {actor} another positional beat in {after}.{position_tail}",
                    "{actor} keeps the {move} disciplined and makes {defender} rebuild the attack in {after}.{position_tail}",
                    "The {move} gives {actor} enough structure to survive the next beat in {after}.{position_tail}",
                    "{actor} stays connected to the {move}, using the {identity} to limit the danger in {after}.{position_tail}",
                    "From {after}, {actor}'s {move} interrupts {defender}'s progress without conceding more position.{position_tail}",
                    "{actor} uses the {move} to keep the ground exchange competitive in {after}.{position_tail}",
                ),
                "countered": (
                    "{style_setup}, {actor} counters into the {move} from {before} and reaches {after}.{position_tail}{escape_tail}",
                    "{actor}'s {identity} turns the opening into the {move}, settling in {after}.{position_tail}{escape_tail}",
                    "The counter route gives {actor} the {move} from {before}.{position_tail}{escape_tail}",
                ),
            }
        pool = pools.get(kind)
        return (pool, expanded) if pool else ((), expanded)

    def render_exchange_trace_event(self, event, personality=None, technical=False):
        """Render one exchange exclusively from its completed trace facts.

        ``event['result']`` remains available to compatibility and audit tools,
        but it is intentionally not used here: that older broad-action prose can
        name a different strike or target from the selected technique. Voice and
        technical detail are presentation-only and consume no simulation RNG.
        """
        referee_ground_action = event.get("referee_ground_action") or {}
        if referee_ground_action.get("type") == "standup":
            return str(referee_ground_action.get("text") or "The referee stands the fighters up.")
        voice = self.commentary_personality(personality)
        move = event.get("move", {}) or {}
        exchange = event.get("exchange", {}) or {}
        actor = str(event.get("actor_name") or "The attacker")
        defender = str(event.get("defender_name") or "the opponent")
        move_name = self.exchange_display_move(event)
        target = str(move.get("target") or "").replace("_", " ")
        outcome = str(event.get("outcome") or "control")
        defense = str((event.get("defense") or {}).get("name") or "").replace("_", " ")
        before = str(event.get("position_before") or "range").replace("_", " ")
        after = str(event.get("position_after") or before).replace("_", " ")
        target_copy = f" to the {target}" if target and target.casefold() not in move_name.casefold() else ""
        landing_copy = (
            f" on {defender}'s {target}" if target and target.casefold() not in move_name.casefold()
            else f" on {defender}"
        )
        defense_copy = defense or "defense"
        kind = self.exchange_commentary_kind(event)
        facts = {
            "actor": actor, "defender": defender, "move": move_name,
            "target_copy": target_copy, "landing_copy": landing_copy,
            "defense": defense_copy, "before": before, "after": after,
        }
        balanced = {
            "landed": (
                "{actor} lands the {move}{landing_copy}.",
                "The {move} gets through for {actor}{landing_copy}.",
                "{actor} finds {defender} with the {move}{target_copy}.",
            ),
            "blocked": (
                "{defender} denies {actor}'s {move} with the {defense}.",
                "{actor} tries the {move}{target_copy}; {defender}'s {defense} stops it.",
                "The {move} from {actor} is turned away by {defender}'s {defense}.",
            ),
            "slipped": (
                "{defender} reads the {move} from {actor} and gets clear with the {defense}.",
                "{actor}'s {move} misses as {defender} uses the {defense}.",
                "{defender}'s {defense} takes them away from {actor}'s {move}.",
            ),
            "countered": (
                "On the counter, {actor} lands the {move}{landing_copy}.",
                "{actor} answers immediately with the {move}{target_copy}.",
                "The counter window opens and {actor} scores with the {move}{landing_copy}.",
            ),
            "transitioned": (
                "{actor} uses the {move} to move the fight from {before} to {after}.",
                "The {move} carries {actor} from {before} into {after}.",
                "{actor} completes the {move} and settles in {after}.",
            ),
            "escaped": (
                "{actor} uses the {move} to escape from {before} to {after}.",
                "The {move} gets {actor} out of {before} and back to {after}.",
                "{actor} clears the control with the {move}, reaching {after}.",
            ),
            "denied_transition": (
                "{actor} attempts the {move} from {before}, but {defender} denies the transition.",
                "{actor}'s {move} does not advance position; {defender} keeps the fight in {before}.",
                "{defender} stops {actor}'s {move}, leaving the position at {before}.",
            ),
            "knockdown": (
                "{actor} lands the {move}{landing_copy} and drops {defender}.",
                "The {move} from {actor} puts {defender} down.",
                "{actor} drops {defender} with the {move}{target_copy}.",
            ),
            "submission": (
                "{actor} attacks with the {move} from {before}; {defender} has to defend.",
                "From {before}, {actor} builds a submission threat with the {move}.",
                "{actor} finds the {move} in {before} and forces {defender} to respond.",
            ),
            "control": (
                "{actor} uses the {move} to maintain control from {after}.",
                "The {move} keeps {actor} in control at {after}.",
                "{actor} settles the position with the {move} from {after}.",
            ),
            "survived": (
                "{actor} stays composed with {move} from {after}, limiting the danger.",
                "From {after}, {actor}'s {move} creates enough space to reset defensively.",
                "{actor} uses {move} to blunt the offense and stay safe in {after}.",
            ),
        }
        if kind == "countered":
            if outcome == "knockdown":
                balanced[kind] = (
                    "On the counter, {actor}'s {move} drops {defender}.",
                    "{actor} times the counter {move} and puts {defender} down.",
                    "The counter window opens; {actor}'s {move} produces the knockdown.",
                )
            elif outcome == "takedown":
                balanced[kind] = (
                    "{actor} counters with the {move} and completes it into {after}.",
                    "On the counter, {actor}'s {move} takes the fight to {after}.",
                    "{actor} answers the opening with the {move}, settling in {after}.",
                )
            elif outcome == "submission_attempt":
                balanced[kind] = (
                    "{actor} counters into the {move} from {before}.",
                    "The counter opens a {move} attempt for {actor} in {before}.",
                    "{actor} answers by attacking the {move} from {before}.",
                )

        pool = balanced.get(kind, balanced["control"])
        evidence_pool, evidence_facts = self.evidence_driven_exchange_pool(event, kind, facts)
        if evidence_pool:
            pool = evidence_pool
            facts = evidence_facts
        if voice == "Concise":
            pool = pool[:2]
        line = self.stable_commentary_choice(event, f"exchange:{voice}:{kind}", pool).format(**facts)
        if voice == "Excitable":
            line = line.rstrip(".") + "!"

        context = []
        technical_context_due = technical or (
            voice == "Technical" and self.stable_commentary_due(event, "technical-context", 4)
        )
        signature = bool(event.get("signature") or move.get("signature"))
        try:
            mastery = max(0, int(event.get("move_mastery", 0) or 0))
        except (TypeError, ValueError):
            mastery = 0
        if signature:
            context.append(self.stable_commentary_choice(event, "signature", (
                f"{move_name.capitalize()} is one of {actor}'s signature techniques.",
                f"{actor} has gone to a signature move in the {move_name}.",
                f"That {move_name} belongs to {actor}'s declared signature set.",
            )))
        elif mastery >= 75 and technical_context_due:
            context.append(f"Recorded {move_name} mastery: {mastery}.")

        trait_context = (
            str(event.get("trait_commentary") or "")
            if "trait_commentary" in event
            else self.trait_exchange_commentary(event, kind)
        )
        if trait_context:
            context.append(trait_context)
        camp_context = (
            str(event.get("camp_commentary") or "")
            if "camp_commentary" in event
            else self.camp_exchange_commentary(event, kind)
        )
        if camp_context:
            context.append(camp_context)

        plan_change = event.get("plan_change", {}) or {}
        plan = str(event.get("plan") or "")
        if plan_change and plan:
            camp_specialties = {
                str(value).strip().casefold()
                for value in (event.get("actor_camp_specialties", ()) or ()) if str(value).strip()
            }
            if camp_context and "gameplanning" in camp_specialties:
                context.append(f"{actor} is now working under the {plan} plan.")
            else:
                camp = str(event.get("actor_camp") or "").strip()
                coach = str(event.get("actor_coach") or "").strip()
                corner = (
                    f"{coach} and the {camp} corner" if coach and camp
                    else f"The {camp} corner" if camp
                    else f"{actor}'s corner"
                )
                context.append(f"{corner} sends {actor} out under the {plan} plan.")

        flags = event.get("flags", {}) or {}
        damage_delta = event.get("damage_delta", {}) or {}
        defender_key = event.get("defender")
        defender_damage = max(0, int(round(float(damage_delta.get(defender_key, 0) or 0))))
        if flags.get("hurt") and defender_damage:
            if technical or voice == "Technical":
                context.append(f"The trace records {defender_damage} damage on {defender}.")
            else:
                head = max(0, int(round(float((event.get("head_delta") or {}).get(defender_key, 0) or 0))))
                body = max(0, int(round(float((event.get("body_delta") or {}).get(defender_key, 0) or 0))))
                leg = max(0, int(round(float((event.get("leg_delta") or {}).get(defender_key, 0) or 0))))
                cut = max(0, int(round(float((event.get("cut_delta") or {}).get(defender_key, 0) or 0))))
                exact_cut_events = ((event.get("cut_events") or {}).get(defender_key, ()) or ())
                if cut and exact_cut_events:
                    # The separate structured cut line names the recorded
                    # location and supported medical facts. Do not add a second
                    # generic sentence that could contradict or duplicate it.
                    damage_pool = ()
                    channel = "damage:cut:structured"
                elif cut:
                    damage_pool = (
                        f"A cut is now part of the picture for {defender}.",
                        f"That exchange leaves visible damage on {defender}.",
                        f"The target area is opening up on {defender}.",
                    )
                    channel = "damage:cut"
                elif head >= body and head >= leg and head:
                    damage_pool = (
                        f"That landed clean upstairs on {defender}.",
                        f"{defender} felt the head contact in that exchange.",
                        f"The clean work to the head adds up on {defender}.",
                        f"{defender} has to respect the damage coming high.",
                    )
                    channel = "damage:head"
                elif body >= leg and body:
                    damage_pool = (
                        f"The body work registers on {defender}.",
                        f"{defender} absorbs another meaningful touch downstairs.",
                        f"That attack makes {defender} protect the body.",
                        f"The damage through the midsection is building on {defender}.",
                    )
                    channel = "damage:body"
                elif leg:
                    damage_pool = (
                        f"{defender}'s base takes the damage from that exchange.",
                        f"The leg work is beginning to register on {defender}.",
                        f"{defender} has to reset the stance after that contact.",
                        f"That attack adds another mark against {defender}'s damaged leg.",
                    )
                    channel = "damage:leg"
                else:
                    damage_pool = (
                        f"The exchange adds clean damage on {defender}.",
                        f"That scoring action leaves an impression on {defender}.",
                        f"{defender} cannot ignore the damage from that exchange.",
                        f"The clean contact adds to {defender}'s accumulated damage.",
                    )
                    channel = "damage:general"
                if damage_pool and (cut or defender_damage >= 3):
                    context.append(self.stable_commentary_choice(event, channel, damage_pool))
        if int(event.get("actor_streak", 0) or 0) >= 3 and outcome in {
                "landed", "knockdown", "takedown", "submission_attempt", "position_change"}:
            context.append(f"{actor} keeps the attacking run going.")

        stance_matchup = str(event.get("stance_matchup") or move.get("stance_matchup") or "")
        actor_stance = str(event.get("actor_stance") or move.get("active_stance") or "")
        if technical_context_due and actor_stance and stance_matchup in {"open", "closed", "switch"}:
            context.append(f"Stance read: {actor_stance} in a {stance_matchup}-stance matchup.")
        actor_style = str(event.get("actor_style") or "").strip()
        defender_style = str(event.get("defender_style") or "").strip()
        if technical_context_due and actor_style and defender_style:
            context.append(f"Style read: {actor}'s {actor_style} against {defender}'s {defender_style}.")
        if kind in {"knockdown", "countered"} and outcome == "knockdown":
            if bool(event.get("championship")):
                context.append("That is a major swing in this championship bout.")
            if int(event.get("rivalry_heat", 0) or 0) > 0:
                context.append("The rivalry has another decisive exchange.")

        if technical:
            details = []
            if target:
                details.append(f"the intended target was the {target}")
            if defense:
                verb = "succeeded with" if outcome == "defended" else "attempted"
                details.append(f"{defender} {verb} the {defense}")
            follow_up = str(exchange.get("follow_up") or "").replace("_", " ")
            if follow_up and follow_up != "disengagement":
                details.append(f"the recorded follow-up lane was {follow_up}")
            if details:
                context.append("Technical detail: " + "; ".join(details) + ".")
        return " ".join((line, *context))

    def finalize_fight_result(self, a, b, winner, loser, method, round_no, lines, state):
        no_winner = method in ("Draw", "No Contest")
        if not no_winner and not state.get("stoppage_review"):
            state["stoppage_review"] = self.stoppage_review_from_evidence(loser, method, state)
        winner_id = "" if no_winner or winner is None else str(getattr(winner, "fighter_id", "") or "")
        loser_id = "" if no_winner or loser is None else str(getattr(loser, "fighter_id", "") or "")
        trace = list(state.get("trace", []))
        trace.append({
            "type": "official_result", "round": round_no,
            "clock": state.get("official_time", "0:00"),
            "winner": "" if no_winner or winner is None else self.fight_state_key(winner, state),
            "loser": "" if no_winner or loser is None else self.fight_state_key(loser, state), "method": method,
            "verdict": str(state.get("decision_verdict") or method),
            "point_deductions": deepcopy(state.get("point_deductions", {})),
            "technical_outcome": deepcopy(state.get("technical_outcome")),
        })
        exchange_events = [event for event in trace if event.get("type") == "exchange"]
        round_analysis = self.build_round_analysis(exchange_events, state.get("plans", {}), state.get("stance_switches", {}))
        last_exchange = exchange_events[-1] if exchange_events else {}
        signature_summary = {}
        family_summary = {}
        technique_summary = {}
        for fighter, key in ((a, "a"), (b, "b")):
            signature_ids = set(getattr(fighter, "signature_moves", []) or [])
            rows = {}
            for move_id in signature_ids:
                attempts = [event for event in exchange_events if event.get("actor") == key and event.get("move_id") == move_id]
                if not attempts:
                    continue
                landed = sum(event.get("outcome") in ("landed", "knockdown", "takedown", "submission_attempt", "position_change") for event in attempts)
                finish = int(
                    method not in ("Decision", "Technical Decision", "Draw", "No Contest")
                    and last_exchange.get("actor") == key and last_exchange.get("move_id") == move_id
                )
                rows[move_id] = {"attempts": len(attempts), "landed": landed, "finishes": finish}
            signature_summary[key] = rows
            families = {}
            for event in exchange_events:
                if event.get("actor") != key:
                    continue
                family = event.get("move_family") or self.move_family(event.get("move", {}))
                family_row = families.setdefault(family, {"attempts": 0, "effective": 0})
                family_row["attempts"] += 1
                family_row["effective"] += event.get("outcome") in ("landed", "knockdown", "takedown", "submission_attempt", "position_change")
            family_summary[key] = families
            actor_events = [event for event in exchange_events if event.get("actor") == key]
            move_counts = {}
            stance_matchups = {}
            selection_reasons = {}
            mechanic_totals = {"energy": 0.0, "miss_risk": 0.0, "counter_risk": 0.0}
            for event in actor_events:
                move_id = str(event.get("move_id", "") or "")
                if move_id:
                    move_counts[move_id] = move_counts.get(move_id, 0) + 1
                stance_matchup = str(event.get("move", {}).get("stance_matchup", "") or "unknown")
                stance_matchups[stance_matchup] = stance_matchups.get(stance_matchup, 0) + 1
                for reason in event.get("move", {}).get("selection_reasons", ()):
                    selection_reasons[reason] = selection_reasons.get(reason, 0) + 1
                mechanics = event.get("move_mechanics", {}) or {}
                for metric in mechanic_totals:
                    mechanic_totals[metric] += float(mechanics.get(metric, 1.0) or 1.0)
            count = max(1, len(actor_events))
            technique_summary[key] = {
                "top_moves": [
                    {"move_id": move_id, "attempts": attempts}
                    for move_id, attempts in sorted(move_counts.items(), key=lambda item: (-item[1], item[0]))[:5]
                ],
                "completed_sequences": sum(
                    bool(event.get("move_sequence", {}).get("completed_follow_up")) for event in actor_events
                ),
                "stance_matchups": stance_matchups,
                "selection_reasons": selection_reasons,
                "average_mechanics": {
                    metric: round(total / count, 3) for metric, total in mechanic_totals.items()
                },
            }
            if getattr(fighter, "last_fight_stats", None) is not None:
                fighter.last_fight_stats["signature_moves"] = deepcopy(rows)
                fighter.last_fight_stats["move_families"] = deepcopy(families)
        exchange_summary = {
            key: {
                "counters_attempted": sum(
                    1 for event in exchange_events
                    if event.get("actor") == key and event.get("exchange", {}).get("counter_consumed")
                ),
                "counters_successful": sum(
                    1 for event in exchange_events
                    if event.get("actor") == key and event.get("exchange", {}).get("counter_success")
                ),
                "counter_windows_created": sum(
                    1 for event in exchange_events
                    if event.get("defender") == key and event.get("exchange", {}).get("counter_opportunity")
                ),
                "move_families": deepcopy(family_summary.get(key, {})),
            }
            for key in ("a", "b")
        }
        self._last_fight_result = FightResult(
            winner_id=winner_id, loser_id=loser_id, method=method,
            verdict=str(state.get("decision_verdict") or method), round_no=round_no,
            commentary=tuple(lines), trace=tuple(deepcopy(trace)),
            scorecards=tuple(deepcopy(state.get("judge_scores", []))),
            metrics={
                "a": deepcopy(getattr(a, "last_fight_stats", None) or {}),
                "b": deepcopy(getattr(b, "last_fight_stats", None) or {}),
                "plans": deepcopy(state.get("plans", {})),
                "exchanges": exchange_summary,
                "signature_moves": deepcopy(signature_summary),
                "techniques": deepcopy(technique_summary),
                "round_analysis": deepcopy(round_analysis),
                "damage_summary": deepcopy(state.get("visible_damage", {})),
                "move_reads": deepcopy(state.get("move_reads", {})),
                "referee": deepcopy(state.get("referee_profile", {})),
                "stoppage_review": deepcopy(state.get("stoppage_review")),
            },
            rules={
                "rounds": self.rules.get("rounds", 3),
                "title_rounds": self.rules.get("title_rounds", 5),
                "round_length": self.rules.get("round_length", 5),
            },
        )
        return self._last_fight_result

    @staticmethod
    def build_round_analysis(exchange_events, plans=None, stance_switches=None):
        rows = {}
        effective = {"landed", "knockdown", "takedown", "submission_attempt", "position_change"}
        for event in exchange_events:
            round_no = int(event.get("round", 1))
            row = rows.setdefault(round_no, {
                "round": round_no, "corners": {"a": {"moves": {}, "families": {}, "effective": 0, "attempts": 0, "defenses": {}, "sequences": [], "damage_events": []},
                                                  "b": {"moves": {}, "families": {}, "effective": 0, "attempts": 0, "defenses": {}, "sequences": [], "damage_events": []}},
                "stance_switches": [], "plan_changes": [],
            })
            actor, defender = event.get("actor"), event.get("defender")
            if actor not in ("a", "b"):
                continue
            corner = row["corners"][actor]
            move_id = str(event.get("move_id", "") or "generic")
            family = str(event.get("move_family", "") or "Other")
            corner["moves"][move_id] = corner["moves"].get(move_id, 0) + 1
            corner["families"][family] = corner["families"].get(family, 0) + 1
            corner["attempts"] += 1
            corner["effective"] += event.get("outcome") in effective
            if defender in ("a", "b"):
                defense_id = str(event.get("defense_id", "") or "generic_defense")
                defenses = row["corners"][defender]["defenses"]
                defenses[defense_id] = defenses.get(defense_id, 0) + 1
                row["corners"][defender]["damage_events"].extend(
                    deepcopy(event.get("visible_damage_events", []) or [])
                )
            sequence = event.get("move_sequence", {}) or {}
            if sequence.get("completed_follow_up"):
                corner["sequences"].append({
                    "source": sequence.get("source_move_id", ""), "move": move_id,
                    "step": sequence.get("step", 0), "branch": sequence.get("branch_reason", ""),
                })
        for key, switches in (stance_switches or {}).items():
            for switch in switches:
                rows.setdefault(int(switch.get("round", 1)), {"round": int(switch.get("round", 1)), "corners": {}, "stance_switches": [], "plan_changes": []})["stance_switches"].append({"corner": key, **switch})
        for key, plan in (plans or {}).items():
            for change in plan.get("history", []):
                if int(change.get("round", 0)) <= 0:
                    continue
                round_no = int(change["round"])
                if round_no in rows:
                    rows[round_no]["plan_changes"].append({"corner": key, **deepcopy(change)})
        return [rows[key] for key in sorted(rows)]

    def _simulate_fight_with_caches(self, a, b, fight):
        self.ensure_rule_defaults()
        max_rounds = self.rules["title_rounds"] if fight.get("main", False) or fight.get("title", False) else self.rules["rounds"]
        round_length_factor = self.rules["round_length"] / 5
        ticks_per_round = max(10, round(18 * round_length_factor))
        a_key, b_key = "a", "b"
        referee_name = self.fight_officiating_rng().choice(["cautious", "standard", "permissive", "late"])
        try:
            rivalry_heat = max(0, int(getattr(a, "rivalry_heat", 0) or 0), int(getattr(b, "rivalry_heat", 0) or 0))
        except (TypeError, ValueError):
            rivalry_heat = 0
        if hasattr(self, "rivalry_heat_between"):
            try:
                rivalry_heat = max(0, int(self.rivalry_heat_between(a, b) or 0))
            except (AttributeError, TypeError, ValueError):
                pass
        state = {
            "fighter_keys": {id(a): a_key, id(b): b_key},
            "position": "range",
            "top": None,
            "bottom": None,
            "clinch_controller": None,
            "clinch_ticks": 0,
            "gas": {a_key: self.starting_fight_gas(a), b_key: self.starting_fight_gas(b)},
            "gas_cap": {a_key: self.starting_fight_gas(a), b_key: self.starting_fight_gas(b)},
            # ``damage`` remains the backward-compatible aggregate durability
            # channel used by the engine.  Location-specific channels power the
            # public fight metrics and must only contain damage to that target.
            "damage": {a_key: 0, b_key: 0},
            "hurt": {a_key: 0, b_key: 0},
            "max_hurt": {a_key: 0, b_key: 0},
            # ``head`` is the calibrated short-term reaction load used by the
            # existing mechanics. ``head_trauma`` is the permanent evidence
            # channel used by the trace and public post-fight statistics.
            "head": {a_key: 0, b_key: 0},
            "head_trauma": {a_key: 0, b_key: 0},
            "body": {a_key: 0, b_key: 0},
            "leg": {a_key: 0, b_key: 0},
            "cuts": {a_key: 0, b_key: 0},
            "cut_state": {a_key: [], b_key: []},
            "visible_damage": {a_key: [], b_key: []},
            "visible_damage_milestones": {
                a_key: {channel: 0 for channel in self.VISIBLE_DAMAGE_MILESTONES},
                b_key: {channel: 0 for channel in self.VISIBLE_DAMAGE_MILESTONES},
            },
            "last_visible_damage_events": [],
            "control": {a_key: 0, b_key: 0},
            "impact": {a_key: 0, b_key: 0},
            "danger": {a_key: 0, b_key: 0},
            "scores": {a_key: [], b_key: []},
            "judge_scores": self.make_judge_cards(a, b, a_key, b_key),
            "knockdowns": {a_key: 0, b_key: 0},
            "unanswered": {a_key: 0, b_key: 0},
            "referee": referee_name,
            "referee_profile": {"name": referee_name, **deepcopy(self.REFEREE_PROFILES[referee_name])},
            "fouls": {a_key: [], b_key: []},
            "point_deductions": {a_key: {}, b_key: {}},
            "last_foul": None,
            "finish_detail": "",
            "finish_category": "",
            "official_time": "",
            "context": self.fight_context(a, b, fight, a_key, b_key),
            "plans": self.fight_plan_state(a, b, fight),
            "counter_window": None,
            "night_form": self.fight_night_form(a, b, a_key, b_key),
            "championship_pacing": bool(fight.get("main") or fight.get("title")),
            "is_title_fight": bool(fight.get("title")),
            "rivalry_heat": rivalry_heat,
            "low_level_chaos": max(0, 68 - ((a.overall + b.overall) / 2)) / 68,
            "last_actor": None,
            "actor_streak": 0,
            "ticks_per_round": ticks_per_round,
            "max_rounds": max_rounds,
            "fighters": {a_key: a, b_key: b},
            "commentary_salt": zlib.crc32(
                repr(self.fight_presentation_rng().getstate()).encode("utf-8")
            ),
            "commentary_profiles": {
                a_key: self.commentary_fighter_profile(a),
                b_key: self.commentary_fighter_profile(b),
            },
            "trait_commentary_seen": {
                a_key: {"rounds": set(), "count": 0},
                b_key: {"rounds": set(), "count": 0},
            },
            "camp_commentary_seen": {
                a_key: {"rounds": set(), "count": 0},
                b_key: {"rounds": set(), "count": 0},
            },
            "ground_inactivity": 0,
            "ground_warning": False,
            "last_referee_ground_action": None,
            "last_submission_technique": None,
            "head_to_head": self.commentary_head_to_head(a, b),
            "round_leaders": [],
            "trace": [],
            "move_reads": {
                a_key: {"moves": {}, "targets": {}, "tags": {}, "setups": {}},
                b_key: {"moves": {}, "targets": {}, "tags": {}, "setups": {}},
            },
            "move_exertion": {a_key: 0.0, b_key: 0.0},
            "move_miss_pressure": {a_key: 0.0, b_key: 0.0},
            "move_counter_vulnerability": {a_key: 0.0, b_key: 0.0},
            "move_chains": {a_key: {}, b_key: {}},
            "current_stance": {a_key: a.stance, b_key: b.stance},
            "stance_switch_tick": {a_key: -99, b_key: -99},
            "stance_switches": {a_key: [], b_key: []},
            "stats": {
                a_key: {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0, "control_ticks": 0},
                b_key: {"sig": 0, "sig_att": 0, "td": 0, "td_att": 0, "sub_att": 0, "control_ticks": 0},
            },
        }
        a_scale = f"{a.scale_weight} lb" if a.scale_weight else "not recorded"
        b_scale = f"{b.scale_weight} lb" if b.scale_weight else "not recorded"
        a_signatures = ", ".join(self.fighter_signature_move_labels(a)) or "none declared"
        b_signatures = ", ".join(self.fighter_signature_move_labels(b)) or "none declared"
        lines = [f"Tale of the tape: {a.style_label} / {a.stance} / {a.behaviour} / {a.trait} (signatures: {a_signatures}) vs {b.style_label} / {b.stance} / {b.behaviour} / {b.trait} (signatures: {b_signatures}). Rules: {max_rounds}x{self.rules['round_length']}. Scale: {a_scale} vs {b_scale}."]
        for fighter in (a, b):
            trait_intro = self.commentary_trait_intro(fighter)
            if trait_intro:
                lines.append(trait_intro)
        lines.extend(self.commentary_opening_context(a, b, fight, state))

        round_commentary = []

        def add_fight_line(line):
            clean = line.strip()
            if not clean:
                return
            # Keep every generated call. The player may choose a full play-by-
            # play watch, so repeated templates and clocked exchanges are still
            # meaningful commentary rather than disposable duplicates.
            round_commentary.append(line)

        def flush_round_commentary():
            """Flush the complete round call without dropping play-by-play."""
            lines.extend(round_commentary)
            round_commentary.clear()

        for round_no in range(1, max_rounds + 1):
            # Commentary beats are not evenly spaced in a real round.  Use a
            # local, stable RNG so clock variety never changes combat rolls.
            state["round_clock_seconds"] = self.fight_clock_schedule(a, b, round_no, ticks_per_round)
            round_stats = {a_key: {"impact": 0, "control": 0, "danger": 0}, b_key: {"impact": 0, "control": 0, "danger": 0}}
            # Every scored round begins standing. Ground and clinch control cannot
            # leak through the horn into the next round.
            state["position"] = "range"
            if state["position"] in ("range", "pocket", "clinch", "cage"):
                state["top"] = None
                state["bottom"] = None
            if state["position"] in ("range", "pocket"):
                state["clinch_controller"] = None
            # A horn ends any unanswered sequence. Carrying a late flurry into
            # the next round could otherwise create a stoppage after both
            # fighters had received a full corner break.
            state["unanswered"][a_key] = 0
            state["unanswered"][b_key] = 0
            if round_no > 1:
                transition = self.commentary_round_transition(a, b, state)
                if transition:
                    lines.append(f"Between rounds: {transition}")
            lines.append(f"Round {round_no}: {self.fight_phrase('round_start', a, b, state=state)}")

            for tick in range(1, ticks_per_round + 1):
                state["round"] = round_no
                state["tick"] = tick
                state["official_time"] = self.elapsed_round_time(tick, ticks_per_round, state["round_clock_seconds"])
                state["early_round"] = tick <= max(3, ticks_per_round // 3)
                a_init = self.initiative(a, b, state)
                b_init = self.initiative(b, a, state)
                actor, defender = (a, b) if a_init >= b_init else (b, a)
                if state["last_actor"] == self.fight_state_key(actor, state) and state["actor_streak"] >= 2:
                    other = defender
                    other_init = b_init if other is b else a_init
                    actor_init = a_init if actor is a else b_init
                    comeback_chance = 0.24 + min(0.28, state["actor_streak"] * 0.06) + max(0, other.fight_iq - 55) / 220
                    if (other_init + self.fight_mechanics_rng().randint(-8, 18) > actor_init - 22
                            and self.fight_mechanics_rng().random() < comeback_chance):
                        actor, defender = defender, actor
                if state["last_actor"] == self.fight_state_key(actor, state):
                    state["actor_streak"] += 1
                else:
                    state["last_actor"] = self.fight_state_key(actor, state)
                    state["actor_streak"] = 1
                action = self.choose_action(actor, defender, state, round_no, tick)
                state["last_foul"] = None
                state["last_visible_damage_events"] = []
                trace_before = self.fight_trace_snapshot(a, b, state)
                round_before = deepcopy(round_stats)
                result = self.resolve_exchange(actor, defender, action, state, round_stats)
                for key in (a_key, b_key):
                    damage_gain = max(0, state["damage"][key] - trace_before["damage"][key])
                    state["hurt"][key] += damage_gain
                    state["max_hurt"][key] = max(state["max_hurt"][key], state["hurt"][key])
                self.update_dynamic_stance(actor, defender, state)
                state["last_move_payload"] = self.select_exchange_move(
                    actor, defender, action, trace_before["position"], state.get("last_strike_target"), state,
                )
                state["last_move_actor"] = self.fight_state_key(actor, state)
                state["last_visible_damage_events"] = self.record_visible_damage_events(
                    actor, defender, trace_before, state,
                )
                counter_window = state.get("counter_window") or {}
                if (counter_window.get("created_tick") == tick
                        and counter_window.get("created_round") == round_no):
                    counter_window["source_move_id"] = state["last_move_payload"]["move_id"]
                    counter_window["source_counter_risk"] = state["last_move_payload"]["counter_risk"]
                self.apply_exchange_fatigue(actor, defender, action, state)
                control_fighter = state["top"] if state["position"] in ("guard", "half guard", "side control", "mount", "back control") else state["clinch_controller"]
                if control_fighter:
                    state["stats"][control_fighter]["control_ticks"] += 1
                ground_note = self.update_ground_inactivity(state, action)
                incident = self.resolve_fight_incident(actor, defender, state) if not ground_note else ""
                trace_event = self.record_fight_trace_exchange(
                    a, b, actor, defender, action, result, trace_before, round_before, state, round_stats,
                )
                clock = self.round_clock(tick, ticks_per_round, state["round_clock_seconds"])
                exchange_call = self.render_exchange_trace_event(trace_event)
                if exchange_call:
                    rendered = f"  [{clock}] {exchange_call}"
                    add_fight_line(rendered)
                    trace_event["commentary"].append(rendered.strip())
                    damage_lines = self.render_visible_damage_narratives(trace_event)
                    trace_event["damage_narrative"] = list(damage_lines)
                    for damage_line in damage_lines:
                        rendered = f"  [{clock}] {damage_line}"
                        add_fight_line(rendered)
                        trace_event["commentary"].append(rendered.strip())
                    presence = self.fighter_presence_line(actor, defender, state)
                    if presence:
                        rendered = f"  [{clock}] {presence}"
                        add_fight_line(rendered)
                        trace_event["commentary"].append(rendered.strip())
                if ground_note:
                    referee_action = trace_event.get("referee_ground_action") or {}
                    if referee_action.get("type") != "standup":
                        rendered = f"  [{clock}] {ground_note}"
                        add_fight_line(rendered)
                        trace_event["commentary"].append(rendered.strip())
                else:
                    if incident:
                        rendered = f"  [{clock}] {incident}"
                        add_fight_line(rendered)
                        trace_event["commentary"].append(rendered.strip())
                    flavor = self.dynamic_flavor_line(actor, defender, state, round_no)
                    if flavor:
                        rendered = f"  [{clock}] {flavor}"
                        add_fight_line(rendered)
                        trace_event["commentary"].append(rendered.strip())
                stoppage = self.check_fight_stoppage(actor, defender, state)
                if stoppage:
                    winner, loser, method, detail = stoppage
                    rendered = f"  [{clock}] {detail}"
                    add_fight_line(rendered)
                    trace_event["commentary"].append(rendered.strip())
                    trace_event["stoppage"] = {
                        "winner": self.fight_state_key(winner, state),
                        "loser": self.fight_state_key(loser, state),
                        "method": method,
                        "reason": state.get("finish_category") or method,
                    }
                    flush_round_commentary()
                    lines.extend(self.commentary_closing_context(a, b, winner, method, state))
                    self.attach_fight_stats(a, b, state, round_no, lines)
                    self.finalize_fight_result(a, b, winner, loser, method, round_no, lines, state)
                    return winner, loser, method, round_no, lines

            flush_round_commentary()

            judge_rounds = []
            for judge in state["judge_scores"]:
                winner, loser, score = self.score_round(a, b, round_stats, state, judge=judge)
                if winner is None:
                    a_score, b_score = 10, 10
                else:
                    a_score, b_score = (10, score) if winner is a else (score, 10)
                deductions = {
                    a_key: int(state["point_deductions"][a_key].get(round_no, 0)),
                    b_key: int(state["point_deductions"][b_key].get(round_no, 0)),
                }
                a_score = max(7, a_score - deductions[a_key])
                b_score = max(7, b_score - deductions[b_key])
                judge[self.fight_state_key(a, state)].append(a_score)
                judge[self.fight_state_key(b, state)].append(b_score)
                judge["rounds"].append({
                    "round": round_no, "a_score": a_score, "b_score": b_score,
                    "deductions": deductions,
                    "evidence": deepcopy(self.round_evidence_from_trace(state, round_no)),
                })
                judge_rounds.append((a_score, b_score))
            # This is only a running broadcast estimate; the three official cards
            # remain independent until the decision is announced after the fight.
            a_average = round(sum(score[0] for score in judge_rounds) / len(judge_rounds))
            b_average = round(sum(score[1] for score in judge_rounds) / len(judge_rounds))
            state["scores"][self.fight_state_key(a, state)].append(a_average)
            state["scores"][self.fight_state_key(b, state)].append(b_average)
            total_a = sum(state["scores"][self.fight_state_key(a, state)])
            total_b = sum(state["scores"][self.fight_state_key(b, state)])
            momentum_key = a_key if round_stats[a_key]["impact"] + round_stats[a_key]["danger"] >= round_stats[b_key]["impact"] + round_stats[b_key]["danger"] else b_key
            momentum_name = a.name if momentum_key == a_key else b.name
            if total_a > total_b:
                broadcast_read = f"{a.name} is ahead on the unofficial broadcast card"
            elif total_b > total_a:
                broadcast_read = f"{b.name} is ahead on the unofficial broadcast card"
            else:
                broadcast_read = "the unofficial broadcast card is even"
            lines.append(
                f"Round {round_no} summary: Broadcast read - {broadcast_read}; official cards remain sealed. "
                f"Metrics - {a.name}: impact {round_stats[self.fight_state_key(a, state)]['impact']}, control {round_stats[self.fight_state_key(a, state)]['control']}, danger {round_stats[self.fight_state_key(a, state)]['danger']}; "
                f"{b.name}: impact {round_stats[self.fight_state_key(b, state)]['impact']}, control {round_stats[self.fight_state_key(b, state)]['control']}, danger {round_stats[self.fight_state_key(b, state)]['danger']}. "
                f"Gas: {a.name} {round(state['gas'][a_key])}, {b.name} {round(state['gas'][b_key])}. Momentum: {momentum_name}. "
                f"Move families (effective/used) - {a.name}: {self.round_move_family_summary(state, a_key, round_no)}; "
                f"{b.name}: {self.round_move_family_summary(state, b_key, round_no)}."
            )
            state["commentary_memory"] = {
                "leader": momentum_key, "a_damage": state["damage"][a_key], "b_damage": state["damage"][b_key],
                "a_gas": round(state["gas"][self.fight_state_key(a, state)]), "b_gas": round(state["gas"][self.fight_state_key(b, state)]), "round": round_no,
            }
            callback = self.commentary_round_callback(a, b, state, momentum_key, round_no)
            if callback:
                lines.append(f"Broadcast read: {callback}")
            if round_no < max_rounds:
                lines.extend(self.adapt_fight_plans(a, b, state, round_no, max_rounds))
                corner = self.check_corner_stoppage(a, b, state, round_no)
                if corner:
                    winner, loser, method, detail = corner
                    lines.append(detail)
                    lines.extend(self.commentary_closing_context(a, b, winner, method, state))
                    self.attach_fight_stats(a, b, state, round_no, lines)
                    self.finalize_fight_result(a, b, winner, loser, method, round_no, lines, state)
                    return winner, loser, method, round_no, lines
                self.recover_between_rounds(a, b, state)

        lines.extend(self.final_scorecard_lines(a, b, state))
        decision = self.decision_from_judges(a, b, state)
        state["decision_verdict"] = decision["verdict"]
        if decision["winner"] is None:
            lines.append(f"Official verdict: {decision['verdict']}.")
            lines.append(self.fight_phrase("draw", a, b, score=decision["summary"]))
            lines.extend(self.commentary_closing_context(a, b, None, "Draw", state))
            self.attach_fight_stats(a, b, state, max_rounds, lines)
            self.finalize_fight_result(a, b, None, None, "Draw", max_rounds, lines, state)
            return a, b, "Draw", max_rounds, lines
        winner = decision["winner"]
        loser = b if winner is a else a
        method = "Decision"
        lines.append(f"Official verdict: {decision['verdict']}.")
        lines.append(self.fight_phrase("decision", winner, loser, score=decision["summary"]))
        lines.extend(self.commentary_closing_context(a, b, winner, method, state))
        self.attach_fight_stats(a, b, state, max_rounds, lines)
        self.finalize_fight_result(a, b, winner, loser, method, max_rounds, lines, state)
        return winner, loser, method, max_rounds, lines

    def commentary_head_to_head(self, a, b):
        """Read prior meetings from stable opponent IDs, with a safe legacy fallback."""
        meetings = a_wins = b_wins = 0
        last_result = ""
        b_id = str(getattr(b, "fighter_id", "") or "")

        # Current careers keep a structured pre-bout ledger with the opponent's
        # durable identity. It is the authoritative source because display
        # names are not unique and can also change over a long career.
        for entry in (getattr(a, "bout_rating_history", None) or []):
            if not isinstance(entry, dict):
                continue
            opponent_id = str(entry.get("opponent_id", "") or "")
            if not b_id or opponent_id != b_id:
                continue
            result = str(entry.get("result", "") or "").upper()
            meetings += 1
            a_wins += int(result == "W")
            b_wins += int(result == "L")
            if not last_result:
                last_result = str(entry.get("date", "") or "")
        if meetings:
            return {"meetings": meetings, "a_wins": a_wins, "b_wins": b_wins, "last_result": last_result}

        # Legacy text rows have no durable identity. Accept them only when the
        # requested opponent name resolves to one fighter in the known world;
        # same-name opponents must never inherit another fighter's history.
        if a.name.casefold() == b.name.casefold():
            return {"meetings": 0, "a_wins": 0, "b_wins": 0, "last_result": ""}
        if hasattr(self, "all_fighter_objects"):
            same_name = [
                fighter for fighter in self.all_fighter_objects()
                if str(getattr(fighter, "name", "")).casefold() == b.name.casefold()
            ]
            if len(same_name) != 1 or same_name[0] is not b:
                return {"meetings": 0, "a_wins": 0, "b_wins": 0, "last_result": ""}
        else:
            return {"meetings": 0, "a_wins": 0, "b_wins": 0, "last_result": ""}

        for entry in (a.fight_history or []):
            text = str(entry)
            folded = text.casefold()
            if b.name.casefold() not in folded or (" def. " not in folded and "fought to a draw" not in folded):
                continue
            meetings += 1
            if f"{a.name} def.".casefold() in folded:
                a_wins += 1
            elif f"{b.name} def.".casefold() in folded:
                b_wins += 1
            last_result = text
        return {"meetings": meetings, "a_wins": a_wins, "b_wins": b_wins, "last_result": last_result}

    def commentary_opening_context(self, a, b, fight, state=None):
        lines = []
        # ``dict.get`` evaluates its default eagerly. The previous expression
        # therefore repeated the complete ID/legacy history lookup even though
        # fight setup had already stored the result in state.
        head_to_head = (state or {}).get("head_to_head")
        if head_to_head is None:
            head_to_head = self.commentary_head_to_head(a, b)
        prior_meetings = head_to_head["meetings"]
        if fight.get("title"):
            lines.append("Broadcast context: championship stakes raise the pressure; composure and late-round reserves could decide this one.")
        if hasattr(self, "rivalry_heat_between") and self.rivalry_heat_between(a, b):
            heat = self.rivalry_heat_between(a, b) if hasattr(self, "rivalry_heat_between") else max(getattr(a, "rivalry_heat", 0), getattr(b, "rivalry_heat", 0))
            lines.append(f"Broadcast context: this rivalry is running at {heat}/100 heat — every exchange carries extra meaning.")
        if prior_meetings:
            lines.append(f"Broadcast context: head-to-head is {a.name} {head_to_head['a_wins']}-{head_to_head['b_wins']} {b.name} across {prior_meetings} prior meeting{'s' if prior_meetings != 1 else ''}; adjustments will matter early.")
        a_corner = self.commentary_corner_identity(a)
        b_corner = self.commentary_corner_identity(b)
        shared_verified_camp = (
            a_corner["verified_gym"] and b_corner["verified_gym"]
            and a_corner["camp"].casefold() == b_corner["camp"].casefold()
        )
        corner_reads = []
        if shared_verified_camp:
            shared = a_corner
            room_facts = []
            if shared["coach"]:
                room_facts.append(f"led by {shared['coach']}")
            location = shared["city"] or shared["region"]
            if location:
                room_facts.append(f"based in {location}")
            if shared["specialties"]:
                specialties = list(shared["specialties"])
                specialty_copy = ", ".join(specialties[:-1]) + (
                    f" and {specialties[-1]}" if len(specialties) > 1 else specialties[-1]
                )
                room_facts.append(f"known for {specialty_copy}")
            details = f", {', '.join(room_facts)}" if room_facts else ""
            corner_reads.append(
                f"{a.name} and {b.name} are stablemates from {shared['camp']}{details}."
            )
        else:
            for fighter in (a, b):
                camp_intro = self.commentary_camp_intro(fighter)
                if camp_intro:
                    corner_reads.append(camp_intro)
        if corner_reads:
            lines.extend(corner_reads)
        if fight.get("region") and hasattr(self, "fighter_event_connection"):
            a_home = self.fighter_event_connection(a, fight["region"], fight.get("city", ""))
            b_home = self.fighter_event_connection(b, fight["region"], fight.get("city", ""))
            if a_home["strength"] >= 0.52 and a_home["strength"] > b_home["strength"] + 0.15:
                lines.append(f"Broadcast context: {a.name} is fighting in a {a_home['level'].lower()} market and has the crowd behind them tonight.")
            elif b_home["strength"] >= 0.52 and b_home["strength"] > a_home["strength"] + 0.15:
                lines.append(f"Broadcast context: {b.name} is fighting in a {b_home['level'].lower()} market and has the crowd behind them tonight.")
            elif a_home["strength"] >= 0.52 and b_home["strength"] >= 0.52:
                lines.append("Broadcast context: both fighters carry a meaningful local connection tonight, making this a split-room atmosphere.")
        a_morale = max(0, min(100, getattr(a, "morale", 60)))
        b_morale = max(0, min(100, getattr(b, "morale", 60)))
        def readiness_word(morale):
            if morale >= 80:
                return "energised and confident"
            if morale >= 65:
                return "settled and ready"
            if morale >= 50:
                return "composed"
            return "under visible pressure"

        lines.append(
            f"Fight-night readiness: {a.name} looks {readiness_word(a_morale)}; "
            f"{b.name} looks {readiness_word(b_morale)}. "
            "The stronger corner still has to prove it through skill and conditioning."
        )
        return lines

    def commentary_round_callback(self, a, b, state, leader_key, round_no):
        leaders = state.setdefault("round_leaders", [])
        prior = leaders[-1] if leaders else ""
        leaders.append(leader_key)
        leader = a if leader_key == self.fight_state_key(a, state) else b
        trailing = b if leader is a else a
        head_to_head = state.get("head_to_head", {})
        if prior and prior != leader_key:
            prior_name = a.name if prior == self.fight_state_key(a, state) else b.name
            return f"Momentum has swung from {prior_name} to {leader.name}; {trailing.name}'s corner must answer the adjustment."
        if state["cuts"].get(self.fight_state_key(trailing, state), 0) >= 2:
            return f"{trailing.name}'s face is showing the accumulated work, and the referee will be watching it closely."
        if state["body"].get(self.fight_state_key(trailing, state), 0) >= 16:
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
        leader_is_a = leader == self.fight_state_key(a, state)
        trailing = b if leader_is_a else a
        leader_fighter = a if leader_is_a else b
        leader_damage = memory.get("a_damage", 0) if leader_is_a else memory.get("b_damage", 0)
        trailing_damage = memory.get("b_damage", 0) if leader_is_a else memory.get("a_damage", 0)
        if trailing_damage - leader_damage >= 10:
            return f"{trailing.name}'s corner needs urgency after absorbing the heavier damage in round {memory.get('round', 1)}."
        leader_gas = memory.get("a_gas", 0) if leader_is_a else memory.get("b_gas", 0)
        trailing_gas = memory.get("b_gas", 0) if leader_is_a else memory.get("a_gas", 0)
        if leader_gas - trailing_gas >= 12:
            return f"{leader_fighter.name} carries the fresher gas tank; {trailing.name} needs to change the pace."
        return f"{leader_fighter.name} edged the last round, but the fight remains close enough for a tactical swing."

    def commentary_closing_context(self, a, b, winner, method, state):
        if winner is None:
            return ["Broadcast recap: neither fighter created enough separation; the unresolved story is likely to invite more debate."]
        loser = b if winner is a else a
        if hasattr(self, "rivalry_heat_between") and self.rivalry_heat_between(winner, loser):
            return [f"Broadcast recap: {winner.name} wins a meaningful rivalry chapter by {method}; the feud may not be finished."]
        head_to_head = state.get("head_to_head", {})
        if head_to_head.get("meetings", 0):
            a_wins = head_to_head.get("a_wins", 0) + int(winner is a)
            b_wins = head_to_head.get("b_wins", 0) + int(winner is b)
            return [f"Broadcast recap: the head-to-head now stands {a.name} {a_wins}-{b_wins} {b.name}; this rivalry has real history."]
        memory = state.get("commentary_memory", {})
        leader = memory.get("leader")
        if leader and leader != self.fight_state_key(winner, state):
            leader_name = a.name if leader == self.fight_state_key(a, state) else b.name
            return [f"Broadcast recap: {winner.name} turned the fight after {leader_name} had the earlier momentum."]
        return [f"Broadcast recap: {winner.name}'s game plan held up across the fight and earned the {method} victory."]

    def attach_fight_stats(self, a, b, state, ending_round, lines):
        """Build a readable box score from the same events that produced commentary."""
        def metric(value):
            return max(0, int(round(float(value or 0))))

        seconds_per_tick = (self.rules.get("round_length", 5) * 60) / max(1, state.get("ticks_per_round", 18))
        for fighter in (a, b):
            s = state["stats"][self.fight_state_key(fighter, state)]
            plan_row = self.fight_plan_for(fighter, state)
            s["control_secs"] = metric(s["control_ticks"] * seconds_per_tick)
            s["knockdowns"] = metric(state["knockdowns"].get(self.fight_state_key(fighter, state), 0))
            fighter.last_fight_stats = {
                "sig": metric(s["sig"]), "sig_att": metric(s["sig_att"]), "td": metric(s["td"]), "td_att": metric(s["td_att"]),
                "sub_att": metric(s["sub_att"]), "control_secs": s["control_secs"], "knockdowns": s["knockdowns"], "rounds": metric(ending_round),
                # Keep damage_taken for older profile/save consumers, but make
                # the public total exactly match its visible location breakdown.
                # The separate internal damage pool remains responsible for
                # recovery and stoppage logic during the fight.
                "damage_taken": metric(state.get("head_trauma", state["head"])[self.fight_state_key(fighter, state)] + state["body"][self.fight_state_key(fighter, state)] + state["leg"][self.fight_state_key(fighter, state)]),
                "head_damage": metric(state.get("head_trauma", state["head"])[self.fight_state_key(fighter, state)]),
                "body_damage": metric(state["body"][self.fight_state_key(fighter, state)]), "leg_damage": metric(state["leg"][self.fight_state_key(fighter, state)]), "cuts": metric(state["cuts"][self.fight_state_key(fighter, state)]),
                "max_hurt": metric(state["max_hurt"][self.fight_state_key(fighter, state)]),
                "cut_details": deepcopy(state["cut_state"][self.fight_state_key(fighter, state)]),
                "visible_damage": deepcopy(
                    state.get("visible_damage", {}).get(self.fight_state_key(fighter, state), [])
                ),
                "fight_plan": plan_row["initial"], "final_fight_plan": plan_row["current"],
                "plan_effective_actions": metric(plan_row["effective_actions"]),
                "plan_attempts": metric(plan_row["attempts"]),
                "plan_history": deepcopy(plan_row["history"]),
                "plan_adjustments": metric(plan_row.get("adjustments", 0)),
                "plan_confidence": round(float(plan_row.get("confidence", 0.5)), 3),
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
            f"{a.name:<{name_width}}  {line_for(a)}  {a.last_fight_stats['head_damage']:>3}/{a.last_fight_stats['body_damage']:>2}/{a.last_fight_stats['leg_damage']:>2}/{a.last_fight_stats['cuts']}",
            f"{b.name:<{name_width}}  {line_for(b)}  {b.last_fight_stats['head_damage']:>3}/{b.last_fight_stats['body_damage']:>2}/{b.last_fight_stats['leg_damage']:>2}/{b.last_fight_stats['cuts']}",
            (f"Plan recap - {a.name}: {a.last_fight_stats['fight_plan']} -> {a.last_fight_stats['final_fight_plan']}; "
             f"{a.last_fight_stats['plan_effective_actions']}/{a.last_fight_stats['plan_attempts']} effective actions."),
            (f"Plan recap - {b.name}: {b.last_fight_stats['fight_plan']} -> {b.last_fight_stats['final_fight_plan']}; "
             f"{b.last_fight_stats['plan_effective_actions']}/{b.last_fight_stats['plan_attempts']} effective actions."),
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
        career_signatures = getattr(fighter, "career_signature_stats", None)
        if not isinstance(career_signatures, dict):
            career_signatures = {}
            fighter.career_signature_stats = career_signatures
        for move_id, row in (stats.get("signature_moves", {}) or {}).items():
            total = career_signatures.setdefault(move_id, {"attempts": 0, "landed": 0, "finishes": 0})
            for key in ("attempts", "landed", "finishes"):
                total[key] = int(total.get(key, 0)) + int(row.get(key, 0))
        career_families = getattr(fighter, "career_move_family_stats", None)
        if not isinstance(career_families, dict):
            career_families = {}
            fighter.career_move_family_stats = career_families
        for family, row in (stats.get("move_families", {}) or {}).items():
            total = career_families.setdefault(family, {"attempts": 0, "effective": 0})
            for key in ("attempts", "effective"):
                total[key] = int(total.get(key, 0)) + int(row.get(key, 0))
        if won and result_method in FINISH_METHODS:
            fighter.career_finishes = getattr(fighter, "career_finishes", 0) + 1
        if won and result_method in KO_METHODS:
            fighter.career_knockouts = getattr(fighter, "career_knockouts", 0) + 1
        if won and result_method in SUBMISSION_METHODS:
            fighter.career_submissions = getattr(fighter, "career_submissions", 0) + 1
        fighter.last_fight_stats = None

    def starting_fight_gas(self, fighter):
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        resilience = self.ds(fighter, "resilience", fighter.toughness)
        cap = 92 + (conditioning - 50) * 0.18 + (fighter.cardio - 50) * 0.09 + (resilience - 50) * 0.04
        trait = 4 if fighter.trait == "Cardio Machine" else -5 if fighter.trait == "Bad Weight Cut" else 0
        penalty = fighter.fatigue * 0.48 + fighter.weight_cut_penalty * 1.35 + getattr(fighter, "division_size_penalty", 0) * 0.32
        return max(18, min(100, round(cap + trait - penalty)))

    def update_ground_inactivity(self, state, action):
        state["last_referee_ground_action"] = None
        if state["position"] not in self.GROUND_POSITIONS:
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
            note = self.fight_presentation_choice([
                "The referee calls for more activity from the grounded fighters.",
                "The referee circles the action and warns both fighters to work.",
                "\"Let's go, work!\" - the referee wants more from the ground exchange.",
                "The crowd murmurs as the referee urges the fighters to improve position or stand.",
                "The referee crouches in close and tells them to be busy on the mat.",
            ])
            state["last_referee_ground_action"] = {
                "type": "warning", "position": state["position"], "text": note,
            }
            return note
        threshold = self.referee_profile(state)["standup_threshold"]
        if state["ground_warning"] and state["ground_inactivity"] >= threshold:
            prior_position = state["position"]
            state["position"] = "range"
            state["top"] = None
            state["bottom"] = None
            state["clinch_controller"] = None
            state["ground_inactivity"] = 0
            state["ground_warning"] = False
            note = self.fight_presentation_choice([
                "After a prolonged stalemate on the mat, the referee stands them up.",
                "The referee has seen enough of the lull and brings them back to the feet.",
                "Stalemate on the ground - the referee resets the fighters at range.",
                "The referee waves it up; the ground position had gone stagnant.",
            ])
            state["last_referee_ground_action"] = {
                "type": "standup", "position": prior_position, "text": note,
            }
            return note
        return ""

    def fight_context(self, a, b, fight, a_key=None, b_key=None):
        region = fight.get("region", fight.get("event_region", ""))
        a_key = a_key or f"fighter-{id(a)}"
        b_key = b_key or f"fighter-{id(b)}"
        context = {a_key: {}, b_key: {}}
        for fighter, opponent in ((a, b), (b, a)):
            stance_edge = self.stance_matchup_edge(fighter, opponent)
            home_edge = 2.2 if region and fighter.region == region else 0
            prime_edge = self.prime_fight_edge(fighter)
            experience_edge = self.experience_fight_edge(fighter)
            pressure_edge = self.pressure_fight_edge(fighter, opponent, fight)
            rivalry_target = self.resolve_rivalry_target(fighter) if hasattr(self, "resolve_rivalry_target") else None
            friend_target = self.resolve_friend_target(fighter) if hasattr(self, "resolve_friend_target") else None
            rivalry_edge = (1.6 + min(4.2, getattr(fighter, "rivalry_heat", 0) / 24)
                            if rivalry_target is opponent else (-1.5 if friend_target is opponent else 0))
            reach_edge = (self.ds(fighter, "reach", 50) - self.ds(opponent, "reach", 50)) * 0.035
            size_edge = (self.ds(fighter, "natural_size", 50) - self.ds(opponent, "natural_size", 50)) * 0.04
            style_edge = self.style_matchup_bonus(fighter, opponent) * 0.55
            morale_edge = self.morale_fight_edge(fighter)
            context[a_key if fighter is a else b_key] = {
                "stance": stance_edge,
                "home": home_edge,
                "prime": prime_edge,
                "experience": experience_edge,
                "pressure": pressure_edge,
                "rivalry": rivalry_edge,
                "reach": reach_edge,
                "size": size_edge,
                "style": style_edge,
                "morale": morale_edge,
            }
        return context

    def morale_fight_edge(self, fighter):
        """Return a deliberately small fight-night readiness adjustment.

        Morale is neutral at 60 and capped at +/-2.5.  Core technical values are
        generally measured in the dozens and night-form alone spans +/-22, so
        morale can shade execution without deciding a fight by itself.
        """
        morale = max(0, min(100, getattr(fighter, "morale", 60)))
        return round(max(-2.5, min(2.5, (morale - 60) / 16)), 2)

    def fight_night_form(self, a, b, a_key=None, b_key=None):
        """One bounded performance roll for the whole bout, not a result override.

        This represents game-plan execution, timing and minor physical readiness.
        It alters initiative and every technical exchange, so an underdog can earn
        an upset through the same actions that decide every other fight. Consistent
        fighters remain steadier, but no elite athlete is mechanically perfect.
        """
        form = {}
        a_key = a_key or f"fighter-{id(a)}"
        b_key = b_key or f"fighter-{id(b)}"
        rating_gap = abs(a.overall - b.overall)
        # A narrow overall gap means the public and matchmaker cannot cleanly
        # separate the two athletes. It therefore carries a little more normal
        # fight-night uncertainty than a true mismatch. This is symmetric and
        # zero-centred: it raises neither fighter's expected result by itself.
        close_match_variance = max(0, 4 - rating_gap) * 1.5
        for fighter in (a, b):
            consistency = self.ds(fighter, "consistency", 50)
            # A modestly wider range lets a sharp game plan, timing, or an
            # off-night matter in close contests. It remains zero-centred and
            # bounded, so ratings, conditioning, damage, and skill layers still
            # do the decisive work over a large sample.
            spread = 12.2 + max(0, 86 - consistency) * 0.055 + close_match_variance
            form[a_key if fighter is a else b_key] = round(max(-22, min(22, self.fight_mechanics_rng().gauss(0, spread))), 2)
        return form

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
        values = state.get("context", {}).get(self.fight_state_key(fighter, state), {})
        return sum(values.get(key, 0) for key in keys) * 0.45

    def turnaround_recovery_modifier(self, fighter):
        """How much the gap since a fighter's last bout leaves in the tank.

        Deliberately small: the day a card is booked on should colour a fight,
        not decide it. Returns 0 for anyone without a dated previous bout, so
        older saves are unaffected.
        """
        rest_days = self.fighter_rest_days(
            fighter, self.month, self.week, getattr(self, "_active_card_day", None)
        )
        if rest_days is None:
            return 0.0
        # Six weeks is an unremarkable turnaround; short notice costs more than
        # a long lay-off gives back.
        return max(-0.7, min(0.3, (rest_days - 42) / 130))

    def recover_between_rounds(self, a, b, state):
        for fighter in (a, b):
            conditioning = self.ds(fighter, "conditioning", fighter.cardio)
            resilience = self.ds(fighter, "resilience", fighter.toughness)
            camp_quality = fighter.camp_quality or self.gym_quality(fighter.camp)
            camp_recovery = min(2.4, camp_quality / 70 + fighter.camp_weeks * 0.08 + fighter.camp_boost * 0.12)
            camp_recovery += self.turnaround_recovery_modifier(fighter)
            recovery = 2 + conditioning / 30 + fighter.cardio / 36 + resilience / 55 + camp_recovery
            recovery -= state["hurt"][self.fight_state_key(fighter, state)] / 28 + state["body"][self.fight_state_key(fighter, state)] / 9 + state["leg"][self.fight_state_key(fighter, state)] / 24
            if fighter.trait == "Cardio Machine":
                recovery += 2.2
            if fighter.trait == "Bad Weight Cut":
                recovery -= 3
            recovery += self.context_edge(fighter, state, "prime", "experience", "pressure") * 0.18
            elite_control = max(0, fighter.overall - 78) / 14
            recovery += elite_control * 1.6
            hurt_recovery = max(0.25, recovery * 0.06)
            if state.get("championship_pacing") and state.get("round", 1) >= 3:
                hurt_recovery += 1.4 + elite_control * 1.2
            state["hurt"][self.fight_state_key(fighter, state)] = max(
                0, state["hurt"][self.fight_state_key(fighter, state)] - hurt_recovery
            )
            # Corners restore a little, never a fresh tank. The original fight cap
            # already includes the fighter's camp and weight-cut condition.
            state["gas"][self.fight_state_key(fighter, state)] = max(3, min(state["gas_cap"][self.fight_state_key(fighter, state)], state["gas"][self.fight_state_key(fighter, state)] + max(1, recovery)))

    def check_corner_stoppage(self, a, b, state, round_no):
        state["round"] = round_no
        state["official_time"] = f"{self.rules.get('round_length', 5)}:00"
        for fighter, opponent in ((a, b), (b, a)):
            damage = state["hurt"][self.fight_state_key(fighter, state)]
            body = state["body"][self.fight_state_key(fighter, state)]
            leg = state["leg"][self.fight_state_key(fighter, state)]
            gas = state["gas"][self.fight_state_key(fighter, state)]
            danger = state["danger"][self.fight_state_key(opponent, state)]
            if damage > fighter.toughness * 1.05 or body > 30 or leg > 28 or (gas < 10 and danger > 18):
                # Corner stoppages should be exceptional medical decisions, not
                # a second, frequent TKO route. A corner can see a severe
                # accumulation of damage only once between rounds, after the
                # referee has already allowed the fighter to survive the horn.
                # The former 8% base chance made a routine bad round end an
                # implausibly common concession across a full card.
                chance = (0.012
                          + max(0, damage - fighter.toughness * 1.08) / 520
                          + max(0, body - 30) / 230
                          + max(0, leg - 29) / 250
                          + max(0, 7 - gas) / 210)
                if self.fight_mechanics_rng().random() < min(0.22, chance):
                    method = "Corner Stoppage"
                    return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, self.fight_phrase("corner_stoppage", opponent, fighter), state)
        return None

    def make_judge_cards(self, a, b, a_key=None, b_key=None):
        profiles = ["Damage-first", "Balanced", "Control-sensitive"]
        self.fight_judging_rng().shuffle(profiles)
        a_key = a_key or f"fighter-{id(a)}"
        b_key = b_key or f"fighter-{id(b)}"
        return [
            {"name": f"Judge {index + 1}", "profile": profile, a_key: [], b_key: [], "rounds": []}
            for index, profile in enumerate(profiles)
        ]

    def decision_from_judges(self, a, b, state):
        cards = []
        a_key = self.fight_state_key(a, state)
        b_key = self.fight_state_key(b, state)
        votes = {a_key: 0, b_key: 0}
        for judge in state["judge_scores"]:
            a_total = sum(judge[self.fight_state_key(a, state)])
            b_total = sum(judge[self.fight_state_key(b, state)])
            cards.append((judge["name"], a_total, b_total))
            if a_total > b_total:
                votes[self.fight_state_key(a, state)] += 1
            elif b_total > a_total:
                votes[self.fight_state_key(b, state)] += 1
        if votes[a_key] >= 2:
            winner = a
        elif votes[b_key] >= 2:
            winner = b
        else:
            winner = None
        tied_cards = 3 - votes[a_key] - votes[b_key]
        if winner is not None:
            loser_key = b_key if winner is a else a_key
            winner_key = a_key if winner is a else b_key
            if votes[winner_key] == 3:
                verdict = "Unanimous Decision"
            elif tied_cards:
                verdict = "Majority Decision"
            elif votes[loser_key]:
                verdict = "Split Decision"
            else:
                verdict = "Unanimous Decision"
        elif tied_cards == 3:
            verdict = "Unanimous Draw"
        elif tied_cards == 2:
            verdict = "Majority Draw"
        else:
            verdict = "Split Draw"
        summary = ", ".join(f"{a_total}-{b_total}" for _name, a_total, b_total in cards)
        return {"winner": winner, "cards": cards, "votes": votes, "summary": summary,
                "verdict": verdict, "tied_cards": tied_cards}

    def final_scorecard_lines(self, a, b, state):
        decision = self.decision_from_judges(a, b, state)
        lines = ["Official scorecards:"]
        for card, (judge, a_total, b_total) in zip(state["judge_scores"], decision["cards"]):
            leader = a.name if a_total > b_total else b.name if b_total > a_total else "Even"
            lines.append(f"  {judge} [{card['profile']}]: {a.name} {a_total}, {b.name} {b_total} ({leader})")
            for scored_round in card.get("rounds", []):
                deductions = scored_round.get("deductions", {})
                for key, points in deductions.items():
                    if points:
                        fighter_name = a.name if key == self.fight_state_key(a, state) else b.name
                        lines.append(
                            f"    Round {scored_round['round']}: {fighter_name} -{points} point"
                            f"{'s' if points != 1 else ''} for fouls"
                        )
        lines.append(f"  Judges' vote: {a.name} {decision['votes'][self.fight_state_key(a, state)]}, {b.name} {decision['votes'][self.fight_state_key(b, state)]}")
        return lines

    def fight_clock_schedule(self, a, b, round_no, ticks_per_round):
        """Return deterministic, naturally irregular commentary times.

        The engine still resolves the same number of exchanges.  This only
        spaces the broadcast calls, using a local RNG so simulation outcomes
        remain exactly independent of presentation timing.
        """
        total_seconds = max(1, int(self.rules.get("round_length", 5) * 60))
        seed_text = f"{getattr(a, 'fighter_id', a.name)}|{getattr(b, 'fighter_id', b.name)}|{round_no}|{ticks_per_round}|{total_seconds}"
        rng = random.Random(zlib.crc32(seed_text.encode("utf-8")))
        weights = [rng.triangular(0.48, 1.72, 0.96) for _ in range(max(1, ticks_per_round))]
        total_weight = max(0.001, sum(weights))
        elapsed = 0.0
        schedule = []
        previous = total_seconds
        for weight in weights:
            elapsed += weight
            seconds_left = max(0, min(total_seconds, total_seconds - round(total_seconds * elapsed / total_weight)))
            # Each commentary beat must visibly progress the clock.
            seconds_left = min(seconds_left, max(0, previous - 1))
            schedule.append(seconds_left)
            previous = seconds_left
        return schedule

    def round_clock(self, tick, ticks_per_round, clock_seconds=None):
        total_seconds = self.rules.get("round_length", 5) * 60
        if clock_seconds:
            seconds_left = clock_seconds[min(len(clock_seconds) - 1, max(0, tick - 1))]
        else:
            seconds_left = max(0, round(total_seconds * (ticks_per_round - tick) / max(1, ticks_per_round)))
        return f"{seconds_left // 60}:{seconds_left % 60:02d}"

    def elapsed_round_time(self, tick, ticks_per_round, clock_seconds=None):
        total_seconds = self.rules.get("round_length", 5) * 60
        if clock_seconds:
            seconds_left = clock_seconds[min(len(clock_seconds) - 1, max(0, tick - 1))]
            elapsed = total_seconds - seconds_left
        else:
            elapsed = min(total_seconds, max(0, round(total_seconds * tick / max(1, ticks_per_round))))
        return f"{elapsed // 60}:{elapsed % 60:02d}"

    def fighter_presence_line(self, actor, defender, state):
        if state.get("actor_streak", 0) < 3 or self.fight_presentation_random() > 0.32:
            return ""
        position = state.get("position", "range")
        defender_key = self.fight_state_key(defender, state)
        if position in self.GROUND_POSITIONS:
            defender_on_top = state.get("top") == defender_key
            if defender_on_top:
                return self.fight_presentation_choice([
                    f"{defender.name} settles the hips in {position} and clears the nearest attacking grip.",
                    f"{defender.name} widens the base in {position}, refusing to be pulled into the next scramble.",
                    f"{defender.name} controls a wrist from the top of {position} and makes {actor.name} rebuild.",
                    f"{defender.name} keeps the shoulders square in {position} while watching for the next submission entry.",
                    f"{defender.name} stays patient on top in {position} and denies {actor.name} an easy angle.",
                ])
            return self.fight_presentation_choice([
                f"{defender.name} builds a frame from {position} and keeps the hips moving underneath.",
                f"{defender.name} hand-fights from {position}, protecting the neck before searching for space.",
                f"{defender.name} keeps an elbow-knee connection in {position} and denies the clean follow-up.",
                f"{defender.name} shifts the hips in {position}, forcing {actor.name} to adjust the pressure.",
                f"{defender.name} stays composed underneath in {position} and works toward the next escape layer.",
            ])
        if state["hurt"][defender_key] > defender.toughness * 0.55:
            return self.fight_presentation_choice([
                f"{defender.name} shells up, takes a breath, and tries to reset the range.",
                f"{defender.name} is hurt but keeps framing and looking for a way off the fence.",
                f"{defender.name} fires a short warning shot to stop {actor.name} from rushing in.",
            ])
        if state["gas"][defender_key] < 24:
            return self.fight_presentation_choice([
                f"{defender.name} is visibly tired and takes an extra second before resetting.",
                f"{defender.name}'s guard is sagging as the pace starts to bite.",
                f"{defender.name} circles away with heavy legs and tries to slow the fight down.",
            ])
        return self.fight_presentation_choice([
            f"{defender.name} answers with movement and makes {actor.name} start again.",
            f"{defender.name} shows a counter and keeps {actor.name} honest.",
            f"{defender.name} circles off the center line before the next exchange.",
        ])

    def resolve_fight_incident(self, actor, defender, state):
        """Resolve the rare foul path on the mechanics stream.

        Fouls can restore gas, so they are simulation events rather than flavour.
        Keeping them out of ``dynamic_flavor_line`` means changing commentary
        frequency or wording cannot alter a fighter's recovery.
        """
        if self.fight_mechanics_rng().random() > 0.12:
            return ""
        cap = state.get("gas_cap", {}).get(self.fight_state_key(defender, state), 100)
        gas_def = state["gas"][self.fight_state_key(defender, state)]
        pos = state["position"]
        if self.fight_mechanics_rng().random() < 0.06 and pos in ("range", "pocket", "clinch", "cage"):
            # Keep the calibrated five-entry draw. A range-level grounded knee
            # represents an illegal knee during a defended level change; a
            # fence grab represents the boundary reached during the exchange.
            # Both are legal incident descriptions without changing RNG shape.
            foul = self.fight_mechanics_rng().choice(["eye poke", "eye poke", "low blow", "fence grab", "grounded knee"])
            actor_key = self.fight_state_key(actor, state)
            prior_fouls = state.setdefault("fouls", {}).setdefault(actor_key, [])
            # Three recorded incidents is the bout-local cap. It prevents a
            # pathological RNG run from producing unlimited timeouts or points.
            if len(prior_fouls) >= 3:
                return ""
            deducted = len(prior_fouls) >= 2
            recovery_seconds = 300 if foul == "low blow" else 90 if foul == "eye poke" else 0
            foul_record = {
                "round": int(state.get("round", 1)), "tick": int(state.get("tick", 1)),
                "fighter": actor_key, "type": foul, "point_deducted": deducted,
                "warning_number": len(prior_fouls) + 1,
                "recovery_seconds": recovery_seconds,
                "referee": state.get("referee", "standard"),
                "accidental": True,
            }
            prior_fouls.append(foul_record)
            state["last_foul"] = foul_record
            if deducted:
                round_deductions = state.setdefault("point_deductions", {}).setdefault(actor_key, {})
                foul_round = foul_record["round"]
                round_deductions[foul_round] = round_deductions.get(foul_round, 0) + 1
            penalty_text = " The referee deducts one point after the repeated fouls." if deducted else ""
            if foul == "eye poke":
                state["gas"][self.fight_state_key(defender, state)] = min(cap, gas_def + 4)
                self.maybe_flag_technical_foul_stoppage(actor, defender, foul_record, state)
                return self.fight_presentation_choice([
                    f"Action stops - {actor.name} catches {defender.name} with a stray eye poke and the referee gives time to recover.",
                    f"{defender.name} turns away blinking after a finger to the eye; the referee calls a brief timeout.",
                ]) + penalty_text
            if foul == "low blow":
                state["gas"][self.fight_state_key(defender, state)] = min(cap, gas_def + 3)
                self.maybe_flag_technical_foul_stoppage(actor, defender, foul_record, state)
                return f"{defender.name} drops to a knee after a low blow and takes the full recovery time from the referee.{penalty_text}"
            if foul == "grounded knee":
                return f"The referee sternly warns {actor.name} about a knee to a grounded opponent.{penalty_text}"
            return f"The referee warns {actor.name} for grabbing the fence.{penalty_text}"
        return ""

    def referee_profile(self, state):
        """Return an explicit, rating-independent officiating profile."""
        name = str(state.get("referee") or "standard")
        profile = state.get("referee_profile")
        if isinstance(profile, dict) and profile.get("name") == name:
            return profile
        return {"name": name, **deepcopy(self.REFEREE_PROFILES.get(name, self.REFEREE_PROFILES["standard"]))}

    def maybe_flag_technical_foul_stoppage(self, actor, defender, foul_record, state):
        """Flag an accidental foul stoppage only when visible trauma prevents continuation."""
        defender_key = self.fight_state_key(defender, state)
        foul = foul_record["type"]
        cut = self.cut_medical_evidence(defender, state)
        head = state.get("head", {}).get(defender_key, 0)
        body = state.get("body", {}).get(defender_key, 0)
        cannot_continue = (
            foul == "eye poke" and cut["vision_risk"] and cut["max_severity"] >= 5 and head >= 55
        ) or (foul == "low blow" and body >= 60)
        if cannot_continue:
            state["technical_foul_stoppage"] = {
                "offender": self.fight_state_key(actor, state),
                "injured": defender_key,
                "foul": foul,
                "accidental": True,
                "round": int(state.get("round", 1)),
            }

    def technical_foul_outcome(self, actor, defender, state):
        """Apply the configured completed-round threshold to an accidental foul stop."""
        foul_stop = state.pop("technical_foul_stoppage", None)
        if not foul_stop:
            return None
        completed_rounds = max(0, int(state.get("round", 1)) - 1)
        max_rounds = int(state.get("max_rounds", 3))
        required_rounds = 3 if max_rounds >= 5 else 2
        injured = state.get("fighters", {}).get(foul_stop["injured"], defender)
        offender = state.get("fighters", {}).get(foul_stop["offender"], actor)
        evidence = {
            **foul_stop, "completed_rounds": completed_rounds,
            "required_rounds": required_rounds,
        }
        if completed_rounds < required_rounds:
            state["decision_verdict"] = "No Contest — accidental foul before the scorecard threshold"
            state["technical_outcome"] = {**evidence, "method": "No Contest"}
            detail = (
                f"{injured.name} cannot continue after the accidental {foul_stop['foul']}. "
                f"Only {completed_rounds} round(s) are complete; the bout is ruled a No Contest."
            )
            return injured, offender, "No Contest", detail
        decision = self.decision_from_judges(
            state["fighters"].get("a", actor), state["fighters"].get("b", defender), state,
        )
        if decision["winner"] is None:
            state["decision_verdict"] = f"Technical {decision['verdict']}"
            method = "Draw"
            winner, loser = injured, offender
        else:
            state["decision_verdict"] = f"Technical {decision['verdict']}"
            method = "Technical Decision"
            winner = decision["winner"]
            loser = state["fighters"]["b"] if winner is state["fighters"]["a"] else state["fighters"]["a"]
        state["technical_outcome"] = {**evidence, "method": method, "verdict": state["decision_verdict"]}
        detail = (
            f"{injured.name} cannot continue after the accidental {foul_stop['foul']}. "
            f"With {completed_rounds} completed rounds, the official scorecards decide the bout: "
            f"{state['decision_verdict']}."
        )
        return winner, loser, method, detail

    def dynamic_flavor_line(self, actor, defender, state, round_no):
        """Return an occasional presentation-only atmospheric beat."""
        if self.fight_presentation_random() > 0.12:
            return ""
        dmg_def = state["hurt"][self.fight_state_key(defender, state)]
        gas_act = state["gas"][self.fight_state_key(actor, state)]
        gas_def = state["gas"][self.fight_state_key(defender, state)]
        streak = state.get("actor_streak", 0)
        pos = state["position"]

        pool = []
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
                f"A tense feeling-out spell as both reset the range.",
                f"{actor.name} pumps a couple of feints, fishing for a reaction.",
                f"{actor.name} rolls the shoulders and resets, measuring the distance.",
                f"{actor.name} steps in and out of range, baiting a counter.",
                f"{actor.name} paws with the lead hand, hunting an opening.",
                f"A brief lull as {actor.name} circles and studies {defender.name}.",
                f"{actor.name} feints the level change, testing {defender.name}'s reactions.",
                f"{actor.name} bounces on the balls of the feet, changing rhythm.",
            ]
            switches = (state.get("stance_switches") or {}).get(self.fight_state_key(actor, state), [])
            if switches and int(switches[-1].get("round", 0)) == int(state.get("round", 0)) \
                    and int(switches[-1].get("tick", 0)) == int(state.get("tick", 0)):
                pool.append(
                    f"{actor.name} deliberately switches from {switches[-1].get('from')} to "
                    f"{switches[-1].get('to')}, hunting a fresh angle."
                )
        elif pos in ("clinch", "cage"):
            pool += [
                f"They grind against the fence, each looking for an underhook.",
                f"The referee watches the clinch closely, ready to break it if it stalls.",
                f"{actor.name} digs for double underhooks and turns {defender.name} along the cage.",
                f"Heads pressed together, they fight for wrist control in the tie-up.",
                f"{actor.name} thuds a knee up the middle of the clinch to stay busy.",
                f"A grinding clinch battle - neither wants to give up the position.",
            ]
        return self.fight_presentation_choice(pool) if pool else ""

    def initiative(self, fighter, opponent, state):
        aggression = (self.ds(fighter, "aggression", 50) - 50) * 0.09
        pressure = 8 if fighter.behaviour in ("Pressure", "Volume", "Dynamic Attacker") else 0
        caution = -7 if fighter.behaviour == "Cautious" else 0
        freshness = state["gas"][self.fight_state_key(fighter, state)] * 0.17 - state["hurt"][self.fight_state_key(fighter, state)] * 0.18
        mental = self.skill_bundle(fighter, "mental") * 0.13 + self.ds(fighter, "confidence", 50) * 0.07
        mobility = (self.ds(fighter, "mobility", 50) + self.ds(fighter, "reflexes", 50)) * 0.04
        context = self.context_edge(fighter, state, "home", "prime", "experience", "pressure", "rivalry", "stance", "style", "morale")
        night_form = state.get("night_form", {}).get(self.fight_state_key(fighter, state), 0)
        plan_row = self.fight_plan_for(fighter, state)
        plan_bonus = {
            "Pressure and volume": 4.0, "Wrestle early": 2.2,
            "Cage grind": 2.0, "Conserve energy": -2.4,
            "Protect a lead": -2.0, "Chase a finish": 4.8,
        }.get(plan_row["current"], 0.0) * plan_row["execution"]
        window = state.get("counter_window") or {}
        if plan_row["current"] == "Counter striking" and window.get("fighter") == self.fight_state_key(fighter, state):
            plan_bonus += 5.0 * plan_row["execution"]
        return freshness + mental + mobility + aggression + fighter.momentum * 0.95 + night_form * 0.78 + fighter.camp_boost * 1.3 - fighter.weight_cut_penalty * 0.9 - getattr(fighter, "division_size_penalty", 0) * 0.55 + pressure + caution + context + plan_bonus + self.fight_mechanics_rng().randint(-10, 10)

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
        phase_profiles = self.STYLE_BIAS.get(phase, {})
        for index, style in enumerate(self.fighter_styles(fighter)):
            profile = phase_profiles.get(style)
            if not profile:
                continue
            influence = 1.0 if index == 0 else 0.35
            for action, mult in profile.items():
                if action in weights:
                    weights[action] *= 1 + (mult - 1) * influence
        return weights

    def choose_action(self, fighter, opponent, state, round_no, tick):
        position = state["position"]
        gas = state["gas"][self.fight_state_key(fighter, state)]
        tired = gas < 42
        exhausted = gas < 22
        hurt = state["hurt"][self.fight_state_key(fighter, state)] > fighter.toughness * 0.65
        mental = self.skill_bundle(fighter, "mental")
        aggression = self.ds(fighter, "aggression", 50)
        if gas < 8 and self.fight_mechanics_rng().random() < 0.62:
            return "survive"
        if exhausted and self.fight_mechanics_rng().random() < 0.22 + max(0, 35 - gas) / 90:
            return "survive"
        if hurt and fighter.recovery + mental + self.ds(fighter, "stun_recovery", fighter.recovery) + self.fight_mechanics_rng().randint(-35, 25) > 185:
            return "survive"
        fighter_key = self.fight_state_key(fighter, state)
        controller = state.get("clinch_controller")
        if position == "failed shot":
            if controller == fighter_key:
                return self.weighted_choice({
                    "front_headlock": self.ds_avg(fighter, ("sprawl", "front_headlock", "clinch_control"), fighter.wrestling),
                    "force_cage": self.ds_avg(fighter, ("cage_wrestling", "clinch_control", "strength"), fighter.wrestling),
                    "disengage": self.ds_avg(fighter, ("discipline", "footwork", "fight_iq"), fighter.fight_iq),
                })
            return self.weighted_choice({
                "re_shot": self.ds_avg(fighter, ("chain_wrestling", "takedown_speed", "conditioning"), fighter.wrestling),
                "recover_shot": self.ds_avg(fighter, ("get_ups", "scrambles", "clinch_defence"), fighter.takedown_defence),
            })
        if position == "standing back control":
            if controller == fighter_key:
                return self.weighted_choice({
                    "mat_return": self.ds_avg(fighter, ("cage_wrestling", "throws", "back_control", "strength"), fighter.wrestling),
                    "dirty_boxing": self.ds_avg(fighter, ("dirty_boxing", "knees", "clinch_control"), fighter.striking),
                    "standing_back_ride": self.ds_avg(fighter, ("back_control", "ride_control", "cage_pressure"), fighter.ground_control),
                })
            return self.weighted_choice({
                "standing_escape": self.ds_avg(fighter, ("clinch_defence", "scrambles", "balance"), fighter.takedown_defence),
                "recover_shot": self.ds_avg(fighter, ("get_ups", "cage_wrestling", "strength"), fighter.wrestling),
            })
        if position == "front headlock":
            if state.get("top") == fighter_key:
                return self.weighted_choice({
                    "front_headlock_submission": self.ds_avg(fighter, ("submission_attack", "front_headlock", "killer_instinct"), fighter.submissions),
                    "take_back": self.ds_avg(fighter, ("back_control", "transitions", "scrambles"), fighter.grappling),
                    "turtle_ride": self.ds_avg(fighter, ("ride_control", "top_control", "positional_ability"), fighter.ground_control),
                })
            return self.weighted_choice({
                "front_headlock_escape": self.ds_avg(fighter, ("submission_defence_detail", "scrambles", "guard_work"), fighter.submission_defence),
                "recover_guard": self.skill_bundle(fighter, "bottom_game"),
            })
        if position == "turtle":
            if state.get("top") == fighter_key:
                return self.weighted_choice({
                    "take_back": self.ds_avg(fighter, ("back_control", "ride_control", "transitions"), fighter.grappling),
                    "ground_strikes": self.ds_avg(fighter, ("ground_striking", "ride_control", "elbows"), fighter.ground_control),
                    "turtle_ride": self.ds_avg(fighter, ("ride_control", "top_control", "cage_wrestling"), fighter.ground_control),
                })
            return self.weighted_choice({
                "turtle_escape": self.ds_avg(fighter, ("scrambles", "get_ups", "guard_work"), fighter.grappling),
                "recover_guard": self.skill_bundle(fighter, "bottom_game"),
                "stand_up": self.ds_avg(fighter, ("get_ups", "scrambles", "conditioning"), fighter.takedown_defence),
            })
        if position == "leg entanglement":
            if state.get("top") == fighter_key:
                return self.weighted_choice({
                    "leg_attack": self.ds_avg(fighter, ("leg_locks", "submission_attack", "positional_ability"), fighter.submissions),
                    "leg_control": self.ds_avg(fighter, ("leg_locks", "top_control", "discipline"), fighter.grappling),
                    "disengage_leg": self.ds_avg(fighter, ("discipline", "scrambles", "get_ups"), fighter.fight_iq),
                })
            return self.weighted_choice({
                "leg_escape": self.ds_avg(fighter, ("submission_defence_detail", "scrambles", "flexibility"), fighter.submission_defence),
                "counter_leg_lock": self.ds_avg(fighter, ("leg_locks", "scrambles", "submission_attack"), fighter.submissions),
            })
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
            self.apply_fight_plan_weights(fighter, opponent, state, "range", weights, round_no)
            return self.weighted_choice(weights)
        if position in ("clinch", "cage"):
            weights = {
                "dirty_boxing": self.skill_bundle(fighter, "clinch_attack") + self.ds(fighter, "dirty_boxing", fighter.striking) * 0.45,
                "takedown": self.ds_avg(fighter, ("clinch_takedowns", "throws", "chain_wrestling", "strength"), fighter.wrestling),
                "cage_control": self.ds_avg(fighter, ("cage_pressure", "clinch_control", "cage_wrestling", "strength"), fighter.wrestling),
                "break_clinch": self.skill_bundle(fighter, "clinch_defence") + mental * 0.25,
            }
            if state.get("clinch_controller") == self.fight_state_key(fighter, state):
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
            self.apply_fight_plan_weights(fighter, opponent, state, "clinch", weights, round_no)
            return self.weighted_choice(weights)
        if state["top"] == self.fight_state_key(fighter, state):
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
            self.apply_fight_plan_weights(fighter, opponent, state, "top", weights, round_no)
            return self.weighted_choice(weights)
        weights = {
            "recover_guard": self.ds_avg(fighter, ("guard_work", "bottom_control", "flexibility", "submission_defence_detail"), fighter.grappling),
            "sweep": self.ds_avg(fighter, ("scrambles", "bottom_control", "transitions", "strength"), fighter.grappling),
            "bottom_submission": self.ds_avg(fighter, ("submission_attack", "guard_work", "leg_locks", "confidence"), fighter.submissions) * (1.28 if fighter.behaviour == "Submission Hunter" else 0.78),
            "cling": mental + self.ds(fighter, "resilience", fighter.toughness) + (20 if tired else 0),
            "stand_up": self.ds_avg(fighter, ("get_ups", "scrambles", "sprawl", "conditioning"), fighter.takedown_defence),
        }
        self.apply_style_bias(fighter, weights, "bottom")
        self.apply_fight_plan_weights(fighter, opponent, state, "bottom", weights, round_no)
        return self.weighted_choice(weights)

    def weighted_choice(self, weights):
        cleaned = {key: max(1, int(value)) for key, value in weights.items()}
        total = sum(cleaned.values())
        pick = self.fight_mechanics_rng().randint(1, total)
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
                "{A} shows a stance feint while {B} hovers at boxing range.",
            ],
            "jab_land": [
                "{A} snaps {B}'s head back with a stiff jab.",
                "{A} lands a clean one-two and exits before {B} can answer.",
                "{A} splits the guard with a straight punch.",
                "{A} doubles the jab and disrupts {B}'s stance.",
                "{A} lands a long straight at maximum range.",
                "{A} spears a body jab under {B}'s elbows and exits.",
                "{A} paws with the lead hand, then drives the rear cross through the guard.",
                "{A} lands a triple jab while stepping {B} toward the fence.",
                "{A} scores with a check hook as {B} tries to close distance.",
            ],
            "jab_miss": [
                "{A}'s jab falls short as {B} shifts backward.",
                "{B} parries the jab and keeps the range.",
                "{A} reaches with the jab and is left out of position.",
                "{B} slips outside the straight punch.",
                "{B} catches the body jab on an elbow and pivots away.",
                "{A}'s one-two skims the guard as {B} rolls with it.",
                "{B} leans away from the check hook and resets.",
            ],
            "power_land": [
                "{A} lands a heavy hook that turns {B}'s head.",
                "{A} catches {B} with a loaded overhand.",
                "{A} steps in with a powerful straight right.",
                "{A} lands an uppercut through the middle.",
                "{A} catches {B} cleanly with a compact hook.",
                "{A} digs a shovel hook beneath {B}'s right elbow.",
                "{A} steps across with a corkscrew cross that splits the guard.",
                "{A} loops the rear hand over {B}'s jab.",
                "{A} plants and lands a lead hook-rear uppercut combination.",
                "{A} shifts stance through a body hook and brings the right hand upstairs.",
            ],
            "power_miss": [
                "{A} loads up and misses wide.",
                "{B} rolls beneath the return punch.",
                "{A}'s overhand sails over {B}'s shoulder.",
                "{B} blocks the power shot on the forearms.",
                "{B} steps outside the shovel hook and makes {A} reset.",
                "{A}'s rear uppercut brushes past as {B} pulls away.",
                "{B} ducks beneath the looping rear hand.",
                "{A} tries a check hook, but {B} stops short of the target.",
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
            "teep_land": [
                "{A} drives a lead teep into {B}'s midsection and takes the range back.",
                "{A} stabs a rear teep into the body as {B} steps forward.",
                "{A} feints high and pushes {B} back with a teep to the hip.",
                "{A} posts {B} at the end of a long teep and circles off.",
                "{A} catches {B}'s advance with a teep beneath the sternum.",
                "{A} uses a quick double teep to break {B}'s rhythm.",
            ],
            "teep_miss": [
                "{B} parries the teep aside and keeps advancing.",
                "{A}'s teep slides past the hip as {B} steps off line.",
                "{B} catches the push kick on the forearm and resets the range.",
                "{A} lifts for the teep, but {B} is already outside its reach.",
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
                "{A} traps {B} in the {technique} and forces the tap.",
                "{A} connects the {technique} submission chain and {B} has to tap.",
                "{A} cinches the {technique} before {B} can escape.",
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
                "{A} times the entry with a short hook and {B} folds on contact.",
                "{A} splits the guard with a cross and {B} drops face-first.",
                "{A} lands a pull counter that freezes {B} in place before the fall.",
                "{A} crashes a right over the top and {B}'s legs disappear.",
                "{A} clips {B} behind the ear and the balance is gone instantly.",
                "{A} lands a shovel uppercut and {B} crumples at the fence.",
                "{A} counters the kick with a straight shot and {B} is out.",
                "{A} steps in with a left hand that ends the night immediately.",
                "{A} finds the temple with a looping punch and {B} collapses sideways.",
                "{A} lands a clean counter hook and {B} goes down unconscious.",
                "{A} sits down on the overhand and {B} cannot absorb it.",
                "{A} catches {B} ducking with an uppercut and the fight is over.",
                "{A} lands a check hook as {B} rushes in and {B} falls hard.",
                "{A} hides the right hand behind a feint and knocks {B} cold.",
                "{A} lands a short left on the break and {B} drops immediately.",
            ],
            "walkoff_ko": [
                "{A} lands cleanly and walks away before {B} hits the canvas.",
                "{A} knows the fight is over and turns away after the punch lands.",
                "{A} drops {B} with a single shot and refuses to throw an unnecessary follow-up.",
                "{A} lands the counter, points to the canvas, and lets the referee arrive.",
                "{A} freezes {B} with one punch and calmly steps aside.",
                "{A} sees {B} go stiff and raises a hand before the referee moves in.",
                "{A} lands once, recognises the finish, and backs away.",
                "{A} sends {B} down with a clean shot and does not chase the damage.",
                "{A} turns to celebrate as {B} collapses behind them.",
                "{A} walks off after a perfect counter leaves {B} unable to continue.",
                "{A} lands the final shot so cleanly that no follow-up is needed.",
            ],
            "head_kick_ko": [
                "{A} lands a clean head kick and {B} collapses instantly.",
                "{A}'s shin wraps around the guard and knocks {B} unconscious.",
                "{A} lands a question-mark kick that completely surprises {B}.",
                "{A} whips a high round kick over the shoulder and {B} is out.",
                "{A} hides the head kick behind the jab and {B} never sees it.",
                "{A} lands a switch kick upstairs and {B} falls backward.",
                "{A} cracks {B} with a wheel kick and the arena gasps.",
                "{A} lands a jumping switch kick flush and {B} collapses.",
                "{A} turns the corner with a Brazilian kick and {B} drops.",
                "{A} times the level change with a knee to the head and {B} is done.",
                "{A} lands a shin across the jaw and {B} goes limp.",
                "{A} fires the high kick off the lead leg and ends it immediately.",
                "{A} catches {B} leaning with a head kick that lands perfectly.",
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
                "{A} pins {B} on the cage and pours on straight punches until the referee steps in.",
                "{A} hurts {B} with an uppercut and swarms before {B} can recover.",
                "{A} stacks punches in bunches as {B} stops firing back.",
                "{A} batters {B} from the clinch until the defence disappears.",
                "{A} follows a knockdown with measured punches and the referee has seen enough.",
                "{A} keeps {B} trapped on a knee and lands unanswered shots.",
                "{A} overwhelms {B} with hooks along the fence until the stoppage arrives.",
                "{A} breaks {B}'s guard with elbows and punches in close.",
                "{A} pours on volume while {B} covers up without moving.",
                "{A} lands a knee, then a flurry, and {B} cannot answer.",
                "{A} forces {B} to turn away under a sustained combination.",
                "{A} keeps resetting the angle and landing while {B} only shells.",
                "{A} traps {B} in the pocket and lands until the referee intervenes.",
                "{A} strings together elbows and short punches as {B} wilts.",
                "{A} hurts {B} to the body and finishes with unanswered shots upstairs.",
            ],
            "ground_tko": [
                "{A} postures up and lands repeated clean punches.",
                "{A} traps one wrist and strikes until {B} stops improving position.",
                "{A} secures dominant control and rains down unanswered shots.",
                "{A} flattens {B} out and lands punches until the referee moves in.",
                "{A} rides the hips and keeps landing as {B} covers up.",
                "{A} pins an arm with the knee and hammers away from top position.",
                "{A} stacks {B} against the fence and lands short unanswered punches.",
                "{A} moves to mount and unloads until {B} can no longer defend.",
                "{A} traps {B}'s wrist and lands elbows through the guard.",
                "{A} keeps chest pressure heavy and chips away until the stoppage.",
                "{A} opens a cut with ground elbows and forces the referee's decision.",
                "{A} controls the back and lands punches until {B} stops moving.",
                "{A} postures from half guard and lands a steady drumbeat of shots.",
                "{A} pins {B}'s shoulders and lands clean hammerfists.",
                "{A} keeps the head posted and lands unanswered right hands.",
                "{A} advances to a crucifix and the referee cannot let it continue.",
                "{A} unloads from back mount while {B} is flattened out.",
                "{A} breaks the guard posture and lands elbows until the fight is waved off.",
            ],
            "doctor": [
                "the doctor checks {B}'s facial damage and waves the fight off.",
                "{B}'s cut is too severe and the doctor stops the fight.",
                "the swelling prevents {B} from seeing clearly and the doctor calls it.",
                "the cageside doctor studies the cut, asks {B} to track a finger, and stops the bout.",
                "{B}'s eye is closing fast and the doctor will not allow another round.",
                "the cut over {B}'s eyebrow is pouring blood and the doctor waves it off.",
                "the doctor decides {B} cannot safely defend with the swelling worsening.",
                "{B}'s vision is compromised and the medical inspection ends the contest.",
            ],
            "corner_stoppage": [
                "{B}'s corner refuses to send them out for the next round.",
                "{B}'s corner waves off the fight after the accumulated damage.",
                "the corner has seen enough and tells the referee {B} cannot continue.",
                "{B}'s coaches step onto the apron and stop the damage from continuing.",
                "the towel comes in from {B}'s corner after a brutal round.",
                "{B}'s head coach calls it before the next round can begin.",
                "the corner tells the inspector that {B} is finished for the night.",
                "{B}'s team chooses protection over pride and ends the fight.",
            ],
            "injury_stoppage": [
                "{B} cannot place weight on the damaged leg and the fight is stopped.",
                "{B} signals that they cannot continue after the leg damage.",
                "{B}'s body gives out under the accumulated punishment.",
                "{B} turns away after another body shot and the referee stops it.",
                "{B} drops from the leg damage and cannot stand cleanly.",
                "{B} clutches the ribs and cannot answer the referee's command.",
                "{B}'s knee buckles again and the official waves the bout off.",
                "{B} tries to reset, but the damaged leg will not hold.",
            ],
            "body_kick_knockdown": [
                "{A} folds {B} with a body kick and sends them to the canvas.",
                "{A}'s kick lands under the ribs and drops {B} in pain.",
                "{B} crumples after {A}'s body kick lands cleanly.",
            ],
            "leg_kick_knockdown": [
                "{A} chops the damaged leg and knocks {B} off their feet.",
                "{B}'s base gives way after another clean leg kick from {A}.",
                "{A} lands to the leg and {B} collapses as the balance disappears.",
            ],
            "fatigue_tko": [
                "{B} is exhausted and no longer defending intelligently.",
                "{B} fades badly under the pressure and the referee steps in.",
                "{B} is too tired to protect themselves and the stoppage comes.",
                "{B} wilts in place while {A} keeps landing unanswered shots.",
                "{B}'s reactions are gone and the referee saves them from more damage.",
                "{B} cannot get off the fence and the accumulation forces the stoppage.",
                "{B} is running on fumes and absorbs too many clean punches.",
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
        extra_templates = self.mma_striking_commentary_expansion().get(category, ())
        if extra_templates:
            templates.setdefault(category, []).extend(extra_templates)
        template = self.fight_presentation_choice(templates.get(category, ["{A} continues to work against {B}."]))
        display_name = getattr(self, "fighter_display_name", lambda fighter: fighter.name)
        return template.format(A=display_name(actor), B=display_name(defender), **context)

    def mma_striking_commentary_expansion(self):
        """Additional reachable striking situations for the live MMA broadcast."""
        cached = getattr(self, "_mma_striking_commentary_cache", None)
        if cached is not None:
            return cached
        expanded = {
            "round_start": [
                "{A} probes with the lead hand while {B} keeps changing the target picture.",
                "{A} takes the outside angle and {B} answers by claiming the centre.",
                "both fighters show level-change feints before either commits to a strike.",
                "{A} pressures behind a long guard while {B} looks ready to counter.",
                "{B} paws at range and {A} tests the reactions with a quick stance switch.",
                "the corners call for patience as {A} and {B} begin hand-fighting at range.",
                "{A} edges toward the fence-cutting angle; {B} refuses to stand still.",
                "a tense opening exchange of feints, shoulder rolls and half-steps develops.",
            ],
            "jab_land": [
                "{A} stabs the jab into {B}'s chest and takes the angle outside.",
                "{A} touches the body, then brings the jab back upstairs.",
                "{A} intercepts {B}'s forward step with a sharp lead hand.",
                "{A} paws the guard open and threads the jab through the gap.",
                "{A} triples the jab, forcing {B} to retreat behind the guard.",
                "{A} feints the level change and lands the jab over {B}'s lowered hands.",
                "{A} lands the jab while circling away from {B}'s power side.",
                "{A} uses a body jab to freeze {B}, then scores cleanly to the head.",
                "{A} catches {B} resetting with a straight lead hand.",
                "{A} steps off line after the jab and denies {B} the return.",
            ],
            "jab_miss": [
                "{B} catches the jab on the rear glove and stays in position to answer.",
                "{B} pulls just beyond the jab and makes {A} reach.",
                "{B} bats the lead hand down before it reaches the target.",
                "{A} tries to jab on the entry, but {B} pivots off the centre line.",
                "{B} rolls the shoulder and lets the straight punch skim past.",
                "{A} shows the body jab; {B} reads it and withdraws the target.",
                "{B} changes stance mid-entry and the jab loses its lane.",
                "{A}'s double jab meets a disciplined high guard.",
            ],
            "power_land": [
                "{A} slips outside and fires a clean cross down the middle.",
                "{A} digs a hook to the body before bringing the next punch upstairs.",
                "{A} lands a shovel hook under {B}'s elbow at close range.",
                "{A} catches {B} exiting with a tight lead hook.",
                "{A} steps through with a rear uppercut as {B} changes levels.",
                "{A} uses the jab to hide an overhand that lands behind the ear.",
                "{A} lands a pull counter and is gone before {B} can reload.",
                "{A} shifts stance through the combination and finishes with the cross.",
                "{A} frames with the lead hand and drives a short right into the pocket.",
                "{A} feints to the body and whips the hook around {B}'s guard.",
                "{A} lands a compact three-punch sequence without falling out of stance.",
                "{A} pins {B}'s lead glove and punches through the exposed centre.",
            ],
            "power_miss": [
                "{B} leans outside the hook and watches it pass.",
                "{A} throws the cross, but {B} pivots beyond the rear shoulder.",
                "{B} catches the power shot across both forearms.",
                "{A} tries the uppercut and {B} crowds it before it can extend.",
                "{B} pulls away from the overhand and returns to a safe stance.",
                "{A}'s body hook is smothered by {B}'s elbow.",
                "{B} shells through the combination and slips out after the final punch.",
                "{A} commits to the counter, but {B} never gives the expected opening.",
            ],
            "dirty_boxing_land": [
                "{A} controls the biceps and lands two short punches inside.",
                "{A} frames on the collarbone and clips {B} with an elbow.",
                "{A} pulls the head into a knee before {B} can pummel free.",
                "{A} punches on the break and catches {B} before the guard resets.",
                "{A} digs a hook to the body from the collar tie.",
                "{A} wins head position and sneaks an uppercut through the clinch.",
                "{A} pins one wrist and works short punches with the free hand.",
                "{A} turns {B} toward the fence and lands an elbow over the top.",
            ],
            "dirty_boxing_miss": [
                "{B} wins the inside frame and smothers {A}'s short punches.",
                "{A} looks for the elbow, but {B} pummels underneath and removes the lane.",
                "{B} turns the hips away from the knee and forces a clean reset.",
                "{A} punches on the break; {B} is already outside the pocket.",
                "{B} keeps forehead position and denies {A} room for the uppercut.",
                "{A} tries to work inside, but {B} ties up both wrists.",
            ],
            "ground_strikes_land": [
                "{A} pins an arm and lands a clean elbow from top position.",
                "{A} postures just enough to drive a straight punch through the guard.",
                "{A} uses shoulder pressure to open space for short punches.",
                "{A} lands to the body, then brings an elbow back to the head.",
                "{A} follows the hip escape and keeps scoring with compact shots.",
                "{A} traps {B} against the fence and lands measured ground strikes.",
                "{A} floats with the movement and punches during the transition.",
                "{A} keeps the base wide and lands without surrendering control.",
            ],
            "ground_strikes_miss": [
                "{B} controls the wrists and prevents {A} from posturing to strike.",
                "{A} tries to create punching room, but {B} closes the distance from bottom.",
                "{B} frames at the hips and makes {A}'s elbow miss the target.",
                "{A} postures for ground-and-pound; {B} uses the opening to move.",
                "{B} keeps an active guard and blocks the short punches.",
                "{A} swings from top, but {B} rolls with the shot and stays responsible.",
            ],
            "low_kick_land": [
                "{A} times the weight transfer and kicks through {B}'s lead thigh.",
                "{A} finishes the punching exchange with an outside low kick.",
                "{A} chops the inside leg as {B} settles into stance.",
                "{A} hides the calf kick behind a level-change feint.",
                "{A} steps deep and turns the shin over into the thigh.",
                "{A} catches {B} circling with a kick to the trailing leg.",
                "{A} kicks the base and exits before {B} can plant to counter.",
                "{A} doubles up on the low line after drawing the guard high.",
            ],
            "leg_kick_hurt": [
                "{A} lands another low kick and {B} immediately changes stance.",
                "{B}'s lead leg buckles as {A} drives through another calf kick.",
                "{A} attacks the damaged leg; {B} can no longer hide the reaction.",
                "{B} tries to check, but the compromised base gives way under {A}'s kick.",
                "{A} finds the thigh again and {B}'s lateral movement visibly slows.",
                "{A} pounds the lead leg, forcing {B} to square up uncomfortably.",
            ],
            "body_kick_land": [
                "{A} wraps the shin around {B}'s elbow and into the ribs.",
                "{A} draws the guard high before turning over a kick to the body.",
                "{A} lands the open-side body kick and exits on an angle.",
                "{A} switches smoothly and drives the rear kick into the midsection.",
                "{A} catches {B} breathing with a thudding kick beneath the elbow.",
                "{A} feints low and lands the body kick across the far side.",
                "{A} punches into the kick and makes {B} absorb the full shin.",
                "{A} lands to the body without losing balance or position.",
            ],
            "body_kick_hurt": [
                "{A} slams another kick into the body and {B} folds around the impact.",
                "{B}'s elbow is dropping now; {A} finds the damaged ribs again.",
                "{A} lands flush to the body and {B} retreats with a guarded breath.",
                "{A} attacks the accumulated body damage and forces {B} to shell low.",
                "{B} winces as {A}'s shin lands across the same tender side.",
                "{A} drives the kick through the midsection and takes away more of {B}'s gas.",
            ],
            "high_kick_land": [
                "{A} uses the cross to hide a high kick around {B}'s rear glove.",
                "{A} shows the body kick before whipping the shin upstairs.",
                "{A} steps outside and lands the open-side kick to the head.",
                "{A} changes rhythm, then fires the high kick without a tell.",
                "{A} arcs the kick over {B}'s lowered lead hand.",
                "{A} catches {B} circling toward the power kick.",
                "{A} lands the high kick at the end of a punching combination.",
                "{A} raises the knee late and turns a body read into a head kick.",
            ],
            "kick_miss": [
                "{B} leans beyond the kick and lets {A} spin back to stance.",
                "{A} fires to the body, but {B} slides outside the arc.",
                "{B} withdraws the leg and makes the low kick fall short.",
                "{A} tries the open-side kick; {B} has already changed the angle.",
                "{B} steps inside the kick before {A} can extend it.",
                "{A} shows the high kick, but {B} reads the hip turn early.",
            ],
            "kick_checked": [
                "{B} turns the shin out and checks {A}'s low kick cleanly.",
                "{A} kicks the leg, but {B}'s check meets it shin-to-shin.",
                "{B} braces behind the forearms and blocks the body kick.",
                "{B} raises a tight double guard and absorbs the high kick safely.",
                "{A} attacks the base; {B} checks and stays balanced.",
                "{B} reads the kick and takes the impact on a disciplined block.",
            ],
            "low_kick_checked": [
                "{B} turns the shin outward and checks {A}'s low kick cleanly.",
                "{A} attacks the thigh, but {B} meets the kick shin-to-shin.",
                "{B} lifts the lead leg in time and takes the force out of the low kick.",
                "{A} kicks the base; {B}'s check is already waiting.",
                "{B} reads the hip turn and checks before {A} can kick through the target.",
                "{A}'s calf kick lands on the point of {B}'s raised shin.",
            ],
            "body_kick_checked": [
                "{B} braces the elbow and forearm together to block {A}'s body kick.",
                "{A} turns the kick toward the ribs, but {B} catches it on a tight frame.",
                "{B} slides back and takes the body kick across both forearms.",
                "{A}'s shin reaches the midsection, but {B}'s elbow absorbs the scoring impact.",
                "{B} reads the body kick and closes the guard before it lands cleanly.",
                "{A} kicks beneath the punches; {B} braces and stays balanced.",
            ],
            "high_kick_checked": [
                "{B} raises a tight double guard and blocks {A}'s high kick.",
                "{A} sends the shin upstairs, but {B} gets both gloves to the impact.",
                "{B} leans away while the forearm takes the edge off {A}'s head kick.",
                "{A}'s high kick wraps around the guard without reaching the head cleanly.",
                "{B} sees the kick rise and builds a solid wall around the temple.",
                "{A} tries to finish the combination high; {B}'s guard is in position.",
            ],
            "knockdown": [
                "{A} lands {technique}; {B}'s balance disappears and they fall to the canvas!",
                "{B} tries to recover stance, but {A}'s {technique} sends them down!",
                "{A} catches the entry with {technique} and puts {B} on the floor!",
                "{A}'s {technique} lands at the end of the exchange—{B} is dropped!",
                "{B}'s legs give way after {A} connects with {technique}!",
                "{A} times {technique} perfectly and {B} crashes backward!",
                "A sudden {technique} from {A} drops {B} in the centre!",
                "{A} finds the opening for {technique}; {B} hits the mat hard!",
            ],
            "cut": [
                "{A}'s strike opens a cut along {B}'s eyebrow.",
                "A clean shot from {A} splits the skin beneath {B}'s eye.",
                "{B} wipes at fresh blood after {A}'s strike finds the brow.",
                "{A} lands through the guard and a cut starts to open on {B}.",
                "The impact from {A} leaves visible damage across {B}'s cheek.",
                "{B}'s corner takes notice as {A} opens a cut near the eye.",
            ],
            "survive": [
                "{A} circles away, resets the feet and buys a few seconds to recover.",
                "{A} frames into the clinch and slows {B}'s follow-up attack.",
                "{A} keeps the guard tight and moves laterally out of immediate danger.",
                "{A} fires a short counter to make {B} hesitate before swarming.",
                "{A} changes levels defensively and forces {B} to respect the takedown threat.",
                "{A} breathes behind the high guard and refuses to stay on the fence.",
                "{A} ties up a wrist and uses the lull to recover composure.",
                "{A} retreats in good stance, giving {B} no clean finishing lane.",
            ],
            "standing_tko": [
                "{A} cuts off both exits and lands a sustained unanswered flurry.",
                "{B} is trapped behind the guard as {A} keeps finding clean shots.",
                "{A} attacks head and body until {B} can no longer return fire.",
                "{A} stays measured during the barrage and forces the referee closer.",
                "{B} tries to circle free, but {A} steps across every escape route.",
                "{A} pours on accurate punches while {B} remains stuck on the fence.",
            ],
        }
        deeper_pool = {
            "round_start": [
                "{A} bounces lightly at range while {B} watches the hips for the first real tell.",
                "{A} opens with shoulder feints; {B} answers by showing a level change.",
                "the first exchange is all reads, hand traps and tiny stance adjustments.",
                "{A} takes a half-step inside, then backs out as {B} loads the counter.",
                "{B} tests the outside foot position while {A} keeps the lead hand busy.",
                "{A} circles toward open space and {B} tries to herd them back to the fence.",
                "both fighters are disciplined early, neither giving the other a free entry.",
                "{A} changes rhythm twice before {B} finally gives a reaction.",
                "{B} flashes a low kick feint and {A} immediately squares the stance.",
                "{A} claims the centre, but {B} is already drawing out the first attack.",
            ],
            "jab_land": [
                "{A} lands a jab to the collarbone and uses it to steer {B} backward.",
                "{A} touches the body with the jab, then exits before {B} can counter.",
                "{A} flicks a jab over {B}'s lead shoulder and keeps the feet underneath.",
                "{A} jabs while circling and never lets {B} set the rear hand.",
                "{A} doubles up on the jab and forces {B} to reset the guard.",
                "{A} uses a pawing jab to blind {B}, then snaps the next one clean.",
                "{A} meets {B}'s entry with a stiff jab that stops the advance.",
                "{A} lands the jab at the end of {B}'s breath and makes it count.",
                "{A} jabs to the chest and turns {B} before the return can come.",
                "{A} spears the lead hand through the centre as {B} changes stance.",
            ],
            "jab_miss": [
                "{B} hand-fights the jab away and refuses to give up the centre line.",
                "{A} reaches for the jab, but {B}'s footwork has already moved the target.",
                "{B} dips under the second jab and comes up in counter range.",
                "{A} tries to frame behind the jab; {B} peels it off cleanly.",
                "{B} shoulder-rolls the jab and keeps the counter hidden.",
                "{A}'s jab touches glove but cannot break {B}'s guard structure.",
                "{B} parries down and steps outside before {A} can double up.",
                "{A} jabs to the body, but {B} withdraws the hips in time.",
            ],
            "power_land": [
                "{A} lands the rear hand after freezing {B} with a level feint.",
                "{A} catches {B} leaning with a short hook over the lead side.",
                "{A} digs the body, then comes upstairs with a compact cross.",
                "{A} throws in combination and the final hook catches {B} clean.",
                "{A} sneaks an uppercut between {B}'s elbows in the pocket.",
                "{A} steps off line and rips a punch across {B}'s guard.",
                "{A} finds the counter right as {B} exits with hands low.",
                "{A} loads the body hook and makes {B} respect the inside lane.",
                "{A} lands a short punch while {B} is still turning out.",
                "{A} threads the cross behind the jab and snaps {B}'s head back.",
                "{A} draws the parry and loops the hook around it.",
                "{A} punches through the clinch entry before {B} can tie up.",
            ],
            "power_miss": [
                "{B} reads the loading shoulder and exits before the overhand arrives.",
                "{A} throws hard to the body, but {B} folds the elbow across it.",
                "{B} ducks under the hook and makes {A} spin out of stance.",
                "{A} tries to split the guard; {B} closes the door with both gloves.",
                "{B} slides outside the rear hand and keeps the counter chambered.",
                "{A} overcommits on the hook and {B} is gone before impact.",
                "{B} smothers the uppercut by stepping chest-to-chest.",
                "{A}'s counter is a beat late as {B} resets safely.",
            ],
            "dirty_boxing_land": [
                "{A} bumps with the shoulder and lands a right hand over the top.",
                "{A} controls one wrist and chips in two short punches.",
                "{A} sneaks a knee through the middle as {B} fights for inside position.",
                "{A} frames under the chin and lands the elbow on the break.",
                "{A} turns {B}'s back toward the fence and scores with compact hooks.",
                "{A} punches off the collar tie before {B} can pummel back inside.",
                "{A} lands a short right, then digs a body shot in the clinch.",
                "{A} uses head position to keep {B} still for the uppercut.",
            ],
            "dirty_boxing_miss": [
                "{B} clamps down on the biceps and stops {A}'s inside punches.",
                "{A} looks for the elbow, but {B} wins the head position first.",
                "{B} turns off the fence before {A} can work the dirty boxing.",
                "{A} tries to knee through the clinch, but {B} blocks with the thigh.",
                "{B} pummels inside and takes away {A}'s punching arm.",
                "{A} punches on the exit, but {B} slips under and resets.",
            ],
            "ground_strikes_land": [
                "{A} rides the hip escape and drops an elbow as {B} turns.",
                "{A} pins the wrist and lands a clean right from half guard.",
                "{A} postures only briefly, but the punch gets through clean.",
                "{A} mixes body shots with short elbows to make {B} open up.",
                "{A} keeps the knee heavy across the thigh and lands from top.",
                "{A} punishes the guard recovery with a compact hammerfist.",
                "{A} lands during the scramble and settles back into control.",
                "{A} makes {B} carry weight, then scores with a short elbow.",
                "{A} traps the far arm and lands three measured punches.",
                "{A} floats over the hips and keeps landing as {B} turns.",
            ],
            "ground_strikes_miss": [
                "{B} ties up the wrists and stops {A} from posturing.",
                "{A} tries to elbow, but {B} turns the head off the centre line.",
                "{B} uses butterfly hooks to disrupt {A}'s ground-and-pound.",
                "{A} loads the strike and {B} closes the distance before it lands.",
                "{B} keeps the guard high and absorbs the shot on the forearms.",
                "{A} swings from top, but {B} creates just enough angle to avoid it.",
            ],
            "low_kick_land": [
                "{A} chops the calf as {B} starts to step in.",
                "{A} lands inside low and forces {B} to square up.",
                "{A} kicks the base after the jab and leaves {B} out of stance.",
                "{A} threads a low kick under {B}'s attempted counter.",
                "{A} turns the hip over and lands hard to the outside thigh.",
                "{A} attacks the lead leg while {B}'s weight is planted.",
                "{A} ends the exchange with a calf kick that draws a reaction.",
                "{A} uses the low kick to interrupt {B}'s forward rhythm.",
            ],
            "body_kick_land": [
                "{A} slams the open-side kick into {B}'s ribs.",
                "{A} hides the body kick behind a hand feint and lands clean.",
                "{A} kicks through the elbow and makes {B} take the full impact.",
                "{A} turns the shin into the midsection as {B} shells high.",
                "{A} catches {B} circling and lands the kick across the body.",
                "{A} punches into the body kick and backs {B} up.",
                "{A} lands to the liver side and exits before the return.",
                "{A} whips the rear kick into the ribs after drawing the guard high.",
            ],
            "high_kick_land": [
                "{A} flicks the lead leg high and catches {B} on the guard and temple.",
                "{A} hides the high kick behind the cross and lands at the edge of range.",
                "{A} kicks high as {B} dips toward the body shot.",
                "{A} changes levels, then brings the shin upstairs.",
                "{A} lands the head kick partially, but it still moves {B}.",
                "{A} fires a high kick at the end of a long punching sequence.",
                "{A} beats {B}'s retreat with a fast kick around the guard.",
                "{A} uses the stance switch to open the high kick lane.",
            ],
            "kick_miss": [
                "{B} reads the hip turn and steps outside the kick.",
                "{A} kicks high, but {B} ducks under and resets.",
                "{B} withdraws the lead leg before {A}'s low kick arrives.",
                "{A} looks for the body kick and finds only forearm and air.",
                "{B} slides away from the arc and leaves {A} over-rotated.",
                "{A} throws the kick naked and {B} is already out of range.",
            ],
            "kick_caught": [
                "{B} catches the kick, runs the pipe and puts {A} on the mat.",
                "{B} scoops the body kick and turns it into top position.",
                "{B} traps the leg, drives forward and dumps {A} near the fence.",
                "{A} kicks high-risk and {B} converts the catch into a takedown.",
                "{B} catches the low kick and sweeps out the standing leg.",
            ],
            "clinch_entry": [
                "{A} punches into the clinch and gets forehead position.",
                "{A} crashes behind the guard and locks {B} to the fence.",
                "{A} ducks under the counter and ties up before {B} can pivot.",
                "{A} uses the underhook to turn {B} into the cage.",
                "{A} steps through the pocket and forces a collar-tie battle.",
                "{A} catches {B} backing up and closes the clinch on the fence.",
            ],
            "clinch_denied": [
                "{B} frames on the collarbone and refuses the clinch entry.",
                "{A} reaches for the tie, but {B} circles off the black line.",
                "{B} peels the grip and resets before {A} can connect hands.",
                "{B} posts hard on the shoulder and keeps striking space.",
                "{A} tries to crash in, but {B} meets them with a stiff frame.",
            ],
            "cage_control": [
                "{A} keeps the underhook and makes {B} carry weight on the fence.",
                "{A} pins the wrist and keeps {B} from turning off the cage.",
                "{A} changes levels just enough to freeze {B}'s escape.",
                "{A} leans shoulder-first into {B} and drains the legs.",
                "{A} keeps head position and wins the slow minutes on the cage.",
                "{A} traps {B}'s hips against the fence and chips with knees.",
            ],
            "cage_escape": [
                "{B} wins the pummel, turns the corner and escapes to space.",
                "{B} clears the wrist control and circles away from the fence.",
                "{B} frames across the face and slips off the cage.",
                "{B} times the level change and shucks {A} aside.",
                "{B} gets double inside position and walks back to range.",
            ],
            "break_clinch": [
                "{A} shoves off and resets before {B} can re-clinch.",
                "{A} breaks the tie with a hard frame and returns to range.",
                "{A} circles out of the collar tie and gets back to kickboxing range.",
                "{A} peels the underhook, steps off and clears the fence.",
                "{A} snaps down briefly, then releases to open space.",
            ],
            "takedown_complete": [
                "{A} times the level change and finishes through the hips into {position}.",
                "{A} chains from single to double and lands on top in {position}.",
                "{A} turns the corner and settles into {position} before {B} can scramble.",
                "{A} gets under the centre of gravity and runs {B} down to {position}.",
                "{A} finishes the shot on the second effort and arrives in {position}.",
                "{A} catches the kickboxing stance square and completes the takedown to {position}.",
                "{A} pulls the legs together and slides straight into {position}.",
                "{A} trips from the body lock and lands heavy in {position}.",
            ],
            "slam_takedown": [
                "{A} lifts from the body lock and plants {B} hard into {position}.",
                "{A} elevates the hips, turns, and drops {B} into {position}.",
                "{A} changes levels under the counter and finishes with a heavy slam.",
                "{A} powers through the sprawl and dumps {B} to the canvas.",
                "{A} hoists {B} high enough to make the landing echo.",
            ],
            "takedown_cage": [
                "{A} gets to the legs but {B} posts on the fence to stay upright.",
                "{A} keeps driving through the shot and pins {B} on the cage.",
                "{B} denies the finish for now, but {A} still has the hips trapped.",
                "{A} switches to a single and keeps {B} hopping along the fence.",
                "{A} cannot complete it yet, but {B} is stuck defending the chain.",
            ],
            "takedown_denied": [
                "{B} sprawls, circles and forces {A} back to the feet.",
                "{B} stuffs the head outside and punishes the failed entry.",
                "{B} gets the hips back and breaks {A}'s grip before the finish.",
                "{A} shoots from too far out and {B} reads it all the way.",
                "{B} wins the underhook and shuts the takedown down cold.",
                "{B} bounces off the fence and escapes the second effort.",
            ],
            "pass": [
                "{A} pins the knee shield and slides cleanly to {position}.",
                "{A} forces the hips flat and advances into {position}.",
                "{A} wins the crossface battle and clears to {position}.",
                "{A} beats the frame and settles heavy in {position}.",
                "{A} times the guard recovery and passes straight to {position}.",
                "{A} steps over the butterfly hook and lands in {position}.",
            ],
            "pass_denied": [
                "{B} keeps the knee shield alive and blocks the pass.",
                "{B} frames at the neck and recovers enough hip space.",
                "{A} tries to staple the leg, but {B} wins the inside position.",
                "{B} tracks the hips and prevents {A} from clearing the guard.",
                "{B} clamps half guard and stops the advance.",
                "{B} uses the underhook to make {A} abandon the pass.",
            ],
            "recover_guard": [
                "{A} shrimps hard and threads a knee back inside.",
                "{A} recovers the butterfly hook and slows the pressure.",
                "{A} gets the shin across the belt line and rebuilds guard.",
                "{A} frames the shoulder and brings the legs back into play.",
                "{A} uses the fence to scoot back to guard.",
                "{A} turns the hips at the last second and denies the clean pass.",
            ],
            "hold_position": [
                "{B} crossfaces hard and keeps the hips pinned.",
                "{B} follows the shrimp and denies the guard recovery.",
                "{B} keeps the underhook and stays glued to top position.",
                "{B} floats through the movement and remains heavy.",
                "{B} blocks the knee line and keeps the dominant position.",
                "{B} keeps chest pressure in place and makes {A} start over.",
            ],
            "top_control": [
                "{A} rides the hips and keeps {B} flattened beneath the pressure.",
                "{A} keeps the crossface tight and forces {B} to work from bad posture.",
                "{A} controls the near wrist and makes every escape costly.",
                "{A} stays patient, advancing inches rather than giving space away.",
                "{A} uses shoulder pressure to make {B} breathe under the weight.",
                "{A} keeps the knees pinched and denies {B}'s scramble attempts.",
            ],
            "ref_standup": [
                "the referee wants more action and brings them back to the feet.",
                "{A} stays heavy but inactive, and the referee orders the stand-up.",
                "the mat work stalls out, so the official restarts them at range.",
                "the crowd murmurs as the referee steps in for a reset.",
            ],
            "sweep": [
                "{A} elevates with the butterfly hook and comes up on top.",
                "{A} catches {B} leaning and reverses the position.",
                "{A} times the post, turns the corner and wins the scramble.",
                "{A} uses the fence to build up and roll into top position.",
                "{A} attacks the base and sweeps cleanly to control.",
                "{A} turns defence into offence with a sharp reversal.",
            ],
            "sweep_denied": [
                "{B} posts wide and kills the butterfly sweep.",
                "{A} tries to elevate, but {B}'s base is too strong.",
                "{B} backsteps away from the sweep and keeps top control.",
                "{B} follows the hips and denies the reversal.",
                "{A} looks for the momentum shift, but {B} shuts it down.",
            ],
            "stand_up": [
                "{A} builds to a hip, posts and gets back to standing.",
                "{A} wall-walks inch by inch until the hands break.",
                "{A} creates a frame, turns to a knee and escapes.",
                "{A} posts on the head and scrambles back to range.",
                "{A} uses the fence to stand without giving the back.",
                "{A} clears the ankle grip and returns to open space.",
            ],
            "mat_return": [
                "{B} follows the stand-up and drags {A} back down.",
                "{B} catches the hips and mat-returns {A} before the escape is real.",
                "{B} lifts the near leg and dumps {A} back to the canvas.",
                "{B} keeps the lock and turns {A}'s stand-up into another takedown.",
                "{B} refuses the escape and pulls {A} back into top control.",
            ],
            "cling": [
                "{A} overhooks from bottom and prevents {B} from posturing.",
                "{A} ties up both wrists and forces a slower grappling exchange.",
                "{A} keeps the head close and denies the big ground strikes.",
                "{A} locks a closed guard and buys recovery time.",
                "{A} clamps down just long enough to stop the damage building.",
            ],
            "submission_danger": [
                "{A} snaps into a deep submission threat and {B} has to move immediately.",
                "{B} is stuck defending grips as {A} keeps adjusting the angle.",
                "{A} attacks the finish in transition and nearly catches {B}.",
                "{A} forces {B} into a frantic hand-fight near the edge of danger.",
                "{B} survives, but {A}'s submission threat changes the whole position.",
                "{A} links the grip and makes {B} burn energy to escape.",
                "{A} turns a scramble into a real submission scare.",
                "{B} has to abandon position just to clear {A}'s attack.",
            ],
            "submission_threat": [
                "{A} exposes the neck and makes {B} respect the choke threat.",
                "{A} isolates an arm and starts climbing toward the finish.",
                "{A} attacks the leg entanglement and forces {B} to hand-fight.",
                "{A} uses wrist control to open a submission chain.",
                "{A} threatens from the bottom and makes {B} slow the offence.",
                "{A} keeps hunting grips while {B} tries to posture away.",
                "{A} teases the neck, then switches to the trapped arm.",
                "{A} uses the submission threat to freeze {B}'s escape.",
            ],
            "submission_defended": [
                "{B} clears the choking arm before {A} can connect the grip.",
                "{B} stacks the hips and takes the pressure out of the arm attack.",
                "{A} attacks the leg, but {B} turns the knee line free.",
                "{B} recognises the setup and strips the hands before danger builds.",
                "{B} keeps posture and denies {A}'s submission angle.",
                "{A} reaches for the lock, but {B} wins the grip battle.",
                "{B} hides the elbow and shuts down the arm attack.",
                "{B} steps over the entanglement and escapes the leg-lock look.",
            ],
            "survive": [
                "{A} shells, circles and refuses to give {B} a stationary target.",
                "{A} buys time with a desperate frame and a short clinch.",
                "{A} fires back just enough to slow {B}'s finishing charge.",
                "{A} keeps moving along the fence and avoids the clean follow-up.",
                "{A} changes levels defensively to interrupt {B}'s momentum.",
                "{A} ties up and makes {B} work instead of teeing off.",
                "{A} takes a breath behind the guard and starts to recover.",
                "{A} survives the burst by staying disciplined under pressure.",
            ],
            "ko_finish": [
                "{A} lands a counter right and {B} drops like the signal was cut.",
                "{A} threads the uppercut perfectly and {B} collapses in place.",
                "{A} catches {B} stepping in and ends the exchange instantly.",
                "{A} lands the shot behind the ear and {B}'s balance vanishes.",
                "{A} times the reset with a hook that switches everything off.",
                "{A} splits the guard with a straight left and {B} goes down hard.",
                "{A} lands a compact counter and {B} is out before hitting the mat.",
                "{A} detonates a punch at close range and {B} cannot respond.",
            ],
            "walkoff_ko": [
                "{A} lands once, reads the finish and calmly turns away.",
                "{A} connects clean and lets the referee handle the rest.",
                "{A} points to the canvas as {B} falls from the delayed reaction.",
                "{A} recognises the knockout immediately and refuses the extra shot.",
                "{A} lands the counter and walks off before the crowd catches up.",
                "{A} drops {B} with one punch and already knows the result.",
            ],
            "head_kick_ko": [
                "{A} hides the high kick behind hand traffic and {B} never sees it.",
                "{A} catches {B} dipping with the shin and ends it cold.",
                "{A} whips the kick over the guard and {B} collapses backward.",
                "{A} lands the switch kick clean and the fight is over immediately.",
                "{A} times the level change with a high kick that lands perfectly.",
                "{A} wraps the shin around the glove and shuts {B} down.",
            ],
            "standing_tko": [
                "{A} smells the finish and keeps every punch short and accurate.",
                "{B} is still upright, but the defence is no longer intelligent.",
                "{A} traps {B} on the warning track and pours on unanswered shots.",
                "{A} mixes knees and punches until {B} can only cover up.",
                "{A} keeps the output controlled and leaves the referee no choice.",
                "{B} turns away under pressure and the stoppage is inevitable.",
            ],
            "ground_tko": [
                "{A} flattens {B} out and lands until the referee steps in.",
                "{A} keeps wrist control and punches through every attempted turn.",
                "{A} advances to mount and the unanswered shots pile up quickly.",
                "{A} traps {B} near the fence and lands compact elbows.",
                "{A} keeps the hips pinned and forces the ground stoppage.",
                "{A} rides the back and lands until {B} stops improving position.",
            ],
            "doctor": [
                "the doctor studies the cut closely and decides {B} cannot continue.",
                "{B}'s eye is swelling shut and the medical team waves it off.",
                "the cut is in a bad place and the doctor stops the contest.",
                "{B} insists they can see, but the doctor is not convinced.",
                "the inspection is brief; the damage is too severe to continue.",
            ],
            "corner_stoppage": [
                "{B}'s corner protects their fighter and calls the bout off.",
                "the towel comes in before {B} can take any more damage.",
                "{B}'s coaches have seen enough after the last round.",
                "the inspector receives word from {B}'s corner that the fight is over.",
                "{B}'s corner chooses the long career over one more round.",
            ],
            "injury_stoppage": [
                "{B} tries to step forward, but the damaged leg gives way.",
                "{B} turns from the body damage and cannot continue.",
                "{B} cannot answer the referee after the accumulated leg kicks.",
                "{B}'s ribs are compromised and the official has to stop it.",
                "{B} signals the injury and the bout is waved off.",
            ],
            "fatigue_tko": [
                "{B} is too exhausted to return fire and the referee steps in.",
                "{B}'s guard falls apart under the accumulation.",
                "{A} keeps a steady pace as {B} fades past the point of defence.",
                "{B} is stuck on the fence with nothing left in the tank.",
                "{B} cannot move the feet anymore and the stoppage comes.",
            ],
            "ref_intervention": [
                "The referee closes the distance fast and waves it off.",
                "The official has seen enough and steps between them.",
                "The referee pulls {A} away before another shot can land.",
                "The stoppage arrives as {B} is no longer defending.",
                "The official dives in to protect {B}.",
            ],
            "late_ref": [
                "{B} takes a few extra shots before the referee can get there.",
                "The stoppage is late enough to draw complaints from the corner.",
                "That intervention could have come several punches earlier.",
                "The replay will not flatter the timing of that stoppage.",
            ],
            "early_ref": [
                "{B} objects immediately, but the referee had made the safety call.",
                "{B} tries to wave the stoppage off while still unsteady.",
                "The crowd debates it as {B} argues from a knee.",
                "It is a protective stoppage, and {B} is furious about it.",
            ],
            "aftermath": [
                "{A}'s corner floods in as the official result is prepared.",
                "{A} climbs the fence for a moment, then turns back to check on {B}.",
                "The arena noise spikes as the replay hits the big screen.",
                "{B}'s team enters quickly while {A} is pulled toward the interview.",
                "The broadcast booth is still reacting as the doctors step in.",
                "{A} takes a deep breath, points to the corner and celebrates the finish.",
            ],
            "official_finish": [
                "The official result is {A} by {method} at {time} of round {round_no}.",
                "{A} gets the stoppage by {method}; official time {time} of round {round_no}.",
                "At {time} of round {round_no}, {A} is declared the winner by {method}.",
                "The announcement confirms {A} wins by {method} in round {round_no} at {time}.",
            ],
            "decision": [
                "After the final horn, the cards reward {A}'s cleaner work: {score}.",
                "The judges lean toward {A} after a tight tactical fight, {score}.",
                "{A} takes it on the cards after banking enough rounds, {score}.",
                "The scorecards come in at {score}, and {A} gets the decision.",
                "{A}'s round-by-round work holds up with the judges, {score}.",
            ],
            "draw": [
                "The judges cannot split them; the official card reads {score}.",
                "After all that work, the scorecards land level at {score}.",
                "The bout is ruled a draw, with the cards reading {score}.",
                "Neither fighter gets the nod after a level set of cards, {score}.",
            ],
        }
        for category, lines in deeper_pool.items():
            expanded.setdefault(category, []).extend(lines)
        self._mma_striking_commentary_cache = expanded
        return expanded

    def ds(self, fighter, key, fallback=50):
        skills = fighter.detailed_skills or {}
        return skills.get(key, fallback)

    def ds_avg(self, fighter, keys, fallback=50):
        skills = fighter.detailed_skills or {}
        return round(sum(skills.get(key, fallback) for key in keys) / max(1, len(keys)))

    def skill_bundle(self, fighter, bundle):
        cache = getattr(self, "_fight_skill_bundle_cache", None)
        cache_key = (id(fighter), bundle)
        if cache is not None and cache_key in cache:
            return cache[cache_key]
        keys = FIGHT_SKILL_BUNDLES.get(bundle, ())
        if not keys:
            return fighter.overall
        skills = fighter.detailed_skills or {}
        # Avoid calculating the multi-group overall on every exchange when all
        # detailed keys are present (the normal case). Missing legacy keys still
        # receive exactly the same overall fallback as before.
        missing = any(key not in skills for key in keys)
        fallback = fighter.overall if missing else 50
        value = round(sum(skills.get(key, fallback) for key in keys) / len(keys))
        if cache is not None:
            cache[cache_key] = value
        return value

    def resolve_exchange(self, actor, defender, action, state, round_stats):
        """Resolve one action and maintain a genuine unanswered-offense streak.

        A sequence is unanswered only when significant strikes actually land.
        Meaningful counters such as takedowns, escapes, reversals, or submission
        threats clear the responding fighter's incoming streak.
        """
        actor_key = self.fight_state_key(actor, state)
        defender_key = self.fight_state_key(defender, state)
        actor_stats = state.get("stats", {}).get(actor_key, {})
        actor_round = round_stats.get(actor_key, {})
        sig_before = actor_stats.get("sig", 0)
        response_before = tuple(actor_round.get(key, 0) for key in ("impact", "control", "danger"))
        position_before = (
            state.get("position"), state.get("top"), state.get("bottom"),
            state.get("clinch_controller"),
        )
        active_window = state.get("counter_window") or {}
        state["last_exchange_counter"] = active_window.get("fighter") == actor_key
        state["last_strike_target"] = None
        state["last_move_payload"] = None
        state["last_submission_escape"] = None
        state["last_submission_technique"] = None
        state["intermediate_positions"] = []

        result = self._resolve_exchange_action(actor, defender, action, state, round_stats)

        landed_strikes = actor_stats.get("sig", 0) > sig_before
        response_after = tuple(actor_round.get(key, 0) for key in ("impact", "control", "danger"))
        position_after = (
            state.get("position"), state.get("top"), state.get("bottom"),
            state.get("clinch_controller"),
        )
        meaningful_response = landed_strikes or response_after != response_before or position_after != position_before
        if landed_strikes:
            state["unanswered"][defender_key] = state["unanswered"].get(defender_key, 0) + 1
        if meaningful_response:
            state["unanswered"][actor_key] = 0
            if state.get("hurt", {}).get(actor_key, 0) > 0:
                composure_recovery = 0.15 + self.ds(actor, "stun_recovery", actor.recovery) / 600
                state["hurt"][actor_key] = max(0, state["hurt"][actor_key] - composure_recovery)
        failed_attack = (not landed_strikes and response_after == response_before and position_after == position_before
                         and action not in ("survive", "cling", "ground_control", "cage_control"))
        if failed_attack:
            state["counter_window"] = {
                "fighter": defender_key, "source_action": action,
                "created_round": int(state.get("round", 1)), "created_tick": int(state.get("tick", 1)),
            }
        elif state.get("last_exchange_counter"):
            state["counter_window"] = None
        return result

    def _resolve_exchange_action(self, actor, defender, action, state, round_stats):
        position = state["position"]
        attack = self.action_attack_value(actor, action, state)
        defence = self.action_defence_value(defender, action, state)
        margin = attack - defence + self.fight_mechanics_rng().randint(-18, 18)

        actor_key = self.fight_state_key(actor, state)
        defender_key = self.fight_state_key(defender, state)
        if action == "front_headlock":
            if margin > -5:
                self.set_fight_position(state, "front headlock", top=actor_key, bottom=defender_key)
                round_stats[actor_key]["control"] += 3
                return f"{actor.name} sprawls, circles to the head and locks a front headlock as {defender.name} remains grounded."
            self.set_fight_position(state, "range")
            return f"{defender.name} clears the head and recovers to open space before {actor.name} can consolidate."
        if action == "force_cage":
            self.set_fight_position(state, "cage", controller=actor_key)
            round_stats[actor_key]["control"] += 2
            return f"{actor.name} stuffs the shot and steers {defender.name} upright into the fence."
        if action == "disengage":
            self.set_fight_position(state, "range")
            return f"{actor.name} circles clear after denying the shot and resets at range."
        if action == "re_shot":
            if margin > 6:
                self.set_fight_position(state, "guard", top=actor_key, bottom=defender_key)
                state["stats"][actor_key]["td_att"] += 1
                state["stats"][actor_key]["td"] += 1
                round_stats[actor_key]["control"] += 5
                return f"{actor.name} comes up on a re-shot, turns the corner and finishes into guard."
            if margin > -7:
                self.set_fight_position(state, "cage", controller=actor_key)
                state["stats"][actor_key]["td_att"] += 1
                round_stats[actor_key]["control"] += 2
                return f"{actor.name} chains from the failed entry and drives {defender.name} to the fence."
            self.set_fight_position(state, "front headlock", top=defender_key, bottom=actor_key)
            state["stats"][actor_key]["td_att"] += 1
            round_stats[defender_key]["control"] += 3
            return f"{defender.name} sprawls over the re-shot and secures a front headlock."
        if action == "recover_shot":
            if margin > -3:
                self.set_fight_position(state, "range")
                return f"{actor.name} rebuilds the stance, clears the grips and escapes the failed-shot position."
            self.set_fight_position(state, "cage", controller=defender_key)
            round_stats[defender_key]["control"] += 2
            return f"{defender.name} follows the recovery and pins {actor.name} upright against the fence."
        if action == "mat_return":
            if margin > -2:
                self.set_fight_position(state, "back control", top=actor_key, bottom=defender_key)
                state["stats"][actor_key]["td_att"] += 1
                state["stats"][actor_key]["td"] += 1
                round_stats[actor_key]["control"] += 5
                return f"{actor.name} lifts from the rear body lock and returns {defender.name} to the mat with back control."
            self.set_fight_position(state, "cage", controller=actor_key)
            return f"{defender.name} widens the base and survives the mat return, but {actor.name} keeps fence control."
        if action == "standing_back_ride":
            round_stats[actor_key]["control"] += 3
            return f"{actor.name} keeps the rear waist lock and rides {defender.name} along the fence."
        if action == "standing_escape":
            if margin > 2:
                self.set_fight_position(state, "range")
                return f"{actor.name} peels the hands, turns in and escapes the standing back control."
            round_stats[defender_key]["control"] += 2
            return f"{defender.name} keeps the rear lock and denies {actor.name}'s turn."
        if action == "front_headlock_submission":
            return self.resolve_submission(actor, defender, "submission", margin, state, round_stats)
        if action == "take_back":
            if margin > 4:
                self.set_fight_position(state, "back control", top=actor_key, bottom=defender_key)
                round_stats[actor_key]["control"] += 4
                return f"{actor.name} circles behind the defensive shell and secures back control."
            self.set_fight_position(state, "turtle", top=actor_key, bottom=defender_key)
            round_stats[actor_key]["control"] += 2
            return f"{actor.name} stays attached while {defender.name} builds a tight turtle."
        if action == "turtle_ride":
            if state["position"] != "turtle":
                self.set_fight_position(state, "turtle", top=actor_key, bottom=defender_key)
            round_stats[actor_key]["control"] += 3
            return f"{actor.name} controls the near wrist and keeps {defender.name} broken down in turtle."
        if action == "front_headlock_escape":
            if margin > 5:
                self.set_fight_position(state, "guard", top=defender_key, bottom=actor_key)
                return f"{actor.name} hand-fights free and recovers guard from the front headlock."
            if margin < -9:
                self.set_fight_position(state, "back control", top=defender_key, bottom=actor_key)
                round_stats[defender_key]["control"] += 3
                return f"{defender.name} follows the escape attempt around the hips and takes the back."
            self.set_fight_position(state, "turtle", top=defender_key, bottom=actor_key)
            return f"{actor.name} clears the choke grip but remains shelled in turtle."
        if action == "turtle_escape":
            if margin > 10:
                self.set_fight_position(state, "range")
                return f"{actor.name} posts, stands and turns free from turtle."
            if margin > -4:
                self.set_fight_position(state, "guard", top=defender_key, bottom=actor_key)
                return f"{actor.name} rolls through and recovers guard."
            round_stats[defender_key]["control"] += 2
            return f"{defender.name} blocks the hip and keeps {actor.name} trapped in turtle."
        if action == "leg_attack":
            return self.resolve_submission(actor, defender, "submission", margin, state, round_stats)
        if action == "leg_control":
            round_stats[actor_key]["control"] += 2
            return f"{actor.name} controls the knee line and keeps {defender.name} tied up in the leg entanglement."
        if action == "disengage_leg":
            self.set_fight_position(state, "range")
            return f"{actor.name} clears the legs safely and brings the fight back to standing."
        if action == "leg_escape":
            if margin > 8:
                self.set_fight_position(state, "range")
                return f"{actor.name} clears the knee line, retracts the leg and stands free."
            if margin > -5:
                self.set_fight_position(state, "guard", top=defender_key, bottom=actor_key)
                return f"{actor.name} frees the trapped knee and recovers guard."
            round_stats[defender_key]["control"] += 2
            return f"{defender.name} follows the hips and keeps the knee line trapped."
        if action == "counter_leg_lock":
            if margin > 5:
                self.set_fight_position(state, "leg entanglement", top=actor_key, bottom=defender_key)
                round_stats[actor_key]["danger"] += 3
                return f"{actor.name} wins the pummel between the legs and reverses the entanglement."
            return f"{defender.name} keeps the stronger leg position and denies the counter-lock."

        if action in ("jab", "power_punch", "kick", "dirty_boxing", "ground_strikes"):
            return self.resolve_strike(actor, defender, action, margin, state, round_stats)
        if action in ("shoot", "takedown"):
            return self.resolve_takedown(actor, defender, margin, state, round_stats)
        if action == "clinch":
            controller = state.get("clinch_controller")
            if controller and controller != self.fight_state_key(actor, state):
                if margin > 7:
                    state["clinch_controller"] = self.fight_state_key(actor, state)
                    state["clinch_ticks"] = 0
                    state["position"] = "cage" if state["position"] == "cage" else "clinch"
                    round_stats[self.fight_state_key(actor, state)]["control"] += 2
                    return f"{actor.name} pummels inside, wins the underhook battle, and reverses {defender.name}."
                return f"{defender.name} keeps the stronger clinch position and denies the reversal."
            if margin > -5:
                state["position"] = "clinch"
                state["clinch_controller"] = self.fight_state_key(actor, state)
                state["clinch_ticks"] = 0
                round_stats[self.fight_state_key(actor, state)]["control"] += 1
                return self.fight_phrase("clinch_entry", actor, defender)
            return self.fight_phrase("clinch_denied", actor, defender)
        if action == "cage_control":
            controller = state.get("clinch_controller")
            if controller and controller != self.fight_state_key(actor, state):
                if margin > 7:
                    state["clinch_controller"] = self.fight_state_key(actor, state)
                    state["position"] = "cage"
                    state["clinch_ticks"] = 0
                    round_stats[self.fight_state_key(actor, state)]["control"] += 3
                    return f"{actor.name} digs for double underhooks and turns {defender.name} onto the fence."
                return f"{defender.name} keeps {actor.name} pinned and wins the hand fight."
            if margin > -3:
                was_cage = state["position"] == "cage"
                standing_back_note = ""
                if (was_cage and margin > 32
                        and self.ds(actor, "back_control", actor.grappling)
                        >= self.ds(defender, "clinch_defence", defender.takedown_defence) + 45):
                    self.set_fight_position(
                        state, "standing back control",
                        controller=self.fight_state_key(actor, state),
                    )
                    standing_back_note = (
                        f"{actor.name} wins the pummel and circles to a rear body lock; "
                        f"{defender.name} is still hand-fighting the standing back control."
                    )
                if not standing_back_note:
                    state["position"] = "cage"
                    state["clinch_controller"] = self.fight_state_key(actor, state)
                round_stats[self.fight_state_key(actor, state)]["control"] += 3
                state["clinch_ticks"] = state.get("clinch_ticks", 0) + 1
                if standing_back_note:
                    return standing_back_note
                if not was_cage:
                    return f"{actor.name} walks {defender.name} to the fence, settles head position, and locks the hands."
                return self.fight_presentation_choice([
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
            round_stats[self.fight_state_key(defender, state)]["control"] += 1
            return f"{defender.name} keeps the tie-up and makes {actor.name} work."
        if action in ("advance_position", "recover_guard"):
            return self.resolve_position_move(actor, defender, action, margin, state, round_stats)
        if action in ("submission", "bottom_submission"):
            return self.resolve_submission(actor, defender, action, margin, state, round_stats)
        if action == "ground_control":
            round_stats[self.fight_state_key(actor, state)]["control"] += 3
            return self.fight_phrase("top_control", actor, defender)
        if action == "sweep":
            if margin > 10:
                state["top"] = self.fight_state_key(actor, state)
                state["bottom"] = self.fight_state_key(defender, state)
                state["position"] = "guard"
                round_stats[self.fight_state_key(actor, state)]["control"] += 4
                return self.fight_phrase("sweep", actor, defender)
            round_stats[self.fight_state_key(defender, state)]["control"] += 1
            return self.fight_phrase("sweep_denied", actor, defender)
        if action == "stand_up":
            if margin > 5:
                self.set_fight_position(state, "range")
                return self.fight_phrase("stand_up", actor, defender)
            round_stats[self.fight_state_key(defender, state)]["control"] += 2
            return self.fight_phrase("mat_return", actor, defender)
        if action == "cling":
            round_stats[self.fight_state_key(actor, state)]["control"] += 1
            return self.fight_phrase("cling", actor, defender)
        if action == "survive":
            survive_recovery = 0.18 + self.ds(actor, "conditioning", actor.cardio) / 210 + actor.recovery / 420 + actor.camp_boost / 45
            state["gas"][self.fight_state_key(actor, state)] = min(state["gas_cap"][self.fight_state_key(actor, state)], state["gas"][self.fight_state_key(actor, state)] + survive_recovery)
            state["hurt"][self.fight_state_key(actor, state)] = max(0, state["hurt"][self.fight_state_key(actor, state)] - 1)
            state["head"][self.fight_state_key(actor, state)] = max(
                0, state["head"][self.fight_state_key(actor, state)] - 1,
            )
            if state["position"] in ("guard", "half guard", "side control", "mount", "back control"):
                if state.get("top") == self.fight_state_key(actor, state):
                    return self.fight_presentation_choice([
                        f"{actor.name} settles their weight and takes a breath without giving up top position.",
                        f"{actor.name} stays heavy on top and steadies the pace for a moment.",
                        f"{actor.name} rides the position, catching a breather while staying busy enough to hold it.",
                        f"{actor.name} postures just enough to keep control while recovering.",
                    ])
                return self.fight_presentation_choice([
                    f"{actor.name} closes space from bottom, controls the wrists, and waits for a chance to improve.",
                    f"{actor.name} ties up the hands from underneath and slows the exchange down.",
                    f"{actor.name} frames and hip-escapes just enough to stay in the fight.",
                    f"{actor.name} keeps a tight guard from the bottom and rides out the pressure.",
                ])
            if state["position"] in ("clinch", "cage"):
                return self.fight_presentation_choice([
                    f"{actor.name} leans into the clinch and uses the tie-up to recover.",
                    f"{actor.name} buries their head on the chest in the clinch and catches a breath.",
                    f"{actor.name} pins the tie-up against the fence to steal a moment of rest.",
                    f"{actor.name} clings on in the clinch, slowing everything down to recover.",
                ])
            return self.fight_phrase("survive", actor, defender)
        return None

    def action_attack_value(self, fighter, action, state):
        gas = state["gas"][self.fight_state_key(fighter, state)]
        damage = state["hurt"][self.fight_state_key(fighter, state)]
        leg_damage = state.get("leg", {}).get(self.fight_state_key(fighter, state), 0)
        body_damage = state.get("body", {}).get(self.fight_state_key(fighter, state), 0)
        fatigue = (gas - 50) * 0.32
        low_gas_penalty = max(0, 32 - gas) * 0.45 + max(0, 12 - gas) * 0.9
        burst_actions = {
            "power_punch", "kick", "shoot", "takedown", "submission", "bottom_submission",
            "sweep", "stand_up", "re_shot", "mat_return", "take_back", "turtle_escape",
            "front_headlock_submission", "leg_attack", "leg_escape", "counter_leg_lock",
        }
        # The former dict literal evaluated all fifteen formulas for every one
        # action. Dispatching only the selected action is mathematically and
        # randomly identical, while removing most fight-engine busywork.
        if action == "jab":
            base = self.skill_bundle(fighter, "boxing") * 0.85 + self.ds(fighter, "reach", 50) * 0.18 + fighter.fight_iq * 0.18
        elif action == "power_punch":
            base = self.skill_bundle(fighter, "power_boxing") * 0.65 + fighter.power * 0.55 + self.ds(fighter, "killer_instinct", 50) * 0.16
        elif action == "kick":
            base = self.skill_bundle(fighter, "kick_game") * 0.85 + self.ds(fighter, "mobility", 50) * 0.22
        elif action == "dirty_boxing":
            base = self.skill_bundle(fighter, "clinch_attack") * 0.75 + fighter.toughness * 0.2 + self.ds(fighter, "strength", 50) * 0.18
        elif action == "ground_strikes":
            base = self.ds_avg(fighter, ("ground_striking", "top_control", "elbows", "punch_power"), fighter.ground_control) * 0.75 + fighter.power * 0.25
        elif action == "shoot":
            base = self.skill_bundle(fighter, "shot") * 0.82 + self.ds(fighter, "conditioning", fighter.cardio) * 0.18
        elif action == "takedown":
            base = self.ds_avg(fighter, ("clinch_takedowns", "throws", "chain_wrestling", "strength"), fighter.wrestling) * 0.78 + fighter.ground_control * 0.2
        elif action == "cage_control":
            base = self.ds_avg(fighter, ("cage_pressure", "cage_wrestling", "clinch_control", "strength"), fighter.wrestling) * 0.78 + fighter.fight_iq * 0.22
        elif action == "break_clinch":
            base = self.skill_bundle(fighter, "clinch_defence") * 0.75 + fighter.fight_iq * 0.22
        elif action == "advance_position":
            base = self.ds_avg(fighter, ("transitions", "positional_ability", "scrambles", "mount_control"), fighter.grappling) * 0.72 + fighter.ground_control * 0.25
        elif action == "recover_guard":
            base = self.skill_bundle(fighter, "bottom_game") * 0.8 + fighter.submission_defence * 0.2
        elif action == "submission":
            base = self.skill_bundle(fighter, "submission_game") * 0.68 + fighter.grappling * 0.14
        elif action == "bottom_submission":
            base = self.ds_avg(fighter, ("submission_attack", "guard_work", "leg_locks", "confidence"), fighter.submissions) * 0.66 + fighter.fight_iq * 0.14
        elif action == "sweep":
            base = self.ds_avg(fighter, ("scrambles", "bottom_control", "transitions", "strength"), fighter.grappling) * 0.78 + fighter.wrestling * 0.18
        elif action == "stand_up":
            base = self.ds_avg(fighter, ("get_ups", "scrambles", "sprawl", "conditioning"), fighter.takedown_defence) * 0.82 + fighter.cardio * 0.15
        elif action in ("front_headlock", "force_cage", "standing_back_ride", "turtle_ride"):
            base = self.ds_avg(fighter, ("front_headlock", "clinch_control", "ride_control", "strength"), fighter.wrestling) * 0.82 + fighter.ground_control * 0.16
        elif action in ("re_shot", "mat_return", "take_back"):
            base = self.ds_avg(fighter, ("chain_wrestling", "transitions", "back_control", "strength"), fighter.wrestling) * 0.82 + fighter.cardio * 0.14
        elif action in ("recover_shot", "standing_escape", "front_headlock_escape", "turtle_escape"):
            base = self.ds_avg(fighter, ("scrambles", "get_ups", "clinch_defence", "guard_work"), fighter.takedown_defence) * 0.82 + fighter.cardio * 0.14
        elif action == "front_headlock_submission":
            base = self.ds_avg(fighter, ("submission_attack", "front_headlock", "killer_instinct"), fighter.submissions) * 0.82 + fighter.fight_iq * 0.15
        elif action in ("leg_attack", "counter_leg_lock"):
            base = self.ds_avg(fighter, ("leg_locks", "submission_attack", "scrambles"), fighter.submissions) * 0.84 + fighter.fight_iq * 0.12
        elif action == "leg_control":
            base = self.ds_avg(fighter, ("leg_locks", "top_control", "discipline"), fighter.grappling) * 0.82
        elif action in ("leg_escape", "disengage_leg"):
            base = self.ds_avg(fighter, ("submission_defence_detail", "scrambles", "flexibility", "get_ups"), fighter.submission_defence) * 0.82
        elif action == "disengage":
            base = self.ds_avg(fighter, ("discipline", "footwork", "reflexes"), fighter.fight_iq) * 0.86
        else:
            base = fighter.overall
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
        erratic = self.fight_mechanics_rng().randint(-7, 7) if fighter.trait == "Erratic" else 0
        consistency = (self.ds(fighter, "consistency", 50) - 50) * 0.07
        action_drag = low_gas_penalty * (1.35 if action in burst_actions else 0.65)
        context = self.context_edge(fighter, state, "prime", "experience", "pressure", "rivalry", "morale")
        if action in ("jab", "power_punch", "kick", "dirty_boxing"):
            context += self.context_edge(fighter, state, "stance", "reach")
        if action in ("shoot", "takedown", "cage_control", "ground_control"):
            context += self.context_edge(fighter, state, "size")
        if action in ("submission", "bottom_submission"):
            context += self.context_edge(fighter, state, "experience")
        leg_drag = leg_damage * (0.26 if action in ("kick", "shoot", "takedown", "stand_up") else 0.08)
        body_drag = body_damage * (0.12 if action in burst_actions else 0.05)
        night_form = state.get("night_form", {}).get(self.fight_state_key(fighter, state), 0)
        size_drag = getattr(fighter, "division_size_penalty", 0) * (1.0 if action in ("power_punch", "kick", "dirty_boxing", "ground_strikes", "shoot", "takedown", "cage_control", "sweep") else 0.38)
        return base + fatigue + fighter.momentum * 0.75 + night_form * 1.10 + fighter.camp_boost * 1.6 + trait + erratic + consistency + context - action_drag - leg_drag - body_drag - size_drag

    def action_defence_value(self, fighter, action, state):
        gas = state["gas"][self.fight_state_key(fighter, state)]
        damage = state["hurt"][self.fight_state_key(fighter, state)]
        leg_damage = state.get("leg", {}).get(self.fight_state_key(fighter, state), 0)
        head_damage = state.get("head", {}).get(self.fight_state_key(fighter, state), 0)
        gas_drag = max(0, 34 - gas) * 0.38 + max(0, 12 - gas) * 0.72
        base = self.skill_bundle(fighter, "mental") * 0.1 + fighter.recovery * 0.08
        if action in ("jab", "power_punch", "kick", "dirty_boxing", "ground_strikes"):
            if action == "kick":
                base += self.skill_bundle(fighter, "kick_defence") * 0.48 + fighter.chin * 0.2 + fighter.toughness * 0.24
            elif action == "ground_strikes":
                base += self.skill_bundle(fighter, "bottom_game") * 0.45 + self.ds(fighter, "stun_recovery", fighter.recovery) * 0.2 + fighter.toughness * 0.26
            else:
                base += self.skill_bundle(fighter, "strike_defence") * 0.48 + fighter.chin * 0.22 + fighter.toughness * 0.24
        elif action in ("shoot", "takedown", "cage_control", "front_headlock", "force_cage", "re_shot", "mat_return", "take_back", "standing_back_ride", "turtle_ride"):
            base += self.skill_bundle(fighter, "anti_wrestling") * 0.58 + fighter.wrestling * 0.2
        elif action in ("submission", "bottom_submission", "front_headlock_submission", "leg_attack", "counter_leg_lock"):
            base += self.skill_bundle(fighter, "submission_defence") * 0.82 + fighter.grappling * 0.2
        elif action in ("recover_shot", "standing_escape", "front_headlock_escape", "turtle_escape"):
            base += self.skill_bundle(fighter, "clinch_attack") * 0.36 + self.skill_bundle(fighter, "anti_wrestling") * 0.42
        else:
            base += self.skill_bundle(fighter, "bottom_game") * 0.45 + fighter.wrestling * 0.2
        context = self.context_edge(fighter, state, "prime", "experience", "pressure", "morale")
        if action in ("jab", "power_punch", "kick", "dirty_boxing"):
            context += self.context_edge(fighter, state, "stance", "reach")
        if action in ("shoot", "takedown", "cage_control"):
            context += self.context_edge(fighter, state, "size")
        mobility_drag = leg_damage * (0.18 if action in ("kick", "shoot", "takedown", "cage_control") else 0.07)
        night_form = state.get("night_form", {}).get(self.fight_state_key(fighter, state), 0)
        return base + night_form * 0.78 + fighter.camp_boost * 1.2 + (gas - 50) * 0.24 - damage * 0.22 - head_damage * 0.05 - gas_drag - mobility_drag + (self.ds(fighter, "reflexes", 50) - 50) * 0.05 + context

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
            "front_headlock": 4,
            "force_cage": 4,
            "disengage": 1,
            "re_shot": 6,
            "recover_shot": 4,
            "mat_return": 6,
            "standing_back_ride": 3,
            "standing_escape": 4,
            "front_headlock_submission": 6,
            "take_back": 5,
            "turtle_ride": 3,
            "front_headlock_escape": 5,
            "turtle_escape": 5,
            "leg_attack": 6,
            "leg_control": 3,
            "disengage_leg": 2,
            "leg_escape": 5,
            "counter_leg_lock": 5,
            "survive": 0,
        }
        conditioning = self.ds(actor, "conditioning", actor.cardio)
        defender_conditioning = self.ds(defender, "conditioning", defender.cardio)
        efficiency = 1 - max(-0.16, min(0.26, (conditioning - 55) / 240 + (self.ds(actor, "discipline", 50) - 50) / 470))
        actor_cost = (costs.get(action, 2) * self.engine_settings.get("gas_cost", 1.0)
                      * efficiency * self.plan_energy_multiplier(actor, state))
        if state["gas"][self.fight_state_key(actor, state)] < 30 and action in ("power_punch", "kick", "shoot", "takedown", "submission", "sweep", "stand_up"):
            actor_cost *= 1.22
        if actor.trait == "Cardio Machine":
            actor_cost *= 0.9
        if actor.trait == "Warrior Spirit" and state["gas"][self.fight_state_key(actor, state)] < 35:
            actor_cost *= 0.94
        if actor.trait == "Bad Weight Cut":
            actor_cost *= 1.14
        defender_efficiency = 1 - max(-0.12, min(0.20, (defender_conditioning - 55) / 280))
        defender_cost = max(0.7, actor_cost * 0.5 * defender_efficiency)
        if state["body"][self.fight_state_key(actor, state)] > 12:
            actor_cost += 1 + state["body"][self.fight_state_key(actor, state)] / 28
        if state["body"][self.fight_state_key(defender, state)] > 12:
            defender_cost += 1 + state["body"][self.fight_state_key(defender, state)] / 32
        state["gas"][self.fight_state_key(actor, state)] = max(3, min(state["gas_cap"][self.fight_state_key(actor, state)], state["gas"][self.fight_state_key(actor, state)] - actor_cost))
        state["gas"][self.fight_state_key(defender, state)] = max(3, min(state["gas_cap"][self.fight_state_key(defender, state)], state["gas"][self.fight_state_key(defender, state)] - defender_cost))

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
        return (max(0.0016, min(0.12, chance))
                * self.engine_settings.get("ko_power", 1.0)
                * self.competitive_finish_conversion(actor, defender))

    def competitive_finish_conversion(self, actor, defender):
        """Scale dangerous-moment conversion for evenly matched skilled fighters.

        Low-level bouts keep their established volatility.  In competitive mid-
        and high-level bouts, better composure, recovery, and layered defence
        make a clean opening less likely to become an immediate finish.  Clear
        matchmaking mismatches deliberately retain the full conversion rate.
        """
        cache = getattr(self, "_fight_finish_conversion_cache", None)
        cache_key = (id(actor), id(defender))
        if cache is not None and cache_key in cache:
            return cache[cache_key]
        if abs(actor.overall - defender.overall) > 6:
            value = 1.0
            if cache is not None:
                cache[cache_key] = value
            return value
        average_level = (actor.overall + defender.overall) / 2
        if average_level < 68:
            value = 1.0
        elif average_level < 80:
            value = 0.46
        else:
            value = 0.56
        if cache is not None:
            cache[cache_key] = value
        return value

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
        return self.fight_presentation_choice(options)

    def deliver_flush_knockout(self, actor, defender, action, state, round_stats):
        """Apply a sudden flush KO and register the instant finish with named technique."""
        state["danger"][self.fight_state_key(actor, state)] += 12
        round_stats[self.fight_state_key(actor, state)]["danger"] += 12
        state["damage"][self.fight_state_key(defender, state)] += 14
        head_trauma = state.setdefault("head_trauma", {key: 0 for key in state["head"]})
        state["head"][self.fight_state_key(defender, state)] += 14
        head_trauma[self.fight_state_key(defender, state)] += 14
        state["knockdowns"][self.fight_state_key(actor, state)] += 1
        state["finish_category"] = "walkoff_ko" if self.fight_mechanics_rng().random() < 0.45 else "ko_finish"
        state["flush_knockout"] = True
        technique = self.signature_technique(actor, action)
        detail = self.fight_phrase("signature_ko", actor, defender, technique=technique)
        if state["finish_category"] == "walkoff_ko":
            detail = f"{detail} {self.fight_phrase('walkoff_ko', actor, defender)}"
        state["instant_finish"] = (self.fight_state_key(actor, state), self.fight_state_key(defender, state), "KO", detail)
        return self.fight_phrase("knockdown", actor, defender, technique=technique)

    @staticmethod
    def kick_knockdown_categories(kick_type):
        """Keep strike knockdowns distinct from genuine injury stoppages."""
        if kick_type == "high":
            return "head_kick_ko", "knockdown"
        if kick_type in ("body", "teep"):
            return "body_kick_knockdown", "body_kick_knockdown"
        return "leg_kick_knockdown", "leg_kick_knockdown"

    def knockdown_finish_category(self, action, impact):
        """Choose finish copy without adding a draw to the combat outcome stream."""
        if action != "power_punch":
            return "ko_finish"
        if impact > 9:
            # This mechanics draw already existed in the resolved heavy-punch
            # path; retaining it preserves the frozen outcome stream.
            walkoff = self.fight_mechanics_rng().random() < 0.40
        elif impact > 7:
            # Mid-power knockdowns can vary their presentation, but never
            # consume the mechanics or officiating streams.
            walkoff = self.fight_presentation_random() < 0.40
        else:
            walkoff = False
        return "walkoff_ko" if walkoff else "ko_finish"

    def record_structured_cut(self, defender, state, impact, weapon="strike"):
        """Record cut location and severity without consuming another random draw."""
        defender_key = self.fight_state_key(defender, state)
        locations = ("left eyebrow", "right eyebrow", "left cheek", "right cheek", "nose")
        cuts = state.setdefault("cut_state", {}).setdefault(defender_key, [])
        index = (int(state.get("round", 1)) * 7 + int(state.get("tick", 1)) + len(cuts)) % len(locations)
        severity = max(1, min(5, int(round(float(impact or 1) / 4))))
        cut = {
            "location": locations[index], "severity": severity,
            "bleeding": max(1, min(5, severity + (1 if weapon == "elbow" else 0))),
            "swelling": max(0, min(5, severity - 1)),
            "vision_risk": locations[index] in ("left eyebrow", "right eyebrow") and severity >= 3,
            "weapon": weapon, "round": int(state.get("round", 1)),
            "tick": int(state.get("tick", 1)),
        }
        cuts.append(cut)
        return cut

    def output_multiplier(self, fighter):
        """How busy this fighter is inside a striking sequence.

        Volume is a real, visible identity in MMA: a high-output pressure
        fighter throws far more than a patient counter-striker even when both
        are equally skilled. Stats, style and behaviour all feed this, so
        career strike totals separate fighters instead of converging on one
        league-average number."""
        if fighter is None:
            return 1.0
        aggression = self.ds(fighter, "aggression", 50)
        conditioning = self.ds(fighter, "conditioning", fighter.cardio)
        hand_speed = self.ds(fighter, "hand_speed", fighter.striking)
        multiplier = 1.0
        multiplier += (aggression - 50) / 145
        multiplier += (conditioning - 50) / 260
        multiplier += (hand_speed - 50) / 300
        multiplier *= {
            "Volume": 1.22, "Pressure": 1.14, "Dynamic Attacker": 1.08,
            "Counter": 0.84, "Cautious": 0.78, "Control": 0.90,
            "Submission Hunter": 0.88, "Sprawl And Brawl": 1.0,
        }.get(getattr(fighter, "behaviour", ""), 1.0)
        multiplier *= {
            "Boxer": 1.10, "Kickboxer": 1.10, "Dutch Kickboxer": 1.16, "Muay Thai": 1.06,
            "Karate": 0.86, "Taekwondo": 0.88, "Sanda": 1.02,
            "Wrestler": 0.86, "Freestyle Wrestler": 0.86, "Catch Wrestler": 0.88,
            "BJJ": 0.84, "Luta Livre": 0.86, "Sambo": 0.88, "Judo": 0.86,
            "Grappler": 0.84, "Submission Grappler": 0.82,
        }.get(getattr(fighter, "style", ""), 1.0)
        return max(0.55, min(1.85, multiplier))

    def strike_volume(self, action, margin, landed=True, attempts=None, actor=None):
        """Each commentary beat represents a small, explicit strike sequence, not one invisible strike.

        Pass a pre-drawn ``attempts`` when computing landed strikes for the same
        sequence, so the number that land can never exceed the number thrown."""
        if attempts is None:
            # A round is ~18 ticks shared between both fighters, so each fighter
            # gets ~9 beats and only a fraction of those are striking exchanges.
            # These sequence sizes are what scale the engine to real UFC output:
            # roughly 4-5 significant strikes landed per minute (~20-25 a round).
            # Undersized sequences here previously produced ~5 landed a round,
            # about a fifth of real-world volume.
            base = {
                "jab": self.fight_mechanics_rng().randint(9, 20),
                "power_punch": self.fight_mechanics_rng().randint(7, 15),
                "kick": self.fight_mechanics_rng().randint(5, 12),
                "dirty_boxing": self.fight_mechanics_rng().randint(7, 16),
                "ground_strikes": self.fight_mechanics_rng().randint(10, 26),
            }.get(action, 1)
            attempts = max(1, round(base * self.output_multiplier(actor))) if actor is not None else base
        if not landed:
            return attempts, 0
        accuracy = 0.46 + min(0.38, max(-0.1, margin) / 52)
        if action == "jab":
            accuracy += 0.12
        elif action == "ground_strikes":
            accuracy += 0.08
        return attempts, max(1, min(attempts, round(attempts * accuracy)))

    def kick_target_shares(self, actor, state):
        """Return normalized kick-target weights before the single target draw."""
        teep_chance = 0.08 + max(0, self.ds(actor, "creative_kicks", 50) - 45) / 500
        if any(style in ("Muay Thai", "Kickboxer", "Dutch Kickboxer", "Sanda")
               for style in self.fighter_styles(actor)):
            teep_chance += 0.08
        high_chance = 0.26 + (self.ds(actor, "creative_kicks", 50) - 50) / 300
        body_share = 0.30 + (0.18 if actor.trait == "Body Hunter" else 0)
        leg_share = 1 - teep_chance - high_chance - body_share
        if actor.trait == "Leg Kicker":
            high_chance = max(0.15, high_chance - 0.08)
            body_share = max(0.18, body_share - 0.06)
            leg_share = 1 - teep_chance - high_chance - body_share
        plan_row = self.fight_plan_for(actor, state)
        if plan_row["current"] == "Attack the body":
            body_share += 0.28 * plan_row["execution"]
        elif plan_row["current"] == "Damage the lead leg":
            leg_share += 0.34 * plan_row["execution"]
        shares = {
            "teep": max(0.03, teep_chance), "high": max(0.05, high_chance),
            "body": max(0.05, body_share), "leg": max(0.05, leg_share),
        }
        share_total = sum(shares.values())
        return {target: share / share_total for target, share in shares.items()}

    def resolve_strike(self, actor, defender, action, margin, state, round_stats):
        attempts, _ = self.strike_volume(action, margin, landed=False, actor=actor)
        state["stats"][self.fight_state_key(actor, state)]["sig_att"] += attempts
        state["last_strike_target"] = "head"
        if action == "kick":
            roll = self.fight_mechanics_rng().random()
            shares = self.kick_target_shares(actor, state)
            cursor = 0.0
            kick_type = "leg"
            for target in ("teep", "high", "body", "leg"):
                cursor += shares[target]
                if roll < cursor:
                    kick_type = target
                    break
            state["last_strike_target"] = "body" if kick_type == "teep" else kick_type
            if kick_type == "high":
                kick_power = self.ds(actor, "high_kick_power", actor.power)
                kick_speed = self.ds(actor, "high_kick_speed", actor.striking)
                kick_tech = self.ds(actor, "high_kick_technique", actor.striking)
                defence = self.ds_avg(defender, ("kick_defence", "head_movement", "reflexes", "mobility"), defender.striking)
                label = self.fight_presentation_choice(["a high kick", "a fast head kick", "a question-mark kick", "a high round kick"])
                body_gain, leg_gain = 0, 0
            elif kick_type == "teep":
                kick_power = self.ds_avg(actor, ("low_kick_power", "strength"), actor.power)
                kick_speed = self.ds_avg(actor, ("low_kick_speed", "mobility"), actor.striking)
                kick_tech = self.ds_avg(actor, ("creative_kicks", "low_kick_technique", "footwork"), actor.striking)
                defence = self.ds_avg(defender, ("kick_defence", "reflexes", "mobility", "footwork"), defender.striking)
                label = self.fight_presentation_choice(["a lead teep", "a rear teep", "a stabbing push kick", "a teep to the hip"])
                body_gain, leg_gain = self.fight_mechanics_rng().randint(1, 3), 0
            else:
                kick_power = self.ds(actor, "low_kick_power", actor.power)
                kick_speed = self.ds(actor, "low_kick_speed", actor.striking)
                kick_tech = self.ds(actor, "low_kick_technique", actor.striking)
                defence = self.ds_avg(defender, ("kick_defence", "mobility", "reflexes", "takedown_defence_detail"), defender.striking)
                if kick_type == "body":
                    label = self.fight_presentation_choice(["a hard body kick", "a digging round kick to the ribs", "a thudding kick to the midsection"])
                    body_gain, leg_gain = self.fight_mechanics_rng().randint(2, 5), 0
                else:
                    label = self.fight_presentation_choice(["a chopping low kick", "a calf kick", "an inside leg kick", "a hard kick to the thigh"])
                    body_gain, leg_gain = 0, self.fight_mechanics_rng().randint(2, 5)
            kick_margin = margin + (kick_tech - defence) * 0.28 + (kick_speed - self.ds(defender, "reflexes", 50)) * 0.22
            catch_risk = max(0.03, 0.18 + (defender.wrestling - actor.takedown_defence) / 210 + (self.ds(defender, "takedowns", defender.wrestling) - kick_speed) / 280)
            if kick_margin < -13:
                if self.fight_mechanics_rng().random() < catch_risk:
                    state["position"] = "guard"
                    state["top"] = self.fight_state_key(defender, state)
                    state["bottom"] = self.fight_state_key(actor, state)
                    round_stats[self.fight_state_key(defender, state)]["control"] += 4
                    return self.fight_phrase("kick_caught", actor, defender)
                defended_category = {
                    "high": "high_kick_checked",
                    "body": "body_kick_checked",
                    "leg": "low_kick_checked",
                    "teep": "teep_miss",
                }.get(kick_type, "kick_checked") if defence >= kick_tech + 4 else "kick_miss"
                return self.fight_phrase(defended_category, actor, defender)
            if kick_margin < 4 and self.fight_mechanics_rng().random() < catch_risk * 0.35:
                state["position"] = "guard"
                state["top"] = self.fight_state_key(defender, state)
                state["bottom"] = self.fight_state_key(actor, state)
                round_stats[self.fight_state_key(defender, state)]["control"] += 4
                return self.fight_phrase("kick_caught", actor, defender)
            _attempts, landed = self.strike_volume(action, kick_margin, landed=True, attempts=attempts)
            state["stats"][self.fight_state_key(actor, state)]["sig"] += landed
            impact = max(1, round((kick_margin + kick_power * 0.25 + kick_speed * 0.09) / 10 * self.engine_settings.get("damage", 1.0)))
            if kick_type in ("body", "teep"):
                state["body"][self.fight_state_key(defender, state)] += body_gain
                state["gas"][self.fight_state_key(defender, state)] = max(3, state["gas"][self.fight_state_key(defender, state)] - max(1, body_gain))
            elif kick_type == "leg":
                state["leg"][self.fight_state_key(defender, state)] += leg_gain
                state["gas"][self.fight_state_key(defender, state)] = max(3, state["gas"][self.fight_state_key(defender, state)] - max(1, leg_gain // 2))
            else:
                impact += 1
            state["damage"][self.fight_state_key(defender, state)] += impact
            if kick_type == "high":
                head_trauma = state.setdefault("head_trauma", {key: 0 for key in state["head"]})
                state["head"][self.fight_state_key(defender, state)] += impact
                head_trauma[self.fight_state_key(defender, state)] += impact
            round_stats[self.fight_state_key(actor, state)]["impact"] += impact
            if kick_type == "high" and self.fight_mechanics_rng().random() < self.flush_knockout_chance(actor, defender, kick_power, kick_margin, self.ds(actor, "creative_kicks", 50)):
                return self.deliver_flush_knockout(actor, defender, "high_kick", state, round_stats)
            if self.fight_mechanics_rng().random() < max(0.028, (impact + kick_power * 0.9 + kick_speed * 0.24 - defender.chin - self.ds(defender, "stun_recovery", defender.recovery) * 0.22) / 125):
                state["danger"][self.fight_state_key(actor, state)] += 9
                round_stats[self.fight_state_key(actor, state)]["danger"] += 9
                state["damage"][self.fight_state_key(defender, state)] += 8
                if kick_type == "high":
                    head_trauma = state.setdefault("head_trauma", {key: 0 for key in state["head"]})
                    state["head"][self.fight_state_key(defender, state)] += 8
                    head_trauma[self.fight_state_key(defender, state)] += 8
                elif kick_type in ("body", "teep"):
                    state["body"][self.fight_state_key(defender, state)] += 8
                else:
                    state["leg"][self.fight_state_key(defender, state)] += 8
                state["knockdowns"][self.fight_state_key(actor, state)] += 1
                state["finish_category"], knockdown_category = self.kick_knockdown_categories(kick_type)
                clean_ko_chance = (max(0.08, min(0.8, (kick_power + kick_speed + impact * 7.4 - defender.chin - self.ds(defender, "stun_recovery", defender.recovery) * 0.42) / 122))
                                   * self.competitive_finish_conversion(actor, defender))
                if kick_type == "high" and self.fight_mechanics_rng().random() < clean_ko_chance:
                    detail = self.fight_phrase("head_kick_ko", actor, defender)
                    state["instant_finish"] = (self.fight_state_key(actor, state), self.fight_state_key(defender, state), "KO", detail)
                return self.fight_phrase(knockdown_category, actor, defender, technique=label)
            if kick_type == "high":
                return self.fight_phrase("high_kick_land", actor, defender)
            if kick_type == "teep":
                return self.fight_phrase("teep_land", actor, defender)
            if kick_type == "body":
                category = "body_kick_hurt" if state["body"][self.fight_state_key(defender, state)] >= 10 else "body_kick_land"
                return self.fight_phrase(category, actor, defender, technique=label)
            category = "leg_kick_hurt" if state["leg"][self.fight_state_key(defender, state)] >= 10 else "low_kick_land"
            return self.fight_phrase(category, actor, defender, technique=label)
        if margin < -12:
            miss_category = {
                "jab": "jab_miss",
                "power_punch": "power_miss",
                "dirty_boxing": "dirty_boxing_miss",
                "ground_strikes": "ground_strikes_miss",
            }.get(action, "power_miss")
            return self.fight_phrase(miss_category, actor, defender)
        impact = max(1, round((margin + actor.power * 0.34 + 2.3) / 8.5 * self.engine_settings.get("damage", 1.0)))
        if action == "jab":
            impact = max(1, impact - 2)
        if action == "ground_strikes":
            impact = max(1, impact - 1)
            round_stats[self.fight_state_key(actor, state)]["control"] += 1
        clinch_detail = ""
        if action == "dirty_boxing":
            elbow = self.ds(actor, "elbows", 50)
            knee = self.ds(actor, "knees", 50)
            dirty = self.ds(actor, "dirty_boxing", actor.striking)
            weapon = self.weighted_choice({"elbow": elbow, "knee": knee, "punch": dirty})
            if weapon == "elbow":
                impact += 1
                cut_chance = max(0.04, (elbow + impact * 3 - self.ds(defender, "cut_immunity", 50)) / 180)
                if self.fight_mechanics_rng().random() < cut_chance:
                    state["cuts"][self.fight_state_key(defender, state)] += 1
                    self.record_structured_cut(defender, state, impact, weapon="elbow")
                    clinch_detail = self.fight_presentation_choice([
                        f"{actor.name} slices {defender.name} with a short elbow in the clinch; a cut opens.",
                        f"{actor.name} frames across the guard and an elbow opens a cut on {defender.name}.",
                        f"A compact elbow from {actor.name} splits the skin near {defender.name}'s eye.",
                        f"{actor.name} turns {defender.name} into the fence and lands a cutting elbow over the top.",
                    ])
                else:
                    clinch_detail = self.fight_presentation_choice([
                        f"{actor.name} lands a compact elbow over the top in the clinch.",
                        f"{actor.name} frames on the collarbone and clips {defender.name} with a short elbow.",
                        f"{actor.name} wins head position and sneaks an elbow across {defender.name}'s guard.",
                        f"{actor.name} lands the elbow on the break before {defender.name} can reset.",
                        f"{actor.name} pins one of {defender.name}'s arms and scores with the free elbow.",
                        f"{actor.name} turns inside the tie-up and lands an upward elbow through the middle.",
                    ])
            elif weapon == "knee":
                state["last_strike_target"] = "body"
                body_gain = max(2, round((knee + max(0, margin)) / 34))
                state["body"][self.fight_state_key(defender, state)] += body_gain
                state["gas"][self.fight_state_key(defender, state)] = max(3, state["gas"][self.fight_state_key(defender, state)] - body_gain)
                clinch_detail = self.fight_presentation_choice([
                    f"{actor.name} drives a knee into {defender.name}'s body and makes them fold their elbows in.",
                    f"{actor.name} pulls the head down and lands a straight knee through the centre.",
                    f"{actor.name} wins the collar tie and drives a knee beneath {defender.name}'s elbow.",
                    f"{actor.name} meets {defender.name}'s pummel with a short knee to the body.",
                    f"{actor.name} turns {defender.name} toward the fence and lands a knee before the break.",
                    f"{actor.name} creates just enough space in the clinch to spear the knee upstairs.",
                ])
            else:
                clinch_detail = self.fight_presentation_choice([
                    f"{actor.name} lands short punches while controlling the inside position.",
                    f"{actor.name} pins a wrist and works two compact punches with the free hand.",
                    f"{actor.name} sneaks an uppercut through the clinch before {defender.name} can pummel free.",
                    f"{actor.name} digs a hook to the body, then punches on the break.",
                    f"{actor.name} uses shoulder pressure to open a lane for dirty boxing.",
                    f"{actor.name} keeps forehead position and lands a tight pair of inside punches.",
                ])
        if action == "kick":
            state["body"][self.fight_state_key(defender, state)] += self.fight_mechanics_rng().randint(1, 4)
        state["damage"][self.fight_state_key(defender, state)] += impact
        damage_zone = "body" if action == "dirty_boxing" and weapon == "knee" else "head"
        if damage_zone == "head":
            head_trauma = state.setdefault("head_trauma", {key: 0 for key in state["head"]})
            state["head"][self.fight_state_key(defender, state)] += impact
            head_trauma[self.fight_state_key(defender, state)] += impact
        _attempts, landed = self.strike_volume(action, margin, landed=True, attempts=attempts)
        state["stats"][self.fight_state_key(actor, state)]["sig"] += landed
        round_stats[self.fight_state_key(actor, state)]["impact"] += impact
        if action == "power_punch" and self.fight_mechanics_rng().random() < self.flush_knockout_chance(actor, defender, self.ds(actor, "punch_power", actor.power), margin, self.ds(actor, "creative_punches", 50)):
            return self.deliver_flush_knockout(actor, defender, action, state, round_stats)
        if action == "dirty_boxing":
            clinch_power = self.ds_avg(actor, ("knees", "elbows"), actor.power)
            clinch_creativity = self.ds_avg(actor, ("knees", "elbows"), 50)
            if self.fight_mechanics_rng().random() < self.flush_knockout_chance(actor, defender, clinch_power, margin, clinch_creativity) * 0.7:
                return self.deliver_flush_knockout(actor, defender, "dirty_boxing", state, round_stats)
        if self.fight_mechanics_rng().random() < max(0.022, (impact + actor.power * 0.95 - defender.chin - self.ds(defender, "stun_recovery", defender.recovery) * 0.18) / 120):
            state["danger"][self.fight_state_key(actor, state)] += 8
            round_stats[self.fight_state_key(actor, state)]["danger"] += 8
            state["damage"][self.fight_state_key(defender, state)] += 8
            state[damage_zone][self.fight_state_key(defender, state)] += 8
            state["knockdowns"][self.fight_state_key(actor, state)] += 1
            state["finish_category"] = self.knockdown_finish_category(action, impact)
            clean_ko_chance = (max(0.04, min(0.58, (impact * 7.4 + actor.power - defender.chin - self.ds(defender, "stun_recovery", defender.recovery) * 0.25) / 112))
                               * self.competitive_finish_conversion(actor, defender))
            if action in ("power_punch", "dirty_boxing") and self.fight_mechanics_rng().random() < clean_ko_chance:
                detail = self.fight_phrase(state["finish_category"], actor, defender)
                state["instant_finish"] = (self.fight_state_key(actor, state), self.fight_state_key(defender, state), "KO", detail)
            return self.fight_phrase("knockdown", actor, defender, technique=self.action_label(action))
        cut_resistance = self.ds(defender, "cut_immunity", 50)
        if self.fight_mechanics_rng().random() < max(0.008, (impact - defender.toughness / 24 - cut_resistance / 55) / 46):
            state["cuts"][self.fight_state_key(defender, state)] += 1
            self.record_structured_cut(defender, state, impact, weapon=action)
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
        state["stats"][self.fight_state_key(actor, state)]["td_att"] += 1
        shot_speed = self.ds(actor, "takedown_speed", actor.wrestling)
        setup = self.ds(actor, "takedown_setup", actor.wrestling)
        sprawl = self.ds(defender, "sprawl", defender.takedown_defence)
        size_edge = (self.ds(actor, "natural_size", 50) - self.ds(defender, "natural_size", 50)) * 0.08
        margin += (shot_speed + setup - sprawl - self.ds(defender, "takedown_defence_detail", defender.takedown_defence)) * 0.12 + size_edge
        if margin > 8:
            state["stats"][self.fight_state_key(actor, state)]["td"] += 1
            state["position"] = "half guard" if self.ds(actor, "chain_wrestling", actor.wrestling) > self.ds(defender, "scrambles", defender.grappling) + self.fight_mechanics_rng().randint(-8, 12) else "guard"
            state["top"] = self.fight_state_key(actor, state)
            state["bottom"] = self.fight_state_key(defender, state)
            state["clinch_controller"] = None
            round_stats[self.fight_state_key(actor, state)]["control"] += 5
            if self.ds(actor, "slams", actor.wrestling) > 68 and self.fight_mechanics_rng().random() < 0.22:
                state["damage"][self.fight_state_key(defender, state)] += 3
                state["body"][self.fight_state_key(defender, state)] += 3
                round_stats[self.fight_state_key(actor, state)]["impact"] += 3
                return self.fight_phrase("slam_takedown", actor, defender, position=self.position_label(state["position"]))
            return self.fight_phrase("takedown_complete", actor, defender, position=self.position_label(state["position"]))
        if margin > -8:
            state["position"] = "cage"
            state["clinch_controller"] = self.fight_state_key(actor, state)
            round_stats[self.fight_state_key(actor, state)]["control"] += 2
            return self.fight_phrase("takedown_cage", actor, defender)
        extended_shot = (
            margin <= -35
            and self.ds(defender, "front_headlock", defender.wrestling)
            >= self.ds(actor, "takedown_setup", actor.wrestling) + 45
            and self.ds(defender, "sprawl", defender.takedown_defence)
            >= self.ds(actor, "chain_wrestling", actor.wrestling) + 35
        )
        if not extended_shot:
            self.set_fight_position(state, "range")
            round_stats[self.fight_state_key(defender, state)]["control"] += 2
            return self.fight_phrase("takedown_denied", actor, defender)
        defender_key = self.fight_state_key(defender, state)
        actor_key = self.fight_state_key(actor, state)
        self.set_fight_position(state, "failed shot", controller=defender_key)
        round_stats[defender_key]["control"] += 2
        return (
            f"{defender.name} sprawls on the extended shot while {actor.name} stays connected on the knees; "
            "the failed-shot scramble remains live."
        )

    def resolve_position_move(self, actor, defender, action, margin, state, round_stats):
        if action == "advance_position" and state["top"] == self.fight_state_key(actor, state):
            margin += (self.ds(actor, "transitions", actor.grappling) + self.ds(actor, "positional_ability", actor.grappling) - self.ds(defender, "guard_work", defender.grappling) - self.ds(defender, "scrambles", defender.grappling)) * 0.13
            if margin > 6:
                next_pos = {"guard": "half guard", "half guard": "side control", "side control": "mount", "mount": "back control"}.get(state["position"], "side control")
                if next_pos == "mount" and self.ds(actor, "back_control", actor.grappling) > self.ds(actor, "mount_control", actor.grappling) + 8 and self.fight_mechanics_rng().random() < 0.35:
                    next_pos = "back control"
                state["position"] = next_pos
                round_stats[self.fight_state_key(actor, state)]["control"] += 4
                round_stats[self.fight_state_key(actor, state)]["danger"] += 2
                return self.fight_phrase("pass", actor, defender, position=self.position_label(next_pos))
            round_stats[self.fight_state_key(actor, state)]["control"] += 1
            return self.fight_phrase("pass_denied", actor, defender)
        if action == "recover_guard":
            margin += (self.ds(actor, "guard_work", actor.grappling) + self.ds(actor, "flexibility", 50) - self.ds(defender, "ride_control", defender.ground_control) - self.ds(defender, "top_control", defender.ground_control)) * 0.1
            if margin > 8:
                state["position"] = "guard"
                round_stats[self.fight_state_key(actor, state)]["control"] += 2
                return self.fight_phrase("recover_guard", actor, defender)
            round_stats[self.fight_state_key(defender, state)]["control"] += 2
            return self.fight_phrase("hold_position", actor, defender)
        return None

    def resolve_submission(self, actor, defender, action, margin, state, round_stats):
        actor_key = self.fight_state_key(actor, state)
        defender_key = self.fight_state_key(defender, state)
        state["stats"][actor_key]["sub_att"] += 1
        sub_attack = self.skill_bundle(actor, "submission_game")
        sub_def = self.skill_bundle(defender, "submission_defence")
        technique = self.submission_technique(actor, action, state)
        state["last_submission_technique"] = dict(technique)
        leg_technique = any(token in technique["name"].lower() for token in (
            "heel", "knee", "ankle", "toe hold", "slicer", "cloverleaf",
        ))
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
            round_stats[self.fight_state_key(actor, state)]["danger"] += 14
            state["danger"][self.fight_state_key(actor, state)] += 14
            finish_boost = 1 + (self.ds(actor, "leg_locks", 50) - 50) / 750 if action == "bottom_submission" else 1
            hunter_boost = 1.12 if actor.behaviour == "Submission Hunter" else 1.0
            position_finish = 1.2 if state["position"] in ("mount", "back control") else 1.08 if state["position"] == "side control" else 0.92
            exhaustion_finish = 1 + max(0, 18 - state["gas"][self.fight_state_key(defender, state)]) / 100
            finish_chance = ((0.085 + max(0, margin + danger_bonus) / 240)
                             * finish_boost * hunter_boost * position_finish * exhaustion_finish
                             * self.engine_settings.get("submission_finish", 1.0)
                             * self.competitive_finish_conversion(actor, defender))
            if self.fight_mechanics_rng().random() < min(0.56, finish_chance):
                technical = technique["choke"] and self.fight_mechanics_rng().random() < max(0.08, (self.ds(defender, "toughness", defender.toughness) - self.ds(defender, "composure", defender.fight_iq)) / 360)
                state["submission_finish"] = (self.fight_state_key(actor, state), self.fight_state_key(defender, state), self.submission_finish_text(actor, defender, technique, technical), "Technical Submission" if technical else "Submission")
                return None
            state["gas"][self.fight_state_key(defender, state)] = max(5, state["gas"][self.fight_state_key(defender, state)] - 10)
            if (action == "bottom_submission" and leg_technique
                    and actor.trait == "Submission Ace"
                    and self.ds(actor, "leg_locks", 50) >= 88
                    and self.ds(actor, "leg_locks", 50)
                    >= self.ds(defender, "submission_defence_detail", defender.submission_defence) + 45
                    and margin + danger_bonus > 38
                    and state["position"] in ("guard", "half guard")):
                settled_position = state["position"]
                self.set_fight_position(
                    state, "leg entanglement", top=actor_key, bottom=defender_key,
                )
                state["last_submission_escape"] = {
                    "consequence": "knee line retained; leg entanglement established", "position": "leg entanglement",
                }
                return (
                    f"{actor.name} enters a leg entanglement around the {technique['name']}; "
                    f"{defender.name} clears the first grip but remains tied up after leaving {self.position_label(settled_position)}."
                )
            state["last_submission_escape"] = {
                "consequence": "late defense; position retained", "position": state["position"],
            }
            return self.fight_phrase("submission_danger", actor, defender)
        if margin > 0:
            round_stats[self.fight_state_key(actor, state)]["danger"] += 5
            state["last_submission_escape"] = {
                "consequence": "safe defense; position retained", "position": state["position"],
            }
            return self.fight_phrase("submission_threat", actor, defender)
        if action == "bottom_submission" and margin < -10:
            state["top"] = defender_key
            state["bottom"] = actor_key
            round_stats[self.fight_state_key(defender, state)]["control"] += 2
            state["last_submission_escape"] = {
                "consequence": "top control consolidated", "position": state["position"],
            }
            return f"{defender.name} shrugs off the submission attempt and settles back on top."
        if state["position"] in self.GROUND_POSITIONS:
            reversal = (
                margin < -16
                and defender.trait == "Scramble Artist"
                and self.ds(defender, "scrambles", defender.grappling)
                > self.ds(actor, "positional_ability", actor.grappling)
            )
            if reversal:
                self.set_fight_position(state, "guard", top=defender_key, bottom=actor_key)
                round_stats[defender_key]["control"] += 2
                state["last_submission_escape"] = {
                    "consequence": "reversal to top guard", "position": "guard",
                }
                return f"{defender.name} clears the submission and turns the escape into a reversal on top."
            guard_recovery = (
                margin <= -12
                and defender.trait in ("Scramble Artist", "Submission Ace")
                and self.ds(defender, "guard_work", defender.grappling)
                >= self.ds(actor, "top_control", actor.ground_control) + 8
            )
            if guard_recovery and state["position"] != "guard":
                self.set_fight_position(state, "guard", top=actor_key, bottom=defender_key)
                state["last_submission_escape"] = {
                    "consequence": "guard recovered", "position": state["position"],
                }
                return f"{defender.name} escapes the submission and recovers guard, conceding position but removing the danger."
            state["last_submission_escape"] = {
                "consequence": "grips cleared; position retained", "position": state["position"],
            }
            return f"{defender.name} clears the submission grips but remains in the same legal position."
        state["last_submission_escape"] = {
            "consequence": "safe escape to existing position", "position": state["position"],
        }
        return self.fight_phrase("submission_defended", actor, defender)

    def submission_technique(self, actor, action, state):
        position = state["position"]
        options = []

        def add(techniques):
            options.extend(techniques)

        if position == "leg entanglement":
            add([
                ("heel hook", False, 5), ("inside heel hook", False, 4),
                ("outside heel hook", False, 3), ("kneebar", False, 3),
                ("straight ankle lock", False, 3), ("toe hold", False, 2),
            ])
        if position == "back control":
            add([
                ("rear-naked choke", True, 8), ("short choke", True, 3), ("body-triangle rear-naked choke", True, 3),
                ("face-crank rear-naked choke", True, 2), ("bow-and-arrow choke", True, 2), ("back-control armbar", False, 2),
                ("twister", False, 1), ("neck crank", False, 1),
            ])
        if position in ("mount", "side control"):
            add([
                ("arm-triangle choke", True, 5), ("mounted arm-triangle", True, 3), ("Americana", False, 3),
                ("kimura", False, 3), ("straight armbar", False, 3), ("mounted triangle", True, 2),
                ("paper-cutter choke", True, 2), ("north-south choke", True, 2), ("Von Flue choke", True, 1),
                ("scarf-hold choke", True, 1), ("keylock", False, 2), ("shoulder lock", False, 1),
            ])
        if position in ("guard", "half guard") or action == "bottom_submission":
            add([
                ("guillotine choke", True, 4), ("high-elbow guillotine", True, 2), ("arm-in guillotine", True, 2),
                ("triangle choke", True, 4), ("reverse triangle", True, 2), ("buggy choke", True, 2),
                ("armbar", False, 4), ("belly-down armbar", False, 2), ("omoplata", False, 2),
                ("kimura", False, 3), ("D'Arce choke", True, 3), ("Brabo choke", True, 2),
                ("anaconda choke", True, 2), ("ninja choke", True, 2), ("Peruvian necktie", True, 1),
                ("Japanese necktie", True, 1), ("padlock choke", True, 1), ("Ezekiel choke", True, 1),
            ])
            if self.ds(actor, "leg_locks", 50) > 62:
                add([
                    ("heel hook", False, 3), ("inside heel hook", False, 3), ("outside heel hook", False, 2),
                    ("kneebar", False, 2), ("straight ankle lock", False, 2), ("toe hold", False, 2),
                    ("calf slicer", False, 1), ("knee slicer", False, 1), ("Texas cloverleaf", False, 1),
                ])
        if not options:
            options = [
                ("D'Arce choke", True, 3), ("Brabo choke", True, 2), ("kimura", False, 3),
                ("guillotine choke", True, 2), ("ninja choke", True, 2), ("front headlock choke", True, 2),
                ("Americana", False, 2), ("armbar", False, 2), ("wrist lock", False, 1),
            ]
        expanded = []
        for technique, choke, weight in options:
            expanded.extend([(technique, choke)] * weight)
        technique, choke = self.fight_mechanics_rng().choice(expanded)
        return {"name": technique, "choke": choke}

    def submission_finish_text(self, actor, defender, technique, technical=False):
        name = technique["name"]
        if technical:
            lines = self.fight_presentation_choice([
                [
                    f"{actor.name} locks the {name} and {defender.name} refuses to tap.",
                    f"The referee checks {defender.name}'s arm and receives no response.",
                    f"{actor.name} releases immediately as the referee stops it. Technical submission.",
                ],
                [
                    f"{actor.name} squeezes the {name} until {defender.name} goes limp instead of tapping.",
                    f"The official spots the loss of consciousness and rushes in.",
                    f"{actor.name} lets go at once as the technical submission is called.",
                ],
                [
                    f"{actor.name} tightens the {name} and {defender.name}'s defence fades away.",
                    f"The referee lifts {defender.name}'s hand, gets no response, and stops it.",
                    f"It goes down as a technical submission.",
                ],
                [
                    f"{actor.name} cinches the {name} while {defender.name} stubbornly refuses the tap.",
                    f"{defender.name} stops moving and the referee recognises the danger.",
                    f"The stoppage is immediate once {actor.name} releases.",
                ],
                [
                    f"{actor.name} keeps adjusting the {name} until {defender.name} is no longer responsive.",
                    f"The referee dives in before any extra damage can be done.",
                    f"Technical submission after a clean release from {actor.name}.",
                ],
                [
                    f"{actor.name} closes every escape route on the {name}.",
                    f"{defender.name} tries to ride it out but goes unconscious.",
                    f"The referee stops it as a technical submission.",
                ],
                [
                    f"{actor.name} locks hands on the {name} and waits out the final defence.",
                    f"{defender.name} refuses to concede and the choke takes over.",
                    f"The official waves it off when {defender.name} no longer responds.",
                ],
                [
                    f"{actor.name} forces the {name} deeper as {defender.name}'s arms slow down.",
                    f"The referee checks closely and sees {defender.name} is out.",
                    f"{actor.name} releases cleanly on the technical submission stoppage.",
                ],
            ])
            return " ".join(lines)
        setup = self.fight_presentation_choice([
            [
                f"{actor.name} creates the opening for the {name} and starts the attack.",
                f"{actor.name} improves the angle while {defender.name} fights the hands.",
            ],
            [
                f"{actor.name} chains into the {name} during a scramble.",
                f"{defender.name} tries to roll through, but {actor.name} follows the hips.",
                f"The pressure keeps building as the escape route closes.",
            ],
            [
                f"{actor.name} attacks the {name} in transition.",
                f"{defender.name} tries to peel the grip and turn out, but {actor.name} stays attached.",
            ],
            [
                f"{actor.name} patiently works toward the {name}.",
                f"{defender.name} survives the first squeeze but cannot clear the lock.",
            ],
            [
                f"{actor.name} catches {defender.name} reaching and clamps down on the {name}.",
                f"{defender.name} bridges hard, but the leverage is wrong.",
            ],
            [
                f"{actor.name} sets a trap and turns it into the {name}.",
                f"{defender.name} recognises it too late and runs out of escape room.",
            ],
            [
                f"{actor.name} follows the scramble straight into the {name}.",
                f"{defender.name} posts and twists, but {actor.name} keeps the finishing angle.",
            ],
            [
                f"{actor.name} hides the setup until the {name} is already locked.",
                f"{defender.name} hand-fights desperately but cannot break the grip.",
            ],
        ])
        return " ".join([
            *setup,
            self.fight_phrase("submission_finish", actor, defender, technique=name),
        ])

    def cut_medical_evidence(self, fighter, state):
        cuts = list(state.get("cut_state", {}).get(self.fight_state_key(fighter, state), []) or [])
        if not cuts:
            return {"count": 0, "max_severity": 0, "max_bleeding": 0,
                    "max_swelling": 0, "vision_risk": False, "worst_location": ""}
        worst = max(cuts, key=lambda cut: (cut.get("vision_risk", False), cut.get("severity", 0), cut.get("bleeding", 0)))
        return {
            "count": len(cuts), "max_severity": max(cut.get("severity", 0) for cut in cuts),
            "max_bleeding": max(cut.get("bleeding", 0) for cut in cuts),
            "max_swelling": max(cut.get("swelling", 0) for cut in cuts),
            "vision_risk": any(cut.get("vision_risk", False) for cut in cuts),
            "worst_location": worst.get("location", "facial cut"),
        }

    @staticmethod
    def doctor_stoppage_window(state, cut_evidence):
        """Return whether a between-round medical inspection is warranted."""
        between_rounds = state.get("tick", 0) >= state.get("ticks_per_round", 0)
        serious_cut = (
            cut_evidence.get("count", 0) >= 3
            and (cut_evidence.get("max_bleeding", 0) >= 3 or cut_evidence.get("vision_risk", False))
        )
        return bool(between_rounds and serious_cut)

    def check_fight_stoppage(self, actor, defender, state):
        technical = self.technical_foul_outcome(actor, defender, state)
        if technical:
            return technical
        if "instant_finish" in state:
            winner_name, loser_name, method, detail = state.pop("instant_finish")
            winner = actor if self.fight_state_key(actor, state) == winner_name else defender
            loser = actor if self.fight_state_key(actor, state) == loser_name else defender
            return winner, loser, method, self.finish_sequence(winner, loser, method, detail, state)
        if "submission_finish" in state:
            winner_name, loser_name, detail, method = state["submission_finish"]
            winner = actor if self.fight_state_key(actor, state) == winner_name else defender
            loser = actor if self.fight_state_key(actor, state) == loser_name else defender
            return winner, loser, method, self.finish_sequence(winner, loser, method, detail, state)
        for fighter, opponent in ((actor, defender), (defender, actor)):
            damage = state["hurt"][self.fight_state_key(fighter, state)]
            gas = state["gas"][self.fight_state_key(fighter, state)]
            body = state["body"][self.fight_state_key(fighter, state)]
            leg = state.get("leg", {}).get(self.fight_state_key(fighter, state), 0)
            cuts = state["cuts"][self.fight_state_key(fighter, state)]
            cut_evidence = self.cut_medical_evidence(fighter, state)
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
            # Knockdowns are stored under the scorer.  Stoppage logic needs the
            # number this fighter has suffered, therefore read the opponent's KD.
            knockdowns = state["knockdowns"].get(self.fight_state_key(opponent, state), 0)
            unanswered = state["unanswered"].get(self.fight_state_key(fighter, state), 0)
            ref_mod = self.referee_profile(state)["stoppage_modifier"]
            pacing_mod = (-0.08 if state.get("championship_pacing") else 0) + (-0.145 if championship_late else 0)
            low_mod = low_level_chaos * 0.065
            elite_mod = -elite_control * 0.16
            finish_conversion = self.competitive_finish_conversion(opponent, fighter)
            ko_chance = ((0.108 + low_mod + pacing_mod + elite_mod + (damage - ko_threshold) / 240 + finisher_bonus * 1.08 + exhaustion_bonus + knockdowns * 0.085 + ref_mod)
                         * self.engine_settings.get("ko_power", 1.0) * finish_conversion)
            if damage > ko_threshold and self.fight_officiating_rng().random() < ko_chance:
                clean = knockdowns >= 1 and unanswered < 5 and self.fight_officiating_rng().random() < 0.88
                method = "KO" if clean else "TKO"
                detail = self.finish_strike_text(opponent, fighter, state, clean=clean)
                return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, detail, state)
            unanswered_trigger = 5 if low_level_chaos >= 0.08 else 6
            unanswered_chance = ((0.07 + ref_mod + unanswered * 0.014 + low_level_chaos * 0.035 - elite_control * 0.105
                                  + (-0.06 if state.get("championship_pacing") else 0) + (-0.115 if championship_late else 0))
                                 * finish_conversion)
            if unanswered >= unanswered_trigger and (damage > fighter.toughness * (0.58 if low_level_chaos >= 0.08 else 0.62) or gas < 20) and self.fight_officiating_rng().random() < unanswered_chance:
                method = "TKO"
                category = "ground_tko" if state["position"] in ("guard", "half guard", "side control", "mount", "back control") else "standing_tko"
                detail = self.fight_phrase(category, opponent, fighter)
                return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, detail, state)
            # Doctors assess accumulated facial damage during a real break in
            # the action. Checking on every exchange turned an ordinary two-cut
            # fight into dozens of independent stoppage rolls. Three visible
            # cuts and a between-round inspection are now required; severe cuts
            # retain a meaningful chance without crowding out normal decisions.
            doctor_chance = (0.018 + cuts * 0.008
                             + cut_evidence["max_severity"] * 0.006
                             + cut_evidence["max_bleeding"] * 0.004
                             + (0.018 if cut_evidence["vision_risk"] else 0)
                             - self.ds(fighter, "cut_immunity", 50) / 1700
                             + max(0, damage - fighter.toughness * 0.82) / 700
                             + max(0, state["danger"][self.fight_state_key(opponent, state)] - 18) / 900
                             + max(0, ref_mod) * 0.25)
            doctor_ready = self.doctor_stoppage_window(state, cut_evidence)
            if doctor_ready and self.fight_officiating_rng().random() < max(0.008, min(0.16, doctor_chance)):
                state["finish_category"] = (
                    f"doctor:{cut_evidence['worst_location']}:severity-{cut_evidence['max_severity']}"
                    f":bleeding-{cut_evidence['max_bleeding']}:vision-{int(cut_evidence['vision_risk'])}"
                )
                detail = (
                    f"{self.fight_phrase('doctor', opponent, fighter)} "
                    f"Medical evidence: {cut_evidence['worst_location']}, severity "
                    f"{cut_evidence['max_severity']}, bleeding {cut_evidence['max_bleeding']}."
                )
                return opponent, fighter, "Doctor Stoppage", self.finish_sequence(opponent, fighter, "Doctor Stoppage", detail, state)
            if body > 24 and self.fight_officiating_rng().random() < max(0.05, (body - 18) / 130 + ref_mod):
                method = "Injury Stoppage"
                return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, self.fight_phrase("injury_stoppage", opponent, fighter), state)
            if leg > 29 and self.fight_officiating_rng().random() < max(0.02, (leg - 24) / 150 + ref_mod):
                method = "Injury Stoppage"
                detail = (
                    f"{self.fight_phrase('injury_stoppage', opponent, fighter)} "
                    f"The referee confirms {fighter.name} cannot safely bear weight on the leg."
                )
                return opponent, fighter, method, self.finish_sequence(opponent, fighter, method, detail, state)
            if gas < 10 and damage > fighter.toughness * 0.78 and self.fight_officiating_rng().random() < max(0.025, 0.12 - self.ds(fighter, "resilience", fighter.toughness) / 760 + max(0, 8 - gas) / 150):
                return opponent, fighter, "TKO", self.finish_sequence(opponent, fighter, "TKO", self.fight_phrase("fatigue_tko", opponent, fighter), state)
        return None

    def causal_finish_event(self, winner, state):
        """Return the latest winner-authored exchange with causal finish evidence."""
        winner_key = self.fight_state_key(winner, state) if state.get("fighter_keys") else ""
        excluded = ("composed_survival", "stand_up", "transition", "shot_entry")
        finish_round = int(state.get("round", 0) or 0)
        finish_tick = int(state.get("tick", 0) or 0)
        for event in reversed(state.get("trace", []) or []):
            if event.get("type") != "exchange":
                continue
            if winner_key and event.get("actor") != winner_key:
                continue
            event_round = int(event.get("round", 0) or 0)
            event_tick = int(event.get("tick", 0) or 0)
            if finish_round and event_round and event_round != finish_round:
                continue
            if finish_tick and event_tick and finish_tick - event_tick > 3:
                continue
            move_id = str(event.get("move_id") or "").casefold()
            action = str(event.get("action") or "").casefold()
            move_tags = {
                str(tag).casefold()
                for tag in ((event.get("move", {}) or {}).get("tags", ()) or ())
            }
            flags = event.get("flags", {}) or {}
            defender_key = event.get("defender")
            damage = float((event.get("damage_delta", {}) or {}).get(defender_key, 0) or 0)
            hurt = float((event.get("hurt_delta", {}) or {}).get(defender_key, 0) or 0)
            knockdowns = int((event.get("knockdown_delta", {}) or {}).get(event.get("actor"), 0) or 0)
            striking_impact = int(event.get("sig_delta", 0) or 0) > 0 and (
                float((event.get("round_metric_delta", {}) or {}).get(event.get("actor"), {}).get("impact", 0) or 0) > 0
                or damage > 0 or hurt > 0
            )
            causal = bool(flags.get("knockdown") or flags.get("hurt") or knockdowns or damage > 0 or hurt > 0 or striking_impact)
            if not causal:
                continue
            if any(term in move_id or term in action for term in excluded) and not (flags.get("knockdown") or knockdowns):
                continue
            if ("entry" in move_id or "shot" in move_id or "entry" in move_tags) and not (
                    flags.get("knockdown") or knockdowns or move_tags.intersection({"slam", "suplex"})):
                continue
            return event
        return None

    def finish_strike_text(self, winner, loser, state, clean=False):
        causal_event = self.causal_finish_event(winner, state)
        payload = (causal_event or {}).get("move", {}) or {}
        move_name = str(payload.get("name") or "").strip()
        target = str(payload.get("target") or "").strip()
        if move_name:
            target_copy = f" to the {target}" if target and target.casefold() not in move_name.casefold() else ""
            if clean:
                return f"{winner.name} lands the {move_name}{target_copy} clean and sends {loser.name} down."
            position = self.position_label(state.get("position", "range")).lower()
            return f"{winner.name} keeps the offense coming with the {move_name}{target_copy} from {position}."
        if clean:
            return f"{winner.name} lands the decisive offense and {loser.name} cannot recover."
        return f"{winner.name}'s unanswered offense forces the stoppage."

    def finish_sequence(self, winner, loser, method, detail, state):
        """Build one continuous finish from the current move and position."""
        causal_event = self.causal_finish_event(winner, state) if method in ("KO", "TKO") else None
        if method in ("KO", "TKO"):
            payload = (causal_event or {}).get("move", {}) or {}
        else:
            payload = state.get("last_move_payload") or {}
        move_name = str(payload.get("name") or "").strip()
        target = str(payload.get("target") or "").strip()
        position = self.position_label(state.get("position", "range")).lower()
        target_copy = f" to the {target}" if target and target.casefold() not in move_name.casefold() else ""
        authored = str(detail or "").strip()

        if method == "KO" and move_name:
            action = f"{winner.name} lands the {move_name}{target_copy} flush and {loser.name} cannot recover."
            if state.get("finish_category") == "walkoff_ko":
                action += f" {winner.name} sees it immediately and walks away before {loser.name} hits the canvas."
        elif method == "TKO" and move_name:
            action = (
                f"{winner.name} keeps the {move_name}{target_copy} coming from {position}; "
                f"{loser.name} can no longer answer the attack."
            )
        elif method in ("KO", "TKO") and authored:
            action = authored
            if move_name and move_name.casefold() not in authored.casefold():
                action += f" The finishing exchange is driven by the {move_name}{target_copy} from {position}."
        elif method == "KO":
            action = f"{winner.name} lands the decisive offense and {loser.name} cannot recover."
        elif method == "TKO":
            action = f"{winner.name}'s unanswered offense forces the stoppage."
        elif method in SUBMISSION_METHODS:
            action = authored
            if not action and move_name:
                ending = "the referee intervenes before an injury" if method == "Technical Submission" else f"{loser.name} taps"
                action = f"{winner.name} secures the {move_name} from {position}; {ending}."
        else:
            action = authored

        parts = [action] if action else []
        if method == "KO":
            parts.append("The referee waves the fight off immediately.")
        elif method == "TKO":
            parts.append(f"The referee steps between the fighters and stops {loser.name} from taking further damage.")
        elif method == "Technical Submission" and "referee" not in action.lower():
            parts.append("The referee stops the contest.")
        official_markers = ("official result", "official time", "declared the winner", "announcement confirms")
        if not any(marker in action.casefold() for marker in official_markers):
            official = (
                f"Official result: {winner.name} defeats {loser.name} by {method} at "
                f"{state.get('official_time', '0:00')} of round {state.get('round', 1)}."
            )
            parts.append(official)
        state["finish_detail"] = action
        return " ".join(parts)

    def stoppage_review_from_evidence(self, loser, method, state):
        """Flag unusual stoppage timing for review without changing the official result."""
        if method not in ("TKO", "Doctor Stoppage", "Corner Stoppage") or loser is None:
            return None
        loser_key = self.fight_state_key(loser, state)
        opponent_key = "b" if loser_key == "a" else "a"
        evidence = {
            "hurt": round(state.get("hurt", {}).get(loser_key, 0), 2),
            "knockdowns": int(state.get("knockdowns", {}).get(opponent_key, 0)),
            "unanswered": int(state.get("unanswered", {}).get(loser_key, 0)),
            "cuts": int(state.get("cuts", {}).get(loser_key, 0)),
            "referee": state.get("referee", "standard"),
        }
        flag = ""
        if method == "TKO" and evidence["hurt"] < 45 and evidence["knockdowns"] == 0 and evidence["unanswered"] < 6:
            flag = "unusually early"
        elif (evidence["hurt"] >= 90 or evidence["knockdowns"] >= 3 or evidence["unanswered"] >= 12):
            flag = "unusually late"
        return {"flag": flag, "evidence": evidence} if flag else None

    def round_evidence_from_trace(self, state, round_no):
        """Aggregate one round using only recorded exchange evidence."""
        evidence = {
            key: {
                "impact": 0, "danger": 0, "control": 0, "control_ticks": 0,
                "attempts": 0, "effective_actions": 0, "knockdowns": 0,
                "submission_attempts": 0, "takedowns": 0, "dominant_moments": 0,
                "move_families": {}, "effective_families": {}, "sequence_follow_ups": 0,
            }
            for key in ("a", "b")
        }
        for event in state.get("trace", []):
            if event.get("type") != "exchange" or event.get("round") != round_no:
                continue
            actor = event.get("actor")
            defender = event.get("defender")
            for key in ("a", "b"):
                metric = event.get("round_metric_delta", {}).get(key, {})
                evidence[key]["impact"] += max(0, metric.get("impact", 0))
                evidence[key]["danger"] += max(0, metric.get("danger", 0))
                evidence[key]["control"] += max(0, metric.get("control", 0))
                evidence[key]["control_ticks"] += max(0, event.get("control_delta", {}).get(key, 0))
            if actor not in evidence or defender not in evidence:
                continue
            attempts = event.get("sig_att_delta", 0) + event.get("td_att_delta", 0) + event.get("sub_att_delta", 0)
            evidence[actor]["attempts"] += max(0, attempts)
            evidence[actor]["submission_attempts"] += max(0, event.get("sub_att_delta", 0))
            evidence[actor]["takedowns"] += max(0, event.get("td_delta", 0))
            family = str(event.get("move_family", "Other") or "Other")
            evidence[actor]["move_families"][family] = evidence[actor]["move_families"].get(family, 0) + 1
            evidence[actor]["sequence_follow_ups"] += int(
                bool(event.get("move_sequence", {}).get("completed_follow_up"))
            )
            if event.get("outcome") in ("landed", "knockdown", "takedown", "submission_attempt", "position_change"):
                evidence[actor]["effective_actions"] += 1
                evidence[actor]["effective_families"][family] = (
                    evidence[actor]["effective_families"].get(family, 0) + 1
                )
            # Knockdowns are credited to the scoring actor, just like the
            # cumulative state and public box score.
            knockdowns = max(0, event.get("knockdown_delta", {}).get(actor, 0))
            evidence[actor]["knockdowns"] += knockdowns
            danger_gain = event.get("round_metric_delta", {}).get(actor, {}).get("danger", 0)
            if knockdowns or danger_gain >= 5:
                evidence[actor]["dominant_moments"] += 1
        return evidence

    def score_round(self, a, b, round_stats, state, judge=None):
        """Apply the MMA judging hierarchy to trace-backed round evidence."""
        del round_stats  # Compatibility input; trace evidence is authoritative.
        round_no = int(state.get("round", 1))
        evidence = self.round_evidence_from_trace(state, round_no)
        a_key, b_key = self.fight_state_key(a, state), self.fight_state_key(b, state)
        profile = (judge or {}).get("profile", "Balanced")
        danger_weight = 2.15 if profile == "Damage-first" else 1.9 if profile == "Control-sensitive" else 2.0

        def primary(key):
            row = evidence[key]
            return (row["impact"] + row["danger"] * danger_weight
                    + row["knockdowns"] * 9 + row["submission_attempts"] * 2.5
                    + row["takedowns"] * 1.25)

        a_primary, b_primary = primary(a_key), primary(b_key)
        primary_gap = a_primary - b_primary
        if (a_primary == b_primary == 0
                and evidence[a_key]["attempts"] == evidence[b_key]["attempts"]
                and evidence[a_key]["control_ticks"] == evidence[b_key]["control_ticks"]):
            return None, None, 10
        # Ordinary variance exists only where the effective offense is close.
        ambiguity_band = max(2, 5 * self.engine_settings.get("decision_noise", 1.0))
        if abs(primary_gap) <= ambiguity_band:
            primary_gap += self.fight_judging_rng().uniform(-1.6, 1.6)

        if abs(primary_gap) > 2.0:
            winner_key = a_key if primary_gap > 0 else b_key
        else:
            aggression_gap = (evidence[a_key]["effective_actions"] + evidence[a_key]["attempts"] * 0.12
                              - evidence[b_key]["effective_actions"] - evidence[b_key]["attempts"] * 0.12)
            if abs(aggression_gap) > 1.0:
                winner_key = a_key if aggression_gap > 0 else b_key
            else:
                control_gap = ((evidence[a_key]["control"] - evidence[b_key]["control"])
                               + (evidence[a_key]["control_ticks"] - evidence[b_key]["control_ticks"]) * 0.7)
                if abs(control_gap) > 1.5:
                    winner_key = a_key if control_gap > 0 else b_key
                elif abs(primary_gap) < 0.45 and abs(aggression_gap) < 0.45 and abs(control_gap) < 0.75:
                    return None, None, 10
                else:
                    lean = primary_gap + aggression_gap * 0.35 + control_gap * 0.12
                    winner_key = a_key if lean >= 0 else b_key

        winner, loser = (a, b) if winner_key == a_key else (b, a)
        loser_key = b_key if winner_key == a_key else a_key
        winner_row, loser_row = evidence[winner_key], evidence[loser_key]
        winner_primary, loser_primary = primary(winner_key), primary(loser_key)
        severe_advantage = (
            winner_primary >= loser_primary + 30
            and winner_row["danger"] >= loser_row["danger"] + 10
            and (winner_row["knockdowns"] > loser_row["knockdowns"]
                 or winner_row["dominant_moments"] >= loser_row["dominant_moments"] + 2)
        )
        score = 8 if severe_advantage else 9
        return winner, loser, score

    def action_label(self, action):
        variants = {
            "jab": ["clean straight shots", "a sharp one-two", "a crisp jab-cross", "fast straight punches"],
            "power_punch": ["a heavy power punch", "a looping right hand", "a hard counter", "a loaded hook"],
            "kick": ["a kick to the body and leg", "a thudding body kick", "a chopping low kick", "a quick high-low kick sequence"],
            "dirty_boxing": ["short clinch punches", "inside uppercuts", "shoulder-pressure boxing", "short punches in the tie-up"],
            "ground_strikes": ["ground-and-pound", "short punches from top", "elbows from top control", "heavy shots on the mat"],
        }
        return self.fight_presentation_choice(variants.get(action, [action.replace("_", " ")]))

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
        fighter_styles = self.fighter_styles(fighter)
        opponent_styles = self.fighter_styles(opponent)
        edge = table.get((fighter_styles[0], opponent_styles[0]), 0)
        edge -= table.get((opponent_styles[0], fighter_styles[0]), 0) / 2
        if len(fighter_styles) > 1:
            edge += table.get((fighter_styles[1], opponent_styles[0]), 0) * 0.35
            edge -= table.get((opponent_styles[0], fighter_styles[1]), 0) * 0.175
        if len(opponent_styles) > 1:
            edge += table.get((fighter_styles[0], opponent_styles[1]), 0) * 0.175
            edge -= table.get((opponent_styles[1], fighter_styles[0]), 0) * 0.35
        return edge
