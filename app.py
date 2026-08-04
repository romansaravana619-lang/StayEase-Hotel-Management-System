from flask import Flask, render_template, request, redirect, url_for, flash, session 
import sqlite3
import os
from datetime import datetime
app = Flask(__name__)
app.secret_key = "stayease123"

def save_bill(customer, room, checkin, checkout, amount):

    if not os.path.exists("bills"):
        os.makedirs("bills")

    invoice_no = datetime.now().strftime("%Y%m%d%H%M%S")

    filename = f"bills/{invoice_no}.txt"

    with open(filename, "w", encoding="utf-8") as f:

        f.write("=================================\n")
        f.write("        StayEase Hotel\n")
        f.write("=================================\n\n")

        f.write(f"Invoice No : {invoice_no}\n")
        f.write(f"Customer   : {customer}\n")
        f.write(f"Room No    : {room}\n")
        f.write(f"Check In   : {checkin}\n")
        f.write(f"Check Out  : {checkout}\n")
        f.write(f"Amount     : Rs.{amount}\n")

        f.write("\n")
        f.write("Thank You For Staying With Us.\n")

    return invoice_no

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():

    if "logged_in" in session:
        flash("Room booked successfully!")
        return redirect(url_for("dashboard"))
    
    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        if username == "admin" and password == "12345":

            session["logged_in"] = True
            session["username"] = username

            return redirect(url_for("dashboard"))

        else:
            return render_template(
                "login.html",
                error="Invalid Username or Password"
            )

    return render_template("login.html")

@app.route("/dashboard")
def dashboard():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM rooms")
    total_rooms = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status='Available'")
    available_rooms = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM rooms WHERE status='Occupied'")
    occupied_rooms = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM bookings")
    total_bookings = cursor.fetchone()[0]

    conn.close()

    return render_template(
        "dashboard.html",
        total_rooms=total_rooms,
        available_rooms=available_rooms,
        occupied_rooms=occupied_rooms,
        total_bookings=total_bookings
    )

@app.route("/booking", methods=["GET", "POST"])
def booking():

    if "logged_in" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Load available rooms
    cursor.execute("""
        SELECT room_number
        FROM rooms
        WHERE status='Available'
        ORDER BY room_number
    """)
    available_rooms = cursor.fetchall()

    if request.method == "POST":

        customer_name = request.form["customer_name"]
        phone = request.form["phone"]
        email = request.form["email"]
        aadhar = request.form["aadhar"]
        checkin = request.form["checkin"]
        checkout = request.form["checkout"]
        room_number = request.form["room_number"]
        guests = request.form["guests"]
        address = request.form["address"]

        # Get room type from rooms table
        cursor.execute(
            "SELECT room_type FROM rooms WHERE room_number=?",
            (room_number,)
        )
        room = cursor.fetchone()
        room_type = room["room_type"]

        # Save booking
        cursor.execute("""
            INSERT INTO bookings
            (
                customer_name,
                phone,
                email,
                aadhar,
                checkin,
                checkout,
                room_number,
                room_type,
                guests,
                address
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            customer_name,
            phone,
            email,
            aadhar,
            checkin,
            checkout,
            room_number,
            room_type,
            guests,
            address
        ))

        # Update room status
        cursor.execute(
            "UPDATE rooms SET status='Occupied' WHERE room_number=?",
            (room_number,)
        )

        conn.commit()
        conn.close()

        return redirect(url_for("dashboard"))

    conn.close()

    return render_template(
        "booking.html",
        available_rooms=available_rooms
    )
@app.route("/billing")
def billing():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT
            id,
            customer_name,
            room_number,
            room_type
        FROM bookings
        ORDER BY id DESC
    """)

    bookings = cursor.fetchall()

    conn.close()

    return render_template(
        "billing.html",
        bookings=bookings
    )

@app.route("/billing-history")
def billing_history():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM billing
        ORDER BY id DESC
    """)

    bills = cursor.fetchall()

    conn.close()

    return render_template(
        "billing_history.html",
        bills=bills
    )

@app.route("/generate_bill/<int:id>")
def generate_bill(id):

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    cursor.execute("""
        SELECT *
        FROM bookings
        WHERE id=?
    """, (id,))

    booking = cursor.fetchone()

    cursor.execute("""
        SELECT price
        FROM rooms
        WHERE room_number=?
    """, (booking["room_number"],))

    room = cursor.fetchone()

    price = room["price"]

    # ✅ Save Invoice
    invoice = save_bill(
        booking["customer_name"],
        booking["room_number"],
        booking["checkin"],
        booking["checkout"],
        price
    )

    conn.close()

    return render_template(
        "generate_bill.html",
        booking=booking,
        price=price,
        invoice=invoice
    )

@app.route("/checkout/<int:id>", methods=["POST"])
def checkout(id):
    days = int(request.form["days"])
    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    # Booking details
    cursor.execute(
        "SELECT * FROM bookings WHERE id=?",
        (id,)
    )
    
    booking = cursor.fetchone()

    cursor.execute(
    "SELECT price FROM rooms WHERE room_number=?",
    (booking["room_number"],)
)

    room = cursor.fetchone()

    price = room["price"]

    total = price * days

    if booking:

        room_number = booking["room_number"]

        # Room available again
        cursor.execute(
            "UPDATE rooms SET status='Available' WHERE room_number=?",
            (room_number,)
        )

        cursor.execute("""
INSERT INTO billing
(
    booking_id,
    customer_name,
    room_number,
    room_type,
    price,
    days,
    total,
    bill_date
)
VALUES (?, ?, ?, ?, ?, ?, ?, ?)
""",
(
    booking["id"],
    booking["customer_name"],
    booking["room_number"],
    booking["room_type"],
    price,
    days,
    total,
    datetime.now().strftime("%d-%m-%Y %H:%M")
))

        # Delete booking
        cursor.execute(
            "DELETE FROM bookings WHERE id=?",
            (id,)
        )

        conn.commit()

    conn.close()

    flash("Customer checked out successfully!")

    return redirect(url_for("billing"))

@app.route("/bookings")
def bookings():

    if "logged_in" not in session:
        return redirect(url_for("login"))
    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row

    cursor = conn.cursor()

    cursor.execute("SELECT * FROM bookings")

    booking_list = cursor.fetchall()

    conn.close()

    return render_template(
        "bookings.html",
        bookings=booking_list
    )
@app.route("/delete_booking/<int:id>")
def delete_booking(id):

    conn = sqlite3.connect("stayease.db")
    cursor = conn.cursor()

    cursor.execute(
    "SELECT room_number FROM bookings WHERE id=?",
    (id,)
    )

    room = cursor.fetchone()

    if room:
        cursor.execute(
        "UPDATE rooms SET status='Available' WHERE room_number=?",
        (room[0],)
    )
    cursor.execute("DELETE FROM bookings WHERE id = ?", (id,))

    conn.commit()
    conn.close()
    flash("Booking deleted successfully!")

    return redirect(url_for("bookings"))

@app.route("/edit_booking/<int:id>", methods=["GET", "POST"])
def edit_booking(id):

    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":

        cursor.execute("""
        UPDATE bookings
        SET customer_name=?,
            phone=?,
            email=?,
            aadhar=?,
            checkin=?,
            checkout=?,
            room_type=?,
            guests=?,
            address=?
        WHERE id=?
        """, (

            request.form["customer_name"],
            request.form["phone"],
            request.form["email"],
            request.form["aadhar"],
            request.form["checkin"],
            request.form["checkout"],
            request.form["room_type"],
            request.form["guests"],
            request.form["address"],
            id

        ))

        conn.commit()
        conn.close()

        return redirect("/bookings")

    cursor.execute("SELECT * FROM bookings WHERE id=?", (id,))
    booking = cursor.fetchone()

    conn.close()

    return render_template("edit_booking.html", booking=booking)
@app.route("/rooms", methods=["GET", "POST"])
def rooms():

    if "logged_in" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("stayease.db")
    conn.row_factory = sqlite3.Row
    cursor = conn.cursor()

    if request.method == "POST":

        room_number = request.form["room_number"]
        room_type = request.form["room_type"]
        price = request.form["price"]

        cursor.execute("""
        INSERT INTO rooms
        (room_number, room_type, price, status)
        VALUES (?, ?, ?, ?)
        """, (room_number, room_type, price, "Available"))

        conn.commit()
        flash("Room added successfully!")

    cursor.execute("SELECT * FROM rooms")
    rooms = cursor.fetchall()

    conn.close()

    return render_template("rooms.html", rooms=rooms)
@app.route("/delete_room/<int:id>")
def delete_room(id):

    conn = sqlite3.connect("stayease.db")
    cursor = conn.cursor()

    cursor.execute("DELETE FROM rooms WHERE id=?", (id,))

    conn.commit()
    conn.close()
    flash("Room deleted successfully!")
    return redirect(url_for("rooms"))


@app.route("/logout")
def logout():

    session.clear()

    flash("Logged out successfully!")

    return redirect(url_for("home"))

@app.errorhandler(404)
def page_not_found(error):

    return render_template("404.html"), 404

if __name__ == "__main__":
    app.run(debug=True)