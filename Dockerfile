# Use a lightweight Python base image. Python 3.9 is a common choice,
# and 'slim-buster' provides a minimal Debian environment.
FROM python:3-slim

# Set the working directory inside the container.
# All subsequent commands will be executed relative to this directory.
WORKDIR /app

# Install system dependencies needed for Python packages, application functionality,
# and the Google Cloud SDK.
# 'ffmpeg' is crucial for video processing.
# 'build-essential' is often needed for compiling certain Python packages with native extensions.
# 'curl', 'apt-transport-https', 'gnupg' are required for installing the Google Cloud SDK.
RUN apt-get update && apt-get install -y --no-install-recommends \
    ffmpeg \
    build-essential \
    curl \
    apt-transport-https \
    gnupg \
    && rm -rf /var/lib/apt/lists/*

# Install the Google Cloud SDK.
# This adds the gcloud CLI and related tools to the container.
RUN echo "deb [signed-by=/usr/share/keyrings/cloud.google.gpg] https://packages.cloud.google.com/apt cloud-sdk main" | tee -a /etc/apt/sources.list.d/google-cloud-sdk.list && \
    curl https://packages.cloud.google.com/apt/doc/apt-key.gpg | apt-key --keyring /usr/share/keyrings/cloud.google.gpg add - && \
    apt-get update && apt-get install -y google-cloud-sdk

# Explicitly install the Google Agent Development Kit (ADK) package.
# This provides the 'adk' command.
RUN pip install google-adk

# Copy the requirements.txt file into the container.
# This step is done separately to leverage Docker's build cache.
# If requirements.txt doesn't change, this layer won't be rebuilt.
COPY requirements.txt .

# Install Python dependencies.
# --no-cache-dir prevents pip from storing downloaded packages, reducing image size.
RUN pip install --no-cache-dir -r requirements.txt

# Copy the rest of your application code into the container.
# The '.' indicates copying from the current build context (where the Dockerfile is)
# to the WORKDIR (/app) inside the container.
COPY . .

# Expose the port that your ADK web application will listen on.
# Google Agent ADK typically runs on port 8080 by default.
EXPOSE 8000

# Define the command to run your application.
# This uses the 'adk web' command, which is part of the Google Agent ADK.
# Ensure that 'adk' is in the container's PATH (which it will be after SDK install).
CMD ["adk", "web"]
