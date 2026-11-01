# ==============================================================
#   ONLINE GAS BOOKING & MANAGEMENT SYSTEM  -  admin.py
#   Everything the admin can do: manage customers, cylinders,
#   bookings, deliveries, payments and reports
# ==============================================================

from helpers import *

def show_customers(rows):
    if len(rows) == 0:
        print("No customers found.")
        return
    line(100)
    print("%-5s %-18s %-11s %-25s %-25s %-12s"
          % ("ID", "Name", "Mobile", "Address", "Email", "Username"))
    line(100)
    for r in rows:
        print("%-5s %-18s %-11s %-25s %-25s %-12s"
              % (r[0], r[1][:18], r[2], r[3][:25], r[4][:25], r[5]))
    line(100)


def view_customers():
    cur.execute("SELECT Customer_ID, Name, Mobile, Address, Email, Username FROM Customers")
    show_customers(cur.fetchall())


def search_customer():
    s = get_text("Enter customer name, mobile or ID: ")
    cur.execute("SELECT Customer_ID, Name, Mobile, Address, Email, Username FROM Customers "
                "WHERE Name LIKE %s OR Mobile = %s OR Customer_ID = %s",
                ("%" + s + "%", s, s))
    show_customers(cur.fetchall())


def modify_customer():
    cid = get_int("Enter Customer ID: ")
    cur.execute("SELECT Name, Mobile, Address, Email FROM Customers WHERE Customer_ID = %s",
                (cid,))
    old = cur.fetchone()
    if old is None:
        print("Customer not found.")
        return
    print("Leave a field blank to keep the old value.")
    name = input("Name [" + old[0] + "]: ").strip() or old[0]
    mobile = input("Mobile [" + old[1] + "]: ").strip() or old[1]
    if len(mobile) != 10 or not mobile.isdigit():
        print("Invalid mobile number, keeping the old one.")
        mobile = old[1]
    address = input("Address [" + old[2] + "]: ").strip() or old[2]
    email = input("Email [" + old[3] + "]: ").strip() or old[3]
    try:
        cur.execute("UPDATE Customers SET Name = %s, Mobile = %s, Address = %s, Email = %s "
                    "WHERE Customer_ID = %s", (name, mobile, address, email, cid))
        con.commit()
        print("Customer updated.")
    except Error:
        print("That mobile number belongs to another customer.")


def delete_customer():
    cid = get_int("Enter Customer ID to delete: ")
    cur.execute("SELECT Name FROM Customers WHERE Customer_ID = %s", (cid,))
    row = cur.fetchone()
    if row is None:
        print("Customer not found.")
        return
    # a customer with a booking still in progress cannot be removed
    cur.execute("SELECT COUNT(*) FROM Bookings WHERE Customer_ID = %s AND "
                "Booking_Status IN ('Pending', 'Approved') AND Delivery_Status <> 'Delivered'",
                (cid,))
    if cur.fetchone()[0] > 0:
        print("This customer has an active booking. Finish or cancel it first.")
        return
    if input("Delete " + row[0] + " and all their old bookings? (y/n): ").lower() != "y":
        return
    # child rows (bookings) must go first because of the foreign key
    cur.execute("DELETE FROM Bookings WHERE Customer_ID = %s", (cid,))
    cur.execute("DELETE FROM Customers WHERE Customer_ID = %s", (cid,))
    con.commit()
    print("Customer deleted.")


def add_cylinder():
    t = get_text("Enter cylinder type (e.g. Domestic 14.2 kg): ")
    s = get_int("Enter opening stock: ")
    try:
        p = float(input("Enter price: "))
    except ValueError:
        print("Invalid price.")
        return
    if s < 0 or p <= 0:
        print("Stock and price must be positive.")
        return
    try:
        cur.execute("INSERT INTO Cylinders(Cylinder_Type, Stock, Price, Last_Updated) "
                    "VALUES(%s, %s, %s, %s)", (t, s, p, date.today()))
        con.commit()
        print("Cylinder added with ID", cur.lastrowid)
    except Error:
        print("This cylinder type already exists.")


def update_cylinder():
    show_cylinders()
    cyl = get_int("Enter Cylinder ID: ")
    cur.execute("SELECT Stock, Price FROM Cylinders WHERE Cylinder_ID = %s", (cyl,))
    row = cur.fetchone()
    if row is None:
        print("No such cylinder.")
        return
    print("1. Add new stock")
    print("2. Change price")
    ch = get_int("Enter your choice: ")
    if ch == 1:
        n = get_int("How many cylinders arrived? ")
        if n <= 0:
            print("Must be more than 0.")
            return
        cur.execute("UPDATE Cylinders SET Stock = Stock + %s, Last_Updated = %s "
                    "WHERE Cylinder_ID = %s", (n, date.today(), cyl))
    elif ch == 2:
        try:
            p = float(input("New price (old Rs. " + str(row[1]) + "): "))
        except ValueError:
            print("Invalid price.")
            return
        if p <= 0:
            print("Price must be positive.")
            return
        cur.execute("UPDATE Cylinders SET Price = %s, Last_Updated = %s WHERE Cylinder_ID = %s",
                    (p, date.today(), cyl))
    else:
        print("Invalid choice.")
        return
    con.commit()
    print("Cylinder updated.")


def view_all_bookings():
    print("1. All bookings")
    print("2. Only pending bookings")
    ch = get_int("Enter your choice: ")
    if ch == 2:
        cur.execute(BOOKING_QUERY + " AND B.Booking_Status = 'Pending' ORDER BY B.Booking_ID")
    else:
        cur.execute(BOOKING_QUERY + " ORDER BY B.Booking_ID")
    show_bookings(cur.fetchall())


def approve_booking():
    bid = get_int("Enter Booking ID: ")
    b = get_booking(bid)
    if b is None:
        print("Booking not found.")
        return
    if b[3] != "Pending":
        print("This booking is already", b[3])
        return
    status = choose("Approve or reject? ", ["Approved", "Rejected"])
    cur.execute("UPDATE Bookings SET Booking_Status = %s WHERE Booking_ID = %s", (status, bid))
    if status == "Rejected":
        return_stock(b[1], b[2])
    con.commit()
    print("Booking", status.lower() + ".")


def update_delivery():
    bid = get_int("Enter Booking ID: ")
    b = get_booking(bid)
    if b is None:
        print("Booking not found.")
        return
    if b[3] != "Approved":
        print("Only approved bookings can be delivered. This one is", b[3])
        return
    if b[4] == "Delivered":
        print("Already delivered.")
        return
    status = choose("New delivery status: ", ["Out for Delivery", "Delivered"])
    cur.execute("UPDATE Bookings SET Delivery_Status = %s WHERE Booking_ID = %s", (status, bid))
    con.commit()
    print("Delivery status updated to", status)


def update_payment():
    bid = get_int("Enter Booking ID: ")
    b = get_booking(bid)
    if b is None:
        print("Booking not found.")
        return
    if b[3] in ("Cancelled", "Rejected"):
        print("This booking was", b[3].lower() + ", no payment needed.")
        return
    status = choose("Payment received by: ", ["Paid - Cash", "Paid - UPI", "Paid - Card", "Unpaid"])
    cur.execute("UPDATE Bookings SET Payment_Status = %s WHERE Booking_ID = %s", (status, bid))
    con.commit()
    print("Payment status updated.")


def delete_cancelled():
    cur.execute("SELECT COUNT(*) FROM Bookings WHERE Booking_Status IN ('Cancelled', 'Rejected')")
    n = cur.fetchone()[0]
    if n == 0:
        print("There are no cancelled or rejected bookings.")
        return
    if input("Delete " + str(n) + " cancelled/rejected bookings? (y/n): ").lower() == "y":
        cur.execute("DELETE FROM Bookings WHERE Booking_Status IN ('Cancelled', 'Rejected')")
        con.commit()
        print(n, "bookings deleted.")


def report():
    print("\n================ BOOKING REPORT ================")
    print("Date:", date.today())
    cur.execute("SELECT COUNT(*) FROM Customers")
    print("Total customers        :", cur.fetchone()[0])
    cur.execute("SELECT Booking_Status, COUNT(*) FROM Bookings GROUP BY Booking_Status")
    for r in cur.fetchall():
        print("%-23s: %s" % (r[0] + " bookings", r[1]))
    cur.execute("SELECT COUNT(*) FROM Bookings WHERE Delivery_Status = 'Delivered'")
    print("Delivered bookings     :", cur.fetchone()[0])

    # money collected = price x quantity of all paid bookings
    cur.execute("""SELECT SUM(Y.Price * B.Quantity) FROM Bookings B, Cylinders Y
                   WHERE B.Cylinder_ID = Y.Cylinder_ID AND B.Payment_Status LIKE 'Paid%'""")
    total = cur.fetchone()[0]
    print("Total amount collected : Rs.", total if total is not None else 0)

    print("\nCylinders sold (approved bookings) by type:")
    cur.execute("""SELECT Y.Cylinder_Type, SUM(B.Quantity) FROM Bookings B, Cylinders Y
                   WHERE B.Cylinder_ID = Y.Cylinder_ID AND B.Booking_Status = 'Approved'
                   GROUP BY Y.Cylinder_Type""")
    rows = cur.fetchall()
    if len(rows) == 0:
        print("  none yet")
    for r in rows:
        print("  %-22s : %s" % (r[0], r[1]))

    cur.execute("SELECT Cylinder_Type, Stock FROM Cylinders WHERE Stock < 10")
    rows = cur.fetchall()
    if len(rows) > 0:
        print("\nLOW STOCK WARNING:")
        for r in rows:
            print("  %-22s : only %s left" % (r[0], r[1]))
    print("================================================")


def admin_login():
    print("\n===== ADMIN LOGIN =====")
    u = input("Username: ").strip()
    p = input("Password: ").strip()
    if u == ADMIN_USER and p == ADMIN_PASS:
        admin_menu()
    else:
        print("Wrong admin username or password.")


def admin_menu():
    while True:
        print("\n----- ADMIN MENU -----")
        print(" 1. View all customers")
        print(" 2. Search customer")
        print(" 3. Modify customer")
        print(" 4. Delete customer")
        print(" 5. View cylinder stock")
        print(" 6. Add new cylinder type")
        print(" 7. Update cylinder stock / price")
        print(" 8. View bookings")
        print(" 9. Approve / reject booking")
        print("10. Update delivery status")
        print("11. Update payment status")
        print("12. Delete cancelled bookings")
        print("13. Booking report")
        print("14. Logout")
        ch = get_int("Enter your choice: ")
        if ch == 1:
            view_customers()
        elif ch == 2:
            search_customer()
        elif ch == 3:
            modify_customer()
        elif ch == 4:
            delete_customer()
        elif ch == 5:
            show_cylinders()
        elif ch == 6:
            add_cylinder()
        elif ch == 7:
            update_cylinder()
        elif ch == 8:
            view_all_bookings()
        elif ch == 9:
            approve_booking()
        elif ch == 10:
            update_delivery()
        elif ch == 11:
            update_payment()
        elif ch == 12:
            delete_cancelled()
        elif ch == 13:
            report()
        elif ch == 14:
            print("Logged out.")
            break
        else:
            print("Invalid choice.")
