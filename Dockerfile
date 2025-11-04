FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for hardware access
RUN apt-get update && apt-get install -y \
    can-utils \
    iproute2 \
    usbutils \
    i2c-tools \
    python3-dev \
    build-essential \
    git \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better caching)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy framework and tests
COPY framework/ ./framework/
COPY tests/ ./tests/
COPY config/ ./config/
COPY run_tests.py .

# Set Python path
ENV PYTHONPATH=/app
ENV PYTHONUNBUFFERED=1

# Create reports directory
RUN mkdir -p /app/reports/allure-results

# Default command runs smoke execution profile
ENTRYPOINT ["python", "run_tests.py"]
CMD ["--exec-profile", "smoke"]
