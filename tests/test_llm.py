import unittest
from unittest.mock import patch

from app.llm import generate_sql, explain_results


class TestGenerateSQL(unittest.TestCase):

    @patch("app.llm.urlopen")
    def test_generate_sql_returns_model_response(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = (
            b'{"message": {"content": "SELECT name FROM customers;"}}'
        )

        sql = generate_sql(
            "Show customer names",
            "Table: customers\nColumns: customer_id, name",
        )

        self.assertEqual(sql, "SELECT name FROM customers;")
        mock_urlopen.assert_called_once()

    @patch("app.llm.urlopen")
    def test_generate_sql_sends_question_and_schema(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = (
            b'{"message": {"content": "SELECT name FROM customers;"}}'
        )

        generate_sql(
            "Show customer names",
            "Table: customers\nColumns: customer_id, name",
        )

        request = mock_urlopen.call_args.args[0]
        self.assertIn("/api/chat", request.full_url)

        import json
        payload = json.loads(request.data.decode("utf-8"))

        messages = payload["messages"]
        combined_prompt = " ".join(
            message["content"] for message in messages
        )

        self.assertIn("Show customer names", combined_prompt)
        self.assertIn("customers", combined_prompt)
        self.assertEqual(payload["model"], "qwen2.5:7b-instruct")


class TestExplainResults(unittest.TestCase):

    @patch("app.llm.urlopen")
    def test_explanation_returns_model_response(self, mock_urlopen):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = (
            b'{"message": {"content": "Carlos spent the most."}}'
        )

        result = {
            "success": True,
            "columns": ["name", "total_spent"],
            "rows": [{"name": "Carlos Garcia", "total_spent": 2000.0}],
        }

        answer = explain_results(
            "Which customer spent the most money?",
            "SELECT name, SUM(price) FROM purchases",
            result,
        )

        self.assertEqual(answer, "Carlos spent the most.")

    @patch("app.llm.urlopen")
    def test_explanation_prompt_contains_actual_results(
        self, mock_urlopen
    ):
        mock_response = mock_urlopen.return_value.__enter__.return_value
        mock_response.read.return_value = (
            b'{"message": {"content": "Carlos spent the most."}}'
        )

        result = {
            "success": True,
            "rows": [{"name": "Carlos Garcia", "total_spent": 2000.0}],
        }

        explain_results(
            "Which customer spent the most money?",
            "SELECT name FROM customers",
            result,
        )

        request = mock_urlopen.call_args.args[0]

        import json
        payload = json.loads(request.data.decode("utf-8"))

        combined_prompt = " ".join(
            message["content"] for message in payload["messages"]
        )

        self.assertIn("Carlos Garcia", combined_prompt)
        self.assertIn("2000.0", combined_prompt)
        self.assertIn("Which customer spent the most money?", combined_prompt)


if __name__ == "__main__":
    unittest.main()