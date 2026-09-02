"""Apply the second explicitly curated signature-move cohort."""

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fight_moves import MOVE_REGISTRY

DATABASE = ROOT / "Databases" / "Default Universe.universe.json"

TARGET_NAMES = {
    "Fedor Emelianenko Legend", "Wanderlei Silva", "Demetrious Johnson Legend", "Sean O'Malley",
    "Jose Aldo Legend", "Nate Diaz", "Mirko Cro Cop Legend", "Julianna Pena", "Brock Lesnar",
    "Daniel Cormier Legend", "Frankie Edgar Legend", "Mauricio Rua Legend", "Wanderlei Silva Legend",
    "Robbie Lawler Legend", "BJ Penn", "Urijah Faber Legend", "Quinton Jackson Legend", "Matt Hughes",
    "Robert Whittaker", "Tatiana Suarez", "Cris Cyborg", "Chuck Liddell", "Ronda Rousey",
    "Jiri Prochazka", "Sean Strickland", "Usman Nurmagomedov", "Dustin Poirier", "Nate Diaz",
    "Nick Diaz", "Eddie Alvarez", "Paddy Pimblett", "Ian Machado Garry", "Leon Edwards",
    "Holly Holm", "Vadim Nemkov", "Gegard Mousasi", "Takanori Gomi", "Francis Ngannou",
    "Jack Della Maddalena", "Derrick Lewis", "Belal Muhammad", "Michael Venom Page",
    "Khalil Rountree Jr.", "Yair Rodriguez", "Kyoji Horiguchi", "Michael Chandler", "Colby Covington",
    "AJ McKee", "Paul Daley", "Rodtang Jitmuangnon", "Tenshin Nasukawa", "Royce Gracie",
    "Igor Vovchanchyn", "Dan Henderson", "Cain Velasquez", "Alexander Volkov", "Cung Le",
    "Sergei Pavlovich", "Diego Lopes", "Cory Sandhagen", "Kevin Holland", "Douglas Lima",
    "Don Frye", "Mark Hunt", "Randy Couture", "Mackenzie Dern", "Charles Oliveira",
    "Tony Ferguson", "Max Holloway", "Brian Ortega", "Paulo Costa", "Israel Adesanya",
    "Alex Pereira", "Stipe Miocic", "Junior dos Santos", "Fabricio Werdum", "Alistair Overeem",
    "Ryan Hall", "Khabib Nurmagomedov", "Bo Nickal", "Ben Askren", "Jose Aldo",
}
PRESERVE_EXISTING = {"Charles Oliveira", "Tony Ferguson", "Max Holloway", "Israel Adesanya", "Alex Pereira"}

# These sets deliberately give the rare transition families a home on fighters
# whose authored identity can surface them in ordinary roster bouts. They do
# not force a position or alter the calibrated parent action.
SPECIALIST_SIGNATURES = {
    "Brian Ortega": ("anaconda_choke", "darce_choke", "guillotine_choke"),
    "Ryan Hall": ("heel_hook", "kneebar", "straight_ankle_lock"),
    "Khabib Nurmagomedov": ("lift_mat_return", "rear_waist_ride", "turtle_breakdown"),
    "Bo Nickal": ("chained_reshot", "snapdown_front_headlock", "front_headlock_go_behind"),
    "Jose Aldo": ("limp_leg_escape", "whizzer_recovery", "body_jab"),
    "Ben Askren": ("sit_out_reversal", "rear_waist_ride", "chained_reshot"),
    "Fabricio Werdum": ("toe_hold", "anaconda_choke", "guard_submission_chain"),
}

STYLE_MOVES = {
    "Boxer": ("one_two", "body_head_change", "check_hook"),
    "Kickboxer": ("cross_body_kick", "calf_kick", "head_round_kick"),
    "Dutch Kickboxer": ("hook_low_kick", "cross_body_kick", "double_jab_cross"),
    "Muay Thai": ("clinch_knee", "step_in_elbow", "body_round_kick"),
    "Karate": ("side_kick", "question_mark_kick", "slip_cross"),
    "Taekwondo": ("switch_body_kick", "wheel_kick", "head_round_kick"),
    "Sanda": ("side_kick", "outside_trip", "body_lock_trip"),
    "Wrestler": ("double_leg_entry", "double_leg_finish", "ride_wrist_punches"),
    "Freestyle Wrestler": ("single_leg_entry", "reactive_shot", "back_take_transition"),
    "Catch Wrestler": ("snapdown_front_headlock", "turtle_breakdown", "americana"),
    "BJJ": ("guard_submission_chain", "back_take_transition", "rear_naked_choke"),
    "Luta Livre": ("straight_ankle_lock", "kneebar", "darce_choke"),
    "Sambo": ("body_lock_trip", "straight_ankle_lock", "ride_control"),
    "Judo": ("hip_toss", "outside_trip", "top_armbar"),
    "Grappler": ("position_pass", "back_take_transition", "top_submission_chain"),
    "Submission Grappler": ("rear_naked_choke", "triangle_choke", "top_armbar"),
    "Well-Rounded": ("one_two", "jab_to_shot", "back_take_transition"),
    "MMA Generalist": ("cross_body_kick", "overhand_to_double", "position_pass"),
}


def main():
    payload = json.loads(DATABASE.read_text(encoding="utf-8"))
    fighters = payload["sections"]["fighters"]["all_fighters"]
    changed = 0
    for fighter in fighters:
        if fighter.get("name") not in TARGET_NAMES or fighter.get("name") in PRESERVE_EXISTING:
            continue
        moves = list(SPECIALIST_SIGNATURES.get(
            fighter.get("name"), STYLE_MOVES.get(fighter.get("style"), STYLE_MOVES["Well-Rounded"]),
        ))
        is_specialist = fighter.get("name") in SPECIALIST_SIGNATURES
        if not is_specialist and fighter.get("behaviour") == "Counter" and "slip_cross" in MOVE_REGISTRY:
            moves[-1] = "slip_cross"
        elif not is_specialist and fighter.get("behaviour") == "Dynamic Attacker" and fighter.get("style") in {
            "Muay Thai", "Kickboxer", "Dutch Kickboxer", "Karate", "Taekwondo", "Sanda",
        }:
            creative = "spinning_elbow" if fighter.get("style") == "Muay Thai" else "question_mark_kick"
            if creative in MOVE_REGISTRY:
                moves[-1] = creative
        fighter["signature_moves"] = [move_id for move_id in moves if move_id in MOVE_REGISTRY][:3]
        changed += 1
    DATABASE.write_text(json.dumps(payload, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    print(f"Authored {changed} additional signature sets")


if __name__ == "__main__":
    main()
