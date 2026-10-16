
import sqlite3
import time

import sqlglot
from sqlglot import exp

from app.database import DATABASE_PATH


DB_PATH = DATABASE_PATH

MAX_ROWS = 100
QUERY_TIMEOUT_SECONDS = 5
MAX_SQL_LENGTH = 10_000
PROGRESS_CHECK_INTERVAL = 1_000


def validate_sql(sql: str) -> tuple[bool, str]:
    """Validate that SQL contains exactly one read-only query."""

    if not isinstance(sql, str) or not sql.strip():
        return False, "SQL query is empty."

    if len(sql) > MAX_SQL_LENGTH:
        return False, "SQL query exceeds the maximum allowed length."

    try:
        statements = sqlglot.parse(sql, read="sqlite")
    except sqlglot.errors.ParseError as error:
        return False, f"SQL syntax error: {error}"

    # Reject multiple statements and empty input.
    if len(statements) != 1 or statements[0] is None:
        return False, "Exactly one SQL statement is allowed."

    tree = statements[0]

    # Allow SELECT statements and SELECT-based CTEs only.
    if not isinstance(
        tree,
        (exp.Select, exp.Union, exp.Intersect, exp.Except),
    ):
        return False, "Only SELECT queries are allowed."

    # Reject database-modifying and command expressions.
    forbidden = (
        exp.Insert,
        exp.Update,
        exp.Delete,
        exp.Create,
        exp.Drop,
        exp.Alter,
        exp.Command,
    )

    for node in tree.walk():
        if isinstance(node, forbidden):
            return (
                False,
                f"Forbidden SQL operation: {type(node).__name__}.",
            )

    return True, "SQL validation passed."


def execute_sql(sql: str) -> dict:
    """Validate and execute a read-only SQL query with a time limit."""

    is_valid, validation_message = validate_sql(sql)

    if not is_valid:
        return {
            "success": False,
            "error": validation_message,
        }

    if not DB_PATH.exists():
        return {
            "success": False,
            "error": f"Database not found: {DB_PATH}",
        }

    try:
        # Open the configured SQLite database in read-only mode.
        database_uri = DB_PATH.resolve().as_uri() + "?mode=ro"

        with sqlite3.connect(
            database_uri,
            uri=True,
            timeout=QUERY_TIMEOUT_SECONDS,
        ) as connection:
            connection.row_factory = sqlite3.Row

            # SQLite calls this handler periodically while executing
            # virtual-machine instructions. Return 1 only when the
            # elapsed time exceeds the configured query limit.
            query_start = time.monotonic()

            def should_interrupt() -> int:
                elapsed = time.monotonic() - query_start
                return int(elapsed > QUERY_TIMEOUT_SECONDS)

            connection.set_progress_handler(
                should_interrupt,
                PROGRESS_CHECK_INTERVAL,
            )

            cursor = connection.execute(sql)

            columns = [
                column[0]
                for column in (cursor.description or [])
            ]

            rows = [
                dict(row)
                for row in cursor.fetchmany(MAX_ROWS)
            ]

            return {
                "success": True,
                "columns": columns,
                "rows": rows,
                "row_count_returned": len(rows),
                "truncated_possible": len(rows) == MAX_ROWS,
            }

    except sqlite3.Error as error:
        error_message = str(error)

        if "interrupted" in error_message.lower():
            error_message = (
                f"Query exceeded the {QUERY_TIMEOUT_SECONDS}-second "
                "execution time limit."
            )

        return {
            "success": False,
            "error": error_message,
        }


if __name__ == "__main__":
    test_queries = [
        "SELECT name FROM customers LIMIT 3;",
        "DELETE FROM customers;",
        "SELECT name FROM customers; SELECT name FROM products;",
        "SELECT * FROM nonexistent_table;",
    ]

    for query in test_queries:
        print(f"\nQuery: {query}")
        print(execute_sql(query))
