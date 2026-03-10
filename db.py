from db_operations import connect
import sqlite3
from db_operations import (
    initialise_db,
    create_user,
    get_user,
    update_balance,
    log_transaction,
    get_all_users,
    get_all_transactions,
    get_user_transactions
)
initialise_db()


def login():
    name = input("Enter your name: ")

    user = get_user(name)

    if user:
        print(f"Welcome back {name}!")
        return user
    else:
        print("Account not found. Creating new account...")
        create_user(name)
        user = get_user(name)
        print("Account created successfully.")
        return user


def fund_account(user):
    import sqlite3
    from db_operations import connect, log_transaction

    amount = float(input("Enter amount to fund: "))

    if amount <= 0:
        print("Invalid funding amount.")
        return

    connection = connect()
    try:
        cursor = connection.cursor()

        # Start a transaction
        cursor.execute("BEGIN")

        # Fetch fresh balance
        cursor.execute("SELECT balance FROM users WHERE id = ?", (user[0],))
        current_balance = cursor.fetchone()[0]

        # Update balance
        new_balance = current_balance + amount
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user[0]))

        # Log transaction
        from datetime import datetime
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        cursor.execute("""
            INSERT INTO transactions (user_id, type, amount, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
        """, (user[0], "credit", amount, timestamp, "Account funding"))

        # Commit transaction (everything succeeds together)
        connection.commit()
        print(f"Funding successful. New balance: ₦{new_balance}")

    except sqlite3.Error as e:
        # Rollback in case of any error (atomicity)
        connection.rollback()
        print("Funding failed, transaction rolled back.")
        print("Error:", e)

    finally:
        connection.close()

def shop(user):
    """
    Handles shopping, adding items to a cart, checking out,
    updating user balance in DB, reducing stock, and logging transactions atomically.
    """
    from db_operations import connect, get_user, update_balance, log_transaction
    from datetime import datetime
    import random

    connection = connect()
    cursor = connection.cursor()

    # Fetch items from database
    cursor.execute("SELECT id, name, price, stock FROM items")
    items = cursor.fetchall()

    if not items:
        print("No items available.")
        connection.close()
        return

    print("\n---- AVAILABLE ITEMS ----")
    for item in items:
        print(f"{item[0]}. {item[1]} - ₦{item[2]} (Stock: {item[3]})")

    try:
        item_id = int(input("Enter item ID to purchase: "))
        quantity = int(input("Enter quantity: "))
    except ValueError:
        print("Invalid input.")
        connection.close()
        return

    # Find selected item
    selected_item = next((item for item in items if item[0] == item_id), None)

    if not selected_item:
        print("Item not found.")
        connection.close()
        return

    item_id, name, price, stock = selected_item

    if quantity > stock:
        print("Not enough stock available.")
        connection.close()
        return

    total_cost = price * quantity

    # Get fresh user balance
    fresh_user = get_user(user[1])
    current_balance = fresh_user[2]

    if current_balance < total_cost:
        print("Insufficient funds.")
        connection.close()
        return

    # Atomic transaction
    try:
        # Begin transaction
        cursor.execute("BEGIN")

        # Deduct balance
        new_balance = current_balance - total_cost
        update_balance(user[1], new_balance)

        # Reduce stock
        new_stock = stock - quantity
        cursor.execute("UPDATE items SET stock = ? WHERE id = ?", (new_stock, item_id))

        

        # Commit everything
        connection.commit()

    except Exception as e:
        connection.rollback()
        print(f"Transaction failed: {e}")
        connection.close()
        return

    # Receipt
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    trans_id = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"

    # Log transaction
    log_transaction(user[0], "debit", total_cost, f"Purchased {quantity} x {name}", trans_id)

    print("\n----- RECEIPT -----")
    print(f"Date/Time: {timestamp}")
    print(f"Transaction ID: {trans_id}")
    print(f"{name} x{quantity} - ₦{total_cost}")
    print(f"New Balance: ₦{new_balance}")
    print("------------------")

    # Ledger
    with open("Transaction.txt 1.0", "a", encoding="utf-8") as ledger:
        ledger.write("\n----- NEW TRANSACTION -----\n")
        ledger.write(f"Username: {user[1]}\n")
        ledger.write(f"Transaction ID: {trans_id}\n")
        ledger.write(f"Date/Time: {timestamp}\n")
        ledger.write("------------------\n")
        ledger.write(f"{name} x{quantity} - ₦{total_cost}\n")
        ledger.write("------------------\n")
        ledger.write(f"TOTAL: ₦{total_cost}\n")
        ledger.write(f"New Balance: ₦{new_balance}\n")
        ledger.write("------------------\n")

    connection.close()


def view_balance(user):
    fresh_user = get_user(user[1])
    print(f"\nCurrent Balance: ₦{fresh_user[2]}")

def view_transactions(user):

    connection = connect()
    cursor = connection.cursor()

    cursor.execute("""
    SELECT type, amount, timestamp, details, transaction_group
    FROM transactions
    WHERE user_id = ?
    ORDER BY timestamp DESC
    """, (user[0],))

    records = cursor.fetchall()

    if not records:
        print("\nNo transactions yet.\n")
    else:
        print("\n--- Transaction History ---")

    for t_type, amount, timestamp, details, group in records:
        if group:
         print(f"{timestamp} | {t_type.upper()} | ₦{amount} | {details} | TXN: {group}")
        else:
         print(f"{timestamp} | {t_type.upper()} | ₦{amount} | {details}")

    connection.close()

def menu(user):
    while True:
        print("""
        ---- MAIN MENU ----
        1. Fund Account
        2. Shop
        3. View Balance
        4. View Transactions
        5. Logout
        """)

        choice = input("Select an option: ")

        if choice == "1":
            fund_account(user)

        elif choice == "2":
            shop(user)

        elif choice == "3":
            view_balance(user)

        elif choice == "4":
            view_transactions(user)

        elif choice == "5":
            print("Logging out...")
            break

        else:
            print("Invalid option. Try again.")


login_user = login()
menu(login_user)

