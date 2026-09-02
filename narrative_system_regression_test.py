"""Focused regressions for bounded, event-driven narrative story threads."""

import inspect
import random
import tkinter as tk
import time
from copy import deepcopy
from dataclasses import replace
from unittest.mock import patch

from constants import STORY_THREAD_ACTIVE_BEAT_LIMIT, STORY_THREAD_ACTIVE_LIMIT
from main import FightEmpireApp


def require(condition, message):
    if not condition:
        raise AssertionError(message)


def same_division_pair(app):
    divisions = {}
    for fighter in app.roster:
        divisions.setdefault((fighter.gender, fighter.weight), []).append(fighter)
    return next((fighters[:2] for fighters in divisions.values() if len(fighters) >= 2), None)


def main():
    root = tk.Tk()
    root.withdraw()
    callback_errors = []
    root.report_callback_exception = lambda _exc, value, _tb: callback_errors.append(value)
    try:
        app = FightEmpireApp(root, startup_progress=lambda _value, _text: None)
        pair = same_division_pair(app)
        require(pair, "The seeded player roster has no same-division narrative test pair.")
        a, b = pair
        for fighter in (a, b):
            fighter.rival = ""
            fighter.rival_fighter_id = ""
            fighter.rivalry_heat = 0
            fighter.rivalry_origin = ""
            fighter.rivalry_rematch_due = False

        # Narrative tracking is event-driven and must not consume the simulation
        # RNG merely to assign IDs or retain presentation text.
        rng_before = random.getstate()
        require(app.establish_rivalry(a, b, "Narrative regression callout", heat=55),
                "A valid rivalry was not established.")
        require(random.getstate() == rng_before,
                "Creating a story thread consumed the shared simulation RNG.")

        story_key = app.rivalry_story_key(a, b)
        thread = app.story_thread(story_key)
        require(thread and thread["type"] == "Rivalry" and thread["phase"] == "emerging",
                "Rivalry creation did not create an indexed emerging story.")
        require(thread["fighter_ids"] == [a.fighter_id, b.fighter_id],
                "Story participants were not stored by stable fighter ID.")
        require(thread in app.story_threads_for_fighter(a) and thread in app.story_threads_for_fighter(b),
                "The direct participant index did not expose the rivalry on both fighter profiles.")
        require(len(thread["beats"]) == 1 and thread["beats"][0]["kind"] == "origin",
                "The rivalry origin was not retained as the first story beat.")

        # Replayed callbacks may update heat twice, but their stable narrative
        # event reference must not duplicate the beat.
        app.build_rivalry_heat(a, b, 5, note="The press conference escalated the feud.")
        beat_count = len(app.story_thread(story_key)["beats"])
        app.build_rivalry_heat(a, b, 5, note="The press conference escalated the feud.")
        require(len(app.story_thread(story_key)["beats"]) == beat_count,
                "The same event reference duplicated a narrative beat.")

        # Duplicate display names must not enter the thread or context identity.
        duplicate = replace(b, fighter_id=f"{b.fighter_id}-duplicate")
        app.roster.append(duplicate)
        require(duplicate.fighter_id not in app.story_thread(story_key)["fighter_ids"],
                "A same-name fighter inherited another fighter's story identity.")
        app.roster.remove(duplicate)

        # A decisive outcome settles a cooled feud, creates a public Chronicle
        # payoff, and keeps both durable participant IDs.
        with patch("world.random.randint", return_value=48):
            app.resolve_rivalry_result(a, b, {"main": True, "title": False}, "Submission")
        thread = app.story_thread(story_key)
        require(thread["status"] == "resolved" and thread["phase"] == "settled" and thread["resolution"],
                "A decisive rivalry result did not resolve the story thread.")
        public = app.world_chronicle[0]
        require(public["type"] == "Rivalry" and public.get("story_id") == thread["story_id"],
                "The rivalry payoff was not linked into the World Chronicle.")
        require(public.get("fighter_ids") == [a.fighter_id, b.fighter_id],
                "The public rivalry payoff lost stable participant identity.")

        # Title-chase, reign, and redemption chapters reuse direct fighter keys
        # and advance only when their owning result is reported.
        company = app.player_company_name
        app.record_title_chase_story(company, a, b, "Regression contender surge")
        chase_key = app.title_chase_story_key(company, a)
        require(app.story_thread(chase_key)["phase"] == "contender",
                "A contender surge did not open a title-chase story.")
        title_rng_before = random.getstate()
        app.record_title_story_result(
            company, a, b, "Decision", defense=False, loser_was_champion=True,
            title_label=f"{a.gender} {a.weight} championship",
        )
        require(random.getstate() == title_rng_before,
                "Title-story recording consumed the shared simulation RNG.")
        require(app.story_thread(chase_key)["status"] == "resolved",
                "Winning a championship did not resolve the fighter's title chase.")
        require(app.story_thread(app.title_reign_story_key(company, a))["status"] == "active",
                "A championship win did not begin the winner's reign story.")
        require(app.story_thread(app.title_reign_story_key(company, b))["status"] == "resolved",
                "A championship loss did not close the former champion's reign story.")

        app.record_redemption_story_result(
            company, a, b, "Decision", {"title": True}, loser_was_champion=True,
        )
        redemption_key = app.redemption_story_key(b)
        require(app.story_thread(redemption_key)["status"] == "active",
                "A title loss did not open a redemption story.")
        app.record_redemption_story_result(
            company, b, a, "TKO", {"main": True}, loser_was_champion=False,
        )
        require(app.story_thread(redemption_key)["status"] == "resolved",
                "A meaningful comeback win did not resolve the redemption story.")

        # Serious injuries now form a complete treatment-to-return story using
        # the existing medical and result events rather than a recovery scan.
        a.serious_injury = ""
        a.serious_injury_pending = False
        a.serious_injury_history = []
        a.injured = 0
        with (
            patch("world.random.choice", side_effect=lambda values: values[0]),
            patch("world.random.randint", return_value=7),
            patch("world.random.sample", return_value=[]),
        ):
            require(app.apply_serious_injury(a, "narrative regression"),
                    "A serious injury did not create its domain state.")
        injury_key = app.injury_story_key(a)
        require(app.story_thread(injury_key)["phase"] == "decision_required",
                "A player serious injury did not open a medical decision story.")
        with patch("world.random.randint", return_value=1):
            require(app.resolve_serious_injury(a, "surgery"),
                    "The serious-injury treatment decision failed.")
        require(app.story_thread(injury_key)["phase"] == "surgical_recovery",
                "Surgery did not advance the injury story into recovery.")
        a.injured = 0
        completed = a.serious_injury
        a.serious_injury = ""
        a.serious_injury_history.append(f"Month {app.month}: Cleared to return after {completed.lower()}.")
        app.upsert_story_thread(
            injury_key, "Injury Comeback", status="active", phase="return_pending",
            importance=4, fighters=[a], companies=[company], beat_kind="medical_clearance",
            beat_ref=f"{injury_key}:test-clearance", summary=f"{a.name} was medically cleared.",
            stakes="The first fight back will determine the competitive meaning of the recovery.",
        )
        app.record_redemption_story_result(company, a, b, "Decision", {"main": True})
        require(app.story_thread(injury_key)["status"] == "resolved",
                "The first fight back did not resolve the injury-comeback story.")

        app.record_comeback_contract_story(a, farewell=False, fights=2, company=company)
        comeback_key = app.comeback_story_key(a)
        a.guaranteed_fights = 2
        a.contract_fights_completed = 2
        a.comeback_contract = False
        app.record_comeback_fight_result(company, a, b, True, "Decision")
        require(app.story_thread(comeback_key)["phase"] == "commitment_complete",
                "Completing guaranteed comeback fights did not advance the comeback story.")

        # Retirement decisions now retain the opponent and final result rather
        # than becoming an isolated generic retirement headline.
        farewell_fighter = replace(
            a, name="Farewell Veteran", fighter_id=f"{a.fighter_id}-farewell",
            rival="Farewell Rival", rival_fighter_id=f"{b.fighter_id}-farewell-rival",
            friend="", friend_fighter_id="", farewell_story_key="",
            retirement_pending=False, retired=False, retirement_requested_month=0,
            guaranteed_fights=0, contract_fights_completed=0, fight_history=[],
            bout_rating_history=[], career_arc=None, career_arc_history=[],
        )
        farewell_rival = replace(
            b, name="Farewell Rival", fighter_id=f"{b.fighter_id}-farewell-rival",
            rival="Farewell Veteran", rival_fighter_id=farewell_fighter.fighter_id,
            friend="", friend_fighter_id="", farewell_story_key="",
            retirement_pending=False, retired=False, fight_history=[], bout_rating_history=[],
        )
        ordinary_opponent = replace(
            b, name="Ordinary Farewell Opponent", fighter_id=f"{b.fighter_id}-farewell-ordinary",
            rival="", rival_fighter_id="", friend="", friend_fighter_id="",
            farewell_story_key="", retirement_pending=False, retired=False,
            fight_history=[], bout_rating_history=[],
        )
        app.roster.extend([farewell_fighter, farewell_rival, ordinary_opponent])
        farewell_rng = random.getstate()
        app.mark_retirement_fight_required(farewell_fighter, "Narrative regression career review")
        farewell_key = farewell_fighter.farewell_story_key
        farewell = app.story_thread(farewell_key)
        require(farewell and farewell["type"] == "Career Farewell"
                and farewell["phase"] == "final_fight_requested",
                "A retirement decision did not open a direct Career Farewell chapter.")
        require(random.getstate() == farewell_rng,
                "Opening a Career Farewell consumed simulation RNG.")
        farewell_beats = len(farewell["beats"])
        app.mark_retirement_fight_required(farewell_fighter, "Narrative regression career review")
        require(len(app.story_thread(farewell_key)["beats"]) == farewell_beats,
                "Repeating the retirement callback duplicated the farewell origin.")
        require("career rival" in app.fight_story_summary(
            farewell_fighter, farewell_rival, {"main": True},
        ).lower(), "Fight context did not frame a career-rival farewell.")
        rival_score, rival_connection = app.farewell_matchup_score(farewell_fighter, farewell_rival)
        ordinary_score, _ordinary_connection = app.farewell_matchup_score(farewell_fighter, ordinary_opponent)
        require(rival_connection["kind"] == "rivalry" and rival_score < ordinary_score,
                "The existing candidate scorer did not prefer a credible career-rival farewell.")
        duplicate_farewell_name = replace(
            farewell_fighter, fighter_id=f"{farewell_fighter.fighter_id}-duplicate",
            farewell_story_key="", retirement_pending=False,
        )
        require(app.story_thread(farewell_key) not in app.story_threads_for_fighter(duplicate_farewell_name),
                "A same-name fighter inherited another fighter's farewell story.")
        history_owner = replace(
            farewell_fighter, fighter_id=f"{farewell_fighter.fighter_id}-history-owner",
            rival="", rival_fighter_id="", farewell_story_key="", retirement_pending=False,
            bout_rating_history=[{
                "opponent_id": farewell_rival.fighter_id,
                "opponent_name": farewell_rival.name, "result": "W",
            }],
        )
        same_name_stranger = replace(
            farewell_rival, fighter_id=f"{farewell_rival.fighter_id}-same-name-stranger",
            rival="", rival_fighter_id="",
        )
        require(app.farewell_prior_meetings(history_owner, farewell_rival) == 1
                and app.farewell_prior_meetings(history_owner, same_name_stranger) == 0,
                "Farewell history treated a same-name stranger as a former opponent.")
        app.record_farewell_fight_story(
            company, farewell_fighter, farewell_rival, "Decision", {"main": True},
        )
        farewell = app.story_thread(farewell_key)
        require(farewell["status"] == "resolved" and farewell["phase"] == "farewell_win"
                and farewell["opponent_id"] == farewell_rival.fighter_id
                and farewell["opponent_connection"] == "rivalry",
                "The final result did not preserve the opponent and rivalry meaning.")
        require(farewell in app.story_threads_for_fighter(farewell_rival),
                "The final opponent could not see the shared farewell chapter.")
        farewell_beat_count = len(farewell["beats"])
        farewell_chronicle_count = len(app.world_chronicle)
        app.record_farewell_fight_story(
            company, farewell_fighter, farewell_rival, "Decision", {"main": True},
        )
        require(len(app.story_thread(farewell_key)["beats"]) == farewell_beat_count
                and len(app.world_chronicle) == farewell_chronicle_count,
                "Replaying a farewell result duplicated its beat or Chronicle payoff.")

        legacy_farewell = replace(
            ordinary_opponent, name="Legacy Pending Farewell",
            fighter_id=f"{ordinary_opponent.fighter_id}-legacy", farewell_story_key="",
            retirement_pending=True, retirement_reason="Legacy final fight required",
            retirement_requested_month=0,
        )
        app.roster.append(legacy_farewell)
        legacy_result = app.record_farewell_fight_story(
            company, farewell_rival, legacy_farewell, "TKO", {"main": False},
        )
        require(legacy_result and legacy_farewell.farewell_story_key
                and app.story_thread(legacy_farewell.farewell_story_key)["status"] == "resolved",
                "A legacy pending retiree did not create and settle a farewell at the owning result event.")

        academy_fighter = replace(
            a, fighter_id=f"{a.fighter_id}-academy", academy_graduate=True,
            academy_prospect_id="academy-regression",
            career_arc=None, career_arc_history=[], career_achievements=[],
        )
        academy_prospect = {
            "prospect_id": "academy-regression", "amateur_w": 8, "amateur_l": 1, "amateur_d": 0,
            "rating": 68, "potential": 91, "milestones": [],
        }
        app.record_academy_mentorship_story(
            academy_prospect, phase="coaches_aligned",
            summary="The academy coaches aligned around a long-term plan.",
        )
        app.record_academy_graduate(academy_prospect, academy_fighter, "MMA Developmental")
        lineage_key = app.academy_lineage_story_key(academy_fighter)
        require(app.story_thread(lineage_key)["phase"] == "professional_graduate",
                "Academy graduation did not begin a senior lineage story.")
        app.record_title_story_result(
            company, academy_fighter, b, "Submission", defense=False,
            loser_was_champion=False, title_label=f"{academy_fighter.gender} {academy_fighter.weight} championship",
        )
        require(app.story_thread(lineage_key)["status"] == "resolved"
                and app.story_thread(lineage_key)["phase"] == "homegrown_champion",
                "A graduate's championship win did not complete the academy lineage story.")
        mentorship = app.story_thread(app.academy_mentorship_story_key(academy_prospect))
        require(mentorship["status"] == "active" and mentorship["phase"] == "senior_transition"
                and academy_fighter.fighter_id in mentorship["fighter_ids"],
                "Academy mentorship did not continue into the graduating fighter's senior career.")
        app.record_coaching_fight_outcome(
            company, academy_fighter, b, "Submission", {"main": True, "title": True},
        )
        mentorship = app.story_thread(app.academy_mentorship_story_key(academy_prospect))
        require(mentorship["status"] == "resolved" and mentorship["phase"] == "mentorship_fulfilled",
                "A graduate's championship did not pay off the academy mentorship story.")

        # Academy graduation is a domain transaction. A late narrative hook
        # must roll back with the roster, finance, academy and RNG state.
        rollback_prospect = {
            "prospect_id": "academy-rollback-regression", "name": "Rollback Prospect",
            "age": 18, "gender": a.gender, "weight": a.weight, "region": a.region,
            "rating": 61, "potential": 82, "amateur_w": 4, "amateur_l": 0,
            "amateur_d": 0, "milestones": [],
        }
        app.repair_academy_prospect(rollback_prospect)
        stories_before_rollback = deepcopy(app.story_threads)
        rng_before_rollback = random.getstate()

        def fail_after_story(_prospect, _sport):
            app.upsert_story_thread(
                "academy-rollback-probe", "Academy Lineage", status="active",
                phase="professional_graduate", importance=3,
                summary="This story must not survive a failed graduation.",
                beat_kind="graduation", beat_ref="academy-rollback-probe:graduation",
            )
            raise RuntimeError("forced late graduation failure")

        app._promote_academy_prospect_to_sport = fail_after_story
        try:
            success, _message, graduated = app.promote_academy_prospect_to_sport(
                rollback_prospect, "MMA Developmental"
            )
        finally:
            del app.__dict__["_promote_academy_prospect_to_sport"]
        require(not success and graduated is None,
                "The forced academy graduation failure did not report a rollback.")
        require(app.story_threads == stories_before_rollback
                and app.story_thread("academy-rollback-probe") is None,
                "A failed academy graduation left narrative state or its index behind.")
        require(random.getstate() == rng_before_rollback,
                "Academy graduation rollback did not restore simulation RNG state.")

        b.main_event_promise = True
        b.top_opponent_promise = True
        b.promise_deadline_month = app.month + 6
        promise_key = app.contract_promise_story_key(b)
        app.record_contract_promise_story(b, ["main-event", "top-opponent"], company)
        require(app.story_thread(promise_key)["phase"] == "commitment_made",
                "Contract promises did not begin a commitment story.")
        b.main_event_promise = False
        app.resolve_contract_promise_story(b, ["main-event"], kept=True, company=company)
        require(app.story_thread(promise_key)["phase"] == "partially_fulfilled",
                "Keeping one of two promises did not preserve the remaining commitment.")
        b.top_opponent_promise = False
        app.resolve_contract_promise_story(b, ["top-opponent"], kept=True, company=company)
        require(app.story_thread(promise_key)["status"] == "resolved",
                "Fulfilling every contract promise did not resolve the commitment story.")

        # Contract pressure, exit, defection and a cross-promotional revenge
        # fight remain one direct-ID saga across ownership changes.
        contract_fighter = replace(
            a, fighter_id=f"{a.fighter_id}-contract-saga", contract_story_key="",
            career_arc=None, career_arc_history=[], career_achievements=[],
        )
        contract_rng = random.getstate()
        app.record_contract_pressure(contract_fighter, company, 3)
        contract_key = contract_fighter.contract_story_key
        app.record_contract_pressure(contract_fighter, company, 1)
        final_month_beats = len(app.story_thread(contract_key)["beats"])
        app.record_contract_pressure(contract_fighter, company, 1)
        require(contract_fighter.contract_story_key == contract_key
                and len(app.story_thread(contract_key)["beats"]) == final_month_beats,
                "Repeated final-month contract warnings duplicated or replaced the active saga.")
        app.record_contract_exit(contract_fighter, company, "Contract expired without a renewal")
        require(app.story_thread(contract_key)["phase"] == "expired_exit",
                "Contract expiry did not advance the pressure story into a market exit.")
        new_company = app.promotions[0].name
        app.record_contract_signing(contract_fighter, new_company, source="Rival market offer")
        contract_thread = app.story_thread(contract_key)
        require(contract_thread["phase"] == "defection"
                and contract_thread["former_company"] == company
                and contract_thread["current_company"] == new_company,
                "A rival signing did not preserve both sides of the contract defection.")
        contract_context = app.fight_story_summary(contract_fighter, b, {"crossover": True})
        require("first time since the contract defection" in contract_context,
                "A cross-company matchup did not expose the defection stakes.")
        app.record_contract_revenge_fight(
            contract_fighter, b, new_company, company, "Decision", "Contract Revenge Night",
        )
        contract_thread = app.story_thread(contract_key)
        require(contract_thread["status"] == "resolved" and contract_thread["phase"] == "revenge_won"
                and not contract_fighter.contract_story_key,
                "The cross-promotional revenge result did not resolve and release the direct saga key.")
        namesake = replace(contract_fighter, fighter_id=f"{contract_fighter.fighter_id}-namesake", contract_story_key="")
        require(app.active_contract_saga(namesake) is None,
                "A same-name fighter inherited another fighter's contract saga.")

        returner = replace(
            a, fighter_id=f"{a.fighter_id}-contract-return", contract_story_key="",
            career_arc=None, career_arc_history=[], career_achievements=[],
        )
        app.record_contract_pressure(returner, company, 1)
        return_key = returner.contract_story_key
        app.record_contract_exit(returner, company, "Released by mutual agreement")
        app.record_contract_signing(returner, company, source="Return negotiation")
        require(app.story_thread(return_key)["status"] == "resolved"
                and app.story_thread(return_key)["phase"] == "return_signing"
                and not returner.contract_story_key,
                "A fighter returning to the former promotion did not close the contract saga.")
        require(random.getstate() == contract_rng,
                "Contract narrative recording consumed simulation RNG.")
        contract_integrations = {
            "expiry warnings": inspect.getsource(type(app).check_contract_warnings),
            "player expiry": inspect.getsource(type(app).update_contracts),
            "automatic renewal": inspect.getsource(type(app).auto_renew_player_contracts),
            "batch renewal": inspect.getsource(type(app).auto_negotiate_player_contracts),
            "AI signing": inspect.getsource(type(app).complete_ai_free_agent_signing),
            "AI expiry": inspect.getsource(type(app).update_ai_contracts),
            "cross-promotional revenge": inspect.getsource(type(app).run_superfight_night),
        }
        for label, source in contract_integrations.items():
            require("record_contract_" in source,
                    f"The {label} path is no longer wired to contract sagas.")

        # A child-promotion chapter follows one durable fighter from development
        # through the senior roster. Fight hooks read only the saved direct key,
        # so an ordinary card does not need an alumni or roster scan.
        feeder_fighter = replace(
            a, fighter_id=f"{a.fighter_id}-feeder-pathway", feeder_story_key="",
            contract_story_key="", career_arc=None, career_arc_history=[],
            career_achievements=[], champion=False, interim_champion=False,
        )
        feeder_namesake = replace(
            feeder_fighter, fighter_id=f"{feeder_fighter.fighter_id}-namesake",
            feeder_story_key="",
        )
        child_company = "Narrative Regression Child"
        feeder_rng = random.getstate()
        feeder_thread = app.record_feeder_pathway_transition(
            feeder_fighter, child_company, company, phase="development_loan",
            pathway_kind="loan", importance=3,
            summary=f"{feeder_fighter.name} entered a child-promotion development loan.",
            event_ref=f"feeder-regression:loan:{feeder_fighter.fighter_id}",
        )
        feeder_key = feeder_fighter.feeder_story_key
        require(feeder_thread and feeder_thread["type"] == "Feeder Pathway"
                and feeder_thread["phase"] == "development_loan",
                "A child-promotion move did not begin an ID-safe feeder pathway.")
        require(app.active_feeder_pathway(feeder_namesake) is None,
                "A same-name fighter inherited another fighter's feeder pathway.")
        app.record_feeder_fight_result(
            child_company, feeder_fighter, b, "Decision", {"main": True, "title": False},
        )
        require(app.story_thread(feeder_key)["phase"] == "child_breakthrough",
                "A featured child-promotion win did not advance the development chapter.")
        app.record_feeder_pathway_transition(
            feeder_fighter, child_company, company, phase="parent_recalled",
            pathway_kind="loan", importance=4,
            summary=f"{feeder_fighter.name} returned to the parent roster.",
            event_ref=f"feeder-regression:recall:{feeder_fighter.fighter_id}",
        )
        app.roster.append(feeder_fighter)
        require("returned to the parent roster" in app.fight_story_summary(
                    feeder_fighter, b, {"main": False, "title": False}),
                "Matchmaking did not expose the stakes of a feeder graduate's parent debut.")
        app.record_feeder_fight_result(
            company, feeder_fighter, b, "Decision", {"main": False, "title": False},
        )
        require(app.story_thread(feeder_key)["phase"] == "parent_debut_win"
                and app.story_thread(feeder_key)["parent_fights"] == 1,
                "The first senior result did not become the feeder graduate's parent debut.")
        app.record_feeder_fight_result(
            company, feeder_fighter, b, "Submission", {"main": True, "title": True},
        )
        require(app.story_thread(feeder_key)["status"] == "resolved"
                and app.story_thread(feeder_key)["phase"] == "parent_champion"
                and not feeder_fighter.feeder_story_key,
                "A parent-company championship did not complete the feeder pathway.")
        app.roster.remove(feeder_fighter)
        require(random.getstate() == feeder_rng,
                "Feeder-pathway recording consumed simulation RNG.")

        feeder_integrations = {
            "development loan": inspect.getsource(type(app).loan_fighter_to_child_promotion),
            "loan recall": inspect.getsource(type(app).recall_fighter_from_child_promotion),
            "paid transfer": inspect.getsource(type(app).take_fighter_from_child_promotion),
            "player result": inspect.getsource(type(app).apply_result),
            "draw result": inspect.getsource(type(app).apply_draw_result),
            "AI result": inspect.getsource(type(app).simulate_ai_promotion_month),
            "contract departure": inspect.getsource(type(app).record_contract_exit),
            "final-fight retirement": inspect.getsource(type(app).retire_after_final_fight_if_due),
        }
        for label, source in feeder_integrations.items():
            require("record_feeder" in source or "resolve_feeder" in source,
                    f"The {label} path is no longer wired to feeder stories.")
        feeder_source = inspect.getsource(type(app).record_feeder_fight_result)
        for forbidden in ("all_fighter_objects", "fighter_instances_with_companies", "fight_history", "world_chronicle"):
            require(forbidden not in feeder_source,
                    f"Feeder result handling regressed into a world/history scan through {forbidden}.")
        require(feeder_source.index("feeder_story_key") < feeder_source.index("company ="),
                "Ordinary fights no longer exit feeder handling before story/company work.")

        # The existing eight-point Giant Slayer result now opens a prove-it
        # chapter. Only subsequent results for the saved fighter key advance it.
        breakout_fighter = replace(
            a, name="Breakout Underdog", fighter_id=f"{a.fighter_id}-breakout",
            striking=60, wrestling=60, grappling=60, cardio=60, chin=60,
            detailed_skills={}, breakout_story_key="", feeder_story_key="",
            contract_story_key="", record_w=5, record_l=2, record_d=0,
            career_achievements=[], fight_history=[],
        )
        breakout_favorite = replace(
            b, name="Established Favourite", fighter_id=f"{b.fighter_id}-breakout-favourite",
            striking=78, wrestling=78, grappling=78, cardio=78, chin=78,
            detailed_skills={}, breakout_story_key="", record_w=14, record_l=3, record_d=0,
            career_achievements=[], fight_history=[],
        )
        breakout_rng = random.getstate()
        app.evaluate_fight_achievements(
            breakout_fighter, breakout_favorite, {"main": False, "title": False},
            "Decision", company,
        )
        breakout_key = breakout_fighter.breakout_story_key
        breakout_thread = app.story_thread(breakout_key)
        require(breakout_thread and breakout_thread["type"] == "Breakout Run"
                and breakout_thread["phase"] == "giant_slayer"
                and breakout_thread["upset_gap"] >= 8,
                "A qualifying Giant Slayer result did not begin a Breakout Run.")
        origin_beats = len(breakout_thread["beats"])
        app.evaluate_fight_achievements(
            breakout_fighter, breakout_favorite, {"main": False, "title": False},
            "Decision", company,
        )
        require(len(app.story_thread(breakout_key)["beats"]) == origin_beats,
                "Replaying the same upset callback created a false follow-up beat.")
        require("prove the upset" in app.fight_story_summary(
                    breakout_fighter, b, {"main": False, "title": False}),
                "Matchmaking did not expose post-upset pressure.")
        breakout_value, breakout_reason = app.ai_story_matchup_value(company, breakout_fighter, b)
        require(breakout_value >= 4 and "breakout run" in breakout_reason,
                "A credible AI candidate pair did not recognize an active breakout run.")
        breakout_namesake = replace(
            breakout_fighter, fighter_id=f"{breakout_fighter.fighter_id}-namesake",
            breakout_story_key="",
        )
        require(app.active_breakout_run(breakout_namesake) is None,
                "A same-name fighter inherited another fighter's breakout chapter.")

        breakout_fighter.record_d += 1
        app.record_breakout_fight_story(
            company, breakout_fighter, b, "Draw", {"main": True, "title": False},
        )
        require(app.story_thread(breakout_key)["phase"] == "expectations_unresolved",
                "A draw did not preserve the uncertainty after a major upset.")
        breakout_fighter.record_w += 1
        app.record_breakout_fight_story(
            company, breakout_fighter, b, "Decision", {"main": False, "title": False},
        )
        require(app.story_thread(breakout_key)["phase"] == "momentum_building",
                "The first post-upset win did not build breakout momentum.")
        breakout_fighter.record_w += 1
        app.record_breakout_fight_story(
            company, breakout_fighter, b, "Submission", {"main": False, "title": False},
        )
        require(app.story_thread(breakout_key)["status"] == "resolved"
                and app.story_thread(breakout_key)["phase"] == "breakout_confirmed"
                and app.story_thread(breakout_key)["follow_up_wins"] == 2
                and not breakout_fighter.breakout_story_key,
                "Two follow-up wins did not confirm and close the breakout chapter.")
        breakout_timeline = app.fighter_career_timeline_rows(breakout_fighter, limit=20)
        require(any(row["kind"] == "Breakout Run" for row in breakout_timeline),
                "The Fighter Profile timeline omitted a completed breakout chapter.")

        title_shocker = replace(
            breakout_fighter, name="Title Shocker", fighter_id=f"{a.fighter_id}-title-shocker",
            breakout_story_key="", record_w=7, record_l=4, record_d=0,
        )
        app.record_breakout_fight_story(
            company, title_shocker, breakout_favorite, "TKO", {"main": True, "title": True},
        )
        title_shock_key = app.new_breakout_run_story_key(title_shocker, breakout_favorite)
        title_shock_thread = app.story_thread(title_shock_key)
        title_shock_count = len(app.story_threads)
        app.record_breakout_fight_story(
            company, title_shocker, breakout_favorite, "TKO", {"main": True, "title": True},
        )
        require(title_shock_thread and title_shock_thread["status"] == "resolved"
                and title_shock_thread["phase"] == "championship_shock"
                and not title_shocker.breakout_story_key
                and len(app.story_threads) == title_shock_count,
                "A title upset did not resolve immediately or deduplicate its callback.")

        stalled_breakout = replace(
            breakout_fighter, name="Stalled Breakout", fighter_id=f"{a.fighter_id}-stalled-breakout",
            breakout_story_key="", record_w=4, record_l=1, record_d=0,
        )
        app.record_breakout_fight_story(
            company, stalled_breakout, breakout_favorite, "Decision",
            {"main": False, "title": False}, major_upset=True,
        )
        stalled_key = stalled_breakout.breakout_story_key
        stalled_breakout.record_l += 1
        app.record_breakout_fight_story(
            company, b, stalled_breakout, "Decision",
            {"main": False, "title": False}, major_upset=False,
        )
        require(app.story_thread(stalled_key)["phase"] == "pressure_setback"
                and app.story_thread(stalled_key)["status"] == "active",
                "A first post-upset defeat ended the story before its defining next result.")
        stalled_breakout.record_l += 1
        app.record_breakout_fight_story(
            company, b, stalled_breakout, "TKO",
            {"main": False, "title": False}, major_upset=False,
        )
        require(app.story_thread(stalled_key)["phase"] == "run_stalled"
                and app.story_thread(stalled_key)["status"] == "resolved"
                and app.story_thread(stalled_key)["setbacks"] == 2
                and not stalled_breakout.breakout_story_key,
                "A second follow-up defeat did not close the stalled breakout run.")
        require(random.getstate() == breakout_rng,
                "Breakout story recording consumed simulation RNG.")
        breakout_integrations = {
            "decisive achievements": inspect.getsource(type(app).evaluate_fight_achievements),
            "draw settlement": inspect.getsource(type(app).apply_draw_result),
            "retirement": inspect.getsource(type(app).retire_after_final_fight_if_due),
            "AI matchup intent": inspect.getsource(type(app).ai_story_matchup_value),
        }
        for label, source in breakout_integrations.items():
            require("breakout" in source.lower(),
                    f"The {label} path is no longer wired to Breakout Runs.")
        breakout_source = inspect.getsource(type(app).record_breakout_fight_story)
        for forbidden in ("all_fighter_objects", "fighter_instances_with_companies", "fight_history", "world_chronicle"):
            require(forbidden not in breakout_source,
                    f"Breakout result handling regressed into a world/history scan through {forbidden}.")

        # Established fighters now carry a durable Career Crossroads after a
        # third straight simulated loss. Follow-up results and actual career
        # decisions update only that direct fighter key.
        crossroads_fighter = replace(
            a, name="Crossroads Veteran", fighter_id=f"{a.fighter_id}-crossroads",
            age=34, record_w=15, record_l=9, record_d=1, popularity=52,
            crossroads_story_key="", breakout_story_key="", feeder_story_key="",
            contract_story_key="", fight_history=[], career_achievements=[],
            bout_rating_history=[{"result": "L"}, {"result": "L"}, {"result": "L"}, {"result": "W"}],
        )
        crossroads_rng = random.getstate()
        app.record_crossroads_fight_story(
            company, b, crossroads_fighter, "Decision", {"main": False, "title": False},
        )
        crossroads_key = crossroads_fighter.crossroads_story_key
        crossroads_thread = app.story_thread(crossroads_key)
        require(crossroads_thread and crossroads_thread["type"] == "Career Crossroads"
                and crossroads_thread["phase"] == "decline_pressure"
                and crossroads_thread["losses_at_origin"] == 3,
                "A veteran's third straight loss did not begin a Career Crossroads.")
        origin_beats = len(crossroads_thread["beats"])
        app.record_crossroads_fight_story(
            company, b, crossroads_fighter, "Decision", {"main": False, "title": False},
        )
        require(len(app.story_thread(crossroads_key)["beats"]) == origin_beats,
                "Replaying the crossroads origin result duplicated a story beat.")
        require("career crossroads" in app.fight_story_summary(
                    crossroads_fighter, b, {"main": False, "title": False}).lower(),
                "Matchmaking did not expose an active veteran crossroads.")
        crossroads_value, crossroads_reason = app.ai_story_matchup_value(company, crossroads_fighter, b)
        require(crossroads_value >= 3 and "career crossroads" in crossroads_reason,
                "A credible AI candidate pair did not recognize a Career Crossroads.")
        crossroads_namesake = replace(
            crossroads_fighter, fighter_id=f"{crossroads_fighter.fighter_id}-namesake",
            crossroads_story_key="",
        )
        require(app.active_crossroads_story(crossroads_namesake) is None,
                "A same-name fighter inherited another veteran's crossroads.")

        crossroads_fighter.record_d += 1
        app.record_crossroads_fight_story(
            company, crossroads_fighter, b, "Draw", {"main": True, "title": False},
        )
        require(app.story_thread(crossroads_key)["phase"] == "uncertain_draw",
                "A draw did not preserve uncertainty in a Career Crossroads.")
        app.record_crossroads_reinvention(
            crossroads_fighter, company, crossroads_fighter.weight, "Welterweight",
        )
        require(app.story_thread(crossroads_key)["phase"] == "division_reinvention"
                and app.story_thread(crossroads_key)["reinventions"] == 1,
                "A division move did not become a visible crossroads reinvention.")
        reinvention_beats = len(app.story_thread(crossroads_key)["beats"])
        app.record_crossroads_reinvention(
            crossroads_fighter, company, crossroads_fighter.weight, "Welterweight",
        )
        require(len(app.story_thread(crossroads_key)["beats"]) == reinvention_beats
                and app.story_thread(crossroads_key)["reinventions"] == 1,
                "Replaying a division move duplicated its crossroads reinvention.")
        crossroads_fighter.record_w += 1
        app.record_crossroads_fight_story(
            company, crossroads_fighter, b, "Submission", {"main": True, "title": False},
        )
        require(app.story_thread(crossroads_key)["status"] == "resolved"
                and app.story_thread(crossroads_key)["phase"] == "recovery_win"
                and not crossroads_fighter.crossroads_story_key,
                "A recovery win did not close the fighter's crossroads.")
        require(any(row["kind"] == "Career Crossroads"
                    for row in app.fighter_career_timeline_rows(crossroads_fighter, limit=20)),
                "The Fighter Profile timeline omitted a resolved Career Crossroads.")

        released_veteran = replace(
            crossroads_fighter, name="Released Veteran",
            fighter_id=f"{a.fighter_id}-released-crossroads", crossroads_story_key="",
            record_w=12, record_l=10, record_d=0,
            bout_rating_history=[{"result": "L"}, {"result": "L"}, {"result": "L"}],
        )
        app.record_crossroads_fight_story(
            company, b, released_veteran, "TKO", {"main": False, "title": False},
        )
        released_key = released_veteran.crossroads_story_key
        app.resolve_crossroads_departure(
            released_veteran, company, "released", "Released after roster review."
        )
        require(app.story_thread(released_key)["status"] == "resolved"
                and app.story_thread(released_key)["phase"] == "released"
                and not released_veteran.crossroads_story_key,
                "A roster release did not provide a durable crossroads ending.")
        require(random.getstate() == crossroads_rng,
                "Career Crossroads story recording consumed simulation RNG.")

        crossroads_integrations = {
            "player result": inspect.getsource(type(app).apply_result),
            "draw settlement": inspect.getsource(type(app).apply_draw_result),
            "AI result": inspect.getsource(type(app).simulate_ai_promotion_month),
            "regional result": inspect.getsource(type(app).simulate_regional_feeder_month),
            "division move": inspect.getsource(type(app).complete_weight_class_move),
            "contract exit": inspect.getsource(type(app).record_contract_exit),
            "retirement": inspect.getsource(type(app).retire_after_final_fight_if_due),
        }
        for label, source in crossroads_integrations.items():
            require("crossroads" in source.lower(),
                    f"The {label} path is no longer wired to Career Crossroads stories.")
        crossroads_source = inspect.getsource(type(app).record_crossroads_fight_story)
        for forbidden in ("all_fighter_objects", "fighter_instances_with_companies", "fight_history", "world_chronicle"):
            require(forbidden not in crossroads_source,
                    f"Crossroads result handling regressed into a world/history scan through {forbidden}.")
        require("limit=4" in crossroads_source,
                "Crossroads discovery no longer uses its four-result bounded streak lookup.")

        # Staff careers use their durable staff ID and one saved direct key.
        # Contract warnings reuse the existing staff loop; no second calendar
        # pass or staff-market discovery is allowed.
        staff_member = deepcopy(app.staff[0])
        staff_member["staff_story_key"] = ""
        staff_rng = random.getstate()
        original_staff = app.staff
        app.staff = [staff_member]
        staff_member["contract_months"] = 3
        app.check_staff_contract_warnings()
        staff_key = staff_member["staff_story_key"]
        staff_thread = app.story_thread(staff_key)
        require(staff_thread and staff_thread["type"] == "Staff Tenure"
                and staff_thread["phase"] == "renewal_window"
                and staff_thread["staff_ids"] == [staff_member["staff_id"]],
                "A staff renewal warning did not begin an ID-safe tenure story.")
        staff_member["contract_months"] = 1
        app.check_staff_contract_warnings()
        final_staff_beats = len(staff_thread["beats"])
        app.check_staff_contract_warnings()
        require(staff_thread["phase"] == "final_month"
                and len(staff_thread["beats"]) == final_staff_beats,
                "A repeated staff warning duplicated its direct narrative beat.")
        app.record_staff_tenure_story(
            staff_member, phase="renewed",
            summary=f"{staff_member['name']} renewed their staff contract.",
            event_ref=f"staff-regression-renewed:{staff_member['staff_id']}",
        )
        require(app.active_staff_tenure(staff_member)["phase"] == "renewed",
                "A successful staff renewal did not advance the same tenure.")
        namesake_staff = deepcopy(staff_member)
        namesake_staff["staff_id"] = f"{staff_member['staff_id']}-namesake"
        namesake_staff["staff_story_key"] = ""
        namesake_story = app.record_staff_tenure_story(
            namesake_staff, phase="appointed",
            summary=f"A different {namesake_staff['name']} joined the promotion.",
        )
        require(namesake_story and namesake_story["story_key"] != staff_key
                and namesake_story["staff_ids"] == [namesake_staff["staff_id"]],
                "Same-name staff members shared a tenure identity.")
        departure = f"{staff_member['name']} left after their contract expired."
        app.record_staff_tenure_story(
            staff_member, phase="contract_expired", status="resolved", importance=3,
            summary=departure, resolution=departure,
            event_ref=f"staff-regression-expired:{staff_member['staff_id']}",
        )
        require(app.story_thread(staff_key)["status"] == "resolved"
                and app.active_staff_tenure(staff_member) is None,
                "A staff departure did not close its tenure chapter.")
        app.staff = original_staff
        require(random.getstate() == staff_rng,
                "Staff-tenure narrative recording consumed simulation RNG.")
        staff_integrations = {
            "contract warnings": inspect.getsource(type(app).check_staff_contract_warnings),
            "contract expiry": inspect.getsource(type(app).update_staff_contracts),
            "hire and renewal": inspect.getsource(type(app).open_staff_negotiation),
            "release": inspect.getsource(type(app).fire_selected_staff),
        }
        for label, source in staff_integrations.items():
            require("record_staff_tenure_story" in source,
                    f"The staff {label} path is no longer wired to tenure stories.")
        require("active_staff_tenure" in inspect.getsource(type(app).open_selected_staff_profile),
                "Staff Profiles no longer expose the current tenure story.")

        # First-of-kind contribution milestones turn tenure into an actual
        # career without copying event history or producing repetitive beats.
        milestone_staff = [
            {"name": "Mara Match", "role": "Matchmaker", "skill": 78, "morale": 72,
             "staff_id": "STF-milestone-matchmaker", "staff_story_key": ""},
            {"name": "Mina Market", "role": "Marketing", "skill": 76, "morale": 75,
             "staff_id": "STF-milestone-marketing", "staff_story_key": ""},
            {"name": "Brooke Cast", "role": "Broadcast Producer", "skill": 80, "morale": 77,
             "staff_id": "STF-milestone-broadcast", "staff_story_key": ""},
            {"name": "Sam Scout", "role": "Scout", "skill": 82, "morale": 79,
             "staff_id": "STF-milestone-scout", "staff_story_key": ""},
        ]
        original_staff = app.staff
        app.staff = milestone_staff
        milestone_rng = random.getstate()
        standout_package = {
            "event_name": "Staff Legacy Night", "fight_count": 6, "average_excitement": 82,
            "finance": {
                "attendance": 9_800, "venue_capacity": 10_000, "marketing": 25_000,
                "broadcast_income": 400_000, "ticket_revenue": 300_000,
            },
            "media_outcome": {"delivered": True},
        }
        written = app.record_event_staff_milestones(standout_package)
        require(len(written) == 3,
                "A standout event did not create matchmaker, marketing and broadcast milestones.")
        matchmaker = milestone_staff[0]
        matchmaker_key = matchmaker["staff_story_key"]
        matchmaker_thread = app.story_thread(matchmaker_key)
        require(matchmaker_thread["contribution_kinds"] == ["standout_card"]
                and matchmaker_thread["staff_legacy_score"] == 4,
                "A staff contribution did not add one bounded legacy milestone.")
        beats_before = len(matchmaker_thread["beats"])
        legacy_before = matchmaker_thread["staff_legacy_score"]
        app.record_event_staff_milestones(standout_package)
        require(len(matchmaker_thread["beats"]) == beats_before
                and matchmaker_thread["staff_legacy_score"] == legacy_before,
                "Repeating the same type of staff achievement duplicated its beat or legacy reward.")

        scout_member = milestone_staff[3]
        app.record_staff_contribution(
            "Scout", "comprehensive_dossier",
            "Sam Scout completed a comprehensive dossier on a leading prospect.",
            member=scout_member, event_ref="staff-milestone-scout:1", importance=4,
        )
        scout_key = scout_member["staff_story_key"]
        require(app.story_thread(scout_key)["contribution_kinds"] == ["comprehensive_dossier"],
                "A direct known-scout contribution did not advance that scout's tenure.")
        poor_package = {
            "event_name": "Staff Setback Night", "fight_count": 5, "average_excitement": 35,
            "finance": {
                "attendance": 3_000, "venue_capacity": 10_000, "marketing": 20_000,
                "broadcast_income": 0, "ticket_revenue": 90_000,
            },
            "media_outcome": {"delivered": False},
        }
        app.record_event_staff_milestones(poor_package)
        require(matchmaker_thread["phase"] == "role_setback"
                and "card_backlash" in matchmaker_thread["contribution_kinds"]
                and matchmaker_thread["staff_legacy_score"] == legacy_before - 1,
                "A poor event did not create one bounded staff-career setback.")
        app.staff = original_staff
        require(random.getstate() == milestone_rng,
                "Staff contribution narratives consumed simulation RNG.")
        contribution_integrations = {
            "scouting result": inspect.getsource(type(app).process_scouting_reports),
            "medical clearance": inspect.getsource(type(app).age_and_develop_fighters),
            "event settlement and fighter promise": inspect.getsource(type(app)._finish_event_unchecked),
        }
        for label, source in contribution_integrations.items():
            require("record_staff_contribution" in source or "record_event_staff_milestones" in source,
                    f"The {label} path is no longer wired to staff career milestones.")
        contribution_source = inspect.getsource(type(app).record_staff_contribution)
        for forbidden in ("all_fighter_objects", "world_chronicle", "result_history", "fight_history"):
            require(forbidden not in contribution_source,
                    f"Staff contribution recording regressed into a world/history scan through {forbidden}.")
        staff_profile_source = inspect.getsource(type(app).open_selected_staff_profile)
        require("staff_legacy_score" in staff_profile_source and "contribution_kinds" in staff_profile_source,
                "Staff Profiles no longer expose career legacy and milestone count.")

        # Phase 2 and world-story helpers remain direct event writes. They
        # connect existing weight, camp, relationship, company and other-sport
        # events without adding a calendar-wide discovery pass.
        phase_two_rng = random.getstate()
        app.record_weight_journey_story(
            a, phase="turnaround_started",
            summary=f"{a.name} began a weight-cut turnaround.",
        )
        app.record_weight_journey_story(
            a, phase="division_reinvention", status="resolved", importance=4,
            summary=f"{a.name} found a sustainable division.",
            resolution="The division move completed the weight chapter.",
        )
        require(app.story_thread(app.weight_journey_story_key(a))["status"] == "resolved",
                "A completed division reinvention did not resolve the weight story.")

        original_camp = a.camp
        target_gym = next((gym for gym in app.gyms if gym.name != original_camp), None)
        require(target_gym and app.move_fighter_to_gym(a, target_gym, "Narrative regression move"),
                "A valid gym move did not complete.")
        gym_thread = app.story_thread(app.gym_journey_story_key(a))
        require(gym_thread and gym_thread["phase"] == "camp_move" and target_gym.name in gym_thread["companies"],
                "A camp move did not create an indexed gym-journey beat.")
        coaching_key = app.coaching_loyalty_story_key(a, target_gym.name)
        require(app.story_thread(coaching_key)["phase"] == "new_partnership",
                "A significant fighter's gym move did not begin a coaching-loyalty chapter.")
        split_gym = next((gym for gym in app.gyms if gym.name not in {original_camp, target_gym.name}), None)
        require(split_gym and app.move_fighter_to_gym(a, split_gym, "Sought better fit and coaching attention"),
                "A valid gym-split move did not complete.")
        require(app.story_thread(app.gym_journey_story_key(a))["phase"] == "gym_split",
                "A move driven by fit and coaching attention was not framed as a gym split.")
        require(app.story_thread(coaching_key)["status"] == "resolved"
                and app.story_thread(coaching_key)["phase"] == "gym_split",
                "Leaving a coach for fit or attention did not resolve the prior coaching chapter.")
        new_coaching_key = app.coaching_loyalty_story_key(a, split_gym.name)
        a.career_win_streak = 3
        app.record_coaching_fight_outcome(company, a, b, "Decision", {"main": True})
        require(app.story_thread(new_coaching_key)["phase"] == "breakthrough",
                "A defining win did not advance the active coaching partnership.")

        market_region = app.player_region
        a.regional_popularity = dict(getattr(a, "regional_popularity", {}) or {})
        a.regional_popularity[market_region] = 59
        app.update_regional_popularity(a, market_region, 1, "Hometown regression appearance")
        hometown = app.story_thread(app.hometown_story_key(a, market_region))
        require(hometown and hometown["phase"] == "local_hero",
                "Crossing a home-market milestone did not begin a hometown-hero story.")
        a.birth_region = market_region
        a.hometown = "Narrative Test City"
        home_event = {
            "name": "Narrative Homecoming", "region": market_region,
            "city": a.hometown, "month": app.month, "week": app.week,
            "fights": [{
                "fighters": [a.name, b.name], "fighter_ids": [a.fighter_id, b.fighter_id],
                "main": True, "title": False,
            }],
        }
        home_rng = random.getstate()
        written = app.record_homecoming_booking(home_event, company)
        hometown = app.story_thread(app.hometown_story_key(a, market_region))
        require(written and hometown["phase"] == "homecoming_booked",
                "Booking a known home-market headliner did not create a homecoming beat.")
        require("homecoming" in app.fight_story_summary(a, b, home_event["fights"][0] | {
                    "region": market_region, "city": a.hometown,
                }).lower(),
                "Fight context did not expose the booked homecoming stakes.")
        app.record_hometown_fight_story(
            a, b, home_event["fights"][0] | {"region": market_region, "city": a.hometown},
            "Decision", True, event_name=home_event["name"], company=company,
        )
        require(app.story_thread(app.hometown_story_key(a, market_region))["phase"] == "homecoming_triumph",
                "A main-event homecoming win did not become a hometown triumph.")
        title_fight = {"main": True, "title": True, "region": market_region, "city": a.hometown}
        app.record_hometown_fight_story(
            a, b, title_fight, "Submission", True,
            event_name="Narrative Home Title", company=company,
        )
        hometown = app.story_thread(app.hometown_story_key(a, market_region))
        title_beat_count = len(hometown["beats"])
        app.record_hometown_fight_story(
            a, b, title_fight, "Submission", True,
            event_name="Narrative Home Title", company=company,
        )
        require(hometown["status"] == "resolved" and hometown["phase"] == "home_title_triumph"
                and len(hometown["beats"]) == title_beat_count,
                "A home-title payoff did not resolve once with a deduplicated result beat.")
        require(random.getstate() == home_rng,
                "Homecoming narrative recording consumed simulation RNG.")
        hometown_integrations = {
            "scheduled event": inspect.getsource(type(app).schedule_event),
            "immediate event": inspect.getsource(type(app).run_event),
            "player settlement": inspect.getsource(type(app).apply_regional_show_effects),
            "AI settlement": inspect.getsource(type(app).simulate_ai_promotion_month),
        }
        for label, source in hometown_integrations.items():
            require("record_homecoming_booking" in source or "record_hometown_fight_story" in source,
                    f"The {label} path is no longer wired to homecoming stories.")

        friend_a = replace(
            a, name="Longtime Friend A", fighter_id=f"{a.fighter_id}-friend-a",
            friend="Longtime Friend B", friend_fighter_id=f"{b.fighter_id}-friend-b",
            rival="", rival_fighter_id="", record_w=8, record_l=3, record_d=0,
            relationship_story_keys=[],
        )
        friend_b = replace(
            b, name="Longtime Friend B", fighter_id=f"{b.fighter_id}-friend-b",
            friend="Longtime Friend A", friend_fighter_id=f"{a.fighter_id}-friend-a",
            rival="", rival_fighter_id="", record_w=7, record_l=4, record_d=0,
            relationship_story_keys=[],
        )
        relationship_rng = random.getstate()
        relationship = app.record_relationship_fight_story(
            company, friend_a, friend_b, "Decision", {"main": True},
        )
        relationship_key = app.relationship_story_key(friend_a, friend_b)
        require(relationship and relationship["phase"] == "friendship_tested"
                and relationship["fighter_ids"] == [friend_a.fighter_id, friend_b.fighter_id]
                and relationship["relationship_kind"] == "friendship"
                and relationship["meetings"] == 1
                and relationship_key in friend_a.relationship_story_keys
                and relationship_key in friend_b.relationship_story_keys,
                "An ID-backed friendship was not connected to its first fight result.")
        first_relationship_beats = len(relationship["beats"])
        app.record_relationship_fight_story(
            company, friend_a, friend_b, "Decision", {"main": True},
        )
        require(relationship["meetings"] == 1 and len(relationship["beats"]) == first_relationship_beats,
                "Replaying a friendship result duplicated its relationship beat.")
        require("friendship" in app.fight_story_summary(friend_a, friend_b, {"main": True}).lower(),
                "Fight context did not expose the active friendship stakes.")
        relationship_value, relationship_reason = app.ai_story_matchup_value(company, friend_a, friend_b)
        require(relationship_value >= 4 and "relationship tension" in relationship_reason,
                "A credible AI pair did not recognize active friendship tension.")
        namesake = replace(friend_b, fighter_id=f"{friend_b.fighter_id}-namesake", friend_fighter_id="")
        require(app.record_relationship_fight_story(
                    company, friend_a, namesake, "Decision", {"main": False}) is None,
                "A same-name fighter inherited another fighter's friendship story.")

        friend_a.record_d += 1
        friend_b.record_d += 1
        app.record_relationship_fight_story(company, friend_a, friend_b, "Draw", {"main": True})
        require(relationship["phase"] == "rematch_unresolved" and relationship["meetings"] == 2,
                "A friendship rematch draw did not preserve the relationship question.")
        friend_a.record_w += 1
        friend_b.record_l += 1
        app.record_relationship_fight_story(
            company, friend_a, friend_b, "Submission", {"main": True},
        )
        require(relationship["status"] == "resolved"
                and relationship["phase"] == "competitive_respect"
                and relationship["meetings"] == 3
                and not friend_a.relationship_story_keys and not friend_b.relationship_story_keys,
                "A non-rival friendship series did not resolve through competitive respect.")

        stablemate_a = replace(
            a, name="Stablemate A", fighter_id=f"{a.fighter_id}-stablemate-a",
            friend="", friend_fighter_id="", rival="", rival_fighter_id="",
            camp="Shared Room", record_w=9, record_l=4, record_d=0,
            relationship_story_keys=[],
        )
        stablemate_b = replace(
            b, name="Stablemate B", fighter_id=f"{b.fighter_id}-stablemate-b",
            friend="", friend_fighter_id="", rival="", rival_fighter_id="",
            camp="Shared Room", record_w=8, record_l=5, record_d=0,
            relationship_story_keys=[],
        )
        stablemate = app.record_relationship_fight_story(
            company, stablemate_a, stablemate_b, "Decision", {"main": True},
        )
        stablemate_key = app.relationship_story_key(stablemate_a, stablemate_b)
        require(stablemate and stablemate["status"] == "cooling"
                and stablemate["phase"] == "stablemate_bout"
                and stablemate["shared_camp"] == "Shared Room"
                and stablemate_key in stablemate_a.relationship_story_keys
                and stablemate_key in stablemate_b.relationship_story_keys,
                "A featured stablemate bout did not open a shared-room aftermath.")
        stablemate_a.camp = "New Room"
        stablemate_a.record_w += 1
        stablemate_b.record_l += 1
        app.record_relationship_fight_story(
            company, stablemate_a, stablemate_b, "TKO", {"main": True},
        )
        require(app.story_thread(stablemate_key)["status"] == "resolved"
                and app.story_thread(stablemate_key)["phase"] == "camp_split_rematch"
                and not stablemate_a.relationship_story_keys
                and not stablemate_b.relationship_story_keys,
                "A post-split rematch did not resolve the former stablemates' chapter.")

        fractured_a = replace(
            friend_a, name="Fractured Friend A", fighter_id=f"{friend_a.fighter_id}-fractured",
            friend_fighter_id=f"{friend_b.fighter_id}-fractured",
            rival_fighter_id=f"{friend_b.fighter_id}-fractured", record_w=10, record_l=5,
            relationship_story_keys=[],
        )
        fractured_b = replace(
            friend_b, name="Fractured Friend B", fighter_id=f"{friend_b.fighter_id}-fractured",
            friend_fighter_id=f"{friend_a.fighter_id}-fractured",
            rival_fighter_id=f"{friend_a.fighter_id}-fractured", record_w=10, record_l=5,
            relationship_story_keys=[],
        )
        fractured = app.record_relationship_fight_story(
            company, fractured_a, fractured_b, "Decision", {"main": True},
        )
        require(fractured["status"] == "active" and fractured["phase"] == "friendship_fractured",
                "A rivalry between friends did not become active competitive fallout.")
        fractured_a.record_l += 1
        fractured_b.record_w += 1
        app.record_relationship_fight_story(
            company, fractured_b, fractured_a, "Decision", {"main": True},
        )
        fractured_a.record_w += 1
        fractured_b.record_l += 1
        app.record_relationship_fight_story(
            company, fractured_a, fractured_b, "TKO", {"main": True},
        )
        require(fractured["status"] == "resolved" and fractured["phase"] == "fallout_settled"
                and fractured["meetings"] == 3,
                "A three-fight friendship rivalry did not receive a final relationship verdict.")
        require(random.getstate() == relationship_rng,
                "Relationship-story recording consumed simulation RNG.")
        relationship_source = inspect.getsource(type(app).record_relationship_fight_story)
        for forbidden in ("resolve_friend_target", "_rivalry_fighter_pool", "all_fighter_objects",
                          "fight_history", "world_chronicle"):
            require(forbidden not in relationship_source,
                    f"Relationship result recording regressed into a world/history scan through {forbidden}.")
        require(relationship_source.index("not winner_keys and not loser_keys")
                < relationship_source.index("key = self.relationship_story_key"),
                "Ordinary unrelated bouts no longer exit before pair-key and story-index work.")
        relationship_integrations = {
            "decisive player result": inspect.getsource(type(app).apply_result),
            "draw result": inspect.getsource(type(app).apply_draw_result),
            "AI result": inspect.getsource(type(app).simulate_ai_promotion_month),
            "regional result": inspect.getsource(type(app).simulate_regional_feeder_month),
        }
        for label, source in relationship_integrations.items():
            require("record_relationship_fight_story" in source,
                    f"The {label} path is no longer wired to relationship chapters.")

        farewell_source = inspect.getsource(type(app).record_farewell_fight_story)
        for forbidden in ("all_fighter_objects", "self.promotions", "self.roster", "self.free_agents"):
            require(forbidden not in farewell_source,
                    f"Farewell settlement regressed into a world scan through {forbidden}.")
        farewell_integrations = {
            "decisive MMA result": inspect.getsource(type(app).apply_result),
            "draw result": inspect.getsource(type(app).apply_draw_result),
            "no-contest result": inspect.getsource(type(app).apply_no_contest_result),
            "AI result": inspect.getsource(type(app).simulate_ai_promotion_month),
            "regional result": inspect.getsource(type(app).simulate_regional_feeder_month),
            "other-sport result": inspect.getsource(type(app).apply_combat_sport_result),
        }
        for label, source in farewell_integrations.items():
            require("record_farewell_fight_story" in source,
                    f"The {label} path is no longer wired to Career Farewell chapters.")
        require("fight_history" not in inspect.getsource(type(app).farewell_prior_meetings),
                "Farewell relationship history regressed from fighter IDs to display-name text.")
        require("farewell_matchup_score" in inspect.getsource(type(app).process_overdue_retirement_fights),
                "Automated retirement showcases no longer prefer meaningful existing candidates.")

        promo = app.promotions[0]
        app.record_promotion_era_story(
            promo, phase="investor_rescue", summary=f"{promo.name} entered a recovery era.", importance=5,
        )
        era = app.story_thread(app.promotion_era_story_key(promo.name))
        require(era and era["type"] == "Promotion Era" and era["companies"] == [promo.name],
                "A promotion-era event did not retain its company identity.")

        rival_company = next(item.name for item in app.promotions if item.name != promo.name)
        war_rng = random.getstate()
        war = app.record_promotion_war_event(
            promo.name, rival_company, "talent_signing",
            f"{promo.name} won the first contested signing.", fighters=[a],
            event_ref="promotion-war-regression:1",
        )
        app.record_promotion_war_event(
            promo.name, rival_company, "talent_signing",
            f"{promo.name} won the first contested signing.", fighters=[a],
            event_ref="promotion-war-regression:1",
        )
        require(war["contests"] == 1 and war["scoreboard"][promo.name] == 1,
                "A replayed promotion-rivalry event changed the scoreboard twice.")
        for index in range(2, 7):
            app.record_promotion_war_event(
                promo.name, rival_company, "competitive_event",
                f"{promo.name} won promotional exchange {index}.", fighters=[a],
                event_ref=f"promotion-war-regression:{index}",
            )
        war_key = app.promotion_war_story_key(promo.name, rival_company)
        war = app.story_thread(war_key)
        require(war["status"] == "resolved" and war["phase"] == "decisive_lead"
                and war["leader"] == promo.name,
                "A decisive multi-event promotion rivalry did not reach a scored resolution.")
        require(random.getstate() == war_rng,
                "Promotion-rivalry recording consumed simulation RNG.")
        academy_rival = next(
            item.name for item in app.promotions
            if item.name not in {promo.name, rival_company}
        )
        contested_lead = {
            "prospect_id": "contested-lead-regression", "name": "Contested Lead",
            "rival_offer": {"promotion": academy_rival},
        }
        academy_war = app.record_academy_recruitment_win(contested_lead, company)
        require(academy_war and academy_war["scoreboard"][company] == 1
                and academy_rival in academy_war["companies"],
                "A contested academy signing did not advance the promotion rivalry.")
        integration_sources = {
            "AI contract signing": inspect.getsource(type(app).complete_ai_free_agent_signing),
            "academy poaching": inspect.getsource(type(app).place_academy_lead_with_rival),
            "sanctioned superfight": inspect.getsource(type(app).run_superfight_night),
            "player contract signing": inspect.getsource(type(app).open_contract_negotiation),
        }
        for label, source in integration_sources.items():
            require("record_promotion_war_event" in source or "record_academy_recruitment_win" in source,
                    f"The {label} path is no longer wired to promotion-rivalry stories.")
        storylines_source = inspect.getsource(type(app).open_storylines_window)
        require("PROMOTION SCOREBOARD" in storylines_source and "contests" in storylines_source,
                "The Storylines browser no longer exposes promotion-rivalry scoring.")

        app.record_combat_sport_story(
            "Boxing", "Regression Boxing", a, b, phase="champion",
            summary=f"{a.name} won a boxing championship.", importance=4,
        )
        require(app.story_thread(app.combat_sport_story_key("Boxing", a))["phase"] == "champion",
                "An other-sport title result did not begin a persistent career chapter.")
        app.record_crossover_story(
            a, b, phase="superfight_result", status="resolved",
            summary=f"{a.name} completed a crossover bout against {b.name}.",
            resolution="The crossover showcase reached its result.",
        )
        require(app.story_thread(app.crossover_story_key(a))["status"] == "resolved",
                "A crossover result did not resolve its multi-sport chapter.")
        ai_value, ai_reason = app.ai_story_matchup_value(company, a, b)
        require(ai_value > 0 and ai_reason,
                "Existing connected stories did not contribute bounded AI matchup intent.")
        ai_source = inspect.getsource(type(app).ai_story_matchup_value)
        for forbidden in ("all_fighter_objects", "_rivalry_fighter_pool", "world_chronicle", "fight_history"):
            require(forbidden not in ai_source,
                    f"AI narrative intent regressed into a world/history scan through {forbidden}.")
        app.narrative_ai_intent_enabled = False
        require(app.ai_story_matchup_value(company, a, b) == (0, ""),
                "The deterministic performance-isolation switch did not disable AI story scoring.")
        app.narrative_ai_intent_enabled = True
        require(random.getstate() == phase_two_rng,
                "Phase 2 narrative event recording consumed the shared simulation RNG.")

        # Fighter timeline assembly is lazy and local to one selected fighter.
        # The annual review reads the bounded thread index once at year-end and
        # archives a small evidence-backed selection with the awards record.
        timeline_rng = random.getstate()
        timeline = app.fighter_career_timeline_rows(a, limit=40)
        timeline_kinds = {row["kind"] for row in timeline}
        require({"Weight Journey", "Gym Journey", "Crossover Career"}.issubset(timeline_kinds),
                "The unified fighter timeline omitted connected career chapters.")
        timeline_source = inspect.getsource(type(app).fighter_career_timeline_rows)
        for forbidden in ("fighter_instances_with_companies", "world_chronicle", "result_records", "ai_event_archive"):
            require(forbidden not in timeline_source,
                    f"Fighter timeline regressed into a world/history scan through {forbidden}.")

        review_year = app.current_year()
        review_rows = app.annual_story_review_rows(review_year)
        require(review_rows and len(review_rows) <= 8,
                "The annual story review did not select a bounded set of current-year threads.")
        app.awards_history.insert(0, {"year": str(review_year), "awards": []})
        app.inbox.append({
            "subject": f"{review_year} End-of-Year Awards", "body": "Regression awards",
            "type": "Awards", "resolved": False,
        })
        app.record_legacy_year(review_year, [])
        require(app.awards_history[0].get("stories"),
                "The annual review was not retained beside the awards history.")
        require(app.story_thread(f"annual-review:{review_year}")["status"] == "resolved",
                "Year-end review did not create a resolved permanent story chapter.")
        require("Defining stories:" in app.inbox[-1]["body"],
                "The year-end awards message did not expose its defining story selection.")
        require(random.getstate() == timeline_rng,
                "Timeline or annual-review presentation consumed simulation RNG.")

        # Active writes retain a bounded number of beats and a bounded number
        # of live threads. This prevents long careers from slowing by history size.
        for index in range(STORY_THREAD_ACTIVE_BEAT_LIMIT + 8):
            app.upsert_story_thread(
                "bounded-beats", "Test", fighters=[a], beat_kind="update",
                beat_ref=f"bounded-beat:{index}", summary=f"Beat {index}",
            )
        require(len(app.story_thread("bounded-beats")["beats"]) == STORY_THREAD_ACTIVE_BEAT_LIMIT,
                "An active story exceeded its hard beat limit.")
        for index in range(STORY_THREAD_ACTIVE_LIMIT + 12):
            app.upsert_story_thread(
                f"active-limit:{index}", "Test", fighters=[a],
                beat_ref=f"active-limit:{index}", summary=f"Thread {index}",
            )
        active = [row for row in app.story_threads if row.get("status") not in {"resolved", "abandoned"}]
        require(len(active) <= STORY_THREAD_ACTIVE_LIMIT,
                "Active story storage exceeded its hard world limit.")

        # Serialization includes only persistent bounded state; the transient
        # lookup is rebuilt from that state and old-save absence is harmless.
        serialized = app.serialize_world()
        require("story_threads" in serialized and len(serialized["story_threads"]) == len(app.story_threads),
                "Story threads were not included in the save payload.")
        app.story_threads = [{"malformed": True}]
        app.repair_story_threads(serialized["story_threads"])
        require(app.story_thread(story_key) and app.story_thread(story_key)["status"] == "resolved",
                "Current-format story state did not survive normalization.")
        repaired_contract = app.story_thread(contract_key)
        require(repaired_contract and repaired_contract["former_company"] == company
                and repaired_contract["current_company"] == new_company,
                "Contract defection identity did not survive current-format story normalization.")
        repaired_staff = app.story_thread(staff_key)
        require(repaired_staff and repaired_staff["staff_ids"] == [staff_member["staff_id"]]
                and repaired_staff["staff_names"] == [staff_member["name"]]
                and repaired_staff["staff_role"] == staff_member["role"],
                "Staff tenure identity did not survive current-format story normalization.")
        repaired_feeder = app.story_thread(feeder_key)
        require(repaired_feeder and repaired_feeder["child_company"] == child_company
                and repaired_feeder["parent_company"] == company
                and repaired_feeder["parent_fights"] == 2
                and repaired_feeder["status"] == "resolved",
                "Feeder pathway identity and progress did not survive save normalization.")
        repaired_breakout = app.story_thread(breakout_key)
        require(repaired_breakout and repaired_breakout["origin_opponent_id"] == breakout_favorite.fighter_id
                and repaired_breakout["upset_gap"] >= 8
                and repaired_breakout["follow_up_fights"] == 3
                and repaired_breakout["follow_up_wins"] == 2
                and repaired_breakout["status"] == "resolved",
                "Breakout origin and follow-up progress did not survive save normalization.")
        repaired_crossroads = app.story_thread(crossroads_key)
        require(repaired_crossroads and repaired_crossroads["origin_opponent_id"] == b.fighter_id
                and repaired_crossroads["losses_at_origin"] == 3
                and repaired_crossroads["crossroads_fights"] == 2
                and repaired_crossroads["reinventions"] == 1
                and repaired_crossroads["status"] == "resolved",
                "Career Crossroads origin and decision progress did not survive save normalization.")
        repaired_relationship = app.story_thread(relationship_key)
        require(repaired_relationship and repaired_relationship["relationship_kind"] == "friendship"
                and repaired_relationship["meetings"] == 3
                and len(repaired_relationship["winner_ids"]) == 2
                and repaired_relationship["status"] == "resolved",
                "Friendship identity and series progress did not survive save normalization.")
        repaired_farewell = app.story_thread(farewell_key)
        require(repaired_farewell and repaired_farewell["opponent_id"] == farewell_rival.fighter_id
                and repaired_farewell["opponent_connection"] == "rivalry"
                and repaired_farewell["farewell_result"] == "farewell_win"
                and repaired_farewell["status"] == "resolved",
                "Farewell opponent identity and result did not survive save normalization.")
        repaired_stablemates = app.story_thread(stablemate_key)
        require(repaired_stablemates and repaired_stablemates["relationship_kind"] == "stablemates"
                and repaired_stablemates["shared_camp"] == "Shared Room"
                and repaired_stablemates["phase"] == "camp_split_rematch",
                "Stablemate origin and camp-split payoff did not survive save normalization.")
        repaired_matchmaker = app.story_thread(matchmaker_key)
        require(repaired_matchmaker
                and set(repaired_matchmaker["contribution_kinds"]) == {"standout_card", "card_backlash"}
                and repaired_matchmaker["staff_legacy_score"] == legacy_before - 1,
                "Staff career contributions did not survive current-format story normalization.")
        repaired_war = app.story_thread(war_key)
        require(repaired_war and repaired_war["scoreboard"][promo.name] == 6
                and repaired_war["contests"] == 6,
                "Promotion-rivalry scoring did not survive current-format save normalization.")
        malformed_war = deepcopy(repaired_war)
        malformed_war["story_key"] = "malformed-promotion-war"
        malformed_war["scoreboard"] = {promo.name: "not-a-score", rival_company: -7, "extra": 99}
        malformed_war["contests"] = "not-a-count"
        app.repair_story_threads([malformed_war])
        repaired_malformed = app.story_thread("malformed-promotion-war")
        require(repaired_malformed["scoreboard"] == {promo.name: 0, rival_company: 0}
                and repaired_malformed["contests"] == 0,
                "Malformed promotion-rivalry score data was not normalized safely.")
        app.repair_story_threads(None)
        require(app.story_threads == [] and app.ensure_story_thread_index() == {},
                "A legacy save without story threads did not receive a safe empty default.")

        # The hot-path helper itself must remain independent of global history
        # and fighter-world enumerations.
        source = inspect.getsource(type(app).upsert_story_thread)
        for forbidden in ("all_fighter_objects", "world_chronicle", "result_history", "fight_history"):
            require(forbidden not in source,
                    f"Story upsert regressed into a global/history scan through {forbidden}.")
        app.repair_story_threads([])
        app.narrative_tracking_enabled = True
        started = time.perf_counter()
        for index in range(20_000):
            app.upsert_story_thread(
                "performance-probe", "Test", fighters=[a],
                beat_ref=f"performance:{index}", summary="Bounded event update",
            )
        elapsed = time.perf_counter() - started
        require(elapsed / 20_000 < 0.00025,
                f"Indexed narrative update exceeded the 250 microsecond event budget ({elapsed / 20_000:.7f}s).")
        before_disabled = len(app.story_threads)
        app.narrative_tracking_enabled = False
        app.upsert_story_thread("disabled-probe", "Test", fighters=[a], summary="Must not be written")
        require(len(app.story_threads) == before_disabled and app.story_thread("disabled-probe") is None,
                "The performance-audit disable switch still wrote narrative state.")
        app.narrative_tracking_enabled = True

        # Declining a veteran request closes it immediately, so the later
        # deadline cannot apply a second trust/morale penalty.
        veteran = a
        veteran.career_arc = None
        require(app.start_career_arc(veteran, "Veteran Final Run", "Narrative regression"),
                "Veteran final-run test story did not start.")
        trust_before, morale_before = veteran.relationship_trust, veteran.morale
        ok, _note, _follow_up = app.apply_career_arc_plan(veteran, "decline")
        require(ok and veteran.career_arc is None,
                "Declining a veteran final run did not close the story.")
        expected = (max(1, trust_before - 8), max(15, morale_before - 6))
        app.month += 24
        app.process_career_arcs()
        require((veteran.relationship_trust, veteran.morale) == expected,
                "A declined veteran story was penalized again after its old deadline.")

        # Losing a belt closes Keep The Champion as a failed chapter rather
        # than awarding successful-completion morale and trust bonuses.
        champion = b
        champion.career_arc = None
        champion.champion = True
        require(app.start_career_arc(champion, "Champion Ambition", "Narrative regression"),
                "Champion-retention test story did not start.")
        trust_before, morale_before = champion.relationship_trust, champion.morale
        champion.champion = False
        app.process_career_arcs()
        require(champion.career_arc is None,
                "A lost championship left the retention story active.")
        require(champion.relationship_trust < trust_before and champion.morale < morale_before,
                "A title loss incorrectly rewarded successful retention.")

        # Breakout writes sit inside the existing event transaction. Restoring
        # its full snapshot must restore both the direct fighter key and thread.
        rollback_breakout = replace(
            a, name="Rollback Breakout", fighter_id=f"{a.fighter_id}-breakout-rollback",
            breakout_story_key="", feeder_story_key="", contract_story_key="",
            career_arc=None, career_arc_history=[], career_achievements=[],
        )
        app.roster.append(rollback_breakout)
        rollback_key = app.new_breakout_run_story_key(rollback_breakout, b)
        rollback_breakout.breakout_story_key = rollback_key
        app.upsert_story_thread(
            rollback_key, "Breakout Run", status="active", phase="giant_slayer",
            importance=4, fighters=[rollback_breakout, b], companies=[company],
            beat_kind="giant_slayer", beat_ref=f"{rollback_key}:origin",
            summary="Rollback Breakout scored a major upset.",
            stakes="The next result must prove the upset.",
        )
        rollback_thread_before = deepcopy(app.story_thread(rollback_key))
        rollback_rng = random.getstate()
        transaction_snapshot = app.capture_event_transaction_state()
        rollback_breakout.record_w += 1
        app.record_breakout_fight_story(
            company, rollback_breakout, b, "Decision", {"main": False, "title": False},
            major_upset=False,
        )
        require(app.story_thread(rollback_key)["phase"] == "momentum_building",
                "The rollback probe did not mutate its breakout chapter.")
        app.restore_event_transaction_state(transaction_snapshot)
        random.setstate(rollback_rng)
        restored_breakout = next(
            fighter for fighter in app.roster if fighter.fighter_id == rollback_breakout.fighter_id
        )
        require(restored_breakout.breakout_story_key == rollback_key
                and app.story_thread(rollback_key) == rollback_thread_before,
                "Event rollback did not restore the breakout pointer and story thread.")
        require(random.getstate() == rollback_rng,
                "Breakout rollback did not restore simulation RNG.")

        rollback_crossroads = replace(
            a, name="Rollback Crossroads", fighter_id=f"{a.fighter_id}-crossroads-rollback",
            crossroads_story_key="", breakout_story_key="", feeder_story_key="",
            contract_story_key="", career_arc=None, career_arc_history=[],
        )
        app.roster.append(rollback_crossroads)
        rollback_crossroads_key = app.new_crossroads_story_key(rollback_crossroads, b)
        rollback_crossroads.crossroads_story_key = rollback_crossroads_key
        rollback_crossroads_thread = app.upsert_story_thread(
            rollback_crossroads_key, "Career Crossroads", status="active",
            phase="decline_pressure", importance=4, fighters=[rollback_crossroads, b],
            companies=[company], beat_kind="third_straight_loss",
            beat_ref=f"{rollback_crossroads_key}:origin",
            summary="Rollback Crossroads reached a career crossroads.",
            stakes="A reinvention or recovery must answer the losing run.",
        )
        rollback_crossroads_thread["reinventions"] = 0
        rollback_crossroads_before = deepcopy(rollback_crossroads_thread)
        rollback_rng = random.getstate()
        transaction_snapshot = app.capture_event_transaction_state()
        app.record_crossroads_reinvention(
            rollback_crossroads, company, rollback_crossroads.weight, "Welterweight",
        )
        require(app.story_thread(rollback_crossroads_key)["phase"] == "division_reinvention",
                "The rollback probe did not mutate its Career Crossroads.")
        app.restore_event_transaction_state(transaction_snapshot)
        random.setstate(rollback_rng)
        restored_crossroads = next(
            fighter for fighter in app.roster if fighter.fighter_id == rollback_crossroads.fighter_id
        )
        require(restored_crossroads.crossroads_story_key == rollback_crossroads_key
                and app.story_thread(rollback_crossroads_key) == rollback_crossroads_before,
                "Event rollback did not restore the crossroads pointer and story thread.")
        require(random.getstate() == rollback_rng,
                "Career Crossroads rollback did not restore simulation RNG.")

        rollback_friend_a = replace(
            a, name="Rollback Friend A", fighter_id=f"{a.fighter_id}-friend-rollback-a",
            friend="Rollback Friend B", friend_fighter_id=f"{b.fighter_id}-friend-rollback-b",
            rival="", rival_fighter_id="", relationship_story_keys=[],
            record_w=7, record_l=3, record_d=0,
        )
        rollback_friend_b = replace(
            b, name="Rollback Friend B", fighter_id=f"{b.fighter_id}-friend-rollback-b",
            friend="Rollback Friend A", friend_fighter_id=f"{a.fighter_id}-friend-rollback-a",
            rival="", rival_fighter_id="", relationship_story_keys=[],
            record_w=6, record_l=4, record_d=0,
        )
        app.roster.extend([rollback_friend_a, rollback_friend_b])
        rollback_relationship = app.record_relationship_fight_story(
            company, rollback_friend_a, rollback_friend_b, "Decision", {"main": True},
        )
        rollback_relationship_key = app.relationship_story_key(rollback_friend_a, rollback_friend_b)
        rollback_relationship_before = deepcopy(rollback_relationship)
        rollback_rng = random.getstate()
        transaction_snapshot = app.capture_event_transaction_state()
        rollback_friend_a.record_w += 1
        rollback_friend_b.record_l += 1
        app.record_relationship_fight_story(
            company, rollback_friend_a, rollback_friend_b, "Submission", {"main": True},
        )
        require(app.story_thread(rollback_relationship_key)["status"] == "resolved",
                "The rollback probe did not resolve its relationship chapter.")
        app.restore_event_transaction_state(transaction_snapshot)
        random.setstate(rollback_rng)
        restored_friend_a = next(
            fighter for fighter in app.roster if fighter.fighter_id == rollback_friend_a.fighter_id
        )
        restored_friend_b = next(
            fighter for fighter in app.roster if fighter.fighter_id == rollback_friend_b.fighter_id
        )
        require(app.story_thread(rollback_relationship_key) == rollback_relationship_before
                and rollback_relationship_key in restored_friend_a.relationship_story_keys
                and rollback_relationship_key in restored_friend_b.relationship_story_keys,
                "Event rollback did not restore the relationship thread and both fighter-local keys.")
        require(random.getstate() == rollback_rng,
                "Relationship rollback did not restore simulation RNG.")

        rollback_farewell = replace(
            a, name="Rollback Farewell", fighter_id=f"{a.fighter_id}-farewell-rollback",
            farewell_story_key="", retirement_pending=False, retired=False,
            retirement_requested_month=0, guaranteed_fights=0, contract_fights_completed=0,
            rival="Rollback Farewell Rival", rival_fighter_id=f"{b.fighter_id}-farewell-rollback-rival",
            fight_history=[], bout_rating_history=[],
        )
        rollback_farewell_rival = replace(
            b, name="Rollback Farewell Rival", fighter_id=f"{b.fighter_id}-farewell-rollback-rival",
            rival="Rollback Farewell", rival_fighter_id=rollback_farewell.fighter_id,
            farewell_story_key="", retirement_pending=False, retired=False,
            fight_history=[], bout_rating_history=[],
        )
        app.roster.extend([rollback_farewell, rollback_farewell_rival])
        app.mark_retirement_fight_required(rollback_farewell, "Rollback career review")
        rollback_farewell_key = rollback_farewell.farewell_story_key
        rollback_farewell_before = deepcopy(app.story_thread(rollback_farewell_key))
        rollback_chronicle_before = deepcopy(app.world_chronicle)
        rollback_rng = random.getstate()
        transaction_snapshot = app.capture_event_transaction_state()
        app.record_farewell_fight_story(
            company, rollback_farewell, rollback_farewell_rival, "Decision", {"main": True},
        )
        require(app.story_thread(rollback_farewell_key)["status"] == "resolved",
                "The rollback probe did not resolve its Career Farewell.")
        app.restore_event_transaction_state(transaction_snapshot)
        random.setstate(rollback_rng)
        restored_farewell = next(
            fighter for fighter in app.roster if fighter.fighter_id == rollback_farewell.fighter_id
        )
        require(restored_farewell.farewell_story_key == rollback_farewell_key
                and app.story_thread(rollback_farewell_key) == rollback_farewell_before
                and app.world_chronicle == rollback_chronicle_before,
                "Event rollback did not restore the farewell pointer, thread, and Chronicle.")
        require(random.getstate() == rollback_rng,
                "Career Farewell rollback did not restore simulation RNG.")

        # The UI reads the saved index and must be callable without advancing
        # time or changing the simulation RNG.
        app.repair_story_threads(serialized["story_threads"])
        month_before, week_before, rng_before = app.month, app.week, random.getstate()
        window = app.open_storylines_window()
        root.update_idletasks()
        require((app.month, app.week) == (month_before, week_before) and random.getstate() == rng_before,
                "Opening Storylines advanced or randomized the simulation.")
        if window is not None:
            window.destroy()

        require(not callback_errors, f"Tk callback errors occurred: {callback_errors}")
        print("NARRATIVE SYSTEM REGRESSION TEST PASSED")
    finally:
        root.destroy()


if __name__ == "__main__":
    main()
