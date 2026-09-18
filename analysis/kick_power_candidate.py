"""Disposable 1% resolved-kick power trial; production resolver is untouched."""
import ast
import inspect
import random
import textwrap
from contextlib import contextmanager
from unittest.mock import patch

from fight_engine_audit import FightAuditHarness


def scale_kick_power(value, action):
    return value * 1.01 if action == 'kick' else value


def patched_resolver(original):
    tree = ast.parse(textwrap.dedent(inspect.getsource(original)))
    class Insert(ast.NodeTransformer):
        count = 0
        def visit_Assign(self, node):
            if (len(node.targets) == 1 and isinstance(node.targets[0], ast.Name)
                    and node.targets[0].id == 'kick_margin'):
                self.count += 1
                addition = ast.parse('kick_power = _trial_scale_kick_power(kick_power, action)').body[0]
                return [addition, node]
            return node
    insert = Insert(); tree = insert.visit(tree)
    if insert.count != 1:
        raise ValueError('Strike resolver changed: expected one kick-margin assignment')
    namespace = dict(__import__('fight_engine').__dict__, _trial_scale_kick_power=scale_kick_power)
    exec(compile(ast.fix_missing_locations(tree), __file__, 'exec'), namespace)
    return namespace['resolve_strike']


@contextmanager
def kick_power_trial(enabled=False):
    active = getattr(FightAuditHarness, '_kick_power_trial', False)
    if active and not enabled:
        raise ValueError('Cannot disable kick-power trial inside nested trial')
    rng = random.getstate()
    try:
        if active or not enabled:
            yield
        elif getattr(FightAuditHarness, '_standing_head_damage_trial', False):
            original_ds = FightAuditHarness.ds
            def ds(engine, fighter, key, fallback=50):
                value = original_ds(engine, fighter, key, fallback)
                return value * 1.01 if key in {'high_kick_power', 'low_kick_power'} else value
            with patch.object(FightAuditHarness, 'ds', ds), patch.object(FightAuditHarness, '_kick_power_trial', True, create=True):
                yield
        else:
            with patch.object(FightAuditHarness, 'resolve_strike', patched_resolver(FightAuditHarness.resolve_strike)), \
                 patch.object(FightAuditHarness, '_kick_power_trial', True, create=True):
                yield
    finally:
        random.setstate(rng)
