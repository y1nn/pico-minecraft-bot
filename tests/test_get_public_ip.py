import sys
import subprocess
from unittest.mock import MagicMock, patch

# Mock dependencies that are not installed or have side effects on import
# These must be mocked before importing the module under test
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
        # Scenario: External service returns an IP with newline
        mock_check_output.return_value = b"2.2.2.2\n"

        assert get_public_ip() == "2.2.2.2"
        mock_check_output.assert_called_once()
        # Ensure it called curl ifconfig.me with correct arguments
        args, kwargs = mock_check_output.call_args
        command = args[0]
        assert command == ["curl", "-s", "ifconfig.me"]
        assert kwargs.get("timeout") == 5

def test_get_public_ip_empty_env():
    """Test fallback when SERVER_IP is set but empty string."""
    with patch("os.getenv") as mock_getenv, \
         patch("subprocess.check_output") as mock_check_output:

        # Scenario: SERVER_IP is empty string, which is falsy
        mock_getenv.return_value = ""
        mock_check_output.return_value = b"3.3.3.3\n"

        assert get_public_ip() == "3.3.3.3"
        mock_check_output.assert_called_once()

def test_get_public_ip_timeout():
    """Test get_public_ip handles subprocess timeout."""
    with patch("os.getenv") as mock_getenv, \
         patch("subprocess.check_output") as mock_check_output:

        mock_getenv.return_value = None
        # Raise TimeoutExpired
        mock_check_output.side_effect = subprocess.TimeoutExpired(cmd=["curl"], timeout=5)

        assert get_public_ip() == "Unknown IP"

def test_get_public_ip_os_error():
    """Test get_public_ip handles OSError (e.g. curl not found)."""
    with patch("os.getenv") as mock_getenv, \
         patch("subprocess.check_output") as mock_check_output:

        mock_getenv.return_value = None
        # Raise OSError
        mock_check_output.side_effect = OSError("No such file or directory")

        assert get_public_ip() == "Unknown IP"

def test_get_public_ip_subprocess_error():
    """Test get_public_ip handles generic SubprocessError."""
    with patch("os.getenv") as mock_getenv, \
         patch("subprocess.check_output") as mock_check_output:

        mock_getenv.return_value = None
        # Raise SubprocessError
        mock_check_output.side_effect = subprocess.SubprocessError("Command failed")

        assert get_public_ip() == "Unknown IP"
