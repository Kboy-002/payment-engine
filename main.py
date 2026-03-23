from auth import hash_password, verify_password
from shop_logic import shop
from inventory import view_inventory, add_item, update_item, delete_item, low_stock_alert
from analytics import display_sales_report, sales_report
from db_operations import (
    initialise_db,
    create_user,
    get_user,
    db_connection
)
from datetime import datetime

initialise_db()


def login():
    while True:
        name = input("Enter your name: ").strip().lower()
        if not name:
            print("Name cannot be empty. Please try again.")
            continue
        password = input("Enter your password: ").strip()
        if not password:
            print("Password cannot be empty. Please try again.")
            continue
        break

    user = get_user(name)

    if user:
        stored_hash = user[2]
        if verify_password(password, stored_hash):
            print(f"Welcome back {name}!")
            return user
        else:
            print("Incorrect password. Try again.")
            return login()
    else:
        print("Account not found. Creating new account...")
        create_user(name, password, role="customer", branch_id=1)
        user = get_user(name)
        print("Account created successfully.")
        return user


def fund_account(user):
    try:
        amount = float(input("Enter amount to fund: "))
    except ValueError:
        print("Invalid amount.")
        return

    if amount <= 0:
        print("Invalid funding amount.")
        return

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT balance FROM users WHERE id = %s", (user[0],))
                current_balance = cur.fetchone()[0]

                new_balance = current_balance + amount
                cur.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user[0]))

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                branch_id = user[5]  # correct index for branch_id (was user[4] which is role)
                cur.execute("""
                    INSERT INTO transactions
                    (user_id, type, amount, item_name, quantity, timestamp, branch_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user[0], "credit", float(amount), "Wallet Funding", 0, timestamp, branch_id))

        print(f"Funding successful. New balance: ₦{new_balance:,.2f}")
    except Exception as e:
        print("Funding failed.")
        print("Error:", e)


def view_balance(user):
    fresh_user = get_user(user[1])  # user[1] is name
    print(f"\nCurrent Balance: ₦{fresh_user[3]:,.2f}")  # fresh_user[3] is balance


def view_transactions(user):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT type, amount, item_name, quantity, timestamp
                FROM transactions
                WHERE user_id = %s
                ORDER BY timestamp DESC
            """, (user[0],))
            records = cur.fetchall()

    if not records:
        print("\nNo transactions yet.\n")
        return

    print("\n--- Transaction History ---")
    for t_type, amount, item_name, quantity, timestamp in records:
        if t_type == "debit":
            print(f"{timestamp} | {t_type.upper()} | ₦{amount:,.2f} | {item_name} x{quantity}")
        else:
            print(f"{timestamp} | {t_type.upper()} | ₦{amount:,.2f} | {item_name}")


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
            branch_input = input("Enter branch ID (or ALL): ").strip()
            if branch_input == "":
                branch_input = None
            display_sales_report(branch_input)
        elif choice == "7":
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