FROM python:3.10-slim-bullseye

# Set the working directory in the container
WORKDIR /app

# Copy the dependencies file to the working directory
COPY requirements.txt .

# Install dependencies, including gunicorn and eventlet for the server.
# This command is platform-agnostic as pip will fetch the correct wheels for the target architecture.
# Consolidating into a single RUN command improves layer caching.
RUN pip install --no-cache-dir -r requirements.txt gunicorn eventlet

# Copy the rest of the application code (app.py and the templates/static folders)
COPY . .

# Make port 5003 available to the world outside this container
EXPOSE 5003

# Define environment variables
ENV FLASK_APP=app.py
ENV FLASK_RUN_HOST=0.0.0.0

# Run app.py when the container launches using gunicorn
# The --worker-class eventlet is crucial for Flask-SocketIO performance.
CMD ["gunicorn", "--workers", "2", "--threads", "2", "--bind", "0.0.0.0:5003", "--worker-class", "eventlet", "app:app"]
