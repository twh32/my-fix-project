# Stage 1: Build the React front-end
FROM node:18-alpine as frontend-build
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm install
COPY frontend/ .
RUN npm run build

# Stage 2: Build the final image with the Flask API and React build
FROM python:3.13-slim
WORKDIR /app

# Copy the entire project (including your Flask back-end and other code)
COPY . /app

# Copy the built React app from Stage 1 to the static folder in the Flask app
RUN mkdir -p static && cp -R /app/frontend/build/* static/

# Upgrade pip and install Python dependencies
RUN python3 -m pip install --upgrade pip
RUN python3 -m pip install --no-cache-dir --default-timeout=100 simplefix pytest flask requests flask-cors

# Expose the API port
EXPOSE 5002

# Set environment variable for production
ENV FLASK_ENV=production

# Start the Flask app
CMD ["python3", "internal_api.py"]