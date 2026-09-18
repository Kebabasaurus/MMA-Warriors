"""Observe actual chain decisions; previews are not guaranteed legal completions."""
import argparse
from collections import Counter
from copy import deepcopy
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import fight_moves
from analysis.fight_candidate_context import candidate_context
from analysis.compare_candidate_striking import fixture_schedule
from analysis.generate_chain_opportunity_report import inspect_trace
from analysis.generate_variety_opportunity_report import (
    TerminalRngHarness, final_selection_pool, source_fingerprints,
)
from fight_engine_audit import run_audited_fight, synthetic_fighter
from fight_moves.submission_identity import compatible_submission_ids, SUBMISSION_PARENT_ACTIONS
from tools.move_registry_parity import canonical_bytes, build_dump


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


class ChainSelectionHarness(TerminalRngHarness):
    """Delegate every real call once, keeping observations outside fight state."""
    def _simulate_fight_with_caches(self, *args):
        self.decisions = {}
        self._decision = self._selection = None
        return super()._simulate_fight_with_caches(*args)

    def choose_action(self, fighter, opponent, state, round_no, tick):
        key = (round_no, tick, self.fight_state_key(fighter, state))
        row = dict(chain=deepcopy((state.get('move_chains') or {}).get(key[2], {})))
        if key in self.decisions:
            raise ValueError('Duplicate action observation')
        previous = self._decision
        self._decision = row
        try:
            chosen = super().choose_action(fighter, opponent, state, round_no, tick)
            row['chosen_action'] = chosen
            self.decisions[key] = row
            return chosen
        finally:
            self._decision = previous

    def _chain_action_bonuses(self, *args):
        result = super()._chain_action_bonuses(*args)
        if self._decision is not None:
            # Copy before prepared intent can mutate the returned dictionary.
            self._decision['preview_bonuses'] = dict(result)
        return result

    def _chain_action_weights(self, *args):
        result = super()._chain_action_weights(*args)
        if self._decision is not None:
            self._decision['tickets'] = {k: max(1, int(v)) for k, v in result.items()}
        return result

    def select_exchange_move(self, actor, defender, action, position, target, state, **kwargs):
        key = (state['round'], state['tick'], self.fight_state_key(actor, state))
        row = self.decisions.get(key)
        if row is None:
            raise ValueError('Named selection without action observation')
        previous = self._selection
        self._selection = row
        row['selection_chain_before'] = deepcopy((state.get('move_chains') or {}).get(key[2], {}))
        row['resolved_technique'] = deepcopy(kwargs.get('resolved_technique'))
        try:
            result = super().select_exchange_move(actor, defender, action, position, target, state, **kwargs)
            row['selected_move'] = result['move_id']
            row['named_chain_id'] = result.get('sequence_occurrence_id', '')
            return result
        finally:
            self._selection = previous

    def _move_candidates(self, *args):
        result = super()._move_candidates(*args)
        if self._selection is not None:
            self._selection['context_candidate_ids'] = [d.move_id for d in result[0]]
        return result

    def _move_static_score(self, actor, definition, *args):
        result = super()._move_static_score(actor, definition, *args)
        if self._selection is not None:
            self._selection['last_scored_id'] = definition.move_id
            if result is None:
                self._selection.setdefault('static_rejected_ids', []).append(definition.move_id)
        return result

    def _move_rarity_gate(self, *args):
        result = super()._move_rarity_gate(*args)
        if self._selection is not None and not result:
            self._selection.setdefault('rarity_rejected_ids', []).append(self._selection['last_scored_id'])
        return result

    def _select_from_pool(self, eligible, active_counter, signature_moves, chain_candidates,
                          active_chain, identity, action, position, target, state):
        pool, kind = final_selection_pool(eligible, active_counter, signature_moves,
                                         chain_candidates, active_chain, expanded=True)
        row = self._selection
        if row is None:
            raise ValueError('Final pool without selector scope')
        row.update(eligible_ids=[d.move_id for _, d in eligible],
                   chain_candidates=sorted(chain_candidates), pool=list(pool), pool_kind=kind,
                   selector_chain=deepcopy(active_chain))
        selected = super()._select_from_pool(eligible, active_counter, signature_moves,
                                             chain_candidates, active_chain, identity,
                                             action, position, target, state)
        if selected.move_id not in pool:
            raise ValueError('Observed pool disagrees with selector')
        return selected


def classify(row, root_id):
    """Disjoint final-selection stages; never infer precise upstream rejection."""
    chain = row.get('selector_chain', row.get('selection_chain_before', {}))
    options = set(chain.get('branch_options') or (chain.get('next_move_id'),))
    if chain.get('occurrence_id') != root_id:
        return 'root_changed_or_cleared_before_named_selection'
    context_ids = options.intersection(row.get('context_candidate_ids', ()))
    if not context_ids:
        return 'no_context_compatible_successor'
    if (row.get('chosen_action') in SUBMISSION_PARENT_ACTIONS
            and row.get('resolved_technique') is not None and not context_ids.intersection(
                compatible_submission_ids(row['resolved_technique']))):
        return 'resolved_hold_incompatible_with_successors'
    if context_ids.issubset(row.get('static_rejected_ids', ())):
        return 'all_context_successors_static_rejected'
    rejected = set(row.get('static_rejected_ids', ())) | set(row.get('rarity_rejected_ids', ()))
    if context_ids.issubset(rejected):
        return 'all_context_successors_static_or_rarity_rejected'
    live = set(row.get('chain_candidates', ()))
    eligible = live.intersection(row.get('eligible_ids', ()))
    if not live:
        return 'context_successors_absent_from_live_chain_pool'
    if not eligible:
        return 'successors_rejected_before_final_pool'
    if not eligible.intersection(row.get('pool', ())):
        return 'eligible_successors_excluded_by_' + row.get('pool_kind', 'unknown')
    if row.get('selected_move') not in options:
        return 'successor_in_pool_but_other_move_selected'
    return 'successor_selected_without_recorded_completion'


def inspect_decisions(trace, decisions):
    rows = inspect_trace(trace)
    events = [e for e in trace if e.get('type') == 'exchange']
    for event in events:
        observed = decisions.get((event['round'], event['tick'], event['actor']))
        if observed is None or observed.get('chosen_action') != event['action']:
            raise ValueError('Missing or mismatched live decision')
    roots = {}
    for index, event in enumerate(events):
        occurrence = event.get('sequence_occurrence_id')
        if occurrence and (int(event.get('chain_depth', 0) or 0) >= 2
                           or (event.get('move_sequence') or {}).get('continuation_available')):
            roots.setdefault(occurrence, index)
    if not rows:
        return []  # Same round-two-bout denominator as the established report.
    if len(roots) != len(rows):
        raise ValueError('Root denominator mismatch')
    output = []
    for (occurrence, index), original in zip(roots.items(), rows):
        root = events[index]
        following = next((e for e in events[index + 1:] if e['actor'] == root['actor']), None)
        item = dict(root_id=occurrence, root_move_id=root['move_id'],
                    stage=original['stage_loss_reason'])
        if item['stage'] in {'undeclared_other_action', 'declared_action_no_named_completion'}:
            key = (following['round'], following['tick'], following['actor'])
            observed = decisions.get(key)
            if observed is None or observed['chosen_action'] != following['action']:
                raise ValueError('Missing or mismatched live decision')
            item['decision'] = observed
            if item['stage'] == 'undeclared_other_action':
                bonuses, tickets = observed.get('preview_bonuses', {}), observed.get('tickets', {})
                if not tickets:
                    item['detail'] = 'no_weighted_menu_observed'
                elif not bonuses:
                    item['detail'] = 'no_positive_continuation_preview'
                else:
                    item['detail'] = 'positive_preview_but_other_action_chosen'
                    item['preview_action_probability'] = sum(tickets.get(k, 0) for k in bonuses) / sum(tickets.values())
                    item['chosen_action_probability'] = tickets[observed['chosen_action']] / sum(tickets.values())
            else:
                item['detail'] = classify(observed, occurrence)
        output.append(item)
    return output


def fingerprints():
    result = source_fingerprints()
    for name in ('analysis/chain_selection_diagnostics.py', 'analysis/generate_chain_opportunity_report.py',
                 'analysis/gift_wrap_mount_candidate.py'):
        result[name] = hashlib.sha256((ROOT / name).read_bytes()).hexdigest()
    return result


def build_report(fights=300, *, gift_wrap_mount=False):
    schedule = fixture_schedule(fights)
    sources, rng = fingerprints(), random.getstate()
    bouts, all_rows = [], []
    with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=gift_wrap_mount):
        registry_hash = digest(build_dump(fight_moves))
        for index, fixture in enumerate(schedule):
            spec = fixture['spec']
            a = synthetic_fighter(fixture['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
            b = synthetic_fighter(fixture['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
            a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
            before = digest([asdict(a), asdict(b), fixture])
            control, observer = TerminalRngHarness(), ChainSelectionHarness()
            plain = run_audited_fight(control, a, b, fixture['seed'], spec['fight'])
            observed = run_audited_fight(observer, a, b, fixture['seed'], spec['fight'])
            if plain != observed or control.terminal_rng_states != observer.terminal_rng_states:
                raise ValueError(f'Instrumentation changed bout {index}')
            if before != digest([asdict(a), asdict(b), fixture]):
                raise ValueError('Input mutation')
            rows = inspect_decisions(observed['trace'], observer.decisions)
            all_rows.extend(dict(row, bout_index=index, seed=fixture['seed'], spec_id=spec['id']) for row in rows)
            bouts.append(dict(bout_index=index, seed=fixture['seed'], spec_id=spec['id'],
                              input_sha256=before, audit_sha256=digest(observed),
                              terminal_rng_sha256=digest(observer.terminal_rng_states), parity=True))
        if registry_hash != digest(build_dump(fight_moves)):
            raise ValueError('Registry mutation')
    if rng != random.getstate() or sources != fingerprints():
        raise ValueError('Caller RNG or source changed')
    probability_rows = [r for r in all_rows if 'preview_action_probability' in r]
    return dict(scope='Read-only combined candidate; positive preview is not guaranteed final legality',
                fights=fights, gift_wrap_mount=gift_wrap_mount, attempted_roots=len(all_rows),
                stages=dict(Counter(r['stage'] for r in all_rows)),
                details=dict(Counter(r['detail'] for r in all_rows if 'detail' in r)),
                mean_preview_probability_on_other_choices=(sum(r['preview_action_probability'] for r in probability_rows)
                                                           / len(probability_rows) if probability_rows else None),
                all_bout_parity=True, registry_sha256=registry_hash, source_sha256=sources,
                bouts=bouts, roots=all_rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fights', type=int, default=300)
    parser.add_argument('--gift-wrap-mount', action='store_true')
    parser.add_argument('--output', type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    report = build_report(args.fights, gift_wrap_mount=args.gift_wrap_mount)
    if args.output:
        with args.output.open('x', encoding='utf-8') as stream:
            json.dump(report, stream, indent=2)
            stream.write('\n')
    print(json.dumps({k: v for k, v in report.items() if k not in {'roots', 'bouts', 'source_sha256'}}, indent=2))


if __name__ == '__main__':
    main()
