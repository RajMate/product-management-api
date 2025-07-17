FROM python:3.9-slim

WORKDIR /app

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

# Copy requirements first for better layer caching
COPY requirements.txt .

# Install database drivers and dependencies
RUN pip install --no-cache-dir -r requirements.txt \
    pymysql \
    psycopg2-binary

# Copy the application code
COPY ./src /app/src

# Install curl for health check
RUN apt-get update && \
    apt-get install -y --no-install-recommends curl && \
    rm -rf /var/lib/apt/lists/*

# Create non-root user for security
RUN adduser --disabled-password --gecos "" appuser && \
    chown -R appuser:appuser /app

# Switch to non-root user
USER appuser

# Expose port
EXPOSE 8080

# Health check
HEALTHCHECK --interval=30s --timeout=5s --start-period=30s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Command to run the application
CMD ["python", "-m", "src.main.python.app"]