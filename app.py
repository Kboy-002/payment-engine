from flask import Flask, request, jsonify
from db_operations import get_user, create_user, initialise_db

app = Flask(__name__)

# make sure database tables exist
initialise_db()


@app.route('/')
def home():
    return "Smart POS API running"


@app.route('/login', methods=['POST'])
def login():

    data = request.json
    name = data.get('name', '').strip().lower()

    if not name:
        return jsonify({"error": "Name is required"}), 400

    user = get_user(name)

    if user:

        return jsonify({
            "message": f"Welcome back {name}!",
            "user": {
                "id": user[0],
                "name": user[1],
                "balance": user[2],
                "role": user[3]
            }
        })

    else:

        create_user(name, "customer")
        user = get_user(name)

        return jsonify({
            "message": "Account created successfully.",
            "user": {
                "id": user[0],
                "name": user[1],
                "balance": user[2]
            }
        })


@app.route('/fund', methods=['POST'])
def fund_account():

    data = request.json
    name = data.get("name")
    amount = data.get("amount")

    if not name or not amount:
        return jsonify({"error": "Name and amount required"}), 400

    user = get_user(name.lower())

    if not user:
        return jsonify({"error": "User not found"}), 404

    try:

        from db_operations import db_connection
        from datetime import datetime

        with db_connection() as cursor:

            cursor.execute(
                "SELECT balance FROM users WHERE id = ?",
                (user[0],)
            )

            current_balance = cursor.fetchone()[0]

            new_balance = current_balance + float(amount)

            cursor.execute(
                "UPDATE users SET balance = ? WHERE id = ?",
                (new_balance, user[0])
            )

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
                "Wallet funding"
            ))

        return jsonify({
            "message": "Funding successful",
            "new_balance": new_balance
        })

    except Exception as e:

        return jsonify({
            "error": "Funding failed",
            "details": str(e)
        }), 500


@app.route('/items', methods=['GET'])
def get_items():

    from db_operations import db_connection

    with db_connection() as cursor:

        cursor.execute("""
        SELECT id, name, price, stock FROM items
        """)

        items = cursor.fetchall()

    inventory = []

    for item in items:

        inventory.append({
            "id": item[0],
            "name": item[1],
            "price": item[2],
            "stock": item[3]
        })

    return jsonify(inventory)


from shop_logic import purchase_item_logic

@app.route('/purchase', methods=['POST'])
def purchase():

    data = request.json

    name = data.get("name")
    item_id = data.get("item_id")
    quantity = data.get("quantity")

    if not name or not item_id or not quantity:
        return jsonify({"error": "name, item_id and quantity required"}), 400

    result = purchase_item_logic(name, int(item_id), int(quantity))

    if result["status"] == "success":
        return jsonify(result)
    else:
        return jsonify(result), 400

@app.route('/transactions', methods=['GET'])
def get_transactions():

    name = request.args.get("name")

    if not name:
        return jsonify({"error": "User name required"}), 400

    from db_operations import db_connection, get_user

    user = get_user(name.lower())

    if not user:
        return jsonify({"error": "User not found"}), 404

    with db_connection() as cursor:

        cursor.execute("""
        SELECT type, amount, timestamp, details
        FROM transactions
        WHERE user_id = ?
        ORDER BY id DESC
        """, (user[0],))

        records = cursor.fetchall()

    history = []

    for r in records:

        history.append({
            "type": r[0],
            "amount": r[1],
            "timestamp": r[2],
            "details": r[3]
        })

    return jsonify(history)


@app.route('/add-item', methods=['POST'])
def add_item_api():

    data = request.json

    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")
    username = data.get("user")

    if not name or not price or not stock or not username:
        return jsonify({"error": "name, price, stock and user required"}), 400

    from db_operations import db_connection, get_user

    user = get_user(username.lower())

    if not user:
        return jsonify({"error": "User not found"}), 404

    # RBAC CHECK
    if user[3] != "vendor":
        return jsonify({"error": "Only vendors can add items"}), 403

    try:

        with db_connection() as cursor:

            cursor.execute("""
            INSERT INTO items (name, price, stock)
            VALUES (?, ?, ?)
            """, (name, price, stock))

        return jsonify({
            "message": "Item added successfully"
        })

    except Exception as e:

        return jsonify({
            "error": "Failed to add item",
            "details": str(e)
        }), 500

@app.route('/update-item', methods=['PUT'])
def update_item():

    data = request.json

    username = data.get("user")
    item_id = data.get("item_id")
    price = data.get("price")
    stock = data.get("stock")

    if not username or not item_id:
        return jsonify({"error": "user and item_id required"}), 400

    from db_operations import db_connection, get_user

    user = get_user(username.lower())

    if not user:
        return jsonify({"error": "User not found"}), 404

    # RBAC check
    if user[3] != "vendor":
        return jsonify({"error": "Only vendors can update items"}), 403

    try:

        with db_connection() as cursor:

            # Check item exists
            cursor.execute(
                "SELECT name FROM items WHERE id = ?",
                (item_id,)
            )

            item = cursor.fetchone()

            if not item:
                return jsonify({"error": "Item not found"}), 404

            # Update price if provided
            if price is not None:

                cursor.execute(
                    "UPDATE items SET price = ? WHERE id = ?",
                    (price, item_id)
                )

            # Update stock if provided
            if stock is not None:

                cursor.execute(
                    "UPDATE items SET stock = ? WHERE id = ?",
                    (stock, item_id)
                )

        return jsonify({
            "message": "Item updated successfully"
        })

    except Exception as e:

        return jsonify({
            "error": "Update failed",
            "details": str(e)
        }), 500

@app.route('/restock-item', methods=['POST'])
def restock_item():

    data = request.json

    username = data.get("user")
    item_id = data.get("item_id")
    quantity = data.get("quantity")

    if not username or not item_id or not quantity:
        return jsonify({"error": "user, item_id and quantity required"}), 400

    from db_operations import db_connection, get_user
    from datetime import datetime

    user = get_user(username.lower())

    if not user:
        return jsonify({"error": "User not found"}), 404

    # RBAC check
    if user[3] != "vendor":
        return jsonify({"error": "Only vendors can restock items"}), 403

    try:

        with db_connection() as cursor:

            # Get item info
            cursor.execute(
                "SELECT name, stock FROM items WHERE id = ?",
                (item_id,)
            )

            item = cursor.fetchone()

            if not item:
                return jsonify({"error": "Item not found"}), 404

            item_name, current_stock = item

            new_stock = current_stock + int(quantity)

            # Update stock
            cursor.execute(
                "UPDATE items SET stock = ? WHERE id = ?",
                (new_stock, item_id)
            )

            # Log restock
            timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

            cursor.execute("""
            INSERT INTO restock_logs
            (item_id, item_name, quantity_added, timestamp)
            VALUES (?, ?, ?, ?)
            """, (
                item_id,
                item_name,
                quantity,
                timestamp
            ))

        return jsonify({
            "message": "Restock successful",
            "item": item_name,
            "added": quantity,
            "new_stock": new_stock
        })

    except Exception as e:

        return jsonify({
            "error": "Restock failed",
            "details": str(e)
        }), 500


@app.route('/delete-item', methods=['DELETE'])
def delete_item():

    data = request.json

    username = data.get("user")
    item_id = data.get("item_id")

    if not username or not item_id:
        return jsonify({"error": "user and item_id required"}), 400

    from db_operations import db_connection, get_user

    user = get_user(username.lower())

    if not user:
        return jsonify({"error": "User not found"}), 404

    # RBAC check
    if user[3] != "vendor":
        return jsonify({"error": "Only vendors can delete items"}), 403

    try:

        with db_connection() as cursor:

            # check item exists
            cursor.execute(
                "SELECT name FROM items WHERE id = ?",
                (item_id,)
            )

            item = cursor.fetchone()

            if not item:
                return jsonify({"error": "Item not found"}), 404

            item_name = item[0]

            # delete item
            cursor.execute(
                "DELETE FROM items WHERE id = ?",
                (item_id,)
            )

        return jsonify({
            "message": "Item deleted successfully",
            "item_removed": item_name
        })

    except Exception as e:

        return jsonify({
            "error": "Delete failed",
            "details": str(e)
        }), 500

@app.route('/sales-report', methods=['GET'])
def get_sales_report():
    from analytics import sales_report
    branch_id = request.args.get('branch_id')

    if branch_id:
        branch_id = int(branch_id)

    report = sales_report(branch_id)

    return jsonify(report)

if __name__ == '__main__':
    app.run(debug=True)

