FROM python:3.12-slim

# Install compilers (Keep this, needed for uvloop/pandas)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Use the root requirements.txt for a complete environment
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy everything from the root context
COPY . .

# Run uvicorn pointing to the backend module
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000", "--loop", "uvloop"]