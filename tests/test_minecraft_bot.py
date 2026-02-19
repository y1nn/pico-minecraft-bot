import sys
import unittest
from unittest.mock import MagicMock, patch, mock_open

# Mock dependencies that are not installed or have side effects on import
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

# Now import the functions to test
from scripts.minecraft_bot import strip_ansi, read_all_properties, read_property, PROPERTIES_FILE

class TestMinecraftBot(unittest.TestCase):

    def test_strip_ansi_empty(self):
        self.assertEqual(strip_ansi(""), "")

    def test_strip_ansi_no_ansi(self):
        text = "Hello World"
        self.assertEqual(strip_ansi(text), text)

    def test_strip_ansi_with_color(self):
        text = "\x1b[31mRed Text\x1b[0m"
        self.assertEqual(strip_ansi(text), "Red Text")

    @patch('builtins.open', new_callable=mock_open, read_data="pvp=true\nmax-players=20\n#comment=ignored")
    @patch('scripts.minecraft_bot.PROPERTIES_FILE', 'server.properties') # Mock the constant if possible, or use side_effect
    def test_read_all_properties_success(self, mock_file):
        # We need to ensure read_all_properties uses the mocked open
        # The function uses the global PROPERTIES_FILE which is imported.
        # However, since we patched builtins.open, any open call will use it.
        props = read_all_properties()
        self.assertEqual(props.get('pvp'), 'true')
        self.assertEqual(props.get('max-players'), '20')
        self.assertNotIn('#comment', props)

    @patch('builtins.open', side_effect=FileNotFoundError)
    def test_read_all_properties_file_not_found(self, mock_file):
        props = read_all_properties()
        self.assertEqual(props, {})

    @patch('scripts.minecraft_bot.read_all_properties')
    def test_read_property_uses_read_all(self, mock_read_all):
        mock_read_all.return_value = {'pvp': 'false'}
        val = read_property('pvp')
        self.assertEqual(val, 'false')
        mock_read_all.assert_called_once()

if __name__ == '__main__':
    unittest.main()
