from datetime import datetime
import random


def add(balance, fund):
    return balance + fund


def subtract(balance, item):
    return balance - item


def transfer_credit(balance, amount):
    return balance + amount


def transfer_debit(balance, amount):
    return balance - amount


user_list = {
    "Shawn": 1000.0,
    "Aisha": 2000.0,
    "Ofe": 3000.0,
    "Grace": 4000.0
}

items = {
    "bread": 1800.0,
    "cashew": 750.0,
    "juice": 1200.0,
    "meat pie": 850,
    "chicken": 3600
}

fund = 0

while True:
    user = input("Welcome, what is your name? (Yes to tap out) ").capitalize()
    if user.lower() == 'yes':
        break
    if user not in user_list:
        user_list[user] = float(input("What is your balance? "))
        print(f"Your balance is : {user_list[user]}")
    else:
        print(f"Hey! {user}, Welcome. ")
    answer = input(
        "Would you like to fund your account via a transfer or direct credit? ").lower()
    if answer != 'transfer':
        fund = float(input("How much would you like to fund with? "))
        user_list[user] = add(user_list[user], fund)
        print(f"Your updated account balance is : {user_list[user]}")
    else:
        account_name = input(
            "Whose account do you want to transfer from? ").capitalize()
        if account_name not in user_list:
            print(
                f"Sorry, {account_name} does not have an existing account with us.")
            continue
        if account_name == user:
            print(f"You cannot transfer from your own account {user}")
            continue
        else:
            amount = float(input("How much would you like to transfer? "))
        if amount <= 0:
            print("Invalid transfer amount")
            continue
        if user_list[account_name] >= amount:
            user_list[account_name] = transfer_debit(
                user_list[account_name], amount)
            print(
                f"The sum of {amount} has been moved from {account_name} and the updated balance is: {user_list[account_name]}")
            user_list[user] = transfer_credit(user_list[user], amount)
            print(
                f"{user}! Your account has been credited with {amount}, your updated balance is: {user_list[user]}")
        else:
            print(
                f"{account_name} does not have sufficient funds, account balance: {user_list[account_name]}")
    total_cost = 0
    receipt = {}
    insufficient = False
    while True:
        item = input("What item would you like to purchase? ").lower()
        if item not in items:
            print(f"Sorry we are out of {item}")
            continue
        price = items[item]
        quantity = int(input(f"How many {item} would you like to buy? "))
        subtotal = price * quantity
        if user_list[user] < (subtotal + total_cost):
            print("Insuffient funds for this item.")
            insufficient = True
            break
        total_cost += subtotal
        if item in receipt:
            receipt[item]["qty"] += quantity
            receipt[item]["subtotal"] += subtotal
        else:
            receipt[item] = {
                "price": price,
                "qty": quantity,
                "subtotal": subtotal
            }
        print(f"{item} has been added. Costs: {price}")
        print(f"Total price in cart: {total_cost}")
        more = input(
            "Would you like to add more to your cart? (yes/no) ").lower()
        if more != 'yes':
            break

    if insufficient:
        print("Checkout is cancled because of insuffient balance. ")
        continue
    print(f"Checkout total is {total_cost}")
    if user_list[user] >= total_cost:
        user_list[user] = subtract(user_list[user], total_cost)
        print(f"Purchase successful, your balance is : {user_list[user]}")
        timestamp = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
        txn_id = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000,9999)}"
        print("\n------ RECEIPT ------")
        print(f"Date/Time : {timestamp}")
        print(f"TRANSACTION ID: {txn_id}")
        print("---------------------")
        for item, details in receipt.items():
            print(
                f"{item.capitalize()} x{details['qty']}  -  {details['subtotal']}")
        print("---------------------")
        print(f"TOTAL: {total_cost}")
        print(f"Thank you for shopping with us {user}!")
        break
print(user_list)
