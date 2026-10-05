"""ClickHouse database client and query validator."""

from __future__ import annotations

import logging
import re
from typing import Any, Dict, List, Optional, Tuple

import clickhouse_connect
import pandas as pd
import sqlparse

from src.config import settings

logger = logging.getLogger(__name__)

# Dangerous SQL keywords that should never be executed
DANGEROUS_KEYWORDS = {
    "DROP",
    "TRUNCATE",
    "ALTER",
    "DELETE",
    "UPDATE",
    "INSERT",
    "CREATE",
    "RENAME",
    "GRANT",
    "REVOKE",
    "SYSTEM",
    "KILL",
    "OPTIMIZE",
    "ATTACH",
    "DETACH",
}


class SqlValidationError(Exception):
    """Raised when a SQL query violates safety constraints."""

    pass


class ClickHouseClient:
    """Client for ClickHouse connection and safe query execution."""

    def __init__(
        self,
        host: Optional[str] = None,
        port: Optional[int] = None,
        username: Optional[str] = None,
        password: Optional[str] = None,
        database: Optional[str] = None,
    ):
        self.host = host or settings.clickhouse_host
        self.port = port or settings.clickhouse_http_port
        self.username = username or settings.clickhouse_user
        self.password = password or settings.clickhouse_password
        self.database = database or settings.clickhouse_db

    def get_connection(self):
        """Create and return a clickhouse-connect client."""
        return clickhouse_connect.get_client(
            host=self.host,
            port=self.port,
            username=self.username,
            password=self.password,
            database=self.database,
        )

    def ping(self) -> bool:
        """Check if ClickHouse is accessible."""
        try:
            client = self.get_connection()
            result = client.command("SELECT 1")
            client.close()
            return result == 1
        except Exception as e:
            logger.warning(f"ClickHouse ping failed: {e}")
            return False

    def get_table_names(self) -> List[str]:
        """Get list of tables in the database."""
        client = self.get_connection()
        try:
            result = client.query("SHOW TABLES")
            return [row[0] for row in result.result_rows]
        finally:
            client.close()

    def get_table_schemas(self) -> Dict[str, str]:
        """Fetch CREATE TABLE statements for all tables in the database."""
        client = self.get_connection()
        schemas: Dict[str, str] = {}
        try:
            tables = self.get_table_names()
            for table in tables:
                try:
                    res = client.command(f"SHOW CREATE TABLE `{self.database}`.`{table}`")
                    if isinstance(res, str):
                        schemas[table] = res.strip()
                except Exception as e:
                    logger.warning(f"Failed to fetch DDL for table {table}: {e}")
            return schemas
        finally:
            client.close()

    @staticmethod
    def validate_safe_sql(sql: str) -> Tuple[bool, str]:
        """Validate that a SQL statement is safe for execution (SELECT only).

        Args:
            sql: The raw SQL string to validate.

        Returns:
            Tuple of (is_valid, error_message).
        """
        if not sql or not sql.strip():
            return False, "SQL statement is empty"

        # Remove trailing semicolon and comments for clean analysis
        cleaned_sql = sql.strip().rstrip(";")
        parsed = sqlparse.parse(cleaned_sql)

        if not parsed:
            return False, "Failed to parse SQL statement"

        if len(parsed) > 1:
            return False, "Multiple statements are not permitted"

        stmt = parsed[0]
        tokens = [t for t in stmt.tokens if not t.is_whitespace]
        if not tokens:
            return False, "No tokens found in SQL statement"

        first_token = tokens[0]
        first_token_val = first_token.value.upper()

        # Allow SELECT or WITH (for CTEs)
        if first_token_val not in ("SELECT", "WITH"):
            return False, f"Only SELECT or WITH queries are permitted (got: {first_token_val})"

        # Check for dangerous keywords in all tokens
        for token in stmt.flatten():
            token_val = token.value.upper()
            if token_val in DANGEROUS_KEYWORDS:
                return False, f"Disallowed keyword detected: {token_val}"

        return True, ""

    def run_query(self, sql: str) -> pd.DataFrame:
        """Validate and execute a SQL query on ClickHouse.

        Args:
            sql: SQL statement to execute.

        Returns:
            pandas DataFrame containing the result rows.

        Raises:
            SqlValidationError: If query does not pass security validation.
            Exception: If execution on ClickHouse fails.
        """
        is_valid, error_msg = self.validate_safe_sql(sql)
        if not is_valid:
            raise SqlValidationError(f"Invalid SQL: {error_msg}")

        client = self.get_connection()
        try:
            result = client.query(sql)
            df = pd.DataFrame(result.result_rows, columns=result.column_names)
            return df
        finally:
            client.close()
