from flask import Flask, render_template_string, request, redirect, url_for, session
import pymysql
import os
from datetime import datetime

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "change_this_secret_key")

DB_HOST = os.getenv("DB_HOST")
DB_USER = os.getenv("DB_USER", "admin")
DB_PASSWORD = os.getenv("DB_PASSWORD")
DB_NAME = os.getenv("DB_NAME", "campus_ledger")


def get_db():
    return pymysql.connect(
        host=DB_HOST,
        user=DB_USER,
        password=DB_PASSWORD,
        database=DB_NAME,
        cursorclass=pymysql.cursors.DictCursor,
        autocommit=False
    )


def init_db():
    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS clubs (
            id INT AUTO_INCREMENT PRIMARY KEY,
            code VARCHAR(20) UNIQUE NOT NULL,
            name VARCHAR(255) NOT NULL,
            budget DECIMAL(10,2) NOT NULL,
            balance DECIMAL(10,2) NOT NULL,
            tickets_sold INT DEFAULT 0
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INT AUTO_INCREMENT PRIMARY KEY,
            club_code VARCHAR(20) NOT NULL,
            amount DECIMAL(10,2) NOT NULL,
            category VARCHAR(255) NOT NULL,
            status VARCHAR(50) DEFAULT 'Pending',
            created_at VARCHAR(50) NOT NULL
        )
    """)

    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(100) UNIQUE NOT NULL,
            password VARCHAR(100) NOT NULL,
            role VARCHAR(50) NOT NULL
        )
    """)

    cur.execute("SELECT COUNT(*) AS count FROM clubs")
    if cur.fetchone()["count"] == 0:
        cur.executemany("""
            INSERT INTO clubs (code, name, budget, balance, tickets_sold)
            VALUES (%s, %s, %s, %s, %s)
        """, [
            ("CSC", "Computer Science Society", 2500.00, 1240.50, 150),
            ("ROB", "Robotics & Engineering Club", 4000.00, 450.00, 20),
            ("SBC", "Student Business Council", 1500.00, 1500.00, 0)
        ])

    cur.execute("SELECT COUNT(*) AS count FROM users")
    if cur.fetchone()["count"] == 0:
        cur.executemany("""
            INSERT INTO users (username, password, role)
            VALUES (%s, %s, %s)
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
        input, select { width: 100%; padding: 8px; margin: 6px 0 12px; box-sizing: border-box; }
        button { background: #2563eb; color:white; border:0; padding:10px 14px; border-radius:6px; cursor:pointer; }
        .danger { background:#dc2626; }
        .success { background:#16a34a; }
        .grid { display:grid; grid-template-columns: 2fr 1fr; gap:20px; }
        .msg { background:#fef3c7; padding:10px; border-radius:6px; margin-bottom:15px; }
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

    {% if message %}
    <div class="msg">{{ message }}</div>
    {% endif %}

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
        input { width:100%; padding:10px; margin:8px 0 15px; box-sizing: border-box; }
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


@app.route("/")
def dashboard():
    if not login_required():
        return redirect(url_for("login"))

    message = request.args.get("message")

    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clubs ORDER BY id ASC")
    clubs = cur.fetchall()
    cur.execute("SELECT * FROM transactions ORDER BY id DESC")
    transactions = cur.fetchall()
    conn.close()

    return render_template_string(UI, clubs=clubs, transactions=transactions, message=message)


@app.route("/login", methods=["GET", "POST"])
def login():
    error = None

    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        conn = get_db()
        cur = conn.cursor()
        cur.execute(
            "SELECT * FROM users WHERE username=%s AND password=%s",
            (username, password)
        )
        user = cur.fetchone()
        conn.close()

        if user:
            session["username"] = user["username"]
            session["role"] = user["role"]
            return redirect(url_for("dashboard"))

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
    category = request.form["category"].strip()

    if amount <= 0:
        return redirect(url_for("dashboard", message="Amount must be more than 0."))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("""
        INSERT INTO transactions (club_code, amount, category, status, created_at)
        VALUES (%s, %s, %s, 'Pending', %s)
    """, (club_code, amount, category, datetime.now().strftime("%Y-%m-%d %H:%M:%S")))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard", message="Expense request submitted successfully."))


@app.route("/approve/<int:tx_id>")
def approve_transaction(tx_id):
    if not login_required() or session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM transactions WHERE id=%s", (tx_id,))
    tx = cur.fetchone()

    if tx and tx["status"] == "Pending":
        cur.execute("SELECT * FROM clubs WHERE code=%s", (tx["club_code"],))
        club = cur.fetchone()

        if club and float(club["balance"]) >= float(tx["amount"]):
            new_balance = float(club["balance"]) - float(tx["amount"])

            cur.execute("UPDATE clubs SET balance=%s WHERE code=%s", (new_balance, tx["club_code"]))
            cur.execute("UPDATE transactions SET status='Approved' WHERE id=%s", (tx_id,))
            message = "Transaction approved."
        else:
            cur.execute("UPDATE transactions SET status='Rejected' WHERE id=%s", (tx_id,))
            message = "Transaction rejected due to insufficient balance."

        conn.commit()
    else:
        message = "Transaction not found or already processed."

    conn.close()
    return redirect(url_for("dashboard", message=message))


@app.route("/reject/<int:tx_id>")
def reject_transaction(tx_id):
    if not login_required() or session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    conn = get_db()
    cur = conn.cursor()
    cur.execute("UPDATE transactions SET status='Rejected' WHERE id=%s", (tx_id,))
    conn.commit()
    conn.close()

    return redirect(url_for("dashboard", message="Transaction rejected."))


@app.route("/add_club", methods=["POST"])
def add_club():
    if not login_required() or session.get("role") != "admin":
        return redirect(url_for("dashboard"))

    code = request.form["code"].upper().strip()
    name = request.form["name"].strip()
    budget = float(request.form["budget"])

    if budget <= 0:
        return redirect(url_for("dashboard", message="Budget must be more than 0."))

    conn = get_db()
    cur = conn.cursor()

    cur.execute("SELECT * FROM clubs WHERE code=%s", (code,))
    existing = cur.fetchone()

    if existing:
        conn.close()
        return redirect(url_for("dashboard", message="Club code already exists. Use another code."))

    cur.execute("""
        INSERT INTO clubs (code, name, budget, balance, tickets_sold)
        VALUES (%s, %s, %s, %s, 0)
    """, (code, name, budget, budget))

    conn.commit()
    conn.close()

    return redirect(url_for("dashboard", message="Club added successfully."))


@app.route("/api/v1/treasury")
def treasury_api():
    conn = get_db()
    cur = conn.cursor()
    cur.execute("SELECT * FROM clubs ORDER BY id ASC")
    clubs = cur.fetchall()
    conn.close()

    return {"status": "success", "records": clubs}


if __name__ == "__main__":
    init_db()
    app.run(host="0.0.0.0", port=5000, debug=True)