# Use an official Python runtime as a parent image that is compatible with Raspberry Pi (ARM architecture)
# python:3.10-slim-bullseye is a good choice for ARMv7/ARM64.
FROM python:3.10-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install any needed packages specified in requirements.txt
# --no-cache-dir ensures that pip doesn't store the downloaded packages, keeping the image size smaller.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of the application code (app.py and the templates/static folders)
COPY . .

# Make port 5003 available to the world outside this container
EXPOSE 5003

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py when the container launches
# Use gunicorn for a more production-ready server than Flask's built-in one.
# We need to install it first.
RUN pip install gunicorn
CMD ["gunicorn", "--workers", "2", "--threads", "2", "--bind", "0.0.0.0:5003", "--worker-class", "eventlet", "app:app"]
