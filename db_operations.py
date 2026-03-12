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

def create_restock_table():
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS restock_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        item_id INTEGER,
        item_name TEXT,
        quantity_added INTEGER,
        timestamp TEXT
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

# INVENTORY MANAGEMENT FUNCTIONS


def view_inventory():
    """Fetches and prints all items in the inventory."""
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("SELECT id, name, price, stock FROM items")
    items = cursor.fetchall()

    if not items:
        print("\nNo items in inventory.\n")
    else:
        print("\n--- INVENTORY ---")
        for item in items:
            print(
                f"ID: {item[0]} | {item[1]} | Price: ₦{item[2]} | Stock: {item[3]}")
        print("----------------\n")

    connection.close()


def add_item(name, price, stock):

    connection = connect()
    cursor = connection.cursor()

    try:
        cursor.execute("BEGIN")

        # CHECK IF ITEM ALREADY EXISTS
        cursor.execute(
            "SELECT id, stock FROM items WHERE LOWER(name) = LOWER(?)",
            (name,)
        )

        item = cursor.fetchone()

        if item:

            item_id, current_stock = item
            new_stock = current_stock + stock

            cursor.execute(
                "UPDATE items SET stock = ?, price = ? WHERE id = ?",
                (new_stock, price, item_id)
            )

            print(f"Item already exists. Stock increased to {new_stock}.")

        else:

            cursor.execute(
                "INSERT INTO items (name, price, stock) VALUES (?, ?, ?)",
                (name, price, stock)
            )

            print(f"New item '{name}' added to inventory.")

        connection.commit()

    except Exception as e:

        connection.rollback()
        print(f"Failed to add item: {e}")

    finally:

        connection.close()


def update_item(item_id, name=None, price=None, stock=None):
    from datetime import datetime

    connection = connect()
    cursor = connection.cursor()

    try:
        cursor.execute("BEGIN")

        cursor.execute("SELECT name, price, stock FROM items WHERE id = ?", (item_id,))
        item = cursor.fetchone()

        if not item:
            print("Item not found.")
            return

        old_name, old_price, old_stock = item

        new_name = name if name is not None else old_name
        new_price = price if price is not None else old_price
        new_stock = stock if stock is not None else old_stock

        cursor.execute(
            "UPDATE items SET name = ?, price = ?, stock = ? WHERE id = ?",
            (new_name, new_price, new_stock, item_id)
        )

        # DETECT RESTOCK
        if new_stock > old_stock:

            added_quantity = new_stock - old_stock
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
            INSERT INTO restock_logs (item_id, item_name, quantity_added, timestamp)
            VALUES (?, ?, ?, ?)
            """, (item_id, new_name, added_quantity, timestamp))

        connection.commit()
        print("Item updated successfully.")

    except Exception as e:
        connection.rollback()
        print(f"Update failed: {e}")

    finally:
        connection.close()


def delete_item(item_id):
    """Deletes an item from the inventory."""
    connection = connect()
    cursor = connection.cursor()
    try:
        cursor.execute("BEGIN")
        cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))
        connection.commit()
        print(f"Item ID {item_id} deleted successfully.")
    except Exception as e:
        connection.rollback()
        print(f"Failed to delete item: {e}")
    finally:
        connection.close()

def low_stock_alert(threshold=5):
    """
    Displays items whose stock is below a given threshold.
    Default threshold is 5.
    """
    connection = connect()
    cursor = connection.cursor()

    cursor.execute(
        "SELECT id, name, stock FROM items WHERE stock <= ?",
        (threshold,)
    )

    items = cursor.fetchall()

    if items:
        print("\n⚠ LOW STOCK ALERT ⚠")
        for item in items:
            print(f"{item[1]} - Only {item[2]} left in stock")
        print("------------------------")
    else:
        print("\nInventory levels are healthy.\n")

    connection.close()

def view_restock_logs():
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("SELECT item_name, quantity_added, timestamp FROM restock_logs ORDER BY timestamp DESC")
    logs = cursor.fetchall()

    print("\n--- RESTOCK HISTORY ---")

    for log in logs:
        print(f"{log[2]} | {log[0]} | +{log[1]} units")

    connection.close()

def sales_report():
    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT details, amount
    FROM transactions
    WHERE type = 'debit'
    """)

    sales = cursor.fetchall()

    if not sales:
        print("\nNo sales data available.\n")
        connection.close()
        return

    sales_data = {}
    total_revenue = 0

    for details, amount in sales:

        try:
            parts = details.split(" x ")

            quantity = int(parts[0].replace("Purchased ", ""))
            item_name = parts[1]

        except:
            continue

        if item_name not in sales_data:
            sales_data[item_name] = 0

        sales_data[item_name] += quantity
        total_revenue += amount

    print("\n------ SALES REPORT ------\n")

    for item, qty in sales_data.items():
        print(f"{item}")
        print(f"Total Sold: {qty}\n")

    print("--------------------------")
    print(f"Total Revenue: ₦{total_revenue}")
    print("--------------------------")

    connection.close()