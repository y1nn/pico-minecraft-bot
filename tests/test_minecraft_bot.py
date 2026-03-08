import sys
from unittest.mock import MagicMock

# Mock dependencies that are not installed or have side effects on import
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

from scripts.minecraft_bot import (
    parse_blocked_whitelist_line,
    parse_chat_line,
    parse_death_line,
    parse_join_line,
    strip_ansi,
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


def test_parse_join_line_valid():
    line = "[10:20:30 INFO]: Steve joined the game"
    assert parse_join_line(line) == "Steve"


def test_parse_join_line_invalid():
    line = "[10:20:30 INFO]: Steve left the game"
    assert parse_join_line(line) is None


def test_parse_chat_line_valid():
    line = "[10:20:30 INFO]: <Alex> hello everyone"
    assert parse_chat_line(line) == ("Alex", "hello everyone")


def test_parse_chat_line_invalid():
    line = "[10:20:30 INFO]: Alex says hello"
    assert parse_chat_line(line) is None


def test_parse_death_line_valid():
    line = "[10:20:30 INFO]: Steve was slain by Zombie"
    assert parse_death_line(line) == "Steve was slain by Zombie"


def test_parse_death_line_invalid_chat_message():
    line = "[10:20:30 INFO]: <Steve> I died in lava"
    assert parse_death_line(line) is None


def test_parse_death_line_invalid_non_death():
    line = "[10:20:30 INFO]: Steve joined the game"
    assert parse_death_line(line) is None


def test_parse_blocked_whitelist_line_valid():
    line = "[10:20:30 INFO]: Disconnecting Notch (/1.2.3.4:12345): You are not white-listed on this server!"
    assert parse_blocked_whitelist_line(line) == "Notch"


def test_parse_blocked_whitelist_line_invalid():
    line = "[10:20:30 INFO]: Disconnecting Notch (/1.2.3.4:12345): Timed out"
    assert parse_blocked_whitelist_line(line) is None
