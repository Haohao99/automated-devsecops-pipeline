# Use the unpatched base image so Trivy still catches base CVEs if scanning image vulnerabilities later,
# but let's fix the configuration misconfiguration it complained about!
FROM python:3.9-slim-buster

# Set the working directory inside the container
WORKDIR /app

# =======================================================================
# ✅ DEVSECOPS FIX: Create a non-root user for security compliance
# =======================================================================
RUN useradd -u 10001 appuser && chown -R appuser:appuser /app

# Copy dependency mappings and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code
COPY . .

# Ensure the non-root user owns the copied application files
RUN chown -R appuser:appuser /app

# 🚨 Switch the active container user away from root to our limited user
USER appuser

# Expose port 5000 for web traffic
EXPOSE 5000

# Command to run the application
CMD ["python", "main.py"]
