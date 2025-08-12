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
    {"id": 1, "name": "Microscope", "price": 2999, "image": "images/Microscope.jpeg"},
    {"id": 2, "name": "Magnifier", "price": 899, "image": "images/Magnifier.jpeg"},
    {"id": 3, "name": "Safety Glasses", "price": 599, "image": "images/Glasses.jpeg"},
    {"id": 4, "name": "Beaker", "price": 399, "image": "images/Beaker.jpeg"},
    {"id": 5, "name": "Coat", "price": 1499, "image": "images/Coat.jpeg"}
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
    address = request.form["address"]
    equipment_name = request.form["equipment_name"]
    equipment_price = request.form["equipment_price"]

    # Optional: store image for history
    equipment = next((eq for eq in equipment_list if eq["id"] == equipment_id), None)
    equipment_image = equipment["image"] if equipment else ""

    # Save booking in file
    with open("booking.txt", "a") as f:
        f.write(f"{equipment_name},{equipment_price},{address},{equipment_image},Active\n")

    return render_template("booking_confirmation.html")

@app.route("/history")
def history():
    bookings = []
    try:
        with open("booking.txt", "r") as f:
            for line in f:
                parts = line.strip().split(",")
                if len(parts) >= 4:
                    bookings.append({
                        "name": parts[0],
                        "price": parts[1],
                        "address": parts[2],
                        "image": parts[3],
                        "status": parts[4] if len(parts) > 4 else "Active"
                    })
    except FileNotFoundError:
        pass

    return render_template("booking_history.html", bookings=bookings)

@app.route("/cancel_booking/<int:booking_index>", methods=["POST"])
def cancel_booking(booking_index):
    try:
        with open("booking.txt", "r") as f:
            lines = f.readlines()

        if 0 <= booking_index < len(lines):
            parts = lines[booking_index].strip().split(",")
            if len(parts) < 5:
                parts.append("Active")  # If no status, default to Active

            parts[4] = "Canceled"  # Mark status as canceled
            lines[booking_index] = ",".join(parts) + "\n"

        with open("booking.txt", "w") as f:
            f.writelines(lines)

    except FileNotFoundError:
        pass

    return redirect(url_for("history"))

# Logout
@app.route("/logout")
def logout():
    session.pop("user_id", None)
    return redirect(url_for("welcome"))

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
