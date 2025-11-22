"""UI tab configuration helpers decoupled from the GUI toolkit."""

from __future__ import annotations

DEFAULT_TABS = [
    ("Physiologie", "I. Physiologische Mikroanalyse", "physiology"),
    ("Psychologie", "II. Psycho-Neurologische Tiefenanalyse", "psychology"),
    ("Sensorik", "III. Sensorische Mikroprofile", "sensory"),
    ("Historie", "IV. Entwicklungsgeschichte", "history"),
    ("GEM-Matrix", "XI. GEM V1.3 Steuerungs-Matrix", "gem_matrix"),
]

STATIC_TABS = ["Dossier", "Chat-Labor"]


def all_tab_names() -> list[str]:
    """Return the ordered list of tab labels used by the UI."""

    return [tab_name for tab_name, _, _ in DEFAULT_TABS] + list(STATIC_TABS)
