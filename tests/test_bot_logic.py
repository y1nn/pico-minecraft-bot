import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add scripts to path so we can import minecraft_bot
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'scripts'))

import minecraft_bot

class TestBotLogic(unittest.TestCase):

    def setUp(self):
        self.chat_id = 12345
        minecraft_bot.ALLOWED_CHAT_IDS = [self.chat_id]

    @patch('minecraft_bot.stop_server')
    @patch('minecraft_bot.answer_callback')
    @patch('minecraft_bot.edit_message')
    @patch('minecraft_bot.get_server_status')
    @patch('minecraft_bot.get_main_keyboard')
    @patch('time.sleep')
    def test_stop_server_flow(self, mock_sleep, mock_get_kb, mock_get_status, mock_edit, mock_answer, mock_stop):
        """
        Test the full flow for stop server:
        1. Click 'Stop' -> Shows confirmation (doesn't stop yet)
        2. Click 'Cancel' -> Returns to main menu (doesn't stop)
        3. Click 'Stop' -> Click 'Confirm' -> Stops server
        """
        # Setup mocks
        mock_stop.return_value = "Stopped"
        mock_get_status.return_value = "Status"
        mock_get_kb.return_value = {"inline_keyboard": []}

        # 1. Test "Stop" click -> Confirmation
        stop_callback = {
            "id": "cb_1",
            "data": "stop_server",
            "message": {
                "chat": {"id": self.chat_id},
                "message_id": 100
            }
        }

        minecraft_bot.handle_callback(stop_callback)

        # Verify stop_server was NOT called
        mock_stop.assert_not_called()
        # Verify message was edited to show confirmation
        # We can check if "Are you sure" or similar is in the text argument (args[2])
        args, _ = mock_edit.call_args
        self.assertIn("Are you sure", args[2])

        # 2. Test "Cancel" click
        mock_edit.reset_mock()
        cancel_callback = {
            "id": "cb_2",
            "data": "cancel_stop",
            "message": {
                "chat": {"id": self.chat_id},
                "message_id": 100
            }
        }

        minecraft_bot.handle_callback(cancel_callback)

        # Verify stop_server was NOT called
        mock_stop.assert_not_called()
        # Verify returned to main menu
        args, _ = mock_edit.call_args
        self.assertEqual(args[2], "Status\n" + minecraft_bot.COMMANDS_HELP)

        # 3. Test "Confirm" click
        mock_edit.reset_mock()
        confirm_callback = {
            "id": "cb_3",
            "data": "confirm_stop",
            "message": {
                "chat": {"id": self.chat_id},
                "message_id": 100
            }
        }

        minecraft_bot.handle_callback(confirm_callback)

        # Verify stop_server WAS called
        mock_stop.assert_called_once()
        # Verify status update
        self.assertTrue(mock_edit.called)

if __name__ == '__main__':
    unittest.main()
