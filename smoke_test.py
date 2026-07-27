import importlib.util
import json
import random
import sys
import tempfile
import tkinter as tk
from dataclasses import asdict
from pathlib import Path


ROOT = Path(__file__).resolve().parent
MAIN = ROOT / "main.py"


def load_game_module():
    spec = importlib.util.spec_from_file_location("mma_warriors", MAIN)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def assert_true(condition, message):
    if not condition:
        raise AssertionError(message)


def main():
    game = load_game_module()
    root = tk.Tk()
    root.withdraw()
    try:
        startup_updates = []
        app = game.FightEmpireApp(root, startup_progress=lambda value, text: startup_updates.append((value, text)))
        assert_true(startup_updates and startup_updates[-1][0] == 100, "Startup progress did not reach its ready state")
        assert_true(all(a[0] <= b[0] for a, b in zip(startup_updates, startup_updates[1:])), "Startup progress moved backwards")
        app.start_company_choice.set("Spectator Mode")
        app.new_game()
        assert_true(app.spectator_mode, "Spectator Mode failed before lazy Log screen construction")
        app.start_company_choice.set(game.PLAYER_PROMOTION_NAME)
        app.new_game()
        addin_names = {row[0] for row, _gender in app.bamma_initial_addin_data()}
        opening_roster_names = [fighter.name for fighter in app.roster]
        all_opening_names = [fighter.name for fighter in app.all_database_fighters()]
        assert_true(len(app.roster) >= 160, "BAMMA's opening roster was capped below its intended depth")
        assert_true(addin_names.issubset(opening_roster_names), "A requested BAMMA add-in fighter was omitted from the opening roster")
        assert_true(all(all_opening_names.count(name) == 1 for name in addin_names),
                    "A BAMMA add-in fighter was duplicated elsewhere in the initial database")
        latest_bamma_additions = {
            "Lani Daniels", "Danielle Perkins", "Nyrene Crowley", "Forrest Molinari",
            "Sara Collins", "Noor Oosterhoff", "Victoria Friday Uduak",
        }
        assert_true(len(app.roster) >= 175, "BAMMA's expanded opening roster target was not retained")
        assert_true(latest_bamma_additions.issubset(opening_roster_names), "A supplied second-wave BAMMA fighter was omitted")
        assert_true(all(all_opening_names.count(name) == 1 for name in latest_bamma_additions),
                    "A supplied second-wave BAMMA fighter was duplicated in the initial database")
        lani_daniels = next(fighter for fighter in app.roster if fighter.name == "Lani Daniels")
        assert_true(lani_daniels.record == "12-4-2", "Lani Daniels did not retain her authored pre-universe record")
        bamma_closed = app.bamma_initial_closed_divisions()
        assert_true(bamma_closed.issubset(app.closed_divisions), "BAMMA's requested female divisions did not start closed")
        assert_true(not any(app.belt_key(fighter.gender, fighter.weight) in bamma_closed for fighter in app.roster),
                    "A BAMMA fighter remained in a requested closed division")
        female_featherweights = [fighter for fighter in app.roster if fighter.gender == "Female" and fighter.weight == "Featherweight"]
        assert_true(len(female_featherweights) >= 3, "BAMMA did not receive its two additional generated female featherweight slots")
        bamma_as_ai = app.player_company_as_promotion()
        assert_true(all(not app.promotion_division_open(bamma_as_ai, "Female", weight) for weight in ("Middleweight", "Light Heavyweight", "Heavyweight")),
                    "BAMMA's closed female divisions remain eligible for AI recruitment")
        assert_true(all(fighter.weight in game.WEIGHTS for fighter in app.all_database_fighters()),
                    "Initial database contains a fighter outside the normal game divisions")
        for screen_name in app.screen_builders:
            app.ensure_screen_built(screen_name)
        assert_true(set(app.screen_builders) == app.built_screens, "One or more lazy management screens failed to build")
        champion_probe = next((fighter for fighter in app.roster if fighter.champion or fighter.interim_champion), None)
        if champion_probe is None:
            champion_probe = max(app.roster, key=app.champion_sort_value)
            app.belts, app.belt_history = app.set_primary_champion(
                app.roster, app.belts, app.belt_history, champion_probe,
                "Smoke-test championship fixture.",
            )
        assert_true("TITLE WARNING" in app.champion_non_title_warning_text([champion_probe], False),
                    "Matchmaking does not warn when a champion is booked without Title selected")
        assert_true(app.champion_non_title_warning_text([champion_probe], True) == "",
                    "Matchmaking warns about a champion even when Title is selected")
        title_challenger = app.create_generated_fighter(weight=champion_probe.weight, gender=champion_probe.gender)
        interim_challenger = app.create_generated_fighter(weight=champion_probe.weight, gender=champion_probe.gender)
        assert_true(not app.divisional_title_is_interim([champion_probe, title_challenger], True),
                    "A primary champion's title bout was incorrectly marked interim")
        assert_true(app.divisional_title_is_interim([title_challenger, interim_challenger], True),
                    "A title bout without the active primary champion was not marked interim")
        interim_map = app.blank_belts()
        interim_map[app.belt_key(champion_probe.gender, champion_probe.weight)] = interim_challenger.name
        assert_true(not app.interim_title_participates(interim_map, champion_probe, title_challenger),
                    "An unrelated primary-title bout would incorrectly clear the interim belt")
        assert_true(app.interim_title_participates(interim_map, champion_probe, interim_challenger),
                    "A real champion-versus-interim bout was not recognized as a unification")
        original_special_belts = dict(app.special_belts)
        original_special_titles = list(champion_probe.special_titles or [])
        app.special_belts = {"BMF": {"name": "BMF", "holder": "", "defenses": 0, "history": []}}
        assert_true(app.award_special_belt("BMF", champion_probe, title_challenger, "Decision"),
                    "A player-created special belt could not be awarded")
        assert_true(app.special_belts["BMF"]["holder"] == champion_probe.name and "BMF" in champion_probe.special_titles,
                    "Special-belt holder state did not update")
        assert_true(not app.special_belt_booking_error("BMF", (champion_probe, title_challenger)),
                    "Special-belt holder could not defend their championship")
        assert_true(bool(app.special_belt_booking_error("BMF", (title_challenger, interim_challenger))),
                    "A held special belt could be booked without its champion")
        original_a_history = list(champion_probe.bout_rating_history or [])
        original_b_history = list(title_challenger.bout_rating_history or [])
        app.record_bout_rating_history(champion_probe, title_challenger, "W", "L", {"title": True, "divisional_title": True, "interim": True, "special_belt": "BMF"})
        assert_true(champion_probe.bout_rating_history[0]["interim"] and title_challenger.bout_rating_history[0]["interim"],
                    "Interim-title stakes were not stored for both fighters' profile histories")
        assert_true(champion_probe.bout_rating_history[0]["special_belt"] == "BMF" and title_challenger.bout_rating_history[0]["special_belt"] == "BMF",
                    "Double-title special-belt stakes were not stored for both fighter profiles")
        assert_true(champion_probe.bout_rating_history[0]["divisional_title"] and title_challenger.bout_rating_history[0]["divisional_title"],
                    "Double-title divisional stakes were not retained distinctly")
        assert_true(app.fight_stakes_label({"title": True, "divisional_title": True, "special_belt": "BMF"}) == "DIVISIONAL TITLE + BMF TITLE",
                    "Double-title profile history does not display both championships distinctly")
        assert_true(app.fight_stakes_label({"title": True, "divisional_title": True, "interim": True}) == "INTERIM TITLE",
                    "Interim title history is not labelled distinctly from the primary championship")
        ai_title_probe = next(
            promotion for promotion in app.promotions
            if not getattr(promotion, "is_regional_feeder", False)
            and any((promotion.belts or {}).values())
        )
        ai_holders = {name for name in (ai_title_probe.belts or {}).values() if name}
        ai_ready = [fighter for fighter in ai_title_probe.roster if not fighter.retired]
        unavailable_title_holder = next(
            fighter for fighter in ai_ready
            if (ai_title_probe.belts or {}).get(app.belt_key(fighter.gender, fighter.weight)) == fighter.name
            and sum(1 for other in ai_ready if other is not fighter and other.gender == fighter.gender and other.weight == fighter.weight) >= 2
        )
        unavailable_division = [
            fighter for fighter in ai_ready
            if fighter is not unavailable_title_holder
            and fighter.gender == unavailable_title_holder.gender
            and fighter.weight == unavailable_title_holder.weight
        ]
        assert_true(
            not app.ai_divisional_title_bout_is_valid(
                ai_title_probe, unavailable_division[0], unavailable_division[1]
            ),
            "AI title validation accepted a bout that excluded a live reigning champion",
        )
        unavailable_card = app.build_ai_card(ai_title_probe, unavailable_division, 4)
        assert_true(
            not any(fight.get("title") for fight in unavailable_card),
            "AI treated an unavailable reigning champion as a vacant belt",
        )
        random_state = random.getstate()
        champion_appearances = 0
        for seed in range(20):
            random.seed(seed)
            ai_card = app.build_ai_card(ai_title_probe, ai_ready, 12)
            for fight in ai_card:
                participating_champions = {fight["a"].name, fight["b"].name} & ai_holders
                champion_appearances += len(participating_champions)
                assert_true(not participating_champions or fight.get("title"),
                            "AI booked a recognized champion in their division without putting the title at stake")
        random.setstate(random_state)
        assert_true(champion_appearances > 0, "AI title-booking regression probe produced no champion appearances")
        champion_probe.bout_rating_history = original_a_history
        title_challenger.bout_rating_history = original_b_history
        champion_probe.special_titles = original_special_titles
        app.special_belts = original_special_belts
        assert_true(app.contract_time_remaining_label(1) == "1 mo", "Contract screen does not show readable time remaining")
        assert_true(app.contract_time_remaining_label(14) == "1y 2mo", "Long contract duration is not compact and readable")
        assert_true(app.contract_expiry_date_label(1) == app.format_game_date(app.month + 1, 1),
                    "Contract expiry date does not match the monthly contract tick")
        original_scheduled_events = list(app.scheduled_events)
        stale_prefix = next(promotion.name for promotion in app.promotions if promotion.name != app.player_company_name)
        naming_fights = [{"fighters": [app.roster[0].name, app.roster[1].name], "main": True, "tier": "Main Card"}]
        stale_event = {"name": f"{stale_prefix} 1: Main Event", "fights": naming_fights}
        app.refresh_scheduled_event_auto_name(stale_event)
        assert_true(stale_event["name"].startswith(f"{app.player_company_name} 1:"),
                    "A stale generated event prefix was not migrated to the controlled promotion")
        assert_true(stale_event.get("auto_named") is True, "Migrated event name was not marked as automatic")
        manual_event = {"name": "Saturday Night Violence", "auto_named": False, "fights": naming_fights}
        app.refresh_scheduled_event_auto_name(manual_event)
        assert_true(manual_event["name"] == "Saturday Night Violence", "A manual event name was overwritten")
        app.scheduled_events = original_scheduled_events
        matchmaking_columns = set(app.available_tree["columns"])
        assert_true({"history", "last", "form", "activity", "fit", "elo", "record"}.issubset(matchmaking_columns),
                    "Matchmaking is missing career context or recommendation columns")
        history_pair = next(
            (a, b) for index, a in enumerate(app.roster) for b in app.roster[index + 1:]
            if a.gender == b.gender and a.weight == b.weight
        )
        history_a, history_b = history_pair
        original_history = list(history_a.fight_history)
        history_a.fight_history.insert(0, f"Month 3 Week 2: {history_a.name} def. {history_b.name} by Decision")
        original_bout_history = list(history_a.bout_rating_history or [])
        history_a.bout_rating_history = list(original_bout_history)
        history_a.bout_rating_history.insert(0, {"date": "Month 3 Week 2", "result": "W", "opponent_name": history_b.name})
        app._matchup_history_cache = {}
        assert_true(app.matchup_history_indicator(history_a, history_b) == "1 prior", "Matchmaking did not detect a prior meeting")
        assert_true(app.matchup_display_name(history_a, history_b).endswith(" II"), "Matchmaking did not label the rematch correctly")
        repeated_score = app.matchmaking_score(history_a, history_b)[0]
        assert_true(app.fighter_last_fight_date_label(history_a) == app.format_game_date(3, 2), "Matchmaking lost the fighter's last-fight date")
        assert_true(app.matchmaking_fit_score(history_a, history_b) is not None, "Matchmaking did not calculate pair fit")
        assert_true("Record" in app.matchmaking_fighter_brief(history_a), "Selected-fighter brief omits career record")
        history_a.fight_history = original_history
        history_a.bout_rating_history = original_bout_history
        app._matchup_history_cache = {}
        fresh_score = app.matchmaking_score(history_a, history_b)[0]
        assert_true(repeated_score < fresh_score, "Assistant scoring does not discourage stale repeat pairings")
        recovery_probe = app.roster[0]
        original_available_week = recovery_probe.available_week
        recovery_probe.available_week = app.calendar_week_index() + 3
        assert_true(app.fighter_current_roster_status(recovery_probe).startswith("Available "), "Roster still labels a recovering fighter as Ready")
        assert_true(app.available_status_filter.get() == "All", "Matchmaking still hides unavailable fighters by default")
        assert_true(app.fighter_matchmaking_status(recovery_probe, app.month, app.week).startswith("Available "),
                    "Matchmaking does not expose the recovery status of an unavailable fighter")
        assert_true(len(app.booking_horizontal_split.panes()) == 2, "Matchmaking no longer has two independently sized panels")
        original_booked = list(app.booked)
        history_b_available_week = history_b.available_week
        history_b.available_week = 0
        app.booked = [{"fighters": [recovery_probe.name, history_b.name], "main": True, "tier": "Main Card"}]
        earliest_month, earliest_week = app.earliest_booked_card_date()
        assert_true(app.calendar_week_index(earliest_month, earliest_week) == recovery_probe.available_week,
                    "Earliest Valid Date ignored a booked fighter's recovery window")
        app.booked = original_booked
        history_b.available_week = history_b_available_week
        recovery_probe.available_week = original_available_week
        assistant_candidates = app.assistant_matchmaking_candidates(app.month, app.week)
        assert_true(assistant_candidates, "Assistant could not find any legal opening matchup")
        assert_true(all(a.gender == b.gender and a.weight == b.weight for _score, _reason, a, b, _title in assistant_candidates),
                    "Assistant produced a mixed-gender or cross-division pairing")
        assert_true(all(not a.retirement_pending and not b.retirement_pending for _score, _reason, a, b, _title in assistant_candidates),
                    "Assistant selected a fighter awaiting retirement")
        booked_count = len(app.booked)
        app.assistant_pick_matchup()
        assert_true(len(app.booked) == booked_count and len(app.available_tree.selection()) == 2,
                    "Assistant Pick should present a reviewable pair instead of silently booking it")
        app.title_fight.set(False); app.main_event.set(False)
        assert_true(app.nav_buttons["editor"].cget("text") == "World Editor", "Navigation still presents the mixed-scope editor as a database-only tool")
        app.refresh_editor_scope_banner()
        assert_true("Career:" in app.editor_career_target_var.get(), "World Editor does not identify the current career target")
        assert_true("Pack:" in app.editor_database_target_var.get(), "World Editor does not identify the starting-universe target")
        assert_true(app.fight_timer_delay.get() == 2150, "Live fight default speed is not 2150 ms")
        assert_true(app.rules.get("active_fighter_target") == 1200, "New worlds must use the 1,200 active-fighter floor")
        assert_true(len(app.gyms) >= 55, "The world gym network is too small to support mature saves")
        assert_true(sum(gym.capacity for gym in app.gyms) >= 6000, "Gym capacity cannot support the active fighter population")
        assert_true(set(game.REGIONS).issubset({gym.region for gym in app.gyms}), "At least one world region has no gym pathway")
        attention_probe = type("AttentionProbe", (), {"capacity": 100, "member_count": 200})()
        assert_true(0.60 <= app.gym_attention_multiplier(attention_probe) < 0.80, "Overcrowding attention is not bounded correctly")
        gym_probe = next(gym for gym in app.gyms if gym.name != "Independent")
        fighter_probe = app.free_agents[0]
        original_camp = fighter_probe.camp
        fighter_probe.camp = "Independent"
        assert_true(app.move_fighter_to_gym(fighter_probe, gym_probe, "Smoke test"), "Gym movement was not applied")
        assert_true(fighter_probe.camp_history[-1]["from"] == "Independent" and fighter_probe.camp_history[-1]["to"] == gym_probe.name,
                    "Gym tenure history did not retain the move")
        fighter_probe.camp = original_camp
        for region, pools in game.REGIONAL_NAME_POOLS.items():
            for group in ("male", "female", "last"):
                assert_true(len(set(pools.get(group, []))) >= 30,
                            f"{region} generated {group} name pool fell below 30 unique entries")
            male_names = {name.casefold() for name in pools["male"]}
            female_names = {name.casefold() for name in pools["female"]}
            assert_true(not male_names.intersection(female_names),
                        f"{region} generated name pools still mix male and female first names")
        global_male_names = {name.casefold() for name in game.FIRST_NAMES}
        global_female_names = {name.casefold() for name in game.FEMALE_FIRST_NAMES}
        assert_true(not global_male_names.intersection(global_female_names),
                    "Fallback generated name pools still mix male and female first names")
        uk_name_asset = json.loads((ROOT / "assets" / "uk_first_names.json").read_text(encoding="utf-8"))
        assert_true(
            (len(uk_name_asset.get("female", [])), len(uk_name_asset.get("male", [])),
             len(uk_name_asset.get("neutral", []))) == (712, 744, 54),
            "Packaged UK first-name directory is incomplete",
        )
        uk_pools = game.REGIONAL_NAME_POOLS["UK"]
        shared_uk_names = {name.casefold() for name in uk_name_asset["female"]}.intersection(
            name.casefold() for name in uk_name_asset["male"]
        )
        expected_uk_female = {name for name in uk_name_asset["female"] if name.casefold() not in shared_uk_names}
        expected_uk_male = {name for name in uk_name_asset["male"] if name.casefold() not in shared_uk_names}
        assert_true(expected_uk_female.issubset(uk_pools["female"]),
                    "UK female generation pool did not load the complete gendered directory")
        assert_true(expected_uk_male.issubset(uk_pools["male"]),
                    "UK male generation pool did not load the complete gendered directory")
        identity_sample = [app.create_generated_fighter(region="Europe") for _ in range(80)]
        assert_true(all(fighter.nationality != "European" for fighter in identity_sample),
                    "Generated European fighters still use a generic continental nationality")
        assert_true(len({fighter.nationality for fighter in identity_sample}) >= 8,
                    "Generated European nationality variety is too narrow")
        assert_true(len({fighter.hometown for fighter in identity_sample}) >= 20,
                    "Generated European hometown variety is too narrow")
        real_identities = {fighter.name: fighter for fighter in app.all_database_fighters() if not fighter.generated}
        for name, city, nationality in (
            ("Amanda Nunes", "Pojuca", "Brazilian"),
            ("Conor McGregor", "Crumlin", "Irish"),
            ("Islam Makhachev", "Makhachkala", "Russian"),
            ("Jon Jones", "Rochester", "American"),
            ("Tom Aspinall CW", "Salford", "British"),
            ("Matthew Green", "Birmingham", "British"),
            ("Brett Akey", "Ontario", "Canadian"),
            ("Markell Holmes", "Arkansas", "American"),
        ):
            assert_true(name in real_identities and real_identities[name].hometown == city,
                        f"Verified real-fighter birthplace was not applied for {name}")
            assert_true(real_identities[name].nationality == nationality,
                        f"Verified real-fighter nationality was not applied for {name}")
        for name in ("Matthew Green", "Brett Akey", "Markell Holmes", "Max Holzer", "Leon Edwards"):
            fighter = real_identities[name]
            assert_true(
                (fighter.record_history_baseline_w, fighter.record_history_baseline_l, fighter.record_history_baseline_d)
                == (fighter.record_w, fighter.record_l, fighter.record_d),
                f"Real fighter {name} did not retain their seeded pre-universe record",
            )
        for age, minimum_room in ((20, 12), (23, 9), (28, 7)):
            potential_probe = app.create_generated_fighter(min_skill=50, max_skill=50, age_override=age)
            assert_true(potential_probe.potential - potential_probe.overall >= minimum_room,
                        f"Age {age} generated fighter did not receive at least +{minimum_room} potential room")
        regional_form_probe = app.create_generated_fighter(min_skill=55, max_skill=55, age_override=22)
        regional_form_probe.contract_type = "Developmental"
        regional_form_probe.record_w, regional_form_probe.record_l, regional_form_probe.record_d = 8, 2, 0
        assert_true(app.regional_record_development_bonus(regional_form_probe) == 10,
                    "A genuinely strong regional record did not boost development")
        feeder_probe = next(promotion for promotion in app.promotions if promotion.is_regional_feeder)
        feeder_fighter_probe = feeder_probe.roster[0]
        assert_true(feeder_fighter_probe.feeder_origin == feeder_probe.name,
                    "New regional fighters store a region instead of their actual feeder promotion")
        original_feeder_values = (
            feeder_fighter_probe.age, feeder_fighter_probe.record_w, feeder_fighter_probe.record_l,
            feeder_fighter_probe.record_d, feeder_fighter_probe.momentum, feeder_fighter_probe.popularity,
            feeder_fighter_probe.injured, feeder_fighter_probe.retirement_pending,
            feeder_fighter_probe.record_history_baseline_w, feeder_fighter_probe.record_history_baseline_l,
            feeder_fighter_probe.record_history_baseline_d,
        )
        feeder_fighter_probe.age = 25
        feeder_fighter_probe.record_w, feeder_fighter_probe.record_l, feeder_fighter_probe.record_d = 9, 4, 0
        # Eligibility is measured against real, in-engine bouts only (record
        # minus the pre-universe backstory baseline). Zero the baseline here
        # too so this fixture represents a fighter who genuinely fought these
        # 9-4 bouts, not one still carrying a randomized fabricated backstory.
        feeder_fighter_probe.record_history_baseline_w = 0
        feeder_fighter_probe.record_history_baseline_l = 0
        feeder_fighter_probe.record_history_baseline_d = 0
        feeder_fighter_probe.momentum = 5
        feeder_fighter_probe.popularity = 28
        feeder_fighter_probe.injured = 0
        feeder_fighter_probe.retirement_pending = False
        assessment = app.regional_candidate_assessment(feeder_fighter_probe, feeder_probe)
        assert_true(assessment["eligible"] and assessment["status"] == "Eligible Now",
                    "Regional prospects browser and graduation engine do not recognize a proven candidate")
        (
            feeder_fighter_probe.age, feeder_fighter_probe.record_w, feeder_fighter_probe.record_l,
            feeder_fighter_probe.record_d, feeder_fighter_probe.momentum, feeder_fighter_probe.popularity,
            feeder_fighter_probe.injured, feeder_fighter_probe.retirement_pending,
            feeder_fighter_probe.record_history_baseline_w, feeder_fighter_probe.record_history_baseline_l,
            feeder_fighter_probe.record_history_baseline_d,
        ) = original_feeder_values
        original_feeder_roster = feeder_probe.roster
        feeder_probe.roster = []
        try:
            assert_true(app.regional_graduate_fighters(feeder_probe) == 0,
                        "An empty feeder candidate pool does not exit graduation cleanly")
        finally:
            feeder_probe.roster = original_feeder_roster
        original_free_agents = app.free_agents
        original_feeder_rosters = {id(promotion): list(promotion.roster) for promotion in app.promotions if promotion.is_regional_feeder}
        app.free_agents = []
        try:
            year_end_callups = app.promote_year_end_regional_candidates()
            assert_true(0 <= year_end_callups <= 5,
                        "Year-end regional call-ups did not respect the five-fighter cap")
            assert_true(len(app.free_agents) == year_end_callups,
                        "Year-end regional call-ups did not move fighters into free agency")
            assert_true(all(fighter.market_origin == "Year-end regional graduate" for fighter in app.free_agents),
                        "Year-end call-ups were not marked as free-agent regional graduates")
        finally:
            for promotion in app.promotions:
                if promotion.is_regional_feeder:
                    promotion.roster = original_feeder_rosters[id(promotion)]
            app.free_agents = original_free_agents
        assert_true("regional_prospects" in app.tab_pages,
                    "Regional Prospects is missing from World navigation")
        assert_true({"status", "promotion", "record", "overall", "potential", "path"}.issubset(set(app.regional_prospect_tree["columns"])),
                    "Regional Prospects is missing readiness, promotion, or fighter-stat columns")
        development_factors = app.fighter_development_factors(regional_form_probe)
        assert_true({label.split(" (")[0] for label, _value in development_factors}.issuperset({
            "Gym quality", "Gym facilities", "Coaching and style fit", "Age and remaining prime",
            "Potential room", "Recent victories and momentum", "Motivation and morale", "Fatigue and injuries",
        }), "Fighter development explanation is missing a material simulation input")
        assert_true(abs(sum(value for _label, value in development_factors) - app.monthly_development_score(regional_form_probe)) < 0.001,
                    "Displayed fighter development factors do not equal the actual growth score")
        division_key = app.belt_key("Male", "Flyweight")
        app.closed_divisions.add(division_key)
        app.player_managed_divisions.add(division_key)
        if "Flyweight" in app.weight_classes:
            app.weight_classes.remove("Flyweight")
        original_showinfo = game.messagebox.showinfo
        game.messagebox.showinfo = lambda *_args, **_kwargs: None
        try:
            assert_true(app.reopen_selected_division("Male", "Flyweight"),
                        "A contracted gendered division could not be reopened")
        finally:
            game.messagebox.showinfo = original_showinfo
        assert_true(division_key not in app.closed_divisions and division_key not in app.player_managed_divisions,
                    "Reopened division retained a hidden closed/managed flag")
        assert_true("Flyweight" in app.weight_classes and "Flyweight" in app.active_player_division_weights("Male"),
                    "Reopened division did not return to player matchmaking")
        saturated_probe = game.Fighter(**asdict(regional_form_probe))
        saturated_probe.name = "Saturated Skill Repair Probe"
        saturated_probe.fighter_id = "smoke-saturated-skill-repair"
        saturated_probe.style = "Kickboxer"
        app.ensure_detailed_skills(saturated_probe)
        for key in saturated_probe.detailed_skills:
            if key not in {"reach", "natural_size"}:
                saturated_probe.detailed_skills[key] = 99
        app.sync_broad_skills_from_details(saturated_probe)
        saturated_before = saturated_probe.overall
        repair = app.rebalance_saturated_detailed_skills(saturated_probe, max_overall_drop=2)
        standing_after = [saturated_probe.detailed_skills[key] for key in game.DETAILED_SKILL_GROUPS["Standing"]]
        assert_true(repair["groups"] and not all(value >= 98 for value in standing_after),
                    "Saturated detailed-skill repair left an entire technical tab at 98-99")
        assert_true(saturated_probe.overall >= saturated_before - 2,
                    "Detailed-skill repair changed headline OVR beyond its migration bound")
        growth_probe = game.Fighter(**asdict(regional_form_probe))
        growth_probe.name = "Sparse Detailed Growth Probe"
        growth_probe.style = "Kickboxer"
        growth_probe.trait = "Gym Rat"
        growth_probe.potential = 99
        app.ensure_detailed_skills(growth_probe)
        for key in growth_probe.detailed_skills:
            if key not in {"reach", "natural_size"}:
                growth_probe.detailed_skills[key] = 95
        app.sync_broad_skills_from_details(growth_probe)
        growth_before = dict(growth_probe.detailed_skills)
        random.seed(220726)
        app.apply_development_growth(growth_probe, 3)
        changed_growth = [key for key, value in growth_probe.detailed_skills.items() if value != growth_before.get(key)]
        assert_true(len(changed_growth) <= 14, "One development month altered an entire detailed-skill profile")
        assert_true(not {"reach", "natural_size"}.intersection(changed_growth),
                    "Training development changed fixed body measurements")
        for _index in range(20):
            elite_generated = app.create_generated_fighter(min_skill=94, max_skill=96, age_override=27)
            for group_name, keys in game.DETAILED_SKILL_GROUPS.items():
                values = [elite_generated.detailed_skills.get(key, 50) for key in keys]
                assert_true(not all(value >= 98 for value in values),
                            f"Generated elite began with a fully capped {group_name} profile")
                assert_true(len(set(values)) >= 4,
                            f"Generated elite began with an unnaturally flat {group_name} profile")
        promotion_names = [promo.name for promo in app.promotions]
        for company in (
            "Ultimate Fighting Championship",
            "Professional Fighters League",
            "ONE Championship",
            "RIZIN Fighting Federation",
            "KSW",
            "Cage Warriors",
            "Legacy Fighting Alliance",
            "Oktagon MMA",
            "BRAVE Combat Federation",
            "Absolute Championship Akhmat",
            "PRIDE Fighting Championships",
            "Strikeforce",
            "World Extreme Cagefighting",
        ):
            assert_true(company in promotion_names, f"{company} promotion missing")
        assert_true(app.player_company_name not in promotion_names, "Player company duplicated in AI promotions")
        ufc = next(promo for promo in app.promotions if promo.name == "Ultimate Fighting Championship")
        assert_true(any(fighter.name == "Islam Makhachev" for fighter in ufc.roster), "Initial UFC seed lost its authored fighters")
        conor = app.find_fighter_anywhere("Conor McGregor")
        topuria = app.find_fighter_anywhere("Ilia Topuria")
        khabib = app.find_fighter_anywhere("Khabib Nurmagomedov")
        assert_true(all(fighter and fighter.realism_profile_version == 1 for fighter in (conor, topuria, khabib)),
                    "A signature real fighter did not receive its authored engine profile")
        assert_true(conor.detailed_skills["punch_power"] >= 98 and conor.detailed_skills["takedowns"] <= 85
                    and conor.detailed_skills["takedown_defence_detail"] >= 93,
                    "Prime McGregor profile does not distinguish counter striking from offensive wrestling")
        assert_true(topuria.detailed_skills["punch_power"] >= 98 and topuria.detailed_skills["submission_attack"] >= 93
                    and topuria.detailed_skills["takedown_defence_detail"] >= 92,
                    "Topuria profile does not represent his boxing and complete grappling base")
        assert_true(khabib.detailed_skills["chain_wrestling"] >= 98 and khabib.detailed_skills["top_control"] >= 98
                    and khabib.striking <= 84 and khabib.wrestling >= 96,
                    "Khabib profile does not separate historically elite grappling from open-space striking")
        pride = next(promo for promo in app.promotions if promo.name == "PRIDE Fighting Championships")
        strikeforce = next(promo for promo in app.promotions if promo.name == "Strikeforce")
        wec = next(promo for promo in app.promotions if promo.name == "World Extreme Cagefighting")
        assert_true(any(fighter.name == "Kazushi Sakuraba" for fighter in pride.roster), "PRIDE legend roster did not seed")
        assert_true(any(fighter.name == "Kimbo Slice" for fighter in strikeforce.roster), "Strikeforce legend roster did not seed")
        assert_true(any(fighter.name == "Miguel Torres" for fighter in wec.roster), "WEC legend roster did not seed")
        app.start_company_choice.set(app.player_company_name)
        app.new_game()
        app.refresh_assistant()
        assert_true(set(app.assistant_kpis) == {"show", "card", "contracts", "divisions", "runway", "medical"},
                    "Weekly command centre KPI set is incomplete")
        unscouted_probe = app.free_agents[0]
        app.scouting_reports.pop(unscouted_probe.name, None)
        windows_before = set(root.winfo_children())
        app.open_contract_negotiation(unscouted_probe)
        root.update_idletasks()
        negotiation_windows = [child for child in root.winfo_children() if child not in windows_before and isinstance(child, tk.Toplevel)]
        assert_true(negotiation_windows, "Unscouted free agent was still blocked from contract negotiation")
        for child in negotiation_windows:
            child.destroy()
        assert_true("academy" in app.nav_buttons, "Promotion navigation is missing the Fight Academy link")
        retired_marker_probe = app.roster[0]
        original_retired = retired_marker_probe.retired
        retired_marker_probe.retired = True
        marker_canvas = tk.Canvas(root, width=180, height=180)
        app.draw_profile_portrait(marker_canvas, retired_marker_probe)
        marker_text = [marker_canvas.itemcget(item, "text") for item in marker_canvas.find_all() if marker_canvas.type(item) == "text"]
        marker_fills = [marker_canvas.itemcget(item, "fill") for item in marker_canvas.find_all() if marker_canvas.type(item) == "oval"]
        assert_true("RTD" in marker_text and "#315a70" in marker_fills, "Retired fighter portrait seal is missing or uses the pending-retirement colour")
        retired_marker_probe.retired = original_retired
        marker_canvas.destroy()
        renewal_probes = [fighter for fighter in app.roster[:2] if not fighter.retirement_pending]
        old_contracts = [(fighter.purse, fighter.contract_months) for fighter in renewal_probes]
        for fighter in renewal_probes:
            fighter.contract_months = 1
            fighter.relationship_trust = 100
            fighter.morale = 100
            fighter.negotiation_persona = "Loyalist"
        cash_before_batch_test = app.cash
        app.cash = max(app.cash, 100_000_000)
        original_random = random.random
        random.random = lambda: 0.0
        try:
            renewal_report = app.auto_negotiate_player_contracts(renewal_probes)
        finally:
            random.random = original_random
        app.cash = cash_before_batch_test
        assert_true(renewal_report["renewed"] == len(renewal_probes) and all(fighter.contract_months >= 10 for fighter in renewal_probes), "Batch auto-negotiation did not renew every selected accepted deal")
        assert_true(all(fighter.purse >= old[0] * 1.03 for fighter, old in zip(renewal_probes, old_contracts)), "Batch auto-negotiation undercut existing fighter pay")
        snapshot_a = next(fighter for fighter in app.roster if fighter.gender == "Male" and fighter.weight == "Lightweight")
        snapshot_b = next(fighter for fighter in app.roster if fighter is not snapshot_a and fighter.gender == snapshot_a.gender and fighter.weight == snapshot_a.weight)
        saved_events = list(app.scheduled_events)
        saved_pending = list(app.pending_rebookings)
        saved_camps = {fighter.fighter_id: (fighter.camp_weeks, fighter.camp_boost) for fighter in (snapshot_a, snapshot_b)}
        receiving_card = {"name": "Smoke Test 2", "venue": "Regional Arena", "region": app.player_region, "city": "London", "month": app.month + 1, "week": 2, "fights": []}
        app.scheduled_events = [receiving_card]
        app.queue_cancelled_bout_rebooking({"name": "Smoke Test 1"}, {"tier": "Prelims"}, [snapshot_a.name, snapshot_b.name])
        assert_true(len(receiving_card["fights"]) == 1 and receiving_card["fights"][0]["fighters"] == [snapshot_a.name, snapshot_b.name],
                    "Cancelled bout did not move to the next existing suitable player card")
        assert_true(not any("Rebooked Bouts" in event.get("name", "") for event in app.scheduled_events),
                    "Cancelled-bout handling created a dedicated rebooking card")
        app.scheduled_events = []
        app.queue_cancelled_bout_rebooking({"name": "Smoke Test 1"}, {"tier": "Prelims"}, [snapshot_a.name, snapshot_b.name])
        assert_true(not app.scheduled_events and not app.pending_rebookings,
                    "A cancelled bout without a future card did not fall away cleanly")
        cancellable = {"name": "Cancel Me", "venue": "Regional Arena", "region": app.player_region, "city": "London", "month": app.month + 2, "week": 1, "fights": []}
        app.scheduled_events = [cancellable]
        app.refresh_upcoming(); app.upcoming_tree.selection_set("0")
        app.cancel_selected_scheduled_event()
        assert_true(cancellable in app.scheduled_events, "Card cancellation did not require inline confirmation")
        app.cancel_selected_scheduled_event()
        assert_true(cancellable not in app.scheduled_events, "Confirmed card cancellation did not remove the event")
        app.scheduled_events = saved_events
        app.pending_rebookings = saved_pending
        for fighter in (snapshot_a, snapshot_b):
            fighter.camp_weeks, fighter.camp_boost = saved_camps[fighter.fighter_id]
        app.refresh_upcoming()
        before_ovr, before_elo, before_record = snapshot_a.overall, snapshot_a.elo_rating, snapshot_a.record
        app.apply_result(snapshot_a, snapshot_b, {"main": False, "title": False}, "Decision")
        rating_entry = snapshot_a.bout_rating_history[0]
        assert_true((rating_entry["self_overall"], rating_entry["self_elo"], rating_entry["self_record"]) == (before_ovr, before_elo, before_record), "Historical result ratings were not captured before the bout changed them")
        assert_true(0 <= app.fighter_activity_rating(snapshot_a) <= 100 and 0 <= app.fighter_competitiveness_rating(snapshot_a) <= 100, "Fighter activity or competitiveness rating is out of range")
        archive_probe = {"date": "Month 1 Week 1", "company": "Smoke Test", "event": "Archive Card 1", "summary": "Archive probe", "fights": 1, "gate": "$0", "profit": "$0", "log": ["Archive probe"], "fight_logs": []}
        app.archive_result_record(archive_probe)
        assert_true(any(row.get("event") == "Archive Card 1" for row in app.result_index), "Permanent results index did not receive a completed card")
        ufc = next(promo for promo in app.promotions if promo.name == "Ultimate Fighting Championship")
        assert_true(any(fighter.name == "Islam Makhachev" for fighter in ufc.roster), "New-game reset replaced authored UFC fighters with generated filler")
        assert_true(any(fighter.name == "AJ McKee" for promo in app.promotions if promo.name == "Professional Fighters League" for fighter in promo.roster), "New-game reset replaced authored PFL fighters with generated filler")
        pfl = next(promo for promo in app.promotions if promo.name == "Professional Fighters League")
        cage_warriors = next(promo for promo in app.promotions if promo.name == "Cage Warriors")
        lewis = next(fighter for fighter in pfl.roster if fighter.name == "Lewis McGrillen")
        omar = next(fighter for fighter in cage_warriors.roster if fighter.name == "Omar Tugarev")
        brett = next(fighter for fighter in app.free_agents if fighter.name == "Brett Akey")
        assert_true(not lewis.generated and lewis.weight == "Bantamweight" and lewis.source_url, "PFL real-fighter replacement was not seeded in-place")
        assert_true(not omar.generated and omar.weight == "Lightweight" and omar.source_url, "Cage Warriors real-fighter replacement was not seeded in-place")
        assert_true(not brett.generated and brett.weight == "Lightweight" and brett.potential >= 87, "Custom real-fighter replacement did not retain its requested ceiling")
        curated_names = {"Lewis McGrillen", "Omar Tugarev", "Brett Akey", "Markell Holmes", "Max Holzer"}
        assert_true(sum(fighter.name in curated_names for fighter in app.all_database_fighters()) == len(curated_names), "Curated real-fighter replacement introduced a duplicate")
        feeder_rosters = [promo for promo in app.promotions if getattr(promo, "is_regional_feeder", False)]
        assert_true(feeder_rosters and all(len(promo.roster) == 70 for promo in feeder_rosters), "Regional feeder promotions should open with 70 fighters each")
        app.start_company_choice.set("Spectator Mode")
        app.new_game()
        assert_true(app.spectator_mode and not app.rules.get("scouting_mode", True), "Fresh spectator games must start with scouting mode disabled")
        app.refresh_assistant()
        assert_true(not any("division only has 0" in message.lower() for _priority, message, _action, _tag in app._assistant_messages), "Spectator Assistant still reports nonexistent player divisions")
        assert_true("WORLD SIMULATION" in app.assistant_snapshot.cget("text"), "Spectator Assistant does not present a world command centre")
        app.start_company_choice.set(game.PLAYER_PROMOTION_NAME)
        app.new_game()
        app.refresh_promotion_rankings(track=False)
        company_rank_map, world_rank_map = app.division_rank_maps()
        champion = next((fighter for fighter in app.roster if fighter.champion), None)
        if champion:
            champion_key = app.fighter_identity_key(champion)
            same_division = [fighter for fighter in app.roster if not fighter.retired and fighter.gender == champion.gender and fighter.weight == champion.weight]
            contenders = [fighter for fighter in same_division if not fighter.champion]
            assert_true(champion.ranking_position == 0, "Company champion still occupies contender rank #1")
            assert_true(company_rank_map.get((app.player_company_name, champion_key)) == "C", "Company champion does not display as champion")
            assert_true(world_rank_map.get(champion_key, "").startswith("#"), "Worldwide division ranking incorrectly labels a company champion as world champion")
            assert_true(app.rank_label_for_fighter(champion, app.player_company_name, world=False) == "C", "Profile lost the company champion label")
            assert_true(app.rank_label_for_fighter(champion, app.player_company_name, world=True).startswith("#"), "Profile uses a company title as a worldwide championship")
            if contenders:
                assert_true(min(fighter.ranking_position for fighter in contenders) == 1, "Leading company contender does not occupy rank #1")
        assert_true(app.morale_fight_edge(type("MoraleProbe", (), {"morale": 100})()) == 2.5, "High morale fight edge exceeded or missed its bound")
        assert_true(app.morale_fight_edge(type("MoraleProbe", (), {"morale": 0})()) == -2.5, "Low morale fight edge exceeded or missed its bound")
        app.record_change("Popularity", app.player_company_name, 2, "Smoke-test attributed change")
        assert_true(app.change_journal[-1]["reason"] == "Smoke-test attributed change", "Attributed change journal did not record causality")
        ufc = next(promo for promo in app.promotions if promo.name == "Ultimate Fighting Championship")
        paddy = next(fighter for fighter in ufc.roster if fighter.name == "Paddy Pimblett")
        assert_true(paddy.camp == "NexGen MMA", "Paddy Pimblett was not assigned to NexGen MMA")
        saved_world = app.serialize_world()
        islam_before = next(fighter for fighter in ufc.roster if fighter.name == "Islam Makhachev")
        islam_snapshot = (islam_before.age, islam_before.record, islam_before.overall, islam_before.camp)
        original_expansion = app.expanded_real_fighter_data
        app.expanded_real_fighter_data = lambda: (_ for _ in ()).throw(AssertionError("Save loading consulted the universe fighter database"))
        try:
            app.apply_world_data(saved_world)
        finally:
            app.expanded_real_fighter_data = original_expansion
        ufc = next(promo for promo in app.promotions if promo.name == "Ultimate Fighting Championship")
        islam_after = next(fighter for fighter in ufc.roster if fighter.name == "Islam Makhachev")
        assert_true((islam_after.age, islam_after.record, islam_after.overall, islam_after.camp) == islam_snapshot, "Save loading changed serialized real-fighter state")
        assert_true(any(entry.get("reason") == "Smoke-test attributed change" for entry in app.change_journal), "Attributed change journal did not survive save/load")
        assert_true(app.ai_roster_target(ufc) == 400, "UFC should target a 400-fighter roster")
        assert_true(app.ai_roster_cap(ufc) > 370, "UFC roster cap should permit a deep world-class roster")
        assert_true(app.ai_division_target(ufc) == 25, "UFC division depth target is too low for its roster plan")
        assert_true(app.ai_financial_runway(ufc) >= 6_500_000, "UFC finance runway is too small for its roster plan")
        assert_true(app.ai_contract_reserve(ufc) >= app.ai_financial_runway(ufc) * 0.69, "AI signing reserve does not protect operating runway")
        legacy_finance_probe = game.Promotion(
            "Finance Migration Probe", "USA", 60, -500_000, [], stability=4,
            strategy={"finance_model_version": 1},
        )
        app.promotions.append(legacy_finance_probe)
        app.rebalance_ai_finance_model()
        assert_true(legacy_finance_probe.strategy.get("finance_model_version") == 2, "Legacy AI finance migration was not recorded")
        assert_true(legacy_finance_probe.cash >= app.ai_financial_runway(legacy_finance_probe), "Legacy AI finance migration did not restore operating runway")
        assert_true(legacy_finance_probe.stability >= 28, "Legacy AI finance migration did not protect company stability")
        app.promotions.remove(legacy_finance_probe)
        opening_depth_probe = game.Promotion(
            "Opening Depth Probe", "USA", 45, 1_500_000, [], weight_classes=["Flyweight"],
        )
        original_feeder_flags = [(promotion, promotion.is_regional_feeder) for promotion in app.promotions]
        for promotion, _was_feeder in original_feeder_flags:
            promotion.is_regional_feeder = True
        app.promotions.append(opening_depth_probe)
        app.month = 1
        app.week = 1
        app.rules["opening_division_depth_seeded"] = False
        added_depth = app.seed_opening_ai_division_depth()
        assert_true(added_depth >= 12, "Opening-week division filler did not populate both Flyweight divisions")
        assert_true(len(opening_depth_probe.roster) == 12, "Opening-week division filler did not reach the six-fighter floor")
        assert_true(all(fighter.contract_type == "Depth Contract" for fighter in opening_depth_probe.roster), "Opening-week filler did not use short depth contracts")
        assert_true(app.seed_opening_ai_division_depth() == 0, "Opening-week division filler ran more than once")
        for fighter in opening_depth_probe.roster:
            fighter.contract_type = "Free Agent"
            fighter.contract_months = 0
            fighter.exclusive = False
        app.free_agents.extend(opening_depth_probe.roster)
        app.promotions.remove(opening_depth_probe)
        for promotion, was_feeder in original_feeder_flags:
            promotion.is_regional_feeder = was_feeder
        assert_true(len(app.roster) >= 90, "Player roster too small")
        assert_true(len(app.free_agents) >= 150, "Free agent pool too small")
        assert_true(len(app.gyms) >= 15, "Gym database too small")
        assert_true(len(game.EXTRA_MALE_FIRST_NAMES) == 100 and len(set(game.EXTRA_MALE_FIRST_NAMES)) == 100, "Male name expansion is incomplete")
        assert_true(len(game.EXTRA_FEMALE_FIRST_NAMES) == 100 and len(set(game.EXTRA_FEMALE_FIRST_NAMES)) == 100, "Female name expansion is incomplete")
        assert_true(len(game.EXTRA_LAST_NAMES) == 200 and len(set(game.EXTRA_LAST_NAMES)) == 200, "Surname expansion is incomplete")
        for region in game.REGIONS:
            pool = game.REGIONAL_NAME_POOLS.get(region, {})
            assert_true(len(pool.get("male", ())) >= 16 and len(pool.get("female", ())) >= 16 and len(pool.get("last", ())) >= 20, f"{region} regional name pool lacks depth")
        opening_generated = next(fighter for fighter in app.roster if getattr(fighter, "generated", False))
        assert_true(opening_generated.universe_entry_year == 2026 and opening_generated.universe_entry_month == 0, "Opening-universe generated fighter lost entry provenance")
        assert_true(
            (opening_generated.record_history_baseline_w, opening_generated.record_history_baseline_l, opening_generated.record_history_baseline_d)
            == (opening_generated.record_w, opening_generated.record_l, opening_generated.record_d),
            "Opening-universe generated fighter did not retain its historical record baseline",
        )
        app.spectator_mode = True
        app._advance_in_progress = True
        app._advance_job = {"total": 12, "completed": 3}
        assert_true(app.handle_spectator_space_stop() == "break", "Space did not handle an active spectator simulation")
        assert_true(app._advance_job.get("stop_requested"), "Space did not request a safe spectator simulation stop")
        app._advance_in_progress = False
        app._advance_job = None
        app.spectator_mode = False
        original_month = app.month
        app.month = 235
        runtime_entrant = app.create_generated_fighter(age_override=20, gender="Female", weight="Bantamweight")
        assert_true(runtime_entrant.record == "0-0-0", "Post-launch generated fighter should debut with no prior record")
        assert_true(
            (runtime_entrant.record_history_baseline_w, runtime_entrant.record_history_baseline_l, runtime_entrant.record_history_baseline_d) == (0, 0, 0),
            "Post-launch generated fighter received a pre-universe baseline",
        )
        assert_true(runtime_entrant.annual_overalls == {"2045": runtime_entrant.overall}, "Post-launch generated fighter received an incorrect rating-history year")
        legacy_entrant = game.Fighter(
            "Legacy Entry Probe", "Bantamweight", 20, 4, 2, 60, 75, 56, 59, 65, 21, 3, 76, 12000,
            gender="Female", fight_history=["Month 211 Week 1: Legacy Entry Probe def. Camila Valdez by Decision"],
            annual_overalls={"2026": 58, "2044": 61, "2045": 63},
            record_history_baseline_w=2, record_history_baseline_l=0, record_history_baseline_d=0,
        )
        app.ensure_fighter_business_stats(legacy_entrant)
        assert_true(legacy_entrant.universe_entry_year == 2043, "Legacy post-launch entry year was not inferred from recorded history")
        assert_true((legacy_entrant.record_history_baseline_w, legacy_entrant.record_history_baseline_l, legacy_entrant.record_history_baseline_d) == (0, 0, 0), "Legacy post-launch entrant retained a fake pre-universe record")
        assert_true(legacy_entrant.annual_overalls == {"2044": 61, "2045": 63}, "Legacy post-launch entrant retained a fake 2026 rating peak")
        app.month = original_month
        expected_sport_rosters = {
            "Boxing": 92,
            "Kickboxing": 50,
            "Muay Thai": 89,
            "Wrestling": 50,
            "Brazilian Jiu-Jitsu": 50,
        }
        real_roster_names = app.combat_sport_real_roster_data()
        for sport, minimum in expected_sport_rosters.items():
            world = app.combat_sport_worlds.get(sport, {})
            roster = world.get("roster", [])
            known_names = set(real_roster_names.get(sport, []))
            if sport == "Muay Thai":
                known_names.update(real_roster_names.get("Lethwei", []))
            assert_true(len(roster) >= minimum, f"{sport} real roster too small")
            assert_true(sum(fighter.name in known_names for fighter in roster) >= minimum, f"{sport} roster is not real-name seeded")
            app.ensure_combat_sport_circuit_state(sport, world, world.get("promotion", ""), False)
            assert_true(
                app.combat_sport_roster_target(sport, world) == minimum * 2,
                f"{sport} roster target should be double its seeded depth",
            )
            for fighter in roster:
                native_sport = fighter.primary_discipline if fighter.primary_discipline in game.COMBAT_SPORT_WEIGHT_CLASSES else sport
                valid_classes = {label for label, _limit in app.combat_sport_weight_ladder(native_sport, fighter.gender)}
                assert_true(fighter.sport_weight_class in valid_classes, f"{fighter.name} has invalid {native_sport} class {fighter.sport_weight_class}")
                key = app.combat_sport_division_key(fighter, sport)
                assert_true(key.endswith(app.combat_sport_competition_class(sport, fighter)), f"{fighter.name} circuit division key is stale")
        sport_examples = {
            ("Boxing", "Oleksandr Usyk"): "Cruiserweight",
            ("Muay Thai", "Rodtang Jitmuangnon"): "Super Featherweight",
            ("Wrestling", "Henry Cejudo"): "57 kg",
            ("Brazilian Jiu-Jitsu", "Gabi Garcia"): "Super Heavyweight",
        }
        for (sport, name), expected_class in sport_examples.items():
            fighter = next(candidate for candidate in app.combat_sport_worlds[sport]["roster"] if candidate.name == name)
            assert_true(fighter.sport_weight_class == expected_class, f"{name} should be {expected_class}, not {fighter.sport_weight_class}")
        # Every mapped real athlete must use the sport's actual class, rather
        # than a leftover MMA placeholder from an older save.
        for sport, world in app.combat_sport_worlds.items():
            for fighter in world.get("roster", []):
                native_sport = fighter.primary_discipline if fighter.primary_discipline in game.COMBAT_SPORT_WEIGHT_CLASSES else sport
                expected_class = game.COMBAT_SPORT_REAL_DIVISIONS.get(native_sport, {}).get(fighter.name)
                if expected_class:
                    assert_true(
                        fighter.sport_weight_class == expected_class,
                        f"{fighter.name} should be {expected_class} in {native_sport}, not {fighter.sport_weight_class}",
                    )
        profiled_sport_fighters = [fighter for world in app.combat_sport_worlds.values() for fighter in world.get("roster", []) if fighter.name in set(real_roster_names.get(fighter.primary_discipline, []))]
        assert_true(len(profiled_sport_fighters) >= 270, "Real child-sport profile coverage is incomplete")
        assert_true(all(fighter.sport_profile_version >= 1 for fighter in profiled_sport_fighters), "Real child-sport profile migration was not applied")
        assert_true(all(fighter.prime_start <= fighter.age <= fighter.prime_end for fighter in profiled_sport_fighters), "A starting real child-sport athlete is outside their prime")
        assert_true(all(fighter.style in game.STYLES and fighter.trait in game.TRAITS and fighter.behaviour in game.BEHAVIOURS for fighter in profiled_sport_fighters), "Real child-sport identity contains invalid values")
        sport_checks = {
            ("Boxing", "Floyd Mayweather Jr"): (50, 0, 0, "Counter Specialist", "Counter"),
            ("Boxing", "Oleksandr Usyk"): (24, 0, 0, "Adaptable", "Dynamic Attacker"),
            ("Muay Thai", "Rodtang Jitmuangnon"): (272, 43, 10, "Knockout Artist", "Pressure"),
            ("Wrestling", "Aleksandr Karelin"): (887, 2, 0, "Title Mentality", "Control"),
            ("Brazilian Jiu-Jitsu", "Roger Gracie"): (76, 7, 3, "Pressure Fighter", "Control"),
        }
        for (sport, name), expected in sport_checks.items():
            fighter = next(candidate for candidate in app.combat_sport_worlds[sport]["roster"] if candidate.name == name)
            actual = (fighter.record_w, fighter.record_l, fighter.record_d, fighter.trait, fighter.behaviour)
            assert_true(actual == expected, f"{name} profile mismatch: {actual} != {expected}")
        random.seed(1)
        usyk_a = app.create_real_combat_sport_athlete("Oleksandr Usyk", "Boxing", "Test", 4)
        random.seed(999)
        usyk_b = app.create_real_combat_sport_athlete("Oleksandr Usyk", "Boxing", "Test", 4)
        deterministic_a = (usyk_a.age, usyk_a.record, usyk_a.stance, usyk_a.trait, usyk_a.behaviour, usyk_a.detailed_skills, usyk_a.walk_weight)
        deterministic_b = (usyk_b.age, usyk_b.record, usyk_b.stance, usyk_b.trait, usyk_b.behaviour, usyk_b.detailed_skills, usyk_b.walk_weight)
        assert_true(deterministic_a == deterministic_b, "Real child-sport profiles still depend on random seed")
        development_probe = game.Fighter(**asdict(usyk_a))
        development_probe.name = "Sport Development Probe"
        development_probe.age = 20
        development_probe.prime_start = 27
        development_probe.prime_end = 36
        development_probe.injured = 0
        development_probe.potential = 92
        development_probe.striking = development_probe.power = development_probe.chin = 55
        development_probe.cardio = development_probe.fight_iq = 55
        development_probe.detailed_skills = dict(development_probe.detailed_skills or {})
        for key in app.combat_sport_development_profile("Boxing")["growth"]:
            development_probe.detailed_skills[key] = 55
        before_rating = app.combat_sport_display_rating(development_probe, "Boxing")
        before_kicks = development_probe.detailed_skills.get("high_kick_technique", 50)
        random.seed(42)
        changed = app.adjust_combat_sport_skill_bundle(development_probe, "Boxing", 1, "Smoke-test native training", key_count=5)
        after_rating = app.combat_sport_display_rating(development_probe, "Boxing")
        assert_true(changed and after_rating > before_rating, "Native child-sport training did not increase the readable sport rating")
        assert_true(development_probe.detailed_skills.get("high_kick_technique", 50) == before_kicks, "Boxing development incorrectly trained kick technique")
        incompatible_probe = game.Fighter(**asdict(development_probe))
        incompatible_probe.name = "Incompatible Focus Probe"
        incompatible_probe.camp_focus = "Grappling"
        incompatible_probe.potential = 95
        random.seed(12)
        incompatible_changed = app.adjust_combat_sport_skill_bundle(incompatible_probe, "Boxing", 1, "Incompatible-focus test", key_count=5)
        boxing_keys = set(app.combat_sport_development_profile("Boxing")["growth"])
        assert_true(incompatible_changed and set(incompatible_changed) <= boxing_keys, "Incompatible child-sport focus trained non-native skills")
        development_probe.potential = int(after_rating)
        capped_rating = app.combat_sport_display_rating(development_probe, "Boxing")
        assert_true(not app.combat_sport_growth_allowed(development_probe, "Boxing"), "Child-sport potential ceiling was not enforced")
        capped_broad = (development_probe.striking, development_probe.power, development_probe.cardio, development_probe.fight_iq)
        capped_details = dict(development_probe.detailed_skills)
        capped_changed = app.adjust_combat_sport_skill_bundle(development_probe, "Boxing", 1, "Blocked above potential", key_count=5)
        assert_true(not capped_changed and app.combat_sport_display_rating(development_probe, "Boxing") == capped_rating, "Child-sport training exceeded potential")
        assert_true(capped_broad == (development_probe.striking, development_probe.power, development_probe.cardio, development_probe.fight_iq) and capped_details == development_probe.detailed_skills, "Blocked child-sport training still mutated skills")
        capped_key_probe = game.Fighter(**asdict(incompatible_probe))
        capped_key_probe.detailed_skills["hand_speed"] = 99
        capped_key_before = (capped_key_probe.striking, app.combat_sport_display_rating(capped_key_probe, "Boxing"))
        assert_true(not app.adjust_combat_sport_training_key(capped_key_probe, "Boxing", "hand_speed", 1, "Capped key test"), "Capped detailed skill reported a false gain")
        assert_true(capped_key_before == (capped_key_probe.striking, app.combat_sport_display_rating(capped_key_probe, "Boxing")), "Capped detailed skill silently raised broad rating")
        medical_probe = game.Fighter(**asdict(development_probe))
        medical_probe.name = "Player Child-Sport Medical Probe"
        medical_probe.sport_employer = app.player_company_name
        medical_probe.serious_injury = ""
        medical_probe.serious_injury_pending = False
        random.seed(81)
        assert_true(app.apply_serious_injury(medical_probe, "smoke test") and medical_probe.serious_injury_pending, "Player child-sport athlete did not receive a medical decision")
        app.resolve_serious_injury(medical_probe, "surgery")
        assert_true(not medical_probe.serious_injury_pending, "Player child-sport medical decision did not resolve")
        app.record_combat_sport_rating_snapshot(usyk_a, "Boxing")
        assert_true(usyk_a.sport_rating_history.get("Boxing"), "Child-sport rating history was not recorded")
        floyd = next(candidate for candidate in app.combat_sport_worlds["Boxing"]["roster"] if candidate.name == "Floyd Mayweather Jr")
        floyd.age, floyd.record_w, floyd.record_l, floyd.record_d = 41, 61, 2, 1
        floyd.fight_history = ["Evolved save test"]
        floyd.sport_profile_version = 0
        floyd.trait = "Erratic"
        app.repair_combat_sport_worlds()
        assert_true((floyd.age, floyd.record_w, floyd.record_l, floyd.record_d) == (41, 61, 2, 1), "Sport-profile migration reset an evolved career ledger")
        assert_true(floyd.trait == "Counter Specialist" and floyd.sport_profile_version >= 1, "Sport-profile migration did not repair the combat identity")
        all_mma = list(app.roster) + list(app.free_agents) + [fighter for promotion in app.promotions for fighter in promotion.roster]
        sean = next(fighter for fighter in all_mma if fighter.name == "Sean O'Malley")
        loneer = next(fighter for fighter in all_mma if fighter.name == "Lone'er Kavanagh")
        assert_true(sean.stance == "Switch" and sean.trait == "Showman" and sean.rating_profile_version >= 3, "Sean O'Malley's authored MMA identity was not applied")
        assert_true(loneer.gender == "Male", "Lone'er Kavanagh gender regression")
        assert_true(any(fighter.primary_discipline == "Lethwei" and fighter.name == "Dave Leduc" for fighter in app.combat_sport_worlds["Muay Thai"]["roster"]), "Lethwei legends were not added to Muay Thai")
        dave = next(fighter for fighter in app.combat_sport_worlds["Muay Thai"]["roster"] if fighter.name == "Dave Leduc")
        assert_true(dave.sport_weight_class == "Openweight" and app.combat_sport_competition_class("Muay Thai", dave) == "Heavyweight", "Lethwei-to-Muay-Thai class translation failed")
        boxing_names = {fighter.name for fighter in app.combat_sport_worlds["Boxing"]["roster"]}
        assert_true("Muhammad Ali" not in boxing_names and "Sugar Ray Robinson" not in boxing_names and "Floyd Mayweather Jr" in boxing_names, "Boxing roster should be modern-era focused")
        kickboxing_world = app.combat_sport_worlds["Kickboxing"]
        ai_card = app.run_combat_sport_card("Kickboxing", kickboxing_world, kickboxing_world["promotion"], target_bouts=5)
        assert_true(ai_card and len(ai_card["results"]) >= 4, "AI combat-sport card builder failed")
        rotation_world = app.seed_combat_sport_worlds()["Kickboxing"]
        original_worlds = app.combat_sport_worlds
        app.combat_sport_worlds = {"Kickboxing": rotation_world}
        for _ in range(12):
            app.run_combat_sport_card("Kickboxing", rotation_world, rotation_world["promotion"], target_bouts=10)
            for fighter in rotation_world["roster"]:
                fighter.fatigue = 0
        fought = sum(1 for fighter in rotation_world["roster"] if fighter.record_w + fighter.record_l + fighter.record_d > 0)
        app.combat_sport_worlds = original_worlds
        assert_true(fought >= 42, "Combat-sport AI card rotation is too top-heavy")
        ok, division = app.open_player_combat_division("Boxing")
        assert_true(ok and not division["roster"] and division.get("promotion_name") == f"{app.player_company_name} Boxing", "Player child-promotion launch failed")
        boxing_world = app.combat_sport_worlds["Boxing"]
        ladder_ids_before = {fighter.fighter_id for fighter in boxing_world["roster"]}
        youth = app.player_combat_signable_youth("Boxing")
        assert_true(youth and all(fighter.age < 20 for fighter in youth), "Player child-sport youth market was not populated with under-20 athletes")
        assert_true(not ({fighter.fighter_id for fighter in youth} & ladder_ids_before), "Player-only youth recruits leaked into the flagship ladder")
        intake_month = app.month
        assert_true(app.ensure_player_combat_signable_depth("Boxing", boxing_world) == 0, "Youth market ignored its two-month intake cadence")
        app.month = intake_month + 1
        assert_true(app.ensure_player_combat_signable_depth("Boxing", boxing_world) == 0, "Youth market replenished after only one month")
        app.month = intake_month + 2
        assert_true(app.ensure_player_combat_signable_depth("Boxing", boxing_world) <= 12, "Youth market intake exceeded its controlled monthly batch")
        app.month = intake_month
        market_signing = app.player_combat_signable_youth("Boxing")[0]
        signed, signing_note, signed_youth = app.sign_player_combat_youth("Boxing", market_signing.fighter_id)
        assert_true(signed and signing_note and signed_youth in boxing_world["roster"] and signed_youth.sport_employer == app.player_company_name, "Youth recruit was not transferred into the player ladder when signed")
        assert_true(all(fighter.fighter_id != signed_youth.fighter_id for fighter in app.player_combat_signable_youth("Boxing")), "Signed youth remained duplicated in the private recruitment market")
        # A player child promotion begins empty; simulate deliberate signings
        # before proving that its normal card loop remains functional.
        candidates = sorted((fighter for fighter in boxing_world["roster"] if fighter.sport_employer == boxing_world["promotion"]), key=lambda fighter: (app.combat_sport_display_rating(fighter, "Boxing"), fighter.potential), reverse=True)[12:24]
        for fighter in candidates:
            fighter.sport_employer = app.player_company_name
        division["roster"] = [signed_youth.name] + [fighter.name for fighter in candidates]
        existing_windows = set(root.winfo_children())
        app.open_player_combat_division_window("Boxing")
        root.update_idletasks()
        sport_windows = [child for child in root.winfo_children() if child not in existing_windows and child.winfo_class() == "Toplevel"]
        assert_true(sport_windows, "Player combat-sport management window did not open")
        sport_window = sport_windows[-1]
        descendants = []
        pending = list(sport_window.winfo_children())
        while pending:
            widget = pending.pop()
            descendants.append(widget)
            pending.extend(widget.winfo_children())
        notebooks = [widget for widget in descendants if widget.winfo_class() == "TNotebook"]
        assert_true(notebooks and len(notebooks[0].tabs()) == 4, "Player combat-sport manager did not render its four workspaces")
        auto_fill_buttons = [widget for widget in descendants if widget.winfo_class() == "TButton" and widget.cget("text") == "Auto-Fill Card"]
        assert_true(auto_fill_buttons, "Player combat-sport manager did not render the editable smart-card action")
        auto_fill_buttons[0].invoke()
        root.update_idletasks()
        assert_true(division.get("booked_bouts"), "Player combat-sport auto-fill did not create an editable card")
        division["booked_bouts"] = []
        sport_window.destroy()
        player_card = app.run_combat_sport_card("Boxing", app.combat_sport_worlds["Boxing"], app.player_company_name, player_owned=True, target_bouts=5, event_name="Smoke Boxing Night")
        assert_true(player_card and len(player_card["results"]) >= 4 and division.get("events"), "Player combat-sport card builder failed")
        assert_true(player_card.get("event_name") == "Smoke Boxing Night", "Player combat-sport custom event name was not preserved")
        sport_result = player_card["results"][0]
        assert_true(any(line.startswith("Camp:") for line in sport_result.get("log", [])), "Combat-sport camps are not reaching the fight log")
        assert_true(any(line.startswith("Weigh-in:") for line in sport_result.get("log", [])), "Combat-sport weigh-ins are not reaching the fight log")
        assert_true(any(line.startswith("Fight-night readiness:") for line in sport_result.get("log", [])), "Combat-sport readiness metrics are not visible")
        assert_true(sport_result.get("condition") and sport_result.get("readiness"), "Combat-sport condition/readiness telemetry missing")
        assert_true(all(log.get("heading") and log.get("lines") for log in player_card.get("fight_logs", [])), "Combat-sport live replay contract incomplete")
        for replay in player_card.get("fight_logs", []):
            assert_true(replay.get("sport") == "Boxing", "Combat-sport replay lost its sport identity")
            assert_true(replay.get("a_record") and replay.get("b_record"), "Combat-sport replay records missing")
            assert_true(replay.get("a_start_gas") is not None and replay.get("b_start_gas") is not None, "Combat-sport starting condition missing")
            assert_true(sum(1 for line in replay["lines"] if line.startswith("Result:")) == 1, "Combat-sport replay needs one official terminal result")
            assert_true(replay["lines"][-1].startswith("Result:"), "Combat-sport replay continued after its official result")
        crossover_probe = candidates[-1]
        crossover_probe.retirement_pending = False
        crossover_id = crossover_probe.fighter_id
        boxing_record = crossover_probe.record
        division["booked_bouts"] = [{"a": crossover_probe.name, "b": candidates[-2].name}]
        moved, move_note = app.move_player_combat_athlete_to_mma("Boxing", crossover_probe)
        assert_true(moved and move_note and crossover_probe in app.roster and crossover_probe.fighter_id == crossover_id, "Player child-sport crossover did not preserve fighter identity")
        assert_true(crossover_probe not in app.combat_sport_worlds["Boxing"]["roster"] and crossover_probe.name not in division["roster"], "Crossover athlete remained duplicated in the child-sport roster")
        assert_true(crossover_probe.multi_sport_records.get("Boxing") == boxing_record and crossover_probe.primary_discipline == "MMA" and crossover_probe.sport_employer == "", "Crossover records or employment were not converted to MMA")
        assert_true(not any(crossover_probe.name in (bout.get("a"), bout.get("b")) for bout in division.get("booked_bouts", [])), "Crossover athlete remained booked on a child-sport card")
        for sport, sport_world in app.combat_sport_worlds.items():
            roster = sport_world.get("roster", [])
            a = roster[0]
            b = next((candidate for candidate in roster[1:] if candidate.gender == a.gender), roster[1])
            playback = app.simulate_combat_sport_bout(sport, a, b)
            lines = playback.get("log", [])
            assert_true(any(line.lstrip().startswith("[") for line in lines), f"{sport} replay has no clocked live exchanges")
            expected_phase = "MATCH CLOCK" if sport == "Brazilian Jiu-Jitsu" else "PERIOD " if sport == "Wrestling" else "ROUND "
            assert_true(any(line.startswith(expected_phase) for line in lines), f"{sport} replay has no visible round/match start")
            assert_true(playback.get("start_stamina") and playback.get("condition"), f"{sport} replay condition telemetry missing")
        situation_bank = app.combat_sport_striking_situation_bank()
        for sport in ("Boxing", "Kickboxing", "Muay Thai", "Lethwei"):
            assert_true(sport in situation_bank and len(situation_bank[sport]) >= 8, f"{sport} striking situation bank missing")
            assert_true(all(len(pool.get("land", [])) >= 50 and len(pool.get("defended", [])) >= 50 for pool in situation_bank[sport].values()), f"{sport} striking situation variety regressed")
        bjj_bank = app.combat_sport_bjj_situation_bank()
        assert_true(len(bjj_bank) >= 16, "BJJ live action families missing")
        assert_true(all(len(pool.get("land", [])) >= 50 and len(pool.get("defended", [])) >= 50 for pool in bjj_bank.values()), "BJJ commentary variety regressed")
        bjj_roster = app.combat_sport_worlds["Brazilian Jiu-Jitsu"]["roster"]
        bjj_a = bjj_roster[0]
        bjj_b = next(candidate for candidate in bjj_roster[1:] if candidate.gender == bjj_a.gender)
        bjj_actions = app.combat_sport_live_actions("Brazilian Jiu-Jitsu")
        bjj_state = {"position": "standing", "top": None, "bottom": None}
        app.combat_sport_bjj_apply_transition(bjj_state, "guard pull", bjj_a, bjj_b, True)
        assert_true(bjj_state == {"position": "guard", "top": bjj_b.name, "bottom": bjj_a.name}, "BJJ guard-pull transition failed")
        legal_bottom = {action[0] for action in app.combat_sport_bjj_legal_actions(bjj_actions, bjj_a, bjj_state)}
        assert_true("sweep" in legal_bottom and "guard pass" not in legal_bottom, "BJJ bottom-position action gating failed")
        app.combat_sport_bjj_apply_transition(bjj_state, "sweep", bjj_a, bjj_b, True)
        assert_true(bjj_state["top"] == bjj_a.name and bjj_state["position"] == "guard", "BJJ sweep transition failed")
        terminal = app.combat_sport_bjj_terminal_line(bjj_a, bjj_b, bjj_state)
        assert_true(bjj_a.name in terminal and bjj_b.name in terminal and "taps" in terminal, "BJJ finish commentary is not linked to the result")
        mma_striking = app.mma_striking_commentary_expansion()
        for category in ("jab_land", "power_land", "dirty_boxing_miss", "ground_strikes_miss", "body_kick_land", "leg_kick_hurt", "kick_checked", "knockdown"):
            assert_true(len(mma_striking.get(category, [])) >= 6, f"MMA {category} commentary variety regressed")
        card_order_probe = [
            {"heading": "Headline", "label": "MAIN EVENT"},
            {"heading": "Co-main", "label": "CO-MAIN EVENT"},
            {"heading": "Opener", "label": "EARLY PRELIMS"},
        ]
        live_order = app.fight_night_log_order(card_order_probe)
        assert_true([row["heading"] for row in live_order] == ["Opener", "Co-main", "Headline"], "Fight night did not run from opener to main event")
        assert_true(app.fight_night_log_order(live_order) == live_order, "Already-correct fight-night order was reversed twice")
        assert_true(app.event_fight_order([1, 2, 3]) == [3, 2, 1], "Player event execution order was not flipped")
        feeder_promotions = [promotion for promotion in app.promotions if promotion.is_regional_feeder]
        assert_true(len(feeder_promotions) == 16, "Regional feeder promotion expansion missing")
        assert_true(all(promotion.cash == 0 and all(fighter.age >= 17 for fighter in promotion.roster) for promotion in feeder_promotions), "Regional feeders must be non-financial with a 17-year minimum intake age")
        original_month = app.month
        app.month = 13
        app.rules.pop("regional_wonderkid_last_year", None)
        feeder_total = sum(len(promotion.roster) for promotion in feeder_promotions)
        wonderkid = app.spawn_annual_regional_wonderkid()
        assert_true(wonderkid is not None and wonderkid.age == 17 and 80 <= wonderkid.overall <= 84 and 87 <= wonderkid.potential <= 95, "Annual regional wonderkid profile is invalid")
        assert_true(sum(len(promotion.roster) for promotion in feeder_promotions) == feeder_total + 1, "Annual wonderkid was not placed into a regional promotion")
        assert_true(app.spawn_annual_regional_wonderkid() is None, "Annual regional wonderkid spawned twice in one year")
        app.month = original_month
        feeder_champions_before = {
            id(fighter)
            for promotion in feeder_promotions
            for fighter in promotion.roster
            if fighter.champion
        }
        app.ensure_all_company_champions()
        for promotion in feeder_promotions:
            champion_counts = {}
            for fighter in promotion.roster:
                if fighter.champion:
                    key = app.belt_key(fighter.gender, fighter.weight)
                    champion_counts[key] = champion_counts.get(key, 0) + 1
            assert_true(all(count == 1 for count in champion_counts.values()), "Regional feeder divisions must crown at most one champion each")
        feeder_champions_after = {
            id(fighter)
            for promotion in feeder_promotions
            for fighter in promotion.roster
            if fighter.champion
        }
        assert_true(feeder_champions_after == feeder_champions_before,
                    "Regional feeder maintenance appointed a champion without a title fight")
        feeder_probe = feeder_promotions[0]
        washed_out = app.create_regional_feeder_fighter(feeder_probe.region, app.active_fighter_names(), "Male")
        washed_out.age, washed_out.record_w, washed_out.record_l, washed_out.potential = 22, 0, 14, 60
        feeder_probe.roster.append(washed_out)
        app.regional_review_underperformers(feeder_probe)
        assert_true(washed_out in app.free_agents and washed_out not in feeder_probe.roster and not washed_out.retired, "Young regional washouts should reset into free agency rather than retire")
        assert_true(all(app.promotion_strategy(promotion).get("identity") and app.promotion_strategy(promotion).get("current_mode") for promotion in app.promotions), "Promotion strategy profiles missing")
        assert_true(all(getattr(promotion, "executive", {}).get("name") and getattr(promotion, "executive", {}).get("archetype") for promotion in app.promotions), "Promotion executive profiles missing")
        assert_true(all(getattr(fighter, "negotiation_persona", "") and getattr(fighter, "agent_name", "") for fighter in app.roster[:25]), "Fighter negotiation profiles missing")
        assert_true(all(getattr(fighter, "camp_focus", "") for fighter in app.roster[:25]), "Fighter camp-focus profiles missing")
        assert_true(all(getattr(fighter, "camp_intensity", "") for fighter in app.roster[:25]), "Fighter camp-intensity profiles missing")
        assert_true(all("specialty" in member and "reputation" in member for member in app.staff), "Staff specialization profiles missing")
        app.record_world_story("Test", "Smoke-test chronicle entry")
        assert_true(app.world_chronicle and app.world_chronicle[0]["type"] == "Test", "World chronicle did not record an entry")
        legacy_probe = app.roster[0]
        legacy_probe.title_wins = 2
        legacy_probe.title_defenses = 3
        assert_true(app.compute_legacy_score(legacy_probe) > 0, "Legacy scoring failed")
        volume_probe = app.create_generated_fighter(min_skill=82, max_skill=82, age_override=35)
        volume_probe.primary_discipline = "Wrestling"
        volume_probe.record_w, volume_probe.record_l, volume_probe.record_d = 887, 2, 0
        assert_true(app.compute_legacy_score(volume_probe) < 600,
                    "Extreme combat-sport record volume still overwhelms bounded legacy scoring")
        assert_true(app.fighter_career_sport(volume_probe) == "Wrestling",
                    "Historical leaderboards cannot separate careers by combat sport")
        standings = app.industry_standings_rows()
        tier_names = {row["tier"] for row in standings}
        assert_true({"Global", "National", "Regional", "Local"}.issubset(tier_names),
                    "Industry tier calibration does not provide all four levels in a starting world")
        assert_true(all(row["power"] == round(sum(value for _label, value in row["components"])) for row in standings),
                    "Displayed industry power does not equal its exposed component breakdown")
        ufc_row = next(row for row in standings if row["name"] == "Ultimate Fighting Championship" and row["sport"] == "MMA")
        wrestling_row = next(row for row in standings if row["sport"] == "Wrestling" and not row["player"])
        assert_true(ufc_row["power"] > wrestling_row["power"],
                    "Cross-sport record volume still inflates a circuit above the leading MMA promotion")
        app.refresh_companies()
        assert_true(app.select_company_by_name(wrestling_row["name"], wrestling_row["sport"]),
                    "Combat-sport standings row could not be selected by its full identity")
        circuit_data = app.selected_company_data()
        assert_true(circuit_data and circuit_data.get("combat_sport") and circuit_data.get("sport") == "Wrestling",
                    "Combat-sport standings row cannot resolve its company-hub data")
        windows_before = set(root.winfo_children())
        app.open_selected_company_hub()
        root.update_idletasks()
        circuit_windows = [child for child in root.winfo_children() if child not in windows_before and isinstance(child, tk.Toplevel)]
        assert_true(circuit_windows, "Combat-sport standings row did not open a company hub")
        for child in circuit_windows:
            child.destroy()
        app.open_records_ledger_window()
        record_windows = [child for child in root.winfo_children() if isinstance(child, tk.Toplevel) and "Historical Records" in child.title()]
        assert_true(record_windows, "Historical records ledger did not open")
        record_windows[-1].destroy()
        app.refresh_historical_records()
        assert_true(app.historical_records.get("world", {}).get("Most Career Wins"), "Official world records were not generated")
        app.open_record_book_window()
        book_windows = [child for child in root.winfo_children() if isinstance(child, tk.Toplevel) and "Official Record Book" in child.title()]
        assert_true(book_windows, "Official record book did not open")
        book_windows[-1].destroy()
        champion_probe = app.roster[0]
        champion_probe.gender, champion_probe.weight = "Male", "Lightweight"
        app.belts[app.belt_key("Male", "Lightweight")] = champion_probe.name
        defenses_before = champion_probe.title_defenses
        app.set_primary_champion(app.roster, app.belts, app.belt_history, champion_probe, "Normalisation check.")
        assert_true(champion_probe.title_defenses == defenses_before, "Title normalisation incorrectly counted as a defense")
        app.set_primary_champion(app.roster, app.belts, app.belt_history, champion_probe, "Title fight check.", defense=True)
        assert_true(champion_probe.title_defenses == defenses_before + 1, "Real title defense was not recorded")
        promised = app.roster[0]
        promised.main_event_promise = True
        promised.promise_deadline_month = app.month
        trust_before = promised.relationship_trust
        app.month += 1
        app.review_contract_promises()
        app.month -= 1
        assert_true(not promised.main_event_promise and promised.relationship_trust < trust_before, "Broken contract-promise handling failed")
        draw_a, draw_b = app.roster[0], app.roster[1]
        draws_before = (draw_a.record_d, draw_b.record_d)
        app.apply_draw_result(draw_a, draw_b, {"title": False})
        app.record_season_result(draw_a, draw_b, "Draw", 3, {"title": False, "main": False}, 50, app.player_company_name)
        draw_stats = app.season_bucket()["fighters"]
        assert_true((draw_a.record_d, draw_b.record_d) == (draws_before[0] + 1, draws_before[1] + 1), "Draws did not update both fighter records")
        assert_true(draw_stats[draw_a.name].get("draws") and not draw_stats[draw_a.name]["wins"], "Draw was incorrectly recorded as a win")

        sport_history_probe = app.combat_sport_worlds["Boxing"]["roster"][0]
        app.record_combat_sport_rating_snapshot(sport_history_probe, "Boxing")
        sport_history_probe_name = sport_history_probe.name
        data = app.serialize_world()
        for sport_world in data["combat_sport_worlds"].values():
            sport_world.pop("roster_target", None)
        data["rules"]["active_fighter_target"] = 560
        for promotion in data["promotions"]:
            for fighter in promotion["roster"]:
                if fighter["name"] == "Yair Rodriguez":
                    fighter["rating_profile_version"] = 0
                if fighter["name"] in {"Conor McGregor", "Ilia Topuria"}:
                    fighter["realism_profile_version"] = 0
        for fighter in data["free_agents"]:
            if fighter["name"] == "Georges St-Pierre":
                fighter["age"] = 45
                fighter["legend_prime_age_version"] = 0
            if fighter["name"] == "Khabib Nurmagomedov":
                fighter["realism_profile_version"] = 0
        app.apply_world_data(data)
        assert_true(app.rules.get("active_fighter_target") == 1200, "Legacy active-fighter floor was not migrated")
        assert_true(app.gym_by_name("American Top Team") is not None, "Gym load repair failed")
        loaded_sport_history_probe = next(fighter for fighter in app.combat_sport_worlds["Boxing"]["roster"] if fighter.name == sport_history_probe_name)
        assert_true(loaded_sport_history_probe.sport_rating_history.get("Boxing"), "Child-sport development history did not survive save/load")
        yair = app.find_fighter_anywhere("Yair Rodriguez")
        assert_true(yair and yair.rating_profile_version == 0, "Save load recalibrated an existing real fighter from the database")
        gsp = app.find_fighter_anywhere("Georges St-Pierre")
        assert_true(gsp and gsp.age == 45 and gsp.legend_prime_age_version == 0, "Save load changed a serialized legend from the database")
        migrated_signatures = [app.find_fighter_anywhere(name) for name in ("Conor McGregor", "Ilia Topuria", "Khabib Nurmagomedov")]
        assert_true(all(fighter and fighter.realism_profile_version == 1 for fighter in migrated_signatures),
                    "Existing-save signature fighter migration did not run")
        active_fighters = app.roster + app.free_agents + [fighter for promo in app.promotions for fighter in promo.roster]
        assert_true(all(getattr(fighter, "career_arc_version", 0) >= 2 for fighter in active_fighters), "Career-arc migration failed")
        assert_true(all(getattr(fighter, "birth_region", "") in game.REGIONS and getattr(fighter, "regional_popularity", None) for fighter in active_fighters), "Regional identity migration failed")
        identity_probe = app.create_generated_fighter(region="UK")
        assert_true(identity_probe.birth_region in game.REGIONS and identity_probe.hometown and identity_probe.fighting_base == "UK", "Generated fighter regional identity failed")
        hometown_connection = app.fighter_event_connection(identity_probe, identity_probe.birth_region, identity_probe.hometown)
        assert_true(hometown_connection["level"] == "Hometown" and hometown_connection["strength"] == 1.0, "Hometown event connection failed")
        app.open_regional_identity_window(identity_probe)
        identity_windows = [child for child in root.winfo_children() if isinstance(child, tk.Toplevel) and "Market Identity" in child.title()]
        assert_true(identity_windows, "Regional identity window did not open")
        identity_windows[-1].destroy()
        veteran = next(fighter for fighter in active_fighters if fighter.age >= 30)
        veteran.age = max(veteran.age, veteran.prime_end + 1)
        veteran.momentum = 5
        veteran.motivation = 95
        veteran.professionalism = 95
        veteran.trait = "Warrior Spirit"
        app.ensure_detailed_skills(veteran)
        veteran.detailed_skills["resilience"] = 95
        veteran.detailed_skills["conditioning"] = 95
        assert_true(0 < app.veteran_resurgence_chance(veteran) <= 0.045, "Veteran resurgence probability is outside its intended cap")
        veteran.momentum = -1
        assert_true(app.veteran_resurgence_chance(veteran) == 0, "Veteran resurgence should require a strong winning run")

        pair = None
        fighters = [game.Fighter(**asdict(fighter)) for fighter in app.roster[:60]]
        for first in fighters:
            for second in fighters:
                if first.name != second.name and first.gender == second.gender and first.weight == second.weight:
                    pair = (first, second)
                    break
            if pair:
                break
        assert_true(pair is not None, "No valid same-division fight pair found")
        winner, loser, method, round_no, lines = app.simulate_fight(pair[0], pair[1], {"main": True, "title": False})
        assert_true(winner.name != loser.name, "Fight sim returned same winner and loser")
        assert_true(method, "Fight sim returned no method")
        assert_true(1 <= round_no <= app.rules.get("title_rounds", 5), "Fight sim returned invalid round")
        assert_true(lines, "Fight sim returned no commentary")
        for fighter in pair:
            stats = fighter.last_fight_stats
            assert_true(stats is not None and "head_damage" in stats, "Fight metrics do not store genuine head damage")
            assert_true(all(isinstance(stats.get(key), int) for key in ("knockdowns", "head_damage", "body_damage", "leg_damage", "cuts")), "Fight metrics contain non-integer combat statistics")
            assert_true(stats["damage_taken"] >= stats["head_damage"] + stats["body_damage"] + stats["leg_damage"], "Location damage exceeds aggregate damage")

        app.sim_gender_filter.set(pair[0].gender)
        app.sim_weight_filter.set(pair[0].weight)
        app.refresh_sim_fighter_choices()
        filtered = app.sim_filtered_fighters()
        assert_true(len(filtered) >= 4, "Simulator division filter did not provide a tournament field")
        assert_true(all(f.gender == pair[0].gender and f.weight == pair[0].weight for f in filtered), "Simulator filters returned the wrong division")
        app.sim_tournament_size.set(4)
        app.auto_seed_sim_tournament()
        seeded_names = [app.sim_tournament_list.get(index) for index in app.sim_tournament_list.curselection()]
        assert_true(len(seeded_names) == 4, "Tournament auto-seeding failed")
        app.run_simulation_tournament()
        tournament_report = app.sim_tournament_report.get("1.0", "end")
        assert_true("CHAMPION:" not in tournament_report and "hidden until you watch" in tournament_report, "Tournament results are not hidden before watching")
        assert_true(len(app.sim_tournament_package.get("fight_logs", [])) == 3, "Tournament did not build a watchable fight-night card")
        assert_true(app.sim_tournament_bracket.get("champion"), "Tournament did not build a visual bracket state")

        app.editor_search.set(pair[0].name)
        app.refresh_database_editor()
        editor_rows = app.editor_tree.get_children()
        assert_true(editor_rows, "Database editor search did not find a fighter")
        app.editor_tree.selection_set(editor_rows[0])
        app.load_selected_editor_fighter()
        edited = app.editor_selected_fighter
        prior_power = edited.power
        app.editor_vars["power"].set(min(99, prior_power + 1))
        app.editor_vars["owner"].set("Free Agent")
        app.save_database_editor_fighter()
        assert_true(edited in app.free_agents, "Database editor did not move fighter to free agency")
        assert_true(edited.power >= prior_power, "Database editor did not apply combat rating change")

        rizin = next(promotion for promotion in app.promotions if promotion.name == "RIZIN Fighting Federation")
        cage_warriors = next(promotion for promotion in app.promotions if promotion.name == "Cage Warriors")
        assert_true(len(rizin.roster) >= 100 and len(cage_warriors.roster) >= 100, "Regional promotions lack full rosters")
        japanese_last_names = set(game.REGIONAL_NAME_POOLS["Japan"]["last"])
        uk_last_names = set(game.REGIONAL_NAME_POOLS["UK"]["last"])
        assert_true(sum(fighter.name.split()[-1] in japanese_last_names for fighter in rizin.roster) >= 35, "RIZIN generated roster lacks Japanese name depth")
        assert_true(sum(fighter.name.split()[-1] in uk_last_names for fighter in cage_warriors.roster) >= 30, "Cage Warriors generated roster lacks UK name depth")
        japan_feeder = next(promotion for promotion in feeder_promotions if promotion.name == "Japan Fight Circuit")
        assert_true(sum(fighter.name.split()[-1] in japanese_last_names for fighter in japan_feeder.roster) >= 60, "Japan feeder roster lacks regional name integrity")
        ai_contract_probe = rizin.roster[0]
        ai_contract_probe.contract_months = 2
        app.age_and_develop_fighters([ai_contract_probe])
        assert_true(ai_contract_probe.contract_months == 1, "AI fighter contracts are not ticking down")
        blue_chip = app.create_generated_fighter(10, 25, 84, 90, gender="Male", weight="Lightweight")
        blue_chip.age, blue_chip.potential, blue_chip.record_w, blue_chip.record_l = 23, 96, 7, 1
        app.free_agents.append(blue_chip)
        assert_true(app.is_blue_chip_prospect(blue_chip), "Blue-chip prospect classification failed")
        app.advance_free_agent_market()
        assert_true(blue_chip.player_talent_alerted and blue_chip.player_talent_window_until > app.month, "Player did not receive a blue-chip scouting window")
        # Newly available fighters now receive one player-only market month.
        # Advance every ordinary candidate past that grace period so this probe
        # verifies the AI market itself without touching the protected blue chip.
        for fighter in app.free_agents:
            if fighter is not blue_chip:
                fighter.player_talent_window_until = min(getattr(fighter, "player_talent_window_until", 0), app.month - 1)
        for _ in range(4):
            app.ai_create_contract_offers()
        assert_true(any(fighter.ai_offer_company and fighter.ai_offer_purse > 0 for fighter in app.free_agents), "AI signing market did not create a visible rival offer")
        assert_true(not blue_chip.ai_offer_company, "AI bid during the player-exclusive scouting window")
        blue_chip.player_talent_window_until = app.month - 1
        # Make a lawful RIZIN lightweight lane for the post-window priority
        # offer. The seeded database can start several fighters over the normal
        # division cap, so one removal is not necessarily a usable offer slot.
        for fighter in app.free_agents:
            if fighter.ai_offer_company == rizin.name:
                app.clear_ai_contract_offer(fighter)
        # Treat the probe company as a large, well-funded operator. The seed
        # roster intentionally starts RIZIN above its normal small-company cap;
        # that is not a legal environment for testing an additional signing.
        rizin.size = max(80, rizin.size)
        while sum(fighter.gender == "Male" and fighter.weight == "Lightweight" for fighter in rizin.roster) >= app.ai_division_target(rizin) + 1:
            rizin_slot = next(fighter for fighter in rizin.roster if fighter.gender == "Male" and fighter.weight == "Lightweight" and not fighter.champion and not fighter.interim_champion)
            rizin.roster.remove(rizin_slot)
            rizin_slot.contract_months = 0
            rizin_slot.exclusive = False
            rizin_slot.contract_type = "Free Agent"
            app.free_agents.append(rizin_slot)
        rizin.cash = max(rizin.cash, 10_000_000)
        # Isolate the priority path being tested. Existing seeded blue chips
        # retain their player windows; this probe is the one whose window has
        # just expired and should therefore receive the next eligible offer.
        for fighter in app.free_agents:
            if fighter is not blue_chip and app.is_blue_chip_prospect(fighter):
                fighter.player_talent_window_until = app.month + 12
        app.ai_create_contract_offers()
        assert_true(bool(blue_chip.ai_offer_company), "Blue-chip prospect did not receive a priority AI offer after the scouting window")
        showcase_fighters = []
        # A valid five-fight card can be made across divisions; each bout
        # remains gender and weight-class matched.
        for weight in ("Flyweight", "Bantamweight", "Featherweight", "Lightweight", "Welterweight"):
            for _ in range(2):
                candidate = app.create_generated_fighter(8, 18, 58, 72, gender="Female", weight=weight)
                candidate.free_agent_months = 2
                showcase_fighters.append(candidate)
        app.free_agents.extend(showcase_fighters)
        showcase_counter = app.independent_showcase_counter
        app.simulate_free_agent_showcases()
        assert_true(app.independent_showcase_counter == showcase_counter + 1, "Independent showcase did not run")
        assert_true(app.result_records and app.result_records[0].get("company") == "Independent Circuit", "Independent showcase was not recorded in results")
        assert_true(app.result_records[0].get("fights", 0) >= 5, "Independent showcase ran with fewer than five bouts")

        failed_company = next(promotion for promotion in app.promotions if promotion.name == "Absolute Championship Akhmat")
        failed_roster_before = len(failed_company.roster)
        failed_company.cash = -600_000
        failed_company.stability = 1
        failed_company.executive["rescue_capital_used"] = True
        app.month = max(app.month, 37)
        app.process_promotion_failures()
        assert_true(failed_company in app.promotions and failed_company.name not in app.defunct_promotions, "Failed promotion should survive through a distressed buyout")
        assert_true(failed_company.cash >= 2_500_000 and failed_company.stability >= 32, "Distressed buyout did not inject cash and stability")
        assert_true(len(failed_company.roster) < failed_roster_before // 2, "Distressed buyout did not shed most of the roster")
        failure_save = app.serialize_world()
        app.apply_world_data(failure_save)
        recovered_company = next((promotion for promotion in app.promotions if promotion.name == failed_company.name), None)
        assert_true(recovered_company is not None and len(recovered_company.roster) == len(failed_company.roster), "Distressed buyout did not persist correctly")

        app.enter_spectator_mode()
        assert_true(app.spectator_mode and app.player_company_name == "Spectator", "Spectator mode did not activate")
        assert_true(any(promotion.name == "BAMMA" for promotion in app.promotions), "Spectator mode did not hand BAMMA to the AI")
        observer_target = next(promotion for promotion in app.promotions if not promotion.is_regional_feeder)
        app.take_control_of_company(observer_target.name)
        assert_true(not app.spectator_mode and app.player_company_name == observer_target.name, "Taking control did not exit spectator mode")

        app.pending_custom_promotion_config = {
            "name": "Smoke Test Championship", "region": "Canada", "size": 38, "cash": 2_500_000,
            "stability": 64, "reputation": "Regional", "personality": "Seasonal", "roster_depth": 8,
            "genders": ["Male", "Female"], "weights": ["Featherweight", "Lightweight"], "theme": "UFC",
        }
        app.start_company_choice.set("Create New Promotion...")
        app.new_game()
        assert_true(app.player_company_name == "Smoke Test Championship" and app.company_show_personality == "Seasonal",
                    "Create-promotion mode lost its identity or event philosophy")
        assert_true(len(app.roster) == 32 and {fighter.weight for fighter in app.roster} == {"Featherweight", "Lightweight"},
                    "Create-promotion mode did not respect selected roster depth and divisions")
        assert_true(any(promotion.name == "BAMMA" for promotion in app.promotions),
                    "Create-promotion mode removed the original database promotion instead of handing it to AI")
        assert_true(all(key in app.closed_divisions for key in set(app.blank_belts()) - {app.belt_key(gender, weight) for gender in ("Male", "Female") for weight in ("Featherweight", "Lightweight")}),
                    "Create-promotion mode silently reopened unselected divisions")
        custom_save = app.serialize_world()
        app.apply_world_data(custom_save)
        assert_true(app.player_company_name == "Smoke Test Championship" and app.company_show_personality == "Seasonal" and len(app.roster) == 32,
                    "Custom promotion did not survive a save round-trip")

        app.pending_custom_promotion_config = {
            "name": "Northern Women's Fighting", "region": "Canada", "size": 22, "cash": 800_000,
            "stability": 58, "reputation": "Local", "personality": "Prospect Builder", "roster_depth": 8,
            "genders": ["Female"], "weights": ["Flyweight"], "theme": "UFC",
        }
        app.start_company_choice.set("Create New Promotion...")
        app.new_game()
        active_key = app.belt_key("Female", "Flyweight")
        app.refresh_assistant()
        assert_true(app.assistant_kpis["divisions"].cget("text") == "0 thin",
                    "Weekly Assistant reports deliberately closed divisions as roster shortages")
        assert_true(len(app.roster) == 8 and all(fighter.gender == "Female" and fighter.weight == "Flyweight" for fighter in app.roster),
                    "Limited custom promotion generated fighters outside its selected division")
        assert_true(not any(app.belts.values()),
                    "Limited custom promotion appointed a champion instead of leaving the selected title vacant")
        assert_true(any(message.get("subject") == f"Vacant Championship - {active_key}" and not message.get("resolved", False)
                        for message in app.inbox),
                    "Limited custom promotion did not alert the player about its vacant championship")
        assert_true(app.fanbase.get("home_region") == "Canada" and app.event_name.get().startswith("Northern Women's Fighting 1"),
                    "Custom promotion inherited the database company's fanbase or event identity")
        app.enter_spectator_mode()
        custom_ai = next(promotion for promotion in app.promotions if promotion.name == "Northern Women's Fighting")
        app.ensure_all_company_champions()
        app.seed_opening_ai_division_depth()
        for _ in range(20):
            app.simulate_ai_promotion_month(custom_ai, develop=False)
        assert_true(all(fighter.gender == "Female" and fighter.weight == "Flyweight" for fighter in custom_ai.roster),
                    "AI handoff or monthly simulation reopened a custom promotion's closed divisions")
        app.take_control_of_company(custom_ai.name)
        assert_true(app.closed_divisions == set(app.blank_belts()) - {active_key},
                    "Taking control did not restore the custom promotion's division restrictions")
        closed_market_fighter = next(
            fighter for fighter in app.free_agents
            if app.belt_key(fighter.gender, fighter.weight) in app.closed_divisions
        )
        app.refresh_market()
        closed_row = next(
            row_id for row_id, fighter in app.market_tree_fighters.items()
            if fighter is closed_market_fighter
        )
        assert_true(app.market_tree.item(closed_row, "values")[1] == "DIVISION CLOSED",
                    "Free-agent market does not clearly identify a closed player division")
        assert_true("You may still sign them" in app.market_scout_summary(closed_market_fighter),
                    "Free-agent scout panel does not explain closed-division signings")

        roster_fighter = next(fighter for fighter in app.roster if not fighter.retired)
        original_closed = set(app.closed_divisions)
        closed_key = app.belt_key(roster_fighter.gender, roster_fighter.weight)
        app.closed_divisions.add(closed_key)
        app.roster_gender_filter.set("All")
        app.weight_filter.set("All")
        app.roster_status_filter.set("All")
        app.refresh_roster()
        roster_row = next(
            row_id for row_id, fighter in app.roster_tree_fighters.items()
            if app.fighter_identity_key(fighter) == app.fighter_identity_key(roster_fighter)
        )
        assert_true(
            app.roster_tree.item(roster_row, "values")[-1] == "DIVISION CLOSED - MOVE REQUIRED",
            "A contracted fighter in a closed division is not visible with a clear roster warning",
        )
        assert_true(
            roster_fighter.weight in app.player_roster_filter_weights(roster_fighter.gender),
            "The roster weight filter hides an occupied closed division",
        )
        assert_true(
            roster_fighter.weight not in app.player_weight_move_targets(roster_fighter),
            "The weight-change picker offers the fighter's closed division as a destination",
        )
        app.closed_divisions = original_closed
        app.refresh_roster()

        title_holder = app.roster[0]
        title_challenger = next(fighter for fighter in app.roster if fighter is not title_holder)
        title_holder.champion = True
        title_challenger.champion = False
        title_challenger.interim_champion = False
        holder_role, challenger_role = app.fight_corner_title_statuses(
            {"title": True, "divisional_title": True, "interim": False}, title_holder, title_challenger,
        )
        assert_true(holder_role == "UNDISPUTED CHAMPION" and challenger_role == "TITLE CHALLENGER",
                    "Fight-night title presentation does not distinguish the champion from the challenger")
        app.rules["live_auto_play_card"] = True
        app.rules["live_follow_commentary"] = False
        serialized_preferences = app.serialize_world()["rules"]
        assert_true(serialized_preferences["live_auto_play_card"] is True and serialized_preferences["live_follow_commentary"] is False,
                    "Fight-night viewer preferences are not persisted with the save")

        rival_fighter = next(fighter for promo in app.promotions for fighter in promo.roster if not fighter.retired)
        saved_reports = dict(app.scouting_reports)
        app.rules["scouting_mode"] = True
        rival_report_key = rival_fighter.fighter_id
        app.scouting_reports.pop(rival_report_key, None)
        app.scouting_reports.pop(rival_fighter.name, None)
        assert_true(not app.fighter_profile_stats_visible(rival_fighter, app.promotions[0].name),
                    "Unscouted rival profile still exposes private ratings")
        assert_true(app.start_scout_report_for_fighter(rival_fighter, "basic"),
                    "A rival-promotion fighter cannot be scouted from their profile")
        assert_true(app.scouting_reports[rival_report_key]["status"] == "In progress",
                    "Rival profile scouting did not create a report")
        profile_windows_before = set(root.winfo_children())
        app.open_fighter_profile_window(rival_fighter)
        root.update_idletasks()
        rival_windows = [child for child in root.winfo_children() if child not in profile_windows_before and isinstance(child, tk.Toplevel)]
        assert_true(rival_windows, "Unscouted rival fighter could not open a profile")
        def nested_widgets(parent):
            children = []
            for child in parent.winfo_children():
                children.append(child)
                children.extend(nested_widgets(child))
            return children
        profile_buttons = [widget.cget("text") for window in rival_windows for widget in nested_widgets(window) if widget.winfo_class() == "TButton"]
        assert_true("Basic Dossier" in profile_buttons and "Full Evaluation" in profile_buttons and "Observe Next Fight" in profile_buttons,
                    "Unscouted rival profile does not expose scout actions")
        for child in rival_windows:
            child.destroy()
        app.scouting_reports = saved_reports

        assert_true(app.player_bout_purse_factor({"tier": "Main Card"}) == 1.0, "Main-card player purse factor changed")
        assert_true(app.player_bout_purse_factor({"tier": "Prelims"}) == 0.75, "Player prelim purse reduction missing")
        assert_true(app.player_bout_purse_factor({"tier": "Early Prelims"}) == 0.55, "Player early-prelim purse reduction missing")
        finance_probe = app.calculate_event_finance(
            45, 55_000, {"venue": "Regional Arena", "broadcaster": "No Coverage", "fights": []}, [],
            contracted_fighter_pay=100_000,
        )
        assert_true(finance_probe["tier_purse_savings"] > 0 and finance_probe["contracted_fighter_pay"] > finance_probe["fighter_pay"],
                    "Player lower-card savings are not reflected in event finance")

        import persistence
        original_active_path = app.active_save_path
        original_showinfo = persistence.messagebox.showinfo
        original_askyesno = persistence.messagebox.askyesno
        original_save_slot_dir = app.save_slot_dir
        original_save_name = app.save_slot_name.get()
        original_active_name = app.active_save_name
        with tempfile.TemporaryDirectory(prefix="mma_warriors_quick_save_") as temp_dir:
            quick_path = Path(temp_dir) / "savegame.json"
            app.active_save_path = lambda: quick_path
            persistence.messagebox.showinfo = lambda *_args, **_kwargs: None
            try:
                assert_true(app.save_game(), "Quick save reported failure")
            finally:
                app.active_save_path = original_active_path
                persistence.messagebox.showinfo = original_showinfo
            quick_data = json.loads(quick_path.read_text(encoding="utf-8"))
            assert_true(quick_data.get("_save_meta", {}).get("slot_name") == app.active_save_name,
                        "Quick save did not write a valid save payload")
            app.save_slot_name.set("")
            app.set_active_save_name("Do Not Autofill")
            assert_true(app.save_slot_name.get() == "", "Active save name leaked into the save-slot destination field")
            slot_root = Path(temp_dir) / "Existing Slot"
            slot_root.mkdir()
            existing_slot = slot_root / "savegame.json"
            existing_slot.write_text('{"preserve": true}', encoding="utf-8")
            app.save_slot_dir = lambda _name=None, create=True, group=None: slot_root
            app.save_slot_name.set("Existing Slot")
            persistence.messagebox.askyesno = lambda *_args, **_kwargs: False
            app.save_selected_slot()
            assert_true(existing_slot.read_text(encoding="utf-8") == '{"preserve": true}',
                        "Declining a save-slot overwrite still changed the existing save")
        app.active_save_path = original_active_path
        app.save_slot_dir = original_save_slot_dir
        app.save_slot_name.set(original_save_name)
        app.set_active_save_name(original_active_name)
        persistence.messagebox.showinfo = original_showinfo
        persistence.messagebox.askyesno = original_askyesno

        print("SMOKE TEST PASSED")
        print(f"Roster: {len(app.roster)} | Free agents: {len(app.free_agents)} | Promotions: {promotion_names} | Gyms: {len(app.gyms)}")
        print(f"Sample fight: {winner.name} def. {loser.name} by {method} R{round_no}")
    finally:
        root.destroy()


if __name__ == "__main__":
    try:
        main()
    except Exception as exc:
        print(f"SMOKE TEST FAILED: {exc}", file=sys.stderr)
        raise
