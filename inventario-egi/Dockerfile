# =============================================================
# Dockerfile - App web Flask
# =============================================================
FROM python:3.11-slim

# libs necesarias para pymssql para compilar/conectar
RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

# Usuario no-root
RUN useradd -m appuser
USER appuser

EXPOSE 5000
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--chdir", "backend/src", "app:app"]