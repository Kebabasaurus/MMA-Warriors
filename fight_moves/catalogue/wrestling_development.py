"""Slice 6 common-position entries and takedowns, without new resolution rolls.

The current shared resolver settles successful shots/throws in guard or half guard;
near-successes can remain on the cage. Follow-ups accommodate those actual outcomes.
"""
from ..presets import takedown
from ..schema import move, STANDING_POSITIONS

COMMON_CLINCH = frozenset({"clinch", "cage"})
SETTLED_TOP_POSITIONS = ("guard", "half guard")


def _shot(move_id, name, skills, styles, entry, follow_ups, tag="level-change"):
    return move(move_id, name, "shoot", STANDING_POSITIONS,
                attack_skills=skills, defense_skills=("sprawl", "takedown_defence_detail"),
                preferred_styles=styles, minimum_skill=50, entry_family=entry,
                defense_families=("sprawl", "whizzer", "hip pressure"),
                follow_ups=follow_ups, tags=("wrestling", "entry", tag))


SHOTS = (
    _shot("sweep_single_entry", "sweep-single entry",
          ("takedown_speed", "footwork", "takedown_setup"),
          ("Freestyle Wrestler", "Grappler"), "single leg",
          ("single_leg_finish", "knee_slice_pass", "chest_to_chest_pin")),
    _shot("low_single_entry", "low-single entry",
          ("takedown_speed", "mobility", "takedowns"),
          ("Freestyle Wrestler", "Well-Rounded"), "single leg",
          ("single_leg_finish", "hip_pressure_ride")),
    _shot("high_crotch_entry", "high-crotch entry",
          ("takedown_setup", "takedown_speed", "strength"),
          ("Wrestler", "Freestyle Wrestler", "Grappler"), "high crotch",
          ("high_crotch_finish", "body_lock_pass", "chest_to_chest_pin")),
    _shot("duck_under_single_entry", "duck-under single-leg entry",
          ("head_movement", "takedown_setup", "chain_wrestling"),
          ("Catch Wrestler", "Well-Rounded", "Grappler"), "single leg",
          ("single_leg_finish", "knee_slice_pass")),
    _shot("arm_drag_leg_entry", "arm-drag leg entry",
          ("clinch_control", "takedown_speed", "takedown_setup"),
          ("Grappler", "BJJ", "Luta Livre"), "single leg",
          ("single_leg_finish", "chest_to_chest_pin"), tag="wrist-control"),
    _shot("inside_step_double_entry", "inside-step double-leg entry",
          ("footwork", "takedowns", "chain_wrestling"),
          ("Freestyle Wrestler", "Well-Rounded", "MMA Generalist"), "double leg",
          ("double_leg_finish", "hip_pressure_ride", "knee_slice_pass")),
)


def _finish(move_id, name, skills, styles, entry, families, tag, positions=COMMON_CLINCH):
    return takedown(move_id, name, entry_family=entry,
                    finish_positions=SETTLED_TOP_POSITIONS, positions=positions,
                    styles=styles, attack_skills=skills,
                    defense_skills=("takedown_defence_detail", "scrambles", "clinch_defence"),
                    minimum_skill=52, defense_families=families, tags=(tag,),
                    follow_ups=("chest_to_chest_pin", "knee_slice_pass"))


TAKEDOWNS = (
    _finish("run_pipe_single", "run-the-pipe single-leg finish",
            ("chain_wrestling", "takedowns", "clinch_control"),
            ("Freestyle Wrestler", "Grappler", "Well-Rounded"), "single leg",
            ("whizzer", "limp leg", "balance"), "chain"),
    _finish("treetop_single_finish", "treetop single-leg finish",
            ("takedowns", "strength", "clinch_control"),
            ("Wrestler", "Freestyle Wrestler", "Sambo"), "single leg",
            ("hop", "limp leg", "balance"), "wrestling", positions={"clinch"}),
    _finish("corner_turn_double", "corner-turn double-leg finish",
            ("chain_wrestling", "takedown_speed", "footwork"),
            ("Freestyle Wrestler", "Well-Rounded", "Grappler"), "double leg",
            ("sprawl", "fence post", "underhook"), "chain"),
    _finish("timed_foot_sweep", "timed foot sweep",
            ("throws", "clinch_takedowns", "reflexes"),
            ("Judo", "Sanda", "Well-Rounded"), "over-under",
            ("base", "hop", "hip turn"), "trip"),
    _finish("ankle_block_takedown", "body-lock ankle-block takedown",
            ("clinch_takedowns", "clinch_control", "cage_wrestling"),
            ("Sambo", "Grappler", "Wrestler"), "body lock",
            ("wide base", "underhook", "hip turn"), "trip"),
    _finish("inner_thigh_throw", "inner-thigh throw",
            ("throws", "clinch_control", "clinch_takedowns"),
            ("Judo", "Sambo", "Grappler"), "underhook",
            ("hip block", "back step", "balance"), "throw", positions={"clinch"}),
    _finish("sweeping_hip_throw", "sweeping hip throw",
            ("throws", "strength", "clinch_takedowns"),
            ("Judo", "Sambo", "Well-Rounded"), "over-under",
            ("hip block", "back step", "underhook"), "throw", positions={"clinch"}),
)


WRESTLING_DEVELOPMENT = (*SHOTS, *TAKEDOWNS)
