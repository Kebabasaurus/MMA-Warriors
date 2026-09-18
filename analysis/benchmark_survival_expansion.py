"""Paired CPU samples on actual 400/440 catalogues, with whole-bout work intact."""
import argparse
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import random
from statistics import median
import sys
from time import process_time

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0,str(ROOT))
from analysis.fight_candidate_context import candidate_context
from analysis.compare_candidate_striking import fixture_schedule
from analysis.evaluate_joint_fight_candidate import registry_fingerprint
from fight_engine_audit import FightAuditHarness, run_audited_fight, synthetic_fighter
from tools.move_registry_parity import canonical_bytes


def digest(value):
    return hashlib.sha256(canonical_bytes(value)).hexdigest()


def build_report(fights=44,repeats=3):
    if type(fights) is not int or type(repeats) is not int or min(fights,repeats)<1:
        raise ValueError('Positive integer sample sizes required')
    paths = [ROOT/'fight_engine.py',ROOT/'fight_engine_audit.py',Path(__file__)]
    paths += list((ROOT/'fight_moves').rglob('*.py')) + list((ROOT/'analysis').glob('*candidate*.py'))
    def sources():
        return {p.relative_to(ROOT).as_posix():hashlib.sha256(p.read_bytes()).hexdigest() for p in paths}
    hashes,rng = sources(),random.getstate()
    fixtures = []
    for item in fixture_schedule(fights):
        spec = item['spec']
        a = synthetic_fighter(item['a_name'],spec['a_level'],spec['a_style'],spec['a_behaviour'],0)
        b = synthetic_fighter(item['b_name'],spec['b_level'],spec['b_style'],spec['b_behaviour'],1)
        a.stance,b.stance = spec.get('a_stance',a.stance),spec.get('b_stance',b.stance)
        fixtures.append((a,b,item['seed'],spec['fight']))
    def inputs():
        return digest([(asdict(a),asdict(b),seed,config) for a,b,seed,config in fixtures])
    fixture_hash = inputs()
    arms = {'control':[],'expanded':[]}
    for repeat in range(repeats):
        for name in (('control','expanded') if repeat%2==0 else ('expanded','control')):
            with candidate_context(entries=True,chains=True,draft_content=True,gift_wrap_mount=True,
                                   heel_hook_identity=True,hold_transitions=True,cradle_setup=True,
                                   standing_head_damage=True,kick_power=True,survival_expansion=name=='expanded'):
                registry_hash = registry_fingerprint()
                harness, results = FightAuditHarness(),[]
                start = process_time()
                for a,b,seed,config in fixtures:
                    results.append(run_audited_fight(harness,a,b,seed,config))
                cpu = process_time()-start
                arms[name].append(dict(cpu_seconds=cpu,audit_sha256=digest(results),registry_sha256=registry_hash))
    if sources()!=hashes or inputs()!=fixture_hash or random.getstate()!=rng:
        raise AssertionError('Benchmark source, input or RNG changed')
    for samples in arms.values():
        if len({s['audit_sha256'] for s in samples})!=1:
            raise AssertionError('Repeated same-arm bouts differ')
    control = median(s['cpu_seconds'] for s in arms['control'])
    expanded = median(s['cpu_seconds'] for s in arms['expanded'])
    return dict(scope='Unprofiled whole-bout CPU; changed trajectories confound overhead; not whole-career latency',
                fights=fights,repeats=repeats,source_sha256=hashes,fixture_sha256=fixture_hash,arms=arms,
                median_control_cpu_seconds=control,median_expanded_cpu_seconds=expanded,
                median_cpu_change_pct=100*(expanded/control-1))


if __name__=='__main__':
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists(): raise FileExistsError(args.output)
    report = build_report()
    with args.output.open('x',encoding='utf-8') as stream: json.dump(report,stream,indent=2)
    print(report['median_cpu_change_pct'])
