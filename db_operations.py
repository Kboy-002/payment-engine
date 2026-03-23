import os
import psycopg2
from contextlib import contextmanager
from datetime import datetime
from auth import hash_password, verify_password

# Load environment variables (must be called before this file is imported)
from dotenv import load_dotenv
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    raise ValueError("DATABASE_URL environment variable is not set")


@contextmanager
def db_connection():
    """Context manager for PostgreSQL connections with SSL required."""
    # sslmode=require is necessary for Supabase
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


def initialise_db():
    """Create tables if they don't exist."""
    with db_connection() as conn:
        with conn.cursor() as cur:
            # Branches table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS branches (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL
                )
            """)
            # Insert default branch (HQ)
            cur.execute("""
                INSERT INTO branches (id, name)
                VALUES (1, 'HQ')
                ON CONFLICT (id) DO NOTHING
            """)

            # Users table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id SERIAL PRIMARY KEY,
                    name TEXT UNIQUE NOT NULL,
                    password_hash TEXT NOT NULL,
                    balance REAL DEFAULT 0,
                    role TEXT DEFAULT 'customer',
                    branch_id INTEGER DEFAULT 1 REFERENCES branches(id)
                )
            """)

            # Items table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS items (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    price REAL NOT NULL,
                    stock INTEGER NOT NULL,
                    branch_id INTEGER DEFAULT 1 REFERENCES branches(id)
                )
            """)

            # Transactions table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS transactions (
                    id SERIAL PRIMARY KEY,
                    user_id INTEGER REFERENCES users(id),
                    type TEXT,
                    amount REAL,
                    item_name TEXT,
                    quantity INTEGER,
                    timestamp TEXT,
                    branch_id INTEGER DEFAULT 1 REFERENCES branches(id)
                )
            """)

            # Restock logs table
            cur.execute("""
                CREATE TABLE IF NOT EXISTS restock_logs (
                    id SERIAL PRIMARY KEY,
                    item_id INTEGER REFERENCES items(id),
                    item_name TEXT,
                    quantity_added INTEGER,
                    timestamp TEXT,
                    branch_id INTEGER DEFAULT 1 REFERENCES branches(id)
                )
            """)

            # Default items
            cur.execute("SELECT COUNT(*) FROM items")
            count = cur.fetchone()[0]
            if count == 0:
                items = [
                    ("Rice", 5000, 50, 1),
                    ("Beans", 3000, 40, 1),
                    ("Garri", 1500, 100, 1),
                ]
                cur.executemany("""
                    INSERT INTO items (name, price, stock, branch_id)
                    VALUES (%s, %s, %s, %s)
                """, items)

            # Default users
            cur.execute("SELECT COUNT(*) FROM users")
            count_users = cur.fetchone()[0]
            if count_users == 0:
                default_password_hash = hash_password("password")
                users = [
                    ("admin", default_password_hash, 0, "admin", 1),
                    ("testuser", default_password_hash, 100000, "customer", 1),
                ]
                cur.executemany("""
                    INSERT INTO users (name, password_hash, balance, role, branch_id)
                    VALUES (%s, %s, %s, %s, %s)
                """, users)

    print("Database initialized successfully.")


def create_user(name, password, role="customer", branch_id=1):
    with db_connection() as conn:
        with conn.cursor() as cur:
            hashed = hash_password(password)
            cur.execute("""
                INSERT INTO users (name, password_hash, balance, role, branch_id)
                VALUES (%s, %s, %s, %s, %s)
            """, (name, hashed, 0.0, role, branch_id))


def get_user(name):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE name = %s", (name,))
            return cur.fetchone()


def get_user_by_name(name):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users WHERE name = %s", (name,))
            row = cur.fetchone()
            if row:
                return {
                    'id': row[0],
                    'name': row[1],
                    'password_hash': row[2],
                    'balance': row[3],
                    'role': row[4],
                    'branch_id': row[5],
                }
            return None


def update_balance(name, amount):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("UPDATE users SET balance = %s WHERE name = %s", (amount, name))


def delete_user():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM users")
            print("All users deleted")


def get_all_users():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM users")
            return cur.fetchall()


def get_all_transactions():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT * FROM transactions")
            return cur.fetchall()


def log_transaction(user_id, tx_type, amount, item_name="", quantity=0, branch_id=1):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO transactions
                (user_id, type, amount, item_name, quantity, timestamp, branch_id)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
            """, (user_id, tx_type, amount, item_name, quantity, timestamp, branch_id))


def get_user_transactions(user_id):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT type, amount, item_name, quantity, timestamp
                FROM transactions
                WHERE user_id = %s
                ORDER BY id DESC
            """, (user_id,))
            return cur.fetchall()


def view_restock_logs():
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT item_name, quantity_added, timestamp
                FROM restock_logs
                ORDER BY timestamp DESC
            """)
            logs = cur.fetchall()
    print("\n--- RESTOCK HISTORY ---")
    for log in logs:
        print(f"{log[2]} | {log[0]} | +{log[1]} units")