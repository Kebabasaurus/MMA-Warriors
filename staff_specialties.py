"""Stable, explanatory catalogue for staff specialties.

The catalogue owns the player-facing explanation and the approved identity of
live effects.  Domain helpers still own execution; a missing or future
specialty is preserved and shown as descriptive-only rather than gaining a
bonus because a free-form string happened to match.
"""

from copy import deepcopy


STAFF_SPECIALTY_DEFINITIONS = {
    "Prospect eye": {
        "id": "prospect_eye", "role": "Scout", "category": "Scouting",
        "description": "Recognises young fighters whose present read understates their development ceiling.",
        "advantages": "Tighter prospect reports for younger or high-upside targets.",
        "drawbacks": "Less useful on established veterans with little development room.",
        "triggers": "Scout report/search where the fighter is age 27 or younger or has a clear potential gap.",
        "strength": "Moderate", "classification": "Live mechanic",
    },
    "International network": {
        "id": "international_network", "role": "Scout", "category": "Scouting",
        "description": "Maintains useful contacts outside the promotion's home region.",
        "advantages": "Improves scouting reads for fighters outside the player's region.",
        "drawbacks": "No special lift for local targets; overseas information remains uncertain.",
        "triggers": "Scout report/search where fighter or target region differs from the player's region.",
        "strength": "Moderate", "classification": "Live mechanic",
    },
    "Women’s divisions": {
        "id": "womens_divisions", "role": "Scout", "category": "Scouting",
        "description": "Builds specialist knowledge of the women's fighter market.",
        "advantages": "Improves scouting reads for female fighters.",
        "drawbacks": "No special lift for male targets.",
        "triggers": "Scout report/search for a female fighter.",
        "strength": "Moderate", "classification": "Live mechanic",
    },
    "Injury prevention": {
        "id": "injury_prevention", "role": "Doctor", "category": "Medical",
        "description": "A broad medical practice focus used to explain the doctor's role.",
        "advantages": "No specialty-specific bonus is claimed; the Doctor's existing effective skill remains authoritative.",
        "drawbacks": "Does not prevent every injury or override sporting/medical clearance.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Weight-cut safety": {
        "id": "weight_cut_safety", "role": "Doctor", "category": "Medical",
        "description": "Signals a medical preference for safer weight-management practices.",
        "advantages": "No separate hidden weight-cut effect is applied in this version.",
        "drawbacks": "Cannot waive a weigh-in miss or make an unfit fighter eligible.",
        "triggers": "Personality and hiring fit only until the approved medical rules are implemented.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Recovery planning": {
        "id": "recovery_planning", "role": "Doctor", "category": "Medical",
        "description": "Emphasises staged return-to-training decisions.",
        "advantages": "No specialty-specific recovery multiplier is claimed.",
        "drawbacks": "Cannot shorten a recorded layoff without the existing medical resolver.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Regional campaigns": {
        "id": "regional_campaigns", "role": "Marketing", "category": "Commercial",
        "description": "Understands local outlets, venues and regional audience habits.",
        "advantages": "No specialty-specific campaign bonus is added; marketing skill/effect remains the live mechanic.",
        "drawbacks": "Does not create audience or income without an approved campaign action.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Digital promotion": {
        "id": "digital_promotion", "role": "Marketing", "category": "Commercial",
        "description": "Focuses on digital content and repeatable online campaign work.",
        "advantages": "No unregistered digital multiplier is applied.",
        "drawbacks": "Does not bypass campaign capacity, cost or outcome uncertainty.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Sponsor sales": {
        "id": "sponsor_sales", "role": "Marketing", "category": "Commercial",
        "description": "Presents sponsor-facing commercial experience without changing contract terms.",
        "advantages": "No automatic sponsor acceptance or fee increase is claimed.",
        "drawbacks": "Cannot waive activation duties or the existing settlement rules.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Campaign Coordinator": {
        "id": "campaign_coordinator", "role": "Marketing", "category": "Commercial",
        "description": "Turns the promotion's paid media work into a repeatable, cost-aware campaign calendar.",
        "advantages": "Reduces the cost of an eligible paid media campaign by a bounded 2%.",
        "drawbacks": "Does not improve campaign heat, action capacity, acceptance rolls or zero-cost appearances.",
        "triggers": "The effective Marketing lead has this specialty when a paid media campaign is quoted or settled.",
        "strength": "Bounded 2%", "classification": "Live mechanic",
    },
    "Contender logic": {
        "id": "contender_logic", "role": "Matchmaker", "category": "Matchmaking",
        "description": "Frames booking work around rankings, title merit and division structure.",
        "advantages": "No separate scoring bonus is attached; current eligibility rules remain authoritative.",
        "drawbacks": "Cannot waive inactivity, title-merit or champion-protection gates.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Prospect protection": {
        "id": "prospect_protection", "role": "Matchmaker", "category": "Matchmaking",
        "description": "Signals care around developmentally appropriate matchmaking.",
        "advantages": "No hidden protection from legitimate bookings is applied.",
        "drawbacks": "Cannot block an eligible bout or reveal hidden future outcomes.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Grudge booking": {
        "id": "grudge_booking", "role": "Matchmaker", "category": "Matchmaking",
        "description": "Recognises the commercial value of rivalry and narrative continuity.",
        "advantages": "No automatic rivalry creation or outcome influence is applied.",
        "drawbacks": "Cannot override readiness, title or weight-class validation.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Compliance": {
        "id": "compliance", "role": "Drug Testing Officer", "category": "Compliance",
        "description": "Signals procedural focus on testing administration.",
        "advantages": "No detection or sanction mechanic is inferred from the label.",
        "drawbacks": "Cannot turn a random result into a confirmed violation or injury.",
        "triggers": "Personality only until J5's provider/case system is implemented.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Targeted testing": {
        "id": "targeted_testing", "role": "Drug Testing Officer", "category": "Compliance",
        "description": "Signals a preference for targeted testing plans.",
        "advantages": "No targeting or detection bonus is active yet.",
        "drawbacks": "Cannot choose a confirmed case or sanction without J5 rules.",
        "triggers": "Personality only until J5's provider/case system is implemented.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Live production": {
        "id": "live_production", "role": "Broadcast Producer", "category": "Broadcast",
        "description": "Emphasises reliable live-show execution and production readiness.",
        "advantages": "No automatic production-tier change is applied.",
        "drawbacks": "Cannot waive an agreed rights production threshold.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Story packages": {
        "id": "story_packages", "role": "Broadcast Producer", "category": "Broadcast",
        "description": "Emphasises coherent event presentation and story continuity.",
        "advantages": "No automatic audience or rights bonus is applied.",
        "drawbacks": "Cannot convert a forecast into a guaranteed result.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Production Coordinator": {
        "id": "production_coordinator", "role": "Broadcast Producer", "category": "Broadcast",
        "description": "Keeps the live card's staging plan efficient without cutting safety or athlete obligations.",
        "advantages": "Reduces eligible production-staging cost by a bounded 2%.",
        "drawbacks": "Does not reduce security, setup guarantees, broadcaster fees, commentator pay, medical, testing or athlete pay.",
        "triggers": "The effective Broadcast Producer lead has this specialty when event finance is calculated.",
        "strength": "Bounded 2%", "classification": "Live mechanic",
    },
    "Contract trust": {
        "id": "contract_trust", "role": "Talent Relations", "category": "Talent",
        "description": "Signals careful communication around contract expectations.",
        "advantages": "No unapproved loyalty or salary modifier is attached.",
        "drawbacks": "Cannot prevent expiry, severance or a player's explicit negotiation choice.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Veteran management": {
        "id": "veteran_management", "role": "Talent Relations", "category": "Talent",
        "description": "Signals experience managing established fighters and career transitions.",
        "advantages": "No hidden morale or retirement protection is applied.",
        "drawbacks": "Cannot override a fighter's contract, readiness or sporting choice.",
        "triggers": "Personality and hiring fit only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Contract Administrator": {
        "id": "contract_administrator", "role": "Talent Relations", "category": "Talent",
        "description": "Keeps negotiation paperwork, approvals and offer administration efficient.",
        "advantages": "Adds a bounded 2% saving to the existing negotiation-administration basis.",
        "drawbacks": "Never reduces a fighter's salary, purse, signing bonus or player-selected terms.",
        "triggers": "The effective Talent Relations lead has this specialty when a negotiation target or transfer assessment is prepared.",
        "strength": "Bounded 2%", "classification": "Live mechanic",
    },
    "Development blocks": {
        "id": "development_blocks", "role": "Academy Coach", "category": "Academy",
        "description": "Organises a prospect's work into a measurable development block.",
        "advantages": "Explains a coach's fit for the Academy block workflow; the bounded role effect is recorded on the assignment.",
        "drawbacks": "Cannot supervise more than one active cohort or change a fighter's combat ratings directly.",
        "triggers": "Player explicitly assigns the coach to an existing Academy development block.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Prospect fundamentals": {
        "id": "prospect_fundamentals", "role": "Academy Coach", "category": "Academy",
        "description": "Prioritises repeatable fundamentals while a prospect is still building an amateur base.",
        "advantages": "Provides a clear coaching identity in the Academy dossier.",
        "drawbacks": "Does not add a second bonus or override the selected plan focus.",
        "triggers": "Profile and assignment presentation only; no hidden bonus is inferred from the label.",
        "strength": "Descriptive", "classification": "Personality only",
    },
    "Performance planning": {
        "id": "performance_planning", "role": "Academy Coach", "category": "Academy",
        "description": "Tracks workload and readiness across a prospect's committed block.",
        "advantages": "Makes the block's evidence and review cadence easier to understand.",
        "drawbacks": "Cannot clear injury, guarantee growth or replace the legacy Trainer fallback.",
        "triggers": "Profile and assignment presentation only in the current build.",
        "strength": "Descriptive", "classification": "Personality only",
    },
}


def staff_specialty_definition(specialty, role=""):
    """Return a copy, preserving unknown legacy values as descriptive-only."""
    name = str(specialty or "Operations")
    definition = STAFF_SPECIALTY_DEFINITIONS.get(name)
    if definition is None:
        role = str(role or "Operations")
        definition = {
            "id": "unknown_" + name.lower().replace(" ", "_"), "role": role,
            "category": "Unclassified", "description": "Legacy or future specialty retained without guessing its effect.",
            "advantages": "None claimed until a definition is approved.",
            "drawbacks": "No mechanic is inferred from an unknown label.",
            "triggers": "Descriptive display only.", "strength": "Descriptive",
            "classification": "Personality only",
        }
    return deepcopy(definition)


def staff_specialty_snapshot(member):
    member = member if isinstance(member, dict) else {}
    definition = staff_specialty_definition(member.get("specialty", "Operations"), member.get("role", "Operations"))
    definition.update({"staff_id": str(member.get("staff_id", "") or ""), "name": str(member.get("name", "Staff") or "Staff")})
    return definition


def validate_staff_specialty_catalogue():
    required = ("id", "role", "category", "description", "advantages", "drawbacks", "triggers", "strength", "classification")
    missing = []
    for name, definition in STAFF_SPECIALTY_DEFINITIONS.items():
        if any(not str(definition.get(key, "")).strip() for key in required):
            missing.append(name)
        if definition.get("classification") not in ("Live mechanic", "Personality only"):
            missing.append(name)
    return missing
