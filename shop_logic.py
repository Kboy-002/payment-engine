from db_operations import db_connection, get_user
from datetime import datetime
import random
from logger import log_event


def shop(user):
    """
    Handles shopping using a cart system.
    Users can add multiple items before checkout.
    """

    # FETCH ITEMS
    with db_connection() as cursor:
        cursor.execute("SELECT id, name, price, stock FROM items")
        items = cursor.fetchall()

    if not items:
        print("No items available.")
        return

    print("\n---- AVAILABLE ITEMS ----")
    for item in items:
        print(f"{item[0]}. {item[1]} - ₦{item[2]} (Stock: {item[3]})")

    cart = {}

    # SHOPPING LOOP
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

        # SHOW CART
        print("\n---- CURRENT CART ----")

        total = 0

        for item in cart.values():
            item_total = item["price"] * item["qty"]
            total += item_total
            print(f"{item['name']} x{item['qty']} = ₦{item_total}")

        print(f"Cart Total: ₦{total}")

    if not cart:
        print("Cart is empty.")
        return

    # TOTAL COST
    total_cost = sum(item["price"] * item["qty"] for item in cart.values())

    # GET FRESH USER BALANCE
    fresh_user = get_user(user[1])
    current_balance = fresh_user[2]

    if current_balance < total_cost:
        print("Insufficient funds.")
        return

    try:

        with db_connection() as cursor:

            # DEDUCT BALANCE
            new_balance = current_balance - total_cost

            cursor.execute(
                "UPDATE users SET balance = ? WHERE id = ?",
                (new_balance, user[0])
            )

            # GENERATE TRANSACTION ID
            trans_id = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000,9999)}"

            # PROCESS CART
            for item_id, item in cart.items():

                new_stock = item["stock"] - item["qty"]

                cursor.execute(
                    "UPDATE items SET stock = ? WHERE id = ?",
                    (new_stock, item_id)
                )

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                cursor.execute("""
                INSERT INTO transactions
                (user_id, type, amount, timestamp, details, transaction_group)
                VALUES (?, ?, ?, ?, ?, ?)
                """, (
                    user[0],
                    "debit",
                    item["price"] * item["qty"],
                    timestamp,
                    f"Purchased {item['qty']} x {item['name']}",
                    trans_id
                ))

        # LOG SUCCESS
        log_event("INFO", "Purchase completed", trans_id)

    except Exception as e:

        log_event("ERROR", "Transaction failure", str(e))
        print("Transaction failed. Please try again.")
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

    # LEDGER FILE
    with open("Transaction.txt 1.0", "a", encoding="utf-8") as ledger:

        ledger.write("\n----- NEW TRANSACTION -----\n")
        ledger.write(f"Username: {user[1]}\n")
        ledger.write(f"Transaction ID: {trans_id}\n")
        ledger.write(f"Date/Time: {timestamp}\n")

        for item in cart.values():
            ledger.write(
                f"{item['name']} x{item['qty']} - ₦{item['price'] * item['qty']}\n"
            )

        ledger.write("------------------\n")
        ledger.write(f"TOTAL: ₦{total_cost}\n")
        ledger.write(f"New Balance: ₦{new_balance}\n")
        ledger.write("------------------\n")