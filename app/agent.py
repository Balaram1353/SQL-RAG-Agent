from app.vector_store import build_index, search
from app.llm import generate_sql, explain_results
from app.sql_executor import execute_sql
from app.schema import get_schema
from app.database import get_connection

MAX_SQL_ATTEMPTS = 2


def get_full_schema_description() -> str:
    """Retrieve complete SQLite schema without calling the LLM."""

    conn = get_connection()

    try:
        cursor = conn.cursor()

        tables = cursor.execute("""
            SELECT name, sql
            FROM sqlite_master
            WHERE type = 'table'
              AND name NOT LIKE 'sqlite_%'
            ORDER BY name
        """).fetchall()

        if not tables:
            return "No user tables were found in the database."

        sections = ["# Complete Database Schema"]

        for table_name, create_sql in tables:
            sections.append(f"\n## Table: {table_name}")

            # Column details
            safe_name = table_name.replace('"', '""')

            columns = cursor.execute(
                f'PRAGMA table_info("{safe_name}")'
            ).fetchall()

            sections.append("\n### Columns")
            sections.append(
                "| Column | Data Type | Not Null | Default | Primary Key |"
            )
            sections.append(
                "|---|---|---|---|---|"
            )

            for col in columns:
                _, name, data_type, not_null, default, pk = col

                sections.append(
                    f"| {name} | {data_type or 'UNDECLARED'} "
                    f"| {'Yes' if not_null else 'No'} "
                    f"| {default if default is not None else 'None'} "
                    f"| {'Yes' if pk else 'No'} |"
                )

            # Foreign key details
            foreign_keys = cursor.execute(
                f'PRAGMA foreign_key_list("{safe_name}")'
            ).fetchall()

            sections.append("\n### Foreign Keys")

            if foreign_keys:
                for fk in foreign_keys:
                    sections.append(
                        f"- `{fk[3]}` references "
                        f"`{fk[2]}.{fk[4]}`"
                    )
            else:
                sections.append("None")

            # Original CREATE TABLE statement
            sections.append("\n### CREATE TABLE Statement")
            sections.append("```sql")
            sections.append(
                create_sql or "-- Definition unavailable"
            )
            sections.append("```")

        return "\n".join(sections)

    finally:
        conn.close()



def answer_question(question: str) -> dict:

    normalized = " ".join(question.lower().strip().split())

    schema_keywords = [
    "schema",
    "all tables",
    "every table",
    "table structure",
    "table definitions",
    "column information",
    "all columns",
    "database structure",
    "describe tables",
    "list tables",
    "show tables",
    "table details",
    "structure of every table",
    ]

    is_schema_request = any(
    keyword in normalized
    for keyword in schema_keywords
    )

    if is_schema_request:
        try:
            schema_description = get_full_schema_description()

            return {
                "question": question,
                "answer": schema_description,
                "sql": "",
                "results": [],
                "columns": [],
                "attempts": 0,
            }
        except Exception as exc:
            return {
                "question": question,
                "error": f"Could not retrieve database schema: {exc}",
            }


    # 2. Deterministic guardrail for profit questions.
    profit_terms = ("profit", "profitable", "profitability")

    if any(term in question.lower() for term in profit_terms):
        schema = get_schema()

        available_columns = {
            column["name"].lower()
            for table in schema.values()
            for column in table["columns"]
        }

        cost_columns = {
            "cost",
            "unit_cost",
            "cost_price",
            "purchase_price",
            "cost_amount",
        }

        if not available_columns.intersection(cost_columns):
            return {
                "question": question,
                "error": (
                    "Actual profit cannot be calculated because the database "
                    "does not contain a recognized cost column. Selling price "
                    "can be used to calculate revenue, but revenue is not "
                    "profit. Please provide product cost data to calculate profit."
                ),
            }

    # 3. Retrieve relevant schema.
    index = build_index()
    results = search(index, question, top_k=4)

    schema_context = "\n\n".join(
        result["text"] for result in results
    )

    # 4. Generate SQL and retry if validation or execution fails.
    sql = ""
    query_result = None
    attempts = 0

    repair_question = question

    for attempt in range(1, MAX_SQL_ATTEMPTS + 1):
        attempts = attempt

        sql = generate_sql(
            repair_question,
            schema_context,
        )

        query_result = execute_sql(sql)

        if query_result["success"]:
            break

        if attempt < MAX_SQL_ATTEMPTS:
            repair_question = f"""
The original user question is:
{question}

Your previous SQL query failed validation or execution.

Previous SQL:
{sql}

Error returned by the SQL executor:
{query_result["error"]}

Correct the SQL query to answer the original user question.
Use only tables and columns in the supplied schema.
Return exactly one read-only SQLite SELECT query.
Do not attempt to modify the database.
Return only the SQL, without Markdown fences or explanation.
"""

    # 5. Return an error if all attempts fail.
    if query_result is None or not query_result["success"]:
        return {
            "question": question,
            "sql": sql,
            "attempts": attempts,
            "error": (
                query_result["error"]
                if query_result
                else "No SQL query was executed."
            ),
        }

    # 6. Explain the actual query results.
    answer = explain_results(
        question,
        sql,
        query_result,
    )

    return {
        "question": question,
        "sql": sql,
        "columns": query_result["columns"],
        "results": query_result["rows"],
        "row_count_returned": query_result["row_count_returned"],
        "attempts": attempts,
        "answer": answer,
    }



if __name__ == "__main__":
    print("Starting SQL-RAG Agent...")
    print("Loading the schema and embedding index. Please wait.")

    # Warm up the index once when the application starts.
    build_index()

    print("\nSQL-RAG Agent is ready!")
    print("Ask questions about your database.")
    print("Type 'exit' or 'quit' to stop.\n")

    while True:
        try:
            question = input("You: ").strip()

            if question.lower() in {"exit", "quit"}:
                print("Closing SQL-RAG Agent. Goodbye!")
                break

            if not question:
                print("Please enter a question.\n")
                continue

            response = answer_question(question)

            if "error" in response:
                print(f"\nError: {response['error']}")
            else:
                print("\nGenerated SQL:")
                print(response["sql"])

                print("\nDatabase results:")
                print(response["results"])

                print("\nAnswer:")
                print(response["answer"])

                print(f"\nSQL attempts: {response['attempts']}")

            print("\n" + "-" * 60 + "\n")

        except (KeyboardInterrupt, EOFError):
            print("\nClosing SQL-RAG Agent. Goodbye!")
            break
        except Exception as exc:
            print(f"\nAn unexpected error occurred: {exc}\n")
