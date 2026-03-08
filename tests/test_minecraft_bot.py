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
    parse_allowed_chat_ids,
    parse_int_env,
    update_property,
    read_property,
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

def test_parse_allowed_chat_ids_ignores_invalid_values():
    raw = "123, abc, , -100456, 42x, 7"
    assert parse_allowed_chat_ids(raw) == [123, -100456, 7]


def test_parse_int_env_returns_default_on_invalid(monkeypatch):
    monkeypatch.setenv("OWNER_ID", "not-a-number")
    assert parse_int_env("OWNER_ID", default=99) == 99


def test_update_property_appends_missing_key(tmp_path, monkeypatch):
    props = tmp_path / "server.properties"
    props.write_text("motd=hello\n")

    monkeypatch.setattr("scripts.minecraft_bot.PROPERTIES_FILE", str(props))

    update_property("view-distance", "10")

    assert props.read_text() == "motd=hello\nview-distance=10\n"


def test_read_property_preserves_text_after_equals(tmp_path, monkeypatch):
    props = tmp_path / "server.properties"
    props.write_text("motd=hello=world\n")

    monkeypatch.setattr("scripts.minecraft_bot.PROPERTIES_FILE", str(props))

    assert read_property("motd") == "hello=world"


def test_handle_text_broadcast_confirmation_escapes_markdown(monkeypatch):
    from scripts import minecraft_bot as bot

    sent = []

    def fake_send_message(chat_id, text, reply_markup=None):
        sent.append((chat_id, text, reply_markup))

    monkeypatch.setattr(bot, "ALLOWED_CHAT_IDS", [123])
    monkeypatch.setattr(bot, "send_message", fake_send_message)
    monkeypatch.setattr(bot, "rcon_command", lambda *_args, **_kwargs: "ok")

    bot.pending_broadcast.clear()
    bot.pending_broadcast[123] = True

    bot.handle_text({"chat": {"id": 123}, "text": "A_*[]()`", "from": {"first_name": "Admin"}})

    assert sent
    assert sent[0][0] == 123
    assert sent[0][1] == f"✅ *Broadcast Sent:*\n{bot.escape_markdown('A_*[]()`')}"
    assert bot.pending_broadcast[123] is False
