from flask import Flask, render_template_string, request, redirect, url_for, session
import sqlite3
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = "change_this_secret_key"
DB_NAME = "campus_ledger.db"


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            code TEXT UNIQUE NOT NULL,
            name TEXT NOT NULL,
            budget REAL NOT NULL,
            balance REAL NOT NULL,
            tickets_sold INTEGER DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            club_code TEXT NOT NULL,
            amount REAL NOT NULL,
            category TEXT NOT NULL,
            status TEXT DEFAULT 'Pending',
            created_at TEXT NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) FROM clubs")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO clubs (code, name, budget, balance, tickets_sold)
            VALUES (?, ?, ?, ?, ?)
        """, [
            ("CSC", "Computer Science Society", 2500.00, 1240.50, 150),
            ("ROB", "Robotics & Engineering Club", 4000.00, 450.00, 20),
            ("SBC", "Student Business Council", 1500.00, 1500.00, 0)
        ])

    cur.execute("SELECT COUNT(*) FROM users")
    if cur.fetchone()[0] == 0:
        cur.executemany("""
            INSERT INTO users (username, password, role)
            VALUES (?, ?, ?)
        """, [
            ("admin", "admin123", "admin"),
            ("treasurer", "club123", "treasurer")
        ])

    conn.commit()
    conn.close()


UI = """
<!DOCTYPE html>
<html>
<head>
    <title>Campus Club Treasury System</title>
    <style>
        body { font-family: Arial; margin: 0; background: #f4f6f8; }
        .nav { background: #0f172a; color: white; padding: 15px 30px; display:flex; justify-content:space-between; }
        .container { width: 90%; margin: 30px auto; }
        .card { background: white; padding: 20px; border-radius: 10px; margin-bottom: 20px; box-shadow: 0 2px 8px #ddd; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align:left; }
        th { background: #f1f5f9; }
        input, select { width: 100%; padding: 8px; margin: 6px 0 12px; }
        button { background: #2563eb; color:white; border:0; padding:10px 14px; border-radius:6px; cursor:pointer; }
        .danger { background:#dc2626; }
        .success { background:#16a34a; }
        .grid { display:grid; grid-template-columns: 2fr 1fr; gap:20px; }
    </style>
</head>
<body>
<div class="nav">
    <b>Campus Club Treasury System</b>
    <span>
        Logged in as: {{ session.get("username") }} |
        Role: {{ session.get("role") }} |
        <a href="/logout" style="color:white;">Logout</a>
    </span>
</div>

<div class="container">
    <div class="grid">
        <div>
            <div class="card">
                <h2>Club Treasury</h2>
                <table>
                    <tr>
                        <th>Code</th><th>Name</th><th>Budget</th><th>Balance</th><th>Tickets Sold</th>
                    </tr>
                    {% for club in clubs %}
                    <tr>
                        <td>{{ club.code }}</td>
                        <td>{{ club.name }}</td>
                        <td>${{ "%.2f"|format(club.budget) }}</td>
                        <td>${{ "%.2f"|format(club.balance) }}</td>
                        <td>{{ club.tickets_sold }}</td>
                    </tr>
                    {% endfor %}
                </table>
            </div>

            <div class="card">
                <h2>Transaction History</h2>
                <table>
                    <tr>
                        <th>ID</th><th>Club</th><th>Amount</th><th>Category</th><th>Status</th><th>Date</th><th>Action</th>
                    </tr>
                    {% for tx in transactions %}
                    <tr>
                        <td>{{ tx.id }}</td>
                        <td>{{ tx.club_code }}</td>
                        <td>${{ "%.2f"|format(tx.amount) }}</td>
                        <td>{{ tx.category }}</td>
                        <td>{{ tx.status }}</td>
                        <td>{{ tx.created_at }}</td>
                        <td>
                            {% if session.get("role") == "admin" and tx.status == "Pending" %}
                            <a href="/approve/{{ tx.id }}"><button class="success">Approve</button></a>
                            <a href="/reject/{{ tx.id }}"><button class="danger">Reject</button></a>
                            {% else %}
                            -
                            {% endif %}
                        </td>
                    </tr>
                    {% endfor %}
                </table>
            </div>
        </div>

        <div>
            <div class="card">
                <h2>Submit Expense Request</h2>
                <form method="POST" action="/submit">
                    <label>Club</label>
                    <select name="club_code">
                        {% for club in clubs %}
                        <option value="{{ club.code }}">{{ club.name }}</option>
                        {% endfor %}
                    </select>

                    <label>Amount</label>
                    <input type="number" step="0.01" name="amount" required>

                    <label>Category</label>
                    <input type="text" name="category" required>

                    <button type="submit">Submit Request</button>
                </form>
            </div>

            {% if session.get("role") == "admin" %}
            <div class="card">
                <h2>Add New Club</h2>
                <form method="POST" action="/add_club">
                    <label>Club Code</label>
                    <input type="text" name="code" required>

                    <label>Club Name</label>
                    <input type="text" name="name" required>

                    <label>Budget</label>
                    <input type="number" step="0.01" name="budget" required>

                    <button type="submit">Add Club</button>
                </form>
            </div>
            {% endif %}
        </div>
    </div>
</div>
</body>
</html>
"""


LOGIN_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>Login</title>
    <style>
        body { font-family: Arial; background:#f4f6f8; }
        .box { width:350px; margin:100px auto; background:white; padding:25px; border-radius:10px; box-shadow:0 2px 8px #ddd; }
        input { width:100%; padding:10px; margin:8px 0 15px; }
        button { width:100%; background:#2563eb; color:white; border:0; padding:10px; border-radius:6px; }
    </style>
</head>
<body>
<div class="box">
    <h2>Campus Ledger Login</h2>
    <p><b>Admin:</b> admin / admin123</p>
    <p><b>Treasurer:</b> treasurer / club123</p>

    {% if error %}
    <p style="color:red;">{{ error }}</p>
    {% endif %}

    <form method="POST">
        <label>Username</label>
        <input type="text" name="username" required>

        <label>Password</label>
        <input type="password" name="password" required>

        <button type="submit">Login</button>
    </form>
</div>
</body>
</html>
"""


def login_required():
    return "username" in session


@app.route("/", methods=["GET"])
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    conn = get_db()
    clubs = conn.execute("SELECT * FROM clubs").fetchall()
    transactions = conn.execute("SELECT * FROM transactions ORDER BY id DESC").fetchall()
    conn.close()

    return render_template_string(UI, clubs=clubs, transactions=transactions)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        user = conn.execute(
            "SELECT * FROM users WHERE username=? AND password=?",
            (username, password)
        ).fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"

    return render_template_string(LOGIN_UI, error=error)


@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))


@app.route("/submit", methods=["POST"])
def submit_transaction():
    if not login_required():
        return redirect(url_for("login"))

    club_code = request.form["club_code"]
    amount = float(request.form["amount"])
    category = request.form["category"]

    conn = get_db()
    conn.execute("""
        INSERT INTO transactions (club_code, amount, category, status, created_at)
        VALUES (?, ?, ?, 'Pending', ?)
    """, (club_code, amount, category, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/approve/<int:tx_id>")
def approve_transaction(tx_id):
    if not login_required() or session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db()
    tx = conn.execute("SELECT * FROM transactions WHERE id=?", (tx_id,)).fetchone()

    if tx and tx["status"] == "Pending":
        club = conn.execute("SELECT * FROM clubs WHERE code=?", (tx["club_code"],)).fetchone()

        if club and club["balance"] >= tx["amount"]:
            new_balance = club["balance"] - tx["amount"]

            conn.execute("UPDATE clubs SET balance=? WHERE code=?", (new_balance, tx["club_code"]))
            conn.execute("UPDATE transactions SET status='Approved' WHERE id=?", (tx_id,))
        else:
            conn.execute("UPDATE transactions SET status='Rejected' WHERE id=?", (tx_id,))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/reject/<int:tx_id>")
def reject_transaction(tx_id):
    if not login_required() or session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db()
    conn.execute("UPDATE transactions SET status='Rejected' WHERE id=?", (tx_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/add_club", methods=["POST"])
def add_club():
    if not login_required() or session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    code = request.form["code"].upper()
    name = request.form["name"]
    budget = float(request.form["budget"])

    conn = get_db()
    conn.execute("""
        INSERT INTO clubs (code, name, budget, balance, tickets_sold)
        VALUES (?, ?, ?, ?, 0)
    """, (code, name, budget, budget))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard"))


@app.route("/api/v1/treasury")
def treasury_api():
    conn = get_db()
    clubs = conn.execute("SELECT * FROM clubs").fetchall()
    conn.close()

    data = [dict(club) for club in clubs]
    return {"status": "success", "records": data}


if __name__ == "__main__":
    if not os.path.exists(DB_NAME):
        init_db()
    else:
        init_db()

    app.run(host="0.0.0.0", port=5000, debug=True)