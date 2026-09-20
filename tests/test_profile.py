import copy
import unittest

from MPC_Key_37.profile import load, validate, four_parameters, bounded_offset, ACTIONS


class ProfileTests(unittest.TestCase):
    def test_complete_default_mapping(self):
        profile = load()
        self.assertEqual(set(profile["buttons"]), set(ACTIONS))

    def test_duplicate_and_performance_collision_rejected(self):
        profile = copy.deepcopy(load())
        profile["buttons"]["stop"] = profile["buttons"]["play"].copy()
        with self.assertRaisesRegex(ValueError, "Duplicate"):
            validate(profile)
        profile = copy.deepcopy(load())
        profile["knobs"][0]["channel"] = profile["performance_channel"]
        with self.assertRaisesRegex(ValueError, "performance"):
            validate(profile)

    def test_invalid_encodings_and_ranges_rejected(self):
        for field, value in (("channel", 0), ("channel", 17), ("identifier", 128),
                             ("encoding", "guessed"), ("channel", True)):
            profile = copy.deepcopy(load())
            profile["knobs"][0][field] = value
            with self.assertRaises(ValueError):
                validate(profile)

    def test_unavailable_controls_can_be_disabled(self):
        profile = copy.deepcopy(load())
        profile["knobs"][0] = None
        profile["buttons"]["play"] = None
        self.assertIs(validate(profile), profile)

    def test_half_bank_preserves_holes_and_order(self):
        values = ["a", None, "c", "d", "e", "f"]
        self.assertEqual(four_parameters(values, 0), ["a", None, "c", "d"])
        self.assertEqual(four_parameters(values, 1), ["e", "f", None, None])
        self.assertEqual(four_parameters([], 1), [None] * 4)

    def test_offsets_clamp_at_empty_short_and_last_page(self):
        for size in (0, 1, 3):
            self.assertEqual(bounded_offset(0, 4, size, 4), 0)
        self.assertEqual(bounded_offset(4, -16, 20, 4), 0)
        self.assertEqual(bounded_offset(16, 4, 21, 4), 17)
        self.assertEqual(bounded_offset(16, 0, 5, 4), 1)
