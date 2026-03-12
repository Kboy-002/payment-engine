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
from db_operations import view_inventory, add_item, update_item, delete_item, low_stock_alert, sales_report

def login():
    name = input("Enter your name: ").lower()

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
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?",
                       (new_balance, user[0]))

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
    Handles shopping using a cart system.
    Users can add multiple items before checkout.
    """
    from db_operations import connect, get_user
    from datetime import datetime
    import random

    connection = connect()
    cursor = connection.cursor()

    # Fetch items
    cursor.execute("SELECT id, name, price, stock FROM items")
    items = cursor.fetchall()

    if not items:
        print("No items available.")
        connection.close()
        return

    print("\n---- AVAILABLE ITEMS ----")
    for item in items:
        print(f"{item[0]}. {item[1]} - ₦{item[2]} (Stock: {item[3]})")

    # CART STORAGE
    cart = {}

    while True:
        try:
            item_id = int(input("\nEnter item ID to add to cart (0 to checkout): "))
        except ValueError:
            print("Invalid input.")
            continue

        if item_id == 0:
            break

        selected_item = next((item for item in items if item[0] == item_id), None)

        if not selected_item:
            print("Item not found.")
            continue

        item_id, name, price, stock = selected_item

        try:
            quantity = int(input("Enter quantity: "))
        except ValueError:
            print("Invalid quantity.")
            continue

        if quantity > stock:
            print("Not enough stock available.")
            continue

        # ADD TO CART
        if item_id in cart:
            cart[item_id]["qty"] += quantity
        else:
            cart[item_id] = {
                "name": name,
                "price": price,
                "qty": quantity,
                "stock": stock
            }

        print(f"{quantity} x {name} added to cart.")

        # DISPLAY CART
        print("\n---- CURRENT CART ----")
        total = 0
        for item in cart.values():
            item_total = item["price"] * item["qty"]
            total += item_total
            print(f"{item['name']} x{item['qty']} = ₦{item_total}")
        print(f"Cart Total: ₦{total}")

    if not cart:
        print("Cart is empty.")
        connection.close()
        return

    # CALCULATE TOTAL
    total_cost = sum(item["price"] * item["qty"] for item in cart.values())

    # GET FRESH USER BALANCE
    fresh_user = get_user(user[1])
    current_balance = fresh_user[2]

    if current_balance < total_cost:
        print("Insufficient funds.")
        connection.close()
        return

    # ATOMIC TRANSACTION
    try:
        cursor.execute("BEGIN")

        # Deduct user balance
        new_balance = current_balance - total_cost
        cursor.execute("UPDATE users SET balance = ? WHERE id = ?", (new_balance, user[0]))

        # GENERATE TRANSACTION ID
        trans_id = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"

        # PROCESS CART ITEMS
        for item_id, item in cart.items():
            new_stock = item["stock"] - item["qty"]
            cursor.execute("UPDATE items SET stock = ? WHERE id = ?", (new_stock, item_id))

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            cursor.execute("""
                INSERT INTO transactions (user_id, type, amount, timestamp, details, transaction_group)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (
                user[0],
                "debit",
                item["price"] * item["qty"],
                timestamp,
                f"Purchased {item['qty']} x {item['name']}",
                trans_id
            ))

        connection.commit()

    except Exception as e:
        connection.rollback()
        print(f"Transaction failed: {e}")
        connection.close()
        return

    # RECEIPT
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    print("\n----- RECEIPT -----")
    print(f"Date/Time: {timestamp}")
    print(f"Transaction ID: {trans_id}")
    for item in cart.values():
        print(f"{item['name']} x{item['qty']} - ₦{item['price'] * item['qty']}")
    print("------------------")
    print(f"TOTAL: ₦{total_cost}")
    print(f"New Balance: ₦{new_balance}")
    print("------------------")

    # LEDGER
    with open("Transaction.txt 1.0", "a", encoding="utf-8") as ledger:
        ledger.write("\n----- NEW TRANSACTION -----\n")
        ledger.write(f"Username: {user[1]}\n")
        ledger.write(f"Transaction ID: {trans_id}\n")
        ledger.write(f"Date/Time: {timestamp}\n")
        for item in cart.values():
            ledger.write(f"{item['name']} x{item['qty']} - ₦{item['price'] * item['qty']}\n")
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
            print(
                f"{timestamp} | {t_type.upper()} | ₦{amount} | {details} | TXN: {group}")
        else:
            print(f"{timestamp} | {t_type.upper()} | ₦{amount} | {details}")

    connection.close()

def inventory_menu():
    while True:
        print("\n---- INVENTORY MANAGEMENT ----")
        print("1. View Inventory")
        print("2. Add Item")
        print("3. Update Item")
        print("4. Delete Item")
        print("5. Low Stock Alert")
        print("6. Sales Report")
        print("7. Back to Main Menu")

        choice = input("Select an option: ")

        if choice == "1":
            view_inventory()

        elif choice == "2":
            name = input("Enter item name: ")

            try:
                price = float(input("Enter price: "))
                stock = int(input("Enter stock quantity: "))
            except ValueError:
                print("Invalid input.")
                continue

            add_item(name, price, stock)

        elif choice == "3":
            try:
                item_id = int(input("Enter item ID to update: "))
            except ValueError:
                print("Invalid ID.")
                continue

            name = input("Enter new name (leave blank to keep current): ")
            price = input("Enter new price (leave blank to keep current): ")
            stock = input("Enter new stock (leave blank to keep current): ")

            name = name if name else None
            price = float(price) if price else None
            stock = int(stock) if stock else None

            update_item(item_id, name, price, stock)

        elif choice == "4":
            try:
                item_id = int(input("Enter item ID to delete: "))
            except ValueError:
                print("Invalid ID.")
                continue

            delete_item(item_id)

        elif choice == "5":
            low_stock_alert()

        elif choice == "6":
            sales_report()

        elif choice == "6":
            break

        else:
            print("Invalid option.")


def menu(user):
    while True:
        print("""
        ---- MAIN MENU ----
        1. Fund Account
        2. Shop
        3. View Balance
        4. View Transactions
        5. Inventory Management
        6. Logout
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
            inventory_menu()

        elif choice == "6":
            print("Logging out...")
            break

        else:
            print("Invalid option. Try again.")


login_user = login()
menu(login_user)
