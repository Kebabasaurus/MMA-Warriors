"""Reconcile recorded variety with opportunity counts; never change gameplay."""
import argparse
from collections import defaultdict
import hashlib
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))
from analysis.generate_variety_opportunity_report import maximum_distinct_matching


def summarize(rows):
    count = len(rows)
    return dict(fighters=count, mean_selections=sum(r['selections'] for r in rows)/max(1,count),
                mean_distinct=sum(r['distinct'] for r in rows)/max(1,count),
                mean_fixed_pool_bound=sum(r['bound'] for r in rows)/max(1,count),
                fewer_than_20_selections=sum(r['selections']<20 for r in rows),
                fixed_pool_bound_below_20=sum(r['bound']<20 for r in rows),
                actual_at_least_20=sum(r['distinct']>=20 for r in rows))


def analyze(record, inventory):
    if not record.get('all_bout_parity'):
        raise ValueError('Source lacks full-bout observation parity')
    if record['registry_sha256'] != inventory['registry_sha256']:
        raise ValueError('Observation and inventory registries differ')
    indices = [b['index'] for b in record['bouts']]
    if indices != list(range(record['fights'])) or not indices:
        raise ValueError('Incomplete or unordered bout inventory')
    selections = defaultdict(list)
    identities = set()
    for event in record['observations']:
        index, actor = event['bout_index'], event['actor']
        if index not in range(record['fights']) or actor not in ('a', 'b'):
            raise ValueError('Invalid bout or actor')
        identity = (index, event['round'], event['tick'], actor)
        if identity in identities:
            raise ValueError('Duplicate selection observation')
        identities.add(identity)
        pool = event.get('pool') or [event['selected']]
        if event['selected'] not in pool:
            raise ValueError('Selected move not in observed final pool')
        selections[index, actor].append(event)
    fighters, offered = [], set()
    for index in indices:
        for actor in ('a', 'b'):
            events = selections[index, actor]
            pools = [r.get('pool') or [r['selected']] for r in events]
            for pool in pools:
                offered.update(pool)
            fighters.append(dict(bout=index, actor=actor, selections=len(events),
                                 style=events[0]['style'] if events else 'unknown',
                                 distinct=len({r['selected'] for r in events}),
                                 bound=maximum_distinct_matching(pools)))
    overall = summarize(fighters)
    if abs(overall['mean_distinct'] - inventory['mean_distinct_moves_per_fighter']) > .0001:
        raise ValueError('Observed distinct mean does not reconcile to coverage')
    cohorts = {}
    for name, low, high in (('0-9',0,9),('10-19',10,19),('20-29',20,29),('30-44',30,44),('45+',45,float('inf'))):
        cohorts[name] = summarize([r for r in fighters if low<=r['selections']<=high])
    unused = inventory['unobserved_active_move_ids']
    return dict(scope='Derived from recorded mount-refined paths, not fresh simulation or universal feasibility',
                overall=overall, selection_count_cohorts=cohorts,
                styles={style:summarize([r for r in fighters if r['style']==style])
                        for style in sorted({r['style'] for r in fighters})},
                unused_offered_in_final_pool=sorted(set(unused)&offered),
                unused_never_in_final_pool=sorted(set(unused)-offered), fighters=fighters)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--observations',type=Path,default=ROOT/'analysis/mount_repertoire_selection_300.json')
    parser.add_argument('--coverage',type=Path,default=ROOT/'analysis/joint_candidate_gift_wrap_mount_coverage.json')
    parser.add_argument('--output',type=Path,required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    inputs = {str(path):path.read_bytes() for path in (args.observations,args.coverage)}
    report = analyze(json.loads(inputs[str(args.observations)]),json.loads(inputs[str(args.coverage)])['arms']['combined'])
    report['input_sha256'] = {name:hashlib.sha256(data).hexdigest() for name,data in inputs.items()}
    report['analysis_source_sha256'] = {str(path):hashlib.sha256(path.read_bytes()).hexdigest() for path in
        (Path(__file__),ROOT/'analysis/generate_variety_opportunity_report.py')}
    if any(Path(name).read_bytes()!=data for name,data in inputs.items()):
        raise ValueError('Inputs changed during analysis')
    with args.output.open('x',encoding='utf-8') as stream:
        json.dump(report,stream,indent=2)
        stream.write('\n')
    print(json.dumps({k:v for k,v in report.items() if k not in ('fighters','styles')},indent=2))


if __name__=='__main__':
    main()
