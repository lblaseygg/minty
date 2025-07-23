# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
ENV FLASK_APP=backend/app.py
ENV FLASK_ENV=production

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    default-libmysqlclient-dev \
    pkg-config \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Upgrade pip and setuptools
RUN pip install --upgrade pip setuptools wheel

# Copy requirements first for better caching
COPY requirements.txt /app/

# Install Python dependencies with error handling
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt || \
    (echo "Failed to install requirements, trying individual packages..." && \
     pip install --no-cache-dir Flask==2.3.3 Flask-CORS==4.0.0 Flask-JWT-Extended==4.5.3 Flask-SQLAlchemy==3.0.5 SQLAlchemy==2.0.21 PyMySQL==1.1.0 scikit-learn==1.3.0 XGBoost==1.7.6 pandas==2.0.3 numpy==1.24.3 yfinance==0.2.18 requests==2.31.0 python-dotenv==1.0.0 gunicorn==21.2.0)

# Copy project
COPY . /app/

# Create a non-root user
RUN adduser --disabled-password --gecos '' appuser
RUN chown -R appuser:appuser /app
USER appuser

# Expose port
EXPOSE 5001

# Run the application
CMD ["python", "backend/app.py"]