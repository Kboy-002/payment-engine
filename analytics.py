from db_operations import  db_connection
def sales_report():
    with db_connection() as cursor:
      cursor.execute("""
    SELECT details, amount
    FROM transactions
    WHERE type = 'debit'
    """)

      sales = cursor.fetchall()

    if not sales:
        print("\nNo sales data available.\n")
        return

    sales_data = {}
    total_revenue = 0

    for details, amount in sales:

        try:
            parts = details.split(" x ")

            quantity = int(parts[0].replace("Purchased ", ""))
            item_name = parts[1]

        except:
            continue

        if item_name not in sales_data:
            sales_data[item_name] = 0

        sales_data[item_name] += quantity
        total_revenue += amount

    print("\n------ SALES REPORT ------\n")

    for item, qty in sales_data.items():
        print(f"{item}")
        print(f"Total Sold: {qty}\n")

    print("--------------------------")
    print(f"Total Revenue: ₦{total_revenue}")
    print("--------------------------")
