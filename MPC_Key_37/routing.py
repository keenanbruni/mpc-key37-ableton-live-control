"""State for shared pad notes; independent of Live for replay testing."""
from .profile import BANK_A, BANK_D, BANK_E

PAGES = {
    "A": BANK_A,
    "B": tuple("clip_{}".format(i + 1) for i in range(16)),
    "C": tuple("scene_{}".format(i + 1) for i in range(16)),
    "D": BANK_D,
    "E": BANK_E,
}

# A drum rack's 4x4 grid counts from C1 at the bottom-left pad, left to
# right, then upward; physical pads are numbered the same way.
DRUM_GRID_BASE_NOTE = 36


def canonical_pad_note(index):
    """Note a physical pad plays in the drum grid: C1 upward in pad order."""
    return DRUM_GRID_BASE_NOTE + index


def pad_translations(notes, channel):
    """(x, y, note, channel) entries mapping each hardware pad note to its
    grid position.  x counts right and y counts down from the top row."""
    return tuple(
        (index % 4, 3 - index // 4, note, channel - 1)
        for index, note in enumerate(notes))


class PadRouter:
    def __init__(self):
        self.page = "A"
        self._last_a = None
        self._last_d = None
        self._held = {}

    def select(self, page, now):
        if page == "A" and self._last_a is not None and 0 <= now - self._last_a <= 0.4:
            self.page = "E"
            self._last_a = None
        elif page == "D" and self._last_d is not None and 0 <= now - self._last_d <= 0.4:
            # Performance mode deliberately has no virtual pad actions.  The
            # MPC's pad notes remain available to an armed Live instrument.
            self.page = "P"
            self._last_d = None
        else:
            self.page = page
            self._last_a = now if page == "A" else None
            self._last_d = now if page == "D" else None
        # Release old destinations immediately when changing pages. A late
        # note-off must never be delivered to the new page's command.
        return self.release_all()

    def receive(self, pad, value):
        if self.page == "P":
            return []
        if value:
            if pad in self._held:
                return []
            action = PAGES[self.page][pad]
            self._held[pad] = action
            return [(action, value)]
        action = self._held.pop(pad, None)
        return [(action, 0)] if action else []

    def release_all(self):
        events = [(action, 0) for action in self._held.values()]
        self._held.clear()
        return events

    def reset(self):
        events = self.release_all()
        self.page = "A"
        self._last_a = None
        self._last_d = None
        return events
