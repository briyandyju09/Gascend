from helpers import *
from customer import register, customer_login
from admin import admin_login

def main():
    if con is None:
        return

    while True:
        print("\n" + "=" * 45)
        print("   ONLINE GAS BOOKING & MANAGEMENT SYSTEM")
        print("=" * 45)
        print("1. New customer registration")
        print("2. Customer login")
        print("3. Admin login")
        print("4. Exit")
        ch = get_int("Enter your choice: ")
        try:
            if ch == 1:
                register()
            elif ch == 2:
                customer_login()
            elif ch == 3:
                admin_login()
            elif ch == 4:
                print("Thank you for using the system!")
                break
            else:
                print("Invalid choice.")
        except Error as e:
            con.rollback()
            print("Database error:", e)

    con.close()


main()
