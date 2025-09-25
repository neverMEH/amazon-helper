# Use Ubuntu base with Python to avoid Docker Hub auth issues
FROM ubuntu:22.04

# Prevent interactive prompts during package installation
ENV DEBIAN_FRONTEND=noninteractive

# Install Python 3.11, pip, and Node.js
RUN apt-get update && apt-get install -y \
    software-properties-common \
    curl \
    && add-apt-repository ppa:deadsnakes/ppa \
    && apt-get update \
    && apt-get install -y \
    python3.11 \
    python3.11-dev \
    python3.11-distutils \
    python3-pip \
    && curl -fsSL https://deb.nodesource.com/setup_18.x | bash - \
    && apt-get install -y nodejs \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Set Python 3.11 as default
RUN update-alternatives --install /usr/bin/python3 python3 /usr/bin/python3.11 1 \
    && update-alternatives --install /usr/bin/python python /usr/bin/python3.11 1

# Set working directory
WORKDIR /app

# Copy Python requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy frontend and build
COPY frontend/package*.json frontend/
WORKDIR /app/frontend
RUN npm install
COPY frontend/ .
RUN npm run build

# Go back to app directory
WORKDIR /app

# Copy the rest of the application
COPY . .

# Expose port (Railway will set PORT env var)
EXPOSE 8001

# Start the application
CMD ["python", "main_supabase.py"]