"""Evidence-based narrative presentation; no simulation state or random draws."""


def compact(value, limit=420):
    text = " ".join(str(value or "").split())
    return text if len(text) <= limit else text[:limit - 3].rsplit(" ", 1)[0] + "..."


def chapter_context(thread):
    """Copy publication-time facts, never a reference to a mutable chapter."""
    if not thread:
        return {}
    beats = thread.get("beats", []) or []
    closed = thread.get("status") in {"resolved", "abandoned"}
    return {
        "opening": compact(thread.get("opening_summary"), 800),
        "opening_label": "How it began" if thread.get("opening_is_origin") else "Earlier recorded context",
        "changed": compact(beats[-1].get("summary"), 800) if beats else "",
        "outlook": compact(thread.get("resolution") if closed else thread.get("stakes"), 800),
        "outlook_label": "Chapter conclusion" if closed else "Still at stake",
        "status": str(thread.get("status", "active")),
    }


def context_text(context, existing=""):
    parts = []
    seen = {compact(existing, 800).casefold()}
    for key, label in (("opening", context.get("opening_label", "Earlier recorded context")),
                       ("changed", "Latest development"),
                       ("outlook", context.get("outlook_label", "Still at stake"))):
        value = compact(context.get(key), 800)
        if value and value.casefold() not in seen:
            parts.append(f"{label.upper()}\n{value}")
            seen.add(value.casefold())
    return "\n\n".join(parts)


def ranked_fight_stories(app, a, b, fight):
    """Rank a fixed set of direct lookups; never search the world or alter booking."""
    candidates = []
    seen = set()

    def add(text, priority, thread=None, key=""):
        text = compact(text)
        key = key or str((thread or {}).get("story_key", "")) or text.casefold()
        if not text or key in seen:
            return
        seen.add(key)
        thread = thread or {}
        evidence = ""
        beats = thread.get("beats", []) or []
        if beats:
            beat = beats[-1]
            latest = compact(beat.get("summary"), 220)
            if latest and latest.casefold() != text.casefold():
                evidence = f" Recorded M{beat.get('month', '?')} W{beat.get('week', '?')}: {latest}"
        candidates.append((priority, int(thread.get("importance", 1) or 1),
                           int(thread.get("last_updated_month", 0) or 0),
                           int(thread.get("last_updated_week", 0) or 0), key, text, evidence))

    def active(thread, priority, prefer_latest=False):
        if not thread or thread.get("status") in {"resolved", "abandoned"}:
            return
        beats = thread.get("beats", []) or []
        latest = beats[-1].get("summary", "") if beats else ""
        text = (latest or thread.get("stakes")) if prefer_latest else (thread.get("stakes") or latest)
        add(text, priority, thread)

    if fight.get("title") or fight.get("divisional_title"):
        champions = [f for f in (a, b) if getattr(f, "champion", False)]
        if len(champions) == 1:
            champion = champions[0]
            challenger = b if champion is a else a
            text = f"{champion.name}'s championship reign is at stake against {challenger.name}."
        elif not champions:
            text = "A vacant championship and a new divisional era are at stake."
        else:
            text = f"Championship stakes bring {a.name} and {b.name} together."
        add(text, 95, key="championship")
    for fighter, opponent in ((a, b), (b, a)):
        if getattr(fighter, "retirement_pending", False):
            connection = app.farewell_opponent_connection(fighter, opponent)
            label = connection.get("label", "")
            text = (f"{fighter.name}'s final fight pairs them with {label} {opponent.name}; this bout will close their career."
                    if label else f"{fighter.name}'s final fight will close their career.")
            add(text, 100, app.active_farewell_story(fighter), key=f"farewell:{fighter.fighter_id}")
        contract = app.active_contract_saga(fighter)
        if contract:
            phase = contract.get("phase", "")
            if phase in {"renewal_window", "final_month", "talks_stalled", "talks_broken_down"}:
                active(contract, 78 if phase == "final_month" else 58, True)
            elif phase == "defection":
                former = str(contract.get("former_company", "") or "")
                if former and app.fighter_company_name(opponent) == former:
                    add(f"{fighter.name} faces {former} for the first time since the contract defection.", 80, contract)
        feeder = app.active_feeder_pathway(fighter)
        if feeder and feeder.get("parent_company") == app.fighter_company_name(fighter):
            if feeder.get("phase") in {"parent_recalled", "parent_transfer", "parent_debut_win", "parent_debut_draw", "parent_debut_setback", "parent_breakthrough"}:
                active(feeder, 65, True)
        active(app.active_breakout_run(fighter), 76, True)
        active(app.active_crossroads_story(fighter), 82, True)
        region = str(fight.get("region", "") or "")
        if region:
            home = app.story_thread(app.hometown_story_key(fighter, region))
            if home and home.get("phase") == "homecoming_booked":
                active(home, 72, True)
        arc = app.active_career_arc(fighter)
        if arc and arc.get("type") in {"Veteran Final Run", "Homegrown Champion", "Champion Ambition"}:
            add(f"{fighter.name}: {arc.get('objective', arc.get('title', 'an active career chapter'))}",
                70, key=f"career:{fighter.fighter_id}")
    active(app.story_thread(app.rivalry_story_key(a, b)), 80)
    active(app.story_thread(app.relationship_story_key(a, b)), 74)
    candidates.sort(key=lambda row: (-row[0], -row[1], -row[2], -row[3], row[4]))
    if not candidates:
        return ""
    primary = candidates[0]
    text = primary[5] + primary[6]
    secondary = next((row for row in candidates[1:] if row[5].casefold() != primary[5].casefold()), None)
    if secondary:
        text += f" Also at stake: {secondary[5]}"
    return text


def weekly_digest(entries, company, month, week):
    """A lazy reader view of at most 240 reports, not another calendar pass."""
    eligible = [row for row in entries[:240]
                if row.get("month") and row.get("week")
                and (int(row["month"]), int(row["week"])) <= (month, week)
                and int(row.get("importance", 1) or 1) >= 3
                and row.get("type") != "Weekly Digest"]
    if not eligible:
        return None
    date = max((int(row["month"]), int(row["week"])) for row in eligible)
    rows = [row for row in eligible if (int(row["month"]), int(row["week"])) == date]
    rows.sort(key=lambda row: (company in (row.get("companies", []) or []),
                              int(row.get("importance", 1) or 1)), reverse=True)
    selected, seen = [], set()
    for row in rows:
        key = row.get("story_id") or compact(row.get("headline")).casefold()
        if key in seen:
            continue
        seen.add(key)
        selected.append(row)
        if len(selected) == 5:
            break
    sections = ["The most recent week with significant recorded developments. Your promotion is prioritized; routine notices are omitted."]
    for index, row in enumerate(selected, 1):
        section = f"{index}. {row.get('headline', 'World story')}"
        detail = compact(row.get("detail"), 420)
        if detail and detail.casefold() != compact(row.get("headline")).casefold():
            section += "\n" + detail
        context = row.get("narrative_context", {}) or {}
        outlook = compact(context.get("outlook"), 280)
        if outlook and outlook not in detail:
            section += f"\n{context.get('outlook_label', 'Still at stake')}: {outlook}"
        sections.append(section)
    return {"type": "Weekly Digest", "headline": f"Week in stories: M{date[0]} W{date[1]}",
            "month": date[0], "week": date[1], "importance": 5,
            "detail": "\n\n".join(sections),
            "companies": list(dict.fromkeys(value for row in selected for value in row.get("companies", []) or [])),
            "fighters": list(dict.fromkeys(value for row in selected for value in row.get("fighters", []) or [])),
            "fighter_ids": list(dict.fromkeys(value for row in selected for value in row.get("fighter_ids", []) or []))}


def media_voice(fighter, action, band, target_name=""):
    """Authored game copy, not purported real quotations or invented fight facts."""
    name = fighter.name
    if getattr(fighter, "professionalism", 50) >= 75:
        approach = "A measured approach, with the emphasis on earning credibility."
    elif getattr(fighter, "charisma", 50) >= 75:
        approach = "An outspoken approach, with the emphasis on getting noticed."
    elif getattr(fighter, "age", 25) >= 34:
        approach = "A veteran's perspective rather than a promise of overnight success."
    else:
        approach = "An understated approach, leaving room for performances to make the case."
    reaction = {
        "Viral": "The campaign broke through into wider attention.",
        "Strong": "The campaign connected with its audience.",
        "Routine": "The campaign maintained a presence without a major breakthrough.",
        "Flat": "The campaign struggled to attract interest.",
        "Backlash": "The campaign drew backlash rather than winning over its audience.",
    }.get(band, "The campaign produced a recorded media response.")
    subject = f"{name}'s {action.lower()}"
    if action == "Call Out" and target_name:
        subject += f" aimed at {target_name}"
    return f"{subject}: {reaction} {approach}"
