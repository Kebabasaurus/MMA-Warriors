"""Saved fighter traits: player explanations, bounded effects and camp progression."""
from types import MappingProxyType


def definition(category, description, advantages, drawbacks, triggers, strength, personality_only=False):
    return MappingProxyType(dict(category=category, description=description,
        advantages=advantages, drawbacks=drawbacks, triggers=triggers,
        strength=strength, personality_only=personality_only))


# Strength describes the implemented modifier, not a promise of wins.
_ROWS = {
    'Fan Favourite': ('Commercial', 'Crowd appeal helps build events.', '+12 event build; extra post-fight popularity opportunities.', 'No direct combat bonus.', 'Event promotion and MMA results.', 'Strong commercial'),
    'Fragile': ('Recovery', 'Physical vulnerability needs careful management.', 'None.', 'Higher injury risk; -3 strike defence.', 'Injury checks and defending strikes.', 'Moderate drawback'),
    'Clutch': ('Combat', 'Finds an extra effort with a depleted tank.', '+6 action rating below 45 gas; +5 event build.', 'Does not prevent exhaustion.', 'Low gas; title readiness in other sports.', 'Situational +6'),
    'Slow Starter': ('Combat', 'Takes time to settle into the opening.', 'None.', '-3 action rating early in MMA; small readiness penalty in other sports; -2 event build.', 'Early portion of round one.', 'Early -3'),
    'Big Finisher': ('Combat', 'Favours dangerous finishing attacks.', 'More power-punch selection; +8 event build.', 'Attack preference is not a finish guarantee.', 'Action selection and promotion.', 'Moderate preference'),
    'Marketable': ('Commercial', 'Draws commercial attention.', '+14 event build and stronger press-conference promotion.', 'No direct combat bonus.', 'Promotion and face-offs.', 'Strong commercial'),
    'Gym Rat': ('Development', 'Consistent training supports skill growth.', '+9 development score and 8% higher skill-growth chance before caps.', 'Potential and readiness still limit development.', 'Monthly development and training.', 'Moderate growth'),
    'Erratic': ('Combat', 'Performance varies from exchange to exchange.', 'Can gain up to 7 action-rating points.', 'Can lose up to 7; other-sport readiness penalty.', 'Every MMA action-rating roll.', 'Random -7 to +7'),
    'Weight Bully': ('Combat', 'Uses real natural size in close physical contests.', 'Up to +3 close-control action rating from natural size above 60.', 'No benefit without size; weight-cut penalties still apply.', 'Clinch, wrestling and ground-control actions.', 'Bounded 0 to +3'),
    'Cardio Machine': ('Combat', 'Sustains work and recovers between rounds.', '+4 starting gas, 10% lower action gas cost, +2.2 corner recovery; later-round action bonus.', 'Gas caps and damage still apply.', 'Starting gas, exchanges and corners.', 'Strong endurance'),
    'Fast Starter': ('Combat', 'Commits to early offence.', '+6 action rating early in round one; attack-selection preference.', 'Early rating bonus expires.', 'Opening round and action selection.', 'Early +6'),
    'Comeback Artist': ('Combat', 'Responds when personally hurt.', '+7 action rating when hurt exceeds 45% of toughness.', 'Requires taking damage; does not heal it.', 'Own accumulated hurt.', 'Situational +7'),
    'Iron Chin': ('Combat', 'Resists striking pressure.', '+3 strike defence; lower injury tendency.', 'No immunity to knockdowns or stoppages.', 'Strike defence and injury checks.', 'Defence +3'),
    'Glass Cannon': ('Combat', 'Dangerous offence with vulnerable defence.', 'More power-punch selection.', '-3 strike defence.', 'Attack selection and strike defence.', 'Offence/defence tradeoff'),
    'Submission Ace': ('Combat', 'Seeks submission opportunities.', 'Submission preference and specialist grappling options; +7 event build.', 'Requires a legal submission opportunity.', 'Grappling action selection.', 'Specialist preference'),
    'Knockout Artist': ('Combat', 'Favours powerful striking.', 'More power-punch selection; +9 event build.', 'Powerful attacks cost stamina.', 'Attack selection and promotion.', 'Moderate preference'),
    'Pressure Fighter': ('Combat', 'Prefers taking the initiative.', 'Pressure-oriented attack selection.', 'Does not guarantee control or initiative.', 'Choosing actions.', 'Moderate preference'),
    'Counter Specialist': ('Combat', 'Prefers countering opportunities.', 'Counter-oriented plans and action selection.', 'Still needs an opponent opening.', 'Planning and action selection.', 'Specialist preference'),
    'Showman': ('Commercial', 'Turns attention into event interest.', '+12 event build and lively face-offs.', 'Face-offs can create rivalry tension.', 'Promotion and press conferences.', 'Strong commercial'),
    'Trash Talker': ('Commercial', 'Uses confrontation to raise attention.', '+10 event build and lively face-offs.', 'Confrontations can spark rivalries.', 'Promotion and press conferences.', 'Commercial tradeoff'),
    'Quiet Professional': ('Commercial', 'Takes a restrained public approach.', 'Respectful face-offs with similarly quiet fighters.', '-1 event build; little promotional spectacle.', 'Event build and press conferences.', 'Small commercial'),
    'Coach Favourite': ('Development', 'Works comfortably with the corner.', '+1 readiness in other combat sports.', 'No extra MMA camp multiplier.', 'Non-MMA bout preparation.', 'Small +1'),
    'Bad Weight Cut': ('Combat', 'Has a persistent conditioning disadvantage.', 'None.', '-5 starting gas, +14% action gas cost, -3 corner recovery and an action penalty.', 'MMA preparation and exchanges, even after making weight.', 'Strong drawback'),
    'Injury Magnet': ('Recovery', 'Needs extra care around training and competition.', 'None.', 'Higher effective injury tendency; -5 event build.', 'Injury checks and promotion.', 'Moderate drawback'),
    'Media Natural': ('Commercial', 'Comfortable in promotional appearances.', '+13 event build and lively press conferences.', 'Media campaign results also depend on separate media attributes.', 'Promotion and face-offs.', 'Strong commercial'),
    'Gym Leader': ('Personality', 'Recognised as a leader around the gym.', 'Personality only; no live team-wide bonus.', 'No guaranteed effect on teammates.', 'Profile and broadcast identity.', 'Personality only', True),
    'Front Runner': ('Combat', 'Struggles when the fight turns against them.', 'None.', '-6 action rating when own hurt exceeds 35% of toughness.', 'Own accumulated hurt.', 'Situational -6'),
    'Late Bloomer': ('Personality', 'A reputation for developing later.', 'Personality only; prime ages and career arc drive actual growth.', 'Does not move prime ages or raise potential.', 'Profile and broadcast identity.', 'Personality only', True),
    'Veteran Savvy': ('Development', 'Experience cushions career decline.', 'Adds a decline buffer and reduces decline pressure.', 'Does not stop ageing.', 'Monthly development and decline.', 'Moderate protection'),
    'Prospect Mindset': ('Combat', 'Still learning to handle bigger occasions.', '+3 event build.', 'Pressure penalty against a much more popular opponent on a main/title bout.', 'High-profile bouts.', 'Small tradeoff'),
    'Short Notice Hero': ('Commercial', 'Carries a reputation for answering late calls.', '+4 event build.', 'No exemption from readiness, medical or short-camp penalties.', 'Event promotion.', 'Small +4'),
    'Title Mentality': ('Combat', 'Responds to high-profile and long fights.', 'Pressure bonus on main/title bouts; +6 action rating in rounds four and five; +6 event build.', 'Late-round bonus needs a long fight.', 'High stakes and rounds four/five.', 'Situational +6'),
    'Technical Learner': ('Development', 'Absorbs technical training efficiently.', '+8 development score; 8% higher skill-growth chance before caps.', 'Potential and skill caps still apply.', 'Training and monthly development.', 'Moderate growth'),
    'Warrior Spirit': ('Combat', 'Keeps competing through fatigue and hurt.', '+4 action rating under strain; small low-gas efficiency benefit and decline protection.', 'Does not override medical stoppages.', 'Low gas, own hurt and career decline.', 'Situational +4'),
    'Fast Healer': ('Recovery', 'Returns sooner after ordinary fight recovery.', 'Two fewer layoff weeks; lower injury tendency.', 'Minimum layoff and serious-injury rules remain.', 'Post-fight recovery and injury checks.', 'Recovery -2 weeks'),
    'Slow Healer': ('Recovery', 'Needs more time between demanding fights.', 'None.', 'Two extra layoff weeks and higher injury tendency.', 'Post-fight recovery and injury checks.', 'Recovery +2 weeks'),
    'Adaptable': ('Development', 'Training supports a broader technical response.', '+4 development score.', 'Tactical adjustment still depends on skills and plans.', 'Monthly development.', 'Small growth'),
    'Momentum Fighter': ('Combat', 'Confidence amplifies a successful run.', 'Positive career momentum adds 1.5 action-rating points per momentum point; development benefit.', 'The bonus follows career momentum, not consecutive live exchanges.', 'Positive career momentum.', 'State dependent'),
    'Regional Star': ('Commercial', 'Builds recognition on the regional circuit.', '+2 regional winner popularity bonus.', 'No automatic national-level following.', 'Winning a regional bout.', 'Small +2'),
    'Overlooked Talent': ('Development', 'Benefits from regional breakthrough opportunities.', 'Regional recognition, development and graduation preference.', 'Still must meet sporting eligibility.', 'Regional results and progression.', 'Regional opportunity'),
    'Body Hunter': ('Combat', 'Invests in body attacks.', 'Higher body-target and body-action preference.', 'No direct damage multiplier.', 'Striking selection.', 'Specialist preference'),
    'Leg Kicker': ('Combat', 'Prioritises attacking the opponent’s base.', 'Higher low-kick and leg-target preference.', 'No direct damage multiplier.', 'Kick selection.', 'Specialist preference'),
    'Cage Specialist': ('Combat', 'Works well in close wrestling exchanges.', '+5 to cage control, takedowns and dirty boxing; cage preference.', 'Requires the relevant action.', 'Close-range actions.', 'Specialist +5'),
    'Elbow Specialist': ('Combat', 'Prefers compact inside attacks.', '+4 dirty-boxing action rating; elbow preference in Muay Thai.', 'MMA bonus applies to dirty boxing, not only elbows.', 'Inside striking.', 'Specialist +4'),
    'Scramble Artist': ('Combat', 'Finds opportunities in loose grappling.', '+5 sweeps, guard recovery and stand-ups; specialist escapes.', 'An escape must still win its contest.', 'Scramble and recovery actions.', 'Specialist +5'),
    'Fight Finisher': ('Combat', 'Presses an opponent who is already hurt.', '+4 finishing-action rating when opponent hurt exceeds 30% of their toughness.', 'Requires an already-hurt opponent.', 'Power punches, kicks, ground strikes and submissions.', 'Situational +4'),
}
TRAIT_DEFINITIONS = MappingProxyType({name: definition(*values) for name, values in _ROWS.items()})

INJURY_MODIFIERS = MappingProxyType({'Fragile': 18, 'Injury Magnet': 18, 'Slow Healer': 18,
                                  'Iron Chin': -10, 'Veteran Savvy': -10, 'Fast Healer': -10})


def trait_defence_modifier(fighter, action):
    if action not in {'jab', 'power_punch', 'kick', 'dirty_boxing', 'ground_strikes'}:
        return 0
    return {'Iron Chin': 3, 'Fragile': -3, 'Glass Cannon': -3}.get(fighter.trait, 0)


def trait_attack_modifier(fighter, action, state, actor_key):
    if fighter.trait == 'Slow Starter':
        return -3 if state.get('round') == 1 and state.get('early_round', False) else 0
    if fighter.trait == 'Weight Bully' and action in {'clinch', 'takedown', 'shoot', 'cage_control', 'ground_control', 'sweep'}:
        size = (getattr(fighter, 'detailed_skills', {}) or {}).get('natural_size', 50)
        return max(0, min(3, (size - 60) / 10))
    if fighter.trait == 'Fight Finisher' and action in {'power_punch', 'kick', 'ground_strikes', 'submission', 'bottom_submission'}:
        opponents = [(key, other) for key, other in state.get('fighters', {}).items() if key != actor_key]
        if len(opponents) == 1:
            key, opponent = opponents[0]
            return 4 if state.get('hurt', {}).get(key, 0) > opponent.toughness * .3 else 0
    return 0


def effective_injury_tendency(fighter):
    """Anchor legacy risk at migration; apply subsequent trait changes live."""
    current = getattr(fighter, 'trait', '')
    baseline = getattr(fighter, 'trait_injury_baseline', None)
    if baseline is None:
        baseline = current
    return max(1, min(100, fighter.injury_proneness + INJURY_MODIFIERS.get(current, 0)
                       - INJURY_MODIFIERS.get(baseline, 0)))


# Every change follows a connected identity and requires repeated eligible camps.
EVOLUTION_PATHS = MappingProxyType({
    'Slow Starter': ('Technical Learner',), 'Erratic': ('Quiet Professional',),
    'Front Runner': ('Clutch',), 'Bad Weight Cut': ('Gym Rat',),
    'Gym Rat': ('Technical Learner',), 'Technical Learner': ('Adaptable',),
    'Prospect Mindset': ('Clutch', 'Technical Learner'), 'Clutch': ('Title Mentality',),
    'Big Finisher': ('Fight Finisher',), 'Pressure Fighter': ('Cardio Machine',),
    'Showman': ('Media Natural',), 'Trash Talker': ('Showman',),
    'Overlooked Talent': ('Regional Star',), 'Comeback Artist': ('Warrior Spirit',),
})


def progress_camp_trait(fighter, quality, weeks, month):
    """Three or more distinct months of suitable camps, with a 12-month cooldown."""
    old = fighter.trait
    paths = EVOLUTION_PATHS.get(old, ())
    progress = dict(getattr(fighter, 'trait_progress', {}) or {})
    history = list(getattr(fighter, 'trait_history', []) or [])
    if weeks < 2 or not paths or quality < 60 or fighter.professionalism < 60 or fighter.motivation < 55:
        return None
    if history and month - history[-1]['month'] < 12:
        return None
    if progress.get('source') != old:
        progress = {'source': old, 'target': paths[0], 'points': 0, 'last_month': -1}
    if progress.get('last_month') == month:
        return None
    progress['last_month'] = month
    progress['points'] = min(100, progress.get('points', 0) + min(34, max(15, round(quality / 4 + min(weeks, 8)))))
    fighter.trait_progress = progress
    if progress['points'] < 100:
        return None
    if getattr(fighter, 'trait_injury_baseline', None) is None:
        fighter.trait_injury_baseline = old
    fighter.trait = progress['target']
    event = {'month': month, 'from': old, 'to': fighter.trait,
             'reason': 'Sustained preparation across multiple qualifying camps.'}
    fighter.trait_history = (history + [event])[-30:]
    fighter.trait_progress = {}
    return event
