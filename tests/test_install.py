import json
from pathlib import Path
import tempfile
import unittest
import zipfile
from tools.install import install


class InstallTests(unittest.TestCase):
    def test_update_preserves_profile_and_backs_up(self):
        with tempfile.TemporaryDirectory() as temp:
            library = Path(temp)
            destination, backup = install(library)
            self.assertIsNone(backup)
            config = destination / "midi_profile.json"
            profile = json.loads(config.read_text())
            profile["name"] = "My verified preset"
            config.write_text(json.dumps(profile))
            _, backup = install(library)
            self.assertEqual(json.loads(config.read_text())["name"], "My verified preset")
            with zipfile.ZipFile(backup) as archive:
                self.assertEqual(json.loads(archive.read("MPC_Key_37/midi_profile.json"))["name"], "My verified preset")
            self.assertFalse((destination / "__pycache__").exists())
            install(library, replace_profile=True)
            self.assertNotEqual(json.loads(config.read_text())["name"], "My verified preset")
