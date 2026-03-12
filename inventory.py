from db_operations import db_connection
from datetime import datetime

# INVENTORY MANAGEMENT FUNCTIONS


def view_inventory():
    """Fetches and prints all items in the inventory."""

    with db_connection() as cursor:
        cursor.execute("SELECT id, name, price, stock FROM items")
        items = cursor.fetchall()

    if not items:
        print("\nNo items in inventory.\n")
    else:
        print("\n--- INVENTORY ---")
        for item in items:
            print(f"ID: {item[0]} | {item[1]} | Price: ₦{item[2]} | Stock: {item[3]}")
        print("----------------\n")


def add_item(name, price, stock):
    """Adds a new item or increases stock if item exists."""

    try:
        with db_connection() as cursor:

            # CHECK IF ITEM EXISTS
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

    except Exception as e:
        print(f"Failed to add item: {e}")


def update_item(item_id, name=None, price=None, stock=None):
    """Updates item details and logs restock events."""

    try:
        with db_connection() as cursor:

            cursor.execute(
                "SELECT name, price, stock FROM items WHERE id = ?",
                (item_id,)
            )

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

            print("Item updated successfully.")

    except Exception as e:
        print(f"Update failed: {e}")


def delete_item(item_id):
    """Deletes an item from the inventory."""

    try:
        with db_connection() as cursor:

            cursor.execute("DELETE FROM items WHERE id = ?", (item_id,))

            print(f"Item ID {item_id} deleted successfully.")

    except Exception as e:
        print(f"Failed to delete item: {e}")


def low_stock_alert(threshold=5):
    """Displays items whose stock is below the threshold."""

    with db_connection() as cursor:

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