from dataclasses import dataclass, field
from uuid import uuid4

from constants import DETAILED_SKILL_GROUPS


@dataclass(eq=False)
class Fighter:
    # Identity equality (eq=False) is deliberate: fighters are compared and looked
    # up by object identity / fighter_id, never by value. The auto-generated
    # value __eq__ over 150+ fields made membership checks in the world sim
    # catastrophically slow (it dominated month processing). Identity __eq__ is
    # O(1), matches how the code uses fighters, and keeps instances hashable.
    name: str
    weight: str
    age: int
    record_w: int
    record_l: int
    striking: int
    wrestling: int
    grappling: int
    cardio: int
    chin: int
    popularity: int
    momentum: int
    morale: int
    purse: int
    record_d: int = 0
    gender: str = "Male"
    champion: bool = False
    interim_champion: bool = False
    interim_title_wins: int = 0
    interim_title_defenses: int = 0
    special_titles: list = None
    injured: int = 0
    region: str = "USA"
    nationality: str = "American"
    primary_discipline: str = "MMA"
    combat_background: str = "Mixed martial arts"
    sport_employer: str = ""
    sport_weight_class: str = ""
    multi_sport_records: dict = None
    crossover_history: list = None
    birth_country: str = ""
    birth_region: str = ""
    hometown: str = ""
    residence: str = ""
    training_location: str = ""
    fighting_base: str = ""
    cultural_connections: list = None
    regional_popularity: dict = None
    home_event_history: list = None
    height: str = ""
    style: str = "Well-Rounded"
    stance: str = "Orthodox"
    trait: str = "Gym Rat"
    potential: int = 70
    prime_start: int = 26
    prime_end: int = 33
    career_archetype: str = "Balanced Development"
    contract_months: int = 12
    guaranteed_fights: int = 0
    contract_fights_completed: int = 0
    comeback_contract: bool = False
    fatigue: int = 0
    rank_score: int = 0
    title_shots: int = 0
    last_fight: str = "None"
    last_fight_month: int = 0
    power: int = 65
    takedown_defence: int = 65
    ground_control: int = 65
    submissions: int = 65
    submission_defence: int = 65
    recovery: int = 65
    toughness: int = 65
    fight_iq: int = 65
    behaviour: str = "Dynamic Attacker"
    camp: str = "Independent"
    rival: str = ""
    friend: str = ""
    exclusive: bool = True
    contract_type: str = "Exclusive"
    negotiation_heat: int = 0
    media_heat: int = 0
    detailed_skills: dict = None
    star_quality: int = 50
    charisma: int = 50
    professionalism: int = 50
    injury_proneness: int = 20
    finishing_instinct: int = 50
    media_presence: int = 50
    sponsor_appeal: int = 50
    portrait_bg: str = "#333333"
    portrait_accent: str = "#c3a45d"
    fight_history: list = None
    # Academy results are a separate amateur ledger. They inform a fighter's
    # background, but never count toward the professional record or universe
    # record shown on the main profile history tab.
    amateur_w: int = 0
    amateur_l: int = 0
    amateur_d: int = 0
    amateur_bout_history: list = None
    amateur_history_migration_version: int = 0
    # Pre-bout ratings retained independently of the bounded card replay archive.
    bout_rating_history: list = None
    annual_overalls: dict = None
    sport_rating_history: dict = None
    sport_development_log: list = None
    # Compact, attributed MMA development history. Only meaningful rating
    # changes are retained; the current factor breakdown is calculated live.
    development_log: list = None
    motivation: int = 65
    retired: bool = False
    retirement_reason: str = ""
    retirement_pending: bool = False
    retirement_requested_month: int = 0
    retirement_fight_completed: bool = False
    # The month a completed comeback becomes eligible for its separate farewell
    # bout. This prevents the final comeback fight from also consuming it.
    retirement_fight_due_after_month: int = 0
    comeback_completion_prompted: bool = False
    camp_quality: int = 0
    camp_weeks: int = 0
    camp_boost: int = 0
    camp_focus: str = "Balanced"
    camp_intensity: str = "Standard"
    walk_weight: int = 0
    scale_weight: float = 0.0
    missed_weight: bool = False
    weight_cut_penalty: int = 0
    # A durable penalty for voluntarily competing above the fighter's natural
    # frame. Unlike a bad cut, it applies every bout until they move again.
    division_size_penalty: int = 0
    division_size_note: str = ""
    elo_rating: int = 1500
    career_sig_strikes: int = 0
    career_takedowns: int = 0
    career_control_secs: int = 0
    career_knockdowns: int = 0
    career_sub_attempts: int = 0
    career_submissions: int = 0
    career_finishes: int = 0
    career_knockouts: int = 0
    career_stat_rounds: int = 0
    career_stat_fights: int = 0
    available_week: int = 0
    # Day-precision clearance. available_week stays the coarse gate so older
    # saves keep working; this refines it once a fighter has fought on a dated
    # card. Zero means "fall back to available_week".
    available_day: int = 0
    last_fight_day_index: int = 0
    hall_of_fame: bool = False
    legacy_score: int = 0
    title_wins: int = 0
    title_defenses: int = 0
    award_count: int = 0
    rivalry_history: list = None
    win_bonus: int = 0
    ppv_points: int = 0
    champions_clause: bool = False
    title_shot_clause: bool = False
    owed_title_shot: bool = False
    rating_profile_version: int = 0
    realism_profile_version: int = 0
    sport_profile_version: int = 0
    legend_prime_age_version: int = 0
    prime_legend_age_override_version: int = 0
    prime_rating_profile_version: int = 0
    career_arc_version: int = 0
    feeder_origin: str = ""
    market_origin: str = ""
    regional_record_w: int = 0
    regional_record_l: int = 0
    regional_record_d: int = 0
    regional_record_month: int = 0
    regional_entry_w: int = 0
    regional_entry_l: int = 0
    regional_entry_d: int = 0
    ai_offer_company: str = ""
    ai_offer_purse: int = 0
    ai_offer_months: int = 0
    ai_offer_signing_bonus: int = 0
    free_agent_months: int = 0
    showcase_last_month: int = -99
    player_talent_alerted: bool = False
    player_talent_window_until: int = 0
    ai_offer_deadline_month: int = 0
    negotiation_persona: str = "Professional"
    agent_name: str = "Independent"
    main_event_promise: bool = False
    top_opponent_promise: bool = False
    promise_deadline_month: int = 0
    relationship_trust: int = 55
    serious_injury: str = ""
    serious_injury_pending: bool = False
    serious_injury_history: list = None
    serious_injury_recurrence: int = 0
    rivalry_heat: int = 0
    rivalry_origin: str = ""
    rivalry_rematch_due: bool = False
    rivalry_last_month: int = 0
    weight_class_history: list = None
    weight_move_last_month: int = -99
    career_achievements: list = None
    career_goal: str = ""
    career_goal_target: int = 0
    career_goal_progress: int = 0
    career_goal_history: list = None
    career_win_streak: int = 0
    career_goal_last_review: int = 0
    ranking_position: int = 0
    previous_ranking_position: int = 0
    ranking_reason: str = ""
    # Stable career identity. Names, employers, sports and weight classes can all
    # change; this value must not. It is intentionally not player-facing.
    fighter_id: str = field(default_factory=lambda: f"FTR-{uuid4().hex[:16]}")
    # Record carried into the current universe. The individual bouts behind this
    # baseline were not simulated here, so profile history labels it separately.
    record_history_baseline_w: int = -1
    record_history_baseline_l: int = -1
    record_history_baseline_d: int = -1
    # Generated opening-universe fighters can carry a small established record.
    # Fighters created after play begins are true in-universe entrants and begin
    # at 0-0-0 with their first rating snapshot in their entry year.
    generated: bool = False
    # Curated real-world seed data can retain the public profile used to verify
    # it. Generated fighters intentionally have no source URL.
    source_url: str = ""
    universe_entry_month: int = 0
    universe_entry_year: int = 0
    camp_joined_month: int = 0
    camp_history: list = None

    @property
    def overall(self):
        if self.detailed_skills:
            return round((self.striking + self.wrestling + self.grappling + self.cardio + self.chin + self.detailed_group_average("Mental") + self.detailed_group_average("Physical")) / 7)
        return round((self.striking + self.wrestling + self.grappling + self.cardio + self.chin) / 5)

    def detailed_group_average(self, group):
        if not self.detailed_skills:
            return 0
        keys = DETAILED_SKILL_GROUPS[group]
        return round(sum(self.detailed_skills.get(key, 50) for key in keys) / len(keys))

    @property
    def record(self):
        # Always show the full MMA record. A visible zero makes it clear that
        # draws are tracked, rather than silently omitted from the display.
        return f"{self.record_w}-{self.record_l}-{self.record_d}"

    @property
    def status(self):
        if self.injured:
            return f"Injured {self.injured} mo"
        if self.fatigue >= 45:
            return "Needs rest"
        return "Ready"

    @property
    def star_power(self):
        return round(self.popularity * 0.65 + self.momentum * 4 + self.overall * 0.35)


@dataclass
class Gym:
    name: str
    region: str
    city: str
    quality: int
    reputation: int
    specialties: list
    head_coach: str
    capacity: int
    monthly_fee: int
    morale: int = 65
    facilities: int = 60
    scouting: int = 50
    member_count: int = 0
    notes: str = ""
    momentum: int = 0
    development_reputation: int = 50
    history: list = None
    last_review_month: int = 0
    capacity_growth: int = 0


@dataclass
class Promotion:
    name: str
    region: str
    size: int
    cash: int
    roster: list
    momentum: int = 0
    reputation: str = "Regional"
    reputation_score: int = 40
    stability: int = 50
    show_history: list = None
    event_counter: int = 1
    belts: dict = None
    interim_belts: dict = None
    special_belts: dict = None
    belt_history: dict = None
    rules: dict = None
    broadcasters: list = None
    weight_classes: list = None
    scheduled_events: list = None
    finance: dict = None
    staff: list = None
    scouting: list = None
    inbox: list = None
    owner_goals: list = None
    post_show_bonuses: dict = None
    show_personality: str = "Balanced"
    is_regional_feeder: bool = False
    strategy: dict = None
    strategic_rival: str = ""
    executive: dict = None
    era_history: list = None
    legacy_score: int = 0
    academy: dict = None
    closed_divisions: list = None
    closed_division_policy_set: bool = False
    regional_division_activity: dict = None
