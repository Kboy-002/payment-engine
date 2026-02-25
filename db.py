import sqlite3
from db_operations import (
    initialise_db,
    create_user,
    get_user,
    update_balance,
    log_transaction,
    get_all_users,
    get_all_transactions
)
initialise_db()


def login():
    name = input("Enter your name: ")

    user = get_user(name)

    if user:
        print(f"Welcome back {name}!")
        print(f"Your balance is ₦{user[2]}")
        return user
    else:
        print("Account not found. Creating new account...")
        create_user(name)
        user = get_user(name)
        print("Account created successfully.")
        return user


def fund_account(user):
    amount = float(input("Enter amount to fund: "))

    if amount <= 0:
        print("Invalid funding amount.")
        return

    fresh_user = get_user(user[1])

    current_balance = fresh_user[2]
    new_balance = current_balance + amount

    update_balance(user[1], new_balance)

    # Log transaction
    log_transaction(user[0], "credit", amount, "Account funding")

    print(f"Funding successful. New balance: ₦{new_balance}")


def shop(user):
    """
    Handles shopping, adding items to a cart, checking out,
    updating user balance in DB, and logging transactions.
    """
    # Example items — in a real app these could be in a DB table too
    items = {
        "bread": 2800,
        "water": 500,
        "butter": 800,
        "juice": 1000,
        "chicken": 3700
    }

    cart = {}
    total_cost = 0

    while True:
        print("\nAvailable items:")
        for name, price in items.items():
            print(f"{name.capitalize()}: ₦{price}")

        choice = input(
            f"{user[1].capitalize()}, what would you like to buy? (type 'done' to checkout): ").lower()
        if choice == "done":
            break

        if choice not in items:
            print(f"Sorry, {choice} is not available.")
            continue

        quantity = int(input(f"How many {choice} would you like? "))
        subtotal = items[choice] * quantity

        # Fetch the fresh balance from DB
        fresh_user = get_user(user[1])
        if fresh_user[2] < total_cost + subtotal:
            print("Insufficient funds for this item.")
            continue

        # Add to cart
        if choice in cart:
            cart[choice]['qty'] += quantity
            cart[choice]['subtotal'] += subtotal
        else:
            cart[choice] = {"price": items[choice],
                            "qty": quantity, "subtotal": subtotal}

        total_cost += subtotal
        print(f"Added {quantity} x {choice} to cart. Cart total: ₦{total_cost}")

    if not cart:
        print("No items purchased. Exiting shop.")
        return

    # Deduct total cost from DB
    new_balance = fresh_user[2] - total_cost
    update_balance(user[1], new_balance)

    # Log each item as a transaction
    for item_name, data in cart.items():
        log_transaction(user[0], "debit", data['subtotal'],
                        f"Purchased {data['qty']} x {item_name}")

    print("\n----- RECEIPT -----")
    from datetime import datetime
    import random
    timestamp = datetime.now().strftime("%d-%m-%Y %H:%M:%S")
    trans_id = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"
    print(f"Date/Time: {timestamp}")
    print(f"Transaction ID: {trans_id}")
    for item_name, data in cart.items():
        print(f"{item_name.capitalize()} x{data['qty']} - ₦{data['subtotal']}")
    print(f"TOTAL: ₦{total_cost}")
    print(f"New Balance: ₦{new_balance}")
    print("------------------")

    with open("Transaction.txt 1.0", "a", encoding="utf-8") as ledger:
        ledger.write("\n----- NEW TRANSACTION -----\n")
        ledger.write(f"Username: {user[1]}\n")
        ledger.write(f"Transaction ID: {trans_id}\n")
        ledger.write(f"Date/Time: {timestamp}\n")
        ledger.write("------------------\n")

        for item_name, data in cart.items():
            ledger.write(f"{item_name} x{data['qty']} - ₦{data['subtotal']}\n")

        ledger.write("------------------\n")
        ledger.write(f"TOTAL: ₦{total_cost}\n")
        ledger.write(f"New Balance: ₦{new_balance}\n")
        ledger.write("------------------\n")


user = login()
fund_account(user)
shop(user)

for item in get_all_transactions():
    print(item)

