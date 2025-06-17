# Use an official Python image
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the project files into the container
COPY . /app

# Install dependencies
RUN python3 -m venv venv && \
    . venv/bin/activate && \
    pip install --upgrade pip && \
    pip install -r requirements.txt

# Set PYTHONPATH for the container
ENV PYTHONPATH=/app

# Expose the application port
EXPOSE 8000

# Command to run the application
CMD ["venv/bin/python", "main.py"]