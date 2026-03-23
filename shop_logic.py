from db_operations import db_connection, get_user
from datetime import datetime
import random
from logger import log_event


def shop(user):
    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, price, stock FROM items")
            items = cur.fetchall()

    if not items:
        print("No items available.")
        return

    print("\n---- AVAILABLE ITEMS ----")
    for item in items:
        print(f"{item[0]}. {item[1]} - ₦{item[2]} (Stock: {item[3]})")

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

        if item_id in cart:
            cart[item_id]["qty"] += quantity
        else:
            cart[item_id] = {"name": name, "price": price, "qty": quantity, "stock": stock}

        print(f"{quantity} x {name} added to cart.")

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

    total_cost = sum(item["price"] * item["qty"] for item in cart.values())

    fresh_user = get_user(user[1].lower())  # user[1] is name
    current_balance = fresh_user[3]        # fresh_user[3] is balance

    if current_balance < total_cost:
        print("Insufficient funds.")
        return

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                new_balance = current_balance - total_cost
                cur.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user[0]))

                trans_id = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"
                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                for item_id, item in cart.items():
                    new_stock = item["stock"] - item["qty"]
                    cur.execute("UPDATE items SET stock = %s WHERE id = %s", (new_stock, item_id))

                    branch_id = user[5]  # correct index for branch_id (was user[4] which is role)
                    cur.execute("""
                        INSERT INTO transactions
                        (user_id, type, amount, item_name, quantity, timestamp, branch_id)
                        VALUES (%s, %s, %s, %s, %s, %s, %s)
                    """, (
                        user[0],
                        "debit",
                        item["price"] * item["qty"],
                        item["name"],
                        item["qty"],
                        timestamp,
                        branch_id
                    ))

        log_event("INFO", "Purchase completed", trans_id)

    except Exception as e:
        log_event("ERROR", "Transaction failure", str(e))
        print("Transaction failed. Please try again.")
        return

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

    with open("Transaction.txt 1.0", "a", encoding="utf-8") as ledger:
        ledger.write("\n----- NEW TRANSACTION -----\n")
        ledger.write(f"Username: {user[1]}\n")
        ledger.write(f"Transaction ID: {trans_id}\n")
        ledger.write(f"Date/Time: {timestamp_display}\n")
        for item in cart.values():
            ledger.write(f"{item['name']} x{item['qty']} - ₦{item['price'] * item['qty']}\n")
        ledger.write("------------------\n")
        ledger.write(f"TOTAL: ₦{total_cost}\n")
        ledger.write(f"New Balance: ₦{new_balance}\n")
        ledger.write("------------------\n")


def purchase_item_logic(user_id, item_id, quantity, branch_id):
    from db_operations import db_connection
    from datetime import datetime

    try:
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, price, stock FROM items WHERE id = %s AND branch_id = %s",
                            (item_id, branch_id))
                item = cur.fetchone()
                if not item:
                    return {"status": "error", "message": "Item not found in your branch"}

                item_name, price, stock = item
                if stock < quantity:
                    return {"status": "error", "message": "Not enough stock"}

                cur.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    return {"status": "error", "message": "User not found"}
                balance = row[0]

                total_cost = price * quantity
                if balance < total_cost:
                    return {"status": "error", "message": "Insufficient balance"}

                new_balance = balance - total_cost
                cur.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))

                new_stock = stock - quantity
                cur.execute("UPDATE items SET stock = %s WHERE id = %s", (new_stock, item_id))

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("""
                    INSERT INTO transactions
                    (user_id, type, amount, item_name, quantity, timestamp, branch_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, "debit", total_cost, item_name, quantity, timestamp, branch_id))

        return {
            "status": "success",
            "item": item_name,
            "quantity": quantity,
            "total_cost": total_cost,
            "new_balance": new_balance
        }
    except Exception as e:
        return {"status": "error", "message": "Purchase failed", "details": str(e)}