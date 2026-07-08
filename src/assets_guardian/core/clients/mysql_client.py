import logging
import time
from typing import TYPE_CHECKING, Any

import mysql.connector
from mysql.connector import Error

if TYPE_CHECKING:
    from mysql.connector.abstracts import MySQLConnectionAbstract
    from mysql.connector.pooling import PooledMySQLConnection

logger = logging.getLogger(__name__)


class MySQLClient:
    """MySQL database connector with resilience management.

    This class wraps `mysql-connector-python` to provide a robust interface
    for interacting with a MySQL database. It includes automatic reconnection
    logic with exponential backoff to handle network instability.

    Attributes:
        host (str): The host of the MySQL server.
        port (int): The connection port (default: 3306).
        user (str): The username for the client connection.
        password (str): The password associated with the user.
        database (str): The target database name.
        max_retries (int): Maximum number of connection attempts before giving up.
    """

    host: str
    port: int
    user: str
    password: str
    database: str
    max_retries: int

    def __init__(
        self,
        host: str,
        port: int,
        user: str,
        password: str,
        database: str,
        max_retries: int = 5,
    ) -> None:
        """Initializes the connector settings.

        Args:
            host: MySQL server address.
            port: Server port.
            user: Connection username.
            password: Connection password.
            database: Target database name.
            max_retries: Number of retry attempts for the connection.
        """
        self.__config = {
            "host": host,
            "port": port,
            "user": user,
            "password": password,
            "database": database,
        }
        self.__connection: PooledMySQLConnection | MySQLConnectionAbstract | None = None
        self.__max_retries = max_retries

    def connect(self) -> bool:
        """Establishes a connection to the MySQL server with a retry strategy.

        Attempts to connect to the server using exponential backoff
        (2^attempt seconds) between each failure.

        Returns:
            bool: True if connection succeeded, False after exhausting attempts.
        """
        for attempt in range(self.__max_retries + 1):
            try:
                self.__connection = mysql.connector.connect(**self.__config)
                if self.__connection and self.__connection.is_connected():
                    logger.info(
                        "MySQL connection opened for host %s with user %s",
                        self.__config["host"],
                        self.__config["user"],
                    )
                    return True
            except Error as e:
                if attempt < self.__max_retries:
                    wait_time = 2**attempt
                    logger.warning(
                        "Connection attempt %d failed: %s. Retrying in %ds",
                        attempt + 1,
                        e,
                        wait_time,
                    )
                    time.sleep(wait_time)
                else:
                    logger.exception(
                        "Failed to connect to MySQL database after %d retries: %s",
                        self.__max_retries,
                    )

        return False

    def __fetch_results(self, cursor: Any) -> list[dict[str, Any]]:
        """Extracts results from a cursor as a list of dictionaries.

        Each dictionary represents a row, with keys representing column names.

        Args:
            cursor: The MySQL cursor after query execution.

        Returns:
            list[dict[str, Any]]: List of rows (dictionaries). Empty if no results.
        """
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            return [dict(zip(columns, row, strict=False)) for row in cursor.fetchall()]
        return []

    def __ensure_connected(self) -> bool:
        """Verifies connection state and reconnects if necessary.

        Returns:
            bool: True if connection is active or was re-established, False otherwise.
        """
        if self.__connection is not None and self.__connection.is_connected():
            return True
        logger.error("No active connection. Attempting to reconnect.")
        return self.connect()

    def execute_query(
        self, query: str, params: dict[str, Any] | None = None
    ) -> list[dict[str, Any]] | int | None:
        """Executes a SQL query (read or write).

        If the query starts with "SELECT", returns the results as a list.
        Otherwise (INSERT, UPDATE, DELETE), commits the transaction and returns
        the number of affected rows.

        Args:
            query: The SQL query string.
            params: Dictionary of parameters for the query (optional).

        Returns:
            - List of dictionaries for SELECT queries.
            - Integer representing affected rows for write queries.
            - None if connection or SQL error occurs.
        """
        if not self.__ensure_connected() or self.__connection is None:
            return None

        cursor = self.__connection.cursor()
        try:
            cursor.execute(query, params or {})
            if query.strip().upper().startswith("SELECT"):
                logger.debug("Executing SELECT query: %s", query)
                return self.__fetch_results(cursor)
            logger.debug("Executing write query: %s", query)
            self.__connection.commit()
            return int(cursor.rowcount)
        except Error:
            logger.exception("Error executing query: %s")
            return None
        finally:
            cursor.close()

    def close(self) -> None:
        """Properly closes the active MySQL connection.

        Resets the internal connection attribute after closure.
        """
        if self.__connection is not None and self.__connection.is_connected():
            self.__connection.close()
            logger.info(
                "MySQL connection closed for host %s with user %s",
                self.__config["host"],
                self.__config["user"],
            )
            self.__connection = None
