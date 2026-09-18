"""Observational trait cards shared by fighter profile pages."""
import tkinter as tk
from tkinter import ttk

from fighter_traits import TRAIT_DEFINITIONS


CATEGORY_COLORS = {
    "Combat": "#dca166", "Development": "#81c995", "Recovery": "#79c5d3",
    "Commercial": "#d6bb70", "Personality": "#bca1dd",
}


def build_trait_card(app, parent, fighter, stats_visible=True, expanded=False):
    """Create a width-aware card without changing the fighter or consuming RNG."""
    colors = app.colors
    background = colors["panel"]
    card = tk.Frame(parent, bg=background, highlightthickness=1,
                    highlightbackground=colors["line"])
    if not stats_visible:
        tk.Label(card, text="TRAIT • UNKNOWN", bg=background, fg=colors["muted"],
                 font=("Tahoma", 10, "bold"), anchor="w").pack(fill="x", padx=16, pady=(14, 6))
        label = tk.Label(card, text="Scout this fighter to reveal their trait and its effects.",
                         bg=background, fg=colors["text"], font=("Tahoma", 10),
                         anchor="w", justify="left", wraplength=300)
        label.pack(fill="x", padx=16, pady=(0, 16))
        card.bind("<Configure>", lambda event: label.configure(wraplength=max(80, event.width - 36)))
        return card

    name = str(getattr(fighter, "trait", "") or "Unknown")
    definition = TRAIT_DEFINITIONS.get(name, {})
    category = definition.get("category", "Personality")
    accent = CATEGORY_COLORS.get(category, colors["gold"])
    readable = getattr(app, "accessible_tab_text", lambda _background, preferred: preferred)
    accent_text = readable(background, accent)
    tk.Frame(card, height=3, bg=accent).pack(fill="x")
    body = tk.Frame(card, bg=background)
    body.pack(fill="both", expand=True, padx=16, pady=12)
    labels = []

    def line(parent_widget, text, foreground=None, font=None, padding=(0, 5)):
        label = tk.Label(parent_widget, text=text, bg=background,
                         fg=foreground or colors["text"], font=font or ("Tahoma", 10),
                         justify="left", anchor="w", wraplength=300)
        label.pack(fill="x", pady=padding)
        labels.append(label)
        return label

    line(body, f"{category.upper()} TRAIT", accent_text, ("Tahoma", 8, "bold"))
    line(body, name, colors["text"], ("Tahoma", 16, "bold"))
    line(body, definition.get("description", "No verified trait definition is available."))
    strength = definition.get("strength", "Not assessed")
    line(body, f"Strength: {strength}", colors["muted"], ("Tahoma", 9))
    if definition.get("personality_only"):
        line(body, "PERSONALITY ONLY • No direct mechanical modifier", accent_text, ("Tahoma", 8, "bold"))

    details = tk.Frame(body, bg=background)
    for title, key in (("ADVANTAGES", "advantages"), ("DRAWBACKS", "drawbacks"), ("WHEN IT APPLIES", "triggers")):
        line(details, title, accent_text, ("Tahoma", 8, "bold"), (7, 3))
        value = definition.get(key) or "None specified."
        if isinstance(value, (tuple, list)):
            value = "\n".join(str(item) for item in value)
        line(details, str(value))

    progress = getattr(fighter, "trait_progress", {}) or {}
    if isinstance(progress, dict) and progress.get("target"):
        line(details, "DEVELOPING HABIT", accent_text, ("Tahoma", 8, "bold"), (7, 3))
        points = max(0, min(100, int(progress.get("points", 0) or 0)))
        line(details, f"{progress['target']} • {points}/100 progress")
        meter = tk.Canvas(details, height=8, bg=background, highlightthickness=0)
        meter.pack(fill="x", pady=(0, 5))
        def draw_progress(event):
            meter.delete("all")
            meter.create_rectangle(0, 0, event.width, 8, fill=colors["line"], outline="")
            if points:
                meter.create_rectangle(0, 0, event.width * points / 100, 8, fill=accent, outline="")
        meter.bind("<Configure>", draw_progress)
        line(details, "Repeated compatible camps build lasting change.", colors["muted"], ("Tahoma", 9))
    history = getattr(fighter, "trait_history", []) or []
    if history:
        latest = history[-1]
        if isinstance(latest, dict):
            previous = latest.get("from", latest.get("old_trait", ""))
            current = latest.get("to", latest.get("new_trait", name))
            if previous:
                line(details, f"Last change: {previous} → {current}", colors["muted"], ("Tahoma", 9))

    shown = [bool(expanded)]
    def toggle():
        shown[0] = not shown[0]
        render_expansion()

    button = ttk.Button(body, command=toggle)
    button.pack(anchor="w", pady=(6, 0))

    def render_expansion():
        button.configure(text="Hide Trait Effects −" if shown[0] else "Show Trait Effects +")
        if shown[0]:
            details.pack(fill="x", before=button)
        else:
            details.pack_forget()

    def resize(event):
        for label in labels:
            label.configure(wraplength=max(80, event.width - 36))

    card.bind("<Configure>", resize, add="+")
    render_expansion()
    return card
