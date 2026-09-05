"""Deterministic, cosmetic fighter portrait support.

The public imports intentionally keep the identity model usable without Tk.
Rendering is imported lazily so headless simulation and data tools never need
to initialise an image backend.
"""

from .identity import (
    CURRENT_PORTRAIT_VERSION,
    ensure_portrait_identity,
    portrait_identity,
    trait_hash,
)
from .state import portrait_state


def render_portrait(canvas, fighter, size=None, ratings_visible=True, **options):
    """Draw *fighter* using the standard-library renderer."""
    from .render import render_portrait as _render_portrait
    return _render_portrait(canvas, fighter, size=size, ratings_visible=ratings_visible, **options)


__all__ = (
    "CURRENT_PORTRAIT_VERSION", "ensure_portrait_identity", "portrait_identity",
    "portrait_state", "render_portrait", "trait_hash",
)
