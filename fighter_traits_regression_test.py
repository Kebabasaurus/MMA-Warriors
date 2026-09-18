"""Trait contracts: truthful catalogue, live bounds, development and old saves."""
from copy import deepcopy
import ast
import inspect
import json
import random
import textwrap
import unittest

from constants import TRAITS
from fighter_traits import (TRAIT_DEFINITIONS, EVOLUTION_PATHS,
    effective_injury_tendency, progress_camp_trait,
    trait_attack_modifier, trait_defence_modifier)
from models import Fighter
from events import EventMixin
from fight_engine import FightEngineMixin
from fight_release import ReleaseFightEngineMixin
from world import WorldMixin
from persistence import FIGHTER_SAVE_FIELDS, load_model_row, serialize_fighter_model


def fighter(trait='Gym Rat', **overrides):
    values = dict(name='Trait fixture', weight='Lightweight', age=25,
        record_w=5, record_l=1, striking=65, wrestling=65, grappling=65,
        cardio=65, chin=65, popularity=50, momentum=0, morale=70, purse=1000,
        trait=trait, professionalism=90, motivation=90, injury_proneness=30)
    values.update(overrides)
    return Fighter(**values)


class TraitRegressionTests(unittest.TestCase):
    def test_every_mechanical_trait_has_runtime_evidence(self):
        # Explicit live function inventory: no seeding, catalogue prose, camp
        # identity assignment, or commentary function can satisfy this gate.
        evidence = {
            EventMixin.fight_build_score: (
                'Fan Favourite', 'Marketable', 'Media Natural', 'Showman',
                'Trash Talker', 'Quiet Professional', 'Short Notice Hero', 'Injury Magnet'),
            FightEngineMixin.choose_action: ('Big Finisher', 'Knockout Artist',
                'Submission Ace', 'Pressure Fighter', 'Counter Specialist'),
            FightEngineMixin.action_attack_value: ('Clutch', 'Comeback Artist',
                'Fast Starter', 'Cardio Machine', 'Title Mentality', 'Warrior Spirit',
                'Momentum Fighter', 'Cage Specialist', 'Elbow Specialist',
                'Scramble Artist', 'Front Runner', 'Bad Weight Cut', 'Erratic'),
            FightEngineMixin.pressure_fight_edge: ('Prospect Mindset',),
            FightEngineMixin.punch_target_shares: ('Body Hunter',),
            FightEngineMixin.kick_target_shares: ('Leg Kicker',),
            WorldMixin.fighter_development_factors: ('Gym Rat', 'Technical Learner', 'Adaptable'),
            WorldMixin.monthly_decline_score: ('Veteran Savvy',),
            WorldMixin.set_post_fight_recovery: ('Fast Healer', 'Slow Healer'),
            WorldMixin.combat_sport_readiness_modifier: ('Coach Favourite',),
            WorldMixin.simulate_regional_feeder_month: ('Regional Star', 'Overlooked Talent'),
            trait_attack_modifier: ('Weight Bully', 'Slow Starter', 'Fight Finisher'),
            trait_defence_modifier: ('Iron Chin', 'Glass Cannon', 'Fragile'),
        }
        observed = set()
        for function, names in evidence.items():
            tree = ast.parse(textwrap.dedent(inspect.getsource(function)))
            body = tree.body[0].body
            if body and isinstance(body[0], ast.Expr) and isinstance(body[0].value, ast.Constant):
                body = body[1:]  # Never count a docstring as mechanic evidence.
            literals = {node.value for statement in body for node in ast.walk(statement)
                        if isinstance(node, ast.Constant) and isinstance(node.value, str)}
            for name in names:
                self.assertIn(name, literals, f'{name} lost live evidence in {function.__name__}')
            observed.update(names)
        expected = {name for name, entry in TRAIT_DEFINITIONS.items() if not entry['personality_only']}
        self.assertEqual(observed, expected)

    def test_native_attack_and_defence_apply_live_modifiers(self):
        host = ReleaseFightEngineMixin()
        subject, opponent = fighter(), fighter(name='Opponent', toughness=80)
        state = {'fighters': {'a': subject, 'b': opponent},
            'fighter_keys': {id(subject): 'a', id(opponent): 'b'},
            'gas': {'a': 80, 'b': 80}, 'hurt': {'a': 0, 'b': 0},
            'round': 1, 'early_round': True, 'position': 'range'}
        subject.detailed_skills = {'natural_size': 90}
        for name, action, expected in (('Weight Bully', 'takedown', 3),
                ('Weight Bully', 'jab', 0), ('Slow Starter', 'jab', -3),
                ('Fight Finisher', 'power_punch', 4)):
            subject.trait = 'Gym Rat'
            state['hurt']['b'] = 25
            before = host.action_attack_value(subject, action, state)
            subject.trait = name
            self.assertAlmostEqual(host.action_attack_value(subject, action, state) - before, expected)
        subject.trait = 'Fight Finisher'
        state['hurt'] = {'a': 50, 'b': 0}
        actual = host.action_attack_value(subject, 'power_punch', state)
        subject.trait = 'Gym Rat'
        self.assertEqual(actual, host.action_attack_value(subject, 'power_punch', state))
        for name, expected in (('Iron Chin', 3), ('Fragile', -3), ('Glass Cannon', -3)):
            for action in ('jab', 'kick', 'ground_strikes', 'submission'):
                subject.trait = 'Gym Rat'
                before = host.action_defence_value(subject, action, state)
                subject.trait = name
                self.assertAlmostEqual(host.action_defence_value(subject, action, state) - before,
                                       0 if action == 'submission' else expected)

    def test_commercial_traits_change_actual_event_build(self):
        subject = fighter('Gym Leader', star_quality=20, charisma=20,
                          media_presence=0, media_heat=0, negotiation_heat=0)
        host = EventMixin()
        baseline = host.fight_build_score(subject, rank=25)
        for name, expected in (('Fan Favourite', 12), ('Marketable', 14),
                ('Media Natural', 13), ('Showman', 12), ('Trash Talker', 10),
                ('Quiet Professional', -1), ('Short Notice Hero', 4), ('Injury Magnet', -5)):
            subject.trait = name
            self.assertEqual(host.fight_build_score(subject, rank=25) - baseline, expected)

    def test_canonical_combat_sport_behaviours_change_selection(self):
        host = WorldMixin()
        for behaviour, action, expected in (('Pressure', 'combination', 1.30),
                ('Dynamic Attacker', 'combination', 1.30), ('Counter', 'counter cross', 1.35),
                ('Cautious', 'counter cross', 1.35), ('Volume', 'counter cross', 1.0)):
            subject = fighter(behaviour=behaviour)
            self.assertEqual(host.combat_sport_action_multiplier('Boxing', subject, action, 80), expected)

    def test_catalogue_complete_and_explicit(self):
        self.assertEqual(len(TRAITS), 46)
        self.assertEqual(set(TRAITS), set(TRAIT_DEFINITIONS))
        categories = {'Combat', 'Development', 'Recovery', 'Commercial', 'Personality'}
        for name, entry in TRAIT_DEFINITIONS.items():
            with self.subTest(trait=name):
                self.assertIn(entry['category'], categories)
                for field in ('description', 'advantages', 'drawbacks', 'triggers', 'strength'):
                    self.assertTrue(entry[field].strip(), field)
                self.assertEqual(entry['personality_only'], entry['category'] == 'Personality')
                if entry['personality_only']:
                    self.assertIn('Personality only', entry['advantages'])
                else:
                    self.assertTrue(entry['advantages'] != 'None.' or entry['drawbacks'] != 'None.')
        with self.assertRaises(TypeError):
            TRAIT_DEFINITIONS['Gym Rat']['strength'] = 'Changed'
        for source, targets in EVOLUTION_PATHS.items():
            self.assertIn(source, TRAITS)
            self.assertTrue(targets)
            self.assertTrue(all(target in TRAITS and target != source for target in targets))

    def test_weight_bully_requires_size_and_relevant_action(self):
        subject = fighter('Weight Bully')
        for size, expected in ((0, 0), (60, 0), (70, 1), (80, 2), (90, 3), (1000, 3)):
            subject.detailed_skills = {'natural_size': size}
            self.assertEqual(trait_attack_modifier(subject, 'takedown', {}, 'a'), expected)
            self.assertEqual(trait_attack_modifier(subject, 'power_punch', {}, 'a'), 0)
        subject.detailed_skills = {}
        self.assertEqual(trait_attack_modifier(subject, 'takedown', {}, 'a'), 0)

    def test_opening_penalty_expires(self):
        subject = fighter('Slow Starter')
        self.assertEqual(trait_attack_modifier(subject, 'jab', {'round': 1, 'early_round': True}, 'a'), -3)
        for state in ({'round': 1, 'early_round': False}, {'round': 2, 'early_round': True}, {}):
            self.assertEqual(trait_attack_modifier(subject, 'jab', state, 'a'), 0)

    def test_defence_bounded_and_strike_specific(self):
        for name, expected in (('Iron Chin', 3), ('Fragile', -3), ('Glass Cannon', -3), ('Gym Rat', 0)):
            subject = fighter(name)
            self.assertEqual(trait_defence_modifier(subject, 'power_punch'), expected)
            self.assertEqual(trait_defence_modifier(subject, 'submission'), 0)
            self.assertEqual(trait_defence_modifier(subject, 'takedown'), 0)

    def test_finisher_uses_opponents_hurt_not_own(self):
        subject, opponent = fighter('Fight Finisher'), fighter(toughness=80)
        state = {'fighters': {'a': subject, 'b': opponent}, 'hurt': {'a': 100, 'b': 24}}
        self.assertEqual(trait_attack_modifier(subject, 'power_punch', state, 'a'), 0)
        state['hurt'] = {'a': 0, 'b': 25}
        self.assertEqual(trait_attack_modifier(subject, 'power_punch', state, 'a'), 4)
        self.assertEqual(trait_attack_modifier(subject, 'jab', state, 'a'), 0)
        self.assertEqual(trait_attack_modifier(subject, 'power_punch', {}, 'a'), 0)

    def test_injury_baseline_preserves_old_attributes_and_tracks_change(self):
        subject = fighter('Fragile', injury_proneness=48)
        self.assertEqual(effective_injury_tendency(subject), 48)
        subject.trait_injury_baseline = 'Fragile'
        subject.trait = 'Iron Chin'
        self.assertEqual(effective_injury_tendency(subject), 20)
        self.assertEqual(subject.injury_proneness, 48)
        subject.trait = 'Fragile'
        self.assertEqual(effective_injury_tendency(subject), 48)
        self.assertEqual(effective_injury_tendency(fighter('Fragile', injury_proneness=100)), 100)
        for trait, raw, expected in (('Fragile', 95, 100), ('Iron Chin', 2, 1)):
            subject = fighter(trait, injury_proneness=raw, trait_injury_baseline='')
            self.assertEqual(effective_injury_tendency(subject), expected)
            self.assertEqual(subject.injury_proneness, raw)

    def test_progress_requires_distinct_months_and_cooldown(self):
        subject = fighter()
        raw = (subject.injury_proneness, subject.chin, subject.toughness)
        rng = random.getstate()
        self.assertIsNone(progress_camp_trait(subject, 100, 8, 100))
        progress = deepcopy(subject.trait_progress)
        self.assertIsNone(progress_camp_trait(subject, 100, 8, 100))
        self.assertEqual(subject.trait_progress, progress)
        self.assertIsNone(progress_camp_trait(subject, 100, 8, 101))
        self.assertIsNone(progress_camp_trait(subject, 100, 8, 102))
        event = progress_camp_trait(subject, 100, 8, 103)
        self.assertEqual((event['from'], event['to']), ('Gym Rat', 'Technical Learner'))
        self.assertEqual(subject.trait_injury_baseline, 'Gym Rat')
        self.assertIsNone(progress_camp_trait(subject, 100, 8, 114))
        self.assertEqual(subject.trait_progress, {})
        self.assertIsNone(progress_camp_trait(subject, 100, 8, 115))
        self.assertTrue(subject.trait_progress)
        self.assertEqual(raw, (subject.injury_proneness, subject.chin, subject.toughness))
        self.assertEqual(random.getstate(), rng)

    def test_ineligible_camps_do_not_change_identity(self):
        for changes, quality, weeks in (({}, 59, 8), ({}, 100, 1),
                ({'professionalism': 59}, 100, 8), ({'motivation': 54}, 100, 8),
                ({'trait': 'Iron Chin'}, 100, 8)):
            subject = fighter(**changes)
            before = deepcopy(subject.__dict__)
            self.assertIsNone(progress_camp_trait(subject, quality, weeks, 100))
            self.assertEqual(subject.__dict__, before)

    def test_save_roundtrip_and_legacy_baseline(self):
        subject = fighter('Fragile', trait_injury_baseline='')
        subject.trait_progress = {'source': 'Fragile', 'target': 'Gym Rat', 'points': 30, 'last_month': 22}
        subject.trait_history = [{'month': 10, 'from': 'Gym Rat', 'to': 'Fragile', 'reason': 'Fixture'}]
        row = json.loads(json.dumps(serialize_fighter_model(subject)))
        restored = load_model_row(row, Fighter, FIGHTER_SAVE_FIELDS, 'trait fixture')
        for field in ('trait', 'trait_progress', 'trait_history', 'trait_injury_baseline', 'injury_proneness'):
            self.assertEqual(getattr(restored, field), getattr(subject, field))
        for field in ('trait_progress', 'trait_history', 'trait_injury_baseline'):
            row.pop(field)
        legacy = load_model_row(row, Fighter, FIGHTER_SAVE_FIELDS, 'legacy trait fixture')
        self.assertEqual(legacy.trait_injury_baseline, 'Fragile')
        self.assertEqual(effective_injury_tendency(legacy), subject.injury_proneness)
        legacy.trait = 'Gym Rat'
        self.assertEqual(effective_injury_tendency(legacy), subject.injury_proneness - 18)


if __name__ == '__main__':
    unittest.main()
