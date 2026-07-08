"""Tests for the DbConnector representing the MySQL client connection and query execution interface."""

import logging
from unittest.mock import MagicMock

import pytest
from mysql.connector import Error

from assets_guardian.core.clients.mysql_client import MySQLClient as DbConnector

# Disable logger output during testing to keep the test runner output clean
logging.getLogger("assets_guardian.core.clients.mysql_client").setLevel(logging.CRITICAL)


@pytest.fixture
def db_config():
    """Provide a mock database configuration dictionary."""
    return {
        "host": "localhost",
        "port": 3306,
        "user": "user",
        "password": "password",
        "database": "db",
    }


@pytest.fixture
def connector(db_config):
    """Provide an instance of DbConnector with a maximum of 2 connection retries."""
    return DbConnector(**db_config, max_retries=2)


def test_successful_connect(connector, mocker):
    """Verify that a successful database connection is established on the first attempt."""
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    assert connector.connect() is True
    assert mock_connect.call_count == 1


def test_retry_connect_success(connector, mocker):
    """Verify that connect retries after a failure and succeeds on the second attempt."""
    mock_sleep = mocker.patch("time.sleep")
    mock_connect = mocker.patch("mysql.connector.connect")

    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True

    # Fails the first time, succeeds on the second
    mock_connect.side_effect = [Error("Conn failed"), mock_conn]

    assert connector.connect() is True
    assert mock_connect.call_count == 2
    mock_sleep.assert_called_once_with(1)  # 2**0 backoff delay


def test_connect_all_fails(connector, mocker):
    """Verify that connect returns False when all connection attempts and retries fail."""
    mock_sleep = mocker.patch("time.sleep")
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_connect.side_effect = Error("Conn failed")

    assert connector.connect() is False
    assert mock_connect.call_count == 3  # Initial + 2 retries
    assert mock_sleep.call_count == 2


def test_execute_select_query(connector, mocker):
    """Verify execution of a SELECT query correctly maps result tuples to list of dictionaries."""
    # Mock connection
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.description = [("id",), ("name",)]
    mock_cursor.fetchall.return_value = [(1, "Alice"), (2, "Bob")]
    mock_conn.cursor.return_value = mock_cursor

    # First connect
    connector.connect()

    results = connector.execute_query("SELECT * FROM users")

    assert results == [
        {"id": 1, "name": "Alice"},
        {"id": 2, "name": "Bob"},
    ]
    mock_cursor.execute.assert_called_once()
    mock_cursor.close.assert_called_once()


def test_execute_write_query(connector, mocker):
    """Verify execution of a write query (e.g. INSERT) commits changes and returns the rowcount."""
    # Mock connection
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn.cursor.return_value = mock_cursor

    # First connect
    connector.connect()

    result = connector.execute_query("INSERT INTO users (name) VALUES ('Charlie')")

    assert result == 1
    mock_conn.commit.assert_called_once()
    mock_cursor.close.assert_called_once()


def test_execute_query_reconnects_if_needed(connector, mocker):
    """Verify that execute_query automatically reconnects if no active connection exists before executing query."""
    # Mock connection setup
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn.cursor.return_value = mock_cursor

    # Do not call connect() explicitly
    result = connector.execute_query("UPDATE users SET name='X'")

    assert result == 1
    assert mock_connect.call_count == 1


def test_execute_query_fails_if_reconnect_fails(connector, mocker):
    """Verify execute_query returns None when it tries to reconnect automatically but the reconnection fails."""
    # Mock connection to fail
    mocker.patch("mysql.connector.connect", side_effect=Error("Conn failed"))
    mocker.patch("time.sleep")

    result = connector.execute_query("SELECT 1")

    assert result is None


def test_execute_query_with_params(connector, mocker):
    """Verify that execute_query properly forwards parameterized SQL statements and values to the cursor."""
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn.cursor.return_value = mock_cursor

    params = {"id": 1, "name": "Bob"}
    result = connector.execute_query("UPDATE users SET name=%(name)s WHERE id=%(id)s", params)

    assert result == 1
    mock_cursor.execute.assert_called_once_with(
        "UPDATE users SET name=%(name)s WHERE id=%(id)s", params
    )


def test_execute_select_empty_description(connector, mocker):
    """Verify that execute_query returns an empty list if description is None for a SELECT-like query."""
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    mock_cursor = MagicMock()
    mock_cursor.description = None
    mock_conn.cursor.return_value = mock_cursor

    result = connector.execute_query("SELECT 1")

    assert result == []


def test_execute_query_error(connector, mocker):
    """Verify execute_query returns None and closes the cursor when cursor execution raises an Error."""
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    mock_cursor = MagicMock()
    mock_cursor.execute.side_effect = Error("Query failed")
    mock_conn.cursor.return_value = mock_cursor

    result = connector.execute_query("SELECT * FROM non_existent")

    assert result is None
    mock_cursor.close.assert_called_once()


def test_execute_query_reconnects_if_lost(connector, mocker):
    """Verify execute_query detects a lost connection and automatically connects to a new one before executing."""
    mock_connect = mocker.patch("mysql.connector.connect")

    # First connection (will be simulated as lost/disconnected)
    mock_conn1 = MagicMock()
    mock_conn1.is_connected.return_value = False

    # Second connection (active and returned by subsequent connect attempt)
    mock_conn2 = MagicMock()
    mock_conn2.is_connected.return_value = True
    mock_cursor = MagicMock()
    mock_cursor.rowcount = 1
    mock_conn2.cursor.return_value = mock_cursor

    mock_connect.side_effect = [mock_conn1, mock_conn2]

    # Force connection mock so is_connected gets called and evaluated to False
    connector.connect()  # Now connector is "connected" but mock_conn1.is_connected() == False

    result = connector.execute_query("UPDATE x SET y=1")

    assert result == 1
    assert mock_connect.call_count == 2


def test_close(connector, mocker):
    """Verify that close closes the active database connection if it is currently connected."""
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    connector.connect()
    connector.close()

    mock_conn.close.assert_called_once()


def test_close_already_closed(connector, mocker):
    """Verify that close does not call close on the connection if it is already disconnected."""
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = False
    mock_connect.return_value = mock_conn

    connector.connect()
    connector.close()

    assert mock_conn.close.call_count == 0


def test_close_no_connection(connector):
    """Verify that calling close when no connection has been attempted does not raise any errors."""
    # Should not raise any error
    connector.close()


def test_execute_select_no_commit(connector, mocker):
    """Verify that commit is not called for SELECT statements."""
    # Mock connection
    mock_connect = mocker.patch("mysql.connector.connect")
    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True
    mock_connect.return_value = mock_conn

    # Mock cursor
    mock_cursor = MagicMock()
    mock_cursor.description = [("id",)]
    mock_conn.cursor.return_value = mock_cursor

    connector.execute_query("SELECT 1")

    assert mock_conn.commit.call_count == 0


def test_retry_connect_success_last_attempt(connector, mocker):
    """Verify that connect succeeds when previous attempts fail but the very last retry attempt succeeds."""
    mock_sleep = mocker.patch("time.sleep")
    mock_connect = mocker.patch("mysql.connector.connect")

    mock_conn = MagicMock()
    mock_conn.is_connected.return_value = True

    # Fails 2 times, succeeds on the 3rd (last attempt since max_retries=2)
    mock_connect.side_effect = [Error("Conn failed"), Error("Conn failed"), mock_conn]

    assert connector.connect() is True
    assert mock_connect.call_count == 3
    assert mock_sleep.call_count == 2
