from db_operations import create_user, get_user, update_balance, delete_user, get_all_users

# Create user
create_user("David")
create_user("Sarah")
create_user("Michael")

# Fetch user
user = get_user("David")
print("Before update:", user)

# Update balance
update_balance("David", 5000.0)

# Fetch again
user = get_user("David")
print("After update:", user)

# Delete user
delete_user()
# Fetch again to confirm deletion
user = get_user("David")
print("After deletion:", user)


print("All users:", get_all_users())