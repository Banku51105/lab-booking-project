from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3
import os

app = Flask(__name__)
app.secret_key = "secret_key_for_session"

# Database setup
def init_db():
    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT UNIQUE,
                    password TEXT
                )''')
    c.execute('''CREATE TABLE IF NOT EXISTS bookings (
                    booking_id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id TEXT,
                    equipment TEXT,
                    date TEXT,
                    time TEXT,
                    status TEXT
                )''')
    conn.commit()
    conn.close()

# Home route
@app.route("/")
def welcome():
    return render_template("welcome.html")

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        try:
            c.execute("INSERT INTO users (user_id, password) VALUES (?, ?)", (user_id, password))
            conn.commit()
            conn.close()
            return redirect(url_for("login"))
        except sqlite3.IntegrityError:
            conn.close()
            return "User ID already exists!"
    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        user_id = request.form["user_id"]
        password = request.form["password"]

        conn = sqlite3.connect("database.db")
        c = conn.cursor()
        c.execute("SELECT * FROM users WHERE user_id = ? AND password = ?", (user_id, password))
        user = c.fetchone()
        conn.close()

        if user:
            session["user_id"] = user_id
            return redirect(url_for("home"))
        else:
            return "Invalid credentials!"
    return render_template("login.html")

# Home page after login
@app.route("/home")
def home():
    if "user_id" not in session:
        return redirect(url_for("login"))
    return render_template("home.html", user_id=session["user_id"])

# Equipment data (you can replace with real names/images later)
equipment_list = [
    {"id": 1, "name": "Equipment 1", "price": 1000, "image": "images/e1.jpg"},
    {"id": 2, "name": "Equipment 2", "price": 2000, "image": "images/e2.jpg"},
    {"id": 3, "name": "Equipment 3", "price": 1500, "image": "images/e3.jpg"},
    {"id": 4, "name": "Equipment 4", "price": 1200, "image": "images/e4.jpg"},
    {"id": 5, "name": "Equipment 5", "price": 1800, "image": "images/e5.jpg"}
]

@app.route("/book")
def book():
    return render_template("booking.html", equipment_list=equipment_list)

@app.route("/book/<int:equipment_id>")
def book_equipment(equipment_id):
    equipment = next((item for item in equipment_list if item["id"] == equipment_id), None)
    if not equipment:
        return "Equipment not found", 404
    return render_template("book_equipment.html", equipment=equipment)

@app.route("/confirm_booking/<int:equipment_id>", methods=["POST"])
def confirm_booking(equipment_id):
    equipment = next((item for item in equipment_list if item["id"] == equipment_id), None)
    if not equipment:
        return "Equipment not found", 404

    address = request.form["address"]
    user_id = session.get("user_id")

    # Save booking in plain text
    with open("bookings.txt", "a") as f:
        f.write(f"{user_id},{equipment['name']},{equipment['price']},{address}\n")

    return render_template("booking_confirmation.html")

# Booking history
@app.route("/booking_history")
def booking_history():
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("SELECT * FROM bookings WHERE user_id = ?", (session["user_id"],))
    bookings = c.fetchall()
    conn.close()

    return render_template("booking_history.html", bookings=bookings)

# Cancel booking
@app.route("/cancel/<int:booking_id>")
def cancel(booking_id):
    if "user_id" not in session:
        return redirect(url_for("login"))

    conn = sqlite3.connect("database.db")
    c = conn.cursor()
    c.execute("UPDATE bookings SET status = 'Cancelled' WHERE booking_id = ? AND user_id = ?", (booking_id, session["user_id"]))
    conn.commit()
    conn.close()

    return redirect(url_for("booking_history"))

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("welcome"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
