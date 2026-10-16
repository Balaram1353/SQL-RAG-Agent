from app.database import get_connection


def get_schema():
    connection = get_connection()
    cursor = connection.cursor()

    tables = cursor.execute("""
        SELECT name
        FROM sqlite_master
        WHERE type = 'table'
        AND name NOT LIKE 'sqlite_%'
        ORDER BY name;
    """).fetchall()

    schema = {}

    for (table_name,) in tables:

        columns = cursor.execute(
            f"PRAGMA table_info({table_name});"
        ).fetchall()

        foreign_keys = cursor.execute(
            f"PRAGMA foreign_key_list({table_name});"
        ).fetchall()

        schema[table_name] = {
            "columns": [
                {
                    "name": column[1],
                    "type": column[2],
                    "primary_key": bool(column[5]),
                }
                for column in columns
            ],
            "foreign_keys": [
                {
                    "column": fk[3],
                    "references_table": fk[2],
                    "references_column": fk[4],
                }
                for fk in foreign_keys
            ],
        }

    connection.close()

    return schema


if __name__ == "__main__":
    schema = get_schema()

    for table, information in schema.items():

        print(f"\nTable: {table}")

        print("Columns:")

        for column in information["columns"]:
            print(
                f"  {column['name']} "
                f"({column['type']}) "
                f"PK={column['primary_key']}"
            )

        print("Foreign keys:")

        for foreign_key in information["foreign_keys"]:
            print(
                f"  {foreign_key['column']} "
                f"→ "
                f"{foreign_key['references_table']}."
                f"{foreign_key['references_column']}"
            )