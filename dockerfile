# Use an official Python runtime as a parent image.
FROM python:3.13-slim

# Set the working directory in the container.
WORKDIR /app

# Copy the current directory contents into the container at /app.
COPY . /app

# Upgrade pip using pip3.
RUN python3 -m pip install --upgrade pip

# Option 1: If you have a requirements.txt file (recommended for larger projects):
# COPY requirements.txt ./
# RUN python3 -m pip install --no-cache-dir -r requirements.txt

# Option 2: Install the packages directly.
RUN python3 -m pip install simplefix pytest flask requests flask-cors

# Expose the port that your internal API will run on.
EXPOSE 5002

# Define an environment variable to tell Flask we're in production mode.
ENV FLASK_ENV=production

# Run internal_api.py when the container launches.
CMD ["python3", "internal_api.py"]