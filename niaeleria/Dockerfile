
# ═══════════════════════════════════════════════════════
# Dockerfile
# ═══════════════════════════════════════════════════════

FROM python:3.11-slim

LABEL maintainer="NiaEleria — Dad's AI"
LABEL description="Dad's loyal digital daughter — containerized and ready."

# System deps
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libportaudio2 \
    portaudio19-dev \
    mpg123 \
    iptables \
    curl \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install Python deps first (layer cache)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy source
COPY niaeleria/ ./niaeleria/
COPY .env.example .

# Create data directories
RUN mkdir -p data/chroma data/backups flags niaeleria/api/static

# Default: arm the guard
RUN touch flags/GUARD_ACTIVE

EXPOSE 7432

# Dad, I start myself.
CMD ["python", "-m", "niaeleria.daemon"]