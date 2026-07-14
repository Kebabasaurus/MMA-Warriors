import importlib.util
import sys
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
        app = game.FightEmpireApp(root)
        assert_true(app.fight_timer_delay.get() == 2150, "Live fight default speed is not 2150 ms")
        assert_true(app.rules.get("active_fighter_target") == 1200, "New worlds must use the 1,200 active-fighter floor")
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
        ):
            assert_true(company in promotion_names, f"{company} promotion missing")
        assert_true(app.player_company_name not in promotion_names, "Player company duplicated in AI promotions")
        assert_true(len(app.roster) >= 90, "Player roster too small")
        assert_true(len(app.free_agents) >= 150, "Free agent pool too small")
        assert_true(len(app.gyms) >= 15, "Gym database too small")
        expected_sport_rosters = {
            "Boxing": 50,
            "Kickboxing": 50,
            "Muay Thai": 70,
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
        assert_true(any(fighter.primary_discipline == "Lethwei" and fighter.name == "Dave Leduc" for fighter in app.combat_sport_worlds["Muay Thai"]["roster"]), "Lethwei legends were not added to Muay Thai")
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
        assert_true(ok and len(division["roster"]) >= 10, "Player combat-sport division launch failed")
        player_card = app.run_combat_sport_card("Boxing", app.combat_sport_worlds["Boxing"], app.player_company_name, player_owned=True, target_bouts=5)
        assert_true(player_card and len(player_card["results"]) >= 4 and division.get("events"), "Player combat-sport card builder failed")
        sport_result = player_card["results"][0]
        assert_true(any(line.startswith("Camp:") for line in sport_result.get("log", [])), "Combat-sport camps are not reaching the fight log")
        assert_true(any(line.startswith("Weigh-in:") for line in sport_result.get("log", [])), "Combat-sport weigh-ins are not reaching the fight log")
        assert_true(any(line.startswith("Fight-night readiness:") for line in sport_result.get("log", [])), "Combat-sport readiness metrics are not visible")
        assert_true(sport_result.get("condition") and sport_result.get("readiness"), "Combat-sport condition/readiness telemetry missing")
        assert_true(all(log.get("heading") and log.get("lines") for log in player_card.get("fight_logs", [])), "Combat-sport live replay contract incomplete")
        feeder_promotions = [promotion for promotion in app.promotions if promotion.is_regional_feeder]
        assert_true(len(feeder_promotions) == 10, "Regional feeder promotions missing")
        assert_true(all(promotion.cash == 0 and all(fighter.age >= 16 for fighter in promotion.roster) for promotion in feeder_promotions), "Regional feeders must be non-financial and age-16 minimum")
        app.ensure_all_company_champions()
        assert_true(all(not any(fighter.champion or fighter.interim_champion for fighter in promotion.roster) for promotion in feeder_promotions), "Regional feeders should not carry championship belts")
        feeder_probe = feeder_promotions[0]
        washed_out = app.create_regional_feeder_fighter(feeder_probe.region, app.active_fighter_names(), "Male")
        washed_out.age, washed_out.record_w, washed_out.record_l, washed_out.potential = 22, 0, 14, 60
        feeder_probe.roster.append(washed_out)
        app.regional_review_underperformers(feeder_probe)
        assert_true(washed_out.retirement_pending and washed_out in feeder_probe.roster and not washed_out.retired, "Regional career review should require a final retirement fight")
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

        data = app.serialize_world()
        data["rules"]["active_fighter_target"] = 560
        for promotion in data["promotions"]:
            for fighter in promotion["roster"]:
                if fighter["name"] == "Yair Rodriguez":
                    fighter["rating_profile_version"] = 0
        for fighter in data["free_agents"]:
            if fighter["name"] == "Georges St-Pierre":
                fighter["age"] = 45
                fighter["legend_prime_age_version"] = 0
        app.apply_world_data(data)
        assert_true(app.rules.get("active_fighter_target") == 1200, "Legacy active-fighter floor was not migrated")
        assert_true(app.gym_by_name("American Top Team") is not None, "Gym load repair failed")
        yair = app.find_fighter_anywhere("Yair Rodriguez")
        assert_true(yair and yair.style == "Karate" and yair.rating_profile_version == 2, "Real-fighter rating migration failed")
        gsp = app.find_fighter_anywhere("Georges St-Pierre")
        assert_true(gsp and gsp.age == 31 and gsp.legend_prime_age_version == 1, "Legend prime-age migration failed")
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
        for _ in range(4):
            app.ai_create_contract_offers()
        assert_true(any(fighter.ai_offer_company and fighter.ai_offer_purse > 0 for fighter in app.free_agents), "AI signing market did not create a visible rival offer")
        assert_true(not blue_chip.ai_offer_company, "AI bid during the player-exclusive scouting window")
        blue_chip.player_talent_window_until = app.month - 1
        app.ai_create_contract_offers()
        assert_true(bool(blue_chip.ai_offer_company), "Blue-chip prospect did not receive a priority AI offer after the scouting window")
        showcase_a = app.create_generated_fighter(8, 18, 58, 72, gender="Female", weight="Flyweight")
        showcase_b = app.create_generated_fighter(8, 18, 58, 72, gender="Female", weight="Flyweight")
        showcase_a.free_agent_months = showcase_b.free_agent_months = 2
        app.free_agents.extend((showcase_a, showcase_b))
        showcase_counter = app.independent_showcase_counter
        app.simulate_free_agent_showcases()
        assert_true(app.independent_showcase_counter == showcase_counter + 1, "Independent showcase did not run")
        assert_true(app.result_records and app.result_records[0].get("company") == "Independent Circuit", "Independent showcase was not recorded in results")

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
