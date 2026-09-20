import unittest
from MPC_Key_37.routing import PadRouter, canonical_pad_note, pad_translations


class RouterTests(unittest.TestCase):
    def test_same_pad_is_routed_by_page(self):
        router = PadRouter()
        self.assertEqual(router.receive(0, 127), [("previous_device", 127)])
        self.assertEqual(router.select("B", 1), [("previous_device", 0)])
        self.assertEqual(router.receive(0, 0), [])
        self.assertEqual(router.receive(0, 127), [("clip_1", 127)])

    def test_no_duplicate_press_or_release(self):
        router = PadRouter()
        router.receive(0, 127)
        self.assertEqual(router.receive(0, 90), [])
        self.assertEqual(router.receive(0, 0), [("previous_device", 0)])
        self.assertEqual(router.receive(0, 0), [])

    def test_deliberate_double_a_opens_commands(self):
        router = PadRouter()
        router.select("A", 10)
        router.select("A", 10.25)
        self.assertEqual(router.page, "E")
        router.select("A", 12)
        self.assertEqual(router.page, "A")
        router.select("A", 13)
        self.assertEqual(router.page, "A")

    def test_double_d_opens_performance_page_without_commands(self):
        router = PadRouter()
        router.select("D", 10)
        router.select("D", 10.25)
        self.assertEqual(router.page, "P")
        self.assertEqual(router.receive(0, 127), [])
        self.assertEqual(router.receive(0, 0), [])
        router.select("D", 12)
        self.assertEqual(router.page, "D")

    def test_reconnect_releases_and_resets(self):
        router = PadRouter()
        router.select("D", 10)
        router.receive(10, 127)
        self.assertEqual(router.reset(), [("arm", 0)])
        self.assertEqual(router.page, "A")
        self.assertEqual(router.receive(10, 0), [])

    def test_canonical_notes_follow_physical_pad_order(self):
        self.assertEqual([canonical_pad_note(i) for i in range(16)],
                         list(range(36, 52)))

    def test_pad_translations_place_hardware_notes_on_the_grid(self):
        # The captured MPC Key 37 pad notes are scattered; the grid positions
        # must still run bottom-left across each row, then upward.
        notes = [37, 36, 42, 82, 40, 38, 46, 44, 48, 47, 45, 43, 49, 55, 51, 53]
        self.assertEqual(pad_translations(notes, 10), (
            (0, 3, 37, 9), (1, 3, 36, 9), (2, 3, 42, 9), (3, 3, 82, 9),
            (0, 2, 40, 9), (1, 2, 38, 9), (2, 2, 46, 9), (3, 2, 44, 9),
            (0, 1, 48, 9), (1, 1, 47, 9), (2, 1, 45, 9), (3, 1, 43, 9),
            (0, 0, 49, 9), (1, 0, 55, 9), (2, 0, 51, 9), (3, 0, 53, 9)))
