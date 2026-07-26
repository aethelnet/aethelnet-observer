"""
ASCII art utilities for the bot.

This module provides a minimal, backward-compatible ASCIIArt class with a
get_phase_totem method so handlers that expect that API will not raise
AttributeError. Implementations can be extended later with richer artwork.
"""

from typing import Optional


class ASCIIArt:
    """Utility for generating simple ASCII totems / phase indicators."""

    @staticmethod
    def get_totem(phase: Optional[int] = 0) -> str:
        """
        Return a simple totem representation for a given phase.

        phase may be an int or a string that can be converted to int. Unknown
        values fall back to a generic symbol.
        """
        try:
            idx = int(phase) if phase is not None else 0
        except Exception:
            idx = 0

        # Simple mapping — expand as needed.
        mapping = {
            0: "(.)",
            1: "/\\",
            2: "<*>",
            3: "[#]",
            4: "{*}"
        }
        return mapping.get(idx, "(.)")

    @staticmethod
    def get_phase_totem(phase: Optional[int] = 0) -> str:
        """
        Backward-compatible wrapper expected by handlers.

        Delegates to get_totem to preserve a single source of truth.
        """
        return ASCIIArt.get_totem(phase)

    @staticmethod
    def render_phase_totem(phase: Optional[int] = 0) -> str:
        """
        Return a slightly more descriptive string for UI display.
        """
        totem = ASCIIArt.get_totem(phase)
        return f"PHASE {phase}: {totem}"


__all__ = ["ASCIIArt"]
