import sys
import os
import unittest
import json
from unittest.mock import MagicMock, patch

# Mock dependencies that are not installed or have side effects on import
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()
sys.modules["subprocess"] = MagicMock()

# Add parent directory to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

try:
    import scripts.minecraft_bot as bot
    from scripts.minecraft_bot import strip_ansi
except ImportError:
    pass

class TestMinecraftBot(unittest.TestCase):

    # Original tests from main (converted to unittest style)
    def test_strip_ansi_empty(self):
        self.assertEqual(strip_ansi(""), "")

    def test_strip_ansi_no_ansi(self):
        text = "Hello World"
        self.assertEqual(strip_ansi(text), text)

    def test_strip_ansi_with_color(self):
        text = "\x1b[31mRed Text\x1b[0m"
        self.assertEqual(strip_ansi(text), "Red Text")

    def test_strip_ansi_multiple_codes(self):
        text = "\x1b[1m\x1b[32mBold Green\x1b[0m"
        self.assertEqual(strip_ansi(text), "Bold Green")

    def test_strip_ansi_complex(self):
        text = "Normal \x1b[33mYellow\x1b[0m Mixed \x1b[44mBlueBG\x1b[0m"
        self.assertEqual(strip_ansi(text), "Normal Yellow Mixed BlueBG")

    def test_strip_ansi_other_escapes(self):
        # Test some other CSI sequences
        text = "Hello\x1b[2JWorld" # Clear screen
        self.assertEqual(strip_ansi(text), "HelloWorld")

    # New tests for get_playtime_top
    def setUp(self):
        # Create temporary directory structure
        self.test_dir = "/tmp/minecraft_bot_test"
        if not os.path.exists(self.test_dir):
            os.makedirs(self.test_dir)

        self.stats_dir = os.path.join(self.test_dir, "world", "stats")
        os.makedirs(self.stats_dir, exist_ok=True)

        self.properties_file = os.path.join(self.test_dir, "server.properties")
        with open(self.properties_file, "w") as f:
            f.write("pvp=true\n")

        # Patch PROPERTIES_FILE in the imported module
        bot.PROPERTIES_FILE = self.properties_file

    def tearDown(self):
        import shutil
        if os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_get_playtime_top_empty(self):
        msg = bot.get_playtime_top()
        self.assertEqual(msg, "No stats available.")

    def test_get_playtime_top_with_data(self):
        # Create usercache.json
        usercache = [{"name": "Player1", "uuid": "uuid1"}]
        with open(os.path.join(self.test_dir, "usercache.json"), "w") as f:
            json.dump(usercache, f)

        # Create stat file
        stat_data = {
            "stats": {
                "minecraft:custom": {
                    "minecraft:play_time": 72000 # 1 hour
                }
            }
        }
        with open(os.path.join(self.stats_dir, "uuid1.json"), "w") as f:
            json.dump(stat_data, f)

        msg = bot.get_playtime_top()
        self.assertIn("Player1", msg)
        self.assertIn("1.0 hours", msg)

    def test_get_playtime_top_malformed_json_inner_catch(self):
        # Create malformed stat file to trigger inner except
        with open(os.path.join(self.stats_dir, "bad.json"), "w") as f:
            f.write("{ invalid json }")

        # Create valid usercache
        with open(os.path.join(self.test_dir, "usercache.json"), "w") as f:
            f.write("[]")

        # Should check behavior when inner except catches error
        msg = bot.get_playtime_top()
        self.assertEqual(msg, "No stats available.")

    def test_get_playtime_top_outer_exception_oserror(self):
        # Mock os.listdir to raise OSError
        with patch("os.listdir", side_effect=OSError("Disk error")):
            msg = bot.get_playtime_top()
            self.assertIn("Error calculating stats: Disk error", msg)

    def test_get_playtime_top_outer_exception_typeerror(self):
        # Case 1: usercache is null
        with open(os.path.join(self.test_dir, "usercache.json"), "w") as f:
            f.write("null")

        msg = bot.get_playtime_top()
        # Should catch TypeError
        self.assertIn("Error calculating stats", msg)

    def test_get_playtime_top_outer_exception_keyerror(self):
        # Create usercache with missing keys
        usercache = [{"name": "Player1"}] # missing uuid
        with open(os.path.join(self.test_dir, "usercache.json"), "w") as f:
            json.dump(usercache, f)

        msg = bot.get_playtime_top()
        # Should catch KeyError
        self.assertIn("Error calculating stats", msg)

if __name__ == "__main__":
    unittest.main()
