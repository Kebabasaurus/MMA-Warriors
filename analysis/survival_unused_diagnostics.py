"""Read-only paired current-440 selector and resolved-hold frequency diagnostic."""
import argparse
from collections import Counter
from contextlib import contextmanager
import hashlib
import json
from pathlib import Path
import sys
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from analysis import repertoire_selection_diagnostics as observer


def build_report(fights=300):
    source = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    context, select = observer.candidate_context, observer.RepertoireHarness.select_exchange_move
    holds = Counter()

    @contextmanager
    def expanded(**kwargs):
        with context(**kwargs, survival_expansion=True) as definitions:
            yield definitions

    def observe(self, actor, defender, action, position, target, state, **kwargs):
        technique = kwargs.get('resolved_technique') or {}
        if technique:
            holds[(action, position, technique.get('name', ''),
                   (technique.get('transition') or {}).get('kind', ''),
                   tuple(self.fighter_styles(actor)))] += 1
        return select(self, actor, defender, action, position, target, state, **kwargs)

    with patch.object(observer, 'candidate_context', expanded), \
            patch.object(observer.RepertoireHarness, 'select_exchange_move', observe):
        report = observer.build_report(fights, retained_damage=True)
    if hashlib.sha256(Path(__file__).read_bytes()).hexdigest() != source:
        raise ValueError('Diagnostic source changed during collection')
    report['source_sha256']['analysis/survival_unused_diagnostics.py'] = source
    report['survival_expansion'] = True
    report['scope'] += '; current 440 survival candidate; explicit resolved holds; frequency only, not acceptance'
    report['resolved_hold_contexts'] = [
        dict(action=key[0], position=key[1], hold=key[2], transition=key[3],
             styles=list(key[4]), count=count)
        for key, count in sorted(holds.items())]
    report.pop('observations')
    return report


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--fights', type=int, default=300)
    parser.add_argument('--output', type=Path, required=True)
    args = parser.parse_args()
    if args.output.exists():
        raise FileExistsError(args.output)
    report = build_report(args.fights)
    with args.output.open('x', encoding='utf-8') as stream:
        json.dump(report, stream, indent=2)
        stream.write('\n')
    print(json.dumps(dict(fights=args.fights, all_bout_parity=report['all_bout_parity'],
                         missing=[row for row in report['move_counts'] if not row['selected']]), indent=2))


if __name__ == '__main__':
    main()
