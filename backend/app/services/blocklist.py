"""Fast local safety net — layer 2 of the moderation stack.

Not a substitute for the classifier: it only catches the most blatant terms so
an obviously bad draft never even reaches the (paid, slower) Claude check. Word
boundaries keep it from tripping on substrings ("wapenstilstand" is fine,
"knal" is not blocked, etc.). Deliberately conservative and easy to extend.
"""

from __future__ import annotations

import re

# Dutch + a few English terms. Lowercase; matched on word boundaries.
_BLOCKED_TERMS: tuple[str, ...] = (
    # violence / weapons
    "pistool", "geweer", "mes steken", "neersteken", "wapen", "kogel",
    "bom", "explosie", "bloed", "vermoord", "moord", "doodschieten",
    "gun", "knife", "kill", "blood", "weapon",
    # death / grief
    "begrafenis", "overleden", "gestorven", "dood ging", "doodgaan",
    # adult / substances  ("dronken" is also past-tense of "drinken", so skip it)
    "alcohol", "dronkaard", "sigaret", "drugs", "seks", "naakt",
    # scary
    "nachtmerrie", "demon", "duivel", "kwelling", "martel",
)

_PATTERN = re.compile(
    r"\b(" + "|".join(re.escape(t) for t in _BLOCKED_TERMS) + r")\b",
    re.IGNORECASE,
)


def find_blocked_terms(*texts: str) -> list[str]:
    """Return the distinct blocked terms found across the given texts."""
    found: list[str] = []
    for text in texts:
        for match in _PATTERN.findall(text or ""):
            term = match.lower()
            if term not in found:
                found.append(term)
    return found
