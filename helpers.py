# ==============================================================
#   ONLINE GAS BOOKING & MANAGEMENT SYSTEM  -  helpers.py
#   Settings, database connection, table setup and the small
#   functions used by both customer.py and admin.py
# ==============================================================

import mysql.connector
from mysql.connector import Error
from datetime import date

# ---------- connection settings (change if your MySQL is different) ----------
HOST = "localhost"
USER = "root"
PASSWD = "root"
PORT = 3306
DB_NAME = "GasBookingDB"

# ---------- admin login ----------
ADMIN_USER = "admin"
ADMIN_PASS = "admin123"

MAX_QTY = 2          # a customer can book at most 2 cylinders at a time

con = None
cur = None


# ==============================================================
#                    DATABASE SETUP
# ==============================================================

def connect():
    """Connects to MySQL, creates the database and tables if needed."""
    global con, cur
    con = mysql.connector.connect(host=HOST, user=USER, passwd=PASSWD, port=PORT)
    cur = con.cursor(buffered=True)
    cur.execute("CREATE DATABASE IF NOT EXISTS " + DB_NAME)
    cur.execute("USE " + DB_NAME)

    cur.execute("""CREATE TABLE IF NOT EXISTS Customers(
                    Customer_ID INT PRIMARY KEY AUTO_INCREMENT,
                    Name VARCHAR(50) NOT NULL,
                    Mobile CHAR(10) NOT NULL UNIQUE,
                    Address VARCHAR(100) NOT NULL,
                    Email VARCHAR(50),
                    Username VARCHAR(30) NOT NULL UNIQUE,
                    Password VARCHAR(30) NOT NULL)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS Cylinders(
                    Cylinder_ID INT PRIMARY KEY AUTO_INCREMENT,
                    Cylinder_Type VARCHAR(30) NOT NULL UNIQUE,
                    Stock INT NOT NULL CHECK (Stock >= 0),
                    Price DECIMAL(8,2) NOT NULL,
                    Last_Updated DATE)""")

    cur.execute("""CREATE TABLE IF NOT EXISTS Bookings(
                    Booking_ID INT PRIMARY KEY AUTO_INCREMENT,
                    Customer_ID INT NOT NULL,
                    Cylinder_ID INT NOT NULL,
                    Booking_Date DATE NOT NULL,
                    Quantity INT NOT NULL,
                    Booking_Status VARCHAR(15) DEFAULT 'Pending',
                    Delivery_Status VARCHAR(20) DEFAULT 'Not Assigned',
                    Payment_Status VARCHAR(20) DEFAULT 'Unpaid',
                    FOREIGN KEY (Customer_ID) REFERENCES Customers(Customer_ID),
                    FOREIGN KEY (Cylinder_ID) REFERENCES Cylinders(Cylinder_ID))""")

    # add some starting stock the first time the program runs
    cur.execute("SELECT COUNT(*) FROM Cylinders")
    if cur.fetchone()[0] == 0:
        data = [("Domestic 14.2 kg", 50, 853.00),
                ("Domestic 5 kg", 30, 318.50),
                ("Commercial 19 kg", 20, 1691.50)]
        for t, s, p in data:
            cur.execute("INSERT INTO Cylinders(Cylinder_Type, Stock, Price, Last_Updated) "
                        "VALUES(%s, %s, %s, %s)", (t, s, p, date.today()))
        con.commit()


# ==============================================================
#                    HELPER FUNCTIONS
# ==============================================================

def line(n=70):
    print("-" * n)


def get_int(msg):
    """Keeps asking until the user types a whole number."""
    while True:
        try:
            return int(input(msg))
        except ValueError:
            print("Please enter a valid number.")


def get_mobile():
    while True:
        m = input("Enter 10 digit mobile number: ").strip()
        if len(m) == 10 and m.isdigit():
            return m
        print("Invalid mobile number.")


def get_text(msg):
    """Does not allow an empty answer."""
    while True:
        s = input(msg).strip()
        if s != "":
            return s
        print("This field cannot be empty.")


def choose(msg, options):
    """Shows a numbered list of options and returns the one picked."""
    for i in range(len(options)):
        print(i + 1, ".", options[i])
    while True:
        ch = get_int(msg)
        if 1 <= ch <= len(options):
            return options[ch - 1]
        print("Invalid choice.")


def show_cylinders():
    cur.execute("SELECT * FROM Cylinders")
    rows = cur.fetchall()
    line()
    print("%-5s %-22s %-8s %-10s %-12s" % ("ID", "Type", "Stock", "Price", "Updated"))
    line()
    for r in rows:
        print("%-5s %-22s %-8s %-10s %-12s" % (r[0], r[1], r[2], r[3], r[4]))
    line()


def show_bookings(rows):
    if len(rows) == 0:
        print("No bookings found.")
        return
    line(100)
    print("%-5s %-15s %-20s %-11s %-4s %-10s %-17s %-12s"
          % ("ID", "Customer", "Cylinder", "Date", "Qty", "Status", "Delivery", "Payment"))
    line(100)
    for r in rows:
        print("%-5s %-15s %-20s %-11s %-4s %-10s %-17s %-12s"
              % (r[0], r[1][:15], r[2][:20], r[3], r[4], r[5], r[6], r[7]))
    line(100)


# all booking queries join the three tables so names are shown instead of IDs
BOOKING_QUERY = """SELECT B.Booking_ID, C.Name, Y.Cylinder_Type, B.Booking_Date,
                          B.Quantity, B.Booking_Status, B.Delivery_Status, B.Payment_Status
                   FROM Bookings B, Customers C, Cylinders Y
                   WHERE B.Customer_ID = C.Customer_ID AND B.Cylinder_ID = Y.Cylinder_ID"""


def get_booking(bid):
    """Returns (Customer_ID, Cylinder_ID, Quantity, Booking_Status, Delivery_Status,
    Payment_Status) of a booking, or None if it does not exist."""
    cur.execute("SELECT Customer_ID, Cylinder_ID, Quantity, Booking_Status, "
                "Delivery_Status, Payment_Status FROM Bookings WHERE Booking_ID = %s", (bid,))
    return cur.fetchone()


def return_stock(cyl_id, qty):
    """Puts cylinders back into stock when a booking is cancelled or rejected."""
    cur.execute("UPDATE Cylinders SET Stock = Stock + %s, Last_Updated = %s "
                "WHERE Cylinder_ID = %s", (qty, date.today(), cyl_id))



# connect as soon as this file is imported, so customer.py and
# admin.py get a ready connection when they do "from helpers import *"
try:
    connect()
except Error as e:
    print("Could not connect to MySQL:", e)
    print("Check that MySQL is running and the password in helpers.py is correct.")
