# Copyright (c) 2025 Mimer Information Technology

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.
#
# See license for more details.

import pytest
from unittest.mock import MagicMock, patch
from mimerpy.pool import MimerPoolError

from mimer_mcp_server.database import connection
from mimer_mcp_server import config


@pytest.fixture(autouse=True)
def reset_pool():
    """Reset the global pool variable before and after each test."""
    connection.pool = None
    yield
    connection.pool = None


@pytest.fixture
def mock_config_vars(monkeypatch):
    """Set up required config variables for database connection."""
    # monkeypatch.setattr(config, "DB_DSN", "test_dsn")
    # monkeypatch.setattr(config, "DB_USER", "test_user")
    # monkeypatch.setattr(config, "DB_PASSWORD", "test_password")
    # # Reset optional configs
    # monkeypatch.setattr(config, "DB_POOL_INITIAL_CON", None)
    # monkeypatch.setattr(config, "DB_POOL_MAX_UNUSED", None)
    # monkeypatch.setattr(config, "DB_POOL_MAX_CON", None)
    # monkeypatch.setattr(config, "DB_POOL_BLOCK", None)
    # monkeypatch.setattr(config, "DB_POOL_DEEP_HEALTH_CHECK", None)
    monkeypatch.setattr(
        connection,
        "DB_CONFIG",
        {
            "dsn": "test_dsn", 
            "user": "test_user", 
            "password": "test_password",
            "initialconnections": None,
            "maxunused": None,
            "maxconnections": None,
            "block": None,
            "deep_health_check": None,
         },
    )


@pytest.fixture
def mock_mimer_pool():
    """Create a mock MimerPool instance."""
    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Configure the mock chain
    mock_cursor.fetchone.return_value = ["test_user"]
    mock_conn.cursor.return_value = mock_cursor
    mock_pool.get_connection.return_value.__enter__.return_value = mock_conn

    return mock_pool


# --- Tests for init_db_pool() ---


def test_init_db_pool_success(mock_config_vars, mock_mimer_pool):
    """Test successful pool initialization."""
    with patch(
        "mimer_mcp_server.database.connection.MimerPool", return_value=mock_mimer_pool
    ):
        pool = connection.init_db_pool()

        assert pool is not None
        assert connection.pool == pool
        mock_mimer_pool.get_connection.assert_called_once()


def test_init_db_pool_missing_dsn(monkeypatch):
    """Test pool initialization fails when DB_DSN is missing."""
    monkeypatch.setattr(config, "DB_DSN", None)
    monkeypatch.setattr(config, "DB_USER", "test_user")
    monkeypatch.setattr(config, "DB_PASSWORD", "test_password")

    with pytest.raises(ValueError, match="Missing DB_DSN"):
        connection.init_db_pool()


def test_init_db_pool_missing_user(monkeypatch):
    """Test pool initialization fails when DB_USER is missing."""
    monkeypatch.setattr(config, "DB_DSN", "test_dsn")
    monkeypatch.setattr(config, "DB_USER", None)
    monkeypatch.setattr(config, "DB_PASSWORD", "test_password")

    with pytest.raises(ValueError, match="Missing DB_USER"):
        connection.init_db_pool()


def test_init_db_pool_missing_password(monkeypatch, mock_mimer_pool):
    """Test pool initialization fails when DB_PASSWORD is missing."""
    monkeypatch.setattr(config, "DB_DSN", "test_dsn")
    monkeypatch.setattr(config, "DB_USER", "test_user")
    monkeypatch.setattr(config, "DB_PASSWORD", None)

    with pytest.raises(ValueError, match="Missing DB_PASSWORD"):
        connection.init_db_pool()


def test_init_db_pool_with_custom_config(mock_config_vars, monkeypatch):
    """Test pool initialization with custom pool configuration."""
    monkeypatch.setattr(config, "DB_POOL_INITIAL_CON", "5")
    monkeypatch.setattr(config, "DB_POOL_MAX_UNUSED", "10")
    monkeypatch.setattr(config, "DB_POOL_MAX_CON", "20")
    monkeypatch.setattr(config, "DB_POOL_BLOCK", "false")
    monkeypatch.setattr(config, "DB_POOL_DEEP_HEALTH_CHECK", "yes")

    mock_pool = MagicMock()
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_cursor.fetchone.return_value = ["test_user"]
    mock_conn.cursor.return_value = mock_cursor
    mock_pool.get_connection.return_value.__enter__.return_value = mock_conn

    with patch("mimer_mcp_server.database.connection.MimerPool") as MockPool:
        MockPool.return_value = mock_pool
        connection.init_db_pool()

        # Verify MimerPool was called with correct parameters
        MockPool.assert_called_once()
        call_kwargs = MockPool.call_args.kwargs

        assert call_kwargs["dsn"] == "test_dsn"
        assert call_kwargs["user"] == "test_user"
        assert call_kwargs["password"] == "test_password"
        assert call_kwargs["initialconnections"] == 5
        assert call_kwargs["maxunused"] == 10
        assert call_kwargs["maxconnections"] == 20
        assert call_kwargs["block"] is False
        assert call_kwargs["deep_health_check"] is True


def test_init_db_pool_creation_error(mock_config_vars):
    """Test pool initialization handles MimerPoolError."""
    with patch(
        "mimer_mcp_server.database.connection.MimerPool",
        side_effect=MimerPoolError("Connection failed"),
    ):
        with pytest.raises(MimerPoolError, match="Connection failed"):
            connection.init_db_pool()


# --- Tests for get_connection() ---


def test_get_connection_success(mock_config_vars, mock_mimer_pool):
    """Test getting a connection from initialized pool."""
    with patch(
        "mimer_mcp_server.database.connection.MimerPool", return_value=mock_mimer_pool
    ):
        connection.init_db_pool()
        conn = connection.get_connection()

        assert conn is not None
        mock_mimer_pool.get_connection.assert_called()


def test_get_connection_pool_not_initialized():
    """Test get_connection raises error when pool is not initialized."""
    connection.pool = None

    with pytest.raises(
        RuntimeError, match="Database connection pool is not initialized"
    ):
        connection.get_connection()


def test_get_connection_multiple_calls(mock_config_vars, mock_mimer_pool):
    """Test that multiple get_connection calls use the same pool."""
    with patch(
        "mimer_mcp_server.database.connection.MimerPool", return_value=mock_mimer_pool
    ):
        connection.init_db_pool()

        conn1 = connection.get_connection()
        conn2 = connection.get_connection()

        assert (
            mock_mimer_pool.get_connection.call_count == 3
        )  # 1 in init + 2 explicit calls


# --- Tests for close_db_pool() ---


def test_close_db_pool_success(mock_config_vars, mock_mimer_pool):
    """Test successful pool closure."""
    with patch(
        "mimer_mcp_server.database.connection.MimerPool", return_value=mock_mimer_pool
    ):
        connection.init_db_pool()
        connection.close_db_pool()

        mock_mimer_pool.close.assert_called_once()
        assert connection.pool is None


def test_close_db_pool_when_not_initialized():
    """Test closing pool when it's not initialized (should not raise error)."""
    connection.pool = None
    connection.close_db_pool()  # Should not raise
    assert connection.pool is None


def test_close_db_pool_handles_errors(mock_config_vars, mock_mimer_pool):
    """Test that close_db_pool handles errors gracefully."""
    mock_mimer_pool.close.side_effect = Exception("Close failed")

    with patch(
        "mimer_mcp_server.database.connection.MimerPool", return_value=mock_mimer_pool
    ):
        connection.init_db_pool()

        # Should not raise, just log the error
        connection.close_db_pool()

        mock_mimer_pool.close.assert_called_once()
        assert connection.pool is None


# --- Integration tests ---


def test_pool_lifecycle(mock_config_vars, mock_mimer_pool):
    """Test complete pool lifecycle: init -> use -> close."""
    with patch(
        "mimer_mcp_server.database.connection.MimerPool", return_value=mock_mimer_pool
    ):
        # Initialize
        pool = connection.init_db_pool()
        assert pool is not None

        # Use
        conn = connection.get_connection()
        assert conn is not None

        # Close
        connection.close_db_pool()
        assert connection.pool is None

        # Verify cannot use after close
        with pytest.raises(RuntimeError):
            connection.get_connection()


def test_pool_reinitialization(mock_config_vars, mock_mimer_pool):
    """Test that pool can be reinitialized after closing."""
    with patch(
        "mimer_mcp_server.database.connection.MimerPool", return_value=mock_mimer_pool
    ):
        # First initialization
        connection.init_db_pool()
        connection.close_db_pool()

        # Reinitialize
        pool = connection.init_db_pool()
        assert pool is not None
        assert connection.pool == pool
