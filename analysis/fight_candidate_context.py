"""Scoped developer candidates: no saved state or production registration changes.

Use only in a single-threaded, disposable audit process. Every binding restores on
exit, including nested trials and exceptions. Caller RNG is preserved as well.
"""
from contextlib import contextmanager, ExitStack
from dataclasses import replace
from analysis.heel_hook_identity_candidate import apply_heel_hook_identity
from analysis.submission_chain_candidate import submission_chain_trial
from analysis.cradle_setup_candidate import cradle_setup_trial
from analysis.standing_head_damage_candidate import standing_head_damage_trial
from analysis.kick_power_candidate import kick_power_trial
from analysis.survival_expansion_candidate import survival_expansion_trial, expanded_definitions
import random
from unittest.mock import patch
from analysis.continuation_branch_candidate import apply_continuation_branches
from analysis.continuation_strength_candidate import continuation_strength_trial
from analysis.repertoire_readaptation_candidate import repertoire_readaptation_trial
from analysis.continuation_commitment_candidate import continuation_commitment_trial
from analysis.gift_wrap_control_candidate import apply_gift_wrap_control
from analysis.gift_wrap_mount_candidate import apply_gift_wrap_mount
from analysis.boxing_chain_pool_candidate import boxing_chain_pool_trial

import fight_engine
import fight_moves
import fight_moves.catalogue as catalogue
import fight_moves.registry as registry
from fight_engine_audit import FightAuditHarness
from fight_moves.catalogue.specialist_entry_development import SPECIALIST_ENTRY_DEVELOPMENT
from fight_moves.catalogue.front_headlock_development import FRONT_HEADLOCK_DEVELOPMENT
from fight_moves.catalogue.turtle_development import TURTLE_DEVELOPMENT
from fight_moves.catalogue.failed_shot_development import FAILED_SHOT_DEVELOPMENT
from fight_moves.catalogue.standing_back_development import STANDING_BACK_DEVELOPMENT
from fight_moves.catalogue.leg_entanglement_development import LEG_ENTANGLEMENT_DEVELOPMENT

DRAFT_MOVE_DEFINITIONS = (SPECIALIST_ENTRY_DEVELOPMENT + FRONT_HEADLOCK_DEVELOPMENT
                          + TURTLE_DEVELOPMENT + FAILED_SHOT_DEVELOPMENT + STANDING_BACK_DEVELOPMENT
                          + LEG_ENTANGLEMENT_DEVELOPMENT)


@contextmanager
def candidate_context(*, entries=False, chains=False, draft_content=False, pocket_action_bias=True,
                      continuation_branches=False, stronger_continuation=False,
                      repertoire_readaptation=False, continuation_commitment=False, gift_wrap_control=False,
                      gift_wrap_mount=False, jab_readaptation=False, boxing_chain_pool=False,
                      heel_hook_identity=False, hold_transitions=False, cradle_setup=False, standing_head_damage=False,
                      kick_power=False, survival_expansion=False):
    if survival_expansion and not (entries and chains and draft_content):
        raise ValueError('Survival expansion requires the combined candidate')
    if (hold_transitions or cradle_setup) and not entries:
        raise ValueError('Submission development requires experimental entries')
    if getattr(FightAuditHarness, '_heel_hook_identity_trial', False) and not heel_hook_identity:
        raise ValueError('Cannot disable heel-hook repair inside an active nested trial')
    if heel_hook_identity and not entries:
        raise ValueError('Heel-hook identity repair requires experimental entries')
    active_pool = getattr(FightAuditHarness._chain_action_weights, '_boxing_chain_pool_trial', False)
    active_other = (getattr(FightAuditHarness._chain_action_weights, '_stronger_continuation_trial', False)
                    or getattr(FightAuditHarness._chain_action_weights, '_continuation_commitment_trial', False)
                    or getattr(FightAuditHarness._move_contextual_score, '_repertoire_readaptation_trial', False))
    if (boxing_chain_pool and active_other) or (active_pool and (
            stronger_continuation or continuation_commitment or repertoire_readaptation or jab_readaptation)):
        raise ValueError('Boxing pool trial cannot inherit or combine nested tuning policies')
    if boxing_chain_pool and (not chains or stronger_continuation or continuation_commitment or
                              repertoire_readaptation or jab_readaptation):
        raise ValueError('Boxing pool trial requires chains and isolated weighting/selection policy')
    if jab_readaptation and (not chains or repertoire_readaptation):
        raise ValueError('Jab readaptation requires chains and cannot combine with broad readaptation')
    if gift_wrap_mount and (not chains or gift_wrap_control):
        raise ValueError('Mount refinement requires chains and cannot combine with the broad gift-wrap trial')
    if gift_wrap_control and not chains:
        raise ValueError('Gift-wrap control trial requires chains')
    if continuation_commitment and (not chains or stronger_continuation):
        raise ValueError('Commitment requires chains and cannot combine with stronger continuation')
    if stronger_continuation and not chains:
        raise ValueError('Stronger continuation trial requires chain mechanics')
    if repertoire_readaptation and not chains:
        raise ValueError('Repertoire readaptation requires chain mechanics')
    definitions = tuple(fight_moves.MOVE_DEFINITIONS)
    if entries:
        # force_cage starts in a controlled failed shot; cage is its destination.
        # Keep legacy normal-play authoring unchanged until candidate acceptance.
        definitions = tuple(replace(move, positions=frozenset({'failed shot'}))
                            if move.move_id == 'fence_drive' else move
                            for move in definitions)
    if draft_content:
        by_id = {move.move_id: move for move in definitions}
        for move in DRAFT_MOVE_DEFINITIONS:
            if move.move_id in by_id and by_id[move.move_id] != move:
                raise ValueError(f"Conflicting candidate move: {move.move_id}")
        definitions += tuple(move for move in DRAFT_MOVE_DEFINITIONS if move.move_id not in by_id)
    if continuation_branches:
        if not chains:
            raise ValueError("Continuation branch trial requires chain mechanics")
        definitions = apply_continuation_branches(definitions)
    if gift_wrap_control:
        definitions = apply_gift_wrap_control(definitions)
    if gift_wrap_mount:
        definitions = apply_gift_wrap_mount(definitions)
    if heel_hook_identity:
        definitions = apply_heel_hook_identity(definitions)
    if survival_expansion:
        definitions = expanded_definitions(definitions)
    errors = fight_moves.validate_move_registry(definitions)
    if errors:
        raise ValueError("Invalid candidate registry: " + "; ".join(errors))
    index = fight_moves.MoveIndex(definitions)
    graph = fight_moves.MoveChainGraph(definitions)
    bindings = dict(MOVE_DEFINITIONS=definitions,
                    MOVE_REGISTRY={move.move_id: move for move in definitions},
                    MOVE_INDEX=index, legal_moves=index.legal_moves,
                    CHAIN_GRAPH=graph, chain_depth=graph.chain_depth)
    rng_before = random.getstate()
    try:
        with ExitStack() as stack:
            stack.enter_context(standing_head_damage_trial(standing_head_damage))
            stack.enter_context(kick_power_trial(kick_power))
            stack.enter_context(survival_expansion_trial(survival_expansion))
            stack.enter_context(submission_chain_trial(hold_transitions))
            stack.enter_context(cradle_setup_trial(cradle_setup))
            stack.enter_context(patch.object(FightAuditHarness, '_heel_hook_identity_trial',
                                             heel_hook_identity, create=True))
            stack.enter_context(continuation_strength_trial(stronger_continuation))
            stack.enter_context(boxing_chain_pool_trial(boxing_chain_pool))
            stack.enter_context(repertoire_readaptation_trial(
                repertoire_readaptation or jab_readaptation,
                actions={'jab'} if jab_readaptation else None))
            stack.enter_context(continuation_commitment_trial(continuation_commitment))
            stack.enter_context(patch.object(FightAuditHarness, "_experimental_specialist_entries", entries, create=True))
            stack.enter_context(patch.object(FightAuditHarness, "_experimental_chain_action_weighting", chains, create=True))
            stack.enter_context(patch.object(FightAuditHarness, "_experimental_pocket_action_bias",
                                             pocket_action_bias, create=True))
            stack.enter_context(patch.multiple(fight_engine, MOVE_REGISTRY=bindings["MOVE_REGISTRY"],
                                              legal_moves=index.legal_moves))
            for module in (fight_moves, registry):
                stack.enter_context(patch.multiple(module, **bindings))
            stack.enter_context(patch.object(catalogue, "MOVE_DEFINITIONS", definitions))
            yield definitions
    finally:
        random.setstate(rng_before)
