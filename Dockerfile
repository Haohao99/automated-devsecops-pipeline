# =======================================================================
# 🚨 INTENTIONAL SECURITY FLAW #2: OUTDATED BASE IMAGE
# Using an old Python version ensures Trivy finds vulnerabilities (CVEs).
# =======================================================================
FROM python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# Copy dependency mappings and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Expose port 5000 for web traffic
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]