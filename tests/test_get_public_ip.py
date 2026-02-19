import sys
import subprocess
from unittest.mock import MagicMock, patch

# Mock dependencies that are not installed or have side effects on import
sys.modules["requests"] = MagicMock()
sys.modules["dotenv"] = MagicMock()

# Now import the function to test
from scripts.minecraft_bot import get_public_ip

def test_get_public_ip_from_env():
    """Test get_public_ip when SERVER_IP environment variable is set."""
    with patch("os.getenv") as mock_getenv:
        mock_getenv.return_value = "1.1.1.1"
        assert get_public_ip() == "1.1.1.1"
        mock_getenv.assert_called_with("SERVER_IP")

def test_get_public_ip_from_service():
    """Test get_public_ip fallback to external service when environment variable is not set."""
    with patch("os.getenv") as mock_getenv, \
         patch("subprocess.check_output") as mock_check_output:

        # Scenario: SERVER_IP is not set
        mock_getenv.return_value = None
        # Scenario: External service returns an IP
        mock_check_output.return_value = b"2.2.2.2\n"

        assert get_public_ip() == "2.2.2.2"
        mock_check_output.assert_called_once()
        # Ensure it called curl ifconfig.me
        args, _ = mock_check_output.call_args
        command = args[0]
        assert "curl" in command
        assert "ifconfig.me" in command

def test_get_public_ip_failure():
    """Test get_public_ip failure when both environment variable is unset and service call fails."""
    with patch("os.getenv") as mock_getenv, \
         patch("subprocess.check_output") as mock_check_output:

        # Scenario: SERVER_IP is not set
        mock_getenv.return_value = None
        # Scenario: External service call fails
        mock_check_output.side_effect = subprocess.SubprocessError("Command failed")

        assert get_public_ip() == "Unknown IP"
