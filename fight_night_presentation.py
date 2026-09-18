"""Read-only presentation of recorded fight commentary in a Tk Text timeline."""
import re


TIMELINE_TAGS = frozenset({
    "heading", "result", "round", "round_separator", "clock", "action",
    "analysis", "separator", "metrics", "knockdown", "finish", "cut",
    "referee", "impact", "narrative",
})
_CLOCK = re.compile(r"^\s*\[\d{1,2}:\d{2}\]")


def classify_fight_line(value):
    """Classify explicit source structure; incidental combat words are narrative.

    In particular, mentioning a potential finish, cut or knockdown cannot establish
    that it happened. A caller with an existing event tag may pass that tag instead.
    """
    source = str(value).strip()
    if source and set(source) <= set("-=─━_ "):
        return "separator"
    if re.match(r"^(?:Result:|OFFICIAL (?:RESULT|SCORECARDS)\b)", source, re.I):
        return "result"
    if re.match(r"^(?:Finish|Stoppage):", source, re.I):
        return "finish"
    if re.match(r"^(?:Round|Period)\s+\d+\s+summary:", source, re.I):
        return "analysis"
    if re.match(r"^(?:ROUND\s+\d+|PERIOD\s+\d+|MATCH CLOCK|R\d+\s*:|Match:)", source, re.I):
        return "round"
    if re.match(r"^(?:Corner read|Mat-side read|Broadcast read|Broadcast desk|Fight-night readiness|Corner):", source, re.I):
        return "analysis"
    if re.match(r"^(?:FIGHT METRICS\b|Metrics:|Statistics:|Box score:)", source, re.I):
        return "metrics"
    if _CLOCK.match(source):
        # Only emphatic, positive recorded phrases earn an event accent. Mere
        # mention of danger, a possible cut or being hard to knock down does not.
        negated = re.search(r"\b(?:not|never|without|no|cannot)\b|n't\b", source, re.I)
        if not negated:
            if re.search(r"\b(?:referee(?: has seen enough and)? stops? (?:the )?(?:fight|contest)|gets the tap|(?:has|had|have) to tap|taps? to|and it's all over|goes unconscious|loses consciousness)\b", source, re.I):
                return 'finish'
            if re.search(r"\b(?:scores a knockdown|is knocked down|goes down hard|hits the canvas)\b", source, re.I):
                return 'knockdown'
            if re.search(r"\b(?:visible (?:reddening|bruising|swelling|damage|limp)|reddening spreads|opens? (?:up )?a cut|"
                         r"swelling (?:forms|worsens|spreads)|bruising (?:forms|worsens|spreads)|guarding the midsection|"
                         r"laboured breathing|shifts? (?:their|his|her) weight)\b", source, re.I):
                return "cut"
            # A technique name or an attempted lane is not a landed impact.
            # Require an authored contact verb; defended elbows/body catches
            # therefore remain ordinary action text.
            if re.search(r"\b(?:lands|connects|gets through|reaches|drives|slams|finds)\b", source, re.I):
                return "impact"
        return "action"
    if re.match(r"^(?:MAIN EVENT|CO-MAIN EVENT|TITLE BOUT|INTERIM TITLE|BOUT\s+\d+)\b", source, re.I):
        return "heading"
    return "narrative"


def _readable(text, foreground, background):
    def luminance(color):
        rgb = [channel / 65535 for channel in text.winfo_rgb(color)]
        linear = [v / 12.92 if v <= .04045 else ((v + .055) / 1.055) ** 2.4 for v in rgb]
        return sum(v * weight for v, weight in zip(linear, (.2126, .7152, .0722)))
    base = luminance(background)
    def ratio(color):
        other = luminance(color)
        return (max(base, other) + .05) / (min(base, other) + .05)
    if ratio(foreground) >= 4.5:
        return foreground
    return max(("#ffffff", "#111111"), key=ratio)


def _blend(text, background, accent, accent_share):
    """Return a stable theme-derived tint without changing either input palette."""
    base = text.winfo_rgb(background)
    color = text.winfo_rgb(accent)
    mixed = [round((a * (1 - accent_share) + b * accent_share) / 257) for a, b in zip(base, color)]
    return "#" + "".join(f"{max(0, min(255, channel)):02x}" for channel in mixed)


def configure_fight_timeline(text, colors, font_size=11):
    """Apply theme-derived colours and paragraph geometry; keep existing content."""
    size = max(9, min(24, int(font_size)))
    background = colors.get("panel", colors.get("chrome", text.cget("background")))
    foreground = _readable(text, colors.get("text", "#ffffff"), background)
    accent = _readable(text, colors.get("gold", foreground), background)
    muted = _readable(text, colors.get("muted", foreground), background)
    impact = _readable(text, colors.get("red", accent), background)
    gutter = size * 7
    text.configure(bg=background, fg=foreground, insertbackground=foreground,
                   font=("Tahoma", size), wrap="word", padx=18, pady=14,
                   spacing1=4, spacing2=3, spacing3=8)
    for tag in TIMELINE_TAGS:
        text.tag_configure(tag, foreground=foreground, background=background,
                           font=("Tahoma", size), lmargin1=0, lmargin2=0,
                           rmargin=8, spacing1=4, spacing2=3, spacing3=8)
    for tag in ("heading", "round", "result"):
        text.tag_configure(tag, foreground=accent, font=("Tahoma", size + 1, "bold"),
                           spacing1=14, spacing3=10)
    text.tag_configure("action", lmargin2=gutter)
    text.tag_configure("timeline_hanging", lmargin2=gutter)
    text.tag_configure("clock", foreground=muted, font=("Consolas", size, "bold"))
    text.tag_configure("analysis", foreground=muted, font=("Tahoma", size, "italic"),
                       lmargin1=14, lmargin2=14, spacing1=8, spacing3=10)
    text.tag_configure("metrics", font=("Consolas", max(9, size - 1)), spacing1=2, spacing3=2)
    for tag in ("separator", "round_separator"):
        text.tag_configure(tag, foreground=muted, font=("Consolas", 9), spacing1=4, spacing3=4)
    event_styles = {
        "impact": (colors.get("gold", accent), .16, size),
        "cut": (colors.get("red", impact), .30, size),
        "knockdown": (colors.get("gold", accent), .34, size + 1),
        "referee": (colors.get("gold", accent), .22, size),
        "finish": (colors.get("red", impact), .48, size + 1),
    }
    for tag, (color, strength, event_size) in event_styles.items():
        event_background = _blend(text, background, color, strength)
        text.tag_configure(tag, background=event_background,
                           foreground=_readable(text, foreground, event_background),
                           font=("Tahoma", event_size, "bold"),
                           lmargin1=12, lmargin2=gutter, rmargin=14,
                           spacing1=9, spacing2=4, spacing3=11,
                           relief="raised", borderwidth=1)
    # The timestamp has a span tag, so it takes priority only over its own glyphs.
    text.tag_raise("clock")


def insert_fight_timeline_line(text, value, tag=None):
    """Insert the complete source, adding only a missing terminal newline.

    Caller tags must belong to TIMELINE_TAGS. No filtering, name substitutions,
    summary rewriting or outcome inspection occurs here. Return the chosen tag.
    """
    source = str(value)
    category = classify_fight_line(source) if tag is None else tag
    if category not in TIMELINE_TAGS:
        raise ValueError(f"Unknown fight timeline tag: {category!r}")
    old_state = str(text.cget("state"))
    if old_state == "disabled":
        text.configure(state="normal")
    try:
        start = text.index("end-1c")
        text.insert("end", source + ("" if source.endswith("\n") else "\n"), category)
        clock = _CLOCK.match(source)
        if clock:
            text.tag_add("clock", start, f"{start}+{clock.end()}c")
            # Hanging geometry applies to the paragraph, without replacing source
            # spaces with tabs or changing the archived timestamp text.
            text.tag_add("timeline_hanging", start, f"{start}+{len(source)}c")
            text.tag_raise("timeline_hanging")
            text.tag_raise("clock")
    finally:
        if old_state == "disabled":
            text.configure(state="disabled")
    return category
