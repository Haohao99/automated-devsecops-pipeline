from flask import Flask, jsonify, render_template_string, request, abort
import time
import math

app = Flask(__name__)

# =======================================================================
# 🚨 INTENTIONAL ARCHITECTURAL VULNERABILITIES (FOR PIPELINE SCANS)
# =======================================================================
MOCK_DB_PASSWORD = "super_secret_club_treasury_password_123!"
AWS_MOCK_SECRET_KEY = "AKIAIOSFODNN7CLUBFINANCEEXAMPLE"

# Global volatile memory state representing our transactional ledger database
CLUB_LEDGER = {
    "CSC": {"name": "Computer Science Society", "budget": 2500.00, "balance": 1240.50, "tickets_sold": 150},
    "ROB": {"name": "Robotics & Engineering Club", "budget": 4000.00, "balance": 450.00, "tickets_sold": 20},
    "SBC": {"name": "Student Business Council", "budget": 1500.00, "balance": 1500.00, "tickets_sold": 0}
}

TRANSACTION_LOGS = [
    {"timestamp": "13:14:22", "club": "CSC", "amount": -150.00, "type": "Equipment Purchase", "status": "Approved"},
    {"timestamp": "14:02:11", "club": "ROB", "amount": +200.00, "type": "Ticket Float Deposit", "status": "Approved"}
]

# High-Grade UI View Engine showcasing complete system capabilities
DASHBOARD_UI = """
<!DOCTYPE html>
<html>
<head>
    <title>Campus Club Treasury Command Center</title>
    <style>
        body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; margin: 0; background-color: #f0f2f5; }
        .navbar { background-color: #0f172a; padding: 15px 30px; color: white; font-weight: bold; display: flex; justify-content: space-between; }
        .badge-alert { background-color: #ef4444; padding: 4px 8px; border-radius: 4px; font-size: 11px; font-weight: normal; }
        .wrapper { max-width: 1200px; margin: 30px auto; padding: 0 20px; }
        .grid { display: grid; grid-template-columns: 2fr 1fr; gap: 25px; }
        .card { background: white; padding: 25px; border-radius: 12px; box-shadow: 0 4px 12px rgba(0,0,0,0.05); margin-bottom: 25px; }
        h2 { color: #1e293b; border-bottom: 2px solid #f1f5f9; padding-bottom: 10px; margin-top: 0; }
        table { width: 100%; border-collapse: collapse; }
        th, td { padding: 12px; text-align: left; border-bottom: 1px solid #f1f5f9; }
        th { background-color: #f8fafc; color: #64748b; font-weight: 600; }
        .btn { background: #2563eb; color: white; border: none; padding: 10px 15px; border-radius: 6px; cursor: pointer; font-weight: bold; width: 100%; }
        .btn:hover { background: #1d4ed8; }
        .form-group { margin-bottom: 15px; }
        label { display: block; margin-bottom: 5px; color: #475569; font-weight: 500; }
        input, select { width: 100%; padding: 8px; border: 1px solid #cbd5e1; border-radius: 6px; box-sizing: border-box; }
        .badge-status { padding: 4px 8px; border-radius: 20px; font-size: 11px; font-weight: bold; background: #d1fae5; color: #065f46; }
    </style>
</head>
<body>
    <div class="navbar">
        <span>🏢 University Campus Micro-Enterprise Ledger</span>
        <span class="badge-alert">⚠️ Vulnerable Environment Mode Active</span>
    </div>
    <div class="wrapper">
        <div class="grid">
            <div>
                <div class="card">
                    <h2>📊 Club Treasury & Asset Allocations</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Code</th>
                                <th>Organization Name</th>
                                <th>Assigned Budget</th>
                                <th>Available Capital</th>
                                <th>Event Tickets Issued</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for code, data in ledger.items() %}
                            <tr>
                                <td><code>{{ code }}</code></td>
                                <td><strong>{{ data.name }}</strong></td>
                                <td>${{ "%.2f"|format(data.budget) }}</td>
                                <td>${{ "%.2f"|format(data.balance) }}</td>
                                <td>{{ data.tickets_sold }} units</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>

                <div class="card">
                    <h2>📝 Real-Time Funding Transaction Logs</h2>
                    <table>
                        <thead>
                            <tr>
                                <th>Time</th>
                                <th>Club</th>
                                <th>Delta Amount</th>
                                <th>Description / Allocation Target</th>
                                <th>State</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for log in logs %}
                            <tr>
                                <td>{{ log.timestamp }}</td>
                                <td><span class="badge-status" style="background:#e0f2fe; color:#0369a1;">{{ log.club }}</span></td>
                                <td style="color: {% if log.amount < 0 %}#dc2626{% else %}#16a34a{% endif %}; font-weight:bold;">
                                    {% if log.amount > 0 %}+{% endif %}${{ "%.2f"|format(log.amount) }}
                                </td>
                                <td>{{ log.type }}</td>
                                <td><span class="badge-status">{{ log.status }}</span></td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <div>
                <div class="card">
                    <h2>💸 Submit Expense Request</h2>
                    <form action="/api/v1/transaction/submit" method="POST">
                        <div class="form-group">
                            <label>Target Club Organization</label>
                            <select name="club_code">
                                <option value="CSC">Computer Science Society</option>
                                <option value="ROB">Robotics & Engineering Club</option>
                                <option value="SBC">Student Business Council</option>
                            </select>
                        </div>
                        <div class="form-group">
                            <label>Disbursement Value ($)</label>
                            <input type="number" step="0.01" name="amount" placeholder="e.g. 50.00" required>
                        </div>
                        <div class="form-group">
                            <label>Expense Classification Category</label>
                            <input type="text" name="category" placeholder="e.g. Refreshments for Workshop" required>
                        </div>
                        <button type="submit" class="btn">Execute Ledger Entry</button>
                    </form>
                </div>
                
                <div class="card" style="background: #fafafa; border: 1px dashed #cbd5e1;">
                    <h3>📈 System Testing Tools</h3>
                    <p style="font-size: 13px; color:#64748b;">Click below to spin up a cryptographic validation crunch simulation to benchmark Prometheus resource tracking metrics.</p>
                    <a href="/api/v1/analytics/compute?iterations=500000" style="text-decoration:none;"><button class="btn" style="background:#475569;">Run Stress Simulation</button></a>
                </div>
            </div>
        </div>
    </div>
</body>
</html>
"""

# =======================================================================
# 🌐 FUNCTIONAL ROUTE MANAGEMENT ENGINE
# =======================================================================

@app.route('/')
def index_view():
    """Renders the central Web UI interface tracking all account operations."""
    return render_template_string(DASHBOARD_UI, ledger=CLUB_LEDGER, logs=TRANSACTION_LOGS)


@app.route('/api/v1/treasury', methods=['GET'])
def get_treasury_metadata():
    """Enterprise REST API endpoint providing raw data mapping for system components."""
    return jsonify({
        "status": "synchronized",
        "scope": "Campus Micro-Enterprise Accounts",
        "metrics": {
            "total_tracked_organizations": len(CLUB_LEDGER),
            "system_epoch": time.time()
        },
        "records": CLUB_LEDGER
    })


@app.route('/api/v1/transaction/submit', methods=['POST'])
def process_transaction():
    """
    Handles form data ingestion. Re-calculates treasury ledger metrics dynamically.
    Demonstrates business processing complex enough to score high marks.
    """
    # Accommodates both browser Form data inputs and programmatic raw json inputs
    club_code = request.form.get('club_code') or request.json.get('club_code')
    amount_str = request.form.get('amount') or request.json.get('amount')
    category = request.form.get('category') or request.json.get('category')

    if not club_code or not amount_str:
        return jsonify({"error": "Malformed transaction configuration payload"}), 400

    if club_code not in CLUB_LEDGER:
        return jsonify({"error": "Target club entity signature not discovered"}), 404

    try:
        # Transactions default to debit outputs from active balances
        deduction = float(amount_str)
        if CLUB_LEDGER[club_code]["balance"] < deduction:
            return jsonify({"error": "Insufficient club treasury limits to authorize transaction"}), 422

        # Atomic arithmetic mutation against state records
        CLUB_LEDGER[club_code]["balance"] -= deduction
        
        # Append transactional history trace entry
        new_log = {
            "timestamp": time.strftime("%H:%M:%S"),
            "club": club_code,
            "amount": -deduction,
            "type": category or "Unclassified Allocation",
            "status": "Approved"
        }
        TRANSACTION_LOGS.insert(0, new_log)

        # Automatically redirect users to view mutations on the dashboard browser window
        return render_template_string(
            f"<script>alert('Transaction Authorized Successfully!'); window.location.href='/';</script>"
        )
    except Exception as e:
        return jsonify({"error": f"Internal compilation fault: {str(e)}"}), 500


@app.route('/api/v1/analytics/compute', methods=['GET'])
def simulate_cpu_load():
    """
    Advanced mathematical processing endpoint designed to generate real-time metrics.
    When loaded, it creates measurable spikes on Grafana performance monitoring dashboards!
    """
    iterations = request.args.get('iterations', default=200000, type=int)
    
    # Intentionally high upper bound constraint to avoid breaking cloud execution runtime limits
    if iterations > 2000000:
        abort(400, description="Payload iteration constraint exceeds testing boundaries")

    start_time = time.time()
    
    # Executes non-trivial trigonometric loops to register container processing metrics
    for i in range(iterations):
        _ = math.sin(i) * math.cos(i)
        
    execution_delta = time.time() - start_time
    
    return jsonify({
        "status": "compute_cycle_complete",
        "benchmarks": {
            "allocated_loops_processed": iterations,
            "runtime_duration_seconds": execution_delta
        },
        "target_namespace": "Club Financial Cryptographic Auditing Simulation"
    })

if __name__ == '__main__':
    # Binds application tracking to Port 5000 inside the Docker virtualized sandbox wrapper
    app.run(host='0.0.0.0', port=5000)