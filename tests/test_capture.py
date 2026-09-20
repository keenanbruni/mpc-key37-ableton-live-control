import unittest
from tools.capture_midi import Decoder


class CaptureTests(unittest.TestCase):
    def test_running_status_across_packets_and_realtime(self):
        decoder = Decoder()
        self.assertEqual(list(decoder.feed([0xBF, 100])), [])
        rows = list(decoder.feed([1, 101, 0xF8, 127]))
        self.assertEqual([(r["identifier"], r["value"]) for r in rows], [(100, 1), (101, 127)])
        self.assertTrue(all(r["channel"] == 16 for r in rows))

    def test_pressure_and_releases_are_distinct(self):
        rows = list(Decoder().feed([0x90, 36, 100, 0xA0, 36, 20, 0x80, 36, 0, 0x90, 36, 0]))
        self.assertEqual([r["type"] for r in rows], ["note", "poly_pressure", "note_off", "note"])
        self.assertEqual(rows[-1]["value"], 0)

    def test_pitchbend_and_split_sysex(self):
        decoder = Decoder()
        rows = list(decoder.feed([0xEF, 0, 64, 0xF0, 0x47]))
        self.assertEqual(rows[0]["value"], 8192)
        self.assertEqual(list(decoder.feed([0xF8, 0, 0xF7]))[0]["bytes"], [0xF0, 0x47, 0, 0xF7])

    def test_system_common_cancels_running_status(self):
        decoder = Decoder()
        rows = list(decoder.feed([0x90, 60, 100, 0xF2, 1, 2, 61, 100]))
        self.assertEqual(len(rows), 1)
