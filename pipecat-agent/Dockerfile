FROM python:3.12-slim

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y \
    libgl1 \
    libglib2.0-0 \
    curl \
    && rm -rf /var/lib/apt/lists/*

# Install uv package manager
RUN pip install uv

# Copy project files
COPY pyproject.toml .
COPY bot.py server.py index.html config.py model_utils.py kokoro_tts.py ./

# Install dependencies using uv
RUN uv pip install --system -r pyproject.toml

# Expose port
EXPOSE 7860

# Run the application
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "7860"]
