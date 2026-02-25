import sqlite3

def connect():
  connection = sqlite3.connect("payment_engine.db")
  return connection

def initialise_db():
  connection = connect()
  cursor = connection.cursor()
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
    FOREIGN KEY(user_id) REFERENCES users(id)
)
""")
  connection.commit()
  connection.close()
  



def create_user(name):
  connection = connect()
  cursor = connection.cursor()
  cursor.execute("""
    INSERT INTO users (name, balance)
    VALUES (?, ?)
    """, (name, 0.0))
  connection.commit()
  connection.close()

def get_user(name):
  connection = connect()
  cursor = connection.cursor()
  cursor.execute("""
  SELECT * FROM users Where name = ?
  """, (name,))
  user = cursor.fetchone()
  connection.close()
  return user

def update_balance(name, amount):
  connection = connect()
  cursor = connection.cursor()
  cursor.execute("""
  UPDATE users SET balance = ? WHERE name = ?
  """, (amount, name))
  connection.commit()
  connection.close()

def delete_user():
  connection = connect()
  cursor = connection.cursor()
  cursor.execute("""
  DELETE FROM users 
  """,)
  print("All users deleted")
  connection.commit()
  connection.close()

def get_all_users():
  connection = connect()
  cursor = connection.cursor()
  cursor.execute("""
  SELECT * FROM users
  """)
  users = cursor.fetchall()
  connection.close()
  return users

def get_all_transactions():
  connection = connect()
  cursor = connection.cursor()
  cursor.execute("""
  SELECT * FROM transactions
  """)
  users = cursor.fetchall()
  connection.close()
  return users

from datetime import datetime
def log_transaction(user_id, tx_type, amount, details=""):
    connection = connect()
    cursor = connection.cursor()

    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO transactions (user_id, type, amount, timestamp, details)
    VALUES (?, ?, ?, ?, ?)
    """, (user_id, tx_type, amount, timestamp, details))

    connection.commit()
    connection.close()

def get_user_transactions(user_id):
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
        SELECT type, amount, timestamp, details
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
    """, (user_id,))

    transactions = cursor.fetchall()
    connection.close()
    return transactions
