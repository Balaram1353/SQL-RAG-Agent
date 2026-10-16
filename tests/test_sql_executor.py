
import unittest

from app.sql_executor import execute_sql, validate_sql


class TestSQLValidation(unittest.TestCase):

    def test_valid_select_is_allowed(self):
        valid, message = validate_sql(
            "SELECT name FROM customers LIMIT 3;"
        )

        self.assertTrue(valid, message)

    def test_read_only_cte_is_allowed(self):
        sql = """
        WITH customer_names AS (
            SELECT name FROM customers
        )
        SELECT name FROM customer_names LIMIT 3;
        """

        valid, message = validate_sql(sql)

        self.assertTrue(valid, message)

    def test_delete_is_rejected(self):
        valid, message = validate_sql(
            "DELETE FROM customers;"
        )

        self.assertFalse(valid)
        self.assertIn("SELECT", message)

    def test_multiple_statements_are_rejected(self):
        sql = (
            "SELECT name FROM customers; "
            "SELECT name FROM products;"
        )

        valid, message = validate_sql(sql)

        self.assertFalse(valid)
        self.assertIn("one SQL statement", message)

    def test_pragma_is_rejected(self):
        valid, message = validate_sql(
            "PRAGMA table_info(customers);"
        )

        self.assertFalse(valid)

    def test_empty_query_is_rejected(self):
        valid, message = validate_sql("   ")

        self.assertFalse(valid)

    def test_oversized_query_is_rejected(self):
        valid, message = validate_sql(
            "SELECT '" + ("x" * 10_000) + "';"
        )

        self.assertFalse(valid)


class TestSQLExecution(unittest.TestCase):

    def test_select_returns_results(self):
        result = execute_sql(
            "SELECT name FROM customers LIMIT 3;"
        )

        self.assertTrue(
            result["success"],
            result.get("error", ""),
        )
        self.assertEqual(len(result["rows"]), 3)
        self.assertIn("name", result["columns"])

    def test_nonexistent_table_returns_error(self):
        result = execute_sql(
            "SELECT * FROM nonexistent_table;"
        )

        self.assertFalse(result["success"])
        self.assertIn("no such table", result["error"])

    def test_delete_never_executes(self):
        result = execute_sql("DELETE FROM customers;")

        self.assertFalse(result["success"])


if __name__ == "__main__":
    unittest.main()
