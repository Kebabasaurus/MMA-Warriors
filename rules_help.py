"""Stable, authored Rules Help topics for the promoter office.

This module is deliberately data-only.  It describes how to read decisions in
the existing game; it never imports a mutable formula or calculates a live
ranking, quote, cost, or scouting value.
"""

from copy import deepcopy


HELP_TOPICS = (
    {
        "topic_id": "ranking-scopes",
        "title": "Company rank vs world rank",
        "summary": "A fighter can have a company position and a separate world position.",
        "answer": (
            "Company rank is calculated inside the promotion and division. World rank is calculated "
            "across the visible division outside that company. A champion is shown with a champion "
            "marker only in the scope where that belt exists; historical matchup rows keep the rank "
            "snapshot from before the fight."
        ),
        "why_blocked": (
            "A number may be hidden when Scouting Mode does not reveal that scope, or unavailable "
            "when the historical record did not store a rank snapshot. The UI must say unknown rather "
            "than substitute today's ranking."
        ),
        "action_label": "Open Rankings",
        "action_route": "rankings",
        "aliases": ("opponent ranking", "world ranking", "company ranking", "rank snapshot"),
        "terms": ("company scope", "world scope", "champion marker", "historical snapshot"),
    },
    {
        "topic_id": "title-eligibility",
        "title": "Title challenger eligibility",
        "summary": "A title opportunity is earned through current sporting evidence.",
        "answer": (
            "The challenger check runs before scoring a defence or vacancy. In a major or regional "
            "division, the fighter needs two wins with wins at least losses, or a three-win comeback "
            "streak. Inactivity, a promise, or a shallow division cannot waive that merit check."
        ),
        "why_blocked": (
            "A fighter can be highly rated and still be ineligible if the required win evidence or "
            "cooldown is missing. The blocked reason is a sporting explanation, not a hidden penalty."
        ),
        "action_label": "Open Matchmaking",
        "action_route": "booking",
        "aliases": ("title shot", "challenger", "title merit", "defense eligibility"),
        "terms": ("two wins", "comeback streak", "cooldown", "sporting eligibility"),
    },
    {
        "topic_id": "availability-and-camps",
        "title": "Availability, injuries and camps",
        "summary": "A bookable fighter must be available at the event boundary.",
        "answer": (
            "Medical return dates, current injury, fatigue, retirement status, existing bookings, "
            "division and camp requirements are checked when an option is reviewed and again when "
            "it is filled. A tentative medical plan is not a clearance and cannot silently become an "
            "official bout."
        ),
        "why_blocked": (
            "The workbench keeps a blocked candidate visible with the exact reason—medical return, "
            "fatigue, duplicate booking, wrong division or retirement—so a shallow list is explainable."
        ),
        "action_label": "Open Matchmaking",
        "action_route": "booking",
        "aliases": ("injury", "medical return", "camp", "bookable", "availability"),
        "terms": ("hard blocker", "tentative", "clearance", "revalidation"),
    },
    {
        "topic_id": "staff-contribution",
        "title": "Staff contribution and autonomy",
        "summary": "Staff effects come from the assigned role and recorded work.",
        "answer": (
            "The effective lead and specialty are read from the employed staff identity. Recommendations "
            "are advisory; Manual, Recommendations, Selective Recommendations and Full Auto determine "
            "who may execute a department action. Work receipts show the quote, outcome, evidence key "
            "and any exception, so a page visit never counts as work."
        ),
        "why_blocked": (
            "An action can require player approval when it is not allow-listed, exceeds a limit, lacks "
            "cash reserve, or has no valid target. Unsupported work is recorded as Needs Attention."
        ),
        "action_label": "Open Staff",
        "action_route": "staff",
        "aliases": ("staff skill", "lead staff", "recommendations", "full auto", "department"),
        "terms": ("Manual", "Recommendations", "Selective Recommendations", "Full Auto", "evidence key"),
    },
    {
        "topic_id": "campaign-costs",
        "title": "Campaign costs and receipts",
        "summary": "A campaign brief is separate from its eventual outcome.",
        "answer": (
            "Saving or retargeting a campaign brief does not spend cash or roll a result. A committed "
            "action uses the existing campaign resolver once, with a stable plan/week/action identity "
            "and a recorded receipt. A failed resolver remains retryable; completed evidence is not "
            "rerun when the page is refreshed."
        ),
        "why_blocked": (
            "A brief can be blocked by an expired or departed target, weekly capacity, an action limit, "
            "or insufficient funds. The desk reports that blocker instead of inventing a new target."
        ),
        "action_label": "Open Media Desk",
        "action_route": "website",
        "aliases": ("campaign spend", "media costs", "sponsor duty", "media receipt"),
        "terms": ("brief", "quote", "capacity", "resolver", "receipt"),
    },
    {
        "topic_id": "obligations-and-contracts",
        "title": "Contracts, promises and obligations",
        "summary": "Commitments are visible before they become a negotiation or payment.",
        "answer": (
            "Contract terms, guaranteed fights, signing money, clauses and promise deadlines are kept "
            "on the identity that owns them. Renewal batches quote each selected fighter first, then "
            "require confirmation; partial results are sealed row by row and failed rows are not rerolled."
        ),
        "why_blocked": (
            "A renewal may be blocked by departure, retirement, insufficient reserve or an expired term. "
            "A blocked row remains in the review so the player can choose what to do next."
        ),
        "action_label": "Open Contracts",
        "action_route": "contracts",
        "aliases": ("guaranteed fights", "renewal", "contract promise", "signing bonus", "clauses"),
        "terms": ("quote-first", "partial success", "reserve", "expiry", "row receipt"),
    },
    {
        "topic_id": "finance-vocabulary",
        "title": "Finance vocabulary",
        "summary": "Forecasts, commitments and settled cash are different numbers.",
        "answer": (
            "The cash runway starts from actual cash, includes already-paid and recurring costs, and "
            "shows event commitments with bounded attendance sensitivities. Rights and sponsor income "
            "remain conditional until settlement. A forecast is advice, not a reservation or a ledger "
            "entry, and completed event receipts remain the source of truth."
        ),
        "why_blocked": (
            "A break-even or receipt line may be unavailable when venue capacity, terms or historical "
            "evidence is incomplete. The page labels assumptions instead of presenting a false probability."
        ),
        "action_label": "Open Finance",
        "action_route": "finance",
        "aliases": ("cash runway", "profit", "break even", "forecast", "rights income", "sponsor income"),
        "terms": ("actual cash", "conditional receipt", "sensitivity", "capacity", "settlement"),
    },
    {
        "topic_id": "fight-preparation",
        "title": "Event preparation timeline",
        "summary": "The card build is recorded separately from the fight transcript.",
        "answer": (
            "End of Event, Results and Fight Night archives can show linked campaign evidence, press "
            "lines, weigh-in outcomes, cancelled bouts and final readiness. These cards are read-only "
            "views of the stored package; they do not rerun preparation or change a result."
        ),
        "why_blocked": (
            "Legacy packages may not contain a preparation timeline. The archive says that evidence is "
            "unavailable rather than reconstructing press, weigh-ins or rankings from today's state."
        ),
        "action_label": "Open Fight Night",
        "action_route": "log",
        "aliases": ("press conference", "weigh ins", "weigh-in", "readiness", "cancelled bout"),
        "terms": ("recorded outcome", "legacy archive", "campaign evidence", "final readiness"),
    },
)


def help_topic(topic_id):
    """Return a defensive copy of one stable topic, or ``None``."""
    wanted = str(topic_id or "")
    for topic in HELP_TOPICS:
        if topic.get("topic_id") == wanted:
            return deepcopy(topic)
    return None


def search_help_topics(query=""):
    """Search authored visible text while retaining catalogue order."""
    needle = " ".join(str(query or "").lower().split())
    if not needle:
        return [deepcopy(topic) for topic in HELP_TOPICS]
    matches = []
    for topic in HELP_TOPICS:
        fields = [topic.get("title", ""), topic.get("summary", ""), topic.get("answer", ""), topic.get("why_blocked", "")]
        fields.extend(topic.get("aliases", ()) or ())
        fields.extend(topic.get("terms", ()) or ())
        haystack = " ".join(str(value).lower() for value in fields)
        if needle in haystack:
            matches.append(deepcopy(topic))
    return matches


__all__ = ["HELP_TOPICS", "help_topic", "search_help_topics"]
