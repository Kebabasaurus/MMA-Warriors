# Fight Damage And Clinch Audit

## Damage Model

Each resolved strike updates the same fight state used by commentary and final metrics.

- Striking impact is driven by action margin, power, technique/speed where applicable, and the engine damage setting.
- Kicks use high/low kick power, speed, technique, kick defence, mobility, reflexes, and catch risk.
- Body kicks and clinch knees add body damage and gas pressure; calf/thigh kicks add separate leg damage that slows movement, kicking, shots, takedowns, and defensive mobility.
- Knockdowns add danger and damage; accumulated damage, chin, toughness, durability, composure, fatigue, knockdowns, and referee strictness determine KO/TKO risk.
- Cuts use impact, toughness, and cut immunity. Body damage and cuts have separate stoppage checks.
- Final `FIGHT METRICS` now reports head, body, leg, and cut damage alongside strikes, takedowns, submissions, control, and knockdowns.

Damage numbers are internal simulation units, not literal medical percentages. They should be judged by their effects: momentum, recovery, stoppage risk, corner stoppage, score impact, and post-fight availability.

## Clinch And Cage State

The engine tracks `clinch_controller`, `top`, and `bottom` explicitly.

- A clinch entry assigns control to the successful entrant.
- Cage control maintains the existing controller unless an opponent wins a resolved pummel/underhook reversal. The controller can work short punches, elbows, knees, takedowns, head position, and wrist control; the trapped fighter is weighted toward framing, escaping, or reversing.
- Clinch control cannot silently swap sides.
- A clinch break clears the controller and returns the fight to range.
- A completed takedown, sweep, kick catch, or explicit scramble assigns top/bottom ownership.

## Ground And Referee Logic

- Every round restarts standing.
- Ground control time is recorded only while a fighter owns top position; clinch/cage control uses the explicit clinch controller.
- Ground stand-ups require inactivity over several action ticks and a referee warning. Strikes, passes, submissions, sweeps, escapes, and stand-up attempts reset the inactivity clock.
- Position-specific recovery commentary prevents standing-clinch actions from appearing while a fighter is on the mat.

## Audit Procedure

Run `fight_text_audit.py` after any engine change. It generates 500 same-division, near-rating fights and reports method mix, metrics, empty scale fields, old stand-up phrases, repetition, and sample commentary.

For deeper tuning, compare competitive fights by tier and style rather than using a random mismatch pool. Finishes should come from action selection, skill margins, fatigue, damage, and position, never from a post-fight result override.
