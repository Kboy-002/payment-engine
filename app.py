from dotenv import load_dotenv
load_dotenv()  # must be before any imports that use os.getenv

from flask import Flask, request, jsonify
from auth import token_required, role_required, generate_token, verify_password
import db_operations as db
from shop_logic import purchase_item_logic
import os

SECRET_KEY = os.getenv('JWT_SECRET_KEY')
if not SECRET_KEY:
    raise ValueError("JWT_SECRET_KEY must be set in environment")

app = Flask(__name__)

db.initialise_db()


@app.route('/')
def home():
    return "Smart POS API running"


@app.route('/login', methods=['POST'])
def login():
    data = request.json
    name = data.get('name', '').strip().lower()
    password = data.get('password')

    if not name or not password:
        return jsonify({"error": "Name and password required"}), 400

    user = db.get_user_by_name(name)
    if not user:
        return jsonify({"error": "User not found"}), 404

    if not verify_password(password, user['password_hash']):
        return jsonify({"error": "Invalid credentials"}), 401

    token = generate_token(user['id'], user['role'], user['branch_id'])
    return jsonify({
        "message": "Login successful",
        "token": token,
        "user": {
            "id": user['id'],
            "name": user['name'],
            "role": user['role'],
            "branch_id": user['branch_id']
        }
    })


@app.route('/register', methods=['POST'])
def register():
    data = request.json
    name = data.get('name', '').strip().lower()
    password = data.get('password', '').strip()
    branch_id = data.get('branch_id', 1)
    role = data.get('role', 'customer')

    if not name:
        return jsonify({"error": "Name is required"}), 400
    if not password:
        return jsonify({"error": "Password is required"}), 400

    existing = db.get_user_by_name(name)
    if existing:
        return jsonify({"error": "User already exists"}), 409

    db.create_user(name, password, role, branch_id)
    user = db.get_user_by_name(name)

    token = generate_token(user['id'], user['role'], user['branch_id'])
    return jsonify({
        "message": "Registration successful",
        "token": token,
        "user": {
            "id": user['id'],
            "name": user['name'],
            "role": user['role'],
            "branch_id": user['branch_id']
        }
    }), 201


@app.route('/fund', methods=['POST'])
@token_required
def fund_account():
    data = request.json
    amount = data.get("amount")

    if not amount:
        return jsonify({"error": "Amount required"}), 400

    user_id = request.user['user_id']

    try:
        from db_operations import db_connection
        from datetime import datetime

        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT balance FROM users WHERE id = %s", (user_id,))
                row = cur.fetchone()
                if not row:
                    return jsonify({"error": "User not found"}), 404
                current_balance = row[0]

                new_balance = current_balance + float(amount)
                cur.execute("UPDATE users SET balance = %s WHERE id = %s", (new_balance, user_id))

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("""
                    INSERT INTO transactions
                    (user_id, type, amount, item_name, quantity, timestamp, branch_id)
                    VALUES (%s, %s, %s, %s, %s, %s, %s)
                """, (user_id, "credit", amount, "Wallet funding", 0, timestamp, request.user['branch_id']))

        return jsonify({"message": "Funding successful", "new_balance": f"₦{new_balance:,.2f}"})
    except Exception as e:
        return jsonify({"error": "Funding failed", "details": str(e)}), 500


@app.route('/items', methods=['GET'])
def get_items():
    from db_operations import db_connection

    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, price, stock FROM items")
            items = cur.fetchall()

    inventory = [{"id": i[0], "name": i[1], "price": i[2], "stock": i[3]} for i in items]
    return jsonify(inventory)


@app.route('/purchase', methods=['POST'])
@token_required
def purchase():
    data = request.json
    item_id = data.get("item_id")
    quantity = data.get("quantity")

    if not item_id or not quantity:
        return jsonify({"error": "item_id and quantity required"}), 400

    result = purchase_item_logic(
        request.user['user_id'],
        int(item_id),
        int(quantity),
        request.user['branch_id']
    )
    if result["status"] == "success":
        return jsonify(result)
    else:
        return jsonify(result), 400


@app.route('/transactions', methods=['GET'])
@token_required
def get_transactions():
    user_id = request.user['user_id']
    from db_operations import db_connection

    with db_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT type, amount, item_name, quantity, timestamp
                FROM transactions
                WHERE user_id = %s
                ORDER BY id DESC
            """, (user_id,))
            records = cur.fetchall()

    history = [{"type": r[0], "amount": r[1], "item_name": r[2], "quantity": r[3], "timestamp": r[4]} for r in records]
    return jsonify(history)


@app.route('/add-item', methods=['POST'])
@token_required
@role_required('vendor')
def add_item_api():
    data = request.json
    name = data.get("name")
    price = data.get("price")
    stock = data.get("stock")

    if not name or not price or not stock:
        return jsonify({"error": "name, price, stock required"}), 400

    try:
        from db_operations import db_connection
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("""
                    INSERT INTO items (name, price, stock, branch_id)
                    VALUES (%s, %s, %s, %s)
                """, (name, price, stock, request.user['branch_id']))

        return jsonify({"message": "Item added successfully"})
    except Exception as e:
        return jsonify({"error": "Failed to add item", "details": str(e)}), 500


@app.route('/update-item', methods=['PUT'])
@token_required
@role_required('vendor')
def update_item():
    data = request.json
    item_id = data.get("item_id")
    price = data.get("price")
    stock = data.get("stock")

    if not item_id:
        return jsonify({"error": "item_id required"}), 400

    try:
        from db_operations import db_connection
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM items WHERE id = %s", (item_id,))
                if not cur.fetchone():
                    return jsonify({"error": "Item not found"}), 404

                if price is not None:
                    cur.execute("UPDATE items SET price = %s WHERE id = %s", (price, item_id))
                if stock is not None:
                    cur.execute("UPDATE items SET stock = %s WHERE id = %s", (stock, item_id))

        return jsonify({"message": "Item updated successfully"})
    except Exception as e:
        return jsonify({"error": "Update failed", "details": str(e)}), 500


@app.route('/restock-item', methods=['POST'])
@token_required
@role_required('vendor')
def restock_item():
    data = request.json
    item_id = data.get("item_id")
    quantity = data.get("quantity")

    if not item_id or not quantity:
        return jsonify({"error": "item_id and quantity required"}), 400

    try:
        from db_operations import db_connection
        from datetime import datetime

        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name, stock FROM items WHERE id = %s", (item_id,))
                item = cur.fetchone()
                if not item:
                    return jsonify({"error": "Item not found"}), 404

                item_name, current_stock = item
                new_stock = current_stock + int(quantity)

                cur.execute("UPDATE items SET stock = %s WHERE id = %s", (new_stock, item_id))

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                cur.execute("""
                    INSERT INTO restock_logs (item_id, item_name, quantity_added, timestamp)
                    VALUES (%s, %s, %s, %s)
                """, (item_id, item_name, quantity, timestamp))

        return jsonify({
            "message": "Restock successful",
            "item": item_name,
            "added": quantity,
            "new_stock": new_stock
        })
    except Exception as e:
        return jsonify({"error": "Restock failed", "details": str(e)}), 500


@app.route('/delete-item', methods=['DELETE'])
@token_required
@role_required('vendor')
def delete_item():
    data = request.json
    item_id = data.get("item_id")

    if not item_id:
        return jsonify({"error": "item_id required"}), 400

    try:
        from db_operations import db_connection
        with db_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT name FROM items WHERE id = %s", (item_id,))
                item = cur.fetchone()
                if not item:
                    return jsonify({"error": "Item not found"}), 404
                item_name = item[0]

                cur.execute("DELETE FROM items WHERE id = %s", (item_id,))

        return jsonify({"message": "Item deleted successfully", "item_removed": item_name})
    except Exception as e:
        return jsonify({"error": "Delete failed", "details": str(e)}), 500


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