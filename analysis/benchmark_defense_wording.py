"""Whole-bout paired CPU: actual former three-clause versus sixteen-clause helper."""
import ast
from copy import deepcopy
from dataclasses import asdict
import hashlib
import inspect
import json
from pathlib import Path
import random
from statistics import median
import sys
import textwrap
from time import process_time
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
import fight_engine
from analysis.fight_candidate_context import candidate_context
from analysis.compare_candidate_striking import fixture_schedule
from analysis.generate_variety_opportunity_report import TerminalRngHarness
from fight_engine_audit import run_audited_fight, synthetic_fighter
from tools.move_registry_parity import canonical_bytes


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def old_helper():
    source = textwrap.dedent(inspect.getsource(fight_engine.FightEngineMixin.commentary_defense_clause))
    tree = ast.parse(source)
    assignments = [node for node in ast.walk(tree) if isinstance(node, ast.Assign)
                   and any(isinstance(target, ast.Name) and target.id == 'options' for target in node.targets)]
    if len(assignments) != 1:
        raise ValueError('Ambiguous options assignment')
    options = assignments[0].value
    if (not isinstance(options, ast.Tuple) or len(options.elts) != 15
            or not isinstance(options.elts[0], ast.Name) or options.elts[0].id != 'first'
            or not isinstance(options.elts[1], ast.Starred)
            or not all(isinstance(node, ast.JoinedStr) for node in options.elts[2:])):
        raise ValueError('Changed defense options structure')
    options.elts = options.elts[:2]  # Remove thirteen formatted expressions before execution.
    tree.body[0].decorator_list = []
    ast.fix_missing_locations(tree)
    namespace = dict(vars(fight_engine))
    exec(compile(tree, '<prior-three-clause-helper>', 'exec'), namespace)
    return namespace['commentary_defense_clause'], hashlib.sha256(ast.dump(tree).encode()).hexdigest()


def build_report():
    paths = [ROOT/'fight_engine.py', ROOT/'fight_engine_audit.py', Path(__file__)]
    paths += list((ROOT/'fight_moves').rglob('*.py')) + list((ROOT/'analysis').glob('*candidate*.py'))
    def sources():
        return {str(p.relative_to(ROOT)).replace('\\', '/'): hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    before, rng = sources(), random.getstate()
    former, ast_hash = old_helper()
    current = fight_engine.FightEngineMixin.commentary_defense_clause
    fixtures = []
    for item in fixture_schedule(44):
        spec = item['spec']
        a = synthetic_fighter(item['a_name'], spec['a_level'], spec['a_style'], spec['a_behaviour'], 0)
        b = synthetic_fighter(item['b_name'], spec['b_level'], spec['b_style'], spec['b_behaviour'], 1)
        a.stance, b.stance = spec.get('a_stance', a.stance), spec.get('b_stance', b.stance)
        fixtures.append((a, b, item['seed'], spec['fight']))
    def inputs(): return digest([(asdict(a), asdict(b), seed, cfg) for a,b,seed,cfg in fixtures])
    input_hash = inputs()
    arms = {'old': [], 'new': []}
    for repeat in range(3):
        pairs = {}
        for name in (('old', 'new') if repeat % 2 == 0 else ('new', 'old')):
            with candidate_context(entries=True, chains=True, draft_content=True, gift_wrap_mount=True,
                                   heel_hook_identity=True, hold_transitions=True, cradle_setup=True,
                                   standing_head_damage=True, kick_power=True, survival_expansion=True), \
                    patch.object(fight_engine.FightEngineMixin, 'commentary_defense_clause',
                                 staticmethod(former if name == 'old' else current)):
                engine = TerminalRngHarness()
                audits, states = [], []
                start = process_time()
                for a,b,seed,cfg in fixtures:
                    audits.append(run_audited_fight(engine,a,b,seed,cfg))
                    states.append(engine.terminal_rng_states)
                elapsed = process_time() - start
                reduced = deepcopy(audits)
                for audit in reduced:
                    for event in audit['trace']:
                        event.pop('commentary', None)
                pairs[name] = (reduced, states)
                arms[name].append(dict(cpu_seconds=elapsed, audit_sha256=digest(audits),
                                       facts_sha256=digest(reduced), rng_sha256=digest(states)))
        if pairs['old'] != pairs['new']:
            raise ValueError('Non-commentary audit or terminal RNG mismatch')
    if sources() != before or inputs() != input_hash or random.getstate() != rng:
        raise ValueError('Source/input/caller RNG changed')
    old, new = (median(row['cpu_seconds'] for row in arms[name]) for name in ('old','new'))
    return dict(scope='44 identical combined440 fixtures, three alternating paired whole-bout CPU samples; small noisy sample, not career latency',
                instrumentation='AST removes13 additional options before formatting; all other helper statements preserved; comparisons remove trace commentary only',
                source_sha256=before, reconstructed_ast_sha256=ast_hash, fixture_sha256=input_hash,
                all_bout_facts_and_rng_parity=True, arms=arms, median_old_cpu_seconds=old,
                median_new_cpu_seconds=new, median_cpu_change_pct=100*(new/old-1))


if __name__ == '__main__':
    output = ROOT/'analysis/defense_wording_cpu_44.json'
    if output.exists(): raise FileExistsError(output)
    report = build_report()
    with output.open('x', encoding='utf-8') as stream: json.dump(report,stream,indent=2)
    print(json.dumps({key: value for key,value in report.items() if key.startswith('median') or key == 'all_bout_facts_and_rng_parity'}))
