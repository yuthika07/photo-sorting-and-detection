"""
Concrete folder-naming implementation.
"""

from __future__ import annotations

import re
from typing import Sequence

from app.db.models.person import Person
from app.services.export.interfaces import FolderNamerBase

# Anything that isn't a letter, digit, underscore, or hyphen is stripped
# out — this is what keeps folder names safe across Windows, macOS, and
# Linux, all of which forbid or mishandle different sets of characters
# (":", "/", "\", etc). Being conservative (allow-list, not deny-list)
# means a name like "O'Brien / Priya" degrades safely instead of
# accidentally producing a path with an extra directory in it.
_UNSAFE_CHARACTERS = re.compile(r"[^A-Za-z0-9_-]+")


class PersonFolderNamer(FolderNamerBase):
    """
    Builds an output folder name from one or more Person rows.

    - Searching by one person -> that person's name, e.g. "Alice".
    - Searching by several people -> their names joined with an
      underscore, e.g. "Alice_Bob" — matching this phase's requirement
      that "person1 + person2" produces a "person1_person2" folder.

    People are always sorted by id before naming, so searching
    "Bob + Alice" produces the exact same folder name as
    "Alice + Bob" — the folder a repeat export lands in shouldn't
    depend on the order ids happened to be passed in.
    """

    def build_folder_name(self, persons: Sequence[Person]) -> str:
        """
        Args:
            persons: the people this export was searched by.

        Returns:
            A filesystem-safe folder name.
        """
        sorted_persons = sorted(persons, key=lambda person: person.id)
        labels = [self._sanitize(self._label_for(person)) for person in sorted_persons]
        return "_".join(labels)

    @staticmethod
    def _label_for(person: Person) -> str:
        """
        Use the person's display name if they have one; fall back to a
        stable, still-readable "Person_<id>" if they don't (an
        unconfirmed, auto-clustered person from Phase 6 may not have
        been named yet).
        """
        return person.display_name if person.display_name else f"Person_{person.id}"

    @classmethod
    def _sanitize(cls, label: str) -> str:
        """
        Turn a display name into a safe path component: spaces become
        underscores, then anything else unsafe is stripped entirely.
        """
        collapsed = label.strip().replace(" ", "_")
        cleaned = _UNSAFE_CHARACTERS.sub("", collapsed)
        # A name that was ENTIRELY unsafe characters (rare, but
        # possible) would otherwise collapse to an empty string, which
        # is not a usable path component — fall back to something safe
        # rather than producing a broken folder name.
        return cleaned or "Unnamed"
