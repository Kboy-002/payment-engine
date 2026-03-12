import sqlite3
from contextlib import contextmanager
from datetime import datetime

DATABASE = "database.db"


@contextmanager
def db_connection():

    connection = sqlite3.connect(DATABASE)
    cursor = connection.cursor()

    try:
        yield cursor
        connection.commit()

    except Exception as e:
        connection.rollback()
        raise e

    finally:
        connection.close()


# INITIALISE DATABASE
def initialise_db():

    with db_connection() as cursor:

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            balance REAL NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            type TEXT NOT NULL,
            amount REAL NOT NULL,
            timestamp TEXT NOT NULL,
            details TEXT,
            transaction_group TEXT,
            FOREIGN KEY(user_id) REFERENCES users(id)
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL
        )
        """)

        cursor.execute("""
        CREATE TABLE IF NOT EXISTS restock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            item_name TEXT,
            quantity_added INTEGER,
            timestamp TEXT
        )
        """)

        # INSERT DEFAULT ITEMS
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]

        if count == 0:

            items = [
                ("Rice", 5000, 50),
                ("Beans", 3000, 40),
                ("Garri", 1500, 100)
            ]

            cursor.executemany("""
            INSERT INTO items (name, price, stock)
            VALUES (?, ?, ?)
            """, items)


# CREATE USER
def create_user(name):

    with db_connection() as cursor:

        cursor.execute("""
        INSERT INTO users (name, balance)
        VALUES (?, ?)
        """, (name, 0.0))


# GET USER
def get_user(name):

    with db_connection() as cursor:

        cursor.execute("""
        SELECT * FROM users WHERE name = ?
        """, (name,))

        return cursor.fetchone()


# UPDATE BALANCE
def update_balance(name, amount):

    with db_connection() as cursor:

        cursor.execute("""
        UPDATE users SET balance = ?
        WHERE name = ?
        """, (amount, name))


# DELETE ALL USERS
def delete_user():

    with db_connection() as cursor:

        cursor.execute("DELETE FROM users")

        print("All users deleted")


# GET ALL USERS
def get_all_users():

    with db_connection() as cursor:

        cursor.execute("SELECT * FROM users")

        return cursor.fetchall()


# GET ALL TRANSACTIONS
def get_all_transactions():

    with db_connection() as cursor:

        cursor.execute("SELECT * FROM transactions")

        return cursor.fetchall()


# LOG TRANSACTION
def log_transaction(user_id, tx_type, amount, details="", transaction_group=None):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_connection() as cursor:

        cursor.execute("""
        INSERT INTO transactions
        (user_id, type, amount, timestamp, details, transaction_group)
        VALUES (?, ?, ?, ?, ?, ?)
        """, (user_id, tx_type, amount, timestamp, details, transaction_group))


# GET USER TRANSACTIONS
def get_user_transactions(user_id):

    with db_connection() as cursor:

        cursor.execute("""
        SELECT type, amount, timestamp, details
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        """, (user_id,))

        return cursor.fetchall()


# VIEW RESTOCK HISTORY
def view_restock_logs():

    with db_connection() as cursor:

        cursor.execute("""
        SELECT item_name, quantity_added, timestamp
        FROM restock_logs
        ORDER BY timestamp DESC
        """)

        logs = cursor.fetchall()

    print("\n--- RESTOCK HISTORY ---")

    for log in logs:
        print(f"{log[2]} | {log[0]} | +{log[1]} units")
