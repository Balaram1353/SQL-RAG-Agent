import unittest
from unittest.mock import patch

from app.agent import answer_question


class TestAgent(unittest.TestCase):

    @patch("app.agent.explain_results")
    @patch("app.agent.execute_sql")
    @patch("app.agent.generate_sql")
    @patch("app.agent.search")
    @patch("app.agent.build_index")
    def test_agent_stops_after_two_failed_attempts(
        self,
        mock_build_index,
        mock_search,
        mock_generate_sql,
        mock_execute_sql,
        mock_explain_results,
    ):
        mock_build_index.return_value = []
        mock_search.return_value = [
            {"text": "products(product_id, name, price)"}
        ]

        mock_generate_sql.side_effect = [
            "SELECT missing_column FROM products",
            "SELECT another_missing_column FROM products",
        ]

        mock_execute_sql.side_effect = [
            {"success": False, "error": "no such column: missing_column"},
            {"success": False, "error": "no such column: another_missing_column"},
        ]

        response = answer_question("Which products are available?")

        self.assertEqual(response["attempts"], 2)
        self.assertIn("error", response)
        self.assertEqual(mock_generate_sql.call_count, 2)
        self.assertEqual(mock_execute_sql.call_count, 2)
        mock_explain_results.assert_not_called()

    @patch("app.agent.explain_results")
    @patch("app.agent.execute_sql")
    @patch("app.agent.generate_sql")
    @patch("app.agent.search")
    @patch("app.agent.build_index")
    def test_agent_repairs_failed_sql(
        self,
        mock_build_index,
        mock_search,
        mock_generate_sql,
        mock_execute_sql,
        mock_explain_results,
    ):
        mock_build_index.return_value = []
        mock_search.return_value = [
            {"text": "products(product_id, name, price)"}
        ]

        mock_generate_sql.side_effect = [
            "SELECT nonexistent_column FROM products",
            "SELECT name FROM products",
        ]

        mock_execute_sql.side_effect = [
            {"success": False, "error": "no such column: nonexistent_column"},
            {
                "success": True,
                "columns": ["name"],
                "rows": [{"name": "Laptop"}],
                "row_count_returned": 1,
                "truncated_possible": False,
            },
        ]

        mock_explain_results.return_value = (
            "The query returned Laptop."
        )

        response = answer_question("Which products are available?")

        self.assertEqual(response["attempts"], 2)
        self.assertEqual(
            response["sql"], "SELECT name FROM products"
        )
        self.assertEqual(
            response["results"], [{"name": "Laptop"}]
        )
        self.assertEqual(mock_generate_sql.call_count, 2)
        self.assertEqual(mock_execute_sql.call_count, 2)
        mock_explain_results.assert_called_once()


if __name__ == "__main__":
    unittest.main()