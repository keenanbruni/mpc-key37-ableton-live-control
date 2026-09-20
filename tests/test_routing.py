import unittest
from MPC_Key_37.routing import PadRouter


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

    def test_reconnect_releases_and_resets(self):
        router = PadRouter()
        router.select("D", 10)
        router.receive(10, 127)
        self.assertEqual(router.reset(), [("arm", 0)])
        self.assertEqual(router.page, "A")
        self.assertEqual(router.receive(10, 0), [])
