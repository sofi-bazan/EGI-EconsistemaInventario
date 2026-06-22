# =============================================================
# Dockerfile  —  Backend Flask (Inventario ITU)
# Ubicado en: backend/Dockerfile
# Build:  cd backend/ && docker build -t inventario-egi .
# =============================================================
FROM python:3.11-slim

ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1

# pymssql necesita FreeTDS para conectar a SQL Server
RUN apt-get update && apt-get install -y --no-install-recommends \
        gcc freetds-dev freetds-bin \
    && apt-get clean && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Solo el código del backend
COPY src/ src/

RUN useradd -m appuser && chown -R appuser /app
USER appuser

EXPOSE 5000

# gunicorn arranca desde src/ donde vive app.py, templates/ y static/
CMD ["gunicorn", "-b", "0.0.0.0:5000", "--workers", "2", \
     "--timeout", "60", "--chdir", "src", "app:app"]
