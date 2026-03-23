def sales_report(branch_id=None):
    from db_operations import db_connection

    with db_connection() as conn:
        with conn.cursor() as cur:
            query = """
                SELECT item_name, quantity, amount
                FROM transactions
                WHERE type = 'debit'
            """
            params = []

            if branch_id is not None:
                branch_str = str(branch_id).strip()
                if branch_str.upper() != "ALL":
                    try:
                        branch_int = int(branch_str)
                        query += " AND branch_id = %s"
                        params.append(branch_int)
                    except ValueError:
                        return {"message": "Invalid branch_id"}

            cur.execute(query, params)
            rows = cur.fetchall()

            if not rows:
                return {"message": "No sales data available"}

            total_revenue = 0
            total_items_sold = 0
            product_sales = {}

            for item_name, quantity, amount in rows:
                total_revenue += amount
                total_items_sold += quantity

                if item_name in product_sales:
                    product_sales[item_name] += quantity
                else:
                    product_sales[item_name] = quantity

            top_item = max(product_sales, key=product_sales.get)
            top_quantity = product_sales[top_item]

            return {
                "branch_id": branch_id if branch_id else "ALL",
                "total_revenue": total_revenue,
                "total_items_sold": total_items_sold,
                "total_transactions": len(rows),
                "top_selling_item": top_item,
                "top_selling_quantity": top_quantity
            }


def display_sales_report(branch_id=None):
    report = sales_report(branch_id)

    if "message" in report:
        print("\n" + report["message"] + "\n")
        return

    print("\n----- SALES REPORT -----")
    print(f"Branch: {report['branch_id']}")
    print(f"Total Revenue: ₦{report['total_revenue']:.2f}")
    print(f"Total Items Sold: {report['total_items_sold']}")
    print(f"Total Transactions: {report['total_transactions']}")
    print(f"Top Selling Item: {report['top_selling_item']} ({report['top_selling_quantity']})")
    print("-------------------------\n")