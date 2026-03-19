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
            item_id = int(
                input("\nEnter item ID to add to cart (0 to checkout): "))
        except ValueError:
            print("Invalid input.")
            continue

        if item_id == 0:
            break

        selected_item = next(
            (item for item in items if item[0] == item_id), None)

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
    fresh_user = get_user(user[1].lower())
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
            trans_id = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"

            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            # PROCESS CART
            for item_id, item in cart.items():

                new_stock = item["stock"] - item["qty"]

                # UPDATE STOCK
                cursor.execute(
                    "UPDATE items SET stock = ? WHERE id = ?",
                    (new_stock, item_id)
                )
                branch_id = user[4]

                # ✅ NEW STRUCTURED TRANSACTION INSERT
                cursor.execute("""
                INSERT INTO transactions
                (user_id, type, amount, item_name, quantity, timestamp, branch_id)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    user[0],
                    "debit",
                    item["price"] * item["qty"],
                    item["name"],
                    item["qty"],
                    timestamp,
                    branch_id
                ))

        # LOG SUCCESS
        log_event("INFO", "Purchase completed", trans_id)

    except Exception as e:

        log_event("ERROR", "Transaction failure", str(e))
        print("Transaction failed. Please try again.")
        return

    # RECEIPT
    timestamp_display = datetime.now().strftime("%d-%m-%Y %H:%M:%S")

    print("\n----- RECEIPT -----")
    print(f"Date/Time: {timestamp_display}")
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
        ledger.write(f"Date/Time: {timestamp_display}\n")

        for item in cart.values():
            ledger.write(
                f"{item['name']} x{item['qty']} - ₦{item['price'] * item['qty']}\n"
            )

        ledger.write("------------------\n")
        ledger.write(f"TOTAL: ₦{total_cost}\n")
        ledger.write(f"New Balance: ₦{new_balance}\n")
        ledger.write("------------------\n")


def purchase_item_logic(user_name, item_id, quantity):

    from db_operations import db_connection, get_user
    from datetime import datetime

    user = get_user(user_name.lower())

    if not user:
        return {"status": "error", "message": "User not found"}

    try:

        with db_connection() as cursor:

            # GET USER BRANCH
            branch_id = user[4]

            # GET ITEM (ONLY FROM SAME BRANCH)
            cursor.execute(
                "SELECT name, price, stock FROM items WHERE id = ? AND branch_id = ?",
                (item_id, branch_id)
            )
            item = cursor.fetchone()

            if not item:
                return {"status": "error", "message": "Item not found in your branch"}

            item_name, price, stock = item

            if stock < quantity:
                return {"status": "error", "message": "Not enough stock"}

            # CHECK BALANCE
            cursor.execute(
                "SELECT balance FROM users WHERE id = ?",
                (user[0],)
            )
            balance = cursor.fetchone()[0]

            total_cost = price * quantity

            if balance < total_cost:
                return {"status": "error", "message": "Insufficient balance"}

            # UPDATE BALANCE
            new_balance = balance - total_cost
            cursor.execute(
                "UPDATE users SET balance = ? WHERE id = ?",
                (new_balance, user[0])
            )

            # UPDATE STOCK
            new_stock = stock - quantity
            cursor.execute(
                "UPDATE items SET stock = ? WHERE id = ?",
                (new_stock, item_id)
            )

            # LOG TRANSACTION (UPDATED)
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
            INSERT INTO transactions
            (user_id, type, amount, item_name, quantity, timestamp, branch_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                user[0],
                "debit",
                total_cost,
                item_name,
                quantity,
                timestamp,
                user[4]  # branch_id
            ))

        return {
            "status": "success",
            "item": item_name,
            "quantity": quantity,
            "total_cost": total_cost,
            "new_balance": new_balance
        }

    except Exception as e:
        return {
            "status": "error",
            "message": "Purchase failed",
            "details": str(e)
        }
