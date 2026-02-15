FROM python:3.9-slim

# Install Docker CLI (client only) to allow controlling the host docker
RUN apt-get update && apt-get install -y docker.io && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Copy requirements and install
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source code
COPY scripts/ ./scripts/
COPY setup.py .
COPY .env.example .

# Default command
CMD ["python3", "scripts/minecraft_bot.py"]
