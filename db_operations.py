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
  cursor.execute("""
CREATE TABLE IF NOT EXISTS items(
id INTEGER PRIMARY KEY AUTOINCREMENT,
name TEXT UNIQUE NOT NULL,
price REAL NOT NULL,
stock INTEGER NOT NULL
    )
""")
  try:
    cursor.execute("""
    ALTER TABLE transactions
    ADD COLUMN transaction_group TEXT
    """)
  except:
    pass
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

def log_transaction(user_id, tx_type, amount, details="", transaction_group=None):

    connection = connect()
    cursor = connection.cursor()

    from datetime import datetime
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    cursor.execute("""
    INSERT INTO transactions (user_id, type, amount, timestamp, details, transaction_group)
    VALUES (?, ?, ?, ?, ?, ?)
    """, (user_id, tx_type, amount, timestamp, details, transaction_group))

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
