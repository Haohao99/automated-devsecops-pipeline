from flask import Flask, jsonify, render_template_string
import os

app = Flask(__name__)

# 🚨 INTENTIONAL SECURITY FLAW: HARDCODED SECRETS 
# Your pipeline's Secret Scanner (Gitleaks/TruffleHog) will flag this.
MOCK_DB_PASSWORD = "super_secret_password_123!"
AWS_FAKE_KEY = "AKIAIOSFODNN7EXAMPLE" 

EMPLOYEES = [
    {"id": 1, "name": "Alice Smith", "role": "Cloud Architect", "department": "Engineering"},
    {"id": 2, "name": "Bob Jones", "role": "Security Analyst", "department": "DevSecOps"}
]

@app.route('/')
def home():
    return "<h1>🏢 Corporate Employee Portal (Vulnerable Version Live)</h1>"

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
