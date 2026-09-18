"""The application fight engine: immutable profile, native methods, no audit patches.

Historical calibration hosts continue to inherit FightEngineMixin directly. This
explicit composition makes normal play independent of process-global trial scopes.
"""
from fight_engine import FightEngineMixin
from fight_release_extensions import ReleaseCradleMixin, ReleaseSubmissionChainMixin
from fight_moves.release_registry import (
    RELEASE_MOVE_DEFINITIONS, RELEASE_MOVE_REGISTRY, RELEASE_MOVE_INDEX,
)
from fight_moves.catalogue.survival_development import SURVIVAL_ROLES


LEGACY_SURVIVAL_ROLES = {
    'bottom_frame_survival': 'bottom', 'hip_frame_ground_breather': 'bottom',
    'heavy_top_breather': 'top',
}
PHYSICAL_GROUND = frozenset({
    'guard', 'half guard', 'side control', 'mount', 'back control', 'turtle', 'front headlock',
})


def survival_role_allows(move_id, position, actor_key, state):
    role = SURVIVAL_ROLES.get(move_id, LEGACY_SURVIVAL_ROLES.get(move_id, 'any'))
    if move_id in LEGACY_SURVIVAL_ROLES and position not in PHYSICAL_GROUND:
        return False
    if role == 'any':
        return True
    if actor_key not in {'a', 'b'}:
        return False
    if role in {'top', 'bottom'}:
        return (state.get(role) == actor_key and state.get('top') in {'a', 'b'}
                and state.get('bottom') in {'a', 'b'} and state.get('top') != state.get('bottom'))
    controller = state.get('clinch_controller')
    if role == 'controller':
        return controller == actor_key
    if role == 'controlled':
        return controller in {'a', 'b'} and controller != actor_key
    raise ValueError(f'Unknown survival role: {role}')


class ReleaseProfileMixin:
    _fight_move_registry = RELEASE_MOVE_REGISTRY
    _fight_move_definitions = RELEASE_MOVE_DEFINITIONS
    _experimental_specialist_entries = True
    _experimental_chain_action_weighting = True
    _experimental_pocket_action_bias = True
    _release_head_damage = True
    _survival_expansion_enabled = True

    def _legal_fight_moves(self, action, position, target):
        return RELEASE_MOVE_INDEX.legal_moves(action, position, target)

    def ds(self, fighter, key, fallback=50):
        value = super().ds(fighter, key, fallback)
        # This is the accepted combined trial's exact detailed-skill adjustment,
        # including previews and low-kick/strength averages, not a damage bonus.
        return value * 1.01 if key in {'high_kick_power', 'low_kick_power'} else value

    def _move_candidates(self, actor, action, position, target, state):
        rows, styles, identity, actor_key, counter = super()._move_candidates(
            actor, action, position, target, state)
        if action == 'survive':
            rows = [move for move in rows if survival_role_allows(move.move_id, position, actor_key, state)]
        return rows, styles, identity, actor_key, counter

    @staticmethod
    def commentary_move_id_label(move_id):
        return FightEngineMixin.commentary_move_id_label(move_id, registry=RELEASE_MOVE_REGISTRY)

    @staticmethod
    def fighter_signature_move_labels(fighter):
        return FightEngineMixin.fighter_signature_move_labels(fighter, registry=RELEASE_MOVE_REGISTRY)

    @staticmethod
    def update_move_sequence(state, event, *, independent_alternatives=False):
        return FightEngineMixin.update_move_sequence(state, event,
            independent_alternatives=independent_alternatives, registry=RELEASE_MOVE_REGISTRY)

    @staticmethod
    def exchange_combination_components(action, attempts, landed, target, move_id=''):
        return FightEngineMixin.exchange_combination_components(action, attempts, landed, target,
            move_id, registry=RELEASE_MOVE_REGISTRY)


class ReleaseFightEngineMixin(ReleaseCradleMixin, ReleaseSubmissionChainMixin,
                             ReleaseProfileMixin, FightEngineMixin):
    """Accepted 440 identities and mechanics, enabled for every application bout."""
