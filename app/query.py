from app.database import get_connection


def run_query(sql):
    connection = get_connection()

    cursor = connection.cursor()
    cursor.execute(sql)

    results = cursor.fetchall()

    connection.close()

    return results


if __name__ == "__main__":
    results = run_query(
        "SELECT name, country FROM customers"
    )

    for row in results:
        print(row)
