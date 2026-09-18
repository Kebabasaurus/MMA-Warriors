"""Disposable 2% landed impact trial; production resolver is never rewritten."""
import ast
from contextlib import contextmanager
import inspect
import random
import textwrap
from unittest.mock import patch

import fight_engine
from fight_engine_audit import FightAuditHarness


def scale_impact(impact, action, state):
    # Use resolved target, not the legacy damage channel (body punches still
    # write head damage there). Do not scale clinch, ground or knockdown bonuses.
    if (state.get('position') in {'range', 'pocket'} and action in {'jab', 'power_punch', 'kick'}
            and state.get('last_strike_target') in {'head', 'high'}):
        return impact * 1.02
    return impact


def patched_resolver(original):
    tree = ast.parse(textwrap.dedent(inspect.getsource(original)))
    class Insert(ast.NodeTransformer):
        count = 0
        def visit_AugAssign(self, node):
            # Exactly the two landed base-impact awards, not the separate +8
            # knockdown awards or any head/body bookkeeping statements.
            if (isinstance(node.target, ast.Subscript) and isinstance(node.target.value, ast.Subscript)
                    and isinstance(node.target.value.value, ast.Name) and node.target.value.value.id == 'state'
                    and isinstance(node.target.value.slice, ast.Constant) and node.target.value.slice.value == 'damage'
                    and isinstance(node.value, ast.Name) and node.value.id == 'impact'
                    and isinstance(node.op, ast.Add)):
                self.count += 1
                addition = ast.parse('impact = _trial_scale_impact(impact, action, state)').body[0]
                return [addition, node]
            return node
    insert = Insert()
    tree = insert.visit(tree)
    if insert.count != 2:
        raise ValueError('Strike resolver changed: expected exactly two landed impact awards')
    namespace = dict(fight_engine.__dict__, _trial_scale_impact=scale_impact)
    exec(compile(ast.fix_missing_locations(tree), __file__, 'exec'), namespace)
    return namespace['resolve_strike']


@contextmanager
def standing_head_damage_trial(enabled=False):
    active = getattr(FightAuditHarness, '_standing_head_damage_trial', False)
    if active and not enabled:
        raise ValueError('Cannot disable standing head damage inside nested trial')
    rng = random.getstate()
    try:
        if active or not enabled:
            yield
        else:
            with patch.object(FightAuditHarness, 'resolve_strike', patched_resolver(FightAuditHarness.resolve_strike)), \
                 patch.object(FightAuditHarness, '_standing_head_damage_trial', True, create=True):
                yield
    finally:
        random.setstate(rng)
