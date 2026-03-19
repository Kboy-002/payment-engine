from db_operations import db_connection
with db_connection() as cursor:
    cursor.execute("SELECT * FROM users")
    rows = cursor.fetchall()
    for row in rows:
        print(row)
