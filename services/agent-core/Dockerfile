# ---- Base Stage ----
# Use an official Python runtime as a parent image.
# Using python:3.11-slim as it's a smaller image.
FROM python:3.11-slim as base

# Set environment variables
# PYTHONDONTWRITEBYTECODE: Prevents Python from writing .pyc files to disc.
# PYTHONUNBUFFERED: Prevents Python from buffering stdout and stderr.
ENV PYTHONDONTWRITEBYTECODE 1
ENV PYTHONUNBUFFERED 1

# Set the working directory in the container
WORKDIR /app

# ---- Builder Stage ----
# This stage is for installing dependencies
FROM base as builder

# Install build dependencies if any (e.g., for compiling certain Python packages)
# RUN apt-get update && apt-get install -y build-essential

# Copy the dependencies file and install them
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# ---- Final Stage ----
# This is the final image that will be deployed
FROM base as final

# Copy the installed dependencies from the builder stage
COPY --from=builder /usr/local/lib/python3.11/site-packages /usr/local/lib/python3.11/site-packages
COPY --from=builder /usr/local/bin /usr/local/bin

# Copy the application code
COPY main.py .

# Expose the port the app runs on
EXPOSE 8080

# Command to run the application using uvicorn
CMD uvicorn main:app --host 0.0.0.0 --port $PORT