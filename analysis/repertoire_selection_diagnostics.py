"""Observe actual repeated selections and unused alternatives on fixed paths."""
import argparse
from collections import Counter, defaultdict
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
from analysis.compare_candidate_striking import fixture_schedule
from analysis.fight_candidate_context import candidate_context
from analysis.generate_variety_opportunity_report import TerminalRngHarness, final_selection_pool, source_fingerprints
from fight_engine_audit import run_audited_fight, synthetic_fighter
from tools.move_registry_parity import canonical_bytes, build_dump


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


class RepertoireHarness(TerminalRngHarness):
    def _simulate_fight_with_caches(self, *args):
        self.rows = []
        self._observed_selection = None
        self._choice_context = None
        return super()._simulate_fight_with_caches(*args)

    def choose_action(self, fighter, opponent, state, round_no, tick):
        slot = self.fight_state_key(fighter, state)
        # Capture input facts, not an inferred winning random survival branch.
        before = dict(gas=state['gas'][slot], hurt=state['hurt'][slot],
                      hurt_threshold=fighter.toughness * 0.65,
                      position=state['position'], top=state.get('top'),
                      bottom=state.get('bottom'), controller=state.get('clinch_controller'))
        action = super().choose_action(fighter, opponent, state, round_no, tick)
        self._choice_context = dict(before, action=action, actor=slot, round=round_no, tick=tick)
        return action

    def select_exchange_move(self, actor, defender, action, position, target, state, **kwargs):
        slot = self.fight_state_key(actor, state)
        row = dict(actor=slot, style=self.fighter_styles(actor)[0], action=action,
                   position=position, round=state['round'], tick=state['tick'],
                   gas=state.get('gas', {}).get(slot),
                   hurt=state.get('hurt', {}).get(slot),
                   uses=dict(((state.get('move_reads') or {}).get(slot) or {}).get('moves', {})))
        row['choice_context'] = self._choice_context
        if not self._choice_context or any(self._choice_context[key] != row[key]
                                          for key in ('actor','action','round','tick')):
            raise ValueError('Choice-time context does not match named selection')
        previous, self._observed_selection = self._observed_selection, row
        try:
            selected = super().select_exchange_move(actor, defender, action, position, target, state, **kwargs)
            row['selected'] = selected['move_id']
            self.rows.append(row)
            return selected
        finally:
            self._observed_selection = previous

    def _select_from_pool(self, eligible, active_counter, signature_moves, chain_candidates,
                          active_chain, identity, action, position, target, state):
        pool, kind = final_selection_pool(eligible, active_counter, signature_moves,
                                         chain_candidates, active_chain, expanded=True)
        row = self._observed_selection
        row.update(pool=list(pool), kind=kind, scores={d.move_id: score for score,d in eligible})
        selected = super()._select_from_pool(eligible, active_counter, signature_moves, chain_candidates,
                                            active_chain, identity, action, position, target, state)
        if selected.move_id not in pool:
            raise ValueError('Reconstructed pool disagrees with actual selection')
        return selected


def summarize(rows, definitions=()):
    actions = defaultdict(Counter)
    losing = Counter()
    selected_counts, eligible_counts, offered_counts = Counter(), Counter(), Counter()
    cohorts = defaultdict(Counter)
    for row in rows:
        selected, uses, pool = row['selected'], row['uses'], row.get('pool', ())
        selected_counts[selected] += 1
        eligible_counts.update(row.get('scores', {}).keys())
        offered_counts.update(pool)
        cohort = cohorts[selected]
        cohort['pool_' + row.get('kind', 'unwrapped')] += 1
        cohort['action_' + row['action']] += 1
        cohort['position_' + row.get('position', 'unknown')] += 1
        cohort['style_' + row['style']] += 1
        cohort['round_' + str(row.get('round', 'unknown'))] += 1
        cohort['third_or_later'] += uses.get(selected, 0) >= 2
        cohort['with_alternative'] += len(pool) > 1
        choice = row.get('choice_context') or {}
        gas = choice.get('gas')
        cohort['choice_gas_' + ('unknown' if gas is None else
               'below8' if gas < 8 else '8to22' if gas < 22 else '22plus')] += 1
        counts = actions[row['action']]
        counts['selections'] += 1
        counts['third_or_later_use'] += uses.get(selected, 0) >= 2
        counts['singleton'] += len(pool) == 1
        counts['generic_or_unwrapped'] += not bool(pool)
        scores = row.get('scores', {})
        unseen = [key for key in pool if key != selected and not uses.get(key, 0)]
        near = [key for key in unseen if scores[selected] - scores[key] <= 2.2]
        if uses.get(selected, 0) >= 2 and near:
            counts['repeat_with_unseen_near_final_alternative'] += 1
            counts['repeat_near_' + row['kind']] += 1
            for key in near:
                losing[(row['style'], row['action'], selected, key)] += 1
    return dict(total_selections=len(rows),
                top_ten_move_share_pct=round(100 * sum(n for _,n in selected_counts.most_common(10)) / max(1,len(rows)),2),
                move_counts=[dict(move_id=key, selected=selected_counts[key], scored_eligible=eligible_counts[key],
                                  offered=offered_counts[key], cohorts=dict(cohorts[key]))
                             for key in sorted(set(selected_counts) | set(eligible_counts) | set(offered_counts)
                                               | {m.move_id for m in definitions if not m.deprecated},
                                               key=lambda k: (-selected_counts[k],k))],
                by_action={k:dict(v) for k,v in sorted(actions.items())},
                repeated_choice_with_near_unseen_alternatives=[
                    dict(style=key[0], action=key[1], selected=key[2], alternative=key[3], cases=count)
                    for key,count in losing.most_common(30)])


def concentration_floor(action_counts, total, definitions):
    """Fixed-action lower bound: ten IDs already cover an entire small family.

    No assumption about equal weights, skills or simultaneous eligibility is needed.
    Generic/unregistered selections invalidate an action's registry-only bound, so
    callers must reconcile real selected IDs before using it as evidence.
    """
    if total != sum(action_counts.values()) or total <= 0:
        raise ValueError('Action denominator does not reconcile')
    pools = defaultdict(set)
    for move in definitions:
        if not move.deprecated:
            pools[move.parent_action].add(move.move_id)
    return [dict(action=action, registered_ids=sorted(pools[action]),
                 selections=count, total_selections=total,
                 minimum_top_ten_pct=100 * count / total)
            for action,count in sorted(action_counts.items()) if 0 < len(pools[action]) <= 10]


def observed_concentration_bounds(rows, definitions):
    by_id = {move.move_id: move for move in definitions if not move.deprecated}
    unknown_actions = {row['action'] for row in rows
                       if row['selected'] not in by_id or
                       by_id[row['selected']].parent_action != row['action']}
    counts = Counter(row['action'] for row in rows)
    return [row for row in concentration_floor(counts,len(rows),definitions)
            if row['action'] not in unknown_actions]


def sources():
    hashes = source_fingerprints()
    hashes['analysis/repertoire_selection_diagnostics.py'] = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    hashes['analysis/gift_wrap_mount_candidate.py'] = hashlib.sha256((ROOT/'analysis/gift_wrap_mount_candidate.py').read_bytes()).hexdigest()
    for path in (ROOT/'analysis').glob('*candidate.py'):
        hashes[path.relative_to(ROOT).as_posix()] = hashlib.sha256(path.read_bytes()).hexdigest()
    return hashes


def build_report(fights=300, *, retained_damage=False):
    fixtures = fixture_schedule(fights)
    before_sources, before_rng = sources(), random.getstate()
    rows, bouts = [], []
    with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True,
                           standing_head_damage=retained_damage, kick_power=retained_damage,
                           heel_hook_identity=retained_damage, hold_transitions=retained_damage,
                           cradle_setup=retained_damage):
        registry = digest(build_dump(fight_moves))
        for index, fixture in enumerate(fixtures):
            spec = fixture['spec']
            a = synthetic_fighter(fixture['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
            b = synthetic_fighter(fixture['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
            a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
            inputs = digest([asdict(a),asdict(b),fixture])
            control, observer = TerminalRngHarness(), RepertoireHarness()
            plain = run_audited_fight(control,a,b,fixture['seed'],spec['fight'])
            observed = run_audited_fight(observer,a,b,fixture['seed'],spec['fight'])
            if plain != observed or control.terminal_rng_states != observer.terminal_rng_states:
                raise ValueError('Instrumentation changed bout')
            if inputs != digest([asdict(a),asdict(b),fixture]):
                raise ValueError('Input changed')
            if len(observer.rows) != sum(e.get('type')=='exchange' for e in observed['trace']):
                raise ValueError('Missing selection observations')
            rows.extend(dict(row,bout_index=index,seed=fixture['seed'],spec_id=spec['id']) for row in observer.rows)
            bouts.append(dict(index=index,seed=fixture['seed'],spec_id=spec['id'],
                              input_sha256=inputs,audit_sha256=digest(observed),
                              rng_sha256=digest(observer.terminal_rng_states)))
        if registry != digest(build_dump(fight_moves)):
            raise ValueError('Registry changed')
        definitions = tuple(fight_moves.MOVE_DEFINITIONS)
        floors = observed_concentration_bounds(rows,definitions)
    if sources()!=before_sources or random.getstate()!=before_rng:
        raise ValueError('Source or caller RNG changed')
    return dict(scope='Observed final pools; scored eligibility is after static/rarity gates, not all legal actions',
                retained_damage=retained_damage,
                fixed_action_concentration_bounds=floors,
                fights=fights, all_bout_parity=True, registry_sha256=registry,
                source_sha256=before_sources, **summarize(rows,definitions), bouts=bouts, observations=rows)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fights',type=int,default=300)
    parser.add_argument('--retained-damage',action='store_true',help='Current head/kick/submission combined candidate')
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    if args.output and args.output.exists():
        raise FileExistsError(args.output)
    report = build_report(args.fights, retained_damage=args.retained_damage)
    if args.output:
        with args.output.open('x',encoding='utf-8') as stream:
            json.dump(report,stream,indent=2)
            stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in {'observations','bouts','source_sha256'}},indent=2))


if __name__=='__main__':
    main()
