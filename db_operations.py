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
    from db_operations import db_connection

    with db_connection() as cursor:

        # -------------------- BRANCHES --------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS branches (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL
        )
        """)
        # Insert default branch (HQ)
        cursor.execute("""
        INSERT OR IGNORE INTO branches (id, name)
        VALUES (1, 'HQ')
        """)

        # -------------------- USERS --------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            balance REAL DEFAULT 0,
            role TEXT DEFAULT 'customer',
            branch_id INTEGER DEFAULT 1,
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
        """)

        # -------------------- ITEMS --------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            price REAL NOT NULL,
            stock INTEGER NOT NULL,
            branch_id INTEGER DEFAULT 1,
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
        """)

        # -------------------- TRANSACTIONS --------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            type TEXT,
            amount REAL,
            item_name TEXT,
            quantity INTEGER,
            timestamp TEXT,
            branch_id INTEGER DEFAULT 1,
            FOREIGN KEY (user_id) REFERENCES users(id),
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
        """)

        # -------------------- RESTOCK LOGS --------------------
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS restock_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            item_id INTEGER,
            item_name TEXT,
            quantity_added INTEGER,
            timestamp TEXT,
            branch_id INTEGER DEFAULT 1,
            FOREIGN KEY (branch_id) REFERENCES branches(id)
        )
        """)

        # -------------------- DEFAULT ITEMS --------------------
        cursor.execute("SELECT COUNT(*) FROM items")
        count = cursor.fetchone()[0]

        if count == 0:
            items = [
                ("Rice", 5000, 50, 1),
                ("Beans", 3000, 40, 1),
                ("Garri", 1500, 100, 1)
            ]
            cursor.executemany("""
            INSERT INTO items (name, price, stock, branch_id)
            VALUES (?, ?, ?, ?)
            """, items)

        # -------------------- DEFAULT USERS --------------------
        cursor.execute("SELECT COUNT(*) FROM users")
        count_users = cursor.fetchone()[0]

        if count_users == 0:
            users = [
                ("Admin", 0, "admin", 1),
                ("TestUser", 100000, "customer", 1)
            ]
            cursor.executemany("""
            INSERT INTO users (name, balance, role, branch_id)
            VALUES (?, ?, ?, ?)
            """, users)

    print("Database initialized successfully.")

# CREATE USER


def create_user(name, role="customer"):

    with db_connection() as cursor:

        cursor.execute("""
        INSERT INTO users (name, balance, role)
        VALUES (?, ?, ?)
        """, (name, 0.0, role))


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
def log_transaction(user_id, tx_type, amount, details=""):

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    with db_connection() as cursor:

        cursor.execute("""
        INSERT INTO transactions
        (user_id, type, amount, timestamp, details)
        VALUES (?, ?, ?, ?, ?)
        """, (user_id, tx_type, amount, timestamp, details))


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
