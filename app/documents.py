
import json
from pathlib import Path

from app.schema import get_schema


DESCRIPTIONS_PATH = (
    Path(__file__).resolve().parent.parent
    / "data"
    / "schema_descriptions.json"
)


def load_schema_descriptions() -> dict:
    """Load optional business descriptions for tables and columns."""

    if not DESCRIPTIONS_PATH.exists():
        return {}

    with DESCRIPTIONS_PATH.open(
        "r",
        encoding="utf-8",
    ) as file:
        return json.load(file)


def schema_to_documents(schema: dict) -> list[dict]:
    """Create enriched retrieval documents for each database table."""

    descriptions = load_schema_descriptions()
    documents = []

    for table_name, information in schema.items():
        table_description = descriptions.get(table_name, {})
        column_descriptions = table_description.get("columns", {})

        lines = [
            f"Table: {table_name}",
            f"Business description: "
            f"{table_description.get('description', 'Not provided.')}",
            "",
            "Columns:",
        ]

        for column in information["columns"]:
            column_name = column["name"]
            primary_key = (
                " PRIMARY KEY"
                if column["primary_key"]
                else ""
            )

            business_description = column_descriptions.get(
                column_name,
                "No business description provided.",
            )

            lines.append(
                f"- {column_name}: {column['type']}{primary_key}. "
                f"Meaning: {business_description}"
            )

        lines.extend(["", "Relationships:"])

        if information["foreign_keys"]:
            for foreign_key in information["foreign_keys"]:
                lines.append(
                    f"- {foreign_key['column']} -> "
                    f"{foreign_key['references_table']}."
                    f"{foreign_key['references_column']}"
                )
        else:
            lines.append("- None")

        documents.append({
            "id": table_name,
            "text": "\n".join(lines),
        })

    return documents


if __name__ == "__main__":
    schema = get_schema()
    documents = schema_to_documents(schema)

    for document in documents:
        print("=" * 60)
        print(f"ID: {document['id']}")
        print(document["text"])
