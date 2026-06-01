from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)

# =======================================================================
# 🚨 INTENTIONAL SECURITY FLAW #1: HARDCODED SECRETS 
# Your pipeline's Secret Scanner (Gitleaks/TruffleHog) will flag this.
# =======================================================================
MOCK_DB_PASSWORD = "super_secret_password_123!"
AWS_FAKE_KEY = "AKIAIOSFODNN7EXAMPLE" 

# Simulated Employee Database
EMPLOYEES = [
    {"id": 1, "name": "Alice Smith", "role": "Cloud Architect", "department": "Engineering"},
    {"id": 2, "name": "Bob Jones", "role": "Security Analyst", "department": "DevSecOps"},
    {"id": 3, "name": "Charlie Brown", "role": "Infrastructure Engineer", "department": "Operations"}
]

# Root Route: HTML Web Interface
@app.route('/')
def home():
    html_template = """
    <!#DOCTYPE html>
    <html>
    <head>
        <title>Internal Employee Portal</title>
        <style>
            body { font-family: Arial, sans-serif; margin: 40px; background-color: #f4f6f9; }
            h1 { color: #2c3e50; }
            table { width: 100%; border-collapse: collapse; margin-top: 20px; background: white; }
            th, td { padding: 12px; text-align: left; border-bottom: 1px solid #ddd; }
            th { background-color: #34495e; color: white; }
            .badge { background: #e74c3c; color: white; padding: 5px 10px; border-radius: 4px; font-size: 12px; }
        </style>
    </head>
    <body>
        <h1>🏢 Corporate Employee Portal</h1>
        <p>Status: <span class="badge">Connected to Mock DB</span></p>
        <table>
            <tr>
                <th>ID</th>
                <th>Name</th>
                <th>Role</th>
                <th>Department</th>
            </tr>
            {% for emp in employees %}
            <tr>
                <td>{{ emp.id }}</td>
                <td><strong>{{ emp.name }}</strong></td>
                <td>{{ emp.role }}</td>
                <td>{{ emp.department }}</td>
            </tr>
            {% endfor %}
        </table>
    </body>
    </html>
    """
    return render_template_string(html_template, employees=EMPLOYEES)

# API Route: Returns JSON data
@app.route('/api/v1/employees', methods=['GET'])
def get_employees():
    return jsonify({"status": "success", "data": EMPLOYEES})

if __name__ == '__main__':
    # Run the web application on port 5000
    app.run(host='0.0.0.0', port=5000)