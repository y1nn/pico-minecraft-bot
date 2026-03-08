import sys
import subprocess
from unittest.mock import MagicMock

import pytest

# Mock dependencies that are not installed or have side effects on import
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

from scripts import minecraft_bot as bot


def test_monitor_logs_uses_configured_compose_file(monkeypatch):
    fake_process = MagicMock()
    fake_process.stdout.readline.side_effect = [""]

    popen_mock = MagicMock(side_effect=[fake_process, KeyboardInterrupt()])

    monkeypatch.setattr(bot, "COMPOSE_FILE", "/tmp/custom-compose.yml")
    monkeypatch.setattr(subprocess, "check_output", MagicMock(return_value=b"true"))
    monkeypatch.setattr(subprocess, "Popen", popen_mock)

    with pytest.raises(KeyboardInterrupt):
        bot.monitor_logs()

    popen_args = popen_mock.call_args_list[0][0][0]
    assert popen_args == [
        "docker",
        "compose",
        "-f",
        "/tmp/custom-compose.yml",
        "logs",
        "-f",
        "--tail=0",
        bot.CONTAINER_NAME,
    ]
