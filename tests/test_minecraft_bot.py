import unittest
from unittest.mock import MagicMock, patch, mock_open
import json
import os
import sys

# Ensure scripts can be imported
sys.path.append(os.path.join(os.getcwd(), 'scripts'))

from minecraft_bot import get_playtime_top

class TestPlaytime(unittest.TestCase):
    @patch('minecraft_bot.os.path.exists')
    @patch('minecraft_bot.os.listdir')
    @patch('minecraft_bot.open')
    @patch('minecraft_bot.os.path.dirname')
    def test_get_playtime_top(self, mock_dirname, mock_file_open, mock_listdir, mock_exists):
        # Setup mocks
        mock_dirname.return_value = "/data"
        mock_exists.return_value = True
        mock_listdir.return_value = ["uuid1.json", "uuid2.json", "other.txt"]

        # User cache content
        user_cache_data = [
            {"uuid": "uuid1", "name": "Player1"},
            {"uuid": "uuid2", "name": "Player2"}
        ]

        # Stats content
        stats_uuid1 = {
            "stats": {
                "minecraft:custom": {
                    "minecraft:play_time": 72000 # 1 hour
                }
            }
        }
        stats_uuid2 = {
            "stats": {
                "minecraft:custom": {
                    "minecraft:play_time": 144000 # 2 hours
                }
            }
        }

        def side_effect(filename, mode='r'):
            content = "{}"
            if "usercache.json" in filename:
                content = json.dumps(user_cache_data)
            elif "uuid1.json" in filename:
                content = json.dumps(stats_uuid1)
            elif "uuid2.json" in filename:
                content = json.dumps(stats_uuid2)

            m = mock_open(read_data=content).return_value
            return m

        mock_file_open.side_effect = side_effect

        # Run function
        result = get_playtime_top()

        # Assertions
        print(f"Result:\n{result}")
        self.assertIn("🏆 *Top Playtime:*", result)
        self.assertIn("1. 👤 *Player2:* `2.0 hours`", result)
        self.assertIn("2. 👤 *Player1:* `1.0 hours`", result)

    @patch('minecraft_bot.os.path.exists')
    @patch('minecraft_bot.os.listdir')
    @patch('minecraft_bot.open')
    @patch('minecraft_bot.os.path.dirname')
    def test_get_playtime_top_empty(self, mock_dirname, mock_file_open, mock_listdir, mock_exists):
        # Setup mocks for empty result
        mock_dirname.return_value = "/data"
        mock_exists.return_value = True
        mock_listdir.return_value = [] # No files

        def side_effect(filename, mode='r'):
            if "usercache.json" in filename:
                return mock_open(read_data="[]").return_value
            return mock_open(read_data="{}").return_value

        mock_file_open.side_effect = side_effect

        # Run function
        result = get_playtime_top()

        # Assertions
        print(f"Result Empty:\n{result}")
        self.assertEqual(result, "No stats available.")

if __name__ == '__main__':
    unittest.main()
