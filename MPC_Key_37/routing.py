"""State for shared pad notes; independent of Live for replay testing."""
from .profile import BANK_A, BANK_D, BANK_E

PAGES = {
    "A": BANK_A,
    "B": tuple("clip_{}".format(i + 1) for i in range(16)),
    "C": tuple("scene_{}".format(i + 1) for i in range(16)),
    "D": BANK_D,
    "E": BANK_E,
}


class PadRouter:
    def __init__(self):
        self.page = "A"
        self._last_a = None
        self._held = {}

    def select(self, page, now):
        if page == "A" and self._last_a is not None and 0 <= now - self._last_a <= 0.4:
            self.page = "E"
            self._last_a = None
        else:
            self.page = page
            self._last_a = now if page == "A" else None
        # Release old destinations immediately when changing pages. A late
        # note-off must never be delivered to the new page's command.
        return self.release_all()

    def receive(self, pad, value):
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
        return events
