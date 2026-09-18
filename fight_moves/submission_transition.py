"""Authored adjacent-hold geometry; a changed name alone is not a chain."""
PAIRS = {
    'guard': frozenset({('triangle choke', 'armbar'), ('triangle choke', 'omoplata'),
                        ('armbar', 'triangle choke'), ('armbar', 'kimura'),
                        ('kimura', 'armbar'), ('omoplata', 'triangle choke')}),
    'top': frozenset({('americana', 'straight armbar'), ('americana', 'kimura'),
                      ('kimura', 'straight armbar'), ('straight armbar', 'americana'),
                      ('straight armbar', 'kimura')}),
}


def transition_identity(technique):
    if not isinstance(technique, dict):
        return None
    fact = technique.get('transition')
    if not isinstance(fact, dict):
        return None
    kind = fact.get('kind')
    if not all(isinstance(fact.get(key), str) for key in ('kind', 'from', 'to')):
        return None
    if (fact.get('from'), fact.get('to')) not in PAIRS.get(kind, ()):
        return None
    if str(technique.get('name', '')).casefold() != fact.get('to'):
        return None
    if (any(type(fact.get(key)) is not int or fact[key] <= 0 for key in ('root_tick', 'tick', 'round'))
            or fact['tick'] != fact['root_tick'] + 1 or fact.get('actor') not in {'a', 'b'}
            or fact.get('top') not in {'a', 'b'} or fact.get('bottom') not in {'a', 'b'}
            or fact['top'] == fact['bottom']):
        return None
    if kind == 'guard' and fact.get('position') == 'guard' and fact['actor'] == fact['bottom']:
        return 'guard_submission_chain'
    if (kind == 'top' and fact.get('position') in {'side control', 'mount'}
            and fact['actor'] == fact['top']):
        return 'top_submission_chain'
    return None
