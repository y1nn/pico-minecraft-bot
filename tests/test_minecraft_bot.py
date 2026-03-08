import sys
from unittest.mock import MagicMock

# Mock dependencies that are not installed or have side effects on import
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

from scripts.minecraft_bot import (
    strip_ansi,
    escape_markdown,
    parse_chat_line,
    parse_join_line,
    parse_death_line,
    parse_blocked_whitelist_line,
    format_playtime_message,
    get_online_players_msg,
)

def test_strip_ansi_empty():
    assert strip_ansi("") == ""

def test_strip_ansi_no_ansi():
    text = "Hello World"
    assert strip_ansi(text) == text

def test_strip_ansi_with_color():
    text = "\x1b[31mRed Text\x1b[0m"
    assert strip_ansi(text) == "Red Text"

def test_strip_ansi_multiple_codes():
    text = "\x1b[1m\x1b[32mBold Green\x1b[0m"
    assert strip_ansi(text) == "Bold Green"

def test_strip_ansi_complex():
    text = "Normal \x1b[33mYellow\x1b[0m Mixed \x1b[44mBlueBG\x1b[0m"
    assert strip_ansi(text) == "Normal Yellow Mixed BlueBG"

def test_strip_ansi_other_escapes():
    # Test some other CSI sequences
    text = "Hello\x1b[2JWorld" # Clear screen
    assert strip_ansi(text) == "HelloWorld"

def test_parse_chat_line_valid():
    line = "[12:00:00] [Server thread/INFO]: <Steve> hello there"
    assert parse_chat_line(line) == ("Steve", "hello there")

def test_parse_chat_line_invalid():
    line = "[12:00:00] [Server thread/INFO]: Steve joined the game"
    assert parse_chat_line(line) is None

def test_parse_join_line_valid():
    line = "[12:00:01] [Server thread/INFO]: Alex joined the game"
    assert parse_join_line(line) == "Alex"

def test_parse_join_line_invalid():
    line = "[12:00:01] [Server thread/INFO]: Alex left the game"
    assert parse_join_line(line) is None

def test_parse_death_line_valid():
    line = "[12:00:02] [Server thread/INFO]: Steve was slain by Zombie"
    assert parse_death_line(line) == "Steve was slain by Zombie"

def test_parse_death_line_invalid_chat_message():
    line = "[12:00:02] [Server thread/INFO]: <Steve> I almost died"
    assert parse_death_line(line) is None

def test_parse_death_line_invalid_non_death():
    line = "[12:00:03] [Server thread/INFO]: Steve joined the game"
    assert parse_death_line(line) is None

def test_parse_blocked_whitelist_line_valid():
    line = "[12:00:04] [Server thread/INFO]: Disconnecting Herobrine (You are not white-listed on this server!)"
    assert parse_blocked_whitelist_line(line) == "Herobrine"

def test_parse_blocked_whitelist_line_invalid():
    line = "[12:00:04] [Server thread/INFO]: Disconnecting Herobrine (Timed out)"
    assert parse_blocked_whitelist_line(line) is None

def test_escape_markdown_escapes_special_characters():
    raw = r"A_*[]()`\\B"
    assert escape_markdown(raw) == r"A\_\*\[\]\(\)\`\\\\B"

def test_format_playtime_message_escapes_player_names():
    msg = format_playtime_message([("A_*[]()`,\\", 2.5)])
    assert "*A\\_\\*\\[\\]\\(\\)\\`,\\\\:*" in msg

def test_get_online_players_msg_escapes_inline_keyboard_text(monkeypatch):
    from scripts import minecraft_bot

    monkeypatch.setattr(minecraft_bot, "get_online_players_list", lambda: ["Bad_*[]()`,\\Name"])
    msg, kb = get_online_players_msg()

    assert "Online Players" in msg
    assert kb["inline_keyboard"][0][0]["text"] == r"👤 Bad\_\*\[\]\(\)\`,\\Name"
