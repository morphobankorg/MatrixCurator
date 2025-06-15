FROM python:bookworm

# Set the working directory
WORKDIR /app

# Copy the entire application code
COPY . .

# Install dependencies
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install .

ENV STREAMLIT_SERVER_PORT=80

# Define the command to run your application (e.g., using uvicorn or gunicorn)
CMD ["streamlit", "run", "src/streamlit_app.py"]