# ==============================================================
#   ONLINE GAS BOOKING & MANAGEMENT SYSTEM  -  customer.py
#   Everything a customer can do: register, login, book,
#   track, cancel and update profile
# ==============================================================

from helpers import *

def register():
    print("\n===== NEW CUSTOMER REGISTRATION =====")
    name = get_text("Enter name: ")
    mobile = get_mobile()
    address = get_text("Enter address: ")
    email = input("Enter email (optional): ").strip()
    if email != "" and ("@" not in email or "." not in email):
        print("Invalid email, it will be left blank.")
        email = ""
    username = get_text("Choose a username: ")
    password = get_text("Choose a password (min 4 characters): ")
    if len(password) < 4:
        print("Password too short. Registration cancelled.")
        return

    cur.execute("SELECT * FROM Customers WHERE Username = %s OR Mobile = %s", (username, mobile))
    if cur.fetchone() is not None:
        print("Username or mobile number already registered.")
        return

    cur.execute("INSERT INTO Customers(Name, Mobile, Address, Email, Username, Password) "
                "VALUES(%s, %s, %s, %s, %s, %s)",
                (name, mobile, address, email, username, password))
    con.commit()
    print("Registration successful! Your Customer ID is", cur.lastrowid)


def customer_login():
    print("\n===== CUSTOMER LOGIN =====")
    u = input("Username: ").strip()
    p = input("Password: ").strip()
    cur.execute("SELECT Customer_ID, Name FROM Customers WHERE Username = %s AND Password = %s",
                (u, p))
    row = cur.fetchone()
    if row is None:
        print("Wrong username or password.")
    else:
        print("Welcome,", row[1] + "!")
        customer_menu(row[0])


def book_cylinder(cid):
    print("\n===== BOOK A CYLINDER =====")
    # only one active booking is allowed at a time
    cur.execute("SELECT COUNT(*) FROM Bookings WHERE Customer_ID = %s AND "
                "Booking_Status IN ('Pending', 'Approved') AND Delivery_Status <> 'Delivered'",
                (cid,))
    if cur.fetchone()[0] > 0:
        print("You already have a booking that is not delivered yet.")
        return

    show_cylinders()
    cyl = get_int("Enter Cylinder ID: ")
    cur.execute("SELECT Cylinder_Type, Stock, Price FROM Cylinders WHERE Cylinder_ID = %s", (cyl,))
    row = cur.fetchone()
    if row is None:
        print("No such cylinder.")
        return

    qty = get_int("Enter quantity (max " + str(MAX_QTY) + "): ")
    if qty < 1 or qty > MAX_QTY:
        print("Quantity must be between 1 and", MAX_QTY)
        return
    if qty > row[1]:
        print("Sorry, only", row[1], "cylinders are in stock.")
        return

    try:
        cur.execute("INSERT INTO Bookings(Customer_ID, Cylinder_ID, Booking_Date, Quantity) "
                    "VALUES(%s, %s, %s, %s)", (cid, cyl, date.today(), qty))
        bid = cur.lastrowid
        # reduce stock straight away so the same cylinders are not booked twice
        cur.execute("UPDATE Cylinders SET Stock = Stock - %s, Last_Updated = %s "
                    "WHERE Cylinder_ID = %s", (qty, date.today(), cyl))
        con.commit()
    except Error as e:
        con.rollback()
        print("Booking failed:", e)
        return
    print("Booking successful! Booking ID:", bid)
    print("Amount to pay: Rs.", row[2] * qty)


def my_bookings(cid):
    cur.execute(BOOKING_QUERY + " AND B.Customer_ID = %s ORDER BY B.Booking_ID DESC", (cid,))
    show_bookings(cur.fetchall())


def track_booking(cid):
    bid = get_int("Enter Booking ID: ")
    cur.execute(BOOKING_QUERY + " AND B.Booking_ID = %s AND B.Customer_ID = %s", (bid, cid))
    row = cur.fetchone()
    if row is None:
        print("No such booking in your account.")
        return
    print("\nBooking ID      :", row[0])
    print("Cylinder        :", row[2])
    print("Booked on       :", row[3])
    print("Quantity        :", row[4])
    print("Booking status  :", row[5])
    print("Delivery status :", row[6])
    print("Payment status  :", row[7])


def cancel_booking(cid):
    bid = get_int("Enter Booking ID to cancel: ")
    b = get_booking(bid)
    if b is None or b[0] != cid:
        print("No such booking in your account.")
    elif b[3] != "Pending":
        print("Only pending bookings can be cancelled. This one is", b[3])
    else:
        cur.execute("UPDATE Bookings SET Booking_Status = 'Cancelled' WHERE Booking_ID = %s",
                    (bid,))
        return_stock(b[1], b[2])
        con.commit()
        print("Booking cancelled.")


def update_profile(cid):
    print("\nLeave a field blank to keep the old value.")
    cur.execute("SELECT Address, Email, Password FROM Customers WHERE Customer_ID = %s", (cid,))
    old = cur.fetchone()
    address = input("New address: ").strip() or old[0]
    email = input("New email: ").strip() or old[1]
    password = input("New password: ").strip() or old[2]
    cur.execute("UPDATE Customers SET Address = %s, Email = %s, Password = %s "
                "WHERE Customer_ID = %s", (address, email, password, cid))
    con.commit()
    print("Profile updated.")


def customer_menu(cid):
    while True:
        print("\n----- CUSTOMER MENU -----")
        print("1. Book a cylinder")
        print("2. View cylinder availability")
        print("3. My booking history")
        print("4. Track a booking")
        print("5. Cancel a booking")
        print("6. Update my profile")
        print("7. Logout")
        ch = get_int("Enter your choice: ")
        if ch == 1:
            book_cylinder(cid)
        elif ch == 2:
            show_cylinders()
        elif ch == 3:
            my_bookings(cid)
        elif ch == 4:
            track_booking(cid)
        elif ch == 5:
            cancel_booking(cid)
        elif ch == 6:
            update_profile(cid)
        elif ch == 7:
            print("Logged out.")
            break
        else:
            print("Invalid choice.")
