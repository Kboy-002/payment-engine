from datetime import datetime  # i need this for my timestamp on the receipt
import random  # Also needed in generating the transaction ID


# Payment logic for purchase, debit and credit
def add(balance, fund):
    return balance + fund


def subtract(balance, item):
    return balance - item


def transfer_credit(balance, credit):
    return balance + credit


def transfer_debit(balance, debit):
    return balance - debit


# Dictionaries for users and items to purchase
user_list = {
    "Kayode": 1000,
    "Kolade": 2000,
    "Korede": 3000,
    "Ayomide": 4000,
    "Funds": 200000
}
items = {
    "bread": 2800,
    "water": 500,
    "butter": 800,
    "juice": 1000,
    "chicken": 3700
}

fund = 0
# Loop for account creation and funding
while True:
    user = input(
        "Hey welcome, what is your name? (input ok to exit): ").capitalize()
    if user.lower() == 'ok':
        break
    if user not in user_list:
        user_list[user] = float(input("What is your account balance? "))
        fund = float(
            input(f"Hey! {user}, how much would you like to fund your account with? "))
    else:
        fund = float(input(
            f"Hey welcome {user}, how much would you like to fund your account with? "))
    if fund <= 0:
        print("Invalid fund amount")
        continue
    answer = input(
        "How would you like to fund your account? (Transfer/Direct Credit) ").lower()
    if answer != 'transfer':
        user_list[user] = add(user_list[user], fund)
        print(f"Your updated account balance is: {user_list[user]}")
    else:
        name = input(
            "Whose account would you like to transfer from? ").capitalize()
        if name not in user_list:
            print(
                f"Sorry this user ({name}) does not have an account with us.")
            continue
        if name.capitalize() == user:
            print(f"You just created an account, you can't self transfer.")
        else:
            if user_list[name] >= fund:
                user_list[name] = transfer_debit(user_list[name], fund)
                print(
                    f"{name} account has been debited with {fund}, and your balance is : {user_list[name]}")
                user_list[user] = transfer_credit(user_list[user], fund)
                print(
                    f"Hey! {user}, your account has been credited with : {fund}")
                print(f"Your updated account balance is: {user_list[user]}")
            else:
                print(f"{name} account balance is Insufficent")
  # Creation of the shopping loop
    total_cost = 0
    receipt = {}
    insufficent = False
    while True:
        item = input(
            f"Hi {user} welcome to Kingsway Store, what would you like to buy? ").lower()
        if item not in items:
            print(f"Oh snap! we're out of {item}.")
            continue
        price = items[item]
        print(f"{item} costs: {price}")
        quantity = int(input(f"How many {item} would you like to purchase? "))
        subtotal = price * quantity
        if user_list[user] >= (total_cost + subtotal):
            total_cost += subtotal
            print(f"Total cost in cart : {total_cost}")
            if item in receipt:
                receipt[item]['qty'] += quantity
                receipt[item]['subtotal'] += subtotal
            else:
                receipt[item] = {
                    "price": price,
                    "qty": quantity,
                    "subtotal": subtotal
                }
        else:
            print("Sorry, your balance is not sufficient to carry on.")
            insufficent = True
            break
        more = input(
            "Would you like to add more items to your cart? (yes/no) ")
        if more.lower() != 'yes':
            break
# creating the checkout sytem and receipt
    if insufficent:
        print(
            f"You can't shop anymore, your balance can't keep up: {user_list[user]}")
        break
    if user_list[user] >= total_cost:
        print(f"Your payment of {total_cost} is successful!")
        timestamp = datetime.now().strftime("%d-%m-%Y  %H:%M:%S")
        trans_id = f"TXN-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{random.randint(1000, 9999)}"
        print("\n-------RECEIPT-------")
        print(f"Date/Time: {timestamp}")
        print(f"Transaction-ID: {trans_id}")
        print("---------------------")
        for item, data in receipt.items():
            print(f"{item} x{data['qty']} - {data['subtotal']}")
        print("---------------------")
        print(f"TOTAL COST: {total_cost}")
        print("---------------------")
        print(f"Thank you for shopping with Kingsway {user}")
        with open("Transaction.txt", "a") as file:
          file.write("\n----- NEW TRANSACTION -----\n")
          file.write(f"Username: {user}\n")
          file.write(f"Transaction ID: {trans_id}\n")
          file.write(f"Date/Time: {timestamp}\n")
          for item, data in receipt.items():
            file.write(f"{item} x{data['qty']} - {data['subtotal']}\n")
          file.write(f"Total Amount: {total_cost}\n")
          file.write(f"---------------------")
        break
