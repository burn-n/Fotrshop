# Use lightweight Python image
FROM python:3.11-slim

# Prevent Python from buffering logs (important for Railway logs)
ENV PYTHONUNBUFFERED=1

# Set working directory
WORKDIR /app

# Install system dependencies (minimal, but safe)
RUN apt-get update && apt-get install -y \
    gcc \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Copy only requirements first (better caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the project
COPY . .

# Optional: ensure username.txt exists (prevents crash)
RUN touch username.txt

# Run your script
CMD ["python", "script.py"]
