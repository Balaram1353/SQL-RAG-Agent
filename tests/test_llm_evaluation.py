import unittest

from app.agent import answer_question


class TestLLMEvaluation(unittest.TestCase):
    """Evaluate the agent against known answers from the sample database."""

    def test_customer_spending(self):
        response = answer_question(
            "Which customer spent the most money? "
            "Calculate spending using product price and quantity."
        )

        self.assertNotIn(
            "error",
            response,
            f"Agent failed to answer the question: {response}",
        )

        self.assertTrue(
            response["results"],
            f"Expected at least one result. Response: {response}",
        )

        self.assertEqual(
            response["results"][0]["name"],
            "Carlos Garcia",
            f"Unexpected customer. Response: {response}",
        )

    def test_highest_revenue_product(self):
        response = answer_question(
            "Which product generated the highest revenue? "
            "Calculate revenue as selling price multiplied by quantity."
        )

        self.assertNotIn(
            "error",
            response,
            f"Agent failed to answer the question: {response}",
        )

        self.assertTrue(
            response["results"],
            f"Expected at least one result. Response: {response}",
        )

        self.assertEqual(
            response["results"][0]["name"],
            "Laptop",
            f"Expected Laptop to have the highest revenue. "
            f"Response: {response}",
        )

        revenue_column = next(
            (
                column
                for column in response["columns"]
                if "revenue" in column.lower()
                or "sales" in column.lower()
            ),
            None,
        )

        self.assertIsNotNone(
            revenue_column,
            f"Expected a revenue or sales column. Response: {response}",
        )

        self.assertAlmostEqual(
            float(response["results"][0][revenue_column]),
            2400.0,
            places=2,
            msg=f"Incorrect highest revenue. Response: {response}",
        )

    def test_profit_question_is_rejected_without_cost_data(self):
        response = answer_question(
            "Which product generated the highest profit?"
        )

        self.assertIn("error", response)
        self.assertIn("cost", response["error"].lower())
        self.assertNotIn("sql", response)


if __name__ == "__main__":
    unittest.main()