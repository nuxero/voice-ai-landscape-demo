# Use an official Python runtime as a parent image
FROM python:3.12-slim

# Set the working directory in the container
WORKDIR /app

# Install uv package manager
RUN pip install --no-cache-dir uv

# Copy project files
COPY pyproject.toml ./
COPY config.py ./
COPY agent.py ./
COPY server.py ./
COPY index.html ./

# Install dependencies using uv sync
RUN uv sync --no-dev

# Download model files
RUN uv run agent.py download-files

# Expose the web server port
EXPOSE 7860

# Default command (can be overridden in docker-compose)
CMD ["uv", "run", "python", "server.py"]
