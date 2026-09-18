"""Audit-only Sprawl And Brawl disengagement preference after a retained shot."""
import argparse
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import random
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis import evaluate_joint_fight_candidate as evaluator
from analysis.compare_candidate_striking import fixture_schedule
from fight_engine_audit import FightAuditHarness
from tools.move_registry_parity import canonical_bytes

ESCAPE_MULTIPLIER = 1.58


def escape_tickets(weights):
    """Reallocate the original integer budget with one ticket per legal action."""
    cleaned = {key: max(1, int(value)) for key, value in weights.items()}
    budget = sum(cleaned.values()) - len(cleaned)
    demand = {key: value * (ESCAPE_MULTIPLIER if key == 'disengage' else 1.0) - 1.0
              for key, value in cleaned.items()}
    total = sum(demand.values())
    if not budget or not total:
        return cleaned
    quotas = {key: budget * value / total for key, value in demand.items()}
    result = {key: 1 + int(quotas[key]) for key in cleaned}
    remainder = sum(cleaned.values()) - sum(result.values())
    ranked = sorted(cleaned, key=lambda key: -(quotas[key] - int(quotas[key])))
    for key in ranked[:remainder]:
        result[key] += 1
    return result


@contextmanager
def escape_intent_trial(enabled=False):
    """One non-stacking menu preference; no forced choice or added action."""
    original, rng = FightAuditHarness._chain_action_weights, random.getstate()
    def adjusted(engine, fighter, opponent, state, weights, round_no, tick):
        if (getattr(engine, '_experimental_specialist_entries', False)
                and state.get('position') == 'failed shot'
                and state.get('clinch_controller') == engine.fight_state_key(fighter, state)
                and fighter.behaviour == 'Sprawl And Brawl' and 'disengage' in weights):
            weights = escape_tickets(weights)
        return original(engine, fighter, opponent, state, weights, round_no, tick)
    adjusted._failed_shot_escape_intent = True
    try:
        if enabled and not getattr(original, '_failed_shot_escape_intent', False):
            with patch.object(FightAuditHarness, '_chain_action_weights', adjusted):
                yield
        else:
            yield
    finally:
        random.setstate(rng)


def build_report():
    """Keep the complete canonical calibration and its original failure list."""
    rng = random.getstate()
    try:
        source_names = ('fight_engine.py', 'fight_engine_audit.py', 'constants.py', 'models.py',
                        'analysis/fight_candidate_context.py', 'analysis/evaluate_joint_fight_candidate.py',
                        'analysis/compare_candidate_striking.py', 'analysis/failed_shot_escape_intent.py')
        paths = [ROOT / name for name in source_names] + sorted((ROOT / 'fight_moves').rglob('*.py'))
        hashes = {path.relative_to(ROOT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest() for path in paths}
        reference = ROOT / 'analysis/fight_engine_baseline.json'
        reference_hash = hashlib.sha256(reference.read_bytes()).hexdigest()
        schedule_hash = hashlib.sha256(canonical_bytes(fixture_schedule(calibration_corpus=True))).hexdigest()
        with escape_intent_trial(True):
            result = evaluator.calibration_trial()
        if (result['reference_sha256'] != reference_hash
                or hashlib.sha256(reference.read_bytes()).hexdigest() != reference_hash):
            raise RuntimeError('Calibration reference changed while collecting escape-intent trial')
        if any(hashlib.sha256((ROOT / name).read_bytes()).hexdigest() != value for name, value in hashes.items()):
            raise RuntimeError('Source changed while collecting escape-intent trial')
        result.update(scope='Audit-only retained-shot escape preference; calibration alone is not full-plan acceptance',
                      configuration=dict(failed_shot_controller_behaviour='Sprawl And Brawl',
                                         disengage_demand_multiplier=ESCAPE_MULTIPLIER,
                                         conserve_integer_ticket_budget=True,
                                         specialist_entries=True, chain_action_weighting=True, draft_content=True),
                      source_sha256=hashes, input_schedule_sha256=schedule_hash)
        return result
    finally:
        random.setstate(rng)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output', type=Path, help='New full-calibration artifact; existing files are never overwritten')
    args = parser.parse_args(argv)
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    result = build_report()
    if args.output:
        with args.output.open('x', encoding='utf-8') as output:
            json.dump(result, output, indent=2)
    print(json.dumps({key: result[key] for key in ('overall', 'failures')} if args.output else result, indent=2))
    return int(bool(result['failures']))


if __name__ == '__main__':
    raise SystemExit(main())
