# Use a Python base image
FROM python:3.13-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the requirements file and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the application code
COPY . .

# Create a non-root user
RUN adduser --disabled-password --gecos "" myuser && chown -R myuser:myuser /app

# Switch to the non-root user
USER myuser

# Set environment variables (if needed)
ENV PATH="/home/myuser/.local/bin:$PATH"

# Expose the port your app runs on (default is 8000 for ADK web)
EXPOSE 8000

# Command to run the application
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port $PORT"]