Overview: 

Payment Engine is a Python-based simulation of a real-world payment and shopping system.
It models account creation, funding (including credit and peer-to-peer transfers), and an online store experience with cart handling, checkout, receipt generation, and ledger storage.
The system enforces real-world funding rules such as:

No negative funding

No zero-value transfers

Prevention of invalid transactions

Proper debit and credit balance validation

How It Works:

A user enters their name.

If the account exists, the system proceeds.

If the account does not exist, a new account is created.

The user funds their account.

The user proceeds to the store.

Items can be added to cart.

On checkout:
Balance validation is performed.
A receipt is generated.
A transaction ID and timestamp are attached.
The transaction is stored in a ledger.

Features:

Account creation and management

Account funding with validation rules

Debit and credit handling

Peer-to-peer transfer logic

Cart system with quantity handling

Checkout system

Receipt generation with:
Transaction ID,
Timestamp,
Persistent ledger logging.

How to Run:

Clone the repository or download the source code.

Open the project in your Python environment.

Run the main file.

What I Learned:

Building this project helped me connect real-world payment experiences with system design thinking.
I learned how to:

Translate real-world financial rules into program logic.

Design validation systems that prevent improper transactions.

Structure code to simulate real application flows.

Generate receipts and maintain transaction records.

Think like both a user and a system designer.

This project strengthened my understanding of control flow, data structures, and building practical systems from scratch.
