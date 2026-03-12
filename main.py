from shop_logic import shop
from inventory import view_inventory, add_item, update_item, delete_item, low_stock_alert
from analytics import sales_report

from db_operations import (
    initialise_db,
    create_user,
    get_user,
    db_connection
)

from datetime import datetime


# INITIALISE DATABASE
initialise_db()


# LOGIN SYSTEM
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


# FUND WALLET
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

        with db_connection() as cursor:

            # GET CURRENT BALANCE
            cursor.execute(
                "SELECT balance FROM users WHERE id = ?",
                (user[0],)
            )

            current_balance = cursor.fetchone()[0]

            # UPDATE BALANCE
            new_balance = current_balance + amount

            cursor.execute(
                "UPDATE users SET balance = ? WHERE id = ?",
                (new_balance, user[0])
            )

            # LOG TRANSACTION
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
            INSERT INTO transactions
            (user_id, type, amount, timestamp, details)
            VALUES (?, ?, ?, ?, ?)
            """, (
                user[0],
                "credit",
                amount,
                timestamp,
                "Account funding"
            ))

        print(f"Funding successful. New balance: ₦{new_balance}")

    except Exception as e:

        print("Funding failed.")
        print("Error:", e)


# VIEW BALANCE
def view_balance(user):

    fresh_user = get_user(user[1])

    print(f"\nCurrent Balance: ₦{fresh_user[2]}")


# VIEW TRANSACTIONS
def view_transactions(user):

    with db_connection() as cursor:

        cursor.execute("""
        SELECT type, amount, timestamp, details, transaction_group
        FROM transactions
        WHERE user_id = ?
        ORDER BY timestamp DESC
        """, (user[0],))

        records = cursor.fetchall()

    if not records:
        print("\nNo transactions yet.\n")
        return

    print("\n--- Transaction History ---")

    for t_type, amount, timestamp, details, group in records:

        if group:
            print(
                f"{timestamp} | {t_type.upper()} | ₦{amount} | {details} | TXN: {group}"
            )

        else:
            print(
                f"{timestamp} | {t_type.upper()} | ₦{amount} | {details}"
            )


# INVENTORY MENU
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

        elif choice == "7":

            break

        else:
            print("Invalid option.")


# MAIN MENU
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


# START PROGRAM
login_user = login()
menu(login_user)