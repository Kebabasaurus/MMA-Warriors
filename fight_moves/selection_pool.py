"""Bounded ordinary repertoire, applied only after all move eligibility gates."""


def ordinary_selection_pool(rows, chain_candidates, active_chain, expanded=False):
    """Keep established top-five chains; admit only close ordinary alternatives.

    Rows are already ranked and counter-filtered. Extra choices must be within
    three existing 2.2-point weight half-lives of the strongest score. The cap
    of eight bounds work; no score, move identity or random stream is changed.
    Authored singleton priority is handled by the caller before this helper.
    """
    pool = rows[:5]
    continuations = [row for row in pool if row[1].move_id in chain_candidates]
    if continuations:
        preferred = [row for row in continuations if row[1].move_id == active_chain.get('next_move_id')]
        return preferred or continuations, 'chain'
    if expanded and pool:
        pool = pool + [row for row in rows[5:8] if pool[0][0] - row[0] <= 6.6]
    return pool, 'ordinary'
