# Use an official Python runtime as a parent image
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install dependencies required by FAISS, networkx, and document loaders
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpoppler-cpp-dev \
    pkg-config \
    python3-dev \
    && rm -rf /var/lib/apt/lists/*

# Install python packages
COPY requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt pydantic-settings

# Copy project
COPY . /app/

# Expose port
EXPOSE 8000

# Command to run the application
CMD ["uvicorn", "api.server:app", "--host", "0.0.0.0", "--port", "8000"]
