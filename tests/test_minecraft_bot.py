import sys
from unittest.mock import MagicMock

# Mock dependencies that are not installed or have side effects on import
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

from scripts.minecraft_bot import strip_ansi

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


class _FakeStdout:
    def __init__(self, lines):
        self._lines = iter(lines)

    def readline(self):
        return next(self._lines)


class _FakeProcess:
    def __init__(self, lines):
        self.stdout = _FakeStdout(lines)


def test_monitor_logs_chat_not_relayed_when_chat_mode_disabled(monkeypatch):
    from scripts import minecraft_bot

    chat_line = "[12:00:00] [Server thread/INFO]: <Steve> Hello\n"
    fake_process = _FakeProcess([chat_line, ""])

    broadcast_calls = []

    def fake_broadcast(message, reply_markup=None):
        broadcast_calls.append((message, reply_markup))

    check_output_calls = iter([b"true\n"])

    def fake_check_output(*args, **kwargs):
        try:
            return next(check_output_calls)
        except StopIteration:
            raise KeyboardInterrupt()

    monkeypatch.setattr(minecraft_bot, "chat_mode_enabled", False)
    monkeypatch.setattr(minecraft_bot.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(minecraft_bot.subprocess, "Popen", lambda *a, **k: fake_process)
    monkeypatch.setattr(minecraft_bot, "broadcast_message", fake_broadcast)

    try:
        minecraft_bot.monitor_logs()
    except KeyboardInterrupt:
        pass

    assert broadcast_calls == []


def test_monitor_logs_chat_relayed_once_when_chat_mode_enabled(monkeypatch):
    from scripts import minecraft_bot

    chat_line = "[12:00:00] [Server thread/INFO]: <Steve> Hello\n"
    fake_process = _FakeProcess([chat_line, ""])

    broadcast_calls = []

    def fake_broadcast(message, reply_markup=None):
        broadcast_calls.append((message, reply_markup))

    check_output_calls = iter([b"true\n"])

    def fake_check_output(*args, **kwargs):
        try:
            return next(check_output_calls)
        except StopIteration:
            raise KeyboardInterrupt()

    monkeypatch.setattr(minecraft_bot, "chat_mode_enabled", True)
    monkeypatch.setattr(minecraft_bot.subprocess, "check_output", fake_check_output)
    monkeypatch.setattr(minecraft_bot.subprocess, "Popen", lambda *a, **k: fake_process)
    monkeypatch.setattr(minecraft_bot, "broadcast_message", fake_broadcast)

    try:
        minecraft_bot.monitor_logs()
    except KeyboardInterrupt:
        pass

    assert broadcast_calls == [("💬 *Steve:* Hello", None)]
