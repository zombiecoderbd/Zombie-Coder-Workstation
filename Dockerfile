# ZombieCoder Local AI - Dockerfile
# Agent Workstation Layer - "যেখানে কোড ও কথা বলে"

FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONPATH=/app/server
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV LOG_LEVEL=INFO

# Install system dependencies
RUN apt-get update && apt-get install -y \\
    gcc \\
    g++ \\
    git \\
    curl \\
    redis-tools \\
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir --upgrade pip && \\
    pip install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p logs data workspace && \\
    chmod 755 logs data workspace

# Create non-root user for security
RUN useradd -m -u 1000 zombiecoder && \\
    chown -R zombiecoder:zombiecoder /app

USER zombiecoder

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \\
    CMD curl -f http://localhost:8000/api/status || exit 1

# Expose port
EXPOSE 8000

# Start command
CMD ["python", "server/main.py"]