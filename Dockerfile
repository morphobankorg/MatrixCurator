# Stage 1: The Builder
# This stage installs PDM and creates a requirements.txt file from your pdm.lock.
# This keeps the final image clean and free of build-time tools like PDM.
FROM python:3.12-slim AS builder

# Install PDM
RUN pip install pdm

# Set the working directory
WORKDIR /app

# Copy only the files needed to install dependencies
COPY pyproject.toml pdm.lock ./

# Generate a requirements.txt file from the lock file for production dependencies
# The -f flag specifies the FORMAT, and the -o flag specifies the OUTPUT file.
RUN pdm export -f requirements -o requirements.txt --prod --without-hashes

# Stage 2: The Final Image
# This stage builds the lean, final image for production.

FROM python:3.12-slim

# Set environment variables for best practices in Python containers
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1

# Set the working directory
WORKDIR /app

# Copy the requirements.txt from the builder stage
COPY --from=builder /app/requirements.txt .

# Install the production dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code and other necessary files into the container
COPY src/ ./src

ENV STREAMLIT_SERVER_PORT=80

# Define the command to run your application (e.g., using uvicorn or gunicorn)
CMD ["streamlit", "run", "src/streamlit_app.py"]